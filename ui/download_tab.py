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
