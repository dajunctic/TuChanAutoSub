# AutoViSub Pro 🎬
**Bilibili Video Downloader & Advanced Subtitle Automation Suite**

AutoViSub Pro là giải pháp toàn diện để tải video từ Bilibili, tự động trích xuất phụ đề cứng (hard subtitles), dịch thuật bằng AI và lồng tiếng (VoiceOver) hoàn toàn tự động.

---

## ✨ Tính năng nổi bật

### 1. 📥 Tải Video & Quản lý Project
- **Bilibili Downloader:** Tải video chất lượng cao với thanh tiến trình thời gian thực.
- **Project Hub:** Tự động lưu trạng thái làm việc. Bạn có thể quay lại project cũ bất cứ lúc nào.
- **Auto-Load:** Ghi nhớ video đang xử lý gần nhất.

### 2. 🔍 Nhận dạng Phụ đề (OCR)
- **RapidVideOCR (Khuyên dùng):** Hiệu suất cực cao, hỗ trợ GPU (ONNX), độ chính xác tuyệt vời cho tiếng Hoa, Nhật, Hàn.
- **EasyOCR:** Engine linh hoạt cho các ngôn ngữ phổ thông.
- **Auto-Detect Region:** Tự động phân tích video để tìm vùng chứa phụ đề, không cần quét toàn bộ khung hình giúp tăng tốc 3-5 lần.
- **Real-time Preview:** Xem trực tiếp quá trình quét phụ đề ngay trên giao diện.

### 3. 🌐 Dịch thuật AI Thông minh
- **Gemini AI (Pro/Flash):** Dịch thuật ngữ cảnh siêu chuẩn, hỗ trợ dịch theo lô (batch) cực nhanh. Đặc biệt tối ưu cho truyện Tiên hiệp/Cổ trang với Prompt Hán Việt chuẩn.
- **LM Studio (Local LLM):** Sử dụng các mô hình như Gemma, Llama chạy offline hoàn toàn.
- **Google Translate:** Miễn phí và ổn định.

### 4. 🎙️ Lồng tiếng (VoiceOver) & Rendering
- **Đa dạng Voice:** Hỗ trợ Edge-TTS (Microsoft), gTTS và **VieNeu** (Model AI lồng tiếng Việt Nam cao cấp).
- **Auto-Speedup:** Tự động tăng tốc giọng đọc để khớp với thời gian xuất hiện của phụ đề nếu câu thoại quá dài.
- **Professional Rendering:** 
  - Ghi đè phụ đề tiếng Việt lên vùng phụ đề gốc với mask bo góc chuyên nghiệp.
  - Hỗ trợ chèn Logo cá nhân (Watermark) tùy chỉnh vị trí/kích thước.
  - Mix âm thanh nền (background music) và giọng lồng tiếng thông minh.

---

## 🚀 Cài đặt nhanh

### Bước 1: Clone repository
```bash
git clone https://github.com/your-repo/AutoViSub.git
cd AutoViSub
```

### Bước 2: Chạy script Setup tự động
```bash
python setup.py
```
*Script này sẽ tải FFmpeg, yt-dlp và tạo các thư mục cần thiết.*

### Bước 3: Cài đặt thư viện Python
```bash
pip install -r requirements.txt
```
*Lưu ý: Nếu bạn có GPU NVIDIA, hãy đảm bảo đã cài CUDA để RapidOCR và Torch chạy nhanh nhất.*

### Bước 4: Khởi chạy ứng dụng
```bash
streamlit run main.py
```

---

## 🛠️ Quy trình sử dụng (Workflow)

1. **📁 Project Selection:** Dán link Bilibili hoặc chọn video có sẵn trong máy.
2. **🔍 Subtitle Extraction:** Chọn ngôn ngữ gốc và chạy OCR. Bạn có thể để hệ thống tự phát hiện vùng hoặc vẽ thủ công.
3. **🌐 Translation:** Chọn Engine dịch (Google/Gemini). Nếu dùng Gemini, hãy nhập API Key trong phần Global Settings.
4. **🎙️ VoiceOver:** Chọn giọng đọc và phong cách. Hệ thống sẽ tự tạo file audio cho từng câu.
5. **🎬 Video Rendering:** Tùy chỉnh font chữ, logo và xuất video cuối cùng.

> 💡 **Mẹo:** Sử dụng nút **"🚀 START FULL AUTO MODE"** để hệ thống tự động chạy từ đầu đến cuối mà không cần can thiệp.

---

## 📦 Yêu cầu hệ thống
- **OS:** Windows (do có sử dụng ffmpeg.exe đi kèm)
- **Python:** 3.10+
- **GPU:** NVIDIA GPU (khuyên dùng để chạy RapidOCR & Gemini Translation Batch)
- **Bộ nhớ:** Trống ít nhất 5GB cho các model AI

---

## 🤝 Đóng góp & Bản quyền
Project được phát triển bởi **TuChan**. Mọi ý kiến đóng góp vui lòng mở Issue trên GitHub.

**License:** MIT

---
**Made with ❤️ for the Subbing Community**
