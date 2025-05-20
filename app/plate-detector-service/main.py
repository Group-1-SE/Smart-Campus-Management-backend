from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import easyocr
from collections import Counter
import time
from datetime import datetime, timedelta
import os
import requests
from fastapi import HTTPException

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load the license plate cascade classifier
plate_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml')
reader = easyocr.Reader(['en'])

camera = cv2.VideoCapture(0)  # Use camera index (0 for default webcam)

# Global variables for plate detection logic
reading_window = 10  # seconds
cooldown_period = 10  # seconds
plate_readings = []
current_plate = None
last_detection_time = None
is_reading = False
reading_start_time = None
last_snapshot = None
snapshot_path = "snapshots"
os.makedirs(snapshot_path, exist_ok=True)

# Track the last plate number sent to avoid duplicate notifications
last_sent_plate = None
last_sent_time = None
notification_cooldown = 30  # seconds between notifications for the same plate

def send_plate_to_backend(plate_number, filename):
    global last_sent_plate, last_sent_time
    current_time = time.time()
    
    # Format plate number by replacing spaces with hyphens
    formatted_plate = plate_number.replace(" ", "-")
    
    # Check if we should send this plate number
    if (formatted_plate != last_sent_plate or 
        not last_sent_time or 
        (current_time - last_sent_time) > notification_cooldown):
        try:
            response = requests.post(
                "http://localhost:8001/detect",
                json={"plate_number": formatted_plate, "filename": filename}
            )
            if response.status_code == 200:
                last_sent_plate = formatted_plate
                last_sent_time = current_time
                print(f"Successfully sent plate number {formatted_plate} to backend")
            else:
                print(f"Failed to send plate number to backend. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending plate number to backend: {str(e)}")

def preprocess_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply bilateral filter to remove noise while keeping edges sharp
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresh

def get_most_common_plate(readings):
    if not readings:
        return None
    counter = Counter(readings)
    return counter.most_common(1)[0][0]

def save_snapshot(frame, plate_text):
    global last_snapshot
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Format plate number by replacing spaces with hyphens
    formatted_plate = plate_text.replace(" ", "-")
    filename = f"{snapshot_path}/vehicle_{timestamp}_{formatted_plate}.jpg"
    cv2.imwrite(filename, frame)
    last_snapshot = filename
    return filename

def generate_frames():
    global plate_readings, current_plate, last_detection_time, is_reading, reading_start_time
    
    while True:
        success, frame = camera.read()
        if not success:
            break

        # Create a copy of the frame for drawing
        display_frame = frame.copy()
        current_time = time.time()
        
        # Check if we're in cooldown period
        if last_detection_time and (current_time - last_detection_time) < cooldown_period:
            remaining_cooldown = int(cooldown_period - (current_time - last_detection_time))
            cv2.putText(display_frame, f"Cooldown: {remaining_cooldown}s", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        # Check if we're in reading window
        elif is_reading:
            if (current_time - reading_start_time) < reading_window:
                remaining_reading = int(reading_window - (current_time - reading_start_time))
                cv2.putText(display_frame, f"Reading: {remaining_reading}s", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Process frame for plate detection
                processed = preprocess_image(frame)
                plates = plate_cascade.detectMultiScale(processed, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                for (x, y, w, h) in plates:
                    plate_roi = frame[y:y+h, x:x+w]
                    plate_gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
                    plate_gray = cv2.bilateralFilter(plate_gray, 11, 17, 17)
                    
                    text_result = reader.readtext(plate_gray)
                    
                    if text_result:
                        plate_text = text_result[0][1]
                        confidence = text_result[0][2]
                        
                        if confidence > 0.5:
                            plate_readings.append(plate_text)
                            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            text_size = cv2.getTextSize(plate_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                            cv2.rectangle(display_frame, (x, y-30), (x+text_size[0], y), (0, 255, 0), -1)
                            cv2.putText(display_frame, plate_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX,
                                        0.8, (255, 255, 255), 2)
            else:
                # Reading window ended, process results
                current_plate = get_most_common_plate(plate_readings)
                if current_plate:
                    # Save snapshot when plate is detected
                    filename = save_snapshot(frame, current_plate)
                    print(filename)
                    # Send plate number to main backend
                    send_plate_to_backend(current_plate, filename)
                plate_readings = []
                is_reading = False
                last_detection_time = current_time
        else:
            # Start new reading window
            is_reading = True
            reading_start_time = current_time
            plate_readings = []

        _, buffer = cv2.imencode('.jpg', display_frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/current_plate")
def get_current_plate():
    return {
        "plate": current_plate,
        "snapshot": last_snapshot if last_snapshot else None
    }

@app.get("/snapshot/{filename}")
def get_snapshot(filename: str):
    file_path = os.path.join(snapshot_path, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Snapshot {filename} not found")
    return FileResponse(file_path)
