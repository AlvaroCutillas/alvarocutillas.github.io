const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const path=require('path');
const check=(condition,message)=>{if(!condition)throw Error(message);};
const html='file:///'+path.resolve(__dirname,'../../projects/black-scholes-basics.html').replaceAll('\\','/');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(html);check(await page.locator('figure svg.has-coordinate-reader').count()===13,'All static figures must be interactive');
 let inspected=0;
 for(let i=0;i<13;i++){
  const figure=page.locator('figure').nth(i),svg=figure.locator('svg');await svg.scrollIntoViewIfNeeded();
  const count=await figure.locator('.chart-data').evaluate(el=>JSON.parse(el.textContent).axes.length);
  for(let j=0;j<count;j++){
   const target=await figure.evaluate((el,j)=>{
    const ax=JSON.parse(el.querySelector('.chart-data').textContent).axes[j],series=ax.series[0];
    const valid=series.points.filter(p=>p[3]>=ax.box[1]+2&&p[3]<=ax.box[1]+ax.box[3]-2),p=valid[Math.floor(valid.length/2)];
    const xy=new DOMPoint(p[2],p[3]).matrixTransform(el.querySelector('svg').getScreenCTM());return {clientX:xy.x,clientY:xy.y,x:p[0],y:p[1],label:series.label,xLabel:ax.xLabel,mode:series.mode};
   },j);
   await page.mouse.move(target.clientX,target.clientY);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));await page.waitForFunction(()=>!document.querySelector('.chart-tooltip').hidden);
   const read=await page.locator('.chart-tooltip').evaluate(el=>({label:el.querySelector('.is-nearest .chart-tooltip-label').textContent,value:el.querySelector('.is-nearest strong').textContent,x:el.querySelector('.chart-tooltip-header strong').textContent,text:el.textContent,rows:[...el.querySelectorAll('.chart-tooltip-row')].map(r=>({label:r.querySelector('.chart-tooltip-label').textContent,value:r.querySelector('strong').textContent})),box:el.getBoundingClientRect().toJSON()}));
   const row=read.rows.find(r=>r.label===target.label);
   check(row||read.label===target.label,`Curve not identified in figure ${i}, panel ${j}: ${read.label} vs ${target.label}`);
   const value=Number((row?.value||read.value).replaceAll(',',''));
   check(Math.abs(value-target.y)<.000061,`Coordinate mismatch: ${value} vs ${target.y}`);
   check(read.box.x>=11&&read.box.right<=1440-11&&read.box.y>=11&&read.box.bottom<=1100-11,'Tooltip must fit the viewport');
   inspected++;
   if(i===4&&j===1)await page.screenshot({path:path.join(__dirname,'hover-gamma.png')});
   if(i===2&&j===0)await page.screenshot({path:path.join(__dirname,'hover-gbm.png')});
   if(target.mode==='step')check(read.text.includes('Bin:'),'Histogram bin context');
  }
 }
 await page.mouse.move(0,0);check(await page.locator('.chart-tooltip').evaluate(el=>el.hidden),'Tooltip hides on leave');
 const plot=page.locator('figure').filter({has:page.locator('#convergence-title')}).locator('svg');
 await plot.scrollIntoViewIfNeeded();await plot.focus();await page.keyboard.press('Home');await page.waitForFunction(()=>!document.querySelector('.chart-tooltip').hidden);check((await page.locator('.chart-tooltip-header strong').textContent())==='25','Log-axis keyboard reads an actual observation');
 await page.keyboard.press('ArrowRight');check((await page.locator('.chart-tooltip-header strong').textContent())==='50','Keyboard moves to next observation');await page.keyboard.press('Escape');check(await page.locator('.chart-tooltip').evaluate(el=>el.hidden),'Escape dismisses');
 await page.locator('#pricing-notebook').scrollIntoViewIfNeeded();await page.locator('#input-yield').fill('2');await page.locator('#calculate').click();const live=page.locator('#live-plot svg');await live.scrollIntoViewIfNeeded();await live.focus();await page.keyboard.press('Home');check((await page.locator('.chart-tooltip').textContent()).includes('European call'),'Notebook reader survives recalculation');
 await page.locator('#input-kind').selectOption('put');await page.locator('#calculate').click();await page.locator('#live-plot svg').scrollIntoViewIfNeeded();await page.locator('#live-plot svg').focus();await page.keyboard.press('ArrowRight');check((await page.locator('.chart-tooltip').textContent()).includes('European put'),'Reader updates selected option');
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await mobile.goto(html);
 const mobileSvg=mobile.locator('figure svg').first();await mobileSvg.scrollIntoViewIfNeeded();
 const tap=await mobileSvg.evaluate(svg=>{const ax=JSON.parse(svg.closest('figure').querySelector('.chart-data').textContent).axes[0],p=ax.series[0].points[220],t=new DOMPoint(p[2],p[3]).matrixTransform(svg.getScreenCTM());return {x:t.x,y:t.y};});
 await mobile.touchscreen.tap(tap.x,tap.y);await mobile.waitForFunction(()=>!document.querySelector('.chart-tooltip').hidden);const mobileBox=await mobile.locator('.chart-tooltip').boundingBox();check(mobileBox.x>=11&&mobileBox.x+mobileBox.width<=379,'Touch tooltip stays on screen');await mobile.screenshot({path:path.join(__dirname,'hover-mobile.png')});
 await mobile.touchscreen.tap(5,70);check(await mobile.locator('.chart-tooltip').evaluate(el=>el.hidden),'Outside tap dismisses');
 check(errors.length===0,'Browser errors: '+errors.join(';'));
 console.log(JSON.stringify({staticFigures:13,inspectedPanels:inspected,mouse:'passed',sampledValues:'passed',logarithmicAxes:'passed',histogramBins:'passed',keyboard:'passed',notebookRecalculation:'passed',mobileTouch:'passed',browserErrors:errors}));await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
