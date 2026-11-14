# ShiftLens — Appsmith Manager Studio Configuration Guide

Thư mục này hướng dẫn kết nối **Appsmith Community Edition (CE)** với **FastAPI Backend** để Store Manager có thể quản lý, chỉnh sửa và phê duyệt (Approve) các phiên bản SOP & Rubric.

---

## 1. Nguyên tắc Bảo mật (Security Boundary)
- Appsmith **chỉ giao tiếp qua REST API (FastAPI)**, tuyệt đối **không kết nối trực tiếp đến Database** bằng Service Key hay database credentials.
- Sử dụng JWT Token có role `manager` để xác thực.

---

## 2. Danh sách REST Datasource & Queries

### 2.1. Đăng nhập Quản lý (Login)
- **Method**: `POST`
- **URL**: `{{appsmith.store.API_URL || 'http://localhost:8000'}}/v1/auth/login`
- **Body**:
  ```json
  {
    "username_or_email": "{{inp_username.text}}",
    "password": "{{inp_password.text}}"
  }
  ```
- **Post-exec Action**: Lưu `access_token` vào Appsmith Store:
  ```javascript
  storeValue('TOKEN', LoginQuery.data.access_token);
  storeValue('USER', LoginQuery.data.user);
  ```

---

### 2.2. Lấy danh sách SOP của quán (List SOPs)
- **Method**: `GET`
- **URL**: `{{appsmith.store.API_URL || 'http://localhost:8000'}}/v1/sops`
- **Headers**:
  - `Authorization`: `Bearer {{appsmith.store.TOKEN}}`
- **Output**: Bind vào `Table_SOPs`.

---

### 2.3. Tạo Bản thảo SOP mới (Create Draft Version)
- **Method**: `POST`
- **URL**: `{{appsmith.store.API_URL || 'http://localhost:8000'}}/v1/admin/sops/{{Table_SOPs.selectedRow.id}}/draft`
- **Headers**:
  - `Authorization`: `Bearer {{appsmith.store.TOKEN}}`
- **Body**:
  ```json
  {
    "steps": {{JSON.parse(inp_steps_json.text)}},
    "rubric": {{JSON.parse(inp_rubric_json.text)}}
  }
  ```
> **Lưu ý**: Tổng trọng số `weight` của tất cả các tiêu chí trong Rubric bắt buộc phải bằng **100**.

---

### 2.4. Phê duyệt Phiên bản SOP (Approve Version)
- **Method**: `POST`
- **URL**: `{{appsmith.store.API_URL || 'http://localhost:8000'}}/v1/admin/sop-versions/{{inp_version_id.text}}/approve`
- **Headers**:
  - `Authorization`: `Bearer {{appsmith.store.TOKEN}}`
- **Kết quả**:
  - Phiên bản mới được đánh dấu `approved` và trở thành `active_version_id`.
  - Phiên bản cũ được chuyển sang `superseded` (bất biến, không thể sửa đổi).
  - Các buổi luyện tập mới của nhân viên sẽ tự động nhận phiên bản này.

---

### 2.5. Báo cáo Năng lực Nhân viên & Bằng chứng (Store Competency Analytics)
- **Method**: `GET`
- **URL**: `{{appsmith.store.API_URL || 'http://localhost:8000'}}/v1/admin/analytics`
- **Headers**:
  - `Authorization`: `Bearer {{appsmith.store.TOKEN}}`
- **Output**: Trả về `pass_rate`, `average_score`, `critical_failure_count` và `recent_sessions` kèm `exact_quote` của từng nhân viên trong cửa hàng.

---

## 3. Import 1-Click OpenAPI 3.0 Spec
File [openapi.json](file:///d:/Thu_muc_C/Codex_Hackerthon/admin-appsmith/openapi.json) chứa đầy đủ 14 đường dẫn REST API chuẩn của hệ thống ShiftLens. Bạn có thể Import trực tiếp file này vào **Appsmith Datasource** hoặc **Postman** để tạo tự động toàn bộ các queries.
