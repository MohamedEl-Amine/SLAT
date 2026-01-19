#!/usr/bin/env python3
"""
Secure Local Attendance Terminal (SLAT)
Main entry point for the application.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from gui.public_interface import PublicInterface

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SLAT")
    app.setApplicationVersion("1.0")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Start with public interface
    window = PublicInterface()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()