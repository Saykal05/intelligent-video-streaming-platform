import cv2
import torch
import subprocess
import threading

# ffmpeg.exe tam yolu
ffmpeg_path = r"C:\Users\emins\Downloads\ffmpeg-2025-05-19-git-c55d65ac0a-full_build\ffmpeg-2025-05-19-git-c55d65ac0a-full_build\bin\ffmpeg.exe"

# YOLOv5 modelini indir ve yükle
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', trust_repo=True)
model.conf = 0.4  # Confidence threshold

# Video kaynakları (kamera + iki video dosyası)
sources = [
    0,
    r"C:\Users\emins\Desktop\Multimedia Systems Project\video1.mp4",
    r"C:\Users\emins\Desktop\Multimedia Systems Project\video2.mp4"
]

# UDP portları, raw ve annotated video için
ports = [
    {'raw': 5000, 'annotated': 6000},
    {'raw': 5002, 'annotated': 6002},
    {'raw': 5004, 'annotated': 6004},
]

def ffmpeg_process(width, height, fps, port):
    command = [
        ffmpeg_path,
        '-y',
        '-f', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', f'{width}x{height}',
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-f', 'rtp',
        f'udp://127.0.0.1:{port}'
    ]
    return subprocess.Popen(command, stdin=subprocess.PIPE)

def process_source(src_index):
    cap = cv2.VideoCapture(sources[src_index])
    if not cap.isOpened():
        print(f"Kaynak açılamadı: {sources[src_index]}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or fps is None:
        fps = 25

    ff_raw = ffmpeg_process(width, height, fps, ports[src_index]['raw'])
    ff_annotated = ffmpeg_process(width, height, fps, ports[src_index]['annotated'])

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Videoyu başa sar
            continue

        # Raw stream
        try:
            ff_raw.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print(f"Raw FFmpeg pipe kapandı, kaynak index: {src_index}")
            break

        # Annotate frame
        results = model(frame)
        detections = results.xyxy[0]  # detections tensor

        for *box, conf, cls in detections:
            x1, y1, x2, y2 = map(int, box)
            label = f"{model.names[int(cls)]} {conf:.2f}"
            color = (0, 255, 0) if int(cls) == 0 else (255, 0, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Annotated stream
        try:
            ff_annotated.stdin.write(frame.tobytes())
        except BrokenPipeError:
            print(f"Annotated FFmpeg pipe kapandı, kaynak index: {src_index}")
            break

    cap.release()
    ff_raw.stdin.close()
    ff_annotated.stdin.close()
    ff_raw.wait()
    ff_annotated.wait()

threads = []
for i in range(len(sources)):
    t = threading.Thread(target=process_source, args=(i,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
