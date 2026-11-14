# ShiftLens — AI Workforce Training & Simulation Platform

> **Codex Community Hackathon Hanoi (14/11/2026)**  
> Biến quy trình chuẩn (SOP) thành bài tập mô phỏng tương tác trên thiết bị di động thật với khách hàng AI và đánh giá năng lực có bằng chứng trích dẫn thực tế.

---

## 1. Giới thiệu & Định vị cốt lõi

**ShiftLens** không phải là một chatbot tra cứu tài liệu thông thường. Sản phẩm giải quyết bài toán cốt lõi của các chuỗi F&B và bán lẻ (bắt đầu từ các quán cà phê độc lập 5–20 nhân viên tại Hà Nội):
1. **Quản lý (Buyer)**: Thiết lập quy trình chuẩn (SOP Steps) và bộ tiêu chí đánh giá (Rubric tổng 100 điểm) một cách trực quan trên giao diện No-code (Appsmith).
2. **Nhân viên (User)**: Mở ứng dụng di động Android độc lập, thực hành nhập vai (roleplay) với khách hàng AI khó tính trong các tình huống thực tế (kèm phát giọng nói TTS).
3. **Đánh giá có minh chứng (Evidence-based)**: Server đối soát câu chữ nguyên văn (`exact_quote`) để chấm điểm xác định, tuyệt đối ngăn chặn AI ảo giác bằng chứng và phát hiện lỗi nghiêm trọng (`critical_failure`).

---

## 2. Kiến trúc Hệ thống (System Architecture)

```
[Quản lý: Appsmith UI]          [Nhân viên: Android Expo APK]
        │ REST + Bearer                    │ REST + Bearer
        └─────────────────┬────────────────┘
                          ▼
              [FastAPI Backend Server]
           (Auth JWT, Tenant Isolation, 
            SOP Versioning, Session Pin)
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
[Cơ sở dữ liệu]                 [AI Gateway: Google GenAI]
• SQLite (Local / Test)          • Module 1: AI Compiler (Tạo tình huống)
• Supabase PostgreSQL (Prod)     • Module 2: Simulator (Khách hàng AI)
                                  • Module 3: Evaluator (Trích xuất quote)
                                           │
                                           ▼
                                [Deterministic Scoring Engine]
                                 • Đối soát exact_quote server-side
                                 • Tính điểm Rubric (Tổng 100đ)
                                 • Kiểm tra vi phạm chí tử (Critical)
```

### Nguyên tắc ranh giới tin cậy (Trust Boundary)
- **LLM chỉ đóng vai trò đề xuất văn bản**: Kịch bản bối cảnh, câu nói của khách, đoạn trích dẫn quote và nhận xét.
- **Server là nguồn sự thật duy nhất**: Quyền hạn, cách ly Tenant, tính điểm xác định, kiểm tra tính xác thực của quote trong transcript và quản lý phiên bản SOP bất biến (`immutable`).

---

## 3. Cấu trúc Thư mục

```
Codex_Hackerthon/
├── .agents/                          # Bộ kỹ năng & Luật dự án chuẩn hóa cho AI
│   ├── rules/
│   │   └── project-rules.md          # Quy chuẩn kỹ thuật & bảo mật
│   └── skills/
│       ├── shiftlens-architecture/   # Kiến trúc & luồng dữ liệu E2E
│       ├── backend-development/      # Quy chuẩn FastAPI, Schemas, AI modes
│       ├── mobile-android-expo/      # Hướng dẫn React Native Android & EAS build APK
│       └── evaluation-governance/    # Động cơ tính điểm xác định & chống ảo giác
├── AGENTS.md                         # Hướng dẫn nhanh cho Agent AI / Collaborator
├── GEMINI.md                         # Chỉ dẫn môi trường Gemini / Antigravity
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── main.py                   # Điểm khởi chạy FastAPI & Health Check
│   │   ├── config.py                 # Cấu hình môi trường & AI Mode
│   │   ├── database.py               # Kết nối SQLAlchemy
│   │   ├── models.py                 # Entities: Tenant, Account, SOP, Session, Turn...
│   │   ├── schemas.py                # Pydantic Schemas
│   │   ├── auth.py                   # JWT Token & Xác thực Tenant
│   │   ├── seed.py                   # Khởi tạo dữ liệu mẫu (Café A & Café B)
│   │   ├── routers/                  # Auth, SOPs, Admin, Training endpoints
│   │   └── services/                 # AI Service (Live/Stub), Scoring Engine, SOP Service
│   ├── tests/                        # Bộ kiểm thử Pytest tự động
│   └── requirements.txt
├── mobile/                           # Ứng dụng Di động Android (React Native Expo)
│   ├── src/
│   │   ├── api/                      # Client API & TypeScript types
│   │   ├── context/                  # Quản lý Auth & Endpoint động
│   │   └── screens/                  # LoginScreen, SopListScreen, SimulationScreen, ResultScreen
│   ├── app.json                      # Cấu hình Android Package & Theme
│   ├── eas.json                      # Cấu hình EAS Build ra file .apk độc lập
│   └── package.json
├── admin-appsmith/                   # Hướng dẫn cấu hình No-code UI cho Quản lý
└── scripts/                          # Scripts chạy thử E2E và kiểm thử tự động
```

---

## 4. Hướng dẫn Khởi chạy Nhanh

### 4.1. Khởi chạy Backend (FastAPI)
```bash
cd backend

# Cài đặt thư viện:
pip install -r requirements.txt

# Khởi tạo dữ liệu mẫu (Café A & B):
python -m app.seed

# Chạy kiểm thử tự động (11/11 tests pass):
python -m pytest -v

# Khởi chạy máy chủ:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Tài liệu API tương tác (Swagger UI): `http://localhost:8000/docs`
- Kiểm tra trạng thái AI: `http://localhost:8000/v1/health`

### 4.2. Khởi chạy Ứng dụng Mobile Android (Expo & Android Studio)
```bash
cd mobile

# Cài đặt thư viện:
npm install

# Tuỳ chọn đặt URL Backend mặc định qua biến môi trường (xem mobile/.env.example):
# EXPO_PUBLIC_API_URL=http://192.168.1.xxx:8000

# Chạy ở chế độ phát triển:
npx expo start
```

#### Cách 1: Mở và Build trực tiếp bằng Android Studio (Local Gradle — Khuyên dùng)
Thư mục native `mobile/android/` đã được sinh sẵn bằng `npx expo prebuild --platform android` và lưu trong repository (kèm cấu hình `android:usesCleartextTraffic="true"` để gọi LAN HTTP trên điện thoại thật):
1. Mở **Android Studio** → **Open** → chọn thư mục `mobile/android`.
2. Chờ **Gradle Sync** hoàn tất.
3. Build APK từ Android Studio hoặc chạy lệnh Gradle từ `mobile/android`:
   - Bản Debug: `./gradlew :app:assembleDebug` → File APK tại `mobile/android/app/build/outputs/apk/debug/app-debug.apk`
   - Bản Release độc lập (nhúng sẵn JS bundle, không cần Metro): `./gradlew :app:assembleRelease` → File APK tại `mobile/android/app/build/outputs/apk/release/app-release.apk`
4. Lưu ý kết nối mạng trên điện thoại thật: Dùng địa chỉ IP LAN của máy chạy FastAPI (ví dụ `http://192.168.1.xxx:8000`) hoặc HTTPS tunnel. Có thể sửa trực tiếp tại ô **Server URL** ngay trên màn hình Đăng nhập (tự động lưu qua `AsyncStorage` kể cả sau khi Force-Stop).

#### Cách 2: Build APK qua đám mây (EAS Build)
```bash
cd mobile
eas build -p android --profile preview
```

---

## 5. Dữ liệu Mẫu để Demo (Seeded Fixtures)

Mật khẩu chung cho tất cả tài khoản mẫu: **`ShiftLens@2026`**

| Cửa hàng (Tenant) | Vai trò | Tài khoản | Đặc thù chính sách |
| :--- | :--- | :--- | :--- |
| **Café Sữa Đá Cầu Giấy (Café A)** | Quản lý | `manager_a` | Nghiêm ngặt: Tuyệt đối không tự ý hoàn tiền khi chưa xin phép quản lý. |
| **Café Sữa Đá Cầu Giấy (Café A)** | Nhân viên | `emp_a` | |
| **Hanoi Craft Coffee (Café B)** | Quản lý | `manager_b` | Linh hoạt: Được phép đổi món mới hoặc tặng voucher dưới 50.000đ. |
| **Hanoi Craft Coffee (Café B)** | Nhân viên | `emp_b` | |

---

## 6. Kịch bản Nghiệm thu Demo (Hackathon Checklist)
- [x] **Backend 100% Pass Tests**: Đã kiểm thử tự động toàn bộ logic Auth, SOP Versioning, Tenant Isolation, Scoring Engine.
- [x] **Chế độ chạy kép**: Chạy offline mượt mà với `AI_MODE=stub`, chuyển đổi tức thì sang Live Gemini API (`AI_MODE=live`) khi có `GEMINI_API_KEY`.
- [x] **Mobile Android Sẵn sàng**: UI thiết kế chuẩn mobile, hỗ trợ âm thanh giọng nói TTS tiếng Việt (`expo-speech`), cấu hình sẵn EAS build APK.
- [x] **Đối soát dẫn chứng**: Không cho phép AI bịa đặt quote (quote không có trong lời nhân viên sẽ bị chấm 0 điểm).
- [x] **Bộ Skills cho AI**: Đầy đủ tài liệu chuẩn trong `.agents/skills/` để bất kỳ lập trình viên hoặc AI Agent nào cũng nắm bắt dự án ngay lập tức.
