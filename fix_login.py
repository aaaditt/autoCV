import os

login_path = r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\pages\login.html"

if os.path.exists(login_path):
    with open(login_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix Google Login Button
    content = content.replace(
        '<button class="flex items-center justify-center gap-3 w-full h-12 bg-surface-container-lowest border border-outline-variant/30 rounded-full text-on-surface font-medium hover:bg-surface-container-low transition-colors duration-200">',
        '<button onclick="auth.loginWithGoogle()" class="flex items-center justify-center gap-3 w-full h-12 bg-surface-container-lowest border border-outline-variant/30 rounded-full text-on-surface font-medium hover:bg-surface-container-low transition-colors duration-200">'
    )
    
    # Fix Create Account Link
    content = content.replace(
        '<a class="text-primary-container font-semibold hover:underline inline-flex items-center gap-1 group" href="#">',
        '<a class="text-primary-container font-semibold hover:underline inline-flex items-center gap-1 group" href="javascript:auth.loginWithGoogle()">'
    )
    
    # Update signInWithEmail to use Toast
    content = content.replace(
        'alert("Login Failed: " + err.message);',
        'toast("Login Failed: " + err.message, "error");'
    )
    
    with open(login_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Login page fixed.")
else:
    print("Login page not found.")
