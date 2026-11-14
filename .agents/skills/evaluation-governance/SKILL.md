---
name: evaluation-governance
description: Cơ chế kiểm định bằng chứng đánh giá (Evidence Governance), chống AI ảo giác dẫn chứng và động cơ tính điểm tất định (Deterministic Scoring Engine).
---

# Evaluation Governance & Deterministic Scoring Engine

## 1. Vấn đề giải quyết
Trong đào tạo nhân viên, nếu để LLM tự cho điểm số ngẫu nhiên hoặc tự bịa ra lý do, kết quả sẽ không đáng tin cậy và không thể dùng làm thước đo chuẩn hóa. 

ShiftLens áp dụng nguyên tắc **Deterministic Scoring Engine** do Server kiểm soát 100%:

## 2. Quy trình kiểm định dẫn chứng 4 bước
1. **Trích xuất bằng chứng từ AI**:
   - AI Evaluator chỉ làm nhiệm vụ đọc transcript và tìm xem câu nói nào của nhân viên thể hiện việc thỏa mãn tiêu chí $C_i$.
   - AI trả về `exact_quote` (chuỗi trích dẫn nguyên văn) và `passed: true | false`.
2. **Đối soát tính nguyên văn trên Server (Server-side Quote Verification)**:
   - Server lấy chuỗi `exact_quote` và tìm kiếm (case-insensitive & whitespace-normalized) trong toàn bộ các câu trả lời thực tế mà nhân viên đã gửi trong phiên đó (`employee_text`).
   - Nếu `exact_quote` không tồn tại trong transcript $\rightarrow$ **Phát hiện dẫn chứng ảo giác (Hallucinated Evidence)**:
     - Gán `passed = false`.
     - Gán điểm tiêu chí đó về $0$.
     - Ghi chú: `"Bằng chứng trích dẫn không có thật trong hội thoại."`
3. **Cộng điểm xác định theo Rubric**:
   - Mỗi tiêu chí $C_i$ có trọng số cố định $W_i$ đã được Manager phê duyệt trong SOP.
   - $\text{Total Score} = \sum (W_i \times (\text{passed}_i ? 1 : 0))$.
4. **Kiểm tra Tiêu chí chí tử (Critical Criterion Enforcement)**:
   - Nếu bất kỳ tiêu chí nào có cờ `critical = true` mà bị đánh rớt (`passed = false`):
     - `critical_failure = true`.
     - `passed = false` cho toàn bộ bài thi, **ngay cả khi tổng điểm $\ge 70$**.
     - (Ví dụ: Vi phạm chính sách an toàn, cãi tay đôi với khách, tự ý bồi thường trái phép).
