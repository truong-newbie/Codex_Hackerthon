# ShiftLens — Pitch Deck, Demo Script & User Validation Kit (W11 & W12)

Tài liệu này phục vụ trực tiếp cho phần thi thuyết trình (**Pitch & GTM - Gate G7**) và kiểm chứng người dùng thực tế (**User Validation - W11**) tại **Codex Community Hackathon Hanoi**.

---

## 1. Định Vị Cốt Lõi & Chân Dung Khách Hàng (Buyer vs. User Map)

| Yếu tố | Chi tiết xác định |
| :--- | :--- |
| **Beachhead Market** | Quán cà phê độc lập & chuỗi nhỏ quy mô **5–20 nhân viên** tại Hà Nội (Cầu Giấy, Đống Đa, Hai Bà Trưng, Tây Hồ). |
| **Người mua (Buyer)** | **Chủ quán / Quản lý cửa hàng (Store Manager)**: Đau đầu vì tỷ lệ thay mới nhân sự part-time cao (2–3 tháng/lần), tốn hàng chục giờ đóng vai khách hàng kèm cặp người mới và xử lý khủng hoảng khi nhân viên tự ý hoàn tiền/cãi khách. |
| **Người dùng (End User)** | **Nhân viên mới / Part-time Barista & Cashier**: Ngại đọc tài liệu SOP dài dòng, lúng túng khi gặp khách phàn nàn thực tế tại quầy. |
| **Giá trị cốt lõi** | Biến SOP riêng của từng quán thành **kịch bản nhập vai khách hàng AI trên điện thoại Android** và **chấm điểm xác định có trích dẫn câu nói nguyên văn (`exact_quote`)**. |

---

## 2. Kịch Bản Demo Sân Khấu 3 Phút (Chạy Trên Điện Thoại Android Thật)

### ⏱️ 00:00 – 00:30 | Nêu vấn đề & Chứng minh Native Android Reality (Gate G1)
* **Lời thoại**:
  > *"Một quán cà phê 10 nhân viên tại Hà Nội phải tuyển và đào tạo lại nhân viên part-time liên tục. Chủ quán không thể trực tiếp đóng vai khách khó tính để kèm từng bạn, còn gửi file SOP thì nhân viên đọc xong vẫn xử lý sai khi khách mắng. ShiftLens giải quyết triệt để việc này: biến SOP của quán thành phòng tập mô phỏng khách hàng AI kèm đánh giá có dẫn chứng nguyên văn."*
* **Thao tác kỹ thuật**:
  - Trên điện thoại Android thật đang chiếu màn hình: Mở Cài đặt Android $\rightarrow$ bấm **Buộc dừng (Force-stop)** ứng dụng **ShiftLens** $\rightarrow$ Mở lại ứng dụng từ màn hình chính.

### ⏱️ 00:30 – 01:25 | Nhân viên Café A Thực hành & Chấm điểm Bằng chứng (Gate G2 & G5)
* **Thao tác kỹ thuật**:
  1. Bấm đăng nhập nhanh **☕ Café A (`emp_a`)** (Chính sách nghiêm ngặt: *Không tự ý hoàn tiền khi chưa xin phép quản lý*).
  2. Chỉ vào huy hiệu **`● AI LIVE`** và **`v1 Active`**. Nhấn **Bắt đầu Phiên mới (Pin v1)**.
  3. Khách hàng AI mở lời phàn nàn ly cà phê muối bị mặn; bấm nút **`🔊 Nghe TTS`** phát giọng nói tiếng Việt.
  4. Gửi phản hồi tuân thủ SOP (xin lỗi + kiểm tra hóa đơn + đổi ly mới + xin ý kiến quản lý).
  5. Nhấn **Chấm điểm** $\rightarrow$ Trình chiếu màn hình **Báo cáo Đánh giá (100/100đ — ĐẠT YÊU CẦU)**:
     - Chỉ rõ dòng **`✓ Bằng chứng nguyên văn (Exact Quote Verified)`** được trích xuất chính xác từ lời nhân viên.
     - Nhấn mạnh: Server tự tính điểm theo trọng số Rubric; nếu AI bịa quote hoặc nhân viên vi phạm tiêu chí `Critical`, hệ thống tự động đánh trượt ngay lập tức.

### ⏱️ 01:25 – 02:20 | Đa Cửa Hàng (Café B) & Quản Lý Duyệt SOP v2 (Gate G3 & G4)
* **Thao tác kỹ thuật**:
  1. Chuyển sang tài khoản **🌿 Café B (`emp_b`)** $\rightarrow$ Mở một phiên học (`Session #1`), hệ thống ghim **`Pinned: v1`** (Chính sách linh hoạt dưới 50.000đ).
  2. Trên máy tính, mở **Manager Studio (`/studio` hoặc Appsmith)** với tài khoản Quản lý Café B (`manager_b`).
  3. Nhấn **Nạp Mẫu Demo SOP v2** (bổ sung quy định *Tặng kèm 01 bánh quy bơ miễn phí*) $\rightarrow$ nhấn **Tạo Bản Thảo Mới (Create Draft)** $\rightarrow$ nhấn **Phê Duyệt & Kích Hoạt (Approve v2)**.

### ⏱️ 02:20 – 03:00 | Chứng minh Session Pinning bất biến & Lộ trình Go-To-Market (Gate G3 & G7)
* **Thao tác kỹ thuật**:
  1. Trên điện thoại của `emp_b`, bấm **🔄 Làm mới**: Thẻ SOP hiển thị ngay **`v2 Active`**.
  2. Bấm bắt đầu phiên học mới (`Session #2`) $\rightarrow$ Kịch bản AI lập tức áp dụng quy định tặng bánh quy của **`v2`**.
  3. Quay lại mục **Lịch sử Phiên học** ngay bên dưới: Chỉ cho BGK thấy `Session #1` vẫn giữ nguyên nhãn **`📌 Pinned: v1`**, đảm bảo tính bất biến của dữ liệu đào tạo!
* **Lời kết GTM**:
  > *"Chúng tôi tiếp cận 10 quán cà phê độc lập đầu tiên tại khu vực Cầu Giấy & Đống Đa thông qua hình thức thiết lập miễn phí 1 quy trình xử lý phàn nàn trong 15 phút, đo lường trực tiếp thời gian onboard nhân viên mới giảm từ 5 ngày xuống 2 ca thực hành."*

---

## 3. Phiếu Phỏng Vấn Người Dùng Thực Tế (User Validation Form — W11)

> **Quy tắc trung thực (G7)**: Chỉ ghi nhận số liệu từ phỏng vấn thật (có sự đồng ý của người trả lời). Nếu một chỉ số chưa đo lường thực tế, trình bày rõ là *Giả thuyết cần kiểm chứng trong đợt Pilot 2 tuần*.

### A. Câu hỏi dành cho Chủ quán / Quản lý (2 người)
1. Quán của anh/chị hiện có bao nhiêu nhân viên part-time? Trung bình bao lâu phải tuyển và đào tạo người mới một lần?
2. Khi nhân viên mới gặp khách phàn nàn đồ uống tại quầy, lỗi phổ biến nhất họ hay mắc là gì (cãi khách, tự ý đền tiền, hay đứng im)?
3. Hiện tại anh/chị kiểm tra xem nhân viên đã thuộc quy trình (SOP) bằng cách nào? Mất khoảng bao nhiêu thời gian mỗi tuần?
4. Nếu có ứng dụng đóng vai khách khó tính để nhân viên tự luyện trên điện thoại và gửi lại bảng chấm điểm kèm câu nói thực tế của nhân viên cho anh/chị xem, anh/chị sẵn sàng thử nghiệm trong 2 tuần tới chứ?

### B. Câu hỏi dành cho Nhân viên Part-time (3 người)
1. Lúc mới vào làm ca đầu tiên, bạn được hướng dẫn quy trình xử lý khi khách phàn nàn bằng cách nào (đọc giấy/tin nhắn Zalo hay người cũ chỉ miệng)?
2. Bạn có từng gặp tình huống khách phàn nàn gắt gỏng mà lúc đó không có quản lý ở quầy chưa? Lúc đó bạn cảm thấy thế nào?
3. Giữa việc đọc một file quy trình dài 3 trang và việc chat thử 3 lượt với khách hàng ảo trên điện thoại để biết ngay mình nói đúng hay sai, bạn thích cách nào hơn?

---

## 4. Kế Hoạch Tiếp Cận 10 Khách Hàng Đầu Tiên (Go-To-Market)

1. **Tệp khách hàng mục tiêu (10 quán đầu tiên)**:
   - Các quán cà phê specialty & quán cà phê học bài quanh khu vực **Làng Đại học Cầu Giấy (Xuân Thủy, Duy Tân, Tô Hiệu)** và **Đống Đa (Chùa Láng, Đặng Văn Ngữ)** có từ 8–15 nhân viên part-time sinh viên.
2. **Chiến lược thâm nhập (Wedge Strategy)**:
   - Không bán phần mềm phức tạp: Cung cấp gói **"Chuẩn hóa 1 SOP Xử lý Phàn nàn trong 15 phút"**.
   - Chủ quán chỉ cần gửi tin nhắn Zalo quy định hiện tại $\rightarrow$ Đội ngũ nạp lên Manager Studio $\rightarrow$ Chủ quán bấm duyệt và gửi link cài APK cho nhân viên mới thực hành ngay trước ca làm.
3. **Chỉ số đo lường Pilot (Pilot KPIs trong 14 ngày)**:
   - Tỷ lệ nhân viên mới hoàn thành đạt ($\ge 70$ điểm, không vi phạm Critical) trong $\le 3$ lần thử.
   - Số lần nhân viên mới phải gọi điện hỏi quản lý khi xử lý sự cố đồ uống trong tuần đầu tiên.
   - Tỷ lệ duy trì sử dụng (Retention) của cửa hàng sau 2 tuần và mức sẵn sàng chi trả (WTP giả thuyết: 199.000đ – 299.000đ/cửa hàng/tháng).
