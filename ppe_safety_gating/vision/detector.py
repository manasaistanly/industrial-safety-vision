import cv2
import numpy as np
import time
import logging

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None


class Detector:
    """YOLOv8-based detector for PPE (person, helmet, vest).

    - Loads a local YOLOv8 model path or a pretrained name.
    - Filters detections by class name keywords.
    - Blurs faces on the provided frame (Haar cascade) to preserve privacy.
    """

    PPE_KEYWORDS = {
        "person": ["person"],
        "helmet": ["helmet", "hardhat", "hat"],
        "vest": ["vest", "safety vest", "reflective vest"],
    }

    def __init__(self, model_path=None, device=None, face_cascade_path=None):
        self.model = None
        self.device = device
        if YOLO is None:
            raise RuntimeError("ultralytics YOLO package is required (pip install ultralytics)")
        self.model = YOLO(model_path or "yolov8n.pt")
        if device:
            try:
                self.model.to(device)
            except Exception:
                logging.warning("Could not set device for YOLO model")

        # Load face cascade for blurring (privacy)
        if face_cascade_path is None:
            face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(face_cascade_path)

    def _match_name(self, name):
        name_lower = name.lower()
        for key, variants in self.PPE_KEYWORDS.items():
            for v in variants:
                if v in name_lower:
                    return key
        return None

    def blur_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        for (x, y, w, h) in faces:
            roi = frame[y : y + h, x : x + w]
            blur = cv2.GaussianBlur(roi, (51, 51), 0)
            frame[y : y + h, x : x + w] = blur
        return frame

    def predict(self, frame, conf_thresh=0.3):
        """Run inference and return a dict with detections and an anonymized frame.

        returns: {
            "frame": blurred_frame,
            "detections": [ {"label": "person"|"helmet"|"vest", "conf": float, "bbox": [x1,y1,x2,y2] }, ... ]
        }
        If inference fails, raises Exception (caller must enforce fail-safe BLOCK).
        """
        if self.model is None:
            raise RuntimeError("Detector model not loaded")

        # do not keep images beyond memory; we return frame only for optional local feedback
        self.blur_faces(frame)

        # run model
        start = time.time()
        try:
            results = self.model(frame)[0]
        except Exception as e:
            raise
        detections = []
        names = self.model.names if hasattr(self.model, "names") else {}
        boxes = results.boxes
        for i in range(len(boxes)):
            box = boxes[i]
            conf = float(box.conf[0]) if hasattr(box, "conf") else float(box.conf)
            if conf < conf_thresh:
                continue
            cls = int(box.cls[0]) if hasattr(box.cls, "cls") else int(box.cls)
            label = names.get(cls, str(cls))
            mapped = self._match_name(label)
            if mapped is None:
                continue
            xyxy = box.xyxy[0].tolist() if hasattr(box, "xyxy") else box.xyxy.tolist()
            detections.append({"label": mapped, "conf": conf, "bbox": xyxy})

        return {"frame": frame, "detections": detections, "inference_time": time.time() - start}
