"""
Translate Tab - Subtitle translation with multiple engines
"""

import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QGroupBox,
    QComboBox, QLineEdit, QSpinBox, QListWidget,
    QMessageBox, QFileDialog, QPlainTextEdit, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
# Lazy import to avoid PyTorch DLL issues
# from sub_processor import SubtitleProcessor


class TranslateWorker(QThread):
    """Worker thread for translation"""
    progress = pyqtSignal(float)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    log = pyqtSignal(str)
    
    def __init__(self, subtitles, engine, lm_studio_url, custom_prompt, gemini_keys, gemini_batch_size):
        super().__init__()
        self.subtitles = subtitles
        self.engine = engine
        self.lm_studio_url = lm_studio_url
        self.custom_prompt = custom_prompt
        self.gemini_keys = gemini_keys
        self.gemini_batch_size = gemini_batch_size
        
    def run(self):
        """Run translation"""
        try:
            self.log.emit(f"Starting translation with {self.engine} engine...")
            
            from sub_processor import SubtitleProcessor
            processor = SubtitleProcessor()
            
            def progress_callback(percent):
                self.progress.emit(percent)
                
            translated = processor.translate_subtitles(
                self.subtitles,
                progress_callback=progress_callback,
                engine=self.engine,
                lm_studio_url=self.lm_studio_url if self.engine == 'lmstudio' else None,
                custom_prompt=self.custom_prompt if self.custom_prompt else None,
                gemini_keys=self.gemini_keys if self.engine == 'gemini' else None,
                gemini_batch_size=self.gemini_batch_size
            )
            
            self.log.emit(f"Translation completed! Translated {len(translated)} subtitles")
            self.finished.emit(translated)
            
        except Exception as e:
            self.error.emit(f"Translation error: {str(e)}")


class TranslateTab(QWidget):
    """Tab for subtitle translation"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.chinese_subtitles = []
        self.vietnamese_subtitles = []
        self.translate_worker = None
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(20, 20, 20, 20)
        self.container_layout.setSpacing(15)
        
        self.init_ui()
        
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)
        
    def init_ui(self):
        """Initialize UI components inside container layout"""
        layout = self.container_layout
        
        # Title
        title = QLabel("🌐 Translate Subtitles")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Input section
        input_group = QGroupBox("Input Subtitles")
        input_layout = QVBoxLayout()
        
        input_buttons = QHBoxLayout()
        
        load_btn = QPushButton("📂 Load SRT File")
        load_btn.setProperty("class", "secondary")
        load_btn.clicked.connect(self.load_srt)
        input_buttons.addWidget(load_btn)
        
        load_project_btn = QPushButton("📁 Load from Project")
        load_project_btn.setProperty("class", "secondary")
        load_project_btn.clicked.connect(self.load_from_project)
        input_buttons.addWidget(load_project_btn)
        
        input_buttons.addStretch()
        
        self.input_count_label = QLabel("0 subtitles loaded")
        self.input_count_label.setStyleSheet("color: #80848E;")
        input_buttons.addWidget(self.input_count_label)
        
        input_layout.addLayout(input_buttons)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Translation settings
        settings_group = QGroupBox("Translation Settings")
        settings_layout = QVBoxLayout()
        
        # Engine selection
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("Translation Engine:"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["google", "gemini", "lmstudio"])
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        engine_layout.addWidget(self.engine_combo)
        engine_layout.addStretch()
        settings_layout.addLayout(engine_layout)
        
        # LM Studio settings
        self.lmstudio_group = QGroupBox("LM Studio Settings")
        lmstudio_layout = QVBoxLayout()
        
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("API URL:"))
        self.lmstudio_url = QLineEdit()
        self.lmstudio_url.setText("http://localhost:1234/v1/chat/completions")
        url_layout.addWidget(self.lmstudio_url)
        lmstudio_layout.addLayout(url_layout)
        
        self.lmstudio_group.setLayout(lmstudio_layout)
        self.lmstudio_group.setVisible(False)
        # settings_layout.addWidget(self.lmstudio_group)
        
        # Gemini settings
        self.gemini_group = QGroupBox("Gemini API Settings")
        gemini_layout = QVBoxLayout()
        
        keys_layout = QVBoxLayout()
        keys_layout.addWidget(QLabel("API Keys (one per line):"))
        self.gemini_keys_text = QPlainTextEdit()
        self.gemini_keys_text.setMaximumHeight(80)
        self.gemini_keys_text.setPlaceholderText("Enter your Gemini API keys, one per line")
        keys_layout.addWidget(self.gemini_keys_text)
        gemini_layout.addLayout(keys_layout)
        
        batch_layout = QHBoxLayout()
        batch_layout.addWidget(QLabel("Batch Size:"))
        self.gemini_batch_spin = QSpinBox()
        self.gemini_batch_spin.setMinimum(10)
        self.gemini_batch_spin.setMaximum(200)
        self.gemini_batch_spin.setValue(80)
        batch_layout.addWidget(self.gemini_batch_spin)
        batch_layout.addStretch()
        gemini_layout.addLayout(batch_layout)
        
        self.gemini_group.setLayout(gemini_layout)
        self.gemini_group.setVisible(False)
        # Hide these as per request to move keys to settings
        # settings_layout.addWidget(self.gemini_group) 
        
        # Custom prompt
        prompt_layout = QVBoxLayout()
        prompt_layout.addWidget(QLabel("Custom Prompt (optional):"))
        self.custom_prompt = QPlainTextEdit()
        self.custom_prompt.setMaximumHeight(80)
        self.custom_prompt.setPlaceholderText("Leave empty for default prompt")
        prompt_layout.addWidget(self.custom_prompt)
        settings_layout.addLayout(prompt_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Connect signals for auto-save
        self.engine_combo.currentIndexChanged.connect(self.auto_save)
        self.lmstudio_url.textChanged.connect(self.auto_save)
        self.gemini_keys_text.textChanged.connect(self.auto_save)
        self.gemini_batch_spin.valueChanged.connect(self.auto_save)
        self.custom_prompt.textChanged.connect(self.auto_save)
        
        # Progress
        progress_group = QGroupBox("Translation Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #80848E; font-size: 11px;")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Output section
        output_group = QGroupBox("Translated Subtitles")
        output_layout = QVBoxLayout()
        
        output_buttons = QHBoxLayout()
        
        export_btn = QPushButton("💾 Export SRT")
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(self.export_srt)
        output_buttons.addWidget(export_btn)
        
        output_buttons.addStretch()
        
        self.output_count_label = QLabel("0 subtitles translated")
        self.output_count_label.setStyleSheet("color: #80848E;")
        output_buttons.addWidget(self.output_count_label)
        
        output_layout.addLayout(output_buttons)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.translate_btn = QPushButton("▶️ Start Translation")
        self.translate_btn.clicked.connect(self.start_translation)
        self.translate_btn.setMinimumWidth(150)
        self.translate_btn.setMinimumHeight(40)
        button_layout.addWidget(self.translate_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.clicked.connect(self.stop_translation)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumWidth(150)
        self.stop_btn.setMinimumHeight(40)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
    def on_engine_changed(self, engine):
        """Handle engine selection change"""
        # Kept for compatibility but visibility handled by request
        pass
        
    def load_srt(self):
        """Load SRT file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load SRT File",
            "",
            "SRT Files (*.srt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                    
                processor = SubtitleProcessor()
                self.chinese_subtitles = processor.parse_srt(srt_content)
                
                self.input_count_label.setText(f"{len(self.chinese_subtitles)} subtitles loaded")
                self.status_label.setText(f"Loaded {len(self.chinese_subtitles)} subtitles from {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load SRT: {e}")
                
    def load_from_project(self):
        """Load subtitles from current project"""
        if not self.main_window.current_project:
            QMessageBox.information(self, "Info", "No project loaded")
            return
            
        project_folder = self.main_window.get_project_folder(self.main_window.current_project)
        srt_path = os.path.join(project_folder, "chinese_subtitles.srt")
        
        if not os.path.exists(srt_path):
            QMessageBox.warning(self, "Warning", "No Chinese subtitles found in project. Please extract subtitles first.")
            return
            
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
                
            processor = SubtitleProcessor()
            self.chinese_subtitles = processor.parse_srt(srt_content)
            
            self.input_count_label.setText(f"{len(self.chinese_subtitles)} subtitles loaded")
            self.status_label.setText(f"Loaded {len(self.chinese_subtitles)} subtitles from project")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load subtitles: {e}")
            
    def start_translation(self):
        """Start translation"""
        if not self.chinese_subtitles:
            QMessageBox.warning(self, "Warning", "Please load subtitles first")
            return
            
        engine = self.engine_combo.currentText()
        
        # Validate settings
        if engine == "gemini":
            # Pull from settings tab first
            keys_text = self.main_window.settings_tab.gemini_keys.toPlainText().strip()
            # Fallback to project-specific if global is empty (though group is hidden)
            if not keys_text:
                keys_text = self.gemini_keys_text.toPlainText().strip()
                
            if not keys_text:
                QMessageBox.warning(self, "Warning", "Please enter Gemini API keys in Settings tab")
                return
            gemini_keys = [k.strip() for k in keys_text.split('\n') if k.strip()]
        else:
            gemini_keys = None
            
        # Disable UI
        self.translate_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.vietnamese_subtitles = []
        
        # Start translation worker
        self.translate_worker = TranslateWorker(
            self.chinese_subtitles,
            engine,
            self.lmstudio_url.text() if engine == "lmstudio" else None,
            self.custom_prompt.toPlainText().strip() or None,
            gemini_keys,
            self.gemini_batch_spin.value()
        )
        
        self.translate_worker.progress.connect(self.on_progress)
        self.translate_worker.finished.connect(self.on_translation_finished)
        self.translate_worker.error.connect(self.on_error)
        self.translate_worker.log.connect(self.on_log)
        self.translate_worker.start()
        
    def stop_translation(self):
        """Stop translation"""
        if self.translate_worker and self.translate_worker.isRunning():
            self.translate_worker.terminate()
            self.translate_worker.wait()
            self.status_label.setText("Translation stopped by user")
            self.reset_ui()
            
    def on_progress(self, percent):
        """Update progress"""
        self.progress_bar.setValue(int(percent))
        
    def on_translation_finished(self, subtitles):
        """Handle translation completion"""
        self.vietnamese_subtitles = subtitles
        self.output_count_label.setText(f"{len(subtitles)} subtitles translated")
        self.status_label.setText(f"✅ Translation complete! Translated {len(subtitles)} subtitles")
        self.progress_bar.setValue(100)
        self.reset_ui()
        
        # Auto-save to project
        if self.main_window.current_project:
            project_folder = self.main_window.get_project_folder(self.main_window.current_project)
            srt_path = os.path.join(project_folder, "vietnamese_subtitles.srt")
            
            processor = SubtitleProcessor()
            processor.save_to_srt(subtitles, srt_path)
            
            self.status_label.setText(f"✅ Saved to {srt_path}")
            
    def on_error(self, error_msg):
        """Handle error"""
        self.status_label.setText(f"❌ Error: {error_msg}")
        QMessageBox.critical(self, "Translation Error", error_msg)
        self.reset_ui()
        
    def on_log(self, message):
        """Handle log message"""
        self.status_label.setText(message)
        
    def reset_ui(self):
        """Reset UI to initial state"""
        self.translate_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def export_srt(self):
        """Export translated subtitles"""
        if not self.vietnamese_subtitles:
            QMessageBox.information(self, "Info", "No translated subtitles to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Translated SRT",
            "vietnamese_subtitles.srt",
            "SRT Files (*.srt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                processor = SubtitleProcessor()
                processor.save_to_srt(self.vietnamese_subtitles, file_path)
                QMessageBox.information(self, "Success", f"Translated subtitles exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
                
    def on_project_loaded(self, video_path, project_data):
        """Called when a project is loaded"""
        # Load saved translation data
        if 'translate' in project_data:
            trans_data = project_data['translate']
            
            if 'engine' in trans_data:
                index = self.engine_combo.findText(trans_data['engine'])
                if index >= 0:
                    self.engine_combo.setCurrentIndex(index)
                    
            if 'lmstudio_url' in trans_data:
                self.lmstudio_url.setText(trans_data['lmstudio_url'])
                
            if 'gemini_keys' in trans_data and trans_data['gemini_keys']:
                self.gemini_keys_text.setPlainText('\n'.join(trans_data['gemini_keys']))
                
            if 'custom_prompt' in trans_data:
                self.custom_prompt.setPlainText(trans_data['custom_prompt'])
                
        # Try to auto-load Chinese subtitles
        project_folder = self.main_window.get_project_folder(video_path)
        srt_path = os.path.join(project_folder, "chinese_subtitles.srt")
        
        if os.path.exists(srt_path):
            try:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                    
                processor = SubtitleProcessor()
                self.chinese_subtitles = processor.parse_srt(srt_content)
                self.input_count_label.setText(f"{len(self.chinese_subtitles)} subtitles loaded")
            except:
                pass
                
    def get_state(self):
        """Get current state for saving"""
        gemini_keys_text = self.gemini_keys_text.toPlainText().strip()
        gemini_keys = [k.strip() for k in gemini_keys_text.split('\n') if k.strip()] if gemini_keys_text else []
        
        return {
            'engine': self.engine_combo.currentText(),
            'lmstudio_url': self.lmstudio_url.text(),
            'gemini_keys': gemini_keys,
            'custom_prompt': self.custom_prompt.toPlainText(),
            'gemini_batch_size': self.gemini_batch_spin.value()
        }

    def auto_save(self):
        """Auto-save project state"""
        if self.main_window:
            self.main_window.save_project(silent=True)
