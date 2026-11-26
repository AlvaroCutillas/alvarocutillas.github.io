/* Capa de interacción compartida de las páginas de proyecto (versión sobria de la portada).
   Progreso de lectura, sección activa en el índice, aparición suave de figuras y recuento
   de las cifras del resumen. Sin dependencias; respeta el movimiento reducido. */
(() => {
  'use strict';
  const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const root = document.documentElement;

  // 1. Barra de progreso de lectura
  const bar = document.createElement('div');
  bar.className = 'reading-progress';
  bar.setAttribute('aria-hidden', 'true');
  document.body.appendChild(bar);
  let ticking = false;
  const onScroll = () => {
    ticking = false;
    const max = root.scrollHeight - innerHeight;
    bar.style.transform = `scaleX(${max > 0 ? Math.min(1, scrollY / max) : 0})`;
  };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  addEventListener('resize', onScroll);
  onScroll();

  if (!('IntersectionObserver' in window)) return;

  // 2. Índice: resalta la sección que se está leyendo
  const sections = new Map();
  document.querySelectorAll('.toc a[href^="#"]').forEach(a => {
    let id = '';
    try { id = decodeURIComponent(a.getAttribute('href').slice(1)); } catch (_) { return; }
    const el = id && document.getElementById(id);
    if (!el) return;
    if (!sections.has(el)) sections.set(el, []);
    sections.get(el).push(a);
  });
  if (sections.size) {
    let current = [];
    const spy = new IntersectionObserver(entries => entries.forEach(e => {
      if (!e.isIntersecting) return;
      current.forEach(a => a.classList.remove('is-active'));
      current = sections.get(e.target) || [];
      current.forEach(a => a.classList.add('is-active'));
    }), { rootMargin: '-20% 0px -70% 0px' });
    sections.forEach((_, el) => spy.observe(el));
  }

  // 3. Aparición suave: solo lo que aún está por debajo de la pantalla (nada parpadea al cargar)
  if (!RM) {
    const els = [...document.querySelectorAll('main .figure-card, main .panel, main .callout, main .table-wrap')]
      .filter(el => !el.closest('.hero') && !el.parentElement.closest('.figure-card, .panel, .callout')
        && el.getBoundingClientRect().top > innerHeight);
    els.forEach(el => el.classList.add('fx'));
    const show = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); show.unobserve(e.target); }
    }), { rootMargin: '0px 0px -6% 0px' });
    els.forEach(el => show.observe(el));
    addEventListener('beforeprint', () => els.forEach(el => el.classList.add('in')));
  }

  // 4. Cifras del resumen: recuento breve que termina en el texto original exacto
  if (!RM) {
    // Los valores con id los escribe el propio laboratorio de la página: no se tocan
    document.querySelectorAll('.hero-stats .stat strong:not([id])').forEach(el => {
      const text = el.textContent.trim();
      const m = text.match(/^(-?)(\d{1,3}(?:,\d{3})+|\d*\.?\d+)$/);
      if (!m) return;
      const raw = m[2], target = parseFloat(raw.replace(/,/g, '')), dec = (raw.split('.')[1] || '').length, grouped = raw.includes(',');
      const fmt = v => {
        let s = v.toFixed(dec);
        if (grouped) s = s.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        return m[1] + s;
      };
      const t0 = performance.now(), dur = 1300;
      const step = now => {
        const k = Math.min(1, (now - t0) / dur);
        el.textContent = k >= 1 ? text : fmt(target * (1 - Math.pow(2, -10 * k)));
        if (k < 1) requestAnimationFrame(step);
      };
      el.textContent = fmt(0);
      requestAnimationFrame(step);
    });
  }
})();
