from pathlib import Path
import html,json,re
from bs4 import BeautifulSoup
from mathml import math
ROOT=Path(__file__).parent
OUT=ROOT.parent.parent/'projects'/'equity-factor-model.html'
content='\n'.join(p.read_text(encoding='utf-8') for p in sorted(ROOT.glob('content-*.html')))
data=json.loads((ROOT/'computed.json').read_text(encoding='utf-8'))
figs=json.loads((ROOT/'figures.json').read_text(encoding='utf-8'))
order=re.findall(r'{{figure:([\w-]+)}}',content)
assert len(order)==len(set(order))==19
for number,name in enumerate(order,1):
    fig=figs[name].replace("'DejaVu Sans'","'DejaVu Sans', Arial, sans-serif")
    fig=re.sub(r'Figure \d{2}',f'Figure {number:02d}',fig)
    content=content.replace('{{figure:'+name+'}}',fig)
def table(caption,head,rows):
    body=''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td class="num">')+str(cell)+('</th>' if i==0 else '</td>') for i,cell in enumerate(row))+'</tr>' for row in rows)
    return '<div class="table-wrap"><table><caption>'+caption+'</caption><thead><tr>'+''.join('<th scope="col">'+h+'</th>' for h in head)+'</tr></thead><tbody>'+body+'</tbody></table></div>'
pct=lambda x:f'{100*x:.6f}%'
a=data['style'];c=data['cross'];names=data['dataset']['names']
rows=[]
for i,name in enumerate(['Alpha (bp/month)',*names]):
    mult=1e4 if i==0 else 1
    rows.append([name,f"{([data['dataset']['alpha'],*data['dataset']['truth']][i])*mult:.6f}",f"{a['b'][i]*mult:.6f}",f"{a['classic_se'][i]*mult:.6f}",f"{a['hac_se'][i]*mult:.6f}",f"{a['b'][i]/a['hac_se'][i]:.6f}"])
content=content.replace('{{table:coefficients}}',table('Reference time-series regression · 180 training months · HAC lag 6 · 60 withheld months',['Term','Generating value','Estimate','Classical SE','HAC SE','HAC t'],rows))
rows=[]
for name,key in [('Market + four styles','style'),('Market only','capm')]:
    r=data[key];rows.append([name,f"{r['b'][0]*1e4:.6f}",f"{r['b'][1]:.6f}",f"{r['r2']:.6f}",pct(r['rmse'])])
content=content.replace('{{table:comparison}}',table('Same generated portfolio and chronological split; future realized factor returns support attribution',['Model','Alpha (bp/month)','Market beta','Training R²','Withheld RMSE'],rows))
rows=[[name,f'{v:.10f}',pct(v/a['variance'])] for name,v in zip([*names,'Residual'],a['contributions'])]
rows.append(['Total',f"{a['variance']:.10f}",'100.000000%'])
content=content.replace('{{table:risk}}',table('Training sample variance identity · centered factor covariance and residual SSE divided by T−1',['Component','Variance contribution','Share of total'],rows))
rows=[[name+' score',f'{v:.6f}'] for name,v in zip(names[1:],c['exposure'])]
rows.extend([['Sector '+chr(65+i)+' net weight',pct(v)] for i,v in enumerate(c['sector_net'])])
content=content.replace('{{table:sort}}',table('Value signal · 20% tails within each sector · long +1 / short −1 · characteristic scores are not betas',['Exposure','Signed portfolio value'],rows))
truth=[.014,.009,.012,.006,-.004,-.012,-.006,-.014]
rows=[[name,pct(t),pct(v)] for name,t,v in zip(['Intercept (sector A)',*names[1:],'Sector B − A','Sector C − A','Sector D − A'],truth,c['fit']['b'])]
content=content.replace('{{table:cross}}',table('Joint cross-sectional return regression · 160 stocks · styles per score standard deviation · baseline sector A',['Term','Generating coefficient','OLS coefficient'],rows))
content=content.replace('{{interactive}}',(ROOT/'notebook.html').read_text(encoding='utf-8'))
content=content.replace('{{dataset}}',json.dumps(data['dataset'],separators=(',',':')).replace('<','\\u003c'))
sections=re.findall(r'<section id="([^"]+)" data-title="([^"]+)"',content)
assert len(sections)==30
groups=[('foundations','Part I','Foundations &amp; equity styles',[(1,5,'Return models and pricing'),(6,10,'Empirical benchmarks and styles')]),
        ('estimation','Part II','Signals &amp; estimation',[(11,15,'Cross-sectional construction'),(16,20,'Inference and validation')]),
        ('risk','Part III','Risk &amp; implementation',[(21,25,'Covariance and portfolio implementation'),(26,27,'Laboratory and worked studies'),(28,30,'Appendix, exercises and references')])]
toc=[]
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
js='\n'.join((ROOT/name).read_text(encoding='utf-8') for name in ['chart-coordinates.js','draw.js','notebook.js'])
hero='''<svg viewBox="0 0 350 205" role="img" aria-labelledby="hero-plot-title"><title id="hero-plot-title">Schematic factor exposures; decorative illustration, not computed estimates.</title><g stroke="#25312a" stroke-width="1"><path d="M25 160H330M25 120H330M25 80H330M25 40H330"/></g><g><rect x="42" y="57" width="35" height="103" fill="#a7bdb3" opacity=".8"/><rect x="106" y="91" width="35" height="69" fill="#d3ad84" opacity=".7"/><rect x="170" y="74" width="35" height="86" fill="#91a9bd" opacity=".75"/><rect x="234" y="109" width="35" height="51" fill="#a7bdb3" opacity=".5"/></g><g fill="#a7bdb3" font-size="9" font-family="system-ui,sans-serif"><text x="42" y="185">VALUE</text><text x="99" y="185">MOMENTUM</text><text x="171" y="185">QUALITY</text><text x="232" y="185">LOW VOL</text></g></svg>'''
page='''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="An extensive equity factor model study guide: value, momentum, quality, low volatility, CAPM and multifactor pricing, point-in-time signals, cross-sectional construction, OLS and HAC inference, factor covariance, risk and offline numerical laboratories."><meta name="theme-color" content="#050505"><title>Equity Factor Model · Quant Basics - Alvaro Cutillas</title><style>'''+css+'''</style></head><body>
<a class="skip" href="#content">Skip to notes</a><nav aria-label="Primary navigation"><div class="wrap nav-inner"><a class="brand" href="https://alvarocutillas.github.io/">Alvaro Cutillas</a><div class="nav-links"><a href="../index.html#quant-basics">Quant Basics ↗</a><a class="lab-link" href="#laboratory">Factor Lab ↗</a><button class="print-button" type="button">Print notes</button></div></div><div class="reading-progress" aria-hidden="true"></div></nav>
<main id="content"><header class="hero"><div class="wrap"><div class="hero-grid"><div><div class="eyebrow">Quant Basics 08 / Equities / Signals &amp; risk</div><h1>Equity Factor<br><span>Model</span></h1><p class="lede">From stock characteristics to common return drivers. A complete set of notes on equity styles, factor estimation and portfolio risk.</p><p class="context">Theory, intuition and computed examples in one reading path. Build the signal, estimate the exposure and distinguish attribution from prediction.</p><div class="tag-row"><span class="tag">Value &amp; momentum</span><span class="tag">Quality &amp; low volatility</span><span class="tag">Regression</span><span class="tag">HAC inference</span><span class="tag">Factor risk</span></div></div><div class="hero-visual"><div class="visual-head"><span>Foundations / 08</span><span>Equity factors</span></div>'''+hero+'''<div class="visual-foot"><div>Formation characteristics<b>Signals &amp; portfolios</b></div><div>Common return drivers<b>Exposures &amp; risk</b></div></div></div></div><div class="hero-stats" aria-label="Study guide contents"><div class="stat"><strong>30</strong><small>Chapters &amp; appendices</small></div></div></div></header>
<div class="wrap document"><aside class="toc" aria-label="On this page"><div class="toc-title">Contents</div><div class="toc-columns">'''+''.join(toc)+'''</div></aside><article class="article" aria-label="Equity factor model study notes">'''+content+'''</article></div></main>
<footer class="wrap"><span>Alvaro Cutillas · Quantitative Finance Portfolio</span><span>Quant Basics 08 · Equity Factor Model</span></footer><script>'''+js+'''</script></body></html>'''
OUT.parent.mkdir(parents=True,exist_ok=True)
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
