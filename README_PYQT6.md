# AutoViSub Pro - PyQt6 Desktop Version

Modern desktop application for video subtitle extraction and translation, built with PyQt6.

## 🚀 Quick Start

### Running the PyQt6 Application

```bash
python main_qt.py
```

### Running the Streamlit Web Version (Original)

```bash
streamlit run main.py
```

## ✨ Features

### PyQt6 Desktop Version
- **Native Desktop Experience**: Fast, responsive native Windows application
- **Modern UI**: Discord-inspired dark theme with smooth animations
- **Project Management**: Save and load projects with all settings
- **Multi-threaded Operations**: Non-blocking UI during long operations
- **Interactive Region Selection**: Click and drag to select subtitle regions
- **Real-time Progress**: Live progress bars and status updates

### Core Features (Both Versions)
1. **📥 Video Download**
   - Download from Bilibili and other platforms
   - Real-time download progress
   - Auto-load as project

2. **🔍 OCR Subtitle Extraction**
   - Interactive region selection on video preview
   - Support for EasyOCR and RapidOCR engines
   - Multiple language support (Chinese, English, Japanese, Korean)
   - Real-time subtitle detection
   - Configurable extraction parameters

3. **🌐 Translation**
   - Multiple translation engines:
     - Google Translate (free)
     - Gemini API (batch processing)
     - LM Studio (local AI)
   - Custom translation prompts
   - Batch processing for efficiency

4. **🎬 Video Rendering**
   - Burn Vietnamese subtitles into video
   - FFmpeg-powered rendering
   - Progress tracking

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- FFmpeg (included in project)

### Install Dependencies

```bash
pip install -r requirements.txt
```

## 🎨 UI Comparison

### PyQt6 Desktop Version
- **Pros:**
  - ✅ Native desktop performance
  - ✅ No browser required
  - ✅ Better for video processing
  - ✅ More responsive UI
  - ✅ System tray integration (future)
  - ✅ Keyboard shortcuts

- **Cons:**
  - ❌ Requires installation
  - ❌ Platform-specific builds needed for distribution

### Streamlit Web Version
- **Pros:**
  - ✅ Easy to deploy
  - ✅ Cross-platform (runs in browser)
  - ✅ Easy to share
  - ✅ Quick prototyping

- **Cons:**
  - ❌ Requires web browser
  - ❌ Slower for heavy operations
  - ❌ Limited UI customization

## 🏗️ Project Structure

```
AutoSub/
├── main_qt.py              # PyQt6 application entry point
├── main.py                 # Streamlit application entry point
├── ui/                     # PyQt6 UI components
│   ├── main_window.py      # Main window with tabs
│   ├── download_tab.py     # Video download tab
│   ├── ocr_tab.py          # OCR extraction tab
│   ├── translate_tab.py    # Translation tab
│   ├── render_tab.py       # Video rendering tab
│   └── settings_tab.py     # Settings tab
├── downloader.py           # Video download logic
├── sub_processor.py        # OCR and translation logic
├── video_renderer.py       # Video rendering logic
├── projects/               # Project files and state
└── downloads/              # Downloaded videos
```

## 🎯 Usage Guide

### 1. Download a Video
1. Go to "📥 Download Video" tab
2. Paste Bilibili URL
3. Click "Start Download"
4. Load as project when complete

### 2. Extract Subtitles
1. Go to "🔍 Extract Subtitles" tab
2. Click "Load Frame" to preview video
3. Click and drag to select subtitle region
4. Configure OCR settings
5. Click "Start Extraction"

### 3. Translate Subtitles
1. Go to "🌐 Translate" tab
2. Click "Load from Project" to load extracted subtitles
3. Select translation engine
4. Configure API keys if needed (Gemini)
5. Click "Start Translation"

### 4. Render Video
1. Go to "🎬 Render Video" tab
2. Paths auto-filled from project
3. Click "Start Rendering"
4. Wait for completion

## ⚙️ Settings

Configure default settings in the "⚙️ Settings" tab:
- FFmpeg paths
- Default folders
- Default OCR engine and language
- Default translation engine
- UI preferences

## 🔧 Keyboard Shortcuts (PyQt6)

- `Ctrl+N` - New Project
- `Ctrl+O` - Open Project
- `Ctrl+S` - Save Project
- `Ctrl+Q` - Quit Application

## 🐛 Troubleshooting

### PyQt6 won't start
```bash
pip install --upgrade PyQt6 PyQt6-WebEngine
```

### OCR not working
Make sure you have installed:
```bash
pip install easyocr opencv-python
```

### Video rendering fails
Check FFmpeg is in the project folder:
- `ffmpeg.exe`
- `ffprobe.exe`

## 📝 License

MIT License - Feel free to use and modify!

## 🙏 Credits

- **PyQt6** - Desktop GUI framework
- **Streamlit** - Web UI framework
- **EasyOCR** - OCR engine
- **RapidOCR** - Fast OCR engine
- **FFmpeg** - Video processing
- **yt-dlp** - Video downloading

---

**Choose your version:**
- Use **PyQt6** (`main_qt.py`) for desktop power users
- Use **Streamlit** (`main.py`) for quick web-based usage
