#!/usr/bin/env python3
"""
Secure Local Attendance Terminal (SLAT)
Main entry point for the application.
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.public_interface import PublicInterface

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SLAT")
    app.setApplicationVersion("1.0")

    # Start with public interface
    window = PublicInterface()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()