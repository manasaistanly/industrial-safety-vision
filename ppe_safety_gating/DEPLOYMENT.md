# PPE Safety Gating - Deployment Checklist

## Pre-Deployment Validation

### Hardware Setup
- [ ] NVIDIA Jetson or Intel NUC with GPU available
- [ ] IP CCTV camera connected and tested (ping camera IP)
- [ ] RTSP stream accessible and tested with ffprobe
- [ ] GPIO pins verified with multimeter (if relay mode)
- [ ] PLC network connectivity tested (if PLC mode)
- [ ] Stack light wired and tested
- [ ] Buzzer tested
- [ ] Power supply rated for all components

### Software Setup
- [ ] Python 3.8+ installed
- [ ] All dependencies installed: `pip install -r requirements-ppe.txt`
- [ ] YOLOv8 model downloaded and verified
- [ ] GPIO library installed (Jetson.GPIO or RPi.GPIO)
- [ ] File permissions correct (read access to model, write access to db)

### Safety Tests
- [ ] Test BLOCK state: Run main.py, verify machine disabled on startup
- [ ] Test camera loss: Disconnect RTSP, verify machine stays disabled
- [ ] Test inference failure: Remove model file temporarily, verify BLOCK
- [ ] Test PPE detection: Person without helmet/vest → RED light + buzzer
- [ ] Test PPE compliance: Person with helmet + vest → GREEN light
- [ ] Test continuous monitoring: Walk in/out of zone, verify instant response
- [ ] Test fail-safe on exception: Force exception, verify BLOCK persists

### Logging Tests
- [ ] Verify SQLite database created
- [ ] Log file readable and contains events
- [ ] No images stored
- [ ] No identities logged
- [ ] Timestamps correct

### Integration Tests
- [ ] Run for 1 hour continuous operation
- [ ] Verify no crashes or hangs
- [ ] Check system resources (CPU, memory)
- [ ] Verify all events logged correctly

---

## Installation Steps

### 1. Prepare Edge Device

```bash
# Jetson setup
sudo apt-get update
sudo apt-get install python3-pip python3-dev
sudo apt-get install python3-jetson-gpio

# OR Raspberry Pi setup
pip install RPi.GPIO

# Install Python dependencies
pip install -r ppe_safety_gating/requirements-ppe.txt
```

### 2. Download YOLOv8 Model

```bash
cd ppe_safety_gating
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 3. Configure Network

```bash
# Find camera IP
nmap -p 554 192.168.0.0/24

# Test RTSP stream
ffprobe rtsp://<CAMERA_IP>:554/stream
```

### 4. Configure GPIO Pins (if using relay mode)

Edit `main.py` or pass command-line arguments:
```bash
--relay-pin 17      # GPIO17 for machine enable/disable
--green-pin 27      # GPIO27 for green LED
--red-pin 22        # GPIO22 for red LED
--buzzer-pin 23     # GPIO23 for buzzer
```

### 5. Test Run

```bash
python main.py \
  --rtsp rtsp://192.168.0.5:554/stream \
  --mode relay \
  --relay-pin 17
```

Expected behavior:
- Red LED on (BLOCK - no person present)
- Buzzer may beep
- Database created: `ppe_safety_events.db`

---

## Production Deployment

### Option A: Run as Systemd Service (Recommended)

**Create `/etc/systemd/system/ppe-safety-gating.service`:**

```ini
[Unit]
Description=PPE Safety Gating System
After=network.target
StartLimitBurst=5
StartLimitIntervalSec=30s

[Service]
Type=simple
User=root
WorkingDirectory=/home/jetson/ppe_safety_gating
ExecStart=/usr/bin/python3 main.py \
  --rtsp rtsp://192.168.0.5:554/stream \
  --mode relay \
  --relay-pin 17 \
  --green-pin 27 \
  --red-pin 22 \
  --buzzer-pin 23 \
  --db /var/log/ppe_safety_events.db

Restart=on-failure
RestartSec=10s

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ppe-safety

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable ppe-safety-gating
sudo systemctl start ppe-safety-gating

# Monitor
sudo journalctl -u ppe-safety-gating -f
```

### Option B: Run in Screen/tmux

```bash
screen -S ppe-safety -d -m bash -c 'cd /home/jetson/ppe_safety_gating && python main.py --rtsp ... --mode relay'

# Attach to monitor
screen -r ppe-safety

# Detach
# Ctrl+A then D
```

### Option C: Docker Deployment (Advanced)

**Dockerfile:**

```dockerfile
FROM nvcr.io/nvidia/l4t-base:latest

RUN apt-get update && apt-get install -y python3-pip python3-dev
COPY ppe_safety_gating /app/ppe_safety_gating
WORKDIR /app/ppe_safety_gating

RUN pip install -r requirements-ppe.txt
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

ENTRYPOINT ["python", "main.py"]
```

**Build and run:**

```bash
docker build -t ppe-safety-gating .
docker run --runtime nvidia --privileged -v /dev:/dev ppe-safety-gating \
  --rtsp rtsp://192.168.0.5:554/stream \
  --mode relay
```

---

## Monitoring & Maintenance

### Check System Status

```bash
# View running process
ps aux | grep main.py

# Check recent events
tail -100 /var/log/ppe_safety_events.db

# Monitor CPU/Memory
top -p $(pgrep -f main.py)
```

### Database Maintenance

```bash
# Backup database
cp ppe_safety_events.db ppe_safety_events.db.backup

# Export logs as CSV
sqlite3 ppe_safety_events.db ".mode csv" ".headers on" "SELECT * FROM events;" > events.csv

# Delete old events (keep 30 days)
sqlite3 ppe_safety_events.db "DELETE FROM events WHERE ts < (strftime('%s', 'now') - 2592000);"
```

### Hardware Diagnostics

```bash
# Test GPIO
python -c "import Jetson.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.OUT); GPIO.output(17, GPIO.HIGH); print('GPIO OK')"

# Test camera RTSP
ffprobe -hide_banner rtsp://192.168.0.5:554/stream 2>&1 | head -20

# Test PLC (if using)
python -c "from control.plc import PLCController; p = PLCController('192.168.0.10'); print('PLC OK')"
```

---

## Emergency Procedures

### Manual Override (Emergency Only)

If system must be disabled in emergency:

**For Relay Mode:**
```bash
# This physically enables machine (bypass safety check)
# Only authorized personnel should have access
python -c "import Jetson.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.OUT); GPIO.output(17, GPIO.HIGH)"
```

**Stop the service:**
```bash
sudo systemctl stop ppe-safety-gating
```

### Fail-Safe Verification

Test that system defaults to BLOCK:
1. Stop the service: `sudo systemctl stop ppe-safety-gating`
2. Verify relay is de-energized (machine disabled)
3. Verify red light is ON
4. Verify machine cannot start

---

## Log Review & Compliance

### Weekly Review

1. Check total BLOCK events
2. Identify patterns (e.g., specific times with high non-compliance)
3. Review any anomalies
4. Archive logs

### Monthly Report

```bash
sqlite3 ppe_safety_events.db << EOF
SELECT 
  strftime('%Y-%m-%d', datetime(ts, 'unixepoch')) as date,
  COUNT(*) as total_events,
  SUM(CASE WHEN action_taken='ALLOW' THEN 1 ELSE 0 END) as allows,
  SUM(CASE WHEN action_taken='BLOCK' THEN 1 ELSE 0 END) as blocks,
  ROUND(100.0 * SUM(CASE WHEN action_taken='ALLOW' THEN 1 ELSE 0 END) / COUNT(*), 2) as compliance_rate
FROM events
GROUP BY date
ORDER BY date DESC;
EOF
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "RTSP connection timeout" | Verify camera IP, test with ffprobe, check network |
| "GPIO: Permission denied" | Run with sudo or add user to gpio group |
| "Modbus connection failed" | Check PLC IP, verify port 502 open, test with modbus-cli |
| "YOLO model not found" | Download model: `python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"` |
| "High CPU usage" | Use smaller model (yolov8n), reduce frame rate, check for inference errors |
| "Relay always on/off" | Test GPIO pin with multimeter, verify GPIO not held by another process |

---

## Sign-Off

- [ ] System deployed and tested
- [ ] All safety tests passed
- [ ] Staff trained on emergency procedures
- [ ] Logging verified
- [ ] Backup power configured (UPS recommended)
- [ ] Maintenance schedule set
- [ ] Escalation contacts documented

**Deployment Date:** ___________

**Deployed By:** ___________

**Verified By (Safety Officer):** ___________
