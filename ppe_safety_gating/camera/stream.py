import time
import threading
import cv2


class RTSPStream:
    """Robust RTSP stream reader with reconnect and fail-safe behavior.

    Usage:
        s = RTSPStream(url)
        frame = s.read()
    If the stream is unavailable, read() returns None and the caller must
    enforce fail-safe (BLOCK) behavior.
    """

    def __init__(self, url, reconnect_interval=5, ffmpeg_backend=False):
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.lock = threading.Lock()
        self.cap = None
        self.running = True
        self._open()

    def _open(self):
        with self.lock:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
            # cv2.VideoCapture will use underlying ffmpeg/gstreamer depending on build
            self.cap = cv2.VideoCapture(self.url)

    def read(self):
        """Return a frame (BGR) or None if unavailable. Caller must treat None as BLOCK."""
        with self.lock:
            if self.cap is None or not self.cap.isOpened():
                try:
                    self._open()
                except Exception:
                    time.sleep(self.reconnect_interval)
                    return None
            ret, frame = self.cap.read()
            if not ret or frame is None:
                # try to re-open once
                try:
                    self._open()
                except Exception:
                    pass
                time.sleep(self.reconnect_interval)
                return None
            return frame

    def stop(self):
        with self.lock:
            self.running = False
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
