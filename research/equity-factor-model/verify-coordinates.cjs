const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const url=pathToFileURL(path.resolve(__dirname,'../../projects/equity-factor-model.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});await page.goto(url);let panels=0;
 for(let i=0;i<19;i++){
  const figure=page.locator('figure').nth(i);await figure.locator('svg').scrollIntoViewIfNeeded();
  const count=await figure.locator('.chart-data').evaluate(el=>JSON.parse(el.textContent).axes.length);
  for(let j=0;j<count;j++){
   const target=await figure.evaluate((el,j)=>{
    const ax=JSON.parse(el.querySelector('.chart-data').textContent).axes[j],s=ax.series[0],reference=ax.series.find(s=>s.mode==='markers')||s;
    const valid=reference.points.filter(p=>p[3]>=ax.box[1]+1&&p[3]<=ax.box[1]+ax.box[3]-1),p=valid[Math.floor(valid.length*.55)];
    const left=s.points.filter(q=>q[2]<=p[2]+1e-8).at(-1),right=s.points.find(q=>q[2]>=p[2]-1e-8);
    const weight=right[2]===left[2]?0:(p[2]-left[2])/(right[2]-left[2]);
    const expected=ax.yScale==='log'?Math.exp(Math.log(left[1])+weight*(Math.log(right[1])-Math.log(left[1]))):left[1]+weight*(right[1]-left[1]);
    const t=new DOMPoint(p[2],p[3]).matrixTransform(el.querySelector('svg').getScreenCTM());
    return {x:t.x,y:t.y,expected,name:s.label,percent:ax.yFormat==='percent',series:ax.series.filter(s=>s.mode!=='markers'||s.points.some(q=>Math.abs(q[2]-p[2])<1e-5)).length};
   },j);
   await page.mouse.move(target.x,target.y);await page.waitForFunction(()=>!document.getElementById('chart-coordinate-tooltip').hidden);
   const tip=await page.locator('#chart-coordinate-tooltip').evaluate(el=>({rows:[...el.querySelectorAll('.chart-tooltip-row')].map(r=>({label:r.querySelector('.chart-tooltip-label').textContent,text:r.querySelector('strong').textContent})),box:el.getBoundingClientRect().toJSON(),background:getComputedStyle(el).backgroundColor}));
   const row=tip.rows.find(r=>r.label===target.name);assert.ok(row,'Missing curve '+i);
   let value=Number(row.text.replace(/[% ,]/g,''));if(target.percent){value/=100;assert.match(row.text,/%/);}
   assert.ok(Math.abs(value-target.expected)<.000061,'Mismatch '+i+': '+value+' vs '+target.expected);
   assert.equal(tip.rows.length,target.series);assert.equal(tip.background,'rgb(20, 20, 22)');assert.ok(tip.box.x>=11&&tip.box.right<=1429&&tip.box.y>=11&&tip.box.bottom<=1089);panels++;
  }
  await figure.screenshot({path:path.join(__dirname,'verified-figure-'+String(i+1).padStart(2,'0')+'.png')});
 }
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();await page.locator('#live-plot svg').focus();await page.keyboard.press('End');
 assert.equal(await page.locator('#chart-coordinate-tooltip .chart-tooltip-row').count(),2);await page.screenshot({path:path.join(__dirname,'laboratory-hover.png')});await page.keyboard.press('Escape');
 await page.locator('#input-model').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(__dirname,'controls-desktop.png')});
 await page.locator('.eq').nth(22).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(__dirname,'formula-detail.png')});
 const touch=await browser.newContext({viewport:{width:390,height:844},hasTouch:true});const mobile=await touch.newPage();await mobile.goto(url);
 await mobile.locator('#sort-plot svg').scrollIntoViewIfNeeded();
 const point=await mobile.locator('#sort-plot svg').evaluate(svg=>{const p=new DOMPoint(120,110).matrixTransform(svg.getScreenCTM());return {x:p.x,y:p.y};});
 await mobile.touchscreen.tap(point.x,point.y);assert.ok(await mobile.locator('#chart-coordinate-tooltip').isVisible());assert.equal(await mobile.locator('#chart-coordinate-tooltip .chart-tooltip-row').count(),1);
 await mobile.screenshot({path:path.join(__dirname,'touch-inspection.png')});await mobile.touchscreen.tap(15,100);assert.ok(!(await mobile.locator('#chart-coordinate-tooltip').isVisible()));
 await mobile.locator('#input-model').scrollIntoViewIfNeeded();await mobile.screenshot({path:path.join(__dirname,'controls-mobile.png')});
 fs.writeFileSync(path.join(__dirname,'coordinates-verification.json'),JSON.stringify({panels,coordinateAccuracy:'passed',percentUnits:'passed',neutralCardAndBounds:'passed',allSeries:'passed',keyboardAndTouch:'passed'},null,2));
 console.log(panels+' chart panels: coordinate accuracy, units, all-series inspection, keyboard and touch passed');await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
