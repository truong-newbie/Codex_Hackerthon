# ShiftLens v1.2 — nhật ký triển khai

Baseline: `bb9e79b` trên `main` (local đi trước `origin/main` một commit ở thời điểm bắt đầu). Working tree ban đầu sạch.

Môi trường đã thấy: Node/npm và Java có trong PATH. `python`, `py`, `python3`, `uv`, `docker`, `adb` chưa có trong PATH. Có Python đi kèm LibreOffice tại `C:\Program Files\LibreOffice\program\python.exe`. Dependency backend đã tải vào `backend/.deps` (được ignore), nhưng Windows Application Control chặn `.pyd` của SQLAlchemy cả trong lẫn ngoài sandbox; pytest chưa thể import ứng dụng. PowerShell đang chặn chạy `.ps1` theo execution policy. `backend/shiftlens.db` và `backend/.env` tồn tại; chưa đọc nội dung hay sửa database.

## U00 — DONE

- Đã đọc baseline/plan/rules, Git status, manifests và các file liên quan.
- Chưa dùng database vận hành hoặc key Live.

## U01 — IN_PROGRESS

- Test fixture đã chuyển sang SQLite tạm và ép AI stub trước khi import app; có guard ngăn reset DB khác.
- Script benchmark cũng dùng SQLite tạm và ép stub trước khi import app, không ghi vào database cấu hình của operator.
- Bỏ thao tác tạo bảng khi import `app.main`.
- Test phụ thuộc thứ tự tạo Café B v2 đã được sửa để tự tạo fixture.
- `run_tests.ps1` và preflight được thay bằng runner cô lập/read-only mặc định.
- Preflight đã chạy với PowerShell process `-ExecutionPolicy Bypass`: chỉ kiểm tra file và báo tests/Android/Live chưa xác minh; không seed, không sửa DB.
- Đã thử pytest sau khi cài dependency nhưng import SQLAlchemy bị Windows Application Control chặn DLL, kể cả khi thử ngoài sandbox. Cần môi trường Python được phép chạy native dependencies, kiểm chứng canary DB và test order trước khi đánh DONE.

## U02 — IN_PROGRESS

- Studio đã dùng DOM `textContent` cho login identity, analytics, quote và version list; JWT được loại khỏi API log hiển thị.
- `scripts/check_studio_dom.js` chạy đạt với quote HTML độc hại, kiểm tra `innerHTML` bị cấm và token không nằm trong API log. JavaScript syntax cũng đạt. Cần browser regression test thật trước khi đánh DONE.

## U03 — IN_PROGRESS

- AI mode và environment sai sẽ bị từ chối; production yêu cầu secret riêng và CORS allowlist, demo mode bị chặn.
- Mặc định SQLite đã được neo vào thư mục `backend/`; SQLite connection bật foreign keys. Staging/production chỉ nhận CORS origin HTTPS.
- HTTP/validation/500 trả `detail`, `code`, `request_id`; request ID nằm trong header. Input lỗi validation và exception provider không được phản hồi nguyên văn.
- Health phân biệt `stub`, `unavailable`, `unverified`; `live_ready` chỉ là false cho đến khi có probe thực sự. Placeholder key không được coi là key Live.
- `scripts/check_config_policy.py` đã chạy đạt với mode sai, secret mặc định, CORS thiếu/HTTP và cấu hình production hợp lệ; script không import DB. Cần API runtime tests, probe Live, giới hạn request và config schema đầy đủ.

## U04 — IN_PROGRESS

- Thêm công cụ `scripts/inspect_db_metadata.py` mở SQLite ở chế độ read-only và in schema, số hàng, checksum schema, `quick_check`, vi phạm FK, nhóm duplicate và active-version mismatch; không in nội dung record.
- Đã kiểm tra riêng file `backend/shiftlens.db`: 126976 bytes; 8 bảng, 2 tenant, 4 account, 4 membership, 2 SOP, 2 version, chưa có session/turn/result. `quick_check=ok`, 0 FK violation, 0 nhóm duplicate, 0 active-version mismatch. Schema SHA-256: `044830a655e987f561acd5f190d4217f33dee555a075cb482aa62f949235151f`.
- Chưa tạo/chạy Alembic migration; không stamp hoặc sửa database này. PostgreSQL chưa kiểm chứng.

## U05 — IN_PROGRESS

- Mobile type cho approve response đã khớp schema backend; TypeScript typecheck đạt.
- Chưa làm pagination, canonical status, OpenAPI drift checks.

## U08 — IN_PROGRESS

- Provider errors không còn lộ chuỗi exception trong response/log ứng dụng; key thiếu/placeholder fail-closed.
- Chưa có probe Live, timeout/retry phân loại, provenance và validation semantic đầu ra.

## U09 — IN_PROGRESS

- Mật khẩu mới dùng PBKDF2 SHA-256 với salt riêng; hash demo cũ được nâng cấp sau đăng nhập hợp lệ. Studio ẩn mật khẩu/nút tài khoản mẫu khi demo mode tắt.
- Chưa có rate limit, reset/revoke account, quản lý nhân viên và kiểm thử runtime.

## U07 — IN_PROGRESS

- Quote verifier không còn nối nhiều lượt employee để match.
- Stub evaluator kiểm tra vi phạm hoàn tiền ở toàn transcript trước khi chấp nhận câu đúng.
- Đã thêm regression tests cho cross-turn quote và câu đúng rồi vi phạm critical; Python AST parse đạt, pytest còn bị môi trường chặn.
- Heuristic tiếng Việt hiện vẫn có nguy cơ bỏ sót câu vừa nhắc quản lý vừa hứa tự hoàn tiền trong cùng lượt; chưa thể coi policy evaluator an toàn để quyết định nhân sự.

## U10/U11 — IN_PROGRESS

- Mobile có lỗi API kèm HTTP status; lỗi mạng khi resume giữ ID phiên để người dùng mở lại.
- Send/evaluate/back được khóa trong thao tác xung đột; tin chỉ hiện như đã commit sau khi server xác nhận. Sau lỗi send, client thử đọc lại phiên để xác định request có được commit không. Trạng thái commit mơ hồ khóa send/evaluate cho đến khi mở lại phiên từ lịch sử.
- TypeScript typecheck đạt. Chưa có idempotency key hay recovery operation bền vững theo U06; chưa đánh DONE.

## U13 — IN_PROGRESS

- Manager có thể `POST /v1/admin/sops` với title, steps, rubric để tạo SOP và draft v1 trong một transaction; tenant lấy từ JWT. Employee không thấy SOP chưa duyệt, tenant khác không thấy SOP vừa tạo.
- Studio có ô tạo SOP mới từ nội dung Steps/Rubric và mẫu khởi đầu cho tenant chưa có SOP; sau tạo vẫn phải phê duyệt draft. Có regression test cho create→approve→employee visibility, nhưng chưa chạy được pytest tại máy này.
- Chưa có editor từng bước dễ dùng, sửa draft, archive, audit và guard concurrency/unique DB.

## U14/U15 — IN_PROGRESS

- Studio có bộ chọn nhiều SOP, giữ SOP đang chọn sau refresh; preset Café B chỉ áp dụng cho SOP tương ứng. DOM regression check đạt với tên SOP độc hại.
- KPI analytics được tính trên toàn bộ tenant bằng aggregate query, trong khi danh sách gần đây vẫn giới hạn 50; có regression test 51 phiên. Chưa kiểm chứng runtime, chưa có pagination và lọc nhân viên/SOP.

## U17 — IN_PROGRESS

- Thêm `backend/.dockerignore`; Docker chạy bằng user không phải root, startup không tự seed dữ liệu demo. Lệnh seed bị chặn ở production.
- Seed ngoài test chỉ chạy khi `DEMO_MODE=true`; script `start_demo.ps1` bật flag này có chủ đích và kiểm tra exit code của seed/server.
- Thêm GitHub Actions chạy pytest ở Python 3.12, typecheck mobile và Studio DOM check. Workflow chưa chạy trên CI; không coi là đã đạt.
- Chưa có migration, container build/scan, backup/restore, deployment staging.

## U20/U22 — IN_PROGRESS

- Benchmark chỉ đo TestClient trên dữ liệu tạm với AI stub; chưa đo HTTP mạng/Live nên không dùng để tuyên bố SLA.
- README đã bỏ số test pass cũ và checklist release cũ; thêm API contract đang triển khai. Runbook migration/backup/release evidence vẫn thiếu.

U06, U12, U16, U18–U19, U21: TODO. Cập nhật mục này khi triển khai tiếp; không coi kế hoạch đã hoàn thành.

## Kiểm tra tại máy hiện tại

- Python AST parse: đạt cho 27 file `backend/app`, `backend/tests` và `scripts`.
- `npx.cmd tsc --noEmit`: đạt.
- `node scripts/check_studio_dom.js`: đạt.
- `python scripts/check_config_policy.py` bằng Python LibreOffice: đạt.
- PowerShell parser: đạt cho `run_tests.ps1`, `preflight_check.ps1`, `start_demo.ps1`; script demo được lưu UTF-8 BOM cho PowerShell 5.1.
- `git diff --check`: đạt.
- Backend pytest: bị Windows Application Control chặn native SQLAlchemy dependency; chưa có kết quả pass/fail.
- Docker/Android/Live: chưa có công cụ, thiết bị hoặc bằng chứng chạy thực tế.
