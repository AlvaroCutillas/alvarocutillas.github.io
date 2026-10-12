(() => {
'use strict';
const form=document.getElementById('yield-form'),colors=['#a7bdb3','#d3ad84','#91a9bd','#7e8d86'];
const ref=[.035,-.02,.025,-.015,1.6,6.5];
const quoteTimes=[.25,.5,.75,1,1.5,2,3,4,5,7,10,12,15,20,25,30];
function load(T,tau){
 const x=T/tau,e=Math.exp(-x),a=Math.abs(x)<1e-5?1-x/2+x*x/6-x*x*x/24+x**4/120:-Math.expm1(-x)/x;
 return [a,a-e];
}
function sample(T,p,model='nss'){
 const [a,b]=load(T,p[4]),x=T/p[4];
 let z=p[0]+p[1]*a+p[2]*b,f=p[0]+p[1]*Math.exp(-x)+p[2]*x*Math.exp(-x);
 if(model==='nss'){const [,b2]=load(T,p[5]),x2=T/p[5];z+=p[3]*b2;f+=p[3]*x2*Math.exp(-x2);}
 return {T,z,f,d:Math.exp(-T*z)};
}
function par(T,p,m=2,model='nss'){
 let sum=0,d;for(let j=1;j<=Math.round(T*m);j++){d=sample(j/m,p,model).d;sum+=d;}
 return m*(1-d)/sum;
}
function valueBond(p,T=5,c=.04,m=2,N=100,shift=0,model='nss'){
 const n=Math.round(T*m),flows=[];let P=0,A=0,B=0;
 for(let j=1;j<=n;j++){const t=j/m,cf=N*c/m+(j===n?N:0),d=sample(t,p,model).d*Math.exp(-shift*t),pv=cf*d;flows.push({t,cf,d,pv});P+=pv;A+=t*pv;B+=t*t*pv;}
 const atYield=y=>flows.reduce((v,a,i)=>v+a.cf/((1+y/m)**(i+1)),0);
 let lo=-m+1e-10,hi=1;while(atYield(hi)>P&&hi<1e6)hi*=2;
 for(let i=0;i<100;i++){const mid=(lo+hi)/2;if(atYield(mid)>P)lo=mid;else hi=mid;}
 return {price:P,ytm:(lo+hi)/2,duration:A/P,convexity:B/P,dv01:.0001*A,flows};
}
const quotes=quoteTimes.map((T,i)=>({T,y:sample(T,ref).z+.00012*Math.sin(7*i)+.00004*Math.cos(3*i),train:i%5!==2}));
function design(T,tau,model){const [a,b]=load(T,tau[0]);return model==='ns'?[1,a,b]:[1,a,b,load(T,tau[1])[1]];}
function linearQR(X,y){
 const n=X.length,k=X[0].length,Q=[],R=Array.from({length:k},()=>Array(k).fill(0));
 for(let j=0;j<k;j++){
  const v=X.map(r=>r[j]);const original=Math.hypot(...v);
  for(let pass=0;pass<2;pass++)for(let i=0;i<j;i++){const r=v.reduce((s,x,h)=>s+x*Q[i][h],0);R[i][j]+=r;for(let h=0;h<n;h++)v[h]-=r*Q[i][h];}
  const norm=Math.hypot(...v);if(norm<1e-9*original)return null;R[j][j]=norm;Q.push(v.map(v=>v/norm));
 }
 const b=Array(k).fill(0),qy=Q.map(q=>q.reduce((s,v,i)=>s+v*y[i],0));
 for(let j=k-1;j>=0;j--){let v=qy[j];for(let h=j+1;h<k;h++)v-=R[j][h]*b[h];b[j]=v/R[j][j];}
 if(b.some(v=>Math.abs(v)>.15))return null;
 const residual=X.map((r,i)=>r.reduce((s,v,j)=>s+v*b[j],0)-y[i]);
 return {b,loss:residual.reduce((s,v)=>s+v*v,0),minPivot:Math.min(...R.map((r,i)=>Math.abs(r[i]))),maxPivot:Math.max(...R.map((r,i)=>Math.abs(r[i])))};
}
function calibrate(model='nss'){
 const train=quotes.filter(q=>q.train),y=train.map(q=>q.y),dims=model==='ns'?1:2;
 const lo=[Math.log(.15),Math.log(.25)],hi=[Math.log(10),Math.log(30)];
 let calls=0;
 function objective(u){calls++;const tau=u.map(Math.exp),X=train.map(q=>design(q.T,tau,model)),r=linearQR(X,y);return r?{...r,u:[...u],tau}:null;}
 const candidates=[],size=dims===1?101:25;
 for(let i=0;i<size;i++)for(let j=0;j<(dims===1?1:size);j++){
  const u=[lo[0]+(hi[0]-lo[0])*i/(size-1)];if(dims===2)u.push(lo[1]+(hi[1]-lo[1])*j/(size-1));
  const r=objective(u);if(r)candidates.push(r);
 }
 candidates.sort((a,b)=>a.loss-b.loss);let best=candidates[0];if(!best)throw Error('No numerically admissible calibration candidate.');
 for(const start of candidates.slice(0,8)){
  let current=start,step=.18;
  for(let it=0;it<180&&step>2e-8;it++){
   let next=current;
   for(let dx=-1;dx<=1;dx++)for(let dy=(dims===1?0:-1);dy<=(dims===1?0:1);dy++){
    if(dx===0&&dy===0)continue;const u=[Math.max(lo[0],Math.min(hi[0],current.u[0]+dx*step))];
    if(dims===2)u.push(Math.max(lo[1],Math.min(hi[1],current.u[1]+dy*step)));
    const r=objective(u);if(r&&r.loss<next.loss)next=r;
   }
   if(next===current)step*=.5;else current=next;
  }
  if(current.loss<best.loss)best=current;
 }
 const b=best.b,p=[b[0],b[1],b[2],dims===2?b[3]:0,best.tau[0],dims===2?best.tau[1]:6.5];
 return {p,calls,loss:best.loss,pivotRatio:best.maxPivot/best.minPivot,model};
}
const pct=x=>(100*x).toFixed(4)+'%',dec=(x,n=5)=>Number(x).toLocaleString('en-US',{minimumFractionDigits:n,maximumFractionDigits:n});
let last=null,fitAudit=null;
function read(){
 const fields=['b0','b1','b2','b3','tau1','tau2','horizon','face','coupon','frequency','maturity','shock'],v={};
 for(const k of fields)v[k]=Number(form.elements[k].value);
 if(form.elements.model.value==='ns'){v.b3=0;v.tau2=6.5;}
 if(!fields.every(k=>Number.isFinite(v[k])))throw Error('Every numeric input must be finite.');
 if(v.maturity>v.horizon)throw Error('Bond maturity must be within the curve horizon.');
 if(Math.abs(v.maturity*v.frequency-Math.round(v.maturity*v.frequency))>1e-8)throw Error('Maturity × coupon frequency must be an integer for this regular exact-year schedule.');
 if(Math.min(v.tau1,v.tau2,v.face,v.maturity)<=0)throw Error('Decay times, face value and maturity must be positive.');
 return {p:[v.b0/100,v.b1/100,v.b2/100,v.b3/100,v.tau1,v.tau2],model:form.elements.model.value,...v};
}
function sync(){const disabled=form.elements.model.value==='ns';for(const k of ['b3','tau2'])form.elements[k].disabled=disabled;}
function draw(host,panels,title){
 const W=800,H=panels.length===2?550:330,axes=[];
 let svg='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="'+title+'"><title>'+title+'</title><rect width="800" height="'+H+'" fill="#0d0d0d"/>';
 panels.forEach((panel,i)=>{
  const box=panels.length===2?[76,34+i*267,686,190]:[76,34,686,225];
  const xs=panel.series.flatMap(s=>s.xy.map(p=>p[0])),ys=panel.series.flatMap(s=>s.xy.map(p=>p[1]));
  const xmin=Math.min(...xs),xmax=Math.max(...xs),yr=Math.max(...ys)-Math.min(...ys),pad=yr>1e-12?yr*.08:Math.max(Math.abs(ys[0])*.08,.001);
  const ymin=Math.min(...ys)-pad,ymax=Math.max(...ys)+pad,X=x=>box[0]+(x-xmin)/(xmax-xmin)*box[2],Y=y=>box[1]+(ymax-y)/(ymax-ymin)*box[3];
  svg+='<text x="'+box[0]+'" y="'+(box[1]-14)+'" fill="#c8cec8" font-size="12">'+panel.title+'</text>';
  for(let j=0;j<=4;j++){
   const x=xmin+(xmax-xmin)*j/4,y=ymin+(ymax-ymin)*j/4;
   svg+='<path d="M'+X(x)+' '+box[1]+'V'+(box[1]+box[3])+'M'+box[0]+' '+Y(y)+'H'+(box[0]+box[2])+'" fill="none" stroke="#252b26"/>';
   svg+='<text x="'+X(x)+'" y="'+(box[1]+box[3]+19)+'" fill="#939b94" font-size="10" text-anchor="middle">'+x.toFixed(panel.xdigits||0)+'</text>';
   svg+='<text x="'+(box[0]-9)+'" y="'+(Y(y)+3)+'" fill="#939b94" font-size="10" text-anchor="end">'+(panel.percent?(100*y).toFixed(2)+'%':y.toFixed(panel.ydigits??3))+'</text>';
  }
  const series=panel.series.map((s,j)=>{
   const color=s.color||colors[j],points=s.xy.map(p=>[p[0],p[1],X(p[0]),Y(p[1])]);
   svg+='<path d="'+points.map((p,k)=>(k?'L':'M')+p[2].toFixed(3)+' '+p[3].toFixed(3)).join(' ')+'" fill="none" stroke="'+color+'" stroke-width="2"/>';
   return {label:s.label,color,mode:'line',points};
  });
  svg+='<text x="'+(box[0]+box[2]/2)+'" y="'+(box[1]+box[3]+42)+'" fill="#a5ada6" text-anchor="middle" font-size="11">'+panel.x+'</text>';
  const cy=box[1]+box[3]/2;svg+='<text x="18" y="'+cy+'" transform="rotate(-90 18 '+cy+')" fill="#a5ada6" text-anchor="middle" font-size="11">'+panel.y+'</text>';
  axes.push({box,xLabel:panel.x,yLabel:panel.y,xScale:'linear',yScale:'linear',yFormat:panel.percent?'percent':null,xlim:[xmin,xmax],ylim:[ymin,ymax],series});
 });
 svg+='</svg>';const container=document.getElementById(host);container.innerHTML=svg;window.ChartCoordinates.attach(container.querySelector('svg'),{viewBox:[0,0,W,H],axes});
}
function audit(p,model){
 const rows=quotes.map(q=>({...q,pred:sample(q.T,p,model).z}));
 const rmse=role=>Math.sqrt(rows.filter(q=>q.train===role).reduce((s,q)=>s+(q.pred-q.y)**2,0)/rows.filter(q=>q.train===role).length)*1e4;
 document.querySelector('#quote-table tbody').innerHTML=rows.map(q=>'<tr><th scope="row">'+q.T+'</th><td>'+(q.train?'Training':'Withheld')+'</td><td class="num">'+pct(q.y)+'</td><td class="num">'+pct(q.pred)+'</td><td class="num">'+dec((q.pred-q.y)*1e4,3)+'</td></tr>').join('');
 const method=fitAudit?'Browser fit: profiled linear coefficients via re-orthogonalized QR; logarithmic decay grid and eight local pattern searches. '+fitAudit.calls+' objective evaluations.':'Current parameter comparison; these quotes have not been fitted in this session.';
 document.getElementById('fit-status').textContent=method+' Training RMSE: '+dec(rmse(true),3)+' bp. Withheld RMSE: '+dec(rmse(false),3)+' bp. Withheld quotes never enter the objective.';
 return {rows,training:rmse(true),holdout:rmse(false)};
}
function build(){
 try{
  window.ChartCoordinates.hide();sync();const o=read(),{p,model}=o;
  const b=valueBond(p,o.maturity,o.coupon/100,o.frequency,o.face,0,model),shift=o.shock/1e4;
  const shocked=valueBond(p,o.maturity,o.coupon/100,o.frequency,o.face,shift,model),quadratic=b.price*(1-b.duration*shift+.5*b.convexity*shift**2);
  const curves=Array.from({length:601},(_,i)=>sample(o.horizon*i/600,p,model));
  const pars=Array.from({length:Math.round(o.horizon*2)},(_,i)=>{const T=(i+1)/2,c=par(T,p,2,model);return [T,2*Math.log1p(c/2)];});
  draw('live-plot',[{title:'Continuous rates and equivalent par rates',x:'Maturity (years)',y:'Annual rate',percent:true,xdigits:1,series:[
   {label:'Continuous zero',xy:curves.map(s=>[s.T,s.z])},
   {label:'Instantaneous forward',xy:curves.map(s=>[s.T,s.f])},
   {label:'Semiannual par, continuous equivalent',xy:pars}]},
   {title:'Discount factors under the selected shock',x:'Maturity (years)',y:'Discount factor',xdigits:1,series:[
    {label:'Base discount',xy:curves.map(s=>[s.T,s.d])},
    {label:'Shocked discount',xy:curves.map(s=>[s.T,s.d*Math.exp(-shift*s.T)])}]}],'Current term structure and discount factors');
  const shocks=Array.from({length:121},(_,i)=>-300+5*i);
  draw('shock-plot',[{title:'Bond price under parallel continuous-zero shifts',x:'Parallel zero shift (basis points)',y:'Bond price',ydigits:2,series:[
   {label:'Exact repricing',color:colors[0],xy:shocks.map(s=>[s,valueBond(p,o.maturity,o.coupon/100,o.frequency,o.face,s/1e4,model).price])},
   {label:'Duration approximation',color:colors[2],xy:shocks.map(s=>[s,b.price*(1-b.duration*s/1e4)])},
   {label:'Duration + convexity',color:colors[1],xy:shocks.map(s=>[s,b.price*(1-b.duration*s/1e4+.5*b.convexity*(s/1e4)**2)])}]}],'Exact and approximated bond shock prices');
  document.getElementById('result-price').textContent=dec(b.price);
  document.getElementById('result-ytm').textContent=pct(b.ytm);
  document.getElementById('result-duration').textContent=dec(b.duration,4);
  document.getElementById('result-dv01').textContent=dec(b.dv01,6);
  document.getElementById('result-convexity').textContent=dec(b.convexity,4);
  document.getElementById('result-shocked').textContent=dec(shocked.price);
  document.getElementById('result-error').textContent=dec(quadratic-shocked.price,6);
  const minF=Math.min(...curves.map(s=>s.f));
  document.getElementById('curve-status').textContent='D(0) = 1; all sampled discount factors are positive. Short-rate limit: '+pct(p[0]+p[1])+'. Long-rate limit: '+pct(p[0])+'. Minimum sampled forward: '+pct(minF)+'. '+(minF<0?'Negative forwards are present: this is a negative-rate curve assumption, not an automatic arbitrage diagnosis.':'All sampled forwards are nonnegative; the displayed discount curve is decreasing.');
  document.querySelector('#cash-table tbody').innerHTML=b.flows.map(r=>'<tr><th scope="row">'+r.t+'</th><td class="num">'+dec(r.cf,4)+'</td><td class="num">'+dec(r.d,8)+'</td><td class="num">'+dec(r.pv,6)+'</td></tr>').join('');
  const calibration=audit(p,model);
  document.getElementById('notebook-note').textContent='YTM is nominal with '+o.frequency+' compounding periods per year. Par curves use semiannual coupons independently of the selected bond frequency. Duration, convexity and DV01 refer to a parallel continuous-zero shift; DV01 is the positive first-order loss for +1 bp. Synthetic calibration uses equal zero-rate weights, decay bounds τ₁ ∈ [0.15, 10], τ₂ ∈ [0.25, 30] years and |β| ≤ 15%. The search has no global-optimum guarantee. CSV exports the current curve and parameters.';
  last={o,b,shocked,quadratic,curves,pars,calibration};document.getElementById('calc-error').textContent='';
 }catch(e){document.getElementById('calc-error').textContent=e.message;}
}
form.addEventListener('submit',e=>{e.preventDefault();fitAudit=null;build();});
form.elements.model.addEventListener('change',()=>{fitAudit=null;sync();});
document.getElementById('reset-inputs').addEventListener('click',()=>{form.reset();fitAudit=null;build();});
document.getElementById('fit-quotes').addEventListener('click',()=>{
 if(!form.reportValidity())return;
 try{read();const fit=calibrate(form.elements.model.value);fitAudit=fit;
  ['b0','b1','b2','b3'].forEach((k,i)=>form.elements[k].value=100*fit.p[i]);
  form.elements.tau1.value=fit.p[4];form.elements.tau2.value=fit.p[5];build();
 }catch(e){document.getElementById('calc-error').textContent=e.message;}
});
document.getElementById('download-curve').addEventListener('click',()=>{
 if(!last)return;const {o,curves}=last;
 const head='maturity_years,zero_continuous_decimal,forward_continuous_decimal,discount_factor,shocked_discount_factor,model,beta0_decimal,beta1_decimal,beta2_decimal,beta3_decimal,tau1_years,tau2_years,shock_bps';
 const rows=curves.map(s=>[s.T,s.z,s.f,s.d,s.d*Math.exp(-o.shock/1e4*s.T),o.model,...o.p,o.shock].join(','));
 const blob=new Blob([head+'\n'+rows.join('\n')+'\n'],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='yield-curve.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
window.YieldLab={sample,load,par,valueBond,linearQR,calibrate,quotes,get last(){return last;},get fit(){return fitAudit;}};
document.querySelector('.print-button').addEventListener('click',()=>print());
let printedDetails=[];
addEventListener('beforeprint',()=>{printedDetails=[...document.querySelectorAll('details')].map(el=>[el,el.open]);printedDetails.forEach(([el])=>el.open=true);});
addEventListener('afterprint',()=>{printedDetails.forEach(([el,open])=>el.open=open);printedDetails=[];});
const progress=document.querySelector('.reading-progress');
function updateProgress(){const total=document.documentElement.scrollHeight-innerHeight;progress.style.width=(total>0?100*scrollY/total:0)+'%';}
addEventListener('scroll',updateProgress,{passive:true});addEventListener('resize',updateProgress);build();updateProgress();
})();
