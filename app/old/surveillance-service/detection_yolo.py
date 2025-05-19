from ultralytics import YOLO
import cv2
import time
from publisher import publish_alert

def run_yolo_detection():
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(0)

    last_alert_time = 0
    cooldown = 15  

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        boxes = results[0].boxes

        person_detected = False
        for box in boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            if label == "person":
                person_detected = True
                confidence = float(box.conf[0])
                break  # Only care about the first person detected

        current_time = time.time()
        if person_detected:
            if current_time - last_alert_time > cooldown:
                publish_alert({
                    "type": "suspicious_activity",
                    "label": "person",
                    "confidence": confidence,
                    "location": "Gate A",
                })
                print("🔔 Alert sent for suspicious activity (person).")
                last_alert_time = current_time
            else:
                print("⏳ Person detected but alert suppressed (cooldown).")

        annotated = results[0].plot()
        cv2.imshow("YOLOv8 Detection", annotated)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
