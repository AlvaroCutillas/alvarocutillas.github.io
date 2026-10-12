from pathlib import Path
import json
import numpy as np
from scipy.stats import norm,t
from scipy.integrate import quad
from scipy.optimize import linprog
from risk import empirical,normal_risk,student_risk
root=Path(__file__).parent
cases=[]
for nu in [2.05,2.5,3,5,10,30,100]:
    for alpha in [.8,.95,.99,.999,.9999]:
        q=t.ppf(alpha,nu);es=quad(lambda x:x*t.pdf(x,nu),q,np.inf,epsabs=1e-9)[0]/(1-alpha)
        scale=np.sqrt((nu-2)/nu);v,e=student_risk(alpha,nu)
        assert abs(v-scale*q)<1e-10
        assert abs(e-scale*es)<max(1e-7,abs(e)*1e-8)
        cases.append({'distribution':'student','nu':nu,'alpha':alpha,'mean':0.,'sd':10000.,'reference':[10000*v,10000*e]})
for a in [.8,.9,.95,.975,.99,.999,.9999]:
    v,e=normal_risk(a,-500,10000)
    cases.append({'distribution':'normal','nu':5,'alpha':a,'mean':-500,'sd':10000,'reference':[v,e]})
assert np.allclose(empirical([0,10,100],.95,[.94,.04,.02]),(10.,46.))
assert np.allclose(empirical(range(10),.85),(8,26/3))
assert empirical([5]*10,.99)==(5.,5.)
assert empirical([-10,-5],.95)==(-5.,-5.)
assert np.allclose(empirical([0,100],.95,[.96,.04]),(0.,80.))
assert np.allclose(empirical([0,100,200],.95,[.9216,.0768,.0016]),[100,103.2])
# Check the auxiliary representation through an independent linear program.
loss=np.array([0.,10.,100.]);prob=np.array([.94,.04,.02])
c=np.r_[1,prob/.05]
A=np.column_stack([-np.ones(3),-np.eye(3)])
lp=linprog(c,A_ub=A,b_ub=-loss,bounds=[(None,None)]+[(0,None)]*3,method='highs')
assert lp.success and abs(lp.fun-46)<1e-10 and abs(lp.x[0]-10)<1e-10
print('Student ES integration:',35,'cases; empirical boundary/atom tests and independent CVaR LP passed')
print('Exercise 1:',normal_risk(.99,-800,24000))
print('Exercise 6:',1000+np.sqrt(10)*1000*norm.ppf(.99),np.sqrt(10)*(100+1000*norm.ppf(.99)))
q=2+3.2*(5**.25-1);es=q+(.8+.25*(q-2))/.75
print('Exercise 8:',q,es)
(root/'reference-cases.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
