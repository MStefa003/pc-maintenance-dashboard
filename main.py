"""
PC Maintenance Dashboard - Main Entry Point
A simple, cross-platform desktop application for system maintenance.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window_simple import MainWindow

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
