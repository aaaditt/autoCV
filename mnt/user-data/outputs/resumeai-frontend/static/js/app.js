// ── Config ──────────────────────────────────────────────
const API = window.RESUMEAI_API_URL || 'http://localhost:5000/api';

// ── API Client ───────────────────────────────────────────
const api = {
  async post(path, body, isFormData = false) {
    const opts = { method: 'POST', credentials: 'include' };
    if (isFormData) {
      opts.body = body;
    } else {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(`${API}${path}`, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
  },
  async get(path) {
    const res = await fetch(`${API}${path}`, { credentials: 'include' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
  }
};

// ── Auth ─────────────────────────────────────────────────
const auth = {
  user: null,
  async init() {
    try {
      const data = await api.get('/auth/me');
      if (data.authenticated) { this.user = data.user; this._updateUI(); }
    } catch {}
  },
  async logout() {
    await api.post('/auth/logout', {});
    this.user = null;
    window.location.href = '/';
  },
  _updateUI() {
    const nameEl = document.getElementById('nav-user');
    if (nameEl && this.user) nameEl.textContent = this.user.name?.split(' ')[0] || this.user.email;
    const avatarEl = document.getElementById('nav-avatar');
    if (avatarEl && this.user) avatarEl.textContent = (this.user.name || this.user.email || 'U')[0].toUpperCase();
    document.querySelectorAll('.auth-show').forEach(el => el.classList.remove('hidden'));
    document.querySelectorAll('.auth-hide').forEach(el => el.classList.add('hidden'));
  },
  requireAuth() {
    if (!this.user) { window.location.href = '/?login=true'; return false; }
    return true;
  }
};

// ── Score Ring ───────────────────────────────────────────
function renderScoreRing(el, score) {
  const r = 40, c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const color = score >= 75 ? '#34C759' : score >= 50 ? '#FF9F0A' : '#FF3B30';
  el.innerHTML = `
    <svg width="96" height="96" viewBox="0 0 96 96" style="transform:rotate(-90deg)">
      <circle fill="none" stroke="var(--bg-secondary)" stroke-width="8" cx="48" cy="48" r="${r}"/>
      <circle fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round"
        cx="48" cy="48" r="${r}"
        stroke-dasharray="${c}" stroke-dashoffset="${c}"
        style="transition:stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)"
        id="${el.id}-fill"/>
    </svg>
    <div class="score-ring-text" style="color:${color};position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:1.375rem;font-weight:700">${score}%</div>
  `;
  requestAnimationFrame(() => setTimeout(() => {
    const f = document.getElementById(`${el.id}-fill`);
    if (f) f.style.strokeDashoffset = offset;
  }, 80));
}

// ── Skeleton ─────────────────────────────────────────────
function showSkeleton(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = `
    <div style="display:flex;flex-direction:column;align-items:center;gap:16px;padding:32px">
      <div class="skeleton" style="width:96px;height:96px;border-radius:50%"></div>
      <div class="skeleton skeleton-text" style="width:100px"></div>
    </div>
    <div style="padding:0 16px 16px;display:flex;flex-direction:column;gap:8px">
      <div class="skeleton skeleton-text" style="width:60%"></div>
      <div style="display:flex;gap:6px">
        <div class="skeleton" style="height:28px;width:80px;border-radius:980px"></div>
        <div class="skeleton" style="height:28px;width:60px;border-radius:980px"></div>
        <div class="skeleton" style="height:28px;width:100px;border-radius:980px"></div>
      </div>
      <div class="skeleton skeleton-text" style="width:40%;margin-top:8px"></div>
      <div style="display:flex;gap:6px">
        <div class="skeleton" style="height:28px;width:70px;border-radius:980px"></div>
        <div class="skeleton" style="height:28px;width:90px;border-radius:980px"></div>
      </div>
    </div>`;
}

// ── Toast ────────────────────────────────────────────────
function toast(msg, type = '') {
  let c = document.querySelector('.toast-container');
  if (!c) { c = document.createElement('div'); c.className = 'toast-container'; document.body.appendChild(c); }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Dropzone ─────────────────────────────────────────────
function setupDropzone(zoneId, inputId, onFile) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  if (!zone || !input) return;
  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('dragover'); if (e.dataTransfer.files[0]) _handleFile(e.dataTransfer.files[0], zone, onFile); });
  input.addEventListener('change', () => { if (input.files[0]) _handleFile(input.files[0], zone, onFile); });
}

function _handleFile(file, zone, onFile) {
  const validExts = ['.pdf', '.docx', '.doc'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!validExts.includes(ext)) { toast('Invalid file type. Use PDF or DOCX.', 'error'); return; }
  if (file.size > 10 * 1024 * 1024) { toast('File too large. Max 10MB.', 'error'); return; }
  zone.classList.add('has-file');
  zone.innerHTML = `
    <div style="color:var(--success);font-size:1.5rem">✓</div>
    <div class="upload-main">${file.name}</div>
    <div class="upload-sub">${(file.size/1024).toFixed(0)} KB &nbsp;·&nbsp;
      <span style="color:var(--accent);cursor:pointer" onclick="resetDropzone('${zone.id}','${zone.dataset.inputId || ''}')">Remove</span>
    </div>`;
  onFile(file);
}

window.resetDropzone = function(zoneId, inputId) {
  const zone = document.getElementById(zoneId);
  if (!zone) return;
  zone.classList.remove('has-file');
  zone.innerHTML = zone.dataset.originalHtml || '';
};

// ── Tabs ─────────────────────────────────────────────────
function setupTabs(groupId) {
  document.querySelectorAll(`[data-tabs="${groupId}"] .tab`).forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll(`[data-tabs="${groupId}"] .tab`).forEach(t => t.classList.remove('active'));
      document.querySelectorAll(`[data-tab-content="${groupId}"]`).forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      const t = document.getElementById(tab.dataset.target);
      if (t) t.classList.add('active');
    });
  });
}

// ── Diff ─────────────────────────────────────────────────
function generateDiff(original, optimized) {
  const a = original.split('\n'), b = optimized.split('\n');
  let html = '';
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const o = a[i] ?? '', n = b[i] ?? '';
    if (o === n) html += `<div>${esc(o) || '&nbsp;'}</div>`;
    else {
      if (o) html += `<div class="diff-removed">${esc(o)}</div>`;
      if (n) html += `<div class="diff-added">${esc(n)}</div>`;
    }
  }
  return html;
}

function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ── Shared nav HTML ──────────────────────────────────────
function renderNav(activePage) {
  const pages = [
    { href: '/pages/dashboard.html', label: 'Dashboard' },
    { href: '/pages/optimize.html',  label: 'Optimize' },
    { href: '/pages/pricing.html',   label: 'Pricing' },
  ];
  return `
    <nav class="nav">
      <div class="nav-inner">
        <a href="/index.html" class="nav-logo">ResumeAI</a>
        <div class="nav-links">
          ${pages.map(p => `<a href="${p.href}" class="nav-link${p.label===activePage?' font-medium':''}">${p.label}</a>`).join('')}
          <div class="auth-hide">
            <button class="btn btn-primary btn-sm" onclick="showLoginModal()">Get Started Free</button>
          </div>
          <div class="auth-show hidden" style="display:flex;align-items:center;gap:8px">
            <div style="width:32px;height:32px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-size:0.875rem;font-weight:600;cursor:pointer" id="nav-avatar">U</div>
          </div>
        </div>
      </div>
    </nav>`;
}

document.addEventListener('DOMContentLoaded', () => { auth.init(); });
