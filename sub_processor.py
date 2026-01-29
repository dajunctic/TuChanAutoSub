import cv2
import os
import easyocr
from deep_translator import GoogleTranslator
import datetime
import warnings

# Suppress warnings from easyocr/torch if any
warnings.filterwarnings("ignore")

class SubtitleProcessor:
    def __init__(self, lang='ch'):
        """
        Initialize EasyOCR reader.
        lang code mapping: 'ch' -> 'ch_sim', 'en' -> 'en', etc.
        """
        # Map simple lang codes to EasyOCR codes
        lang_map = {
            'ch': 'ch_sim',
            'en': 'en',
            'japan': 'ja',
            'korean': 'ko'
        }
        
        target_lang = lang_map.get(lang, 'ch_sim')
        langs = [target_lang]
        if target_lang != 'en':
            langs.append('en') # Always include English as secondary
            
        print(f"Initializing EasyOCR with languages: {langs}...")
        # gpu=True if CUDA is available, else False. auto-detect usually works.
        self.reader = easyocr.Reader(langs) 
        self.translator = GoogleTranslator(source='auto', target='vi')

    def formatted_time(self, seconds):
        """Convert seconds to SRT time format: HH:MM:SS,mmm"""
        td = datetime.timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int(td.microseconds / 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def extract_subtitles(self, video_path, crop_region=None, progress_callback=None, subtitle_callback=None):
        """
        Extract hard subtitles from video using EasyOCR.
        crop_region: tuple (ymin, ymax, xmin, xmax) as values 0.0 to 1.0. 
                     Default is None (bottom 25%).
        subtitle_callback: Optional callback(subtitle_list) called whenever a new subtitle is detected
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        
        # Calculate pixel crop coordinates
        if crop_region:
            ymin, ymax, xmin, xmax = crop_region
            y1 = int(height * ymin)
            y2 = int(height * ymax)
            x1 = int(width * xmin)
            x2 = int(width * xmax)
        else:
            # Default: Bottom 25%
            y1 = int(height * 0.75) 
            y2 = height
            x1 = 0
            x2 = width

        # Ensure valid ranges
        y1 = max(0, y1); y2 = min(height, y2)
        x1 = max(0, x1); x2 = min(width, x2)

        subtitles = []
        current_sub = None

        
        # Check ever 0.5 seconds (fps / 2) to save time, as subs don't change that fast
        step = max(1, int(fps / 2)) 
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_idx % step != 0:
                frame_idx += 1
                continue
            
            if progress_callback:
                progress_callback(frame_idx / total_frames)

            # Crop designated area
            cropped = frame[y1:y2, x1:x2]
            
            # OCR
            # result structure: [(bbox, text, confidence)]
            try:
                result = self.reader.readtext(cropped)
            except Exception as e:
                print(f"OCR Error at frame {frame_idx}: {e}")
                result = []
            
            detected_text = ""
            if result:
                # Filter low confidence and join
                texts = [item[1] for item in result if item[2] > 0.4] # Confidence > 0.4
                detected_text = " ".join(texts).strip()

            current_time = frame_idx / fps

            if detected_text:
                if current_sub and self.similar_text(current_sub['text'], detected_text):
                    # Same subtitle, extend duration
                    current_sub['end'] = current_time
                else:
                    # New subtitle
                    if current_sub:
                        subtitles.append(current_sub)
                        # Call real-time callback with updated list
                        if subtitle_callback:
                            subtitle_callback(subtitles.copy())
                    
                    current_sub = {
                        'start': current_time,
                        'end': current_time,
                        'text': detected_text
                    }
            else:
                # No text
                if current_sub:
                    subtitles.append(current_sub)
                    # Call real-time callback
                    if subtitle_callback:
                        subtitle_callback(subtitles.copy())
                    current_sub = None
            
            frame_idx += 1

        if current_sub:
            subtitles.append(current_sub)
            if subtitle_callback:
                subtitle_callback(subtitles.copy())

        cap.release()
        return subtitles

    def similar_text(self, text1, text2):
        # Basic similarity check to avoid flickering
        if text1 == text2: return True
        # Allow minor OCR variations
        return False

    def translate_subtitles(self, subtitles, progress_callback=None):
        translated_subs = []
        total = len(subtitles)
        for i, sub in enumerate(subtitles):
            original = sub['text']
            # Clean up text (OCR sometimes produces garbage)
            if len(original) < 2: 
                continue 

            try:
                translated = self.translator.translate(original)
            except Exception as e:
                translated = original 
            
            translated_subs.append({
                'start': sub['start'],
                'end': sub['end'],
                'text': translated,
                'original': original
            })
            
            if progress_callback:
                progress_callback((i + 1) / total)
                
        return translated_subs

    def save_to_srt(self, subtitles, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, sub in enumerate(subtitles):
                # Min duration 1.5s if too short
                duration = sub['end'] - sub['start']
                end_time = sub['end']
                if duration < 1.0:
                     end_time = sub['start'] + 1.5

                f.write(f"{i+1}\n")
                start = self.formatted_time(sub['start'])
                end = self.formatted_time(end_time)
                
                f.write(f"{start} --> {end}\n")
                f.write(f"{sub['text']}\n\n")
