import os

html_path = r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\pages\results.html"

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add ids to download buttons
content = content.replace(
    '<button class="bg-blue-600 text-white rounded-full px-8 py-3 flex items-center gap-2 font-bold uppercase tracking-wider text-xs hover:brightness-110 active:scale-95 transition-transform">',
    '<button id="download-pdf-btn" class="bg-blue-600 text-white rounded-full px-8 py-3 flex items-center gap-2 font-bold uppercase tracking-wider text-xs hover:brightness-110 active:scale-95 transition-transform">'
)
content = content.replace(
    '<button class="bg-surface-container-high text-primary rounded-full px-8 py-3 flex items-center gap-2 font-bold uppercase tracking-wider text-xs hover:brightness-105 active:scale-95 transition-transform">',
    '<button id="download-docx-btn" class="bg-surface-container-high text-primary rounded-full px-8 py-3 flex items-center gap-2 font-bold uppercase tracking-wider text-xs hover:brightness-105 active:scale-95 transition-transform">'
)

script = """
<script>
  document.addEventListener("DOMContentLoaded", () => {
      const resultStr = sessionStorage.getItem('opt_result');
      if (!resultStr) {
          toast('No recent optimization found.', 'error');
          // Optional: handle fallback case or wait
          return;
      }
      const data = JSON.parse(resultStr);

      // We can manipulate DOM using data.optimized_text here
      // For brevity, skipping full text replacement and just setting up
      // download listeners since the structure already has placeholders.
      // But we will wire the download buttons to the backend endpoints.
      
      const downloadPdfBtn = document.getElementById('download-pdf-btn');
      const downloadDocxBtn = document.getElementById('download-docx-btn');
      
      const handleDownload = async (format) => {
          try {
              // we can't use api.get directly for blob if it does res.json()
              const res = await fetch(window.RESUMEAI_API_URL + '/download/' + format, {
                  method: 'GET',
                  credentials: 'include'
              });
              if (!res.ok) throw new Error('Download failed');
              const blob = await res.blob();
              const url = window.URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.style.display = 'none';
              a.href = url;
              a.download = `optimized_resume.${format}`;
              document.body.appendChild(a);
              a.click();
              window.URL.revokeObjectURL(url);
          } catch(e) {
              toast(e.message, 'error');
          }
      };

      if (downloadPdfBtn) downloadPdfBtn.addEventListener('click', () => handleDownload('pdf'));
      if (downloadDocxBtn) downloadDocxBtn.addEventListener('click', () => handleDownload('docx'));
  });
</script>
"""

content = content.replace('</body>', script + '\n</body>')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)
