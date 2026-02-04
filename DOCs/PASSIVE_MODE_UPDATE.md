# SLAT Passive Mode Update

## Overview
The SLAT public interface has been completely redesigned to work as a **passive attendance terminal**. Instead of requiring users to select methods and press buttons, the terminal now operates automatically based on the mode configured by the administrator.

## Key Changes

### 1. **New Passive Operation Model**
- **No method selection screen** - Terminal starts directly in the configured mode
- **No button pressing required** - Users simply walk up and present their credential
- **Always-on camera** - For QR and Face modes, camera feed is embedded and always active
- **Automatic detection** - System continuously scans for QR codes or faces
- **3-second cooldown** - Prevents duplicate scans when someone lingers

### 2. **Three Operating Modes**

#### Mode 1: QR Code Scanning (Default)
- Camera displays live feed
- Automatically detects and reads QR codes
- User walks up, shows QR code, attendance recorded
- Visual feedback: "QR DETECTE" overlay on camera feed

#### Mode 2: Face Recognition
- Camera displays live feed with face detection
- Automatically recognizes registered faces
- Confidence percentage displayed on success
- Visual feedback: Green box around detected face

#### Mode 3: ID Card Entry
- Simple text input field always visible
- User types ID and presses Enter
- Minimal interface for manual entry

### 3. **Administrator Controls**

#### New Setting: Attendance Mode
Location: **Admin Interface → Settings Tab → Mode du terminal de présence**

Options:
- 🔲 **Scan QR Code** - For contactless QR badge scanning
- 👤 **Reconnaissance Faciale** - For hands-free face recognition
- 🔢 **Saisie Carte ID** - For manual ID card entry

The administrator sets the mode based on the current time window:
- Morning arrival window → Set to desired mode
- Afternoon departure window → Change if needed
- Terminal automatically applies the selected mode

### 4. **User Experience Flow**

**Old Flow (Interactive):**
1. User arrives at terminal
2. Sees three method buttons
3. Clicks desired method
4. Camera/input opens in popup
5. Confirms action
6. Receives feedback

**New Flow (Passive):**
1. User walks up to terminal
2. Terminal is already in scanning mode
3. User simply presents credential (face/QR/ID)
4. Attendance automatically recorded
5. Brief success message with photo
6. Screen clears after 3 seconds

### 5. **Technical Implementation**

#### Files Modified:
- `src/database.py` - Added `attendance_mode` setting (qr/face/card)
- `src/gui/public_interface.py` - Complete rewrite for passive operation
- `src/gui/admin_interface.py` - Added mode selector in settings
- `src/utils/qr_scanner.py` - Added `scan_frame()` for single-frame scanning

#### Key Features:
- **Embedded camera feed** - 640x480 display within main window
- **Real-time processing** - 30 FPS camera updates
- **Scan cooldown** - 3-second delay between successful scans
- **Visual feedback** - Employee photo and name displayed on success
- **Duplicate prevention** - Same window/day/action checking still active
- **Auto-clear status** - Success/error messages clear after 3 seconds

### 6. **Benefits**

For Administrators:
- Set-and-forget operation
- Switch modes based on time window
- No user training required
- Reduced interaction = fewer errors

For Employees:
- Faster check-in/out (no button clicking)
- More intuitive (just show credential)
- Contactless operation
- Immediate visual feedback

For System:
- Reduced complexity
- Better camera utilization
- Cleaner UI
- Less code maintenance

### 7. **Configuration Workflow**

**Morning Setup (08:30-09:00 Arrival):**
1. Admin accesses settings (F11 x5)
2. Sets mode to "Face Recognition" or "QR Code"
3. Saves settings
4. Exits admin interface
5. Terminal starts in selected mode
6. Employees walk up and scan automatically

**Afternoon Setup (16:00-16:30 Departure):**
1. Admin can change mode if desired
2. Same terminal, different mode
3. Or keep same mode for consistency

### 8. **Backup Files**
- `public_interface_old.py` - Original interactive version
- `public_interface_backup.py` - Previous version before passive mode
- `public_interface_new.py` - New passive implementation (copied to main)

### 9. **Migration Notes**

**No Breaking Changes:**
- Database schema unchanged
- All employee data preserved
- Face/QR enrollment process unchanged
- Admin interface fully compatible
- Same duplicate prevention logic

**What Changed:**
- Public terminal UI/UX completely redesigned
- No more method selection buttons
- Camera always embedded (not popup)
- Mode controlled by admin settings

### 10. **Testing Checklist**

- [x] QR mode starts automatically
- [x] Face mode starts automatically
- [x] Card mode displays input field
- [x] Camera feed displays correctly
- [x] QR codes detected and processed
- [x] Faces recognized with confidence
- [x] Duplicate prevention still works
- [x] Status messages display and clear
- [x] Admin can change mode
- [x] 3-second cooldown prevents duplicates

## Usage Instructions

### For Administrators:
1. Press F11 five times quickly to access admin interface
2. Navigate to "Paramètres" (Settings) tab
3. Select desired mode from "Mode du terminal de présence" dropdown
4. Save settings
5. Exit back to public terminal
6. Terminal automatically restarts in new mode

### For Employees:
1. Walk up to terminal
2. **QR Mode**: Hold QR code in front of camera
3. **Face Mode**: Look at camera
4. **Card Mode**: Type ID and press Enter
5. Wait for confirmation message
6. Done!

## Future Enhancements

Potential additions:
- Voice feedback ("Bonjour, Jean!")
- Sound notifications (beep on success)
- Multi-language support
- Attendance statistics on screen
- Company announcements display
- Weather/time display
- Employee of the month photo

## Support

If you encounter issues:
1. Check camera is connected (QR/Face modes)
2. Verify mode is set correctly in admin settings
3. Check employees have QR codes/faces enrolled
4. Review logs in admin interface
5. Restart terminal if camera freezes

---

**Developed by Innovista Dev**
*Version 2.0 - Passive Mode*
*Date: January 2026*
