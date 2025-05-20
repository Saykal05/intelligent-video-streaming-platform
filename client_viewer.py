# client_viewer.py

import cv2
import sys

def main():
    try:
        stream_id = int(sys.argv[1])
    except:
        stream_id = 0

    port = 5000 + (stream_id * 2)
    url = f"udp://127.0.0.1:{port}"

    cap = cv2.VideoCapture(url)  # default backend kullan
    if not cap.isOpened():
        print(f"[ERROR] Bağlanılamadı: {url}")
        sys.exit(1)

    print(f"[INFO] Stream {stream_id} (port {port}) dinleniyor. Çıkmak için 'q' basın.")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        cv2.imshow(f"Stream {stream_id}", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
