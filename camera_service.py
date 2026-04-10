import cv2
import threading
import time
import config

class CameraService:
    def __init__(self, camera_index=config.CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap = None
        self.is_running = False
        self.lock = threading.Lock()
        self.last_frame = None

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()

    def _capture_loop(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.last_frame = frame
            time.sleep(0.03) # ~30 FPS

    def get_frame(self):
        with self.lock:
            return self.last_frame
