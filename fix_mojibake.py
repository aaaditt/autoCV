import os
import glob
import re

replacements = {
    "Ã¢â‚¬â€ ": "&mdash;",
    "Ã°Å¸â€œâ€ž": "📄",
    "ðŸ“„": "<span class=\"material-symbols-outlined\" style=\"font-size:2rem;color:var(--text-3);\">description</span>",
    "Ã¢Å“Â¦": "✦",
    "Ã‚Â·": "&middot;",
    "Ã¢â€¢Â Ã¢â€¢Â Ã¢â€¢Â ": "•••",
    "Ã¢â€¢Â": "•",
    "ðŸ‘‹": "👋",
    "ðŸš€": "🚀",
    "ðŸ—’": "🔒", # This was replacing lock icon `ðŸ—’` or similar, let's replace with `lock`
    "âœ¦": "✦",
    "textContent = '&mdash;'": "innerHTML = '&mdash;'",
    "textContent = '&middot;'": "innerHTML = '&middot;'",
    "Ã—": "&times;"
}

files = glob.glob('frontend/**/*.html', recursive=True) + glob.glob('frontend/**/*.js', recursive=True)

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for bad, good in replacements.items():
        content = content.replace(bad, good)
        
    # Also fix textContent = '&mdash;' which causes the literal &mdash; to show up
    content = content.replace(".textContent = '&mdash;'", ".innerHTML = '&mdash;'")
    
    if original != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
