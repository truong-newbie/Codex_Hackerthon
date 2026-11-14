# ShiftLens — phân công hoàn thiện MVP trong 3 giờ

**Mục tiêu:** đưa codebase hiện tại tới một vertical slice chạy được từ đầu đến cuối, đồng thời sinh và giữ lại project Android Gradle để mở, build và chạy bằng Android Studio.

Tài liệu này rút gọn [Execution Plan v1.1](../01_ShiftLens_Execution_Plan_v1.1.docx), đối chiếu với [SRS v1.1](../02_ShiftLens_SRS_v1.1.docx) và [Masterplan](SHIFTLENS_WINNING_MASTERPLAN.md). Kế hoạch gốc dành đội 4 người và khoảng 4–5 giờ; lịch dưới đây giả định **4 người làm song song trong 3 giờ**, tận dụng phần code đã có.

## 1. Định nghĩa “hoàn chỉnh” trong 3 giờ

Ở cuối giờ thứ ba, nhóm cần có:

1. Project `mobile/android` được tạo, lưu trong repository và mở/sync được bằng Android Studio.
2. Android Studio build được APK bằng Gradle; APK cài được lên điện thoại Android thật.
3. Nhân viên đăng nhập, chọn SOP theo cửa hàng, bắt đầu mô phỏng, gửi 1–3 lượt và xem kết quả có điểm, quote được server kiểm chứng, trạng thái `AI LIVE`/`AI STUB` rõ ràng.
4. Quản lý dùng Manager Studio hiện có để tạo và duyệt SOP v2; phiên mới dùng v2, phiên cũ vẫn ghim phiên bản ban đầu.
5. Cấu hình API có thể truy cập từ điện thoại thật; thông tin đăng nhập và URL backend vẫn còn sau khi force-stop/mở lại.

Đây là mục tiêu **MVP demo có thể build và chạy**, chưa phải bản production: SRS Auth/RLS production, billing, analytics, camera, STT, import PDF và các tính năng ngoài luồng demo được để sau. Chỉ tuyên bố AI Live nếu `/v1/health` báo `ai_mode=live`, `live_ready=true` và app thực hiện được request Gemini thật.

## 2. Tình trạng codebase đã xác nhận

- Backend đã có login/JWT, tenant scoping, SOP draft/approve, start/turn/evaluate, lịch sử phiên và chi tiết phiên trong `backend/app/routers/`.
- `backend/app/routers/studio_router.py` đã phục vụ giao diện quản lý tại `/studio`; chưa cần dựng lại Manager Studio trong 3 giờ.
- App mobile đã có các màn hình login, danh sách SOP/phiên gần đây, mô phỏng, kết quả, TTS và telemetry.
- Điểm nghẽn Android: hiện chưa có thư mục native `mobile/android`. `package.json` dùng Expo SDK 52 nhưng chưa có AsyncStorage. `mobile/src/utils/storage.ts` chỉ dùng `localStorage` trên web và bộ nhớ tạm trên Android, nên đăng nhập/URL sẽ mất sau khi app bị đóng hẳn.
- Vì vậy ưu tiên còn lại là sửa lưu trữ native, cấu hình địa chỉ backend, sinh project Gradle, build APK và kiểm tra thật trên thiết bị. Không dành thời gian viết lại backend hoặc dựng lại UI đã có.

## 3. Chia việc cho 4 người

| Người phụ trách | Quyền sở hữu | Việc phải hoàn thành | Bằng chứng bàn giao |
|---|---|---|---|
| **A — Backend & AI** | `backend/` | Khởi chạy API và seed Café A/B; xác nhận health, login, SOP, start/turn/evaluate hoạt động. Cấu hình Gemini ở backend nếu đã có key; giữ `stub` minh bạch nếu chưa có. Sửa blocker P0 ở auth, tenant, quote/scoring hoặc lỗi 502/503. | URL API truy cập được; health JSON; một kết quả có `sop_version_id`, `ai_mode`, quote và điểm từ server. |
| **B — Mobile app** | `mobile/src/` | Thay storage Android bằng `@react-native-async-storage/async-storage`; lưu/khôi phục token, user và server URL. Cấu hình URL API theo môi trường; xử lý loading/lỗi mạng; giữ nguyên badge mode và version/latency. Kiểm tra luồng login → SOP → chat → result. | Force-stop/mở lại vẫn giữ đăng nhập và URL; luồng nhân viên không crash; lỗi API hiển thị rõ. |
| **C — Android Studio & build** | `mobile/android/` | Cùng B chốt dependency/config, chạy Expo prebuild để sinh Android project; mở `mobile/android` trong Android Studio, sync Gradle, xử lý SDK/JDK/manifest; build APK và cài lên thiết bị. Giữ thư mục `android/`, Gradle wrapper và cấu hình cần thiết trong repo. | Android Studio mở được project; Gradle build thành công; có APK và đường dẫn file; app mở được trên điện thoại. |
| **D — Manager Studio, tích hợp & demo** | `backend/app/routers/studio_router.py`, `docs/`, `scripts/` | Dùng `/studio` với `manager_b`, tạo draft/approve v2; kiểm tra v1/v2 pinning và tách tenant. Chuẩn bị tài khoản, API URL, demo script, checklist và hướng dẫn build Android Studio. Ghi rõ trạng thái Live/Stub, không tạo số liệu phỏng vấn/latency giả. | Manager duyệt được v2; ảnh/chụp log hoặc IDs chứng minh v1/v2; README hướng dẫn chạy; kịch bản demo 3 phút. |

**Quy tắc phối hợp:** API owner gửi URL, trạng thái health và tài khoản mẫu cho B/C/D trong 10 phút đầu. B không đổi response contract nếu chưa báo A. C tạo project Android từ cấu hình Expo hiện tại; không sửa Kotlin/Gradle tùy tiện nếu chưa cần. Mọi thay đổi `app.json`, dependency Expo hoặc native config phải được B và C phối hợp trước khi build lại.

## 4. Lịch 180 phút

| Thời gian | Cả nhóm cần đạt | A — Backend/AI | B — Mobile | C — Android build | D — Manager/demo |
|---|---|---|---|---|---|
| **00–15 phút** | Chốt phạm vi, kiểm tra máy/SDK/thiết bị/mạng/key; phân nhánh và URL API | Chạy API, kiểm tra DB/seed, `/v1/health` | Kiểm tra app và luồng hiện có; xác định API URL | Xác nhận Android Studio, JDK, SDK, adb; kiểm tra thiết bị | Kiểm tra `/studio`, tài khoản mẫu, chọn SOP demo |
| **15–55 phút** | Bắt đầu 4 luồng song song, không mở rộng tính năng | Sửa blocker backend/live; xác nhận request API trực tiếp | Cài AsyncStorage; lưu/khôi phục auth + URL; xử lý lỗi mạng | Cài dependency sau khi B chốt; chạy `npx expo prebuild --platform android`; mở project trong Studio | Tạo/duyệt v2 trên Café B; kiểm tra `active_version` và log |
| **55–95 phút** | Tạo bản tích hợp đầu tiên | Cấp API ổn định, kiểm tra score/quote/tenant | Hoàn thành login → list → start → turn → evaluate | Gradle sync và `assembleDebug`; cài thử, sửa blocker build/native | Kiểm tra session history và pin v1/v2; chuẩn bị demo theo đúng dữ liệu |
| **95–130 phút** | Chạy E2E trên thiết bị thật | Theo dõi API/AI và sửa lỗi phát sinh | Sửa lỗi UI, force-stop persistence, retry/timeout | Build lại APK sau thay đổi; cài APK mới lên thiết bị | Chạy demo từ đầu, xác nhận v2 mới và v1 cũ; ghi checklist |
| **130–160 phút** | Chốt các release gate P0 | Xác nhận mode thật, isolation, quote và lỗi fail-closed | Hoàn tất luồng result, mode badge, version/latency | Build APK bàn giao; lưu `mobile/android` và Gradle wrapper; hướng dẫn mở project | Viết/chỉnh hướng dẫn chạy, chốt demo script và phương án dự phòng |
| **160–180 phút** | Code freeze, bàn giao project và rehearsal 3 phút | Không thêm feature; hỗ trợ blocker P0 | Không thêm feature; sửa lỗi chỉ khi chặn demo | Xác nhận mở/build lại được từ Android Studio | Rehearsal, ghi rõ điều kiện còn thiếu và đóng gói deliverable |

## 5. Build Android bằng Android Studio

Ứng dụng vẫn dùng React Native + Expo; `mobile/android` là project Android Gradle native được Expo sinh ra. Có thể mở project này trực tiếp trong Android Studio và build bằng Gradle.

1. Cài dependency JS theo lockfile. Khi thêm lưu trữ native, dùng Expo-compatible AsyncStorage và cập nhật lockfile.
2. Từ `mobile/`, sinh project Android: `npx expo prebuild --platform android`.
3. Mở `mobile/android` bằng Android Studio, chờ Gradle Sync, chọn thiết bị/emulator và build `app`.
4. Có thể build nhanh bằng Gradle task `:app:assembleDebug`; APK thường nằm tại `mobile/android/app/build/outputs/apk/debug/app-debug.apk`.
5. Để chạy độc lập không cần Metro, tạo và kiểm tra bản `release`/APK có JS bundle; xử lý signing trước khi phân phối cho người khác. Build debug phù hợp phát triển, không tự chứng minh APK đã độc lập.
6. Commit `mobile/android/` cùng Gradle wrapper và cấu hình native cần thiết; không commit `node_modules`, build output, keystore hay secret.
7. Đặt URL backend mà app dùng lúc chạy. Emulator Android thường gọi host máy dev qua `10.0.2.2`; điện thoại thật cần IP LAN có thể truy cập hoặc HTTPS tunnel. `localhost` trên điện thoại là chính điện thoại, không phải máy chạy FastAPI.

Sau khi thay đổi cấu hình Expo/native plugin, chạy prebuild lại có kiểm soát rồi sync/build trong Android Studio. Không ghi đè chỉnh sửa native thủ công mà chưa lưu/đưa vào config tương ứng.

## 6. Điều kiện bắt đầu và cut-line

Để 3 giờ đủ thực tế, trước giờ tính giờ cần chuẩn bị Android Studio + Android SDK/JDK, điện thoại/USB hoặc emulator, Python environment và npm dependencies. Nếu luật hackathon cho phép, chuẩn bị sẵn Gemini key và HTTPS endpoint; secret chỉ đặt ở backend, không đưa vào APK.

Điện thoại thật phải truy cập được backend. `10.0.2.2` chỉ dành cho Android emulator. Nếu dùng Wi-Fi nội bộ, xác nhận firewall và địa chỉ LAN; nếu demo qua mạng khác, dùng HTTPS tunnel. Nếu chưa có Gemini key hoặc API chưa tới được mạng, vẫn build được app nhưng chỉ nghiệm thu `AI STUB`, không gọi đó là Live.

Nếu trễ, cắt theo thứ tự: EAS build (dùng Gradle/Android Studio), cấu hình Appsmith riêng (dùng `/studio` đã có), TTS nếu lỗi, giới hạn roleplay còn 1 lượt, benchmark P50/P95 và phần mở rộng pitch. Không cắt: project Gradle mở được, APK build/cài được, luồng employee end-to-end, server-side quote/scoring, tenant boundary và nhãn AI trung thực.

Nếu mất quá 30 phút để tạo/sync native project, một người xử lý SDK/JDK/Gradle trong khi các thành viên khác tiếp tục luồng API và mobile. Không để cả nhóm chờ build; đến phút 95 phải có quyết định rõ: build tiếp trên máy thật, hoặc báo giới hạn môi trường và giữ lại log lỗi cụ thể.

## 7. Checklist nghiệm thu cuối giờ

- [ ] `mobile/android` có trong repo, Android Studio mở project và Gradle Sync thành công.
- [ ] APK được build, cài và mở trên Android; có đường dẫn APK và biết đang là debug hay release.
- [ ] Force-stop rồi mở lại: token/user/server URL được khôi phục; gửi được request mới.
- [ ] Đăng nhập employee → chọn SOP → tạo session → ít nhất một lượt chat → evaluate → xem score/quote/critical result.
- [ ] App hiển thị `AI LIVE` chỉ khi server báo live và request Gemini thành công; nếu stub thì ghi `AI STUB`.
- [ ] Manager Café B tạo và duyệt v2; session mới ghim v2, session cũ giữ v1.
- [ ] Café A không truy cập dữ liệu Café B; quote không có trong transcript không được tính điểm.
- [ ] Hướng dẫn chạy backend, cấu hình URL và mở/build project Android Studio được ghi vào tài liệu bàn giao.
- [ ] Demo 3 phút đã rehearsal; số liệu người dùng/độ trễ chỉ trình bày khi đã đo thật.

## 8. Tài liệu tham chiếu

- [Execution Plan v1.1](../01_ShiftLens_Execution_Plan_v1.1.docx)
- [SRS v1.1](../02_ShiftLens_SRS_v1.1.docx)
- [Winning Masterplan](SHIFTLENS_WINNING_MASTERPLAN.md)
- [Mobile Android Expo skill](../.agents/skills/mobile-android-expo/SKILL.md)
- [ShiftLens architecture skill](../.agents/skills/shiftlens-architecture/SKILL.md)
