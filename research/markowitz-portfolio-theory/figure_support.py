from pathlib import Path
from io import StringIO
import re, json, math
import numpy as np
from scipy.special import ndtr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

ROOT=Path(__file__).parent
ACC='#a7bdb3'; WARM='#d3ad84'; GRAY='#7e8d86'; BLUE='#91a9bd'
plt.rcParams.update({'figure.facecolor':'#0d0d0d','axes.facecolor':'#0d0d0d','axes.edgecolor':'#424842','text.color':'#c8cec8','axes.labelcolor':'#a5ada6','xtick.color':'#939b94','ytick.color':'#939b94','grid.color':'#252b26','font.family':'DejaVu Sans','font.size':9,'axes.titlesize':11,'axes.titleweight':'medium','svg.fonttype':'none','legend.frameon':False,'axes.spines.top':False,'axes.spines.right':False,'lines.linewidth':2,'savefig.facecolor':'#0d0d0d'})

def bs(S=100.,K=100.,r=.05,q=0.,sig=.2,tau=1.):
    S=np.asarray(S,dtype=float)
    if tau<=0: return {'call':np.maximum(S-K,0),'put':np.maximum(K-S,0)}
    if sig<=0:
        return {'call':np.maximum(S*np.exp(-q*tau)-K*np.exp(-r*tau),0),'put':np.maximum(K*np.exp(-r*tau)-S*np.exp(-q*tau),0)}
    d1=(np.log(S/K)+(r-q+.5*sig*sig)*tau)/(sig*np.sqrt(tau)); d2=d1-sig*np.sqrt(tau)
    a=np.exp(-q*tau); b=np.exp(-r*tau); pdf=np.exp(-d1*d1/2)/np.sqrt(2*np.pi)
    return {'call':S*a*ndtr(d1)-K*b*ndtr(d2),'put':K*b*ndtr(-d2)-S*a*ndtr(-d1),'d1':d1,'d2':d2,'dc':a*ndtr(d1),'dp':-a*ndtr(-d1),'gamma':a*pdf/(S*sig*np.sqrt(tau)),'vega':S*a*pdf*np.sqrt(tau),'tc':-S*a*pdf*sig/(2*np.sqrt(tau))-r*K*b*ndtr(d2)+q*S*a*ndtr(d1),'tp':-S*a*pdf*sig/(2*np.sqrt(tau))+r*K*b*ndtr(-d2)-q*S*a*ndtr(-d1),'rc':K*tau*b*ndtr(d2),'rp':-K*tau*b*ndtr(-d2),'qc':-tau*S*a*ndtr(d1),'qp':tau*S*a*ndtr(-d1)}

def crr(S=100.,K=100.,r=.05,q=0.,sig=.2,tau=1.,n=400,put=True,american=True,boundary=False):
    if tau<=0: return max(K-S,0) if put else max(S-K,0)
    dt=tau/n; u=np.exp(sig*np.sqrt(dt)); d=1/u; p=(np.exp((r-q)*dt)-d)/(u-d); disc=np.exp(-r*dt)
    if not 0<p<1: raise ValueError('Invalid CRR probabilities')
    spots=S*np.exp((2*np.arange(n+1)-n)*sig*np.sqrt(dt))
    v=np.maximum(K-spots,0) if put else np.maximum(spots-K,0)
    frontier=[]; levels=[]
    for i in range(n-1,-1,-1):
        v=disc*(p*v[1:]+(1-p)*v[:-1]); spots=S*np.exp((2*np.arange(i+1)-i)*sig*np.sqrt(dt))
        intrinsic=np.maximum(K-spots,0) if put else np.maximum(spots-K,0)
        if boundary:
            exercise=(intrinsic>1e-10)&(intrinsic>=v-1e-10)
            if np.any(exercise): frontier.append((i*dt,float(np.max(spots[exercise]) if put else np.min(spots[exercise]))))
        if american: v=np.maximum(v,intrinsic)
        if n==3: levels.append({'i':i,'spots':spots.tolist(),'values':v.tolist()})
    return (float(v[0]),frontier,levels) if boundary else float(v[0])

FIGURES={}
def chart_data(fig):
    """Export plotted observations and SVG-space axes; never infer values from path pixels."""
    width,height=fig.get_size_inches()*72
    pixel_width,pixel_height=fig.get_size_inches()*fig.dpi
    result={'viewBox':[0,0,float(width),float(height)],'axes':[]}
    for ax in fig.axes:
        bx,by,bw,bh=ax.get_position().bounds
        series=[]
        def export_points(xy,transform):
            xy=np.asarray(xy,dtype=float)
            pixel=transform.transform(xy)
            data=ax.transData.inverted().transform(pixel)
            values=np.column_stack([data[:,0],data[:,1],pixel[:,0]*width/pixel_width,height-pixel[:,1]*height/pixel_height])
            values=values[np.isfinite(values).all(axis=1)]
            return [[float(v) for v in point] for point in values[np.argsort(values[:,2],kind='stable')]]
        for line in ax.lines:
            if line.get_label().startswith('_'): continue
            points=export_points(line.get_xydata(),line.get_transform())
            if len(points)<2: continue
            series.append({'label':line.get_label(),'color':line.get_color(),'mode':'snap' if len(points)>2 and (line.get_marker() not in [None,'','None','none',' '] or getattr(ax,'_hover_snap',False)) else 'line','points':points})
        for item in getattr(ax,'_hover_series',[]):
            series.append({**item,'points':export_points(item['points'],ax.transData)})
        if series:
            result['axes'].append({'box':[float(bx*width),float((1-by-bh)*height),float(bw*width),float(bh*height)],'xLabel':ax.get_xlabel().replace('$','').replace('S_T','Sₜ'),'yLabel':ax.get_ylabel().replace('$',''),'xScale':ax.get_xscale(),'yScale':ax.get_yscale(),'xFormat':getattr(ax,'_hover_xformat',None),'yFormat':getattr(ax,'_hover_yformat',None),'xlim':[float(v) for v in ax.get_xlim()],'ylim':[float(v) for v in ax.get_ylim()],'series':series})
    return result

def save(name,fig,caption,detail):
    fig.tight_layout(pad=1.5)
    hover_data=json.dumps(chart_data(fig),separators=(',',':'),allow_nan=False).replace('<',r'\u003c')
    buf=StringIO(); fig.savefig(buf,format='svg'); plt.close(fig)
    svg=buf.getvalue(); svg=svg[svg.index('<svg'):]
    # Prefix generated IDs so independently rendered SVGs can coexist.
    svg=re.sub(r'id="([^"]+)"',lambda m:'id="'+name+'-'+m[1]+'"',svg)
    svg=re.sub(r'url\(#([^)]+)\)',lambda m:'url(#'+name+'-'+m[1]+')',svg)
    svg=re.sub(r'(?:xlink:href|href)="#([^"]+)"',lambda m:'href="#'+name+'-'+m[1]+'"',svg)
    svg=svg.replace('<svg ',f'<svg role="img" aria-labelledby="{name}-title {name}-desc" ',1)
    p=svg.index('>')+1
    svg=svg[:p]+f'<title id="{name}-title">{caption}</title><desc id="{name}-desc">{detail}</desc>'+svg[p:]
    FIGURES[name]=f'<figure class="figure-card figure-wide"><div class="plot">{svg}</div><script type="application/json" class="chart-data">{hover_data}</script><figcaption><strong>{caption}</strong>{detail}</figcaption></figure>'

def axbase(ax,x,y,title=None):
    ax.set_xlabel(x); ax.set_ylabel(y); ax.grid(alpha=.6); ax.set_axisbelow(True)
    if title: ax.set_title(title,loc='left',pad=13)

