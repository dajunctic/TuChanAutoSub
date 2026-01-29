# AutoViSub 📺

**Bilibili Video Downloader & Automatic Subtitle Extractor/Translator**

Tự động tải video từ Bilibili, trích xuất phụ đề cứng (hard subtitles) bằng OCR, dịch sang tiếng Việt và xuất file SRT.

---

## ✨ Tính năng

- 🎬 **Tải video từ Bilibili** với thanh tiến trình real-time
- 🤖 **Tự động phát hiện vùng phụ đề** bằng AI (phân tích frame differences)
- 📝 **OCR thông minh** sử dụng EasyOCR với hỗ trợ đa ngôn ngữ
- 🌐 **Dịch tự động** sang tiếng Việt
- 📊 **Hiển thị real-time** kết quả OCR trong bảng
- 💾 **Xuất file SRT** chuẩn để sử dụng với video player
- 🎨 **Giao diện web đẹp** với Streamlit

---

## 🚀 Cài đặt nhanh

### Bước 1: Clone repository

```bash
git clone <repository-url>
cd AutoSub
```

### Bước 2: Chạy setup tự động

```bash
python setup.py
```

Script này sẽ tự động:
- ✅ Tải FFmpeg (cho xử lý video)
- ✅ Tải yt-dlp (cho download Bilibili)
- ✅ Tạo các thư mục cần thiết

### Bước 3: Cài đặt thư viện Python

```bash
pip install -r requirements.txt
```

**Lưu ý:** Quá trình cài đặt có thể mất 5-10 phút do cần tải PyTorch và EasyOCR.

### Bước 4: Chạy ứng dụng

```bash
streamlit run main.py
```

Ứng dụng sẽ mở tại: `http://localhost:8501`

---

## 📋 Yêu cầu hệ thống

- **Python:** 3.8 - 3.11 (khuyến nghị 3.10)
- **RAM:** Tối thiểu 4GB (khuyến nghị 8GB+)
- **Disk:** ~3GB cho thư viện
- **GPU:** Không bắt buộc, nhưng tăng tốc OCR đáng kể nếu có CUDA

---

## 🎯 Hướng dẫn sử dụng

### 1. Tải video

1. Dán URL video Bilibili vào ô input
2. Bấm **"Download Video"**
3. Đợi tải xong (có thanh tiến trình)

### 2. Trích xuất phụ đề (2 cách)

#### Cách 1: Tự động (Khuyến nghị) ⭐

1. Bấm nút **"🚀 Auto-Detect & Extract Subtitles"**
2. Hệ thống sẽ:
   - Tự động phát hiện vùng phụ đề
   - Chạy OCR ngay lập tức
   - Hiển thị kết quả real-time trong bảng

#### Cách 2: Thủ công

1. Mở **"Manual Adjustment"**
2. Vẽ khung chọn vùng phụ đề trên ảnh
3. Bấm **"Extract & Translate Subtitles"**

### 3. Dịch và xuất file

1. Sau khi OCR xong, bấm **"🌐 Translate to Vietnamese"**
2. Xem bảng dịch
3. Bấm **"📥 Download SRT File"** để tải file phụ đề

---

## 📁 Cấu trúc project

```
AutoSub/
├── main.py                    # Ứng dụng Streamlit chính
├── downloader.py              # Module tải video
├── sub_processor.py           # Module OCR và dịch
├── auto_detect_region.py      # Module tự động phát hiện vùng phụ đề
├── setup.py                   # Script cài đặt tự động
├── setup_ffmpeg.py            # Script cài FFmpeg (legacy)
├── requirements.txt           # Danh sách thư viện Python
├── README.md                  # File này
├── downloads/                 # Thư mục chứa video đã tải
└── .gitignore                 # Git ignore file
```

---

## 🛠️ Xử lý sự cố

### Lỗi: "FFmpeg not found"

```bash
python setup.py
```

Hoặc tải thủ công từ [ffmpeg.org](https://ffmpeg.org/download.html) và đặt `ffmpeg.exe` vào thư mục gốc.

### Lỗi: "CUDA out of memory"

Giảm số lượng frame xử lý hoặc tắt GPU:
- Mở `sub_processor.py`
- Sửa `self.reader = easyocr.Reader(langs, gpu=False)`

### Lỗi: "No subtitles detected"

- Kiểm tra video có phụ đề cứng không (không phải soft subs)
- Thử điều chỉnh vùng crop thủ công
- Kiểm tra ngôn ngữ đã chọn đúng chưa

### OCR chậm

- Sử dụng GPU nếu có (cài CUDA + cuDNN)
- Giảm độ phân giải video
- Tăng `step` trong `sub_processor.py` (line 84)

---

## 🔧 Cấu hình nâng cao

### Thay đổi ngôn ngữ OCR

Mở sidebar → chọn **Source Language**

### Tùy chỉnh vùng phụ đề mặc định

Sửa file `sub_processor.py`, dòng 70:

```python
y1 = int(height * 0.75)  # 0.75 = 75% từ trên xuống
```

### Thay đổi ngưỡng confidence OCR

Sửa file `sub_processor.py`, dòng 113:

```python
texts = [item[1] for item in result if item[2] > 0.4]  # 0.4 = 40%
```

---

## 📦 Thư viện sử dụng

| Thư viện | Mục đích |
|----------|----------|
| `streamlit` | Giao diện web |
| `yt-dlp` | Tải video Bilibili |
| `opencv-python` | Xử lý video/hình ảnh |
| `easyocr` | Nhận dạng ký tự quang học |
| `torch` | Deep learning framework |
| `deep-translator` | Dịch thuật |
| `scipy` | Xử lý tín hiệu (auto-detect) |
| `pandas` | Hiển thị bảng dữ liệu |

---

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

---

## 📝 License

MIT License - Xem file `LICENSE` để biết thêm chi tiết.

---

## 🙏 Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video downloader
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - OCR engine
- [Streamlit](https://streamlit.io/) - Web framework
- [FFmpeg](https://ffmpeg.org/) - Video processing

---

## 📧 Liên hệ

Nếu có vấn đề hoặc câu hỏi, vui lòng tạo Issue trên GitHub.

---

**Made with ❤️ for Vietnamese subtitle enthusiasts**
