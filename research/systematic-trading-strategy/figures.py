from figure_support import *
from strategy import *
from matplotlib.ticker import PercentFormatter
from scipy.stats import norm
def percent(ax,x=False,y=False):
    if x:ax.xaxis.set_major_formatter(PercentFormatter(1));ax._hover_xformat='percent'
    if y:ax.yaxis.set_major_formatter(PercentFormatter(1));ax._hover_yformat='percent'
def finish(name,fig,title,detail):
    fig.savefig(ROOT/(name+'.png'),dpi=130);save(name,fig,'Figure 00 · '+title,detail)
prices,state=market();N=len(prices)-1;days=np.arange(N+1);returns=prices[1:]/prices[:-1]-1
bt=run(prices);start=bt['start']
gross=run(prices,cost_bps=0)
hold=run(prices,rule='hold',vol_control=False,start=start)
cash=run(prices,rule='cash',vol_control=False,start=start)

fig,axes=plt.subplots(2,1,figsize=(10,5),sharex=True)
axes[0].plot(days,prices,color=ACC,label='Synthetic asset price');axbase(axes[0],'Trading day','Price','A deliberately changing synthetic market')
axes[1].plot(np.arange(1,N+1),returns,color=GRAY,lw=.7,label='Daily simple return');percent(axes[1],y=True)
for ax in axes:ax._hover_snap=True
axbase(axes[1],'Trading day','Return','Changing drift, volatility and serial dependence')
finish('market',fig,'Synthetic price and return observations','1,512 sessions; initial price 100; Mulberry32 seed 5105 and Box–Muller shocks. Five equally sized artificial regimes have specified log-return drift, volatility and AR(1) coefficients. These are teaching data, not market history.')

fig,ax=plt.subplots(figsize=(10,4))
x=np.arange(1,6);r=np.array([.10,-.10,.08,-.06,.04])
correct=np.r_[0,r[:-1]>0].astype(float)*r
illegal=(r>0).astype(float)*r
ax.plot(np.r_[0,x],100*np.r_[1,np.cumprod(1+correct)],color=ACC,marker='o',label='Past-return position')
ax.plot(np.r_[0,x],100*np.r_[1,np.cumprod(1+illegal)],color=WARM,marker='o',label='Illegal same-return selector')
ax.plot(np.r_[0,x],100*np.r_[1,np.cumprod(1+r)],color=BLUE,marker='o',label='Buy and hold')
axbase(ax,'Return period','Wealth index','Future information creates artificial performance');ax.legend(fontsize=8)
finish('timing',fig,'The effect of a look-ahead selector','Five simple returns: +10%, −10%, +8%, −6%, +4%; zero cash return and no costs. The illegal rule selects exposure using the return it then claims to earn. The past-return rule is only a simplified timing example, not the laboratory execution convention.')

fig,ax=plt.subplots(figsize=(10,4))
r=np.tile([.10,-.10],10);x=np.arange(21)
ax.plot(x,np.r_[0,np.cumprod(1+r)-1],color=ACC,marker='o',label='Compounded simple return')
ax.plot(x,np.r_[0,np.cumsum(r)],color=WARM,ls='--',label='Sum of simple returns')
percent(ax,y=True);axbase(ax,'Return period','Cumulative return','Alternating equal percentage moves do not cancel');ax.legend()
finish('compounding',fig,'Compounding and arithmetic aggregation','Twenty alternating +10% and −10% returns. Each two-period cycle multiplies wealth by 0.99. Summing simple returns reports zero while compounded wealth falls.')

L=63;mom=np.full(N+1,np.nan);mom[L:]=prices[L:]/prices[:-L]-1
fig,axes=plt.subplots(2,1,figsize=(10,4.9),sharex=True)
axes[0].plot(days,prices,color=ACC,label='Price')
ma=np.convolve(prices,np.ones(L)/L,mode='valid');axes[0].plot(days[L-1:],ma,color=WARM,label='63-observation moving average');axes[0].legend(fontsize=8)
axbase(axes[0],'Trading day','Price','Smoothing the same price observations')
axes[1].plot(days[L:],mom[L:],color=BLUE,label='63-session trailing return');axes[1].axhline(0,color=GRAY,ls='--')
percent(axes[1],y=True);axbase(axes[1],'Trading day','Trailing return','A time-series momentum formation signal')
for ax in axes:ax._hover_snap=True
finish('momentum',fig,'Trailing returns and a moving-average filter','Same seed-5105 market. The moving average uses 63 price observations; momentum compares price with the price 63 sessions earlier. These related filters have different definitions and need not trigger on the same dates.')

z=np.zeros(N+1)
for k in range(L,N+1):
    win=prices[k-L+1:k+1];z[k]=(prices[k]-win.mean())/win.std(ddof=1)
fig,ax=plt.subplots(figsize=(10,4))
ax.plot(days[L:],z[L:],color=ACC,label='Rolling price z-score')
ax.axhline(-1,color=WARM,ls='--',label='Contrarian entry condition')
axbase(ax,'Trading day','Price z-score','A normalized deviation is not proof of mean reversion');ax._hover_snap=True;ax.legend()
finish('reversion',fig,'A contrarian signal in a changing market','Rolling mean and sample standard deviation of 63 price observations, including the formation-day close. The illustrative long/cash rule is long while z &lt; −1. Price levels need not be stationary, and this standardization does not establish predictability.')

vol=np.array([returns[max(0,k-20):k].std(ddof=1)*np.sqrt(252) if k>=20 else np.nan for k in range(N+1)])
fig,axes=plt.subplots(2,1,figsize=(10,4.9),sharex=True)
axes[0].plot(days[20:],vol[20:],color=WARM,label='Trailing annualized asset volatility');axes[0].axhline(.12,color=BLUE,ls='--',label='12% target');percent(axes[0],y=True);axes[0].legend(fontsize=8)
axbase(axes[0],'Trading day','Annualized volatility','Forecast scale is backward looking')
weights=target_weights(prices)
axes[1].plot(days,weights,color=ACC,label='Formation-day target exposure');percent(axes[1],y=True);axbase(axes[1],'Trading day','Target risky weight','Long/cash momentum with an exposure cap of 100%')
for ax in axes:ax._hover_snap=True
finish('voltarget',fig,'Volatility scaling and risky exposure','63-session momentum, 20-session sample-volatility window, annualization factor 252 and target 12%. Targets use information through the formation close. Realized portfolio volatility need not equal the target.')

costs=np.linspace(0,50,26);out=[run(prices,cost_bps=float(c))['metrics'] for c in costs]
fig,axes=plt.subplots(1,2,figsize=(10,4.2))
axes[0].plot(costs,[v['cagr'] for v in out],color=ACC,label='Net CAGR');axes[0].axhline(.02,color=GRAY,ls='--',label='Cash CAGR');percent(axes[0],y=True)
axbase(axes[0],'One-way cost (bps)','Annualized return','The same signal at different trading costs');axes[0].legend(fontsize=8)
axes[1].plot(costs,[v['sharpe'] for v in out],color=WARM,label='Net excess-return Sharpe');axes[1].axhline(0,color=GRAY,ls='--')
axbase(axes[1],'One-way cost (bps)','Sharpe estimate','Risk-adjusted results after proportional fees')
finish('costs',fig,'Trading-cost sensitivity','Same synthetic market, signal, sizing and common evaluation interval. Cost is an all-in proportional deduction per one-way traded notional; initial investment is charged. Cash earns 2% effective annually. This is not a calibrated broker or market-impact model.')

fig,ax=plt.subplots(figsize=(10,4))
t=np.linspace(0,10,150)
for lam,c in [(.1,ACC),(.3,WARM),(.8,BLUE)]:
    ax.plot(t,1-np.exp(-lam*t),color=c,label='Arrival intensity '+str(lam)+'/unit time')
percent(ax,y=True);axbase(ax,'Waiting time','Probability of at least one arrival','Waiting longer changes opportunity and risk');ax.legend(fontsize=8)
finish('execution',fig,'A simplified execution-opportunity model','Independent Poisson arrivals with constant intensity. The curve is P(at least one arrival) = 1 − exp(−λt), not a real limit-order fill probability: queue position, cancellations, adverse selection and price changes are deliberately absent.')

toyprices=np.array([100,110,99,103.95,98.7525])
toy=run(toyprices,start=0,targets=np.array([1,0,1,0,0]),cost_bps=10,cash_annual=0,capital=100)
fig,ax=plt.subplots(figsize=(10,4))
idx=np.arange(5);stock=np.r_[0,[v['stock_after']*v['price_end']/v['price_start'] for v in toy['ledger']]]
cashv=np.r_[100,[v['cash_after'] for v in toy['ledger']]]
ax.plot(idx,toy['equity'],color=ACC,marker='o',label='Total wealth');ax.plot(idx,stock,color=WARM,marker='o',label='Stock value');ax.plot(idx,cashv,color=BLUE,marker='o',label='Cash balance')
axbase(ax,'Trading day','Currency units','A cash-and-shares ledger reconciles wealth');ax.legend(fontsize=8)
finish('ledger',fig,'Position and cash accounting','Initial wealth 100; toy prices 100, 110, 99, 103.95, 98.7525. Formation targets alternate long/cash; one-session execution delay, 10 bps one-way cost, zero cash return. The first formation-day signal enters at the following close.')

fig,ax=plt.subplots(figsize=(10,4.5))
for b,label,c in [(gross,'Strategy, zero cost',GRAY),(bt,'Strategy, 10 bps',ACC),(hold,'Buy and hold, 10 bps',WARM),(cash,'Cash at 2%',BLUE)]:
    ax.plot(b['days'],b['equity']/b['equity'][0]*100,color=c,label=label)
ax._hover_snap=True;axbase(ax,'Trading day','Wealth index','Common start, complete warm-up and explicit costs');ax.legend(fontsize=8)
finish('equity',fig,'Comparable equity curves','Evaluation begins at close 64 after 63-session signal warm-up plus a one-session delay. The first earned return is day 65. Every curve starts at wealth index 100; strategy and buy-and-hold initial trades pay their specified cost. Cash is not a zero-return benchmark.')

wf,schedule=walk_forward(prices)
fig,axes=plt.subplots(2,1,figsize=(10,4.9),sharex=True)
axes[0].plot(wf['days'],wf['equity']/wf['equity'][0]*100,color=ACC,label='Stitched walk-forward wealth')
fixed=run(prices,vol_control=False,start=504)
axes[0].plot(fixed['days'],fixed['equity']/fixed['equity'][0]*100,color=BLUE,label='Fixed 63-session rule');axes[0].legend(fontsize=8);axbase(axes[0],'Trading day','Wealth index','Past-only selection with execution latency')
look=np.zeros(N+1)
for s in schedule:look[s['fit_close']:s['last_formation_day']+1]=s['lookback']
last_formation=schedule[-1]['last_formation_day']
axes[1].plot(days[504:last_formation+1],look[504:last_formation+1],color=WARM,label='Selected lookback',drawstyle='steps-post')
for ax in axes:ax._hover_snap=True
axbase(axes[1],'Formation day','Lookback (sessions)','Five candidates, refit every 126 sessions')
finish('walkforward',fig,'Walk-forward selection and stitched evaluation','Candidates 21, 42, 63, 126 and 252 sessions; up to 504 past sessions for selection; common eligible training start; 10 bps cost. First fit occurs after close 504 and first influences return 506. Positions and cash continue across evaluation blocks.')

rng=np.random.default_rng(5106);train=rng.normal(0,.01,(400,100,504));test=rng.normal(0,.01,(400,100,252))
ts=np.sqrt(252)*train.mean(axis=2)/train.std(axis=2,ddof=1);os=np.sqrt(252)*test.mean(axis=2)/test.std(axis=2,ddof=1)
Ms=[1,5,10,20,50,100];best=[];future=[]
for m in Ms:
    idx=np.argmax(ts[:,:m],axis=1);best.append(ts[np.arange(400),idx].mean());future.append(os[np.arange(400),idx].mean())
fig,ax=plt.subplots(figsize=(10,4))
ax.plot(Ms,best,color=WARM,marker='o',label='Selected in-sample Sharpe')
ax.plot(Ms,future,color=ACC,marker='o',label='Selected out-of-sample Sharpe')
ax.axhline(0,color=GRAY,ls='--');ax.set_xscale('log');axbase(ax,'Number of tested strategies','Mean annualized sample Sharpe','Selecting the best of noise creates a winner');ax.legend(fontsize=8)
finish('selection',fig,'Multiple testing under a zero-edge null','400 independent experiments; each candidate has IID normal zero-mean returns, standard deviation 1%; training 504 sessions and independent evaluation 252 sessions. NumPy seed 5106. The toy trials are independent, unlike many correlated real strategy variants.')

fig,axes=plt.subplots(1,2,figsize=(10,4.2))
looks=[21,42,63,126,252]
descriptive=[run(prices,L,vol_control=False,start=253)['metrics'] for L in looks]
axes[0].plot(looks,[m['cagr'] for m in descriptive],color=ACC,marker='o',label='Net CAGR')
axes[1].plot(looks,[m['volatility'] for m in descriptive],color=WARM,marker='o',label='Annualized volatility')
for ax,label in zip(axes,['CAGR','Annualized volatility']):
    percent(ax,y=True);axbase(ax,'Lookback (sessions)',label,'Same eligible sample, different rules')
finish('metrics',fig,'Return and volatility comparisons','Long/cash momentum without volatility scaling; lookbacks 21–252; cost 10 bps and cash 2%. All begin at close 253. This is a descriptive sample comparison, not a forecast.')

rho=np.linspace(-.5,.8,160);q=252
factor=np.sqrt(q/(1+2*sum((1-k/q)*rho**k for k in range(1,q))))
fig,ax=plt.subplots(figsize=(10,4))
ax.plot(rho,factor,color=ACC,label='AR(1) aggregation multiplier')
ax.axhline(np.sqrt(252),color=WARM,ls='--',label='IID √252 multiplier')
axbase(ax,'Lag-one return correlation','Daily-to-annual Sharpe multiplier','Autocorrelation changes time aggregation');ax.legend(fontsize=8)
finish('sharpe',fig,'Sharpe scaling under serial dependence','Stationary additive differential returns with autocorrelation ρᵏ and finite variance. The multiplier is √q divided by √(1 + 2Σ(1−k/q)ρᵏ). It concerns aggregated additive returns, not exact compounding of a trading account.')

fig,axes=plt.subplots(2,1,figsize=(10,4.9),sharex=True)
for b,label,c in [(bt,'Strategy',ACC),(hold,'Buy and hold',WARM)]:
    axes[0].plot(b['days'],b['equity']/b['equity'][0]*100,color=c,label=label)
    axes[1].plot(b['days'],b['metrics']['drawdown'],color=c,label=label)
for ax in axes:ax._hover_snap=True;ax.legend(fontsize=8)
axbase(axes[0],'Trading day','Wealth index','The path matters as well as the endpoint')
axbase(axes[1],'Trading day','Drawdown','Relative to each curve’s running maximum');percent(axes[1],y=True)
finish('drawdown',fig,'Equity and drawdown paths','Same common-period strategy and buy-and-hold curves as Figure 10. Drawdown includes the initial wealth observation and is signed: zero at a high-water mark, negative below it.')

Ls=np.arange(21,253,7);fig,ax=plt.subplots(figsize=(10,4.2))
for c,color in [(0,ACC),(10,WARM),(25,BLUE)]:
    vals=[run(prices,int(L),vol_control=False,start=253,cost_bps=c)['metrics']['cagr'] for L in Ls]
    ax.plot(Ls,vals,color=color,label=str(c)+' bps one-way cost')
percent(ax,y=True);ax._hover_snap=True;axbase(ax,'Lookback (sessions)','CAGR','A parameter neighborhood rather than one winning point');ax.legend(fontsize=8)
finish('robustness',fig,'Lookback and trading-cost sensitivity','Same synthetic market and common start at close 253; no volatility scaling. These are exploratory in-sample variants. Inspecting the surface counts as research selection and does not create new out-of-sample evidence.')

participation=np.linspace(.0001,.25,220);fig,ax=plt.subplots(figsize=(10,4))
for sigma,c in [(.01,ACC),(.02,WARM),(.04,BLUE)]:
    impact=.5*sigma*np.sqrt(participation)*10000
    ax.plot(participation,impact,color=c,label='Daily volatility '+str(int(sigma*100))+'%')
percent(ax,x=True);axbase(ax,'Trade / daily traded volume','Illustrative impact (bps)','A larger book need not retain the same cost');ax.legend(fontsize=8)
finish('capacity',fig,'An illustrative capacity curve','Square-root impact toy model: 0.5 × daily volatility × √(trade/volume), converted to bps. The coefficient, participation horizon and functional form require empirical calibration; this figure is not an execution-cost forecast.')

fig,axes=plt.subplots(1,2,figsize=(10,4.2))
rng=np.random.default_rng(5107);rep=[]
# Block resampling of already-realized strategy returns: conditional path risk only.
net=bt['returns'];n=len(net);block=20
for _ in range(600):
    starts=rng.integers(0,n,size=int(np.ceil(n/block)))
    res=np.concatenate([net[(np.arange(block)+s)%n] for s in starts])[:n]
    eq=np.r_[1,np.cumprod(1+res)]
    rep.append([(eq[-1])**(252/n)-1,np.min(eq/np.maximum.accumulate(eq)-1)])
rep=np.array(rep)
for ax,k,label,c in zip(axes,[0,1],['CAGR','Maximum signed drawdown'],[ACC,WARM]):
    hist,edges=np.histogram(rep[:,k],bins=35,density=True);mid=(edges[1:]+edges[:-1])/2
    ax.plot(mid,hist,color=c,label='Circular-block resamples');ax._hover_snap=True
    percent(ax,x=True);axbase(ax,label,'Resample density','Conditional uncertainty in '+('growth' if k==0 else 'path losses'))
finish('bootstrap',fig,'Block resampling of realized strategy returns','600 circular moving-block resamples of the fixed strategy’s net return series, block length 20, NumPy seed 5107. This resamples returns without rerunning signals or refitting parameters; it is a conditional path diagnostic, not a complete strategy-research uncertainty analysis.')

fig,ax=plt.subplots(figsize=(10,4))
cost=np.r_[0,np.cumsum(bt['fees'])/100000];drift=[]
ax.plot(bt['days'],cost,color=WARM,label='Cumulative nominal fees / initial wealth')
ax.plot(bt['days'],gross['equity']/100000-bt['equity']/100000,color=ACC,label='Gross-minus-net wealth / initial wealth')
percent(ax,y=True);ax._hover_snap=True;axbase(ax,'Trading day','Fraction of initial wealth','Fees and lost compounding are different quantities');ax.legend(fontsize=8)
finish('attribution',fig,'Trading costs and cumulative wealth drag','Nominal fee payments are accumulated without reinvestment. Gross-minus-net wealth also reflects the compounding of wealth that would have remained invested. Neither curve is a return series by itself.')

def trim(m):return {k:v for k,v in m.items() if k!='drawdown'}
computed={'metrics':{name:trim(b['metrics']) for name,b in [('Strategy, gross',gross),('Strategy, net',bt),('Buy and hold',hold),('Cash',cash)]},
          'start':start,'periods':len(bt['returns']),'ledger':toy['ledger'],'walk':schedule,
          'walk_metrics':trim(wf['metrics']),'fixed_walk_metrics':trim(fixed['metrics']),
          'bootstrap':{'cagr':np.quantile(rep[:,0],[.025,.975]).tolist(),'drawdown':np.quantile(rep[:,1],[.025,.975]).tolist()},
          'selection':{'trials':Ms,'train':best,'test':future}}
(ROOT/'figures.json').write_text(json.dumps(FIGURES),encoding='utf-8')
(ROOT/'computed.json').write_text(json.dumps(computed,indent=2),encoding='utf-8')
(ROOT/'market.json').write_text(json.dumps({'prices':prices.tolist(),'regimes':state.tolist()}),encoding='utf-8')
print('Generated',len(FIGURES),'figures; strategy net CAGR',bt['metrics']['cagr'])
