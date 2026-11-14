from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Manager Studio Web UI"])

STUDIO_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ShiftLens — Manager Studio (SOP & Rubric Governance)</title>
  <style>
    :root {
      --bg: #0f172a;
      --card: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --primary: #2563eb;
      --green: #10b981;
      --amber: #f59e0b;
      --red: #ef4444;
    }
    * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
    body { margin: 0; background: var(--bg); color: var(--text); padding: 24px; }
    .container { max-width: 1120px; margin: 0 auto; }
    .header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 16px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }
    .badge { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .badge-live { background: #065f46; color: #6ee7b7; }
    .badge-stub { background: #7c2d12; color: #fdba74; }
    .grid { display: grid; grid-template-columns: 340px 1fr; gap: 20px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
    h1, h2, h3 { margin-top: 0; }
    label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 6px; font-weight: 600; }
    input, textarea { width: 100%; background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 10px 12px; border-radius: 8px; margin-bottom: 12px; font-size: 13px; }
    textarea { min-height: 120px; font-family: monospace; }
    button { cursor: pointer; border: none; border-radius: 8px; padding: 10px 16px; font-weight: 700; font-size: 13px; color: white; background: var(--primary); transition: opacity 0.15s; }
    button:hover { opacity: 0.9; }
    .btn-green { background: var(--green); }
    .btn-amber { background: var(--amber); color: #0f172a; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
    .quick-row { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
    .version-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 8px; }
    .status-pill { font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 700; text-transform: uppercase; }
    .st-approved { background: #065f46; color: #a7f3d0; }
    .st-draft { background: #78350f; color: #fde68a; }
    .st-superseded { background: #334155; color: #94a3b8; }
    .log-box { background: #020617; border: 1px solid var(--border); padding: 12px; border-radius: 8px; font-family: monospace; font-size: 12px; color: #38bdf8; max-height: 200px; overflow-y: auto; white-space: pre-wrap; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 style="margin-bottom:4px;">ShiftLens — Manager Studio</h1>
        <div style="color:var(--muted);font-size:13px;">Quản trị SOP, Trọng số Rubric (100đ) & Phê duyệt Phiên bản (REST + Bearer JWT)</div>
      </div>
      <div id="healthBadge" class="badge badge-stub">Checking AI...</div>
    </div>

    <div class="grid">
      <!-- Left Column: Auth & Version History -->
      <div>
        <div class="card">
          <h3>1. Đăng nhập Store Manager</h3>
          <div class="quick-row">
            <button class="btn-outline" onclick="quickLogin('manager_a')">☕ Manager Café A</button>
            <button class="btn-outline" onclick="quickLogin('manager_b')">🌿 Manager Café B</button>
          </div>
          <label>Tài khoản</label>
          <input id="username" value="manager_b" />
          <label>Mật khẩu</label>
          <input id="password" type="password" value="ShiftLens@2026" />
          <button style="width:100%" onclick="login()">Đăng Nhập Quản Lý</button>
          <div id="userInfo" style="margin-top:12px;font-size:13px;color:#38bdf8;"></div>
        </div>

        <div class="card">
          <h3>2. Lịch sử Phiên bản SOP</h3>
          <div id="versionsList" style="font-size:13px;color:var(--muted);">Chưa đăng nhập.</div>
        </div>
      </div>

      <!-- Right Column: SOP Steps & Rubric Editor -->
      <div>
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h3 style="margin:0;" id="sopTitleHeading">3. Trình Soạn Thảo SOP & Rubric</h3>
            <button class="btn-amber" onclick="applyDemoV2Preset()">⚡ Nạp Mẫu Demo SOP v2</button>
          </div>

          <label>Các bước thực hiện SOP (Steps JSON - Unique IDs):</label>
          <textarea id="stepsInput"></textarea>

          <div style="display:flex;justify-content:space-between;align-items:center;">
            <label>Bộ tiêu chí chấm điểm Rubric (Tổng trọng số bắt buộc = 100):</label>
            <span id="weightSum" style="font-size:12px;font-weight:700;color:#10b981;">Tổng: 100/100</span>
          </div>
          <textarea id="rubricInput" oninput="updateWeightSum()"></textarea>

          <div class="quick-row" style="margin-top:8px;">
            <button onclick="createDraft()">📝 Bước 1: Tạo Bản Thảo Mới (Create Draft)</button>
            <button class="btn-green" id="approveBtn" onclick="approveLatestDraft()">✅ Bước 2: Phê Duyệt & Kích Hoạt (Approve vN)</button>
          </div>

          <label style="margin-top:16px;">Nhật ký Phản hồi REST API (Bằng chứng kỹ thuật):</label>
          <div id="apiLog" class="log-box">Sẵn sàng kết nối FastAPI...</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let token = '';
    let currentSop = null;
    let latestDraftId = null;

    function logApi(title, data) {
      const box = document.getElementById('apiLog');
      box.textContent = `[${new Date().toLocaleTimeString()}] ${title}:\\n` + JSON.stringify(data, null, 2);
    }

    async function checkHealth() {
      try {
        const res = await fetch('/v1/health');
        const data = await res.json();
        const badge = document.getElementById('healthBadge');
        badge.className = 'badge ' + (data.ai_mode === 'live' ? 'badge-live' : 'badge-stub');
        badge.textContent = `AI_MODE: ${data.ai_mode.toUpperCase()} | LIVE_READY: ${data.live_ready}`;
      } catch (e) {}
    }

    function quickLogin(user) {
      document.getElementById('username').value = user;
      document.getElementById('password').value = 'ShiftLens@2026';
      login();
    }

    async function login() {
      const username_or_email = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      const res = await fetch('/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username_or_email, password })
      });
      const data = await res.json();
      logApi('POST /v1/auth/login', data);
      if (!res.ok) {
        alert(data.detail || 'Đăng nhập thất bại');
        return;
      }
      token = data.access_token;
      document.getElementById('userInfo').innerHTML =
        `✓ Đã đăng nhập: <b>${data.user.full_name}</b><br/>📍 Cửa hàng: <b>${data.user.tenant_name}</b> (${data.user.role})`;
      await loadSops();
    }

    async function loadSops() {
      const res = await fetch('/v1/sops', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const sops = await res.json();
      logApi('GET /v1/sops', sops);
      if (!sops.length) return;
      currentSop = sops[0];
      document.getElementById('sopTitleHeading').textContent = `3. SOP: ${currentSop.title}`;
      if (currentSop.active_version) {
        document.getElementById('stepsInput').value = JSON.stringify(currentSop.active_version.steps, null, 2);
        document.getElementById('rubricInput').value = JSON.stringify(currentSop.active_version.rubric, null, 2);
        updateWeightSum();
      }
      renderVersions(currentSop.versions, currentSop.active_version?.id);
    }

    function renderVersions(versions, activeId) {
      const container = document.getElementById('versionsList');
      latestDraftId = null;
      container.innerHTML = versions.map(v => {
        if (v.status === 'draft' && !latestDraftId) latestDraftId = v.id;
        const stClass = v.status === 'approved' ? 'st-approved' : (v.status === 'draft' ? 'st-draft' : 'st-superseded');
        const activeMark = v.id === activeId ? ' (ACTIVE)' : '';
        return `
          <div class="version-item">
            <div>
              <b>Phiên bản v${v.version_no}${activeMark}</b>
              <div style="font-size:11px;color:#94a3b8;">ID: ${v.id}</div>
            </div>
            <div style="display:flex;gap:6px;align-items:center;">
              <span class="status-pill ${stClass}">${v.status}</span>
              ${v.status === 'draft' ? `<button class="btn-green" style="padding:4px 8px;font-size:11px;" onclick="approveVersion('${v.id}')">Duyệt</button>` : ''}
            </div>
          </div>
        `;
      }).join('');
    }

    function updateWeightSum() {
      try {
        const rubric = JSON.parse(document.getElementById('rubricInput').value);
        const sum = rubric.reduce((acc, item) => acc + (Number(item.weight) || 0), 0);
        const el = document.getElementById('weightSum');
        el.textContent = `Tổng trọng số: ${sum}/100`;
        el.style.color = sum === 100 ? '#10b981' : '#ef4444';
      } catch (e) {}
    }

    function applyDemoV2Preset() {
      if (!currentSop) {
        alert('Vui lòng đăng nhập Manager trước!');
        return;
      }
      const steps = [
        { id: "S1", instruction: "Lắng nghe với thái độ cầu thị, xin lỗi khách và mời khách ngồi nghỉ tại quầy." },
        { id: "S2", instruction: "Kiểm tra hóa đơn và xác nhận lỗi pha chế của ly đồ uống." },
        { id: "S3", instruction: "[CẬP NHẬT v2] Chủ động pha lại ly mới ngay lập tức VÀ tặng kèm 01 bánh quy bơ miễn phí cùng voucher 50.000đ." }
      ];
      document.getElementById('stepsInput').value = JSON.stringify(steps, null, 2);
      logApi('Preset Loaded', { message: 'Đã nạp nội dung cập nhật SOP v2. Hãy nhấn Tạo Bản Thảo Mới -> Phê Duyệt!' });
    }

    async function createDraft() {
      if (!currentSop) return alert('Vui lòng đăng nhập trước!');
      try {
        const steps = JSON.parse(document.getElementById('stepsInput').value);
        const rubric = JSON.parse(document.getElementById('rubricInput').value);
        const res = await fetch(`/v1/admin/sops/${currentSop.id}/draft`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ steps, rubric })
        });
        const data = await res.json();
        logApi(`POST /v1/admin/sops/${currentSop.id}/draft`, data);
        if (!res.ok) return alert(data.detail || 'Lỗi tạo bản thảo');
        latestDraftId = data.id;
        await loadSops();
      } catch (e) {
        alert('JSON không hợp lệ: ' + e.message);
      }
    }

    async function approveVersion(versionId) {
      const res = await fetch(`/v1/admin/sop-versions/${versionId}/approve`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      logApi(`POST /v1/admin/sop-versions/${versionId}/approve`, data);
      if (!res.ok) return alert(data.detail || 'Lỗi phê duyệt');
      await loadSops();
    }

    async function approveLatestDraft() {
      if (!latestDraftId) return alert('Hãy nhấn Bước 1: Tạo Bản Thảo Mới trước khi phê duyệt!');
      await approveVersion(latestDraftId);
    }

    checkHealth();
  </script>
</body>
</html>
"""

@router.get("/studio", response_class=HTMLResponse, include_in_schema=True)
def manager_studio_ui():
    """Giao diện No-Code Manager Studio tích hợp sẵn phục vụ cấu hình và phê duyệt SOP v2."""
    return HTMLResponse(content=STUDIO_HTML)
