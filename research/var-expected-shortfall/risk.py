import numpy as np
from scipy.stats import norm, t, chi2
from scipy.special import xlogy

def empirical(loss, alpha, weights=None):
    """Inverse empirical CDF and exact fractional-tail ES, including atoms."""
    loss=np.asarray(loss,dtype=float)
    if not 0<alpha<1 or len(loss)==0 or not np.isfinite(loss).all():
        raise ValueError('Finite observations and 0 < alpha < 1 required')
    w=np.ones(len(loss))/len(loss) if weights is None else np.asarray(weights,dtype=float)
    if len(w)!=len(loss) or np.any(w<0) or not np.isfinite(w).all() or w.sum()<=0:
        raise ValueError('Invalid weights')
    active=w>0; loss=loss[active]; w=w[active]/w[active].sum()
    idx=np.argsort(loss); loss=loss[idx]; w=w[idx]
    cdf=np.cumsum(w); cdf[-1]=1.
    q=loss[min(np.searchsorted(cdf,alpha-1e-14,side='left'),len(loss)-1)]
    es=q+np.dot(w,np.maximum(loss-q,0))/(1-alpha)
    return float(q),float(es)

def normal_risk(alpha, mean=0., sd=1.):
    z=norm.ppf(alpha)
    return mean+sd*z,mean+sd*norm.pdf(z)/(1-alpha)

def student_risk(alpha, nu=5, mean=0., sd=1.):
    if nu<=2: raise ValueError('Finite-variance scale requires nu > 2')
    a=sd*np.sqrt((nu-2)/nu); q=t.ppf(alpha,nu)
    return mean+a*q,mean+a*(nu+q*q)/(nu-1)*t.pdf(q,nu)/(1-alpha)

def coverage(n,k,p):
    phat=k/n
    ll0=xlogy(k,p)+xlogy(n-k,1-p)
    ll1=xlogy(k,phat)+xlogy(n-k,1-phat)
    lr=2*(ll1-ll0)
    return float(lr),float(chi2.sf(lr,1))

def independence(hits):
    h=np.asarray(hits,dtype=int); counts=np.zeros((2,2),dtype=int)
    for a,b in zip(h[:-1],h[1:]): counts[a,b]+=1
    totals=counts.sum(axis=1)
    if np.any(totals==0): return counts.tolist(),None,None
    probs=counts[:,1]/totals; pooled=counts[:,1].sum()/counts.sum()
    alt=sum(xlogy(counts[i,1],probs[i])+xlogy(counts[i,0],1-probs[i]) for i in [0,1])
    null=xlogy(counts[:,1].sum(),pooled)+xlogy(counts[:,0].sum(),1-pooled)
    lr=2*(alt-null)
    return counts.tolist(),float(lr),float(chi2.sf(lr,1))
