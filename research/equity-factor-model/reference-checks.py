from pathlib import Path
import json
import numpy as np
from model import dataset,analyze,cross_section,serializable,TRUTH,COV
ROOT=Path(__file__).parent
d=dataset();cases=[]
for model in ['style','capm']:
    for train in [60,180,228]:
        for lags in [0,6,12]:
            for noise in [.005,.02]:
                beta=TRUTH*np.array([1,-1,2,.5,-.7])
                a=analyze(d,beta=beta,alpha=-.003,noise=noise,train=train,lags=lags,model=model)
                assert np.allclose(a['variance'],np.var(a['y'][:train],ddof=1),rtol=1e-12,atol=1e-15)
                assert abs(sum(a['contributions'])-a['variance'])<1e-15
                cases.append({'o':dict(zip(['market','value','momentum','quality','lowvol'],beta))|{'alpha':-30,'noise':noise*100,'train':train,'lags':lags,'model':model},'result':a})
sorts=[]
for signal in range(4):
    for tail in [10,20,30]:
        for balanced in [False,True]:
            c=cross_section(d,style=signal,tail=tail,balanced=balanced,cost=37)
            w=c['weights']
            assert np.allclose([w[w>0].sum(),w[w<0].sum(),sum(abs(w))],[1,-1,2],atol=1e-13)
            assert abs(c['gross']-c['net']-.0074)<1e-13
            if balanced:assert np.allclose(c['sector_net'],0,atol=1e-13)
            sorts.append({'o':{'signal':signal,'tail':tail,'neutral':'balanced' if balanced else 'unrestricted','cost':37},'result':c})
perfect=analyze(d,noise=0)
assert np.allclose(perfect['b'],np.r_[.0004,TRUTH],atol=1e-13)
assert perfect['rmse']<1e-13
assert np.linalg.eigvalsh(COV).min()>0
z=np.array([s['z'] for s in d['stocks']])
assert np.allclose(z.mean(axis=0),0,atol=1e-14)
assert np.allclose(z.var(axis=0),1,atol=1e-14)
(ROOT/'reference-cases.json').write_text(json.dumps(serializable({'attribution':cases,'sorts':sorts}),separators=(',',':')),encoding='utf-8')
print(f'{len(cases)} SVD/HAC reference cases, {len(sorts)} stock sorts, variance identities, exact recovery and normalization passed.')
