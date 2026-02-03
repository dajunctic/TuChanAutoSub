"""
Launcher script for AutoViSub Pro PyQt6
Handles lazy imports to avoid DLL issues
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Import Qt first before any heavy libraries
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    
    # Create app early
    app = QApplication(sys.argv)
    app.setApplicationName("AutoViSub Pro")
    app.setOrganizationName("AutoViSub")
    app.setApplicationVersion("2.0.0")
    
    # Now import the rest
    from main_qt import setup_app_style, MainWindow
    
    # Setup styling
    setup_app_style(app)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
