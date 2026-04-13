import os
import glob
import re

# Comprehensive list of mojibake patterns to fix
replacements = {
    "Å“Â¦": "✦",
    "Ã¢â‚¬â€": "&mdash;",
    "Ã°Å¸â€œâ€ž": "📄",
    "ðŸ“„": "<span class=\"material-symbols-outlined\" style=\"font-size:2rem;color:var(--text-3);\">description</span>",
    "Ã¢Å“Â¦": "✦",
    "Ã‚Â·": "&middot;",
    "Ã¢â€¢Â Ã¢â€¢Â Ã¢â€¢Â ": "•••",
    "Ã¢â€¢Â": "•",
    "ðŸ‘‹": "👋",
    "ðŸš€": "🚀",
    "ðŸ—’": "🔒", 
    "âœ¦": "✦",
    "Ã—": "&times;",
    "Ã©": "é",
    "Ã¡": "á",
    "Ã³": "ó",
    "Ãº": "ú",
    "Ã±": "ñ",
    "Ã": "&agrave;", # Common partial corruption
}

files = glob.glob('frontend/**/*.html', recursive=True) + \
        glob.glob('frontend/**/*.js', recursive=True) + \
        glob.glob('frontend/**/*.css', recursive=True)

for filepath in files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        for bad, good in replacements.items():
            if bad in content:
                content = content.replace(bad, good)
        
        # Fixed potential literal &mdash; vs symbol
        content = content.replace(".textContent = '&mdash;'", ".innerHTML = '&mdash;'")
        content = content.replace(".textContent = '&middot;'", ".innerHTML = '&middot;'")
        
        if original != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
    except Exception as e:
        print(f"Could not process {filepath}: {e}")
