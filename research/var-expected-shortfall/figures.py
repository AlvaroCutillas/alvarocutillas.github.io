from figure_support import *
from risk import *
from scipy.stats import norm,t,genpareto,binom
from scipy.optimize import linprog
from matplotlib.ticker import PercentFormatter

def percent(ax,x=False,y=False):
    if x: ax.xaxis.set_major_formatter(PercentFormatter(1)); ax._hover_xformat='percent'
    if y: ax.yaxis.set_major_formatter(PercentFormatter(1)); ax._hover_yformat='percent'

def finish(name,fig,title,detail):
    fig.savefig(ROOT/(name+'.png'),dpi=150)
    save(name,fig,'Figure 00 · '+title,detail)

# All datasets are synthetic; seeds and assumptions appear in the captions.
alpha=.975; q,e=normal_risk(alpha)
x=np.linspace(-3.5,4.2,600)
fig,ax=plt.subplots(figsize=(10,4.2))
ax.plot(x,norm.pdf(x),color=ACC,label='Normal density')
ax.fill_between(x,norm.pdf(x),where=x>=q,color=WARM,alpha=.25)
ax.axvline(q,color=WARM,ls='--',label='VaR 97.5%')
ax.axvline(e,color=BLUE,ls=':',label='ES 97.5%')
axbase(ax,'Loss / standard deviation','Density','A threshold and the average beyond it');ax.legend()
finish('tail',fig,'Value at Risk and Expected Shortfall','Standard normal losses. Shading marks the upper 2.5% probability mass; VaR is 1.9600 and ES is 2.3378 standard deviations. Vertical reference lines are coordinates, not additional density curves.')

fig,axes=plt.subplots(1,2,figsize=(10,4.2))
ls=[0,10,100];ps=[.94,.04,.02];axes[0].bar(ls,ps,width=[4,4,4],color=[GRAY,ACC,WARM])
axes[0]._hover_series=[{'label':'Probability mass','color':ACC,'mode':'snap','points':list(zip(ls,ps))}]
axbase(axes[0],'Loss','Probability mass','A quantile at an atom');percent(axes[0],y=True)
u=np.linspace(.9,.999,301)
qv=[0 if a<=.94 else 10 if a<=.98 else 100 for a in u]
ev=[(2.4/(1-a)) if a<=.94 else 10+1.8/(1-a) if a<=.98 else 100 for a in u]
axes[1].plot(u,qv,color=ACC,label='VaR',drawstyle='steps-post')
axes[1].plot(u,ev,color=WARM,label='ES');percent(axes[1],x=True);axes[1].legend()
axes[1]._hover_snap=True
axbase(axes[1],'Confidence level','Loss','ES includes fractional boundary mass')
finish('atoms',fig,'Discrete loss distribution and tail risk','Losses 0, 10 and 100 have probabilities 94%, 4% and 2%. At 95% confidence, VaR is 10 and ES is 46. The plotted discrete quantile uses the inverse-CDF convention; hover returns sampled confidence levels.')

fig,ax=plt.subplots(figsize=(10,4))
a=np.linspace(.90,.999,301)
v1=[];e1=[];v2=[];e2=[]
for z in a:
    v,es=empirical([0,100],z,[.96,.04]);v1.append(2*v);e1.append(2*es)
    v,es=empirical([0,100,200],z,[.9216,.0768,.0016]);v2.append(v);e2.append(es)
ax.plot(a,v1,color=GRAY,label='Sum of standalone VaRs',drawstyle='steps-post')
ax.plot(a,v2,color=ACC,label='VaR of combined loss',drawstyle='steps-post')
ax.plot(a,e1,color=BLUE,label='Sum of standalone ES')
ax.plot(a,e2,color=WARM,label='ES of combined loss');percent(ax,x=True)
ax._hover_snap=True;ax.legend(fontsize=8,ncol=2);axbase(ax,'Confidence level','Loss','Two independent rare-loss exposures')
finish('coherence',fig,'Diversification and subadditivity','Each independent exposure loses 100 with probability 4%, otherwise zero. At 95% confidence, standalone VaRs sum to 0 while portfolio VaR is 100; ES is 103.2 compared with a standalone sum of 160.')

fig,axes=plt.subplots(1,2,figsize=(10,4.2))
x=np.linspace(-5,7,700);scale=np.sqrt(3/5)
axes[0].plot(x,norm.pdf(x),color=ACC,label='Normal')
axes[0].plot(x,t.pdf(x/scale,5)/scale,color=WARM,label='Student t, ν = 5')
axes[0].set_yscale('log');axes[0].set_ylim(1e-7,1)
axbase(axes[0],'Loss / standard deviation','Density (log scale)','Same variance, different tails');axes[0].legend()
a=np.linspace(.90,.999,150)
for label,fn,c in [('Normal',normal_risk,ACC),('Student t, ν = 5',student_risk,WARM)]:
    vals=np.array([fn(z) for z in a]);axes[1].plot(a,vals[:,0],color=c,label=label+' VaR');axes[1].plot(a,vals[:,1],color=c,ls='--',label=label+' ES')
percent(axes[1],x=True);axes[1].legend(fontsize=8);axbase(axes[1],'Confidence level','Loss / standard deviation','Tail shape changes high-confidence risk')
finish('student',fig,'Normal and Student-t risk at matched volatility','Both loss models have mean zero and standard deviation one. Student-t degrees of freedom 5; scale √(3/5). A logarithmic density axis makes the difference in extreme tails visible.')

fig,ax=plt.subplots(figsize=(10,4))
rho=np.linspace(-.99,.99,150);sd=np.sqrt(.5*(1+rho))
ax.plot(rho,normal_risk(.99)[0]*sd,color=ACC,label='Portfolio VaR 99%')
ax.plot(rho,normal_risk(.99)[1]*sd,color=WARM,label='Portfolio ES 99%')
ax.axhline(normal_risk(.99)[1],color=BLUE,ls='--',label='Sum of weighted standalone ES')
ax.legend();axbase(ax,'Correlation','Loss / asset standard deviation','Equal weights in two unit-volatility normal assets')
finish('dependence',fig,'Correlation and portfolio tail risk','A 50/50 portfolio of two jointly normal, zero-mean losses with unit standard deviation. Changing correlation changes risk even though each marginal distribution is unchanged.')

fig,ax=plt.subplots(figsize=(10,4))
h=np.arange(1,31);m=.08;s=1
ax.plot(h,h*m+np.sqrt(h)*s*norm.ppf(.99),color=ACC,label='IID normal VaR, with drift')
ax.plot(h,np.sqrt(h)*(m+s*norm.ppf(.99)),color=WARM,ls='--',label='Square-root scaled one-day VaR')
ax.plot(h,h*m+np.sqrt(h)*s*norm.pdf(norm.ppf(.99))/.01,color=BLUE,label='IID normal ES, with drift')
ax._hover_snap=True
axbase(ax,'Horizon (days)','Loss units','Mean scales linearly; standard deviation scales with √h');ax.legend(fontsize=8)
finish('horizon',fig,'Horizon scaling and the role of expected loss','Independent additive daily normal losses: mean 0.08, standard deviation 1. This is a fixed-exposure mathematical benchmark; compound returns, volatility dynamics and nonlinear positions need separate treatment.')

rng=np.random.default_rng(4104);sample=rng.normal(0,1,250)
fig,axes=plt.subplots(1,2,figsize=(10,4.3))
sorted_l=np.sort(sample);cdf=np.arange(1,251)/250
axes[0].plot(sorted_l,cdf,color=ACC,label='Empirical CDF',drawstyle='steps-post')
axes[0].plot(x,norm.cdf(x),color=BLUE,ls='--',label='Population CDF')
axes[0]._hover_snap=True;percent(axes[0],y=True);axbase(axes[0],'Loss','Cumulative probability','An empirical distribution has steps');axes[0].legend()
a=np.linspace(.90,.999,200);risk=np.array([empirical(sample,z) for z in a])
axes[1].plot(a,risk[:,0],color=ACC,label='Empirical VaR')
axes[1].plot(a,risk[:,1],color=WARM,label='Empirical ES')
axes[1].plot(a,norm.ppf(a),color=BLUE,ls='--',label='Normal VaR')
percent(axes[1],x=True);axbase(axes[1],'Confidence level','Loss','Finite data cap the empirical tail');axes[1].legend(fontsize=8)
finish('history',fig,'Historical-style estimation from finite observations','250 synthetic standard normal losses, NumPy seed 4104. Quantiles use the inverse empirical CDF and ES uses the exact fractional tail. These are simulated observations, not market returns.')

fig,axes=plt.subplots(1,2,figsize=(10,4.2))
age=np.arange(250);w=.97**age;w/=w.sum()
axes[0].plot(age,w,color=ACC,label='λ = 0.97 normalized weights');percent(axes[0],y=True)
axbase(axes[0],'Observation age (days)','Scenario probability','Recency weighting changes effective information')
lam=np.linspace(.90,.999,150);eff=[]
for la in lam:
    wt=la**age;wt/=wt.sum();eff.append(1/np.sum(wt*wt))
axes[1].plot(lam,eff,color=BLUE,label='Effective sample size')
axbase(axes[1],'Decay factor λ','Effective sample size','250 observations, unequal weights')
finish('weighted',fig,'Exponential weights and effective sample size','Scenario weights proportional to λ raised to observation age; age zero is newest. Effective sample size is 1/Σw², an information diagnostic rather than an exact count of independent tail observations.')

# Exact full repricing of a short European call under physical spot scenarios.
rng=np.random.default_rng(4105);Z=rng.standard_normal(150000)
S=100;K=100;r=.02;vol=.25;T=.5;dt=1/252;mu=.06
spot=S*np.exp((mu-.5*vol*vol)*dt+vol*np.sqrt(dt)*Z)
base=bs(S,K,r,0,vol,T);future=bs(spot,K,r,0,vol,T-dt)['call']
full=future-base['call'];delta=base['dc']*(spot-S)+base['tc']*dt
dg=delta+.5*base['gamma']*(spot-S)**2
fig,ax=plt.subplots(figsize=(10,4.2))
z=np.linspace(-4,4,450);sp=S*np.exp((mu-.5*vol*vol)*dt+vol*np.sqrt(dt)*z)
ax.plot(z,bs(sp,K,r,0,vol,T-dt)['call']-base['call'],color=ACC,label='Full-revaluation short-call loss')
ax.plot(z,base['dc']*(sp-S)+base['tc']*dt,color=GRAY,ls='--',label='Delta + time loss')
ax.plot(z,base['dc']*(sp-S)+.5*base['gamma']*(sp-S)**2+base['tc']*dt,color=WARM,ls=':',label='Delta–gamma + time loss')
axbase(ax,'Physical normal shock Z','Loss per option','Convex option value produces nonlinear short-position losses');ax.legend(fontsize=8)
finish('nonlinear',fig,'Linear approximation and full option revaluation','Short one call; S = K = 100, risk-free rate 2%, volatility 25%, initial maturity 0.5 years and horizon 1/252 years. Physical drift is 6%; option values use risk-neutral Black–Scholes pricing with unchanged volatility and rates.')

rng=np.random.default_rng(4106);sizes=np.array([250,500,1000,2000,5000,10000,25000]);rm=[]
target=normal_risk(.99)
for n in sizes:
    estimates=np.array([empirical(rng.standard_normal(n),.99) for _ in range(300)])
    rm.append(np.sqrt(np.mean((estimates-target)**2,axis=0)))
fig,ax=plt.subplots(figsize=(10,4))
rm=np.array(rm)
ax.loglog(sizes,rm[:,0],color=ACC,marker='o',label='VaR RMSE')
ax.loglog(sizes,rm[:,1],color=WARM,marker='o',label='ES RMSE')
ax.loglog(sizes,.9*np.sqrt(sizes[0]/sizes),color=GRAY,ls='--',label='N⁻¹ᐟ² reference')
axbase(ax,'Simulation paths','Root mean squared error','Tail estimates need many scenarios');ax.legend()
finish('convergence',fig,'Monte Carlo estimation error','99% risk of standard normal losses. Each sample size uses 300 independent synthetic replications, NumPy seed 4106. RMSE includes finite-sample bias; the dashed line shows a rate reference, not a fitted guarantee.')

rng=np.random.default_rng(4107);n=700;shock=rng.standard_normal(n);shock[350:370]*=3
returns=np.empty(n);variance=1.
forecast=np.empty(n)
for i in range(n):
    forecast[i]=np.sqrt(variance);returns[i]=forecast[i]*shock[i];variance=.97*variance+.03*returns[i]**2
fig,ax=plt.subplots(figsize=(10,4.2))
day=np.arange(1,n+1)
ax.plot(day,returns,color=GRAY,lw=.7,label='Synthetic realized loss')
ax.plot(day,norm.ppf(.99)*forecast,color=ACC,label='Pre-observation EWMA VaR')
ax.plot(day,norm.pdf(norm.ppf(.99))/.01*forecast,color=WARM,label='Pre-observation EWMA ES')
ax._hover_snap=True
ax.legend(fontsize=8);axbase(ax,'Day','Loss units','Forecast volatility reacts after observed shocks')
finish('filtered',fig,'Volatility filtering and forecast timing','Synthetic losses driven by EWMA variance with λ = 0.97, seed 4107. Innovations on days 351–370 are deliberately multiplied by three. Forecasts use only earlier losses; the injected episode violates the normal-innovation forecast model.')

fig,axes=plt.subplots(1,2,figsize=(10,4.2))
y=np.linspace(0,12,400)
for xi,c in [(0,ACC),(.25,WARM),(.6,BLUE)]:
    axes[0].plot(y,genpareto.sf(y,xi,scale=1),color=c,label='ξ = '+str(xi))
axes[0].set_yscale('log');axbase(axes[0],'Excess above threshold','Survival probability','Generalized Pareto tails');axes[0].legend()
aa=np.linspace(.96,.999,200);u=2;beta=.8;pu=.05
for xi,c in [(0,ACC),(.25,WARM),(.6,BLUE)]:
    q=u+beta*np.log(pu/(1-aa)) if xi==0 else u+beta/xi*((pu/(1-aa))**xi-1)
    es=q+(beta+xi*(q-u))/(1-xi)
    axes[1].plot(aa,es,color=c,label='ES, ξ = '+str(xi))
percent(axes[1],x=True);axbase(axes[1],'Confidence level','Loss','Tail-shape sensitivity beyond the threshold');axes[1].legend()
finish('evt',fig,'Peaks-over-threshold models','Generalized Pareto survival curves use scale 1. ES extrapolation uses threshold 2, exceedance probability 5% and scale 0.8. Parameters are illustrative population inputs; no tail fit to market data is implied.')

fig,ax=plt.subplots(figsize=(10,4))
rr=np.linspace(-.95,.95,200)
for nu,c in [(4,WARM),(10,BLUE)]:
    dep=2*t.cdf(-np.sqrt((nu+1)*(1-rr)/(1+rr)),nu+1)
    ax.plot(rr,dep,color=c,label='Student-t copula, ν = '+str(nu))
ax.plot(rr,np.zeros_like(rr),color=ACC,label='Gaussian copula, |ρ| < 1')
percent(ax,y=True);axbase(ax,'Copula correlation parameter','Upper-tail dependence','Same correlation need not mean the same co-extremes');ax.legend()
finish('copula',fig,'Asymptotic tail dependence','For a Student-t copula, λᵤ = 2 Tν₊₁(−√((ν+1)(1−ρ)/(1+ρ))). A nonsingular Gaussian copula has zero asymptotic tail dependence; this does not mean independence at finite thresholds.')

sd=np.array([.01,.016,.022]);corr=np.array([[1,.2,.1],[.2,1,.4],[.1,.4,1]])
cov=corr*sd[:,None]*sd[None,:];weights=np.array([.5,.3,.2]);W=1e6
port_sd=np.sqrt(weights@cov@weights);contrib=W*normal_risk(.99)[1]*weights*(cov@weights)/port_sd
fig,ax=plt.subplots(figsize=(10,4))
ax.bar(np.arange(1,4),contrib,color=[ACC,WARM,BLUE],width=.55)
ax._hover_series=[{'label':'Component ES','color':ACC,'mode':'snap','points':list(zip(np.arange(1,4),contrib))}]
ax.set_xticks([1,2,3],['Asset A','Asset B','Asset C'])
axbase(ax,'Asset index','99% ES contribution (€)','Capital weights and risk shares differ')
finish('allocation',fig,'Euler allocation of normal Expected Shortfall','Wealth €1,000,000; weights 50%, 30%, 20%; daily volatilities 1%, 1.6%, 2.2%; correlations AB = 0.2, AC = 0.1, BC = 0.4; zero means. Contributions sum to portfolio ES.')

loss=np.array([0,10,100]);prob=np.array([.94,.04,.02]);theta=np.linspace(-15,110,501)
objective=theta+np.maximum(loss[None,:]-theta[:,None],0)@prob/.05
fig,ax=plt.subplots(figsize=(10,4))
ax.plot(theta,objective,color=ACC,label='CVaR auxiliary objective')
ax.axvline(10,color=WARM,ls='--',label='Minimizing threshold')
ax.axhline(46,color=BLUE,ls=':',label='ES = 46')
axbase(ax,'Auxiliary threshold θ','Objective value','Convexity turns a tail average into optimization');ax.legend()
finish('objective',fig,'Rockafellar–Uryasev representation','The discrete distribution from Figure 02 at 95% confidence. The minimum of θ + E[(L−θ)₊]/0.05 is 46; a minimizer is the 95% quantile 10.')

# Same number of violations, distinct temporal arrangement.
even=np.zeros(500,dtype=int);even[[19,71,123,177,219,267,321,373,421,477]]=1
cluster=np.zeros(500,dtype=int);cluster[240:250]=1
fig,axes=plt.subplots(2,1,figsize=(10,4.8),sharex=True)
for ax,h,label in zip(axes,[even,cluster],['Dispersed exceedances','Clustered exceedances']):
    ax.plot(np.arange(1,501),np.cumsum(h),color=ACC if ax is axes[0] else WARM,label=label,drawstyle='steps-post')
    ax.plot(np.arange(1,501),np.arange(1,501)*.02,color=GRAY,ls='--',label='Expected cumulative count')
    ax._hover_snap=True
    ax.legend(fontsize=8,loc='upper left');axbase(ax,'Day','Cumulative breaches',label)
finish('backtest',fig,'Coverage and temporal independence','Both artificial 500-day hit sequences have 10 exceedances, exactly 2% coverage. The second concentrates all breaches in ten consecutive days. Coverage alone does not diagnose clustering.')

rng=np.random.default_rng(4108);base=rng.standard_normal(1000)
b=np.array([empirical(rng.choice(base,len(base),replace=True),.99) for _ in range(1200)])
fig,axes=plt.subplots(1,2,figsize=(10,4.2))
for ax,i,label,c in zip(axes,[0,1],['VaR','ES'],[ACC,WARM]):
    hist,edges=np.histogram(b[:,i],bins=35,density=True);mid=(edges[1:]+edges[:-1])/2
    ax.plot(mid,hist,color=c,label='Bootstrap '+label,drawstyle='steps-mid')
    ax._hover_series=[];ax._hover_snap=True
    ax.axvline(normal_risk(.99)[i],color=BLUE,ls='--',label='Population '+label)
    axbase(ax,'Estimated loss threshold','Bootstrap density',label+' uncertainty');ax.legend(fontsize=8)
finish('uncertainty',fig,'Sampling uncertainty in the tail','An IID nonparametric bootstrap of one 1,000-observation synthetic normal sample: 1,200 resamples, seed 4108. The bootstrap is conditional on the observed empirical distribution and cannot generate an unseen crisis.')

normal_table=[]
for a in [.95,.975,.99,.995,.999]:
    nv,ne=normal_risk(a,0,10000);tv,te=student_risk(a,5,0,10000)
    normal_table.append({'alpha':a,'normal_var':nv,'normal_es':ne,'student_var':tv,'student_es':te})
option_table={}
for name,losses in [('Delta + time',delta),('Delta–gamma + time',dg),('Full revaluation',full)]:
    v,es=empirical(losses,.99);option_table[name]={'var':v,'es':es}
out={'normal':normal_table,'portfolio':{'sd':W*port_sd,'var':W*port_sd*normal_risk(.99)[0],'es':float(contrib.sum()),'contributions':contrib.tolist()},'options':option_table,
     'backtests':{name:{'coverage':coverage(500,10,.02),'independence':independence(h)} for name,h in [('Dispersed',even),('Clustered',cluster)]},
     'bootstrap':{'var_interval':np.quantile(b[:,0],[.025,.975]).tolist(),'es_interval':np.quantile(b[:,1],[.025,.975]).tolist(),'sample_risk':empirical(base,.99)}}
(ROOT/'figures.json').write_text(json.dumps(FIGURES),encoding='utf-8')
(ROOT/'computed.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print('Generated',len(FIGURES),'computed figures')
