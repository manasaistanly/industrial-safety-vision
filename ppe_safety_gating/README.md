# AI-Based Hard Safety Gating System for PPE Compliance

## Overview

This is a **production-grade, real-world implementable** AI system that enforces PPE compliance in MSME shop floors using existing CCTV cameras and edge AI. If required PPE is not detected, the system **physically prevents machine operation** using relay or PLC control.

### Design Philosophy

**Safety must be enforced by system design, not by fear, punishment, or human surveillance.**

- If PPE is missing → unsafe work must be physically impossible
- Fully automated enforcement (no supervisors needed)
- Privacy-preserving by design (no face recognition, no worker identification)
- Fail-safe by default (defaults to BLOCK on any error)

---

## System Architecture

```
ppe_safety_gating/
├── camera/
│   └── stream.py          # RTSP camera handling with reconnect logic
├── vision/
│   ├── detector.py        # YOLOv8 PPE detection (person, helmet, vest)
│   └── zones.py           # Zone-wise PPE rules enforcement
├── safety/
│   └── gatekeeper.py      # ALLOW / BLOCK decision engine
├── control/
│   ├── relay.py           # GPIO relay control (Jetson/RPi GPIO)
│   └── plc.py             # PLC Modbus TCP control
├── feedback/
│   └── indicators.py      # LED stack light + buzzer control
├── event_storage/
│   └── events.py          # Anonymous safety event logging (SQLite)
└── main.py                # System orchestrator
```

---

## Core Safety Logic

**Exact enforcement flow (no alternatives):**

```python
IF required_PPE_detected == TRUE:
    enable_machine()
    set_indicator(GREEN)
ELSE:
    disable_machine()
    set_indicator(RED)
```

### Fail-Safe Defaults

- Default system state: **BLOCK**
- If AI crashes → BLOCK
- If camera feed is lost → BLOCK
- If inference fails → BLOCK
- If power fails → BLOCK (relay normally open)
- If any exception occurs → BLOCK

---

## Hardware Requirements

### Edge Device
- **NVIDIA Jetson Nano/Xavier** (recommended) or
- **Intel NUC** with NVIDIA GPU support

### Camera
- IP CCTV camera with **RTSP streaming** support
- Example: `rtsp://192.168.0.5:554/stream`

### Control Interface
Choose **one**:
1. **GPIO Relay** (Jetson/Raspberry Pi GPIO)
   - GPIO HIGH → Machine enabled
   - GPIO LOW → Machine disabled
   
2. **PLC via Modbus TCP**
   - Industrial-grade reliability
   - Host: `192.168.0.10` (configurable)
   - Port: `502` (standard Modbus)

### Feedback Hardware
- **Red/Green Stack Light** (dual LED indicator)
  - Green: PPE compliant, machine ready
  - Red: PPE missing, machine locked
- **Buzzer** (optional audio alarm)
  - Activates when PPE is missing

---

## Installation

### 1. Install Dependencies

```bash
python -m pip install -r ppe_safety_gating/requirements-ppe.txt
```

### 2. Prepare YOLOv8 Model

```bash
# Download model (first run will auto-download)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 3. Configure GPIO (Jetson/RPi Only)

```bash
# Install Jetson.GPIO or RPi.GPIO
# Jetson:
sudo apt-get install python3-jetson-gpio

# Raspberry Pi:
pip install RPi.GPIO
```

---

## Running the System

### Relay Mode (GPIO Control)

```bash
cd ppe_safety_gating
python main.py \
  --rtsp rtsp://192.168.0.5:554/stream \
  --model yolov8n.pt \
  --mode relay \
  --relay-pin 17 \
  --green-pin 27 \
  --red-pin 22 \
  --buzzer-pin 23 \
  --db ppe_safety_events.db
```

### PLC Mode (Modbus TCP)

```bash
cd ppe_safety_gating
python main.py \
  --rtsp rtsp://192.168.0.5:554/stream \
  --model yolov8n.pt \
  --mode plc \
  --plc-host 192.168.0.10 \
  --plc-port 502 \
  --plc-coil 1 \
  --green-pin 27 \
  --red-pin 22 \
  --buzzer-pin 23 \
  --db ppe_safety_events.db
```

---

## Configuration

### GPIO Pin Assignments (BCM)

| Component | Default Pin | Description |
|-----------|------------|-------------|
| Relay Enable | 17 | Machine enable/disable |
| Green LED | 27 | PPE compliant |
| Red LED | 22 | PPE missing |
| Buzzer | 23 | Audio alarm (optional) |

Modify `--relay-pin`, `--green-pin`, `--red-pin`, `--buzzer-pin` as needed.

### PLC Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| Host | 192.168.0.10 | PLC IP address |
| Port | 502 | Modbus TCP port |
| Coil Address | 1 | PLC coil to write (0=disable, 1=enable) |

### Zone-Based PPE Rules

Edit `vision/zones.py` to define per-zone requirements:

```python
rules = {
    "default": {"helmet", "vest"},
    "high_hazard": {"helmet", "vest", "gloves"},  # example
    "paint_booth": {"helmet", "vest", "respirator"},  # example
}
zones = ZoneRules(rules)
```

---

## Logging & Monitoring

### Anonymous Event Log

The system logs **only**:
- `timestamp` - Unix time
- `zone_id` - Zone identifier
- `missing_ppe` - Comma-separated list of missing items
- `action_taken` - "ALLOW" or "BLOCK"

**Never stored:**
- Images
- Video
- Faces
- Worker identities
- Biometric data

### Query Event Log

```python
import sqlite3
conn = sqlite3.connect("ppe_safety_events.db")
cur = conn.cursor()

# Get last 10 BLOCKs
cur.execute("SELECT * FROM events WHERE action_taken='BLOCK' ORDER BY ts DESC LIMIT 10")
for row in cur:
    print(row)
```

---

## Real-World Behavior

1. **Machine cannot start without PPE**
   - Worker enters the zone
   - System detects person
   - If no helmet/vest detected → red light + buzzer → machine locked
   - Worker self-corrects (puts on PPE)
   - System re-checks immediately
   - Green light → machine enabled

2. **No human enforcement required**
   - Fully automated
   - No supervisor review
   - No penalties or punishment
   - No identification of workers

3. **Consistent 24/7 enforcement**
   - Even at night/weekends
   - Even if worker argues
   - No exceptions

4. **Fail-safe on any error**
   - Camera disconnected → BLOCK
   - AI inference error → BLOCK
   - Network lost → BLOCK
   - Power loss → relay opens → BLOCK

---

## Module API Reference

### camera.stream.RTSPStream

```python
stream = RTSPStream(url="rtsp://192.168.0.5:554/stream")
frame = stream.read()  # Returns numpy array or None
stream.stop()
```

### vision.detector.Detector

```python
detector = Detector(model_path="yolov8n.pt")
result = detector.predict(frame, conf_thresh=0.3)
# result = {
#     "frame": blurred_frame,
#     "detections": [{"label": "person|helmet|vest", "conf": 0.95, "bbox": [x1,y1,x2,y2]}, ...],
#     "inference_time": 0.05
# }
```

### vision.zones.ZoneRules

```python
rules = ZoneRules({"default": {"helmet", "vest"}})
is_compliant, missing_ppe = rules.check(detections, zone_id="default")
# Returns (True, set()) or (False, {"helmet"}) etc.
```

### control.relay.RelayController

```python
relay = RelayController(enable_pin=17)
relay.enable()   # GPIO HIGH -> machine on
relay.disable()  # GPIO LOW -> machine off
relay.cleanup()
```

### control.plc.PLCController

```python
plc = PLCController(host="192.168.0.10", port=502, coil_address=1)
plc.enable()   # Write True to coil
plc.disable()  # Write False to coil
plc.close()
```

### feedback.indicators.IndicatorController

```python
indicator = IndicatorController(green_pin=27, red_pin=22, buzzer_pin=23)
indicator.set_allow()   # Green on, red off
indicator.set_block()   # Red on, buzzer on, green off
indicator.off()         # All off
indicator.cleanup()
```

### safety.gatekeeper.Gatekeeper

```python
gatekeeper = Gatekeeper(controller, indicator, logger.log_event)
action = gatekeeper.enforce(zone_id="default", is_compliant=True, missing_ppe=set())
# Returns Action.ALLOW or Action.BLOCK
```

### logging.events.EventLogger

```python
logger = EventLogger(db_path="ppe_safety_events.db")
logger.log_event(zone_id="default", missing_ppe=["helmet"], action_taken="BLOCK")
```

---

## Troubleshooting

### Camera Not Connecting

```bash
# Test RTSP stream with ffmpeg
ffprobe rtsp://192.168.0.5:554/stream

# Check camera is reachable
ping 192.168.0.5
```

### GPIO Permissions Error

```bash
# Grant user GPIO permissions (Jetson)
sudo usermod -a -G gpio $USER
newgrp gpio

# Or run with sudo
sudo python main.py ...
```

### Modbus Connection Failed

```bash
# Test PLC connectivity
python -c "from control.plc import PLCController; plc = PLCController('192.168.0.10'); print(plc.client)"
```

### YOLO Model Too Slow

Use a smaller model:
```bash
--model yolov8n.pt   # Nano (fastest)
--model yolov8s.pt   # Small
--model yolov8m.pt   # Medium (higher accuracy, slower)
```

---

## Safety Certifications & Compliance

This system is designed for:
- **OSHA regulations** (PPE enforcement)
- **ISO 12100** (machine safety)
- **IEC 61508** (functional safety principles)

For certification, additional validation and hazard analysis may be required.

---

## Contributing

Safety-critical modifications require:
1. Code review by safety engineer
2. Testing on real hardware
3. Documentation of changes
4. Validation against fail-safe requirements

---

## License

Internal use only. Not for redistribution without authorization.

---

## Support

For issues or questions:
- Check troubleshooting section above
- Review event logs: `ppe_safety_events.db`
- Check system logs: `journalctl -u ppe-safety-gating` (if systemd service)

---

**Safety First. Always.**
