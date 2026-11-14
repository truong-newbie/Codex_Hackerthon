---
name: mobile-android-expo
description: Hướng dẫn phát triển ứng dụng di động Android bằng React Native và Expo, tích hợp expo-speech Text-to-Speech và cấu hình EAS Build APK.
---

# Mobile Android Expo Development Guide - ShiftLens

## 1. Yêu cầu & Công nghệ
- Node.js v20+ / npm v10+
- React Native với **Expo SDK**
- Thư viện âm thanh / giọng nói: `expo-speech`
- Đóng gói ứng dụng: **EAS Build** (profile `preview` sinh file `.apk` cài trực tiếp lên điện thoại Android)

## 2. Tiêu chí nghiệm thu cốt lõi (G1 & FR-15)
- App phải chạy độc lập trên điện thoại Android thật dưới dạng file APK cài đặt (không phụ thuộc Expo Go khi chấm thi).
- Cho phép **force-stop** (đóng hẳn ứng dụng trong cài đặt Android), mở lại và thực hiện một request AI mới thành công.
- Hiển thị rõ ràng huy hiệu trạng thái: `AI LIVE` (màu xanh lá) hoặc `AI STUB` (màu cam) để ban giám khảo thẩm định.

## 3. Luồng màn hình (Screens Flow)
1. **LoginScreen**:
   - Chọn nhanh tài khoản mẫu: Employee Café A (`emp_a@shiftlens.com`), Employee Café B (`emp_b@shiftlens.com`) hoặc nhập thủ công.
   - Lưu trữ JWT Token vào bộ nhớ an toàn (`AsyncStorage` / SecureStore).
2. **SopListScreen**:
   - Hiển thị danh sách các quy trình SOP đang có hiệu lực (`Approved Active`) của cửa hàng.
   - Nút "Bắt đầu luyện tập" gọi API `/v1/training/start`.
3. **SimulationScreen**:
   - Hiển thị bối cảnh tình huống do AI sinh ra (`situation`) và mục tiêu học tập (`learning_objective`).
   - Lời mở đầu của khách hàng (`opening_message`).
   - Nút loa phát âm thanh giọng nói khách hàng qua `expo-speech` (hỗ trợ ngôn ngữ tiếng Việt `vi-VN`).
   - Ô nhập văn bản phản hồi của nhân viên (giới hạn tối đa 4 lượt).
   - Nút "Kết thúc & Nhận đánh giá" khi đã hoàn thành ít nhất 1 lượt đối thoại.
4. **ResultScreen**:
   - Tổng điểm trên thang 100.
   - Huy hiệu Đạt (`PASSED`) hoặc Không Đạt (`FAILED`).
   - Cảnh báo nếu phạm lỗi nghiêm trọng (`critical_failure`).
   - Chi tiết từng tiêu chí: Điểm, Trạng thái, Lời nhận xét, và **Đoạn trích dẫn nguyên văn bằng chứng (`exact_quote`)**.
   - Lời khuyên rèn luyện tiếp theo (`coaching_tip`).

## 4. Cách chạy và build APK
```bash
cd mobile
npm install
# Chạy môi trường phát triển (Expo)
npx expo start
# Build APK độc lập qua EAS Build:
eas build -p android --profile preview
```
