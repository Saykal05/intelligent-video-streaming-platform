import cv2
import torch

# Load YOLOv5s model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', trust_repo=True)
model.conf = 0.4  # Minimum confidence threshold

# Video paths
video1_path = r"C:\Users\emins\Desktop\Multimedia Systems Project\video1.mp4"
video2_path = r"C:\Users\emins\Desktop\Multimedia Systems Project\video2.mp4"

# Capture sources
cap1 = cv2.VideoCapture(video1_path)
cap2 = cv2.VideoCapture(video2_path)
cap3 = cv2.VideoCapture(0)

def detect_and_annotate(frame):
    results = model(frame)
    detections = results.xyxy[0]  # x1, y1, x2, y2, conf, cls

    for *box, conf, cls in detections:
        label = f"{model.names[int(cls)]} {conf:.2f}"
        x1, y1, x2, y2 = map(int, box)
        color = (0, 255, 0) if int(cls) == 0 else (255, 0, 0)  # green for person
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return frame

while True:
    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()
    ret3, frame3 = cap3.read()

    # Restart video1 if ends
    if not ret1:
        cap1.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret1, frame1 = cap1.read()
    if not ret2:
        cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret2, frame2 = cap2.read()

    if ret1:
        annotated1 = detect_and_annotate(frame1)
        cv2.imshow('Video1 + Detection', annotated1)
    if ret2:
        annotated2 = detect_and_annotate(frame2)
        cv2.imshow('Video2 + Detection', annotated2)
    if ret3:
        annotated3 = detect_and_annotate(frame3)
        cv2.imshow('Webcam + Detection', annotated3)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap1.release()
cap2.release()
cap3.release()
cv2.destroyAllWindows()
