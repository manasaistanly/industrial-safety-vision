from ultralytics import YOLO
import supervision as sv
import cv2
import numpy as np

class SafeDetector:
    def __init__(self, model_path="yolov8n.pt", device="cpu", conf_threshold=0.4):
        """
        Wrapper for YOLOv8 model tailored for Safety Monitoring.
        """
        self.model = YOLO(model_path)
        self.device = device
        self.conf_threshold = conf_threshold
        
        # Define classes of interest based on COCO or custom model
        # For standard YOLOv8 COCO: 0 is Person.
        # Ideally we use a custom trained model for PPE.
        # Here we default to COCO but allow mapping.
        # IF using standard COCO:
        # 0: person
        # We assume we might detect 'backpack' or 'handbag' as proxy for testing if no custom model
        # But critical: USER REQUESTED PPE.
        # We will assume the model `model_path` provided IS the custom model or we filter for Person only 
        # for behavior and assume downstream logic handles the rest.
        
        # For this implementation, we simply return all detections and let Logic filter.
        
    def detect(self, frame):
        """
        Run inference on a frame.
        Returns: sv.Detections
        """
        results = self.model(frame, device=self.device, verbose=False, conf=self.conf_threshold)[0]
        
        # Convert to supervision Detections
        detections = sv.Detections.from_ultralytics(results)
        
        return detections
