# Video giới thiệu ShiftLens

- **File xem/chia sẻ:** `ShiftLens_intro_2min.mp4` — 2 phút 03 giây, 1280×720, H.264/AAC.
- **Phụ đề rời:** `ShiftLens_intro_vi.srt` (phụ đề cũng được nhúng trong MP4).
- **Kịch bản:** `scenes.json`, gồm 10 cảnh và lời thuyết minh tiếng Việt.

Video dùng đồ họa và giao diện **minh họa theo luồng trong mã nguồn**. Điểm số 85/100 ở cảnh kết quả là ví dụ minh họa. Đây không phải bản ghi ứng dụng chạy trên thiết bị hay bằng chứng Gemini Live đang hoạt động.

Để dựng lại trên máy Windows có Chrome, cài `ffmpeg-static` và `puppeteer-core` vào `.video-build` bằng npm, cài `gTTS` vào `.video-build/py` bằng pip, rồi chạy lần lượt `generate_voice.py`, `render.js`, `build_video.py`. Tạo giọng đọc cần kết nối dịch vụ TTS.
