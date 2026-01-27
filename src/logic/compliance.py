from ..utils.geometry import box_contains_box
from loguru import logger

class PPEComplianceEngine:
    def __init__(self, mandatory_ppe=None):
        """
        Initialize PPE Compliance Engine.
        mandatory_ppe: list of int, class IDs of required PPE. Defaults to [1, 2] if None.
        """
        if mandatory_ppe is None:
            # Default mapping: ID -> Name. Ideally passed from Config.
            # Assuming YOLO Class IDs: 0=Person, 1=Helmet, 2=Vest, etc.
            self.mandatory_ppe = [1, 2] # Default to Helmet and Vest
        else:
            self.mandatory_ppe = mandatory_ppe

    def check_compliance(self, detections):
        """
        Check PPE compliance for each detected Person.
        detections: sv.Detections containing ALL objects (Person + PPE).
        
        Returns: 
            list of dicts: [{person_id, missing_ppe: [], status: 'SAFE'/'UNSAFE'}]
        """
        people = detections[detections.class_id == 0] # Assuming class 0 is Person
        ppe_items = detections[detections.class_id != 0] # Everything else is PPE? 
                                                         # Warning: Make sure model doesn't detect other stuff.
        
        results = []
        
        # We need tracker IDs to be consistent, but for per-frame compliance we just need boxes.
        # If tracker_id is present, use it.
        
        for i, (box, _, _, class_id, tracker_id, _) in enumerate(people):
            person_result = {
                "tracker_id": tracker_id if tracker_id is not None else -1,
                "box": box,
                "status": "SAFE",
                "missing": []
            }
            
            # Find PPE items geometrically inside this Person's box
            # Actually, PPE is usually ON the person, so extensive overlap or containment.
            # We iterate all PPE items.
            
            # Simple approach: Check if ANY Helmet is in box, ANY Vest is in box, etc.
            # Note: This is O(N*M) but N and M are small (~5-50).
            
            # TODO: Add specific class checks based on config (hardcoded for now as example)
            # Assuming: 1=Helmet, 2=Vest.
            
            detected_ppe_classes = set()
            for (p_box, _, _, p_class_id, _, _) in ppe_items:
                if box_contains_box(box, p_box, threshold=0.1): # Lower threshold as PPE is small
                    detected_ppe_classes.add(p_class_id)
            
            # Check mandatory (using dummy ID 1 for demonstration if not configured)
            # In production, use self.mandatory_ppe from config
            required = self.mandatory_ppe if self.mandatory_ppe else [1] 
            
            for req_id in required:
                if req_id not in detected_ppe_classes:
                    # Map ID to name if possible
                    name = "PPE_Item"
                    if req_id == 1: name = "Helmet"
                    elif req_id == 2: name = "Vest"
                    
                    person_result['missing'].append(name)
                    person_result['status'] = "UNSAFE"
            
            results.append(person_result)
            
        return results
