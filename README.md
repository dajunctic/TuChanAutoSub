# AutoViSub - Bilibili Downloader & Subtitle Translator

This application allows you to:
1. Download videos from Bilibili.
2. Automatically extract hard-coded subtitles (OCR).
3. Translate subtitles to Vietnamese.
4. Export as `.srt`.

## Prerequisites

- **Python 3.8 - 3.11** (Recommended).  
  *Note: Python 3.12+ (and especially 3.14) may not support the `paddlepaddle` and `paddleocr` libraries required for subtitle extraction.*
- **System Dependencies**:
  - Visual C++ Redistributable (for OpenCV/Paddle setup on Windows).

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *If installation of `paddlepaddle` fails, you can still use the Downloader feature, but Extraction will be disabled.*

2. Run the App:
   ```bash
   streamlit run main.py
   ```

## Usage

1. Paste a Bilibili URL (e.g., `https://www.bilibili.com/video/BV...`).
2. Click **Download**.
3. Once downloaded, preview the video.
4. Click **Extract & Translate Subtitles**.
   - *First run might take longer to download OCR models.*
5. Download the generated `.srt` file.

## Troubleshooting

- **ImportError: libGL.so.1...**: On Linux, install `ffmpeg libsm6 libxext6`.
- **OCR Library not found**: Please downgrade Python to 3.10.
