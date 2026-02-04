# Camera Lifecycle Implementation - Validation

## Implemented Rules

### ✅ Camera Disabled Outside Working Windows
- Camera will not activate when outside morning/afternoon windows
- UI displays working hours and explains why camera is disabled
- Users are informed of the next available window

### ✅ Camera Opens Only After Key Press
- **Inside working window**: Camera does NOT start automatically
- User must press **SPACE** or **ENTER** to activate camera
- Clear instructions displayed on screen
- Works for both QR and Face Recognition modes

### ✅ Camera Stays ON for 2 Minutes
- Session timer starts when camera is activated
- Timer set to exactly 120 seconds (2 minutes)
- Real-time countdown displayed to user with color indicators:
  - **Green** (✓): > 60 seconds remaining
  - **Orange** (⚠): 30-60 seconds remaining
  - **Red** (⏰): < 30 seconds remaining

### ✅ Each Successful Scan Extends Timer by 2 Minutes
- **QR Code scan**: Resets timer to 2 minutes after successful attendance
- **Face Recognition**: Resets timer to 2 minutes after successful attendance
- Extension is logged to console for debugging
- Countdown display updates immediately

### ✅ Timer Expiration Closes Camera Immediately
- When timer reaches 0, camera is closed automatically
- Camera resources are properly released
- All timers are stopped
- UI shows reactivation instructions
- User can press SPACE/ENTER again to reactivate

## Implementation Details

### New Properties Added
```python
self.camera_active = False  # Track if camera is currently active
self.camera_session_timer = QTimer()  # 2-minute timeout timer
self.camera_session_duration = 120  # 2 minutes in seconds
self.camera_session_remaining = 0  # Countdown seconds
self.countdown_timer = QTimer()  # UI update timer (1 second intervals)
```

### New UI Elements
1. **camera_instruction_label**: Shows activation/reactivation instructions
2. **camera_countdown_label**: Shows real-time session countdown (MM:SS)

### Key Methods

#### `is_in_working_window()`
- Checks if current time falls within morning or afternoon windows
- Returns True/False

#### `activate_camera()`
- Initializes camera hardware
- Starts frame processing timer (30ms = ~33 FPS)
- Starts 2-minute session timer
- Starts countdown display timer (1 second updates)
- Shows camera feed and countdown

#### `deactivate_camera()`
- Releases camera hardware
- Stops all timers
- Hides camera feed
- Shows reactivation instructions

#### `extend_camera_session()`
- Called after successful QR scan or face recognition
- Resets session timer to 2 minutes
- Restarts timer
- Updates countdown display

#### `on_camera_session_timeout()`
- Called when 2-minute timer expires
- Immediately calls deactivate_camera()

#### `update_camera_countdown()`
- Updates every second
- Decrements remaining time
- Updates UI with MM:SS format
- Changes color based on remaining time

### Key Press Handling
- **SPACE** or **ENTER**: Activates camera (if in working window and camera inactive)
- **TAB**: Switches between enabled methods
- **F11** (5 times): Opens admin interface

## User Experience Flow

### Scenario 1: Within Working Window
1. User arrives at terminal
2. Screen shows: "⌨️ Appuyez sur ESPACE ou ENTRÉE pour activer la caméra"
3. User presses SPACE
4. Camera activates with countdown: "✓ Session: 02:00"
5. User scans QR code
6. Attendance recorded
7. Timer resets: "✓ Session: 02:00"
8. If no activity for 2 minutes → Camera closes
9. Screen shows: "⏱️ Session caméra expirée" + reactivation instructions

### Scenario 2: Outside Working Window
1. User arrives at terminal
2. Screen shows: "⏰ Caméra désactivée en dehors des fenêtres horaires"
3. Display shows working hours (morning/afternoon)
4. Pressing SPACE shows error: "⏰ Hors fenêtre horaire - Caméra désactivée"
5. User must use Card ID mode (if enabled)

### Scenario 3: Multiple Scans
1. Camera activated
2. Employee 1 scans at 02:00 remaining → Attendance recorded, timer reset to 02:00
3. Employee 2 scans at 01:45 remaining → Attendance recorded, timer reset to 02:00
4. Employee 3 scans at 00:30 remaining → Attendance recorded, timer reset to 02:00
5. Continues until 2 minutes pass with no activity

## Testing Checklist

- [ ] Camera does NOT start when outside working windows
- [ ] Camera does NOT start automatically when in QR/Face mode
- [ ] Camera starts when SPACE is pressed (within working window)
- [ ] Camera starts when ENTER is pressed (within working window)
- [ ] Countdown displays correctly (MM:SS format)
- [ ] Countdown color changes at 60s and 30s thresholds
- [ ] QR scan extends timer to 2:00
- [ ] Face recognition extends timer to 2:00
- [ ] Timer expiration closes camera
- [ ] Reactivation works after expiration
- [ ] Multiple employees can use same session (with timer extension)
- [ ] Camera properly releases resources on timeout
- [ ] Mode switching properly cleans up camera

## Benefits of This Model

1. **Energy Efficient**: Camera only runs when needed
2. **Privacy Focused**: Camera isn't always watching
3. **User Control**: Explicit activation required
4. **Fair to Multiple Users**: Each scan extends the session
5. **Predictable**: Clear countdown and visual feedback
6. **Secure**: Outside working hours = camera disabled
7. **Resource Management**: Automatic cleanup after timeout

## Session Extension Example

```
08:00 - User presses SPACE → Camera ON, Timer: 02:00
08:01 - Employee A scans → Timer: 02:00 (extended)
08:02 - Employee B scans → Timer: 02:00 (extended)
08:03 - Employee C scans → Timer: 02:00 (extended)
08:04 - No activity...
08:05 - No activity...
08:06 - TIMEOUT → Camera OFF
```

Without the extension model:
```
08:00 - User presses SPACE → Camera ON, Timer: 02:00
08:01 - Employee A scans → Timer: 01:00 (counting down)
08:02 - TIMEOUT → Camera OFF (Employee B and C need to reactivate)
```

The extension model is much better for multi-employee scenarios!
