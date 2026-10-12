from pathlib import Path
import html,json,re
from bs4 import BeautifulSoup
from mathml import math
ROOT=Path(__file__).parent
OUT=ROOT.parent.parent/'projects'/'var-expected-shortfall.html'
content='\n'.join(p.read_text(encoding='utf-8') for p in sorted(ROOT.glob('content-*.html')))
data=json.loads((ROOT/'computed.json').read_text(encoding='utf-8'))
figs=json.loads((ROOT/'figures.json').read_text(encoding='utf-8'))
order=re.findall(r'{{figure:(\w+)}}',content)
assert len(order)==len(set(order))==17
for number,name in enumerate(order,1):
    fig=figs[name].replace("'DejaVu Sans'","'DejaVu Sans', Arial, sans-serif")
    fig=re.sub(r'Figure \d{2}',f'Figure {number:02d}',fig)
    content=content.replace('{{figure:'+name+'}}',fig)
def table(caption,head,rows):
    body=''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td class="num">')+str(cell)+('</th>' if i==0 else '</td>') for i,cell in enumerate(row))+'</tr>' for row in rows)
    return '<div class="table-wrap"><table><caption>'+caption+'</caption><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in head)+'</tr></thead><tbody>'+body+'</tbody></table></div>'
money=lambda x:f'€{x:,.2f}'
rows=[[f"{100*p['alpha']:.1f}%"]+[money(p[k]) for k in ['normal_var','normal_es','student_var','student_es']] for p in data['normal']]
content=content.replace('{{table:normal}}',table('Population risk · wealth €1,000,000 · mean zero · horizon standard deviation 1% of wealth',['Confidence','Normal VaR','Normal ES','Student-t VaR','Student-t ES'],rows))
p=data['portfolio'];rows=[['Portfolio loss standard deviation',money(p['sd']),'—'],['Portfolio VaR 99%',money(p['var']),'—'],['Portfolio ES 99%',money(p['es']),'100.0000%']]
rows += [['Asset '+c+' component ES',money(v),f"{100*v/p['es']:.4f}%"] for c,v in zip('ABC',p['contributions'])]
content=content.replace('{{table:portfolio}}',table('Joint-normal portfolio · wealth €1,000,000 · capital weights 50%, 30%, 20%',['Quantity','Currency value','Share of ES'],rows))
rows=[[name,f"{v['var']:.6f}",f"{v['es']:.6f}"] for name,v in data['options'].items()]
content=content.replace('{{table:options}}',table('One short European call · one trading day · 150,000 shared synthetic scenarios · 99% confidence',['Revaluation rule','VaR','ES'],rows))
rows=[]
for name,d in data['backtests'].items():
    counts,lr,pv=d['independence']
    rows.append([name,'10 / 500',f"{d['coverage'][0]:.6f}",str(counts),f'{lr:.6f}',f'{pv:.6g}'])
content=content.replace('{{table:backtests}}',table('Artificial hit sequences · target confidence 98% · asymptotic p-values shown as illustrations; transition counts are sparse',['Sequence','Breaches','Coverage LR','Transitions [[00,01],[10,11]]','Independence LR','Asymptotic p'],rows))
b=data['bootstrap'];rows=[[label,f"{b['sample_risk'][i]:.6f}",f"{b[key][0]:.6f}",f"{b[key][1]:.6f}"] for i,(label,key) in enumerate([('VaR','var_interval'),('ES','es_interval')])]
content=content.replace('{{table:bootstrap}}',table('99% risk · standard-normal synthetic sample · 1,000 observations · 1,200 IID resamples · percentile intervals conditional on the sample',['Measure','Sample estimate','Bootstrap 2.5%','Bootstrap 97.5%'],rows))
content=content.replace('{{interactive}}',(ROOT/'notebook.html').read_text(encoding='utf-8'))
sections=re.findall(r'<section id="([^"]+)" data-title="([^"]+)"',content)
assert len(sections)==30
toc=[]
groups=[('foundations','Part I','Risk-measure foundations',[(1,10,None)]),
        ('methods','Part II','Models &amp; estimation',[(11,18,'Scenario and distribution models'),(19,20,'Attribution and portfolio choice')]),
        ('practice','Part III','Validation &amp; practice',[(21,25,'Forecast evaluation'),(26,27,'Numerical study'),(28,30,'Appendix and further reading')])]
for key,part,title,ranges in groups:
    toc.append(f'<div class="toc-column" aria-labelledby="toc-{key}-title"><div class="toc-part">{part}</div><h2 id="toc-{key}-title">{title}</h2>')
    for first,last,subheading in ranges:
        if subheading:toc.append(f'<div class="toc-subheading">{subheading}</div>')
        toc.append(f'<ol class="toc-chapters" start="{first}">')
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
hero='''<svg viewBox="0 0 350 205" role="img" aria-labelledby="hero-plot-title"><title id="hero-plot-title">Schematic loss density with a tail threshold and tail mean.</title><defs><clipPath id="hero-tail-clip"><rect x="221" y="0" width="110" height="170"/></clipPath></defs><g stroke="#25312a" stroke-width="1"><path d="M25 160H330M25 120H330M25 80H330M25 40H330"/></g><path d="M25 158C68 158 80 152 98 132S125 56 149 40S188 52 207 91S237 148 271 156S313 158 330 158V160H25Z" fill="#d3ad84" opacity=".23" clip-path="url(#hero-tail-clip)"/><path d="M25 158C68 158 80 152 98 132S125 56 149 40S188 52 207 91S237 148 271 156S313 158 330 158" stroke="#a7bdb3" stroke-width="2.5" fill="none"/><path d="M221 56V160" stroke="#d3ad84" stroke-width="1.3" stroke-dasharray="5 5"/><path d="M250 94V160" stroke="#91a9bd" stroke-width="1.3" stroke-dasharray="3 4"/><g fill="#829789" font-size="9" font-family="system-ui,sans-serif"><text x="25" y="191">LOSS DENSITY</text><text x="215" y="181">VaR</text><text x="245" y="181">ES</text><text x="305" y="191">LOSS</text></g></svg>'''
page='''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="An extensive VaR and Expected Shortfall study guide: quantiles, discrete tails, normal and Student-t models, historical and Monte Carlo estimation, EVT, risk allocation, ES optimization and backtesting, with computed figures and an offline interactive laboratory.">
<meta name="theme-color" content="#050505"><title>VaR &amp; Expected Shortfall · Quant Basics — Álvaro Cutillas</title><style>'''+css+'''</style></head><body>
<a class="skip" href="#content">Skip to notes</a>
<nav aria-label="Primary navigation"><div class="wrap nav-inner"><a class="brand" href="https://alvarocutillas.github.io/">Álvaro Cutillas</a><div class="nav-links"><a href="../index.html#quant-basics">Quant Basics ↗</a><a class="lab-link" href="markowitz-portfolio-theory.html">Portfolio Theory ↗</a><button class="print-button" type="button">Print notes</button></div></div><div class="reading-progress" aria-hidden="true"></div></nav>
<main id="content"><header class="hero"><div class="wrap"><div class="hero-grid"><div><div class="eyebrow">Quant Basics 04 / Risk measurement / Tail distributions</div><h1>Value at Risk<br><span>&amp; Expected<br>Shortfall</span></h1><p class="lede">From loss quantiles to the severity of extreme outcomes. A complete set of notes on tail-risk measurement, estimation and forecast validation.</p><p class="context">Definitions, derivations and computed examples in one reading path. Understand what the threshold tells you, what happens beyond it and how much evidence supports the estimate.</p><div class="tag-row"><span class="tag">Tail risk</span><span class="tag">Historical simulation</span><span class="tag">Monte Carlo</span><span class="tag">Extreme-value theory</span><span class="tag">Backtesting</span></div></div><div class="hero-visual"><div class="visual-head"><span>Foundations / 04</span><span>Loss distributions</span></div>'''+hero+'''<div class="visual-foot"><div>Value at Risk<b>Tail threshold</b></div><div>Expected Shortfall<b>Tail severity</b></div></div></div></div><div class="hero-stats" aria-label="Study guide contents"><div class="stat"><strong>30</strong><small>Chapters &amp; appendices</small></div></div></div></header>
<div class="wrap document"><aside class="toc" aria-label="On this page"><div class="toc-title">Contents</div><div class="toc-columns">'''+''.join(toc)+'''</div></aside><article class="article" aria-label="Value at Risk and Expected Shortfall study notes">'''+content+'''</article></div></main>
<footer class="wrap"><span>Álvaro Cutillas · Quantitative Finance Portfolio</span><span>Quant Basics 04 · VaR &amp; Expected Shortfall</span></footer><script>'''+js+'''</script></body></html>'''
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
