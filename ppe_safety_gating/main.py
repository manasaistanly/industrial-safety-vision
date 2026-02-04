"""Main orchestrator for PPE safety gating.

Design notes:
- Default system state is BLOCK. Any exception -> BLOCK.
- No face processing beyond immediate blurring (no storage).
- No identity or image storage; only anonymous events logged.
"""
import time
import argparse
import logging

from camera.stream import RTSPStream
from vision.detector import Detector
from vision.zones import ZoneRules
from control.relay import RelayController
from feedback.indicators import IndicatorController
from safety.gatekeeper import Gatekeeper
from event_storage.events import EventLogger


def build_components(args):
    # Camera
    stream = RTSPStream(args.rtsp)

    # Detector
    detector = Detector(model_path=args.model)

    # Zones
    zones = ZoneRules()

    # Controller (relay mode by default)
    if args.mode == "relay":
        controller = RelayController(enable_pin=args.relay_pin)
    else:
        # PLC mode
        from control.plc import PLCController

        controller = PLCController(host=args.plc_host, port=args.plc_port, coil_address=args.plc_coil)

    # Indicators
    indicators = IndicatorController(green_pin=args.green_pin, red_pin=args.red_pin, buzzer_pin=args.buzzer_pin)

    # Logger
    logger = EventLogger(db_path=args.db)

    gatekeeper = Gatekeeper(controller=controller, indicator=indicators, logger=logger.log_event)

    return stream, detector, zones, gatekeeper, logger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rtsp", required=True, help="RTSP URL of the camera")
    parser.add_argument("--model", default="yolov8n.pt", help="YOLOv8 model path")
    parser.add_argument("--mode", choices=["relay", "plc"], default="relay")
    parser.add_argument("--relay-pin", type=int, default=17)
    parser.add_argument("--green-pin", type=int, default=27)
    parser.add_argument("--red-pin", type=int, default=22)
    parser.add_argument("--buzzer-pin", type=int, default=23)
    parser.add_argument("--plc-host", type=str, default="192.168.0.10")
    parser.add_argument("--plc-port", type=int, default=502)
    parser.add_argument("--plc-coil", type=int, default=1)
    parser.add_argument("--db", default="ppe_safety_events.db")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # Default to BLOCK on startup
    try:
        stream, detector, zones, gatekeeper, logger = build_components(args)
    except Exception as e:
        logging.exception("Failed to initialize components; system will remain in BLOCK state")
        return

    last_action = None
    zone_id = "default"

    try:
        while True:
            frame = None
            try:
                frame = stream.read()
            except Exception:
                frame = None

            # If camera feed lost -> BLOCK (fail-safe)
            if frame is None:
                gatekeeper.enforce(zone_id, False, {"helmet", "vest"})
                last_action = "BLOCK"
                time.sleep(1)
                continue

            # Run inference
            try:
                out = detector.predict(frame)
            except Exception:
                # inference failure -> BLOCK
                gatekeeper.enforce(zone_id, False, {"helmet", "vest"})
                last_action = "BLOCK"
                time.sleep(1)
                continue

            detections = out.get("detections", [])

            # If no person present => BLOCK (do not enable machine when no person present)
            person_present = any(d.get("label") == "person" for d in detections)
            if not person_present:
                gatekeeper.enforce(zone_id, False, {"helmet", "vest"})
                last_action = "BLOCK"
                time.sleep(0.5)
                continue

            # Check PPE
            is_compliant, missing = zones.check(detections, zone_id)

            action = gatekeeper.enforce(zone_id, is_compliant, missing)
            last_action = action.value

            # continuous re-check while person present
            time.sleep(0.2)

    except KeyboardInterrupt:
        logging.info("Shutting down: cleaning up hardware interfaces")
    finally:
        try:
            stream.stop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
