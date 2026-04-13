/**
 * AutoCV Auth Module v2
 * Handles Supabase auth state, user_type (student/recruiter), plan gating.
 * No email-string hacks. Plan + user_type come from backend session sync.
 */

const API = window.RESUMEAI_API_URL || 'http://localhost:5000/api';

// ── API Client ─────────────────────────────────────────
const api = {
  async post(path, body, isFormData = false) {
    const opts = { method: 'POST', credentials: 'include' };
    if (isFormData) {
      opts.body = body;
    } else {
      opts.headers = { 'Content-Type': 'application/json' };
      opts.body = JSON.stringify(body);
    }
    let res;
    try {
      res = await fetch(`${API}${path}`, opts);
    } catch (e) {
      throw new Error('Cannot reach server. Please check your connection.');
    }
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { throw new Error(res.status === 404 ? `API endpoint not found: ${path}` : `Server error (${res.status})`); }
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
  },
  async get(path) {
    let res;
    try {
      res = await fetch(`${API}${path}`, { credentials: 'include' });
    } catch (e) {
      throw new Error('Cannot reach server. Please check your connection.');
    }
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch { throw new Error(res.status === 404 ? `API endpoint not found: ${path}` : `Server error (${res.status})`); }
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
  }
};
window.api = api;

// ── Toast ─────────────────────────────────────────────
function toast(msg, type = '') {
  console.log(`[Toast ${type.toUpperCase()}]: ${msg}`);
  let c = document.querySelector('.toast-container');
  if (!c) {
    c = document.createElement('div');
    c.className = 'toast-container';
    document.body.appendChild(c);
  }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => { if (el.parentNode) el.remove(); }, 4500);
}
window.toast = toast;

// ── Auth ─────────────────────────────────────────────
const auth = {
  user: null,
  supabase: null,

  // Computed getters — no email hacks
  get userType()    { return this.user?.user_type || 'guest'; },
  get plan()        { return this.user?.plan || 'free'; },
  get isPro()       { return this.plan === 'pro'; },
  get isSingle()    { return this.plan === 'single'; },
  get isPaid()      { return this.plan === 'single' || this.plan === 'pro'; },
  get isRecruiter() { return this.userType === 'recruiter'; },
  get isStudent()   { return this.userType === 'student'; },
  get isLoggedIn()  { return !!this.user; },

  /**
   * Feature matrix — mirrors backend plan_service.py
   */
  getFeatures() {
    if (this.isRecruiter) {
      const recruiterMatrix = {
        free: { batch_size: 5, overage_allowed: false, overage_cost_per_resume: 0, csv_export: false, saved_presets: false },
        pro:  { batch_size: 50, overage_allowed: true, overage_cost_per_resume: 1, csv_export: true, saved_presets: true },
      };
      return recruiterMatrix[this.plan] || recruiterMatrix['free'];
    }

    const matrix = {
      guest:  { weekly_scans: 1, ai_rewrite: false, download: false, full_keywords: false, rewrites: 0, cover_letter: false, templates: false },
      free:   { weekly_scans: 3, ai_rewrite: false, download: false, full_keywords: true, rewrites: 0, cover_letter: false, templates: false },
      single: { weekly_scans: 999, ai_rewrite: true, download: true, full_keywords: true, rewrites: 1, cover_letter: false, templates: true },
      pro:    { weekly_scans: -1, ai_rewrite: true, download: true, full_keywords: true, rewrites: -1, cover_letter: true, templates: true },
    };
    return matrix[this.plan] || matrix['free'];
  },

  /**
   * Initialize auth — set up Supabase client, check session, update UI
   */
  async init() {
    const sb = window.supabase || (typeof supabase !== 'undefined' ? supabase : null);
    if (sb) {
      if (!window.SUPABASE_URL || !window.SUPABASE_ANON_KEY) {
        console.error("Supabase configuration missing (URL or Anon Key)");
        return;
      }
      this.supabase = sb.createClient(window.SUPABASE_URL, window.SUPABASE_ANON_KEY);
      this.setupAuthListener();
    }

    // Try restoring session
    try {
      await this.refreshUser();
    } catch (err) {
      console.warn("Session sync failed:", err);
    }

    // Page guard: redirect unauthenticated users from private pages
    const privatePages = ['/pages/dashboard', '/pages/results', '/pages/account', '/pages/student/', '/pages/recruiter/'];
    const path = window.location.pathname;
    const isPrivate = privatePages.some(p => path.includes(p));
    const isOptimize = path.includes('/pages/optimize');
    const isGuest = new URLSearchParams(window.location.search).get('guest') === 'true';
    const isCallback = window.location.hash.includes('access_token=');

    if ((isPrivate || (isOptimize && !isGuest)) && !this.user && !isCallback) {
      window.location.href = '/pages/login.html';
      return;
    }

    this._updateUI();

    // Fire custom event so pages can hook into auth ready
    window.dispatchEvent(new CustomEvent('auth:ready', { detail: { user: this.user } }));
  },

  setupAuthListener() {
    this.supabase.auth.onAuthStateChange(async (event, session) => {
      console.log("Auth Event:", event);
      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
        if (session) {
          // Always set a baseline user from Supabase so redirect works
          // even if backend session sync is slow/down
          this.user = session.user;

          try {
            const res = await api.post('/auth/session', {
              access_token: session.access_token,
              user: session.user,
            });
            this.user = res.user || session.user;
          } catch (e) {
            console.warn("Backend session sync failed (using Supabase session as fallback):", e);
          }

          this._updateUI();

          // Redirect from auth pages to correct dashboard
          const path = window.location.pathname;
          const isLoginPage = path.includes('login.html') || path.includes('signup.html');
          
          if (isLoginPage) {
            this.redirectToDashboard();
          }

        }
      } else if (event === 'SIGNED_OUT') {
        this.user = null;
        this._updateUI();
      }
    });
  },

  async refreshUser() {
    try {
      if (this.supabase) {
        const { data: { session } } = await this.supabase.auth.getSession();
        if (session) {
          // Sync with backend to get plan/user_type from DB
          const res = await api.post('/auth/session', {
            access_token: session.access_token,
            user: session.user,
          });
          this.user = res.user;
          return;
        }
      }
      // Fallback: check backend session
      const data = await api.get('/auth/me');
      if (data.authenticated) {
        this.user = data.user;
      }
    } catch (e) {
      console.warn("Could not refresh user session:", e);
    }
  },

  async loginWithGoogle() {
    if (!this.supabase) {
      return toast('Auth service not available', 'error');
    }
    if (this.user) {
      this.redirectToDashboard();
      return;
    }
    try {
      const { error } = await this.supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: window.location.origin + '/pages/dashboard.html' }
      });
      if (error) throw error;
    } catch (err) {
      toast(err.message, 'error');
    }
  },

  async loginWithEmail(email, password) {
    if (!this.supabase) {
      return toast('Auth service not available', 'error');
    }
    try {
      const { data, error } = await this.supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      return data;
    } catch (err) {
      toast(err.message, 'error');
      throw err;
    }
  },

  async signupWithEmail(email, password, fullName = '', userType = 'student') {
    if (!this.supabase) {
      return toast('Auth service not available', 'error');
    }
    try {
      const { data, error } = await this.supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName, user_type: userType },
          emailRedirectTo: window.location.origin + '/pages/login.html',
        }
      });
      if (error) throw error;
      return data;
    } catch (err) {
      toast(err.message, 'error');
      throw err;
    }
  },

  async logout() {
    if (this.supabase) {
      await this.supabase.auth.signOut();
    }
    await api.post('/auth/logout', {});
    this.user = null;
    window.location.href = '/';
  },

  /**
   * Redirect to correct dashboard based on user_type
   */
  redirectToDashboard() {
    window.location.href = this.isRecruiter
      ? '/pages/recruiter/dashboard.html'
      : '/pages/dashboard.html';
  },

  /**
   * Update all UI based on current auth state.
   * Uses CSS classes on body for visibility gating.
   */
  _updateUI() {
    const logged = !!this.user;

    // Toggle body classes for CSS visibility system
    document.body.classList.toggle('is-logged-in', logged);
    document.body.classList.toggle('is-pro', this.isPro);
    document.body.classList.toggle('is-paid', this.isPaid);
    document.body.classList.toggle('user-type-student', logged && this.isStudent);
    document.body.classList.toggle('user-type-recruiter', logged && this.isRecruiter);
    document.body.classList.toggle('theme-recruiter', logged && this.isRecruiter);

    if (!logged) return;

    // Resolve display name
    let fullName = this.user.name || this.user.user_metadata?.full_name;
    if (!fullName) {
      const emailPart = (this.user.email || 'user').split('@')[0];
      fullName = emailPart.charAt(0).toUpperCase() + emailPart.slice(1);
    }

    // Update avatar/username in nav
    document.querySelectorAll('#nav-avatar').forEach(el => {
      el.textContent = fullName[0].toUpperCase();
    });
    document.querySelectorAll('#nav-username').forEach(el => {
      el.textContent = fullName;
    });

    // Update greeting
    document.querySelectorAll('#user-greeting').forEach(el => {
      const hour = new Date().getHours();
      const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
      el.textContent = `${greeting}, ${fullName.split(' ')[0]} 👋`;
    });

    // Update plan badges
    const planLabels = { free: 'Free Plan', single: 'Single Plan', pro: 'Pro Plan' };
    document.querySelectorAll('.plan-badge').forEach(el => {
      el.textContent = planLabels[this.plan] || 'Free Plan';
      el.className = 'plan-badge badge';
      if      (this.isPro) el.classList.add('badge-pro');
      else if (this.isSingle) el.classList.add('badge-blue');
      else    el.classList.add('badge-gray');
    });

    // Update user type badges
    document.querySelectorAll('.user-type-badge').forEach(el => {
      el.textContent = this.isRecruiter ? 'Recruiter' : 'Student';
      el.className = 'user-type-badge badge';
      el.classList.add(this.isRecruiter ? 'badge-purple' : 'badge-blue');
    });
  },

  /**
   * Save an optimization to Supabase
   */
  async saveOptimization(data) {
    if (!this.user || !this.supabase) return;
    try {
      const { error } = await this.supabase
        .from('optimizations')
        .insert([{
          user_id: this.user.id,
          optimization_id: data.optimization_id || `opt-${Date.now()}`,
          filename: data.filename || 'Resume.pdf',
          job_title: data.job_title || 'General Application',
          original_score: data.original_score || 0,
          optimized_score: data.optimized_score || 0,
          original_text: data.original_text || '',
          optimized_text: data.optimized_text || '',
          jd_snippet: (data.jd_text || '').substring(0, 200),
          created_at: new Date().toISOString(),
        }]);
      if (error) console.warn("Failed to save optimization:", error.message);
      else console.log("Optimization saved.");
    } catch (e) {
      console.error("Save optimization error:", e);
    }
  },

  requireAuth() {
    if (!this.user) {
      window.location.href = '/pages/login.html';
      return false;
    }
    return true;
  },

  /**
   * Show manual payment modal (PayPal flow)
   */
  showPaymentModal(plan = 'Free', price = '0') {
    const isFree = plan === 'Free';
    const modal = document.createElement('div');
    modal.className = 'modal-overlay active';
    modal.innerHTML = `
      <div class="modal" style="max-width:520px;position:relative;">
          <button class="modal-close" id="close-modal">✕</button>
          <div style="text-align:center;margin-bottom:28px;">
              <div style="width:56px;height:56px;border-radius:var(--r-md);background:${isFree ? 'var(--green-light)' : 'var(--primary-light)'};color:${isFree ? 'var(--green)' : 'var(--primary)'};display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:1.5rem;">
                  ${isFree ? '🚀' : '💳'}
              </div>
              <h2 style="font-size:1.375rem;margin-bottom:8px;">${isFree ? 'Start Building Today' : 'Upgrade to ' + plan}</h2>
              <p class="text-muted">${isFree ? 'Explore AutoCV with your free account.' : 'Unlock premium features for your career.'}</p>
          </div>

          ${!isFree ? `
          <div style="background:var(--surface-2);border:1px solid var(--border);border-radius:var(--r-md);padding:24px;margin-bottom:24px;">
              <div style="display:flex;justify-content:space-between;align-items:baseline;padding-bottom:16px;border-bottom:1px solid var(--border);margin-bottom:16px;">
                  <span style="font-weight:600;color:var(--text-2);">${plan} Plan</span>
                  <div>
                      <span style="font-size:1.75rem;font-weight:800;color:var(--primary);">${price}</span>
                      <span class="text-muted text-sm">${plan === 'Pro' ? '/mo' : ''}</span>
                  </div>
              </div>
              <div style="display:flex;flex-direction:column;gap:12px;">
                  <div style="display:flex;gap:10px;align-items:start;">
                      <span style="width:24px;height:24px;border-radius:50%;background:var(--primary);color:#fff;font-size:0.7rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px;">1</span>
                      <p class="text-sm"><strong>PayPal:</strong> aaditchandra2212@gmail.com</p>
                  </div>
                  <div style="display:flex;gap:10px;align-items:start;">
                      <span style="width:24px;height:24px;border-radius:50%;background:var(--primary);color:#fff;font-size:0.7rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px;">2</span>
                      <p class="text-sm"><strong>Bank Transfer:</strong> Message on LinkedIn for details</p>
                  </div>
                  <div style="display:flex;gap:10px;align-items:start;">
                      <span style="width:24px;height:24px;border-radius:50%;background:var(--primary);color:#fff;font-size:0.7rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px;">3</span>
                      <p class="text-sm"><strong>Process:</strong> Send payment & email to <strong>aaditchandra2212@gmail.com</strong></p>
                  </div>
              </div>
          </div>
          <a href="mailto:work.aadit@gmail.com?subject=AutoCV - Plan Upgrade (${plan})&body=Hi Aadit, I've sent the payment for the ${plan} plan. My email: "
             class="btn btn-primary btn-full btn-lg" style="margin-bottom:12px;">
              Verify Payment & Proceed
          </a>
          ` : `
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
              <button id="skip-to-login" class="btn btn-secondary">Skip for now</button>
              <button id="go-to-login" class="btn btn-primary">Get Started Free</button>
          </div>
          `}
          <p style="text-align:center;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-3);margin-top:8px;">Questions? linkedin.com/in/aadit-chandra</p>
      </div>
    `;
    document.body.appendChild(modal);

    document.getElementById('close-modal').onclick = () => modal.remove();
    if (isFree) {
      document.getElementById('skip-to-login').onclick = () => {
        modal.remove();
        window.location.href = '/pages/optimize.html?guest=true';
      };
      document.getElementById('go-to-login').onclick = () => {
        modal.remove();
        this.loginWithGoogle();
      };
    }
  },
};

// ── Score Ring Utility ──────────────────────────────────
function renderScoreRing(el, score, size = 96) {
  const r = size * 0.42, c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const color = score >= 75 ? 'var(--green)' : score >= 50 ? 'var(--orange)' : 'var(--red)';
  el.innerHTML = `
    <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="transform:rotate(-90deg)">
      <circle fill="none" stroke="var(--surface-3)" stroke-width="8" cx="${size/2}" cy="${size/2}" r="${r}"/>
      <circle fill="none" stroke="${color}" stroke-width="8" stroke-linecap="round"
        cx="${size/2}" cy="${size/2}" r="${r}"
        stroke-dasharray="${c}" stroke-dashoffset="${c}"
        style="transition:stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)"
        id="${el.id}-fill"/>
    </svg>
    <div class="score-ring-text" style="color:${color}">${score}%</div>
  `;
  requestAnimationFrame(() => setTimeout(() => {
    const f = document.getElementById(`${el.id}-fill`);
    if (f) f.style.strokeDashoffset = offset;
  }, 80));
}
window.renderScoreRing = renderScoreRing;

// ── Skeleton ─────────────────────────────────────────
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
        <div class="skeleton" style="height:28px;width:80px;border-radius:var(--r-pill)"></div>
        <div class="skeleton" style="height:28px;width:60px;border-radius:var(--r-pill)"></div>
      </div>
    </div>`;
}
window.showSkeleton = showSkeleton;

// ── Utilities ─────────────────────────────────────────
function esc(s) {
  if (!s) return '';
  return s.toString().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
window.esc = esc;

// ── Dropzone ─────────────────────────────────────────
function setupDropzone(zoneId, inputId, onFile) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  if (!zone || !input) return;
  zone.dataset.inputId = inputId;
  zone.dataset.originalHtml = zone.innerHTML;
  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('dragover'); if (e.dataTransfer.files[0]) _handleFile(e.dataTransfer.files[0], zone, onFile); });
  input.addEventListener('change', () => { if (input.files[0]) _handleFile(input.files[0], zone, onFile); });
}
window.setupDropzone = setupDropzone;

function _handleFile(file, zone, onFile) {
  const validExts = ['.pdf', '.docx', '.doc'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!validExts.includes(ext)) { toast('Invalid file type. Use PDF or DOCX.', 'error'); return; }
  if (file.size > 10 * 1024 * 1024) { toast('File too large. Max 10MB.', 'error'); return; }
  zone.classList.add('has-file');
  zone.innerHTML = `
    <div style="color:var(--green);font-size:1.5rem">✓</div>
    <div class="upload-main">${file.name}</div>
    <div class="upload-sub">${(file.size/1024).toFixed(0)} KB &nbsp;·&nbsp;
      <span class="upload-browse" onclick="window.resetDropzone('${zone.id}')">Remove</span>
    </div>`;
  onFile(file);
}

window.resetDropzone = function(zoneId) {
  const zone = document.getElementById(zoneId);
  if (!zone) return;
  zone.classList.remove('has-file');
  zone.innerHTML = zone.dataset.originalHtml || '';
  // Reset the file input
  const inputId = zone.dataset.inputId;
  if (inputId) {
    const input = document.getElementById(inputId);
    if (input) input.value = '';
  }
};

// ── Multi-file Dropzone (for recruiter batch) ──────────
function setupMultiDropzone(zoneId, inputId, onFiles) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  if (!zone || !input) return;
  input.multiple = true;
  zone.addEventListener('click', () => input.click());
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('dragover'); if (e.dataTransfer.files.length) onFiles(Array.from(e.dataTransfer.files)); });
  input.addEventListener('change', () => { if (input.files.length) onFiles(Array.from(input.files)); });
}
window.setupMultiDropzone = setupMultiDropzone;

// ── Tabs ─────────────────────────────────────────────
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
window.setupTabs = setupTabs;

// ── Diff ─────────────────────────────────────────────
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
window.generateDiff = generateDiff;

// ── Wait for Auth ────────────────────────────────────
/**
 * Convenience: wait for auth to be ready, then call callback.
 * Usage: waitForAuth((user) => { ... })
 */
function waitForAuth(callback) {
  if (auth.user !== undefined && auth.user !== null) {
    callback(auth.user);
  } else {
    window.addEventListener('auth:ready', (e) => {
      callback(e.detail.user);
    }, { once: true });
  }
}
window.waitForAuth = waitForAuth;

// ── Initialize ───────────────────────────────────────
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => auth.init());
} else {
  auth.init();
}

window.auth = auth;
console.log("AutoCV Auth v2 loaded | API:", API);
