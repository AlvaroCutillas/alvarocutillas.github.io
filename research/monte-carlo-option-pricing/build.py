"""Assemble the standalone Monte Carlo study guide with offline figures and MathML."""
from pathlib import Path
import html
import json
import re
from bs4 import BeautifulSoup
from mathml import math

ROOT = Path(__file__).parent
OUT = ROOT.parent.parent / 'projects' / 'monte-carlo-option-pricing.html'
content = '\n'.join(p.read_text(encoding='utf-8') for p in sorted(ROOT.glob('content-*.html')))
data = json.loads((ROOT / 'computed.json').read_text(encoding='utf-8'))
figures = json.loads((ROOT / 'figures.json').read_text(encoding='utf-8'))
figure_order = re.findall(r'{{figure:(\w+)}}', content)
assert len(figure_order) == len(set(figure_order)) == 16
for number, name in enumerate(figure_order, 1):
    figure = figures[name].replace("'DejaVu Sans'", "'DejaVu Sans', Arial, sans-serif")
    figure = re.sub(r'Figure \d{2}', f'Figure {number:02d}', figure)
    content = content.replace('{{figure:' + name + '}}', figure)

def table(caption, headers, rows):
    head = ''.join('<th scope="col">' + h + '</th>' for h in headers)
    body = ''.join('<tr>' + ''.join(
        ('<th scope="row">' if i == 0 else '<td class="num">') + str(cell) +
        ('</th>' if i == 0 else '</td>') for i, cell in enumerate(row)
    ) + '</tr>' for row in rows)
    return '<div class="table-wrap"><table><caption>' + caption + '</caption><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table></div>'

f = lambda x: f'{x:.6f}'
rows = [[x['method'], f(x['value']), f(x['se']), f(x['absolute_error']),
         f"{x['units']:,}", f"{x['pilot_evaluations']:,}"] for x in data['example_methods']]
content = content.replace('{{table:methods}}', table(
    'One-year European call · 100,000 production payoff evaluations · NumPy seeds: 1701 pilot, 1702 production · exact value 10.450584',
    ['Estimator', 'Price', 'Standard error', 'Absolute error', 'Independent units', 'Additional pilot work'], rows))

x = data['asian'][0]
rows = [
    ['Arithmetic · plain', f(x['plain']['value']), f(x['plain']['se']), '40,000', '0'],
    ['Arithmetic · geometric control', f(x['control']['value']), f(x['control']['se']), '40,000', '40,000'],
    ['Geometric · analytical', f(x['geometric_exact']), 'Exact', '—', '—']
]
content = content.replace('{{table:asian}}', table(
    'Twelve equally spaced fixings, excluding the initial spot · independent 40,000-path pilot and 40,000-path production sample · seed 1008',
    ['Contract / estimator', 'Price', 'Standard error', 'Production paths', 'Additional pilot paths'], rows))

rows = [[str(x['steps']), f(x['discrete']['value']), f(x['discrete']['se']),
         f(x['bridge']['value']), f(x['bridge']['se'])] for x in data['barrier']['rows']]
content = content.replace('{{table:barrier}}', table(
    'Up-and-out call · upper barrier 130, no rebate · 60,000 coupled paths per mesh · seed 1009 · continuous reference ' + f(data['barrier']['reference']),
    ['Intervals', 'Node-only value', 'Node-only SE', 'Bridge-weighted value', 'Bridge SE'], rows))

rows = [[str(x['degree']), f(x['training_value']), f(x['test']['value']), f(x['test']['se']),
         f(x['test']['value'] - 1.96*x['test']['se']) + ' – ' + f(x['test']['value'] + 1.96*x['test']['se'])]
        for x in data['lsm']['rows']]
content = content.replace('{{table:lsm}}', table(
    'Bermudan put · 50 exercise dates · 25,000 training paths / 50,000 independent evaluation paths · seeds 1012 / 1013 · 1,600-step American CRR reference ' + f(data['lsm']['american_crr']),
    ['Polynomial degree', 'In-sample value', 'Held-out policy value', 'Held-out SE', 'Pointwise 95% policy interval'], rows))

content = content.replace('{{interactive}}', (ROOT / 'notebook.html').read_text(encoding='utf-8'))
sections = re.findall(r'<section id="([^"]+)" data-title="([^"]+)"', content)
assert len(sections) == 28
toc = []
groups = [('foundations', 'Part I', 'Foundations', 1, 10),
          ('methods', 'Part II', 'Methods &amp; applications', 11, 21),
          ('practice', 'Part III', 'Practice &amp; references', 22, 28)]
for group, part, heading, start, end in groups:
    toc.append(f'<div class="toc-column" aria-labelledby="toc-{group}-title"><div class="toc-part">{part}</div><h2 id="toc-{group}-title">{heading}</h2>')
    ranges = [(22, 25, 'Practice'), (26, 28, 'Appendix and further reading')] if group == 'practice' else [(start, end, None)]
    for first, last, subheading in ranges:
        if subheading:
            toc.append(f'<div class="toc-subheading">{subheading}</div>')
        toc.append(f'<ol class="toc-chapters" start="{first}">')
        for i in range(first, last + 1):
            key, title = sections[i - 1]
            toc.append(f'<li><a href="#{key}"><span class="toc-number" aria-hidden="true">{i:02d}</span><span>{title}</span></a></li>')
        toc.append('</ol>')
    toc.append('</div>')

equations = [0]
def display(match):
    equations[0] += 1
    expression = html.unescape(match[1].strip())
    return '<div class="eq"><div class="eq-scroll">' + math(expression, True) + '</div><span class="eq-number">(' + str(equations[0]).zfill(2) + ')</span></div>'

content = re.sub(r'\\\[(.*?)\\\]', display, content, flags=re.S)
content = re.sub(r'\\\((.*?)\\\)', lambda m: math(html.unescape(m[1].strip())), content, flags=re.S)
assert not re.search(r'{{.*?}}', content)
css = '\n'.join((ROOT / name).read_text(encoding='utf-8')
                for name in ['base.css', 'enhancements.css', 'chart-coordinates.css', 'project.css'])
js = '\n'.join((ROOT / name).read_text(encoding='utf-8')
               for name in ['chart-coordinates.js', 'notebook.js'])

hero_svg = '''<svg viewBox="0 0 350 205" role="img" aria-labelledby="hero-plot-title"><title id="hero-plot-title">Illustration of simulated scenarios and an average approaching a model value.</title><g stroke="#25312a" stroke-width="1"><path d="M20 155H330M20 115H330M20 75H330M20 35H330"/></g><g fill="none" stroke-width="1.3" opacity=".5"><path d="M20 96L44 87L68 100L92 79L116 86L140 65L164 77L188 55L212 74L236 46L260 52L284 36L308 51L330 29" stroke="#a7bdb3"/><path d="M20 96L44 112L68 107L92 124L116 110L140 132L164 117L188 128L212 123L236 148L260 132L284 140L308 137L330 157" stroke="#a7bdb3"/><path d="M20 96L44 95L68 81L92 105L116 91L140 96L164 110L188 99L212 112L236 95L260 104L284 92L308 89L330 96" stroke="#d3ad84"/><path d="M20 96L44 80L68 91L92 98L116 75L140 88L164 70L188 90L212 86L236 94L260 82L284 88L308 82L330 90" stroke="#778e84"/></g><path d="M20 76C75 77 104 85 155 88S253 91 330 92L330 101C253 102 208 101 155 105S75 118 20 121Z" fill="#a7bdb3" opacity=".09"/><path d="M20 88C46 69 64 119 87 97S117 92 144 96S188 99 216 95S277 97 330 96" fill="none" stroke="#e4ece7" stroke-width="2.2"/><path d="M20 96H330" stroke="#d3ad84" stroke-width="1" stroke-dasharray="5 5"/><circle cx="330" cy="96" r="3" fill="#e4ece7"/><g fill="#829789" font-size="9" font-family="system-ui, sans-serif"><text x="20" y="184">SIMULATED SCENARIOS</text><text x="242" y="184">EXPECTED VALUE</text></g></svg>'''
page = '''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="An extensive Monte Carlo option pricing study guide: risk-neutral simulation, statistical uncertainty, variance reduction, quasi-Monte Carlo, Asian and barrier options, Greeks and American least-squares Monte Carlo, with computed figures and an interactive laboratory.">
<meta name="theme-color" content="#050505">
<title>Monte Carlo Option Pricing · Quant Basics — Álvaro Cutillas</title>
<style>''' + css + '''</style></head><body>
<a class="skip" href="#content">Skip to notes</a>
<nav aria-label="Primary navigation"><div class="wrap nav-inner"><a class="brand" href="https://alvarocutillas.github.io/">Álvaro Cutillas</a><div class="nav-links"><a href="../index.html#quant-basics">Quant Basics ↗</a><a class="lab-link" href="black-scholes-basics.html">Black–Scholes ↗</a><button class="print-button" type="button">Print notes</button></div></div><div class="reading-progress" aria-hidden="true"></div></nav>
<main id="content">
<header class="hero"><div class="wrap"><div class="hero-grid"><div><div class="eyebrow">Quant Basics 02 / Derivatives / Simulation &amp; estimation</div><h1>Monte Carlo<br><span>Option Pricing</span></h1><p class="lede">From risk-neutral expectations to simulated cash flows. A complete set of notes on pricing, statistical uncertainty and efficient estimation.</p><p class="context">Mathematical foundations, practical intuition and computed experiments in one reading path. Learn how to estimate a value, measure its uncertainty and improve the calculation.</p><div class="tag-row"><span class="tag">Risk-neutral simulation</span><span class="tag">Variance reduction</span><span class="tag">Path-dependent options</span><span class="tag">Greeks</span><span class="tag">Optimal stopping</span></div></div><div class="hero-visual"><div class="visual-head"><span>Foundations / 02</span><span>Monte Carlo valuation</span></div>''' + hero_svg + '''<div class="visual-foot"><div>Scenarios<b>Simulate cash flows</b></div><div>Estimation<b>Measure uncertainty</b></div></div></div></div><div class="hero-stats" aria-label="Study guide contents"><div class="stat"><strong>28</strong><small>Chapters &amp; appendices</small></div></div></div></header>
<div class="wrap document"><aside class="toc" aria-label="On this page"><div class="toc-title">Contents</div><div class="toc-columns">''' + ''.join(toc) + '''</div></aside><article class="article" aria-label="Monte Carlo option pricing study notes">''' + content + '''</article></div>
</main><footer class="wrap"><span>Álvaro Cutillas · Quantitative Finance Portfolio</span><span>Quant Basics 02 · Monte Carlo Option Pricing</span></footer>
<script>''' + js + '''</script></body></html>'''
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(page, encoding='utf-8')
soup = BeautifulSoup(page, 'html.parser')
math_count = len(soup.find_all('math'))
for element in soup(['script', 'style', 'svg', 'math']):
    element.decompose()
report = {'output': str(OUT.resolve()), 'bytes': OUT.stat().st_size,
          'prose_words': len(soup.get_text(' ', strip=True).split()),
          'display_equations': equations[0], 'math_expressions': math_count,
          'sections': len(sections), 'figures': len(figure_order)}
(ROOT / 'build-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))

# Portfolio EN/ES localization: retain the selector when regenerating the study.
import sys as _localization_sys
_localization_sys.path.insert(0,str(ROOT.parent/'localization'))
from localize import localize_page as _localize_page
_localize_page(OUT)
