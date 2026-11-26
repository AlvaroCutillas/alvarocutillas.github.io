"""Genera index.html (home del portfolio, mundo visual «working paper»).

Contenido: textos y métricas de research/home/source-index.html (home original, fuente de contenido).
Figuras: calculadas aquí con datos reales (frontera y riqueza walk-forward de research/portfolio-optimization)
o con fórmulas analíticas (Black–Scholes, criterio de Kelly) con parámetros ilustrativos declarados.

Uso:  python research/home/build_home.py   (desde la raíz del repo)
Contrato conservado con research/portfolio-optimization/analysis/page.py y audit.py:
  <a class="project-card" href="projects/portfolio-optimization.html"> (sin enlaces anidados, sin otra
  aparición previa de ese href) con el bloque <!-- portfolio-optimization-results -->.
"""
import csv, math, re, sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[2]
OLD = (SITE / 'research' / 'home' / 'source-index.html').read_text(encoding='utf-8')
R = SITE / 'research' / 'portfolio-optimization' / 'results'


# ---------- 1. Contenido existente ----------
def cards(section_id):
    sec = OLD[OLD.index(f'id="{section_id}"'):]
    sec = sec[:sec.index('</section>')]
    out = []
    for m in re.finditer(r'<a class="project-card" href="([^"]+)">(.*?)</a>\s*(?=<a class="project-card"|</div>)', sec, re.S):
        href, body = m.group(1), m.group(2)

        def g(p):
            r = re.search(p, body, re.S)
            return r[1].strip() if r else ''
        out.append(dict(
            href=href, kind=g(r'class="project-kind">(.*?)<'), index=g(r'class="index">(.*?)<'),
            title=g(r'<h3>(.*?)</h3>'), text=g(r'<p>(.*?)</p>'),
            tags=re.findall(r'class="tag">(.*?)<', body), context=g(r'class="metric-context">(.*?)<'),
            metrics=re.findall(r'<div class="metric"><b>(.*?)</b><span>(.*?)</span></div>', body),
            cta=g(r'class="project-link">(.*?)\s*<span')))
    return out


featured, basics = cards('projects'), cards('quant-basics')
assert len(featured) == 3 and len(basics) == 8, (len(featured), len(basics))
OPT_RESULTS = re.search(r'<!-- portfolio-optimization-results -->.*?<!-- /portfolio-optimization-results -->', OLD, re.S)[0]


# ---------- 2. Utilidades de figura ----------
class Plot:
    def __init__(self, W, H, xr, yr, xt, yt, fx='{:.0f}', fy='{:.0f}', L=52, Rr=16, T=14, B=40):
        self.W, self.H, self.xr, self.yr, self.L, self.Rr, self.T, self.B = W, H, xr, yr, L, Rr, T, B
        self.parts = []
        for t in xt:
            lab = f'<text class="tk" x="{self.x(t):.1f}" y="{H-B+18}" text-anchor="middle">{fx.format(t)}</text>' if fx else ''
            self.parts.append(f'<line class="g" x1="{self.x(t):.1f}" y1="{T}" x2="{self.x(t):.1f}" y2="{H-B}"/>' + lab)
        for t in yt:
            self.parts.append(f'<line class="g" x1="{L}" y1="{self.y(t):.1f}" x2="{W-Rr}" y2="{self.y(t):.1f}"/>'
                              f'<text class="tk" x="{L-8}" y="{self.y(t)+4:.1f}" text-anchor="end">{fy.format(t)}</text>')
        self.parts.append(f'<line class="axis" x1="{L}" y1="{H-B}" x2="{W-Rr}" y2="{H-B}"/>')

    def x(self, v): return self.L + (v - self.xr[0]) / (self.xr[1] - self.xr[0]) * (self.W - self.L - self.Rr)
    def y(self, v): return self.T + (self.yr[1] - v) / (self.yr[1] - self.yr[0]) * (self.H - self.T - self.B)
    def path(self, pts): return 'M' + ' L'.join(f'{self.x(a):.1f},{self.y(b):.1f}' for a, b in pts)
    def add(self, s): self.parts.append(s)

    def svg(self, tid, title, desc):
        return (f'<svg class="fig" viewBox="0 0 {self.W} {self.H}" role="img" aria-labelledby="{tid}-t {tid}-d">'
                f'<title id="{tid}-t">{title}</title><desc id="{tid}-d">{desc}</desc>' + ''.join(self.parts) + '</svg>')


# ---------- 3. Figura 1: frontera eficiente (datos reales) ----------
front = [(float(r['volatility']), float(r['return'])) for r in csv.DictReader(open(R / 'efficient_frontier.csv', encoding='utf-8'))]
assets = [(r['ticker'], float(r['annual_volatility']), float(r['annual_arithmetic_mean']))
          for r in csv.DictReader(open(R / 'descriptive_stats.csv', encoding='utf-8'))]
p = Plot(900, 460, (0, 0.24), (-0.06, 0.14), (0, .05, .10, .15, .20), (-.05, 0, .05, .10), fx='{:.0%}', fy='{:.0%}', L=58, Rr=24)
p.add(f'<path class="curve accent" pathLength="1" d="{p.path(front)}"/>')
off = {'SPY': (10, -8, 'start'), 'IWM': (10, 4, 'start'), 'EFA': (-10, 4, 'end'), 'EEM': (10, 4, 'start'), 'AGG': (10, 16, 'start'),
       'TLT': (10, 4, 'start'), 'LQD': (12, -6, 'start'), 'VNQ': (-10, -8, 'end'), 'GLD': (10, 4, 'start'), 'DBC': (10, 4, 'start')}
for t, v, r in assets:
    dx, dy_, a = off[t]
    p.add(f'<g class="pt"><circle cx="{p.x(v):.1f}" cy="{p.y(r):.1f}" r="3.6"/><text x="{p.x(v)+dx:.1f}" y="{p.y(r)+dy_:.1f}" text-anchor="{a}">{t}</text></g>')
gx, gy = p.x(front[0][0]), p.y(front[0][1])
p.add(f'<g class="gmv"><circle cx="{gx:.1f}" cy="{gy:.1f}" r="5.5"/><line x1="{gx:.1f}" y1="{gy+7:.1f}" x2="{gx:.1f}" y2="{gy+40:.1f}"/>'
      f'<text x="{gx+6:.1f}" y="{gy+52:.1f}">Min. variance</text></g>')
p.add(f'<text class="ax" x="{(p.L+p.W-p.Rr)/2:.0f}" y="{p.H-6}" text-anchor="middle">Annualised volatility</text>')
p.add(f'<text class="ax" transform="translate(12 {(p.T+p.H-p.B)/2:.0f}) rotate(-90)" text-anchor="middle">Annualised mean return</text>')
FIG1 = p.svg('f1', 'Long-only efficient frontier of ten ETFs',
             'Annualised volatility against annualised arithmetic mean return for ten ETFs and the long-only efficient frontier solved on the 2010 to 2018 training sample.')
minv = front[0]

# ---------- 4. Figura 2: riqueza neta walk-forward (datos reales) ----------
rows = list(csv.DictReader(open(R / 'walk_forward_daily_net.csv', encoding='utf-8')))
series = {'Equal weight': 'ink', 'Max Sharpe · sample': 'muted', 'Max Sharpe · LW capped': 'accent'}
wealth = {k: [] for k in series}
w = {k: 1.0 for k in series}
for i, r in enumerate(rows):
    for k in series:
        w[k] *= 1 + float(r[k])
        if i % 4 == 0 or i == len(rows) - 1:
            wealth[k].append((i, w[k]))
n = len(rows)
p2 = Plot(560, 330, (0, n), (0.8, 3.0), (), (1, 2, 3), fx='', fy='{:.0f}×', L=40, Rr=150, B=44)
for t in (0, .25, .5, .75, 1.0):  # etiquetas de año reales a partir de las fechas
    i = min(int(t * (n - 1)), n - 1)
    p2.add(f'<text class="tk" x="{p2.x(t*n):.1f}" y="{p2.H-p2.B+18}" text-anchor="middle">{rows[i]["date"][:4]}</text>')
dy = {'Equal weight': -8, 'Max Sharpe · sample': 12, 'Max Sharpe · LW capped': 4}
for k, c in series.items():
    p2.add(f'<path class="curve {c}" pathLength="1" d="{p2.path(wealth[k])}"/>')
    ex, ey = wealth[k][-1]
    p2.add(f'<text class="lbl {c}" x="{p2.x(ex)+8:.1f}" y="{p2.y(ey)+dy[k]:.1f}">{k} {ey:.2f}×</text>')
FIG2 = p2.svg('f2', 'Cumulative net wealth of three portfolio rules',
              'Walk-forward cumulative net wealth of one unit invested in an equal-weight portfolio, an uncapped sample maximum-Sharpe portfolio and a Ledoit–Wolf, 25% capped maximum-Sharpe portfolio.')


# ---------- 5. Figura 3: valor de una call europea (fórmula analítica, parámetros ilustrativos) ----------
def ncdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def call(S, K, T, r, s):
    d1 = (math.log(S / K) + (r + s * s / 2) * T) / (s * math.sqrt(T))
    return S * ncdf(d1) - K * math.exp(-r * T) * ncdf(d1 - s * math.sqrt(T))


Ss = [60 + i * 0.5 for i in range(0, 161)]
p3 = Plot(560, 330, (60, 140), (0, 45), (60, 80, 100, 120, 140), (0, 10, 20, 30, 40), L=40, Rr=70, B=44)
p3.add(f'<path class="curve muted dash" pathLength="1" d="{p3.path([(s, max(s-100, 0)) for s in Ss])}"/>')
p3.add(f'<path class="curve ink" pathLength="1" d="{p3.path([(s, call(s, 100, 1.0, .03, .2)) for s in Ss])}"/>')
p3.add(f'<path class="curve accent" pathLength="1" d="{p3.path([(s, call(s, 100, .25, .03, .2)) for s in Ss])}"/>')
p3.add(f'<text class="lbl muted" x="{p3.x(140)+8:.1f}" y="{p3.y(call(140,100,1.0,.03,.2))+36:.1f}">Payoff</text>')
p3.add(f'<text class="lbl ink" x="{p3.x(140)+8:.1f}" y="{p3.y(call(140,100,1.0,.03,.2))+4:.1f}">T = 1.0</text>')
p3.add(f'<text class="lbl accent" x="{p3.x(140)+8:.1f}" y="{p3.y(call(140,100,1.0,.03,.2))+20:.1f}">T = 0.25</text>')
p3.add(f'<text class="ax" x="{(p3.L+p3.W-p3.Rr)/2:.0f}" y="{p3.H-4}" text-anchor="middle">Spot price</text>')
FIG3 = p3.svg('f3', 'European call value against spot price',
              'Black–Scholes value of a European call with strike 100, rate 3% and volatility 20% for one year and three months to maturity, against the payoff at expiry.')

# ---------- 6. Figura 4: crecimiento logarítmico esperado de Kelly (p = 0,55; apuesta a la par) ----------
pw = 0.55


def g_(f): return pw * math.log(1 + f) + (1 - pw) * math.log(1 - f)


fs = [i / 400 for i in range(0, 381)]
fk = 2 * pw - 1
fz = next(f for f in fs[1:] if g_(f) < 0)
p4 = Plot(560, 330, (0, 0.95), (-0.04, 0.014), (0, .2, .4, .6, .8), (-.03, -.02, -.01, 0), fx='{:.1f}', fy='{:.0%}', L=46, Rr=24, B=44)
p4.add(f'<path class="curve accent" pathLength="1" d="{p4.path([(f, g_(f)) for f in fs])}"/>')
p4.add(f'<g class="gmv"><circle cx="{p4.x(fk):.1f}" cy="{p4.y(g_(fk)):.1f}" r="5"/><text x="{p4.x(fk)+4:.1f}" y="{p4.y(g_(fk))-12:.1f}">Full Kelly</text></g>')
p4.add(f'<g class="pt"><circle cx="{p4.x(fz):.1f}" cy="{p4.y(0):.1f}" r="3.6"/><text x="{p4.x(fz)+8:.1f}" y="{p4.y(0)+18:.1f}">Growth turns negative</text></g>')
p4.add(f'<text class="ax" x="{(p4.L+p4.W-p4.Rr)/2:.0f}" y="{p4.H-4}" text-anchor="middle">Staked fraction</text>')
FIG4 = p4.svg('f4', 'Expected log-growth against the staked fraction',
              'Expected logarithmic growth per bet for a 55% win probability at even odds, peaking at the full Kelly fraction and turning negative at about twice that fraction.')

FIGS = [
    (FIG2, 'Cumulative net wealth of one unit invested, walk-forward, after trading costs.'),
    (FIG3, 'European call value against spot, strike 100. Illustrative parameters: r = 3%, σ = 20%.'),
    (FIG4, 'Expected log-growth per bet against the staked fraction. Illustrative: p = 0.55, even odds.'),
]


# ---------- 7. Marcado ----------
def tags(ts): return '<span class="tags">' + ''.join(f'<span class="tag">{t}</span>' for t in ts) + '</span>'


def metrics_of(c):
    if 'portfolio-optimization' in c['href']:
        return OPT_RESULTS
    return '<div class="metrics">' + ''.join(f'<div class="metric"><b>{b}</b><span>{s}</span></div>' for b, s in c['metrics']) + '</div>'


def feature(c, fig):
    svg, cap = fig
    return f'''
      <a class="project-card" href="{c['href']}">
        <div class="project-body">
          <span class="project-kind">{c['kind']}</span>
          <h3>{c['title']}</h3>
          <p>{c['text']}</p>
          {metrics_of(c)}
          <div class="metric-context">{c['context']}</div>
          {tags(c['tags'])}
          <span class="project-link">{c['cta']} <span aria-hidden="true">↗</span></span>
        </div>
        <figure class="project-figure">{svg}<figcaption>{cap}</figcaption></figure>
      </a>'''


def basic(c):
    return f'''
      <a class="project-card" href="{c['href']}">
        <span class="index">{c['index']}</span>
        <span class="basic-main"><h3>{c['title']}</h3><p>{c['text']}</p></span>
        {tags(c['tags'])}
        <span class="arrow" aria-hidden="true">↗</span>
      </a>'''


CSS = (Path(__file__).parent / 'home.css').read_text(encoding='utf-8')
mv, mr = minv
page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="Álvaro Cutillas — Quantitative Finance Portfolio" />
  <meta name="theme-color" content="#f3eee2" />
  <title>Álvaro Cutillas — Quantitative Finance</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&amp;family=IBM+Plex+Mono:wght@400;500&amp;display=swap" rel="stylesheet" />
  <style>{CSS}</style>
</head>
<body>

<a class="skip" href="#projects">Skip to projects</a>
<nav>
  <div class="wrap nav-inner">
    <a class="brand" href="index.html">Álvaro Cutillas</a>
    <div class="nav-links">
      <a href="#projects">Projects</a>
      <a href="#about">About</a>
      <a href="#contact">Contact</a>
    </div>
  </div>
</nav>

<main class="wrap">

  <header class="hero">
    <h1>Álvaro Cutillas</h1>
    <div class="hero-meta">
      <div>
        <p class="role">Quantitative Finance · Economics · Python</p>
        <p class="social-links"><a href="https://github.com/AlvaroCutillas">GitHub ↗</a> <a href="https://www.linkedin.com/in/%C3%A1lvaro-cutillas/">LinkedIn ↗</a> <a href="mailto:acutillas.finance@gmail.com">Email ↗</a></p>
      </div>
      <p class="thesis">Quantitative research with explicit assumptions, reproducible code and results that hold up out of sample.</p>
    </div>
  </header>

  <figure class="lead-figure">
    {FIG1}
    <figcaption>
      <span class="cap"><b>Figure 1.</b> Long-only efficient frontier of ten ETFs, solved on the 2010–2018 training sample. Dots are individual assets.</span>
      <span class="note">The minimum-variance portfolio sits at {mv:.1%} volatility and {mr:.1%} mean return.</span>
    </figcaption>
  </figure>

  <section class="projects" id="projects" aria-labelledby="highlighted-projects-title">
    <div class="projects-head">
      <h2 id="highlighted-projects-title">Highlighted Projects</h2>
      <span>Reproducible research · Methods · Evidence</span>
    </div>
    <p class="projects-intro">My most curated work.</p>
    <div class="feature-list">{''.join(feature(c, FIGS[i]) for i, c in enumerate(featured))}
    </div>
  </section>

  <section class="projects" id="quant-basics" aria-labelledby="quant-basics-title">
    <div class="projects-head">
      <h2 id="quant-basics-title">Quant Basics</h2>
      <span>Foundations · 8 studies</span>
    </div>
    <p class="projects-intro">Detailed studies on the tools and models behind quantitative finance, combining theory, derivations, computed figures and interactive laboratories.</p>
    <div class="basic-list">{''.join(basic(c) for c in basics)}
    </div>
  </section>

  <section class="section" id="about">
    <div class="projects-head"><h2>About</h2></div>
    <div class="about-grid">
      <p class="about-text">
        I am building toward a career in <strong>quantitative finance</strong>,
        combining economics, programming, statistics and mathematical modelling.
        I care about clear assumptions, reproducible analysis and results that can be defended.
      </p>
      <div class="details">
        <div class="detail"><small>Focus</small><div>Derivatives, risk, portfolio construction, systematic research</div></div>
        <div class="detail"><small>Tools</small><div>Python, NumPy, Pandas, SciPy, Matplotlib, Git</div></div>
        <div class="detail"><small>Based in</small><div>Madrid, Spain</div></div>
      </div>
    </div>
  </section>

</main>

<section class="cta" id="contact">
  <div class="wrap cta-inner">
    <div>
      <h2>See the work. Then let’s talk.</h2>
      <p>
        If you are hiring for quantitative finance, risk or research roles,
        I can walk you through the assumptions, implementation and decisions behind every project here.
      </p>
    </div>
    <div class="cta-actions">
      <a class="btn primary" href="mailto:acutillas.finance@gmail.com">Contact me</a>
      <a class="btn" href="assets/Alvaro-Cutillas-CV.pdf" target="_blank" rel="noopener">View CV ↗</a>
    </div>
  </div>
  <footer class="wrap">
    <div>© <span id="year"></span> Álvaro Cutillas</div>
    <span>Quantitative Finance Portfolio</span>
  </footer>
</section>

<script>
  document.getElementById("year").textContent = new Date().getFullYear();
</script>
</body>
</html>
'''
(SITE / 'index.html').write_text(page, encoding='utf-8')
sys.path.insert(0, str(SITE / 'research' / 'localization'))
from localize import localize_page
localize_page(SITE / 'index.html')
print('index.html', len(page), '| Kelly f*=%.2f, g=0 en f=%.2f' % (fk, fz))
