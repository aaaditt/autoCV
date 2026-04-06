import os
import re

optimize_html_path = r"c:\Aadit\Personal\code-ide\antigravity\AutoCV\frontend\pages\optimize.html"

with open(optimize_html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add IDs to elements
content = content.replace('<div class="w-full h-48 border-2 border-dashed', '<input type="file" id="resume-input" class="hidden" accept=".pdf,.doc,.docx" /><div id="upload-zone" data-input-id="resume-input" class="w-full h-48 border-2 border-dashed')

content = content.replace('<textarea class="w-full h-64 bg-surface border-none', '<textarea id="jd-input" class="w-full h-64 bg-surface border-none')

content = content.replace('<button class="w-full bg-primary-container text-on-primary-container py-4', '<button id="analyze-btn" class="w-full bg-primary-container text-on-primary-container py-4')

content = content.replace('<section class="w-[58%] bg-surface-container-low overflow-y-auto p-10 flex flex-col items-center">', '<section id="right-panel" class="w-[58%] bg-surface-container-low overflow-y-auto p-10 flex flex-col items-center">')

content = content.replace('<span class="w-6 h-6 flex items-center justify-center rounded-full border border-outline text-[10px] font-bold">2</span>', '<span id="step-2" class="w-6 h-6 flex items-center justify-center rounded-full border border-outline text-[10px] font-bold">2</span>')

# Empty out the right panel and let JS render it or keep it static?
# The instructions say "Right panel of optimizer shows skeleton before analysis runs". I think I'll leave the static content and let JS replace it, or empty it. Let's make it an empty div inside right-panel.
right_panel_pattern = re.compile(r'(<section id="right-panel" class="w-\[58%] bg-surface-container-low overflow-y-auto p-10 flex flex-col items-center">).*?(</section>)', re.DOTALL)
content = right_panel_pattern.sub(r'\1\n<div class="flex items-center justify-center w-full h-full text-on-secondary-container">Start by uploading your resume and job description.</div>\n\2', content)

script = """
<script>
  let resumeFile = null;
  document.addEventListener("DOMContentLoaded", () => {
      // Step 3 wireup
      setupDropzone('upload-zone', 'resume-input', file => { resumeFile = file; });

      const analyzeBtn = document.getElementById('analyze-btn');
      const jdInput = document.getElementById('jd-input');
      const rightPanel = document.getElementById('right-panel');

      analyzeBtn.addEventListener('click', async () => {
        if (!resumeFile) return toast('Please upload a resume first', 'error');
        const jd = jdInput.value.trim();
        if (jd.length < 50) return toast('Job description needs to be at least 50 chars', 'error');
        
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = 'Analyzing...';
        
        rightPanel.innerHTML = '<div id="skeleton-container" class="w-full h-full flex items-center justify-center"></div>';
        showSkeleton('skeleton-container');

        const formData = new FormData();
        formData.append('resume', resumeFile);
        formData.append('job_description', jd);

        try {
          const res = await api.post('/analyze', formData, true);
          renderAnalysisResults(res);
        } catch (e) {
          if (e.message.includes('LIMIT_REACHED') || e.message === 'Limit reached') {
              window.location.href = '/pages/upgrade.html';
          } else {
              toast(e.message, 'error');
              rightPanel.innerHTML = '<div class="text-error text-center p-10 mt-20"><p>Failed to analyze. Please try again.</p></div>';
          }
        } finally {
          analyzeBtn.disabled = false;
          analyzeBtn.innerHTML = 'Analyze My Resume Free <span class="material-symbols-outlined text-[18px]">arrow_forward</span>';
        }
      });
  });

  function renderAnalysisResults(data) {
     const rightPanel = document.getElementById('right-panel');
     rightPanel.innerHTML = `
      <div class="max-w-2xl w-full space-y-8 animate-page">
         <div class="bg-surface-container-lowest rounded-xl p-8 shadow-sm flex flex-col md:flex-row items-center gap-10">
            <div class="relative flex items-center justify-center w-32 h-32 shrink-0" id="score-ring-container"></div>
            <div class="flex-1 text-center md:text-left">
                <h3 class="text-lg font-bold mb-1">Analysis Complete</h3>
                <p class="text-sm text-on-secondary-container leading-relaxed">Your resume was compared against the job description.</p>
                <div class="flex justify-center md:justify-start gap-4 mt-4">
                    <div class="flex items-center gap-1.5 text-tertiary font-semibold text-xs">
                        <span class="material-symbols-outlined text-[16px]">check_circle</span>
                        ${data.matched_count} Matched
                    </div>
                    <div class="flex items-center gap-1.5 text-error font-semibold text-xs">
                        <span class="material-symbols-outlined text-[16px]">cancel</span>
                        ${data.missing_count + data.blurred_missing_count} Missing
                    </div>
                </div>
            </div>
         </div>
         <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
                <h4 class="text-xs font-bold uppercase tracking-wider text-on-secondary-container">Matched</h4>
                <div class="flex flex-wrap gap-2">
                    ${data.visible_matched.map(kw => `<span class="px-3 py-1.5 bg-tertiary-container/10 text-tertiary text-[11px] font-bold rounded-full">${kw}</span>`).join('')}
                    ${data.blurred_matched_count > 0 ? `<span class="px-3 py-1.5 bg-surface-container-high text-on-secondary-container text-[11px] font-bold rounded-full blur-[2px] select-none">+${data.blurred_matched_count} more</span>` : ''}
                </div>
            </div>
            <div class="space-y-4">
                <h4 class="text-xs font-bold uppercase tracking-wider text-on-secondary-container">Critical Gaps</h4>
                <div class="flex flex-wrap gap-2 relative">
                    <span class="px-3 py-1.5 bg-surface-container-high text-on-secondary-container text-[11px] font-bold rounded-full blur-[3px] select-none">Hidden Keyword</span>
                    <span class="px-3 py-1.5 bg-surface-container-high text-on-secondary-container text-[11px] font-bold rounded-full blur-[4px] select-none">Another Hidden</span>
                    <div class="absolute inset-0 flex items-center justify-center"><span class="material-symbols-outlined text-primary text-[20px] bg-white rounded-full">lock</span></div>
                </div>
            </div>
         </div>
         <div class="relative overflow-hidden bg-primary rounded-xl p-8 text-white shadow-xl shadow-primary/20 mt-8 group">
            <div class="absolute -right-20 -bottom-20 w-64 h-64 bg-primary-container blur-3xl rounded-full opacity-50 group-hover:scale-125 transition-transform duration-700"></div>
            <div class="relative z-10 flex flex-col md:flex-row gap-8 items-center">
                <div class="flex-1 space-y-4 text-center md:text-left">
                    <h2 class="text-2xl font-bold leading-tight">Unlock AI Tailoring</h2>
                    <ul class="space-y-2 inline-block text-left">
                        <li class="flex items-center gap-2 text-sm text-white/90"><span class="material-symbols-outlined text-[18px]">verified</span>Generate AI-optimized bullet points</li>
                    </ul>
                </div>
                <div class="bg-white/10 backdrop-blur-md rounded-2xl p-6 text-center min-w-[160px] border border-white/20 shadow-lg">
                    <button onclick="handleOptimizeNow()" id="optimize-now-btn" class="w-full bg-white text-primary px-6 py-3 rounded-full text-sm font-bold hover:scale-105 active:scale-95 transition-all shadow-md">
                        Optimize Now
                    </button>
                    <p class="text-[10px] uppercase tracking-widest text-white/70 mt-3">$19 One-time</p>
                </div>
            </div>
         </div>
      </div>
     `;
     renderScoreRing(document.getElementById('score-ring-container'), data.score);
     
     const step2 = document.getElementById('step-2');
     if (step2) {
         step2.classList.remove('border', 'border-outline');
         step2.classList.add('bg-primary', 'text-white');
         step2.parentElement.classList.remove('opacity-40');
     }
  }

  window.handleOptimizeNow = async () => {
    const btn = document.getElementById('optimize-now-btn');
    btn.disabled = true;
    btn.innerHTML = 'Redirecting...';
    try {
        const res = await api.post('/payments/checkout/single', {});
        window.location.href = res.url;
    } catch (e) {
        toast(e.message, 'error');
        btn.disabled = false;
        btn.innerHTML = 'Optimize Now';
    }
  }
</script>
"""

content = content.replace('</body>', script + '\n</body>')

with open(optimize_html_path, 'w', encoding='utf-8') as f:
    f.write(content)
