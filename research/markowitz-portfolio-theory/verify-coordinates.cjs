const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const url=pathToFileURL(path.resolve(__dirname,'../../projects/markowitz-portfolio-theory.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(url);
 let inspected=0;
 for(let i=0;i<16;i++){
  const figure=page.locator('figure').nth(i);await figure.locator('svg').scrollIntoViewIfNeeded();
  const axes=await figure.locator('.chart-data').evaluate(el=>JSON.parse(el.textContent).axes.length);
  for(let j=0;j<axes;j++){
   const target=await figure.evaluate((el,j)=>{
    const ax=JSON.parse(el.querySelector('.chart-data').textContent).axes[j],s=ax.series[0];
    const valid=s.points.filter(p=>p[3]>=ax.box[1]+1&&p[3]<=ax.box[1]+ax.box[3]-1),p=valid[Math.floor(valid.length*.55)];
    const t=new DOMPoint(p[2],p[3]).matrixTransform(el.querySelector('svg').getScreenCTM());
    return {x:t.x,y:t.y,expected:p[1],name:s.label,percent:ax.yFormat==='percent'};
   },j);
   await page.mouse.move(target.x,target.y);await page.waitForFunction(()=>!document.getElementById('chart-coordinate-tooltip').hidden);
   const tip=await page.locator('#chart-coordinate-tooltip').evaluate(el=>({rows:[...el.querySelectorAll('.chart-tooltip-row')].map(r=>({label:r.querySelector('.chart-tooltip-label').textContent,text:r.querySelector('strong').textContent})),box:el.getBoundingClientRect().toJSON()}));
   const row=tip.rows.find(r=>r.label===target.name);assert.ok(row,'Figure '+i);
   let value=Number(row.text.replace(/[% ,]/g,''));if(target.percent){value/=100;assert.match(row.text,/%/);}
   assert.ok(Math.abs(value-target.expected)<.000061,'Hover coordinate mismatch: '+i);
   assert.ok(tip.box.x>=11&&tip.box.right<=1429&&tip.box.y>=11&&tip.box.bottom<=1089);inspected++;
  }
  await figure.screenshot({path:path.join(__dirname,'figure-'+String(i+1).padStart(2,'0')+'.png')});
 }
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();const live=page.locator('#live-plot svg');
 await live.focus();await live.press('Home');assert.ok(await page.locator('#chart-coordinate-tooltip').isVisible());await live.press('ArrowRight');await live.press('Escape');
 assert.ok(!(await page.locator('#chart-coordinate-tooltip').isVisible()));
 await page.locator('[name=mode]').selectOption('longonly');await page.locator('#calculate').click();await live.focus();await live.press('End');
 assert.match(await page.locator('#chart-coordinate-tooltip').innerText(),/Efficient frontier/);
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await mobile.goto(url);
 const svg=mobile.locator('figure svg').first();await svg.scrollIntoViewIfNeeded();const tap=await svg.evaluate(svg=>{
  const ax=JSON.parse(svg.closest('figure').querySelector('.chart-data').textContent).axes[0],p=ax.series[0].points[90];
  const t=new DOMPoint(p[2],p[3]).matrixTransform(svg.getScreenCTM());return {x:t.x,y:t.y};
 });
 await mobile.touchscreen.tap(tap.x,tap.y);await mobile.waitForFunction(()=>!document.getElementById('chart-coordinate-tooltip').hidden);
 assert.equal(await mobile.locator('.chart-tooltip-row').count(),5);const box=await mobile.locator('#chart-coordinate-tooltip').boundingBox();assert.ok(box.x>=11&&box.x+box.width<=379);
 await mobile.screenshot({path:path.join(__dirname,'correlation-mobile-touch.png')});await mobile.touchscreen.tap(5,70);
 assert.ok(!(await mobile.locator('#chart-coordinate-tooltip').isVisible()));assert.deepEqual(errors,[]);
 const report={figures:16,panels:inspected,percentageUnits:'passed',mouseCoordinates:'passed',keyboard:'passed',liveRecalculation:'passed',mobileTouch:'passed',errors};
 fs.writeFileSync(path.join(__dirname,'coordinates-verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
