import os
import re

def update_file(path, replacements, script_data=None):
    if not os.path.exists(path):
        print(f"Skipping {path}: File not found")
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    if script_data:
        content = content.replace('</body>', script_data + '\n</body>')
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. Update Landing Page (index.html)
landing_path = r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\index.html"
update_file(landing_path, {
    '<div class="text-xl font-bold tracking-tight text-slate-900">AutoCV</div>': '<a href="/index.html" class="text-xl font-bold tracking-tight text-slate-900 hover:opacity-80 transition-opacity">AutoCV</a>',
    '<button class="bg-primary-container text-on-primary-container px-6 py-2 rounded-full font-semibold hover:opacity-80 transition-opacity">Get Started</button>': '<button onclick="auth.loginWithGoogle()" class="bg-primary-container text-on-primary-container px-6 py-2 rounded-full font-semibold hover:opacity-80 transition-opacity">Get Started</button>',
    '<button class="bg-white text-primary-container px-10 py-5 rounded-full font-bold text-lg shadow-xl hover:scale-105 active:scale-95 transition-all">': '<button onclick="auth.loginWithGoogle()" class="bg-white text-primary-container px-10 py-5 rounded-full font-bold text-lg shadow-xl hover:scale-105 active:scale-95 transition-all">'
})

# 2. Update Pricing Page (pricing.html)
pricing_path = r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\pages\pricing.html"
update_file(pricing_path, {
    '<div class="text-xl font-bold tracking-tight text-slate-900 dark:text-white">AutoCV</div>': '<a href="/index.html" class="text-xl font-bold tracking-tight text-slate-900 dark:text-white hover:opacity-80 transition-opacity">AutoCV</a>',
    '<button class="text-slate-600 dark:text-slate-400 font-medium hover:opacity-80 transition-opacity">Login</button>': '<button onclick="window.location.href=\'login.html\'" class="text-slate-600 dark:text-slate-400 font-medium hover:opacity-80 transition-opacity">Login</button>',
    '<button class="bg-primary text-on-primary px-6 py-2 rounded-full font-semibold hover:opacity-90 transition-opacity">Get Started</button>': '<button onclick="auth.loginWithGoogle()" class="bg-primary text-on-primary px-6 py-2 rounded-full font-semibold hover:opacity-90 transition-opacity">Get Started</button>',
    '<button class="w-full py-3 rounded-full bg-surface-container-high text-primary font-bold hover:bg-surface-container-highest transition-colors">Start Free</button>': '<button onclick="auth.loginWithGoogle()" class="w-full py-3 rounded-full bg-surface-container-high text-primary font-bold hover:bg-surface-container-highest transition-colors">Start Free</button>',
    '<button class="w-full py-3 rounded-full editorial-gradient text-white font-bold hover:opacity-90 transition-opacity">Get Single</button>': '<button onclick="api.post(\'/payments/checkout/single\',{}).then(r=>window.location.href=r.checkout_url)" class="w-full py-3 rounded-full editorial-gradient text-white font-bold hover:opacity-90 transition-opacity">Get Single</button>',
    '<button class="w-full py-3 rounded-full bg-on-surface text-surface font-bold hover:opacity-90 transition-opacity">Go Pro</button>': '<button onclick="api.post(\'/payments/checkout/pro\',{}).then(r=>window.location.href=r.checkout_url)" class="w-full py-3 rounded-full bg-on-surface text-surface font-bold hover:opacity-90 transition-opacity">Go Pro</button>'
})

# 3. Update Dashboard Page (dashboard.html)
dashboard_path = r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\pages\dashboard.html"
update_file(dashboard_path, {
    '<span class="text-lg font-bold text-slate-900 dark:text-white tracking-tight">AutoCV</span>': '<a href="/index.html" class="text-lg font-bold text-slate-900 dark:text-white tracking-tight hover:opacity-80 transition-opacity">AutoCV</a>',
    'href="#"': 'href="javascript:void(0)"', # Temporary neutralizer
    'Dashboard\n            </a>': 'Dashboard\n            </a>', # Fixed in script
}, script_data="""
<script>
  document.addEventListener("DOMContentLoaded", () => {
      // Fix Sidebar Links
      const links = document.querySelectorAll('aside nav a');
      links[0].href = 'dashboard.html';
      links[1].href = 'optimize.html';
      links[2].href = 'history.html';
      links[3].href = 'account.html';
      
      const newResumeBtn = document.querySelector('aside button');
      if (newResumeBtn) newResumeBtn.onclick = () => window.location.href = 'optimize.html';

      // Fix Top Nav Login/Started -> Logout
      const topNavButtons = document.querySelector('header .flex.items-center.gap-4');
      if (topNavButtons) {
          topNavButtons.innerHTML = `
            <button onclick="auth.logout()" class="text-slate-600 text-sm font-medium hover:opacity-80 transition-opacity">Logout</button>
            <div class="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold" id="nav-avatar">U</div>
          `;
      }
  });
</script>
""")

# 4. Mobile Menu Fix (Common Navigation injection)
def add_mobile_menu(path):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add hamburger icon and basic mobile menu logic
    if '<nav' in content and 'mobile-menu-injected' not in content:
        hamburger = """
        <button id="mobile-menu-btn" class="md:hidden text-slate-900 p-2">
            <span class="material-symbols-outlined">menu</span>
        </button>
        <!-- mobile-menu-injected -->
        """
        content = content.replace('<div class="flex items-center gap-4">', hamburger + '<div class="hidden md:flex items-center gap-4">')
        
        mobile_js = """
        <script>
        document.addEventListener('DOMContentLoaded', () => {
            const btn = document.getElementById('mobile-menu-btn');
            if (btn) {
                btn.onclick = () => {
                   const menu = document.createElement('div');
                   menu.className = 'fixed inset-0 z-[100] bg-white flex flex-col p-8 gap-6 animate-page';
                   menu.innerHTML = `
                     <div class="flex justify-between items-center mb-8">
                        <span class="text-xl font-bold">AutoCV</span>
                        <button id="close-menu" class="p-2"><span class="material-symbols-outlined">close</span></button>
                     </div>
                     <a href="/index.html" class="text-lg font-bold border-b pb-4">Home</a>
                     <a href="/pages/pricing.html" class="text-lg font-bold border-b pb-4">Pricing</a>
                     <a href="/pages/login.html" class="text-lg font-bold border-b pb-4">Login</a>
                     <button onclick="auth.loginWithGoogle()" class="bg-primary text-white py-4 rounded-full font-bold mt-4">Get Started</button>
                   `;
                   document.body.appendChild(menu);
                   document.getElementById('close-menu').onclick = () => menu.remove();
                };
            }
        });
        </script>
        """
        content = content.replace('</body>', mobile_js + '</body>')
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

add_mobile_menu(landing_path)
add_mobile_menu(pricing_path)

# Update app.js to include toast and other missing features
with open(r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\static\js\app.js", 'r', encoding='utf-8') as f:
    app_js = f.read()

# Add missing signInWithGoogle if needed or fix login.html reference
# The login.html had signInWithEmail() call which expects api.post('/auth/login')
# I'll make sure it's working by adding a global toast to window if missing
if 'window.toast = toast;' not in app_js:
    app_js = app_js.replace('// ── Shared nav HTML ──────────────────────────────────────', 'window.toast = toast;\n\n// ── Shared nav HTML ──────────────────────────────────────')

with open(r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\static\js\app.js", 'w', encoding='utf-8') as f:
    f.write(app_js)
