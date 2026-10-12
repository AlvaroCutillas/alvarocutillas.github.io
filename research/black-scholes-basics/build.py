from pathlib import Path
import re,json,html
from mathml import math
from bs4 import BeautifulSoup

ROOT=Path(__file__).parent
OUT=ROOT.parent.parent/'projects'/'black-scholes-basics.html'
content=(ROOT/'content.html').read_text(encoding='utf-8')
content=content.replace(r'\operatorname{P\&L}',r'\operatorname{PnL}')
data=json.loads((ROOT/'computed.json').read_text(encoding='utf-8'))
figs=json.loads((ROOT/'figures.json').read_text(encoding='utf-8'))
for name in figs:
    # System font fallback keeps scientific SVG labels consistent with the portfolio.
    figs[name]=figs[name].replace("'DejaVu Sans'", "'DejaVu Sans', Arial, sans-serif")
figure_titles={
    'payoffs':'Option payoffs and financed terminal profit',
    'smoothing':'European call values at different maturities',
    'gbm':'Risk-neutral GBM paths and terminal price distribution',
    'greeks':'European call sensitivities across maturities',
    'tangent':'First- and second-order spot sensitivity approximations',
    'hedging':'Replication error under discrete rebalancing',
    'iv':'European price–volatility relationship and illustrative skew',
    'american':'American put values and early-exercise premium',
    'boundary':'American put exercise boundary estimated by a CRR lattice',
    'convergence':'CRR price convergence and European approximation error',
    'dividends':'European and American call values under continuous dividends',
    'mc':'Monte Carlo standard errors and sample size',
    'density':'Strike derivatives and the risk-neutral density',
}
for name,title in figure_titles.items():
    figs[name]=re.sub(r'Figure (\d{2}) · [^<]+',lambda m:'Figure '+m[1]+' · '+title,figs[name])
for i,name in enumerate(re.findall(r'{{figure:(\w+)}}',content),1):
    figs[name]=re.sub(r'Figure \d{2}',f'Figure {i:02d}',figs[name])
for name,figure in figs.items(): content=content.replace('{{figure:'+name+'}}',figure)

def table(caption,head,rows):
    return '<div class="table-wrap"><table><caption>'+caption+'</caption><thead><tr>'+''.join('<th>'+h+'</th>' for h in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td'+(' class="num"' if i>0 else '')+'>'+str(v)+'</td>' for i,v in enumerate(row))+'</tr>' for row in rows)+'</tbody></table></div>'
b=data['benchmark']
rows=[['Price',f"{b['call']:.6f}",f"{b['put']:.6f}"],['Delta',f"{b['dc']:.6f}",f"{b['dp']:.6f}"],['Gamma',f"{b['gamma']:.6f}",f"{b['gamma']:.6f}"],['Vega / 1 vol point',f"{b['vega']/100:.6f}",f"{b['vega']/100:.6f}"],['Theta / year',f"{b['tc']:.6f}",f"{b['tp']:.6f}"],['Theta / calendar day (365)',f"{b['tc']/365:.6f}",f"{b['tp']/365:.6f}"],['Rho / 1 rate point',f"{b['rc']/100:.6f}",f"{b['rp']/100:.6f}"],['Yield sensitivity / 1 yield point',f"{b['qc']/100:.6f}",f"{b['qp']/100:.6f}"]]
content=content.replace('{{table:benchmark}}',table('European benchmark · S = K = 100, r = 5%, q = 0, σ = 20%, τ = 1',['Quantity','Call','Put'],rows))
rows=[[str(x['n'])]+[f"{x[k]:.6f}" for k in ['ec','ac','ep','ap']] for x in data['convergence']]
rows.append(['BSM exact','10.450584','Equal to European','5.573526','No elementary formula'])
content=content.replace('{{table:convergence}}',table('CRR convergence · one-year benchmark, continuous yield q = 0',['Steps N','European call','American call','European put','American put'],rows))
rows=[]
for level in reversed(data['tree3']):
    for j,(spot,value) in enumerate(zip(level['spots'],level['values'])):
        intrinsic=max(100-spot,0)
        rows.append([f"i = {level['i']}, j = {j}",f'{spot:.6f}',f'{intrinsic:.6f}',f'{value:.6f}','Exercise' if intrinsic>0 and abs(value-intrinsic)<1e-7 else 'Continue'])
content=content.replace('{{table:tree3}}',table('Three-step American put · selected values before maturity',['Node','Spot','Immediate payoff','American value','Decision'],rows))
content=content.replace('{{interactive}}',(ROOT/'notebook.html').read_text(encoding='utf-8'))
sections=re.findall(r'<section id="([^"]+)" data-title="([^"]+)"',content)
toc=[]
toc_groups=[
    ('european','Part I','European options',1,13),
    ('american','Part II','American options',14,20),
    ('appendix','Part III','Appendix &amp; references',21,26),
]
for group,part,heading,start,end in toc_groups:
    toc.append(f'<div class="toc-column" aria-labelledby="toc-{group}-title"><div class="toc-part">{part}</div><h2 id="toc-{group}-title">{heading}</h2>')
    for first,last,subheading in ([(21,23,'Implementation'),(24,26,'Appendix and further reading')] if group=='appendix' else [(start,end,None)]):
        if subheading: toc.append(f'<div class="toc-subheading">{subheading}</div>')
        toc.append(f'<ol class="toc-chapters" start="{first}">')
        for i in range(first,last+1):
            key,title=sections[i-1]
            toc.append(f'<li><a href="#{key}"><span class="toc-number" aria-hidden="true">{i:02d}</span><span>{title}</span></a></li>')
        toc.append('</ol>')
    toc.append('</div>')
eq=[0]
def display(match):
    eq[0]+=1
    return '<div class="eq"><div class="eq-scroll">'+math(match[1].strip(),True)+'</div><span class="eq-number">('+str(eq[0]).zfill(2)+')</span></div>'
content=re.sub(r'\\\[(.*?)\\\]',display,content,flags=re.S)
content=re.sub(r'\\\((.*?)\\\)',lambda m:math(m[1].strip()),content,flags=re.S)
css=(ROOT/'base.css').read_text(encoding='utf-8')+'\n'+(ROOT/'enhancements.css').read_text(encoding='utf-8')+'\n'+(ROOT/'chart-coordinates.css').read_text(encoding='utf-8')
js=(ROOT/'chart-coordinates.js').read_text(encoding='utf-8')+'\n'+(ROOT/'notebook.js').read_text(encoding='utf-8')
hero_svg='''<svg viewBox="0 0 350 205" role="img" aria-labelledby="hero-plot-title"><title id="hero-plot-title">European pricing smooths a call payoff; American puts add an exercise frontier.</title><g stroke="#25312a" stroke-width="1"><path d="M20 160H330M20 120H330M20 80H330M20 40H330"/></g><path d="M20 160L160 160L330 30" fill="none" stroke="#d3ad84" stroke-width="1.4" stroke-dasharray="5 5"/><path d="M20 160C80 160 123 149 162 128S246 62 330 27" fill="none" stroke="#a7bdb3" stroke-width="2.5"/><path d="M20 28C76 63 131 105 180 129S273 157 330 160" fill="none" stroke="#7c8f83" stroke-width="2"/><circle cx="160" cy="129" r="4" fill="#dce8df"/><g fill="#829789" font-size="9" font-family="system-ui, sans-serif"><text x="21" y="184">VALUE</text><text x="301" y="184">SPOT</text><text x="144" y="202">STRIKE K</text></g><path d="M160 25V166" stroke="#46574b" stroke-dasharray="3 6"/></svg>'''
page='''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="An extensive Black–Scholes–Merton study guide: European call and put derivations, Greeks, implied volatility, hedging, and American optimal stopping with computed figures and examples.">
<meta name="theme-color" content="#050505">
<title>Black–Scholes Option Pricing · Quant Basics — Álvaro Cutillas</title>
<style>'''+css+'''</style>
</head>
<body>
<a class="skip" href="#content">Skip to notes</a>
<nav aria-label="Primary navigation"><div class="wrap nav-inner"><a class="brand" href="https://alvarocutillas.github.io/">Álvaro Cutillas</a><div class="nav-links"><a href="../index.html#quant-basics">Quant Basics ↗</a><a class="lab-link" href="black-scholes.html">Pricing Lab ↗</a><button class="print-button" type="button">Print notes</button></div></div><div class="reading-progress" aria-hidden="true"></div></nav>
<main id="content">
<header class="hero"><div class="wrap"><div class="hero-grid"><div><div class="eyebrow">Quant Basics 01 / Derivatives / Theory & valuation</div><h1>Black–Scholes<br><span>Option Pricing</span></h1><p class="lede">From European replication to American optimal exercise. A complete set of notes on the model, its mathematics and its limits.</p><p class="context">Derivations, intuition, formulas and computed figures in one reading path. Start with the contract; finish with the exercise frontier.</p><div class="tag-row"><span class="tag">European options</span><span class="tag">American options</span><span class="tag">Stochastic calculus</span><span class="tag">Greeks</span><span class="tag">Optimal stopping</span></div></div><div class="hero-visual"><div class="visual-head"><span>Foundations / 01</span><span>Black–Scholes–Merton</span></div>'''+hero_svg+'''<div class="visual-foot"><div>European<b>Replication</b></div><div>American<b>Optimal stopping</b></div></div></div></div><div class="hero-stats" aria-label="Study guide contents"><div class="stat"><strong>26</strong><small>Chapters &amp; appendices</small></div></div></div></header>
<div class="wrap document"><aside class="toc" aria-label="On this page"><div class="toc-title">Contents</div><div class="toc-columns">'''+''.join(toc)+'''</div></aside><article class="article" aria-label="Black–Scholes study notes">'''+content+'''</article></div>
</main><footer class="wrap"><span>Álvaro Cutillas · Quantitative Finance Portfolio</span><span>Quant Basics 01 · Black–Scholes–Merton</span></footer>
<script>'''+js+'''</script>
</body></html>'''
OUT.write_text(page,encoding='utf-8')
soup=BeautifulSoup(page,'html.parser')
for x in soup(['script','style','svg','math']): x.decompose()
words=len(soup.get_text(' ',strip=True).split())
print(json.dumps({'output':str(OUT.resolve()),'bytes':OUT.stat().st_size,'prose_words':words,'display_equations':eq[0],'sections':len(sections),'figures':len(figs)},indent=2))

# Portfolio EN/ES localization: retain the selector when regenerating the study.
import sys as _localization_sys
_localization_sys.path.insert(0,str(ROOT.parent/'localization'))
from localize import localize_page as _localize_page
_localize_page(OUT)
