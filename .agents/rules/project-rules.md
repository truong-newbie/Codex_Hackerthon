# Quy chuẩn & Nguyên tắc cốt lõi của Dự án ShiftLens

## 1. Triết lý hệ thống & Ranh giới tin cậy (Trust Boundaries)
- **Định vị**: ShiftLens là nền tảng đào tạo & mô phỏng nhân sự bằng AI dựa trên SOP và đánh giá có bằng chứng. Tuyệt đối không biến thành chatbot tra cứu tài liệu thông thường.
- **AI là cố vấn, Server là nguồn sự thật duy nhất (Single Source of Truth)**:
  - LLM chỉ được dùng để:
    1. Sinh kịch bản & câu mở đầu từ SOP (`AI Compiler`).
    2. Đóng vai khách hàng đối thoại (`Simulator`).
    3. Trích xuất bằng chứng câu nói (`exact_quote`) và nhận xét (`Evaluator`).
  - Server (FastAPI + Python deterministic logic) là bên duy nhất:
    1. Xác thực quyền hạn & cách ly tenant (`Tenant Isolation`).
    2. Quản lý trạng thái và phiên bản SOP (Chỉ Manager mới được Approve; Approved SOP là bất biến `immutable`).
    3. Ghim phiên bản SOP vào buổi luyện tập (`session pin`).
    4. Tính điểm theo trọng số Rubric (tổng 100 điểm) và kiểm tra `critical_failure`.
    5. Kiểm tra tính xác thực của `exact_quote` (Nếu quote không có thật trong transcript của nhân viên -> Bác bỏ, tính 0 điểm cho tiêu chí đó).

## 2. Tiêu chuẩn Mã nguồn (Code Quality)
- **Backend (Python / FastAPI)**:
  - Luôn định nghĩa kiểu dữ liệu chặt chẽ với Pydantic Schemas.
  - Xử lý triệt để ngoại lệ: Hết quota AI, timeout, kết nối DB -> Trả mã lỗi HTTP rõ ràng (503, 502, 422, 404, 403, 401), không crash app.
  - Minh bạch chế độ hoạt động: Trả về cờ `ai_mode: "live" | "stub"` và `live_ready: boolean` trong response để phục vụ kiểm thử và chấm thi trung thực.
- **Mobile (React Native / Expo / Android)**:
  - Ưu tiên tính độc lập của ứng dụng Android: Phải chạy ổn định trên thiết bị thật, hỗ trợ force-stop và mở lại mà không mất tính toàn vẹn phiên.
  - Trải nghiệm âm thanh (`expo-speech`): Phát giọng nói của khách hàng mượt mà, có nút bật/tắt và fallback dạng văn bản rõ ràng nếu thiết bị không hỗ trợ TTS.
  - Phân định rõ trạng thái kết nối và môi trường Backend qua biến môi trường `EXPO_PUBLIC_API_URL`.

## 3. Quy tắc Đa người dùng & Đa chi nhánh (Multi-tenancy)
- Nghiêm cấm tin tưởng `tenant_id` từ phía client gửi lên trong body/query. Luôn trích xuất `tenant_id` và `role` từ JWT token đã được xác thực ở Server.
- Mọi thao tác truy vấn dữ liệu SOP, Session, Transcript, Kết quả phải được ràng buộc theo `tenant_id` của tài khoản hiện tại.
