/* ═══════════════════════════════════════════════════════════
   animations.js — AutoCV Scroll + Animation Controller
   Load with defer on every page.
   ═══════════════════════════════════════════════════════════ */

(function () {
    'use strict';

    /* ──────────────────────────────────────────
       1. SCROLL-TRIGGERED REVEAL
       Adds .visible to any .reveal element when
       it crosses the 15% viewport threshold.
    ────────────────────────────────────────── */
    function initScrollReveal() {
        const targets = document.querySelectorAll('.reveal');
        if (!targets.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target); // Fire once only
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

        targets.forEach(el => observer.observe(el));
    }

    /* ──────────────────────────────────────────
       2. NUMBER COUNTER ANIMATION
       Usage: <span class="counter" data-target="94" data-suffix="%">0</span>
       Triggers when element enters viewport.
    ────────────────────────────────────────── */
    function animateCounter(el) {
        const target = parseInt(el.dataset.target, 10);
        const suffix = el.dataset.suffix || '';
        const prefix = el.dataset.prefix || '';
        const duration = parseInt(el.dataset.duration || 1500, 10);
        const startTime = performance.now();
        const easeOut = t => 1 - Math.pow(1 - t, 3);

        function tick(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = Math.round(easeOut(progress) * target);
            el.textContent = prefix + current.toLocaleString() + suffix;
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    function initCounters() {
        const counters = document.querySelectorAll('.counter');
        if (!counters.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.animated) {
                    entry.target.dataset.animated = 'true';
                    animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(el => observer.observe(el));
    }

    /* ──────────────────────────────────────────
       3. SCORE RING ANIMATOR
       Finds all .score-ring elements with data-score.
       Animates SVG stroke-dashoffset from 283 (0%) to
       target position based on score.
       Usage: <div class="score-ring" data-score="78">
    ────────────────────────────────────────── */
    function animateRing(ring) {
        const score = parseInt(ring.dataset.score || 0, 10);
        const fill = ring.querySelector('.score-ring-fill');
        const label = ring.querySelector('.score-ring-label');
        if (!fill) return;

        const circumference = 283;  // 2 * π * r (r=45 for viewBox 0 0 100 100)
        const target = circumference - (score / 100) * circumference;

        // Color by score
        let color = '#dc2626'; // red
        if (score >= 75) color = '#16a34a';       // green
        else if (score >= 50) color = '#d97706';  // amber

        fill.style.stroke = color;
        fill.style.strokeDasharray = circumference;
        fill.style.strokeDashoffset = circumference; // Start hidden

        // Animate: delay slightly so page settles first
        setTimeout(() => {
            fill.style.transition = 'stroke-dashoffset 1.4s cubic-bezier(0.16,1,0.3,1)';
            fill.style.strokeDashoffset = target;
        }, 200);

        // Count up the number inside the ring
        const numEl = ring.querySelector('.score-ring-num');
        if (numEl) {
            numEl.textContent = '0';
            setTimeout(() => {
                const start = performance.now();
                const dur = 1400;
                const ease = t => 1 - Math.pow(1 - t, 3);
                function tick(now) {
                    const p = Math.min((now - start) / dur, 1);
                    numEl.textContent = Math.round(ease(p) * score);
                    if (p < 1) requestAnimationFrame(tick);
                }
                requestAnimationFrame(tick);
            }, 200);
        }
    }

    function initScoreRings() {
        const rings = document.querySelectorAll('.score-ring[data-score]');
        if (!rings.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.animated) {
                    entry.target.dataset.animated = 'true';
                    animateRing(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });

        rings.forEach(r => observer.observe(r));
    }

    /* ──────────────────────────────────────────
       4. PILL STAGGER REVEAL
       .pill-group elements: pills animate in
       one by one when group enters viewport.
    ────────────────────────────────────────── */
    function initPillGroups() {
        const groups = document.querySelectorAll('.pill-group.animate-pills');
        if (!groups.length) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.animated) {
                    entry.target.dataset.animated = 'true';
                    const pills = entry.target.querySelectorAll('.pill');
                    pills.forEach((pill, i) => {
                        pill.style.opacity = '0';
                        pill.style.transform = 'scale(0.7) translateY(6px)';
                        setTimeout(() => {
                            pill.style.transition = 'opacity 0.35s cubic-bezier(0.34,1.56,0.64,1), transform 0.35s cubic-bezier(0.34,1.56,0.64,1)';
                            pill.style.opacity = '1';
                            pill.style.transform = 'none';
                        }, i * 40);
                    });
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });

        groups.forEach(g => observer.observe(g));
    }

    /* ──────────────────────────────────────────
       5. PROGRESS BAR ANIMATED FILL
       Usage: <div class="plan-bar"><div class="plan-bar-fill" data-width="66"></div></div>
    ────────────────────────────────────────── */
    function initProgressBars() {
        const bars = document.querySelectorAll('.plan-bar-fill[data-width]');
        bars.forEach(bar => {
            const target = bar.dataset.width + '%';
            bar.style.width = '0%';
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            bar.style.transition = 'width 0.9s cubic-bezier(0.16,1,0.3,1)';
                            bar.style.width = target;
                        }, 100);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.5 });
            observer.observe(bar);
        });
    }

    /* ──────────────────────────────────────────
       5b. REVEAL GROUPS
       .reveal-group gains .visible when in view,
       children stagger via CSS transition-delay.
    ────────────────────────────────────────── */
    function initRevealGroups() {
        const groups = document.querySelectorAll('.reveal-group');
        if (!groups.length) return;
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });
        groups.forEach(g => observer.observe(g));
    }

    /* ──────────────────────────────────────────
       6. FORM SHAKE ON ERROR
       Call window.shakeElement(el) from auth/form handlers.
    ────────────────────────────────────────── */
    window.shakeElement = function (el) {
        if (!el) return;
        el.classList.remove('anim-shake');
        void el.offsetWidth; // Reflow to restart animation
        el.classList.add('anim-shake');
        el.addEventListener('animationend', () => el.classList.remove('anim-shake'), { once: true });
    };

    /* ──────────────────────────────────────────
       6b. GLOBAL SHOWTOAST ALIAS  (A14)
       Some pages call showToast() directly.
       Map it to the existing toast() function
       from components.css / config.js.
    ────────────────────────────────────────── */
    window.showToast = function (message, type = 'info') {
        if (typeof window.toast === 'function') {
            window.toast(message, type);
        } else {
            // Inline fallback if toast() not loaded yet
            const container = document.getElementById('toast-container') ||
                (() => {
                    const el = document.createElement('div');
                    el.id = 'toast-container';
                    el.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
                    document.body.appendChild(el);
                    return el;
                })();
            const t = document.createElement('div');
            t.className = `toast toast-${type}`;
            t.textContent = message;
            container.appendChild(t);
            setTimeout(() => t.remove(), 4000);
        }
    };

    /* ──────────────────────────────────────────
       7. TYPING EFFECT
       For hero subtitle cycling text.
       Usage: <span class="typer" data-words='["resumes","candidates","offers"]'></span>
    ────────────────────────────────────────── */
    function initTypers() {
        const typers = document.querySelectorAll('.typer');
        typers.forEach(el => {
            const words = JSON.parse(el.dataset.words || '[]');
            if (!words.length) return;
            let wordIndex = 0, charIndex = 0, deleting = false;
            el.style.borderRight = '2px solid currentColor';
            el.style.animation = 'blink 0.8s step-end infinite';

            function tick() {
                const word = words[wordIndex];
                if (!deleting) {
                    el.textContent = word.slice(0, ++charIndex);
                    if (charIndex === word.length) {
                        deleting = true;
                        setTimeout(tick, 1800);
                        return;
                    }
                } else {
                    el.textContent = word.slice(0, --charIndex);
                    if (charIndex === 0) {
                        deleting = false;
                        wordIndex = (wordIndex + 1) % words.length;
                    }
                }
                setTimeout(tick, deleting ? 50 : 90);
            }
            tick();
        });
    }

    /* ──────────────────────────────────────────
       8. BUTTON RIPPLE EFFECT
       Adds a ripple on click for .btn elements.
    ────────────────────────────────────────── */
    function initButtonRipples() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn');
            if (!btn || btn.classList.contains('btn-ghost') || btn.classList.contains('btn-danger')) return;
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

            const rect = btn.getBoundingClientRect();
            const ripple = document.createElement('span');
            const size = Math.max(rect.width, rect.height) * 2;
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.cssText = `
        position: absolute;
        width: ${size}px; height: ${size}px;
        left: ${x}px; top: ${y}px;
        background: rgba(255,255,255,0.25);
        border-radius: 50%;
        transform: scale(0);
        animation: rippleAnim 0.5s ease-out forwards;
        pointer-events: none;
      `;
            btn.style.overflow = 'hidden';
            btn.style.position = btn.style.position || 'relative';
            btn.appendChild(ripple);
            ripple.addEventListener('animationend', () => ripple.remove());
        });
    }

    /* ──────────────────────────────────────────
       9. NAV SCROLL SHRINK
       Adds .scrolled to .nav on scroll > 20px.
    ────────────────────────────────────────── */
    function initNavScroll() {
        const nav = document.querySelector('.nav');
        if (!nav) return;
        const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 20);
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll(); // Check initial
    }

    /* ── Init All ── */
    function init() {
        initScrollReveal();
        initCounters();
        initScoreRings();
        initPillGroups();
        initProgressBars();
        initRevealGroups();
        initTypers();
        initButtonRipples();
        initNavScroll();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for manual trigger (e.g. after dynamic content loads)
    window.AutoCVAnim = {
        animateRing,
        animateCounter,
        shakeElement: window.shakeElement,
        showToast: window.showToast,
        revealGroup: (el) => el && el.classList.add('visible'),
    };
})();
