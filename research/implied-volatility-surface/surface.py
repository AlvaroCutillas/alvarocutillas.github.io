"""Synthetic European vanilla surface; decimal volatilities and year fractions."""
import numpy as np
from scipy.special import ndtr
from scipy.optimize import brentq, least_squares
DEFAULT=dict(short=.24,long=.18,decay=1.2,rho=-.65,eta=2.3)
def theta(T,p=DEFAULT):
    return p['long']**2*T+(p['short']**2-p['long']**2)*p['decay']*(-np.expm1(-np.asarray(T)/p['decay']))
def theta_prime(T,p=DEFAULT):
    return p['long']**2+(p['short']**2-p['long']**2)*np.exp(-np.asarray(T)/p['decay'])
def ssvi(k,T,p=DEFAULT):
    th=theta(T,p);ph=p['eta']/(1+th);u=ph*np.asarray(k)+p['rho'];z=np.sqrt(u*u+1-p['rho']**2)
    w=.5*th*(1+p['rho']*ph*k+z)
    wk=.5*th*ph*(p['rho']+u/z)
    wkk=.5*th*ph*ph*(1-p['rho']**2)/z**3
    wth=.5*(1+p['rho']*ph*k+z)-.5*th*p['eta']/(1+th)**2*k*(p['rho']+u/z)
    wt=wth*theta_prime(T,p)
    g=(1-k*wk/(2*w))**2-wk**2/4*(1/w+.25)+wkk/2
    return dict(w=w,sigma=np.sqrt(w/T),wk=wk,wkk=wkk,wt=wt,g=g,local=np.where(g>0,np.sqrt(np.maximum(wt/g,0)),np.nan))
def black(F,K,D,T,sigma,put=False):
    F,K=np.broadcast_arrays(F,K);w=np.asarray(sigma)**2*T
    root=np.sqrt(np.maximum(w,1e-300));d1=np.log(F/K)/root+root/2;d2=d1-root
    call=D*(F*ndtr(d1)-K*ndtr(d2))
    price=call-D*(F-K) if put else call
    return np.where(w<=0,D*np.maximum(K-F if put else F-K,0),price)
def vega(F,K,D,T,sigma):
    d1=np.log(F/K)/(sigma*np.sqrt(T))+.5*sigma*np.sqrt(T)
    return D*F*np.exp(-d1*d1/2)/np.sqrt(2*np.pi)*np.sqrt(T)
def implied(price,F,K,D,T,put=False):
    low=D*max(K-F if put else F-K,0);high=D*(K if put else F)
    if T<=0 or min(F,K,D)<=0 or not low<=price<high:raise ValueError('Quote outside finite-IV domain')
    if price==low:return 0.
    top=.5
    while black(F,K,D,T,top,put)<price and top<16:top*=2
    return float(brentq(lambda s:float(black(F,K,D,T,s,put))-price,1e-12,top,xtol=1e-13))
def density(K,T,F,p=DEFAULT):
    k=np.log(np.asarray(K)/F);s=ssvi(k,T,p);d2=-k/np.sqrt(s['w'])-.5*np.sqrt(s['w'])
    return np.exp(-d2*d2/2)/np.sqrt(2*np.pi)*s['g']/(K*np.sqrt(s['w']))
def svi(k,params):
    a,b,rho,m,s=params;x=np.asarray(k)-m;z=np.sqrt(x*x+s*s)
    return a+b*(rho*x+z)
def svi_g(k,params):
    a,b,rho,m,s=params;x=np.asarray(k)-m;z=np.sqrt(x*x+s*s);w=svi(k,params)
    wk=b*(rho+x/z);wkk=b*s*s/z**3
    return (1-k*wk/(2*w))**2-wk**2/4*(1/w+.25)+wkk/2
def calibration():
    T=1.;k=np.linspace(-.4,.4,17);true=ssvi(k,T)['sigma']
    observed=true+.0007*np.sin(np.arange(len(k))*9)+.0003*np.cos(np.arange(len(k))*5)
    train=np.arange(len(k))%4!=2
    fits=[]
    for m0 in [-.15,0,.15,.3]:
        fit=least_squares(lambda p:(svi(k[train],p)-observed[train]**2*T),[.025,.035,-.4,m0,.35],
                          bounds=([1e-6,1e-6,-.98,-1,.015],[.25,1,.98,1,2]),xtol=1e-13,ftol=1e-13,gtol=1e-13,max_nfev=5000)
        fits.append(fit)
    fit=min(fits,key=lambda f:np.sum(f.fun*f.fun));params=fit.x
    pred=np.sqrt(svi(k,params)/T)
    return dict(T=T,k=k,observed=observed,true=true,train=train,params=params,pred=pred,
                train_rmse=float(np.sqrt(np.mean((pred[train]-observed[train])**2))),
                holdout_rmse=float(np.sqrt(np.mean((pred[~train]-observed[~train])**2))),
                min_g=float(svi_g(np.linspace(-5,5,10001),params).min()))
def bounds(p=DEFAULT,H=3):
    th=float(theta(H,p));factor=1+abs(p['rho']);q=min(th,1)
    return dict(horizon_wing=p['eta']*th/(1+th)*factor,horizon_curvature=p['eta']**2*q/(1+q)**2*factor,
                global_wing=p['eta']*factor,global_curvature=p['eta']**2*factor/4)
