import json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from portfolio import MU,COV,unrestricted,long_only,moments,tangency
ROOT=Path(__file__).parent
rng=np.random.default_rng(3099)
cases=[]
for i in range(14):
    B=rng.normal(size=(3,3));S=B@B.T+np.eye(3)*2
    rho=S/np.sqrt(np.diag(S))[:,None]/np.sqrt(np.diag(S))[None,:]
    vol=rng.uniform(.08,.3,3);cov=vol[:,None]*rho*vol[None,:];mu=rng.uniform(.01,.2,3)
    target=float(np.min(mu)+rng.uniform(.05,.95)*np.ptp(mu))
    constrained=bool(i%2)
    if constrained:
        constraints=[{'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones(3)},
                     {'type':'eq','fun':lambda w:mu@w-target,'jac':lambda w:mu}]
        ans=minimize(lambda w:.5*w@cov@w,np.ones(3)/3,jac=lambda w:cov@w,
                     constraints=constraints,bounds=[(0,1)]*3,
                     method='SLSQP',options={'ftol':1e-14,'maxiter':2000})
        assert ans.success,ans.message
        expected=ans.x
        own=long_only(mu,cov,target);assert np.max(abs(expected-own))<3e-6
    else:
        F=np.vstack([np.ones(3),mu])
        K=np.block([[cov,F.T],[F,np.zeros((2,2))]])
        expected=np.linalg.solve(K,np.r_[np.zeros(3),1,target])[:3]
        own=unrestricted(mu,cov,target);assert np.max(abs(expected-own))<1e-9
    cases.append({'mu':mu.tolist(),'vol':vol.tolist(),'rho':[float(rho[0,1]),float(rho[0,2]),float(rho[1,2])],
                  'target':target,'mode':'longonly' if constrained else 'unrestricted','weights':expected.tolist(),
                  'return':float(mu@expected),'volatility':float(np.sqrt(expected@cov@expected))})
# Analytical identity, KKT residual and constraint comparison over a broad target range.
for target in np.linspace(.06,.14,33):
    u=unrestricted(target=target);l=long_only(target=target)
    assert abs(u.sum()-1)<1e-10 and abs(u@MU-target)<1e-10
    assert u@COV@u<=l@COV@l+1e-10
for mode in [False,True]:
    w=tangency(longonly=mode)
    assert w is not None and abs(w.sum()-1)<1e-12
    # Cauchy-Schwarz bound is attained for this positive-budget benchmark.
    e=MU-.02;assert abs((w@e)**2/(w@COV@w)-e@np.linalg.solve(COV,e))<1e-12
for c in [.4,.6,1]:
    g=long_only(cap=c);assert g.min()>-1e-8 and g.max()<=c+1e-8
invalid=np.array([[1,.9,.9],[.9,1,-.9],[.9,-.9,1]])
assert np.linalg.det(invalid)<0
(ROOT/'reference-cases.json').write_text(json.dumps(cases),encoding='utf-8')
print(json.dumps({'independent_reference_cases':len(cases),'qp':'SLSQP versus active-face enumeration','analytical_identity':'passed','constraint_ordering':'passed','tangency_bound':'passed'}))
