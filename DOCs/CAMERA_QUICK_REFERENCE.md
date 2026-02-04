# 🎯 Camera Lifecycle - Quick Reference Card

## 🔑 ACTIVATION KEYS
```
┌──────────────────────────────────────┐
│  SPACE  or  ENTER  = Activate Camera │
└──────────────────────────────────────┘
```

## ⏱️ TIMER RULES
```
┌─────────────────────────────────────────────┐
│ Initial Duration:     2 minutes (120 sec)   │
│ Extension per Scan:   +2 minutes            │
│ Auto-Close:           At 00:00              │
└─────────────────────────────────────────────┘
```

## 🚦 COLOR CODES
```
🟢  ✓ Session: 02:00  →  ✓ Session: 01:01
    GREEN = Safe (> 60 seconds)

🟠  ⚠ Session: 01:00  →  ⚠ Session: 00:31
    ORANGE = Warning (30-60 seconds)

🔴  ⏰ Session: 00:30  →  ⏰ Session: 00:00
    RED = Critical (< 30 seconds)
```

## 📍 AVAILABILITY
```
┌────────────────────────────────────────┐
│ ✅ AVAILABLE: Inside working hours     │
│    • Morning window (arrival)          │
│    • Afternoon window (departure)      │
│                                        │
│ ❌ BLOCKED: Outside working hours      │
│    • Camera cannot be activated        │
│    • Use Card ID mode instead          │
└────────────────────────────────────────┘
```

## 🔄 SESSION FLOW
```
1️⃣ Press SPACE/ENTER
   └─> Camera activates
   └─> Timer starts at 02:00

2️⃣ Scan QR or Face
   └─> Attendance recorded
   └─> Timer resets to 02:00

3️⃣ Another person scans
   └─> Attendance recorded
   └─> Timer resets to 02:00

4️⃣ (continues...)

5️⃣ No activity for 2 minutes
   └─> Timer reaches 00:00
   └─> Camera closes automatically

6️⃣ To reactivate
   └─> Press SPACE/ENTER again
```

## 💡 TIPS

### For Single User
- Activate camera when ready
- Scan your QR/face
- No need to wait - move on
- Camera will auto-close after 2 min

### For Groups
- One person activates camera
- Everyone scans in sequence
- Each scan extends the session
- Last person doesn't need to deactivate

### If Timer Expires
- Don't panic!
- Just press SPACE/ENTER again
- Camera reactivates instantly
- Continue as normal

## 🆘 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Can't activate | Check if you're in working hours |
| Timer expired too fast | Each scan extends it - working as designed |
| Camera won't start | Verify you're in QR or Face mode |
| Wrong mode | Press TAB to switch modes |

## 📋 KEYBOARD SHORTCUTS
```
┌─────────────────────────────────────────────┐
│ SPACE / ENTER  →  Activate camera           │
│ TAB            →  Switch method (QR/Face/ID)│
│ F11 (5x)       →  Admin access               │
│ ESC            →  (Ignored for security)     │
└─────────────────────────────────────────────┘
```

## ⚙️ TECHNICAL SPECS
```
┌─────────────────────────────────────────────┐
│ Frame Rate:           ~33 FPS               │
│ Session Duration:     120 seconds           │
│ Countdown Update:     Every 1 second        │
│ Resource Cleanup:     Automatic             │
│ Multiple Users:       Supported             │
└─────────────────────────────────────────────┘
```

## 🔐 PRIVACY & SECURITY
```
✅ Camera never runs automatically
✅ Explicit user activation required
✅ Limited to working hours only
✅ Automatic timeout and shutdown
✅ Clear visual status indicator
✅ Full transparency to users
```

## 📊 EXAMPLE SCENARIOS

### Scenario A: Rush Hour (Many Employees)
```
Time    | Action              | Timer
--------|---------------------|-------
08:00   | User presses SPACE  | 02:00 🟢
08:00:30| Employee #1 scans   | 02:00 🟢
08:01:00| Employee #2 scans   | 02:00 🟢
08:01:30| Employee #3 scans   | 02:00 🟢
08:02:00| Employee #4 scans   | 02:00 🟢
08:02:30| Employee #5 scans   | 02:00 🟢
...continues as long as people scan within 2 minutes...
```
**Result**: Entire group processed in ONE session!

### Scenario B: Single Employee
```
Time    | Action              | Timer
--------|---------------------|-------
14:30   | User presses SPACE  | 02:00 🟢
14:30:05| Employee scans      | 02:00 🟢
14:30:10| Employee leaves     | 01:55 🟢
14:31   | (no activity)       | 01:00 🟠
14:32   | (no activity)       | 00:00 🔴
14:32:30| Camera auto-closes  | ---
```
**Result**: Clean automatic shutdown

### Scenario C: Outside Hours
```
Time    | Action              | Result
--------|---------------------|--------
22:00   | User presses SPACE  | ❌ ERROR
        |                     | "Outside working hours"
        |                     | Shows schedule
```
**Result**: Camera protected, privacy maintained

---

**Need Help?** Ask your system administrator
**Version:** 1.0
**Last Updated:** February 3, 2026
