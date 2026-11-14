---
name: shiftlens-architecture
description: Kiến trúc tổng thể hệ thống ShiftLens, luồng nghiệp vụ E2E, mô hình dữ liệu và các ranh giới tin cậy (Trust Boundaries).
---

# ShiftLens Architecture & System Design

## 1. Mục tiêu & Vấn đề giải quyết
ShiftLens giúp các chuỗi F&B / bán lẻ giải quyết bài toán đào tạo nhân viên part-time/mới bằng cách:
- Biến SOP khô khan thành bài tập nhập vai tương tác với khách hàng AI.
- Đánh giá khách quan dựa trên bằng chứng phát ngôn thực tế của nhân viên đối chiếu với rubric của quán.

## 2. Các thành phần chính
1. **Manager Studio (Appsmith)**:
   - Quản lý soạn thảo các bước SOP và bộ tiêu chí đánh giá (Rubric).
   - Duyệt (Approve) phiên bản SOP mới (v1 -> v2).
2. **Backend API (FastAPI)**:
   - Cung cấp REST endpoints cho cả Manager và Employee.
   - Quản lý SQLAlchemy Models, SQLite/PostgreSQL, JWT Auth, Multi-tenancy.
   - Đảm bảo tính bất biến của Approved SOP và chốt phiên bản (`session pin`).
3. **AI Gateway (Google GenAI)**:
   - Module 1: AI Compiler (ModuleDraft JSON).
   - Module 2: Simulator (CustomerOutput JSON).
   - Module 3: Evaluator (EvaluationDraft JSON).
4. **Deterministic Scoring Engine**:
   - Khớp nối `exact_quote` với lời thoại thực tế của nhân viên.
   - Cộng điểm theo trọng số, xác định `critical_failure`.
5. **Mobile Android App (React Native Expo)**:
   - Chạy trên điện thoại Android thật.
   - Đăng nhập nhân viên -> Chọn bài SOP -> Chat mô phỏng (tích hợp TTS `expo-speech`) -> Xem báo cáo điểm số chi tiết.

## 3. Data Flow
1. Manager duyệt SOP $v_2$ qua API `/v1/admin/sop-versions/{id}/approve`.
2. Employee gọi `/v1/training/start` -> Backend ghim $v_2$ vào `TrainingSession` -> Gọi AI Compiler sinh kịch bản.
3. Employee gửi lượt chat qua `/v1/training/{id}/turn` (tối đa 4 lượt) -> AI Simulator phản hồi giọng khách.
4. Employee bấm nộp bài qua `/v1/training/{id}/evaluate` -> Evaluator trích xuất câu trích dẫn -> Server tính điểm xác định -> Trả về `FinalResult`.
