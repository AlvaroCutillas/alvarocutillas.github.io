from pathlib import Path
import sys,json
import numpy as np
from scipy.special import ndtr
from scipy.optimize import brentq
from bs4 import BeautifulSoup
from surface import *
ROOT=Path(__file__).parent
rng=np.random.default_rng(6106);cases=[]
def direct_w(k,T,p):
    th=p['long']**2*T+(p['short']**2-p['long']**2)*p['decay']*(1-np.exp(-T/p['decay']))
    ph=p['eta']/(1+th)
    return th/2*(1+p['rho']*ph*k+np.sqrt((ph*k+p['rho'])**2+1-p['rho']**2))
derivative_error=0
for i in range(80):
    p={**DEFAULT,'short':rng.uniform(.1,.5),'long':rng.uniform(.1,.5),'rho':rng.uniform(-.9,.9),'eta':rng.uniform(0,7),'decay':rng.uniform(.3,3)}
    k=rng.uniform(-.7,.7);T=rng.uniform(.2,5);s=ssvi(k,T,p);hk=1e-4;ht=1e-5
    wk=(direct_w(k+hk,T,p)-direct_w(k-hk,T,p))/(2*hk)
    wkk=(direct_w(k+hk,T,p)-2*direct_w(k,T,p)+direct_w(k-hk,T,p))/hk**2
    wt=(direct_w(k,T+ht,p)-direct_w(k,T-ht,p))/(2*ht)
    assert abs(wk-s['wk'])<2e-7
    assert abs(wkk-s['wkk'])<3e-6
    assert abs(wt-s['wt'])<1e-8
    derivative_error=max(derivative_error,abs(wkk-s['wkk']))
    cases.append(dict(p=p,k=float(k),T=float(T),expected={key:float(s[key]) if s[key] is not None and np.isfinite(s[key]) else None for key in ['w','wk','wkk','wt','g','sigma','local']}))
price_cases=[]
for i in range(120):
    F=rng.uniform(20,250);K=F*np.exp(rng.uniform(-.4,.4));D=np.exp(rng.uniform(-.15,.05));T=rng.uniform(.15,4);sig=rng.uniform(.15,.8);put=i%2==1
    root=sig*np.sqrt(T);d1=np.log(F/K)/root+root/2;d2=d1-root
    c=D*(F*ndtr(d1)-K*ndtr(d2));price=float(c-D*(F-K) if put else c)
    assert abs(float(black(F,K,D,T,sig,put))-price)<1e-10
    recovered=implied(price,F,K,D,T,put)
    assert abs(recovered-sig)<1e-8
    price_cases.append(dict(F=F,K=K,D=D,T=T,sigma=sig,put=put,price=price,vega=float(vega(F,K,D,T,sig))))
dupire_error=0
for T in [.25,.5,1,2,3]:
    for k in [-.3,0,.3]:
        r=.03;q=.01;spot=100;F=spot*np.exp((r-q)*T);D=np.exp(-r*T);K=F*np.exp(k)
        def call(K,T):
            f=spot*np.exp((r-q)*T);d=np.exp(-r*T)
            return float(black(f,K,d,T,np.sqrt(direct_w(np.log(K/f),T,DEFAULT)/T)))
        hK=.01;hT=1e-4
        c0=call(K,T);ck=(call(K+hK,T)-call(K-hK,T))/(2*hK)
        ckk=(call(K+hK,T)-2*c0+call(K-hK,T))/hK**2
        ct=(call(K,T+hT)-call(K,T-hT))/(2*hT)
        local2=(ct+q*c0+(r-q)*K*ck)/(.5*K*K*ckk)
        expected=float(ssvi(k,T)['local'])**2
        err=abs(local2-expected)/expected;dupire_error=max(dupire_error,err);assert err<2e-5
        assert abs(ckk/D-float(density(K,T,F)))<1e-7
for T in [.05,.25,1,3,10]:
    th=theta(T);ph=DEFAULT['eta']/(1+th);rho=DEFAULT['rho']
    raw=[th*(1-rho*rho)/2,th*ph/2,rho,-rho/ph,np.sqrt(1-rho*rho)/ph]
    assert np.max(np.abs(svi(np.linspace(-3,3,301),raw)-ssvi(np.linspace(-3,3,301),T)['w']))<1e-14
assert float(ssvi(np.linspace(-3,3,4001),3,{**DEFAULT,'eta':12})['g'].min())<0
assert np.all(ssvi(np.linspace(-5,5,10001),3)['g']>0)
computed=json.loads((ROOT/'computed.json').read_text(encoding='utf-8'))
assert abs(computed['density_mass']-1)<1e-8
assert abs(computed['density_mean']-100*np.exp(.02))<1e-6
page=ROOT.parent.parent/'projects/implied-volatility-surface.html'
code=BeautifulSoup(page.read_text(encoding='utf-8'),'html.parser').find('pre').get_text()
exec(compile(code,'embedded-reference','exec'),{})
(ROOT/'reference-cases.json').write_text(json.dumps({'surface':cases,'prices':price_cases,'cdf':[[float(x),float(ndtr(x))] for x in np.linspace(-12,12,241)]},allow_nan=False),encoding='utf-8')
report=dict(surfaceDerivativeCases=len(cases),priceInversionCases=len(price_cases),maxSecondDerivativeAbsoluteError=derivative_error,maxIndependentDupireRelativeError=dupire_error,rawSVIEquivalence='passed',densityMoments='passed',invalidShapeDetection='passed',embeddedPython='passed')
(ROOT/'reference-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
