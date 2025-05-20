import cv2
import os

def main():
    # Paths to video files
        video1_path = os.path.join(base_dir, 'videos', 'video1.mp4')
        video2_path = os.path.join(base_dir, 'videos', 'video2.mp4')

    # Open sources
    cap1 = cv2.VideoCapture(video1_path)  # Video 1
    cap2 = cv2.VideoCapture(video2_path)  # Video 2
    cap3 = cv2.VideoCapture(0)            # Webcam (device 0)

    if not cap1.isOpened():
        print("Video1 could not be opened:", video1_path)
    if not cap2.isOpened():
        print("Video2 could not be opened:", video2_path)
    if not cap3.isOpened():
        print("Webcam could not be opened")

    while True:
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        ret3, frame3 = cap3.read()

        # Loop video files if frames are finished
        if not ret1:
            cap1.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret1, frame1 = cap1.read()
        if not ret2:
            cap2.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret2, frame2 = cap2.read()

        if ret1:
            cv2.imshow('Video1', frame1)
        if ret2:
            cv2.imshow('Video2', frame2)
        if ret3:
            cv2.imshow('Webcam', frame3)

        # Press 'q' to exit
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    # Release all sources
    cap1.release()
    cap2.release()
    cap3.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
