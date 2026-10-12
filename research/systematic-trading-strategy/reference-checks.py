from pathlib import Path
import json
import numpy as np
from scipy.optimize import brentq
from strategy import market,target_weights,run,rebalance
ROOT=Path(__file__).parent

def independent_account(prices,targets,start,delay,cost_bps,cash_annual,capital,end=None):
    """Solve the holdings equation in shares; independent of the closed-form implementation."""
    if end is None:end=len(prices)-1
    shares=0.;cash=capital;curve=[capital];rows=[]
    rf=(1+cash_annual)**(1/252)-1;c=cost_bps/10000
    for day in range(start+1,end+1):
        P=prices[day-1];equity=cash+shares*P;k=day-1-delay;w=targets[k] if k>=0 else 0
        def equation(q):return q*P-w*(equity-c*abs(q-shares)*P)
        new_shares=brentq(equation,0,equity/P*1.01,xtol=1e-12)
        trade=(new_shares-shares)*P;fee=c*abs(trade)
        cash=cash-trade-fee;shares=new_shares
        post_equity=cash+shares*P
        assert abs(shares*P/post_equity-w)<1e-10
        cash*=1+rf;equity=cash+shares*prices[day];curve.append(equity)
        rows.append({'day':day,'asof':k,'wealth_end':equity,'fee':fee})
    return np.array(curve),rows

cases=[]
configs=[
 ('regimes',5105,1512,63,True,.12,20,10,.02,1,'momentum'),
 ('regimes',5105,1512,63,False,.12,20,10,.02,1,'momentum'),
 ('regimes',5105,1512,63,True,.12,20,0,.02,1,'momentum'),
 ('regimes',5105,1512,63,True,.12,20,35,.02,3,'momentum'),
 ('iid',17,750,42,True,.09,60,8,0,2,'momentum'),
 ('trend',42,900,21,False,.12,20,10,.02,1,'momentum'),
 ('reversion',0,700,126,True,.14,50,17,-.01,4,'contrarian'),
 ('regimes',1,504,252,True,.04,126,100,.15,5,'contrarian'),
 ('iid',4294967295,1000,5,True,.4,5,0,-.05,1,'contrarian'),
 ('regimes',51,600,21,True,.12,20,10,.02,1,'hold'),
 ('regimes',51,600,21,False,.12,20,100,.02,1,'cash')
]
for model,seed,n,L,control,tv,v,c,rf,d,rule in configs:
    prices,_=market(n,seed,model);targets=target_weights(prices,L,rule,control,tv,v)
    options={'lookback':L,'volControl':control,'volTarget':tv,'volWindow':v,'costBps':c,'cashAnnual':rf,'delay':d,'capital':100000,'rule':rule}
    bt=run(prices,L,rule,control,tv,v,c,rf,d)
    independent,rows=independent_account(prices,targets,bt['start'],d,c,rf,100000)
    assert np.allclose(bt['equity'],independent,rtol=1e-11,atol=2e-7)
    assert np.allclose(bt['fees'],[r['fee'] for r in rows],atol=2e-7)
    positions=[0,1,len(independent)//3,len(independent)//2,len(independent)-1]
    m={k:v for k,v in bt['metrics'].items() if k!='drawdown'}
    cases.append({'model':model,'seed':seed,'sessions':n,'options':options,'start':bt['start'],'indices':positions,
                  'prices_head':prices[:10].tolist(),'wealth_reference':independent[positions].tolist(),'metrics':m})
# Randomized post-cost fraction checks, solved independently in share coordinates.
rng=np.random.default_rng(5151)
for _ in range(150):
    E=rng.uniform(1,1e7);P=rng.uniform(.1,1000);h=rng.uniform();w=rng.uniform();c=rng.uniform(0,.01)
    stock,cash,fee,turn=rebalance(E,E*h,w,c)
    old_q=E*h/P
    q=brentq(lambda q:q*P-w*(E-c*abs(q-old_q)*P),0,E/P*1.01,xtol=1e-12)
    assert np.isclose(q*P,stock,rtol=1e-11,atol=1e-7)
    assert np.isclose(stock+cash,E-fee)
    assert np.isclose(stock/(E-fee),w)
    assert cash>=-1e-7
# An unlevered passive account equals price growth after entry cost.
prices,_=market(800,4,'iid')
hold=run(prices,rule='hold',vol_control=False,cost_bps=10,start=64)
assert np.isclose(hold['equity'][-1],100000/1.001*prices[-1]/prices[64],rtol=1e-12)
cash=run(prices,rule='cash',vol_control=False,start=64,cash_annual=.02)
assert np.isclose(cash['metrics']['cagr'],.02,atol=1e-12)
assert cash['metrics']['sharpe'] is None and np.all(cash['fees']==0)
# Suffix replacement: prior formation targets and earned wealth remain identical.
future=prices.copy();future[401:]*=np.linspace(2,8,len(future)-401)
a=target_weights(prices);b=target_weights(future)
assert np.array_equal(a[:401],b[:401])
assert np.allclose(run(prices,end=400)['equity'],run(future,end=400)['equity'],atol=0,rtol=0)
# Weighted account return factor reproduces the saved share ledger.
for row in run(prices)['ledger']:
    asset=row['price_end']/row['price_start']-1
    rf=(1.02)**(1/252)-1;w=row['target'];factor=(1-.001*row['turnover'])*(1+w*asset+(1-w)*rf)
    assert abs(factor-1-row['net_return'])<1e-13
(ROOT/'reference-cases.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
report={'independentAccountCases':len(cases),'rootSolvedRebalances':150,'passiveIdentity':'passed','cashIdentity':'passed','suffixCausality':'passed','returnFactorReconciliation':'passed'}
(ROOT/'reference-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
