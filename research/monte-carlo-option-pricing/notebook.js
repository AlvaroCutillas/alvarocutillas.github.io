(() => {
  'use strict';
  const $=id=>document.getElementById(id),form=$('simulation-form');
  const num=(x,places=6)=>!Number.isFinite(x)?'—':Math.abs(x)>1e9||(x!==0&&Math.abs(x)<1e-6)?x.toExponential(4):x.toLocaleString('en-US',{minimumFractionDigits:places,maximumFractionDigits:places});
  function Phi(x){
    if(x>=8.3)return 1;if(x<=-8.3)return 0;
    const z=Math.abs(x);let term=z,sum=z;
    for(let n=1;n<250;n++){term*=z*z/(2*n+1);sum+=term;if(term<=sum*1e-16)break;}
    const v=Math.exp(-z*z/2)/Math.sqrt(2*Math.PI)*sum;
    return Math.max(0,Math.min(1,x<0?.5-v:.5+v));
  }
  function reference(p){
    const a=p.S*Math.exp(-p.q*p.T),b=p.K*Math.exp(-p.r*p.T);
    if(p.T===0||p.sigma===0)return Math.max(p.put?b-a:a-b,0);
    const d1=(Math.log(p.S/p.K)+(p.r-p.q+p.sigma*p.sigma/2)*p.T)/(p.sigma*Math.sqrt(p.T)),d2=d1-p.sigma*Math.sqrt(p.T);
    return Math.max(0,p.put?b*Phi(-d2)-a*Phi(-d1):a*Phi(d1)-b*Phi(d2));
  }
  function normalStream(seed){
    let state=seed>>>0,spare=null;
    function uniform(){
      state=(state+0x6d2b79f5)|0;let t=state;
      t=Math.imul(t^(t>>>15),1|t);t^=t+Math.imul(t^(t>>>7),61|t);
      return (((t^(t>>>14))>>>0)+.5)/4294967296;
    }
    return ()=>{
      if(spare!==null){const z=spare;spare=null;return z;}
      const radius=Math.sqrt(-2*Math.log(uniform())),angle=2*Math.PI*uniform();
      spare=radius*Math.sin(angle);return radius*Math.cos(angle);
    };
  }
  function unitFactory(p,paired,stream){
    const discount=Math.exp(-p.r*p.T),drift=(p.r-p.q-p.sigma*p.sigma/2)*p.T,scale=p.sigma*Math.sqrt(p.T);
    const one=z=>{
      const spot=p.S*Math.exp(drift+scale*z),y=discount*Math.max(p.put?p.K-spot:spot-p.K,0),c=discount*spot;
      if(!Number.isFinite(y)||!Number.isFinite(c))throw Error('These inputs produce nonfinite simulated values. Use a finite, numerically representable parameter range.');
      return {y,c,hits:y>0?1:0};
    };
    return ()=>{
      const z=scale===0?0:stream(),a=one(z);
      if(!paired)return a;const b=one(-z);
      return {y:(a.y+b.y)/2,c:(a.c+b.c)/2,hits:a.hits+b.hits};
    };
  }
  function simulate(p){
    const paired=p.method==='antithetic'||p.method==='combined',controlled=p.method==='control'||p.method==='combined';
    const unitCost=paired?2:1,M=p.N/unitCost,known=p.S*Math.exp(-p.q*p.T),truth=reference(p);
    if(!Number.isFinite(known)||!Number.isFinite(truth))throw Error('These inputs produce a nonfinite analytical reference or control mean.');
    let beta=0,pilotWork=0;
    if(controlled&&p.T>0&&p.sigma>0){
      const draw=unitFactory(p,paired,normalStream((p.seed^0x9e3779b9)>>>0));
      let my=0,mc=0,cov=0,vc=0;
      for(let i=1;i<=1024;i++){
        const a=draw(),dy=a.y-my,dc=a.c-mc;my+=dy/i;mc+=dc/i;cov+=dy*(a.c-mc);vc+=dc*(a.c-mc);
      }
      if(vc>Number.EPSILON*Math.max(1,mc*mc)*1024)beta=cov/vc;
      pilotWork=1024*unitCost;
    }
    const first=Math.min(100,Math.max(2,Math.floor(M/4))),checkpoints=new Set([M]);
    for(let i=0;i<100;i++)checkpoints.add(Math.round(Math.exp(Math.log(first)+(Math.log(M)-Math.log(first))*i/99)));
    const draw=unitFactory(p,paired,normalStream(p.seed));let mean=0,m2=0,hits=0;const trace=[];
    for(let i=1;i<=M;i++){
      const a=draw(),adjusted=a.y-beta*(a.c-known),delta=adjusted-mean;
      mean+=delta/i;m2+=delta*(adjusted-mean);hits+=a.hits;
      if(checkpoints.has(i)){const se=Math.sqrt(Math.max(0,m2/(i-1)/i));trace.push({n:i,value:mean,se,lower:mean-1.96*se,upper:mean+1.96*se});}
    }
    const se=Math.sqrt(Math.max(0,m2/(M-1)/M));
    if(![mean,se,beta].every(Number.isFinite))throw Error('The calculation exceeded the supported numerical range.');
    return {value:mean,se,lower:mean-1.96*se,upper:mean+1.96*se,truth,beta,pilotWork,work:p.N+pilotWork,units:M,hits,trace,deterministic:p.T===0||p.sigma===0};
  }
  function plot(result){
    window.ChartCoordinates?.hide();
    const W=780,H=330,left=66,right=26,top=30,bottom=55,points=result.trace;
    const xmin=points[0].n,xmax=points[points.length-1].n;
    let ymin=Math.min(result.truth,...points.map(p=>p.lower)),ymax=Math.max(result.truth,...points.map(p=>p.upper));
    const pad=Math.max((ymax-ymin)*.10,Math.abs(result.truth)*.005,.001);ymin-=pad;ymax+=pad;
    const X=x=>left+(Math.log(x)-Math.log(xmin))/(Math.log(xmax)-Math.log(xmin))*(W-left-right),Y=y=>H-bottom-(y-ymin)/(ymax-ymin)*(H-top-bottom);
    const path=key=>points.map((p,i)=>(i?'L':'M')+X(p.n).toFixed(3)+','+Y(p[key]).toFixed(3)).join(' ');
    let grid='',labels='';
    for(let i=0;i<=4;i++){
      const v=ymin+(ymax-ymin)*i/4,yy=Y(v);
      grid+='<line x1="'+left+'" x2="'+(W-right)+'" y1="'+yy+'" y2="'+yy+'" stroke="#242925"/>';
      labels+='<text x="'+(left-10)+'" y="'+(yy+4)+'" text-anchor="end">'+num(v,2)+'</text>';
    }
    const ticks=[xmin,...[100,500,1000,5000,10000,50000,100000,200000].filter(n=>n>xmin&&n<xmax),xmax];
    const selected=ticks.filter((n,i)=>i===0||i===ticks.length-1||X(n)-X(ticks[i-1])>55);
    for(const n of selected)labels+='<text x="'+X(n)+'" y="'+(H-bottom+23)+'" text-anchor="middle">'+num(n,0)+'</text>';
    const band=path('upper')+' '+points.slice().reverse().map(p=>'L'+X(p.n).toFixed(3)+','+Y(p.lower).toFixed(3)).join(' ')+' Z';
    $('live-plot').innerHTML='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-labelledby="mc-live-title mc-live-desc"><title id="mc-live-title">Monte Carlo estimate and pointwise confidence interval</title><desc id="mc-live-desc">Running estimate using independent production units; final estimate '+num(result.value)+', standard error '+num(result.se)+'. Sand dashed line: Black–Scholes reference '+num(result.truth)+'.</desc><g font-family="Inter, system-ui, sans-serif" font-size="11" fill="#9ba99f">'+grid+labels+'<text x="'+(W/2)+'" y="'+(H-9)+'" text-anchor="middle">Independent production units M · logarithmic scale</text><text x="'+left+'" y="17">Option value</text></g><path d="'+band+'" fill="#a7bdb3" fill-opacity=".08"/><path d="'+path('lower')+'" fill="none" stroke="#7e8d86" stroke-width="1" stroke-dasharray="3 4"/><path d="'+path('upper')+'" fill="none" stroke="#7e8d86" stroke-width="1" stroke-dasharray="3 4"/><line x1="'+left+'" x2="'+(W-right)+'" y1="'+Y(result.truth)+'" y2="'+Y(result.truth)+'" stroke="#d3ad84" stroke-width="1.5" stroke-dasharray="6 4"/><path d="'+path('value')+'" fill="none" stroke="#a7bdb3" stroke-width="2"/><circle cx="'+X(xmax)+'" cy="'+Y(result.value)+'" r="3.5" fill="#e8eee9"/></svg>';
    const series=[
      {label:'Monte Carlo estimate',color:'#a7bdb3',key:'value'},
      {label:'95% lower endpoint',color:'#7e8d86',key:'lower'},
      {label:'95% upper endpoint',color:'#7e8d86',key:'upper'}
    ].map(s=>({label:s.label,color:s.color,mode:'snap',points:points.map(p=>[p.n,p[s.key],X(p.n),Y(p[s.key])])}));
    series.push({label:'BSM reference',color:'#d3ad84',mode:'line',points:[[xmin,result.truth,X(xmin),Y(result.truth)],[xmax,result.truth,X(xmax),Y(result.truth)]]});
    window.ChartCoordinates?.attach($('live-plot').querySelector('svg'),{viewBox:[0,0,W,H],axes:[{box:[left,top,W-left-right,H-top-bottom],xLabel:'Independent units M',yLabel:'Option value',xScale:'log',yScale:'linear',xlim:[xmin,xmax],ylim:[ymin,ymax],series}]});
  }
  let runId=0;
  async function calculate(event){
    if(event)event.preventDefault();$('calc-error').textContent='';
    if(!form.reportValidity())return;
    const get=name=>Number(form.elements[name].value);
    const p={S:get('spot'),K:get('strike'),r:get('rate')/100,q:get('yield')/100,sigma:get('vol')/100,T:get('tau'),N:get('budget'),seed:get('seed'),method:form.elements.method.value,put:form.elements.kind.value==='put'};
    if(![p.S,p.K,p.r,p.q,p.sigma,p.T,p.N,p.seed].every(Number.isFinite)||p.S<=0||p.K<=0||p.sigma<0||p.T<0){$('calc-error').textContent='Use finite inputs, positive spot and strike, and non-negative maturity and volatility.';return;}
    if(!Number.isInteger(p.N)||p.N<100||p.N>200000||!Number.isInteger(p.seed)||p.seed<0||p.seed>4294967295){$('calc-error').textContent='Use an integer budget from 100 to 200,000 and a seed from 0 to 4,294,967,295.';return;}
    if((p.method==='antithetic'||p.method==='combined')&&p.N%2){$('calc-error').textContent='Antithetic methods require an even production payoff budget: each independent unit contains two payoffs.';return;}
    const ticket=++runId,button=$('calculate');button.disabled=true;button.textContent='Simulating…';
    await new Promise(resolve=>requestAnimationFrame(resolve));if(ticket!==runId)return;
    try{
      const result=simulate(p),outputs={price:result.value,se:result.se,reference:result.truth,error:Math.abs(result.value-result.truth),lower:result.lower,upper:result.upper};
      for(const [key,value] of Object.entries(outputs))$('result-'+key).textContent=num(value);
      $('result-units').textContent=num(result.units,0);$('result-work').textContent=num(result.work,0);$('result-pilot').textContent=num(result.pilotWork,0);
      $('result-beta').textContent=result.pilotWork?num(result.beta,5):'Not used';
      $('result-hits').textContent=num(result.hits/p.N*100,2)+'%';
      let note='Exact terminal GBM simulation. The estimated standard error uses independent '+((p.method==='antithetic'||p.method==='combined')?'pair averages. ':'payoff observations. ');
      if(result.pilotWork)note+='The control coefficient is fitted on a separate 1,024-unit pilot and frozen for production. ';
      note+='Running intervals are pointwise 95% normal approximations; repeated inspection does not give a simultaneous coverage guarantee.';
      if(result.deterministic)note='Deterministic maturity or volatility limit. The payoff is known exactly, the standard error is zero, and no control pilot is needed.';
      else if(result.hits===0)note='No positive payoff was observed. A zero sample variance does not establish a zero option value; this interval is uninformative for the unresolved payoff tail. Increase the sample or use a justified rare-event method.';
      $('notebook-note').textContent=note;plot(result);
    }catch(error){$('calc-error').textContent=error.message;}
    finally{if(ticket===runId){button.disabled=false;button.textContent='Run simulation';}}
  }
  form.addEventListener('submit',calculate);$('reset-inputs').addEventListener('click',()=>{form.reset();calculate();});calculate();
  const links=[...document.querySelectorAll('.toc a')],sections=[...document.querySelectorAll('.article > section')],progress=document.querySelector('.reading-progress');
  let activeId='',pending=false;
  function update(){
    const max=document.documentElement.scrollHeight-innerHeight;progress.style.width=(max>0?Math.min(100,Math.max(0,scrollY/max*100)):0)+'%';
    const active=sections.filter(s=>s.getBoundingClientRect().top<=130).pop();
    if(active&&active.id!==activeId){activeId=active.id;links.forEach(a=>a.removeAttribute('aria-current'));links.find(a=>a.hash==='#'+activeId)?.setAttribute('aria-current','location');}
    pending=false;
  }
  addEventListener('scroll',()=>{if(!pending){pending=true;requestAnimationFrame(update);}},{passive:true});addEventListener('resize',update);update();
  document.querySelector('.print-button').addEventListener('click',()=>print());
})();
