import itertools
import numpy as np
MU=np.array([.06,.10,.14])
VOL=np.array([.10,.18,.28])
CORR=np.array([[1,.2,.1],[.2,1,.35],[.1,.35,1]])
COV=VOL[:,None]*CORR*VOL[None,:]
RF=.02

def moments(w,mu=MU,cov=COV):
    w=np.asarray(w)
    return {'return':float(w@mu),'variance':float(w@cov@w),
            'volatility':float(np.sqrt(max(w@cov@w,0))),
            'weights':w.tolist(),'gross':float(abs(w).sum())}

def unrestricted(mu=MU,cov=COV,target=None):
    one=np.ones(len(mu));u=np.linalg.solve(cov,one);v=np.linalg.solve(cov,mu)
    A=one@u;B=one@v;C=mu@v;D=A*C-B*B
    if target is None:return u/A
    if D<=1e-12*A*C:
        if abs(target-B/A)>1e-10:raise ValueError('Equal expected returns: target infeasible')
        return u/A
    return u*(C-B*target)/D+v*(A*target-B)/D

def long_only(mu=MU,cov=COV,target=None,cap=1):
    # Enumerate active lower/upper bounds; free coordinates solve the equality KKT system.
    n=len(mu);best=None
    for status in itertools.product([0,1,2],repeat=n): # 0 lower, 1 free, 2 upper
        free=np.flatnonzero(np.array(status)==1);fixed=np.flatnonzero(np.array(status)!=1)
        w=np.array([cap if s==2 else 0. for s in status])
        b=np.array([1-w.sum()] if target is None else [1-w.sum(),target-w@mu])
        if len(free):
            H=cov[np.ix_(free,free)];g=cov[np.ix_(free,fixed)]@w[fixed]
            F=np.ones((1,len(free))) if target is None else np.vstack([np.ones(len(free)),mu[free]])
            K=np.block([[H,F.T],[F,np.zeros((len(b),len(b)))]])
            rhs=np.concatenate([-g,b]);sol=np.linalg.lstsq(K,rhs,rcond=None)[0]
            if np.max(abs(K@sol-rhs))>1e-9:continue
            w[free]=sol[:len(free)]
        elif np.max(abs(b))>1e-9:continue
        if np.min(w)<-1e-8 or np.max(w)>cap+1e-8:continue
        variance=w@cov@w
        if best is None or variance<best[0]:best=(variance,w)
    if best is None:raise ValueError('Target not attainable under these bounds')
    return best[1]

def tangency(mu=MU,cov=COV,rf=RF,longonly=False):
    excess=mu-rf
    if not longonly:
        v=np.linalg.solve(cov,excess)
        if v.sum()<=1e-12:return None
        return v/v.sum()
    best=None
    for mask in range(1,2**len(mu)):
        ix=np.array([i for i in range(len(mu)) if mask>>i&1]);v=np.linalg.solve(cov[np.ix_(ix,ix)],excess[ix])
        if v.sum()<=0:continue
        a=v/v.sum()
        if a.min()<-1e-10:continue
        w=np.zeros(len(mu));w[ix]=a;m=moments(w,mu,cov);s=(m['return']-rf)/m['volatility']
        if s>0 and (best is None or s>best[0]):best=(s,w)
    return None if best is None else best[1]
