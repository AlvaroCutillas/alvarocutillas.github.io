from figure_support import *
from model import curve,loadings,design,par,bond,REFERENCE,quotes
from scipy.interpolate import CubicSpline, PchipInterpolator
from matplotlib.ticker import PercentFormatter
data=json.loads((ROOT/'computed.json').read_text())
T=np.linspace(0,30,601)
def rate_axis(ax): ax.yaxis.set_major_formatter(PercentFormatter(1)); ax._hover_yformat='percent'
def legend(ax): ax.legend(fontsize=8,loc='best')
def done(name,fig,title,detail): save(name,fig,'Figure 00 · '+title,detail)

fig,axs=plt.subplots(1,2,figsize=(11,3.7))
for z,col in zip([.01,.03,.05],[BLUE,ACC,WARM]):
    axs[0].plot(T,np.exp(-z*T),color=col,label=f'Flat zero {100*z:g}%')
axs[1].plot(T,curve(T)[0],color=ACC,label='Continuous zero')
axs[1].plot(T,2*np.expm1(curve(T)[0]/2),color=WARM,label='Nominal semiannual')
axbase(axs[0],'Maturity (years)','Discount factor','Time changes the value of a unit')
axbase(axs[1],'Maturity (years)','Annual rate','Same discount factors, different quotation')
rate_axis(axs[1]);[legend(a) for a in axs]
done('discount',fig,'Discount factors and compounding conventions','Left: three flat continuous-rate curves. Right: reference Svensson zero rates and their nominal semiannual equivalents; the difference is a convention, not a different price.')

fig,ax=plt.subplots(figsize=(11,3.6))
z,f,d=curve(T);ax.plot(T,z,color=ACC,label='Zero rate');ax.plot(T,f,color=WARM,label='Instantaneous forward')
axbase(ax,'Maturity (years)','Continuous annual rate','A zero rate averages the forward curve');rate_axis(ax);legend(ax)
done('forwards',fig,'Zero rates and instantaneous forwards','Reference parameters: β₀ = 3.5%, β₁ = −2%, β₂ = 2.5%, β₃ = −1.5%, τ₁ = 1.6 years, τ₂ = 6.5 years. A rising zero curve implies its marginal forward exceeds its average.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7))
tp=np.arange(.5,30.1,.5)
axs[0].plot(tp,curve(tp)[0],color=ACC,label='Continuous zero')
axs[0].plot(tp,[2*np.log1p(par(t)/2) for t in tp],color=WARM,label='Par, continuous equivalent')
for c,col in zip([0,.04,.08],[BLUE,ACC,WARM]):
    axs[1].plot(tp,[bond(T=t,c=c)['ytm'] for t in tp],color=col,label=f'{100*c:g}% coupon YTM')
axbase(axs[0],'Maturity (years)','Annual rate','Par rates weight coupon-date discounts')
axbase(axs[1],'Maturity (years)','Nominal semiannual YTM','Coupon structure changes the single yield')
[rate_axis(a) for a in axs];[legend(a) for a in axs]
done('par',fig,'Par yields, zero rates and bond yields to maturity','Every bond is priced on the same reference curve. Left: par coupon rates converted to a continuous convention for comparison. Right: YTMs retain their nominal semiannual convention.')

fig,ax=plt.subplots(figsize=(11,3.5))
t=np.linspace(0,.999,201)
for c,col in zip([.02,.04,.06],[BLUE,ACC,WARM]):
    ax.plot(t,100*c/2*t,color=col,label=f'{100*c:g}% annual coupon')
axbase(ax,'Fraction of coupon period elapsed','Accrued interest per 100','Accrual under a proportional-period convention');legend(ax)
done('accrual',fig,'Clean and dirty price conventions','Illustrative regular semiannual coupons: accrued interest equals the coupon amount times the elapsed fraction of its accrual period. Actual schedules, day-count definitions and ex-coupon rules require contract-specific treatment.')

fig,axs=plt.subplots(1,2,figsize=(11,3.6))
tb=np.array([0,1,2,3]); db=np.r_[1,[r['discount'] for r in data['bootstrap']]]
grid=np.linspace(0,3,301);ld=np.interp(grid,tb,np.log(db))
axs[0].plot(grid,np.exp(ld),color=ACC,label='Log-linear discount')
axs[0].plot(tb,db,'o',color=WARM,label='Bootstrapped nodes')
axs[1].plot([1,2,3],[r['par'] for r in data['bootstrap']],'-o',color=WARM,label='Annual par coupon')
axs[1].plot([1,2,3],[.02,.025,.03],'-o',color=ACC,label='Continuous zero')
axbase(axs[0],'Maturity (years)','Discount factor','Exact repricing at the input nodes')
axbase(axs[1],'Maturity (years)','Annual rate','Par quotes versus recovered zero rates')
rate_axis(axs[1]);[legend(a) for a in axs]
done('bootstrap',fig,'A three-instrument bootstrap','Synthetic annual par instruments generated from continuous zero rates of 2%, 2.5% and 3%. Connecting discount nodes requires an interpolation choice; input repricing alone does not determine intermediate forwards.')

fig,axs=plt.subplots(1,2,figsize=(11,3.8))
nodes=np.array([0,.5,1,2,5,10,20,30]);zn=curve(nodes)[0];dn=curve(nodes)[2]
g=np.linspace(.01,29.99,1201);j=np.clip(np.searchsorted(nodes,g)-1,0,len(nodes)-2)
zd=np.interp(g,nodes,zn);slope=(zn[j+1]-zn[j])/(nodes[j+1]-nodes[j])
lf=-(np.log(dn[j+1])-np.log(dn[j]))/(nodes[j+1]-nodes[j])
dl=np.interp(g,nodes,dn);ds=(dn[j+1]-dn[j])/(nodes[j+1]-nodes[j])
for fwd,col,label in [(lf,ACC,'Log-linear discount'),(zd+g*slope,WARM,'Linear zero'),(-ds/dl,BLUE,'Linear discount')]:
    axs[1].plot(g,fwd,color=col,label=label)
for disc,col,label in [(np.exp(np.interp(g,nodes,np.log(dn))),ACC,'Log-linear discount'),(np.exp(-g*zd),WARM,'Linear zero'),(dl,BLUE,'Linear discount')]:
    axs[0].plot(g,disc,color=col,label=label)
axbase(axs[0],'Maturity (years)','Discount factor','Discount curves can look almost identical')
axbase(axs[1],'Maturity (years)','Instantaneous forward','Their derivatives reveal the differences')
rate_axis(axs[1]);[legend(a) for a in axs]
done('interpolation',fig,'Interpolation is a modelling decision','Three interpolants pass through identical discount nodes. Forward jumps are sampled on a fine grid and connected for display; at a knot the one-sided derivative must be specified. The inspector interpolates the displayed samples, not an undefined derivative at the knot.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7))
n=np.array([0,1,2,3,5,7,10,15,20,30]); zz=curve(n)[0]+np.array([0,0,.001,-.0008,.0008,-.0007,.0006,-.0004,.0002,0]);h=n*zz
cs=CubicSpline(n,h,bc_type='natural');pc=PchipInterpolator(n,h)
g=np.linspace(.01,30,901)
axs[0].plot(g,cs(g)/g,color=WARM,label='Natural cubic on Tz')
axs[0].plot(g,pc(g)/g,color=ACC,label='PCHIP on Tz')
axs[0].plot(n[1:],zz[1:],'o',color=BLUE,label='Noisy zero observations')
axs[1].plot(g,cs(g,1),color=WARM,label='Natural cubic derivative')
axs[1].plot(g,pc(g,1),color=ACC,label='PCHIP derivative')
[rate_axis(a) for a in axs];[legend(a) for a in axs]
axbase(axs[0],'Maturity (years)','Continuous zero','Small quotation perturbations')
axbase(axs[1],'Maturity (years)','Instantaneous forward','Differentiation amplifies local detail')
done('spline',fig,'Spline regularity and forward-rate stability','Interpolators are applied to integrated rates h(T) = −log D(T) = Tz(T). PCHIP preserves the monotonicity of h when the nodes are monotone; this illustration is not an implementation of Hagan–West monotone convex interpolation.')

fig,axs=plt.subplots(1,2,figsize=(11,3.5))
pn=np.array([.005,-.02,.008,0,2,6.5]);g=np.linspace(0,10,301)
zn,fn,dn=curve(g,pn,'ns')
axs[0].plot(g,dn,color=ACC,label='Negative short-rate example');axs[0].axhline(1,color=GRAY,lw=1)
axs[1].plot(g,zn,color=ACC,label='Zero');axs[1].plot(g,fn,color=WARM,label='Forward')
axbase(axs[0],'Maturity (years)','Discount factor','D can exceed one')
axbase(axs[1],'Maturity (years)','Continuous annual rate','Negative rates are an explicit assumption')
rate_axis(axs[1]);[legend(a) for a in axs]
done('negative',fig,'Negative rates and discount-factor positivity','This hypothetical Nelson–Siegel curve has negative short rates and positive long rates. Positive discounts do not imply decreasing discounts; the admissibility of negative rates depends on the funding and cash-storage framework.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7));g=np.linspace(0,15,501);a,b=loadings(g,1.6);x=g/1.6
for values,vals,col,label in [(np.ones_like(g),np.ones_like(g),GRAY,'Level'),(a,np.exp(-x),ACC,'Slope'),(b,x*np.exp(-x),WARM,'Curvature')]:
    axs[0].plot(g,values,color=col,label=label);axs[1].plot(g,vals,color=col,label=label)
axbase(axs[0],'Maturity (years)','Loading','Zero-rate loadings')
axbase(axs[1],'Maturity (years)','Loading','Forward-rate loadings')
[legend(a) for a in axs]
done('loadings',fig,'Nelson–Siegel factor loadings','Decay time τ = 1.6 years. The zero curvature loading peaks near 1.793τ; the forward curvature loading peaks at τ. The coefficients have rate units and the loadings are dimensionless.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7))
for delta,col in zip([-.01,0,.01],[BLUE,ACC,WARM]):
    p=REFERENCE.copy();p[1]+=delta
    axs[0].plot(T,curve(T,p,'ns')[0],color=col,label=f'β₁ change {100*delta:+g} pp')
for tau,col in zip([.6,1.6,4],[BLUE,ACC,WARM]):
    p=REFERENCE.copy();p[4]=tau
    axs[1].plot(T,curve(T,p,'ns')[0],color=col,label=f'τ = {tau:g} years')
axbase(axs[0],'Maturity (years)','Continuous zero','Slope moves the short end')
axbase(axs[1],'Maturity (years)','Continuous zero','Decay shifts the location of curvature')
[rate_axis(a) for a in axs];[legend(a) for a in axs]
done('parameters',fig,'Nelson–Siegel parameter interpretation','All other Nelson–Siegel coefficients remain β₀ = 3.5%, β₁ = −2%, β₂ = 2.5%. A decay time is not itself an interest rate and does not move the long-run level.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7))
for beta,col in zip([-.015,0,.015],[BLUE,ACC,WARM]):
    p=REFERENCE.copy();p[3]=beta
    axs[0].plot(T,curve(T,p)[0],color=col,label=f'β₃ = {100*beta:+g}%')
    axs[1].plot(T,curve(T,p)[1],color=col,label=f'β₃ = {100*beta:+g}%')
axbase(axs[0],'Maturity (years)','Continuous zero','An additional curvature component')
axbase(axs[1],'Maturity (years)','Instantaneous forward','A second time scale in forwards')
[rate_axis(a) for a in axs];[legend(a) for a in axs]
done('svensson',fig,'Svensson extends the curvature basis','τ₁ = 1.6 and τ₂ = 6.5 years. The extra component vanishes at both the short and long limits, allowing an additional hump or dip without changing those endpoint limits.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7));q,y,train=quotes();g=np.linspace(0,30,501)
for model,col in [('ns',WARM),('nss',ACC)]:
    fit=data[model+'_fit'];axs[0].plot(g,curve(g,fit['params'],model)[0],color=col,label=model.upper()+' fit')
    axs[1].plot(q,(np.array(fit['pred'])-y)*1e4,'-o',color=col,label=model.upper()+' residual')
axs[0].plot(q[train],y[train],'o',color=BLUE,label='Training quotes')
axs[0].plot(q[~train],y[~train],'s',color='#bbbac7',label='Withheld quotes')
axbase(axs[0],'Maturity (years)','Continuous zero','Same synthetic dataset, different flexibility')
axbase(axs[1],'Maturity (years)','Residual (basis points)','Fitted minus observed')
rate_axis(axs[0]);[legend(a) for a in axs]
done('calibration',fig,'Parametric fitting and withheld-maturity validation','Thirteen of sixteen synthetic zero-rate quotes enter the equal-weight fit. Quotes at 0.75, 4 and 15 years are withheld. Static fits use multistart SciPy least squares on profiled decay times; browser fitting uses its own bounded search.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7));taus=np.geomspace(.15,10,301);loss=[];cond=[]
for tau in taus:
    X=design(q[train],[tau],'ns');b=np.linalg.lstsq(X,y[train],rcond=None)[0]
    loss.append(np.sqrt(np.mean((X@b-y[train])**2))*1e4);cond.append(np.linalg.cond(X))
axs[0].plot(taus,loss,color=ACC,label='Profiled training RMSE')
axs[1].plot(taus,cond,color=WARM,label='Design condition number')
[a.set_xscale('log') for a in axs];axs[1].set_yscale('log')
axbase(axs[0],'Decay time τ (years)','RMSE (basis points)','Linear coefficients are re-estimated at every τ')
axbase(axs[1],'Decay time τ (years)','Condition number','Small decay makes loadings harder to distinguish')
[legend(a) for a in axs]
done('profile',fig,'Profile optimization and identification','The one-dimensional Nelson–Siegel profile separates linear rate coefficients from the nonlinear decay parameter. A low residual and a well-conditioned design answer different questions.')

fig,ax=plt.subplots(figsize=(11,3.6));g=np.linspace(0,80,801)
for p,col,label in [(REFERENCE,ACC,'Reference Svensson'),(data['ns_fit']['params'],WARM,'Fitted Nelson–Siegel'),(data['nss_fit']['params'],BLUE,'Fitted Svensson')]:
    ax.plot(g,curve(g,p,'ns' if 'Nelson' in label else 'nss')[0],color=col,label=label)
ax.axvline(30,color=GRAY,ls='--',lw=1);axbase(ax,'Maturity (years)','Continuous zero','Beyond the last observation: a model assumption');rate_axis(ax);legend(ax)
done('extrapolation',fig,'Long-end extrapolation','The last synthetic quote is at 30 years. Each parametric model converges to its fitted β₀; the extrapolated curves are not independently observed evidence about long-horizon rates.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7));s=np.linspace(-.03,.03,301);b=data['bond'];exact=np.array([bond(shock=v)['price'] for v in s]);lin=b['price']*(1-b['duration']*s);quad=lin+.5*b['price']*b['convexity']*s*s
for val,col,label in [(exact,ACC,'Exact repricing'),(lin,BLUE,'Duration approximation'),(quad,WARM,'Duration + convexity')]:axs[0].plot(s*1e4,val,color=col,label=label)
axs[1].plot(s*1e4,lin-exact,color=BLUE,label='Linear minus exact');axs[1].plot(s*1e4,quad-exact,color=WARM,label='Quadratic minus exact')
axbase(axs[0],'Parallel zero shift (basis points)','Bond price per 100','Five-year 4% semiannual coupon bond')
axbase(axs[1],'Parallel zero shift (basis points)','Price approximation error','The second-order correction improves local accuracy')
[legend(a) for a in axs]
done('convexity',fig,'Duration, convexity and finite shocks','Parallel shifts apply to continuously compounded zero rates. No YTM shift is substituted for that curve shock; all approximations use the matching derivatives of discounted cash flows.')

fig,ax=plt.subplots(figsize=(11,3.5));kn=np.array([0,2,5,10,20,30]);g=np.linspace(0,30,601)
for i,col in zip([1,2,3,4],[BLUE,ACC,WARM,GRAY]):
    ax.plot(g,np.interp(g,kn,np.eye(len(kn))[i]),color=col,label=f'{kn[i]:g}-year key')
axbase(ax,'Cash-flow maturity (years)','Bump weight','Local triangular zero-rate shocks');legend(ax)
done('keyrates',fig,'Key-rate bump functions','Linear hat functions are one possible key-rate convention. The omitted 0- and 30-year endpoint hats complete a partition of unity; risk depends on the chosen nodes and bump interpolation.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7));level=np.full_like(T,.01);twist=.005*(T/15-1);butter=.005*np.exp(-((T-7)/4)**2)
for h,col,label in [(level,ACC,'Level +100 bp'),(twist,BLUE,'Twist −50 to +50 bp'),(butter,WARM,'Belly +50 bp')]:
    axs[0].plot(T,h*1e4,color=col,label=label);axs[1].plot(T,z+h,color=col,label=label)
axs[1].plot(T,z,color=GRAY,label='Base zero')
axbase(axs[0],'Maturity (years)','Zero-rate shock (basis points)','Explicit scenario functions')
axbase(axs[1],'Maturity (years)','Continuous zero','Applying shape shocks to the reference curve')
rate_axis(axs[1]);[legend(a) for a in axs]
done('scenarios',fig,'Level, twist and belly scenarios','These deterministic shocks illustrate curve geometry. They are not estimated PCA components, probability forecasts or historically calibrated stress scenarios.')

fig,ax=plt.subplots(figsize=(11,3.5));ages=np.linspace(0,4,241);horizon=5
static=100*np.exp(-(horizon-ages)*curve(horizon-ages)[0])
forward=100*curve(horizon)[2]/curve(ages)[2]
ax.plot(ages,static,color=ACC,label='Unchanged maturity-indexed curve')
ax.plot(ages,forward,color=WARM,label='Today-implied forward bond price')
axbase(ax,'Holding period (years)','Zero-coupon bond price per 100','A five-year zero under two different assumptions');legend(ax)
done('rolldown',fig,'Roll-down and forward carry','Static-curve roll-down reuses today’s zero rate at the shorter remaining maturity. The forward price uses D(5)/D(h). Neither path is an unconditional real-world prediction; their difference reflects the assumed curve evolution.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7));days=np.arange(121);l=.035+.001*np.sin(days/22);slo=-.02+.004*np.sin(days/30+.3);cur=.025+.003*np.cos(days/18)
for v,col,label in [(l,ACC,'Level β₀'),(slo,BLUE,'Slope β₁'),(cur,WARM,'Curvature β₂')]:axs[0].plot(days,v,color=col,label=label)
for i,col in zip([0,40,80,120],[GRAY,BLUE,WARM,ACC]):
    p=REFERENCE.copy();p[:3]=[l[i],slo[i],cur[i]]
    axs[1].plot(T,curve(T,p,'ns')[0],color=col,label=f'Illustration day {i}')
axbase(axs[0],'Illustration day','Factor value','Deterministic factor paths')
axbase(axs[1],'Maturity (years)','Continuous zero','Time-varying Nelson–Siegel curves')
[rate_axis(a) for a in axs];[legend(a) for a in axs]
done('dynamics',fig,'From a cross-section to time-varying factors','The factor paths are synthetic deterministic signals. A statistical forecasting model or an arbitrage-free dynamic pricing model needs additional transition, probability-measure and risk-premium assumptions.')

(ROOT/'figures.json').write_text(json.dumps(FIGURES),encoding='utf-8')
print('Saved',len(FIGURES),'embedded SVG figures')
