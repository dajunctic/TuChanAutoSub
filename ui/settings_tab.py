"""
Settings Tab - Application settings and preferences
"""

import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QCheckBox, QComboBox, QSpinBox,
    QFormLayout, QFrame, QScrollArea, QPlainTextEdit
)
from PyQt6.QtCore import Qt


class SettingsTab(QWidget):
    """Tab for application settings"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings_file = os.path.join("projects", "settings.json")
        self.settings = {}
        
        # Main layout for the widget
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create scroll area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container widget for scroll area
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(20, 20, 20, 20)
        self.container_layout.setSpacing(20)
        
        self.init_ui()
        
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)
        self.load_settings()
        
    def init_ui(self):
        """Initialize UI components inside container layout"""
        layout = self.container_layout
        
        # Title
        title = QLabel("⚙️ Application Settings")
        title.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Helper to create a card-like group box
        def create_group(title):
            group = QGroupBox(title)
            layout = QFormLayout()
            layout.setSpacing(15)
            layout.setContentsMargins(15, 25, 15, 15)
            layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            group.setLayout(layout)
            return group, layout


        # Paths Group
        paths_group, paths_form = create_group("Default Locations")
        
        self.downloads_path = QLineEdit()
        btn_downloads = QPushButton("Browse")
        btn_downloads.setProperty("class", "secondary")
        btn_downloads.clicked.connect(self.browse_downloads)
        
        dl_row = QHBoxLayout()
        dl_row.addWidget(self.downloads_path)
        dl_row.addWidget(btn_downloads)
        paths_form.addRow("Downloads Folder:", dl_row)
        
        self.projects_path = QLineEdit()
        btn_projects = QPushButton("Browse")
        btn_projects.setProperty("class", "secondary")
        btn_projects.clicked.connect(self.browse_projects)
        
        pj_row = QHBoxLayout()
        pj_row.addWidget(self.projects_path)
        pj_row.addWidget(btn_projects)
        paths_form.addRow("Projects Folder:", pj_row)
        
        layout.addWidget(paths_group)

        # Engine Defaults
        engine_group, engine_form = create_group("Engine Preferences")
        
        self.default_trans_engine = QComboBox()
        self.default_trans_engine.addItems(["gemini", "google", "lmstudio"])
        engine_form.addRow("Preferred Translation API:", self.default_trans_engine)
        
        # Gemini Keys
        self.gemini_keys = QPlainTextEdit()
        self.gemini_keys.setPlaceholderText("Enter Gemini API Keys here (one per line)")
        self.gemini_keys.setMinimumHeight(120)
        engine_form.addRow("Gemini API Keys:", self.gemini_keys)
        
        layout.addWidget(engine_group)

        # Behavior Group
        behavior_group = QGroupBox("System Behavior")
        behavior_layout = QVBoxLayout()
        behavior_layout.setContentsMargins(15, 25, 15, 15)
        self.auto_save_checkbox = QCheckBox("Automatically save project progress on every change")
        self.auto_save_checkbox.setChecked(True)
        self.auto_load_checkbox = QCheckBox("Open the most recent project automatically at startup")
        self.auto_load_checkbox.setChecked(True)
        behavior_layout.addWidget(self.auto_save_checkbox)
        behavior_layout.addWidget(self.auto_load_checkbox)
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("💾 Save All Settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setMinimumWidth(200)
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.setProperty("class", "secondary")
        self.reset_btn.clicked.connect(self.reset_settings)
        self.reset_btn.setMinimumHeight(45)
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # Info section
        info_label = QLabel("""
        <p style='color: #80848E; font-size: 11px;'>
        <b>About AutoViSub Pro 2.0</b><br>
        PyQt6 Desktop Application<br>
        Video Subtitle Extraction & Translation Tool<br><br>
        Features:<br>
        • Download videos from Bilibili<br>
        • Extract hard-coded subtitles with OCR<br>
        • Translate to Vietnamese<br>
        • Render videos with burned-in subtitles<br>
        </p>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
            
    def browse_downloads(self):
        """Browse for downloads folder"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Downloads Folder",
            self.downloads_path.text()
        )
        if directory:
            self.downloads_path.setText(directory)
            
    def browse_projects(self):
        """Browse for projects folder"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Projects Folder",
            self.projects_path.text()
        )
        if directory:
            self.projects_path.setText(directory)
            
    def save_settings(self):
        """Save settings to file"""
        self.settings = {
            'downloads_path': self.downloads_path.text(),
            'projects_path': self.projects_path.text(),
            'default_trans_engine': self.default_trans_engine.currentText(),
            'gemini_keys': self.gemini_keys.toPlainText(),
            'auto_save': self.auto_save_checkbox.isChecked(),
            'auto_load': self.auto_load_checkbox.isChecked()
        }
        
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
            
    def load_settings(self):
        """Load settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                    
                # Apply settings to UI
                if 'downloads_path' in self.settings:
                    self.downloads_path.setText(self.settings['downloads_path'])
                if 'projects_path' in self.settings:
                    self.projects_path.setText(self.settings['projects_path'])
                if 'default_trans_engine' in self.settings:
                    index = self.default_trans_engine.findText(self.settings['default_trans_engine'])
                    if index >= 0:
                        self.default_trans_engine.setCurrentIndex(index)
                if 'gemini_keys' in self.settings:
                    self.gemini_keys.setPlainText(self.settings['gemini_keys'])
                if 'auto_save' in self.settings:
                    self.auto_save_checkbox.setChecked(self.settings['auto_save'])
                if 'auto_load' in self.settings:
                    self.auto_load_checkbox.setChecked(self.settings['auto_load'])
                    
            except Exception as e:
                print(f"Error loading settings: {e}")
                
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.downloads_path.setText(os.path.abspath("downloads"))
            self.projects_path.setText(os.path.abspath("projects"))
            self.default_trans_engine.setCurrentIndex(0)
            self.gemini_keys.setPlainText("")
            self.auto_save_checkbox.setChecked(True)
            self.auto_load_checkbox.setChecked(True)
            
            QMessageBox.information(self, "Success", "Settings reset to defaults")
            
    def on_project_loaded(self, video_path, project_data):
        """Called when a project is loaded"""
        pass  # No project-specific settings
        
    def get_state(self):
        """Get current state for saving"""
        return {}  # Settings are saved separately
