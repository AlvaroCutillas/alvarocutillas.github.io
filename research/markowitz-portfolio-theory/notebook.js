(() => {
 'use strict';
 const $=id=>document.getElementById(id),form=$('portfolio-form'),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
 const mv=(A,v)=>A.map(row=>dot(row,v));
 const fmt=(x,n=4)=>x===null||!Number.isFinite(x)?'—':(Math.abs(x)<1e-10?0:x).toLocaleString('en-US',{minimumFractionDigits:n,maximumFractionDigits:n});
 const pct=x=>x===null?'—':fmt(x*100)+'%';
 function solve(A,b){
  const n=b.length,M=A.map((row,i)=>[...row,b[i]]);
  const scale=Math.max(...A.flat().map(Math.abs));
  for(let k=0;k<n;k++){
   let j=k;for(let i=k+1;i<n;i++)if(Math.abs(M[i][k])>Math.abs(M[j][k]))j=i;
   if(Math.abs(M[j][k])<1e-13*scale)throw Error('The moment system is numerically singular. Use better-separated means or a better-conditioned covariance.');
   [M[k],M[j]]=[M[j],M[k]];
   const p=M[k][k];for(let t=k;t<=n;t++)M[k][t]/=p;
   for(let i=0;i<n;i++)if(i!==k){const f=M[i][k];for(let t=k;t<=n;t++)M[i][t]-=f*M[k][t];}
  }
  return M.map(row=>row[n]);
 }
 function validateCorrelation(R){
  const L=R.map(()=>[0,0,0]);
  for(let i=0;i<3;i++)for(let j=0;j<=i;j++){
   let a=R[i][j];for(let k=0;k<j;k++)a-=L[i][k]*L[j][k];
   if(i===j){if(a<1e-6)throw Error('These correlations do not form a sufficiently positive-definite matrix. Pairwise bounds alone are insufficient; reduce incompatible or nearly perfect correlations.');L[i][j]=Math.sqrt(a);}
   else L[i][j]=a/L[j][j];
  }
 }
 function minvar(mu,S,target=null){
  const one=mu.map(()=>1),u=solve(S,one),A=dot(one,u),g=u.map(x=>x/A);
  if(target===null)return g;
  if(Math.max(...mu)-Math.min(...mu)<1e-10)return Math.abs(target-mu[0])<1e-9?g:null;
  const v=solve(S,mu),B=dot(one,v),C=dot(mu,v),D=A*C-B*B;
  if(D<1e-12*Math.max(A*C,1e-10))throw Error('The expected returns are too close for a stable target-frontier calculation.');
  return u.map((x,i)=>(x*(C-B*target)+v[i]*(A*target-B))/D);
 }
 function faces(mu,S,objective,target=null,rf=0){
  let best=null;
  for(let mask=1;mask<8;mask++){
   const ix=[0,1,2].filter(i=>mask>>i&1),m=ix.map(i=>mu[i]),C=ix.map(i=>ix.map(j=>S[i][j]));
   let a;
   if(objective==='tangency'){
    const z=solve(C,m.map(x=>x-rf)),sum=z.reduce((s,x)=>s+x,0);
    if(sum<=1e-12)continue;a=z.map(x=>x/sum);
   }else a=minvar(m,C,target);
   if(!a||Math.min(...a)<-1e-8)continue;
   const w=[0,0,0];ix.forEach((k,i)=>w[k]=a[i]);const p=moments(w,mu,S);
   const score=objective==='tangency'?(p.mean-rf)/p.vol:-p.variance;
   if(objective==='tangency'&&score<=0)continue;
   if(!best||score>best.score)best={score,w};
  }
  return best?.w||null;
 }
 function moments(w,mu,S){
  if(!w)return null;const variance=dot(w,mv(S,w)),mean=dot(w,mu);
  return {w,mean,variance,vol:Math.sqrt(Math.max(variance,0)),gross:w.reduce((s,x)=>s+Math.abs(x),0)};
 }
 function compute(p){
  const {mu,S,rf}=p,limited=p.mode==='longonly',get=t=>limited?faces(mu,S,'variance',t):minvar(mu,S,t);
  const g=moments(get(null),mu,S),target=moments(get(p.target),mu,S);
  let tw=null;
  if(limited)tw=faces(mu,S,'tangency',null,rf);
  else if(rf<g.mean-1e-10){const z=solve(S,mu.map(x=>x-rf)),sum=z.reduce((s,x)=>s+x,0);tw=z.map(x=>x/sum);}
  const tan=moments(tw,mu,S),spread=Math.max(...mu)-Math.min(...mu),flat=spread<1e-10;
  const lower=limited?Math.min(...mu):Math.min(...mu)-spread*.5,upper=limited?Math.max(...mu):Math.max(...mu)+spread*.5;
  const curve=(start,end)=>Array.from({length:101},(_,i)=>get(start+(end-start)*i/100)).filter(Boolean).map(w=>moments(w,mu,S));
  return {g,target,tan,flat,low:flat?[]:curve(lower,g.mean),high:flat?[]:curve(g.mean,upper)};
 }
 function plot(p,res){
  window.ChartCoordinates?.hide();
  const W=800,H=410,L=66,R=27,T=35,B=58;
  const all=[...res.low,...res.high,res.g,res.target,res.tan].filter(Boolean);
  let xmax=Math.max(...all.map(a=>a.vol),...p.vol)*1.08,xmin=0;
  let ymax=Math.max(...all.map(a=>a.mean),...p.mu,p.rf),ymin=Math.min(...all.map(a=>a.mean),...p.mu,p.rf);
  const pad=Math.max((ymax-ymin)*.1,.005);ymax+=pad;ymin-=pad;
  const X=x=>L+(x-xmin)/(xmax-xmin)*(W-L-R),Y=y=>H-B-(y-ymin)/(ymax-ymin)*(H-T-B);
  let grid='',labels='';
  for(let i=0;i<=4;i++){
   const x=xmax*i/4,y=ymin+(ymax-ymin)*i/4;
   grid+='<path d="M'+X(x)+' '+T+'V'+(H-B)+' M'+L+' '+Y(y)+'H'+(W-R)+'" stroke="#242925" fill="none"/>';
   labels+='<text x="'+X(x)+'" y="'+(H-B+23)+'" text-anchor="middle">'+fmt(x*100,1)+'%</text><text x="'+(L-10)+'" y="'+(Y(y)+4)+'" text-anchor="end">'+fmt(y*100,1)+'%</text>';
  }
  const series=[],path=a=>a.map((v,i)=>(i?'L':'M')+X(v.vol).toFixed(3)+','+Y(v.mean).toFixed(3)).join(' ');
  let curves='';
  for(const [a,color,label] of [[res.low,'#7e8d86','Lower minimum-variance boundary'],[res.high,'#a7bdb3','Efficient frontier']]){
   if(a.length<2)continue;
   curves+='<path d="'+path(a)+'" stroke="'+color+'" fill="none" stroke-width="2"/>';
   const points=a.map(v=>[v.vol*100,v.mean*100,X(v.vol),Y(v.mean)]).sort((a,b)=>a[2]-b[2]);
   series.push({label,color,mode:'line',points});
  }
  if(res.tan){
   const slope=(res.tan.mean-p.rf)/res.tan.vol,limit=Math.min(xmax,(ymax-p.rf)/slope);
   if(limit>0){curves+='<path d="M'+X(0)+' '+Y(p.rf)+'L'+X(limit)+' '+Y(p.rf+slope*limit)+'" stroke="#d3ad84" stroke-width="1.4" stroke-dasharray="5 5" fill="none"/>';
    series.push({label:'Capital allocation line',color:'#d3ad84',mode:'line',points:[[0,p.rf*100,X(0),Y(p.rf)],[limit*100,(p.rf+slope*limit)*100,X(limit),Y(p.rf+slope*limit)]]});}
  }
  let markers='';
  for(let i=0;i<3;i++)markers+='<circle cx="'+X(p.vol[i])+'" cy="'+Y(p.mu[i])+'" r="3" fill="#7e8d86"/><text x="'+(X(p.vol[i])+7)+'" y="'+(Y(p.mu[i])-7)+'" fill="#9ba99f" font-size="10">Asset '+'ABC'[i]+'</text>';
  for(const [v,label,color,dy] of [[res.g,'GMV','#d3ad84',-10],[res.target,'Target','#f5f5f2',16],[res.tan,'Tangency','#91a9bd',-10]]){
   if(!v)continue;markers+='<circle cx="'+X(v.vol)+'" cy="'+Y(v.mean)+'" r="4.5" fill="#101114" stroke="'+color+'" stroke-width="2"/><text x="'+(X(v.vol)+8)+'" y="'+(Y(v.mean)+dy)+'" fill="'+color+'" font-size="10">'+label+'</text>';
  }
  $('live-plot').innerHTML='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-labelledby="live-frontier-title"><title id="live-frontier-title">Computed portfolio opportunity set under the selected constraints</title><g font-family="Inter,system-ui,sans-serif" font-size="11" fill="#9ba99f">'+grid+labels+'<text x="'+(W/2)+'" y="'+(H-12)+'" text-anchor="middle">Annual portfolio volatility (%)</text><text x="'+L+'" y="19">Annual expected simple return (%)</text>'+markers+'</g>'+curves+'</svg>';
  if(series.length)window.ChartCoordinates?.attach($('live-plot').querySelector('svg'),{viewBox:[0,0,W,H],axes:[{box:[L,T,W-L-R,H-T-B],xLabel:'Annual volatility (%)',yLabel:'Expected simple return (%)',xlim:[0,xmax*100],ylim:[ymin*100,ymax*100],xScale:'linear',yScale:'linear',series}]});
 }
 function calculate(event){
  if(event)event.preventDefault();$('calc-error').textContent='';if(!form.reportValidity())return;
  try{
   const get=x=>Number(form.elements[x].value),mu='abc'.split('').map(c=>get('mu-'+c)/100),vol='abc'.split('').map(c=>get('vol-'+c)/100);
   const a=get('rho-ab'),b=get('rho-ac'),c=get('rho-bc'),R=[[1,a,b],[a,1,c],[b,c,1]];
   const p={mu,vol,rf:get('rf')/100,target:get('target')/100,gamma:get('gamma'),mode:form.elements.mode.value};
   if(![...mu,...vol,a,b,c,p.rf,p.target,p.gamma].every(Number.isFinite)||vol.some(x=>x<=0)||p.gamma<=0)throw Error('Use finite moments, positive volatilities and positive risk aversion.');
   validateCorrelation(R);p.S=R.map((row,i)=>row.map((x,j)=>x*vol[i]*vol[j]));
   const res=compute(p);if(![res.g,...res.high,...res.low,res.target,res.tan].filter(Boolean).every(v=>[v.mean,v.vol,v.gross,...v.w].every(Number.isFinite)))throw Error('These inputs exceed the supported numerical range.');
   for(const [prefix,v] of [['gmv',res.g],['target',res.target],['tan',res.tan]]){ $('result-'+prefix+'-mean').textContent=pct(v?.mean??null);$('result-'+prefix+'-vol').textContent=pct(v?.vol??null);}
   $('result-sharpe').textContent=res.tan?fmt((res.tan.mean-p.rf)/res.tan.vol,6):'—';$('result-gross').textContent=pct(res.target?.gross??null);
   const classification=!res.target?'Infeasible':Math.abs(res.target.mean-res.g.mean)<1e-8?'Global minimum variance':res.target.mean<res.g.mean?'Dominated lower branch':'Efficient branch';
   $('result-classification').textContent=classification;
   const y=res.tan?(res.tan.mean-p.rf)/(p.gamma*res.tan.variance):null;
   $('result-risky').textContent=pct(y);$('result-cash').textContent=y===null?'—':pct(1-y);
   const shares=res.target?res.target.w.map((w,i)=>w*mv(p.S,res.target.w)[i]/res.target.variance):null;
   $('lab-weights').innerHTML=[0,1,2].map(i=>'<tr><th scope="row">Asset '+'ABC'[i]+'</th><td class="num">'+pct(res.g.w[i])+'</td><td class="num">'+pct(res.target?.w[i]??null)+'</td><td class="num">'+pct(res.tan?.w[i]??null)+'</td><td class="num">'+pct(shares?.[i]??null)+'</td></tr>').join('');
   let note='Exact-target allocation: '+classification+'. '+(p.mode==='longonly'?'Risky portfolios are long-only. ':'Risky portfolios allow unrestricted shorts and have net budget 100%. ');
   if(!res.target)note+='The requested target is unavailable under these means and constraints. ';
   if(res.flat)note+='All asset means coincide, so the frontier collapses to the GMV point. ';
   if(!res.tan)note+=p.mode==='longonly'?'No positive-excess-return tangency portfolio is available. ':'Conventional positive-budget tangency is unavailable when the risk-free return is at or above the GMV mean. ';
   else note+='The shown cash allocation optimises γ within the chosen tangency fund plus cash, with equal borrowing and lending rates and unrestricted fund leverage. ';
   note+='Inputs are assumed moments; the chart does not represent realised outcomes or estimation confidence intervals.';
   $('notebook-note').textContent=note;plot(p,res);
  }catch(error){$('calc-error').textContent=error.message+($('result-gmv-mean').textContent!=='—'?' Displayed portfolios use the last valid inputs.':'');}
 }
 form.addEventListener('submit',calculate);$('reset-inputs').addEventListener('click',()=>{form.reset();calculate();});calculate();
 const links=[...document.querySelectorAll('.toc a')],sections=[...document.querySelectorAll('.article>section')],progress=document.querySelector('.reading-progress');
 let pending=false,activeId='';
 function update(){const max=document.documentElement.scrollHeight-innerHeight;progress.style.width=(max>0?Math.min(100,Math.max(0,scrollY/max*100)):0)+'%';const active=sections.filter(s=>s.getBoundingClientRect().top<=130).pop();if(active&&active.id!==activeId){activeId=active.id;links.forEach(a=>a.removeAttribute('aria-current'));links.find(a=>a.hash==='#'+activeId)?.setAttribute('aria-current','location');}pending=false;}
 addEventListener('scroll',()=>{if(!pending){pending=true;requestAnimationFrame(update);}},{passive:true});addEventListener('resize',update);update();
 document.querySelector('.print-button').addEventListener('click',()=>print());
})();
