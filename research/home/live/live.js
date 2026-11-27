/* =====================================================================
   Portada interactiva — motores de gráficos, laboratorios y transiciones.
   Sin dependencias externas. Todo lo que se dibuja procede de datos reales
   (research/portfolio-optimization/results) o de fórmulas exactas con
   parámetros ilustrativos declarados en pantalla.
   ===================================================================== */
(() => {
  'use strict';

  /* ---------- Utilidades ---------- */
  const DATA = JSON.parse(document.getElementById('home-data').textContent);
  const root = document.documentElement;
  const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const FINE = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const easeOut = x => 1 - Math.pow(1 - clamp(x, 0, 1), 3);
  const easeOutExpo = x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
  const I18N = () => window.PortfolioI18n;
  const t = s => (I18N() ? I18N().t(s) : s);
  const lang = () => (I18N() ? I18N().language : 'en');
  const locale = () => (lang() === 'es' ? 'es-ES' : 'en-US');
  const num = (x, d = 2) => x.toLocaleString(locale(), { minimumFractionDigits: d, maximumFractionDigits: d });
  const pct = (x, d = 1) => num(x * 100, d) + '%';
  const C = {
    bg: '#07080a', bg2: '#0d0f12', ink: '#eceef1', muted: '#a4abb6', soft: '#6d7580',
    rule: '#1f2228', rule2: '#30343c', accent: '#9fb3c8', hi: '#cddbea', warm: '#e3b26b', pos: '#7fc8a9', neg: '#e07a6f'
  };
  const MONO = '"JetBrains Mono", ui-monospace, Consolas, monospace';
  const hex2rgb = h => { const n = parseInt(h.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; };
  const rgba = (h, a) => { const [r, g, b] = hex2rgb(h); return `rgba(${r},${g},${b},${a})`; };
  const mix = (h1, h2, k, a = 1) => {
    const p = hex2rgb(h1), q = hex2rgb(h2);
    return `rgba(${Math.round(lerp(p[0], q[0], k))},${Math.round(lerp(p[1], q[1], k))},${Math.round(lerp(p[2], q[2], k))},${a})`;
  };
  const onLang = [];
  window.addEventListener('portfolio:languagechange', () => onLang.forEach(fn => fn()));

  // Generador pseudoaleatorio con semilla (mulberry32) y normal estándar (Box–Muller)
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let q = Math.imul(a ^ (a >>> 15), 1 | a);
      q = (q + Math.imul(q ^ (q >>> 7), 61 | q)) ^ q;
      return ((q ^ (q >>> 14)) >>> 0) / 4294967296;
    };
  }
  function gauss(rng) {
    let u = 0;
    while (u === 0) u = rng();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rng());
  }

  // Lienzo con densidad de píxeles correcta y redimensionado automático
  function surface(cv, onResize, maxDpr = 2) {
    const ctx = cv.getContext('2d');
    const s = { cv, ctx, w: 0, h: 0, dpr: 1 };
    s.fit = () => {
      const r = cv.getBoundingClientRect();
      const dpr = Math.min(maxDpr, window.devicePixelRatio || 1);
      const W = Math.max(1, Math.round(r.width * dpr)), H = Math.max(1, Math.round(r.height * dpr));
      if (W === cv.width && H === cv.height && s.w) return;
      cv.width = W; cv.height = H; s.w = r.width; s.h = r.height; s.dpr = dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (onResize) onResize(s);
    };
    s.clear = () => { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height); ctx.setTransform(s.dpr, 0, 0, s.dpr, 0, 0); };
    new ResizeObserver(() => s.fit()).observe(cv);
    return s;
  }

  // Bucle único de animación: cada tarea solo corre mientras su elemento es visible
  const jobs = [];
  function job(el, fn, margin = '120px') {
    const j = { fn, on: false };
    new IntersectionObserver(([e]) => { j.on = e.isIntersecting; }, { rootMargin: margin }).observe(el);
    jobs.push(j);
    return j;
  }
  let lastT = performance.now();
  function frame(now) {
    const dt = Math.min(0.05, (now - lastT) / 1000);
    lastT = now;
    if (!document.hidden) for (const j of jobs) if (j.on) j.fn(dt, now);
    requestAnimationFrame(frame);
  }

  // Marcas de eje «redondas»
  function niceTicks(lo, hi, n = 5) {
    const span = hi - lo || 1, raw = span / n, mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw) || 10 * mag;
    const out = [];
    for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-6; v += step) out.push(+v.toFixed(10));
    return { ticks: out, dec: Math.max(0, -Math.floor(Math.log10(step) + 1e-9)) };
  }

  // Rejilla y rótulos de un gráfico 2D
  function grid(ctx, box, X, Y, xt, yt, fx, fy) {
    ctx.save();
    ctx.font = `400 10.5px ${MONO}`;
    ctx.fillStyle = C.soft;
    ctx.strokeStyle = 'rgba(255,255,255,0.055)';
    ctx.lineWidth = 1;
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    for (const v of xt) {
      const x = Math.round(X(v)) + 0.5;
      ctx.beginPath(); ctx.moveTo(x, box.t); ctx.lineTo(x, box.b); ctx.stroke();
      if (fx) ctx.fillText(fx(v), x, box.b + 8);
    }
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    for (const v of yt) {
      const y = Math.round(Y(v)) + 0.5;
      ctx.beginPath(); ctx.moveTo(box.l, y); ctx.lineTo(box.r, y); ctx.stroke();
      if (fy) ctx.fillText(fy(v), box.l - 8, y);
    }
    ctx.strokeStyle = 'rgba(236,238,241,0.35)';
    ctx.beginPath(); ctx.moveTo(box.l, Math.round(box.b) + 0.5); ctx.lineTo(box.r, Math.round(box.b) + 0.5); ctx.stroke();
    ctx.restore();
  }
  function label(ctx, text, x, y, color = C.muted, align = 'left', size = 11, weight = 400) {
    ctx.save();
    ctx.font = `${weight} ${size}px ${MONO}`;
    ctx.fillStyle = color; ctx.textAlign = align; ctx.textBaseline = 'middle';
    ctx.fillText(text, x, y);
    ctx.restore();
  }
  function tipShow(tip, stage, x, y, html) {
    tip.innerHTML = html;
    const w = stage.clientWidth;
    tip.style.left = clamp(x, 100, w - 100) + 'px';
    tip.style.top = y + 'px';
    tip.style.transform = y < 120 ? 'translate(-50%, 18px)' : 'translate(-50%, calc(-100% - 16px))';
    tip.classList.add('on');
  }
  const tipHide = tip => tip.classList.remove('on');
  const tipRows = (title, rows) => `<b>${title}</b>` + rows.map(([k, v]) => `${k} <em>${v}</em>`).join('<br>');
  const fmtDate = (d, withDay) => new Date(d + 'T00:00:00').toLocaleDateString(locale(), withDay ? { year: 'numeric', month: 'short', day: 'numeric' } : { year: 'numeric', month: 'short' });

  /* ---------- Black–Scholes exacto ---------- */
  function erf(x) { // Abramowitz–Stegun 7.1.26 (error < 1.5e-7)
    const s = Math.sign(x); x = Math.abs(x);
    const k = 1 / (1 + 0.3275911 * x);
    return s * (1 - ((((1.061405429 * k - 1.453152027) * k + 1.421413741) * k - 0.284496736) * k + 0.254829592) * k * Math.exp(-x * x));
  }
  const Ncdf = x => 0.5 * (1 + erf(x / Math.SQRT2));
  const npdf = x => Math.exp(-x * x / 2) / Math.sqrt(2 * Math.PI);
  function bs(S, K, T, r, sig, type) {
    const sq = Math.sqrt(T), d1 = (Math.log(S / K) + (r + sig * sig / 2) * T) / (sig * sq), d2 = d1 - sig * sq, df = Math.exp(-r * T);
    const gamma = npdf(d1) / (S * sig * sq), vega = S * npdf(d1) * sq / 100;
    if (type === 'call') {
      return { price: S * Ncdf(d1) - K * df * Ncdf(d2), delta: Ncdf(d1), gamma, vega,
        theta: (-S * npdf(d1) * sig / (2 * sq) - r * K * df * Ncdf(d2)) / 365, rho: K * T * df * Ncdf(d2) / 100 };
    }
    return { price: K * df * Ncdf(-d2) - S * Ncdf(-d1), delta: Ncdf(d1) - 1, gamma, vega,
      theta: (-S * npdf(d1) * sig / (2 * sq) + r * K * df * Ncdf(-d2)) / 365, rho: -K * T * df * Ncdf(-d2) / 100 };
  }

  /* =====================================================================
     1. Arranque, nombre y revelado
     ===================================================================== */
  function splitName() {
    let i = 0;
    $$('.hn-line').forEach(line => {
      const txt = line.textContent;
      line.textContent = '';
      for (const ch of txt) {
        const s = document.createElement('span');
        s.className = 'hn-char'; s.setAttribute('aria-hidden', 'true');
        s.style.setProperty('--i', i++);
        s.textContent = ch;
        line.appendChild(s);
      }
    });
  }

  function reveals() {
    // Escalonado entre hermanos
    const groups = new Map();
    $$('.reveal').forEach(el => {
      const p = el.parentElement;
      const i = groups.get(p) || 0;
      groups.set(p, i + 1);
      if (!el.style.getPropertyValue('--d')) el.style.setProperty('--d', Math.min(i, 8) * 0.07 + 's');
    });
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    $$('.reveal, .reveal-group').forEach(el => io.observe(el));
    const pipe = $('.pipeline');
    if (pipe) new IntersectionObserver(([e], o) => { if (e.isIntersecting) { pipe.style.setProperty('--line', 1); o.disconnect(); } }, { threshold: 0.3 }).observe(pipe);
  }

  /* ---------- Cifras con recuento animado ---------- */
  function counters() {
    const els = $$('[data-count]');
    els.forEach(el => el.setAttribute('translate', 'no'));
    const show = (el, v) => { el.textContent = num(v, +el.dataset.dec); };
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      const el = e.target, target = +el.dataset.count;
      if (RM) { show(el, target); return; }
      const t0 = performance.now(), dur = 1800;
      const step = now => {
        const k = easeOutExpo((now - t0) / dur);
        show(el, target * k);
        if (k < 1) requestAnimationFrame(step); else el.dataset.done = '1';
      };
      requestAnimationFrame(step);
    }), { threshold: 0.4 });
    els.forEach(el => { el.textContent = num(0, +el.dataset.dec); io.observe(el); });
    onLang.push(() => els.forEach(el => { if (el.dataset.done || RM) show(el, +el.dataset.count); }));
  }

  /* =====================================================================
     2. Navegación, progreso, cursor, botones magnéticos y transición
     ===================================================================== */
  function chrome() {
    const nav = $('nav'), bar = $('.progress'), about = $('.about-text');
    let lastY = scrollY, ticking = false;
    const onScroll = () => {
      ticking = false;
      const y = scrollY, max = document.documentElement.scrollHeight - innerHeight;
      nav.classList.toggle('scrolled', y > 24);
      nav.classList.toggle('hide', y > lastY + 2 && y > innerHeight * 0.9 && !$('.cmdk').open);
      if (y < lastY - 2) nav.classList.remove('hide');
      lastY = y;
      bar.style.setProperty('--p', max > 0 ? y / max : 0);
      if (about && !RM) {
        const r = about.getBoundingClientRect();
        const p = clamp((innerHeight * 0.82 - r.top) / (r.height + innerHeight * 0.3), 0, 1);
        const v = (p * 108).toFixed(1) + '%';
        if (v !== about.dataset.p) { about.dataset.p = v; about.style.setProperty('--p', v); }
      }
    };
    addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
    onScroll();

    // Indicador de sección activa
    const links = $$('.nav-links a'), ind = $('.nav-indicator');
    let current = null;
    const place = () => {
      const a = links.find(l => l.getAttribute('href') === '#' + current);
      links.forEach(l => l.classList.toggle('active', l === a));
      if (!a) { ind.style.opacity = 0; return; }
      ind.style.opacity = 1;
      ind.style.width = a.offsetWidth + 'px';
      ind.style.transform = `translateX(${a.offsetLeft}px)`;
    };
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (e.isIntersecting) { current = e.target.id === 'top' ? null : e.target.id; place(); }
    }), { rootMargin: '-45% 0px -50% 0px' });
    ['top', 'projects', 'quant-basics', 'about', 'contact'].forEach(id => { const s = document.getElementById(id); if (s) io.observe(s); });
    onLang.push(() => requestAnimationFrame(place));
    addEventListener('resize', place);

    // Atajo de teclado según plataforma
    if (!/Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent)) $$('kbd').forEach(k => { if (k.textContent === '⌘K') k.textContent = 'Ctrl K'; });

    // Relleno de los deslizadores
    const fill = i => i.style.setProperty('--f', ((i.value - i.min) / (i.max - i.min) * 100) + '%');
    $$('input[type=range]').forEach(i => { fill(i); i.addEventListener('input', () => fill(i)); });

    // Botones magnéticos y foco de luz en los paneles
    if (FINE && !RM) {
      $$('.magnetic').forEach(b => {
        b.style.transition = 'transform .45s cubic-bezier(.16,1,.3,1), border-color .3s, color .3s';
        b.addEventListener('pointermove', e => {
          const r = b.getBoundingClientRect();
          b.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * 0.22}px, ${(e.clientY - r.top - r.height / 2) * 0.35}px)`;
        });
        b.addEventListener('pointerleave', () => { b.style.transform = ''; });
      });
      $$('.lab, .feature > .project-card').forEach(l => l.addEventListener('pointermove', e => {
        const r = l.getBoundingClientRect();
        l.style.setProperty('--mx', e.clientX - r.left + 'px');
        l.style.setProperty('--my', e.clientY - r.top + 'px');
      }));
    }
  }

  // Navegación entre páginas: la transición la hace el navegador (View Transitions, ver live.css)
  function navigate(href) { location.href = href; }

  /* =====================================================================
     3. Cabecera: Monte Carlo en vivo (GBM) con convergencia a la lognormal
     ===================================================================== */
  function hero() {
    const cv = $('.hero-canvas');
    if (!cv) return;
    const S0 = 100, T = 1, N = 90, dt = T / N, BINS = 56;
    let sigma = 0.2, mu = 0.05;
    const trail = $('.hero-trail'), tctx = trail.getContext('2d');
    let hist = new Float64Array(BINS), n = 0, sumS = 0, sumS2 = 0, conv = [], active = [], ripples = [];
    let rng = mulberry32(20240607), lo = 0, hi = 1, spawnAcc = 0, hudAcc = 0, fadeAcc = 0;
    const L = {};
    const heroEl = cv.parentElement, stage = $('.hud-stage'), narrowMQ = matchMedia('(max-width: 760px)');
    const mount = () => {
      if (narrowMQ.matches && stage) { stage.append(trail, cv); }
      else if (cv.parentElement !== heroEl) { heroEl.insertBefore(cv, heroEl.firstChild); heroEl.insertBefore(trail, cv); }
    };
    mount();
    narrowMQ.addEventListener('change', mount);
    const S = surface(cv, s => {
      trail.width = cv.width; trail.height = cv.height;
      tctx.setTransform(s.dpr, 0, 0, s.dpr, 0, 0);
      layout();
      if (RM) staticRun();
    }, 1.25);
    const out = k => $(`[data-hud="${k}"]`);
    const hudEls = { n: out('n'), mean: out('mean'), exact: out('exact'), ci: out('ci') };
    const spark = surface($('.hud-spark'), () => drawSpark());

    function layout() {
      const w = S.w, h = S.h, narrow = w < 760;
      const hud = $('.hud'), hr = hud ? hud.getBoundingClientRect() : null, cr = cv.getBoundingClientRect();
      // Con el panel a la derecha, el histograma termina justo antes del panel
      const side = hr && hr.left - cr.left > w * 0.55 && hr.width < w * 0.4;
      L.narrow = narrow;
      L.x0 = narrow ? -10 : w * 0.015;
      if (cv.parentElement === stage) {
        // Gráfico propio dentro del panel (móvil): trayectorias a la izquierda, histograma a la derecha
        L.narrow = true;
        L.x0 = 6; L.x1 = w * 0.68; L.hx = L.x1 + 8; L.hw = Math.max(40, w - L.hx - 36);
        L.labelX = w - 6; L.top = 14; L.bot = h - 16;
        setRange();
        return;
      }
      if (side) {
        const end = hr.left - cr.left - 64;
        L.hw = clamp(w * 0.11, 110, 170);
        L.hx = end - L.hw;
        L.x1 = L.hx - 16;
      } else {
        L.x1 = narrow ? w * 0.78 : w * 0.8;
        L.hx = L.x1 + (narrow ? 6 : 16);
        L.hw = Math.max(36, w - L.hx - (narrow ? 34 : 70));
      }
      L.labelX = L.hx + L.hw + (narrow ? 30 : 46);
      L.top = narrow ? h * 0.08 : h * 0.13;
      L.bot = narrow ? h * 0.62 : h * 0.9;
      setRange();
    }
    function setRange() {
      const m = Math.log(S0) + (mu - sigma * sigma / 2) * T, s = sigma * Math.sqrt(T);
      lo = Math.min(m - 3.4 * s, Math.log(S0) - 0.12);
      hi = Math.max(m + 3.4 * s, Math.log(S0) + 0.12);
    }
    const X = k => L.x0 + (k / N) * (L.x1 - L.x0);
    const Y = v => L.bot - ((v - lo) / (hi - lo)) * (L.bot - L.top);

    function spawn() {
      const pts = new Float32Array(N + 1);
      let v = Math.log(S0);
      pts[0] = v;
      const a = (mu - sigma * sigma / 2) * dt, b = sigma * Math.sqrt(dt);
      for (let i = 1; i <= N; i++) { v += a + b * gauss(rng); pts[i] = v; }
      active.push({ pts, k: 0, speed: 0.7 + rng() * 0.9 });
    }
    function record(v) {
      const s = Math.exp(v);
      n++; sumS += s; sumS2 += s * s;
      const b = Math.floor(((v - lo) / (hi - lo)) * BINS);
      if (b >= 0 && b < BINS) hist[b]++;
    }
    function reset() {
      hist = new Float64Array(BINS); n = 0; sumS = 0; sumS2 = 0; conv = []; active = []; spawnAcc = 0;
      tctx.setTransform(1, 0, 0, 1, 0, 0); tctx.clearRect(0, 0, trail.width, trail.height); tctx.setTransform(S.dpr, 0, 0, S.dpr, 0, 0);
      setRange();
    }
    function strokePath(p, from, to, style, width) {
      tctx.beginPath();
      tctx.moveTo(X(from), Y(p.pts[from]));
      for (let i = from + 1; i <= to; i++) tctx.lineTo(X(i), Y(p.pts[i]));
      tctx.strokeStyle = style; tctx.lineWidth = width; tctx.stroke();
    }
    function staticRun() { // Movimiento reducido: una muestra completa, sin animación
      if (!S.w) return;
      reset();
      rng = mulberry32(20240607);
      for (let i = 0; i < 320; i++) { spawn(); const p = active.pop(); strokePath(p, 0, N, rgba(C.accent, 0.09), 1); record(p.pts[N]); }
      pushConv(); updateHud(); draw();
    }
    function pushConv() {
      if (!n) return;
      const mean = sumS / n, sd = Math.sqrt(Math.max(0, sumS2 / n - mean * mean));
      conv.push({ mean, ci: 1.96 * sd / Math.sqrt(n) });
      if (conv.length > 160) conv.shift();
    }
    function updateHud() {
      const exact = S0 * Math.exp(mu * T);
      hudEls.n.textContent = num(n, 0);
      hudEls.exact.textContent = num(exact, 2);
      if (n > 1) {
        const mean = sumS / n, sd = Math.sqrt(Math.max(0, sumS2 / n - mean * mean));
        hudEls.mean.textContent = num(mean, 2);
        hudEls.ci.textContent = num(1.96 * sd / Math.sqrt(n), 2);
      } else { hudEls.mean.textContent = '—'; hudEls.ci.textContent = '—'; }
      drawSpark();
    }
    function drawSpark() { // Estimación frente al valor exacto, con banda de confianza del 95 %
      if (!spark.w) return;
      const c = spark.ctx, w = spark.w, h = spark.h, exact = S0 * Math.exp(mu * T);
      spark.clear();
      if (conv.length < 2) return;
      const span = Math.max(...conv.map(q => Math.abs(q.mean - exact) + q.ci)) * 1.1 || 1;
      const x = i => (i / (conv.length - 1)) * w, y = v => h / 2 - ((v - exact) / span) * (h / 2 - 2);
      c.beginPath();
      conv.forEach((q, i) => (i ? c.lineTo(x(i), y(q.mean + q.ci)) : c.moveTo(x(i), y(q.mean + q.ci))));
      for (let i = conv.length - 1; i >= 0; i--) c.lineTo(x(i), y(conv[i].mean - conv[i].ci));
      c.fillStyle = rgba(C.warm, 0.14); c.fill();
      c.strokeStyle = rgba(C.accent, 0.5); c.setLineDash([2, 3]); c.beginPath(); c.moveTo(0, h / 2); c.lineTo(w, h / 2); c.stroke(); c.setLineDash([]);
      c.beginPath();
      conv.forEach((q, i) => (i ? c.lineTo(x(i), y(q.mean)) : c.moveTo(x(i), y(q.mean))));
      c.strokeStyle = C.ink; c.lineWidth = 1.3; c.stroke();
    }

    function draw() {
      if (!S.w) return;
      const c = S.ctx;
      S.clear();
      const lnS0 = Math.log(S0), m = Math.log(S0) + (mu - sigma * sigma / 2) * T, sd = sigma * Math.sqrt(T);
      // Guías: S0 y E[S_T]
      c.save();
      c.setLineDash([3, 5]); c.lineWidth = 1;
      c.strokeStyle = 'rgba(236,238,241,0.18)';
      c.beginPath(); c.moveTo(L.x0, Y(lnS0)); c.lineTo(L.hx + L.hw, Y(lnS0)); c.stroke();
      const lnE = Math.log(S0 * Math.exp(mu * T));
      c.strokeStyle = rgba(C.warm, 0.4);
      c.beginPath(); c.moveTo(L.x1 - 60, Y(lnE)); c.lineTo(L.hx + L.hw, Y(lnE)); c.stroke();
      c.restore();
      // Cabezas de las trayectorias activas
      for (const p of active) {
        const k = Math.min(N, p.k), i = Math.floor(k), fr = k - i;
        const v = i < N ? lerp(p.pts[i], p.pts[i + 1], fr) : p.pts[N];
        const from = Math.max(0, i - 7);
        c.beginPath(); c.moveTo(X(from), Y(p.pts[from]));
        for (let j = from + 1; j <= i; j++) c.lineTo(X(j), Y(p.pts[j]));
        c.lineTo(X(k), Y(v));
        c.strokeStyle = rgba(C.hi, 0.55); c.lineWidth = 1.2; c.stroke();
        c.beginPath(); c.arc(X(k), Y(v), 1.6, 0, Math.PI * 2); c.fillStyle = C.hi; c.fill();
      }
      // Histograma de S_T frente a la densidad lognormal exacta (en escala logarítmica)
      const peak = 1 / (sd * Math.sqrt(2 * Math.PI)), scale = (L.hw * 0.9) / peak, bw = (hi - lo) / BINS;
      c.fillStyle = rgba(C.accent, 0.3);
      for (let b = 0; b < BINS; b++) {
        if (!hist[b]) continue;
        const len = Math.min(L.hw * 1.05, (hist[b] / (n * bw)) * scale);
        const y0 = Y(lo + b * bw), y1 = Y(lo + (b + 1) * bw);
        c.fillRect(L.hx, y1 + 0.5, len, Math.max(0.5, y0 - y1 - 1));
      }
      c.beginPath();
      for (let j = 0; j <= 140; j++) {
        const v = lo + ((hi - lo) * j) / 140, x = L.hx + Math.exp(-((v - m) ** 2) / (2 * sd * sd)) * peak * scale;
        j ? c.lineTo(x, Y(v)) : c.moveTo(x, Y(v));
      }
      c.strokeStyle = C.warm; c.lineWidth = 1.6; c.stroke();
      c.strokeStyle = 'rgba(236,238,241,0.25)'; c.lineWidth = 1;
      c.beginPath(); c.moveTo(L.hx + 0.5, L.top); c.lineTo(L.hx + 0.5, L.bot); c.stroke();
      // Rótulos de precio
      for (const P of [25, 40, 60, 80, 100, 125, 160, 200, 260, 340]) {
        const v = Math.log(P);
        if (v > lo + 0.02 && v < hi - 0.02) label(c, String(P), L.labelX, Y(v), P === 100 ? C.muted : C.soft, 'right', 10);
      }
      if (!L.narrow) {
        label(c, t('Lognormal density'), L.hx + 4, L.top - 14, C.warm, 'left', 10.5);
        label(c, 't = 0', L.x0 + 6, L.bot + 16, C.soft, 'left', 10);
        label(c, 'T = 1', L.x1, L.bot + 16, C.soft, 'right', 10);
        label(c, 'E[Sₜ]', L.x1 - 64, Y(lnE) - 9, C.warm, 'left', 10);
      }
      // Ondas de clic
      for (const r of ripples) {
        c.beginPath(); c.arc(r.x, r.y, r.r, 0, Math.PI * 2);
        c.strokeStyle = rgba(C.hi, r.a * 0.6); c.lineWidth = 1; c.stroke();
      }
    }

    function step(dt) {
      if (!S.w) return;
      const target = cv.parentElement === stage ? 14 : L.narrow ? 16 : 34;
      spawnAcc += dt * target / 1.4;
      while (spawnAcc >= 1 && active.length < target * 1.6) { spawn(); spawnAcc -= 1; }
      if (spawnAcc > 3) spawnAcc = 0;
      // Desvanecimiento del rastro
      fadeAcc += dt;
      if (fadeAcc > 0) { // en cada fotograma, proporcional al tiempo transcurrido
        tctx.globalCompositeOperation = 'destination-out';
        tctx.fillStyle = `rgba(0,0,0,${(1 - Math.pow(0.97, fadeAcc * 60)).toFixed(3)})`;
        tctx.fillRect(0, 0, S.w, S.h);
        tctx.globalCompositeOperation = 'source-over';
        fadeAcc = 0;
      }
      const keep = [];
      for (const p of active) {
        const prev = Math.floor(p.k);
        p.k += p.speed * 62 * dt;
        const now = Math.min(N, Math.floor(p.k));
        if (now > prev) strokePath(p, prev, now, rgba(C.accent, 0.3), 1);
        if (p.k >= N) record(p.pts[N]); else keep.push(p);
      }
      active = keep;
      ripples = ripples.filter(r => (r.r += 140 * dt, r.a -= 1.4 * dt, r.a > 0));
      hudAcc += dt;
      if (hudAcc > 0.16) { hudAcc = 0; pushConv(); updateHud(); }
      draw();
    }

    // Controles
    $$('[data-hero]').forEach(inp => inp.addEventListener('input', () => {
      const v = +inp.value / 100;
      if (inp.dataset.hero === 'sigma') sigma = v; else mu = v;
      $(`[data-out="${inp.dataset.hero}"]`).textContent = Math.round(v * 100) + '%';
      reset();
      if (RM) staticRun(); else for (let i = 0; i < 24; i++) spawn();
      updateHud();
    }));
    cv.addEventListener('pointerdown', e => {
      if (RM) return;
      const r = cv.getBoundingClientRect();
      ripples.push({ x: e.clientX - r.left, y: e.clientY - r.top, r: 2, a: 1 });
      for (let i = 0; i < 30; i++) spawn();
    });
    onLang.push(() => { updateHud(); draw(); });

    if (!RM) {
      // Abanico inicial: sesenta trayectorias salen a la vez
      for (let i = 0; i < 60; i++) spawn();
      job(cv, step, '0px');
    }
    updateHud();
  }

  /* =====================================================================
     4. Pestañas compartidas
     ===================================================================== */
  function tabs(lab, onChange) {
    const tabsEl = $('.tabs', lab);
    if (!tabsEl) return;
    const pill = document.createElement('i');
    pill.className = 'tab-pill';
    tabsEl.prepend(pill);
    const btns = $$('button', tabsEl);
    const place = () => {
      const b = btns.find(x => x.getAttribute('aria-selected') === 'true');
      if (!b) return;
      pill.style.width = b.offsetWidth + 'px';
      pill.style.transform = `translateX(${b.offsetLeft}px)`;
    };
    btns.forEach(b => b.addEventListener('click', () => {
      btns.forEach(x => { x.setAttribute('aria-selected', x === b); x.tabIndex = x === b ? 0 : -1; });
      place();
      onChange(b.dataset.view);
    }));
    btns.forEach(x => { x.tabIndex = x.getAttribute('aria-selected') === 'true' ? 0 : -1; });
    tabsEl.addEventListener('keydown', e => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      const i = btns.indexOf(document.activeElement);
      if (i < 0) return;
      const j = (i + (e.key === 'ArrowRight' ? 1 : -1) + btns.length) % btns.length;
      btns[j].focus(); btns[j].click();
    });
    new ResizeObserver(place).observe(tabsEl);
    onLang.push(() => requestAnimationFrame(place));
    place();
  }

  /* =====================================================================
     5. Laboratorio de carteras (datos reales)
     ===================================================================== */
  const TC = { SPY: '#9fb3c8', IWM: '#5f82a8', EFA: '#7fc8a9', EEM: '#3f8f78', AGG: '#e3b26b', TLT: '#b9803f', LQD: '#f0d7a4', VNQ: '#c78fb5', GLD: '#e8d36c', DBC: '#e07a6f' };
  const SC = {
    'Equal weight': '#eceef1', 'GMV · sample': '#7d8794', 'Max Sharpe · sample': '#c78fb5',
    'GMV · Ledoit–Wolf': '#7fc8a9', 'Max Sharpe · sample capped': '#e3b26b', 'Max Sharpe · LW capped': '#6f8fb3'
  };
  const OFF = { SPY: [10, -8, 'left'], IWM: [10, 4, 'left'], EFA: [-10, 4, 'right'], EEM: [10, 4, 'left'], AGG: [10, 14, 'left'],
    TLT: [10, 4, 'left'], LQD: [10, -8, 'left'], VNQ: [-10, -8, 'right'], GLD: [10, 4, 'left'], DBC: [10, 4, 'left'] };

  function portfolioLab() {
    const lab = $('[data-lab="portfolio"]');
    if (!lab) return;
    const cv = $('.lab-canvas', lab), tip = $('.tip', lab), legend = $('[data-legend]', lab), stage = $('.lab-stage', lab);
    tip.setAttribute('translate', 'no'); legend.setAttribute('translate', 'no');
    let view = 'frontier', p = RM ? 1 : 0, dirty = true, hover = null;
    const S = surface(cv, () => { dirty = true; if (RM) draw(); });
    const W = DATA.wealth, visible = new Set(W.order), F = DATA.frontier;
    let tan = 0, gmv = 0;
    F.forEach((q, i) => { if (q[1] / q[0] > F[tan][1] / F[tan][0]) tan = i; if (q[0] < F[gmv][0]) gmv = i; });
    const weights = DATA.weights.map(r => { const w = r.slice(1), s = w.reduce((a, b) => a + b, 0) || 1; return { d: r[0], w: w.map(x => x / s) }; });
    const yearTicks = (dates, every) => {
      const out = [];
      let prev = null;
      dates.forEach((d, i) => { const y = +d.slice(0, 4); if (y !== prev && y % every === 0) out.push([i, y]); prev = y; });
      return out;
    };

    function buildLegend() {
      legend.innerHTML = '';
      if (view === 'wealth') {
        W.order.forEach(s => {
          const b = document.createElement('button');
          b.type = 'button'; b.style.setProperty('--c', SC[s]);
          b.setAttribute('aria-pressed', visible.has(s));
          b.innerHTML = `<i></i>${t(s)}`;
          b.addEventListener('click', () => {
            if (visible.has(s) && visible.size > 1) visible.delete(s); else visible.add(s);
            b.setAttribute('aria-pressed', visible.has(s));
            dirty = true; if (RM) draw();
          });
          legend.appendChild(b);
        });
      } else if (view === 'weights') {
        DATA.tickers.forEach(tk => { const s = document.createElement('span'); s.className = 'key'; s.style.setProperty('--c', TC[tk]); s.innerHTML = `<i></i>${tk}`; legend.appendChild(s); });
      } else if (view === 'corr') {
        [[C.warm, t('Negative')], [C.accent, t('Positive')]].forEach(([c, l]) => { const s = document.createElement('span'); s.className = 'key'; s.style.setProperty('--c', c); s.innerHTML = `<i></i>${l}`; legend.appendChild(s); });
      }
    }
    function setView(v) {
      view = v; p = RM ? 1 : 0; hover = null; tipHide(tip); dirty = true;
      $$('[data-caption]', lab).forEach(el => { el.hidden = el.dataset.caption !== v; });
      buildLegend();
      if (RM) draw();
    }
    tabs(lab, setView);
    buildLegend();

    function boxFor() {
      const narrow = S.w < 560;
      const r = view === 'wealth' && !narrow ? S.w - 168 : S.w - 14;
      return { l: narrow ? 42 : 54, t: 18, r, b: S.h - 30, narrow };
    }

    function draw() {
      if (!S.w) return;
      S.clear();
      const c = S.ctx, box = boxFor();
      box.w = box.r - box.l; box.h = box.b - box.t;
      if (view === 'frontier') drawFrontier(c, box);
      else if (view === 'wealth') drawWealth(c, box);
      else if (view === 'weights') drawWeights(c, box);
      else drawCorr(c, box);
    }

    function drawFrontier(c, box) {
      const xr = [0, 0.25], yr = [-0.06, 0.15];
      const X = v => box.l + ((v - xr[0]) / (xr[1] - xr[0])) * box.w, Y = v => box.t + ((yr[1] - v) / (yr[1] - yr[0])) * box.h;
      grid(c, box, X, Y, [0, 0.05, 0.1, 0.15, 0.2, 0.25], [-0.05, 0, 0.05, 0.1, 0.15], v => pct(v, 0), v => pct(v, 0));
      c.strokeStyle = 'rgba(236,238,241,0.2)'; c.beginPath(); c.moveTo(box.l, Y(0)); c.lineTo(box.r, Y(0)); c.stroke();
      if (!box.narrow) label(c, t('Annualised volatility') + ' →', box.r - 4, box.b - 12, C.soft, 'right', 10.5);
      label(c, '↑ ' + t('Annualised return'), box.l + 8, box.t + 8, C.soft, 'left', 10.5);
      const e = easeOut(p), k = Math.max(2, Math.floor(F.length * e));
      // Rayo de máxima razón μ/σ
      if (p > 0.6) {
        const a = clamp((p - 0.6) / 0.4, 0, 1), q = F[tan], s = (xr[1] * 0.98) / q[0];
        c.save(); c.globalAlpha = a; c.setLineDash([4, 5]); c.strokeStyle = rgba(C.warm, 0.55); c.lineWidth = 1;
        c.beginPath(); c.moveTo(X(0), Y(0)); c.lineTo(X(q[0] * s), Y(q[1] * s)); c.stroke(); c.restore();
      }
      // Frontera con resplandor
      c.save();
      c.beginPath(); F.slice(0, k).forEach((q, i) => (i ? c.lineTo(X(q[0]), Y(q[1])) : c.moveTo(X(q[0]), Y(q[1]))));
      c.lineJoin = 'round'; c.strokeStyle = rgba(C.accent, 0.16); c.lineWidth = 9; c.stroke();
      c.strokeStyle = C.accent; c.lineWidth = 2.6; c.stroke();
      c.restore();
      // Activos
      DATA.assets.forEach((a, i) => {
        const q = easeOut(clamp(p * 1.6 - 0.25 - i * 0.05, 0, 1));
        if (q <= 0) return;
        const x = X(a.vol), y = Y(a.mu), hov = hover && hover.asset === i;
        c.beginPath(); c.arc(x, y, (hov ? 6.5 : 4.2) * q, 0, Math.PI * 2);
        c.fillStyle = hov ? TC[a.t] : C.bg; c.fill();
        c.strokeStyle = TC[a.t]; c.lineWidth = 2; c.stroke();
        const o = OFF[a.t] || [10, 4, 'left'];
        c.globalAlpha = q;
        label(c, a.t, x + o[0], y + o[1] - 3, hov ? C.ink : C.muted, o[2], 11, 500);
        c.globalAlpha = 1;
      });
      if (p > 0.85) {
        const a = clamp((p - 0.85) / 0.15, 0, 1);
        c.globalAlpha = a;
        // Rótulos con línea guía para no tapar los activos cercanos
        [[gmv, t('Min. variance'), 44, 40, 'left'], [tan, t('Max μ/σ'), box.narrow ? -14 : -30, box.narrow ? -52 : -46, box.narrow ? 'left' : 'right']].forEach(([i, txt, dx, dy, al]) => {
          const x = X(F[i][0]), y = Y(F[i][1]);
          c.strokeStyle = rgba(C.warm, 0.5); c.lineWidth = 1;
          c.beginPath(); c.moveTo(x, y); c.lineTo(x + dx, y + dy); c.lineTo(x + dx + (al === 'left' ? 8 : -8), y + dy); c.stroke();
          c.beginPath(); c.arc(x, y, 5.5, 0, Math.PI * 2); c.fillStyle = C.warm; c.fill();
          c.strokeStyle = C.bg; c.lineWidth = 2; c.stroke();
          label(c, txt, x + dx + (al === 'left' ? 12 : -12), y + dy, C.warm, al, 11, 500);
        });
        c.globalAlpha = 1;
      }
      if (hover && hover.front != null) {
        const q = F[hover.front], x = X(q[0]), y = Y(q[1]);
        c.strokeStyle = 'rgba(236,238,241,0.25)'; c.setLineDash([2, 4]);
        c.beginPath(); c.moveTo(x, box.b); c.lineTo(x, y); c.lineTo(box.l, y); c.stroke(); c.setLineDash([]);
        c.beginPath(); c.arc(x, y, 6, 0, Math.PI * 2); c.fillStyle = C.hi; c.fill();
      }
      frontierHit = (mx, my) => {
        let best = null, bd = 18;
        DATA.assets.forEach((a, i) => { const d = Math.hypot(X(a.vol) - mx, Y(a.mu) - my); if (d < bd) { bd = d; best = { asset: i, x: X(a.vol), y: Y(a.mu) }; } });
        if (best) return best;
        bd = 46;
        F.forEach((q, i) => { const d = Math.hypot(X(q[0]) - mx, Y(q[1]) - my); if (d < bd) { bd = d; best = { front: i, x: X(q[0]), y: Y(q[1]) }; } });
        return best;
      };
    }
    let frontierHit = () => null, wealthIdx = () => null, weightIdx = () => null, corrCell = () => null;

    function drawWealth(c, box) {
      const n = W.dates.length, ddH = box.h * 0.2, mainB = box.b - ddH - 22;
      let ymax = 1.2;
      visible.forEach(s => { ymax = Math.max(ymax, ...W.series[s]); });
      const yr = [0.8, ymax * 1.04], X = i => box.l + (i / (n - 1)) * box.w;
      const Y = v => box.t + ((yr[1] - v) / (yr[1] - yr[0])) * (mainB - box.t);
      const mbox = { l: box.l, r: box.r, t: box.t, b: mainB };
      const yt = [1, 1.5, 2, 2.5, 3].filter(v => v <= yr[1]);
      const xt = yearTicks(W.dates, box.narrow ? 4 : 2);
      grid(c, mbox, X, Y, [], yt, null, v => num(v, 1) + '×');
      c.save(); c.font = `400 10.5px ${MONO}`; c.fillStyle = C.soft; c.textAlign = 'center';
      xt.forEach(([i, y]) => c.fillText(String(y), X(i), box.b + 14));
      c.restore();
      const k = Math.max(2, Math.floor(n * easeOut(p)));
      const order = W.order.filter(s => s !== W.headline).concat([W.headline]);
      order.forEach(s => {
        if (!visible.has(s)) return;
        const arr = W.series[s], head = s === W.headline;
        c.save();
        c.beginPath();
        for (let i = 0; i < k; i++) i ? c.lineTo(X(i), Y(arr[i])) : c.moveTo(X(i), Y(arr[i]));
        c.lineJoin = 'round';
        if (head) { c.strokeStyle = rgba(SC[s], 0.16); c.lineWidth = 8; c.stroke(); }
        c.strokeStyle = head ? SC[s] : rgba(SC[s], 0.75); c.lineWidth = head ? 2.4 : 1.25; c.stroke();
        c.restore();
      });
      // Etiquetas finales sin solapes
      if (!box.narrow && p > 0.98) {
        const labs = [...visible].map(s => ({ s, y: Y(W.series[s][n - 1]) })).sort((a, b) => a.y - b.y);
        for (let i = 1; i < labs.length; i++) if (labs[i].y - labs[i - 1].y < 14) labs[i].y = labs[i - 1].y + 14;
        labs.forEach(({ s, y }) => {
          const name = t(s), short = name.length > 20 ? name.slice(0, 19) + '…' : name;
          label(c, `${short} ${num(DATA.metrics[s].tw, 2)}×`, box.r + 8, y, s === W.headline ? SC[s] : C.muted, 'left', 10.5, s === W.headline ? 500 : 400);
        });
      }
      // Panel de caída desde máximos de la regla destacada
      const dd = W.dd[W.headline], ddLo = Math.min(...dd) * 1.1, top = box.b - ddH;
      const YD = v => top + (v / ddLo) * ddH;
      c.strokeStyle = 'rgba(255,255,255,0.06)';
      c.beginPath(); c.moveTo(box.l, top + 0.5); c.lineTo(box.r, top + 0.5); c.stroke();
      c.beginPath(); c.moveTo(X(0), YD(0));
      for (let i = 0; i < k; i++) c.lineTo(X(i), YD(dd[i]));
      c.lineTo(X(k - 1), YD(0)); c.closePath();
      c.fillStyle = rgba(C.neg, 0.28); c.fill();
      c.strokeStyle = rgba(C.neg, 0.8); c.lineWidth = 1; c.stroke();
      label(c, `${t('Drawdown')} · ${t(W.headline)}`, box.l + 6, top + 10, C.soft, 'left', 10);
      label(c, pct(Math.min(...dd), 0), box.l - 8, YD(Math.min(...dd)), C.soft, 'right', 10);
      label(c, '0%', box.l - 8, top, C.soft, 'right', 10);
      if (hover && hover.i != null) {
        const x = X(hover.i);
        c.strokeStyle = 'rgba(236,238,241,0.3)'; c.setLineDash([2, 4]);
        c.beginPath(); c.moveTo(x, box.t); c.lineTo(x, box.b); c.stroke(); c.setLineDash([]);
        visible.forEach(s => { c.beginPath(); c.arc(x, Y(W.series[s][hover.i]), s === W.headline ? 5 : 3.5, 0, Math.PI * 2); c.fillStyle = SC[s]; c.fill(); });
      }
      wealthIdx = mx => (mx < box.l || mx > box.r ? null : Math.round(clamp((mx - box.l) / box.w, 0, 1) * (n - 1)));
    }

    function drawWeights(c, box) {
      const m = weights.length, X = i => box.l + (i / (m - 1)) * box.w, Y = v => box.t + (1 - v) * box.h;
      grid(c, box, X, Y, [], [0, 0.25, 0.5, 0.75, 1], null, v => pct(v, 0));
      const xt = yearTicks(weights.map(r => r.d), box.narrow ? 4 : 2);
      c.save(); c.font = `400 10.5px ${MONO}`; c.fillStyle = C.soft; c.textAlign = 'center';
      xt.forEach(([i, y]) => c.fillText(String(y), X(i), box.b + 14));
      c.restore();
      c.save();
      c.beginPath(); c.rect(box.l, box.t - 2, box.w * easeOut(p), box.h + 4); c.clip();
      const cum = weights.map(() => 0);
      DATA.tickers.forEach((tk, j) => {
        c.beginPath();
        weights.forEach((r, i) => { const y = Y(cum[i] + r.w[j]); i ? c.lineTo(X(i), y) : c.moveTo(X(i), y); });
        for (let i = m - 1; i >= 0; i--) c.lineTo(X(i), Y(cum[i]));
        c.closePath();
        const dim = hover && hover.i != null && hover.tk != null && hover.tk !== j;
        c.fillStyle = rgba(TC[tk], dim ? 0.25 : 0.82); c.fill();
        weights.forEach((r, i) => { cum[i] += r.w[j]; });
      });
      c.restore();
      if (hover && hover.i != null) {
        const x = X(hover.i);
        c.strokeStyle = C.ink; c.lineWidth = 1;
        c.beginPath(); c.moveTo(x, box.t); c.lineTo(x, box.b); c.stroke();
      }
      weightIdx = (mx, my) => {
        if (mx < box.l || mx > box.r || my < box.t || my > box.b) return null;
        const i = Math.round(((mx - box.l) / box.w) * (m - 1)), v = 1 - (my - box.t) / box.h;
        let acc = 0, tk = null;
        weights[i].w.forEach((w, j) => { if (tk === null && v >= acc && v < acc + w) tk = j; acc += w; });
        return { i, tk, x: X(i), y: my };
      };
    }

    function drawCorr(c, box) {
      const M = DATA.corr, n = M.length, tk = DATA.tickers;
      const cell = Math.floor(Math.min((S.w - 64) / n, (S.h - 44) / n)), ox = Math.round((S.w - cell * n) / 2 + 22), oy = 30;
      c.save(); c.font = `500 10.5px ${MONO}`; c.textBaseline = 'middle';
      tk.forEach((name, i) => {
        const hl = hover && (hover.r === i || hover.c === i);
        c.fillStyle = hl ? C.ink : C.muted;
        c.textAlign = 'right'; c.fillText(name, ox - 8, oy + i * cell + cell / 2);
        c.textAlign = 'center'; c.fillText(name, ox + i * cell + cell / 2, oy - 12);
      });
      c.restore();
      for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
        const v = M[i][j], q = easeOut(clamp(p * 1.8 - ((i + j) / (2 * n)) * 0.8, 0, 1));
        if (q <= 0) continue;
        const sz = (cell - 2) * q, x = ox + j * cell + (cell - sz) / 2, y = oy + i * cell + (cell - sz) / 2;
        const dim = hover && hover.r !== i && hover.c !== j;
        c.fillStyle = v >= 0 ? mix('#12151a', C.accent, Math.pow(v, 0.9), dim ? 0.45 : 1) : mix('#12151a', C.warm, Math.pow(-v, 0.8), dim ? 0.45 : 1);
        c.beginPath(); c.roundRect ? c.roundRect(x, y, sz, sz, 3) : c.rect(x, y, sz, sz); c.fill();
        if (cell >= 34 && q > 0.9) label(c, num(v, 2), x + sz / 2, y + sz / 2, Math.abs(v) > 0.55 ? C.bg : C.muted, 'center', 9.5);
      }
      if (hover && hover.r != null) {
        c.strokeStyle = C.ink; c.lineWidth = 1.5;
        c.strokeRect(ox + hover.c * cell + 0.5, oy + hover.r * cell + 0.5, cell - 1, cell - 1);
      }
      corrCell = (mx, my) => {
        const j = Math.floor((mx - ox) / cell), i = Math.floor((my - oy) / cell);
        if (i < 0 || j < 0 || i >= n || j >= n) return null;
        return { r: i, c: j, x: ox + j * cell + cell / 2, y: oy + i * cell };
      };
    }

    function onMove(e) {
      const r = cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
      hover = null;
      if (view === 'frontier') {
        const h = frontierHit(mx, my);
        if (h) {
          hover = h;
          if (h.asset != null) {
            const a = DATA.assets[h.asset];
            tipShow(tip, stage, h.x, h.y, tipRows(`${a.t} · ${t(a.role)}`, [[t('Return'), pct(a.mu)], [t('Volatility'), pct(a.vol)], ['Sharpe', num(a.sr, 2)], [t('Max drawdown'), pct(a.dd)]]));
          } else {
            const q = F[h.front];
            tipShow(tip, stage, h.x, h.y, tipRows(t('Frontier portfolio'), [[t('Volatility'), pct(q[0], 2)], [t('Return'), pct(q[1], 2)], ['μ/σ', num(q[1] / q[0], 2)]]));
          }
        }
      } else if (view === 'wealth') {
        const i = wealthIdx(mx);
        if (i != null) {
          hover = { i };
          const rows = [...visible].map(s => [s, W.series[s][i]]).sort((a, b) => b[1] - a[1])
            .map(([s, v]) => [`<span style="color:${SC[s]}">●</span> ${t(s)}`, num(v, 2) + '×']);
          rows.push([t('Drawdown'), pct(W.dd[W.headline][i])]);
          tipShow(tip, stage, mx, my, tipRows(fmtDate(W.dates[i], true), rows));
        }
      } else if (view === 'weights') {
        const h = weightIdx(mx, my);
        if (h) {
          hover = h;
          const r = weights[h.i];
          const rows = DATA.tickers.map((tk, j) => [tk, r.w[j], j]).filter(x => x[1] >= 0.005).sort((a, b) => b[1] - a[1])
            .map(([tk, w, j]) => [`<span style="color:${TC[tk]}">■</span> ${j === h.tk ? '<b style="display:inline">' + tk + '</b>' : tk}`, pct(w, 1)]);
          tipShow(tip, stage, h.x, my, tipRows(fmtDate(r.d, true), rows));
        }
      } else {
        const h = corrCell(mx, my);
        if (h) {
          hover = h;
          tipShow(tip, stage, h.x, h.y, tipRows(`${DATA.tickers[h.r]} × ${DATA.tickers[h.c]}`, [['ρ', num(DATA.corr[h.r][h.c], 2)]]));
        }
      }
      if (!hover) tipHide(tip);
      dirty = true;
      if (RM) draw();
    }
    cv.addEventListener('pointermove', onMove);
    cv.addEventListener('pointerdown', onMove);
    cv.addEventListener('pointerleave', () => { hover = null; tipHide(tip); dirty = true; if (RM) draw(); });
    onLang.push(() => { buildLegend(); dirty = true; draw(); });

    if (!RM) job(lab, dt => {
      if (p < 1) { p = Math.min(1, p + dt / 1.5); dirty = true; }
      if (dirty) { dirty = false; draw(); }
    }, '-10% 0px');
  }

  /* =====================================================================
     6. Laboratorio Black–Scholes (fórmulas exactas)
     ===================================================================== */
  function bsLab() {
    const lab = $('[data-lab="bs"]');
    if (!lab) return;
    const cv = $('.lab-canvas', lab), K = 100, NP = 180, xs = Array.from({ length: NP }, (_, i) => 50 + (100 * i) / (NP - 1));
    const st = { type: 'call', sig: 0.2, T: 1, r: 0.03, S: 108, view: 'price' };
    let disp = null, target = null, ghosts = [], yr = [0, 55], yrT = [0, 55], dirty = true, intro = RM ? 1 : 0;
    const S = surface(cv, () => { dirty = true; if (RM) draw(); });
    const val = (g, v) => (v === 'price' ? g.price : g[v]);
    const curve = (v, T) => xs.map(x => val(bs(x, K, T, st.r, st.sig, st.type), v));
    function recompute() {
      target = curve(st.view, st.T);
      ghosts = [0.2, 0.45, 0.7].map(f => curve(st.view, Math.max(0.01, st.T * f)));
      if (!disp || disp.length !== NP) disp = target.slice();
      let lo = Math.min(...target), hi = Math.max(...target);
      if (st.view === 'price') { lo = 0; hi = Math.max(hi, 50) * 1.08; }
      else if (st.view === 'delta') { lo = st.type === 'call' ? -0.05 : -1.05; hi = st.type === 'call' ? 1.05 : 0.05; }
      else { const pad = (hi - lo) * 0.12 || 0.01; lo = Math.min(0, lo - pad); hi = Math.max(0, hi + pad); }
      yrT = [lo, hi];
      dirty = true;
    }
    function greeks() {
      const g = bs(st.S, K, st.T, st.r, st.sig, st.type);
      const set = (k, v) => { const el = $(`[data-g="${k}"]`, lab); if (el) el.textContent = v; };
      set('v', num(g.price, 2)); set('delta', num(g.delta, 3)); set('gamma', num(g.gamma, 4));
      set('vega', num(g.vega, 3)); set('theta', num(g.theta, 4)); set('rho', num(g.rho, 3));
      return g;
    }
    const titles = { price: 'Option value', delta: 'Delta Δ', gamma: 'Gamma Γ', vega: 'Vega ν (per 1 vol pt)', theta: 'Theta Θ (per day)' };

    function draw() {
      if (!S.w || !target) return;
      S.clear();
      const c = S.ctx, narrow = S.w < 520, box = { l: narrow ? 46 : 56, t: 18, r: S.w - 16, b: S.h - 30 };
      box.w = box.r - box.l; box.h = box.b - box.t;
      const X = v => box.l + ((v - 50) / 100) * box.w, Y = v => box.t + ((yr[1] - v) / (yr[1] - yr[0])) * box.h;
      const tk = niceTicks(yr[0], yr[1], 5);
      grid(c, box, X, Y, [60, 80, 100, 120, 140], tk.ticks, v => String(v), v => num(v, tk.dec));
      if (yr[0] < 0 && yr[1] > 0) { c.strokeStyle = 'rgba(236,238,241,0.22)'; c.beginPath(); c.moveTo(box.l, Y(0)); c.lineTo(box.r, Y(0)); c.stroke(); }
      label(c, t(titles[st.view]), box.l + 8, box.t + 8, C.soft, 'left', 10.5);
      label(c, t('Spot price') + ' →', box.r - 4, box.b - 12, C.soft, 'right', 10.5);
      c.save(); c.beginPath(); c.rect(box.l, box.t - 4, box.w * easeOut(intro), box.h + 8); c.clip();
      // Vencimientos más cortos (decaimiento temporal)
      ghosts.forEach((g, gi) => {
        c.beginPath(); g.forEach((v, i) => (i ? c.lineTo(X(xs[i]), Y(v)) : c.moveTo(X(xs[i]), Y(v))));
        c.strokeStyle = rgba(C.accent, 0.12 + gi * 0.06); c.lineWidth = 1; c.stroke();
      });
      if (st.view === 'price') {
        c.setLineDash([4, 4]);
        c.beginPath(); xs.forEach((x, i) => { const v = st.type === 'call' ? Math.max(x - K, 0) : Math.max(K - x, 0); i ? c.lineTo(X(x), Y(v)) : c.moveTo(X(x), Y(v)); });
        c.strokeStyle = rgba(C.ink, 0.45); c.lineWidth = 1.2; c.stroke(); c.setLineDash([]);
        const grad = c.createLinearGradient(0, box.t, 0, box.b);
        grad.addColorStop(0, rgba(C.accent, 0.26)); grad.addColorStop(1, rgba(C.accent, 0));
        c.beginPath(); disp.forEach((v, i) => (i ? c.lineTo(X(xs[i]), Y(v)) : c.moveTo(X(xs[i]), Y(v))));
        c.lineTo(X(150), Y(Math.max(0, yr[0]))); c.lineTo(X(50), Y(Math.max(0, yr[0]))); c.closePath();
        c.fillStyle = grad; c.fill();
      }
      c.save();
      c.beginPath(); disp.forEach((v, i) => (i ? c.lineTo(X(xs[i]), Y(v)) : c.moveTo(X(xs[i]), Y(v))));
      c.lineJoin = 'round'; c.strokeStyle = rgba(C.hi, 0.16); c.lineWidth = 8; c.stroke();
      c.strokeStyle = C.hi; c.lineWidth = 2.4; c.stroke(); c.restore();
      c.restore();
      // Strike
      label(c, 'K', X(K), box.b - 10, C.muted, 'center', 10.5, 500);
      // Marcador del subyacente y recta tangente (la pendiente es la delta)
      const g = greeks(), v = val(g, st.view), x = X(st.S), y = Y(v);
      c.strokeStyle = rgba(C.warm, 0.35); c.setLineDash([2, 4]);
      c.beginPath(); c.moveTo(x, box.b); c.lineTo(x, y); c.stroke(); c.setLineDash([]);
      if (st.view === 'price') {
        const d = 14;
        c.beginPath(); c.moveTo(X(st.S - d), Y(v - g.delta * d)); c.lineTo(X(st.S + d), Y(v + g.delta * d));
        c.strokeStyle = C.warm; c.lineWidth = 1.6; c.stroke();
        label(c, `Δ = ${num(g.delta, 2)}`, X(st.S + d) + 6, Y(v + g.delta * d) - 2, C.warm, 'left', 11, 500);
      }
      c.beginPath(); c.arc(x, y, 9, 0, Math.PI * 2); c.fillStyle = rgba(C.warm, 0.18); c.fill();
      c.beginPath(); c.arc(x, y, 4.5, 0, Math.PI * 2); c.fillStyle = C.warm; c.fill();
      label(c, `S = ${num(st.S, 1)}`, x, box.b + 18, C.warm, 'center', 10.5, 500);
    }

    // Controles
    tabs(lab, v => { st.view = v; disp = null; intro = RM ? 1 : 0; recompute(); if (RM) draw(); });
    $$('[data-type]', lab).forEach(b => b.addEventListener('click', () => {
      st.type = b.dataset.type;
      $$('[data-type]', lab).forEach(x => x.setAttribute('aria-pressed', x === b));
      recompute(); if (RM) { disp = target.slice(); yr = yrT.slice(); draw(); }
    }));
    $$('[data-bs]', lab).forEach(inp => inp.addEventListener('input', () => {
      const k = inp.dataset.bs, v = +inp.value;
      if (k === 'sig') { st.sig = v / 100; $('[data-out="sig"]', lab).textContent = v + '%'; }
      if (k === 'T') { st.T = v / 100; $('[data-out="T"]', lab).textContent = num(st.T, 2) + 'y'; }
      if (k === 'r') { st.r = v / 1000; $('[data-out="r"]', lab).textContent = num(st.r * 100, 1) + '%'; }
      recompute(); if (RM) { disp = target.slice(); yr = yrT.slice(); draw(); }
    }));
    let down = false;
    const setSpot = e => {
      const r = cv.getBoundingClientRect(), narrow = r.width < 520, l = narrow ? 46 : 56, w = r.width - l - 16;
      st.S = clamp(50 + ((e.clientX - r.left - l) / w) * 100, 51, 149);
      dirty = true; if (RM) draw();
    };
    cv.addEventListener('pointerdown', e => { down = true; setSpot(e); });
    cv.addEventListener('pointermove', e => { if (down || e.pointerType === 'mouse') setSpot(e); });
    addEventListener('pointerup', () => { down = false; });
    onLang.push(() => { dirty = true; draw(); });

    recompute();
    if (RM) { disp = target.slice(); yr = yrT.slice(); }
    else job(lab, dt => {
      if (intro < 1) { intro = Math.min(1, intro + dt / 1.1); dirty = true; }
      let moving = false;
      for (let i = 0; i < NP; i++) { const d = target[i] - disp[i]; if (Math.abs(d) > 1e-6) { disp[i] += d * 0.22; moving = true; } }
      for (let i = 0; i < 2; i++) { const d = yrT[i] - yr[i]; if (Math.abs(d) > 1e-6) { yr[i] += d * 0.18; moving = true; } }
      if (moving || dirty) { dirty = false; draw(); }
    }, '-10% 0px');
    greeks();
  }

  /* =====================================================================
     7. Simulador de Kelly (números aleatorios comunes con semilla)
     ===================================================================== */
  function kellyLab() {
    const lab = $('[data-lab="kelly"]');
    if (!lab) return;
    const cv = $('.lab-canvas', lab), NPATH = 60, NB = 400;
    const st = { p: 0.55, mult: 1, seed: 42 };
    let U = null, paths = [], med = null, term = [], stats = {}, reveal = RM ? 1 : 0, dirty = true, geo = null;
    const S = surface(cv, () => { dirty = true; if (RM) draw(); });
    const g = (f, p) => p * Math.log(1 + f) + (1 - p) * Math.log(1 - f);
    function regen() {
      const rng = mulberry32(st.seed);
      U = new Float32Array(NPATH * NB);
      for (let i = 0; i < U.length; i++) U[i] = rng();
    }
    function compute() {
      const fs = 2 * st.p - 1, f = Math.min(0.99, st.mult * fs), up = Math.log10(1 + f), dn = Math.log10(1 - f);
      paths = []; term = [];
      let loss = 0, dd50 = 0;
      for (let i = 0; i < NPATH; i++) {
        const a = new Float32Array(NB + 1);
        let w = 0, peak = 0, mdd = 0;
        for (let b = 0; b < NB; b++) {
          w += U[i * NB + b] < st.p ? up : dn;
          a[b + 1] = w;
          if (w > peak) peak = w;
          mdd = Math.max(mdd, 1 - Math.pow(10, w - peak));
        }
        paths.push(a); term.push(w);
        if (w < 0) loss++;
        if (mdd > 0.5) dd50++;
      }
      med = new Float32Array(NB + 1);
      const col = new Float32Array(NPATH);
      for (let b = 0; b <= NB; b++) { for (let i = 0; i < NPATH; i++) col[i] = paths[i][b]; col.sort(); med[b] = (col[NPATH / 2 - 1] + col[NPATH / 2]) / 2; }
      const sorted = term.slice().sort((x, y) => x - y);
      stats = { fs, f, g: g(f, st.p), med: Math.pow(10, (sorted[NPATH / 2 - 1] + sorted[NPATH / 2]) / 2), loss: loss / NPATH, dd: dd50 / NPATH };
      const set = (k, v) => { const el = $(`[data-k="${k}"]`, lab); if (el) el.textContent = v; };
      set('fstar', num(fs, 2)); set('f', num(f, 2)); set('g', pct(stats.g, 2));
      set('med', fmtX(stats.med)); set('loss', pct(stats.loss, 0)); set('dd', pct(stats.dd, 0));
      dirty = true;
    }
    const fmtX = w => (w >= 100 ? num(w, 0) : w >= 1 ? num(w, 2) : w >= 0.01 ? num(w, 3) : w.toExponential(1)) + '×';

    function draw() {
      if (!S.w || !paths.length) return;
      S.clear();
      const c = S.ctx, narrow = S.w < 520, l = narrow ? 44 : 56, r = S.w - 14;
      const top = { l, r, t: 16, b: S.h * 0.62 }, bot = { l, r, t: S.h * 0.72, b: S.h - 28 };
      // Riqueza en escala logarítmica
      let lo = 0, hi = 1;
      paths.forEach(a => { for (let b = 0; b <= NB; b += 4) { if (a[b] < lo) lo = a[b]; if (a[b] > hi) hi = a[b]; } });
      lo = Math.max(-4, Math.floor(lo)); hi = Math.min(8, Math.ceil(hi));
      if (hi - lo < 2) lo = hi - 2;
      const X = b => top.l + (b / NB) * (top.r - top.l), Y = v => top.t + ((hi - Math.max(lo, v)) / (hi - lo)) * (top.b - top.t);
      const every = hi - lo > 6 ? 2 : 1, yt = [];
      for (let k = lo; k <= hi; k += every) yt.push(k);
      const SUP = { '-': '⁻', 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹' };
      const pow10 = k => (k === 0 ? '1×' : k === 1 ? '10×' : '10' + String(k).split('').map(ch => SUP[ch]).join('') + '×');
      grid(c, top, X, Y, [0, 100, 200, 300, 400], yt, v => String(v), pow10);
      c.fillStyle = rgba(C.neg, 0.06); c.fillRect(top.l, Y(lo + 0.35), top.r - top.l, Y(lo) - Y(lo + 0.35));
      c.strokeStyle = 'rgba(236,238,241,0.3)'; c.beginPath(); c.moveTo(top.l, Y(0)); c.lineTo(top.r, Y(0)); c.stroke();
      label(c, t('Wealth (log scale)'), top.l + 8, top.t + 8, C.soft, 'left', 10.5);
      const k = Math.max(1, Math.floor(NB * easeOut(reveal)));
      paths.forEach((a, i) => {
        c.beginPath(); c.moveTo(X(0), Y(0));
        for (let b = 1; b <= k; b++) c.lineTo(X(b), Y(a[b]));
        c.strokeStyle = term[i] >= 0 ? rgba(C.accent, 0.22) : rgba(C.neg, 0.25); c.lineWidth = 1; c.stroke();
      });
      // Tendencia teórica: n·g(f)
      c.setLineDash([5, 5]);
      c.beginPath(); c.moveTo(X(0), Y(0)); c.lineTo(X(k), Y((k * stats.g) / Math.LN10));
      c.strokeStyle = rgba(C.ink, 0.65); c.lineWidth = 1.2; c.stroke(); c.setLineDash([]);
      c.save();
      c.beginPath(); c.moveTo(X(0), Y(0));
      for (let b = 1; b <= k; b++) c.lineTo(X(b), Y(med[b]));
      c.lineJoin = 'round'; c.strokeStyle = rgba(C.warm, 0.18); c.lineWidth = 7; c.stroke();
      c.strokeStyle = C.warm; c.lineWidth = 2.2; c.stroke(); c.restore();
      if (!narrow) {
        label(c, t('Median path'), X(k) - 6, Y(med[k]) - 12, C.warm, 'right', 10.5, 500);
      }
      label(c, t('Bets') + ' →', top.r - 4, top.b - 12, C.soft, 'right', 10.5);
      // Crecimiento esperado g(f)
      const fs = stats.fs, fmax = Math.min(0.99, fs * 2.6), gmax = g(fs, st.p);
      const gmin = Math.max(g(fmax, st.p), -gmax * 3);
      const XF = f => bot.l + (f / fmax) * (bot.r - bot.l), YG = v => bot.t + ((gmax * 1.3 - clamp(v, gmin, gmax * 1.3)) / (gmax * 1.3 - gmin)) * (bot.b - bot.t);
      c.strokeStyle = 'rgba(255,255,255,0.06)'; c.strokeRect(bot.l + 0.5, bot.t + 0.5, bot.r - bot.l - 1, bot.b - bot.t - 1);
      c.strokeStyle = 'rgba(236,238,241,0.3)'; c.beginPath(); c.moveTo(bot.l, YG(0)); c.lineTo(bot.r, YG(0)); c.stroke();
      const pts = Array.from({ length: 121 }, (_, i) => (fmax * i) / 120);
      c.beginPath(); c.moveTo(XF(0), YG(0)); pts.forEach(f => c.lineTo(XF(f), YG(g(f, st.p)))); c.lineTo(XF(fmax), YG(0)); c.closePath();
      c.fillStyle = rgba(C.accent, 0.08); c.fill();
      c.beginPath(); pts.forEach((f, i) => (i ? c.lineTo(XF(f), YG(g(f, st.p))) : c.moveTo(XF(f), YG(g(f, st.p)))));
      c.strokeStyle = C.accent; c.lineWidth = 2; c.stroke();
      c.setLineDash([2, 4]); c.strokeStyle = rgba(C.ink, 0.35);
      c.beginPath(); c.moveTo(XF(fs), bot.t); c.lineTo(XF(fs), bot.b); c.stroke();
      if (2 * fs <= fmax) { c.beginPath(); c.moveTo(XF(2 * fs), bot.t); c.lineTo(XF(2 * fs), bot.b); c.stroke(); }
      c.setLineDash([]);
      label(c, 'f*', XF(fs) + 5, bot.t + 9, C.ink, 'left', 10.5, 500);
      if (2 * fs <= fmax) label(c, '2f* · g ≈ 0', XF(2 * fs) + 5, bot.t + 9, C.neg, 'left', 10.5);
      const fx = XF(Math.min(stats.f, fmax)), fy = YG(stats.g);
      c.beginPath(); c.arc(fx, fy, 9, 0, Math.PI * 2); c.fillStyle = rgba(C.warm, 0.2); c.fill();
      c.beginPath(); c.arc(fx, fy, 4.5, 0, Math.PI * 2); c.fillStyle = stats.g >= 0 ? C.warm : C.neg; c.fill();
      label(c, t('Growth per bet g(f)'), bot.l + 8, bot.b - 10, C.soft, 'left', 10.5);
      label(c, t('Staked fraction f') + ' →', bot.r - 4, bot.b + 14, C.soft, 'right', 10.5);
      geo = { bot, fmax };
    }

    const multEl = $('[data-kelly="mult"]', lab);
    function setMult(m) {
      st.mult = m;
      multEl.value = Math.round(m * 100);
      multEl.style.setProperty('--f', (m / 2.5) * 100 + '%');
      $('[data-out="mult"]', lab).textContent = num(m, 2) + '×';
      compute(); if (RM) draw();
    }
    $('[data-kelly="p"]', lab).addEventListener('input', e => {
      st.p = +e.target.value / 100;
      $('[data-out="p"]', lab).textContent = num(st.p, 2);
      compute(); if (RM) draw();
    });
    multEl.addEventListener('input', () => setMult(+multEl.value / 100));
    $('[data-kelly="rerun"]', lab).addEventListener('click', () => {
      st.seed = (st.seed * 48271) % 2147483647;
      regen(); compute(); reveal = RM ? 1 : 0; if (RM) draw();
    });
    // Arrastrar sobre la curva g(f) ajusta la fracción apostada
    let down = false;
    const fromPointer = e => {
      if (!geo) return false;
      const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
      if (!down && (y < geo.bot.t - 10 || y > geo.bot.b + 10)) return false;
      const f = clamp(((x - geo.bot.l) / (geo.bot.r - geo.bot.l)) * geo.fmax, 0, geo.fmax);
      setMult(clamp(Math.round((f / (2 * st.p - 1)) * 20) / 20, 0, 2.5));
      return true;
    };
    cv.addEventListener('pointerdown', e => { if (fromPointer(e)) down = true; });
    cv.addEventListener('pointermove', e => { if (down) fromPointer(e); });
    addEventListener('pointerup', () => { down = false; });
    onLang.push(() => { compute(); draw(); });

    regen(); compute();
    if (!RM) job(lab, dt => {
      if (reveal < 1) { reveal = Math.min(1, reveal + dt / 1.6); dirty = true; }
      if (dirty) { dirty = false; draw(); }
    }, '-10% 0px');
  }

  /* =====================================================================
     8. Superficie de volatilidad implícita en 3D (ilustrativa)
     ===================================================================== */
  function volSurface() {
    const cv = $('.surface-canvas');
    if (!cv) return;
    const NX = 26, NZ = 20;
    let yaw = -0.62, pitch = 0.42, vyaw = 0.18, drag = null, time = 0;
    const S = surface(cv, () => { if (RM) draw(); });
    const iv = (k, T, ph) => {
      const atm = 0.16 + 0.08 * Math.exp(-1.6 * T);
      const sk = -(0.16 / Math.sqrt(T + 0.08)) * (1 + 0.07 * Math.sin(ph));
      const cu = (0.32 / (T + 0.25)) * (1 + 0.1 * Math.cos(ph * 0.7));
      return Math.max(0.06, atm + sk * k * 0.5 + cu * k * k * 0.5);
    };
    function draw() {
      if (!S.w) return;
      S.clear();
      const c = S.ctx, w = S.w, h = S.h, wide = w > 900;
      const cx = wide ? w * 0.7 : w * 0.5, cy = wide ? h * 0.5 : h * 0.36;
      const f = Math.min(w * (wide ? 0.62 : 1.05), h * 1.15), d = 4.2;
      const cyw = Math.cos(yaw), syw = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
      const proj = (x, y, z) => {
        const x1 = x * cyw - z * syw, z1 = x * syw + z * cyw;
        const y2 = y * cp - z1 * sp, z2 = y * sp + z1 * cp, s = f / (d + z2);
        return [cx + x1 * s, cy - y2 * s, z2];
      };
      const ph = time * 0.6;
      const P = [], V = [];
      for (let j = 0; j < NZ; j++) for (let i = 0; i < NX; i++) {
        const k = -0.4 + (0.8 * i) / (NX - 1), T = 0.08 + (1.92 * j) / (NZ - 1), v = iv(k, T, ph);
        P.push(proj((k / 0.4) * 1.25, ((v - 0.22) / 0.18) * 0.85, ((T - 1.04) / 0.96) * 1.05));
        V.push(v);
      }
      // Suelo de referencia
      c.lineWidth = 1;
      for (let i = 0; i <= 8; i++) {
        const u = -1.25 + (2.5 * i) / 8, a = proj(u, -0.95, -1.05), b = proj(u, -0.95, 1.05);
        const q = -1.05 + (2.1 * i) / 8, e = proj(-1.25, -0.95, q), g2 = proj(1.25, -0.95, q);
        c.strokeStyle = 'rgba(159,179,200,0.07)';
        c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.moveTo(e[0], e[1]); c.lineTo(g2[0], g2[1]); c.stroke();
      }
      const vmin = 0.13, vmax = 0.3;
      // Escala de color: azul acero (vol. baja) → ámbar (vol. alta)
      const mix0 = k => { const a = hex2rgb(C.accent), b = hex2rgb(C.warm); return '#' + a.map((v, i) => Math.round(lerp(v, b[i], k)).toString(16).padStart(2, '0')).join(''); };
      const quads = [];
      for (let j = 0; j < NZ - 1; j++) for (let i = 0; i < NX - 1; i++) {
        const a = j * NX + i, b = a + 1, cc = a + NX + 1, dd = a + NX;
        quads.push([a, b, cc, dd, (P[a][2] + P[b][2] + P[cc][2] + P[dd][2]) / 4]);
      }
      quads.sort((q1, q2) => q2[4] - q1[4]);
      for (const q of quads) {
        const v = (V[q[0]] + V[q[2]]) / 2, k = clamp((v - vmin) / (vmax - vmin), 0, 1), depth = clamp((q[4] + 1.6) / 3.2, 0, 1);
        c.beginPath();
        c.moveTo(P[q[0]][0], P[q[0]][1]); c.lineTo(P[q[1]][0], P[q[1]][1]); c.lineTo(P[q[2]][0], P[q[2]][1]); c.lineTo(P[q[3]][0], P[q[3]][1]); c.closePath();
        c.fillStyle = mix(mix0(k), '#0b0d11', 0.62 + depth * 0.18, 0.95);
        c.fill();
        c.strokeStyle = mix(C.accent, C.warm, k, 0.75 - depth * 0.45);
        c.lineWidth = 0.8; c.stroke();
      }
      // Ejes rotulados
      const ax = [[proj(0, -0.95, -1.25), t('Moneyness')], [proj(1.45, -0.95, 0), t('Maturity')], [proj(-1.25, 0.95, -1.05), t('Implied vol')]];
      ax.forEach(([p, txt]) => label(c, txt, p[0], p[1], C.soft, 'center', 10.5));
    }
    cv.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY, yaw, pitch, t: performance.now() }; cv.setPointerCapture(e.pointerId); });
    cv.addEventListener('pointermove', e => {
      if (!drag) return;
      const nyaw = drag.yaw + (e.clientX - drag.x) * 0.008;
      vyaw = clamp((nyaw - yaw) * 30, -2, 2);
      yaw = nyaw;
      pitch = clamp(drag.pitch + (e.clientY - drag.y) * 0.004, 0.12, 1.15);
      if (RM) draw();
    });
    const end = () => { drag = null; };
    cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', end);
    onLang.push(draw);
    if (!RM) job(cv, dt => {
      time += dt;
      if (!drag) { vyaw = lerp(vyaw, 0.18, 0.02); yaw += vyaw * dt; }
      draw();
    });
  }

  /* =====================================================================
     9. Glifos animados de los ocho fundamentos e inclinación 3D
     ===================================================================== */
  function glyphs() {
    const rngPaths = (seed, n, len, vol) => {
      const r = mulberry32(seed);
      return Array.from({ length: n }, () => { let v = 0; const a = [0]; for (let i = 0; i < len; i++) { v += vol * gauss(r) - vol * vol / 2; a.push(v); } return a; });
    };
    const MC = rngPaths(11, 16, 60, 0.05);
    const TS = (() => { const r = mulberry32(5); let v = 0; const a = []; for (let i = 0; i < 520; i++) { v += 0.9 * gauss(r) + 0.25 * Math.sin(i / 40); a.push(v); } return a; })();
    const ma = (a, n) => a.map((_, i) => { let s = 0, c = 0; for (let j = Math.max(0, i - n + 1); j <= i; j++) { s += a[j]; c++; } return s / c; });
    const TF = ma(TS, 12), TL = ma(TS, 40), TSR = { lo: null, hi: null };
    const MKD = (() => { const r = mulberry32(3); return Array.from({ length: 10 }, () => [0.25 + r() * 0.65, 0.15 + r() * 0.55, r() * 6]); })();
    const line = (c, pts, color, w = 1.6) => { c.beginPath(); pts.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y))); c.strokeStyle = color; c.lineWidth = w; c.lineJoin = 'round'; c.stroke(); };
    const G = {
      bs(c, w, h, tm) {
        const X = s => 8 + ((s - 60) / 80) * (w - 16), Y = v => h - 10 - (v / 42) * (h - 22), T = 0.05 + 0.9 * (0.5 + 0.5 * Math.sin(tm));
        c.setLineDash([3, 3]); line(c, [[X(60), Y(0)], [X(100), Y(0)], [X(140), Y(40)]], rgba(C.ink, 0.4), 1); c.setLineDash([]);
        const pts = []; for (let s = 60; s <= 140; s += 2) pts.push([X(s), Y(bs(s, 100, T, 0.03, 0.25, 'call').price)]);
        line(c, pts, C.accent, 2);
        const S = 100 + 28 * Math.sin(tm * 0.7), v = bs(S, 100, T, 0.03, 0.25, 'call').price;
        c.beginPath(); c.arc(X(S), Y(v), 3.5, 0, 7); c.fillStyle = C.warm; c.fill();
      },
      mc(c, w, h, tm) {
        const r = (tm * 0.35) % 1.3, kf = clamp(r, 0, 1) * 60, k = Math.floor(kf), fr = kf - k, X = i => 8 + (i / 60) * (w * 0.72), Y = v => h / 2 - v * (h * 0.9);
        MC.forEach(a => { const pts = a.slice(0, k + 1).map((v, i) => [X(i), Y(v)]); if (k < 60) pts.push([X(kf), Y(lerp(a[k], a[k + 1], fr))]); line(c, pts, rgba(C.accent, 0.45), 1); if (k >= 60) { c.beginPath(); c.arc(X(60), Y(a[60]), 2, 0, 7); c.fillStyle = C.hi; c.fill(); } });
        const bins = new Array(8).fill(0); MC.forEach(a => { const b = clamp(Math.floor((a[60] + 0.45) / 0.9 * 8), 0, 7); bins[b]++; });
        if (k >= 60) bins.forEach((n, b) => { c.fillStyle = rgba(C.warm, 0.6); const y0 = Y(-0.45 + (b * 0.9) / 8); c.fillRect(w * 0.78, y0 - (h * 0.9 * 0.9) / 8 + 1, n * 6 * clamp(r - 1, 0, 0.3) / 0.3, (h * 0.81) / 8 - 2); });
      },
      mk(c, w, h, tm) {
        const X = s => 10 + s * (w - 20), Y = m => h - 10 - m * (h - 20);
        const up = [], dn = [];
        for (let m = 0.05; m <= 0.95; m += 0.02) { const s = 0.12 + Math.sqrt(0.002 + 0.75 * (m - 0.35) ** 2); (m >= 0.35 ? up : dn).push([X(Math.min(s, 1)), Y(m)]); }
        c.setLineDash([3, 3]); line(c, dn, rgba(C.ink, 0.3), 1); c.setLineDash([]);
        line(c, up, C.accent, 2);
        MKD.forEach(([s, m, ph]) => { c.beginPath(); c.arc(X(s + 0.02 * Math.sin(tm + ph)), Y(m + 0.02 * Math.cos(tm * 1.3 + ph)), 2.6, 0, 7); c.fillStyle = C.bg; c.fill(); c.strokeStyle = C.muted; c.lineWidth = 1.2; c.stroke(); });
        const m = 0.45 + 0.4 * (0.5 + 0.5 * Math.sin(tm * 0.8)), s = 0.12 + Math.sqrt(0.002 + 0.75 * (m - 0.35) ** 2);
        c.beginPath(); c.arc(X(s), Y(m), 4, 0, 7); c.fillStyle = C.warm; c.fill();
      },
      var(c, w, h, tm) {
        const X = x => 8 + ((x + 4.5) / 9) * (w - 16), pdf = x => Math.pow(1 + (x * x) / 4, -2.5), Y = v => h - 12 - v * (h - 26);
        const q = -1.65 - 0.65 * (0.5 + 0.5 * Math.sin(tm * 0.9));
        c.beginPath(); c.moveTo(X(-4.5), Y(0)); for (let x = -4.5; x <= q; x += 0.05) c.lineTo(X(x), Y(pdf(x))); c.lineTo(X(q), Y(0)); c.closePath(); c.fillStyle = rgba(C.neg, 0.45); c.fill();
        const pts = []; for (let x = -4.5; x <= 4.5; x += 0.05) pts.push([X(x), Y(pdf(x))]); line(c, pts, C.accent, 1.8);
        c.strokeStyle = C.neg; c.lineWidth = 1.2; c.beginPath(); c.moveTo(X(q), Y(0)); c.lineTo(X(q), Y(0.85)); c.stroke();
        label(c, 'VaR', X(q) + 4, Y(0.82), C.neg, 'left', 10, 500);
        const es = q - 0.75; c.beginPath(); c.arc(X(es), Y(0) - 4, 3, 0, 7); c.fillStyle = C.warm; c.fill();
        label(c, 'ES', X(es), Y(0) - 14, C.warm, 'center', 10, 500);
      },
      ts(c, w, h, tm) {
        const win = 130, pos = (tm * 18) % (TS.length - win - 1), off = Math.floor(pos), fr = pos - off, seg = TS.slice(off, off + win + 1);
        const tLo = Math.min(...seg) - 1, tHi = Math.max(...seg) + 1;
        TSR.lo = TSR.lo == null ? tLo : lerp(TSR.lo, tLo, 0.06); TSR.hi = TSR.hi == null ? tHi : lerp(TSR.hi, tHi, 0.06);
        const lo = TSR.lo, hi = TSR.hi, X = i => 6 + ((i - fr) / (win - 1)) * (w - 12), Y = v => h - 8 - ((v - lo) / (hi - lo)) * (h - 16);
        c.save(); c.beginPath(); c.rect(0, 0, w, h); c.clip();
        line(c, seg.map((v, i) => [X(i), Y(v)]), rgba(C.ink, 0.5), 1);
        line(c, TF.slice(off, off + win + 1).map((v, i) => [X(i), Y(v)]), C.accent, 1.6);
        line(c, TL.slice(off, off + win + 1).map((v, i) => [X(i), Y(v)]), C.warm, 1.6);
        for (let i = off + 1; i <= off + win; i++) {
          const a = TF[i - 1] - TL[i - 1], b = TF[i] - TL[i];
          if (a * b < 0) { const x = X(i - off), y = Y(TF[i]); c.beginPath(); if (b > 0) { c.moveTo(x, y + 4); c.lineTo(x - 4, y + 11); c.lineTo(x + 4, y + 11); } else { c.moveTo(x, y - 4); c.lineTo(x - 4, y - 11); c.lineTo(x + 4, y - 11); } c.fillStyle = b > 0 ? C.pos : C.neg; c.fill(); }
        }
        c.restore();
      },
      iv(c, w, h, tm) {
        const X = k => 8 + ((k + 0.4) / 0.8) * (w - 16), Y = v => h - 8 - ((v - 0.12) / 0.32) * (h - 16);
        [0.1, 0.5, 1.5].forEach((T, n) => {
          const pts = []; for (let k = -0.4; k <= 0.4; k += 0.02) { const atm = 0.16 + 0.08 * Math.exp(-1.6 * T), sk = -(0.16 / Math.sqrt(T + 0.08)) * (1 + 0.15 * Math.sin(tm + n)), cu = (0.32 / (T + 0.25)) * (1 + 0.15 * Math.cos(tm * 0.8 + n)); pts.push([X(k), Y(atm + sk * k * 0.5 + cu * k * k * 0.5)]); }
          line(c, pts, [C.warm, C.accent, rgba(C.accent, 0.5)][n], n === 0 ? 2 : 1.5);
        });
      },
      yc(c, w, h, tm) {
        const ns = (tau, b0, b1, b2, l = 2) => { const x = tau / l, f = (1 - Math.exp(-x)) / x; return b0 + b1 * f + b2 * (f - Math.exp(-x)); };
        const X = tau => 8 + (Math.log(tau / 0.1) / Math.log(300)) * (w - 16), Y = v => h - 8 - (v / 7) * (h - 16);
        for (let g = 3; g >= 0; g--) {
          const ph = tm - g * 0.35, b1 = -2.2 * Math.cos(ph * 0.6), b2 = 2.4 * Math.sin(ph * 0.45), pts = [];
          for (let u = 0; u <= 1.0001; u += 0.02) { const tau = 0.1 * Math.pow(300, u); pts.push([X(tau), Y(ns(tau, 4, b1, b2))]); }
          line(c, pts, g ? rgba(C.accent, 0.12 + (3 - g) * 0.06) : C.accent, g ? 1 : 2);
          if (!g) [0.25, 1, 2, 5, 10, 30].forEach(tau => { c.beginPath(); c.arc(X(tau), Y(ns(tau, 4, b1, b2)), 2.6, 0, 7); c.fillStyle = C.warm; c.fill(); });
        }
      },
      fm(c, w, h, tm) {
        const names = ['MKT', 'HML', 'WML', 'QMJ', 'BAB'], bw = (w - 24) / names.length, zero = h * 0.55;
        c.strokeStyle = 'rgba(236,238,241,0.3)'; c.beginPath(); c.moveTo(8, zero); c.lineTo(w - 8, zero); c.stroke();
        names.forEach((n, i) => {
          const v = Math.sin(tm * 0.8 + i * 1.3) * 0.55 + [0.35, 0.05, 0.15, 0.1, -0.05][i], bh = v * h * 0.42, x = 12 + i * bw + bw * 0.2;
          c.fillStyle = v >= 0 ? rgba(C.accent, 0.85) : rgba(C.warm, 0.85);
          c.fillRect(x, v >= 0 ? zero - bh : zero, bw * 0.6, Math.abs(bh));
          label(c, n, x + bw * 0.3, h - 9, C.soft, 'center', 9);
        });
      }
    };
    $$('.basic').forEach(card => {
      const cv = $('.glyph', card), kind = card.dataset.glyph;
      let tm = Math.random() * 10, hov = false, speed = 1;
      const S = surface(cv, () => draw());
      function draw() { if (!S.w || !G[kind]) return; S.clear(); G[kind](S.ctx, S.w, S.h, tm, hov); }
      card.addEventListener('pointerenter', () => { hov = true; });
      card.addEventListener('pointerleave', () => { hov = false; card.style.transform = ''; });
      if (FINE && !RM) card.addEventListener('pointermove', e => {
        const r = card.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
        card.style.transform = `rotateX(${(0.5 - y) * 7}deg) rotateY(${(x - 0.5) * 9}deg) translateY(-4px)`;
        card.style.setProperty('--mx', x * 100 + '%'); card.style.setProperty('--my', y * 100 + '%');
      });
      if (!RM) job(card, dt => { speed = lerp(speed, hov ? 2.2 : 1, 0.08); tm += dt * speed; draw(); }, '40px');
    });
  }

  /* =====================================================================
     10. Fondo de contacto: curvas de tipos Nelson–Siegel en cresta
     ===================================================================== */
  function ctaCurves() {
    const cv = $('.cta-canvas');
    if (!cv) return;
    let tm = 0;
    const S = surface(cv, () => { if (RM) draw(); }, 1);
    const ns = (tau, b0, b1, b2, l = 2.2) => { const x = tau / l, f = (1 - Math.exp(-x)) / x; return b0 + b1 * f + b2 * (f - Math.exp(-x)); };
    function draw() {
      if (!S.w) return;
      S.clear();
      const c = S.ctx, w = S.w, h = S.h, R = w < 700 ? 18 : 28, x0 = -20, x1 = w + 20;
      for (let i = 0; i < R; i++) {
        const base = h * 0.12 + (i * (h * 0.86)) / R, ph = tm * 0.22 + i * 0.21;
        const b1 = -2.2 * Math.cos(ph), b2 = 3.2 * Math.sin(ph * 0.8 + 1), A = h * 0.075;
        const pts = [];
        for (let u = 0; u <= 1.0001; u += 0.01) {
          // Cresta: la curva Nelson–Siegel se amplifica en el centro y se aplana en los extremos
          const tau = 0.1 * Math.pow(300, u), env = Math.pow(Math.sin(Math.PI * u), 1.6);
          pts.push([lerp(x0, x1, u), base - A * (0.25 + env * (ns(tau, 0, b1, b2) + 2.4))]);
        }
        c.beginPath();
        pts.forEach(([x, y], k) => (k ? c.lineTo(x, y) : c.moveTo(x, y)));
        // Basta tapar la franja inmediatamente inferior (las crestas anteriores no bajan más)
        const floor = Math.min(h + 10, base + (h * 0.86 / R) * 3);
        c.lineTo(x1, floor); c.lineTo(x0, floor); c.closePath();
        c.fillStyle = C.bg; c.fill();
        c.beginPath();
        pts.forEach(([x, y], k) => (k ? c.lineTo(x, y) : c.moveTo(x, y)));
        c.strokeStyle = mix(C.accent, C.warm, i / R, 0.14 + 0.6 * (i / R)); c.lineWidth = 1.2; c.stroke();
      }
    }
    if (RM) return;
    job(cv, dt => { tm += dt; draw(); });
  }

  /* =====================================================================
     11. Paleta de comandos (Ctrl/⌘ + K)
     ===================================================================== */
  function commandPalette() {
    const dlg = $('.cmdk');
    if (!dlg || !dlg.showModal) { $$('.cmdk-open, .footer-hint').forEach(e => e.remove()); return; }
    const input = $('.cmdk-input', dlg), list = $('.cmdk-list', dlg);
    list.setAttribute('translate', 'no');
    let items = [], shown = [], sel = 0;
    const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    function build() {
      const sec = [['#top', 'Top'], ['#projects', 'Highlighted Projects'], ['#quant-basics', 'Quant Basics'], ['#about', 'About'], ['#contact', 'Contact']]
        .map(([href, l]) => ({ label: t(l), href, kind: t('Section'), icon: '#' }));
      const proj = $$('a.project-card').map(a => ({ label: $('h3', a).textContent.trim(), href: a.href, kind: t('Study'), icon: '↗' }));
      const es = lang() === 'es';
      const acts = [
        { label: t('Open CV'), href: 'assets/Alvaro-Cutillas-CV.pdf', blank: true, kind: t('Action'), icon: '⤓' },
        { label: t('Send an email'), href: 'mailto:acutillas.finance@gmail.com', kind: t('Action'), icon: '@' },
        { label: 'GitHub', href: 'https://github.com/AlvaroCutillas', blank: true, kind: t('Action'), icon: '⌥' },
        { label: 'LinkedIn', href: 'https://www.linkedin.com/in/%C3%A1lvaro-cutillas/', blank: true, kind: t('Action'), icon: 'in' },
        { label: es ? 'Switch to English' : 'Cambiar a español', run: () => I18N() && I18N().setLanguage(es ? 'en' : 'es'), kind: es ? 'Idioma' : 'Language', icon: '⇄' }
      ];
      return [...sec, ...proj, ...acts];
    }
    function render() {
      const words = norm(input.value.trim()).split(/\s+/).filter(Boolean);
      shown = items.filter(it => words.every(wd => norm(it.label + ' ' + it.kind).includes(wd)));
      sel = clamp(sel, 0, Math.max(0, shown.length - 1));
      list.innerHTML = '';
      if (!shown.length) { const li = document.createElement('li'); li.className = 'empty'; li.textContent = t('No results'); list.appendChild(li); return; }
      shown.forEach((it, i) => {
        const li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.setAttribute('aria-selected', i === sel);
        li.innerHTML = `<i>${it.icon}</i><span></span><small>${it.kind}</small>`;
        li.querySelector('span').textContent = it.label;
        li.addEventListener('mousemove', () => { if (sel !== i) { sel = i; mark(); } });
        li.addEventListener('click', () => go(it));
        list.appendChild(li);
      });
    }
    const mark = () => $$('li', list).forEach((li, i) => { li.setAttribute('aria-selected', i === sel); if (i === sel) li.scrollIntoView({ block: 'nearest' }); });
    function open() { items = build(); input.value = ''; sel = 0; render(); dlg.showModal(); input.focus(); }
    function go(it) {
      dlg.close();
      if (it.run) it.run();
      else if (it.href.startsWith('#')) { const el = $(it.href); if (el) el.scrollIntoView({ behavior: RM ? 'auto' : 'smooth' }); }
      else if (it.blank) window.open(it.href, '_blank', 'noopener');
      else if (it.href.startsWith('mailto:')) location.href = it.href;
      else navigate(it.href, it.label);
    }
    input.addEventListener('input', () => { sel = 0; render(); });
    input.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { e.preventDefault(); sel = Math.min(shown.length - 1, sel + 1); mark(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(0, sel - 1); mark(); }
      else if (e.key === 'Enter' && shown[sel]) { e.preventDefault(); go(shown[sel]); }
    });
    dlg.addEventListener('click', e => { if (e.target === dlg) dlg.close(); });
    $$('.cmdk-open').forEach(b => b.addEventListener('click', open));
    addEventListener('keydown', e => {
      const typing = /INPUT|TEXTAREA|SELECT/.test((document.activeElement || {}).tagName || '');
      if ((e.key.toLowerCase() === 'k' && (e.metaKey || e.ctrlKey)) || (e.key === '/' && !typing)) {
        e.preventDefault();
        if (dlg.open) dlg.close(); else open();
      }
    });
  }

  /* =====================================================================
     Inicio
     ===================================================================== */
  function init() {
    const y = $('#year');
    if (y) y.textContent = new Date().getFullYear();
    splitName();
    chrome();
    counters();
    hero();
    portfolioLab();
    bsLab();
    kellyLab();
    volSurface();
    glyphs();
    ctaCurves();
    commandPalette();
    requestAnimationFrame(frame);
    // Sin pantalla de arranque: la cabecera se revela en el primer fotograma
    requestAnimationFrame(() => { root.classList.add('ready'); reveals(); });
  }
  // El catálogo de idiomas se ejecuta después de este script: se espera al DOM completo
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
