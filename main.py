# main.py (Entegre Ana Sistem)
import cv2
import torch
import subprocess
import threading
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
from contextlib import asynccontextmanager

# ------------------- Konfigürasyon -------------------
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"  # FFmpeg yolu
SOURCES = [
    {
        'input': 0,
        'name': 'Webcam'
    },
    {
        'input': r"C:\Users\emins\Desktop\Multimedia Systems Project\video1.mp4",
        'name': 'Video 1'
    },
    {
        'input': r"C:\Users\emins\Desktop\Multimedia Systems Project\video2.mp4",
        'name': 'Video 2'
    }
]
PORT_BASE = 5000  # Temel port numarası


# ------------------- Sistem Durumu -------------------
class SystemState:
    def __init__(self):
        self.active_streams: Dict[int, dict] = {}
        self.encoding_params = {
            'resolution': '1280x720',
            'framerate': 30,
            'bitrate': '2M'
        }
        self.analytics_model = None
        self.analytics_metrics = {
            'total_detections': 0,
            'last_processed': None
        }


# ------------------- FastAPI Başlatıcı -------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Model ve sistem kaynaklarını yükle
    app.state.system = SystemState()
    app.state.system.analytics_model = torch.hub.load(
        'ultralytics/yolov5',
        'yolov5s',
        trust_repo=True
    )
    app.state.system.analytics_model.conf = 0.4

    yield  # Uygulama çalışır durumda

    # Kapanışta tüm kaynakları temizle
    for stream_id in list(app.state.system.active_streams.keys()):
        stop_stream_handler(stream_id)


app = FastAPI(lifespan=lifespan)


# ------------------- Video İşleme Çekirdeği -------------------
def video_processor(stream_id: int):
    system = app.state.system
    source = SOURCES[stream_id]

    # Video yakalayıcıyı başlat
    try:
        cap = cv2.VideoCapture(source['input'])
        if not cap.isOpened():
            raise RuntimeError(f"Kaynak açılamadı: {source['input']}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        # FFmpeg encoder'ı başlat
        ffmpeg_cmd = [
            FFMPEG_PATH,
            '-y',
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f"{width}x{height}",
            '-r', str(fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-b:v', system.encoding_params['bitrate'],
            '-f', 'rtp',
            f'udp://127.0.0.1:{PORT_BASE + (stream_id * 2)}'
        ]

        encoder = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        # Gerçek zamanlı işleme döngüsü
        while stream_id in system.active_streams:
            ret, frame = cap.read()
            if not ret:
                if source['input'] != 0:  # Webcam değilse başa sar
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            # Nesne tespiti ve analiz
            results = system.analytics_model(frame)
            detections = results.xyxy[0]

            # Görsel işaretleme
            detection_count = 0
            for *box, conf, cls in detections:
                x1, y1, x2, y2 = map(int, box)
                label = f"{system.analytics_model.names[int(cls)]} {conf:.2f}"
                color = (0, 255, 0) if int(cls) == 0 else (255, 0, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                detection_count += 1

            # Metrikleri güncelle
            system.analytics_metrics['total_detections'] += detection_count
            system.analytics_metrics['last_processed'] = str(datetime.now())

            # Stream'e veri gönder
            try:
                encoder.stdin.write(frame.tobytes())
            except BrokenPipeError:
                break

    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
    finally:
        if cap.isOpened():
            cap.release()
        if encoder.poll() is None:
            encoder.terminate()


# ------------------- API Endpoint'leri -------------------
class StreamControl(BaseModel):
    resolution: Optional[str] = None
    framerate: Optional[int] = None
    bitrate: Optional[str] = None


@app.post("/stream/{stream_id}/start")
def start_stream(stream_id: int):
    system = app.state.system
    if stream_id < 0 or stream_id >= len(SOURCES):
        raise HTTPException(404, "Geçersiz stream ID")

    if stream_id in system.active_streams:
        raise HTTPException(400, "Stream zaten aktif")

    # Yeni iş parçacığı başlat
    thread = threading.Thread(target=video_processor, args=(stream_id,))
    system.active_streams[stream_id] = {
        'thread': thread,
        'params': system.encoding_params.copy()
    }
    thread.start()

    return {"status": f"{SOURCES[stream_id]['name']} başlatıldı"}


@app.post("/stream/{stream_id}/stop")
def stop_stream_handler(stream_id: int):
    system = app.state.system
    if stream_id not in system.active_streams:
        raise HTTPException(404, "Stream bulunamadı")

    del system.active_streams[stream_id]
    return {"status": f"{SOURCES[stream_id]['name']} durduruldu"}


@app.post("/config/encoding")
def update_encoding(params: StreamControl):
    system = app.state.system
    if params.resolution:
        system.encoding_params['resolution'] = params.resolution
    if params.framerate:
        system.encoding_params['framerate'] = params.framerate
    if params.bitrate:
        system.encoding_params['bitrate'] = params.bitrate

    return {"message": "Konfigürasyon güncellendi", "new_config": system.encoding_params}


@app.get("/status")
def system_status():
    return {
        "active_streams": [
            {"id": k, "name": SOURCES[k]['name']}
            for k in app.state.system.active_streams.keys()
        ],
        "encoding_config": app.state.system.encoding_params,
        "analytics_metrics": app.state.system.analytics_metrics
    }


# ------------------- Çalıştırma -------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)