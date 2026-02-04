# Camera Lifecycle - Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SLAT CAMERA LIFECYCLE                            │
└─────────────────────────────────────────────────────────────────────┘

                         ┌──────────────┐
                         │  System      │
                         │  Startup     │
                         └──────┬───────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Check Working Window │
                    └───────┬───────┬───────┘
                            │       │
                    ┌───────┘       └────────┐
                    │                        │
         ┏━━━━━━━━━┷━━━━━━━━━┓    ┏━━━━━━━━┷━━━━━━━┓
         ┃  INSIDE WINDOW    ┃    ┃ OUTSIDE WINDOW ┃
         ┗━━━━━━━━┯━━━━━━━━━┛    ┗━━━━━━━━┯━━━━━━━┛
                  │                        │
                  ▼                        ▼
    ┌─────────────────────────┐  ┌──────────────────────┐
    │ Camera DISABLED         │  │ Camera BLOCKED       │
    │                         │  │                      │
    │ Show: Press SPACE       │  │ Show: Working Hours  │
    │       or ENTER          │  │       + Error Msg    │
    └─────────┬───────────────┘  └──────────────────────┘
              │                            │
              │ User presses               │ User presses
              │ SPACE/ENTER                │ SPACE/ENTER
              ▼                            ▼
    ┌─────────────────────────┐  ┌──────────────────────┐
    │ Camera ACTIVATING       │  │ Show Error           │
    │                         │  │ "Outside Hours"      │
    │ • Initialize hardware   │  └──────────────────────┘
    │ • Start 2-min timer     │
    │ • Start countdown       │
    └─────────┬───────────────┘
              │
              ▼
    ┏━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Camera ACTIVE          ┃
    ┃                        ┃
    ┃ Timer: 02:00 → 00:00   ┃
    ┃ Color: 🟢 → 🟠 → 🔴    ┃
    ┗━━━━━━━━┯━━━━━━━━━━━━━━┛
              │
              │ (Every second)
              ▼
    ┌─────────────────────────┐
    │ Update Countdown        │
    │                         │
    │ • Decrement timer       │
    │ • Update UI color       │
    │ • Check for 0           │
    └─────────┬───────────────┘
              │
        ┏━━━━━╋━━━━━┓
        ┃     │     ┃
    ┌───┘     │     └────┐
    │         │          │
    ▼         ▼          ▼
┌────────┐ ┌─────┐  ┌──────────┐
│ QR     │ │Face │  │ Timer    │
│ Scan   │ │ Rec │  │ Expired  │
└───┬────┘ └──┬──┘  └─────┬────┘
    │         │            │
    │         │            ▼
    │         │      ┌──────────────────────┐
    │         │      │ Camera DEACTIVATING  │
    │         │      │                      │
    │         │      │ • Release hardware   │
    │         │      │ • Stop timers        │
    │         │      │ • Hide camera feed   │
    └─────────┴──────┤                      │
                     └──────────┬───────────┘
    Successful scan            │
    ↓                          ▼
┌────────────────────┐   ┌────────────────────┐
│ EXTEND SESSION     │   │ Camera DISABLED    │
│                    │   │                    │
│ • Reset to 02:00   │   │ Show: Session      │
│ • Continue active  │   │       Expired      │
│ • Process record   │   │       Press SPACE  │
└────────┬───────────┘   └────────────────────┘
         │                        │
         └────────────────────────┘
                  │
                  ▼
         (Loop continues...)


═══════════════════════════════════════════════════════════════════

KEY STATES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┏━━━━━━━━━━━━━━┓  = Primary Active State
┃              ┃
┗━━━━━━━━━━━━━━┛

┌──────────────┐  = Transition/Action State
│              │
└──────────────┘

═══════════════════════════════════════════════════════════════════

TIMER COLOR CODING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 GREEN  (✓) : 02:00 → 01:01  (More than 60 seconds)
🟠 ORANGE (⚠) : 01:00 → 00:31  (30-60 seconds)  
🔴 RED    (⏰) : 00:30 → 00:00  (Less than 30 seconds)

═══════════════════════════════════════════════════════════════════

EXAMPLE TIMELINE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

08:00:00  User presses SPACE
          ├─ Camera ACTIVATES
          └─ Timer: 02:00 🟢

08:01:30  Employee A scans QR
          ├─ Attendance recorded
          ├─ Timer EXTENDS
          └─ Timer: 02:00 🟢

08:02:45  Employee B scans QR
          ├─ Attendance recorded
          ├─ Timer EXTENDS
          └─ Timer: 02:00 🟢

08:03:50  Timer countdown
          └─ Timer: 00:55 🟠

08:04:20  Timer countdown
          └─ Timer: 00:25 🔴

08:04:45  TIMEOUT!
          ├─ Camera DEACTIVATES
          └─ Show: "Session Expired"

08:05:00  User presses SPACE again
          ├─ Camera ACTIVATES
          └─ Timer: 02:00 🟢

          ... Cycle continues ...

═══════════════════════════════════════════════════════════════════

MULTI-USER SCENARIO (Session Extension Benefit):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Time      | Event              | Timer  | Camera State
──────────┼────────────────────┼────────┼──────────────
08:00:00  | User activates     | 02:00  | ACTIVE 🟢
08:00:30  | Employee 1 scans   | 02:00  | ACTIVE 🟢 (Extended!)
08:01:15  | Employee 2 scans   | 02:00  | ACTIVE 🟢 (Extended!)
08:02:50  | Employee 3 scans   | 02:00  | ACTIVE 🟢 (Extended!)
08:03:20  | Employee 4 scans   | 02:00  | ACTIVE 🟢 (Extended!)
08:04:30  | No activity...     | 00:30  | ACTIVE 🔴
08:05:00  | TIMEOUT            | 00:00  | DEACTIVATED

Total: 4 employees processed in ONE session!

Without extension, each would need to reactivate after 2 minutes.

═══════════════════════════════════════════════════════════════════
```
