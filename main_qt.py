"""
AutoViSub Pro - PyQt6 Version
Modern desktop application for video subtitle extraction and translation
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor
from ui.main_window import MainWindow

def setup_app_style(app):
    """Setup a stable, modern, professional dark theme"""
    
    # Professional Dark Color Palette
    BG_MAIN = "#1A1B1E"      # Darker background
    BG_SURFACE = "#25262B"   # Surface for cards
    BG_INPUT = "#141517"     # Darkest for inputs
    ACCENT = "#5865F2"       # Modern Blurple
    ACCENT_HOVER = "#4752C4"
    BORDER = "#373A40"       # Neutral border
    TEXT_PRIMARY = "#E9ECEF" # Near white
    TEXT_SEC = "#909296"     # Grey text
    
    app.setStyleSheet(f"""
        QMainWindow, QWidget {{
            background-color: {BG_MAIN};
            color: {TEXT_PRIMARY};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }}
        
        /* Tabs Styling */
        QTabWidget::pane {{
            border: 1px solid {BORDER};
            border-radius: 8px;
            background-color: {BG_MAIN};
            top: -1px;
        }}
        
        QTabBar::tab {{
            background-color: {BG_SURFACE};
            color: {TEXT_SEC};
            padding: 10px 20px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {ACCENT};
            color: white;
            font-weight: bold;
        }}
        
        /* GroupBox - Fixed the overlap issue */
        QGroupBox {{
            background-color: {BG_SURFACE};
            border: 1px solid {BORDER};
            border-radius: 8px;
            margin-top: 15px; /* Margin to prevent overlap from above */
            padding-top: 30px; /* Internal padding to clear the title */
        }}
        
        QGroupBox::title {{
            /* Standard position is more stable */
            subcontrol-origin: padding;
            subcontrol-position: top left;
            left: 15px;
            top: 10px;
            color: {ACCENT};
            font-weight: bold;
            font-size: 14px;
        }}
        
        /* Input Fields - Clean look */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background-color: {BG_INPUT};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 8px;
            color: {TEXT_PRIMARY};
            min-height: 28px;
        }}
        
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {ACCENT};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {ACCENT};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 10px 18px;
            font-weight: bold;
            min-width: 90px;
        }}
        
        QPushButton:hover {{
            background-color: {ACCENT_HOVER};
        }}
        
        QPushButton:pressed {{
            background-color: #3C45A5;
        }}
        
        /* Secondary Button Style */
        QPushButton[class="secondary"] {{
            background-color: #373A40;
            color: {TEXT_PRIMARY};
        }}
        
        QPushButton[class="secondary"]:hover {{
            background-color: #4A4D54;
        }}
        
        /* Danger Button Style */
        QPushButton[class="danger"] {{
            background-color: #C92A2A;
        }}
        
        QPushButton[class="danger"]:hover {{
            background-color: #A61E1E;
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background-color: {BG_INPUT};
            border: 1px solid {BORDER};
            border-radius: 6px;
            text-align: center;
            height: 20px;
            color: white;
            font-weight: bold;
        }}
        
        QProgressBar::chunk {{
            background-color: {ACCENT};
            border-radius: 5px;
        }}
        
        /* List Handling */
        QListWidget {{
            background-color: {BG_INPUT};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 5px;
        }}
        
        QListWidget::item:selected {{
            background-color: {ACCENT};
            color: white;
        }}
    """)

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("AutoViSub Pro")
    app.setOrganizationName("AutoViSub")
    app.setApplicationVersion("2.0.0")
    
    # Setup styling
    setup_app_style(app)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
