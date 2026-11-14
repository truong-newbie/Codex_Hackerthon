# ShiftLens API v1 — contract đang triển khai

Tài liệu này ghi contract đang có trong code, chưa tuyên bố v1.2 hoàn tất. Các endpoint giữ prefix `/v1` và response legacy `detail` để mobile hiện tại tiếp tục đọc lỗi.

## Lỗi HTTP

Response lỗi có dạng:

```json
{
  "detail": "Thông báo ngắn cho người dùng hoặc danh sách lỗi validation",
  "code": "HTTP_409",
  "request_id": "UUID"
}
```

Header `X-Request-ID` chứa cùng ID. Validation dùng `code: VALIDATION_ERROR` và `detail` là danh sách `{loc, msg, type}`; không trả giá trị input. Lỗi không xử lý dùng `code: INTERNAL_ERROR`, HTTP 500 và thông báo chung. Lỗi provider AI dùng HTTP 502 với thông báo chung; cấu hình Live thiếu key dùng 503. Client có thể dựa vào HTTP status và `code`, không phân tích chuỗi `detail`.

## Health và Live

`GET /v1/health` trả `ai_mode`, `live_configured`, `ai_status`, `live_ready`, `gemini_model`, `version`, `environment` và `status`. `ai_status` hiện là `stub`, `unavailable` hoặc `unverified`. `live_ready` luôn false cho tới khi U08 có probe xác thực với provider; key hiện diện không chứng minh Live hoạt động. Endpoint health vẫn có thể HTTP 200 khi AI Live unavailable, nên chưa dùng làm deployment readiness gate.

## Legacy training

- `POST /v1/training/start`: body `{sop_id}`; trả session và module ghim SOP version.
- `POST /v1/training/{session_id}/turn`: body `{message}` dài 2–1000 ký tự sau trim; tối đa 4 lượt.
- `POST /v1/training/{session_id}/evaluate`: trả kết quả đã lưu nếu phiên đã có result.
- `GET /v1/training/{session_id}`: owner trong tenant đọc transcript/result.
- `GET /v1/training/sessions`: danh sách legacy tối đa 20 phiên, chưa có cursor.
- `POST /v1/admin/sop-versions/{version_id}/approve`: trả `{message, active_version_id, version_no}`. Mobile type đã sửa cho đúng shape.
- `POST /v1/admin/sops`: manager gửi `{title, steps, rubric}`; server lấy tenant từ JWT, tạo SOP cùng draft v1, trả `SOPDetailResponse` và HTTP 201. SOP chưa duyệt chỉ xuất hiện cho manager cùng tenant.

Các mutation training hiện chưa có operation ID/idempotency key. Client phải xem lỗi mạng/timeout là trạng thái chưa rõ, tải lại phiên trước khi tiếp tục. Contract operation, canonical state, pagination và versioning thuộc U05/U06, vẫn đang chờ triển khai.
