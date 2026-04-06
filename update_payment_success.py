import os

html_path = r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\pages\payment-success.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

script = """
<script>
  document.addEventListener("DOMContentLoaded", async () => {
      const urlParams = new URLParams(window.location.search);
      const sessionId = urlParams.get('session_id');

      if (!sessionId) {
          toast('Missing session ID', 'error');
          return;
      }

      try {
          // Verify payment
          const verifyRes = await api.get('/payments/verify/' + sessionId);
          if (verifyRes.paid) {
              // Now call optimize
              const optRes = await api.post('/optimize', {});
              sessionStorage.setItem('opt_result', JSON.stringify(optRes));
              
              // update UI to show success
              document.querySelector('.progress-fill').style.width = '100%';
              setTimeout(() => {
                  window.location.href = '/pages/results.html';
              }, 700);
          } else {
              toast('Payment not confirmed', 'error');
              setTimeout(() => { window.location.href='/pages/dashboard.html'; }, 2000);
          }
      } catch (e) {
          toast(e.message || 'Error processing request', 'error');
          document.querySelector('main').innerHTML = '<div class="text-center p-10"><h2 class="text-xl font-bold text-error">Something went wrong.</h2><p class="mt-4">Please contact support@autocv.co.</p></div>';
      }
  });
</script>
"""

# add URLParams polyfill/typo fix
script = script.replace('URLParams', 'URLSearchParams')

content = content.replace('</body>', script + '\n</body>')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
