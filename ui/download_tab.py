"""
Download Tab - Video download from Bilibili and other sources
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QProgressBar, QTextEdit,
    QGroupBox, QFileDialog, QMessageBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from downloader import download_bilibili_video


class DownloadWorker(QThread):
    """Worker thread for downloading videos"""
    progress = pyqtSignal(float)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    log = pyqtSignal(str)
    
    def __init__(self, url, output_path):
        super().__init__()
        self.url = url
        self.output_path = output_path
        
    def run(self):
        """Run download in background thread"""
        try:
            self.log.emit(f"Starting download from: {self.url}")
            
            def progress_callback(percent):
                self.progress.emit(percent)
                
            result = download_bilibili_video(
                self.url, 
                self.output_path, 
                progress_callback=progress_callback
            )
            
            if result:
                self.log.emit(f"Download completed: {result}")
                self.finished.emit(result)
            else:
                self.error.emit("Download failed - no file returned")
        except Exception as e:
            self.error.emit(f"Download error: {str(e)}")


class AutoWorkflowWorker(QThread):
    """Worker thread for full automation: Download -> OCR -> Translate -> Render"""
    progress = pyqtSignal(float)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, url, output_dir, settings):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.settings = settings
        
    def run(self):
        try:
            video_path = None
            
            # 1. Download (if URL provided)
            if self.url and self.url.startswith("http"):
                self.status.emit("📥 Step 1/4: Downloading video...")
                
                def dl_progress(p): self.progress.emit(p * 0.2) # First 20%
                
                video_path = download_bilibili_video(self.url, self.output_dir, progress_callback=dl_progress)
                if not video_path:
                    self.error.emit("Download failed")
                    return
            else:
                # Assume self.url is already a file path
                video_path = self.url
                self.progress.emit(20)

            # 2. OCR (Auto Detect + Extract)
            self.status.emit("🔍 Step 2/4: Detecting region & Extracting subtitles...")
            from auto_detect_region import auto_detect_subtitle_region
            
            def ocr_progress(p): self.progress.emit(20 + p * 40) # 20% to 60%
            
            region = auto_detect_subtitle_region(video_path, progress_callback=None) # Skip inner progress for speed
            
            # Lazy import processor
            from sub_processor import SubtitleProcessor
            processor = SubtitleProcessor(lang="ch", engine="rapid")
            
            subs = processor.extract_subtitles(
                video_path, 
                crop_region=region,
                progress_callback=lambda p: self.progress.emit(20 + p * 40),
                step=5
            )
            
            if not subs:
                self.error.emit("No subtitles found during OCR")
                return

            # 3. Translate
            self.status.emit("🌐 Step 3/4: Translating to Vietnamese...")
            translated = processor.translate_subtitles(
                subs,
                progress_callback=lambda p: self.progress.emit(60 + p * 20), # 60% to 80%
                engine=self.settings.get("trans_engine", "google"),
                gemini_keys=self.settings.get("gemini_keys")
            )
            
            # Save SRT
            project_folder = self.get_project_folder(video_path)
            srt_path = os.path.join(project_folder, "subtitles_vi.srt")
            processor.save_to_srt(translated, srt_path)

            # 4. Render
            self.status.emit("🎬 Step 4/4: Rendering final video...")
            from video_renderer import render_video_with_vietnamese_subs
            
            output_video = os.path.join(project_folder, f"translated_{os.path.basename(video_path)}")
            
            render_video_with_vietnamese_subs(
                video_path,
                translated,
                output_video,
                subtitle_region=region,
                progress_callback=lambda p: self.progress.emit(80 + p * 20) # 80% to 100%
            )
            
            self.status.emit("✅ All steps completed!")
            self.finished.emit(output_video)
            
        except Exception as e:
            self.error.emit(f"Automation error: {str(e)}")

    def get_project_folder(self, video_path):
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        projects_dir = os.path.abspath("projects")
        folder = os.path.join(projects_dir, video_name)
        os.makedirs(folder, exist_ok=True)
        return folder


class DownloadTab(QWidget):
    """Tab for downloading videos from URLs"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.download_worker = None
        
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
        title = QLabel("📥 Download Video from URL")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # URL Input Group
        url_group = QGroupBox("Video URL")
        url_layout = QVBoxLayout()
        
        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter Bilibili video URL (e.g., https://www.bilibili.com/video/BV...)")
        self.url_input.textChanged.connect(self.auto_save)
        self.url_input.returnPressed.connect(self.start_download)
        url_input_layout.addWidget(self.url_input)
        
        paste_btn = QPushButton("📋 Paste")
        paste_btn.setProperty("class", "secondary")
        paste_btn.clicked.connect(self.paste_url)
        url_input_layout.addWidget(paste_btn)
        
        url_layout.addLayout(url_input_layout)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)
        
        # Output Directory Group
        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout()
        
        self.output_path = QLineEdit()
        self.output_path.setText(os.path.abspath("downloads"))
        self.output_path.textChanged.connect(self.auto_save)
        self.output_path.setReadOnly(True)
        output_layout.addWidget(self.output_path)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.setProperty("class", "secondary")
        browse_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(browse_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Progress
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Log
        log_group = QGroupBox("Download Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Automation Group
        auto_group = QGroupBox("🚀 Workflow Automation")
        auto_layout = QVBoxLayout()
        
        auto_desc = QLabel("Run the complete pipeline from OCR to Final Video Render automatically.")
        auto_desc.setStyleSheet("color: #80848E; font-size: 11px; margin-bottom: 5px;")
        auto_layout.addWidget(auto_desc)
        
        self.auto_btn = QPushButton("🔥 START FULL AUTOMATIC PROCESS")
        self.auto_btn.setStyleSheet("""
            background-color: #5865F2;
            color: white;
            font-weight: bold;
            font-size: 14px;
            padding: 10px;
        """)
        self.auto_btn.clicked.connect(self.start_auto_workflow)
        auto_layout.addWidget(self.auto_btn)
        
        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.download_btn = QPushButton("⬇️ Start Download")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setMinimumWidth(150)
        button_layout.addWidget(self.download_btn)
        
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setProperty("class", "danger")
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setMinimumWidth(150)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
    def paste_url(self):
        """Paste URL from clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        self.url_input.setText(clipboard.text())
        
    def browse_output(self):
        """Browse for output directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_path.text()
        )
        if directory:
            self.output_path.setText(directory)
            
    def start_download(self):
        """Start video download"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a video URL")
            return
            
        output_dir = self.output_path.text()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Disable UI
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.url_input.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        # Start download worker
        self.download_worker = DownloadWorker(url, output_dir)
        self.download_worker.progress.connect(self.on_progress)
        self.download_worker.finished.connect(self.on_finished)
        self.download_worker.error.connect(self.on_error)
        self.download_worker.log.connect(self.on_log)
        self.download_worker.start()
        
    def cancel_download(self):
        """Cancel ongoing download"""
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.terminate()
            self.download_worker.wait()
            self.on_log("Download cancelled by user")
            self.reset_ui()
            
    def on_progress(self, percent):
        """Update progress bar"""
        self.progress_bar.setValue(int(percent))
        
    def on_finished(self, file_path):
        """Handle download completion"""
        self.on_log(f"✅ Download completed successfully!")
        self.progress_bar.setValue(100)
        self.reset_ui()
        
        # Ask to load as project
        reply = QMessageBox.question(
            self,
            "Download Complete",
            f"Video downloaded successfully!\n\n{file_path}\n\nLoad this video as a project?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.main_window.load_project(file_path)
            
    def start_auto_workflow(self):
        """Start the full automation pipeline"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a video URL or select a video file first")
            return
            
        output_dir = self.output_path.text()
        
        gemini_keys_raw = self.main_window.settings_tab.gemini_keys.toPlainText().strip()
        gemini_keys = [k.strip() for k in gemini_keys_raw.split('\n') if k.strip()] if gemini_keys_raw else []
        
        settings = {
            "trans_engine": self.main_window.settings_tab.default_trans_engine.currentText().lower()
            if hasattr(self.main_window, 'settings_tab') else "google",
            "gemini_keys": gemini_keys
        }
        
        if settings["trans_engine"] == "gemini" and not gemini_keys:
            QMessageBox.warning(self, "Warning", "Please enter Gemini API keys in Settings tab first")
            return
        
        # Disable UI
        self.auto_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.on_log("🚀 Starting Full Automation Workflow...")
        
        self.auto_worker = AutoWorkflowWorker(url, output_dir, settings)
        self.auto_worker.progress.connect(self.on_progress)
        self.auto_worker.status.connect(self.on_log)
        self.auto_worker.error.connect(self.on_error)
        
        def on_finished(output_video):
            self.on_log(f"🎉 Process completed! Output saved to: {output_video}")
            self.reset_ui()
            self.auto_btn.setEnabled(True)
            
            # Show completion message
            QMessageBox.information(self, "Success", f"Full automation completed successfully!\n\nVideo saved to:\n{output_video}")
            
            # Load as project
            self.main_window.load_project(url if os.path.isfile(url) else output_video)
            
        self.auto_worker.finished.connect(on_finished)
        self.auto_worker.start()

    def on_error(self, error_msg):
        """Handle download error"""
        self.on_log(f"❌ Error: {error_msg}")
        QMessageBox.critical(self, "Download Error", error_msg)
        self.reset_ui()
        
    def on_log(self, message):
        """Add message to log"""
        self.log_text.append(message)
        
    def reset_ui(self):
        """Reset UI to initial state"""
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.url_input.setEnabled(True)
        
    def on_project_loaded(self, video_path, project_data):
        """Called when a project is loaded"""
        # Update UI with project data if available
        if 'download' in project_data:
            download_data = project_data['download']
            if 'url' in download_data:
                self.url_input.setText(download_data['url'])
                
    def get_state(self):
        """Get current state for saving"""
        return {
            'url': self.url_input.text(),
            'output_path': self.output_path.text()
        }

    def auto_save(self):
        """Auto-save project state"""
        if self.main_window:
            self.main_window.save_project(silent=True)
