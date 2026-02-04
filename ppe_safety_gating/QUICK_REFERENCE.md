# PPE Safety Gating System - Quick Reference Guide

**For:** Shop Floor Supervisors & Machine Operators
**Version:** 1.0
**Last Updated:** February 4, 2026

---

## How It Works (Simple)

### ✅ What You See When Everything is GOOD

- **Green Light ON** 💚
- **Buzzer Silent** 🔇
- **Machine Can Run** ⚙️

**What this means:** Person is wearing required PPE (helmet + safety vest)

### ❌ What You See When Something is WRONG

- **Red Light ON** 🔴
- **Buzzer Beeping** 🔔
- **Machine LOCKED** 🔒

**What this means:** Person is missing required PPE (helmet or vest)

---

## What to Do

### If Red Light is ON

1. **STOP** - Machine will not start
2. **CHECK** - Does the person have:
   - ✅ Safety helmet?
   - ✅ Safety vest?
3. **PUT ON MISSING PPE** - Worker must wear both helmet and vest
4. **WAIT 2 SECONDS** - System rechecks automatically
5. **CHECK GREEN LIGHT** - If green, machine is ready

### If Green Light is ON

- ✅ Machine is ready to operate
- ✅ Person has required PPE
- ✅ Safe to proceed with work

### If Machine Won't Start Even With Green Light

- Check machine power supply
- Check relay connection
- Contact supervisor
- Do NOT force machine operation

---

## Indicator Guide

| Light | Buzzer | Meaning | Action |
|-------|--------|---------|--------|
| 🟢 Green | Silent | PPE Compliant | ✅ Safe to work |
| 🔴 Red | Beeping | PPE Missing | ❌ Put on PPE |
| ⚫ Off | Silent | System offline | ⚠️ Contact admin |

---

## Common Situations

### Situation 1: Worker Without Helmet
```
Step 1: Red light ON, buzzer ON
Step 2: Worker puts helmet on
Step 3: System detects helmet (2-3 seconds)
Step 4: Red light turns OFF
Step 5: Green light turns ON
Step 6: Machine is ready
```

### Situation 2: Worker Forgot Vest
```
Same process as above - system requires BOTH helmet AND vest
```

### Situation 3: Visitor Without PPE
```
Step 1: Visitor enters zone
Step 2: Red light ON, buzzer ON
Step 3: Visitor either:
   a) Puts on PPE → machine unlocks, OR
   b) Leaves zone → light stays red (safe)
```

### Situation 4: System Offline
```
Step 1: Both lights OFF
Step 2: Machine LOCKED (fail-safe)
Step 3: Contact supervisor/admin
Step 4: Do NOT bypass safety system
```

---

## Safety Rules (IMPORTANT)

### ❌ DO NOT

- ❌ Try to override the system
- ❌ Disable safety lights
- ❌ Work without required PPE
- ❌ Bypass the locking mechanism
- ❌ Cover camera or block view

### ✅ DO

- ✅ Wear helmet + vest at ALL TIMES in work zone
- ✅ Report system malfunctions immediately
- ✅ Follow red light warnings
- ✅ Keep camera clear
- ✅ Exit zone if you forget PPE

---

## Troubleshooting

### "Green light won't turn on"

**Checklist:**
1. Are you wearing helmet? ☑️
2. Are you wearing vest? ☑️
3. Are you standing in camera view? ☑️
4. Did you wait 2-3 seconds? ☑️

**If still no green light:**
- System may need restart
- Contact your supervisor

### "Red light stays on even with helmet+vest"

**Possible reasons:**
- Camera angle is bad (camera can't see PPE clearly)
- Move closer to camera or adjust position
- Wait another 2-3 seconds for re-check
- If still red, contact supervisor

### "Buzzer won't stop"

- Buzzer turns off automatically when PPE is detected
- If buzzer keeps beeping:
  - Check that you're wearing helmet AND vest
  - Move into better camera view
  - Contact supervisor if problem continues

### "Light is OFF (not green or red)"

- System may be offline
- Do NOT use machine
- Contact supervisor/admin
- Machine stays locked (safe)

---

## Weekly Checks (For Supervisors)

### Every Monday

1. ✅ Check lights are working (green + red)
2. ✅ Check buzzer is working
3. ✅ Test with someone wearing PPE → should see green
4. ✅ Test with someone without PPE → should see red
5. ✅ Check camera is clean and aligned
6. ✅ Report any issues immediately

### Monthly Review

- Check event log: `ppe_safety_events.db`
- Count compliance incidents
- Identify patterns (specific workers, times, zones)
- Provide feedback to team

---

## Contact Information

| Issue | Contact |
|-------|---------|
| Light not working | ____________________ |
| Buzzer broken | ____________________ |
| Camera problem | ____________________ |
| Machine won't unlock | ____________________ |
| System offline | ____________________ |
| Emergency (override needed) | ____________________ |

---

## Emergency Override (Authorized Personnel Only)

**ONLY TO BE USED IN LIFE-THREATENING EMERGENCIES**

### Manual Override Procedure

1. **Locate** the manual override (location: ________________)
2. **Use** only if:
   - System completely offline, AND
   - Production emergency, AND
   - All other options exhausted
3. **Document** the override:
   - Time: ___________
   - Reason: ___________
   - Approved by: ___________
4. **Report** to supervisor immediately
5. **Restore** safety system as soon as possible

---

## Remember

### Safety is a Choice ✅

- Wear PPE every time
- Don't circumvent the system
- Report problems quickly
- Work safely, go home safe

### Safety is NOT

- ❌ Optional
- ❌ Negotiable
- ❌ A suggestion

---

## Key Takeaways

1. **Red Light** = Put on PPE (helmet + vest)
2. **Green Light** = Safe to work
3. **No Light** = System offline, don't use machine
4. **Helmet + Vest = Required EVERY TIME**
5. **Report Problems Immediately**

---

**Safety First. Always.**

---

## Training Sign-Off

I have read and understand the PPE Safety Gating System operation:

- [ ] I understand red = no PPE, green = OK to work
- [ ] I know to wear helmet + vest every time
- [ ] I understand the buzzer means put on PPE
- [ ] I will report system problems immediately
- [ ] I will not try to bypass the safety system

**Worker Name:** _____________________
**Date:** _____________________
**Supervisor:** _____________________

---

**Questions?** Ask your supervisor or contact the safety team.

---

### All Lights OFF (Power/System Failure)

**What it means:** System is not running

**What to do:**
1. **DO NOT OPERATE MACHINE**
2. Notify facility manager
3. Do NOT attempt manual override
4. Wait for system restart

---

## For Supervisors

### Check System Health
```bash
# View last 20 events
sqlite3 ppe_safety_events.db \
  "SELECT datetime(ts, 'unixepoch'), zone_id, missing_ppe, action_taken \
   FROM events ORDER BY ts DESC LIMIT 20;"

# Daily compliance rate
sqlite3 ppe_safety_events.db \
  "SELECT DATE(datetime(ts, 'unixepoch')) as date, \
   ROUND(100.0 * SUM(CASE WHEN action_taken='ALLOW' THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_compliant \
   FROM events GROUP BY date ORDER BY date DESC;"

# View system logs
sudo journalctl -u ppe-safety-gating -n 50
```

### Restart System
```bash
# Safe restart (will clear any stuck state)
sudo systemctl restart ppe-safety-gating

# Check status
sudo systemctl status ppe-safety-gating
```

### Emergency Override
```bash
# ONLY if emergency (e.g., medical rescue)
# Contact facility manager first

# Temporarily disable
sudo systemctl stop ppe-safety-gating

# Re-enable after emergency
sudo systemctl start ppe-safety-gating
```

---

## Compliance Monitoring

### Daily Check
- [ ] Green/Red lights functional?
- [ ] Buzzer sounds on non-compliance?
- [ ] Any "system error" patterns?
- [ ] Check event log for high BLOCK rate

### Weekly Check
```bash
# Review compliance trends
sqlite3 ppe_safety_events.db << 'EOF'
SELECT 
  DATE(datetime(ts, 'unixepoch')) as date,
  COUNT(*) as total_events,
  SUM(CASE WHEN action_taken='ALLOW' THEN 1 ELSE 0 END) as allows,
  SUM(CASE WHEN action_taken='BLOCK' THEN 1 ELSE 0 END) as blocks
FROM events
WHERE ts > datetime('now', '-7 days')
GROUP BY date;
EOF
```

### Monthly Report
- Total events processed
- Compliance rate trend
- Most common missing PPE
- Any system errors/crashes
- Equipment state (lights, buzzer)

---

## Configuration

### GPIO Pins (if relay mode)
```
Pin 17  → Machine enable/disable relay
Pin 27  → Green LED indicator
Pin 22  → Red LED indicator  
Pin 23  → Buzzer (optional)
```

### PLC Settings (if PLC mode)
```
Host: 192.168.0.10
Port: 502 (Modbus TCP)
Coil: 1 (write 0=off, 1=on)
```

### Zone Requirements (editable)
```
Default: Helmet + Safety Vest
Edit: vision/zones.py
```

---

## Safety Philosophy

**This system enforces safety through design, not punishment.**

✅ No face recognition
✅ No worker tracking  
✅ No penalties applied
✅ No supervisor involvement
✅ No biometric data storage

**Just:** Safe operation is made physically impossible without PPE

---

## Quick Commands

```bash
# Start system
sudo systemctl start ppe-safety-gating

# Stop system (emergency only)
sudo systemctl stop ppe-safety-gating

# View live logs
sudo journalctl -u ppe-safety-gating -f

# Check if running
sudo systemctl status ppe-safety-gating

# Restart (clears stuck state)
sudo systemctl restart ppe-safety-gating

# Enable auto-start on boot
sudo systemctl enable ppe-safety-gating

# View event database
sqlite3 ppe_safety_events.db "SELECT * FROM events LIMIT 10;"

# Export events as CSV
sqlite3 ppe_safety_events.db ".mode csv" "SELECT * FROM events;" > events.csv
```

---

## Contact & Escalation

**System Issue?**
→ Notify facility manager immediately
→ **DO NOT** attempt repairs
→ Do not bypass safety system

**Compliance Concern?**
→ Review events: `sqlite3 ppe_safety_events.db "SELECT * FROM events WHERE action_taken='BLOCK' LIMIT 10;"`
→ Identify patterns (timing, location, missing items)
→ Implement targeted training

**Emergency (Medical/Rescue)?**
→ Call emergency services first
→ Then notify facility manager
→ Manager can authorize temporary override

---

## Expected Behavior

| Scenario | Light | Buzzer | Machine | Action |
|----------|-------|--------|---------|--------|
| Full PPE | 🟢 | OFF | READY | Normal operation |
| No Helmet | 🔴 | ON | LOCKED | Auto-corrects |
| No Vest | 🔴 | ON | LOCKED | Auto-corrects |
| Camera Lost | 🔴 | ON | LOCKED | Reconnects auto |
| System Error | 🔴 | ON | LOCKED | Requires restart |

---

## Data Privacy

✅ **What is logged:**
- Timestamp
- Zone ID
- Missing PPE type
- ALLOW/BLOCK decision

❌ **What is NOT stored:**
- Worker names
- Worker IDs
- Worker faces
- Worker locations
- Video/images
- Identity data

**All logs are anonymous and purely for safety compliance.**

---

**Last Updated:** February 4, 2026
**System Version:** 1.0
**Test Status:** 17/17 Tests Passing ✅
