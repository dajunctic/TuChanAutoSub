import cv2
import os
# import easyocr (Moved to lazy-load inside class)
from deep_translator import GoogleTranslator
import datetime
import warnings

# Suppress warnings from easyocr/torch if any
warnings.filterwarnings("ignore")

import site
import sys
# Ensure user-site packages are in the path (fixes installation issues on Windows)
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

class SubtitleProcessor:
    def __init__(self, lang='ch', engine='rapid'):
        """
        Initialize OCR Engine.
        engine: 'easyocr' or 'rapid'
        """
        self.engine = engine
        self.lang = lang
        self.translator = GoogleTranslator(source='auto', target='vi')
        self.lm_studio_url = "http://localhost:1234/v1"
        self.translation_engine = 'google' # default
        
        if engine == 'easyocr':
            try:
                import easyocr
                # Map simple lang codes to EasyOCR codes
                lang_map = {'ch': 'ch_sim', 'en': 'en', 'ja': 'ja', 'ko': 'ko'}
                target_lang = lang_map.get(lang, 'ch_sim')
                langs = [target_lang]
                if target_lang != 'en': langs.append('en')
                print(f"Initializing EasyOCR with languages: {langs}...")
                self.reader = easyocr.Reader(langs)
            except Exception as e:
                print(f"Failed to initialize EasyOCR: {e}")
                print("Falling back to RapidOCR...")
                self.engine = 'rapid'
                self._init_rapid()
        else:
            self._init_rapid()

    def _init_rapid(self):
        try:
            print("Initializing RapidOCR with GPU/CPU support...")
            from rapidocr_onnxruntime import RapidOCR
            self.rapid_engine = RapidOCR()
        except Exception as e:
            print(f"Failed to initialize RapidOCR: {e}")
            raise e

    def formatted_time(self, seconds):
        """Convert seconds to SRT time format: HH:MM:SS,mmm"""
        td = datetime.timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int(td.microseconds / 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def similar_text(self, text1, text2):
        """Fuzzy text comparison to handle OCR noise"""
        if not text1 or not text2: return False
        if text1 == text2: return True
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio() > 0.8

    def _crop_video_cv2(self, input_path, output_path, crop_region, progress_callback=None):
        """Creates a temporary cropped video for RapidVideOCR to focus on"""
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        ymin, ymax, xmin, xmax = crop_region
        y1, y2 = int(height * ymin), int(height * ymax)
        x1, x2 = int(width * xmin), int(width * xmax)
        
        new_w, new_h = x2 - x1, y2 - y1
        
        # Use mp4v for broad compatibility
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (new_w, new_h))
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            cropped = frame[y1:y2, x1:x2]
            out.write(cropped)
            if progress_callback and frame_idx % 30 == 0:
                progress_callback(frame_idx / total_frames)
            frame_idx += 1
            
        cap.release()
        out.release()

    def parse_srt(self, srt_content):
        """Parses SRT content into list of dicts: [{'start', 'end', 'text'}]"""
        import re
        subtitles = []
        blocks = re.split(r'\n\s*\n', srt_content.strip())
        
        def to_sec(time_str):
            h, m, s = time_str.replace(',', '.').split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)

        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                try:
                    time_line = lines[1]
                    if ' --> ' not in time_line: continue
                    start_str, end_str = time_line.split(' --> ')
                    text = " ".join(lines[2:]).strip()
                    if text:
                        subtitles.append({
                            'start': to_sec(start_str),
                            'end': to_sec(end_str),
                            'text': text
                        })
                except: continue
        return subtitles

    def extract_subtitles_rapid(self, video_path, crop_region=None, progress_callback=None, subtitle_callback=None, min_text_len=2, min_duration=0.5, step=None):
        """
        Custom high-performance extraction with noise filtering and GPU support.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if crop_region:
            ymin, ymax, xmin, xmax = crop_region
            y1, y2 = int(height * ymin), int(height * ymax)
            x1, x2 = int(width * xmin), int(width * xmax)
        else:
            y1, y2, x1, x2 = int(height * 0.75), height, 0, width

        subtitles = []
        current_sub = None
        
        # If no manual step, check every ~0.15s (default)
        if step is None:
            processed_step = max(1, int(fps / 6)) 
        else:
            processed_step = step
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            if frame_idx % processed_step != 0:
                frame_idx += 1; continue
            
            # Progress update with optional preview frame
            preview_frame = None
            if progress_callback:
                if frame_idx % (processed_step * 5) == 0: # Update preview every 5 processed frames
                    preview_frame = frame.copy()
                progress_callback(frame_idx / total_frames, preview_frame)
            
            cropped = frame[max(0,y1):min(height,y2), max(0,x1):min(width,x2)]
            
            try:
                result, _ = self.rapid_engine(cropped)
            except:
                result = None
            
            detected_text = ""
            current_bbox = None
            if result:
                # result format is [ [[x1,y1],[x2,y1],[x2,y2],[x1,y2]], text, confidence ]
                filtered_results = [item for item in result if float(item[2]) > 0.4]
                texts = [item[1] for item in filtered_results]
                detected_text = " ".join(texts).strip()
                
                if filtered_results:
                    all_coords = []
                    for item in filtered_results:
                        all_coords.extend(item[0])
                    
                    xs = [c[0] for c in all_coords]
                    ys = [c[1] for c in all_coords]
                    current_bbox = [min(xs), min(ys), max(xs), max(ys)]

                    # If we have a preview frame, draw the green box on it
                    if preview_frame is not None:
                        bx1 = int(x1 + current_bbox[0])
                        by1 = int(y1 + current_bbox[1])
                        bx2 = int(x1 + current_bbox[2])
                        by2 = int(y1 + current_bbox[3])
                        cv2.rectangle(preview_frame, (bx1, by1), (bx2, by2), (0, 255, 0), 2)
                        # Also pass it back in the next progress call or update the current one
                        if progress_callback: progress_callback(frame_idx / total_frames, preview_frame)

                if len(detected_text) < min_text_len:
                    detected_text = ""
                    current_bbox = None

            current_time = frame_idx / fps
            end_time_estimate = (frame_idx + processed_step) / fps

            if detected_text:
                if current_sub and self.similar_text(current_sub['text'], detected_text):
                    current_sub['end'] = end_time_estimate
                    # Expand bbox if necessary to cover all variations of same text
                    if current_bbox:
                        if 'bbox' not in current_sub:
                            current_sub['bbox'] = current_bbox
                        else:
                            current_sub['bbox'] = [
                                min(current_sub['bbox'][0], current_bbox[0]),
                                min(current_sub['bbox'][1], current_bbox[1]),
                                max(current_sub['bbox'][2], current_bbox[2]),
                                max(current_sub['bbox'][3], current_bbox[3])
                            ]
                else:
                    if current_sub:
                        if (current_sub['end'] - current_sub['start']) >= min_duration:
                            subtitles.append(current_sub)
                            if subtitle_callback: subtitle_callback(subtitles.copy())
                    current_sub = {
                        'start': current_time, 
                        'end': end_time_estimate, 
                        'text': detected_text,
                        'bbox': current_bbox # Relative to crop!
                    }
            else:
                if current_sub:
                    if (current_sub['end'] - current_sub['start']) >= min_duration:
                        subtitles.append(current_sub)
                        if subtitle_callback: subtitle_callback(subtitles.copy())
                    current_sub = None
            frame_idx += 1

        if current_sub and (current_sub['end'] - current_sub['start']) >= min_duration:
            subtitles.append(current_sub)
            if subtitle_callback: subtitle_callback(subtitles.copy())

        cap.release()
        return subtitles

    def extract_subtitles(self, video_path, crop_region=None, progress_callback=None, subtitle_callback=None, min_text_len=2, min_duration=0.5, step=None):
        """Main entry point for extraction, dispatches to selected engine"""
        if self.engine == 'rapid':
            return self.extract_subtitles_rapid(video_path, crop_region, progress_callback, subtitle_callback, min_text_len, min_duration, step)
        
        # Legacy EasyOCR logic (does not support preview yet)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        
        if crop_region:
            ymin, ymax, xmin, xmax = crop_region
            y1, y2 = int(height * ymin), int(height * ymax)
            x1, x2 = int(width * xmin), int(width * xmax)
        else:
            y1, y2, x1, x2 = int(height * 0.75), height, 0, width

        subtitles = []
        current_sub = None
        step = max(1, int(fps / 5)) 
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            if frame_idx % step != 0:
                frame_idx += 1; continue
            
            if progress_callback: progress_callback(frame_idx / total_frames)
            cropped = frame[max(0,y1):min(height,y2), max(0,x1):min(width,x2)]
            
            try: result = self.reader.readtext(cropped)
            except: result = []
            
            detected_text = ""
            if result:
                texts = [item[1] for item in result if item[2] > 0.3]
                detected_text = " ".join(texts).strip()
                if len(detected_text) < min_text_len:
                    detected_text = ""

            current_time = frame_idx / fps
            end_time_estimate = (frame_idx + step) / fps

            if detected_text:
                if current_sub and self.similar_text(current_sub['text'], detected_text):
                    current_sub['end'] = end_time_estimate
                else:
                    if current_sub:
                        if (current_sub['end'] - current_sub['start']) >= min_duration:
                            subtitles.append(current_sub)
                            if subtitle_callback: subtitle_callback(subtitles.copy())
                    current_sub = {'start': current_time, 'end': end_time_estimate, 'text': detected_text}
            else:
                if current_sub:
                    if (current_sub['end'] - current_sub['start']) >= min_duration:
                        subtitles.append(current_sub)
                        if subtitle_callback: subtitle_callback(subtitles.copy())
                    current_sub = None
            frame_idx += 1

        if current_sub:
            subtitles.append(current_sub)
            if subtitle_callback: subtitle_callback(subtitles.copy())

        cap.release()
        return subtitles

    def _translate_batch_lm_studio(self, batch_texts, custom_prompt=None):
        """
        Translates a batch of texts using LM Studio API with the specific Tien Hiep prompt.
        """
        import requests
        
        system_prompt = custom_prompt if custom_prompt else (
            "Bạn là một đại tông sư ngôn ngữ chuyên dịch truyện Tiên hiệp/Cổ trang/Hệ thống. Nhiệm vụ: Dịch phụ đề sang tiếng Việt.\n\n"
            "YÊU CẦU TỐI THƯỢNG:\n\n"
            "HÁN VIỆT TOÀN DIỆN: Mọi tên riêng (Bạc Thanh, Phương Nguyên), cấp bậc (Lục chuyển, Thất chuyển), chiêu thức (Tiên đạo sát chiêu) phải dùng âm Hán Việt chuẩn.\n\n"
            "DỊCH THOÁT Ý & ĐẢO NGỮ PHÁP: - Tuyệt đối không dịch word-by-word.\n\n"
            "Phải đảo trật tự từ cho đúng tiếng Việt: Ví dụ dịch là \"Kỹ năng bị động\", \"Kỹ năng chủ động\" (Tuyệt đối KHÔNG để là B bị động kỹ, Chủ động kỹ).\n\n"
            "\"Đại biến tướng mạo\" phải dịch là \"Diện mạo thay đổi lớn\". Danh từ rồi mới đến tính từ.\n\n"
            "PHONG THÁI HÀO SẢNG: Câu văn phải trôi chảy, sắc bén như phim kiếm hiệp Kim Dung. Xưng hô đúng vế: Ta - Ngươi, Tiền bối - Vãn bối, Bản tọa.\n\n"
            "ĐỊNH DẠNG CỨNG: - CHỈ xuất ra duy nhất bản dịch.\n\n"
            "Cấm mọi loại dấu ngoặc giải thích.\n\n"
            "Giữ nguyên số thứ tự dòng (nếu có)."
        )
        
        user_content = "Dịch đoạn sau:\n"
        for i, text in enumerate(batch_texts):
            user_content += f"{i+1}. {text}\n"
            
        payload = {
            "model": "gemma", # Typically ignored by LM Studio unless multiple models loaded
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.3, # Lower temperature for more consistent formatting
            "stream": False
        }
        
        try:
            response = requests.post(f"{self.lm_studio_url}/chat/completions", json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Parse the content back into lines
            # Expecting lines like "1. [Translation]"
            translated_lines = []
            all_lines = [l.strip() for l in content.split('\n') if l.strip()]
            
            import re
            translations_map = {}
            for line in all_lines:
                match = re.match(r'^(\d+)[.)]\s*(.*)', line)
                if match:
                    idx = int(match.group(1))
                    text = match.group(2).strip()
                    translations_map[idx] = text
            
            # Reconstruct list maintaining order
            for i in range(1, len(batch_texts) + 1):
                if i in translations_map:
                    translated_lines.append(translations_map[i])
                else:
                    # Fallback: if we have roughly same number of lines as batch, use index
                    if len(all_lines) == len(batch_texts):
                        translated_lines.append(all_lines[i-1])
                    else:
                        # Final fallback: empty or original
                        translated_lines.append("") 
            
            return translated_lines
        except Exception as e:
            print(f"LM Studio Error: {e}")
            return None

    def _translate_batch_gemini(self, batch_texts, api_keys, custom_prompt=None):
        import requests
        import json
        import re

        system_prompt = custom_prompt if custom_prompt else (
            "Bạn là một đại tông sư ngôn ngữ chuyên dịch truyện Tiên hiệp. "
            "Dịch phụ đề sang tiếng Việt. Sử dụng âm Hán Việt chuẩn cho tên riêng và chiêu thức. "
            "Chỉ xuất ra bản dịch, giữ nguyên số thứ tự dòng."
        )
        
        user_content = "Dịch danh sách sau (giữ đúng số dòng):\n"
        for i, text in enumerate(batch_texts):
            user_content += f"{i+1}. {text}\n"

        for api_key in api_keys:
            # Cách viết an toàn nhất
            base_url = "https://generativelanguage.googleapis.com/v1beta"
            model_name = "gemini-2.5-flash"
            url = f"{base_url}/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "system_instruction": { # Đưa prompt vào hệ thống riêng biệt
                    "parts": [{"text": system_prompt}]
                },
                "contents": [{
                    "parts": [{"text": user_content}]
                }],
                "generationConfig": {
                    "temperature": 0.2, # Giảm xuống để dịch chính xác hơn
                    "topP": 0.8,
                },
                "safetySettings": [ # Tắt bộ lọc để dịch cảnh đánh nhau/tu tiên
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            }
            
            try:
                response = requests.post(url, json=payload, timeout=60)
                
                if response.status_code == 429:
                    continue
                
                response.raise_for_status()
                result = response.json()
                
                # Kiểm tra xem có bị block nội dung không
                if 'candidates' not in result or not result['candidates'][0].get('content'):
                    print(f"Key {api_key[:5]} bị từ chối do nội dung nhạy cảm.")
                    continue

                content = result['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # Xử lý parse linh hoạt hơn
                translations_map = {}
                lines = content.split('\n')
                for line in lines:
                    # Regex này bắt được cả "1. ", "1/ ", "1) "
                    match = re.search(r'^(\d+)[.)/]\s*(.*)', line)
                    if match:
                        idx = int(match.group(1))
                        translations_map[idx] = match.group(2).strip()

                # Tạo kết quả cuối cùng
                translated_lines = []
                for i in range(1, len(batch_texts) + 1):
                    # Nếu map có thì lấy, không thì lấy dòng thô, cuối cùng mới để trống
                    val = translations_map.get(i)
                    if val:
                        translated_lines.append(val)
                    elif i <= len(lines):
                        translated_lines.append(lines[i-1])
                    else:
                        translated_lines.append("")

                return translated_lines

            except Exception as e:
                print(f"Lỗi Key {api_key[:5]}: {e}")
                continue
                
        return None

    def translate_subtitles(self, subtitles, progress_callback=None, engine='google', lm_studio_url=None, custom_prompt=None, gemini_keys=None, gemini_batch_size=80):
        if lm_studio_url:
            self.lm_studio_url = lm_studio_url
            
        translated_subs = []
        total = len(subtitles)
        
        if engine == 'gemini' and gemini_keys:
            # Gemini Batch Translation
            for i in range(0, total, gemini_batch_size):
                batch = subtitles[i : i + gemini_batch_size]
                batch_texts = [sub['text'] for sub in batch]
                
                translated_batch = self._translate_batch_gemini(batch_texts, gemini_keys, custom_prompt=custom_prompt)
                
                # FALLBACK TO GOOGLE if Gemini fails
                if translated_batch is None:
                    print("Gemini failed for this batch. Falling back to Google Translate.")
                    translated_batch = []
                    for text in batch_texts:
                        try:
                            translated_batch.append(self.translator.translate(text))
                        except:
                            translated_batch.append(text)
                
                # Ensure we have the same number of lines
                if len(translated_batch) < len(batch):
                    translated_batch.extend([""] * (len(batch) - len(translated_batch)))
                
                for j, sub in enumerate(batch):
                    translated_subs.append({
                        'start': sub['start'],
                        'end': sub['end'],
                        'text': translated_batch[j] if translated_batch[j] else sub['text'],
                        'original': sub['text'],
                        'bbox': sub.get('bbox')
                    })
                
                if progress_callback:
                    progress_callback(min(1.0, (i + gemini_batch_size) / total))

        elif engine == 'lm-studio':
            batch_size = 10
            for i in range(0, total, batch_size):
                batch = subtitles[i : i + batch_size]
                batch_texts = [sub['text'] for sub in batch]
                
                translated_batch = self._translate_batch_lm_studio(batch_texts, custom_prompt=custom_prompt)
                
                if translated_batch is None:
                    translated_batch = batch_texts
                
                if len(translated_batch) < len(batch):
                    translated_batch.extend([""] * (len(batch) - len(translated_batch)))
                
                for j, sub in enumerate(batch):
                    translated_subs.append({
                        'start': sub['start'],
                        'end': sub['end'],
                        'text': translated_batch[j] if translated_batch[j] else sub['text'],
                        'original': sub['text'],
                        'bbox': sub.get('bbox')
                    })
                
                if progress_callback:
                    progress_callback(min(1.0, (i + batch_size) / total))
        else:
            # Original Google Translation Logic
            for i, sub in enumerate(subtitles):
                original = sub['text']
                if len(original) < 1: continue 

                try:
                    translated = self.translator.translate(original)
                except Exception as e:
                    translated = original 
                
                translated_subs.append({
                    'start': sub['start'],
                    'end': sub['end'],
                    'text': translated,
                    'original': original,
                    'bbox': sub.get('bbox')
                })
                
                if progress_callback:
                    progress_callback((i + 1) / total)
                    
        return translated_subs

    def save_to_srt(self, subtitles, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, sub in enumerate(subtitles):
                # Min duration 1.0s if too short
                duration = sub['end'] - sub['start']
                end_time = sub['end']
                if duration < 1.0:
                     end_time = sub['start'] + 1.2

                f.write(f"{i+1}\n")
                start = self.formatted_time(sub['start'])
                end = self.formatted_time(end_time)
                
                f.write(f"{start} --> {end}\n")
                f.write(f"{sub['text']}\n\n")
