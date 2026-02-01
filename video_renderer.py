import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

class VideoRenderer:
    """
    Render Vietnamese subtitles onto video by:
    1. Covering original subtitle area with black rectangle
    2. Drawing Vietnamese text on top
    """
    
    def __init__(self):
        # Try to load a Vietnamese-compatible font
        self.font_path = self._find_font()
        
    def _find_font(self):
        """Find a suitable font for Vietnamese text"""
        # Common font paths on Windows
        possible_fonts = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/times.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/seguisb.ttf",  # Segoe UI Semibold - good for Vietnamese
        ]
        
        for font in possible_fonts:
            if os.path.exists(font):
                return font
        
        # Fallback to default
        return None

    def generate_logo_preview(self, video_path, logo_path, position, size_pct, x_offset, y_offset):
        """Generate a single frame preview of the logo overlay"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): return None
        
        ret, frame = cap.read()
        cap.release()
        if not ret: return None
        
        if not logo_path or not os.path.exists(logo_path): return frame
        
        logo_img = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
        if logo_img is None: return frame
        
        # Resize logo
        width = frame.shape[1]
        target_w = int(width * size_pct)
        h, w = logo_img.shape[:2]
        target_h = int(h * (target_w / w))
        logo_img = cv2.resize(logo_img, (target_w, target_h), interpolation=cv2.INTER_AREA)
        
        return self._overlay_logo(frame, logo_img, position, x_offset, y_offset)
    
    def render_video_with_subtitles(
        self, 
        video_path, 
        subtitles, 
        output_path, 
        subtitle_region=None,
        font_size=32,
        progress_callback=None,
        voiceover_audio=None,
        original_volume=0.3,
        logo_path=None,
        logo_position="Top-Left",
        logo_size=0.15,
        logo_x=20,
        logo_y=20
    ):
        """
        Render video with Vietnamese subtitles burned in and optional logo.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Cannot open video file")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Pre-load logo if exists
        logo_img = None
        if logo_path and os.path.exists(logo_path):
            logo_img = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
            if logo_img is not None:
                # Resize logo based on size percentage
                target_w = int(width * logo_size)
                h, w = logo_img.shape[:2]
                target_h = int(h * (target_w / w))
                logo_img = cv2.resize(logo_img, (target_w, target_h), interpolation=cv2.INTER_AREA)

        # Calculate subtitle region in pixels
        if subtitle_region:
            ymin, ymax, xmin, xmax = subtitle_region
            y1 = int(height * ymin)
            y2 = int(height * ymax)
            x1 = int(width * xmin)
            x2 = int(width * xmax)
        else:
            y1, y2, x1, x2 = int(height * 0.75), height, 0, width
        
        # Setup temporary video writer
        temp_output = output_path + ".temp.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))
        
        # Create subtitle time index
        subtitle_index = self._create_subtitle_index(subtitles, fps, total_frames)
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            # 1. Draw Subtitles
            sub_data = subtitle_index.get(frame_idx)
            if sub_data:
                current_text = sub_data['text']
                current_bbox = sub_data['bbox']
                bx1, by1, bx2, by2 = x1, y1, x2, y2
                if current_bbox:
                    bx1 = int(x1 + current_bbox[0])
                    by1 = int(y1 + current_bbox[1])
                    bx2 = int(x1 + current_bbox[2])
                    by2 = int(y1 + current_bbox[3])
                
                frame = self._draw_text_on_frame_v2(frame, current_text, (bx1, by1, bx2, by2), font_size)
            
            # 2. Overlay Logo
            if logo_img is not None:
                frame = self._overlay_logo(frame, logo_img, logo_position, logo_x, logo_y)
            
            out.write(frame)
            frame_idx += 1
            if progress_callback and frame_idx % 30 == 0:
                progress_callback(frame_idx / total_frames)
        
        cap.release()
        out.release()

        # Step 2: Convert to H.264 and MIX AUDIO using ffmpeg
        ffmpeg_exe = os.path.join(os.getcwd(), "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            import subprocess
            if os.path.exists(output_path): os.remove(output_path)
            
            # Base command
            cmd = [ffmpeg_exe, "-y", "-i", temp_output]
            
            if voiceover_audio and os.path.exists(voiceover_audio):
                # MIX: Original background (ducked) + VoiceOver
                # Input 1: Video (temp), Input 2: Original Video (for background audio), Input 3: VoiceOver
                cmd.extend(["-i", video_path, "-i", voiceover_audio])
                # Filter to mix audio: original audio at user-defined volume, voiceover at 1.0
                cmd.extend([
                    "-filter_complex", 
                    f"[1:a]volume={original_volume}[bg];[2:a]volume=1.0[vo];[bg][vo]amix=inputs=2:duration=first[a]",
                    "-map", "0:v:0", "-map", "[a]"
                ])
            else:
                # Just take original audio, apply volume if not 1.0
                if original_volume != 1.0:
                    cmd.extend(["-i", video_path, "-filter_complex", f"[1:a]volume={original_volume}[a]", "-map", "0:v:0", "-map", "[a]"])
                else:
                    cmd.extend(["-i", video_path, "-map", "0:v:0", "-map", "1:a:0?"])

            cmd.extend([
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
                "-c:a", "aac", "-shortest",
                output_path
            ])

            try:
                subprocess.run(cmd, check=True, capture_output=True)
                if os.path.exists(temp_output): os.remove(temp_output)
            except Exception as e:
                print(f"FFMPEG Error: {e}")
                os.rename(temp_output, output_path)
        else:
            if os.path.exists(output_path): os.remove(output_path)
            os.rename(temp_output, output_path)
        
        if progress_callback: progress_callback(1.0)
        return output_path

    def _overlay_logo(self, frame, logo, position, offset_x, offset_y):
        """Overlay logo on frame with transparency support if available"""
        fh, fw = frame.shape[:2]
        lh, lw = logo.shape[:2]
        
        # Determine top-left corner of logo
        if position == "Top-Left":
            x, y = offset_x, offset_y
        else: # Top-Right
            x, y = fw - lw - offset_x, offset_y
            
        # Bounds check
        if x < 0: x = 0
        if y < 0: y = 0
        if x + lw > fw: lw = fw - x
        if y + lh > fh: lh = fh - y
        
        if lw <= 0 or lh <= 0: return frame
        
        logo_part = logo[:lh, :lw]
        
        # Handle transparency (Alpha channel)
        if logo_part.shape[2] == 4:
            alpha = logo_part[:, :, 3] / 255.0
            alpha = np.expand_dims(alpha, axis=2)
            for c in range(0, 3):
                frame[y:y+lh, x:x+lw, c] = (1.0 - alpha[:, :, 0]) * frame[y:y+lh, x:x+lw, c] + alpha[:, :, 0] * logo_part[:, :, c]
        else:
            frame[y:y+lh, x:x+lw] = logo_part[:, :, :3]
            
        return frame
    
    def _create_subtitle_index(self, subtitles, fps, total_frames):
        """
        Create a frame-to-subtitle mapping for fast lookup.
        Now includes bbox if available.
        """
        index = {}
        
        for sub in subtitles:
            # Simple constant 2-frame buffer to prevent flicker
            start_frame = max(0, int(round(sub['start'] * fps)) - 2)
            end_frame = int(round(sub['end'] * fps)) + 2
            
            data = {
                'text': sub['text'],
                'bbox': sub.get('bbox')
            }
            
            for f in range(start_frame, end_frame + 1):
                if 0 <= f < total_frames:
                    index[f] = data
        
        return index
    
    def _draw_text_on_frame_v2(self, frame, text, target_bbox, font_size):
        """
        Draws text centered within a black box. 
        The box covers the target_bbox but expands horizontally if 'text' is wider.
        """
        import textwrap
        tx1, ty1, tx2, ty2 = target_bbox
        target_w = tx2 - tx1
        target_h = ty2 - ty1
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)
        draw = ImageDraw.Draw(pil_img)
        
        # Load font
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, font_size)
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            
        # Wrapping logic: prefer wrapping if text is extremely long, 
        # but the primary goal is to center relative to original area
        # For video subs, we typically want 1-2 lines.
        # We increase chars_per_line to allow horizontal expansion as requested.
        chars_per_line = 60 # Allow more width before wrapping
        lines = textwrap.wrap(text, width=chars_per_line)
        
        line_heights = []
        line_widths = []
        for line in lines:
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_widths.append(bbox[2] - bbox[0])
                line_heights.append(bbox[3] - bbox[1])
            except:
                line_widths.append(draw.textsize(line, font=font)[0])
                line_heights.append(draw.textsize(line, font=font)[1])
        
        total_text_height = sum(line_heights) + (len(lines) - 1) * 8
        max_text_width = max(line_widths) if line_widths else 0
        
        # Determine final box width: at least target_w, but larger if text needs it
        # Increased horizontal padding to 60px (30px each side) for aesthetics
        padding_x = 40
        padding_y = 15
        final_w = max(target_w + padding_x, max_text_width + padding_x * 1.5) 
        final_h = max(target_h + padding_y, total_text_height + padding_y * 1.5)
        
        # Calculate box coordinates (centered on the target_bbox's center)
        center_x = (tx1 + tx2) // 2
        center_y = (ty1 + ty2) // 2
        
        box_x1 = center_x - int(final_w // 2)
        box_y1 = center_y - int(final_h // 2)
        box_x2 = box_x1 + int(final_w)
        box_y2 = box_y1 + int(final_h)
        
        # Draw the unified black mask with ROUNDED CORNERS (Premium look)
        radius = 15 # Corner radius
        draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=radius, fill=(0, 0, 0))

        # Draw text lines centered in the box
        # Correctly center text block vertically within the rounded box
        current_y = box_y1 + (final_h - total_text_height) // 2
        for i, line in enumerate(lines):
            line_w = line_widths[i]
            line_x = box_x1 + (final_w - line_w) // 2
            
            # Subtle outline
            for adj in [-1, 1]:
                draw.text((line_x + adj, current_y), line, font=font, fill=(0,0,0, 180))
                draw.text((line_x, current_y + adj), line, font=font, fill=(0,0,0, 180))
                
            draw.text((line_x, current_y), line, font=font, fill=(255, 255, 255))
            current_y += line_heights[i] + 8

        # Convert back to BGR
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def render_video_with_vietnamese_subs(
    video_path, 
    subtitles, 
    output_path, 
    subtitle_region=None,
    font_size=32,
    progress_callback=None,
    voiceover_audio=None,
    original_volume=0.3,
    logo_path=None,
    logo_position="Top-Left",
    logo_size=0.15,
    logo_x=20,
    logo_y=20
):
    """
    Convenience function to render video with Vietnamese subtitles and optional voiceover/logo.
    """
    renderer = VideoRenderer()
    return renderer.render_video_with_subtitles(
        video_path,
        subtitles,
        output_path,
        subtitle_region,
        font_size,
        progress_callback,
        voiceover_audio,
        original_volume,
        logo_path,
        logo_position,
        logo_size,
        logo_x,
        logo_y
    )
