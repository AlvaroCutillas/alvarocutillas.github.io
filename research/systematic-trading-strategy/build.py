from pathlib import Path
import html,json,re
from bs4 import BeautifulSoup
from mathml import math
ROOT=Path(__file__).parent
OUT=ROOT.parent.parent/'projects'/'systematic-trading-strategy.html'
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
pct=lambda x:f'{100*x:.4f}%'
money=lambda x:f'€{x:,.2f}'
num=lambda x:'—' if x is None else f'{x:.6f}'
fixed=lambda x:f'{0 if abs(x)<5e-7 else x:.6f}'
rows=[[name]+[pct(m[k]) for k in ['total_return','cagr','volatility']]+[num(m['sharpe']),pct(m['max_drawdown']),f"{m['annual_turnover']:.4f} ×",money(m['total_fees'])] for name,m in data['metrics'].items()]
content=content.replace('{{table:performance}}',table('Fixed benchmark · 1,448 return periods · close 64 to close 1,512 · cost 10 bps except gross and cash',['Account','Total return','CAGR','Volatility','Sharpe','Signed max DD','Annual turnover','Nominal fees'],rows))
rows=[[r['day'],r['asof'] if r['asof']>=0 else '—',pct(r['target']),f"{r['price_start']:.4f}",fixed(r['fee']),fixed(r['stock_after']),fixed(r['cash_after']),fixed(r['wealth_end'])] for r in data['ledger']]
content=content.replace('{{table:ledger}}',table('Toy account · rebalance at each interval’s starting close · equity after the following return',['Return day','Formation close','Target','Execution price','Fee','Stock after trade','Cash after trade','End wealth'],rows))
rows=[[s['fit_close'],s['training_start'],s['lookback'],f"{s['training_sharpe']:.6f}",s['first_affected_return']] for s in data['walk']]
content=content.replace('{{table:walk}}',table('Past-only lookback selection · five candidates in ascending order · ties select the first candidate',['Fit after close','Training starts at close','Selected lookback','Training net Sharpe','First affected return'],rows))
rows=[[label]+[pct(m[k]) for k in ['total_return','cagr','volatility']]+[num(m['sharpe']),pct(m['max_drawdown'])] for label,m in [('Walk-forward selected rule',data['walk_metrics']),('Fixed 63-session rule',data['fixed_walk_metrics'])]]
content=content.replace('{{table:walk-results}}',table('Common evaluation begins at close 504 · no volatility scaling · 10 bps cost · cash 2%',['Policy','Total return','CAGR','Volatility','Sharpe','Signed max DD'],rows))
rows=[[label]+[pct(v) for v in data['bootstrap'][key]] for label,key in [('CAGR','cagr'),('Signed maximum drawdown','drawdown')]]
content=content.replace('{{table:bootstrap}}',table('Conditional circular-block return resampling · 600 replications · block length 20',['Metric','Resample 2.5%','Resample 97.5%'],rows))
content=content.replace('{{interactive}}',(ROOT/'notebook.html').read_text(encoding='utf-8'))
sections=re.findall(r'<section id="([^"]+)" data-title="([^"]+)"',content)
assert len(sections)==30
toc=[]
groups=[('foundations','Part I','Signals &amp; risk allocation',[(1,5,'Research foundations'),(6,10,'Signals and sizing')]),
        ('implementation','Part II','Execution &amp; validation',[(11,15,'Portfolios and account mechanics'),(16,20,'Evaluation and selection')]),
        ('practice','Part III','Performance &amp; practice',[(21,25,'Statistical and economic assessment'),(26,27,'Numerical study'),(28,30,'Appendix and further reading')])]
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
hero='''<svg viewBox="0 0 350 205" role="img" aria-labelledby="hero-plot-title"><title id="hero-plot-title">Schematic strategy and benchmark wealth curves; decorative illustration.</title><g stroke="#25312a" stroke-width="1"><path d="M25 160H330M25 120H330M25 80H330M25 40H330"/></g><path d="M25 151L49 148L70 134L89 139L112 112L134 122L158 91L181 97L206 64L227 76L253 46L278 50L302 30L330 22" stroke="#a7bdb3" stroke-width="2.5" fill="none"/><path d="M25 151C87 140 106 122 157 118S240 92 330 83" stroke="#91a9bd" stroke-width="1.4" stroke-dasharray="5 5" fill="none"/><path d="M159 40V160M253 40V160" stroke="#56685e" stroke-width="1" stroke-dasharray="2 5"/><g fill="#829789" font-size="9" font-family="system-ui,sans-serif"><text x="25" y="191">WEALTH</text><text x="164" y="180">REFIT</text><text x="286" y="191">TIME</text></g></svg>'''
page='''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="An extensive systematic trading strategy study guide: signals, information timing, position sizing, cash accounting, execution, costs, walk-forward testing, performance, statistical selection and robustness, with computed figures and an offline interactive laboratory.">
<meta name="theme-color" content="#050505"><title>Systematic Trading Strategy · Quant Basics — Álvaro Cutillas</title><style>'''+css+'''</style></head><body>
<a class="skip" href="#content">Skip to notes</a>
<nav aria-label="Primary navigation"><div class="wrap nav-inner"><a class="brand" href="https://alvarocutillas.github.io/">Álvaro Cutillas</a><div class="nav-links"><a href="../index.html#quant-basics">Quant Basics ↗</a><a class="lab-link" href="var-expected-shortfall.html">VaR &amp; ES ↗</a><button class="print-button" type="button">Print notes</button></div></div><div class="reading-progress" aria-hidden="true"></div></nav>
<main id="content"><header class="hero"><div class="wrap"><div class="hero-grid"><div><div class="eyebrow">Quant Basics 05 / Systematic trading / Research &amp; execution</div><h1>Systematic<br><span>Trading Strategy</span></h1><p class="lede">From trading signals to a self-financing account. A complete set of notes on strategy design, execution and credible performance evaluation.</p><p class="context">Economic intuition, formulas and computed experiments in one reading path. Define what is known, model what is traded and test what remains after costs.</p><div class="tag-row"><span class="tag">Time series</span><span class="tag">Signals</span><span class="tag">Position sizing</span><span class="tag">Transaction costs</span><span class="tag">Walk-forward</span></div></div><div class="hero-visual"><div class="visual-head"><span>Foundations / 05</span><span>Systematic strategies</span></div>'''+hero+'''<div class="visual-foot"><div>Decision process<b>Signals &amp; execution</b></div><div>Research evidence<b>Prospective testing</b></div></div></div></div><div class="hero-stats" aria-label="Study guide contents"><div class="stat"><strong>30</strong><small>Chapters &amp; appendices</small></div></div></div></header>
<div class="wrap document"><aside class="toc" aria-label="On this page"><div class="toc-title">Contents</div><div class="toc-columns">'''+''.join(toc)+'''</div></aside><article class="article" aria-label="Systematic trading strategy study notes">'''+content+'''</article></div></main>
<footer class="wrap"><span>Álvaro Cutillas · Quantitative Finance Portfolio</span><span>Quant Basics 05 · Systematic Trading Strategy</span></footer><script>'''+js+'''</script></body></html>'''
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
