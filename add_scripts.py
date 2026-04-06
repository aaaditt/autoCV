import os
import glob
import re

frontend_dir = r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend"
pages_dir = os.path.join(frontend_dir, "pages")

supabase_cdn = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>\n'
app_js_pattern = re.compile(r'(<script src="([^"]*)app\.js"></script>)')

def add_scripts(filepath, is_index=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False

    # Add supabase to head if not present
    if supabase_cdn.strip() not in content and '<head>' in content:
        content = content.replace('</head>', f'    {supabase_cdn}</head>')
        modified = True

    # Check for app.js and config.js
    if is_index:
        config_str = '<script src="./static/js/config.js"></script>\n'
    else:
        config_str = '<script src="../static/js/config.js"></script>\n'

    if 'app.js' in content and 'config.js' not in content:
        content = app_js_pattern.sub(lambda m: config_str + m.group(1), content)
        modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

add_scripts(os.path.join(frontend_dir, "index.html"), is_index=True)

for html_file in glob.glob(os.path.join(pages_dir, "*.html")):
    add_scripts(html_file)

print("Done")
