from pathlib import Path
import html,json,re
from bs4 import BeautifulSoup
from mathml import math
ROOT=Path(__file__).parent
OUT=ROOT.parent.parent/'projects'/'yield-curve-modelling.html'
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
rows=[[str(r['T']),pct(r['par']),f"{r['discount']:.9f}",pct(r['zero'])] for r in data['bootstrap']]
content=content.replace('{{table:bootstrap}}',table('Annual par bootstrap · dirty price 100 · exact-year annual payments',['Years','Annual par quote','Recovered discount','Continuous zero'],rows))
rows=[]
for label,key in [('Nelson–Siegel','ns_fit'),('Svensson','nss_fit')]:
    f=data[key];p=f['params']
    rows.append([label,*[pct(x) for x in p[:4]],f'{p[4]:.6f}',f'{p[5]:.6f}' if key=='nss_fit' else '—',f"{f['train_rmse_bps']:.6f}",f"{f['holdout_rmse_bps']:.6f}",f"{f['condition']:.3f}"])
content=content.replace('{{table:fit}}',table('Static profiled fits · equal zero-rate weights · coefficient rates shown in percent',['Model','β₀','β₁','β₂','β₃','τ₁ (yr)','τ₂ (yr)','Train (bp)','Withheld (bp)','Design cond.'],rows))
f=data['nss_fit']
rows=[[f'{t:g}','Training' if train else 'Withheld',pct(y),pct(pred),f'{(pred-y)*1e4:+.6f}'] for t,train,y,pred in zip(f['t'],f['train'],f['observed'],f['pred'])]
content=content.replace('{{table:residuals}}',table('Static Svensson residual audit · residual = fitted minus observed · 1 bp = 0.0001',['Years','Role','Observed zero','Fitted zero','Residual (bp)'],rows))
rows=[[f"{r['T']:g}",pct(r['zero']),pct(r['forward']),f"{r['discount']:.9f}",pct(r['par'])] for r in data['rows']]
content=content.replace('{{table:curve}}',table('Reference curve · continuous zeros and forwards · nominal semiannual par coupons',['Years','Zero (continuous)','Forward (continuous)','Discount','Par (semiannual)'],rows))
b=data['bond']
rows=[[f'{t:g}',f'{cf:.6f}',f'{d:.9f}',f'{pv:.6f}'] for t,cf,d,pv in zip(b['t'],b['cf'],b['d'],b['pv'])]
rows.append(['Total','','',f"{b['price']:.6f}"])
content=content.replace('{{table:cashflows}}',table('Reference bond cash-flow ledger · face 100 · coupon 4% · semiannual · accrued interest zero',['Years','Cash flow','Discount','Present value'],rows))
rows=[['Base',f"{b['price']:.6f}",'—'],['Exact +100 bp',f"{b['shocked_price']:.6f}",'0.000000'],['Duration',f"{b['linear']:.6f}",f"{b['linear']-b['shocked_price']:+.6f}"],['Duration + convexity',f"{b['quadratic']:.6f}",f"{b['quadratic']-b['shocked_price']:+.6f}"]]
content=content.replace('{{table:shock}}',table('Parallel continuous-zero shift of +0.01 · amounts per face 100',['Method','Bond price','Approximation minus exact'],rows))
content=content.replace('{{interactive}}',(ROOT/'notebook.html').read_text(encoding='utf-8'))
sections=re.findall(r'<section id="([^"]+)" data-title="([^"]+)"',content)
assert len(sections)==30
groups=[('valuation','Part I','Valuation &amp; construction',[(1,5,'Discounting and rate coordinates'),(6,10,'Contracts, instruments and bootstrapping')]),
        ('calibration','Part II','Representation &amp; calibration',[(11,15,'Interpolation and parametric models'),(16,20,'Estimation, validation and dynamics')]),
        ('risk','Part III','Risk &amp; numerical practice',[(21,25,'Sensitivities and implementation'),(26,27,'Laboratory and worked studies'),(28,30,'Appendix, exercises and references')])]
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
js='\n'.join((ROOT/name).read_text(encoding='utf-8') for name in ['chart-coordinates.js','notebook.js'])
hero='''<svg viewBox="0 0 350 205" role="img" aria-labelledby="hero-plot-title"><title id="hero-plot-title">Schematic zero and forward curves; decorative illustration.</title><g stroke="#25312a" stroke-width="1"><path d="M25 160H330M25 120H330M25 80H330M25 40H330"/></g><g fill="none" stroke-width="2"><path d="M25 147C62 80 96 72 145 83S234 108 330 88" stroke="#a7bdb3"/><path d="M25 147C60 37 88 36 130 76S225 110 330 72" stroke="#d3ad84"/><path d="M25 149C61 86 106 77 147 86S231 107 330 90" stroke="#91a9bd" stroke-dasharray="3 5"/></g><g fill="#829789" font-size="9" font-family="system-ui,sans-serif"><text x="25" y="191">SHORT END</text><text x="158" y="191">MATURITY</text><text x="277" y="191">LONG END</text></g></svg>'''
page='''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="An extensive yield curve modelling study guide: discounts, forwards, par yields, bootstrapping, interpolation, Nelson–Siegel and Svensson calibration, validation, multicurve valuation, duration and dynamic models, with computed figures and an offline laboratory."><meta name="theme-color" content="#050505"><title>Yield Curve Modelling · Quant Basics - Alvaro Cutillas</title><style>'''+css+'''</style></head><body>
<a class="skip" href="#content">Skip to notes</a><nav aria-label="Primary navigation"><div class="wrap nav-inner"><a class="brand" href="https://alvarocutillas.github.io/">Alvaro Cutillas</a><div class="nav-links"><a href="../index.html#quant-basics">Quant Basics ↗</a><a class="lab-link" href="#laboratory">Curve Lab ↗</a><button class="print-button" type="button">Print notes</button></div></div><div class="reading-progress" aria-hidden="true"></div></nav>
<main id="content"><header class="hero"><div class="wrap"><div class="hero-grid"><div><div class="eyebrow">Quant Basics 07 / Fixed income / Construction &amp; calibration</div><h1>Yield Curve<br><span>Modelling</span></h1><p class="lede">From discount factors to coherent term structures. A complete set of notes on construction, parametric calibration and fixed-income risk.</p><p class="context">Derivations, economic intuition and computed examples in one reading path. Build the curve, fit its shape and understand what its rates can tell you.</p><div class="tag-row"><span class="tag">Discount factors</span><span class="tag">Bootstrapping</span><span class="tag">Nelson–Siegel</span><span class="tag">Svensson</span><span class="tag">Duration &amp; convexity</span></div></div><div class="hero-visual"><div class="visual-head"><span>Foundations / 07</span><span>Term structures</span></div>'''+hero+'''<div class="visual-foot"><div>Present-value coordinates<b>Discounts &amp; forwards</b></div><div>Parametric estimation<b>Shape &amp; calibration</b></div></div></div></div><div class="hero-stats" aria-label="Study guide contents"><div class="stat"><strong>30</strong><small>Chapters &amp; appendices</small></div></div></div></header>
<div class="wrap document"><aside class="toc" aria-label="On this page"><div class="toc-title">Contents</div><div class="toc-columns">'''+''.join(toc)+'''</div></aside><article class="article" aria-label="Yield curve modelling study notes">'''+content+'''</article></div></main>
<footer class="wrap"><span>Alvaro Cutillas · Quantitative Finance Portfolio</span><span>Quant Basics 07 · Yield Curve Modelling</span></footer><script>'''+js+'''</script></body></html>'''
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
