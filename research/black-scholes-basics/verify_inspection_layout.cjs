const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const path=require('path');
const check=(ok,message)=>{if(!ok)throw Error(message);};
const html='file:///'+path.resolve(__dirname,'../../projects/black-scholes-basics.html').replaceAll('\\','/');
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const results=[];
  for(const [width,height,touch] of [[978,764,false],[1440,1000,false],[390,844,true],[320,844,true]]){
    const page=await browser.newPage({viewport:{width,height},isMobile:touch,hasTouch:touch});
    const errors=[];page.on('pageerror',e=>errors.push(String(e)));
    await page.goto(html);
    const figure=page.locator('figure').nth(2),svg=figure.locator('svg');
    await svg.evaluate(el=>{
      const remember=e=>{el.inspectedClientX=e.clientX;el.inspectedClientY=e.clientY;};
      el.addEventListener('pointermove',remember);el.addEventListener('pointerdown',remember);
    });
    await svg.evaluate(el=>scrollBy(0,el.getBoundingClientRect().top-270));
    let previous=null;
    for(const fraction of [.2,.5,.8]){
      const target=await figure.evaluate((el,fraction)=>{
        const ax=JSON.parse(el.querySelector('.chart-data').textContent).axes[0],i=Math.round((ax.series[0].points.length-1)*fraction),p=ax.series[2].points[i];
        const t=new DOMPoint(p[2],p[3]).matrixTransform(el.querySelector('svg').getScreenCTM());
        return {x:t.x,y:t.y,values:ax.series.map(s=>({label:s.label,value:s.points[i][1]}))};
      },fraction);
      if(touch)await page.touchscreen.tap(target.x,target.y);else await page.mouse.move(target.x,target.y);
      await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
      const expected=await figure.evaluate(el=>{
        const svg=el.querySelector('svg'),ax=JSON.parse(el.querySelector('.chart-data').textContent).axes[0];
        const px=new DOMPoint(svg.inspectedClientX,0).matrixTransform(svg.getScreenCTM().inverse()).x;
        const x=ax.xlim[0]+(px-ax.box[0])*(ax.xlim[1]-ax.xlim[0])/ax.box[2];
        return ax.series.map(s=>{
          let i=s.points.findIndex(p=>p[0]>=x);i=Math.max(1,i);
          const a=s.points[i-1],b=s.points[i],t=(x-a[0])/(b[0]-a[0]);
          return {label:s.label,value:a[1]+t*(b[1]-a[1])};
        });
      });
      const read=await page.locator('.chart-tooltip').evaluate(el=>({
        hidden:el.hidden,box:el.getBoundingClientRect().toJSON(),background:getComputedStyle(el).backgroundColor,
        rows:[...el.querySelectorAll('.chart-tooltip-row')].map(r=>({label:r.querySelector('.chart-tooltip-label').textContent,value:Number(r.querySelector('strong').textContent.replaceAll(',','')),box:r.getBoundingClientRect().toJSON(),overflow:r.scrollWidth>r.clientWidth})),
        columns:getComputedStyle(el.querySelector('.chart-tooltip-rows')).gridTemplateColumns
      }));
      check(!read.hidden,'Inspector must be visible');check(read.rows.length===10,'All ten paths must be shown');
      for(const value of expected){const row=read.rows.find(r=>r.label===value.label);check(row&&Math.abs(row.value-value.value)<.000051,`Every path must show its correct coordinate: ${width}, x=${fraction}, ${value.label}: ${row?.value} vs ${value.value}`);}
      check(read.background==='rgb(20, 20, 22)','Inspector must have an opaque neutral background');
      check(read.box.width<=276&&read.box.height<190,'Ten paths must fit a compact inspector');
      check(!read.rows.some(r=>r.overflow),'Path labels and values must not overflow');
      check(new Set(read.rows.map(r=>r.box.x)).size===2,'Paths must be arranged in two columns');
      check(read.box.left>=11&&read.box.right<=width-11&&read.box.bottom<=height-11,'Inspector must stay inside the viewport');
      const cursor=await svg.evaluate(el=>({x:el.inspectedClientX,y:el.inspectedClientY}));
      const distance=Math.hypot(Math.max(read.box.left-cursor.x,0,cursor.x-read.box.right),Math.max(read.box.top-cursor.y,0,cursor.y-read.box.bottom));
      check(distance<=30,'Inspector must stay beside the cursor');
      if(previous)check(Math.abs(previous.left-read.box.left)+Math.abs(previous.top-read.box.top)>1,'Inspector must follow movement along the curves');
      previous=read.box;
    }
    await page.screenshot({path:path.join(__dirname,`inspection-${width}.png`)});
    const single=page.locator('figure').nth(1).locator('svg');await single.scrollIntoViewIfNeeded();await single.focus();await page.keyboard.press('Home');
    check((await page.locator('.chart-tooltip').boundingBox()).width===220,'Single-panel inspector must be smaller than the previous design');
    check(errors.length===0,'Browser errors: '+errors.join(';'));
    results.push({viewport:width,allPaths:10,coordinates:'passed',twoColumns:'passed',compact:'passed',neutralBackground:'passed',cursorFollowing:'passed'});
    await page.close();
  }
  console.log(JSON.stringify(results));await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
