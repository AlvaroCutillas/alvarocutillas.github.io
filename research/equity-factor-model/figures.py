from figure_support import *
from model import analyze,cross_section,regression,TRUTH,COV,NAMES
from matplotlib.ticker import PercentFormatter
d=json.loads((ROOT/'computed.json').read_text());data=d['dataset'];F=np.array(data['factors']);a=analyze(data);n=len(F);months=np.arange(1,n+1)
def rates(ax):ax.yaxis.set_major_formatter(PercentFormatter(1));ax._hover_yformat='percent'
def legend(ax):ax.legend(fontsize=8,loc='best')
def done(name,fig,title,detail):
    for ax in fig.axes:
        if ax.get_xlabel() in ['Synthetic month','Stock rank','Stock rank by fitted return','Number of equal-weight stocks','Window end month']:
            ax._hover_snap=True
    save(name,fig,'Figure 00 · '+title,detail)
cols=[ACC,WARM,BLUE,GRAY,'#bbbac7']

fig,axs=plt.subplots(1,2,figsize=(11,3.7))
axs[0].plot(months,a['y'],color=GRAY,label='Observed excess return',lw=1)
axs[0].plot(months,a['all_pred'],color=ACC,label='Fitted factor component',lw=1.5)
for y,col,label in [(a['y'],GRAY,'Observed'),(a['all_pred'],ACC,'Intercept + factors'),(a['residual'],WARM,'Residual')]:axs[1].plot(months,np.cumsum(y),color=col,label=label)
axbase(axs[0],'Synthetic month','Monthly return','Returns and their fitted components')
axbase(axs[1],'Synthetic month','Cumulative arithmetic return','Additive attribution, not compounded wealth')
[rates(x) for x in axs];[legend(x) for x in axs]
done('decomposition',fig,'Factor attribution and residual return','The model is estimated on months 1–180 and applied unchanged through month 240. Cumulative arithmetic returns add exactly; compounding separate components would not preserve this identity.')

fig,ax=plt.subplots(figsize=(11,3.6));cap=analyze(data,model='capm');order=np.argsort(F[:,0]);grid=np.linspace(F[:,0].min(),F[:,0].max(),301)
ax.plot(F[:,0],a['y'],'o',color=GRAY,ms=3,alpha=.6,label='Observed months')
ax.plot(grid,cap['b'][0]+cap['b'][1]*grid,color=ACC,label='Training CAPM line')
axbase(ax,'Market excess return','Portfolio excess return','Covariation identifies beta, not a characteristic score');rates(ax);ax.xaxis.set_major_formatter(PercentFormatter(1));ax._hover_xformat='percent';legend(ax)
done('capm',fig,'Market beta in a return regression','The line uses the first 180 months; the scatter includes all 240 synthetic observations. Marker inspection shows actual observations only at their plotted x-coordinates.')

fig,ax=plt.subplots(figsize=(11,3.6))
for j,col in enumerate(cols):ax.plot(months,np.cumsum(F[:,j]),color=col,label=NAMES[j])
axbase(ax,'Synthetic month','Cumulative arithmetic factor return','Five synthetic factor series');rates(ax);legend(ax)
done('factor-series',fig,'Synthetic factor returns','Market is an excess return; four style series are hypothetical zero-investment factor returns. These are not downloaded Fama–French, QMJ or BAB data and their specified means are not empirical forecasts.')

stocks=data['stocks'];raw=np.array([s['raw'] for s in stocks]);z=np.array([s['z'] for s in stocks]);y=np.array([s['next'] for s in stocks]);sector=np.array([s['sector'] for s in stocks])
fig,axs=plt.subplots(1,2,figsize=(11,3.6));idx=np.arange(1,161);rank=np.argsort(raw[:,0]);clip=np.clip(raw[:,0],*np.quantile(raw[:,0],[.025,.975]))
axs[0].plot(idx,raw[rank,0],color=GRAY,label='Raw descriptor')
axs[0].plot(idx,clip[rank],color=WARM,label='2.5% / 97.5% winsorized')
axs[1].plot(idx,z[rank,0],color=ACC,label='Standardized value score')
axbase(axs[0],'Stock rank','Descriptor units','Clip tails before standardization');axbase(axs[1],'Stock rank','Score (standard deviations)','Mean zero and population variance one');[legend(x) for x in axs]
done('engineering',fig,'Descriptor preprocessing','A synthetic formation-date snapshot of 160 stocks. Winsorization thresholds are cross-sectional quantiles, and each clipped descriptor is centered and scaled within this snapshot.')

fig,ax=plt.subplots(figsize=(11,3.6))
for j,col in enumerate(cols[:4]):ax.plot(np.arange(1,11),cross_section(data,j)['deciles'],'-o',color=col,label=NAMES[j+1])
ax._hover_snap=True;axbase(ax,'Signal decile','Mean next-month return','Realized returns within formation-score deciles');rates(ax);legend(ax)
done('deciles',fig,'Univariate factor sorts','Each decile contains 16 stocks. Lines join discrete decile means; the inspector snaps to a decile. Correlated descriptors and sector effects make these univariate returns different from partial regression coefficients.')

fig,ax=plt.subplots(figsize=(11,3.5))
for bal,col,label in [(False,WARM,'Unrestricted tails'),(True,ACC,'Sector-balanced tails')]:ax.plot(np.arange(1,5),cross_section(data,balanced=bal)['sector_net'],'-o',color=col,label=label)
ax._hover_snap=True;ax.set_xticks([1,2,3,4],['A','B','C','D']);axbase(ax,'Sector index','Net portfolio weight','Dollar neutrality does not imply sector neutrality');rates(ax);legend(ax)
done('neutrality',fig,'Sector exposures of long–short portfolios','Both portfolios are long one unit and short one unit of capital-normalized weights. The balanced construction selects equal tails inside each of four equal-sized sectors, producing zero net weight in every sector.')

fig,axs=plt.subplots(1,2,figsize=(11,3.6));cs=cross_section(data);fit=cs['fit'];order=np.argsort(fit['pred'])
axs[0].plot(idx,y[order],color=GRAY,lw=1,label='Realized stock return');axs[0].plot(idx,fit['pred'][order],color=ACC,label='Cross-sectional fit')
axs[1].plot(idx,fit['e'][order],color=WARM,lw=1,label='Residual')
axbase(axs[0],'Stock rank by fitted return','Next-month return','Joint style and sector attribution');axbase(axs[1],'Stock rank by fitted return','Residual return','Realized minus fitted')
[rates(x) for x in axs];[legend(x) for x in axs]
done('cross-section',fig,'A cross-sectional regression','The realized next-month return is regressed on four standardized formation characteristics and three sector dummies plus an intercept. This is ex post attribution, not a portfolio selected using future returns.')

fig,ax=plt.subplots(figsize=(11,3.5));noise=np.linspace(.001,.10,301)
for slope,col in zip([.005,.01,.02],[BLUE,ACC,WARM]):ax.plot(noise,slope/np.sqrt(slope*slope+noise*noise),color=col,label=f'Linear effect {100*slope:g}%')
axbase(ax,'Specific noise standard deviation','Population Pearson IC','A single independent standardized signal');ax.xaxis.set_major_formatter(PercentFormatter(1));ax._hover_xformat='percent';legend(ax)
done('ic',fig,'Signal strength and cross-sectional noise','For y = θz + ε with Var(z) = 1 and independent ε, IC = θ / sqrt(θ² + σ²). This analytical illustration supplies no empirical estimate of a traded factor premium.')

fig,ax=plt.subplots(figsize=(11,3.5));j=np.arange(1,6);b=a['b'][1:];se=a['hac_se'][1:]
for values,col,label in [(b,ACC,'Estimated beta'),(b-1.95996398454*se,GRAY,'95% lower'),(b+1.95996398454*se,WARM,'95% upper'),(TRUTH,BLUE,'Generating beta')]:ax.plot(j,values,'-o',color=col,label=label,lw=1.5)
ax._hover_snap=True;ax.set_xticks(j,NAMES);axbase(ax,'Factor index','Exposure','Finite samples do not recover every coefficient exactly');legend(ax)
done('betas',fig,'Estimated factor exposures and HAC uncertainty','OLS uses 180 monthly observations. Intervals use asymptotic normal critical value 1.959964 and Newey–West covariance with six lags, Bartlett weights and T/(T−p) adjustment; they are not exact small-sample t intervals.')

fig,ax=plt.subplots(figsize=(11,3.5));rho=np.linspace(-.8,.8,301);true=1.05;value=.5
ax.plot(rho,np.full_like(rho,true),color=ACC,label='Structural market beta')
ax.plot(rho,true+value*rho*.025/.045,color=WARM,label='Population omitted-value slope')
axbase(ax,'Market–value correlation','Market coefficient','Omitting a correlated factor shifts the slope');legend(ax)
done('omission',fig,'Omitted-variable bias','In a two-factor population model, the market-only slope equals βM + βV Cov(M,V)/Var(M). Volatilities are 4.5% and 2.5% per month; no claim is made about a historical market correlation.')

def acf(e,lags=12):
    e=e-e.mean();return np.array([np.dot(e[k:],e[:-k])/np.dot(e,e) for k in range(1,lags+1)])
fig,ax=plt.subplots(figsize=(11,3.5));lags=np.arange(1,13)
ax.plot(lags,acf(a['e']),'-o',color=ACC,label='Fitted residual ACF');ax.plot(lags,.25**lags,color=WARM,label='Generating AR coefficient power')
ax._hover_snap=True;axbase(ax,'Lag (months)','Autocorrelation','Serial dependence survives factor attribution');legend(ax)
done('residuals',fig,'Residual serial correlation','The generating disturbance has AR coefficient 0.25 and state-dependent innovation variance. The displayed sample ACF is centered and normalized by the zero-lag sum of squares.')

fig,ax=plt.subplots(figsize=(11,3.5));ls=np.arange(13);X=np.column_stack([np.ones(180),F[:180]])
ses=[regression(X,a['y'][:180],int(l))['hac_se'][0] for l in ls]
ax.plot(ls,ses,color=ACC,marker='o',label='HAC intercept SE');ax.plot(ls,np.full_like(ls,a['classic_se'][0],dtype=float),color=WARM,label='Classical intercept SE')
ax._hover_snap=True;axbase(ax,'HAC lag count','Monthly alpha standard error','Bandwidth changes the covariance estimate');rates(ax);legend(ax)
done('inference',fig,'Inference with dependent disturbances','Lag zero is heteroskedasticity-robust with the stated finite-sample adjustment. HAC does not change OLS coefficients, and its standard error need not increase monotonically with bandwidth.')

fig,ax=plt.subplots(figsize=(11,3.6));ends=np.arange(60,241);rolling=[]
for end in ends:rolling.append(regression(np.column_stack([np.ones(60),F[end-60:end]]),a['y'][end-60:end],3)['b'][1])
ax.plot(ends,rolling,color=ACC,label='Rolling 60-month market beta');ax.plot(ends,np.full_like(ends,TRUTH[0],dtype=float),color=WARM,label='Constant generating beta')
axbase(ax,'Window end month','Market exposure','Only observations through each window end are used');legend(ax)
done('rolling',fig,'Rolling exposure estimates','The true coefficient is constant in this simulation. Rolling fluctuations illustrate estimation noise, not proof that economic exposure changed.')

fig,axs=plt.subplots(1,2,figsize=(11,3.6));cuts=np.array([60,90,120,150,180,210]);tr=[];test=[]
for c in cuts:
    X=np.column_stack([np.ones(240),F]);f=regression(X[:c],a['y'][:c],3);r=a['y'][c:c+30]-X[c:c+30]@f['b']
    tr.append(f['r2']);test.append(np.sqrt(np.mean(r*r)))
axs[0].plot(cuts,tr,'-o',color=ACC,label='Training R²');axs[1].plot(cuts,test,'-o',color=WARM,label='Next 30-month RMSE')
[setattr(ax,'_hover_snap',True) for ax in axs]
axbase(axs[0],'Training months','R²','Expanding estimation windows');axbase(axs[1],'Training months','Monthly forecast error','Held-out blocks');rates(axs[1]);[legend(x) for x in axs]
done('validation',fig,'Chronological validation','Each coefficient vector is fitted using only the stated prefix. The following 30 months form its evaluation block. This diagnostic display is not used to choose a winning training window.')

fig,ax=plt.subplots(figsize=(11,3.5));N=np.arange(1,201);common=float(TRUTH@COV@TRUTH);specific=.03**2
ax.plot(N,np.sqrt(common+specific/N),color=ACC,label='Total volatility');ax.plot(N,np.sqrt(specific/N),color=WARM,label='Specific volatility');ax.plot(N,np.full_like(N,np.sqrt(common),dtype=float),color=BLUE,label='Common-factor floor')
axbase(ax,'Number of equal-weight stocks','Monthly volatility','Independent specific risk diversifies');rates(ax);legend(ax)
done('diversification',fig,'Diversification and the common-risk floor','All stocks have the same factor exposures, independent 3% specific volatility and equal weights. Total variance is βΣfβ + σ²ε/N; volatility components do not add linearly.')

fig,axs=plt.subplots(1,2,figsize=(11,3.6));values=np.linspace(-1.5,1.5,301);vol=[];vc=[];lc=[]
for v in values:
    p=TRUTH.copy();p[4]=v;var=p@COV@p+.03**2;vol.append(np.sqrt(var));vc.append(p[4]*(COV@p)[4]/var);lc.append(p[0]*(COV@p)[0]/var)
axs[0].plot(values,vol,color=ACC,label='Total monthly volatility');axs[1].plot(values,vc,color=WARM,label='Low-vol variance share');axs[1].plot(values,lc,color=BLUE,label='Market variance share')
axbase(axs[0],'Low-volatility factor exposure','Monthly volatility','A correlated exposure can hedge');axbase(axs[1],'Low-volatility factor exposure','Variance contribution share','Negative contributions are possible')
[rates(x) for x in axs];[legend(x) for x in axs]
done('contributions',fig,'Exposure is different from risk contribution','The theoretical factor covariance is fixed. A negative Euler contribution means the exposure offsets other risk at the current portfolio, not that its standalone variance is negative.')

fig,ax=plt.subplots(figsize=(11,3.5));rng=np.random.default_rng(210);B=rng.normal(0,.4,(30,5));B[:,0]+=1;Ds=np.diag(np.full(30,.03**2));truecov=B@COV@B.T+Ds
sample=rng.multivariate_normal(np.zeros(30),truecov,60);S=np.cov(sample,rowvar=False);shrink=.5*S+.5*np.diag(np.diag(S));jj=np.arange(1,31)
for cov,col,label in [(S,GRAY,'Sample covariance'),(shrink,WARM,'50% diagonal shrinkage'),(truecov,ACC,'Generating factor covariance')]:ax.plot(jj,np.linalg.eigvalsh(cov)[::-1],color=col,label=label)
ax.set_yscale('log');ax._hover_snap=True;axbase(ax,'Eigenvalue index','Monthly variance eigenvalue','Finite observations and covariance regularization');legend(ax)
done('covariance',fig,'Covariance eigenvalues and shrinkage','A separate synthetic 30-stock, 60-month panel is generated from five common factors and independent specific risk. Diagonal shrinkage is a declared 50% example, not an estimated optimal intensity.')

fig,axs=plt.subplots(1,2,figsize=(11,3.7));train=180;mu=F[:train].mean(axis=0);sd=F[:train].std(axis=0);Z=(F[:train]-mu)/sd;yc=a['y'][:train]-a['y'][:train].mean();lams=np.geomspace(.01,1000,101);betas=[];errs=[]
for lam in lams:
    scaled=np.linalg.solve(Z.T@Z+lam*np.eye(5),Z.T@yc);b=scaled/sd;alpha=a['y'][:train].mean()-mu@b;betas.append(b);errs.append(np.sqrt(np.mean((a['y'][train:]-alpha-F[train:]@b)**2)))
betas=np.array(betas)
for j,col in enumerate(cols):axs[0].plot(lams,betas[:,j],color=col,label=NAMES[j])
axs[1].plot(lams,errs,color=WARM,label='Withheld RMSE');[ax.set_xscale('log') for ax in axs]
axbase(axs[0],'Ridge penalty λ','Exposure in original factor units','Factors standardized on training data');axbase(axs[1],'Ridge penalty λ','Monthly error','Sensitivity, not a selected optimum')
rates(axs[1]);[legend(x) for x in axs]
done('ridge',fig,'Ridge regularization and predictive sensitivity','The objective is sum of squared errors plus λ times squared standardized slopes; the intercept is unpenalized. The holdout is shown for explanation and is not used to recommend a selected penalty.')

fig,ax=plt.subplots(figsize=(11,3.5));costs=np.linspace(0,100,101)
for bal,col,label in [(False,WARM,'Unrestricted tails'),(True,ACC,'Sector-balanced tails')]:
    p=cross_section(data,balanced=bal,cost=0);ax.plot(costs,p['gross']-2*costs/1e4,color=col,label=label)
axbase(ax,'One-way establishment cost (basis points)','Net next-month return','Entering one long and one short leg');rates(ax);legend(ax)
done('costs',fig,'Implementation costs change factor outcomes','Weights have gross exposure two and net exposure zero. A one-time linear entry cost cΣ|w| = 2c is deducted. Ongoing rebalancing, financing, stock borrow and impact are outside this snapshot calculation.')

(ROOT/'figures.json').write_text(json.dumps(FIGURES),encoding='utf-8');print('Saved',len(FIGURES),'embedded SVG figures')
