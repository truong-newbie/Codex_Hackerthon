// Dependency-free regression check for the embedded Manager Studio script.
// Fails if API-derived content is assigned to innerHTML or the login token is logged.
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const source = fs.readFileSync(path.join(__dirname, '..', 'backend', 'app', 'routers', 'studio_router.py'), 'utf8');
const script = source.match(/<script>([\s\S]*?)<\/script>/)?.[1];
if (!script) throw new Error('Manager Studio script not found');

class Element {
  constructor() {
    this.children = [];
    this.style = {};
    this.textContent = '';
    this.value = '';
    this.classList = { add: () => {} };
    this.listeners = {};
  }
  set innerHTML(_) { throw new Error('Unsafe innerHTML assignment'); }
  appendChild(child) { this.children.push(child); return child; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(event, callback) { this.listeners[event] = callback; }
}

const nodes = new Map();
const document = {
  getElementById(id) {
    if (!nodes.has(id)) nodes.set(id, new Element());
    return nodes.get(id);
  },
  createElement() { return new Element(); },
};
const unsafeQuote = '<img src=x onerror=alert(1)>';
const token = 'must-not-appear-in-log';
const responses = {
  '/v1/health': { status: 'ok', ai_mode: 'stub', live_ready: false },
  '/v1/auth/login': {
    access_token: token,
    user: { username: 'manager_a', full_name: '<Manager>', tenant_name: '<Café A>', role: 'manager' },
  },
  '/v1/sops': [{
    id: 'sop-a', title: '<Complaint SOP>',
    active_version: { id: 'v1', steps: [], rubric: [] },
    versions: [{ id: 'v1', version_no: 1, status: 'approved' }, { id: 'draft-id', version_no: 2, status: 'draft' }],
  }, {
    id: 'sop-b', title: '<img src=x onerror=alert(2)>',
    active_version: null, versions: [],
  }],
  '/v1/admin/analytics': {
    total_sessions: 1, pass_rate: 100, average_score: 100, critical_failure_count: 0,
    recent_sessions: [{
      session_id: 'session-1', employee_name: '<Employee>', employee_username: 'emp_a',
      sop_version_no: 1, sop_version_id: 'v1', completed: true, passed: true, score: 100,
      evidence: [{ criterion_id: 'C1', passed: true, exact_quote: unsafeQuote }],
    }],
  },
};
const context = vm.createContext({
  document,
  fetch: async url => ({ ok: true, json: async () => responses[url] }),
  alert: message => { throw new Error(message); },
  console,
});
vm.runInContext(script, context);
vm.runInContext('login()', context).then(() => {
  const log = document.getElementById('apiLog').textContent;
  if (log.includes(token)) throw new Error('Login token leaked into Studio API log');
  const rows = document.getElementById('analyticsList').children;
  if (rows.length !== 1) throw new Error('Analytics row missing');
  const quote = rows[0].children[1].children[0].textContent;
  if (!quote.includes(unsafeQuote)) throw new Error('Quote text was not rendered');
  const selector = document.getElementById('sopSelect');
  if (selector.children.length !== 2) throw new Error('Multiple SOPs were not listed');
  selector.value = 'sop-b';
  selector.listeners.change({ target: selector });
  if (!document.getElementById('sopTitleHeading').textContent.includes('<img src=x')) {
    throw new Error('Selected SOP title was not rendered as text');
  }
  console.log('Manager Studio DOM check passed');
}).catch(error => {
  console.error(error);
  process.exitCode = 1;
});
