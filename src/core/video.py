import cv2
import time
import threading
import queue
from loguru import logger

class VideoSource:
    def __init__(self, source, buffer_size=2):
        """
        Robust Video Source that runs in a separate thread to keep buffer fresh.
        args:
            source: int (webcam) or str (RTSP url / file path)
            buffer_size: Queue size for frames
        """
        self.source = source
        self.cap = cv2.VideoCapture(self.source)
        self.q = queue.Queue(maxsize=buffer_size)
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        
        # Stats
        self.frame_count = 0
        self.start_time = time.time()
        
        # Start reading thread
        self.t = threading.Thread(target=self._update, daemon=True)
        self.t.start()
        
        logger.info(f"Initialized VideoSource: {source}")

    def _update(self):
        while not self.stop_event.is_set():
            if not self.cap.isOpened():
                logger.warning(f"Video source {self.source} reconnecting...")
                self._reconnect()
                time.sleep(1)
                continue

            ret, frame = self.cap.read()
            if not ret:
                # If it's a file, maybe loop or stop? For industry cam, it's reconnect.
                # If persistent failure, wait a bit
                logger.warning("Failed to read frame")
                time.sleep(0.1)
                continue

            # Keep queue fresh: remove old if full
            if self.q.full():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            
            self.q.put(frame)
            self.frame_count += 1

    def _reconnect(self):
        self.cap.release()
        self.cap = cv2.VideoCapture(self.source)

    def read(self):
        """
        Get latest frame from queue. Non-blocking/blocking configurable.
        Returns: frame or None
        """
        try:
            return self.q.get(timeout=1.0) # Wait up to 1s for a frame
        except queue.Empty:
            return None

    def release(self):
        self.stop_event.set()
        self.t.join()
        self.cap.release()
