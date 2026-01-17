# Secure Local Attendance Terminal (SLAT)

A secure, offline attendance tracking system built with PyQt5 and SQLite.

## Features

- Multiple identification methods (ID card, QR code, face recognition)
- Time-window enforcement for attendance
- Admin control panel
- Immutable attendance logs
- Local storage only

## Installation

1. Install Python 3.8+
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```
python src/main.py
```

## Project Structure

- `src/` - Main source code
  - `main.py` - Application entry point
  - `database.py` - SQLite database operations
  - `models.py` - Data models
  - `gui/` - PyQt5 user interfaces
  - `utils/` - Utility functions
- `data/` - Database and encrypted data storage
- `requirements.txt` - Python dependencies

## Security

- All data stored locally
- Face data encrypted
- Attendance logs append-only with integrity hashes
- No network connectivity required