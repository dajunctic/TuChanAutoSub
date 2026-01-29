"""
Auto-setup script for AutoViSub project.
Downloads necessary executables (ffmpeg, yt-dlp) if not present.
Run this after cloning the repository.
"""

import os
import sys
import requests
import zipfile
import io
import platform

def download_file(url, output_path, description="file"):
    """Download a file with progress indication"""
    print(f"📥 Downloading {description}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  Progress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n✅ Downloaded {description} successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Failed to download {description}: {e}")
        return False

def setup_ffmpeg():
    """Download and extract FFmpeg for Windows"""
    if os.path.exists("ffmpeg.exe") and os.path.exists("ffprobe.exe"):
        print("✅ FFmpeg already installed")
        return True
    
    print("\n📦 Setting up FFmpeg...")
    
    if platform.system() != "Windows":
        print("⚠️  This auto-installer is for Windows only.")
        print("   Please install ffmpeg manually for your OS:")
        print("   - Linux: sudo apt install ffmpeg")
        print("   - macOS: brew install ffmpeg")
        return False
    
    url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    
    try:
        print("📥 Downloading FFmpeg (this may take a minute, ~50MB)...")
        response = requests.get(url)
        response.raise_for_status()
        
        print("📂 Extracting FFmpeg...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for name in z.namelist():
                if name.lower().endswith("bin/ffmpeg.exe"):
                    with z.open(name) as source, open("ffmpeg.exe", "wb") as target:
                        target.write(source.read())
                    print("  ✅ Extracted ffmpeg.exe")
                elif name.lower().endswith("bin/ffprobe.exe"):
                    with z.open(name) as source, open("ffprobe.exe", "wb") as target:
                        target.write(source.read())
                    print("  ✅ Extracted ffprobe.exe")
        
        print("✅ FFmpeg installed successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to setup FFmpeg: {e}")
        print("   You can download it manually from: https://ffmpeg.org/download.html")
        return False

def setup_ytdlp():
    """Download yt-dlp executable"""
    exe_name = "yt-dlp.exe" if platform.system() == "Windows" else "yt-dlp"
    
    if os.path.exists(exe_name):
        print("✅ yt-dlp already installed")
        return True
    
    print("\n📦 Setting up yt-dlp...")
    
    if platform.system() == "Windows":
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    else:
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
    
    success = download_file(url, exe_name, "yt-dlp")
    
    if success and platform.system() != "Windows":
        # Make executable on Unix systems
        os.chmod(exe_name, 0o755)
    
    return success

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating project directories...")
    dirs = ["downloads", ".agent", ".agent/workflows"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  ✅ {d}")

def main():
    print("=" * 60)
    print("🚀 AutoViSub - Automatic Setup")
    print("=" * 60)
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Create directories
    create_directories()
    
    # Setup executables
    ffmpeg_ok = setup_ffmpeg()
    ytdlp_ok = setup_ytdlp()
    
    print("\n" + "=" * 60)
    print("📋 Setup Summary")
    print("=" * 60)
    print(f"FFmpeg:  {'✅ Ready' if ffmpeg_ok else '❌ Failed'}")
    print(f"yt-dlp:  {'✅ Ready' if ytdlp_ok else '❌ Failed'}")
    print()
    
    if ffmpeg_ok and ytdlp_ok:
        print("🎉 Setup completed successfully!")
        print()
        print("Next steps:")
        print("  1. Install Python dependencies: pip install -r requirements.txt")
        print("  2. Run the application: streamlit run main.py")
        return True
    else:
        print("⚠️  Setup completed with warnings.")
        print("   Some components may need manual installation.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
