from figure_support import *
from surface import *
from matplotlib.ticker import PercentFormatter
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.integrate import quad

def percent(ax,x=False,y=False):
    if x:ax.xaxis.set_major_formatter(PercentFormatter(1));ax._hover_xformat='percent'
    if y:ax.yaxis.set_major_formatter(PercentFormatter(1));ax._hover_yformat='percent'
def finish(name,fig,title,detail):
    save(name,fig,'Figure 00 · '+title,detail)
k=np.linspace(-.6,.6,241);Ts=[.25,.5,1,2,3];colors=[ACC,BLUE,WARM,GRAY,'#bbbac7']
F=100*np.exp(.02);D=np.exp(-.03)
fig,axes=plt.subplots(1,2,figsize=(10,4))
vol=np.linspace(.001,.8,300)
for K,c in [(80,ACC),(100,BLUE),(120,WARM)]:
    axes[0].plot(vol,black(100,K,1,1,vol),color=c,label=f'K = {K}')
    axes[1].plot(vol,vega(100,K,1,1,vol),color=c,label=f'K = {K}')
for ax in axes:percent(ax,x=True);ax.legend(fontsize=8)
axbase(axes[0],'Implied volatility','Call premium','A monotone price-to-volatility map')
axbase(axes[1],'Implied volatility','Vega per unit volatility','Inversion is poorly conditioned at low vega')
finish('inverse',fig,'Black inversion and its conditioning','European calls; forward 100, discount factor 1, maturity one year. Vega is per 1.00 decimal volatility; divide by 100 for one volatility percentage point.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
K=np.linspace(55,145,241)
for T,c in [(.05,ACC),(.25,BLUE),(1,WARM)]:
    axes[0].plot(K,vega(100,K,1,T,.2),color=c,label=f'T = {T:g}y')
    axes[1].plot(K,.02/np.maximum(vega(100,K,1,T,.2),1e-10),color=c,label=f'T = {T:g}y')
axes[1].set_ylim(0,.025);percent(axes[1],y=True)
axbase(axes[0],'Strike','Vega per unit volatility','Short-dated wings contain little IV information')
axbase(axes[1],'Strike','Approximate IV half-width','A premium half-spread of 0.02')
for ax in axes:ax.legend(fontsize=8)
finish('vega',fig,'Quote uncertainty amplified by inversion','Forward 100, discount factor 1, volatility 20%; first-order IV half-width is 0.02 divided by vega. Values above 2.5 volatility points are clipped visually and excluded from the coordinate readout.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
for T,c in zip(Ts,colors):
    s=ssvi(k,T)
    axes[0].plot(100*np.exp(.02*T+k),s['sigma'],color=c,label=f'{T:g}y')
    axes[1].plot(k,s['w'],color=c,label=f'{T:g}y')
percent(axes[0],y=True)
axbase(axes[0],'Strike','Implied volatility','Strike coordinates depend on the forward')
axbase(axes[1],'Log-forward moneyness k','Total variance w','A common coordinate for every expiry')
for ax in axes:ax.legend(fontsize=8)
finish('coordinates',fig,'Volatility and total-variance coordinates','Synthetic SSVI reference surface; spot 100, continuous rate 3% and yield 1%. Maturities 0.25, 0.5, 1, 2 and 3 years; w = sigma squared times T.')

fig,ax=plt.subplots(figsize=(10,4))
for rho,c in [(-.65,ACC),(0,BLUE),(.65,WARM)]:
    ax.plot(k,ssvi(k,1,{**DEFAULT,'rho':rho})['sigma'],color=c,label=f'rho = {rho:g}')
percent(ax,y=True);axbase(ax,'Log-forward moneyness k','Implied volatility','Changing asymmetry at fixed ATM total variance');ax.legend(fontsize=8)
finish('skew',fig,'Smile asymmetry and the correlation parameter','Three synthetic SSVI slices at one year. Rho controls asymmetry in this parameterization; it is not an estimated physical correlation of an observed market.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
t=np.linspace(.02,5,250)
for p,c,label in [(DEFAULT,ACC,'24% short / 18% long'),({**DEFAULT,'short':.16,'long':.26},WARM,'16% short / 26% long')]:
    axes[0].plot(t,np.sqrt(theta(t,p)/t),color=c,label=label)
    axes[1].plot(t,theta(t,p),color=c,label=label)
percent(axes[0],y=True)
axbase(axes[0],'Maturity (years)','ATM implied volatility','Volatility may fall with maturity')
axbase(axes[1],'Maturity (years)','ATM total variance','Accumulated variance still increases')
for ax in axes:ax.legend(fontsize=8)
finish('term',fig,'Volatility term structure versus accumulated variance','Theta(T) integrates a positive decaying variance rate. Both examples have increasing total variance; a decreasing ATM volatility is not by itself calendar arbitrage.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
strikes=np.linspace(65,135,29);p0=black(F,strikes,D,1,ssvi(np.log(strikes/F),1)['sigma'])
axes[0].plot(strikes,p0-.04,color=GRAY,label='Synthetic bid');axes[0].plot(strikes,p0+.04,color=ACC,label='Synthetic ask')
vv=vega(F,strikes,D,1,ssvi(np.log(strikes/F),1)['sigma'])
axes[1].plot(strikes,ssvi(np.log(strikes/F),1)['sigma']-.04/vv,color=GRAY,label='First-order bid IV')
axes[1].plot(strikes,ssvi(np.log(strikes/F),1)['sigma']+.04/vv,color=ACC,label='First-order ask IV')
percent(axes[1],y=True)
axbase(axes[0],'Strike','Call premium','A constant premium half-spread')
axbase(axes[1],'Strike','Implied volatility','Different uncertainty in volatility units')
for ax in axes:ax.legend(fontsize=8)
finish('quotes',fig,'Premium and volatility quote intervals','Synthetic one-year calls; premium half-spread 0.04. IV curves use a first-order vega conversion, not an exact bound inversion. Every premium bid in the shown range remains above its intrinsic lower bound.')

fig,ax=plt.subplots(figsize=(10,4))
strikes=np.linspace(75,125,151);smile=ssvi(np.log(strikes/F),1)['sigma'];calls=black(F,strikes,D,1,smile)
for f,c,label in [(F,ACC,'Correct forward'),(100,BLUE,'Forward understated'),(104,WARM,'Forward overstated')]:
    out=[]
    for P,K in zip(calls,strikes):
        try:out.append(implied(P,f,K,D,1))
        except ValueError:out.append(np.nan)
    ax.plot(strikes,out,color=c,label=label)
percent(ax,y=True);axbase(ax,'Strike','Recovered call IV','A carry error distorts the recovered smile');ax.legend(fontsize=8)
finish('forward',fig,'Forward-input errors and implied volatility','The same synthetic call premiums are inverted with three forwards. True spot 100, rate 3%, yield 1%, T = 1; the correct forward is about 102.0201. These differences are input errors, not changes in market option prices.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
strikes=np.linspace(45,160,350);call=black(F,strikes,D,1,ssvi(np.log(strikes/F),1)['sigma'])
axes[0].plot(strikes,call,color=ACC,label='Call curve')
axes[0].plot(strikes,D*np.maximum(F-strikes,0),color=GRAY,ls='--',label='Lower bound')
h=1e-3;der=(black(F,strikes+h,D,1,ssvi(np.log((strikes+h)/F),1)['sigma'])-black(F,strikes-h,D,1,ssvi(np.log((strikes-h)/F),1)['sigma']))/(2*h)
axes[1].plot(strikes,der,color=ACC,label='Strike derivative')
axes[1].axhline(-D,color=WARM,ls='--',label='Lower slope bound');axes[1].axhline(0,color=GRAY,lw=1)
for ax in axes:ax.legend(fontsize=8)
axbase(axes[0],'Strike','Call premium','Bounds and decreasing strike prices')
axbase(axes[1],'Strike','dC / dK','Vertical spreads constrain the slope')
finish('vertical',fig,'Call-price bounds and vertical-spread conditions','Reference SSVI, maturity one year. The strike derivative is a central difference with absolute strike step 0.001. Its no-arbitrage range is [-D, 0].')

fig,axes=plt.subplots(1,2,figsize=(10,4))
bad={**DEFAULT,'eta':12}
for p,c,label in [(DEFAULT,ACC,'Reference eta 2.3'),(bad,WARM,'Unconstrained eta 12')]:
    s=ssvi(k,3,p);axes[0].plot(k,s['sigma'],color=c,label=label);axes[1].plot(k,s['g'],color=c,label=label)
axes[1].axhline(0,color=GRAY,ls='--');percent(axes[0],y=True)
for ax in axes:ax.legend(fontsize=8)
axbase(axes[0],'Log-forward moneyness k','Implied volatility','A positive smile can be inconsistent')
axbase(axes[1],'Log-forward moneyness k','Butterfly diagnostic g(k)','Negative g implies negative strike density')
finish('butterfly',fig,'Positive volatility does not guarantee convex option prices','Three-year slices with the same ATM term structure and rho -0.65; only eta changes. The eta 12 example is intentionally invalid. Analytic derivatives of total variance are used in g.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
v1=.30-.09*k;v2=.18-.03*k
for vol,T,c,label in [(v1,.5,ACC,'0.5y / high IV'),(v2,1,WARM,'1y / low IV')]:
    axes[0].plot(k,vol,color=c,label=label);axes[1].plot(k,vol*vol*T,color=c,label=label)
percent(axes[0],y=True)
for ax in axes:ax.legend(fontsize=8)
axbase(axes[0],'Log-forward moneyness k','Implied volatility','Two individually positive smiles')
axbase(axes[1],'Log-forward moneyness k','Total variance','The later variance falls below the earlier')
finish('calendar',fig,'An intentionally inconsistent expiry pair','Toy smiles are constructed directly in volatility units. At k = 0, six-month total variance is 0.045 and one-year total variance is 0.0324. Under the deterministic proportional-carry framework, this violates calendar ordering.')

fig,ax=plt.subplots(figsize=(10,4))
strikes=np.linspace(30,200,501)
ax.plot(strikes,density(strikes,1,F),color=ACC,label='SSVI strike density')
flat=DEFAULT.copy();flat['eta']=0
ax.plot(strikes,density(strikes,1,F,flat),color=BLUE,label='Flat smile with same ATM variance')
axbase(ax,'Terminal price / strike','Density per price unit','Option curvature identifies a pricing distribution');ax.legend(fontsize=8)
finish('density',fig,'Risk-neutral terminal densities','European one-year option surface; both curves use the same forward and ATM total variance. Densities are analytic derivatives of call prices. Risk-neutral probability differs from a physical return forecast.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
nodes=np.array([-.5,-.3,-.1,0,.15,.3,.5]);wn=ssvi(nodes,1)['w'];wn[3]+=.004
cs=CubicSpline(nodes,wn);pch=PchipInterpolator(nodes,wn);ki=np.linspace(nodes[0],nodes[-1],241)
for w,wk,wkk,c,label in [(cs(ki),cs(ki,1),cs(ki,2),WARM,'Unconstrained cubic'),(pch(ki),pch(ki,1),pch(ki,2),BLUE,'PCHIP variance')]:
    axes[0].plot(ki,w,color=c,label=label)
    g=(1-ki*wk/(2*w))**2-wk*wk/4*(1/w+.25)+wkk/2
    axes[1].plot(ki,g,color=c,label=label)
axes[0].plot(nodes,wn,'o',color=ACC,label='Perturbed nodes');axes[1].axhline(0,color=GRAY,ls='--')
for ax in axes:ax.legend(fontsize=8)
axbase(axes[0],'Log-forward moneyness k','Total variance','A small node distortion affects derivatives')
axbase(axes[1],'Log-forward moneyness k','Butterfly diagnostic g(k)','Shape preservation is not an arbitrage proof')
finish('interpolation',fig,'Interpolation and derivative instability','One-year reference nodes with +0.004 total variance added at k = 0. Cubic and PCHIP interpolation are illustrated over their node domain only; neither method imposes the option-price convexity constraint.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
par=np.array([.015,.05,-.6,.04,.25])
for shift,c,label in [(0,ACC,'Baseline'),(.08,BLUE,'Higher b'),(-.08,WARM,'Lower rho')]:
    pp=par.copy()
    if shift>0:pp[1]+=.03
    if shift<0:pp[2]-=.25
    axes[0].plot(k,svi(k,pp),color=c,label=label)
    axes[1].plot(k,svi_g(k,pp),color=c,label=label)
axes[1].axhline(0,color=GRAY,ls='--')
for ax in axes:ax.legend(fontsize=8)
axbase(axes[0],'Log-forward moneyness k','Total variance','Five parameters act jointly')
axbase(axes[1],'Log-forward moneyness k','Butterfly diagnostic g(k)','Validate each candidate after changing shape')
finish('svi',fig,'Raw SVI parameter changes','Baseline (a,b,rho,m,s) = (0.015,0.05,-0.6,0.04,0.25). The second curve raises b to 0.08; the third lowers rho to -0.85. Positivity conditions alone do not establish no arbitrage.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
for T,c in zip(Ts,colors):
    s=ssvi(k,T);axes[0].plot(k,s['sigma'],color=c,label=f'{T:g}y');axes[1].plot(k,s['w'],color=c,label=f'{T:g}y')
percent(axes[0],y=True)
for ax in axes:ax.legend(fontsize=8)
axbase(axes[0],'Log-forward moneyness k','Implied volatility','Coherent slices of one synthetic surface')
axbase(axes[1],'Log-forward moneyness k','Total variance','Calendar-ordered slices at common k')
finish('ssvi',fig,'The reference SSVI surface as maturity slices','Short variance rate 24% squared, long variance rate 18% squared, decay 1.2 years, rho -0.65 and eta 2.3; phi(theta) = eta / (1 + theta). Both global sufficient butterfly bounds pass.')

fit=calibration()
fig,axes=plt.subplots(1,2,figsize=(10,4))
axes[0].plot(k,np.sqrt(svi(k,fit['params'])),color=ACC,label='Fitted raw SVI')
for mask,c,label in [(fit['train'],BLUE,'Calibration quotes'),(~fit['train'],WARM,'Withheld quotes')]:
    axes[0].plot(fit['k'][mask],fit['observed'][mask],'o',color=c,label=label)
    axes[1].plot(fit['k'][mask],10000*(fit['pred'][mask]-fit['observed'][mask]),'o-',color=c,label=label)
percent(axes[0],y=True);axes[1].axhline(0,color=GRAY,ls='--')
for ax in axes:ax.legend(fontsize=8)
axbase(axes[0],'Log-forward moneyness k','Implied volatility','A noisy synthetic one-year slice')
axbase(axes[1],'Log-forward moneyness k','IV residual (basis points)','Quote error and model fit are distinct')
finish('calibration',fig,'Raw SVI calibration with withheld strikes','17 deterministic noisy IV quotes on k in [-0.4,0.4]; indices congruent to 2 modulo 4 are withheld. Fit minimizes equal-weight squared total-variance residuals on 13 calibration quotes using four optimizer starts. One IV basis point is 0.0001 decimal volatility.')

fig,ax=plt.subplots(figsize=(10,4))
wide=np.linspace(-5,5,501);s=ssvi(wide,1)
ax.plot(wide,s['w'],color=ACC,label='Reference total variance')
th=theta(1);ph=DEFAULT['eta']/(1+th)
ax.plot(wide,th/2+th*ph/2*(1+abs(DEFAULT['rho']))*np.abs(wide),color=GRAY,ls='--',label='Largest wing slope guide')
ax.plot(wide,2*np.abs(wide),color=WARM,ls=':',label='Slope-2 asymptotic guide')
ax.set_ylim(0,.8);axbase(ax,'Log-forward moneyness k','Total variance','Wing behavior is a tail assumption');ax.legend(fontsize=8)
finish('wings',fig,'Total-variance wing behavior','Reference one-year SSVI continued to k in [-5,5]. The slope-2 line is an asymptotic comparison, not a pointwise upper bound at finite strikes; portions above the plotted range are clipped.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
for T,c in [(.25,ACC),(1,BLUE),(3,WARM)]:
    s=ssvi(k,T);axes[0].plot(k,s['sigma'],color=c,label=f'Implied {T:g}y');axes[1].plot(k,s['local'],color=c,label=f'Local at {T:g}y')
for ax in axes:percent(ax,y=True);ax.legend(fontsize=8)
axbase(axes[0],'Log-forward moneyness k','Implied volatility','A contract-level price coordinate')
axbase(axes[1],'Log-forward moneyness k','Local volatility','A diffusion coefficient recovered from derivatives')
finish('local',fig,'Implied versus local volatility','Reference SSVI. Local variance equals partial-T total variance at fixed k divided by g(k), under deterministic proportional carry and the smooth local-diffusion assumptions. All shown values use analytic derivatives.')

fig,ax=plt.subplots(figsize=(10,4))
spots=np.linspace(85,115,201);K=100;T=1
sig0=float(ssvi(np.log(K/F),T)['sigma'])
pricessticky=black(spots*np.exp(.02),K,D,T,sig0)
pricesmoney=black(spots*np.exp(.02),K,D,T,ssvi(np.log(K/(spots*np.exp(.02))),T)['sigma'])
h=.001
ax.plot(spots,np.gradient(pricessticky,spots),color=BLUE,label='Sticky strike delta')
ax.plot(spots,np.gradient(pricesmoney,spots),color=ACC,label='Sticky log-moneyness delta')
axbase(ax,'Spot','Call delta','A smile-motion assumption changes the hedge');ax.legend(fontsize=8)
finish('hedge',fig,'Surface-aware spot sensitivities','One-year strike 100; rate 3%, yield 1%. Sticky strike holds this option IV constant; sticky log-moneyness keeps sigma(k,T) fixed while the forward changes with spot. Numerical gradients use a 0.15 spot grid; endpoints are one-sided.')

fig,axes=plt.subplots(1,2,figsize=(10,4))
t=np.linspace(.01,1.5,301);event=.25;w=.04*t+.01*(t>=event);base=.04*t
axes[0].plot(t,np.sqrt(base/t),color=BLUE,label='Diffusive baseline')
axes[0].plot(t,np.sqrt(w/t),color=WARM,label='With an event variance increment')
axes[1].plot(t,base,color=BLUE,label='Diffusive baseline');axes[1].plot(t,w,color=WARM,label='With an event variance increment')
for ax in axes:percent(ax,y=ax==axes[0]);ax._hover_snap=True;ax.legend(fontsize=8);ax.axvline(event,color=GRAY,ls='--')
axbase(axes[0],'Maturity (years)','ATM implied volatility','Annualization emphasizes a short-dated event')
axbase(axes[1],'Maturity (years)','ATM total variance','An additive variance-budget illustration')
finish('event',fig,'A scheduled-event variance budget','Toy ATM variance w(T) = 0.04 T + 0.01 once T reaches 0.25 years. This is a discrete jump in a variance budget, not an exact option-pricing formula for an arbitrary jump distribution; the smooth Dupire formula cannot be applied at the jump.')

(ROOT/'figures.json').write_text(json.dumps(FIGURES,ensure_ascii=False),encoding='utf-8')
rows=[]
for T in Ts:
    f=100*np.exp(.02*T);d=np.exp(-.03*T)
    for kval in [-.2,0,.2]:
        v=float(ssvi(kval,T)['sigma']);strike=f*np.exp(kval);c=float(black(f,strike,d,T,v));put=float(black(f,strike,d,T,v,True))
        rows.append(dict(T=T,k=kval,F=float(f),K=float(strike),D=float(d),sigma=v,w=v*v*T,call=c,put=put,iv=implied(c,f,strike,d,T),vega=float(vega(f,strike,d,T,v))))
mass=quad(lambda x:float(density(np.exp(x),1,F))*np.exp(x),-12,12,epsabs=1e-10)[0]
mean=quad(lambda x:float(density(np.exp(x),1,F))*np.exp(2*x),-12,12,epsabs=1e-9)[0]
data={'rows':rows,'parameters':DEFAULT,'bounds':bounds(),'density_mass':mass,'density_mean':mean,
      'calibration':{a:(b.tolist() if isinstance(b,np.ndarray) else b) for a,b in fit.items()}}
(ROOT/'computed.json').write_text(json.dumps(data,allow_nan=False,indent=2),encoding='utf-8')
print('Generated',len(FIGURES),'figures; density mass',mass,'mean',mean)
