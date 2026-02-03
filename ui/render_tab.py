"""
Render Tab - Video rendering with Vietnamese subtitles
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QGroupBox,
    QLineEdit, QFileDialog, QMessageBox, QComboBox,
    QSpinBox, QCheckBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from video_renderer import render_video_with_vietnamese_subs


class RenderWorker(QThread):
    """Worker thread for video rendering"""
    progress = pyqtSignal(float)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    log = pyqtSignal(str)
    
    def __init__(self, video_path, srt_path, output_path):
        super().__init__()
        self.video_path = video_path
        self.srt_path = srt_path
        self.output_path = output_path
        
    def run(self):
        """Run video rendering"""
        try:
            self.log.emit("Starting video rendering...")
            
            def progress_callback(percent):
                self.progress.emit(percent)
                
            result = render_video_with_vietnamese_subs(
                self.video_path,
                self.srt_path,
                self.output_path,
                progress_callback=progress_callback
            )
            
            if result:
                self.log.emit(f"Rendering completed: {result}")
                self.finished.emit(result)
            else:
                self.error.emit("Rendering failed")
                
        except Exception as e:
            self.error.emit(f"Rendering error: {str(e)}")


class RenderTab(QWidget):
    """Tab for video rendering"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.video_path = None
        self.render_worker = None
        
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
        title = QLabel("🎬 Render Video with Subtitles")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Input video
        video_group = QGroupBox("Input Video")
        video_layout = QHBoxLayout()
        
        self.video_input = QLineEdit()
        self.video_input.setReadOnly(True)
        self.video_input.setPlaceholderText("Video will be loaded from project")
        video_layout.addWidget(self.video_input)
        
        browse_video_btn = QPushButton("📁 Browse")
        browse_video_btn.setProperty("class", "secondary")
        browse_video_btn.clicked.connect(self.browse_video)
        video_layout.addWidget(browse_video_btn)
        
        video_group.setLayout(video_layout)
        layout.addWidget(video_group)
        
        # Subtitle file
        subtitle_group = QGroupBox("Vietnamese Subtitles (SRT)")
        subtitle_layout = QHBoxLayout()
        
        self.subtitle_input = QLineEdit()
        self.subtitle_input.setReadOnly(True)
        self.subtitle_input.setPlaceholderText("Subtitles will be loaded from project")
        subtitle_layout.addWidget(self.subtitle_input)
        
        browse_sub_btn = QPushButton("📁 Browse")
        browse_sub_btn.setProperty("class", "secondary")
        browse_sub_btn.clicked.connect(self.browse_subtitle)
        subtitle_layout.addWidget(browse_sub_btn)
        
        subtitle_group.setLayout(subtitle_layout)
        layout.addWidget(subtitle_group)
        
        # Output file
        output_group = QGroupBox("Output Video")
        output_layout = QHBoxLayout()
        
        self.output_input = QLineEdit()
        self.output_input.setPlaceholderText("Output video path")
        output_layout.addWidget(self.output_input)
        
        browse_output_btn = QPushButton("📁 Browse")
        browse_output_btn.setProperty("class", "secondary")
        browse_output_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(browse_output_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Progress
        progress_group = QGroupBox("Rendering Progress")
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
        
        # Log
        log_group = QGroupBox("Rendering Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.render_btn = QPushButton("▶️ Start Rendering")
        self.render_btn.clicked.connect(self.start_rendering)
        self.render_btn.setMinimumWidth(150)
        self.render_btn.setMinimumHeight(40)
        button_layout.addWidget(self.render_btn)
        
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setProperty("class", "danger")
        self.cancel_btn.clicked.connect(self.cancel_rendering)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setMinimumWidth(150)
        self.cancel_btn.setMinimumHeight(40)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
    def browse_video(self):
        """Browse for input video"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input Video",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*.*)"
        )
        if file_path:
            self.video_input.setText(file_path)
            self.video_path = file_path
            
    def browse_subtitle(self):
        """Browse for subtitle file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Subtitle File",
            "",
            "SRT Files (*.srt);;All Files (*.*)"
        )
        if file_path:
            self.subtitle_input.setText(file_path)
            
    def browse_output(self):
        """Browse for output video"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Output Video",
            "output_with_subtitles.mp4",
            "MP4 Files (*.mp4);;All Files (*.*)"
        )
        if file_path:
            self.output_input.setText(file_path)
            
    def start_rendering(self):
        """Start video rendering"""
        video_path = self.video_input.text()
        subtitle_path = self.subtitle_input.text()
        output_path = self.output_input.text()
        
        # Validation
        if not video_path or not os.path.exists(video_path):
            QMessageBox.warning(self, "Warning", "Please select a valid input video")
            return
            
        if not subtitle_path or not os.path.exists(subtitle_path):
            QMessageBox.warning(self, "Warning", "Please select a valid subtitle file")
            return
            
        if not output_path:
            QMessageBox.warning(self, "Warning", "Please specify an output path")
            return
            
        # Disable UI
        self.render_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        
        # Start rendering worker
        self.render_worker = RenderWorker(video_path, subtitle_path, output_path)
        self.render_worker.progress.connect(self.on_progress)
        self.render_worker.finished.connect(self.on_finished)
        self.render_worker.error.connect(self.on_error)
        self.render_worker.log.connect(self.on_log)
        self.render_worker.start()
        
    def cancel_rendering(self):
        """Cancel rendering"""
        if self.render_worker and self.render_worker.isRunning():
            self.render_worker.terminate()
            self.render_worker.wait()
            self.on_log("Rendering cancelled by user")
            self.reset_ui()
            
    def on_progress(self, percent):
        """Update progress"""
        self.progress_bar.setValue(int(percent))
        
    def on_finished(self, output_path):
        """Handle rendering completion"""
        self.on_log(f"✅ Rendering completed successfully!")
        self.status_label.setText(f"✅ Video saved to: {output_path}")
        self.progress_bar.setValue(100)
        self.reset_ui()
        
        QMessageBox.information(
            self,
            "Rendering Complete",
            f"Video with subtitles has been created:\n\n{output_path}"
        )
        
    def on_error(self, error_msg):
        """Handle error"""
        self.on_log(f"❌ Error: {error_msg}")
        self.status_label.setText(f"❌ Error: {error_msg}")
        QMessageBox.critical(self, "Rendering Error", error_msg)
        self.reset_ui()
        
    def on_log(self, message):
        """Add message to log"""
        self.log_text.append(message)
        
    def reset_ui(self):
        """Reset UI to initial state"""
        self.render_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
    def on_project_loaded(self, video_path, project_data):
        """Called when a project is loaded"""
        self.video_path = video_path
        self.video_input.setText(video_path)
        
        # Auto-load subtitle file from project
        project_folder = self.main_window.get_project_folder(video_path)
        srt_path = os.path.join(project_folder, "vietnamese_subtitles.srt")
        
        if os.path.exists(srt_path):
            self.subtitle_input.setText(srt_path)
            
        # Set default output path
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(project_folder, f"{video_name}_with_subtitles.mp4")
        self.output_input.setText(output_path)
        
        # Load saved render data
        if 'render' in project_data:
            render_data = project_data['render']
            if 'output_path' in render_data:
                self.output_input.setText(render_data['output_path'])
                
    def get_state(self):
        """Get current state for saving"""
        return {
            'output_path': self.output_input.text()
        }

    def auto_save(self):
        """Auto-save project state"""
        if self.main_window:
            self.main_window.save_project(silent=True)
