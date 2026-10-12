"""Reproducible synthetic examples. Monthly returns are decimals."""
from pathlib import Path
import json
import numpy as np
from scipy.stats import rankdata
ROOT=Path(__file__).parent
NAMES=['Market','Value','Momentum','Quality','Low volatility']
TRUTH=np.array([1.05,.35,.25,.45,.20])
CORR=np.array([[1,.15,-.1,-.05,-.35],[.15,1,-.25,.1,.05],[-.1,-.25,1,.15,-.2],[-.05,.1,.15,1,.3],[-.35,.05,-.2,.3,1]])
STD=np.array([.045,.025,.035,.022,.020])
COV=CORR*STD[:,None]*STD[None,:]

def dataset():
    rng=np.random.default_rng(202608)
    factors=rng.multivariate_normal(np.array([.005,.002,.003,.0015,.001]),COV,240)
    eps=[];e=0.
    for i in range(240):
        innovation=.02*(1+.35*abs((factors[i,0]-.005)/.045))*rng.normal()
        e=.25*e+innovation;eps.append(e)
    rng=np.random.default_rng(991);n=160
    sector=np.arange(n)%4;cap=np.exp(2+.9*rng.normal(size=n))
    raw=np.zeros((n,4));raw[:,0]=.8*rng.normal(size=n)+np.array([.5,-.4,.2,-.3])[sector]
    raw[:,1]=.6*rng.normal(size=n)+.25*raw[:,0]+np.array([-.2,.4,0,-.2])[sector]
    raw[:,2]=.6*rng.normal(size=n)-.2*raw[:,0]+.12*np.log(cap)
    raw[:,3]=.7*rng.normal(size=n)-.3*raw[:,1]+np.array([.3,-.2,.2,-.3])[sector]
    low,high=np.quantile(raw,[.025,.975],axis=0);clipped=np.clip(raw,low,high)
    z=(clipped-clipped.mean(axis=0))/clipped.std(axis=0)
    y=.006+z@np.array([.009,.012,.006,-.004])+np.array([.008,-.004,.002,-.006])[sector]+.025*rng.normal(size=n)
    stocks=[{'id':f'EQ{i+1:03d}','sector':int(sector[i]),'cap':float(cap[i]),'raw':raw[i].tolist(),'z':z[i].tolist(),'next':float(y[i])} for i in range(n)]
    return {'seed':202608,'factors':factors.tolist(),'epsilon':eps,'names':NAMES,'truth':TRUTH.tolist(),'alpha':.0004,'stocks':stocks,'covariance':COV.tolist(),'signalSeed':991}

def regression(X,y,lags=6):
    X=np.asarray(X);y=np.asarray(y);n,k=X.shape
    b=np.linalg.lstsq(X,y,rcond=None)[0];pred=X@b;e=y-pred;inv=np.linalg.inv(X.T@X)
    scores=X*e[:,None];meat=scores.T@scores
    for lag in range(1,lags+1):
        cross=scores[lag:].T@scores[:-lag]
        meat+=(1-lag/(lags+1))*(cross+cross.T)
    hac=inv@meat@inv*n/(n-k)
    classic=inv*(e@e/(n-k))
    r2=1-e@e/np.sum((y-y.mean())**2)
    return {'b':b,'pred':pred,'e':e,'hac_se':np.sqrt(np.maximum(0,np.diag(hac))),
            'classic_se':np.sqrt(np.diag(classic)),'r2':r2,'condition':float(np.linalg.cond(X))}

def analyze(d,beta=TRUTH,alpha=.0004,noise=.02,train=180,lags=6,model='style'):
    F=np.asarray(d['factors']);y=alpha+F@beta+np.asarray(d['epsilon'])*noise/.02
    used=F if model=='style' else F[:,:1]
    X=np.column_stack([np.ones(len(F)),used]);fit=regression(X[:train],y[:train],lags)
    pred=X@fit['b'];res=y-pred;S=np.cov(used[:train],rowvar=False)
    S=np.atleast_2d(S);bs=fit['b'][1:];system=float(bs@S@bs);specific=float(fit['e']@fit['e']/(train-1))
    variance=system+specific;contributions=np.r_[bs*(S@bs),specific]
    return {**fit,'y':y,'all_pred':pred,'residual':res,'rmse':float(np.sqrt(np.mean(res[train:]**2))),
            'covariance':S,'system':system,'specific':specific,'variance':variance,'contributions':contributions,
            'volatility':float(np.sqrt(variance)),'test_mean':float(res[train:].mean())}

def cross_section(d,style=0,tail=20,balanced=True,cost=10):
    stocks=d['stocks'];z=np.array([s['z'] for s in stocks]);y=np.array([s['next'] for s in stocks]);sectors=np.array([s['sector'] for s in stocks]);n=len(stocks)
    weights=np.zeros(n);groups=[np.where(sectors==s)[0] for s in range(4)] if balanced else [np.arange(n)]
    for group in groups:
        ordered=group[np.argsort(z[group,style],kind='stable')];k=round(len(group)*tail/100)
        weights[ordered[-k:]]=1/(len(groups)*k);weights[ordered[:k]]=-1/(len(groups)*k)
    gross=float(weights@y);turnover=float(np.abs(weights).sum());net=gross-cost/1e4*turnover
    deciles=[];order=np.argsort(z[:,style],kind='stable')
    for bucket in np.array_split(order,10):deciles.append(float(y[bucket].mean()))
    X=np.column_stack([np.ones(n),z,*[(sectors==j).astype(float) for j in [1,2,3]]])
    fit=regression(X,y,0)
    return {'weights':weights,'gross':gross,'net':net,'turnover':turnover,'deciles':deciles,'exposure':weights@z,
            'sector_net':np.array([weights[sectors==s].sum() for s in range(4)]),'ic':float(np.corrcoef(z[:,style],y)[0,1]),
            'rank_ic':float(np.corrcoef(rankdata(z[:,style]),rankdata(y))[0,1]),'fit':fit}

def serializable(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,dict):return {k:serializable(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [serializable(v) for v in x]
    if isinstance(x,(np.integer,np.floating)):return x.item()
    return x
if __name__=='__main__':
    d=dataset();a=analyze(d);capm=analyze(d,model='capm');cs=cross_section(d)
    result={'dataset':d,'style':a,'capm':capm,'cross':cs}
    (ROOT/'computed.json').write_text(json.dumps(serializable(result),indent=2),encoding='utf-8')
    print(json.dumps(serializable({'style':{k:a[k] for k in ['b','hac_se','r2','rmse','system','specific','volatility']},
                                 'capm':{k:capm[k] for k in ['b','r2','rmse']},'cross':{k:cs[k] for k in ['gross','net','ic','rank_ic','exposure','sector_net']}}),indent=2))
