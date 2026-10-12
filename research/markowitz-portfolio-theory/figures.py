from figure_support import *
from portfolio import *
from matplotlib.ticker import PercentFormatter

def percent(ax,x=False,y=False):
    if x:
        ax.xaxis.set_major_formatter(PercentFormatter(1));ax._hover_xformat='percent'
    if y:
        ax.yaxis.set_major_formatter(PercentFormatter(1));ax._hover_yformat='percent'

def build():
    out={'assets':[{'name':f'Asset {c}','return':float(m),'volatility':float(v)} for c,m,v in zip('ABC',MU,VOL)],
         'covariance':COV.tolist(),'correlation':CORR.tolist(),'risk_free':RF}
    # 1. Correlation, not an average of volatilities, controls diversification.
    w=np.linspace(0,1,201);fig,ax=plt.subplots(figsize=(9.2,3.6))
    for rho,col in zip([-1,-.5,0,.5,1],[BLUE,ACC,GRAY,WARM,'#b7bdba']):
        v=np.sqrt(np.maximum((w*.10)**2+((1-w)*.20)**2+2*w*(1-w)*.1*.2*rho,0))
        ax.plot(w,v,color=col,label=f'Correlation {rho:+.1f}')
    axbase(ax,'Weight in asset A','Portfolio volatility');percent(ax,True,True);ax.legend(ncol=3,fontsize=8)
    save('correlation',fig,'Figure 01 · Correlation and two-asset diversification','Asset volatilities 10% and 20%; fully invested, nonnegative weights. At correlation −1, weight 2/3 in A gives zero variance in this idealised singular model. The positive-definite assumption and inverse-based formulas do not apply to that singular endpoint.')
    # 2. A cloud illustrates feasible portfolios but cannot establish the optimum.
    rng=np.random.default_rng(3001);cloud=rng.dirichlet(np.ones(3),size=1800)
    fig,ax=plt.subplots(figsize=(9.2,3.8));ax.scatter(np.sqrt(np.einsum('ij,jk,ik->i',cloud,COV,cloud)),cloud@MU,s=3,color=GRAY,alpha=.22)
    g=long_only();gm=moments(g);targets=np.linspace(gm['return'],MU.max(),120);ws=np.array([long_only(target=t) for t in targets]);vs=np.sqrt(np.einsum('ij,jk,ik->i',ws,COV,ws))
    ax.plot(vs,targets,color=ACC,label='Long-only efficient frontier');ax.plot([gm['volatility']]*2,[gm['return']]*2,marker='o',color=WARM,label='Global minimum variance')
    for i,c in enumerate('ABC'):ax.annotate('Asset '+c,(VOL[i],MU[i]),xytext=(5,4),textcoords='offset points',fontsize=8)
    ax.scatter(VOL,MU,color=WARM,s=14);axbase(ax,'Portfolio volatility','Expected return');percent(ax,True,True);ax.legend(fontsize=8)
    save('feasible',fig,'Figure 02 · Feasible portfolios and the efficient boundary','Three-asset annual simple-return benchmark; expected returns 6%, 10%, 14%, volatilities 10%, 18%, 28%, correlations AB = .20, AC = .10, BC = .35. Cloud: 1,800 Dirichlet draws, seed 3001. Frontier: constrained optimisation, not the outer edge of the random cloud.')
    # 3. The common covariance term survives increasing breadth.
    n=np.arange(1,101);fig,ax=plt.subplots(figsize=(9.2,3.5))
    for rho,col in zip([0,.1,.3,.6],[ACC,GRAY,WARM,BLUE]):ax.plot(n,.2*np.sqrt(rho+(1-rho)/n),color=col,label=f'Equal correlation {rho:.1f}')
    axbase(ax,'Number of assets n','Equal-weight portfolio volatility');percent(ax,y=True);ax.legend(fontsize=8,ncol=2)
    save('breadth',fig,'Figure 03 · Diversification removes idiosyncratic risk, not common risk','Each asset has 20% volatility and the displayed equal pairwise correlation. Formula σ²[ρ + (1−ρ)/n]. Nonnegative ρ keeps the correlation matrix admissible for every plotted dimension; negative equal correlation cannot be held fixed as n grows without limit.')
    # 4. Preferences are contours in the same risk-return plane.
    s=np.linspace(0,.30,180);fig,ax=plt.subplots(figsize=(9.2,3.5))
    for gamma,col in zip([1,3,6],[GRAY,ACC,WARM]):ax.plot(s,.04+gamma*s*s/2,color=col,label=f'Risk aversion γ = {gamma}')
    axbase(ax,'Portfolio volatility','Expected return at fixed utility 4%');percent(ax,True,True);ax.legend(fontsize=8)
    save('utility',fig,'Figure 04 · Mean–variance indifference curves','Contours of μ − γσ²/2 = 4%, using decimal return units. Higher risk aversion requires more expected return to compensate for the same variance. These are preference contours, not attainable portfolio frontiers.')
    # 5. The scalar quadratic makes the GMV derivative visible.
    rho=.2;s1=.1;s2=.18;w=np.linspace(-.2,1.2,200);variance=w*w*s1*s1+(1-w)**2*s2*s2+2*w*(1-w)*rho*s1*s2
    minw=(s2*s2-rho*s1*s2)/(s1*s1+s2*s2-2*rho*s1*s2);fig,ax=plt.subplots(figsize=(9.2,3.5));ax.plot(w,variance,color=ACC,label='Two-asset variance');ax.axvline(minw,color=WARM,ls='--',label='Minimum-variance weight');axbase(ax,'Weight in asset A','Return variance');percent(ax,x=True);ax.legend(fontsize=8)
    save('gmv',fig,'Figure 05 · The minimum-variance weight minimises a quadratic','Assets A and B: σA = 10%, σB = 18%, correlation .20. The minimum occurs at wA = '+f'{minw:.6f}'+'. Variance uses squared decimal-return units; it is not a percentage volatility.')
    # 6. Separate the lower and upper branches before exporting x-monotone curves.
    g=unrestricted();mg=moments(g);low=np.linspace(-.02,mg['return'],130);high=np.linspace(mg['return'],.22,160);fig,ax=plt.subplots(figsize=(9.2,3.6))
    for tar,col,lab in [(low,GRAY,'Minimum-variance boundary · lower branch'),(high,ACC,'Efficient frontier · upper branch')]:
        weights=np.array([unrestricted(target=t) for t in tar]);vv=np.sqrt(np.einsum('ij,jk,ik->i',weights,COV,weights));ax.plot(vv,tar,color=col,label=lab)
    axbase(ax,'Portfolio volatility','Expected return');percent(ax,True,True);ax.legend(fontsize=8)
    save('frontier',fig,'Figure 06 · The minimum-variance boundary has two branches','Benchmark inputs, unrestricted short selling and net weights summing to one. Only the branch at or above the global minimum-variance return is efficient for increasing mean and decreasing variance. The lower branch is dominated at the same volatility.')
    # 7. Weights, unlike prices, can be negative when short sales are permitted.
    tar=np.linspace(.02,.20,160);ww=np.array([unrestricted(target=t) for t in tar]);fig,ax=plt.subplots(figsize=(9.2,3.6))
    for i,col in enumerate([ACC,WARM,BLUE]):ax.plot(tar,ww[:,i],color=col,label='Asset '+'ABC'[i])
    ax.axhline(0,color=GRAY,lw=.8);axbase(ax,'Target expected return','Portfolio weight');percent(ax,True,True);ax.legend(fontsize=8)
    save('weights',fig,'Figure 07 · Unrestricted frontier weights are affine in target return','Benchmark inputs and no leverage bound. The net budget stays at one while gross exposure can exceed one. The ability to extrapolate the frontier is mathematical permission to take long and short positions, not an executable financing assumption.')
    # 8. A risk-free allocation is a line through the tangency portfolio.
    wt=tangency();mt=moments(wt);s=np.linspace(0,.32,200);fig,ax=plt.subplots(figsize=(9.2,3.6))
    tar=np.linspace(mg['return'],.24,140);vv=np.array([moments(unrestricted(target=t))['volatility'] for t in tar]);ax.plot(vv,tar,color=GRAY,label='Risky efficient frontier');ax.plot(s,RF+(mt['return']-RF)/mt['volatility']*s,color=ACC,label='Capital allocation line');ax.scatter([mt['volatility']],[mt['return']],color=WARM,s=28);axbase(ax,'Portfolio volatility','Expected return');percent(ax,True,True);ax.legend(fontsize=8)
    save('allocation',fig,'Figure 08 · The risk-free asset and the tangency portfolio','Risk-free simple return 2%, benchmark risky moments, common borrowing/lending rate and unrestricted leverage. The line shown is the positive-risky-allocation ray. Negative allocations use |y|σT for volatility and form a different ray.')
    # 9. The financing opportunity changes the selected risky fund.
    rates=np.linspace(0,.045,100);tw=np.array([tangency(rf=r) for r in rates]);fig,ax=plt.subplots(figsize=(9.2,3.5))
    for i,col in enumerate([ACC,WARM,BLUE]):ax.plot(rates,tw[:,i],color=col,label='Asset '+'ABC'[i])
    axbase(ax,'Risk-free simple return','Tangency portfolio weight');percent(ax,True,True);ax.legend(fontsize=8)
    save('tangency',fig,'Figure 09 · Tangency weights depend on the risk-free rate','All plotted rates are below the benchmark global minimum-variance return, so the conventional positive-budget tangency is well defined. Holding the risky mean vector fixed while changing financing is a comparative-static model experiment.')
    # 10. Risk aversion determines the amount of the fund, not its composition.
    gam=np.linspace(1,12,120);y=(mt['return']-RF)/(gam*mt['variance']);fig,ax=plt.subplots(figsize=(9.2,3.5));ax.plot(gam,y,color=ACC,label='Risky tangency allocation y');ax.plot(gam,1-y,color=WARM,label='Risk-free allocation 1 − y');ax.axhline(0,color=GRAY,lw=.8);axbase(ax,'Risk aversion γ','Fraction of initial wealth');percent(ax,y=True);ax.legend(fontsize=8)
    save('aversion',fig,'Figure 10 · Risk aversion and borrowing or lending','Objective μ − γσ²/2 with decimal returns and risk-free return 2%. Negative cash weights denote borrowing. The example assumes the same borrowing and lending rate, and ignores margin and financing limits.')
    # 11. Restricting the feasible set cannot improve the same model optimum.
    fig,ax=plt.subplots(figsize=(9.2,3.6));tar=np.linspace(mg['return'],.16,150);ax.plot([moments(unrestricted(target=t))['volatility'] for t in tar],tar,color=GRAY,label='Unrestricted efficient frontier')
    gl=long_only();mgl=moments(gl);tl=np.linspace(mgl['return'],.14,120);ax.plot([moments(long_only(target=t))['volatility'] for t in tl],tl,color=ACC,label='Long-only efficient frontier');axbase(ax,'Portfolio volatility','Expected return');percent(ax,True,True);ax.legend(fontsize=8)
    save('longonly',fig,'Figure 11 · Short-sale constraints change the feasible frontier','Same population moments for both curves. Long-only returns cannot exceed the highest constituent mean, 14%, or fall below 6%. A constrained portfolio may perform better with estimated inputs, but it cannot beat the unrestricted optimum under identical known inputs and target.')
    # 12. A concentration cap changes feasible targets and active faces.
    cap=.6;targets=np.linspace(.076,.124,120);cw=np.array([long_only(target=t,cap=cap) for t in targets]);fig,ax=plt.subplots(figsize=(9.2,3.6))
    for i,col in enumerate([ACC,WARM,BLUE]):ax.plot(targets,cw[:,i],color=col,label='Asset '+'ABC'[i])
    ax.axhline(cap,color=GRAY,ls='--',label='60% position cap');axbase(ax,'Target expected return','Long-only portfolio weight');percent(ax,True,True);ax.legend(fontsize=8)
    save('caps',fig,'Figure 12 · Position limits create changes in active constraints','Benchmark moments, 0 ≤ wi ≤ 60%, sum wi = 1. Feasible expected returns run from 7.6% to 12.4%. Weights are continuous and piecewise affine in this convex quadratic problem; corners occur when constraints enter or leave the active set.')
    # 13. Capital allocation and risk allocation are different quantities.
    wa=np.linspace(0,1,130);rr=[]
    for a in wa:
        w=np.array([a,(1-a)/2,(1-a)/2]);s=np.sqrt(w@COV@w);rr.append(w*(COV@w)/(s*s))
    rr=np.array(rr);fig,ax=plt.subplots(figsize=(9.2,3.5))
    for i,col in enumerate([ACC,WARM,BLUE]):ax.plot(wa,rr[:,i],color=col,label='Asset '+'ABC'[i])
    axbase(ax,'Capital weight in asset A','Share of portfolio variance');percent(ax,True,True);ax.legend(fontsize=8)
    save('risk',fig,'Figure 13 · Component risk differs from capital weights','Remaining capital is split equally between B and C. Variance contributions wi(Σw)i sum to total variance; dividing by total variance gives the displayed shares. These shares are also the normalised Euler volatility contributions.')
    # 14. Optimisation reacts to a mean input, even if the change is uncertain.
    delta=np.linspace(-.012,.012,120);mw=np.array([tangency(mu=MU+np.array([d,0,0])) for d in delta]);fig,ax=plt.subplots(figsize=(9.2,3.5))
    for i,col in enumerate([ACC,WARM,BLUE]):ax.plot(delta,mw[:,i],color=col,label='Asset '+'ABC'[i])
    axbase(ax,'Change in expected return of A','Tangency portfolio weight');percent(ax,True,True);ax.legend(fontsize=8)
    save('sensitivity',fig,'Figure 14 · Expected-return changes propagate into portfolio weights','Risk-free return 2% and covariance held fixed. The horizontal axis changes A’s annual expected simple return by up to ±1.2 percentage points. This is input sensitivity, not evidence that any changed estimate is more accurate.')
    # 15. Known population covariance permits an honest synthetic evaluation.
    rng=np.random.default_rng(3002);lam=np.linspace(0,1,21);ins=[];true=[];gross=[]
    sets=[rng.multivariate_normal(MU,COV,size=45) for _ in range(240)]
    for l in lam:
        a=[];b=[];c=[]
        for sample in sets:
            sc=np.cov(sample,rowvar=False,ddof=1);est=(1-l)*sc+l*np.diag(np.diag(sc));w=unrestricted(cov=est);a.append(np.sqrt(w@est@w));b.append(np.sqrt(w@COV@w));c.append(abs(w).sum())
        ins.append(np.mean(a));true.append(np.mean(b));gross.append(np.mean(c))
    fig,ax=plt.subplots(figsize=(9.2,3.5));ax.plot(lam,ins,color=GRAY,label='Predicted volatility · fitted covariance');ax.plot(lam,true,color=ACC,label='Population volatility · held-out target');ax.axhline(mg['volatility'],color=WARM,ls='--',label='Population GMV volatility');axbase(ax,'Diagonal shrinkage intensity δ','Average portfolio volatility');percent(ax,True,True);ax.legend(fontsize=8)
    save('shrinkage',fig,'Figure 15 · Estimation and shrinkage in a controlled experiment','240 independent samples of 45 IID one-year multivariate normal simple returns; seed 3002. Covariance only is estimated; GMV does not use means. Diagonal shrinkage intensities are illustrative and not fitted Ledoit–Wolf intensities. Population risk is calculated from the known generating covariance; no intensity is selected using these reported test risks.')
    # 16. The same starting weights define different policies over time.
    rng=np.random.default_rng(3003);ret=rng.multivariate_normal(MU/12,COV/12,size=120);initial=np.array([.5,.3,.2]);buy=(initial*np.cumprod(1+ret,axis=0)).sum(axis=1);reb=np.cumprod(1+ret@initial);times=np.arange(121)/12;fig,ax=plt.subplots(figsize=(9.2,3.5));ax.plot(times,np.r_[1,buy],color=WARM,label='Buy and hold');ax.plot(times,np.r_[1,reb],color=ACC,label='Monthly reset to initial weights');axbase(ax,'Time (years)','Wealth / initial wealth');ax.legend(fontsize=8)
    save('rebalancing',fig,'Figure 16 · Fixed initial weights are not a complete trading policy','Synthetic monthly simple returns with mean μ/12 and covariance Σ/12, seed 3003; starting weights 50%, 30%, 20%. Annualisation is an IID moment approximation; these monthly inputs do not imply exact compounded annual simple-return moments. No costs, no external flows, and no claim of one policy’s general superiority.')
    out['constants']={}
    one=np.ones(3);u=np.linalg.solve(COV,one);v=np.linalg.solve(COV,MU);A=one@u;B=one@v;C=MU@v
    out['constants']={'A':float(A),'B':float(B),'C':float(C),'D':float(A*C-B*B)}
    out['portfolios']={name:moments(w) for name,w in [('Equal weight',np.ones(3)/3),('GMV unrestricted',g),('GMV long-only',gl),('Target 10% unrestricted',unrestricted(target=.1)),('Target 10% long-only',long_only(target=.1)),('Tangency unrestricted',wt),('Tangency long-only',tangency(longonly=True))]}
    for p in out['portfolios'].values():p['sharpe']=(p['return']-RF)/p['volatility']
    out['risk_contributions']=(np.ones(3)/3*(COV@(np.ones(3)/3))/np.sqrt(np.ones(3)/3@COV@(np.ones(3)/3))).tolist()
    (ROOT/'computed.json').write_text(json.dumps(out,indent=2),encoding='utf-8');(ROOT/'figures.json').write_text(json.dumps(FIGURES),encoding='utf-8')
    print(json.dumps({'figures':len(FIGURES),'constants':out['constants'],'portfolios':out['portfolios']},indent=2))

if __name__=='__main__':build()
