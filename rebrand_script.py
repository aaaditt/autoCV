import os
import re

def rebrand(directory):
    # Mapping of replacements
    replacements = {
        r'AutoCV': 'AutoCV',
        r'AutoCV': 'AutoCV',
        r'AutoCV': 'AutoCV',
        r'autocv': 'autocv',
        r'index\.html': 'home.html' # Be careful with this one
    }

    # Files to ignore
    ignore_dirs = {'.git', 'venv', '__pycache__', 'node_modules', '.gemini', 'stitch'}

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith(('.html', '.js', '.css', '.py', '.md', '.env', '.example')):
                file_path = os.path.join(root, file)
                
                # Skip the new index.html for index.html -> home.html replacement to avoid loop
                # Wait, actually I should only replace index.html if it's a link href
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Special case for index.html links
                # Replace links to index.html with home.html
                # But NOT in the root index.html itself (which is now the landing)
                # Actually, I'll do it manually for the landing page link.
                
                new_content = content
                new_content = new_content.replace('AutoCV', 'AutoCV')
                new_content = new_content.replace('AutoCV', 'AutoCV')
                new_content = new_content.replace('AutoCV', 'AutoCV')
                new_content = new_content.replace('autocv', 'autocv')
                
                # Link replacement: href="home.html" -> href="home.html"
                # This should happen in all files EXCEPT the new index.html (landing)
                if not file_path.endswith('frontend\\index.html'):
                    new_content = new_content.replace('href="home.html"', 'href="home.html"')
                    new_content = new_content.replace("href='home.html'", "href='home.html'")
                    new_content = new_content.replace('window.location.href = "home.html"', 'window.location.href = "home.html"')
                    new_content = new_content.replace("window.location.href = 'home.html'", "window.location.href = 'home.html'")

                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated: {file_path}")

if __name__ == "__main__":
    rebrand('c:\\Aadit\\Personal\\code-ide\\antigravity\\AutoCV')
    
    # Manually fix the landing page (index.html) link
    landing_path = 'c:\\Aadit\\Personal\\code-ide\\antigravity\\AutoCV\\frontend\\index.html'
    with open(landing_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the brand and the nav link
    content = content.replace('AutoCV', 'AutoCV')
    content = content.replace('Resume<span class="text-primary italic">AI</span>', 'Auto<span class="text-primary italic">CV</span>')
    content = content.replace("window.location.href = 'home.html'", "window.location.href = 'home.html'")
    
    with open(landing_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Final fix for landing page done.")
