from pathlib import Path
import math
import numpy as np

class Random:
    """Mulberry32 + Box–Muller, matched to the offline browser laboratory."""
    def __init__(self,seed): self.a=int(seed)&0xffffffff; self.spare=None
    def uniform(self):
        self.a=(self.a+0x6D2B79F5)&0xffffffff
        t=self.a
        t=((t^(t>>15))*(t|1))&0xffffffff
        t=(t ^ ((t+(((t^(t>>7))*(t|61))&0xffffffff))&0xffffffff))&0xffffffff
        return ((t^(t>>14))&0xffffffff)/4294967296
    def normal(self):
        if self.spare is not None: z=self.spare;self.spare=None;return z
        u=self.uniform()+.5/4294967296;v=self.uniform()
        r=math.sqrt(-2*math.log(u));a=2*math.pi*v
        self.spare=r*math.sin(a);return r*math.cos(a)

def market(n=1512,seed=5105,model='regimes'):
    rng=Random(seed);gprev=0.;p=[100.];regime=[]
    for j in range(n):
        state=min(4,j*5//n)
        if model=='regimes':
            m=[.0006,-.0007,.0005,0,.0003][state]
            phi=[.12,.10,.15,-.20,.05][state]
            sd=[.008,.016,.010,.012,.009][state]
        else:
            m=.0002;sd=.01;phi={'iid':0,'trend':.20,'reversion':-.20}[model]
        g=m+phi*gprev+sd*rng.normal();p.append(p[-1]*math.exp(g));regime.append(state);gprev=g
    return np.array(p),np.array(regime)

def target_weights(prices,lookback=63,rule='momentum',vol_control=True,target_vol=.12,vol_window=20):
    n=len(prices)-1;r=prices[1:]/prices[:-1]-1
    target=np.zeros(n+1)
    warm=max(lookback,vol_window if vol_control else 0)
    for k in range(warm,n+1):
        if rule=='hold': signal=1.
        elif rule=='cash': signal=0.
        elif rule=='momentum':signal=float(prices[k]>prices[k-lookback])
        else:
            window=prices[k-lookback+1:k+1];s=window.std(ddof=1)
            z=(prices[k]-window.mean())/s if s>1e-14 else 0
            signal=float(z<-1)
        vol=r[k-vol_window:k].std(ddof=1)*np.sqrt(252) if vol_control else 0
        scale=min(1.,target_vol/vol) if vol_control and vol>1e-14 else 1.
        target[k]=signal*scale
    return target

def rebalance(equity,stock_value,w,cost):
    """Desired stock fraction is measured after proportional trading costs."""
    h=stock_value/equity
    u=w*(1+cost*h)/(1+cost*w) if w>=h else w*(1-cost*h)/(1-cost*w)
    turnover=abs(u-h);fee=equity*cost*turnover
    stock=equity*u;cash=equity-fee-stock
    return stock,cash,fee,turnover

def run(prices,lookback=63,rule='momentum',vol_control=True,target_vol=.12,vol_window=20,
        cost_bps=10,cash_annual=.02,delay=1,start=None,end=None,targets=None,capital=100000):
    prices=np.asarray(prices);n=len(prices)-1
    if targets is None: targets=target_weights(prices,lookback,rule,vol_control,target_vol,vol_window)
    if start is None:start=max(lookback,vol_window if vol_control else 0)+delay
    if end is None:end=n
    c=cost_bps/10000;rf=(1+cash_annual)**(1/252)-1
    shares=0.;cash=capital;equity=capital;curve=[equity];ledger=[];returns=[];exposure=[];turnover=[];fees=[]
    for j in range(start+1,end+1):
        k=j-1-delay;w=targets[k] if k>=0 else 0
        begin=equity;old_stock=shares*prices[j-1]
        new_stock,cash,fee,turn=rebalance(begin,old_stock,w,c)
        shares=new_stock/prices[j-1]
        after=begin-fee;cash_after=cash
        cash*=1+rf;equity=shares*prices[j]+cash
        r=equity/begin-1
        ledger.append({'day':j,'asof':k,'price_start':float(prices[j-1]),'price_end':float(prices[j]),'wealth_start':float(begin),
                       'target':float(w),'turnover':float(turn),'fee':float(fee),'stock_after':float(new_stock),'cash_after':float(cash_after),
                       'wealth_after_cost':float(after),'wealth_end':float(equity),'net_return':float(r)})
        curve.append(equity);returns.append(r);exposure.append(w);turnover.append(turn);fees.append(fee)
    result={'start':start,'end':end,'days':np.arange(start,end+1),'equity':np.array(curve),'returns':np.array(returns),
            'exposure':np.array(exposure),'turnover':np.array(turnover),'fees':np.array(fees),'ledger':ledger,'rf':rf}
    result['metrics']=metrics(result)
    return result

def metrics(result):
    r=result['returns'];e=result['equity'];n=len(r);rf=result['rf']
    x=r-rf;sd=x.std(ddof=1) if n>1 else 0
    dd=e/np.maximum.accumulate(e)-1
    mean=x.mean() if n else 0;down=np.sqrt(np.mean(np.minimum(x,0)**2)) if n else 0
    return {'total_return':float(e[-1]/e[0]-1),'cagr':float((e[-1]/e[0])**(252/n)-1) if n else 0,
            'volatility':float(r.std(ddof=1)*np.sqrt(252)) if n>1 else 0,'sharpe':float(mean/sd*np.sqrt(252)) if sd>1e-12 else None,
            'sortino':float(mean/down*np.sqrt(252)) if down>1e-12 else None,'max_drawdown':float(dd.min()),
            'annual_turnover':float(result['turnover'].sum()*252/n) if n else 0,'orders':int(np.sum(result['turnover']>1e-10)),
            'total_fees':float(result['fees'].sum()),'average_exposure':float(result['exposure'].mean()) if n else 0,
            'drawdown':dd.tolist()}

def walk_forward(prices,candidates=(21,42,63,126,252),initial=504,block=126,delay=1,cost_bps=10):
    n=len(prices)-1;targets=np.zeros(n+1);schedule=[];cache={L:target_weights(prices,L,vol_control=False) for L in candidates}
    for fit in range(initial,n,block):
        train_start=max(252+delay,fit-504);scores=[]
        for L in candidates:
            bt=run(prices,L,vol_control=False,start=train_start,end=fit,delay=delay,cost_bps=cost_bps,targets=cache[L])
            scores.append(bt['metrics']['sharpe'] if bt['metrics']['sharpe'] is not None else -np.inf)
        chosen=candidates[int(np.argmax(scores))];last=min(n+1,fit+block)
        targets[fit:last]=cache[chosen][fit:last]
        schedule.append({'fit_close':fit,'training_start':train_start,'lookback':chosen,'training_sharpe':float(max(scores)),
                         'first_affected_return':fit+delay+1,'last_formation_day':last-1})
    return run(prices,vol_control=False,start=initial,delay=delay,cost_bps=cost_bps,targets=targets),schedule
