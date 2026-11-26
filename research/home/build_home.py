"""Genera index.html (home del portfolio) a partir de la home anterior (git HEAD)
y de los resultados reales de research/portfolio-optimization (frontera eficiente).

Uso:  python research/home/build_home.py   (desde la raíz del repo)
Contrato conservado: <a class="project-card" href="projects/portfolio-optimization.html">
con el bloque <!-- portfolio-optimization-results --> que reescribe analysis/page.py.
"""
import csv, re, subprocess, sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[2]
SRC = SITE / 'research' / 'home' / 'source-index.html'  # copia de la home original (fuente de contenido)
if not SRC.exists():
    SRC.write_text(subprocess.run(['git', 'show', 'HEAD:index.html'], cwd=SITE, capture_output=True,
                                  text=True, encoding='utf-8').stdout, encoding='utf-8')
OLD = SRC.read_text(encoding='utf-8')
assert 'project-card' in OLD, 'No se encontró la home original'


# ---------- 1. Extraer tarjetas existentes (contenido real, SVG miniaturas) ----------
def cards(section_id):
    sec = OLD[OLD.index(f'id="{section_id}"'):]
    sec = sec[:sec.index('</section>')]
    out = []
    for m in re.finditer(r'<a class="project-card" href="([^"]+)">(.*?)</a>\s*(?=<a class="project-card"|</div>)', sec, re.S):
        href, body = m.group(1), m.group(2)

        def g(p):
            r = re.search(p, body, re.S)
            return r[1].strip() if r else ''
        svg = re.search(r'<svg.*?</svg>', body, re.S)[0]
        svg = re.sub(r'<desc>.*?</desc>', '', svg, flags=re.S)
        svg = re.sub(r'\s+', ' ', svg)
        out.append(dict(
            href=href, svg=svg, label=g(r'class="visual-label">(.*?)<'),
            kind=g(r'class="project-kind">(.*?)<'), index=g(r'class="index">(.*?)<'),
            title=g(r'<h3>(.*?)</h3>'), text=g(r'<p>(.*?)</p>'),
            tags=re.findall(r'class="tag">(.*?)<', body),
            context=g(r'class="metric-context">(.*?)<'),
            metrics=re.findall(r'<div class="metric"><b>(.*?)</b><span>(.*?)</span></div>', body),
            cta=g(r'class="project-link">(.*?)\s*<span')))
    return out


featured, basics = cards('projects'), cards('quant-basics')
assert len(featured) == 3 and len(basics) == 8, (len(featured), len(basics))

# ---------- 2. Figura hero con datos reales ----------
R = SITE / 'research' / 'portfolio-optimization' / 'results'
front = [(float(r['volatility']), float(r['return'])) for r in csv.DictReader(open(R / 'efficient_frontier.csv', encoding='utf-8'))]
assets = [(r['ticker'], float(r['annual_volatility']), float(r['annual_arithmetic_mean']))
          for r in csv.DictReader(open(R / 'descriptive_stats.csv', encoding='utf-8'))]
W, H, L, Rr, T, B = 640, 470, 58, 18, 18, 52
x0, x1, y0, y1 = 0.0, 0.24, -0.06, 0.14


def X(v): return L + (v - x0) / (x1 - x0) * (W - L - Rr)
def Y(v): return T + (y1 - v) / (y1 - y0) * (H - T - B)


g = []
for t in (0.0, 0.05, 0.10, 0.15, 0.20):
    g.append(f'<line class="g" x1="{X(t):.1f}" y1="{T}" x2="{X(t):.1f}" y2="{H-B}"/><text class="tk" x="{X(t):.1f}" y="{H-B+20}" text-anchor="middle">{t*100:.0f}%</text>')
for t in (-0.05, 0.0, 0.05, 0.10):
    g.append(f'<line class="g" x1="{L}" y1="{Y(t):.1f}" x2="{W-Rr}" y2="{Y(t):.1f}"/><text class="tk" x="{L-10}" y="{Y(t)+4:.1f}" text-anchor="end">{t*100:.0f}%</text>')
curve = 'M' + ' L'.join(f'{X(v):.1f},{Y(r):.1f}' for v, r in front)
area = curve + f' L{X(front[-1][0]):.1f},{H-B} L{X(front[0][0]):.1f},{H-B} Z'
off = {'SPY': (10, -9), 'IWM': (10, 4), 'EFA': (-10, 4), 'EEM': (10, 4), 'AGG': (10, 15), 'TLT': (10, 4),
       'LQD': (12, -5), 'VNQ': (-10, -9), 'GLD': (10, 4), 'DBC': (10, 4)}
pts = []
for t, v, r in assets:
    dx, dy = off[t]
    anchor = 'end' if dx < 0 else 'start'
    pts.append(f'<g class="pt"><circle cx="{X(v):.1f}" cy="{Y(r):.1f}" r="4"/><text x="{X(v)+dx:.1f}" y="{Y(r)+dy:.1f}" text-anchor="{anchor}">{t}</text></g>')
gx, gy = X(front[0][0]), Y(front[0][1])
hero_svg = f'''<svg class="frontier" viewBox="0 0 {W} {H}" role="img" aria-labelledby="fr-t fr-d">
<title id="fr-t">Long-only efficient frontier of ten ETFs</title>
<desc id="fr-d">Annualised volatility against annualised arithmetic mean return for ten ETFs and the long-only efficient frontier solved on the 2010 to 2018 training sample.</desc>
<defs><linearGradient id="fr-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#6cc4ad" stop-opacity=".22"/><stop offset="1" stop-color="#6cc4ad" stop-opacity="0"/></linearGradient></defs>
{''.join(g)}
<path class="area" d="{area}" fill="url(#fr-fill)"/>
<path class="curve" pathLength="1" d="{curve}"/>
{''.join(pts)}
<g class="gmv"><circle cx="{gx:.1f}" cy="{gy:.1f}" r="5.5"/><line x1="{gx:.1f}" y1="{gy+6:.1f}" x2="{gx:.1f}" y2="{gy+38:.1f}" stroke="var(--amber)" stroke-opacity=".5"/><text x="{gx+6:.1f}" y="{gy+48:.1f}">Min. variance</text></g>
<text class="ax" x="{(L+W-Rr)/2:.0f}" y="{H-8}" text-anchor="middle">Annualised volatility</text>
<text class="ax" transform="translate(13 {(T+H-B)/2:.0f}) rotate(-90)" text-anchor="middle">Annualised mean return</text>
</svg>'''


# ---------- 3. Piezas de marcado ----------
def tags(ts):
    return '<div class="tags">' + ''.join(f'<span class="tag">{t}</span>' for t in ts) + '</div>'


def featured_row(c):
    if 'portfolio-optimization' in c['href']:
        met = re.search(r'<!-- portfolio-optimization-results -->.*?<!-- /portfolio-optimization-results -->', OLD, re.S)[0]
    else:
        met = '<div class="metrics">' + ''.join(f'<div class="metric"><b>{b}</b><span>{s}</span></div>' for b, s in c['metrics']) + '</div>'
    return f'''
      <a class="project-card feature" href="{c['href']}">
        <div class="project-visual"><div class="visual-label">{c['label']}</div>{c['svg']}</div>
        <div class="project-body">
          <div class="project-top"><span class="project-kind">{c['kind']}</span><span class="arrow" aria-hidden="true">↗</span></div>
          <h3>{c['title']}</h3>
          <p>{c['text']}</p>
          <div class="project-footer">
            {met}
            <div class="metric-context">{c['context']}</div>
            {tags(c['tags'])}
            <div class="project-link">{c['cta']} <span aria-hidden="true">↗</span></div>
          </div>
        </div>
      </a>'''


def basic_row(c):
    return f'''
      <a class="project-card basic" href="{c['href']}">
        <span class="index">{c['index']}</span>
        <div class="basic-main"><h3>{c['title']}</h3><p>{c['text']}</p></div>
        {tags(c['tags'])}
        <div class="project-visual"><span class="visual-label">{c['label']}</span>{c['svg']}</div>
        <span class="arrow" aria-hidden="true">↗</span>
      </a>'''


CSS = (Path(__file__).parent / 'home.css').read_text(encoding='utf-8')
page = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="Álvaro Cutillas — Quantitative Finance Portfolio" />
  <meta name="theme-color" content="#0b0e0c" />
  <title>Álvaro Cutillas — Quantitative Finance</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;family=IBM+Plex+Mono:wght@400;500&amp;display=swap" rel="stylesheet" />
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

  <section class="hero">
    <div class="hero-copy">
      <h1>Álvaro Cutillas</h1>
      <div class="role">Quantitative Finance · Economics · Python</div>
      <p class="thesis">Quantitative research with explicit assumptions, reproducible code and results that hold up out of sample.</p>
      <div class="quick-links">
        <a class="btn primary" href="#projects">View projects</a>
        <a class="btn" href="assets/Alvaro-Cutillas-CV.pdf" target="_blank" rel="noopener">View CV ↗</a>
      </div>
      <div class="social-links">
        <a href="https://github.com/AlvaroCutillas">GitHub ↗</a>
        <a href="https://www.linkedin.com/in/%C3%A1lvaro-cutillas/">LinkedIn ↗</a>
        <a href="mailto:acutillas.finance@gmail.com">Email ↗</a>
      </div>
    </div>
    <figure class="hero-figure">
      {hero_svg}
      <figcaption><b>Long-only efficient frontier</b> · 10 ETFs · 2010–2018 training sample. Computed in the <span>Portfolio Optimization study</span>.</figcaption>
    </figure>
  </section>

  <section class="projects" id="projects" aria-labelledby="highlighted-projects-title">
    <div class="projects-head">
      <h2 id="highlighted-projects-title">Highlighted Projects</h2>
      <span>Reproducible research · Methods · Evidence</span>
    </div>
    <p class="projects-intro">My most curated work.</p>
    <div class="feature-list">{''.join(featured_row(c) for c in featured)}
    </div>
  </section>

  <section class="projects" id="quant-basics" aria-labelledby="quant-basics-title">
    <div class="projects-head">
      <h2 id="quant-basics-title">Quant Basics</h2>
      <span>Foundations · 8 studies</span>
    </div>
    <p class="projects-intro">Detailed studies on the tools and models behind quantitative finance, combining theory, derivations, computed figures and interactive laboratories.</p>
    <div class="basic-list">{''.join(basic_row(c) for c in basics)}
    </div>
  </section>

  <section class="section" id="about">
    <div class="about-grid">
      <div class="section-label">About</div>
      <div>
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
    </div>
  </section>

  <section class="cta" id="contact">
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
  </section>

  <footer>
    <div>© <span id="year"></span> Álvaro Cutillas</div>
    <span>Quantitative Finance Portfolio</span>
  </footer>

</main>

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
print('index.html', len(page))
