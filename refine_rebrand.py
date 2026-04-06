import os

def cleanup_links_and_brand(directory):
    replacements = {
        'ResumeAI': 'AutoCV',
        'Resume AI': 'AutoCV',
        'Resumeai': 'AutoCV',
        'resumeai': 'autocv',
        '/index.html': '/home.html',
        'href="index.html"': 'href="home.html"',
        'href="welcome.html"': 'href="home.html"', # Redirect onboarding to home as well if needed
    }

    ignore_dirs = {'.git', 'venv', '__pycache__', 'node_modules', '.gemini', 'stitch'}

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if file.endswith(('.html', '.js', '.css', '.py')):
                file_path = os.path.join(root, file)
                
                # Special skip for the NEW root index.html to avoid renaming its own link
                if file_path.endswith('frontend\\index.html'):
                    continue
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                new_content = content
                for old, new in replacements.items():
                    new_content = new_content.replace(old, new)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Refined: {file_path}")

if __name__ == "__main__":
    cleanup_links_and_brand('c:\\Aadit\\Personal\\code-ide\\antigravity\\ResumeAI\\frontend')
