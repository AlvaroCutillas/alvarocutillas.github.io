(() => {
  'use strict';
  const NS='http://www.w3.org/2000/svg';
  const tooltip=document.createElement('div');
  tooltip.className='chart-tooltip';tooltip.id='chart-coordinate-tooltip';tooltip.setAttribute('role','tooltip');tooltip.hidden=true;document.body.append(tooltip);
  const help=document.createElement('p');help.id='chart-coordinate-help';help.className='sr-only';help.textContent='Hover or tap a chart to inspect its curves. With the chart focused, use left and right arrows to inspect points, up and down to change panels, and Escape to dismiss.';document.body.append(help);
  const status=document.createElement('div');status.className='sr-only';status.setAttribute('aria-live','polite');document.body.append(status);
  const instances=new WeakMap();let active=null;
  const node=(tag,attrs={})=>{const el=document.createElementNS(NS,tag);for(const [key,val] of Object.entries(attrs))el.setAttribute(key,val);return el;};
  const finite=Number.isFinite;
  const format=(v,integer=false)=>{
    if(Math.abs(v)<1e-12)v=0;
    if(integer)return v.toLocaleString('en-US',{maximumFractionDigits:0});
    const a=Math.abs(v),digits=a>0&&a<.01?6:4;
    return v.toLocaleString('en-US',{minimumFractionDigits:Math.min(2,digits),maximumFractionDigits:digits});
  };
  function bracket(points,px){
    let lo=0,hi=points.length-1;
    while(hi-lo>1){const mid=(lo+hi)>>1;if(points[mid][2]<=px)lo=mid;else hi=mid;}
    return [lo,hi];
  }
  const scale=(v,lim,kind)=>kind==='log'?(Math.log(v)-Math.log(lim[0]))/(Math.log(lim[1])-Math.log(lim[0])):(v-lim[0])/(lim[1]-lim[0]);
  const unscale=(u,lim,kind)=>kind==='log'?Math.exp(Math.log(lim[0])+u*(Math.log(lim[1])-Math.log(lim[0]))):lim[0]+u*(lim[1]-lim[0]);
  const rawX=(ax,px)=>unscale((px-ax.box[0])/ax.box[2],ax.xlim,ax.xScale);
  const rawY=(ax,py)=>unscale(1-(py-ax.box[1])/ax.box[3],ax.ylim,ax.yScale);
  const pixelY=(ax,y)=>ax.box[1]+ax.box[3]*(1-scale(y,ax.ylim,ax.yScale));
  function pointAt(ax,series,px){
    const points=series.points;
    if(series.mode==='step'){
      const x=rawX(ax,px),bins=series.bins;
      if(x<bins[0]||x>bins[bins.length-1])return null;
      let lo=0,hi=bins.length-1;
      while(hi-lo>1){const mid=(lo+hi)>>1;if(bins[mid]<=x)lo=mid;else hi=mid;}
      const i=Math.min(lo,points.length-1),y=points[i][1];
      return {x,y,px,py:pixelY(ax,y),bin:[bins[i],bins[i+1]],series};
    }
    if(px<points[0][2]-1e-7||px>points[points.length-1][2]+1e-7)return null;
    const [i,j]=bracket(points,px),a=points[i],b=points[j];
    if(series.mode==='snap'){
      const p=Math.abs(a[2]-px)<=Math.abs(b[2]-px)?a:b;
      return {x:p[0],y:p[1],px:p[2],py:p[3],series};
    }
    const t=b[2]===a[2]?0:Math.max(0,Math.min(1,(px-a[2])/(b[2]-a[2]))),py=a[3]+t*(b[3]-a[3]);
    return {x:rawX(ax,px),y:rawY(ax,py),px,py,series};
  }
  function hide(){
    if(active){active.overlay.replaceChildren();active.svg.classList.remove('is-inspecting');active.pinned=false;}
    tooltip.hidden=true;active=null;
  }
  function tooltipContent(ax,values,nearest,x,bin){
    const integer=/Tree steps|Simulation paths/.test(ax.xLabel);
    const header=document.createElement('div');header.className='chart-tooltip-header';
    const label=document.createElement('span');label.textContent=ax.xLabel;
    const value=document.createElement('strong');value.textContent=format(x,integer);header.append(label,value);
    const unit=document.createElement('div');unit.className='chart-tooltip-unit';unit.textContent=ax.yLabel;
    const rows=document.createElement('div');rows.className='chart-tooltip-rows';
    const many=values.length>4;
    tooltip.classList.toggle('has-many-series',many);
    if(many)rows.style.setProperty('--series-rows',Math.ceil(values.length/2));
    for(const item of values){
      const row=document.createElement('div');row.className='chart-tooltip-row'+(item===nearest?' is-nearest':'');
      const swatch=document.createElement('span');swatch.className='chart-tooltip-swatch';swatch.style.background=item.series.color;
      const name=document.createElement('span');name.className='chart-tooltip-label';name.textContent=item.series.label;
      const number=document.createElement('strong');number.textContent=format(item.y);row.append(swatch,name,number);rows.append(row);
    }
    tooltip.replaceChildren(header,unit,rows);
    if(bin){const note=document.createElement('div');note.className='chart-tooltip-foot';note.textContent='Bin: '+format(bin[0])+' to '+format(bin[1]);tooltip.append(note);}
  }
  function place(clientX,clientY){
    tooltip.hidden=false;
    const {width,height}=tooltip.getBoundingClientRect(),margin=12;
    let x=clientX+20,y=clientY+18;
    if(x+width>innerWidth-margin)x=clientX-width-20;
    if(y+height>innerHeight-margin)y=clientY-height-18;
    tooltip.style.left=Math.max(margin,Math.min(innerWidth-width-margin,x))+'px';
    tooltip.style.top=Math.max(margin,Math.min(innerHeight-height-margin,y))+'px';
  }
  function attach(svg,data){
    if(!svg||!data?.axes?.length||instances.has(svg))return;
    const overlay=node('g',{'class':'chart-inspection-overlay','pointer-events':'none','aria-hidden':'true'});svg.append(overlay);
    const controller={svg,data,overlay,pinned:false,axisIndex:0,index:0};instances.set(svg,controller);
    svg.classList.add('has-coordinate-reader');svg.setAttribute('tabindex','0');
    svg.setAttribute('aria-describedby',(svg.getAttribute('aria-describedby')||'')+' chart-coordinate-help');
    function render(ax,px,py,clientX,clientY,keyboard=false){
      if(active!==controller){hide();active=controller;}svg.classList.add('is-inspecting');
      const snap=ax.series.find(s=>s.mode==='snap');
      if(snap){const point=pointAt(ax,snap,px);if(point)px=point.px;}
      const values=ax.series.map(s=>pointAt(ax,s,px)).filter(p=>p&&finite(p.y)&&p.py>=ax.box[1]-.1&&p.py<=ax.box[1]+ax.box[3]+.1);
      if(!values.length){hide();return;}
      const nearest=values.reduce((a,b)=>Math.abs(a.py-py)<=Math.abs(b.py-py)?a:b);
      const shown=values;
      const guide=node('line',{x1:px,x2:px,y1:ax.box[1],y2:ax.box[1]+ax.box[3],stroke:'#a1a1aa','stroke-width':1,'stroke-opacity':.46,'stroke-dasharray':'3 5','vector-effect':'non-scaling-stroke'});
      overlay.replaceChildren(guide);
      for(const point of shown){
        overlay.append(node('circle',{cx:point.px,cy:point.py,r:point===nearest?4:2.5,fill:'#101114',stroke:point.series.color,'stroke-width':point===nearest?2:1.5,'vector-effect':'non-scaling-stroke'}));
        if(point===nearest)overlay.append(node('circle',{cx:point.px,cy:point.py,r:1.5,fill:'#f4f4f5'}));
      }
      tooltipContent(ax,shown,nearest,nearest.x,nearest.bin);place(clientX,clientY);
      if(keyboard)status.textContent=ax.xLabel+' '+format(nearest.x)+'. '+shown.map(p=>p.series.label+' '+format(p.y)).join('; ');
    }
    function inspect(event){
      const matrix=svg.getScreenCTM();if(!matrix)return;
      const p=new DOMPoint(event.clientX,event.clientY).matrixTransform(matrix.inverse());
      const axisIndex=data.axes.findIndex(ax=>p.x>=ax.box[0]&&p.x<=ax.box[0]+ax.box[2]&&p.y>=ax.box[1]&&p.y<=ax.box[1]+ax.box[3]);
      if(axisIndex<0){if(!controller.pinned)hide();return;}
      controller.axisIndex=axisIndex;render(data.axes[axisIndex],p.x,p.y,event.clientX,event.clientY);
    }
    let pending=null,frame=0;
    svg.addEventListener('pointermove',event=>{
      if(event.pointerType!=='touch')controller.pinned=false;
      pending={clientX:event.clientX,clientY:event.clientY};
      if(!frame)frame=requestAnimationFrame(()=>{frame=0;if(pending){const point=pending;pending=null;inspect(point);}});
    });
    svg.addEventListener('pointerdown',event=>{inspect(event);controller.pinned=event.pointerType==='touch';});
    svg.addEventListener('pointerleave',event=>{pending=null;if(event.pointerType!=='touch'&&!controller.pinned&&active===controller)hide();});
    svg.addEventListener('pointercancel',()=>{pending=null;if(active===controller)hide();});
    svg.addEventListener('blur',()=>{if(active===controller&&!controller.pinned)hide();});
    svg.addEventListener('keydown',event=>{
      if(event.key==='Escape'){hide();return;}
      if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(event.key))return;
      event.preventDefault();
      if(event.key==='ArrowUp')controller.axisIndex=(controller.axisIndex-1+data.axes.length)%data.axes.length;
      if(event.key==='ArrowDown')controller.axisIndex=(controller.axisIndex+1)%data.axes.length;
      const ax=data.axes[controller.axisIndex],points=ax.series.find(s=>s.mode==='snap')?.points||ax.series[0].points;
      if(active!==controller)controller.index=Math.floor(points.length/2);
      if(event.key==='ArrowRight')controller.index++;
      if(event.key==='ArrowLeft')controller.index--;
      if(event.key==='Home')controller.index=0;
      if(event.key==='End')controller.index=points.length-1;
      controller.index=Math.max(0,Math.min(points.length-1,controller.index));
      const p=points[controller.index],screen=new DOMPoint(p[2],p[3]).matrixTransform(svg.getScreenCTM());
      render(ax,p[2],p[3],screen.x,screen.y,true);
    });
  }
  document.addEventListener('pointerdown',event=>{if(active&&!active.svg.contains(event.target))hide();});
  addEventListener('scroll',hide,{passive:true,capture:true});addEventListener('resize',hide);
  addEventListener('beforeprint',hide);
  for(const el of document.querySelectorAll('figure .chart-data'))attach(el.closest('figure').querySelector('svg'),JSON.parse(el.textContent));
  window.ChartCoordinates={attach,hide};
})();
