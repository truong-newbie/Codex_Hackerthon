from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from ..config import settings

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
    .container { max-width: 1180px; margin: 0 auto; }
    .header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 16px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }
    .badge { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .badge-live { background: #065f46; color: #6ee7b7; }
    .badge-stub { background: #7c2d12; color: #fdba74; }
    .grid { display: grid; grid-template-columns: 340px 1fr; gap: 20px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
    h1, h2, h3 { margin-top: 0; }
    label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 6px; font-weight: 600; }
    input, textarea, select { width: 100%; background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 10px 12px; border-radius: 8px; margin-bottom: 12px; font-size: 13px; }
    textarea { min-height: 110px; font-family: monospace; }
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
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
    .kpi-box { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 14px; text-align: center; }
    .kpi-val { font-size: 26px; font-weight: 800; margin-top: 4px; }
    .session-row { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
    .quote-chip { font-size: 12px; color: #a7f3d0; background: #064e3b; padding: 4px 8px; border-radius: 6px; display: inline-block; margin-top: 4px; margin-right: 6px; }
    .log-box { background: #020617; border: 1px solid var(--border); padding: 12px; border-radius: 8px; font-family: monospace; font-size: 12px; color: #38bdf8; max-height: 180px; overflow-y: auto; white-space: pre-wrap; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 style="margin-bottom:4px;">ShiftLens — Manager Studio</h1>
        <div style="color:var(--muted);font-size:13px;">Quản trị SOP, Trọng số Rubric (100đ), Phê duyệt Phiên bản & Báo cáo Năng lực Nhân viên</div>
      </div>
      <div id="healthBadge" class="badge badge-stub">Checking AI...</div>
    </div>

    <div class="grid">
      <!-- Left Column: Auth & Version History -->
      <div>
        <div class="card">
          <h3>1. Đăng nhập Store Manager</h3>
          __DEMO_ACTIONS__
          <label>Tài khoản</label>
          <input id="username" value="__DEMO_USERNAME__" />
          <label>Mật khẩu</label>
          <input id="password" type="password" value="__DEMO_PASSWORD__" />
          <button style="width:100%" onclick="login()">Đăng Nhập Quản Lý</button>
          <div id="userInfo" style="margin-top:12px;font-size:13px;color:#38bdf8;"></div>
        </div>

        <div class="card">
          <h3>2. Lịch sử Phiên bản SOP</h3>
          <label for="sopSelect">Chọn SOP</label>
          <select id="sopSelect" aria-label="Chọn SOP"></select>
          <div id="versionsList" style="font-size:13px;color:var(--muted);">Chưa đăng nhập.</div>
        </div>
      </div>

      <!-- Right Column: SOP Steps & Rubric Editor + Employee Analytics -->
      <div>
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h3 style="margin:0;" id="sopTitleHeading">3. Trình Soạn Thảo SOP & Rubric</h3>
            __DEMO_PRESET__
          </div>

          <label for="newSopTitle">Tên SOP mới</label>
          <input id="newSopTitle" placeholder="Ví dụ: Xử lý đồ uống sai công thức" />
          <button class="btn-outline" onclick="createNewSop()">Tạo SOP mới từ Steps và Rubric bên dưới</button>

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

          <label style="margin-top:12px;">Nhật ký Phản hồi REST API (Bằng chứng kỹ thuật):</label>
          <div id="apiLog" class="log-box">Sẵn sàng kết nối FastAPI...</div>
        </div>

        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h3 style="margin:0;">4. Báo Cáo Năng Lực & Bằng Chứng Nhân Viên (Buyer Dashboard)</h3>
            <button class="btn-outline" onclick="loadAnalytics()">🔄 Làm mới Kết quả</button>
          </div>

          <div class="kpi-grid">
            <div class="kpi-box">
              <div style="font-size:11px;color:var(--muted);">TỔNG PHIÊN HỌC</div>
              <div class="kpi-val" id="kpiTotal">0</div>
            </div>
            <div class="kpi-box">
              <div style="font-size:11px;color:var(--muted);">TỶ LỆ ĐẠT (PASS RATE)</div>
              <div class="kpi-val" style="color:#10b981;" id="kpiPassRate">0%</div>
            </div>
            <div class="kpi-box">
              <div style="font-size:11px;color:var(--muted);">ĐIỂM TRUNG BÌNH</div>
              <div class="kpi-val" style="color:#38bdf8;" id="kpiAvgScore">0</div>
            </div>
            <div class="kpi-box">
              <div style="font-size:11px;color:var(--muted);">VI PHẠM CRITICAL</div>
              <div class="kpi-val" style="color:#ef4444;" id="kpiCritical">0</div>
            </div>
          </div>

          <div id="analyticsList" style="font-size:13px;color:var(--muted);">Hãy đăng nhập Store Manager để xem kết quả thực hành của nhân viên.</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let token = '';
    let currentSop = null;
    let allSops = [];
    let latestDraftId = null;

    function logApi(title, data) {
      const box = document.getElementById('apiLog');
      box.textContent = `[${new Date().toLocaleTimeString()}] ${title}:\\n` + JSON.stringify(data, null, 2);
    }

    function makeNode(tag, className, value) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (value !== undefined && value !== null) node.textContent = String(value);
      return node;
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
      document.getElementById('password').value = '__DEMO_PASSWORD__';
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
      logApi('POST /v1/auth/login', { ok: res.ok, user: data.user, detail: data.detail });
      if (!res.ok) {
        alert(data.detail || 'Đăng nhập thất bại');
        return;
      }
      token = data.access_token;
      document.getElementById('userInfo').textContent =
        `✓ Đã đăng nhập: ${data.user.full_name || data.user.username} | 📍 Cửa hàng: ${data.user.tenant_name} (${data.user.role})`;
      await loadSops();
      await loadAnalytics();
    }

    async function loadSops() {
      const res = await fetch('/v1/sops', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const sops = await res.json();
      logApi('GET /v1/sops', sops);
      if (!res.ok || !Array.isArray(sops)) return;
      const previousId = currentSop?.id;
      allSops = sops;
      const selector = document.getElementById('sopSelect');
      selector.replaceChildren();
      for (const sop of sops) {
        const option = makeNode('option', '', sop.title);
        option.value = sop.id;
        selector.appendChild(option);
      }
      if (!sops.length) {
        currentSop = null;
        document.getElementById('versionsList').textContent = 'Chưa có SOP.';
        document.getElementById('stepsInput').value = JSON.stringify([
          { id: 'S1', instruction: 'Lắng nghe và xác minh yêu cầu của khách.' }
        ], null, 2);
        document.getElementById('rubricInput').value = JSON.stringify([
          { id: 'C1', label: 'Xác minh và xử lý đúng quy trình', weight: 100, critical: true }
        ], null, 2);
        updateWeightSum();
        return;
      }
      currentSop = sops.find(sop => sop.id === previousId) || sops[0];
      selector.value = currentSop.id;
      showCurrentSop();
    }

    function showCurrentSop() {
      if (!currentSop) return;
      document.getElementById('sopTitleHeading').textContent = `3. SOP: ${currentSop.title}`;
      const editable = currentSop.versions.find(v => v.status === 'draft') || currentSop.active_version;
      if (editable) {
        document.getElementById('stepsInput').value = JSON.stringify(editable.steps, null, 2);
        document.getElementById('rubricInput').value = JSON.stringify(editable.rubric, null, 2);
        updateWeightSum();
      } else {
        document.getElementById('stepsInput').value = '';
        document.getElementById('rubricInput').value = '';
      }
      renderVersions(currentSop.versions, currentSop.active_version?.id);
    }

    document.getElementById('sopSelect').addEventListener('change', event => {
      currentSop = allSops.find(sop => sop.id === event.target.value) || null;
      showCurrentSop();
    });

    async function loadAnalytics() {
      if (!token) return;
      const res = await fetch('/v1/admin/analytics', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) return;
      const data = await res.json();
      document.getElementById('kpiTotal').textContent = data.total_sessions;
      document.getElementById('kpiPassRate').textContent = `${data.pass_rate}%`;
      document.getElementById('kpiAvgScore').textContent = `${data.average_score}/100`;
      document.getElementById('kpiCritical').textContent = data.critical_failure_count;

      const listEl = document.getElementById('analyticsList');
      listEl.replaceChildren();
      if (!data.recent_sessions.length) {
        listEl.textContent = 'Chưa có phiên thực hành nào từ nhân viên của cửa hàng.';
        return;
      }
      for (const s of data.recent_sessions) {
        const row = makeNode('div', 'session-row');
        const header = makeNode('div');
        header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;';
        const identity = makeNode('div');
        identity.appendChild(makeNode('b', '', `👤 ${s.employee_name} (${s.employee_username})`));
        const pin = makeNode('span', '', `📌 Pinned: v${s.sop_version_no} (${s.sop_version_id})`);
        pin.style.cssText = 'margin-left:8px;font-size:11px;color:#c7d2fe;background:#312e81;padding:2px 6px;border-radius:4px;';
        identity.appendChild(pin);
        const status = makeNode('span', 'status-pill');
        if (s.completed) {
          status.textContent = s.passed ? `✓ ĐẠT (${s.score}/100)` : `✗ CHƯA ĐẠT (${s.score}/100)${s.critical_failure ? ' • CRITICAL FAIL' : ''}`;
          status.classList.add(s.passed ? 'st-approved' : 'st-superseded');
        } else {
          status.textContent = `⏳ Đang học (${s.turns_count}/4 lượt)`;
          status.classList.add('st-draft');
        }
        header.append(identity, status);
        row.appendChild(header);
        const quotes = makeNode('div');
        quotes.style.marginTop = '6px';
        const passedEvidence = (s.evidence || []).filter(ev => ev.passed && ev.exact_quote);
        if (passedEvidence.length) {
          for (const ev of passedEvidence) quotes.appendChild(makeNode('span', 'quote-chip', `✓ ${ev.criterion_id}: "${ev.exact_quote}"`));
        } else {
          const empty = makeNode('span', '', 'Chưa có bằng chứng đạt hoặc đang trong phiên.');
          empty.style.cssText = 'font-size:12px;color:#64748b;';
          quotes.appendChild(empty);
        }
        row.appendChild(quotes);
        listEl.appendChild(row);
      }
    }

    function renderVersions(versions, activeId) {
      const container = document.getElementById('versionsList');
      latestDraftId = null;
      container.replaceChildren();
      for (const v of versions) {
        if (v.status === 'draft' && !latestDraftId) latestDraftId = v.id;
        const stClass = v.status === 'approved' ? 'st-approved' : (v.status === 'draft' ? 'st-draft' : 'st-superseded');
        const activeMark = v.id === activeId ? ' (ACTIVE)' : '';
        const row = makeNode('div', 'version-item');
        const details = makeNode('div');
        details.appendChild(makeNode('b', '', `Phiên bản v${v.version_no}${activeMark}`));
        const id = makeNode('div', '', `ID: ${v.id}`);
        id.style.cssText = 'font-size:11px;color:#94a3b8;';
        details.appendChild(id);
        const actions = makeNode('div');
        actions.style.cssText = 'display:flex;gap:6px;align-items:center;';
        actions.appendChild(makeNode('span', `status-pill ${stClass}`, v.status));
        if (v.status === 'draft') {
          const approveButton = makeNode('button', 'btn-green', 'Duyệt');
          approveButton.style.cssText = 'padding:4px 8px;font-size:11px;';
          approveButton.addEventListener('click', () => approveVersion(v.id));
          actions.appendChild(approveButton);
        }
        row.append(details, actions);
        container.appendChild(row);
      }
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
      if (!currentSop || currentSop.id !== 'sop-complaint-b') {
        alert('Mẫu demo v2 chỉ áp dụng cho SOP Café B. Hãy chọn SOP này trước.');
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

    async function createNewSop() {
      if (!token) return alert('Vui lòng đăng nhập trước!');
      const title = document.getElementById('newSopTitle').value.trim();
      if (title.length < 3) return alert('Tên SOP phải có ít nhất 3 ký tự.');
      try {
        const steps = JSON.parse(document.getElementById('stepsInput').value);
        const rubric = JSON.parse(document.getElementById('rubricInput').value);
        const res = await fetch('/v1/admin/sops', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ title, steps, rubric })
        });
        const data = await res.json();
        logApi('POST /v1/admin/sops', data);
        if (!res.ok) return alert(data.detail || 'Lỗi tạo SOP');
        currentSop = { id: data.id };
        document.getElementById('newSopTitle').value = '';
        await loadSops();
      } catch (e) {
        alert('Không thể tạo SOP: ' + e.message);
      }
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
    """Giao diện No-Code Manager Studio tích hợp sẵn phục vụ cấu hình SOP v2 và xem báo cáo năng lực nhân viên."""
    demo_actions = (
        '<div class="quick-row">'
        '<button class="btn-outline" onclick="quickLogin(\'manager_a\')">☕ Manager Café A</button>'
        '<button class="btn-outline" onclick="quickLogin(\'manager_b\')">🌿 Manager Café B</button>'
        '</div>'
    ) if settings.DEMO_MODE else ""
    demo_preset = (
        '<button class="btn-amber" onclick="applyDemoV2Preset()">⚡ Nạp Mẫu Demo SOP v2</button>'
    ) if settings.DEMO_MODE else ""
    html = (STUDIO_HTML
        .replace("__DEMO_ACTIONS__", demo_actions)
        .replace("__DEMO_PRESET__", demo_preset)
        .replace("__DEMO_USERNAME__", "manager_b" if settings.DEMO_MODE else "")
        .replace("__DEMO_PASSWORD__", "ShiftLens@2026" if settings.DEMO_MODE else ""))
    return HTMLResponse(content=html)
