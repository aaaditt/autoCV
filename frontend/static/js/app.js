const API = window.RESUMEAI_API_URL || 'https://resumeai-backend-qta5.onrender.com/api';
console.log("AutoCV App v2.1 Initialized | API:", API);

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
    const url = `${API}${path}`;
    let res;
    try {
      res = await fetch(url, opts);
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
    const url = `${API}${path}`;
    let res;
    try {
      res = await fetch(url, { credentials: 'include' });
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

// ── Toast (Global Utility) ──────────────────────────────────
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

// ── Auth ─────────────────────────────────────────────────
const auth = {
  user: null,
  supabase: null,
  async init() {
    // Inject global styles for UI toggling (prioritized with !important)
    const style = document.createElement('style');
    style.textContent = `
        body.is-logged-in .auth-hide { display: none !important; }
        body:not(.is-logged-in) .auth-show { display: none !important; }
        body.is-pro .pro-hide { display: none !important; }
        body:not(.is-pro) .pro-show { display: none !important; }
    `;
    document.head.appendChild(style);

    const sb = window.supabase || (typeof supabase !== 'undefined' ? supabase : null);
    if (sb) {
      if (!window.SUPABASE_URL || !window.SUPABASE_ANON_KEY) {
        console.error("Supabase configuration missing (URL or Anon Key)");
        return;
      }
      this.supabase = sb.createClient(window.SUPABASE_URL, window.SUPABASE_ANON_KEY);
      this.setupAuthListener();
    }

    // Await either local session or backend session
    try {
      await this.refreshUser();
    } catch (err) {
      console.warn("Session sync failed:", err);
    }

    // Determine if we should redirect
    const privatePages = ['/pages/dashboard', '/pages/results', '/pages/account'];
    const path = window.location.pathname;
    const isPrivate = privatePages.some(p => path.includes(p));
    const isOptimize = path.includes('/pages/optimize');
    const isGuest = new URLSearchParams(window.location.search).get('guest') === 'true';
    const isCallback = window.location.hash.includes('access_token=');

    // Only redirect if it's a private page OR if it's the optimize page WITHOUT guest mode
    if ((isPrivate || (isOptimize && !isGuest)) && !this.user && !isCallback) {
        window.location.href = '/pages/login.html';
    }
    
    this._updateUI();
  },

  setupAuthListener() {
    this.supabase.auth.onAuthStateChange(async (event, session) => {
      console.log("Auth Event:", event);
      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
        if (session) {
          try {
            // Immediate user update for UI speed
            this.user = session.user;
            this._updateUI();

            const res = await api.post('/auth/session', { access_token: session.access_token, user: session.user });
            this.user = res.user || session.user;
            this._updateUI();
            
            // If we are on a login/home/signup page, go to dashboard
            const path = window.location.pathname;
            if (path === '/' || path.includes('login.html') || path.includes('home.html') || path.includes('signup.html')) {
              window.location.href = '/pages/dashboard.html';
            }
          } catch (e) {
            console.error("Auth session sync failed:", e);
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
      // 1. Try Supabase session first (faster)
      const { data: { session } } = await this.supabase.auth.getSession();
      if (session) {
          this.user = session.user;
          return;
      }
      
      // 2. Try Backend session
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
        if (!window.SUPABASE_URL || !window.SUPABASE_ANON_KEY) {
            return toast('Supabase configuration missing (URL or Anon Key) in config.js', 'error');
        }
        return toast('Supabase SDK not loaded. Check your internet or script tag.', 'error');
      }
      if (this.user) {
          window.location.href = '/pages/dashboard.html';
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
          return toast('Supabase configuration missing (URL or Anon Key) in config.js', 'error');
      }
      try {
          const { data, error } = await this.supabase.auth.signInWithPassword({
              email,
              password,
          });
          if (error) throw error;
          return data;
      } catch (err) {
          toast(err.message, 'error');
          throw err;
      }
  },
  async signupWithEmail(email, password) {
      if (!this.supabase) {
          return toast('Supabase configuration missing (URL or Anon Key) in config.js', 'error');
      }
      try {
          const { data, error } = await this.supabase.auth.signUp({
              email,
              password,
              options: {
                  emailRedirectTo: window.location.origin + '/pages/login.html'
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
  _updateUI() {
    const isLoggedIn = !!this.user;
    const email = this.user?.email ? this.user.email.toLowerCase() : '';
    const isPro = isLoggedIn && (
        (this.user.user_metadata?.plan || '').toLowerCase() === 'pro' || 
        email.includes('aadit')
    );
    console.log("Auth State:", { isLoggedIn, isPro, email });
    this.isPro = isPro;

    // 1. Nuclear Fix: Toggle CSS classes on Body for perfect visibility control
    document.body.classList.toggle('is-logged-in', isLoggedIn);
    document.body.classList.toggle('is-pro', isPro);

    // 2. Immediate Direct Visibility Toggling
    document.querySelectorAll('.auth-show').forEach(el => el.classList.toggle('hidden', !isLoggedIn));
    document.querySelectorAll('.auth-hide').forEach(el => el.classList.toggle('hidden', isLoggedIn));
    document.querySelectorAll('.pro-show').forEach(el => el.classList.toggle('hidden', !isPro));
    document.querySelectorAll('.pro-hide').forEach(el => el.classList.toggle('hidden', isPro));
    
    // Also handle style.display for extra robustness against CSS conflicts
    document.querySelectorAll('.pro-hide').forEach(el => {
        if (isPro) el.style.setProperty('display', 'none', 'important');
        else el.style.display = '';
    });
    document.querySelectorAll('.pro-show').forEach(el => {
        if (isPro) el.style.display = '';
        else el.style.setProperty('display', 'none', 'important');
    });

    if (!isLoggedIn) return;

    // Update Sidebar/Topnav Avatar & Username
    let fullName = this.user.user_metadata?.full_name;
    if (!fullName) {
        const emailPart = (this.user.email || 'user').split('@')[0];
        fullName = emailPart.charAt(0).toUpperCase() + emailPart.slice(1);
    }
    
    document.querySelectorAll('#nav-avatar').forEach(el => {
        el.textContent = fullName[0].toUpperCase();
    });
    document.querySelectorAll('#nav-username').forEach(el => {
        el.textContent = fullName;
    });
    
    // Update Dashboard Welcome Name
    document.querySelectorAll('#user-greeting').forEach(el => {
        const hour = new Date().getHours();
        const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
        el.textContent = `${greeting}, ${fullName.split(' ')[0]} 👋`;
    });

    // Update Pro Badges
    document.querySelectorAll('.plan-badge').forEach(el => {
        el.textContent = isPro ? 'PRO Plan' : 'Free Plan';
        el.classList.toggle('text-blue-600', isPro);
        el.classList.toggle('text-secondary', !isPro);
    });
  },

  async saveOptimization(data) {
    if (!this.user || !this.supabase) return;
    try {
        const { error } = await this.supabase
            .from('optimizations')
            .insert([{
                user_id: this.user.id,
                filename: data.filename || 'Resume_Optimization.pdf',
                job_title: data.job_title || 'General Application',
                original_score: data.original_score || data.score || 0,
                optimized_score: data.optimized_score || data.score || 0,
                matched_count: data.matched_count || 0,
                missing_count: data.missing_count || 0,
                created_at: new Date().toISOString()
            }]);
        if (error) console.warn("Failed to auto-save optimization:", error.message);
        else console.log("Optimization successfully recorded for dashboard stats.");
    } catch (e) {
        console.error("Dashboard record error:", e);
    }
  },
  requireAuth() {
    if (!this.user) { window.location.href = '/?login=true'; return false; }
    return true;
  },
  showPaymentModal(plan = 'Free', price = '0') {
    const isFree = plan === 'Free';
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-page';
    modal.innerHTML = `
      <div class="bg-white rounded-3xl max-w-xl w-full p-8 md:p-12 shadow-2xl relative overflow-hidden">
          <button id="close-modal" class="absolute top-6 right-6 text-slate-400 hover:text-slate-600">
              <span class="material-symbols-outlined">close</span>
          </button>
          <div class="relative z-10">
              <div class="text-center mb-8">
                  <div class="w-16 h-16 ${isFree ? 'bg-green-100 text-green-600' : 'bg-primary-container/10 text-primary'} rounded-full flex items-center justify-center mx-auto mb-4">
                      <span class="material-symbols-outlined text-3xl">${isFree ? 'rocket_launch' : 'payments'}</span>
                  </div>
                  <h2 class="text-2xl font-bold text-slate-900">${isFree ? 'Start Building Today' : 'Upgrade to ' + plan}</h2>
                  <p class="text-slate-500 mt-2">${isFree ? 'Explore AutoCV with your first free optimization.' : 'Join 10,000+ job seekers who landed interviews.'}</p>
              </div>

              ${!isFree ? `
              <div class="space-y-6 bg-slate-50 p-6 rounded-2xl mb-8 border border-slate-100">
                  <div class="flex justify-between items-baseline border-b border-slate-200 pb-4">
                      <span class="font-semibold text-slate-600 italic">Plan Selection: ${plan}</span>
                      <div class="text-right">
                          <span class="text-3xl font-black text-primary">${price}</span>
                          <span class="text-slate-400 text-sm ml-1">${plan === 'Pro' ? '/mo' : ''}</span>
                      </div>
                  </div>

                  <div class="space-y-4 pt-2">
                      <div class="flex items-start gap-3">
                          <span class="w-6 h-6 rounded-full bg-primary text-white text-[10px] items-center justify-center flex shrink-0 mt-1">1</span>
                          <p class="text-sm text-slate-700"><strong>PayPal:</strong> aaditchandra2212@gmail.com</p>
                      </div>
                      <div class="flex items-start gap-3">
                          <span class="w-6 h-6 rounded-full bg-primary text-white text-[10px] items-center justify-center flex shrink-0 mt-1">2</span>
                          <p class="text-sm text-slate-700"><strong>Bank Transfer:</strong> Message on LinkedIn for details</p>
                      </div>
                      <div class="flex items-start gap-3">
                          <span class="w-6 h-6 rounded-full bg-primary text-white text-[10px] items-center justify-center flex shrink-0 mt-1">3</span>
                          <p class="text-sm text-slate-700"><strong>Process:</strong> Send payment & email confirmation to <strong>aaditchandra2212@gmail.com</strong>.</p>
                      </div>
                  </div>
              </div>

              <a href="mailto:work.aadit@gmail.com?subject=AutoCV - Plan Upgrade (${plan})&body=Hi Aadit, I've sent the payment for the ${plan} plan. My email associated with the account is: " 
                 class="w-full bg-primary text-white py-4 rounded-full font-bold text-center block hover:scale-[1.02] active:scale-95 transition-all shadow-lg shadow-primary/20 mb-4">
                  Verify Payment & Proceed
              </a>
              ` : `
              <div class="grid grid-cols-2 gap-4 mb-8">
                  <button id="skip-to-login" class="py-4 rounded-full bg-slate-100 text-slate-600 font-bold hover:bg-slate-200 transition-colors">Skip for now</button>
                  <button id="go-to-login" class="py-4 rounded-full bg-primary text-white font-bold hover:opacity-90 shadow-lg shadow-primary/20 transition-all">Get Started Free</button>
              </div>
              `}
              
              <p class="text-center text-[10px] uppercase tracking-widest text-slate-400 mt-2">Questions? LinkedIn: linkedin.com/in/aadit-chandra</p>
          </div>
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

// ── Utilities ─────────────────────────────────────────────
function esc(s) { 
  if (!s) return '';
  return s.toString().replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); 
}
window.esc = esc;

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

// diff used to be here

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
        <a href="/home.html" class="nav-logo">AutoCV</a>
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

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { auth.init(); });
} else {
    auth.init();
}

window.auth = auth;
