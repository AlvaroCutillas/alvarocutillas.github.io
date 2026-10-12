(() => {
'use strict';
const form=document.getElementById('surface-form'),ivForm=document.getElementById('iv-form');
const colors=['#a7bdb3','#91a9bd','#d3ad84','#7e8d86','#bbbac7'];
function cdf(x){
 const y=Math.abs(x);if(y>37)return x>0?1:0;
 const e=Math.exp(-y*y/2);let tail;
 if(y<7.07106781186547){
  const n=((((((.0352624965998911*y+.700383064443688)*y+6.37396220353165)*y+33.912866078383)*y+112.079291497871)*y+221.213596169931)*y+220.206867912376);
  const d=(((((((.0883883476483184*y+1.75566716318264)*y+16.064177579207)*y+86.7807322029461)*y+296.564248779674)*y+637.333633378831)*y+793.826512519948)*y+440.413735824752);
  tail=e*n/d;
 }else tail=e/(y+1/(y+2/(y+3/(y+4/(y+.65)))))/Math.sqrt(2*Math.PI);
 return x>0?1-tail:tail;
}
function black(F,K,D,T,sigma,put=false){
 if(sigma===0)return D*Math.max(put?K-F:F-K,0);
 const root=sigma*Math.sqrt(T),d1=Math.log(F/K)/root+root/2,d2=d1-root;
 if(K>=F){const c=Math.max(0,D*(F*cdf(d1)-K*cdf(d2)));return put?c+D*(K-F):c;}
 const p=Math.max(0,D*(K*cdf(-d2)-F*cdf(-d1)));return put?p:p+D*(F-K);
}
function vega(F,K,D,T,sigma){
 if(sigma<=0)return 0;const d1=Math.log(F/K)/(sigma*Math.sqrt(T))+.5*sigma*Math.sqrt(T);
 return D*F*Math.exp(-d1*d1/2)/Math.sqrt(2*Math.PI)*Math.sqrt(T);
}
function implied(price,F,K,D,T,put=false){
 if(![price,F,K,D,T].every(Number.isFinite)||Math.min(F,K,D,T)<=0)throw Error('Finite positive forward, strike, discount factor and maturity are required.');
 const low=D*Math.max(put?K-F:F-K,0),high=D*(put?K:F);
 if(price<low||price>=high)throw Error('Premium must be at least '+low.toFixed(8)+' and strictly below '+high.toFixed(8)+' for a finite Black implied volatility.');
 if(price===low)return 0;
 let a=0,b=.5;while(black(F,K,D,T,b,put)<price&&b<16)b*=2;
 if(black(F,K,D,T,b,put)<price)throw Error('The root exceeds the numerical volatility cap of 16.00.');
 for(let i=0;i<90;i++){const m=(a+b)/2;if(black(F,K,D,T,m,put)<price)a=m;else b=m;}
 return (a+b)/2;
}
function theta(T,p){return p.long*p.long*T+(p.short*p.short-p.long*p.long)*p.decay*(-Math.expm1(-T/p.decay));}
function sample(k,T,p){
 const th=theta(T,p),ph=p.eta/(1+th),u=ph*k+p.rho,z=Math.sqrt(u*u+1-p.rho*p.rho);
 const w=th/2*(1+p.rho*ph*k+z),wk=th*ph/2*(p.rho+u/z),wkk=th*ph*ph/2*(1-p.rho*p.rho)/(z*z*z);
 const wth=(1+p.rho*ph*k+z)/2-th/2*p.eta/((1+th)**2)*k*(p.rho+u/z);
 const tp=p.long*p.long+(p.short*p.short-p.long*p.long)*Math.exp(-T/p.decay),wt=wth*tp;
 const g=(1-k*wk/(2*w))**2-wk*wk/4*(1/w+.25)+wkk/2;
 return {w,wk,wkk,wt,g,sigma:Math.sqrt(w/T),local:g>0&&wt>0?Math.sqrt(wt/g):null};
}
function bounds(p,H){
 const th=theta(H,p),f=1+Math.abs(p.rho),q=Math.min(th,1);
 return {horizonWing:p.eta*th/(1+th)*f,horizonCurvature:p.eta*p.eta*q/((1+q)**2)*f,
 globalWing:p.eta*f,globalCurvature:p.eta*p.eta*f/4};
}
const pct=x=>x===null?'Unavailable':(100*x).toFixed(3)+'%';
const dec=(x,d=5)=>Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
let last=null,cellPinned=false;
const cellTip=document.createElement('div');cellTip.id='surface-cell-tooltip';cellTip.className='chart-tooltip';cellTip.hidden=true;cellTip.setAttribute('role','tooltip');document.body.append(cellTip);
function hideCell(){cellTip.hidden=true;document.querySelector('#surface-map .cell-highlight')?.setAttribute('visibility','hidden');cellPinned=false;}
function placeTip(tip,x,y){
 tip.hidden=false;const b=tip.getBoundingClientRect();let left=x+20,top=y+18;
 if(left+b.width>innerWidth-12)left=x-b.width-20;if(top+b.height>innerHeight-12)top=y-b.height-18;
 tip.style.left=Math.max(12,Math.min(innerWidth-b.width-12,left))+'px';tip.style.top=Math.max(12,Math.min(innerHeight-b.height-12,top))+'px';
}
function renderMap(p,o){
 hideCell();const rows=25,cols=49,box=[73,24,650,240],H=o.horizon,cells=[];
 for(let row=0;row<rows;row++)for(let col=0;col<cols;col++){
  const T=H-(H-.05)*row/(rows-1),k=-.6+1.2*col/(cols-1),s=sample(k,T,p),F=o.spot*Math.exp((o.rate-o.yield)*T);
  cells.push({row,col,T,k,...s,K:F*Math.exp(k)});
 }
 const lo=Math.min(...cells.map(c=>c.sigma)),hi=Math.max(...cells.map(c=>c.sigma));
 const color=v=>{const t=(v-lo)/Math.max(hi-lo,1e-12),a=[28,41,35],b=[193,216,206];return 'rgb('+a.map((x,i)=>Math.round(x+(b[i]-x)*t)).join(',')+')';};
 let svg='<svg viewBox="0 0 800 350" tabindex="0" role="img" aria-labelledby="surface-map-title surface-map-desc"><title id="surface-map-title">Synthetic implied volatility across log-moneyness and maturity</title><desc id="surface-map-desc">A 25 by 49 sampled volatility map. Hover or tap for cell values; arrow keys change cells and Escape dismisses the inspector. Time runs from the shortest expiry at the bottom to the longest at the top.</desc><rect width="800" height="350" fill="#0d0d0d"/>';
 const cw=box[2]/cols,ch=box[3]/rows;
 for(const c of cells)svg+='<rect x="'+(box[0]+c.col*cw)+'" y="'+(box[1]+c.row*ch)+'" width="'+(cw+.1)+'" height="'+(ch+.1)+'" fill="'+color(c.sigma)+'"/>';
 svg+='<rect class="cell-highlight" visibility="hidden" width="'+cw+'" height="'+ch+'" fill="none" stroke="#f5f5f2" stroke-width="1.5" pointer-events="none"/>';
 for(let i=0;i<=4;i++){const col=i*(cols-1)/4;svg+='<text x="'+(box[0]+(col+.5)*cw)+'" y="283" fill="#939b94" font-size="10" text-anchor="middle">'+(-.6+1.2*i/4).toFixed(2)+'</text>';}
 for(let i=0;i<=4;i++){const row=i*(rows-1)/4;svg+='<text x="65" y="'+(box[1]+(row+.5)*ch+4)+'" fill="#939b94" font-size="10" text-anchor="end">'+(H-(H-.05)*i/4).toFixed(2)+'</text>';}
 svg+='<text x="398" y="309" fill="#a5ada6" font-size="11" text-anchor="middle">Log-forward moneyness k</text><text x="17" y="144" transform="rotate(-90 17 144)" fill="#a5ada6" font-size="11" text-anchor="middle">Maturity (years)</text>';
 for(let i=0;i<60;i++)svg+='<rect x="'+(250+i*5)+'" y="325" width="5.1" height="8" fill="'+color(lo+(hi-lo)*i/59)+'"/>';
 svg+='<text x="238" y="333" fill="#a5ada6" font-size="10" text-anchor="end">'+pct(lo)+'</text><text x="561" y="333" fill="#a5ada6" font-size="10">'+pct(hi)+'</text></svg>';
 const host=document.getElementById('surface-map');host.innerHTML=svg;const el=host.querySelector('svg');let row=12,col=24;
 function show(r,c,x,y){
  window.ChartCoordinates?.hide();row=Math.max(0,Math.min(rows-1,r));col=Math.max(0,Math.min(cols-1,c));const cell=cells[row*cols+col];
  const rect=el.querySelector('.cell-highlight');rect.setAttribute('x',box[0]+col*cw);rect.setAttribute('y',box[1]+row*ch);rect.setAttribute('visibility','visible');
  cellTip.innerHTML='<div class="chart-tooltip-header"><span>Maturity</span><strong>'+dec(cell.T,4)+' years</strong></div><div class="chart-tooltip-unit">Sampled surface cell</div><div class="chart-tooltip-rows">'+[['Log-moneyness k',dec(cell.k,4)],['Implied volatility',pct(cell.sigma)],['Total variance',dec(cell.w,6)],['Strike',dec(cell.K,4)]].map((a,i)=>'<div class="chart-tooltip-row'+(i===1?' is-nearest':'')+'"><i class="chart-tooltip-swatch" style="background:#a7bdb3"></i><span class="chart-tooltip-label">'+a[0]+'</span><strong>'+a[1]+'</strong></div>').join('')+'</div>';
  placeTip(cellTip,x,y);el.dataset.inspectedRow=row;el.dataset.inspectedCol=col;
 }
 function inspect(e){const pt=new DOMPoint(e.clientX,e.clientY).matrixTransform(el.getScreenCTM().inverse());if(pt.x<box[0]||pt.x>box[0]+box[2]||pt.y<box[1]||pt.y>box[1]+box[3]){if(!cellPinned)hideCell();return;}show(Math.floor((pt.y-box[1])/ch),Math.floor((pt.x-box[0])/cw),e.clientX,e.clientY);}
 el.addEventListener('pointermove',e=>{if(e.pointerType!=='touch'){cellPinned=false;inspect(e);}});
 el.addEventListener('pointerdown',e=>{inspect(e);cellPinned=e.pointerType==='touch';});
 el.addEventListener('pointerleave',e=>{if(e.pointerType!=='touch'&&!cellPinned)hideCell();});
 el.addEventListener('blur',()=>{if(!cellPinned)hideCell();});
 el.addEventListener('keydown',e=>{if(e.key==='Escape'){hideCell();return;}if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(e.key))return;e.preventDefault();
  if(e.key==='ArrowLeft')col--;if(e.key==='ArrowRight')col++;if(e.key==='ArrowUp')row--;if(e.key==='ArrowDown')row++;if(e.key==='Home')col=0;if(e.key==='End')col=cols-1;
  row=Math.max(0,Math.min(rows-1,row));col=Math.max(0,Math.min(cols-1,col));const pt=new DOMPoint(box[0]+(col+.5)*cw,box[1]+(row+.5)*ch).matrixTransform(el.getScreenCTM());show(row,col,pt.x,pt.y);
 });
 return cells;
}
function renderSlices(p,o){
 const Ts=[.1,.25,.5,.75,1].map(x=>o.horizon*x),boxes=[[73,24,687,220],[73,307,687,145]],axes=[];
 const grid=Array.from({length:241},(_,i)=>-.6+1.2*i/240),series=Ts.map(T=>grid.map(k=>sample(k,T,p)));
 const all=series.flat(),limits=[[Math.min(...all.map(s=>s.sigma))*.94,Math.max(...all.map(s=>s.sigma))*1.06],
 [Math.min(0,Math.min(...all.map(s=>s.g)))-.03,Math.max(...all.map(s=>s.g))*1.06]];
 let svg='<svg viewBox="0 0 800 505" role="img" aria-labelledby="live-chart-title"><title id="live-chart-title">Five synthetic volatility slices and their butterfly diagnostics</title><rect width="800" height="505" fill="#0d0d0d"/>';
 const X=k=>73+(k+.6)/1.2*687;
 for(let panel=0;panel<2;panel++){
  const box=boxes[panel],ylim=limits[panel],Y=v=>box[1]+box[3]*(1-(v-ylim[0])/(ylim[1]-ylim[0])),curves=[];
  for(let j=0;j<=4;j++){const v=ylim[0]+(ylim[1]-ylim[0])*j/4,y=Y(v);svg+='<path d="M73 '+y+'H760" stroke="#252b26"/><text x="65" y="'+(y+4)+'" fill="#939b94" font-size="10" text-anchor="end">'+(panel===0?(v*100).toFixed(1)+'%':v.toFixed(2))+'</text>';}
  for(let i=0;i<Ts.length;i++){
   const pts=grid.map((k,j)=>[k,panel===0?series[i][j].sigma:series[i][j].g,X(k),Y(panel===0?series[i][j].sigma:series[i][j].g)]);
   svg+='<path d="'+pts.map((v,j)=>(j?'L':'M')+v[2].toFixed(3)+' '+v[3].toFixed(3)).join(' ')+'" stroke="'+colors[i]+'" stroke-width="1.8" fill="none"/>';
   curves.push({label:Ts[i].toFixed(3)+'y',color:colors[i],mode:'line',points:pts});
  }
  if(panel===1)svg+='<path d="M73 '+Y(0)+'H760" stroke="#a1a1aa" stroke-dasharray="4 5" opacity=".6"/>';
  for(let j=0;j<=4;j++){const k=-.6+1.2*j/4;svg+='<text x="'+X(k)+'" y="'+(box[1]+box[3]+18)+'" fill="#939b94" font-size="10" text-anchor="middle">'+k.toFixed(2)+'</text>';}
  svg+='<text x="17" y="'+(box[1]+box[3]/2)+'" transform="rotate(-90 17 '+(box[1]+box[3]/2)+')" fill="#a5ada6" font-size="11" text-anchor="middle">'+(panel===0?'Implied volatility':'Butterfly diagnostic g')+'</text>';
  axes.push({box,xLabel:'Log-forward moneyness k',yLabel:panel===0?'Implied volatility':'Butterfly diagnostic g',xFormat:null,yFormat:panel===0?'percent':null,xScale:'linear',yScale:'linear',xlim:[-.6,.6],ylim,series:curves});
 }
 svg+='<text x="416" y="282" fill="#a5ada6" font-size="11" text-anchor="middle">Log-forward moneyness k</text><text x="416" y="490" fill="#a5ada6" font-size="11" text-anchor="middle">Log-forward moneyness k</text></svg>';
 const host=document.getElementById('live-plot');host.innerHTML=svg;host.querySelector('svg').addEventListener('pointerenter',hideCell);window.ChartCoordinates?.attach(host.querySelector('svg'),{viewBox:[0,0,800,505],axes});
 document.getElementById('slice-legend').innerHTML=Ts.map((T,i)=>'<span><i style="background:'+colors[i]+'"></i>'+T.toFixed(3)+' years</span>').join('');
}
function recover(){
 const el=document.getElementById('inversion-result');if(!last)return;
 const put=ivForm.elements.kind.value==='put',price=Number(ivForm.elements.premium.value),{F,K,D,T}=last.contract;
 try{const iv=implied(price,F,K,D,T,put),res=black(F,K,D,T,iv,put)-price;
  el.textContent=iv===0?'Intrinsic-limit premium: the numerical root is 0%. Positive volatility cannot be resolved from this premium at its working precision. Try the out-of-the-money side for a deeply in-the-money contract.':'Recovered Black IV: '+pct(iv)+' · repricing residual '+res.toExponential(2)+' premium units. This inversion holds the selected contract and carry inputs fixed.';el.classList.remove('has-error');last.recovered=iv;
 }catch(e){el.textContent=e.message;el.classList.add('has-error');last.recovered=null;}
}
function usePrice(){if(!last)return;ivForm.elements.premium.value=String(ivForm.elements.kind.value==='put'?last.contract.put:last.contract.call);recover();}
function calculate(){
 const val=n=>Number(form.elements.namedItem(n).value),p={short:val('short')/100,long:val('long')/100,decay:val('decay'),rho:val('rho'),eta:val('eta')},
 o={horizon:val('horizon'),spot:val('spot'),rate:val('rate')/100,yield:val('yield')/100,T:val('maturity'),k:val('k')},err=document.getElementById('calc-error');err.textContent='';
 const intervals=[[p.short,.05,.8],[p.long,.05,.8],[p.decay,.05,10],[p.rho,-.95,.95],[p.eta,0,12],[o.horizon,.25,10],[o.spot,1,100000],[o.rate,-.05,.2],[o.yield,0,.2],[o.T,.05,o.horizon],[o.k,-.6,.6]];
 if(!intervals.every(([x,a,b])=>Number.isFinite(x)&&x>=a&&x<=b)){err.textContent='Enter finite values within the displayed ranges. The selected maturity must not exceed the surface horizon.';return;}
 hideCell();window.ChartCoordinates?.hide();const s=sample(o.k,o.T,p),F=o.spot*Math.exp((o.rate-o.yield)*o.T),D=Math.exp(-o.rate*o.T),K=F*Math.exp(o.k);
 const contract={F,K,D,T:o.T,...s,call:black(F,K,D,o.T,s.sigma),put:black(F,K,D,o.T,s.sigma,true)};
 const cells=renderMap(p,o);renderSlices(p,o);const b=bounds(p,o.horizon);
 let minG=Infinity,minWT=Infinity;
 for(let i=0;i<=60;i++)for(let j=0;j<=400;j++){const v=sample(-3+6*j/400,.05+(o.horizon-.05)*i/60,p);minG=Math.min(minG,v.g);minWT=Math.min(minWT,v.wt);}
 const global=b.globalWing<4&&b.globalCurvature<=4,horizon=b.horizonWing<4&&b.horizonCurvature<=4;
 let label=global?'Global sufficient bounds pass':horizon?'Displayed-horizon sufficient bounds pass':'Sufficient butterfly bounds are not met';
 if(minG< -1e-8)label='Butterfly inconsistency found on the diagnostic grid';
 const status=document.getElementById('surface-status');status.classList.toggle('has-violation',minG< -1e-8);
 status.innerHTML='<strong>'+label+'</strong><p>Minimum sampled g = '+dec(minG,5)+'; minimum sampled ∂w/∂T = '+dec(minWT,6)+'. Diagnostic grid: 61 maturities from 0.05 to '+o.horizon+' years and 401 k values from −3 to 3. Calendar sufficient condition passes analytically for this family.</p><p>Global test values: wing '+dec(b.globalWing,4)+', curvature '+dec(b.globalCurvature,4)+'. Horizon values: wing '+dec(b.horizonWing,4)+', curvature '+dec(b.horizonCurvature,4)+'. Required: wing &lt; 4 and curvature ≤ 4.'+(global?'':horizon?' The all-maturity butterfly certificate is unavailable.':' A passing finite grid alone cannot certify all strikes.')+'</p>';
 document.getElementById('result-iv').textContent=pct(s.sigma);document.getElementById('result-call').textContent=dec(contract.call,4);document.getElementById('result-put').textContent=dec(contract.put,4);
 document.getElementById('result-local').textContent=pct(s.local);document.getElementById('result-forward').textContent=dec(F,3)+' / '+dec(K,3);
 document.getElementById('result-variance').textContent=dec(s.w,6);document.getElementById('result-vega').textContent=dec(vega(F,K,D,o.T,s.sigma)/100,5);
 document.getElementById('notebook-note').textContent='Synthetic SSVI with phi(theta) = eta / (1 + theta); a positive decaying ATM variance rate. Forward = spot × exp((rate − yield)T); D = exp(−rate T). Map cells are sampled values, not interpolated observations. Local volatility assumes a smooth European local diffusion and is unavailable when its point diagnostic is invalid. Changing a shape parameter does not calibrate a market chain.';
 last={parameters:p,options:o,contract,bounds:b,minG,minWT,cells};window.SurfaceLab.last=last;usePrice();
}
form.addEventListener('submit',e=>{e.preventDefault();calculate();});ivForm.addEventListener('submit',e=>{e.preventDefault();recover();});
document.getElementById('reset-inputs').addEventListener('click',()=>{form.reset();ivForm.reset();calculate();});
document.getElementById('use-surface-price').addEventListener('click',usePrice);ivForm.elements.kind.addEventListener('change',usePrice);
document.getElementById('download-surface').addEventListener('click',()=>{
 if(!last)return;const {parameters:p,options:o}=last,keys=['maturity_years','log_moneyness','forward','strike','discount','implied_volatility','total_variance','call_premium','put_premium','butterfly_g','local_volatility'];
 const data=last.cells.map(c=>{const F=o.spot*Math.exp((o.rate-o.yield)*c.T),D=Math.exp(-o.rate*c.T);return [c.T,c.k,F,c.K,D,c.sigma,c.w,black(F,c.K,D,c.T,c.sigma),black(F,c.K,D,c.T,c.sigma,true),c.g,c.local===null?'':c.local].join(',');});
 const url=URL.createObjectURL(new Blob([keys.join(',')+'\r\n'+data.join('\r\n')+'\r\n'],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='synthetic-ssvi-surface.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
document.addEventListener('pointerdown',e=>{if(!document.getElementById('surface-map').contains(e.target))hideCell();});
addEventListener('scroll',hideCell,{passive:true,capture:true});addEventListener('resize',hideCell);
document.querySelector('.print-button')?.addEventListener('click',()=>{hideCell();document.querySelectorAll('details').forEach(e=>e.open=true);window.print();});
const progress=document.querySelector('.reading-progress');function update(){if(progress)progress.style.width=(100*scrollY/Math.max(1,document.documentElement.scrollHeight-innerHeight))+'%';}
addEventListener('scroll',update,{passive:true});addEventListener('resize',update);update();
window.SurfaceLab={cdf,black,vega,implied,theta,sample,bounds,last:null};calculate();
})();
