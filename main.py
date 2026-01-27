import cv2
import yaml
import time
import supervision as sv
from loguru import logger
import numpy as np

from src.core.video import VideoSource
from src.core.detector import SafeDetector
from src.core.tracker import SafetyTracker
from src.logic.compliance import PPEComplianceEngine
from src.logic.behavior import BehaviorMonitor
from src.logic.zones import ZoneMonitor
from src.data.alert_manager import AlertManager

def load_config(path="configs/factory_config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def main():
    logger.info("Starting Safety Monitoring System...")
    config = load_config()
    
    # Initialize Core
    source = config['camera']['source']
    fps = config['camera'].get('fps', 30)
    video = VideoSource(source=source)
    detector = SafeDetector() # Defaults to yolov8n
    tracker = SafetyTracker()
    
    # Initialize Logic
    ppe_config = config.get('ppe', {}).get('mandatory_classes', None)
    ppe_engine = PPEComplianceEngine(mandatory_ppe=ppe_config)
    behavior_monitor = BehaviorMonitor(fps=fps)
    zone_monitor = ZoneMonitor(zones_config=config.get('zones'))
    alert_manager = AlertManager()
    
    # Annotators
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator()
    zone_annotators = [sv.PolygonZoneAnnotator(zone=z['zone'], color=sv.Color.RED) for z in zone_monitor.zones]

    try:
        while True:
            frame = video.read()
            if frame is None:
                continue

            # 1. Detection
            detections = detector.detect(frame)
            
            # 2. Tracking
            detections = tracker.update(detections)
            
            # 3. Logic & Alerts
            # Zone Logic
            zone_alerts = zone_monitor.check_overcrowding(detections)
            alert_manager.process_alerts(zone_alerts)
            
            # Behavior Logic
            behavior_alerts = behavior_monitor.update(detections)
            for tid, alerts in behavior_alerts.items():
                alert_manager.process_alerts([f"Person {tid}: {a}" for a in alerts])
            
            # PPE Logic (Placeholder logic as described in engine)
            ppe_results = ppe_engine.check_compliance(detections)
            for res in ppe_results:
                if res['status'] == 'UNSAFE':
                    alert_manager.process_alerts([f"Person {res['tracker_id']} Missing PPE: {res['missing']}"])

            # 4. Visualization
            labels = []
            for i in range(len(detections)):
                class_id = detections.class_id[i]
                tracker_id = detections.tracker_id[i]
                confidence = detections.confidence[i]
                
                # Custom label
                labels.append(f"#{tracker_id} {detector.model.names[class_id]} {confidence:.2f}")

            annotated_frame = box_annotator.annotate(scene=frame.copy(), detections=detections)
            annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
            
            # Draw Zones
            for i, za in enumerate(zone_annotators):
                za.annotate(scene=annotated_frame)

            # Draw Status
            cv2.putText(annotated_frame, "DXSO SAFETY AI", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow("Safety Monitor", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        video.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
