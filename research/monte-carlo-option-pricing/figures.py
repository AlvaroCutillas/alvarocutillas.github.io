from figure_support import *
from scipy.special import ndtri
from scipy.stats import qmc
from scipy.integrate import quad

def summary(y):
    return {'value':float(np.mean(y)),'se':float(np.std(y,ddof=1)/np.sqrt(len(y))),'units':len(y)}

def payoff(z,K=100):
    st=100*np.exp(.03+.2*z)
    return np.exp(-.05)*np.maximum(st-K,0),np.exp(-.05)*st

def beta_stock():
    d2=.15; first=100*np.exp(.05)*ndtr(d2+.2); second=10000*np.exp(.14)*ndtr(d2+.4)
    cross=np.exp(-.1)*(second-100*first)
    return (cross-bs()['call']*100)/(10000*np.expm1(.04))

def build():
    ref=float(bs()['call']); beta=beta_stock(); out={'reference':ref,'put_reference':float(bs()['put']),'beta':beta,'seed':2026}
    # Exact paths, without an SDE discretisation error.
    rng=np.random.default_rng(2026); times=np.linspace(0,1,129)
    paths=100*np.exp(np.column_stack([np.zeros(10),np.cumsum(.03/128+.2/np.sqrt(128)*rng.normal(size=(10,128)),axis=1)]))
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.6),gridspec_kw={'width_ratios':[1.35,1]})
    for i,p in enumerate(paths):axes[0].plot(times,p,color=[ACC,WARM,BLUE,GRAY][i%4],lw=1,alpha=.7,label=f'Path {i+1:02d}')
    axbase(axes[0],'Time (years)','Spot','Risk-neutral GBM sample paths')
    z=np.linspace(-3.5,4,360); y,c=payoff(z); axes[1].plot(z,y,color=ACC,label='Discounted call payoff');axes[1].axvline(-.15,color=WARM,ls=':',lw=1)
    axbase(axes[1],'Normal shock Z','Discounted payoff','Each scenario becomes a cash flow')
    save('paths',fig,'Figure 01 · Exact GBM paths and discounted European call payoffs','S₀ = K = 100, r = 5%, q = 0, σ = 20%, T = 1; NumPy seed 2026. The simulated paths use exact lognormal transitions. Ten paths illustrate possible model outcomes, not a price estimate.')
    # Running estimates and pointwise intervals; nested observations are dependent.
    rng=np.random.default_rng(1001); z=rng.normal(size=100000); y,c=payoff(z)
    ns=np.unique(np.geomspace(100,len(y),130).astype(int)); sums=np.cumsum(y); squares=np.cumsum(y*y)
    means=sums[ns-1]/ns; se=np.sqrt((squares[ns-1]-ns*means**2)/(ns-1)/ns)
    fig,ax=plt.subplots(figsize=(9.2,3.65));ax.plot(ns,means,color=ACC,label='Running estimate');ax.fill_between(ns,means-1.96*se,means+1.96*se,color=ACC,alpha=.10)
    ax.plot(ns,means-1.96*se,color=GRAY,lw=.75,ls=':',label='95% lower endpoint');ax.plot(ns,means+1.96*se,color=GRAY,lw=.75,ls=':',label='95% upper endpoint');ax.axhline(ref,color=WARM,ls='--',label='Black–Scholes reference');ax.set_xscale('log');axbase(ax,'Payoff evaluations N','Call value');ax.legend(fontsize=7.5,ncol=2)
    out['plain']=summary(y)
    save('convergence',fig,'Figure 02 · Running estimates and pointwise confidence intervals','Exact terminal sampling; seed 1001. The shaded intervals are normal approximations at each displayed fixed sample size. They are not a simultaneous confidence band, and the nested estimates are strongly dependent.')
    # A payoff distribution has an atom at zero, in addition to its positive tail.
    fig,ax=plt.subplots(figsize=(9.2,3.4));edges=np.linspace(0,65,66);positive=y[y>0];counts,_=np.histogram(positive,bins=edges);density=counts/(len(y)*np.diff(edges));centres=(edges[:-1]+edges[1:])/2
    ax.stairs(density,edges,color=ACC,lw=1.7);ax._hover_series=[{'label':'Positive-payoff density','color':ACC,'mode':'step','bins':edges.tolist(),'points':np.column_stack([centres,density]).tolist()}]
    axbase(ax,'Discounted payoff','Density per currency unit');ax.text(.97,.86,f'ZERO-PAYOFF MASS: {(y==0).mean():.1%}',transform=ax.transAxes,ha='right',color=WARM,fontsize=10)
    out['zero_mass']=float((y==0).mean())
    save('distribution',fig,'Figure 03 · Discounted payoffs: zero mass and a right tail','100,000 exact-terminal observations, seed 1001. The atom at zero is stated separately; histogram heights integrate to the observed mass in the plotted positive-payoff window. Positive payoffs above 65 are omitted from the window, not from the price estimate.')
    # Independent repetitions assess coverage, unlike one attractive convergence trace.
    rng=np.random.default_rng(1002); sizes=np.array([100,250,500,1000,2500,5000]);coverage=[];rms=[];R=600
    for n in sizes:
        ys=payoff(rng.normal(size=(R,n)))[0];ms=ys.mean(axis=1);ses=ys.std(axis=1,ddof=1)/np.sqrt(n);coverage.append(np.mean(abs(ms-ref)<=1.96*ses));rms.append(np.sqrt(np.mean((ms-ref)**2)))
    fig,axes=plt.subplots(1,2,figsize=(9.2,3.6));axes[0].plot(sizes,np.array(coverage)*100,color=ACC,marker='o',ms=3,label='Observed coverage');axes[0].axhline(95,color=WARM,ls='--',label='Nominal 95%');axes[0].set_xscale('log');axes[0].set_ylim(84,100);axbase(axes[0],'Payoff evaluations N','Coverage (%)');axes[0].legend(fontsize=8)
    axes[1].loglog(sizes,rms,color=ACC,marker='o',ms=3,label='Empirical RMSE');axes[1].loglog(sizes,y.std(ddof=1)/np.sqrt(sizes),color=WARM,ls='--',label='Estimated 1 / √N reference');axbase(axes[1],'Payoff evaluations N','Price RMSE');axes[1].legend(fontsize=8)
    save('coverage',fig,'Figure 04 · Repeated-run coverage and root mean squared error','600 independent experiments per sample size; seed 1002. Coverage itself is noisy: at 95%, its binomial standard error with 600 repetitions is about 0.89 percentage points. No monotonic convergence of an individual run is implied.')
    # Antithetic pairs are independent units; comparisons use equal payoff budgets.
    zgrid=np.linspace(-3,3,400);yp,cp=payoff(zgrid);ym,cm=payoff(-zgrid)
    fig,ax=plt.subplots(figsize=(9.2,3.5));ax.plot(zgrid,yp,color=ACC,label='Y(Z)');ax.plot(zgrid,ym,color=WARM,label='Y(−Z)');ax.plot(zgrid,(yp+ym)/2,color=BLUE,label='Pair average');axbase(ax,'Normal shock Z','Discounted payoff');ax.legend(fontsize=8)
    save('antithetic',fig,'Figure 05 · Antithetic payoffs and the independent pair average','Each Z is accompanied by −Z. Both marginal shocks have the required normal distribution. Standard errors must use the variance of pair averages; treating the two members as independent understates or misstates uncertainty.')
    zgrid=np.linspace(-2.8,3,400);yg,cg=payoff(zgrid);res=yg-beta*(cg-100)
    fig,ax=plt.subplots(figsize=(9.2,3.5));ax.plot(zgrid,yg,color=ACC,label='Raw payoff Y');ax.plot(zgrid,beta*(cg-100),color=WARM,label='Centred stock control');ax.plot(zgrid,res,color=BLUE,label='Adjusted payoff');axbase(ax,'Normal shock Z','Discounted currency units');ax.legend(fontsize=8)
    save('control',fig,'Figure 06 · Removing known stock variation with a control variate',f'The control is e^(−rT)S_T, with known expectation 100. Its population-optimal coefficient is {beta:.6f}, derived from truncated lognormal moments. Adjusted observations can be negative; clipping them would introduce bias.')
    rng=np.random.default_rng(1003);zp=rng.normal(size=250000);a,ca=payoff(zp);b,cb=payoff(-zp);pa=(a+b)/2;pc=(ca+cb)/2;beta_pair=np.cov(pa,pc,ddof=1)[0,1]/pc.var(ddof=1)
    methods={'Plain':a,'Antithetic':pa,'Stock control':a-beta*(ca-100),'Antithetic + control':pa-beta_pair*(pc-100)}
    budgets=np.array([1000,4000,16000,64000]);fig,ax=plt.subplots(figsize=(9.2,3.5))
    for (label,values),col in zip(methods.items(),[GRAY,WARM,ACC,BLUE]):
        cost=2 if 'Antithetic' in label else 1;ax.loglog(budgets,values.std(ddof=1)/np.sqrt(budgets/cost),color=col,marker='o',ms=3,label=label)
    axbase(ax,'Production payoff evaluations N','Projected price standard error');ax.legend(fontsize=8)
    out['variance']=[{'method':label,'variance_per_unit':float(values.var(ddof=1)),'evaluations_per_unit':2 if 'Antithetic' in label else 1,'se_100000':float(values.std(ddof=1)/np.sqrt(100000/(2 if 'Antithetic' in label else 1)))} for label,values in methods.items()]
    save('efficiency',fig,'Figure 07 · Standard errors at equal production payoff budgets','Unit variances estimated from 250,000 independent normal draws, seed 1003. Antithetic methods use N/2 pairs. The combined control coefficient is estimated on this pilot sample; the curves project frozen-coefficient production errors and exclude pilot cost.')
    # Importance sampling for a deep out-of-the-money call.
    K=180.;theta=(np.log(K/100)-.03)/.2;rare=float(bs(K=K)['call']);rng=np.random.default_rng(1004);base=rng.normal(size=80000);raw=payoff(base,K)[0];shift=base+theta;weighted=payoff(shift,K)[0]*np.exp(-theta*shift+.5*theta**2)
    ns=np.unique(np.geomspace(500,len(base),100).astype(int));fig,axes=plt.subplots(1,2,figsize=(9.2,3.55));zz=np.linspace(-3,6,400)
    axes[0].plot(zz,np.exp(-zz**2/2)/np.sqrt(2*np.pi),color=GRAY,label='Target N(0, 1)');axes[0].plot(zz,np.exp(-(zz-theta)**2/2)/np.sqrt(2*np.pi),color=ACC,label='Proposal N(θ, 1)');axes[0].axvline(theta,color=WARM,ls=':',lw=1);axbase(axes[0],'Normal shock Z','Density');axes[0].legend(fontsize=7.5)
    axes[1].plot(ns,np.cumsum(raw)[ns-1]/ns,color=WARM,label='Plain estimate');axes[1].plot(ns,np.cumsum(weighted)[ns-1]/ns,color=ACC,label='Weighted estimate');axes[1].axhline(rare,color=BLUE,ls='--',label='BSM reference');axes[1].set_xscale('log');axbase(axes[1],'Payoff evaluations N','Call value');axes[1].legend(fontsize=7.5)
    out['rare']={'reference':rare,'theta':float(theta),'plain':summary(raw),'importance':summary(weighted),'plain_hits':int((raw>0).sum())}
    save('importance',fig,'Figure 08 · A shifted proposal for a rare exercise event','K = 180; other inputs use the one-year benchmark. Seed 1004. The proposal mean is the exercise threshold in normal coordinates. Every payoff is multiplied by the exact density ratio; changing the sampling law without weights would change the price.')
    # Scrambles are the independent units for randomized QMC uncertainty.
    ns=2**np.arange(7,15);errors={'IID':[],'Antithetic':[],'Scrambled Sobol':[]};R=32;rng=np.random.default_rng(1005)
    for n in ns:
        estimates={key:[] for key in errors}
        for rep in range(R):
            zz=rng.normal(size=n);estimates['IID'].append(payoff(zz)[0].mean())
            zz=rng.normal(size=n//2);estimates['Antithetic'].append(((payoff(zz)[0]+payoff(-zz)[0])/2).mean())
            uu=qmc.Sobol(1,scramble=True,seed=1005000+int(n)+rep).random_base2(int(np.log2(n))).ravel();estimates['Scrambled Sobol'].append(payoff(ndtri(np.clip(uu,1e-15,1-1e-15)))[0].mean())
        for key in errors:errors[key].append(np.sqrt(np.mean((np.array(estimates[key])-ref)**2)))
    fig,ax=plt.subplots(figsize=(9.2,3.5))
    for (key,values),col in zip(errors.items(),[GRAY,WARM,ACC]):ax.loglog(ns,values,color=col,marker='o',ms=3,label=key)
    axbase(ax,'Payoff evaluations per repetition N','Empirical RMSE across 32 repetitions');ax.legend(fontsize=8)
    save('qmc',fig,'Figure 09 · Randomized quasi-Monte Carlo on a one-dimensional payoff','32 independent repetitions per method and N; IID seed 1005, separate Sobol scramble seeds. Each Sobol sample has 2^m points. The comparison uses exact BSM truth; this favourable one-dimensional result is not a universal convergence-rate guarantee.')
    # Couple Euler and exact terminal values to isolate discretisation bias.
    ns=np.array([4,8,16,32,64,128]);rng=np.random.default_rng(1006);diffs={int(n):[] for n in ns};M=100000
    for start in range(0,M,5000):
        dw=rng.normal(size=(5000,128))/np.sqrt(128);exact=100*np.exp(.03+.2*dw.sum(axis=1));exact_y=np.exp(-.05)*np.maximum(exact-100,0)
        for n in ns:
            coarse=dw.reshape(5000,n,128//n).sum(axis=2);euler=100*np.prod(1+.05/n+.2*coarse,axis=1);diffs[int(n)].append(np.exp(-.05)*np.maximum(euler-100,0)-exact_y)
    rows=[{'steps':int(n),**summary(np.concatenate(diffs[int(n)]))} for n in ns];out['euler_bias']=rows
    fig,ax=plt.subplots(figsize=(9.2,3.5));means=np.array([r['value'] for r in rows]);ses=np.array([r['se'] for r in rows]);ax.plot(ns,means,color=ACC,marker='o',ms=3,label='Coupled Euler − exact estimate');ax.fill_between(ns,means-1.96*ses,means+1.96*ses,color=ACC,alpha=.15);ax.axhline(0,color=WARM,ls='--',label='Zero bias');ax.set_xscale('log');axbase(ax,'Euler steps m','Estimated price bias');ax.legend(fontsize=8)
    save('bias',fig,'Figure 10 · Euler discretisation bias and paired statistical uncertainty','100,000 coupled paths; seed 1006. Euler and exact terminals share the same total Brownian increment. Shading is a pointwise 95% normal interval for their expected payoff difference. More samples estimate this bias more precisely; they do not remove it.')
    # Correlated assets and a convex basket payoff.
    rng=np.random.default_rng(1007);base=rng.normal(size=(80000,3));rho=np.linspace(-.45,.9,28);prices=[];ses=[];vol=np.array([.2,.25,.3])
    for rr in rho:
        corr=np.full((3,3),rr);np.fill_diagonal(corr,1);zz=base@np.linalg.cholesky(corr).T;spots=100*np.exp(.05-.5*vol**2+vol*zz);vals=np.exp(-.05)*np.maximum(spots.mean(axis=1)-100,0);prices.append(vals.mean());ses.append(vals.std(ddof=1)/np.sqrt(len(vals)))
    fig,ax=plt.subplots(figsize=(9.2,3.5));ax.plot(rho,prices,color=ACC,label='Arithmetic basket call');ax.fill_between(rho,np.array(prices)-1.96*np.array(ses),np.array(prices)+1.96*np.array(ses),color=ACC,alpha=.12);axbase(ax,'Equal pairwise correlation ρ','Basket call value');ax.legend(fontsize=8)
    save('basket',fig,'Figure 11 · Correlation affects the value of a basket payoff','Three spots initially 100, equal weights, σ = 20%, 25%, 30%, r = 5%, q = 0, K = 100, T = 1; 80,000 common base vectors, seed 1007. The correlation matrix is positive definite throughout the plotted range. Shading shows pointwise Monte Carlo uncertainty.')
    # A discretely monitored geometric average supplies an exact Asian control.
    rng=np.random.default_rng(1008);dw=rng.normal(size=(80000,96))/np.sqrt(96);full=100*np.exp(np.cumsum(.03/96+.2*dw,axis=1));asian=[]
    for m in [12,24,48,96]:
        sample=full[:,96//m-1::96//m];arith=sample.mean(axis=1);geom=np.exp(np.log(sample).mean(axis=1));ay=np.exp(-.05)*np.maximum(arith-100,0);gy=np.exp(-.05)*np.maximum(geom-100,0);mu=np.log(100)+.03*(m+1)/(2*m);v=.04*(m+1)*(2*m+1)/(6*m*m);d=(mu-np.log(100))/np.sqrt(v);gprice=np.exp(-.05)*(np.exp(mu+v/2)*ndtr(d+np.sqrt(v))-100*ndtr(d));bet=np.cov(ay,gy,ddof=1)[0,1]/gy.var(ddof=1)
        # Fit on an independent half-sample and evaluate on the other half.
        bet=np.cov(ay[:40000],gy[:40000],ddof=1)[0,1]/gy[:40000].var(ddof=1);cv=ay[40000:]-bet*(gy[40000:]-gprice)
        asian.append({'fixings':m,'geometric_exact':float(gprice),'plain':summary(ay[40000:]),'control':summary(cv),'beta':float(bet)})
    out['asian']=asian;fig,axes=plt.subplots(1,2,figsize=(9.2,3.5));ms=[r['fixings'] for r in asian];axes[0].plot(ms,[r['control']['value'] for r in asian],color=ACC,marker='o',ms=3,label='Arithmetic Asian · control MC');axes[0].plot(ms,[r['geometric_exact'] for r in asian],color=WARM,marker='o',ms=3,label='Geometric Asian · exact');axbase(axes[0],'Monitoring dates m','Asian call value');axes[0].legend(fontsize=7.5)
    axes[1].semilogy(ms,[r['plain']['se'] for r in asian],color=WARM,marker='o',ms=3,label='Raw arithmetic payoff');axes[1].semilogy(ms,[r['control']['se'] for r in asian],color=ACC,marker='o',ms=3,label='Geometric control');axbase(axes[1],'Monitoring dates m','Standard error, 40,000 production paths');axes[1].legend(fontsize=7.5)
    save('asian',fig,'Figure 12 · Arithmetic Asian pricing with a geometric-average control','Fixings at jT/m, j = 1,…,m; S₀ is excluded from the average. Seed 1008; 40,000 pilot and 40,000 production paths. The analytical geometric price uses exactly the same monitoring schedule as its simulated control.')
    # Brownian-bridge survival weights recover continuous monitoring under GBM.
    B=130.;bb=np.log(B);zmax=(np.log(B/100)-.03)/.2
    integrand=lambda z:np.exp(-.05)*max(100*np.exp(.03+.2*z)-100,0)*(1-np.exp(-2*(bb-np.log(100))*(bb-np.log(100)-.03-.2*z)/.04))*np.exp(-z*z/2)/np.sqrt(2*np.pi)
    barrier_ref=quad(integrand,-.15,zmax,epsabs=1e-11)[0];ns=[4,8,16,32,64,128];rng=np.random.default_rng(1009);discrete={n:[] for n in ns};bridged={n:[] for n in ns}
    for start in range(0,60000,5000):
        dw=rng.normal(size=(5000,128))/np.sqrt(128);full=np.log(100)+np.cumsum(.03/128+.2*dw,axis=1);terminal=np.exp(-.05)*np.maximum(np.exp(full[:,-1])-100,0)
        for n in ns:
            nodes=np.column_stack([np.full(5000,np.log(100)),full[:,128//n-1::128//n]]);alive=np.all(nodes<bb,axis=1);cross=np.exp(np.minimum(0,-2*(bb-nodes[:,:-1])*(bb-nodes[:,1:])/(.04/n)));weights=np.prod(1-cross,axis=1)*alive;discrete[n].append(terminal*alive);bridged[n].append(terminal*weights)
    barrier=[{'steps':n,'discrete':summary(np.concatenate(discrete[n])),'bridge':summary(np.concatenate(bridged[n]))} for n in ns];out['barrier']={'reference':barrier_ref,'rows':barrier}
    fig,ax=plt.subplots(figsize=(9.2,3.5));ax.plot(ns,[r['discrete']['value'] for r in barrier],color=WARM,marker='o',ms=3,label='Node-only monitoring');ax.plot(ns,[r['bridge']['value'] for r in barrier],color=ACC,marker='o',ms=3,label='Bridge survival weights');ax.axhline(barrier_ref,color=BLUE,ls='--',label='Continuous-monitoring quadrature');ax.set_xscale('log');axbase(ax,'Monitoring intervals m','Up-and-out call value');ax.legend(fontsize=8)
    save('barrier',fig,'Figure 13 · Missed barrier crossings and conditional survival weights','Up-and-out call, K = 100, upper barrier 130, no rebate; seed 1009, 60,000 coupled paths. Node-only prices refer to different discrete monitoring contracts. Bridge weights target the continuously monitored GBM contract; the reference is one-dimensional numerical integration of the exact terminal conditional survival payoff.')
    # Finite-difference variance explodes with independent bumps, not with CRN.
    rng=np.random.default_rng(1010);R=80;M=4096;z=rng.normal(size=(R,M));zz=rng.normal(size=(R,M));hs=np.geomspace(.001,3,25);crn=[];ind=[];delta=float(bs()['dc'])
    for h in hs:
        factor=np.exp(.03+.2*z);other=np.exp(.03+.2*zz);plus=np.exp(-.05)*np.maximum((100+h)*factor-100,0);minus=np.exp(-.05)*np.maximum((100-h)*factor-100,0);minus_ind=np.exp(-.05)*np.maximum((100-h)*other-100,0)
        crn.append(((plus-minus)/(2*h)).mean(axis=1).std(ddof=1));ind.append(((plus-minus_ind)/(2*h)).mean(axis=1).std(ddof=1))
    fig,ax=plt.subplots(figsize=(9.2,3.5));ax.loglog(hs,ind,color=WARM,label='Independent bump simulations');ax.loglog(hs,crn,color=ACC,label='Common random numbers');axbase(ax,'Spot bump h','SD of delta estimates across 80 runs');ax.legend(fontsize=8)
    pw=np.exp(-.05)*np.exp(.03+.2*z)*(100*np.exp(.03+.2*z)>100);lr=payoff(z)[0]*z/(100*.2);out['greeks']={'delta_exact':delta,'pathwise':summary(pw.ravel()),'likelihood_ratio':summary(lr.ravel())}
    save('greeks',fig,'Figure 14 · Finite differences: a smaller bump can amplify noise','80 repetitions, 4,096 paths per bump; seed 1010. The common-random-number version reuses each normal shock at both spots. This graph measures standard deviation, not total error: finite-difference bias must also be checked.')
    # MLMC illustrates coupled Euler corrections, not a need to discretise a vanilla GBM payoff.
    rng=np.random.default_rng(1011);levels=np.arange(1,8);vars_c=[];vars_i=[];M=50000
    for ell in levels:
        n=2**ell;dw=rng.normal(size=(M,n))/np.sqrt(n);fine=100*np.prod(1+.05/n+.2*dw,axis=1);coarse=100*np.prod(1+.05/(n/2)+.2*dw.reshape(M,n//2,2).sum(axis=2),axis=1);fy=np.exp(-.05)*np.maximum(fine-100,0);cy=np.exp(-.05)*np.maximum(coarse-100,0);vars_c.append(np.var(fy-cy,ddof=1));vars_i.append(np.var(fy,ddof=1)+np.var(cy,ddof=1))
    fig,ax=plt.subplots(figsize=(9.2,3.5));ax.semilogy(levels,vars_c,color=ACC,marker='o',ms=3,label='Coupled level correction');ax.semilogy(levels,vars_i,color=WARM,marker='o',ms=3,label='Independent level difference');axbase(ax,'Level ℓ (fine steps = 2^ℓ)','Variance of fine − coarse payoff');ax.legend(fontsize=8)
    out['mlmc']=[{'level':int(l),'fine_steps':int(2**l),'coupled_variance':float(v),'independent_variance':float(w)} for l,v,w in zip(levels,vars_c,vars_i)]
    save('mlmc',fig,'Figure 15 · Coupling makes fine-minus-coarse corrections inexpensive','50,000 independent coupled paths per level; seed 1011. Coarse Brownian increments are sums of adjacent fine increments. The independent comparison is Var(fine) + Var(coarse). These Euler levels illustrate MLMC mechanics; exact terminal GBM sampling is preferable for this European benchmark.')
    # Least-squares policies are trained and priced on separate sets of paths.
    def make_paths(rng,m,n):return np.column_stack([np.full(m,100.),100*np.exp(np.cumsum(.03/n+.2/np.sqrt(n)*rng.normal(size=(m,n)),axis=1))])
    n=50;train=make_paths(np.random.default_rng(1012),25000,n);test=make_paths(np.random.default_rng(1013),50000,n);disc=np.exp(-.05/n);rows=[]
    for degree in [1,2,3,5]:
        val=np.maximum(100-train[:,-1],0);coeff={}
        for j in range(n-1,0,-1):
            future=val*disc;intr=np.maximum(100-train[:,j],0);mask=intr>0;x=train[mask,j]/100-1;X=np.vander(x,degree+1,increasing=True);coef=np.linalg.lstsq(X,future[mask],rcond=None)[0];coeff[j]=coef;cont=np.maximum(0,np.polynomial.polynomial.polyval(train[:,j]/100-1,coef));val=np.where(mask&(intr>cont),intr,future)
        cash=np.zeros(len(test));alive=np.ones(len(test),dtype=bool);ex_count=0
        for j in range(1,n):
            intr=np.maximum(100-test[:,j],0);cont=np.maximum(0,np.polynomial.polynomial.polyval(test[:,j]/100-1,coeff[j]));exercise=alive&(intr>0)&(intr>cont);cash[exercise]=intr[exercise]*np.exp(-.05*j/n);alive[exercise]=False;ex_count+=exercise.sum()
        cash[alive]=np.maximum(100-test[alive,-1],0)*np.exp(-.05);rows.append({'degree':degree,'training_value':float(val.mean()*disc),'test':summary(cash),'early_exercise_fraction':float(ex_count/len(test))})
    out['lsm']={'rows':rows,'american_crr':crr(n=1600),'training_paths':len(train),'test_paths':len(test),'dates':n}
    fig,ax=plt.subplots(figsize=(9.2,3.5));degrees=[r['degree'] for r in rows];means=np.array([r['test']['value'] for r in rows]);ses=np.array([r['test']['se'] for r in rows]);ax.plot(degrees,means,color=ACC,marker='o',ms=3,label='Independent policy evaluation');ax.fill_between(degrees,means-1.96*ses,means+1.96*ses,color=ACC,alpha=.14);ax.plot(degrees,[r['training_value'] for r in rows],color=WARM,marker='o',ms=3,label='In-sample valuation');ax.axhline(out['lsm']['american_crr'],color=BLUE,ls='--',label='American put · CRR 1,600');axbase(ax,'Polynomial degree','Put value');ax.legend(fontsize=8);ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    save('lsm',fig,'Figure 16 · Least-squares exercise policies and independent evaluation','25,000 training paths (seed 1012), 50,000 independent test paths (seed 1013), 50 exercise dates. Shading measures test-sample uncertainty conditional on the trained policy. The CRR comparison permits more exercise dates; a confidence interval for a suboptimal policy does not cover its policy bias.')
    # Separate fixed-seed production experiment for the worked comparison table.
    pz=np.random.default_rng(1701).normal(size=2048);py,pc=payoff(pz);ny,nc=payoff(-pz)
    beta_p=np.cov(py,pc,ddof=1)[0,1]/pc.var(ddof=1)
    pp=(py+ny)/2;cp=(pc+nc)/2;beta_a=np.cov(pp,cp,ddof=1)[0,1]/cp.var(ddof=1)
    z=np.random.default_rng(1702).normal(size=100000);py,pc=payoff(z);ny,nc=payoff(-z[:50000]);paired=(py[:50000]+ny)/2;paired_c=(pc[:50000]+nc)/2
    example=[('Plain',py,0,0.),('Antithetic',paired,0,0.),('Stock control',py-beta_p*(pc-100),2048,beta_p),('Antithetic + control',paired-beta_a*(paired_c-100),4096,beta_a)]
    out['example_methods']=[{'method':name,**summary(values),'pilot_evaluations':pilot,'coefficient':float(bet),'absolute_error':float(abs(values.mean()-ref))} for name,values,pilot,bet in example]
    (ROOT/'figures.json').write_text(json.dumps(FIGURES),encoding='utf-8')
    (ROOT/'computed.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps({'figures':len(FIGURES),'reference':ref,'asian':asian[0],'barrier_reference':barrier_ref,'lsm':rows},indent=2))

if __name__=='__main__':build()
