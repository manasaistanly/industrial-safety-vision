import numpy as np
import supervision as sv
from src.logic.compliance import PPEComplianceEngine
from src.logic.behavior import BehaviorMonitor
from src.logic.zones import ZoneMonitor
import time

def demo_logic_verification():
    print("=== Starting Logic Verification Demo ===")
    
    # 1. Test PPE Compliance
    print("\n[TEST 1] PPE Compliance (Missing Helmet)")
    ppe_engine = PPEComplianceEngine()
    
    # Simulate: Person at [100,100,200,300] with NO intersecting PPE
    box_person = np.array([100, 100, 200, 300]) 
    
    # Create fake Detections object for Person (class 0)
    # xyxy, mask, confidence, class_id, tracker_id
    dets = sv.Detections(
        xyxy=np.array([box_person]),
        class_id=np.array([0]),
        confidence=np.array([0.9]),
        tracker_id=np.array([1])
    )
    
    results = ppe_engine.check_compliance(dets)
    # Currently our code Stubs compliance to always PASS or FAIL depending on impl. 
    # In src/logic/compliance.py we had a 'pass' statement for the check logic.
    # Let's verify what it returns.
    print(f"Result: {results}") 
    # Note: Real implementation needs the actual intersection logic uncommented in src/logic/compliance.py
    # verification script helps us see if we need to fix the logic!
    
    # 2. Test Running Behavior
    print("\n[TEST 2] Running Detection")
    behavior = BehaviorMonitor(fps=30)
    
    # Frame 1: Person at 0,0
    det1 = sv.Detections(
        xyxy=np.array([[0,0, 50,100]]),
        class_id=np.array([0]),
        tracker_id=np.array([1])
    )
    behavior.update(det1)
    
    # Frame 2-6: Move HUGE distance (Run)
    # 0 -> 100 pixels in 1 frame is super fast
    for i in range(5):
        pos = (i+1) * 30 # 30px per frame
        det = sv.Detections(
            xyxy=np.array([[pos, 0, pos+50, 100]]),
            class_id=np.array([0]),
            tracker_id=np.array([1])
        )
        alerts = behavior.update(det)
        if len(alerts) > 0:
            print(f"Frame {i}: Alerts: {alerts}")

    # 3. Test Zone Overcrowding
    print("\n[TEST 3] Overcrowding")
    zone_config = [{'name': 'TestZone', 'polygon': [[0,0], [500,0], [500,500], [0,500]], 'max_count': 1}]
    zm = ZoneMonitor(zones_config=zone_config)
    
    # 2 people inside zone
    det_crowd = sv.Detections(
        xyxy=np.array([
            [50,50,100,100], 
            [150,150,200,200]
        ]),
        class_id=np.array([0, 0])
    )
    
    alerts = zm.check_overcrowding(det_crowd)
    print(f"Zone Alerts: {alerts}")
    
    print("\n=== Demo Simulation Complete ===")

if __name__ == "__main__":
    demo_logic_verification()
