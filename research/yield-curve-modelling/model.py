"""Synthetic term-structure examples. Rates are decimals, times exact years."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares, brentq

ROOT = Path(__file__).parent
REFERENCE = np.array([.035, -.020, .025, -.015, 1.6, 6.5])
MATURITIES = np.array([.25,.5,.75,1,1.5,2,3,4,5,7,10,12,15,20,25,30])

def loadings(T, tau):
    x = np.asarray(T, dtype=float)/tau
    small = np.abs(x)<1e-5
    safe = np.where(small, 1., x)
    a = -np.expm1(-x)/safe
    a = np.where(small, 1-x/2+x*x/6-x**3/24+x**4/120, a)
    b = a-np.exp(-x)
    return a,b

def design(T, tau, model='nss'):
    a,b=loadings(T,tau[0])
    cols=[np.ones_like(a),a,b]
    if model=='nss': cols.append(loadings(T,tau[1])[1])
    return np.column_stack(cols)

def curve(T, p=REFERENCE, model='nss'):
    T=np.asarray(T,dtype=float)
    a,b=loadings(T,p[4]); x=T/p[4]
    z=p[0]+p[1]*a+p[2]*b
    f=p[0]+p[1]*np.exp(-x)+p[2]*x*np.exp(-x)
    if model=='nss':
        a2,b2=loadings(T,p[5]); x2=T/p[5]
        z=z+p[3]*b2; f=f+p[3]*x2*np.exp(-x2)
    return z,f,np.exp(-T*z)

def par(T,p=REFERENCE,m=2,model='nss'):
    ts=np.arange(1,round(T*m)+1)/m
    ds=curve(ts,p,model)[2]
    return m*(1-ds[-1])/np.sum(ds)

def bond(p=REFERENCE,T=5,c=.04,m=2,N=100,shock=0,model='nss'):
    assert abs(T*m-round(T*m))<1e-9
    t=np.arange(1,round(T*m)+1)/m
    cf=np.full(len(t),N*c/m); cf[-1]+=N
    d=curve(t,p,model)[2]*np.exp(-shock*t); pv=cf*d
    P=np.sum(pv); dur=np.sum(t*pv)/P; conv=np.sum(t*t*pv)/P
    def price(y): return np.sum(cf/(1+y/m)**np.arange(1,len(t)+1))
    y=brentq(lambda y:price(y)-P,-.9*m,2)
    return {'price':float(P),'ytm':float(y),'duration':float(dur),'convexity':float(conv),
            'dv01':float(.0001*P*dur),'t':t.tolist(),'cf':cf.tolist(),'d':d.tolist(),'pv':pv.tolist()}

def quotes():
    z=curve(MATURITIES)[0]
    i=np.arange(len(z))
    y=z+.00012*np.sin(7*i)+.00004*np.cos(3*i)
    train=i%5!=2
    return MATURITIES,y,train

def fit(model='nss'):
    t,y,train=quotes(); n=1 if model=='ns' else 2
    lo=np.log([.15] if n==1 else [.15,.25])
    hi=np.log([10.] if n==1 else [10.,30.])
    def solve(logtau):
        X=design(t[train],np.exp(logtau),model)
        b=np.linalg.lstsq(X,y[train],rcond=1e-12)[0]
        return X@b-y[train],b
    starts=[np.log([a]) for a in [.3,1,3,8]] if n==1 else [np.log([a,b]) for a in [.4,1.5,4,8] for b in [1,4,10,25]]
    fits=[least_squares(lambda x:solve(x)[0],s,bounds=(lo,hi),ftol=1e-13,xtol=1e-13,gtol=1e-13,max_nfev=700) for s in starts]
    best=min(fits,key=lambda r:np.sum(r.fun**2))
    residual,b=solve(best.x); tau=np.exp(best.x)
    p=np.array([b[0],b[1],b[2],b[3] if n==2 else 0,tau[0],tau[1] if n==2 else 6.5])
    pred=curve(t,p,model)[0]
    return {'model':model,'params':p.tolist(),'train_rmse_bps':float(np.sqrt(np.mean((pred[train]-y[train])**2))*1e4),
            'holdout_rmse_bps':float(np.sqrt(np.mean((pred[~train]-y[~train])**2))*1e4),
            'condition':float(np.linalg.cond(design(t[train],tau,model))),
            't':t.tolist(),'observed':y.tolist(),'train':train.tolist(),'pred':pred.tolist()}

def compute():
    ts=np.array([.5,1,2,5,10,20,30])
    z,f,d=curve(ts)
    rows=[{'T':float(T),'zero':float(Z),'forward':float(F),'discount':float(D),'par':float(par(T))} for T,Z,F,D in zip(ts,z,f,d)]
    b=bond(); shocked=bond(shock=.01)
    b['shocked_price']=shocked['price']; b['linear']=b['price']*(1-b['duration']*.01)
    b['quadratic']=b['price']*(1-b['duration']*.01+.5*b['convexity']*.01**2)
    zboot=np.array([.02,.025,.03]); ds=np.exp(-np.arange(1,4)*zboot)
    pars=[(1-ds[j])/sum(ds[:j+1]) for j in range(3)]
    bootstrap=[{'T':j+1,'par':float(pars[j]),'discount':float(ds[j]),'zero':float(zboot[j])} for j in range(3)]
    return {'reference':REFERENCE.tolist(),'rows':rows,'bond':b,'bootstrap':bootstrap,'ns_fit':fit('ns'),'nss_fit':fit('nss')}

if __name__=='__main__':
    data=compute()
    (ROOT/'computed.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({k:data[k] for k in ['reference','rows','bond']},indent=2))
