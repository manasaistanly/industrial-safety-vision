import numpy as np
from collections import deque
import supervision as sv

class BehaviorMonitor:
    def __init__(self, fps=30):
        """
        Initialize Behavior Monitor.
        fps: int, frames per second of the video source. Used for speed calculation.
        """
        # Maps tracker_id -> deque of (x, y, timestamp)
        self.history = {} 
        self.fps = fps
        self.max_history = fps * 2 # Keep 2 seconds of history
        
        # Logic thresholds
        self.running_threshold = 5.0 # pixels/frame (Needs calibration to meters/sec ideally)

    def update(self, detections):
        """
        Update history and detect behavior.
        detections: sv.Detections (must have tracker_id)
        Returns: dict {tracker_id: ['Running', ...]}
        """
        alerts = {}
        
        # Only track People (class_id 0)
        people = detections[detections.class_id == 0]
        
        import time
        timestamp = time.time()
        
        for box, _, _, class_id, tracker_id, _ in people:
            if tracker_id is None:
                continue
                
            cx = (box[0] + box[2]) / 2
            cy = (box[1] + box[3]) / 2
            
            if tracker_id not in self.history:
                self.history[tracker_id] = deque(maxlen=self.max_history)
            
            self.history[tracker_id].append((cx, cy, timestamp))
            
            # Speed Check
            if len(self.history[tracker_id]) > 5:
                # Calc avg speed over last 5 frames
                recent = list(self.history[tracker_id])[-5:]
                dx = recent[-1][0] - recent[0][0]
                dy = recent[-1][1] - recent[0][1]
                dt = recent[-1][2] - recent[0][2]
                
                dist = np.sqrt(dx**2 + dy**2)
                
                # Avoid division by zero
                if dt > 0:
                    speed = dist / dt # pixels per second
                else:
                    speed = 0
                
                # Threshold needs to be in pixels/second now. 
                # Old was 5 px/frame @ 30fps => 150 px/sec.
                if speed > (self.running_threshold * 30): # Approximate conversion or update threshold config
                    if tracker_id not in alerts:
                        alerts[tracker_id] = []
                    alerts[tracker_id].append("Running")
        
        return alerts
