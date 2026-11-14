# Migration v1.1 → v1.2

Migration đã được chạy trên SQLite mới và bản sao của `backend/shiftlens.db`. **Không chạy trực tiếp trên database đang có writes.** PostgreSQL và khôi phục production chưa được nghiệm thu.

## Database SQLite mới

1. Tạo môi trường Python và cài `backend/requirements.txt`.
2. Đặt `DATABASE_URL` thành SQLite URL tuyệt đối hoặc dùng mặc định `backend/shiftlens.db` nếu chưa có file cũ.
3. Từ `backend/`, chạy `python -m alembic upgrade head`.
4. Xác nhận `alembic_version.version_num = 20261114_0002`. Chỉ khi dùng demo mới đặt `DEMO_MODE=true` rồi chạy `python -m app.seed`.

## SQLite v1.1 đang có dữ liệu

1. Dừng server/worker có thể ghi vào database. Xác nhận đường dẫn DB thực tế từ cấu hình; không suy ra từ thư mục terminal.
2. Chạy `python scripts/inspect_db_metadata.py <đường-dẫn-db>` và lưu `schema_sha256`, số hàng, `quick_check`, FK, duplicate, active pointer. Script chỉ đọc.
3. Chạy `python scripts/check_alembic_migrations.py --legacy-source <đường-dẫn-db>`. Script dùng SQLite backup API, stamp và migrate **trên bản sao tạm**; kiểm tra bảng, lịch sử và file gốc không đổi.
4. Chọn một đường dẫn backup **mới** trong thư mục backup đã có. Chạy:

   ```text
   python scripts/stamp_legacy_sqlite.py <đường-dẫn-db> --apply --backup <đường-dẫn-backup-mới> --expected-schema-sha256 <hash-đã-review>
   ```

   Lệnh kiểm tra cấu trúc v1.1, FK, duplicate, active pointer, result/session, tạo backup nhất quán, so sánh nội dung và schema trước khi ghi `alembic_version=20261114_0001`. Nếu có xung đột, lệnh dừng; xử lý dữ liệu bằng quyết định có chủ đích, không xóa tự động.
5. Đặt `DATABASE_URL` trỏ đúng DB vừa stamp. Từ `backend/`, chạy `python -m alembic upgrade head`. Migration 0002 backfill `state=evaluated` khi đã có result; trường provenance của lịch sử để null/unknown. Payload kết quả cũ không bị viết lại.
6. Chạy lại `inspect_db_metadata.py`, đối chiếu số hàng ở 8 bảng cũ, ID/version pin, `quick_check`, FK và result payload checksum. Khởi động app sau khi các kiểm tra đạt.

`check_alembic_migrations.py` kiểm tra đường nâng cấp trên bản sao trước khi thao tác lên file gốc. Với dữ liệu quan trọng, thử restore backup vào một database khác và xác nhận ứng dụng đọc được trước khi migration chính thức. Không chạy `alembic stamp head` trực tiếp lên DB cũ.

## PostgreSQL

Database mới có thể dùng `postgresql+psycopg://...` với `alembic upgrade head`, nhưng cần integration test trên PostgreSQL thật. Chưa có công cụ baseline PostgreSQL v1.1 đã có dữ liệu; không stamp DB cũ bằng quy trình SQLite. Backup, restore, quyền DB và SSL cần được kiểm chứng ở staging.

## Rollback

Các revision chặn downgrade phá hủy dữ liệu. Nếu chưa có writes sau migration, phục hồi từ backup đã kiểm chứng và cấu hình app cũ. Sau khi có writes v1.2, đánh giá forward fix hoặc restore có đối soát dữ liệu mới; không drop bảng/cột để quay lui.
