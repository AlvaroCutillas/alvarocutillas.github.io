(() => {
'use strict';
const form=document.getElementById('strategy-form');if(!form)return;
function random(seed){
 let a=seed>>>0,spare=null;
 const uniform=()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};
 return ()=>{if(spare!==null){const z=spare;spare=null;return z;}const u=uniform()+.5/4294967296,v=uniform(),r=Math.sqrt(-2*Math.log(u)),ang=2*Math.PI*v;spare=r*Math.sin(ang);return r*Math.cos(ang);};
}
function market(n=1512,seed=5105,model='regimes'){
 const normal=random(seed),p=new Float64Array(n+1);p[0]=100;let prev=0;
 for(let j=0;j<n;j++){
  const state=Math.min(4,Math.floor(j*5/n));
  const mean=model==='regimes'?[.0006,-.0007,.0005,0,.0003][state]:.0002;
  const phi=model==='regimes'?[.12,.10,.15,-.20,.05][state]:({iid:0,trend:.2,reversion:-.2}[model]);
  const sd=model==='regimes'?[.008,.016,.010,.012,.009][state]:.01;
  const g=mean+phi*prev+sd*normal();p[j+1]=p[j]*Math.exp(g);prev=g;
 }
 return p;
}
function moments(a){
 let mean=0;for(const v of a)mean+=v;mean/=a.length;
 let variance=0;for(const v of a)variance+=(v-mean)**2;return {mean,sd:a.length>1?Math.sqrt(variance/(a.length-1)):0};
}
function targets(p,opts){
 const n=p.length-1,r=new Float64Array(n);for(let j=0;j<n;j++)r[j]=p[j+1]/p[j]-1;
 const out=new Float64Array(n+1),warm=Math.max(opts.lookback,opts.volControl?opts.volWindow:0);
 for(let k=warm;k<=n;k++){
  let a=0;
  if(opts.rule==='hold')a=1;
  else if(opts.rule==='cash')a=0;
  else if(opts.rule==='momentum')a=p[k]>p[k-opts.lookback]?1:0;
  else{const m=moments(p.slice(k-opts.lookback+1,k+1));a=m.sd>1e-14&&(p[k]-m.mean)/m.sd<-1?1:0;}
  const vol=opts.volControl?moments(r.slice(k-opts.volWindow,k)).sd*Math.sqrt(252):0;
  out[k]=a*(opts.volControl&&vol>1e-14?Math.min(1,opts.volTarget/vol):1);
 }
 return out;
}
function rebalance(equity,stock,w,c){
 const h=stock/equity,u=w>=h?w*(1+c*h)/(1+c*w):w*(1-c*h)/(1-c*w),turn=Math.abs(u-h),fee=equity*c*turn;
 return {stock:equity*u,cash:equity-fee-equity*u,fee,turn};
}
function metrics(b){
 const n=b.returns.length,mm=moments(b.returns),excess=b.returns.map(x=>x-b.rf),xm=moments(excess),dd=new Float64Array(n+1);
 let peak=b.equity[0],maxDD=0,turn=0,fees=0,exposure=0,orders=0,down=0;
 for(let i=0;i<=n;i++){peak=Math.max(peak,b.equity[i]);dd[i]=b.equity[i]/peak-1;maxDD=Math.min(maxDD,dd[i]);}
 for(let i=0;i<n;i++){turn+=b.turnover[i];fees+=b.fees[i];exposure+=b.exposure[i];if(b.turnover[i]>1e-10)orders++;down+=Math.min(excess[i],0)**2;}
 const ratio=b.equity[n]/b.equity[0];
 return {totalReturn:ratio-1,cagr:Math.pow(ratio,252/n)-1,volatility:mm.sd*Math.sqrt(252),sharpe:xm.sd>1e-12?xm.mean/xm.sd*Math.sqrt(252):null,
 sortino:down>1e-24?xm.mean/Math.sqrt(down/n)*Math.sqrt(252):null,maxDD,annualTurnover:turn*252/n,totalFees:fees,averageExposure:exposure/n,orders,drawdown:dd};
}
function run(p,opts,providedTargets=null){
 const start=opts.start??Math.max(opts.lookback,opts.volControl?opts.volWindow:0)+opts.delay,end=opts.end??p.length-1;
 const t=providedTargets||targets(p,opts),c=opts.costBps/10000,rf=Math.pow(1+opts.cashAnnual,1/252)-1;
 let shares=0,cash=opts.capital,equity=opts.capital;
 const b={start,end,rf,equity:[equity],returns:[],exposure:[],turnover:[],fees:[],ledger:[]};
 for(let j=start+1;j<=end;j++){
  const k=j-1-opts.delay,w=k>=0?t[k]:0,begin=equity,balance=rebalance(begin,shares*p[j-1],w,c);
  shares=balance.stock/p[j-1];cash=balance.cash*(1+rf);equity=shares*p[j]+cash;
  const ret=equity/begin-1;b.equity.push(equity);b.returns.push(ret);b.exposure.push(w);b.turnover.push(balance.turn);b.fees.push(balance.fee);
  b.ledger.push({day:j,asof:k,price_start:p[j-1],price_end:p[j],wealth_start:begin,target:w,turnover:balance.turn,fee:balance.fee,
    stock_after:balance.stock,cash_after:balance.cash,wealth_after_cost:begin-balance.fee,wealth_end:equity,net_return:ret});
 }
 b.metrics=metrics(b);return b;
}
const pct=x=>(100*x).toLocaleString('en-GB',{minimumFractionDigits:2,maximumFractionDigits:2})+'%';
const money=x=>x.toLocaleString('en-GB',{style:'currency',currency:'EUR',minimumFractionDigits:2,maximumFractionDigits:2});
const decimal=x=>x===null?'—':x.toLocaleString('en-GB',{minimumFractionDigits:3,maximumFractionDigits:3});
function render(accounts){
 const names=['Strategy, net','Strategy, zero cost','Buy and hold','Cash'],colors=['#a7bdb3','#7e8d86','#d3ad84','#91a9bd'],start=accounts[0].start,end=accounts[0].end;
 const curves=accounts.map(b=>b.equity.map(x=>x/b.equity[0]*100)),all=curves.flat(),low=Math.min(...all),high=Math.max(...all),span=Math.max(high-low,1);
 const boxes=[[73,24,687,231],[73,314,687,142]],ranges=[[low-span*.07,high+span*.1],[Math.min(...accounts.map(b=>b.metrics.maxDD))-.012,.004]];
 const X=x=>73+(x-start)/(end-start)*687;
 let svg='<svg viewBox="0 0 800 520" role="img" aria-labelledby="live-chart-title"><title id="live-chart-title">Strategy, gross, passive and cash wealth and drawdown paths</title><rect width="800" height="520" fill="#0d0d0d"/>';
 const axes=[];
 for(let panel=0;panel<2;panel++){
  const box=boxes[panel],ylim=ranges[panel],Y=v=>box[1]+box[3]*(1-(v-ylim[0])/(ylim[1]-ylim[0]));
  for(let j=0;j<=4;j++){
   const v=ylim[0]+(ylim[1]-ylim[0])*j/4,y=Y(v);
   svg+='<path d="M73 '+y+'H760" stroke="#252b26"/><text x="65" y="'+(y+4)+'" fill="#939b94" font-size="10" text-anchor="end">'+(panel===0?v.toFixed(1):(100*v).toFixed(1)+'%')+'</text>';
  }
  const series=[];
  for(let k=0;k<4;k++){
   const raw=panel===0?curves[k]:accounts[k].metrics.drawdown;
   const points=Array.from(raw,(v,i)=>[start+i,v,X(start+i),Y(v)]);
   svg+='<path d="'+points.map((a,i)=>(i?'L':'M')+a[2].toFixed(3)+' '+a[3].toFixed(3)).join(' ')+'" stroke="'+colors[k]+'" stroke-width="'+(k===0?2:1.3)+'" fill="none"/>';
   series.push({label:names[k],color:colors[k],mode:'snap',points});
  }
  svg+='<path d="M73 '+box[1]+'V'+(box[1]+box[3])+'H760" fill="none" stroke="#424842"/><text x="16" y="'+(box[1]+box[3]/2)+'" transform="rotate(-90 16 '+(box[1]+box[3]/2)+')" fill="#a5ada6" font-size="11" text-anchor="middle">'+(panel===0?'Wealth index':'Drawdown')+'</text>';
  for(let j=0;j<=4;j++){const x=Math.round(start+(end-start)*j/4);svg+='<text x="'+X(x)+'" y="'+(box[1]+box[3]+19)+'" fill="#939b94" font-size="10" text-anchor="middle">'+x+'</text>';}
  axes.push({box,xLabel:'Trading day',yLabel:panel===0?'Wealth index':'Drawdown',xFormat:null,yFormat:panel===0?null:'percent',xScale:'linear',yScale:'linear',xlim:[start,end],ylim,series});
 }
 svg+='<text x="416" y="287" fill="#a5ada6" font-size="11" text-anchor="middle">Trading day</text><text x="416" y="500" fill="#a5ada6" font-size="11" text-anchor="middle">Trading day</text></svg>';
 const host=document.getElementById('live-plot');host.innerHTML=svg;window.ChartCoordinates?.attach(host.querySelector('svg'),{viewBox:[0,0,800,520],axes});
}
let last=null;
function calculate(){
 const val=name=>Number(form.elements.namedItem(name).value),o={lookback:val('lookback'),volControl:form.elements.namedItem('volmode').value==='on',volTarget:val('voltarget')/100,volWindow:val('volwindow'),
  costBps:val('cost'),cashAnnual:val('cash')/100,delay:val('delay'),capital:val('capital'),rule:form.elements.namedItem('rule').value};
 const n=val('sessions'),seed=val('seed'),model=form.elements.namedItem('model').value,err=document.getElementById('calc-error');err.textContent='';
 const integer=x=>Number.isFinite(x)&&Number.isInteger(x);
 if(![o.lookback,o.volWindow,o.delay,n,seed].every(integer)||o.lookback<5||o.lookback>252||o.volWindow<5||o.volWindow>126||o.delay<1||o.delay>5||n<504||n>3000||seed<0||seed>4294967295||
  ![o.volTarget,o.costBps,o.cashAnnual,o.capital].every(Number.isFinite)||o.volTarget<.01||o.volTarget>.4||o.costBps<0||o.costBps>100||o.cashAnnual<-.05||o.cashAnnual>.15||o.capital<100||o.capital>1e9){
  err.textContent='Enter finite values within the displayed ranges; windows, delay, sessions and seed must be integers.';return;
 }
 try{
  const p=market(n,seed,model),net=run(p,o),start=net.start;
  const gross=run(p,{...o,costBps:0}),hold=run(p,{...o,rule:'hold',volControl:false,start}),cash=run(p,{...o,rule:'cash',volControl:false,start});
  const accounts=[net,gross,hold,cash],m=net.metrics;
  document.getElementById('result-cagr').textContent=pct(m.cagr);document.getElementById('result-sharpe').textContent=decimal(m.sharpe);document.getElementById('result-dd').textContent=pct(m.maxDD);
  document.getElementById('result-wealth').textContent=money(net.equity.at(-1));document.getElementById('result-fees').textContent=money(m.totalFees);
  document.getElementById('result-exposure').textContent=pct(m.averageExposure);document.getElementById('result-turnover').textContent=decimal(m.annualTurnover)+' ×';
  const labels=['Strategy, net','Strategy, zero cost','Buy and hold','Cash'];
  document.getElementById('lab-metrics').innerHTML=accounts.map((b,i)=>'<tr><th scope="row">'+labels[i]+'</th>'+[pct(b.metrics.totalReturn),pct(b.metrics.cagr),pct(b.metrics.volatility),decimal(b.metrics.sharpe),pct(b.metrics.maxDD)].map(v=>'<td class="num">'+v+'</td>').join('')+'</tr>').join('');
  render(accounts);
  document.getElementById('notebook-note').textContent='Synthetic '+({regimes:'five-regime',iid:'IID',trend:'positive-autocorrelation',reversion:'negative-autocorrelation'}[model])+' market; seed '+seed+'. Common evaluation starts at close '+start+' and includes '+net.returns.length+' return periods. A target formed at close k is executed at close k + '+o.delay+' and first earns return k + '+(o.delay+1)+'. '+m.orders+' nonzero rebalance orders. All fills are assumed at synthetic closes; costs are proportional to actual one-way notional. These are exploratory results; the annualized Sharpe uses the IID scaling convention.';
  last={prices:p,options:o,accounts,seed,model};window.StrategyLab.last=last;
 }catch(e){err.textContent=e.message;}
}
form.addEventListener('submit',e=>{e.preventDefault();calculate();});
document.getElementById('reset-inputs').addEventListener('click',()=>{form.reset();calculate();});
document.getElementById('download-ledger').addEventListener('click',()=>{
 if(!last)return;const rows=last.accounts[0].ledger,keys=Object.keys(rows[0]);
 const csv=keys.join(',')+'\r\n'+rows.map(r=>keys.map(k=>r[k]).join(',')).join('\r\n');
 const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='strategy-ledger-seed-'+last.seed+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
document.querySelector('.print-button')?.addEventListener('click',()=>{document.querySelectorAll('details').forEach(e=>e.open=true);window.print();});
const progress=document.querySelector('.reading-progress');function updateProgress(){if(progress)progress.style.width=(100*scrollY/Math.max(1,document.documentElement.scrollHeight-innerHeight))+'%';}
addEventListener('scroll',updateProgress,{passive:true});addEventListener('resize',updateProgress);updateProgress();
window.StrategyLab={market,targets,rebalance,run,metrics,last:null};calculate();
})();
