"""
Main Window for AutoViSub Pro
Modern tabbed interface for video subtitle extraction and translation
"""

import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QFileDialog,
    QMessageBox, QStatusBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

from ui.download_tab import DownloadTab
from ui.ocr_tab import OCRTab
from ui.translate_tab import TranslateTab
from ui.render_tab import RenderTab
from ui.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    """Main application window with tabbed interface"""
    
    def __init__(self):
        super().__init__()
        self.projects_dir = os.path.abspath("projects")
        os.makedirs(self.projects_dir, exist_ok=True)
        
        self.current_project = None
        self.project_data = {}
        
        self.init_ui()
        self.load_last_project()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("AutoViSub Pro - Video Subtitle Extraction & Translation")
        self.setMinimumSize(1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # Create tabs
        self.download_tab = DownloadTab(self)
        self.ocr_tab = OCRTab(self)
        self.translate_tab = TranslateTab(self)
        self.render_tab = RenderTab(self)
        self.settings_tab = SettingsTab(self)
        
        # Add tabs
        self.tab_widget.addTab(self.download_tab, "📥 Download Video")
        self.tab_widget.addTab(self.ocr_tab, "🔍 Extract Subtitles")
        self.tab_widget.addTab(self.translate_tab, "🌐 Translate")
        self.tab_widget.addTab(self.render_tab, "🎬 Render Video")
        self.tab_widget.addTab(self.settings_tab, "⚙️ Settings")
        
        main_layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_project_action = QAction("&New Project", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)
        
        open_project_action = QAction("&Open Project", self)
        open_project_action.setShortcut("Ctrl+O")
        open_project_action.triggered.connect(self.open_project)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        save_project_action = QAction("&Save Project", self)
        save_project_action.setShortcut("Ctrl+S")
        save_project_action.triggered.connect(self.save_project)
        file_menu.addAction(save_project_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_header(self):
        """Create application header"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title_label = QLabel("🎬 AutoViSub Pro")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #5865F2;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Project info
        self.project_label = QLabel("No project loaded")
        self.project_label.setStyleSheet("""
            font-size: 12px;
            color: #80848E;
            padding: 6px 12px;
            background-color: #1E1F22;
            border-radius: 6px;
        """)
        header_layout.addWidget(self.project_label)
        
        # New project button
        new_btn = QPushButton("📁 New Project")
        new_btn.setProperty("class", "secondary")
        new_btn.clicked.connect(self.new_project)
        header_layout.addWidget(new_btn)
        
        # Open project button
        open_btn = QPushButton("📂 Open Project")
        open_btn.setProperty("class", "secondary")
        open_btn.clicked.connect(self.open_project)
        header_layout.addWidget(open_btn)
        
        return header_widget
        
    def new_project(self):
        """Create a new project by selecting a video file"""
        video_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.flv *.wmv);;All Files (*.*)"
        )
        
        if video_path:
            self.load_project(video_path)
            
    def open_project(self):
        """Open an existing project"""
        video_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project Video",
            self.projects_dir,
            "Video Files (*.mp4 *.avi *.mkv *.mov *.flv *.wmv);;All Files (*.*)"
        )
        
        if video_path:
            self.load_project(video_path)
            
    def load_project(self, video_path):
        """Load a project from video path"""
        if not os.path.exists(video_path):
            QMessageBox.warning(self, "Error", f"Video file not found: {video_path}")
            return
            
        self.current_project = video_path
        
        # Get project folder
        project_folder = self.get_project_folder(video_path)
        state_file = os.path.join(project_folder, "project_state.json")
        
        # Load project state if exists
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    self.project_data = json.load(f)
            except Exception as e:
                print(f"Error loading project state: {e}")
                self.project_data = {}
        else:
            self.project_data = {}
            
        # Update UI
        video_name = os.path.basename(video_path)
        self.project_label.setText(f"Project: {video_name}")
        self.status_bar.showMessage(f"Loaded project: {video_name}")
        
        # Save as last project
        last_project_file = os.path.join(self.projects_dir, "last_project.txt")
        with open(last_project_file, 'w', encoding='utf-8') as f:
            f.write(video_path)
            
        # Notify tabs
        self.download_tab.on_project_loaded(video_path, self.project_data)
        self.ocr_tab.on_project_loaded(video_path, self.project_data)
        self.translate_tab.on_project_loaded(video_path, self.project_data)
        self.render_tab.on_project_loaded(video_path, self.project_data)
        
    def save_project(self):
        """Save current project state"""
        if not self.current_project:
            QMessageBox.information(self, "Info", "No project loaded")
            return
            
        project_folder = self.get_project_folder(self.current_project)
        state_file = os.path.join(project_folder, "project_state.json")
        
        # Collect data from tabs
        self.project_data['video_path'] = self.current_project
        self.project_data['download'] = self.download_tab.get_state()
        self.project_data['ocr'] = self.ocr_tab.get_state()
        self.project_data['translate'] = self.translate_tab.get_state()
        self.project_data['render'] = self.render_tab.get_state()
        
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=2, ensure_ascii=False)
            self.status_bar.showMessage("Project saved successfully", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project: {e}")
            
    def load_last_project(self):
        """Load the last opened project"""
        last_project_file = os.path.join(self.projects_dir, "last_project.txt")
        if os.path.exists(last_project_file):
            try:
                with open(last_project_file, 'r', encoding='utf-8') as f:
                    last_path = f.read().strip()
                if last_path and os.path.exists(last_path):
                    self.load_project(last_path)
            except Exception as e:
                print(f"Error loading last project: {e}")
                
    def get_project_folder(self, video_path):
        """Get project folder for a video file"""
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        project_folder = os.path.join(self.projects_dir, video_name)
        os.makedirs(project_folder, exist_ok=True)
        return project_folder
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About AutoViSub Pro",
            """<h2>AutoViSub Pro 2.0</h2>
            <p><b>Video Subtitle Extraction & Translation Tool</b></p>
            <p>Powered by:</p>
            <ul>
                <li>PyQt6 - Modern UI Framework</li>
                <li>EasyOCR / RapidOCR - Subtitle Extraction</li>
                <li>Google Translate / Gemini - Translation</li>
                <li>FFmpeg - Video Processing</li>
            </ul>
            <p>© 2024 AutoViSub Team</p>
            """
        )
        
    def closeEvent(self, event):
        """Handle window close event"""
        # Auto-save project before closing
        if self.current_project:
            self.save_project()
        event.accept()
