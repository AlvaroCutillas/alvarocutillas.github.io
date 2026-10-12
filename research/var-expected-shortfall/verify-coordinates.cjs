const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const url=pathToFileURL(path.resolve(__dirname,'../../projects/var-expected-shortfall.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});
 await page.goto(url);let panels=0;
 for(let i=0;i<17;i++){
  const figure=page.locator('figure').nth(i);await figure.locator('svg').scrollIntoViewIfNeeded();
  const axes=await figure.locator('.chart-data').evaluate(el=>JSON.parse(el.textContent).axes.length);
  for(let j=0;j<axes;j++){
   const target=await figure.evaluate((el,j)=>{
    const ax=JSON.parse(el.querySelector('.chart-data').textContent).axes[j],s=ax.series[0];
    const valid=s.points.filter(p=>p[3]>=ax.box[1]+1&&p[3]<=ax.box[1]+ax.box[3]-1),p=valid[Math.floor(valid.length*.55)];
    const t=new DOMPoint(p[2],p[3]).matrixTransform(el.querySelector('svg').getScreenCTM());
    return {x:t.x,y:t.y,expected:p[1],name:s.label,percent:ax.yFormat==='percent'};
   },j);
   await page.mouse.move(target.x,target.y);
   await page.waitForFunction(()=>!document.getElementById('chart-coordinate-tooltip').hidden);
   const tip=await page.locator('#chart-coordinate-tooltip').evaluate(el=>({rows:[...el.querySelectorAll('.chart-tooltip-row')].map(r=>({label:r.querySelector('.chart-tooltip-label').textContent,text:r.querySelector('strong').textContent})),box:el.getBoundingClientRect().toJSON(),background:getComputedStyle(el).backgroundColor}));
   const row=tip.rows.find(r=>r.label===target.name);assert.ok(row,'Figure '+i);
   let value=Number(row.text.replace(/[% ,]/g,''));if(target.percent){value/=100;assert.match(row.text,/%/);}
   assert.ok(Math.abs(value-target.expected)<.000061,'Hover coordinate mismatch '+i+' '+value+' vs '+target.expected);
   assert.equal(tip.background,'rgb(20, 20, 22)');assert.ok(tip.box.x>=11&&tip.box.right<=1429&&tip.box.y>=11&&tip.box.bottom<=1089);panels++;
  }
  await figure.screenshot({path:path.join(__dirname,'verified-figure-'+String(i+1).padStart(2,'0')+'.png')});
 }
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();
 await page.locator('#live-plot svg').focus();await page.keyboard.press('End');
 assert.equal(await page.locator('.chart-tooltip-row').count(),4);await page.screenshot({path:path.join(__dirname,'laboratory-hover.png')});
 await page.keyboard.press('Escape');assert.ok(!(await page.locator('#chart-coordinate-tooltip').isVisible()));
 fs.writeFileSync(path.join(__dirname,'coordinates-verification.json'),JSON.stringify({panels,coordinateAccuracy:'passed',percentUnits:'passed',compactNeutralCard:'passed',allFourLaboratorySeries:'passed'},null,2));
 console.log('24 chart panels: coordinate accuracy, percentage units, card bounds, four-series laboratory hover passed');await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
