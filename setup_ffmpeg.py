import os
import zipfile
import io
import requests

def install_ffmpeg():
    # URL for yt-dlp recommended build
    url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    print(f"Dang tai FFmpeg tu {url}...")
    print("Vui long doi mot chut (khoang 30-50MB)...")
    
    try:
        r = requests.get(url)
        r.raise_for_status()
        print("Tai xong. Dang giai nen...")
        
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            # The zip structure is usually ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe
            for name in z.namelist():
                # Extract ffmpeg.exe and ffprobe.exe to current root
                if name.lower().endswith("bin/ffmpeg.exe"):
                    print(f"Extracting ffmpeg.exe...")
                    with z.open(name) as source, open("ffmpeg.exe", "wb") as target:
                        target.write(source.read())
                elif name.lower().endswith("bin/ffprobe.exe"):
                    print(f"Extracting ffprobe.exe...")
                    with z.open(name) as source, open("ffprobe.exe", "wb") as target:
                        target.write(source.read())
                        
        print("Da cai dat FFmpeg thanh cong vao thu muc du an!")
        print("Bay gio ban co the tai video ma khong gap loi merge.")
        
    except Exception as e:
        print(f"Loi khi cai dat FFmpeg: {e}")
        print("Ban co the can tai thu cong FFmpeg va copy ffmpeg.exe vao thu muc nay.")

if __name__ == "__main__":
    if os.path.exists("ffmpeg.exe"):
        print("ffmpeg.exe da ton tai. Bo qua.")
    else:
        install_ffmpeg()
