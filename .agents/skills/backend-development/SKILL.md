---
name: backend-development
description: Quy chuẩn phát triển FastAPI, cấu trúc thư mục, Pydantic Schemas, tích hợp google-genai structured output và chế độ chạy kép (Live AI vs Stub).
---

# Backend Development Guide - ShiftLens

## 1. Yêu cầu Công nghệ
- Python 3.10+ (đang chạy Python 3.15)
- Framework: **FastAPI**, **Pydantic v2**, **SQLAlchemy**, **Uvicorn**
- AI Client: `google-genai` (SDK chính thức của Google cho Gemini API)
- Database: SQLite cục bộ (cho dev/test), Supabase PostgreSQL (production ready via `DATABASE_URL`)

## 2. Quy tắc quan trọng
- **Chế độ chạy AI kép**:
  - `AI_MODE="live"`: Yêu cầu biến môi trường `GEMINI_API_KEY`. Gọi trực tiếp Google GenAI model (ví dụ `gemini-2.5-flash` hoặc `gemini-1.5-flash`). Nếu thiếu key hoặc lỗi API, trả mã lỗi HTTP 503/502 rõ ràng kèm thông báo, không crash.
  - `AI_MODE="stub"`: Chế độ mock kiểm thử nhanh, trả dữ liệu mẫu có cấu trúc Pydantic hợp lệ mà không tốn quota AI.
  - Endpoint `/v1/health` luôn trả về:
    ```json
    {
      "status": "ok",
      "ai_mode": "live",
      "live_ready": true,
      "version": "1.1.0"
    }
    ```
- **Ràng buộc Pydantic**:
  - Mọi request/response đều được kiểm tra kiểu dữ liệu qua Pydantic schemas.
  - ModuleDraft, CustomerOutput, EvaluationDraft phải khớp chính xác cấu trúc dữ liệu quy định trong SRS v1.1.

## 3. Cách khởi chạy Backend
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Tài liệu tương tác Swagger UI: `http://localhost:8000/docs`
