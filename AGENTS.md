# Hướng Dẫn Dành Cho AI & Cộng Sự (AGENTS & Collaborator Guide)

Chào mừng bạn đến với dự án **ShiftLens** (Codex Community Hackathon Hanoi).

## 1. Giới thiệu dự án
- **Dự án**: ShiftLens — AI Workforce Training & Simulation Platform.
- **Mục tiêu**: Biến quy trình chuẩn (SOP) thành kịch bản mô phỏng tương tác trên ứng dụng Android thật với khách hàng AI và đánh giá có bằng chứng trích dẫn thực tế.
- **Beachhead**: Chuỗi/quán cà phê F&B độc lập (Café A: chính sách nghiêm ngặt không hoàn tiền; Café B: chính sách linh hoạt cho phép đổi món dưới ngưỡng).

## 2. Cấu trúc thư mục chuẩn
```
Codex_Hackerthon/
├── .agents/                    # Bộ kỹ năng (Skills) & Luật dự án chuẩn hóa cho AI
│   ├── rules/project-rules.md
│   └── skills/
│       ├── shiftlens-architecture/SKILL.md
│       ├── backend-development/SKILL.md
│       ├── mobile-android-expo/SKILL.md
│       └── evaluation-governance/SKILL.md
├── backend/                    # FastAPI Server, SQLAlchemy, Google GenAI SDK, SQLite/Supabase
│   ├── app/                    # Mã nguồn chính
│   │   ├── routers/            # API endpoints (Auth, SOPs, Admin, Training)
│   │   ├── services/           # AI Service, Scoring Engine, SOP Service
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   ├── schemas.py          # Pydantic Schemas
│   │   └── seed.py             # Dữ liệu mẫu (Café A & B)
│   └── tests/                  # Unit tests & Integration tests
├── mobile/                     # Ứng dụng Android React Native Expo
│   ├── src/                    # Màn hình (Login, SOP, Simulation, Result), API, Context
│   ├── app.json                # Cấu hình Expo
│   └── eas.json                # Cấu hình build APK Android
├── admin-appsmith/             # Tài liệu & Payload cấu hình Appsmith No-Code Portal
└── scripts/                    # Scripts test E2E (PowerShell & Bash)
```

## 3. Các nguyên tắc kỹ thuật bất khả xâm phạm
1. **Server là nguồn sự thật**: LLM chỉ sinh văn bản và trích dẫn quote. Điểm số, trạng thái phiên, tính hợp lệ của quote, phân quyền tenant do Server kiểm soát 100%.
2. **Multi-tenancy an toàn**: Lấy `tenant_id` từ JWT, không nhận từ client.
3. **Chế độ chạy kép**: Backend luôn hỗ trợ `AI_MODE="live"` (gọi Gemini) và `AI_MODE="stub"` (cho CI/CD hoặc khi mất mạng).
4. **Mobile Android độc lập**: Đóng gói qua EAS Build profile `preview` để tạo file `.apk` cài lên điện thoại thật.
