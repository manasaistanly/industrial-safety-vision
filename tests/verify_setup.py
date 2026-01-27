import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.logic.behavior import BehaviorMonitor
    from src.logic.compliance import PPEComplianceEngine
    from src.data.alert_manager import AlertManager
    from src.data.storage import DatabaseManager
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_initialization():
    print("Testing BehaviorMonitor...")
    bm = BehaviorMonitor(fps=60)
    assert bm.fps == 60
    assert bm.max_history == 120
    print("BehaviorMonitor OK")

    print("Testing PPEComplianceEngine...")
    ppe = PPEComplianceEngine(mandatory_ppe=[1])
    assert ppe.mandatory_ppe == [1]
    print("PPEComplianceEngine OK")

    print("Testing AlertManager and Database...")
    am = AlertManager()
    # Test threaded audio call (mock winsound if needed or just ensure no crash)
    am.process_alerts(["Test Alert"])
    # Wait a bit for thread
    time.sleep(0.1)
    print("AlertManager OK")

if __name__ == "__main__":
    test_initialization()
