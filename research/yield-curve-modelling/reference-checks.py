from pathlib import Path
import json, math
import numpy as np
from scipy.integrate import quad
from model import curve,loadings,bond,par,REFERENCE,compute
ROOT=Path(__file__).parent
cases=[]
params=[REFERENCE.tolist(),[.005,-.02,.008,0,2,6.5],[.04,0,0,0,1,10],[.025,-.035,.01,.03,.18,22]]
for model in ['ns','nss']:
    for p in params:
        for T in [0,1e-12,1e-7,.25,1,5,15,30]:
            z,f,d=curve(T,p,model)
            cases.append({'model':model,'p':p,'T':T,'z':float(z),'f':float(f),'d':float(d)})
            if T>1e-7:
                integral=quad(lambda u:float(curve(u,p,model)[1]),0,T,epsabs=1e-12)[0]
                assert abs(integral-T*z)<2e-11
        for T,c,m,N in [(5,.04,2,100),(1,0,4,100),(7,.07,1,500),(30,.03,2,100)]:
            b=bond(p,T,c,m,N,model=model);h=1e-4
            plus=bond(p,T,c,m,N,shock=h,model=model)['price'];minus=bond(p,T,c,m,N,shock=-h,model=model)['price']
            fd=-(plus-minus)/(2*h*b['price']);fc=(plus-2*b['price']+minus)/(h*h*b['price'])
            assert abs(fd-b['duration'])<5e-5
            assert abs(fc-b['convexity'])<.002
            cases.append({'model':model,'p':p,'bond':{'T':T,'c':c,'m':m,'N':N},'result':b,'par':par(T,p,m,model)})
data=compute()
for i,r in enumerate(data['bootstrap']):
    prior=sum(x['discount'] for x in data['bootstrap'][:i])
    recovered=(1-r['par']*prior)/(1+r['par'])
    assert abs(recovered-r['discount'])<1e-14
assert abs(data['bond']['price']-103.66010584851593)<1e-10
(ROOT/'reference-cases.json').write_text(json.dumps(cases),encoding='utf-8')
print(len(cases),'independent Python reference cases; forward integration, duration, convexity and bootstrap checks passed')
