import threading
from datetime import datetime
from detection_yolo import run_yolo_detection
from motion_detection import detect_motion

def main():
    print("[INFO] Starting Surveillance Service...")

    # Run YOLO detection for vehicle/person detection
    yolo_thread = threading.Thread(target=run_yolo_detection)
    yolo_thread.start()

    # Check if it's after hours (1 AM - 5 AM)
    current_hour = datetime.now().hour
    if current_hour >= 1 or current_hour <= 5:  # Between 1 AM and 5 AM
        print("[INFO] Motion detection activated (after hours)...")
        motion_thread = threading.Thread(target=detect_motion)
        motion_thread.start()

    # Wait for the YOLO thread to finish
    yolo_thread.join()

if __name__ == "__main__":
    main()
