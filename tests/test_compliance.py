import sys
import os
import numpy as np
import supervision as sv

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.logic.compliance import PPEComplianceEngine

def test_compliance():
    print("Testing Compliance Engine...")
    
    # Initialize engine with new Dataset IDs
    # Person=11, Hardhat=3, Vest=13
    engine = PPEComplianceEngine(mandatory_ppe=[3, 13], person_class_id=11)
    
    # Mock Detections
    # Format: xyxy, mask, confidence, class_id, tracker_id, data
    
    # Case 1: Person Only (Unsafe)
    # Person box: [100, 100, 200, 200]
    
    xyxy = np.array([
        [100, 100, 200, 200], # Person
    ])
    class_id = np.array([11])
    tracker_id = np.array([1])
    
    detections = sv.Detections(
        xyxy=xyxy,
        class_id=class_id,
        tracker_id=tracker_id,
        confidence=np.array([0.9])
    )
    
    results = engine.check_compliance(detections)
    print(f"Case 1 (Person Only): {results[0]['status']} - Missing: {results[0]['missing']}")
    assert results[0]['status'] == "UNSAFE"
    assert "Hardhat" in results[0]['missing']
    assert "Safety Vest" in results[0]['missing']
    
    # Case 2: Person + Hardhat (Unsafe)
    # Hardhat box inside person: [110, 110, 150, 150]
    
    xyxy = np.array([
        [100, 100, 200, 200], # Person
        [110, 110, 150, 150]  # Hardhat (Class 3)
    ])
    class_id = np.array([11, 3])
    tracker_id = np.array([1, None])
    
    detections = sv.Detections(
        xyxy=xyxy,
        class_id=class_id,
        tracker_id=tracker_id,
        confidence=np.array([0.9, 0.9])
    )
    
    results = engine.check_compliance(detections)
    print(f"Case 2 (Person + Hardhat): {results[0]['status']} - Missing: {results[0]['missing']}")
    assert results[0]['status'] == "UNSAFE"
    assert "Hardhat" not in results[0]['missing']
    assert "Safety Vest" in results[0]['missing']

    # Case 3: Person + Hardhat + Vest (Safe)
    # Vest box inside person: [110, 150, 190, 190]
    
    xyxy = np.array([
        [100, 100, 200, 200], # Person
        [110, 110, 150, 150], # Hardhat
        [110, 150, 190, 190]  # Vest (Class 13)
    ])
    class_id = np.array([11, 3, 13])
    tracker_id = np.array([1, None, None])
    
    detections = sv.Detections(
        xyxy=xyxy,
        class_id=class_id,
        tracker_id=tracker_id,
        confidence=np.array([0.9, 0.9, 0.9])
    )
    
    results = engine.check_compliance(detections)
    print(f"Case 3 (Full PPE): {results[0]['status']} - Missing: {results[0]['missing']}")
    assert results[0]['status'] == "SAFE"
    assert len(results[0]['missing']) == 0
    
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_compliance()
