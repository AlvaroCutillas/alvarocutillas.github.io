(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const form = $('pricing-form');
  const num = (x, places=6) => Number.isFinite(x) ? x.toLocaleString('en-US',{minimumFractionDigits:places,maximumFractionDigits:places}) : '—';
  const density = x => Math.exp(-x*x/2)/Math.sqrt(2*Math.PI);
  // Positive-term normal integral expansion; avoids the cancellation of erf's alternating series.
  function Phi(x) {
    if (x >= 8.3) return 1;
    if (x <= -8.3) return 0;
    const z=Math.abs(x); let term=z, sum=z;
    for (let n=1;n<250;n++) {term *= z*z/(2*n+1);sum += term;if (term <= sum*1e-16) break;}
    const integral=density(z)*sum;
    return Math.max(0,Math.min(1,x<0 ? .5-integral : .5+integral));
  }
  function european(S,K,r,q,sigma,tau) {
    if (tau===0) return {call:Math.max(S-K,0),put:Math.max(K-S,0),limit:true};
    const a=Math.exp(-q*tau), b=Math.exp(-r*tau);
    if (sigma===0) return {call:Math.max(S*a-K*b,0),put:Math.max(K*b-S*a,0),limit:true};
    const root=Math.sqrt(tau),d1=(Math.log(S/K)+(r-q+sigma*sigma/2)*tau)/(sigma*root),d2=d1-sigma*root, ph=density(d1);
    const call=Math.max(0,S*a*Phi(d1)-K*b*Phi(d2)),put=Math.max(0,K*b*Phi(-d2)-S*a*Phi(-d1));
    return {call,put,dc:a*Phi(d1),dp:-a*Phi(-d1),gamma:a*ph/(S*sigma*root),vega:S*a*ph*root,
      tc:-S*a*ph*sigma/(2*root)-r*K*b*Phi(d2)+q*S*a*Phi(d1),tp:-S*a*ph*sigma/(2*root)+r*K*b*Phi(-d2)-q*S*a*Phi(-d1),
      rc:K*tau*b*Phi(d2),rp:-K*tau*b*Phi(-d2),probC:Phi(d2),probP:Phi(-d2)};
  }
  function deterministicAmerican(S,K,r,q,tau,put) {
    const dates=[0,tau];
    if(r>0 && q>0 && r!==q) {const z=Math.log(r*K/(q*S))/(r-q);if(z>0 && z<tau) dates.push(z);}
    return Math.max(...dates.map(t => Math.max((put?1:-1)*(K*Math.exp(-r*t)-S*Math.exp(-q*t)),0)));
  }
  function tree(S,K,r,q,sigma,tau,n=400) {
    if(tau===0) return {call:Math.max(S-K,0),put:Math.max(K-S,0)};
    if(sigma===0) return {call:deterministicAmerican(S,K,r,q,tau,false),put:deterministicAmerican(S,K,r,q,tau,true),deterministic:true};
    const dt=tau/n,step=sigma*Math.sqrt(dt),u=Math.exp(step),d=1/u,p=(Math.exp((r-q)*dt)-d)/(u-d),disc=Math.exp(-r*dt);
    if(!(p>0 && p<1)) return {invalid:true};
    const call=new Float64Array(n+1),put=new Float64Array(n+1);
    for(let j=0;j<=n;j++) {const spot=S*Math.exp((2*j-n)*step);call[j]=Math.max(spot-K,0);put[j]=Math.max(K-spot,0);}
    for(let i=n-1;i>=0;i--) for(let j=0;j<=i;j++) {
      const spot=S*Math.exp((2*j-i)*step);
      call[j]=Math.max(spot-K,disc*(p*call[j+1]+(1-p)*call[j]));
      put[j]=Math.max(K-spot,disc*(p*put[j+1]+(1-p)*put[j]));
    }
    return {call:call[0],put:put[0]};
  }
  function plot(S,K,r,q,sigma,tau,kind,current) {
    window.ChartCoordinates?.hide();
    const width=780,height=320,left=63,right=25,top=24,bottom=55;
    const xmin=Math.max(.001,Math.min(S,K)*.5),xmax=Math.max(S,K)*1.5;
    const points=Array.from({length:181},(_,i)=>{const x=xmin+(xmax-xmin)*i/180;return {x,y:european(x,K,r,q,sigma,tau)[kind],payoff:Math.max(kind==='call'?x-K:K-x,0)};});
    const ymax=Math.max(1,...points.map(p=>Math.max(p.y,p.payoff)))*1.1;
    const X=x=>left+(x-xmin)/(xmax-xmin)*(width-left-right),Y=y=>height-bottom-y/ymax*(height-top-bottom);
    let grid='', labels='';
    for(let i=0;i<=4;i++) {const y=ymax*i/4;grid+=`<line x1="${left}" x2="${width-right}" y1="${Y(y)}" y2="${Y(y)}" stroke="#26302a"/>`;labels+=`<text x="${left-10}" y="${Y(y)+4}" text-anchor="end">${num(y,1)}</text>`;}
    for(let i=0;i<=4;i++) {const x=xmin+(xmax-xmin)*i/4;labels+=`<text x="${X(x)}" y="${height-bottom+24}" text-anchor="middle">${num(x,0)}</text>`;}
    const path=(key)=>points.map((p,i)=>`${i?'L':'M'}${X(p.x).toFixed(2)},${Y(p[key]).toFixed(2)}`).join(' ');
    $('live-plot').innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="live-title live-desc"><title id="live-title">European ${kind} value versus spot</title><desc id="live-desc">Analytical ${kind} value and immediate payoff, with current spot ${S}, strike ${K}, volatility ${sigma*100} percent and ${tau} years remaining. Current option value ${current.toFixed(6)}.</desc><g font-family="Inter, system-ui, sans-serif" font-size="11" fill="#9ba99f">${grid}${labels}<text x="${width/2}" y="${height-10}" text-anchor="middle">Spot S · other inputs fixed</text><text x="${left}" y="16">Value per underlying unit</text></g><path d="${path('payoff')}" fill="none" stroke="#d3ad84" stroke-width="1.5" stroke-dasharray="5 4"/><path d="${path('y')}" fill="none" stroke="#a7bdb3" stroke-width="2.4"/><line x1="${X(K)}" x2="${X(K)}" y1="${top}" y2="${height-bottom}" stroke="#596f5e" stroke-dasharray="3 5"/><circle cx="${X(S)}" cy="${Y(current)}" r="4.5" fill="#e7ede7"/><g font-family="Inter, system-ui, sans-serif" font-size="10" fill="#b4c0b7"><text x="${width-right}" y="26" text-anchor="end">Sage: European ${kind} · Sand dashed: payoff</text></g></svg>`;
    window.ChartCoordinates?.attach($('live-plot').querySelector('svg'),{viewBox:[0,0,width,height],axes:[{box:[left,top,width-left-right,height-top-bottom],xLabel:'Spot S',yLabel:kind==='call'?'Call value':'Put value',xScale:'linear',yScale:'linear',xlim:[xmin,xmax],ylim:[0,ymax],series:[
      {label:'European '+kind,color:'#a7bdb3',mode:'line',points:points.map(p=>[p.x,p.y,X(p.x),Y(p.y)])},
      {label:'Immediate payoff',color:'#d3ad84',mode:'line',points:points.map(p=>[p.x,p.payoff,X(p.x),Y(p.payoff)])}
    ]}]});
  }
  function calculate(event) {
    if(event) event.preventDefault();
    if(!form.reportValidity()) return;
    const S=Number(form.elements.spot.value),K=Number(form.elements.strike.value),r=Number(form.elements.rate.value)/100,q=Number(form.elements.yield.value)/100,sigma=Number(form.elements.vol.value)/100,tau=Number(form.elements.tau.value),kind=form.elements.kind.value;
    $('calc-error').textContent='';
    if(![S,K,r,q,sigma,tau].every(Number.isFinite)||S<=0||K<=0||sigma<0||tau<0) {$('calc-error').textContent='Enter finite values, positive spot and strike, and non-negative maturity and volatility.';return;}
    const value=european(S,K,r,q,sigma,tau), american=tree(S,K,r,q,sigma,tau);
    $('result-call').textContent=num(value.call);$('result-put').textContent=num(value.put);
    $('result-acall').textContent=american.invalid?'Unavailable':num(american.call);$('result-aput').textContent=american.invalid?'Unavailable':num(american.put);
    const put=kind==='put';
    const metric={delta:put?value.dp:value.dc,gamma:value.gamma,vega:value.vega/100,theta:(put?value.tp:value.tc)/365,rho:(put?value.rp:value.rc)/100,prob:put?value.probP:value.probC};
    for(const [key,v] of Object.entries(metric)) $('result-'+key).textContent=key==='prob' ? (Number.isFinite(v)?num(v*100,4)+'%':'—') : num(v);
    let note=`European ${kind} sensitivities. CRR 400 approximates both exercise styles; European analytical values provide the diffusion reference.`;
    if(q===0 && r>=0) note+= ' Without dividends and with non-negative rates, American and European calls have equal values in the same tree.';
    if(value.limit) note='Expiry or zero-volatility limit. Prices use the limiting payoff formulas; Greeks are omitted because the smooth non-degenerate formulas do not apply. '+(american.deterministic?'American values optimise deterministic discounted exercise payoff.':'');
    if(american.invalid) {$('calc-error').textContent='At these inputs the 400-step CRR probability lies outside (0, 1). European values remain valid; American estimates need a finer or alternative tree.';note+=' American estimates unavailable for this tree.';}
    $('notebook-note').textContent=note; plot(S,K,r,q,sigma,tau,kind,value[kind]);
  }
  form.addEventListener('submit',calculate);
  $('reset-inputs').addEventListener('click',()=>{form.reset();calculate();});
  calculate();
  const links=[...document.querySelectorAll('.toc a')];
  const sections=[...document.querySelectorAll('.article > section')]; let activeId='';
  const progress=document.querySelector('.reading-progress'); let framePending=false;
  function updateProgress(){
    const max=document.documentElement.scrollHeight-window.innerHeight;
    progress.style.width=(max>0?Math.min(100,Math.max(0,window.scrollY/max*100)):0)+'%';
    const active=sections.filter(s=>s.getBoundingClientRect().top<=130).pop();
    if(active && active.id!==activeId) {activeId=active.id;links.forEach(a=>a.removeAttribute('aria-current'));const match=links.find(a=>a.hash==='#'+activeId);if(match) match.setAttribute('aria-current','location');}
    framePending=false;
  }
  addEventListener('scroll',()=>{if(!framePending){framePending=true;requestAnimationFrame(updateProgress);}},{passive:true});
  addEventListener('resize',updateProgress); updateProgress();
  document.querySelector('.print-button').addEventListener('click',()=>window.print());
})();
