(() => {
'use strict';
const data=JSON.parse(document.getElementById('factor-dataset').textContent),F=data.factors,form=document.getElementById('factor-form'),sortForm=document.getElementById('sort-form');
const names=data.names,styleNames=names.slice(1),draw=window.FactorPlots.draw;
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
const pct=x=>x===null?'Undefined':(100*x).toFixed(3)+'%',dec=(x,d=5)=>x===null?'Undefined':Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
function regression(X,y,lags=6){
 const n=X.length,k=X[0].length,Q=[],R=Array.from({length:k},()=>Array(k).fill(0));
 if(n<=k)throw Error('Regression needs more observations than coefficients.');
 for(let j=0;j<k;j++){
  const v=X.map(r=>r[j]),orig=Math.hypot(...v);
  for(let pass=0;pass<2;pass++)for(let i=0;i<j;i++){const r=dot(v,Q[i]);R[i][j]+=r;for(let h=0;h<n;h++)v[h]-=r*Q[i][h];}
  const norm=Math.hypot(...v);if(norm<1e-10*Math.max(1,orig))throw Error('The regression design is rank deficient.');
  R[j][j]=norm;Q.push(v.map(x=>x/norm));
 }
 const b=Array(k).fill(0),qy=Q.map(q=>dot(q,y));
 for(let j=k-1;j>=0;j--){let v=qy[j];for(let h=j+1;h<k;h++)v-=R[j][h]*b[h];b[j]=v/R[j][j];}
 const invR=Array.from({length:k},()=>Array(k).fill(0));
 for(let col=0;col<k;col++)for(let j=k-1;j>=0;j--){let v=j===col?1:0;for(let h=j+1;h<k;h++)v-=R[j][h]*invR[h][col];invR[j][col]=v/R[j][j];}
 const bread=Array.from({length:k},(_,i)=>Array.from({length:k},(_,j)=>dot(invR[i],invR[j])));
 const pred=X.map(r=>dot(r,b)),e=y.map((v,i)=>v-pred[i]),scores=X.map((r,i)=>r.map(v=>v*e[i]));
 const meat=Array.from({length:k},()=>Array(k).fill(0));
 for(let i=0;i<k;i++)for(let j=0;j<k;j++){
  let v=0;for(let t=0;t<n;t++)v+=scores[t][i]*scores[t][j];
  for(let lag=1;lag<=lags;lag++){let cross=0;for(let t=lag;t<n;t++)cross+=scores[t][i]*scores[t-lag][j]+scores[t][j]*scores[t-lag][i];v+=(1-lag/(lags+1))*cross;}
  meat[i][j]=v;
 }
 const sse=dot(e,e),ym=mean(y),sst=y.reduce((s,v)=>s+(v-ym)**2,0);
 const classic_se=b.map((_,i)=>Math.sqrt(Math.max(0,bread[i][i]*sse/(n-k))));
 const hac_se=b.map((_,i)=>{let v=0;for(let a=0;a<k;a++)for(let c=0;c<k;c++)v+=bread[i][a]*meat[a][c]*bread[c][i];return Math.sqrt(Math.max(0,v*n/(n-k)));});
 return {b,pred,e,classic_se,hac_se,r2:sst>1e-24?1-sse/sst:null};
}
function covariance(rows){
 const k=rows[0].length,m=Array.from({length:k},(_,j)=>mean(rows.map(r=>r[j])));
 return Array.from({length:k},(_,i)=>Array.from({length:k},(_,j)=>rows.reduce((s,r)=>s+(r[i]-m[i])*(r[j]-m[j]),0)/(rows.length-1)));
}
function analyze(o){
 const beta=[o.market,o.value,o.momentum,o.quality,o.lowvol],y=F.map((r,i)=>o.alpha/1e4+dot(r,beta)+data.epsilon[i]*o.noise/2);
 const used=o.model==='capm'?F.map(r=>[r[0]]):F,X=used.map(r=>[1,...r]),fit=regression(X.slice(0,o.train),y.slice(0,o.train),o.lags);
 const pred=X.map(r=>dot(r,fit.b)),residual=y.map((v,i)=>v-pred[i]),S=covariance(used.slice(0,o.train)),b=fit.b.slice(1),sb=S.map(r=>dot(r,b));
 const system=dot(b,sb),specific=dot(fit.e,fit.e)/(o.train-1),variance=system+specific,contributions=b.map((v,i)=>v*sb[i]).concat(specific);
 const rmse=Math.sqrt(mean(residual.slice(o.train).map(v=>v*v))),testMean=mean(residual.slice(o.train));
 return {o,...fit,y,predAll:pred,residual,covariance:S,system,specific,variance,contributions,volatility:Math.sqrt(Math.max(0,variance)),rmse,testMean};
}
function correlation(x,y){const mx=mean(x),my=mean(y),xc=x.map(v=>v-mx),yc=y.map(v=>v-my),den=Math.sqrt(dot(xc,xc)*dot(yc,yc));return den>1e-20?dot(xc,yc)/den:null;}
function ranks(x){
 const sorted=x.map((v,i)=>({v,i})).sort((a,b)=>a.v-b.v||a.i-b.i),r=Array(x.length);
 for(let i=0;i<x.length;){let j=i+1;while(j<x.length&&sorted[j].v===sorted[i].v)j++;const rank=(i+j-1)/2+1;for(let h=i;h<j;h++)r[sorted[h].i]=rank;i=j;}
 return r;
}
function crossSection(o){
 const stocks=data.stocks,n=stocks.length,weights=Array(n).fill(0),balanced=o.neutral==='balanced';
 const groups=balanced?[0,1,2,3].map(s=>stocks.map((r,i)=>r.sector===s?i:null).filter(i=>i!==null)):[stocks.map((_,i)=>i)];
 for(const g of groups){const sorted=[...g].sort((a,b)=>stocks[a].z[o.signal]-stocks[b].z[o.signal]||a-b),k=Math.round(g.length*o.tail/100);if(k<1)throw Error('Each tail must contain at least one stock.');
  sorted.slice(-k).forEach(i=>weights[i]=1/(groups.length*k));sorted.slice(0,k).forEach(i=>weights[i]=-1/(groups.length*k));}
 const y=stocks.map(r=>r.next),score=stocks.map(r=>r.z[o.signal]),gross=dot(weights,y),turnover=weights.reduce((s,v)=>s+Math.abs(v),0);
 const order=stocks.map((_,i)=>i).sort((a,b)=>score[a]-score[b]||a-b),deciles=Array.from({length:10},(_,d)=>mean(order.slice(d*16,(d+1)*16).map(i=>y[i])));
 const exposure=styleNames.map((_,j)=>dot(weights,stocks.map(r=>r.z[j]))),sectorNet=[0,1,2,3].map(s=>weights.reduce((v,w,i)=>v+(stocks[i].sector===s?w:0),0));
 return {o,weights,gross,net:gross-o.cost/1e4*turnover,turnover,deciles,exposure,sectorNet,ic:correlation(score,y),rankIC:correlation(ranks(score),ranks(y))};
}
let last=null,lastSort=null;
function read(){
 const o={model:form.elements.model.value};
 for(const k of ['train','lags','market','value','momentum','quality','lowvol','alpha','noise']){o[k]=Number(form.elements[k].value);if(!Number.isFinite(o[k]))throw Error('Every input must be finite.');}
 if(!Number.isInteger(o.train)||o.train<60||o.train>228)throw Error('Training months must be an integer from 60 to 228.');
 if(!Number.isInteger(o.lags)||o.lags<0||o.lags>12)throw Error('HAC lags must be an integer from 0 to 12.');
 return o;
}
function tstat(b,se){return se>1e-12?b/se:null;}
function build(){
 try{
  window.ChartCoordinates.hide();const a=analyze(read()),o=a.o,k=a.b.length,terms=['Alpha',...(o.model==='capm'?[names[0]]:names)];
  document.getElementById('result-alpha').textContent=dec(a.b[0]*1e4,3)+' bp';
  document.getElementById('result-t').textContent=dec(tstat(a.b[0],a.hac_se[0]),3);
  document.getElementById('result-r2').textContent=a.r2===null?'Undefined':dec(a.r2,4);
  document.getElementById('result-rmse').textContent=pct(a.rmse);
  document.getElementById('result-vol').textContent=pct(a.volatility);
  document.getElementById('result-share').textContent=pct(a.variance>1e-24?a.system/a.variance:null);
  document.getElementById('result-mean').textContent=dec(a.testMean*1e4,3)+' bp';
  document.querySelector('#coefficient-table tbody').innerHTML=terms.map((term,j)=>{const mult=j===0?1e4:1,unit=j===0?' bp':'';return '<tr><th scope="row">'+term+'</th><td class="num">'+dec(a.b[j]*mult)+unit+'</td><td class="num">'+dec(a.classic_se[j]*mult)+unit+'</td><td class="num">'+dec(a.hac_se[j]*mult)+unit+'</td><td class="num">'+dec(tstat(a.b[j],a.hac_se[j]),3)+'</td></tr>';}).join('');
  document.getElementById('model-status').textContent='OLS on months 1–'+o.train+'; months '+(o.train+1)+'–240 withheld. '+k+' coefficients including an intercept. HAC lag '+o.lags+' with Bartlett weights and T/(T−p) adjustment. Changing bandwidth changes uncertainty, not coefficients. Model coefficients are frozen before holdout evaluation.';
  const months=Array.from({length:240-o.train},(_,i)=>i+o.train+1);let cy=0,cp=0;
  const cumY=[],cumP=[];months.forEach(m=>{cy+=a.y[m-1];cp+=a.predAll[m-1];cumY.push([m,cy]);cumP.push([m,cp]);});
  draw('live-plot',[{title:'Withheld monthly excess returns',x:'Synthetic month',snap:true,y:'Monthly excess return',percent:true,series:[{label:'Observed excess return',xy:months.map(m=>[m,a.y[m-1]])},{label:'Model attribution',xy:months.map(m=>[m,a.predAll[m-1]])}]},
   {title:'Withheld cumulative arithmetic return',x:'Synthetic month',snap:true,y:'Cumulative arithmetic return',percent:true,series:[{label:'Observed cumulative',xy:cumY},{label:'Attributed cumulative',xy:cumP}]}],'Chronological holdout attribution');
  const riskNames=[...terms.slice(1),'Residual'];
  document.querySelector('#risk-table tbody').innerHTML=riskNames.map((name,j)=>'<tr><th scope="row">'+name+'</th><td class="num">'+dec(a.contributions[j],8)+'</td><td class="num">'+pct(a.variance>1e-24?a.contributions[j]/a.variance:null)+'</td></tr>').join('');
  document.getElementById('calc-error').textContent='';last=a;
 }catch(e){document.getElementById('calc-error').textContent=e.message;}
}
function buildSort(){
 try{
  const o={signal:Number(sortForm.elements.signal.value),tail:Number(sortForm.elements.tail.value),neutral:sortForm.elements.neutral.value,cost:Number(sortForm.elements.cost.value)};
  if(!Number.isFinite(o.cost)||o.cost<0||o.cost>100)throw Error('Entry cost must be between 0 and 100 basis points.');
  const s=crossSection(o);window.ChartCoordinates.hide();
  for(const [id,value] of [['gross',pct(s.gross)],['net',pct(s.net)],['ic',dec(s.ic,4)],['rank',dec(s.rankIC,4)]])document.getElementById('sort-'+id).textContent=value;
  document.getElementById('sort-status').textContent=styleNames[o.signal]+' score; '+o.tail+'% tails. '+s.weights.filter(w=>w>0).length+' long and '+s.weights.filter(w=>w<0).length+' short stocks. Gross exposure '+dec(s.turnover,2)+', net weight '+dec(s.weights.reduce((a,b)=>a+b,0),6)+'. '+(o.neutral==='balanced'?'Weights are balanced inside each sector.':'Dollar-neutral weights can retain sector bets.')+' Entry cost '+dec(o.cost/1e4*s.turnover*1e4,2)+' bp. IC uses the full 160-stock cross-section.';
  draw('sort-plot',[{title:'Realized returns sorted by '+styleNames[o.signal]+' score',x:'Signal decile',snap:true,y:'Mean next-month return',percent:true,series:[{label:'Decile mean return',xy:s.deciles.map((r,i)=>[i+1,r])}]}],'Formation-score decile outcomes');
  document.querySelector('#sort-exposure tbody').innerHTML=[...styleNames.map((name,j)=>[name+' score',dec(s.exposure[j],5)]),...[0,1,2,3].map((j)=>['Sector '+String.fromCharCode(65+j)+' net weight',pct(s.sectorNet[j])])].map(r=>'<tr><th scope="row">'+r[0]+'</th><td class="num">'+r[1]+'</td></tr>').join('');
  document.getElementById('sort-error').textContent='';lastSort=s;
 }catch(e){document.getElementById('sort-error').textContent=e.message;}
}
form.addEventListener('submit',e=>{e.preventDefault();build();});
sortForm.addEventListener('submit',e=>{e.preventDefault();buildSort();});
document.getElementById('reset-inputs').addEventListener('click',()=>{form.reset();sortForm.reset();build();buildSort();});
function csvDownload(text,name){const url=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
document.getElementById('download-returns').addEventListener('click',()=>{if(!last)return;const a=last;
 const header='synthetic_month,role,market_decimal,value_decimal,momentum_decimal,quality_decimal,lowvol_decimal,portfolio_excess_decimal,attributed_decimal,residual_decimal';
 csvDownload(header+'\n'+F.map((r,i)=>[i+1,i<a.o.train?'training':'withheld',...r,a.y[i],a.predAll[i],a.residual[i]].join(',')).join('\n')+'\n','factor-attribution.csv');
});
document.getElementById('download-stocks').addEventListener('click',()=>{if(!lastSort)return;
 const header='stock_id,sector,value_score,momentum_score,quality_score,lowvol_score,next_return_decimal,portfolio_weight';
 csvDownload(header+'\n'+data.stocks.map((r,i)=>[r.id,String.fromCharCode(65+r.sector),...r.z,r.next,lastSort.weights[i]].join(',')).join('\n')+'\n','factor-stock-sort.csv');
});
window.FactorLab={regression,covariance,analyze,crossSection,correlation,ranks,data,get last(){return last;},get sort(){return lastSort;}};
document.querySelector('.print-button').addEventListener('click',()=>print());let printed=[];
addEventListener('beforeprint',()=>{printed=[...document.querySelectorAll('details')].map(e=>[e,e.open]);printed.forEach(([e])=>e.open=true);});
addEventListener('afterprint',()=>{printed.forEach(([e,open])=>e.open=open);printed=[];});
const progress=document.querySelector('.reading-progress');function update(){const total=document.documentElement.scrollHeight-innerHeight;progress.style.width=(total>0?100*scrollY/total:0)+'%';}
addEventListener('scroll',update,{passive:true});addEventListener('resize',update);build();buildSort();update();
})();
