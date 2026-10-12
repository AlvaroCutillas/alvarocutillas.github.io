from pathlib import Path
import html,json,re
from bs4 import BeautifulSoup
from mathml import math
ROOT=Path(__file__).parent
OUT=ROOT.parent.parent/'projects'/'markowitz-portfolio-theory.html'
content='\n'.join(p.read_text(encoding='utf-8') for p in sorted(ROOT.glob('content-*.html')))
data=json.loads((ROOT/'computed.json').read_text(encoding='utf-8'))
figs=json.loads((ROOT/'figures.json').read_text(encoding='utf-8'))
order=re.findall(r'{{figure:(\w+)}}',content)
assert len(order)==len(set(order))==16
for number,name in enumerate(order,1):
    fig=figs[name].replace("'DejaVu Sans'","'DejaVu Sans', Arial, sans-serif")
    fig=re.sub(r'Figure \d{2}',f'Figure {number:02d}',fig)
    content=content.replace('{{figure:'+name+'}}',fig)

def table(caption,head,rows):
    body=''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td class="num">')+str(cell)+('</th>' if i==0 else '</td>') for i,cell in enumerate(row))+'</tr>' for row in rows)
    return '<div class="table-wrap"><table><caption>'+caption+'</caption><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in head)+'</tr></thead><tbody>'+body+'</tbody></table></div>'

pct=lambda x:f'{100*x:.6f}%'
rows=[[a['name'],pct(a['return']),pct(a['volatility'])] for a in data['assets']]
content=content.replace('{{table:inputs}}',table('Annual simple-return benchmark · risk-free return 2% · correlations AB = 0.20, AC = 0.10, BC = 0.35',['Asset','Expected return','Volatility'],rows))
rows=[['Asset '+c]+[f'{x:.6f}' for x in row] for c,row in zip('ABC',data['covariance'])]
content=content.replace('{{table:covariance}}',table('Covariance matrix · squared decimal-return units',['','Asset A','Asset B','Asset C'],rows))
rows=[[key,f'{value:.9f}'] for key,value in data['constants'].items()]
content=content.replace('{{table:constants}}',table('Unrestricted frontier constants from the supplied covariance and means',['Constant','Value'],rows))
rows=[[name]+[pct(p[k]) for k in ['return','volatility']]+[pct(w) for w in p['weights']]+[f"{p['sharpe']:.6f}"] for name,p in data['portfolios'].items()]
content=content.replace('{{table:portfolios}}',table('Computed population-model portfolios · net budget one · Sharpe ratios use risk-free return 2%',['Portfolio','Expected return','Volatility','Weight A','Weight B','Weight C','Sharpe'],rows))
vol=data['portfolios']['Equal weight']['volatility']
rows=[['Asset '+c,pct(1/3),pct(rc),pct(rc/vol)] for c,rc in zip('ABC',data['risk_contributions'])]
rows.append(['Total','100.000000%',pct(vol),'100.000000%'])
content=content.replace('{{table:risk}}',table('Equal-weight portfolio · Euler decomposition of volatility',['Position','Capital weight','Volatility contribution','Risk share'],rows))
content=content.replace('{{interactive}}',(ROOT/'notebook.html').read_text(encoding='utf-8'))
sections=re.findall(r'<section id="([^"]+)" data-title="([^"]+)"',content)
assert len(sections)==30
toc=[]
groups=[('foundations','Part I','Foundations',[(1,10,None)]),
        ('construction','Part II','Portfolio construction',[(11,20,None)]),
        ('practice','Part III','Estimation &amp; practice',[(21,24,'Estimation and evaluation'),(25,27,'Numerical study'),(28,30,'Appendix and further reading')])]
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
hero='''<svg viewBox="0 0 350 205" role="img" aria-labelledby="hero-plot-title"><title id="hero-plot-title">Schematic illustration of diversification and an efficient frontier.</title><g stroke="#25312a" stroke-width="1"><path d="M25 160H330M25 120H330M25 80H330M25 40H330"/></g><g fill="#778e84" opacity=".6"><circle cx="100" cy="135" r="3"/><circle cx="130" cy="123" r="3"/><circle cx="147" cy="115" r="3"/><circle cx="163" cy="136" r="3"/><circle cx="183" cy="98" r="3"/><circle cx="215" cy="111" r="3"/><circle cx="235" cy="74" r="3"/><circle cx="250" cy="90" r="3"/><circle cx="281" cy="64" r="3"/></g><path d="M85 132C85 110 110 87 153 68S248 39 330 23" stroke="#a7bdb3" stroke-width="2.5" fill="none"/><path d="M85 132C85 151 120 166 155 170" stroke="#7e8d86" stroke-width="1.5" fill="none"/><path d="M25 169L330 25" stroke="#d3ad84" stroke-width="1.3" stroke-dasharray="5 5"/><circle cx="85" cy="132" r="4" fill="#e4ece7"/><circle cx="173" cy="62" r="4" fill="#d3ad84"/><g fill="#829789" font-size="9" font-family="system-ui,sans-serif"><text x="25" y="191">EXPECTED RETURN</text><text x="267" y="191">VOLATILITY</text></g></svg>'''
page='''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="An extensive Markowitz portfolio theory study guide: returns, covariance, diversification, analytical frontiers, tangency portfolios, constraints, risk contributions and estimation uncertainty, with computed figures and an interactive laboratory.">
<meta name="theme-color" content="#050505"><title>Markowitz Portfolio Theory · Quant Basics — Álvaro Cutillas</title><style>'''+css+'''</style></head><body>
<a class="skip" href="#content">Skip to notes</a>
<nav aria-label="Primary navigation"><div class="wrap nav-inner"><a class="brand" href="https://alvarocutillas.github.io/">Álvaro Cutillas</a><div class="nav-links"><a href="../index.html#quant-basics">Quant Basics ↗</a><a class="lab-link" href="monte-carlo-option-pricing.html">Monte Carlo ↗</a><button class="print-button" type="button">Print notes</button></div></div><div class="reading-progress" aria-hidden="true"></div></nav>
<main id="content"><header class="hero"><div class="wrap"><div class="hero-grid"><div><div class="eyebrow">Quant Basics 03 / Portfolio theory / Mean–variance analysis</div><h1>Markowitz<br><span>Portfolio Theory</span></h1><p class="lede">From covariance and diversification to the efficient frontier. A complete set of notes on portfolio choice, constraints and uncertain inputs.</p><p class="context">Derivations, practical intuition and computed examples in one reading path. Understand how assets work together, what makes a portfolio efficient and how estimation changes the answer.</p><div class="tag-row"><span class="tag">Diversification</span><span class="tag">Mean–variance</span><span class="tag">Efficient frontier</span><span class="tag">Risk contributions</span><span class="tag">Estimation uncertainty</span></div></div><div class="hero-visual"><div class="visual-head"><span>Foundations / 03</span><span>Portfolio selection</span></div>'''+hero+'''<div class="visual-foot"><div>Dependence<b>Diversification</b></div><div>Portfolio choice<b>Efficient trade-offs</b></div></div></div></div><div class="hero-stats" aria-label="Study guide contents"><div class="stat"><strong>30</strong><small>Chapters &amp; appendices</small></div></div></div></header>
<div class="wrap document"><aside class="toc" aria-label="On this page"><div class="toc-title">Contents</div><div class="toc-columns">'''+''.join(toc)+'''</div></aside><article class="article" aria-label="Markowitz portfolio theory study notes">'''+content+'''</article></div></main>
<footer class="wrap"><span>Álvaro Cutillas · Quantitative Finance Portfolio</span><span>Quant Basics 03 · Markowitz Portfolio Theory</span></footer><script>'''+js+'''</script></body></html>'''
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
