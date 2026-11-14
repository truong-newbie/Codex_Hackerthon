# Task C — Android Studio & APK build

**Branch:** `feat/task-c-android-studio-build`  
**Owner:** Người 3 — Android Studio & Build  
**Scope:** `mobile/android/` và các cấu hình Android cần thiết để mở, build, cài và chạy ShiftLens.

## Mục tiêu bàn giao

- Project Android Gradle được sinh từ Expo và lưu trong repository tại `mobile/android/`.
- Android Studio mở project và Gradle Sync thành công.
- `:app:assembleDebug` tạo APK cài được.
- Cài APK lên thiết bị/emulator, mở được app và kết nối tới API theo cấu hình.
- Ghi lại đường dẫn APK, phiên bản toolchain và lệnh để người khác build lại.

## Preflight trên máy hiện tại

Đã kiểm tra ngày 14/11/2026:

- Node.js `v24.12.0`, npm `11.6.2`.
- Android SDK có tại `D:\Android\Sdk`; đã có platform `android-35`, platform-tools và build-tools `34.0.0`, `36.0.0`. Chưa thấy build-tools `35.0.0`, NDK `26.1.10909125` hoặc CMake.
- Android Studio có tại `D:\Android Studio\bin\studio64.exe` (build `261.26222.65.2614.16204760`).
- Java trong PATH là `22.0.2`; JBR đi kèm Studio là Java `25.0.3`. React Native Gradle Plugin 0.76 gọi `jvmToolchain(17)`, nên Gradle cần JDK 17 riêng cho compile plugin; Java 22/JBR 25 không thay thế được toolchain đó.
- `ANDROID_HOME`/`ANDROID_SDK_ROOT` chưa có sẵn trong môi trường user; các lệnh CLI bên dưới đặt biến cho tiến trình build.
- Đã cài `mobile` dependencies bằng `npm ci` theo lockfile (879 packages) và chạy `npx expo prebuild --platform android`; `mobile/android` hiện đã tồn tại.
- AVD `Pixel_7_Pro` có sẵn và đã boot (`emulator-5554` xuất hiện ở ADB). Chưa có thiết bị USB được kết nối.
- Nếu Người 2 đổi dependency native (ví dụ AsyncStorage), phải chạy prebuild lại và build lại APK.

## Trạng thái thực thi hiện tại

- **Đã xong:** plan Task C; cài JS dependencies; Expo prebuild; Android project và Gradle wrapper được sinh; AVD đã boot.
- **Đã thử:** Gradle wrapper `8.10.2-all` bị reset kết nối khi tải. Dùng Gradle `8.9` đã có trong máy để kiểm tra; Gradle khởi động được với JDK 22 nhưng dừng ở bước tự tải JDK 17 cho RN Gradle Plugin. Việc cài Microsoft OpenJDK 17 qua `winget` đã được thử nhưng MSI chưa tải được trong môi trường mạng hiện tại.
- **Chưa nghiệm thu:** Android Studio Gradle Sync chưa xác nhận thành công; APK chưa build/cài vì chưa có toolchain JDK 17.
- **Sau khi có JDK 17:** cài thêm Android Build Tools `35.0.0` và NDK `26.1.10909125` từ SDK Manager nếu Gradle yêu cầu; sau đó sync/build lại.

## Trình tự thực hiện

### C1. Chụp trạng thái toolchain và thiết bị

Trong PowerShell:

```powershell
node --version
npm --version
java -version
& 'D:\Android\Sdk\platform-tools\adb.exe' version
& 'D:\Android\Sdk\platform-tools\adb.exe' devices
```

Mở Android Studio, vào **File → Settings → Build, Execution, Deployment → Build Tools → Gradle**, chọn JDK 17 làm Gradle JDK sau khi cài. Không chọn JBR 25 để build project Expo/RN này. Kiểm tra SDK Location trỏ tới `D:\Android\Sdk`; SDK Manager cần platform `android-35`, Build Tools `35.0.0`, NDK `26.1.10909125` (và CMake nếu Gradle yêu cầu). Nếu dùng điện thoại thật, bật USB debugging và chấp nhận RSA prompt; nếu dùng emulator, khởi chạy AVD trước khi cài APK.

**Gate C1:** `adb devices` liệt kê ít nhất một thiết bị ở trạng thái `device`; Android Studio tìm thấy SDK và JDK hợp lệ.

### C2. Cài JS dependencies và sinh project native

Từ repo root:

```powershell
Set-Location mobile
npm ci
$env:ANDROID_HOME = 'D:\Android\Sdk'
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
npx expo prebuild --platform android
```

Kiểm tra `mobile/android/settings.gradle`, `mobile/android/gradlew.bat`, `mobile/android/app/build.gradle` và `mobile/android/local.properties`. Nếu `local.properties` chưa có SDK path, tạo/cập nhật `sdk.dir=D:\\Android\\Sdk` (không commit file local này nếu chứa đường dẫn riêng máy). Không chạy `prebuild --clean` sau khi đã có chỉnh sửa native cần giữ.

**Gate C2:** `mobile/android/` và Gradle wrapper được sinh; prebuild kết thúc mã 0.

### C3. Mở Android Studio và Gradle Sync

Mở `D:\AndroidStudioProjects\Codex_Hackerthon\mobile\android` như một project Gradle. Chờ Sync hoàn tất; xử lý theo thứ tự:

1. Chọn JDK 17 trong Android Studio cho Gradle và toolchain; JBR 25/Java 22 không thỏa yêu cầu `jvmToolchain(17)` của React Native Gradle Plugin.
2. Cài SDK Platform/build-tools đúng phiên bản được Gradle yêu cầu qua SDK Manager.
3. Đảm bảo `sdk.dir` đúng, Gradle wrapper được giữ nguyên và mạng cho phép tải Gradle/Maven dependencies.
4. Chỉ sửa manifest/native config khi có lỗi cụ thể; thay đổi Expo config/plugin phải được phản ánh trong `app.json`/plugin rồi prebuild lại.

**Gate C3:** Android Studio báo Gradle Sync thành công, không còn lỗi SDK/JDK/Manifest.

### C4. Build APK debug và cài chạy

Từ Android Studio chọn **Build → Make Project** hoặc chạy:

```powershell
$env:ANDROID_HOME = 'D:\Android\Sdk'
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:JAVA_HOME = 'C:\Path\To\JDK17' # thay bằng thư mục JDK 17 đã cài
$env:PATH = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:PATH"
Set-Location D:\AndroidStudioProjects\Codex_Hackerthon\mobile\android
& .\gradlew.bat --version
& .\gradlew.bat :app:assembleDebug
```

APK đầu ra dự kiến:

```text
mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

Cài và mở app:

```powershell
& 'D:\Android\Sdk\platform-tools\adb.exe' install -r app\build\outputs\apk\debug\app-debug.apk
& 'D:\Android\Sdk\platform-tools\adb.exe' shell monkey -p com.shiftlens.training 1
```

Đặt API URL phù hợp thiết bị: emulator dùng `10.0.2.2` để tới host máy phát triển; điện thoại thật dùng IP LAN có thể truy cập hoặc HTTPS tunnel. Không dùng `localhost` trên điện thoại để trỏ về máy backend. Kiểm tra app mở được, đăng nhập và gọi được `/v1/health`/API. Debug build có thể cần Metro; nếu cần APK chạy độc lập, build thêm release và xác nhận JS bundle đã được nhúng, đồng thời cấu hình signing trước khi phân phối.

**Gate C4:** APK tồn tại, `adb install` thành công, app mở được và backend reachable từ thiết bị.

### C5. Lưu project và handoff

Giữ `mobile/android/` và các file Gradle wrapper trong git. Không đưa vào git `node_modules`, `app/build/`, `.gradle/`, keystore hoặc secret. Sau thay đổi của Người 2 đối với dependency native, chạy lại `npx expo prebuild --platform android`, Gradle Sync và `:app:assembleDebug`.

Handoff cần ghi:

- Đường dẫn APK và loại build (`debug`/`release`).
- Phiên bản Android Studio, JDK/Gradle và Android SDK đã dùng.
- Địa chỉ backend đã cấu hình, cùng hướng dẫn đổi sang IP/tunnel khác.
- Lệnh build lại và trạng thái cài/chạy trên emulator hoặc thiết bị thật.
- Lỗi còn mở và log liên quan nếu một gate chưa qua.

## Chia thời gian 3 giờ

| Mốc | Kết quả cần có | Việc của Người 3 |
|---|---|---|
| 00–15 phút | Môi trường và thiết bị sẵn sàng | Xác nhận Android Studio, SDK/JDK, adb, thiết bị; xử lý SDK Location/JDK trước khi code. |
| 15–35 phút | Native project được sinh | Chờ Người 2 chốt dependency; chạy `npm ci` và Expo prebuild; kiểm tra wrapper/config. |
| 35–65 phút | Gradle Sync xanh | Mở `mobile/android`, sửa đúng các lỗi SDK/JDK/manifest và tải dependencies. |
| 65–95 phút | APK debug đầu tiên | Chạy `:app:assembleDebug`, cài và ghi lỗi build nếu có. |
| 95–130 phút | Chạy được trên thiết bị | Cấu hình API URL reachable, mở app, phối hợp Người 2 sửa lỗi tích hợp; build lại sau native changes. |
| 130–160 phút | Bàn giao project/APK | Giữ native project trong git, xác nhận output APK và hướng dẫn rebuild. |
| 160–180 phút | Buffer và freeze | Rebuild cuối, rehearsal cài/mở app, ghi giới hạn debug/release và bàn giao. |

## Cut-line và xử lý sự cố

- Nếu Gradle không tương thích Java 22, chuyển Gradle JDK sang Android Studio JBR/JDK 17 trước khi sửa code.
- Nếu thiếu SDK package, dùng SDK Manager cài đúng platform/build-tools mà lỗi nêu; tránh đổi version AGP/Gradle tùy tiện.
- Nếu APK build được nhưng thiết bị không gọi API, kiểm tra URL, firewall, cùng mạng và HTTPS; không coi build thành công là E2E thành công.
- Nếu người 2 đổi native dependency muộn, ưu tiên một lần prebuild/build cuối và chốt dependency trước mốc phút 95.
- Không cắt project Gradle, APK cài được hoặc hướng dẫn build lại. Có thể bàn giao debug APK để phát triển; ghi riêng nếu chưa tạo được standalone release APK.
