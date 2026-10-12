from pathlib import Path
import html,json,re
from bs4 import BeautifulSoup
from mathml import math
ROOT=Path(__file__).parent
OUT=ROOT.parent.parent/'projects'/'implied-volatility-surface.html'
content='\n'.join(p.read_text(encoding='utf-8') for p in sorted(ROOT.glob('content-*.html')))
data=json.loads((ROOT/'computed.json').read_text(encoding='utf-8'))
figs=json.loads((ROOT/'figures.json').read_text(encoding='utf-8'))
order=re.findall(r'{{figure:(\w+)}}',content)
assert len(order)==len(set(order))==19
for number,name in enumerate(order,1):
    fig=figs[name].replace("'DejaVu Sans'","'DejaVu Sans', Arial, sans-serif")
    fig=re.sub(r'Figure \d{2}',f'Figure {number:02d}',fig)
    content=content.replace('{{figure:'+name+'}}',fig)
def table(caption,head,rows):
    body=''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td class="num">')+str(cell)+('</th>' if i==0 else '</td>') for i,cell in enumerate(row))+'</tr>' for row in rows)
    return '<div class="table-wrap"><table><caption>'+caption+'</caption><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in head)+'</tr></thead><tbody>'+body+'</tbody></table></div>'
pct=lambda x:f'{100*x:.6f}%'
rows=[[f"{r['T']:g}",f"{r['k']:+.2f}",f"{r['K']:.6f}",pct(r['sigma']),f"{r['w']:.8f}",f"{r['call']:.6f}",f"{r['put']:.6f}",pct(r['iv'])] for r in data['rows']]
content=content.replace('{{table:chain}}',table('Synthetic European chain · spot 100 · continuous rate 3% · yield 1% · exact year fractions',['T (years)','k','Strike','Surface IV','Total variance','Call','Put','Recovered IV'],rows))
fit=data['calibration']
rows=[[name,f'{value:.9f}'] for name,value in zip(['a','b','rho','m','s'],fit['params'])]
content=content.replace('{{table:fit}}',table('Raw SVI fit · equal total-variance weights · T = 1 year · four optimizer starts',['Parameter','Fitted value'],rows))
rows=[[f"{k:+.2f}",'Fit' if train else 'Withheld',pct(v),pct(pred),f'{10000*(pred-v):+.5f}'] for k,train,v,pred in zip(fit['k'],fit['train'],fit['observed'],fit['pred'])]
content=content.replace('{{table:residuals}}',table('Residuals use fitted minus observed IV · one IV basis point = 0.0001',['k','Role','Observed IV','Fitted IV','Residual (IV bps)'],rows))
b=data['bounds']
rows=[['All positive maturities',f"{b['global_wing']:.6f}",'&lt; 4',f"{b['global_curvature']:.6f}",'≤ 4'],
      ['Maturities up to 3 years',f"{b['horizon_wing']:.6f}",'&lt; 4',f"{b['horizon_curvature']:.6f}",'≤ 4']]
content=content.replace('{{table:bounds}}',table('Reference shape phi(theta) = eta / (1 + theta) · sufficient interval maxima',['Domain','Wing expression','Required','Curvature expression','Required'],rows))
content=content.replace('{{interactive}}',(ROOT/'notebook.html').read_text(encoding='utf-8'))
sections=re.findall(r'<section id="([^"]+)" data-title="([^"]+)"',content)
assert len(sections)==30
toc=[]
groups=[('foundations','Part I','Prices &amp; coordinates',[(1,5,'Valuation and inversion'),(6,10,'Smile geometry and data')]),
        ('construction','Part II','Consistency &amp; calibration',[(11,15,'Static arbitrage and representations'),(16,20,'Fitting, validation and tails')]),
        ('practice','Part III','Dynamics &amp; practice',[(21,25,'Models and risk management'),(26,27,'Numerical study'),(28,30,'Appendix and further reading')])]
for key,part,title,ranges in groups:
    toc.append(f'<div class="toc-column" aria-labelledby="toc-{key}-title"><div class="toc-part">{part}</div><h2 id="toc-{key}-title">{title}</h2>')
    for first,last,subheading in ranges:
        toc.append(f'<div class="toc-subheading">{subheading}</div><ol class="toc-chapters" start="{first}">')
        for i in range(first,last+1):
            anchor,title=sections[i-1]
            toc.append(f'<li><a href="#{anchor}"><span class="toc-number" aria-hidden="true">{i:02d}</span><span>{title}</span></a></li>')
        toc.append('</ol>')
    toc.append('</div>')
eq=[0]
def display(m):
    eq[0]+=1
    return '<div class="eq"><div class="eq-scroll">'+math(html.unescape(m[1].strip()),True)+'</div><span class="eq-number">('+str(eq[0]).zfill(2)+')</span></div>'
content=re.sub(r'\\\[(.*?)\\\]',display,content,flags=re.S)
content=re.sub(r'\\\((.*?)\\\)',lambda m:math(html.unescape(m[1].strip())),content,flags=re.S)
assert not re.search(r'{{.*?}}',content)
css='\n'.join((ROOT/name).read_text(encoding='utf-8') for name in ['base.css','enhancements.css','chart-coordinates.css','project.css'])
js='\n'.join((ROOT/name).read_text(encoding='utf-8') for name in ['chart-coordinates.js','notebook.js'])
hero='''<svg viewBox="0 0 350 205" role="img" aria-labelledby="hero-plot-title"><title id="hero-plot-title">Schematic volatility smiles at different maturities; decorative illustration.</title><g stroke="#25312a" stroke-width="1"><path d="M25 160H330M25 120H330M25 80H330M25 40H330"/></g><g fill="none" stroke-width="2"><path d="M25 45C70 62 110 110 165 129S269 129 330 112" stroke="#a7bdb3"/><path d="M25 74C78 88 115 119 165 132S272 135 330 127" stroke="#91a9bd"/><path d="M25 101C85 107 121 127 165 137S270 142 330 139" stroke="#d3ad84"/></g><path d="M170 40V160" stroke="#56685e" stroke-dasharray="3 5"/><g fill="#829789" font-size="9" font-family="system-ui,sans-serif"><text x="25" y="191">LOW STRIKE</text><text x="156" y="180">ATM</text><text x="267" y="191">HIGH STRIKE</text></g></svg>'''
page='''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="An extensive implied volatility surface study guide: Black inversion, smiles, total variance, market conventions, static arbitrage, SVI and SSVI calibration, density, local volatility and hedge risk, with computed figures and an offline interactive laboratory."><meta name="theme-color" content="#050505"><title>Implied Volatility Surface · Quant Basics — Álvaro Cutillas</title><style>'''+css+'''</style></head><body>
<a class="skip" href="#content">Skip to notes</a><nav aria-label="Primary navigation"><div class="wrap nav-inner"><a class="brand" href="https://alvarocutillas.github.io/">Álvaro Cutillas</a><div class="nav-links"><a href="../index.html#quant-basics">Quant Basics ↗</a><a class="lab-link" href="systematic-trading-strategy.html">Systematic Trading ↗</a><button class="print-button" type="button">Print notes</button></div></div><div class="reading-progress" aria-hidden="true"></div></nav>
<main id="content"><header class="hero"><div class="wrap"><div class="hero-grid"><div><div class="eyebrow">Quant Basics 06 / Options / Calibration &amp; risk</div><h1>Implied Volatility<br><span>Surface</span></h1><p class="lede">From option premiums to coherent smiles across strikes and maturities. A complete set of notes on inversion, calibration and the mathematics of consistency.</p><p class="context">Derivations, economic intuition and computed examples in one reading path. Translate prices, fit the surface and inspect the risks hidden in its derivatives.</p><div class="tag-row"><span class="tag">Implied volatility</span><span class="tag">Smiles &amp; skew</span><span class="tag">SVI / SSVI</span><span class="tag">Static arbitrage</span><span class="tag">Local volatility</span></div></div><div class="hero-visual"><div class="visual-head"><span>Foundations / 06</span><span>Volatility surfaces</span></div>'''+hero+'''<div class="visual-foot"><div>Price coordinates<b>Inversion &amp; calibration</b></div><div>Economic consistency<b>Arbitrage constraints</b></div></div></div></div><div class="hero-stats" aria-label="Study guide contents"><div class="stat"><strong>30</strong><small>Chapters &amp; appendices</small></div></div></div></header>
<div class="wrap document"><aside class="toc" aria-label="On this page"><div class="toc-title">Contents</div><div class="toc-columns">'''+''.join(toc)+'''</div></aside><article class="article" aria-label="Implied volatility surface study notes">'''+content+'''</article></div></main>
<footer class="wrap"><span>Álvaro Cutillas · Quantitative Finance Portfolio</span><span>Quant Basics 06 · Implied Volatility Surface</span></footer><script>'''+js+'''</script></body></html>'''
OUT.write_text(page,encoding='utf-8')
soup=BeautifulSoup(page,'html.parser');math_count=len(soup.find_all('math'))
for el in soup(['style','script','svg','math']):el.decompose()
report={'output':str(OUT.resolve()),'bytes':OUT.stat().st_size,'prose_words':len(soup.get_text(' ',strip=True).split()),'sections':len(sections),'figures':len(order),'display_equations':eq[0],'math_expressions':math_count}
(ROOT/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

# Portfolio EN/ES localization: retain the selector when regenerating the study.
import sys as _localization_sys
_localization_sys.path.insert(0,str(ROOT.parent/'localization'))
from localize import localize_page as _localize_page
_localize_page(OUT)
