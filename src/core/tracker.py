import supervision as sv

class SafetyTracker:
    def __init__(self, track_activation_threshold=0.25, lost_track_buffer=30, frame_rate=30):
        """
        Wrapper for ByteTrack to persist object IDs.
        """
        self.tracker = sv.ByteTrack(
            track_activation_threshold=track_activation_threshold,
            lost_track_buffer=lost_track_buffer,
            frame_rate=frame_rate
        )
        
    def update(self, detections: sv.Detections):
        """
        Update tracker with new detections.
        Returns: sv.Detections (with tracker_id populated)
        """
        return self.tracker.update_with_detections(detections)
