import cv2
from publisher import publish_alert

def detect_motion():
    cap = cv2.VideoCapture(0)
    _, frame1 = cap.read()
    _, frame2 = cap.read()

    while cap.isOpened():
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) < 900:
                continue
            print("[ALERT] Motion Detected!")
            publish_alert({
                "type": "motion_after_hours",
                "location": "Zone B",
                "timestamp": "auto",  # You can use datetime.now().isoformat() instead
            })

        frame1 = frame2
        ret, frame2 = cap.read()
        if not ret:
            break

        cv2.imshow("Motion Detection", frame2)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
