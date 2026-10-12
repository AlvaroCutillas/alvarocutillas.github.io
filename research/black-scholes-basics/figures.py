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
            result['axes'].append({'box':[float(bx*width),float((1-by-bh)*height),float(bw*width),float(bh*height)],'xLabel':ax.get_xlabel().replace('$','').replace('S_T','Sₜ'),'yLabel':ax.get_ylabel().replace('$',''),'xScale':ax.get_xscale(),'yScale':ax.get_yscale(),'xlim':[float(v) for v in ax.get_xlim()],'ylim':[float(v) for v in ax.get_ylim()],'series':series})
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

def build():
    xs=np.linspace(50,150,401); b=bs(); outputs={'benchmark':{k:float(v) for k,v in b.items()}}
    # 1. Payoff versus funded P&L.
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.4))
    for ax,key,intr,title in [(axes[0],'call',np.maximum(xs-100,0),'Long call'),(axes[1],'put',np.maximum(100-xs,0),'Long put')]:
        ax.plot(xs,intr,color=ACC,label='Terminal payoff'); ax.plot(xs,intr-b[key]*np.exp(.05),color=WARM,label='P&L (premium financed at 5%)'); ax.axhline(0,color='#596159',lw=.8); ax.axvline(100,color=GRAY,lw=.8,ls=':'); axbase(ax,'Terminal spot $S_T$','Currency units',title); ax.legend(loc='upper left' if key=='call' else 'upper right',fontsize=7.5)
    save('payoffs',fig,'Figure 01 · Payoff is not profit','K = 100, S₀ = 100, r = 5%, q = 0, σ = 20%, τ = 1 year. Profit subtracts the premium grown to maturity; the two break-even spots are therefore not simply the strike.')
    # 2. Time smoothing.
    fig,ax=plt.subplots(figsize=(9.2,3.65))
    for tau,c in [(1,ACC),(.25,WARM),(.02,BLUE)]: ax.plot(xs,bs(S=xs,tau=tau)['call'],color=c,label=f'European call · τ = {tau:g}')
    ax.plot(xs,np.maximum(xs-100,0),color='#818781',ls='--',lw=1.3,label='Expiry payoff'); axbase(ax,'Spot S','Call value'); ax.legend(fontsize=8)
    save('smoothing',fig,'Figure 02 · The payoff kink becomes a smooth value function','K = 100, r = 5%, q = 0, σ = 20%. A longer maturity changes both uncertainty and carry; it is not only a graphical smoothing parameter.')
    # 3. GBM paths and terminal distribution.
    rng=np.random.default_rng(1973); t=np.linspace(0,1,253); steps=rng.normal(size=(10,252)); paths=100*np.exp(np.cumsum((.05-.5*.2**2)/252+.2/np.sqrt(252)*steps,axis=1)); paths=np.column_stack([np.full(10,100),paths])
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.6),gridspec_kw={'width_ratios':[1.35,1]})
    for i,path in enumerate(paths): axes[0].plot(t,path,color=[ACC,WARM,GRAY,BLUE][i%4],alpha=.6,lw=1,label=f'Path {i+1:02d}')
    axbase(axes[0],'Time (years)','Spot','Ten risk-neutral GBM paths')
    st=np.linspace(35,190,500); den=np.exp(-.5*((np.log(st/100)-(.05-.5*.2**2))/.2)**2)/(st*.2*np.sqrt(2*np.pi))
    axes[1].plot(st,den,color=ACC,label='Risk-neutral density'); axes[1].fill_between(st,den,where=st>100,color=ACC,alpha=.15); axes[1].axvline(100,color=WARM,ls='--',lw=1); axbase(axes[1],'Terminal spot','Density','Lognormal terminal distribution')
    save('gbm',fig,'Figure 03 · Continuous paths, lognormal prices','S₀ = K = 100, r = 5%, q = 0, σ = 20%, T = 1; random seed 1973. The shaded right tail is the event S_T > K. These are model simulations, not market observations.')
    # 4. Greeks.
    fig,axes=plt.subplots(2,2,figsize=(9.2,6.0))
    for tau,c in [(1,ACC),(.25,WARM),(.02,BLUE)]:
        z=bs(S=xs,tau=tau)
        for ax,key in zip(axes.flat,['dc','gamma','vega','tc']): ax.plot(xs,z[key]/(100 if key=='vega' else 1),color=c,label=f'τ = {tau:g}')
    for ax,lab in zip(axes.flat,['Call delta (shares)','Gamma (per spot unit)','Vega (per 1 vol point)','Call theta (per year)']): axbase(ax,'Spot S',lab); ax.axvline(100,color='#565e57',lw=.7,ls=':'); ax.legend(fontsize=7)
    save('greeks',fig,'Figure 04 · Sensitivities respond differently to maturity','K = 100, r = 5%, q = 0, σ = 20%. Gamma concentrates near the strike as expiry approaches; vega tends to zero. Theta uses calendar time, ∂V/∂t, and is shown per year.')
    # 5. Delta tangent.
    fig,ax=plt.subplots(figsize=(9.2,3.6)); xr=np.linspace(75,125,301); curve=bs(S=xr)['call']; tangent=b['call']+b['dc']*(xr-100); quad=tangent+.5*b['gamma']*(xr-100)**2
    ax.plot(xr,curve,color=ACC,label='Exact call'); ax.plot(xr,tangent,color=WARM,label='Delta approximation'); ax.plot(xr,quad,color=BLUE,ls='--',label='Delta + gamma'); ax.scatter([100],[b['call']],color=ACC,s=25); axbase(ax,'Spot S (other inputs fixed)','Call value'); ax.legend(fontsize=8)
    save('tangent',fig,'Figure 05 · Delta matches the tangent, gamma matches local curvature','Expansion about S = 100 for the one-year benchmark. The quadratic approximation improves nearby moves, but it is still a local approximation and does not account for time or volatility changes.')
    # 6. Discrete hedge error distribution, financing and q=0.
    hedge={}; rng=np.random.default_rng(42)
    for n in [12,52,252]:
        paths=5000; spot=np.full(paths,100.); delta=np.full(paths,b['dc']); cash=np.full(paths,b['call']-100*b['dc']); dt=1/n
        for i in range(n):
            spot*=np.exp((.05-.5*.2**2)*dt+.2*np.sqrt(dt)*rng.normal(size=paths)); cash*=np.exp(.05*dt)
            if i<n-1:
                new=bs(S=spot,tau=1-(i+1)*dt)['dc']; cash-=(new-delta)*spot; delta=new
        err=delta*spot+cash-np.maximum(spot-100,0); hedge[n]=err
    fig,ax=plt.subplots(figsize=(9.2,3.65))
    ax._hover_series=[]
    for n,c in zip([12,52,252],[WARM,BLUE,ACC]):
        values,edges,_=ax.hist(hedge[n],bins=np.linspace(-5,5,101),density=True,histtype='step',color=c,lw=1.7,label=f'{n} rebalances · SD = {hedge[n].std(ddof=1):.3f}')
        ax._hover_series.append({'label':f'{n} rebalances','color':c,'mode':'step','bins':edges.tolist(),'points':np.column_stack([(edges[:-1]+edges[1:])/2,values]).tolist()})
    axbase(ax,'Replication portfolio − terminal call payoff','Empirical density'); ax.legend(fontsize=8)
    save('hedging',fig,'Figure 06 · More frequent hedging reduces discretisation error in this model','5,000 GBM paths for each schedule; S₀ = K = 100, r = 5%, q = 0, σ = 20%, T = 1, seed 42. Every rebalance is self-financing. No transaction costs or jumps; the histogram window is −5 to +5.')
    # 7. Price-vol and synthetic smile.
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.5)); vs=np.linspace(.001,.8,240); vals=np.array([bs(sig=s)['call'] for s in vs]); axes[0].plot(vs*100,vals,color=ACC,label='European call'); axes[0].scatter([20],[b['call']],color=WARM,s=25); axes[0].axhline(b['call'],color=WARM,ls=':',lw=.8,label='Benchmark value'); axbase(axes[0],'Volatility (%)','Call value','Implied volatility is an inverse problem')
    k=np.linspace(60,140,200); smile=.2-.12*np.log(k/100)+.35*np.log(k/100)**2; axes[1].plot(k,smile*100,color=WARM,label='Illustrative smile'); axes[1].axhline(20,color=ACC,ls='--',label='Constant BSM volatility'); axbase(axes[1],'Strike K','Implied volatility (%)','Flat model versus a synthetic smile'); axes[1].legend(fontsize=7.5)
    save('iv',fig,'Figure 07 · A unique implied volatility for each admissible European price','Left: benchmark call value as σ varies. Right: a deliberately synthetic strike-dependent volatility curve, not observed quotes or a calibrated arbitrage-free surface.')
    # 8. American vs European.
    x=np.linspace(45,150,140); am=np.array([crr(S=s,n=600) for s in x]); eu=bs(S=x)['put']; intr=np.maximum(100-x,0)
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.65)); axes[0].plot(x,am,color=ACC,label='American put · CRR 600'); axes[0].plot(x,eu,color=WARM,label='European put · BSM'); axes[0].plot(x,intr,color=GRAY,ls='--',label='Immediate exercise'); axbase(axes[0],'Spot S','Put value'); axes[0].legend(fontsize=7.5)
    axes[1].plot(x,am-eu,color=ACC,label='Early-exercise premium'); axbase(axes[1],'Spot S','Early-exercise premium'); axes[1].set_ylim(bottom=0)
    save('american',fig,'Figure 08 · American puts add the value of an exercise decision','K = 100, r = 5%, q = 0, σ = 20%, τ = 1. The American curve uses 600 CRR steps; its small discretisation effects are separate from the analytical European value.')
    # 9. Exercise boundary on one lattice.
    price,frontier,_=crr(n=1600,boundary=True); fr=np.array(frontier); fig,ax=plt.subplots(figsize=(9.2,3.8)); ax._hover_snap=True; ax.fill_between(fr[:,0],0,fr[:,1],color=ACC,alpha=.07); ax.plot(fr[:,0],fr[:,1],color=ACC,lw=1.1,label='Highest exercise node · CRR 1,600'); ax.axhline(100,color=WARM,ls='--',lw=1,label='Expiry threshold K'); ax.set_ylim(65,103); ax.set_xlim(0,1); ax.text(.35,73,'EXERCISE: S ≤ boundary',color=ACC,fontsize=9); ax.text(.35,95,'CONTINUE: S > boundary',color='#b7bdb6',fontsize=9); axbase(ax,'Calendar time t (T = 1)','Put exercise boundary'); ax.legend(loc='upper left',fontsize=8)
    save('boundary',fig,'Figure 09 · The exercise frontier is part of the solution','S₀ = K = 100, r = 5%, q = 0, σ = 20%, T = 1. This is the highest exercise node at each time level of a 1,600-step CRR lattice, not a smoothed exact boundary. The last pre-expiry nodes approach K; the sawtooth pattern reflects the lattice.')
    # 10. CRR convergence.
    ns=[25,50,100,200,400,800,1600]; conv=[]
    for n in ns: conv.append({'n':n,'ec':crr(n=n,put=False,american=False),'ac':crr(n=n,put=False),'ep':crr(n=n,american=False),'ap':crr(n=n)})
    outputs['convergence']=conv
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.65)); axes[0].plot(ns,[v['ep'] for v in conv],color=WARM,marker='o',ms=3,label='European put · CRR'); axes[0].axhline(b['put'],color=GRAY,ls='--',label='European put · BSM'); axes[0].plot(ns,[v['ap'] for v in conv],color=ACC,marker='o',ms=3,label='American put · CRR'); axbase(axes[0],'Tree steps N','Put price'); axes[0].set_xscale('log'); axes[0].legend(fontsize=7.5)
    axes[1].plot(ns,[v['ec']-b['call'] for v in conv],color=ACC,marker='o',ms=3,label='Call pricing error'); axes[1].axhline(0,color=GRAY,ls='--',lw=1,label='Zero error'); axes[1].set_xscale('log'); axbase(axes[1],'Tree steps N','CRR call − exact call')
    save('convergence',fig,'Figure 10 · Convergence is evidence, not an assumption','One-year benchmark, q = 0. Odd and even trees can approach the limit differently, as N = 25 illustrates. European prices have an exact reference; American put values require convergence checks.')
    # 11. American dividend call comparison.
    qs=np.linspace(0,.12,61); ce=np.array([bs(q=q)['call'] for q in qs]); ca=np.array([crr(q=q,put=False,n=800) for q in qs]); fig,ax=plt.subplots(figsize=(9.2,3.6)); ax.plot(qs*100,ce,color=WARM,label='European call · BSM'); ax.plot(qs*100,ca,color=ACC,label='American call · CRR 800'); axbase(ax,'Continuous dividend yield q (%)','Call value'); ax.legend(fontsize=8)
    save('dividends',fig,'Figure 11 · Dividends reduce call value and can make early exercise valuable','S₀ = K = 100, r = 5%, σ = 20%, τ = 1. Continuous yield q varies; this graph does not model discrete cash dividends. With q = 0 and non-negative rates, both exercise styles have the same continuous-time value.')
    # 12. Monte Carlo standard error scaling.
    rng=np.random.default_rng(73); z=rng.normal(size=100000); Y=np.exp(-.05)*np.maximum(100*np.exp((.05-.02)+.2*z)-100,0); ns_mc=np.array([100,500,1000,5000,10000,50000,100000]); se=np.array([Y[:n].std(ddof=1)/np.sqrt(n) for n in ns_mc]); fig,ax=plt.subplots(figsize=(9.2,3.4)); ax.loglog(ns_mc,se,color=ACC,marker='o',ms=4,label='Estimated standard error'); ax.loglog(ns_mc,Y.std(ddof=1)/np.sqrt(ns_mc),color=WARM,ls='--',label='1 / √M reference'); axbase(ax,'Simulation paths M','Price standard error'); ax.legend(fontsize=8)
    save('mc',fig,'Figure 12 · Monte Carlo accuracy grows slowly with sample size','European benchmark call; exact terminal GBM sampling, seed 73. Standard errors are estimated from discounted payoffs. Multiplying M by four approximately halves the standard error.')
    # 13. Strike convexity and density.
    k=np.linspace(50,160,500); vals=bs(K=k)['call']; density=np.exp(-.5*((np.log(k/100)-.03)/.2)**2)/(k*.2*np.sqrt(2*np.pi)); fig,axes=plt.subplots(1,2,figsize=(9.2,3.5)); axes[0].plot(k,vals,color=ACC,label='European call'); axbase(axes[0],'Strike K','European call value','Decreasing and convex in strike'); axes[1].plot(k,np.exp(-.05)*density,color=WARM,label='Discounted density'); axbase(axes[1],'Strike K','∂²C / ∂K²','Discounted risk-neutral density')
    save('density',fig,'Figure 13 · The cross-section of strikes encodes a distribution','S₀ = 100, r = 5%, q = 0, σ = 20%, τ = 1. For a smooth European call price function, its second strike derivative equals e^(−rτ) times the risk-neutral terminal density.')
    outputs['dividend_benchmark']={k:float(v) for k,v in bs(q=.02).items()}
    outputs['american_dividend_call']={'european':float(bs(q=.08)['call']),'american':crr(q=.08,put=False,n=1600)}
    outputs['american_put_1600']=price
    _,_,levels=crr(n=3,boundary=True); outputs['tree3']=levels
    outputs['mc']={'estimate':float(Y.mean()),'se':float(Y.std(ddof=1)/np.sqrt(len(Y)))}
    (ROOT/'computed.json').write_text(json.dumps(outputs,indent=2),encoding='utf-8')
    (ROOT/'figures.json').write_text(json.dumps(FIGURES),encoding='utf-8')
    return outputs

if __name__=='__main__':
    out=build(); print(json.dumps(out,indent=2))
