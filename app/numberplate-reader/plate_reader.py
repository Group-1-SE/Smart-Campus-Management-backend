import cv2
import easyocr
import re
from ultralytics import YOLO
from datetime import datetime
import numpy as np
import requests
import json

# Initialize models
vehicle_model = YOLO('yolov8n.pt')
plate_reader = easyocr.Reader(['en'], gpu=True)  # Enable GPU if available

# Sri Lankan plate pattern (with all common variations)
SRI_LANKAN_PATTERN = re.compile(
    r'^([A-Z]{2,3}\s?-?\s?\d{4}|'      # ABC-1234 or ABC 1234
    r'\d{2,3}\s?-?\s?\d{4}|'           # 12-3456 or 12 3456
    r'[A-Z]{1,2}\d{2,3}\s?-?\s?\d{3})$',  # AB12-345 (newer formats)
    re.IGNORECASE
)

def normalize_plate(text):
    """Convert any Sri Lankan plate to standard format"""
    # Remove all whitespace and convert to uppercase
    clean = re.sub(r'\s+', '', text).upper()
    
    # Insert hyphen if missing between letters/numbers
    if '-' not in clean:
        # For patterns like ABC1234 → ABC-1234
        if re.match(r'^[A-Z]{2,3}\d{4}$', clean):
            clean = f"{clean[:3]}-{clean[3:]}"
        # For patterns like 123456 → 12-3456
        elif re.match(r'^\d{2,3}\d{4}$', clean):
            clean = f"{clean[:2]}-{clean[2:]}"
    
    return clean

def validate_plate(text):
    """Check if text matches any Sri Lankan plate variation"""
    return bool(SRI_LANKAN_PATTERN.match(text))

def send_plate_number(plate_number):
    """Send detected plate number to the endpoint"""
    url = "http://localhost:8001/detect"
    payload = {
        "plate_number": plate_number
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        print(f"Successfully sent plate number: {plate_number}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending plate number: {e}")
        return False

def detect_plates(frame):
    print("Starting vehicle detection...")
    results = vehicle_model(frame)
    plates = []
    
    print(f"Found {len(results[0].boxes)} potential objects")
    for box in results[0].boxes:
        class_name = vehicle_model.names[int(box.cls)]
        print(f"Detected object: {class_name}")
        if class_name in ['car', 'truck', 'bus']:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            # Add padding around the detected region
            padding = 15
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(frame.shape[1], x2 + padding)
            y2 = min(frame.shape[0], y2 + padding)
            
            vehicle_roi = frame[y1:y2, x1:x2]
            
            print(f"Processing vehicle: {class_name}")
            # Enhanced preprocessing for Sri Lankan plates
            gray = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE with different parameters for better number visibility
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # Apply bilateral filter to remove noise while preserving edges
            gray = cv2.bilateralFilter(gray, 11, 17, 17)
            
            # Create multiple versions of the image for different preprocessing
            # Version 1: Standard adaptive threshold
            thresh1 = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Version 2: Otsu's thresholding
            _, thresh2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Version 3: Sharpen the image
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(gray, -1, kernel)
            _, thresh3 = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Noise removal for all versions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
            thresh1 = cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel)
            thresh2 = cv2.morphologyEx(thresh2, cv2.MORPH_CLOSE, kernel)
            thresh3 = cv2.morphologyEx(thresh3, cv2.MORPH_CLOSE, kernel)
            
            # Try multiple OCR attempts with different preprocessing
            plate_texts = []
            confidences = []
            
            # OCR configurations
            ocr_configs = [
                (thresh1, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- '),
                (thresh2, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- '),
                (thresh3, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- '),
                (cv2.bitwise_not(thresh1), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- '),
                (cv2.bitwise_not(thresh2), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- '),
                (cv2.bitwise_not(thresh3), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- '),
                (gray, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- ')
            ]
            
            for img, allowlist in ocr_configs:
                results = plate_reader.readtext(
                    img,
                    allowlist=allowlist,
                    detail=1,
                    paragraph=False,  # Process each line separately
                    min_size=10,      # Minimum text size
                    contrast_ths=0.1, # Lower contrast threshold
                    adjust_contrast=0.5, # Adjust contrast
                    text_threshold=0.6,  # Lower text threshold
                    link_threshold=0.4,  # Lower link threshold
                    low_text=0.4,        # Lower text threshold
                    slope_ths=0.2        # Allow more slope variation
                )
                
                for (bbox, text, prob) in results:
                    if prob > 0.4:  # Lower confidence threshold for numbers
                        plate_texts.append(text)
                        confidences.append(prob)
            
            if plate_texts:
                # Try to find the most likely valid plate
                valid_plates = [(text, conf) for text, conf in zip(plate_texts, confidences) 
                              if validate_plate(text)]
                
                if valid_plates:
                    # Sort by confidence and take the highest
                    valid_plates.sort(key=lambda x: x[1], reverse=True)
                    raw_text = valid_plates[0][0]
                    confidence = valid_plates[0][1]
                else:
                    # If no valid plates, use the highest confidence reading
                    max_conf_idx = confidences.index(max(confidences))
                    raw_text = plate_texts[max_conf_idx]
                    confidence = confidences[max_conf_idx]
                
                print(f"Raw OCR text: {raw_text} (confidence: {confidence:.2f})")
                if validate_plate(raw_text):
                    std_plate = normalize_plate(raw_text)
                    print(f"Valid plate detected: {std_plate}")
                    
                    # Send the plate number to the endpoint
                    send_plate_number(std_plate)
                    
                    # Draw on frame
                    cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
                    cv2.putText(frame, f"{std_plate} ({confidence:.2f})", (x1, y1-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
                else:
                    print(f"Invalid plate format: {raw_text}")
            else:
                print("No text detected in vehicle region")
    
    return frame

def process_image(image_path):
    """Process a single image and return the frame with detected plates"""
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"Error: Could not read image from {image_path}")
        return None
    
    frame = detect_plates(frame)
    return frame

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python plate_reader.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    frame = process_image(image_path)
    
    if frame is not None:
        cv2.imshow('Sri Lankan Plate Recognition', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()