(() => {
'use strict';
const form=document.getElementById('risk-form');if(!form)return;
const colors=['#a7bdb3','#d3ad84','#91a9bd','#7e8d86'];
const phi=x=>Math.exp(-x*x/2)/Math.sqrt(2*Math.PI);
function Phi(x){
 const y=Math.abs(x);if(y>37)return x>0?1:0;
 let tail;
 if(y<7.07106781186547){
  const num=((((((.0352624965998911*y+.700383064443688)*y+6.37396220353165)*y+33.912866078383)*y+112.079291497871)*y+221.213596169931)*y+220.206867912376);
  const den=(((((((.0883883476483184*y+1.75566716318264)*y+16.064177579207)*y+86.7807322029461)*y+296.564248779674)*y+637.333633378831)*y+793.826512519948)*y+440.413735824752);
  tail=Math.exp(-y*y/2)*num/den;
 }else{
  tail=Math.exp(-y*y/2)/(y+1/(y+2/(y+3/(y+4/(y+.65)))))/Math.sqrt(2*Math.PI);
 }
 return x>0?1-tail:tail;
}
function quantile(cdf,p){
 let lo=-1,hi=1;
 while(cdf(lo)>p)lo*=2;
 while(cdf(hi)<p)hi*=2;
 for(let j=0;j<85;j++){const mid=(lo+hi)/2;if(cdf(mid)<p)lo=mid;else hi=mid;}
 return (lo+hi)/2;
}
function logGamma(z){
 const c=[676.5203681218851,-1259.1392167224028,771.32342877765313,-176.61502916214059,12.507343278686905,-.13857109526572012,9.9843695780195716e-6,1.5056327351493116e-7];
 if(z<.5)return Math.log(Math.PI)-Math.log(Math.sin(Math.PI*z))-logGamma(1-z);
 z-=1;let x=.99999999999980993;for(let i=0;i<c.length;i++)x+=c[i]/(z+i+1);
 const t=z+7.5;return .5*Math.log(2*Math.PI)+(z+.5)*Math.log(t)-t+Math.log(x);
}
function betaFraction(a,b,x){
 const tiny=1e-300;let c=1,d=1-(a+b)*x/(a+1);if(Math.abs(d)<tiny)d=tiny;d=1/d;let h=d;
 for(let m=1;m<=500;m++){
  const m2=2*m;let aa=m*(b-m)*x/((a+m2-1)*(a+m2));
  d=1+aa*d;if(Math.abs(d)<tiny)d=tiny;c=1+aa/c;if(Math.abs(c)<tiny)c=tiny;d=1/d;h*=d*c;
  aa=-(a+m)*(a+b+m)*x/((a+m2)*(a+m2+1));
  d=1+aa*d;if(Math.abs(d)<tiny)d=tiny;c=1+aa/c;if(Math.abs(c)<tiny)c=tiny;d=1/d;const delta=d*c;h*=delta;
  if(Math.abs(delta-1)<3e-14)return h;
 }
 throw new Error('Tail integration did not converge. Try different parameters.');
}
function betaI(x,a,b){
 if(x<=0)return 0;if(x>=1)return 1;
 const bt=Math.exp(logGamma(a+b)-logGamma(a)-logGamma(b)+a*Math.log(x)+b*Math.log1p(-x));
 return x<(a+1)/(a+b+2)?bt*betaFraction(a,b,x)/a:1-bt*betaFraction(b,a,1-x)/b;
}
function studentCDF(x,nu){
 if(x===0)return .5;
 const tail=.5*betaI(nu/(nu+x*x),nu/2,.5);return x>0?1-tail:tail;
}
function studentPDF(x,nu){return Math.exp(logGamma((nu+1)/2)-logGamma(nu/2)-.5*Math.log(nu*Math.PI)-(nu+1)/2*Math.log1p(x*x/nu));}
function analytical(alpha,mean,sd,dist,nu){
 if(sd===0)return [mean,mean];
 if(dist==='normal'){const z=quantile(Phi,alpha);return [mean+sd*z,mean+sd*phi(z)/(1-alpha)];}
 const z=quantile(x=>studentCDF(x,nu),alpha),scale=sd*Math.sqrt((nu-2)/nu);
 return [mean+scale*z,mean+scale*(nu+z*z)/(nu-1)*studentPDF(z,nu)/(1-alpha)];
}
function random(seed){
 let a=seed>>>0;
 const uniform=()=>{a=(a+0x6D2B79F5)>>>0;let t=a;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};
 let spare=null;
 const normal=()=>{if(spare!==null){const z=spare;spare=null;return z;}const u=(uniform()+.5/4294967296),v=uniform(),r=Math.sqrt(-2*Math.log(u)),ang=2*Math.PI*v;spare=r*Math.sin(ang);return r*Math.cos(ang);};
 function gamma(shape){
  if(shape<1)return gamma(shape+1)*Math.pow(Math.max(uniform(),1e-15),1/shape);
  const d=shape-1/3,c=1/Math.sqrt(9*d);
  for(;;){const z=normal(),v0=1+c*z;if(v0<=0)continue;const v=v0*v0*v0,u=uniform();if(u<1-.0331*z*z*z*z||Math.log(Math.max(u,1e-15))<.5*z*z+d*(1-v+Math.log(v)))return d*v;}
 }
 return {normal,student:nu=>normal()/Math.sqrt(2*gamma(nu/2)/nu)};
}
function empirical(sorted,alpha,suffix){
 const n=sorted.length,index=Math.max(0,Math.min(n-1,Math.ceil(alpha*n-1e-10)-1)),q=sorted[index];
 const excess=suffix[index+1]-(n-index-1)*q;
 return [q,q+Math.max(0,excess)/(n*(1-alpha))];
}
function suffixSum(sorted){const a=new Float64Array(sorted.length+1);for(let i=sorted.length-1;i>=0;i--)a[i]=a[i+1]+sorted[i];return a;}
function render(p,sorted,suffix){
 const start=Math.min(.9,p.alpha),end=Math.max(.999,p.alpha),confidence=Array.from({length:151},(_,i)=>start+(end-start)*i/150);
 confidence.push(p.alpha);confidence.sort((a,b)=>a-b);
 const values=confidence.map(a=>[...analytical(a,p.mean,p.sd,p.dist,p.nu),...empirical(sorted,a,suffix)]);
 let ymin=Math.min(...values.flat()),ymax=Math.max(...values.flat()),span=ymax-ymin;
 if(span<1e-8){span=Math.max(Math.abs(ymax)*.05,1);ymin-=span/2;ymax+=span/2;}else{ymin-=span*.07;ymax+=span*.1;}
 const box=[74,28,680,268],X=a=>box[0]+(a-start)/(end-start||1)*box[2],Y=v=>box[1]+box[3]-(v-ymin)/(ymax-ymin)*box[3];
 const labels=['Analytical VaR','Analytical ES','Empirical VaR','Empirical ES'];let svg='<svg viewBox="0 0 790 360" role="img" aria-labelledby="live-title"><title id="live-title">Analytical and empirical tail risk across confidence levels</title><rect width="790" height="360" fill="#0d0d0d"/>';
 for(let i=0;i<=4;i++){
  const v=ymin+(ymax-ymin)*i/4,y=Y(v),a=start+(end-start)*i/4,x=X(a);
  svg+='<path d="M74 '+y+'H754" stroke="#252b26"/><text x="65" y="'+(y+4)+'" fill="#939b94" font-size="10" text-anchor="end">'+v.toLocaleString('en-GB',{maximumFractionDigits:0})+'</text>';
  svg+='<text x="'+x+'" y="319" fill="#939b94" font-size="10" text-anchor="middle">'+(100*a).toFixed(2)+'%</text>';
 }
 svg+='<path d="M74 28V296H754" fill="none" stroke="#424842"/><path d="M'+X(p.alpha)+' 28V296" stroke="#6d746e" stroke-dasharray="3 4"/>';
 const series=[];
 for(let k=0;k<4;k++){
  const points=confidence.map((a,i)=>[a,values[i][k],X(a),Y(values[i][k])]);
  svg+='<path d="'+points.map((a,i)=>(i?'L':'M')+a[2].toFixed(3)+' '+a[3].toFixed(3)).join(' ')+'" stroke="'+colors[k]+'" stroke-width="'+(k<2?2:1.5)+'" '+(k>=2?'stroke-dasharray="4 3" ':'')+'fill="none"/>';
  series.push({label:labels[k],color:colors[k],mode:k>=2?'snap':'line',points});
 }
 svg+='<text x="413" y="346" fill="#a5ada6" font-size="11" text-anchor="middle">Confidence level</text><text x="15" y="162" transform="rotate(-90 15 162)" fill="#a5ada6" font-size="11" text-anchor="middle">Loss (€)</text></svg>';
 const host=document.getElementById('live-plot');host.innerHTML=svg;
 window.ChartCoordinates?.attach(host.querySelector('svg'),{viewBox:[0,0,790,360],axes:[{box,xLabel:'Confidence level',yLabel:'Loss (€)',xFormat:'percent',yFormat:null,xScale:'linear',yScale:'linear',xlim:[start,end],ylim:[ymin,ymax],series}]});
}
const currency=x=>x.toLocaleString('en-GB',{style:'currency',currency:'EUR',minimumFractionDigits:2,maximumFractionDigits:2});
function calculate(){
 const n=name=>Number(form.elements.namedItem(name).value);
 const p={wealth:n('wealth'),mean:n('mean'),sd:n('sd'),alpha:n('alpha')/100,nu:n('nu'),paths:n('paths'),seed:n('seed'),dist:form.elements.namedItem('distribution').value};
 const err=document.getElementById('calc-error');err.textContent='';
 if(!Object.values(p).every(x=>typeof x==='string'||Number.isFinite(x))||p.wealth<1||p.wealth>1e9||Math.abs(p.mean)>100||p.sd<0||p.sd>100||p.alpha<.8||p.alpha>.9999||p.nu<2.05||p.nu>100||!Number.isInteger(p.paths)||p.paths<100||p.paths>200000||!Number.isInteger(p.seed)||p.seed<0||p.seed>4294967295){err.textContent='Enter valid finite inputs within the displayed limits; scenario count and seed must be integers.';return;}
 p.mean=p.wealth*p.mean/100;p.sd=p.wealth*p.sd/100;
 try{
  const rng=random(p.seed),scale=p.sd*Math.sqrt((p.nu-2)/p.nu),sample=new Float64Array(p.paths);
  for(let i=0;i<p.paths;i++)sample[i]=p.mean+(p.dist==='normal'?p.sd*rng.normal():scale*rng.student(p.nu));
  sample.sort();const suffix=suffixSum(sample),ref=analytical(p.alpha,p.mean,p.sd,p.dist,p.nu),est=empirical(sample,p.alpha,suffix);
  ['var','es','sample-var','sample-es'].forEach((id,i)=>document.getElementById('result-'+id).textContent=currency([...ref,...est][i]));
  let breaches=0;for(const v of sample)if(v>est[0])breaches++;
  const tail=p.paths*(1-p.alpha);
  document.getElementById('result-tail').textContent=tail.toLocaleString('en-GB',{maximumFractionDigits:4});
  document.getElementById('result-breaches').textContent=breaches.toLocaleString('en-GB')+' / '+p.paths.toLocaleString('en-GB');
  document.getElementById('result-max').textContent=currency(sample.at(-1));
  render(p,sample,suffix);
  const warning=tail<20?' Only '+tail.toFixed(2)+' scenarios’ worth of tail mass: estimates can be highly unstable.':'';
  document.getElementById('notebook-note').textContent=(p.sd===0?'Deterministic loss: VaR and ES equal the specified mean. ':p.dist==='normal'?'Normal losses with the specified horizon mean and standard deviation. ':'Student-t losses, ν = '+p.nu+', rescaled to the specified standard deviation. ')+p.paths.toLocaleString('en-GB')+' synthetic scenarios; seed '+p.seed+'. Empirical risk uses the inverse CDF and fractional boundary mass. Dashed curves show this one sample, not a confidence interval.'+warning;
 }catch(e){err.textContent=e.message;}
}
form.addEventListener('submit',e=>{e.preventDefault();calculate();});
document.getElementById('reset-inputs').addEventListener('click',()=>{form.reset();calculate();});
document.querySelector('.print-button')?.addEventListener('click',()=>{document.querySelectorAll('details').forEach(e=>e.open=true);window.print();});
const progress=document.querySelector('.reading-progress');
function updateProgress(){if(progress)progress.style.width=(100*scrollY/Math.max(1,document.documentElement.scrollHeight-innerHeight))+'%';}
addEventListener('scroll',updateProgress,{passive:true});addEventListener('resize',updateProgress);updateProgress();
// Exposed pure routines support independent numerical verification of this standalone page.
window.RiskLab={analytical,empirical,suffixSum,Phi,studentCDF,random};
calculate();
})();
