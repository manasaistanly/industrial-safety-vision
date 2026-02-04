"""Test suite for PPE Safety Gating System.

Run: python tests.py
"""
import unittest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))

from vision.zones import ZoneRules
from safety.gatekeeper import Gatekeeper, Action

# Import event logger carefully to avoid naming conflict
import importlib.util
spec = importlib.util.spec_from_file_location(
    "event_logger_module",
    os.path.join(os.path.dirname(__file__), "event_storage", "events.py")
)
event_logger_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_logger_module)
EventLogger = event_logger_module.EventLogger


class TestZoneRules(unittest.TestCase):
    """Test zone-based PPE rule checking."""

    def test_default_zone_requires_helmet_and_vest(self):
        rules = ZoneRules()
        required = rules.required_for("default")
        self.assertEqual(required, {"helmet", "vest"})

    def test_check_compliant_with_all_ppe(self):
        rules = ZoneRules()
        detections = [
            {"label": "person", "conf": 0.9},
            {"label": "helmet", "conf": 0.95},
            {"label": "vest", "conf": 0.92},
        ]
        compliant, missing = rules.check(detections, "default")
        self.assertTrue(compliant)
        self.assertEqual(missing, set())

    def test_check_missing_helmet(self):
        rules = ZoneRules()
        detections = [
            {"label": "person", "conf": 0.9},
            {"label": "vest", "conf": 0.92},
        ]
        compliant, missing = rules.check(detections, "default")
        self.assertFalse(compliant)
        self.assertEqual(missing, {"helmet"})

    def test_check_missing_both(self):
        rules = ZoneRules()
        detections = [{"label": "person", "conf": 0.9}]
        compliant, missing = rules.check(detections, "default")
        self.assertFalse(compliant)
        self.assertEqual(missing, {"helmet", "vest"})

    def test_custom_zone_rules(self):
        rules = ZoneRules({"hazard_zone": {"helmet", "vest", "gloves"}})
        detections = [
            {"label": "person"},
            {"label": "helmet"},
            {"label": "vest"},
        ]
        compliant, missing = rules.check(detections, "hazard_zone")
        self.assertFalse(compliant)
        self.assertEqual(missing, {"gloves"})


class TestGatekeeper(unittest.TestCase):
    """Test gatekeeper enforcement logic."""

    def setUp(self):
        self.controller = Mock()
        self.indicator = Mock()
        self.logger = Mock()
        self.gatekeeper = Gatekeeper(self.controller, self.indicator, self.logger)

    def test_allow_when_compliant(self):
        action = self.gatekeeper.enforce("default", True, set())
        self.assertEqual(action, Action.ALLOW)
        self.controller.enable.assert_called_once()
        self.indicator.set_allow.assert_called_once()
        self.logger.assert_called_once()

    def test_block_when_not_compliant(self):
        action = self.gatekeeper.enforce("default", False, {"helmet"})
        self.assertEqual(action, Action.BLOCK)
        self.controller.disable.assert_called()
        self.indicator.set_block.assert_called()
        self.logger.assert_called_once()

    def test_fail_safe_on_controller_error(self):
        self.controller.enable.side_effect = Exception("Hardware error")
        action = self.gatekeeper.enforce("default", True, set())
        self.assertEqual(action, Action.BLOCK)
        self.indicator.set_block.assert_called()

    def test_logs_missing_ppe(self):
        missing = {"helmet", "vest"}
        self.gatekeeper.enforce("default", False, missing)
        # Logger called with missing PPE
        call_args = self.logger.call_args
        self.assertIn("default", call_args[0])
        self.assertEqual(set(call_args[0][1]), missing)


class TestEventLogger(unittest.TestCase):
    """Test anonymous event logging."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.logger = EventLogger(self.temp_db.name)

    def tearDown(self):
        try:
            os.unlink(self.temp_db.name)
        except Exception:
            pass

    def test_log_event_creates_database(self):
        self.assertTrue(os.path.exists(self.temp_db.name))

    def test_log_event_stores_data(self):
        self.logger.log_event("default", ["helmet"], "BLOCK")
        conn = sqlite3.connect(self.temp_db.name)
        cur = conn.cursor()
        cur.execute("SELECT * FROM events")
        rows = cur.fetchall()
        conn.close()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], "default")  # zone_id
        self.assertEqual(rows[0][3], "helmet")  # missing_ppe
        self.assertEqual(rows[0][4], "BLOCK")  # action

    def test_no_identities_logged(self):
        """Verify database schema does not include identity fields."""
        conn = sqlite3.connect(self.temp_db.name)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(events)")
        columns = [col[1] for col in cur.fetchall()]
        conn.close()
        # Ensure no identity-related fields
        forbidden = ["name", "id_card", "face", "worker_id", "employee_id"]
        for col in columns:
            self.assertNotIn(col.lower(), forbidden)

    def test_multiple_events(self):
        self.logger.log_event("default", [], "ALLOW")
        self.logger.log_event("default", ["helmet"], "BLOCK")
        self.logger.log_event("default", ["vest"], "BLOCK")
        
        conn = sqlite3.connect(self.temp_db.name)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM events")
        count = cur.fetchone()[0]
        conn.close()
        self.assertEqual(count, 3)


class TestFailSafeBehavior(unittest.TestCase):
    """Test fail-safe design principles."""

    def test_gatekeeper_default_blocks(self):
        """System should default to BLOCK."""
        controller = Mock()
        indicator = Mock()
        logger = Mock()
        gatekeeper = Gatekeeper(controller, indicator, logger)
        
        # Any non-compliant state -> BLOCK
        action = gatekeeper.enforce("default", False, set())
        self.assertEqual(action, Action.BLOCK)

    def test_block_on_any_exception(self):
        """Any exception should result in BLOCK."""
        controller = Mock()
        controller.enable.side_effect = RuntimeError("Hardware failure")
        controller.disable.side_effect = RuntimeError("Hardware failure")
        
        indicator = Mock()
        logger = Mock()
        gatekeeper = Gatekeeper(controller, indicator, logger)
        
        action = gatekeeper.enforce("default", True, set())
        # Should still BLOCK on exception
        self.assertEqual(action, Action.BLOCK)
        indicator.set_block.assert_called()


class TestIntegration(unittest.TestCase):
    """Integration tests."""

    def test_full_workflow_compliant(self):
        """Test full workflow with compliant PPE."""
        # Setup
        controller = Mock()
        indicator = Mock()
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()
        logger = EventLogger(temp_db.name)
        
        gatekeeper = Gatekeeper(
            controller, indicator, logger.log_event
        )
        rules = ZoneRules()
        
        # Detections with full PPE
        detections = [
            {"label": "person", "conf": 0.9},
            {"label": "helmet", "conf": 0.95},
            {"label": "vest", "conf": 0.92},
        ]
        
        # Check and enforce
        compliant, missing = rules.check(detections, "default")
        action = gatekeeper.enforce("default", compliant, missing)
        
        # Verify
        self.assertEqual(action, Action.ALLOW)
        controller.enable.assert_called_once()
        indicator.set_allow.assert_called_once()
        
        # Cleanup
        os.unlink(temp_db.name)

    def test_full_workflow_non_compliant(self):
        """Test full workflow with missing PPE."""
        # Setup
        controller = Mock()
        indicator = Mock()
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()
        logger = EventLogger(temp_db.name)
        
        gatekeeper = Gatekeeper(
            controller, indicator, logger.log_event
        )
        rules = ZoneRules()
        
        # Detections without helmet
        detections = [
            {"label": "person", "conf": 0.9},
            {"label": "vest", "conf": 0.92},
        ]
        
        # Check and enforce
        compliant, missing = rules.check(detections, "default")
        action = gatekeeper.enforce("default", compliant, missing)
        
        # Verify
        self.assertEqual(action, Action.BLOCK)
        self.assertIn("helmet", missing)
        controller.disable.assert_called()
        indicator.set_block.assert_called()
        
        # Cleanup
        os.unlink(temp_db.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
