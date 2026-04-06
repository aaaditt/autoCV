import os

welcome_path = r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\pages\welcome.html"

if os.path.exists(welcome_path):
    with open(welcome_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update buttons
    content = content.replace(
        '<button class="bg-primary-container text-on-primary-container px-10 py-4 rounded-full font-semibold text-lg flex items-center gap-2 hover:brightness-95 transition-all shadow-md">',
        '<button onclick="window.location.href=\'optimize.html\'" class="bg-primary-container text-on-primary-container px-10 py-4 rounded-full font-semibold text-lg flex items-center gap-2 hover:brightness-95 transition-all shadow-md">'
    )
    content = content.replace(
        '<a class="text-primary font-semibold text-sm hover:underline" href="/dashboard">',
        '<a class="text-primary font-semibold text-sm hover:underline" href="dashboard.html">'
    )
    
    with open(welcome_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Welcome page buttons fixed.")
else:
    print("Welcome page not found.")
