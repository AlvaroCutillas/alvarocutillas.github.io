(() => {
const colors=['#a7bdb3','#d3ad84','#91a9bd','#7e8d86'];
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
   return {label:s.label,color,mode:panel.snap?'snap':'line',points};
  });
  svg+='<text x="'+(box[0]+box[2]/2)+'" y="'+(box[1]+box[3]+42)+'" fill="#a5ada6" text-anchor="middle" font-size="11">'+panel.x+'</text>';
  const cy=box[1]+box[3]/2;svg+='<text x="18" y="'+cy+'" transform="rotate(-90 18 '+cy+')" fill="#a5ada6" text-anchor="middle" font-size="11">'+panel.y+'</text>';
  axes.push({box,xLabel:panel.x,yLabel:panel.y,xScale:'linear',yScale:'linear',yFormat:panel.percent?'percent':null,xlim:[xmin,xmax],ylim:[ymin,ymax],series});
 });
 svg+='</svg>';const container=document.getElementById(host);container.innerHTML=svg;window.ChartCoordinates.attach(container.querySelector('svg'),{viewBox:[0,0,W,H],axes});
}

window.FactorPlots={draw};
})();