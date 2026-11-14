# ShiftLens — Kế hoạch nâng cấp v1.2 và hướng dẫn thực thi cho AI

Ngày lập: 14/11/2026. Baseline: mã nguồn v1.1.0 đang có trong repository.

**Trạng thái tài liệu: đang triển khai.** Xem `docs/upgrade-v1.2/PROGRESS.md` để biết code đã sửa và giới hạn kiểm chứng. Các release gate vẫn để TODO tới khi có đủ bằng chứng.

Mục tiêu: đưa ShiftLens từ MVP demo thành phiên bản có chức năng đúng, phục hồi được khi lỗi, quản trị được nhiều SOP/nhân viên và có bằng chứng nghiệm thu trên Android thật. Không hứa “hoàn hảo tuyệt đối”; chỉ công bố đạt những điều kiện đã kiểm chứng.

## 1. Cách giao tài liệu này cho AI thực hiện

Có thể sao chép nguyên đoạn sau vào phiên làm việc mới:

> Hãy thực hiện kế hoạch trong `docs/SHIFTLENS_UPGRADE_PLAN_V1.2.md`. Trước tiên đọc `AGENTS.md`, các project skills liên quan, trạng thái Git và code thực tế. Thực hiện U00 đến U22 theo thứ tự phụ thuộc, sửa mã nguồn và thêm kiểm thử hồi quy cần thiết. Giữ nguyên thay đổi có sẵn của người dùng; không reset, xóa database vận hành hoặc seed đè dữ liệu. Hoàn thành mỗi hạng mục bằng code, kiểm thử phù hợp và cập nhật bằng chứng/trạng thái trong tài liệu. Không chỉ trả về một kế hoạch khác. Nếu thiếu key, thiết bị hoặc tài khoản triển khai, hoàn thành những phần độc lập và ghi rõ phần chưa được xác minh. Không khai báo Live/APK/production-ready khi chưa có bằng chứng. Không tự triển khai công khai, phát hành, mua dịch vụ hay dùng quota Live số lượng lớn khi chưa được giao phạm vi đó.

### 1.1 Quy trình làm việc bắt buộc

1. Đọc lại code ở thời điểm thực hiện: đường dẫn/dòng tham chiếu trong kế hoạch có thể đã thay đổi.
2. Ghi baseline: commit hiện tại, `git status --short`, phiên bản công cụ và thay đổi có sẵn. Tại lúc lập kế hoạch, `scripts/preflight_check.ps1` đang modified; không tự hoàn nguyên file này.
3. Tạo nhật ký tiến độ ở `docs/upgrade-v1.2/PROGRESS.md`, không chứa token, key, mật khẩu hay transcript thật của người dùng.
4. Làm tuần tự theo mặc định. Chỉ chia nhiều AI khi người giao việc cho phép; nếu có chia việc, phải chốt hợp đồng API và quyền sở hữu file trước.
5. Với mỗi Uxx: đọc file → mô tả thay đổi cụ thể → triển khai → kiểm thử có ý nghĩa → xem diff → cập nhật tiến độ.
6. Không chạy suite backend hiện tại trước khi hoàn thành U01. Fixture hiện tại có thể xóa database đang cấu hình.
7. Không chạy seed, migration thay đổi dữ liệu hoặc script reset trên database vận hành như một thao tác kiểm tra thông thường.
8. Dùng `rg` để tìm code; đọc `.env.example` để biết cấu hình. Không in `.env`, JWT, khóa ký APK hay URL database chứa mật khẩu vào log.
9. Nếu môi trường chặn một lệnh quan trọng, dùng quy trình xin quyền của môi trường; không tìm cách vượt giới hạn bằng công cụ khác.
10. Cài dependency bằng phiên bản tương thích với runtime đã chốt. Không nâng hàng loạt thư viện lên `latest` trong cùng đợt sửa lỗi nghiệp vụ.
11. Không sửa trực tiếp các file generated như OpenAPI/types nếu đã có generator; sửa nguồn rồi sinh lại.
12. Khi cần dừng phiên, ghi chính xác đã sửa gì, đã chạy gì, lỗi còn lại, Uxx tiếp theo và dữ liệu tạm nào đã tạo.

### 1.2 Mẫu cập nhật tiến độ

```text
Task: Uxx
Status: TODO | IN_PROGRESS | BLOCKED | DONE
Baseline commit:
Files changed:
Behavior implemented:
Checks run and results:
Evidence paths:
Remaining limitations:
Next task:
```

`BLOCKED` ở đây là trạng thái trong tài liệu, không phải lệnh điều khiển vòng đời agent. `DONE` chỉ dùng khi tiêu chí của task đã đạt. Nếu code xong nhưng thiếu thiết bị/credentials để nghiệm thu, ghi `IN_PROGRESS — implementation complete, external validation pending`.

## 2. Bối cảnh, phạm vi và những điều phải giữ

### 2.1 Sản phẩm hiện tại

- Buyer: quản lý/chủ quán cà phê; user: nhân viên mới hoặc part-time.
- Backend: FastAPI, Pydantic, SQLAlchemy; SQLite local, hướng tới PostgreSQL/Supabase.
- AI: Google GenAI với Compiler, Simulator, Evaluator; có `live` và `stub`.
- Android: Expo SDK 52, React Native 0.76.2, React 18.3.1, TypeScript; native project đã có trong `mobile/android`.
- Manager: trang `/studio` tích hợp backend và tài liệu REST cho Appsmith.
- Luồng: đăng nhập → chọn SOP approved → tạo phiên ghim version → 1–4 lượt hội thoại → đánh giá → xem lại kết quả.

### 2.2 Nguyên tắc không được phá

1. Tenant và quyền lấy từ xác thực server; không tin `tenant_id`/role trong body hoặc query của client.
2. Nội dung SOP và rubric đã approved không được sửa tại chỗ. Muốn thay đổi phải tạo draft version mới.
3. Phiên đã tạo giữ nguyên `sop_version_id`, kể cả khi version đó được supersede.
4. AI không được quyết định trọng số, điểm tổng, quyền, trạng thái phiên hay phê duyệt SOP.
5. Điểm đạt của tiêu chí phải có bằng chứng hợp lệ; thiếu/bịa quote không được cộng điểm. Critical không đạt thì cả bài không đạt dù điểm ≥70.
6. Result đã lưu là bất biến. Cập nhật scoring engine không tự chấm lại dữ liệu cũ.
7. Lỗi Live không được âm thầm trả dữ liệu stub rồi gắn nhãn Live.
8. Kết quả phục vụ luyện tập; không biến thành quyết định tuyển dụng/kỷ luật tự động.
9. Android APK phải có thể chạy độc lập; Expo Go hoặc typecheck không phải bằng chứng APK đã hoạt động.

### 2.3 Phạm vi v1.2

**Bắt buộc:** toàn bộ U00–U22, gồm sửa lỗi, SOP CRUD cần thiết, quản lý nhân viên trong tenant, báo cáo, bảo mật triển khai, migration, kiểm thử và bàn giao.

**Mốc phát hành:**

- **M1 — Core ổn định:** U00–U12; sửa luồng học và nền tảng bảo vệ dữ liệu.
- **M2 — Pilot tại quán:** thêm U13–U20; quản trị nhiều SOP/nhân viên, báo cáo, vận hành và APK.
- **M3 — Nghiệm thu v1.2:** U21–U22; có bằng chứng thực tế và tài liệu bàn giao.

**Để sau v1.2:** STT/realtime voice, camera/vision, nhập PDF/DOCX bằng AI, billing, tự đăng ký tenant công khai, tích hợp HR, chấm năng lực dài hạn, mở rộng đa quốc gia. Những phần này có roadmap ở mục 15; không tự đưa vào critical path.

### 2.4 Tài liệu nguồn

- `AGENTS.md`, `.agents/rules/project-rules.md`.
- Bốn skill trong `.agents/skills/`: architecture, backend, mobile, evaluation.
- `01_ShiftLens_Execution_Plan_v1.1.docx`, `02_ShiftLens_SRS_v1.1.docx`.
- `README.md`, `3H_BUILD_PLAN_ANDROID_STUDIO.md`, `docs/SHIFTLENS_WINNING_MASTERPLAN.md`.
- Code thực tế là bằng chứng hiện trạng; các dòng “tests pass”/“ready” trong tài liệu cũ không thay thế việc kiểm chứng bản mới.

## 3. Baseline audit và mức độ bằng chứng

Đã kiểm tra ở lượt audit trước khi lập kế hoạch:

- `node mobile/node_modules/typescript/bin/tsc --noEmit -p mobile/tsconfig.json`: exit 0.
- Đọc thấy 25 hàm test backend; chưa chạy lại vì `python`, `py`, `python3` không có trong PATH của shell đó. Không suy ra máy hoàn toàn không có Python.
- Chạy hàm `loadAnalytics()` hiện có bằng Node với DOM/fetch giả lập: HTML trong quote đi nguyên vào chuỗi gán `innerHTML`. Chưa chạy kiểm thử khai thác end-to-end bằng browser.
- Chưa kiểm chứng Gemini Live, APK, thiết bị thật, PostgreSQL hay deployment.

| Finding | Bằng chứng code hiện tại | Tác động | Task |
|---|---|---|---|
| A01 | `backend/tests/conftest.py` gọi `drop_all()` với engine ứng dụng | Có thể mất dữ liệu khi chạy test/preflight | U01 |
| A02 | `studio_router.py` chèn quote vào `innerHTML` | Stored/DOM XSS khi quản lý xem báo cáo | U02 |
| A03 | UI không khóa chấm điểm khi đang gửi; backend chưa bảo vệ thao tác đồng thời | Result có thể lệch transcript, lượt trùng, lỗi khi đánh giá đồng thời | U06, U11 |
| A04 | Stub evaluator `break` khi gặp câu đạt C3 | Có thể bỏ qua vi phạm ở lượt sau | U07 |
| A05 | Quote verifier nối toàn bộ lượt trước khi tìm substring | Chấp nhận quote ghép qua ranh giới lượt | U07 |
| A06 | Mobile thêm tin trước response, không đánh dấu lỗi; lỗi resume xóa session ID | UI lệch server, mất khả năng tự khôi phục | U10, U11 |
| A07 | `live_ready` chỉ nhìn key/mode; lịch sử dùng mode hiện tại | Nhãn không chứng minh AI thực sự đã chạy, sai provenance phiên cũ | U08 |
| A08 | Café B: steps/rubric/UI khác chính sách; preset áp dụng cả Café A | Dạy và chấm theo quy tắc không thống nhất | U07, U13, U14 |
| A09 | Analytics lấy 50 phiên rồi tính tổng; lịch sử chỉ 20 phiên | Báo cáo bị giới hạn mà UI không nói rõ, mất khả năng tìm phiên cũ | U15 |
| A10 | Type approve response sai; `completed` có hai nghĩa | Client mới dễ xử lý sai trạng thái | U05 |
| A11 | Auth restore không `/me`, không xử lý 401 tập trung | Token hết hạn vẫn trông như đăng nhập | U09, U10 |
| A12 | Salt/password demo, secret mặc định, token AsyncStorage | Không phù hợp phân phối công khai | U03, U09, U10 |
| A13 | Docker `COPY . .`, chưa có `.dockerignore`, local có `.env`/DB | Khi build local theo context backend có thể đóng gói secret/data | U17 |
| A14 | Release Android ký debug key, cleartext được bật | Thiếu cấu hình phát hành chuẩn | U18 |
| A15 | Chưa có migrations/driver PostgreSQL/backup workflow | Nâng schema và chuyển DB chưa được bảo đảm | U04, U17 |
| A16 | Test dùng state chung; test TTS/recovery chỉ kiểm tra API/text | Coverage chưa chứng minh tính năng trên điện thoại | U01, U19, U21 |
| A17 | Studio chỉ lấy SOP đầu tiên, chưa có tạo SOP mới/user lifecycle | Chỉ phục vụ được demo seed giới hạn | U13, U14, U16 |

Các finding về race condition là kết luận từ luồng code, phải bổ sung bài tái hiện tự động khi triển khai; không ghi chúng là kết quả load test đã chạy.

## 4. Thiết kế đích cần thống nhất trước khi sửa nhiều file

### 4.1 Ranh giới module và cấu trúc đề xuất

Giữ FastAPI + Expo. Tách logic nghiệp vụ ra service khi cần, không viết lại framework.

```text
backend/
  app/
    main.py                       # create_app/lifespan, không tự mutate DB lúc import
    config.py                     # config có validation theo môi trường
    database.py                   # engine/session factory có thể inject
    models.py
    schemas.py                    # tách package schemas/ chỉ khi file quá lớn
    routers/
      ...                         # giữ router hiện có
      operations_router.py        # trạng thái request thuộc user hiện tại
      accounts_router.py          # manager quản lý nhân viên trong tenant
    services/
      training_service.py         # state/operation orchestration
      operation_service.py        # reservation, idempotency, lease/fencing
      evidence_service.py         # match quote trong từng lượt
      analytics_service.py
      audit_service.py
      ...
    static/studio/                # JS/CSS riêng, DOM safe
  migrations/                     # Alembic
  tests/                          # DB riêng, không dùng DB vận hành
mobile/
  src/
    api/                          # typed errors và contracts
    context/
    hooks/                        # session/recovery/TTS nếu phù hợp
    components/                   # UI dùng lại
    screens/
    utils/                        # secure auth storage, ordinary preferences
scripts/
  preflight_check.ps1             # kiểm tra read-only theo mặc định
  run_tests.ps1                   # test env isolated
  export_openapi.py
docs/upgrade-v1.2/
  PROGRESS.md
  API_CONTRACT.md
  MIGRATION_RUNBOOK.md
  RELEASE_EVIDENCE.md
  AI_QUALITY_REPORT.md
```

Tên file mới là đề xuất; AI được điều chỉnh tổ chức file nếu giữ đúng trách nhiệm và ghi lại quyết định. Không tạo lớp abstraction chỉ để bọc lại một dòng code.

### 4.2 Trạng thái phiên và lượt thoại

Trạng thái canonical của phiên: `active`, `evaluating`, `evaluated`. Có thể thêm `abandoned` khi có chức năng kết thúc bỏ dở rõ ràng; không cần thêm trong đợt sửa đầu.

```text
active + 0..3 lượt -> nhận một lượt mới thành công -> active + 1..4 lượt
active + 1..4 lượt -> reserve evaluate -> evaluating
evaluating -> AI lỗi/validation lỗi -> active, còn nguyên transcript
evaluating -> lưu result thành công -> evaluated
evaluated -> evaluate lại -> trả result đã lưu
evaluated -> gửi lượt mới -> 409 SESSION_COMPLETED
```

- Đủ 4 lượt có nghĩa `dialogue_exhausted=true`, chưa đồng nghĩa đã chấm điểm.
- `evaluation_completed=true` chỉ khi có result được lưu thành công.
- Mỗi phiên chỉ có một thao tác mutate đang có quyền hoàn tất. Start phiên dùng operation riêng trước khi session được tạo.
- Khi bắt đầu, reserve operation cùng snapshot SOP approved hiện tại. SOP đổi trong lúc compiler chạy không làm đổi snapshot đã chọn.
- Thời điểm “bắt đầu phiên” cho pinning là thời điểm server reserve start operation và chọn version, không phải lúc AI trả xong.

### 4.3 Request trùng, concurrency và phục hồi

Thêm `Idempotency-Key` cho `start`, `turn`, `evaluate`; mobile sinh UUID và lưu trước khi gửi.

Operation tối thiểu gồm: `id`, owner/tenant, kind, resource/session ID nếu có, key, hash payload chuẩn hóa, status, attempt, lease expiry, fencing token/revision, response snapshot, error code và timestamps.

| Trường hợp | Hành vi yêu cầu |
|---|---|
| Key chưa tồn tại | Reserve nguyên tử, xử lý đúng một thao tác được phép hoàn tất |
| Cùng key + cùng payload, đã thành công | Trả lại kết quả đã lưu; không tạo lượt/phiên mới |
| Cùng key + payload khác | 409 `IDEMPOTENCY_CONFLICT` |
| Cùng key đang chạy | 409 `OPERATION_IN_PROGRESS`, có operation ID và gợi ý thời gian kiểm tra lại |
| Key khác nhưng session đang bận | 409 `SESSION_BUSY`; không gửi lời gọi AI thứ hai |
| Kết nối mobile timeout sau khi server lưu | Poll trạng thái operation hoặc replay cùng key để nhận kết quả |
| Operation thất bại có thể thử lại | Retry có chủ đích cùng key/payload, attempt mới phải được reserve nguyên tử |
| Worker chết/lease hết hạn | Recovery dùng CAS và fencing; worker cũ không được ghi đè kết quả mới |

Yêu cầu triển khai:

1. Transaction ngắn để kiểm tra quyền, trạng thái, revision và reserve operation; commit trước khi gọi AI.
2. Không giữ write lock SQLite hay transaction dài trong suốt thời gian chờ Gemini.
3. Sau AI, transaction thứ hai chỉ được ghi nếu operation vẫn giữ fencing token/revision phù hợp.
4. Ghi turn/result, cập nhật session và chốt operation trong cùng transaction.
5. Có unique constraint ở DB cho idempotency scope, `(session_id, turn_no)`, `(sop_id, version_no)` và một result/session.
6. Không chỉ dùng Python lock trong process vì nhiều worker/process có thể cùng nhận request.
7. Với SQLite dùng atomic conditional update/CAS phù hợp; với PostgreSQL dùng cơ chế transaction/lock phù hợp và cùng invariant.
8. Timeout phía client không chứng minh server đã hủy request. Không tự resend với key mới.
9. Không tuyên bố “exactly once gọi Gemini”: crash sau provider response nhưng trước DB commit có thể làm lời gọi ngoài bị lặp. Mục tiêu là không nhân đôi dữ liệu được commit; ghi nhận giới hạn chi phí này.
10. Giới hạn retention operation phải dài hơn cửa sổ client có thể replay; không tự purge operation đang pending hoặc result còn cần tham chiếu.

### 4.4 Quy tắc evidence và chấm điểm

- AI trả criterion ID, judgment, quote và ID lượt được trích. Server tự tính offsets, điểm và trạng thái verified.
- Quote phải thuộc đúng session, đúng speaker employee, trong một lượt đã commit trước evaluation snapshot.
- Chuẩn hóa Unicode NFC, chữ hoa/thường và whitespace theo chính sách đã kiểm thử. Giữ dấu tiếng Việt và dấu câu theo mặc định; không strip tùy tiện làm thay đổi nghĩa.
- Nếu cho phép whitespace/case normalization, phải map lại vị trí sang chuỗi gốc. Lưu/display substring gốc, không cắt chuỗi gốc bằng offsets của chuỗi normalized.
- Server tìm quote trong lượt được khai báo; không nối nhiều lượt, không fuzzy match hoặc dùng semantic similarity để thay exact match.
- Giới hạn độ dài quote phù hợp; quote trống/không khớp bị 0 điểm. Không coi một ngưỡng độ dài tùy ý là đủ chứng minh nội dung đạt.
- Judgment thiếu: 0 điểm cho tiêu chí tương ứng. ID ngoài rubric: loại và ghi reason. ID trùng/mâu thuẫn: không dùng “last wins”; tiêu chí đó không được tự cộng điểm, hoặc trả lỗi AI output để người dùng thử lại theo chính sách thống nhất.
- Evidence lưu `turn_id`, original quote, start/end offsets, verification reason và schema/scoring version. Phân biệt lỗi AI thiếu evidence với nhân viên thực sự vi phạm trong lời giải thích, dù rule critical hiện tại vẫn có thể làm kết quả không đạt.
- Mọi judgment critical phải xét toàn transcript. Một câu đúng trước đó không xóa vi phạm sau đó.
- Stub dùng quy tắc/dữ liệu mẫu được hỗ trợ rõ ràng; không giả vờ hiểu mọi rubric tùy ý. Rubric không được hỗ trợ phải trả hạn chế rõ hoặc kết quả bảo thủ có lý do, không tự gán C1..C4 theo vị trí.
- Live evaluator vẫn là thành phần suy luận; quote đúng không đồng nghĩa judgment đúng. Có bộ golden cases do người review để đo false pass/false fail.
- Coach tip không được bịa chính sách ngoài SOP hoặc khẳng định nhân viên đã đủ năng lực nghề nghiệp.

### 4.5 Chính sách dữ liệu demo chuẩn hóa

Không sửa lịch sử approved/result hiện có để khớp fixture mới. Quy tắc mới áp dụng cho database seed mới hoặc qua draft/approve có chủ đích.

Baseline fixture đề xuất cho v1.2:

- **Café A:** xin lỗi; xác minh hóa đơn/đồ uống; đề xuất pha lại; mọi hoàn tiền phải xin quản lý.
- **Café B v1:** xin lỗi; xác minh; được pha lại/đổi món tương đương với giá trị **nhỏ hơn 50.000đ**; ngoài ngưỡng thì xin quản lý. Không tự suy ra được hoàn tiền/voucher từ câu này.
- **Café B v2 demo:** nếu muốn minh họa bánh/voucher thì phải mô tả rõ các quyền và điều kiện đó trong cả steps và rubric. Không giữ một bên “VÀ” nhưng bên kia “HOẶC”.
- Kiểm tra boundary 49.999 / 50.000 / 50.001 theo đúng quy tắc `<50.000`; nếu quản lý muốn `≤50.000` phải sửa đồng bộ văn bản và test.
- Ngưỡng/số tiền cần metadata policy có cấu trúc nếu server áp dụng rule tất định. Không cố suy luận số tiền chính xác chỉ từ việc câu có chuỗi `50`.
- Đây là fixture giả định phục vụ demo; khi pilot phải để quản lý xác nhận chính sách thật.

### 4.6 AI mode, health và nguồn dữ liệu

- `AI_MODE` chỉ nhận `live` hoặc `stub`; giá trị sai làm cấu hình thất bại rõ ràng, không rơi vào stub ngầm.
- Phân biệt `configured`, `availability=unknown|available|unavailable`, `last_checked_at`, `last_success_at`, `last_error_code`.
- Giữ compatibility field `live_ready`, nhưng định nghĩa cụ thể là trạng thái sẵn sàng theo kiểm tra gần nhất; chưa probe thì không gọi là đã xác minh Live.
- Health thường xuyên không được tạo lời gọi Gemini tốn tiền. Probe có timeout, cache và rate limit; thao tác probe chỉ dành manager/operator hoặc CLI được cho phép.
- Cấu hình thiếu key ở Live: training/probe trả 503; hệ thống còn khả năng trả health với lý do cấu hình, không trả stub.
- Mỗi AI operation lưu mode thực tế, model, prompt version, latency, timestamp và trace ID; không lưu secret.
- Không dùng `settings.AI_MODE` hiện tại để diễn giải lịch sử. Phiên hỗn hợp phải hiển thị mixed/chi tiết từng operation; phương án mặc định là pin execution profile khi start và từ chối tiếp tục nếu profile đó không còn khả dụng, kèm hướng dẫn tạo phiên mới.
- Phiên legacy không có metadata: `unknown/legacy`, không tự gán live hoặc stub. Result cũ có `ai_mode` chỉ chứng minh mode ghi ở kết quả đó, không chứng minh cả compiler/simulator đã dùng cùng mode.

### 4.7 Hợp đồng API và tương thích

Giữ API v1 hiện có hoạt động qua adapter. Các mutation v1 cũng phải chạy chung service an toàn; không để đường cũ bypass khóa/rate limit/tenant guard.

| API | Thay đổi đích |
|---|---|
| `POST /v1/auth/login`, `GET /v1/auth/me` | Typed error; tài khoản/membership active; token revocation/version |
| `GET /v1/health` | Health schema có kiểu, readiness và timestamp rõ nghĩa |
| `POST /v1/training/start` | Idempotency; snapshot version; AI provenance |
| `POST /v1/training/{id}/turn` | Idempotency; state/revision; `dialogue_exhausted`, `evaluation_completed` |
| `POST /v1/training/{id}/evaluate` | Một result bất biến; concurrency-safe; evidence version |
| `GET /v1/training/{id}` | Committed transcript, canonical status, pending operation thuộc owner |
| `GET /v1/training/sessions` | Giữ shape list cũ, document giới hạn legacy |
| `GET /v2/training/sessions` | Envelope phân trang: `items`, `next_cursor`, tùy chọn total |
| `GET /v1/operations/{id}` | Chỉ tenant + owner; status và response an toàn cho retry/recovery |
| `POST /v1/sops` | Manager tạo SOP mới và draft đầu tiên; tenant lấy từ auth |
| `POST /v1/admin/sops/{id}/draft` | Giữ API, có provenance/base version và validation |
| `PATCH /v1/admin/sop-versions/{id}` | Chỉ draft; yêu cầu expected revision, conflict 409 |
| `POST /v1/admin/sop-versions/{id}/approve` | Atomic approve; check revision; response đúng `ApproveResponse` |
| `POST /v1/admin/sops/{id}/archive` | Chặn phiên mới; giữ history/version/result |
| `GET /v2/sops` | Danh sách/filter/pagination; employee chỉ active approved theo quyền |
| `GET /v2/admin/analytics` | Metrics toàn tập theo filter; recent_sessions phân trang riêng |
| `GET /v1/admin/training/{id}` | Manager trong tenant xem transcript/evidence; không dùng employee route để nới ownership |
| `/v1/admin/employees` và lifecycle routes | Tạo/mời/vô hiệu hóa nhân viên; không cho manager tự cấp role vượt quyền |

Quy tắc tương thích:

1. Mobile v1.2 dùng các trường trạng thái canonical mới. Không tiếp tục dựa vào `completed` của turn response cũ.
2. Giữ nghĩa legacy của `completed` trên adapter v1 trong giai đoạn chuyển tiếp, document deprecated. Các API mới thống nhất `evaluation_completed`; chỉ bỏ field cũ trong đợt versioning sau.
3. Trước khi phát hành public, chốt policy idempotency cho client cũ: server vẫn khóa state khi thiếu key nhưng không bảo đảm replay sau timeout. Mobile mới luôn gửi key. Không tự suy ra key bằng nội dung vì người dùng có thể gửi hai câu giống nhau có chủ đích.
4. Response error có envelope additive: `error.code`, `error.message`, `request_id`, `retryable`, optional `operation_id`/`retry_after_seconds`; giữ `detail` tương thích trong v1.
5. Mã thống nhất: 401 auth không hợp lệ; 403 role/membership bị chặn; 404 resource ngoài tenant/owner; 409 state/revision/idempotency conflict; 422 input; 429 rate/quota theo quy ước; 502 provider/output lỗi; 503 cấu hình/provider unavailable; 504 vượt deadline.
6. Client không phân loại lỗi bằng cách so sánh chuỗi tiếng Việt. Không trả raw exception/key/provider request body cho người dùng.
7. Cập nhật `admin-appsmith/openapi.json`, mobile types và tài liệu Appsmith cùng đợt. Tạo contract check để phát hiện drift mà typecheck đơn thuần không phát hiện được.
8. Cursor phải được validate, sort ổn định bằng `(created_at,id)`, scope/filter nhất quán, giới hạn page size. Không đưa tenant từ cursor vào query mà bỏ auth scope.

### 4.8 Data migration và dữ liệu cũ

Thêm Alembic. Tạo schema bằng migration; import app/export OpenAPI không được tự tạo bảng.

Entity/field mới dự kiến:

| Entity | Nội dung |
|---|---|
| TrainingSession | canonical state, revision, pinned execution profile; không thay version đã pin |
| Operation | idempotency key scope, payload hash, status, lease/fencing, response snapshot |
| Turn | unique session/turn number, operation ID, metadata AI cần thiết |
| TrainingResult | evidence schema version, scoring version, transcript revision/hash; payload cũ giữ nguyên |
| SOPVersion | unique sop/version number, revision cho draft, base version, optional policy metadata |
| SOP | archived timestamp/status; active pointer giữ đúng version cùng SOP |
| Account/Membership | active flag, auth/token version, credential lifecycle |
| AuditEvent | actor/tenant/action/resource/version/time/request ID; metadata được lọc |

Quy trình migration:

1. Backup bằng phương pháp nhất quán với DB: SQLite backup API hoặc dừng writes rồi copy; không copy mù file DB đang có WAL/writes. PostgreSQL dùng backup/dump phù hợp.
2. Thử restore backup trên DB khác trước khi sửa DB chính.
3. Scan read-only: duplicate turn number/version number, orphan FKs, result/session mismatch, active pointer ngoài SOP, nhiều approved active không nhất quán.
4. Báo cáo conflict để xử lý có chủ đích; không tự xóa hoặc gộp lịch sử để thêm unique constraint cho qua.
5. Apply migration trên bản sao. Backfill trạng thái: có saved result → evaluated; chưa result → active; dữ liệu bất thường phải được báo cáo riêng.
6. Legacy AI metadata để unknown, không lấy môi trường hiện tại điền vào lịch sử.
7. Không rewrite result payload lịch sử. Nếu response schema mới cần trường bổ sung, dùng read adapter có nhãn legacy và nullable fields.
8. Kiểm tra row counts, IDs, version pins, transcript và checksum result trước/sau.
9. Deploy theo expand → migrate → switch reads/writes. Chưa xóa cột cũ trong v1.2.
10. Rollback app chỉ khi phiên bản cũ đọc được schema đã expand. Nếu đã có writes theo schema mới, không downgrade/drop mù; dùng forward fix hoặc restore theo runbook với đánh giá phần dữ liệu mới.

### 4.9 Cấu hình bổ sung và quản trị dữ liệu pilot

Tên biến bên dưới là contract cấu hình đề xuất, cần được implement/document cùng U03/U17; không giả định chúng đã có tác dụng trong code v1.1.

| Cấu hình | Quy tắc |
|---|---|
| `ENVIRONMENT` | Enum development/test/staging/production; không suy ra môi trường từ hostname |
| `AI_MODE` | Enum live/stub; live thiếu key báo unavailable rõ ràng |
| `DEMO_MODE` | Production mặc định false; không tự seed/tạo preset credentials |
| `SECRET_KEY` | Secret ngẫu nhiên mật mã tối thiểu 32 bytes entropy cho HS256; không chấp nhận chuỗi demo |
| `DATABASE_URL` | Mỗi môi trường riêng; test runner tạo engine test riêng thay vì tái sử dụng URL vận hành |
| `CORS_ORIGINS` | Allowlist chính xác cho frontend được phép ở staging/production |
| `AI_REQUEST_TIMEOUT_SECONDS` | Deadline provider được kiểm chứng theo SDK; không chỉ timeout phía mobile |
| `OPERATION_LEASE_SECONDS` | Lớn hơn deadline xử lý dự kiến hoặc có heartbeat; hết lease cần fencing khi retry |
| `MAX_CONCURRENT_AI_OPERATIONS` | Giới hạn concurrency có hiệu lực trên toàn deployment; giá trị chốt sau benchmark stub |
| `ACCESS_TOKEN_TTL_MINUTES` | TTL được document, mobile xử lý hết hạn; không đổi tùy ý mà thiếu auth tests |
| `EXPO_PUBLIC_API_URL` | Public config trong APK, tuyệt đối không chứa key/credentials |

Quản trị dữ liệu tối thiểu cho pilot:

- Chỉ thu thập account, SOP và dữ liệu hội thoại phục vụ học; chưa ghi âm hay thu ảnh nếu chưa có tính năng/consent tương ứng.
- Công bố nơi lưu dữ liệu, ai xem được transcript, mục đích đào tạo và chính sách retention trước khi dùng dữ liệu nhân viên thật.
- Cấu hình thời gian lưu theo yêu cầu đã được chủ hệ thống xác nhận; không tự đặt lịch xóa dữ liệu hiện có khi chưa thống nhất.
- Local pending messages phải được xóa sau reconcile thành công hoặc theo policy đã document; logout phải dọn cache theo account. Không để nội dung hội thoại thật trong crash reports mặc định.
- Quy trình export/delete theo yêu cầu phải xác thực actor/tenant, có audit và xử lý cả backup theo chính sách. Tính bất biến của kết quả nghĩa là không sửa điểm âm thầm; không có nghĩa cấm mọi quy trình xóa dữ liệu được ủy quyền.
- U17/U22 phải bàn giao runbook dữ liệu và quyền truy cập; nếu retention/export/delete chưa có UI, ghi rõ đường vận hành có kiểm soát và hạn chế đó.

## 5. Backlog thực thi và thứ tự phụ thuộc

Priority: P0 = dữ liệu/tính đúng hoặc chặn nghiệm thu; P1 = cần cho pilot sử dụng thực; P2 = nâng chất lượng/vận hành. “Nhỏ/vừa/lớn” là độ rộng công việc, không phải cam kết thời gian.

| ID | Hạng mục | Priority | Phụ thuộc | Quy mô | Trạng thái |
|---|---|---|---|---|---|
| U00 | Baseline, công cụ, bảo vệ thay đổi có sẵn | P0 | — | Nhỏ | DONE |
| U01 | Test isolation và preflight an toàn | P0 | U00 | Vừa | IN_PROGRESS |
| U02 | Sửa XSS Manager Studio | P0 | U01 | Vừa | IN_PROGRESS |
| U03 | Config validation và lỗi có cấu trúc | P0 | U01 | Vừa | IN_PROGRESS |
| U04 | Migration và ràng buộc DB | P0 | U01,U03 | Lớn | IN_PROGRESS |
| U05 | API contract/mobile types/versioning | P0 | U03,U04 | Vừa | IN_PROGRESS |
| U06 | State, idempotency và concurrency | P0 | U04,U05 | Lớn | TODO |
| U07 | Evidence, scoring và fixture policy | P0 | U04,U05,U06 | Lớn | IN_PROGRESS |
| U08 | AI gateway, timeout, provenance/readiness | P0 | U03,U06,U07 | Lớn | IN_PROGRESS |
| U09 | Auth, authorization và rate limits | P0 | U03,U04,U05 | Lớn | IN_PROGRESS |
| U10 | Mobile auth/storage/recovery nền tảng | P0 | U05,U08,U09 | Vừa | IN_PROGRESS |
| U11 | Mobile hội thoại và retry an toàn | P0 | U06,U07,U10 | Lớn | IN_PROGRESS |
| U12 | TTS, validation, accessibility và UI lỗi | P1 | U10,U11 | Vừa | TODO |
| U13 | SOP lifecycle đầy đủ | P1 | U04,U05,U07,U09 | Lớn | IN_PROGRESS |
| U14 | Manager Studio usable, nhiều SOP | P1 | U02,U13 | Lớn | IN_PROGRESS |
| U15 | Analytics, history và manager evidence | P1 | U05,U07,U09,U13 | Vừa | IN_PROGRESS |
| U16 | Quản lý nhân viên trong tenant | P1 | U04,U09,U14 | Lớn | TODO |
| U17 | Docker, CI, secrets, backup và staging | P0 trước public | U03,U04,U09 | Lớn | IN_PROGRESS |
| U18 | Android release/EAS và môi trường mạng | P0 trước release | U10,U11,U12,U17 | Lớn | TODO |
| U19 | Regression/integration/security matrix | P0 | U01–U18 | Lớn | TODO |
| U20 | Observability và benchmark thực tế | P1 | U08,U15,U17,U19 | Vừa | IN_PROGRESS |
| U21 | E2E Android + Gemini + pilot review | P0 | U18,U19,U20 | Lớn | TODO |
| U22 | Tài liệu, release evidence và bàn giao | P0 | U00–U21 | Vừa | IN_PROGRESS |

U19 là đợt tổng hợp kiểm thử; không đợi tới U19 mới viết regression test cho lỗi đang sửa. Những task không phụ thuộc nhau có thể đổi thứ tự nếu nhật ký giải thích rõ.

## 6. Chi tiết từng hạng mục

### U00 — Chốt baseline và môi trường

**Files:** không sửa nghiệp vụ; đọc Git, manifests, docs; tạo `docs/upgrade-v1.2/PROGRESS.md`.

- Ghi branch/commit/status, danh sách file dirty/untracked liên quan. Không tự commit thay đổi của người dùng.
- Xác định Python executable thực tế, Node/npm, Java, Gradle wrapper, Android SDK/adb. Không suy luận phiên bản Python từ câu “đang chạy 3.15” trong skill.
- Ưu tiên baseline Python 3.12 phù hợp Docker hiện tại nếu môi trường cho phép; xác nhận dependency compatibility trước khi chốt.
- Xác định dependency đã cài; giữ `package-lock.json`. Nếu cần cài lại, dùng workflow lockfile và xin quyền mạng theo môi trường.
- Ghi dữ liệu DB hiện hữu cần bảo tồn bằng metadata/count sau khi có công cụ đọc an toàn, không in nội dung nhạy cảm.
- Ghi preflight hiện tại chỉ là script kỹ thuật, chưa chứng minh Live/Android.

**Đạt khi:** có baseline, công cụ đã xác định hoặc blocker cụ thể; thay đổi có sẵn được giữ nguyên; AI biết DB nào tuyệt đối không được dùng cho test.

### U01 — Tách database test và sửa preflight

**Files:** `backend/tests/conftest.py`, `app/database.py`, `app/main.py`, `app/config.py`, `scripts/run_tests.ps1`, `scripts/preflight_check.ps1`; thêm test config nếu cần.

- Refactor `create_app()`/dependency injection để test thay engine/session trước khi app sử dụng DB.
- Bỏ `Base.metadata.create_all()` khỏi import side effect. Dev init dùng command riêng; production dùng migration.
- Fixture dùng SQLite file trong temp directory riêng hoặc DB test ephemeral. Concurrency tests không dùng cùng một connection in-memory để giả lập nhiều connection.
- Mỗi test dữ liệu độc lập; seed test factory theo nhu cầu; xóa phụ thuộc “previous test tạo Café B v2”.
- Force stub ở deterministic suite; Live tests tách marker/config, không chạy mặc định.
- `drop_all` chỉ được phép với engine test được tạo nội bộ và đường dẫn đã kiểm tra; tốt hơn tạo/xóa temp DB theo fixture lifecycle.
- Preflight mặc định read-only, không seed/reset; lựa chọn chạy tests vẫn dùng test DB riêng.
- Kiểm tra exit code ngay sau mỗi external process, kể cả seed khi người dùng chủ động yêu cầu seed.
- Output `PASS/FAIL/SKIPPED/NOT_VERIFIED` từng gate. Không in “ready for live demo” chỉ vì thấy file/pytest pass.
- Network IP detection xử lý máy không có `Get-NetIPAddress`/adapter phù hợp; hiển thị địa chỉ có thể lựa chọn thay vì khẳng định IP đầu tiên luôn đúng.

**Kiểm thử:** production-like canary DB độc lập có record đánh dấu; chạy suite isolated; chứng minh canary không đổi. Chạy một test riêng và đổi thứ tự tests vẫn đúng. Export OpenAPI không tạo DB.

**Đạt khi:** chạy test/preflight không làm thay đổi database vận hành, không tiêu quota AI, không phụ thuộc thứ tự.

### U02 — Hiển thị Studio an toàn

**Files:** `studio_router.py`; có thể tách JS/CSS sang `app/static/studio/`; thêm browser tests.

- Thay nội suy dữ liệu không tin cậy vào `innerHTML` bằng DOM nodes + `textContent`.
- Áp dụng cho quote, tên nhân viên, tên tenant, rubric ID, SOP title, explanation và error messages; không chỉ sửa một chỗ.
- Giữ markup template tĩnh nếu cần, nhưng không ghép dữ liệu vào HTML/event attributes.
- Dùng `addEventListener` thay onclick ghép chuỗi ID. Không render Markdown/HTML từ AI như nội dung tin cậy.
- Không log access token từ login response ra panel; log redacted metadata.
- Nếu tách static resources, thêm CSP phù hợp; CSP hỗ trợ bảo vệ, không thay cho sửa unsafe rendering.

**Kiểm thử:** quote/tên/rubric có dấu `<`, `>`, `&`, dấu nháy, thẻ HTML và event attribute được hiện thành text; không chạy script/khởi tạo request ngoài. Dùng stub fixture chứng minh quote đi từ employee → result → manager view.

**Đạt khi:** UI giữ chức năng và mọi field không tin cậy được render như văn bản; có regression browser test.

### U03 — Cấu hình và error contract

**Files:** `config.py`, `main.py`, `schemas.py`, `.env.example`, AI/router exception handlers.

- Chuyển config sang schema validated, enum AI mode/environment; loại giá trị placeholder ở runtime readiness.
- Production bắt buộc secret đủ mạnh, không dùng demo default; debug accounts/presets chỉ bật bằng flag demo rõ ràng.
- Không buộc app chết khi thiếu key Live nếu yêu cầu health/fail-closed cần trả 503; phân biệt lỗi cấu hình không thể startup và dịch vụ AI unavailable.
- Global error handler có code/request ID, sanitized message; server log không lộ provider exception chứa secret.
- Đặt giới hạn input, page size, provider output, số concurrent operations và request budget bằng config có default/documentation.
- `DATABASE_URL` local dùng đường dẫn ổn định, không vô tình đổi DB theo cwd script. Có migration/runbook cho path cũ.
- Validate origins theo environment; production allowlist CORS phù hợp.

**Kiểm thử:** mode sai, missing/placeholder key, secret mặc định ở production, config DB sai; error shape nhất quán và không chứa sensitive values.

**Đạt khi:** cấu hình sai thất bại minh bạch, app không tráo Live thành Stub, API lỗi có thể xử lý bằng code.

### U04 — Migrations và DB invariants

**Files:** `models.py`, `database.py`, thêm `alembic.ini`, `migrations/`, dependency PostgreSQL, migration runbook.

- Thực hiện mục 4.8, migration baseline hỗ trợ cả DB mới và DB hiện hữu đã được scan.
- Không `stamp head` mù cho DB cũ; so sánh schema trước khi đánh baseline.
- Unique constraints cho version, turn, membership scope, operation và result; indexes cho tenant/user/time/session và filter analytics.
- Kiểm tra FK integrity; bật enforcement SQLite ở connection phù hợp. Active version phải thuộc SOP tương ứng, được service/DB bảo vệ theo thiết kế.
- Dùng timezone UTC nhất quán; serialize ISO 8601 có timezone. UI hiển thị theo locale.
- Tách DB URL test/dev/production, thêm driver PostgreSQL được pin phù hợp và kiểm thử thực sự.
- Audit append-only cho mutation quản trị; không nhét full transcript/secret vào audit metadata.

**Kiểm thử:** fresh migration; upgrade DB v1.1 mẫu có history; conflict detection; unique/FK checks; SQLite và PostgreSQL integration; old result checksums giữ nguyên.

**Đạt khi:** migration có thể tái hiện trên bản sao, rollback/forward-fix rõ, không tự xóa conflict.

### U05 — API contracts và type đồng bộ

**Files:** `schemas.py`, routers, `mobile/src/api/types.ts`, `client.ts`, `scripts/export_openapi.py`, `admin-appsmith/openapi.json`, `docs/upgrade-v1.2/API_CONTRACT.md`.

- Ghi request/response examples, enum/status/error semantics và migration compatibility theo mục 4.7.
- Sửa `approveSopVersion()` trả đúng `ApproveResponse`.
- Thêm canonical state fields, Turn ID, operation metadata và provenance; legacy fields có deprecation rõ ràng.
- Định nghĩa pagination envelope, cursor/filters, limit caps và ordering.
- Sinh OpenAPI không side effects. Chọn generator TypeScript hoặc contract tests kiểm tra shape với schema thật; typecheck không thay cho kiểm tra backend contract.
- Routes tĩnh phải không bị route `/{session_id}` bắt nhầm; test đường `/sessions`/operations/new endpoints.
- Hạn chế extra fields trên mutation; client gửi tenant/role giả phải bị từ chối hoặc bỏ qua theo contract nhất quán, tuyệt đối không ảnh hưởng scope.

**Đạt khi:** backend/mobile/Appsmith cùng contract, có compatibility check và không đổi shape list legacy âm thầm.

### U06 — Orchestration an toàn và idempotency

**Files:** `training_router.py`, `training_service.py`, `operation_service.py`, models/migrations, operation router.

- Triển khai đầy đủ mục 4.2–4.3, router chỉ authorize/validate/delegate/serialize.
- Start: cùng key chỉ tạo một session và một module được commit; version snapshot cố định từ reservation.
- Turn: kiểm tra capacity và revision nguyên tử; operation success gắn đúng một turn; turn số 5 không được commit.
- Evaluate: freeze snapshot transcript đã commit, đặt evaluating trước AI; không nhận turn mới trong thời gian đó; cùng session chỉ một result.
- Kết quả đánh giá lại trả payload đã lưu, kể cả sau restart/deploy; không gọi lại evaluator.
- SOP approval/draft numbering cũng phải có transaction/revision conflict guard, không dựa vào max+1 không bảo vệ.
- Không giữ database transaction dài xuyên lời gọi AI. Không để timeout 25 giây ở mobile trở thành nguyên nhân nhân đôi mutation.
- Recovery operation stale phải có lease/fencing; bài test worker cũ trả muộn không được ghi vào session đã tiến trạng thái.

**Kiểm thử:** dùng barrier/event và separate DB sessions, không chỉ sleep may rủi; hai send song song, hai evaluate, send/evaluate, start replay, timeout-after-commit, restart/stale lease, concurrent approve.

**Đạt khi:** mọi invariant đúng ở SQLite và PostgreSQL, không phát sinh 500 IntegrityError chưa xử lý từ thao tác lặp hợp lệ.

### U07 — Evidence, critical rule và policy fixtures

**Files:** `scoring_engine.py`, `ai_service.py`, `schemas.py`, `seed.py`, evidence service, scoring tests và golden fixtures.

- Sửa verify quote theo từng turn, Unicode/offset mapping và judgment validation ở mục 4.4.
- Stub critical scan toàn transcript; không dừng ở câu đạt đầu tiên. Kiểm thử câu đúng rồi sai, sai rồi đúng và phủ định.
- Không coi riêng từ “không” ở bất kỳ đâu là phủ định hành vi hoàn tiền. Phân biệt “không hoàn tiền” với “hoàn tiền không cần hỏi”.
- Không coi “không xin lỗi”, lặp tên rubric, “50” xuất hiện trong số lớn hơn hoặc chỉ từ “ạ” là bằng chứng đủ cho mọi tiêu chí.
- Tạo policy fixture thống nhất mục 4.5. Metadata rules phải được manager phê duyệt cùng version nếu dùng để chấm.
- Version scoring/evidence schema; giữ result cũ không đổi.
- Golden dataset tối thiểu bao phủ tất cả case trong Q matrix; đề xuất 30 hội thoại synthetic cân bằng đúng/sai/khó để human review, không giả là dữ liệu phỏng vấn thật.
- Báo cáo riêng “quote verification”, “semantic judgment”, “critical false pass”; không dùng một con số pass chung che khuất ba phần.

**Đạt khi:** fake/cross-turn/customer quote không được cộng điểm; critical violation ở bất kỳ lượt nào không bị câu đúng khác che mất trong tập rule hỗ trợ; golden fixtures có nhãn và giải thích.

### U08 — AI gateway và readiness trung thực

**Files:** `ai_service.py`, config, health schema/router, provenance model, error handlers.

- Dùng Google GenAI structured output hiện có; kiểm tra schema lẫn nội dung không trống, độ dài, duplicate/unknown criterion IDs.
- Tách system instruction khỏi dữ liệu SOP/transcript; serialize dữ liệu rõ ràng. Regex injection chỉ là tín hiệu phụ, không phải đảm bảo bảo mật.
- Pin model/prompt version theo operation và execution profile theo phiên; không ghi key vào snapshot.
- Deadline provider/operation phù hợp timeout client. Chọn cấu hình sau khi đo; ghi lại default, không tự tuyên bố SLA chưa đo.
- Retry bounded chỉ với lỗi transient phù hợp; giữ operation identity, có backoff/jitter; không retry vô hạn lỗi 4xx/schema/auth.
- Mapping lỗi quota/network/timeout/config/schema thành typed errors; đủ thông tin để retry manual, không raw stacktrace.
- Health/probe/cache và legacy mode theo mục 4.6. Manager UI/mobile hiển thị unavailable/unknown rõ ràng.
- Không sử dụng lời đáp cứng cho injection rồi ghi provenance “Gemini đã trả”; đánh dấu server guard response nếu chặn trước provider.

**Kiểm thử:** fake provider cho missing key, invalid key, 429, timeout, malformed JSON, blank content, duplicate IDs, provider trả muộn, injection trong SOP/history/current turn; không gọi mạng trong suite mặc định.

**Đạt khi:** Live lỗi có thông báo đúng, không fallback ngầm, nguồn AI được lưu theo operation và history không đổi nhãn theo config mới.

### U09 — Auth, tenant và rate limits

**Files:** `auth.py`, auth router, account/membership models, config, middleware/dependencies.

- Giữ auth nội bộ đã có cho v1.2 nhưng harden; chuyển Supabase Auth chỉ là milestone riêng nếu được chọn sau. Kết nối Supabase Postgres không đồng nghĩa dùng Supabase Auth/RLS.
- Password hash có salt riêng và thuật toán/tham số được kiểm tra theo hướng dẫn hiện hành; thêm hash scheme version, verify legacy và rehash sau login thành công.
- Không khóa người dùng cũ do đổi thuật toán mà không có migration/reset path.
- Validate exp/sub/issuer/audience theo policy đã chốt; user/membership disabled hoặc auth version đã đổi phải bị từ chối dù token chưa hết hạn.
- Chính sách session mặc định: access token có TTL được document và 401 yêu cầu login lại. Nếu thêm refresh token, phải làm đủ rotation, revoke, secure storage và replay detection; không thêm nửa vời.
- Logout có phương án revoke phù hợp; phân biệt logout thiết bị và revoke-all nếu triển khai nhiều session.
- Authorization tập trung: employee own session; manager tenant-scoped; employee không gọi manager mutation; resource khác tenant trả 404.
- Rate limit login và AI operations theo user/tenant/IP phù hợp, không tin X-Forwarded-For từ proxy chưa được cấu hình tin cậy.
- Nếu nhiều worker, store rate limit phải dùng chung hoặc enforce ở gateway; không quảng cáo global limit bằng dictionary từng process.
- Không cho client quyết định role/tenant của tài khoản được tạo; account creation manager chỉ cấp employee trong tenant hiện tại.

**Đạt khi:** auth hết hạn/revoked/disabled xử lý đúng; negative tests cho tenant và role đầy đủ; default demo credentials không hoạt động trong production seed.

### U10 — Mobile auth, storage và app bootstrap

**Files:** `AuthContext.tsx`, `utils/storage.ts`, `api/client.ts`, `LoginScreen.tsx`, `App.tsx`, thêm SecureStore tương thích SDK.

- Tách token vào SecureStore; URL/theme/preferences ở AsyncStorage.
- Migration token legacy: đọc → ghi secure store thành công → mới xóa token cũ. Không nuốt lỗi storage rồi báo đã lưu bền vững.
- Khi bootstrap có token, gọi `/me`; 401 xóa auth và về login, network timeout giữ thông tin cục bộ với trạng thái chưa xác thực/kết nối lỗi, không nhầm thành account invalid.
- Auth/client error giữ HTTP status, error code, request ID và retryable.
- URL validate scheme/host, trim; production chỉ HTTPS. Khi đổi server, reset scope auth/session/cache tương ứng, không gửi token server cũ sang host mới.
- Session/storage keys theo backend + user; logout/login người khác không khôi phục nhầm phiên.
- Không để response đang bay của user cũ ghi vào UI sau logout; dùng generation/request ownership guard.
- Bootstrap không giữ splash vô hạn vì health; phân biệt auth loading và health loading, có timeout và UI retry.

**Đạt khi:** token hết hạn có lối đăng nhập lại; restart giữ đúng account/server/session; lỗi lưu trữ được thông báo; không lộ state qua đổi user/server.

### U11 — Hội thoại, retry và khôi phục phiên

**Files:** `App.tsx`, `SimulationScreen.tsx`, `SopListScreen.tsx`, client, session hooks/storage.

- Message có `pending/sent/failed`, client operation ID và server turn ID. Tin server chưa xác nhận không được hiển thị như committed.
- Lưu pending request tối thiểu trước khi gửi để force-stop có thể reconcile; đánh giá nhu cầu mã hóa/retention nếu lưu nội dung hội thoại cục bộ.
- Giữ text khi lỗi; retry dùng cùng operation key. Timeout không tự tạo tin thứ hai.
- Khi resume: tải server state và operation status; reconcile theo IDs; không nối mù arrays gây trùng.
- Không xóa active session ID vì network error. 401 xử lý auth; 404/ownership mất quyền hiển thị lý do rồi xóa pointer phù hợp.
- Khóa send/evaluate/back theo transition cần thiết; nếu cho rời màn hình khi đang gửi, operation vẫn recover được, có thông báo rõ.
- Nút evaluate disabled khi loading, evaluating hoặc chưa có committed turn; send disabled khi evaluating.
- Bảo đảm unmount/late response không điều hướng sai hoặc ghi vào session khác.
- Sau 4 lượt chỉ cho chấm điểm/xem lại; sau evaluated không gửi thêm. Mở lại phiên completed hiện result và có khả năng xem transcript.
- Không tự xóa session server khi người dùng quay lại danh sách; hỗ trợ “tiếp tục học” rõ ràng.

**Đạt khi:** timeout-before-commit, timeout-after-commit, force-stop trong lúc gửi/evaluate và mất mạng khi resume đều không mất/nhân đôi committed data.

### U12 — TTS và trải nghiệm mobile

**Files:** Simulation/Result/Login/SOP screens, shared components/hooks, styles.

- TTS: onStart/onDone/onStopped/onError theo API SDK đang dùng; nút nghe/dừng, preference bật/tắt; dừng khi rời màn hình.
- Kiểm tra giọng vi-VN, thông báo fallback text khi không có; không nuốt lỗi âm thanh silently.
- UI input dùng giới hạn tương thích backend, counter và thông báo 2–1.000 ký tự; định nghĩa Unicode length nhất quán giữa JS/Python.
- Loading/empty/error/offline states ở từng màn hình; retry không tạo duplicate request.
- Quick replies/preset demo chỉ hiện trong demo flag; luồng luyện tập thật không tự bật câu trả lời chuẩn để làm sai ý nghĩa đánh giá.
- Giảm technical telemetry trên giao diện nhân viên; giữ chế độ debug/demo details cho người cần kiểm chứng.
- Responsive trên điện thoại nhỏ, keyboard không che ô nhập, safe area, font scale, contrast, accessibility labels/touch targets.
- Kết quả phân biệt “chưa có bằng chứng”, “quote không hợp lệ”, “vi phạm chính sách”; không diễn đạt mọi critical fail như đã chứng minh có hành vi sai.

**Đạt khi:** UI chạy được với font lớn, màn hình nhỏ, không có giọng Việt và mạng lỗi; hành vi chính vẫn rõ ràng.

### U13 — SOP lifecycle đầy đủ

**Files:** SOP/admin routers, `sop_service.py`, models/schemas/migrations, fixtures.

- Manager tạo SOP mới trong tenant, draft đầu tiên, xem/edit draft, tạo draft từ version đã có, approve, archive/unarchive theo policy.
- Validate steps/rubric IDs unique, text nonblank/length bound, trọng số integer dương tổng 100, critical flags, policy metadata schema.
- Draft revision tăng khi sửa; stale save/approve bị 409, không âm thầm ghi đè.
- Approve transaction chuyển active pointer và supersede version cũ nguyên tử. Một active approved version/SOP; race approve/create version được test.
- Employee không thấy draft hay SOP archived trong danh sách mở bài mới; vẫn truy cập phiên lịch sử của mình theo version pin.
- Không hard-delete SOP/version có lịch sử. Lưu audit actor/time/base version cho mutation.
- Không tự áp preset bánh/voucher cho mọi tenant; preset chỉ explicit demo action và phải có preview.

**Đạt khi:** một tenant có nhiều SOP và nhiều draft sử dụng được; version cũ/results không đổi; khác tenant không thấy/sửa/approve được.

### U14 — Manager Studio sử dụng thực tế

**Files:** Studio UI/static assets, SOP client/helpers, Appsmith README.

- Dropdown/list chọn SOP, tìm kiếm, trạng thái draft/active/archived; không còn `sops[0]` cố định.
- Form steps/rubric: thêm/sửa/xóa/sắp xếp; tổng trọng số hiển thị ngay; JSON editor chỉ là advanced option.
- Xem nội dung draft, so sánh base version với draft; approve đúng draft đang xem, không tự duyệt “latest” vô tình.
- Unsaved changes warning trong UI, loading/disable request mutation, giữ nội dung khi API lỗi.
- Login/logout manager rõ ràng; reject employee view đúng quyền; 401 reset auth, 403 hiển thị không có quyền.
- Dashboard hiển thị cả evidence đạt và không đạt, lý do, quote verified; mở full transcript qua manager endpoint scoped tenant.
- Xóa token/password khỏi log panel; debug details chỉ bật theo môi trường.
- Đồng bộ tài liệu/query mẫu Appsmith với API; không gọi `/studio` là Appsmith app đã cấu hình/host xong.

**Đạt khi:** manager thực hiện toàn bộ create→edit→review→approve→review results mà không cần sửa JSON thủ công; browser tests cho hai tenant và XSS giữ xanh.

### U15 — Analytics và lịch sử có thể tin cậy

**Files:** admin/training routers, analytics service, query indexes, mobile SOP/history screens, Studio dashboard.

- Aggregate trên toàn bộ tập dữ liệu được filter, không tính KPI từ page 50 records.
- Filter tenant bắt buộc; employee/SOP/version/date range/status optional; date range định nghĩa UTC rõ ràng.
- Tỷ lệ đạt = số completed results passed / số completed results trong filter; pending không tính denominator. Chưa có completed → giá trị/empty state được quy định rõ.
- Mặc định metric “nhân viên” không tính phiên tập thử của manager; nếu cho phép tính cả manager phải hiện filter rõ. Không dùng role hiện tại làm thay đổi lịch sử tùy tiện nếu cần snapshot participant role.
- History pagination, sorting stable, next cursor; metrics và recent list cùng filters nhưng query riêng.
- Tránh N+1 bằng join/eager load/aggregation; giới hạn response evidence; chi tiết tải theo nhu cầu.
- Manager đọc full transcript theo tenant, employee đọc own session; không nới quyền endpoint employee một cách ngầm.
- Có empty/loading/error states; cập nhật dashboard sau approve/phiên mới có refresh rõ ràng.

**Kiểm thử:** 0/1/>50 sessions, mixed pending/evaluated, manager practice, nhiều tenant/SOP, khoảng ngày và pagination không trùng/bỏ sót trên dữ liệu ổn định.

**Đạt khi:** KPI đúng theo truy vấn độc lập và không phụ thuộc page size.

### U16 — Vòng đời nhân viên và cửa hàng pilot

**Files:** accounts router/service, auth/models/migrations, Studio employee management.

- Manager tạo/mời employee vào tenant hiện tại; unique identifiers, input validation và audit.
- Mặc định invitation/activation token ngắn hạn, lưu hash token, single-use, expire, rate limit. Nếu chưa có dịch vụ email, cung cấp link/token cho manager qua kênh quản trị; không tự gửi email khi chưa được giao quyền gửi.
- Reset password/revoke access không trả password/token trong list responses/logs.
- Vô hiệu hóa membership/user theo quyền: manager chỉ quản lý membership trong tenant, không vô hiệu hóa toàn bộ account thuộc tenant khác.
- Employee disabled không tạo turn/evaluate mới, token còn hạn cũng bị chặn. Không xóa lịch sử học.
- Manager không tự nâng employee thành platform admin hoặc sửa manager khác ngoài policy. Tạo tenant/manager đầu tiên dùng operator CLI/bootstrap đáng tin, không public API nhận tenant tùy ý.
- Không mở self-service đăng ký tenant/billing trong v1.2. Multi-membership switch đầy đủ là đợt riêng; document hạn chế tenant hiện tại của login.

**Đạt khi:** quán pilot thêm nhân viên mới và thu hồi quyền được mà không sửa DB thủ công; tenant boundary giữ nguyên.

### U17 — Đóng gói, CI và vận hành an toàn

**Files:** `backend/Dockerfile`, thêm `.dockerignore` đúng context, requirements/lock, CI workflow, deployment/backup docs, scripts.

- Loại `.env*` thực tế, DB, keys, caches, tests artifacts và local config khỏi build image; giữ `.env.example` nếu cần tài liệu và không chứa secret.
- Image chạy non-root, dependencies reproducible, không `--reload`, health/readiness đúng; seed demo không tự chạy ở startup production.
- Migration là bước release riêng có kiểm soát; không để nhiều workers cùng migrate/seed.
- Dev/demo có flag seed rõ; production chỉ bootstrap có chủ đích. Test image không chứa fixture credentials/key/DB local.
- SQLite pilot cần volume bền vững và backup; production PostgreSQL phải có connection pooling, SSL/config phù hợp, quyền DB tối thiểu và backup restore được thử.
- CORS allowlist, HTTPS, proxy settings, rate limits, sanitized logs, secret injection qua environment/secret manager.
- CI: backend lint/check + isolated unit/integration; PostgreSQL service test; mobile typecheck/component tests; contract/OpenAPI drift; build artifacts có provenance.
- CI không dùng secrets Live cho mọi PR; Live smoke riêng được enable có chủ đích. Pin toolchain/lock phù hợp, audit dependencies theo mức phù hợp.
- Tạo runbook migrate/backup/restore/rollback, không tự deploy công khai chỉ vì CI xanh.

**Đạt khi:** build local/staging reproducible; image không có dữ liệu/secret local; restore backup đã được chứng minh ở môi trường riêng.

### U18 — Android release và mạng

**Files:** `app.json`, `eas.json`, native Gradle/manifest, `withCleartextTraffic.js`, env examples, build docs.

- Giữ native project và plugin đồng bộ. Trước `expo prebuild`, xem diff native và lưu thay đổi người dùng; không ghi đè mù.
- Tách dev/demo LAN HTTP với production HTTPS. Không bắt production manifest phải có cleartext=true trong preflight.
- Release signing dùng keystore riêng qua cấu hình bảo mật; không commit keystore/password. Debug keystore chỉ cho debug/demo phù hợp.
- EAS `preview` vẫn tạo APK cài trực tiếp; xác định rõ backend environment/profile và signing. Production package/versionCode upgrade hợp lệ.
- Build release có JS bundle, chạy khi Metro tắt; clean checkout có thể build bằng tài liệu/toolchain đã ghi.
- Validate config API trên emulator và máy thật; backend URL thuộc profile, không nhầm localhost/10.0.2.2 với IP điện thoại.
- Kiểm tra backup Android với SecureStore và local session preferences, reinstall/update behavior được document.
- Ghi SHA-256 APK, commit, profile, package ID, versionCode, signer fingerprint công khai và build command; không ghi private key.

**Đạt khi:** có APK release/preview hợp lệ, cài/mở được trên Android thật; bản public dùng HTTPS và signing đúng; thiếu thiết bị/key phải ghi pending, không đánh DONE bằng build config.

### U19 — Bộ kiểm thử hồi quy và tích hợp

**Files:** backend tests, mobile test setup, Studio browser tests, `docs/upgrade-v1.2/RELEASE_EVIDENCE.md`.

- Thực hiện matrix mục 8, mapping Qxx → test name/evidence path.
- Giữ tests deterministic, cô lập DB/provider/time khi cần; test business invariant, không chỉ mirror implementation.
- Tách unit, integration DB, contract, UI/component, browser, manual device và Live.
- Concurrency tests nhiều connections/workers phù hợp; không để lock một connection che race.
- Fault injection gồm lỗi AI, DB commit, network response loss và late response; không dùng API Live để tạo lỗi giả cho suite.
- XSS có test cả safe DOM unit và browser E2E; tenant test cả session, result, operation, SOP, account và analytics.
- Chạy legacy adapter tests để bản mobile cũ không bypass invariants.
- Các test audio/force-stop thật được ghi manual/device automation, không gán tên test API rồi coi như đã đạt thiết bị.

**Đạt khi:** mọi Qxx bắt buộc có test/evidence hoặc blocker cụ thể; không test phụ thuộc thứ tự; không fake pass Live/device.

### U20 — Quan sát vận hành và đo hiệu năng

**Files:** request logging/middleware, AI metrics, `scripts/benchmark_latency.py`, reports.

- Structured logs: request ID, operation ID, route, latency, status/error code, mode/model/prompt version; không log password/JWT/key/full transcript mặc định.
- Metrics: request/error rates, provider latency, operation pending/lease recovery, DB conflicts, invalid evidence, critical fail, retry count và token/cost nếu provider trả số liệu thật.
- Benchmark riêng HTTP end-to-end và provider timings. Script hiện dùng TestClient không đo mạng điện thoại/HTTPS; ghi rõ phạm vi đo.
- Chạy ít nhất 10 full live flows khi được cấp quota cho nghiệm thu, báo cả failures/retries; 10 mẫu là thăm dò, không đủ tuyên bố SLA production.
- P50/P95 chỉ tính trên mẫu hợp lệ và ghi sample size; không bỏ failure rồi báo thành công 100%. Export JSON/CSV aggregate không chứa secret.
- Load test bằng stub trước; xác định giới hạn concurrency bằng dữ liệu đo, không bắn load Live tốn tiền.
- AI quality report từ golden set human-reviewed; báo riêng false pass critical, false fail, quote rejection và mức không chắc chắn.

**Đạt khi:** tìm nguyên nhân request lỗi qua trace được, báo cáo latency/quality có nguồn và giới hạn rõ ràng.

### U21 — E2E trên thiết bị và nghiệm thu pilot

**Đầu vào cần có:** APK từ U18, backend HTTPS/staging, Gemini key/quota hợp lệ, Android thật, tài khoản tenant demo riêng, người review SOP/golden labels.

- Chạy kịch bản mục 9; lưu bằng chứng đã redacted, ngày/commit/device/network/mode.
- Cả Compiler, Simulator và Evaluator đều phải có operation Live thành công để công bố gate 3-module Live.
- Kiểm thử force-stop ở nhiều thời điểm, mất mạng, mở lại, token hết hạn và nhiều user/backend; không chỉ test mở app từ màn hình chính.
- Manager tạo SOP mới/draft/approve, A/B isolation, pinning v1/v2 và analytics >50 fixture riêng.
- Reviewer kiểm tra policies/quotes/critical decisions, không tự tạo lời chứng thực người dùng hoặc dữ liệu pilot.
- Vấn đề P0 còn mở chặn release. Hạn chế P1 có thể defer chỉ khi người phụ trách sản phẩm chấp nhận và release notes nói rõ.

**Đạt khi:** tất cả release gates bắt buộc có bằng chứng, không chỉ checklist tự đánh dấu.

### U22 — Bàn giao và tài liệu cuối cùng

**Files:** README, Appsmith README/OpenAPI, build/deploy/migration runbooks, release notes, progress/evidence files.

- README phản ánh đúng tính năng/command/requirements hiện có; bỏ số test pass cũ chưa tái kiểm chứng.
- Hướng dẫn onboarding dev, chạy stub/live, test isolated, tạo SOP/user, build APK, migrate và restore.
- Hướng dẫn người dùng cho manager/employee bằng ngôn ngữ nghiệp vụ, không yêu cầu hiểu IDs/schema để thao tác thường ngày.
- Ghi API compatibility/deprecations, legacy data handling, phiên bản scoring/prompt, hạn chế còn lại.
- Bump version nhất quán ở backend config, Expo app config, package metadata và native Android `versionName`/`versionCode`; kiểm tra phiên bản app thực tế và health khớp release manifest. Không tự đổi versionCode ngược so với APK đã phân phối.
- Nếu project skills cần cập nhật nhưng thư mục `.agents` bị bảo vệ/read-only, ghi đề xuất và xử lý theo quyền môi trường; không cố vượt quyền.
- Bàn giao commit/diff, artifacts, test summary, known limitations và hướng phát triển tiếp. Không tự publish/tag/merge nếu phạm vi người giao việc chưa bao gồm.

**Đạt khi:** người/AI mới có thể dựng môi trường, chạy kiểm thử an toàn và tiếp tục task mà không cần đoán lịch sử hội thoại.

## 7. Hướng dẫn kiểm thử và lệnh thực thi an toàn

### 7.1 Trước U01

Chỉ inventory/read-only/typecheck. Không chạy `scripts/preflight_check.ps1`, `scripts/run_tests.ps1` hoặc pytest cũ trên cấu hình ứng dụng đang có.

```powershell
git status --short
Get-Command python, py, python3, node, npm -ErrorAction SilentlyContinue
node mobile/node_modules/typescript/bin/tsc --noEmit -p mobile/tsconfig.json
```

Lệnh typecheck yêu cầu dependencies đã cài; nếu thiếu thì ghi prerequisite thay vì gọi đó là lỗi code.

### 7.2 Sau U01 và U03

Runner mới phải tự tạo test DB và stub provider; không yêu cầu người dùng nhớ đổi `DATABASE_URL` thủ công. Lệnh sau chỉ hợp lệ **sau khi runner đã được sửa và chứng minh isolation**:

```powershell
.\scripts\run_tests.ps1
node mobile/node_modules/typescript/bin/tsc --noEmit -p mobile/tsconfig.json
```

Dùng shell hiện hành và chính sách máy được phép; nếu chạy script bị chặn thì xử lý theo quy trình quyền của môi trường. Runner phải nhận Python path rõ ràng nếu `python` không có PATH và không tự download runtime ngầm.

### 7.3 Sau U04

Tạo command migration rõ ràng cho dev/test/staging. Lệnh `alembic upgrade head` chỉ chạy trên DB target đã xác nhận, có backup nếu DB có dữ liệu. Không thêm thao tác migration vào `export_openapi.py`.

### 7.4 Sau U17/U18

```powershell
# Từ mobile/android, sau khi toolchain/signing đã sẵn sàng:
.\gradlew.bat :app:assembleRelease

# Từ mobile, khi tài khoản EAS và phạm vi build đã được cho phép:
eas build -p android --profile preview
```

Build thành công không tự đánh dấu install/force-stop/Live. Những thao tác đó thuộc U21.

### 7.5 Quy tắc bằng chứng

- Ghi command, cwd, commit, exit code, ngày và phạm vi môi trường.
- Log CI/device phải redact dữ liệu nhạy cảm; test transcript dùng synthetic fixtures.
- Không chạy lại toàn bộ suite nhiều lần khi không có thay đổi liên quan; dùng targeted tests trong vòng sửa, suite đầy đủ tại gate tích hợp.
- Khi một check không chạy được, ghi `NOT_VERIFIED` cùng nguyên nhân; không biến môi trường thiếu công cụ thành pass hoặc kết luận code lỗi.

## 8. Ma trận nghiệm thu bắt buộc

Loại: U = unit; I = integration; C = contract; B = browser/component; D = Android device; L = Live có kiểm soát.

| ID | Tình huống | Kết quả cần chứng minh | Loại | Task |
|---|---|---|---|---|
| Q01 | Chạy tests khi có canary DB khác | DB ngoài fixture không đổi | I | U01 |
| Q02 | Chạy test riêng/đổi thứ tự | Không phụ thuộc state test trước | I | U01 |
| Q03 | Quote/tên/criterion chứa HTML | Hiện text, không thực thi HTML/script | B | U02 |
| Q04 | Mode sai, placeholder key, default secret prod | Fail đúng policy, không stub ngầm | U,I | U03 |
| Q05 | Migration DB v1.1 có history | IDs/pins/result payload không đổi | I | U04 |
| Q06 | Dữ liệu duplicate/orphan trước migration | Báo conflict, không xóa âm thầm | I | U04 |
| Q07 | Approve response và pagination | Mobile/OpenAPI/backend đồng bộ | C | U05 |
| Q08 | 4 lượt rồi gửi lượt 5 | Tối đa 4 committed turns, chưa auto evaluated | I | U06 |
| Q09 | Hai send cùng/khác key song song | Không trùng số lượt/không vượt capacity | I | U06 |
| Q10 | Send và evaluate đồng thời | Result đúng snapshot, không thêm turn sau chốt | I | U06 |
| Q11 | Hai evaluate đồng thời/replay sau restart | Một result, trả lại dữ liệu đã lưu | I | U06 |
| Q12 | Start cùng key, payload mismatch | Một session hoặc 409 conflict đúng nghĩa | I | U06 |
| Q13 | Client timeout sau server commit | Replay/poll không tạo duplicate | I,B,D | U06,U11 |
| Q14 | Lease hết hạn và worker cũ trả muộn | Fencing ngăn ghi sai | I | U06 |
| Q15 | Approve/version creation đồng thời | Một active pointer hợp lệ, version_no unique | I | U06,U13 |
| Q16 | Fake/customer/cross-turn quote | 0 điểm, reason đúng | U,I | U07 |
| Q17 | Unicode NFC, whitespace, case, offsets | Match policy đúng, display substring gốc | U | U07 |
| Q18 | Missing/unknown/duplicate judgment | Không tự cộng điểm hoặc last-wins | U,I | U07 |
| Q19 | Câu đúng rồi vi phạm critical | Không được pass do câu đúng trước đó | U,I | U07 |
| Q20 | Phủ định và số tiền 49.999/50.000/50.001 | Đúng quy tắc fixture được phê duyệt | U,I | U07 |
| Q21 | AI JSON lỗi, rỗng, quota, timeout | Typed error, không commit partial result | I | U08 |
| Q22 | Đổi config live/stub sau tạo phiên | History/provenance không bị viết lại | I,C | U08 |
| Q23 | Prompt injection trong SOP/lời nói/history | Không đổi quyền, rubric, score rule; guard provenance đúng | I,L | U08,U09 |
| Q24 | A truy cập SOP/session/result/operation B | 404, không rò payload | I | U09 |
| Q25 | Employee gọi mutation/analytics quản lý | 403; manager bị scope tenant | I | U09 |
| Q26 | JWT hết hạn, account/membership disabled | Server từ chối, mobile xử lý đúng | I,B,D | U09,U10 |
| Q27 | Đổi server/logout rồi login user khác | Không gửi token/hiện session user cũ | B,D | U10 |
| Q28 | SecureStore lỗi/migrate token legacy | Không mất token trước ghi thành công; lỗi rõ | B,D | U10 |
| Q29 | Gửi tin mất mạng | Tin failed/pending đúng, giữ text, retry cùng ID | B,D | U11 |
| Q30 | Force-stop lúc send/evaluate/resume offline | Reconcile server, không duplicate/mất committed turn | D | U11,U21 |
| Q31 | Không có giọng Việt/TTS lỗi/tắt tiếng | Fallback text, có dừng, không crash | B,D | U12 |
| Q32 | Input quá ngắn/dài, font lớn, bàn phím | Validate nhất quán, UI không che thao tác | B,D | U12 |
| Q33 | Draft edit/approve/archive và v1/v2 pin | Draft hidden, new session v2, old session v1 | I,B,D | U13,U14 |
| Q34 | KPI trên >50 phiên và history nhiều page | Tổng/tỷ lệ đúng filter, không lệ thuộc page | I,B | U15 |
| Q35 | Invite/reset/disable/replay activation | Single-use/expiry, revoke đúng tenant | I,B | U16 |
| Q36 | Build Docker và scan context/image | Không `.env`, DB local, secret/private signing key | I | U17 |
| Q37 | Backup/restore + migration staging | Restore được, schema/data invariant giữ | I | U17 |
| Q38 | APK release, Metro tắt, HTTPS thật | App độc lập, đăng nhập và gọi API được | D | U18 |
| Q39 | Compiler→Simulator→Evaluator Live | Ba operation có provenance Live thật | L,D | U21 |
| Q40 | Benchmark có failure/retry | Báo cả thất bại/sample size/phạm vi, không SLA giả | I,L | U20 |
| Q41 | Golden set human-reviewed | Báo semantic/critical false pass riêng, hạn chế rõ | U,L | U07,U20 |
| Q42 | Result cũ sau nâng scoring/schema | Kết quả đã lưu giữ nguyên, legacy hiển thị được | I,C,B | U04,U07 |

Mục tiêu regression: toàn bộ case deterministic bắt buộc pass; mọi critical false pass trong bộ golden đã duyệt phải được xử lý hoặc chặn phát hành với phạm vi rõ. Không suy ra tỷ lệ chính xác ngoài thực tế chỉ từ tập synthetic nhỏ.

## 9. Kịch bản nghiệm thu Android và quản lý

### 9.1 Happy path Café A

1. Cài APK từ artifact đã ghi hash, tắt Metro.
2. Nhập URL HTTPS staging, kiểm tra health/configured/availability.
3. Login employee A, chỉ thấy SOP được phép.
4. Start phiên, ghi operation/session/version/mode trong evidence kỹ thuật đã redacted.
5. Gửi ít nhất một lượt, nghe/dừng TTS, gửi đủ tình huống cần chấm.
6. Evaluate, mở từng quote về đúng lượt gốc; score/critical theo rubric.
7. Quay lại history, mở lại result; không tạo evaluation mới.

### 9.2 Critical failure

1. Câu đầu đúng policy, câu sau tự ý hoàn tiền.
2. Verify result không bị câu đầu che vi phạm.
3. Một scenario đạt ≥70 điểm số nhưng fail critical vẫn phải overall fail.
4. Có reason và evidence rõ; không invent quote khi nhân viên chưa nói gì chứng minh.

### 9.3 SOP v1/v2 và nhiều SOP

1. Employee B mở phiên theo v1.
2. Manager B chọn đúng SOP, tạo draft v2, sửa steps/rubric đồng bộ, xem diff rồi approve.
3. Phiên mới B dùng v2; phiên đang học vẫn dùng v1.
4. Employee A không thấy thay đổi tenant B; request chéo tenant bị chặn.
5. Tạo SOP thứ hai, chọn qua lại trong Studio; archive một SOP chặn bài mới nhưng giữ history.

### 9.4 Mất mạng và force-stop

Thực hiện riêng từng trường hợp: trước send; sau send trước response; lúc evaluate; sau server commit trước UI nhận; khi bootstrap/resume; khi TTS đang đọc.

Sau mở lại, so sánh số lượt/result với server, đảm bảo không duplicate. Lỗi kết nối chỉ làm trạng thái “chưa đồng bộ”, không tự xóa dữ liệu phiên.

### 9.5 Tài khoản và báo cáo

1. Manager tạo/mời employee mới, activation một lần, employee đăng nhập được.
2. Employee thực hành; manager thấy KPI và evidence đúng filter.
3. Vô hiệu hóa membership; token cũ bị chặn ở request tiếp theo.
4. Logout/login người khác và đổi backend không làm hiện dữ liệu cũ.

## 10. Release gates và điều kiện được tuyên bố hoàn thành

| Gate | Điều kiện | Bằng chứng bắt buộc | Trạng thái |
|---|---|---|---|
| R0 Data safety | Tests isolated, migration/backup không mất dữ liệu | canary + migration/restore report | TODO |
| R1 Security | XSS/tenant/auth/default config/container secrets xử lý | regression + config/image scan | TODO |
| R2 Session integrity | Concurrency/idempotency/recovery invariants đúng | Q08–Q15/Q29–Q30 | TODO |
| R3 Evidence quality | Quote/critical/schema đúng; semantic limits được đo | Q16–Q23/Q41–Q42 | TODO |
| R4 Mobile UX | Network/auth/TTS/validation flows ổn định | component + device evidence | TODO |
| R5 Manager workflow | Nhiều SOP, draft/review/approve/archive/employee lifecycle | browser + API evidence | TODO |
| R6 Analytics | Metrics toàn tập đúng scope/filter | >50 sessions fixture report | TODO |
| R7 Operations | CI, deploy config, logs, backup/restore và rollback có hướng dẫn | CI/runbooks/staging checks | TODO |
| R8 Android reality | APK độc lập và force-stop/relaunch thực tế | APK hash + device run log/video | TODO |
| R9 AI Live | Cả 3 module Live thật trên flow thiết bị | operation provenance + timing/errors | TODO |
| R10 Handoff | Docs/contracts/artifacts/limitations khớp phiên bản | release checklist và manifest | TODO |

- Code complete không đồng nghĩa R8/R9 đạt.
- Không release public khi còn P0 mở, thiếu secrets/signing/HTTPS an toàn hoặc chưa kiểm chứng tenant boundary.
- Không bắt người dùng đổi hết tài khoản/dữ liệu chỉ để migration dễ hơn.
- Nếu chỉ hoàn thành M1, ghi “M1 core implementation”, không gọi toàn bộ v1.2 đã hoàn tất.

## 11. Điều kiện bên ngoài và cách tiếp tục khi thiếu

| Thiếu gì | Phần vẫn làm được | Phần phải ghi chưa xác minh |
|---|---|---|
| Python trong PATH | Tìm executable hợp lệ, frontend/docs/static review | Backend runtime tests tới khi có interpreter |
| Gemini key/quota | Stub/fake provider, timeout/schema/security tests | Live integration/latency/quality trên model thật |
| Android thật | Typecheck/component/native build nếu có SDK | Install/TTS/force-stop/network device |
| Keystore release/EAS login | Code/config/runbook và debug local được phép | Release artifact/phân phối đúng signer |
| HTTPS hosting | Local isolated integration/container build | Device trên mạng ngoài/public readiness |
| PostgreSQL/Supabase | SQLite migrations/tests; PG container nếu công cụ sẵn | Cloud connectivity/RLS/backup của hạ tầng thật |
| Email service | Activation workflow và manager-managed delivery | Gửi email thật, delivery/recovery flow |
| Người review nghiệp vụ | Synthetic fixture và rubric assumptions | Xác nhận SOP/nhãn semantic/golden set bởi quản lý |

Không ghi key hoặc yêu cầu người dùng dán secret vào tài liệu. Chỉ ghi tên biến và nơi cấu hình được bảo vệ. Không để một blocker bên ngoài ngăn các task độc lập khác tiến triển.

## 12. Rủi ro triển khai và biện pháp kiểm soát

| Rủi ro | Biện pháp |
|---|---|
| Quá nhiều thay đổi cùng lúc | Làm task nhỏ, schema/contracts trước client; checkpoint M1/M2/M3 |
| API breaking làm app cũ hỏng | Adapter v1, additive fields, contract tests, deprecation rõ |
| Migrate DB chứa lịch sử thật | Backup consistent + restore rehearsal + scan conflicts + preserve result payload |
| Khóa SQLite suốt thời gian gọi AI | Transaction ngắn, operation reservation/CAS/fencing |
| Retry làm tăng chi phí và lượt trùng | Idempotency + bounded provider retries + persisted operation status |
| Rule stub được hiểu nhầm là AI hiểu nghiệp vụ | Nhãn stub, supported policy fixtures, golden semantic review riêng |
| Cập nhật SDK làm hỏng native build | Giữ baseline khi sửa core; dependency native compatible; prebuild review |
| Copy secret vào image/log/evidence | `.dockerignore`, redaction, runtime secret injection, artifact scan |
| Checklist vượt quá khả năng kiểm thử | NOT_VERIFIED/BLOCKED rõ; không fabricated screenshots/metrics |
| Lỗi regression khi refactor Studio | Giữ DOM safe tests và browser workflow tests xuyên các task |

## 13. Mẫu release evidence và handoff cuối cùng

Tạo `docs/upgrade-v1.2/RELEASE_EVIDENCE.md` theo mẫu:

```text
Release candidate:
Commit / branch:
Backend version / schema revision:
Mobile version / versionCode / package:
Scoring schema / prompt versions:
Build environment:

Automated checks:
- command / environment / exit code / evidence path

Device checks:
- device model / Android version / network / APK hash
- scenarios / actual outcomes / evidence paths

Live checks:
- model / timestamp / operation types / success and failure counts
- latency scope / sample size / limitations

Migration and restore:
- source schema / target schema / checksums or invariants
- backup and restore verification (no credentials)

Open issues:
- severity / task ID / impact / workaround / owner

Release gates:
- R0..R10: PASS | FAIL | NOT_VERIFIED, reason and evidence
```

Definition of Done cho một task: code đúng scope, kiểm thử liên quan đạt, contract/docs cập nhật, không secret, không mất dữ liệu ngoài scope, known limitations ghi rõ, trạng thái tiến độ trung thực.

## 14. Nguồn kỹ thuật để AI đối chiếu khi triển khai

Ưu tiên documentation tương ứng phiên bản thư viện thực tế trong lockfile; kiểm tra lại khi nâng dependency.

- [OWASP DOM XSS prevention](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html): tránh đưa dữ liệu không tin cậy vào `innerHTML`, dùng DOM/text APIs an toàn.
- [Expo SecureStore](https://docs.expo.dev/versions/latest/sdk/securestore/): lưu token trong kho bảo mật, chú ý backup/reinstall và native configuration; không cài bản latest không kiểm tra tương thích SDK 52.
- [Docker build context và .dockerignore](https://docs.docker.com/build/concepts/context/#dockerignore-files): loại secret/data khỏi build context.
- [SQLAlchemy constraints](https://docs.sqlalchemy.org/en/20/core/constraints.html), [Alembic](https://alembic.sqlalchemy.org/en/latest/): tham khảo khi thiết kế constraints/migrations và kiểm chứng trên từng DB.
- [Google GenAI Python SDK](https://googleapis.github.io/python-genai/): kiểm tra timeout/retry/schema options theo SDK được pin, không đoán tên tham số.

## 15. Roadmap sau v1.2 — chỉ làm khi có yêu cầu riêng

| Tính năng | Điều kiện trước khi bắt đầu | Cần thiết kế thêm |
|---|---|---|
| Nhập PDF/DOCX | SOP lifecycle/review ổn định | Parsing/OCR, provenance từng đoạn, draft-only, upload limits, malware/privacy controls |
| STT/voice realtime | Text conversation và operation model ổn định | Consent, transcript correction, latency/cost, background/audio interruptions |
| Adaptive learning | Scoring được calibrate và history đầy đủ | Learning objectives, retry strategy, fairness, human oversight |
| Multi-branch/self-service tenant | Auth/membership/audit vững | Tenant provisioning, approved tenant-switch flow, isolation và billing boundaries |
| Supabase Auth/RLS | Chốt identity migration riêng | Token verification, account linking, revoke, RLS/grants, rollback |
| Subscription/billing | Pilot xác nhận willingness-to-pay | Entitlements server-side, webhook idempotency, refunds, invoice/data retention |
| HR integration | Consent và policy sử dụng kết quả rõ | Export permissions, retention/delete, audit, không tự quyết định nhân sự |
| Multi-locale | Policy/scoring tách khỏi từ khóa tiếng Việt | Localization, language-specific golden sets, voice availability |

Không dùng roadmap để trì hoãn các lỗi P0 của phiên bản hiện tại. Bắt đầu triển khai bằng U00, sau đó U01 trước mọi lần chạy backend suite.
