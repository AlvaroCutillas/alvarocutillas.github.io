const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const url=pathToFileURL(path.resolve(__dirname,'../../projects/monte-carlo-option-pricing.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);let panels=0,series=0;
 for(let i=0;i<16;i++){
  const figure=page.locator('figure').nth(i);await figure.locator('svg').scrollIntoViewIfNeeded();
  const axes=await figure.locator('.chart-data').evaluate(el=>JSON.parse(el.textContent).axes.length);
  for(let j=0;j<axes;j++){
   const target=await figure.evaluate((el,j)=>{
    const ax=JSON.parse(el.querySelector('.chart-data').textContent).axes[j],s=ax.series[0];
    const valid=s.points.filter(p=>p[3]>ax.box[1]+1&&p[3]<ax.box[1]+ax.box[3]-1),p=valid[Math.floor(valid.length*.6)];
    const t=new DOMPoint(p[2],p[3]).matrixTransform(el.querySelector('svg').getScreenCTM());
    return {x:t.x,y:t.y,expected:p[1],name:s.label,mode:s.mode,count:ax.series.length};
   },j);
   await page.mouse.move(target.x,target.y);await page.waitForFunction(()=>!document.getElementById('chart-coordinate-tooltip').hidden);
   const tip=await page.locator('#chart-coordinate-tooltip').evaluate(el=>({rows:[...el.querySelectorAll('.chart-tooltip-row')].map(r=>({label:r.querySelector('.chart-tooltip-label').textContent,y:Number(r.querySelector('strong').textContent.replace(/,/g,''))})),box:el.getBoundingClientRect().toJSON(),text:el.textContent}));
   const row=tip.rows.find(r=>r.label===target.name);assert.ok(row,'Figure '+i+', panel '+j);
   assert.ok(Math.abs(row.y-target.expected)<.000061,'Displayed coordinate '+i+'/'+j+': '+row.y+' / '+target.expected);
   assert.ok(tip.box.x>=11&&tip.box.right<=1429&&tip.box.y>=11&&tip.box.bottom<=1089);
   if(target.mode==='step')assert.match(tip.text,/Bin:/);
   panels++;series+=tip.rows.length;
  }
  await figure.screenshot({path:path.join(__dirname,'figure-'+String(i+1).padStart(2,'0')+'.png')});
 }
 await page.locator('#calculate').click();await page.waitForFunction(()=>!document.getElementById('calculate').disabled);
 const live=page.locator('#live-plot svg');await live.scrollIntoViewIfNeeded();await live.focus();await live.press('End');
 const liveText=await page.locator('#chart-coordinate-tooltip').innerText();assert.match(liveText,/20,000/);assert.match(liveText,/BSM reference/);
 await live.press('Escape');assert.ok(!(await page.locator('#chart-coordinate-tooltip').isVisible()));
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});await mobile.goto(url);
 const svg=mobile.locator('figure svg').first();await svg.scrollIntoViewIfNeeded();
 const tap=await svg.evaluate(svg=>{
  const ax=JSON.parse(svg.closest('figure').querySelector('.chart-data').textContent).axes[0],p=ax.series[0].points[50],v=new DOMPoint(p[2],p[3]).matrixTransform(svg.getScreenCTM());
  return {x:v.x,y:v.y};
 });
 await mobile.touchscreen.tap(tap.x,tap.y);await mobile.waitForFunction(()=>!document.getElementById('chart-coordinate-tooltip').hidden);
 const box=await mobile.locator('#chart-coordinate-tooltip').boundingBox();assert.ok(box.x>=11&&box.x+box.width<=379);
 assert.equal(await mobile.locator('.chart-tooltip-row').count(),10);
 await mobile.screenshot({path:path.join(__dirname,'paths-mobile-touch.png')});await mobile.touchscreen.tap(5,70);
 assert.ok(!(await mobile.locator('#chart-coordinate-tooltip').isVisible()));assert.deepEqual(errors,[]);
 const report={figures:16,panels,inspectedSeries:series,coordinates:'passed',histogram:'passed',liveRecalculation:'passed',keyboard:'passed',mobileTouch:'passed',errors};
 fs.writeFileSync(path.join(__dirname,'coordinates-verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
