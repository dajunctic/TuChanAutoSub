"""
OCR Tab - Subtitle extraction with region selection
"""

import os
import cv2
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QGroupBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QListWidget, QMessageBox, QFileDialog, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QCursor
from auto_detect_region import auto_detect_subtitle_region
# Lazy import to avoid PyTorch DLL issues at startup
# from sub_processor import SubtitleProcessor


class RegionSelectorWidget(QLabel):
    """Widget for selecting subtitle region on video frame"""
    region_selected = pyqtSignal(tuple)  # (x, y, w, h)
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 360)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            background-color: #1E1F22;
            border: 2px solid #4E5058;
            border-radius: 8px;
        """)
        
        self.image = None
        self.start_point = None
        self.end_point = None
        self.current_region = None
        self.drawing = False
        
    def set_image(self, cv_image):
        """Set image from OpenCV format"""
        if cv_image is None:
            return
            
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Scale to fit widget
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image = scaled_pixmap
        self.update()
        
    def paintEvent(self, event):
        """Custom paint event to draw selection rectangle"""
        super().paintEvent(event)
        
        if self.image:
            painter = QPainter(self)
            
            # Draw image centered
            x = (self.width() - self.image.width()) // 2
            y = (self.height() - self.image.height()) // 2
            painter.drawPixmap(x, y, self.image)
            
            # Draw selection rectangle
            if self.start_point and self.end_point:
                pen = QPen(QColor(88, 101, 242), 3, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                
                x1 = min(self.start_point.x(), self.end_point.x())
                y1 = min(self.start_point.y(), self.end_point.y())
                x2 = max(self.start_point.x(), self.end_point.x())
                y2 = max(self.start_point.y(), self.end_point.y())
                
                painter.drawRect(x1, y1, x2 - x1, y2 - y1)
                
    def mousePressEvent(self, event):
        """Handle mouse press for region selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.drawing = True
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for region selection"""
        if self.drawing:
            self.end_point = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release to finalize region"""
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            self.end_point = event.pos()
            self.update()
            
            # Calculate region in original image coordinates
            if self.image:
                img_x = (self.width() - self.image.width()) // 2
                img_y = (self.height() - self.image.height()) // 2
                
                x1 = min(self.start_point.x(), self.end_point.x()) - img_x
                y1 = min(self.start_point.y(), self.end_point.y()) - img_y
                x2 = max(self.start_point.x(), self.end_point.x()) - img_x
                y2 = max(self.start_point.y(), self.end_point.y()) - img_y
                
                # Clamp to image bounds
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(self.image.width(), x2)
                y2 = min(self.image.height(), y2)
                
                w = x2 - x1
                h = y2 - y1
                
                if w > 10 and h > 10:  # Minimum size
                    self.current_region = (x1, y1, w, h)
                    self.region_selected.emit(self.current_region)


class OCRWorker(QThread):
    """Worker thread for OCR extraction"""
    progress = pyqtSignal(float)
    subtitle_found = pyqtSignal(dict)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    log = pyqtSignal(str)
    
    def __init__(self, video_path, crop_region, engine, lang, min_text_len, min_duration, step):
        super().__init__()
        self.video_path = video_path
        self.crop_region = crop_region
        self.engine = engine
        self.lang = lang
        self.min_text_len = min_text_len
        self.min_duration = min_duration
        self.step = step
        
    def run(self):
        """Run OCR extraction"""
        try:
            self.log.emit(f"Starting OCR with {self.engine} engine...")
            
            # Lazy import to avoid DLL issues
            from sub_processor import SubtitleProcessor
            processor = SubtitleProcessor(lang=self.lang, engine=self.engine)
            
            def progress_callback(percent):
                self.progress.emit(percent)
                
            def subtitle_callback(subtitle):
                self.subtitle_found.emit(subtitle)
                
            subtitles = processor.extract_subtitles(
                self.video_path,
                crop_region=self.crop_region,
                progress_callback=progress_callback,
                subtitle_callback=subtitle_callback,
                min_text_len=self.min_text_len,
                min_duration=self.min_duration,
                step=self.step
            )
            
            self.log.emit(f"OCR completed! Found {len(subtitles)} subtitles")
            self.finished.emit(subtitles)
            
        except Exception as e:
            self.error.emit(f"OCR error: {str(e)}")


class OCRTab(QWidget):
    """Tab for OCR subtitle extraction"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.video_path = None
        self.crop_region = None
        self.subtitles = []
        self.ocr_worker = None
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Container
        self.container = QWidget()
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(20, 20, 20, 20)
        self.container_layout.setSpacing(15)
        
        self.init_ui()
        
        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll)
        
    def init_ui(self):
        """Initialize UI components inside container layout"""
        layout = self.container_layout
        
        # Left panel - Preview and region selection
        left_panel = QVBoxLayout()
        
        
        # Video preview
        preview_layout = QVBoxLayout()
        
        self.region_selector = RegionSelectorWidget()
        self.region_selector.setMinimumHeight(550) # Make it taller
        self.region_selector.region_selected.connect(self.on_region_selected)
        preview_layout.addWidget(self.region_selector)
        
        # Region info
        region_info_layout = QHBoxLayout()
        self.region_label = QLabel("No region selected - Click and drag to select subtitle area")
        self.region_label.setStyleSheet("color: #80848E; font-size: 11px;")
        region_info_layout.addWidget(self.region_label)
        
        region_info_layout.addStretch()
        
        load_frame_btn = QPushButton("🖼️ Load Frame")
        load_frame_btn.setProperty("class", "secondary")
        load_frame_btn.clicked.connect(self.load_video_frame)
        region_info_layout.addWidget(load_frame_btn)
        
        auto_detect_btn = QPushButton("🪄 Auto Detect")
        auto_detect_btn.setProperty("class", "secondary")
        auto_detect_btn.clicked.connect(self.auto_detect_region)
        region_info_layout.addWidget(auto_detect_btn)
        
        clear_region_btn = QPushButton("🗑️ Clear")
        clear_region_btn.setProperty("class", "secondary")
        clear_region_btn.clicked.connect(self.clear_region)
        region_info_layout.addWidget(clear_region_btn)
        
        preview_layout.addLayout(region_info_layout)
        left_panel.addLayout(preview_layout)
        
        layout.addLayout(left_panel, 3) # Increased stretch for video
        
        # Right panel - Settings and controls
        right_panel = QVBoxLayout()
        
        # OCR Settings
        settings_group = QGroupBox("OCR Settings")
        settings_layout = QFormLayout()
        settings_layout.setSpacing(8)
        settings_layout.setContentsMargins(10, 20, 10, 10)
        
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["rapid", "easyocr"])
        settings_layout.addRow("Engine:", self.engine_combo)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ch", "en", "ja", "ko"])
        settings_layout.addRow("Language:", self.lang_combo)
        
        self.min_text_spin = QSpinBox()
        self.min_text_spin.setRange(1, 20)
        self.min_text_spin.setValue(2)
        settings_layout.addRow("Min Len:", self.min_text_spin)
        
        self.min_dur_spin = QDoubleSpinBox()
        self.min_dur_spin.setRange(0.1, 10.0)
        self.min_dur_spin.setSingleStep(0.1)
        self.min_dur_spin.setValue(0.5)
        settings_layout.addRow("Min Dur:", self.min_dur_spin)
        
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 30)
        self.step_spin.setValue(5)
        settings_layout.addRow("Step:", self.step_spin)
        
        settings_group.setLayout(settings_layout)
        right_panel.addWidget(settings_group)
        
        # Connect signals for auto-save
        self.engine_combo.currentIndexChanged.connect(self.auto_save)
        self.lang_combo.currentIndexChanged.connect(self.auto_save)
        self.min_text_spin.valueChanged.connect(self.auto_save)
        self.min_dur_spin.valueChanged.connect(self.auto_save)
        self.step_spin.valueChanged.connect(self.auto_save)
        
        # Progress
        progress_group = QGroupBox("Extraction Progress")
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
        right_panel.addWidget(progress_group)
        
        # Extracted subtitles list
        subtitles_group = QGroupBox("Extracted Subtitles")
        subtitles_layout = QVBoxLayout()
        
        self.subtitles_list = QListWidget()
        self.subtitles_list.setMaximumHeight(200)
        subtitles_layout.addWidget(self.subtitles_list)
        
        list_buttons = QHBoxLayout()
        
        export_btn = QPushButton("💾 Export SRT")
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(self.export_srt)
        list_buttons.addWidget(export_btn)
        
        clear_btn = QPushButton("🗑️ Clear List")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_subtitles)
        list_buttons.addWidget(clear_btn)
        
        subtitles_layout.addLayout(list_buttons)
        subtitles_group.setLayout(subtitles_layout)
        right_panel.addWidget(subtitles_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.extract_btn = QPushButton("▶️ Start Extraction")
        self.extract_btn.clicked.connect(self.start_extraction)
        self.extract_btn.setMinimumHeight(40)
        button_layout.addWidget(self.extract_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.clicked.connect(self.stop_extraction)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(40)
        button_layout.addWidget(self.stop_btn)
        
        right_panel.addLayout(button_layout)
        
        right_panel.addStretch()
        
        layout.addLayout(right_panel, 1)
        
    def auto_detect_region(self):
        """Automatically detect subtitle region"""
        if not self.video_path or not os.path.exists(self.video_path):
            QMessageBox.warning(self, "Warning", "Please load a project with a video first")
            return
            
        self.status_label.setText("Detecting subtitle region...")
        self.progress_bar.setValue(0)
        
        # Use a background thread for detection to avoid freezing UI
        class DetectorWorker(QThread):
            finished = pyqtSignal(tuple)
            progress = pyqtSignal(float)
            
            def __init__(self, path):
                super().__init__()
                self.path = path
                
            def run(self):
                from auto_detect_region import auto_detect_subtitle_region
                region = auto_detect_subtitle_region(self.path, progress_callback=self.progress.emit)
                self.finished.emit(region)
                
        self.detector_thread = DetectorWorker(self.video_path)
        self.detector_thread.progress.connect(lambda p: self.progress_bar.setValue(int(p * 100)))
        
        def on_finished(region):
            ymin, ymax, xmin, xmax = region
            
            # Convert percentage back to pixels
            cap = cv2.VideoCapture(self.video_path)
            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            self.crop_region = (
                int(xmin * orig_w),
                int(ymin * orig_h),
                int((xmax - xmin) * orig_w),
                int((ymax - ymin) * orig_h)
            )
            
            # Visual feedback
            self.region_label.setText(
                f"Auto-detected: ({self.crop_region[0]}, {self.crop_region[1]}, "
                f"{self.crop_region[2]}, {self.crop_region[3]})"
            )
            
            # Show the region on a frame
            self.load_video_frame()
            
            # Manually trigger region selection to draw the box
            if self.region_selector.image:
                scale_x = self.region_selector.image.width() / orig_w
                scale_y = self.region_selector.image.height() / orig_h
                
                self.region_selector.start_point = QCursor().pos() # Dummy
                self.region_selector.start_point = self.region_selector.mapFromGlobal(QCursor().pos()) # Dummy
                # Use pixel values directly for the selector
                x1 = int(xmin * self.region_selector.width())
                y1 = int(ymin * self.region_selector.height())
                x2 = int(xmax * self.region_selector.width())
                y2 = int(ymax * self.region_selector.height())
                
                from PyQt6.QtCore import QPoint
                self.region_selector.start_point = QPoint(x1, y1)
                self.region_selector.end_point = QPoint(x2, y2)
                self.region_selector.update()
            
            self.status_label.setText("Region detected successfully")
            self.progress_bar.setValue(100)
            
        self.detector_thread.finished.connect(on_finished)
        self.detector_thread.start()

    def load_video_frame(self):
        """Load a frame from the current video"""
        if not self.video_path or not os.path.exists(self.video_path):
            QMessageBox.warning(self, "Warning", "Please load a project with a video first")
            return
            
        try:
            cap = cv2.VideoCapture(self.video_path)
            
            # Get middle frame
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                self.region_selector.set_image(frame)
            else:
                QMessageBox.warning(self, "Warning", "Failed to read video frame")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load frame: {e}")
            
    def on_region_selected(self, region):
        """Handle region selection"""
        x, y, w, h = region
        
        # Scale region to original video size
        if self.video_path:
            cap = cv2.VideoCapture(self.video_path)
            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # Get scale factor
            if self.region_selector.image:
                scale_x = orig_w / self.region_selector.image.width()
                scale_y = orig_h / self.region_selector.image.height()
                
                self.crop_region = (
                    int(x * scale_x),
                    int(y * scale_y),
                    int(w * scale_x),
                    int(h * scale_y)
                )
                
                self.region_label.setText(
                    f"Region: ({self.crop_region[0]}, {self.crop_region[1]}, "
                    f"{self.crop_region[2]}, {self.crop_region[3]})"
                )
                
    def clear_region(self):
        """Clear selected region"""
        self.crop_region = None
        self.region_selector.start_point = None
        self.region_selector.end_point = None
        self.region_selector.update()
        self.region_label.setText("No region selected")
        
    def start_extraction(self):
        """Start OCR extraction"""
        if not self.video_path or not os.path.exists(self.video_path):
            QMessageBox.warning(self, "Warning", "Please load a project with a video first")
            return
            
        # Disable UI
        self.extract_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.subtitles_list.clear()
        self.subtitles = []
        
        # Start OCR worker
        self.ocr_worker = OCRWorker(
            self.video_path,
            self.crop_region,
            self.engine_combo.currentText(),
            self.lang_combo.currentText(),
            self.min_text_spin.value(),
            self.min_dur_spin.value(),
            self.step_spin.value()
        )
        
        self.ocr_worker.progress.connect(self.on_progress)
        self.ocr_worker.subtitle_found.connect(self.on_subtitle_found)
        self.ocr_worker.finished.connect(self.on_extraction_finished)
        self.ocr_worker.error.connect(self.on_error)
        self.ocr_worker.log.connect(self.on_log)
        self.ocr_worker.start()
        
    def stop_extraction(self):
        """Stop OCR extraction"""
        if self.ocr_worker and self.ocr_worker.isRunning():
            self.ocr_worker.terminate()
            self.ocr_worker.wait()
            self.status_label.setText("Extraction stopped by user")
            self.reset_ui()
            
    def on_progress(self, percent):
        """Update progress"""
        self.progress_bar.setValue(int(percent))
        
    def on_subtitle_found(self, subtitle):
        """Handle new subtitle found"""
        text = subtitle.get('text', '')
        start = subtitle.get('start', 0)
        end = subtitle.get('end', 0)
        
        self.subtitles_list.addItem(f"[{start:.2f}s - {end:.2f}s] {text}")
        
    def on_extraction_finished(self, subtitles):
        """Handle extraction completion"""
        self.subtitles = subtitles
        self.status_label.setText(f"✅ Extraction complete! Found {len(subtitles)} subtitles")
        self.progress_bar.setValue(100)
        self.reset_ui()
        
        # Auto-save to project
        if self.main_window.current_project:
            project_folder = self.main_window.get_project_folder(self.main_window.current_project)
            srt_path = os.path.join(project_folder, "chinese_subtitles.srt")
            
            # Lazy import
            from sub_processor import SubtitleProcessor
            processor = SubtitleProcessor()
            processor.save_to_srt(subtitles, srt_path)
            
            self.status_label.setText(f"✅ Saved to {srt_path}")
            
    def on_error(self, error_msg):
        """Handle error"""
        self.status_label.setText(f"❌ Error: {error_msg}")
        QMessageBox.critical(self, "OCR Error", error_msg)
        self.reset_ui()
        
    def on_log(self, message):
        """Handle log message"""
        self.status_label.setText(message)
        
    def reset_ui(self):
        """Reset UI to initial state"""
        self.extract_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
    def export_srt(self):
        """Export subtitles to SRT file"""
        if not self.subtitles:
            QMessageBox.information(self, "Info", "No subtitles to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save SRT File",
            "subtitles.srt",
            "SRT Files (*.srt);;All Files (*.*)"
        )
        
        if file_path:
            try:
                # Lazy import
                from sub_processor import SubtitleProcessor
                processor = SubtitleProcessor()
                processor.save_to_srt(self.subtitles, file_path)
                QMessageBox.information(self, "Success", f"Subtitles exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
                
    def clear_subtitles(self):
        """Clear subtitles list"""
        self.subtitles = []
        self.subtitles_list.clear()
        self.status_label.setText("Subtitles cleared")
        
    def on_project_loaded(self, video_path, project_data):
        """Called when a project is loaded"""
        self.video_path = video_path
        
        # Load saved OCR data
        if 'ocr' in project_data:
            ocr_data = project_data['ocr']
            
            if 'crop_region' in ocr_data and ocr_data['crop_region']:
                self.crop_region = tuple(ocr_data['crop_region'])
                self.region_label.setText(f"Region: {self.crop_region}")
                
            if 'engine' in ocr_data:
                index = self.engine_combo.findText(ocr_data['engine'])
                if index >= 0:
                    self.engine_combo.setCurrentIndex(index)
                    
            if 'lang' in ocr_data:
                index = self.lang_combo.findText(ocr_data['lang'])
                if index >= 0:
                    self.lang_combo.setCurrentIndex(index)
                    
        # Auto-load frame
        QTimer.singleShot(500, self.load_video_frame)
        
    def get_state(self):
        """Get current state for saving"""
        return {
            'crop_region': list(self.crop_region) if self.crop_region else None,
            'engine': self.engine_combo.currentText(),
            'lang': self.lang_combo.currentText(),
            'min_text_len': self.min_text_spin.value(),
            'min_duration': self.min_dur_spin.value(),
            'step': self.step_spin.value()
        }

    def auto_save(self):
        """Auto-save project state"""
        if self.main_window:
            self.main_window.save_project(silent=True)
