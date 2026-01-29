import subprocess
import os
import sys

def download_bilibili_video(url: str, output_path: str = "downloads", progress_callback=None):
    """
    Tải video từ URL Bilibili bằng yt-dlp library (hoặc fallback sang exe).
    Args:
        url: URL video.
        output_path: Thư mục lưu.
        progress_callback: Hàm nhận giá trị float (0-100) để update progress bar.
    Returns:
        Đường dẫn file đã tải (str) hoặc None nếu lỗi.
    """
    print(f"Bắt đầu tải video từ: {url}")
    os.makedirs(output_path, exist_ok=True)
    
    # Define fallback executable path just in case
    yt_dlp_executable = './yt-dlp'
    if sys.platform == "win32":
        yt_dlp_executable += '.exe'
        
    # Determine absolute path to ffmpeg for yt-dlp
    ffmpeg_path = os.path.abspath("ffmpeg.exe") if os.path.exists("ffmpeg.exe") else None

    try:
        import yt_dlp
        
        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # Prioritize MP4
            'merge_output_format': 'mp4',
            # Explicitly tell yt-dlp where ffmpeg is
            'ffmpeg_location': os.path.dirname(ffmpeg_path) if ffmpeg_path else None
        }

        if progress_callback:
            def my_hook(d):
                if d['status'] == 'downloading':
                    try:
                        p = d.get('_percent_str', '0%').replace('%','')
                        progress_callback(float(p))
                    except:
                        pass
                elif d['status'] == 'finished':
                    progress_callback(100.0)

            ydl_opts['progress_hooks'] = [my_hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ydl.params['ffmpeg_location'] = ... # redundancy check
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Fix extension if merged
            if not filename.lower().endswith('.mp4'):
                filename = os.path.splitext(filename)[0] + '.mp4'
            
            return filename

    except ImportError:
        print("yt_dlp library not found, falling back to subprocess.")
        # Subprocess fallback (no real-time progress bar support implemented here easily)
        command = [
            yt_dlp_executable,
            url,
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '-o',
            os.path.join(output_path, '%(title)s.%(ext)s')
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
            
            # Find latest file
            files = [os.path.join(output_path, f) for f in os.listdir(output_path)]
            if not files:
                return None
            latest_file = max(files, key=os.path.getctime)
            if progress_callback: progress_callback(100.0)
            return latest_file
            
        except subprocess.CalledProcessError as e:
            print(f"Lỗi từ yt-dlp (subprocess):\n{e.stderr}")
            return None
            
    except Exception as e:
        print(f"Lỗi: {e}")
        return None

if __name__ == '__main__':
    bilibili_url = "https://www.bilibili.com/video/BV1jZ4y1c7v9/"
    res = download_bilibili_video(bilibili_url)
    print("Downloaded:", res)