const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const url=pathToFileURL(path.resolve(__dirname,'../../projects/implied-volatility-surface.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});
 await page.goto(url);let panels=0;
 for(let i=0;i<19;i++){
  const figure=page.locator('figure').nth(i);await figure.locator('svg').scrollIntoViewIfNeeded();
  const axes=await figure.locator('.chart-data').evaluate(el=>JSON.parse(el.textContent).axes.length);
  for(let j=0;j<axes;j++){
   const target=await figure.evaluate((el,j)=>{
    const ax=JSON.parse(el.querySelector('.chart-data').textContent).axes[j],s=ax.series[0];
    const reference=ax.series.find(s=>s.mode==='markers')||s;
    const valid=reference.points.filter(p=>p[3]>=ax.box[1]+1&&p[3]<=ax.box[1]+ax.box[3]-1),p=valid[Math.floor(valid.length*.55)];
    const left=s.points.filter(q=>q[2]<=p[2]+1e-8).at(-1),right=s.points.find(q=>q[2]>=p[2]-1e-8);
    const expected=left[1]+(right[1]-left[1])*(right[2]===left[2]?0:(p[2]-left[2])/(right[2]-left[2]));
    const t=new DOMPoint(p[2],p[3]).matrixTransform(el.querySelector('svg').getScreenCTM());
    return {x:t.x,y:t.y,expected,name:s.label,percent:ax.yFormat==='percent'};
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
 const calibration=page.locator('figure').nth(14);await calibration.scrollIntoViewIfNeeded();
 for(const [k,role] of [[.025,null],[.05,'Calibration quotes'],[.1,'Withheld quotes']]){
  const target=await calibration.evaluate((el,k)=>{const ax=JSON.parse(el.querySelector('.chart-data').textContent).axes[0];const px=ax.box[0]+(k-ax.xlim[0])/(ax.xlim[1]-ax.xlim[0])*ax.box[2];const p=new DOMPoint(px,ax.box[1]+ax.box[3]/2).matrixTransform(el.querySelector('svg').getScreenCTM());return {x:p.x,y:p.y};},k);
  await page.mouse.move(target.x,target.y);await page.waitForTimeout(30);
  const labels=await page.locator('#chart-coordinate-tooltip .chart-tooltip-label').allTextContents();
  assert.equal(labels.length,role?2:1);if(role)assert.ok(labels.includes(role));assert.ok(labels.includes('Fitted raw SVI'));
 }
 await page.locator('#surface-map svg').scrollIntoViewIfNeeded();
 for(const [row,col] of [[0,0],[0,48],[12,24],[24,0],[24,48],[7,31]]){
  const pt=await page.locator('#surface-map svg').evaluate((svg,{row,col})=>{const p=new DOMPoint(73+(col+.5)*650/49,24+(row+.5)*240/25).matrixTransform(svg.getScreenCTM());return {x:p.x,y:p.y};},{row,col});
  await page.mouse.move(pt.x,pt.y);await page.waitForTimeout(20);
  const values=await page.locator('#surface-cell-tooltip .chart-tooltip-row strong').allTextContents();
  const expected=await page.evaluate(({row,col})=>SurfaceLab.last.cells[row*49+col],{row,col});
  assert.ok(Math.abs(Number(values[0])-expected.k)<.000051);
  assert.ok(Math.abs(Number(values[1].replace('%',''))/100-expected.sigma)<.0000051);
  assert.ok(Math.abs(Number(values[2])-expected.w)<.00000051);
  assert.ok(Math.abs(Number(values[3].replaceAll(',',''))-expected.K)<.000051);
 }
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();
 await page.locator('#live-plot svg').focus();await page.keyboard.press('End');
 assert.equal(await page.locator('#chart-coordinate-tooltip .chart-tooltip-row').count(),5);await page.screenshot({path:path.join(__dirname,'laboratory-hover.png')});
 await page.keyboard.press('Escape');assert.ok(!(await page.locator('#chart-coordinate-tooltip').isVisible()));
 fs.writeFileSync(path.join(__dirname,'coordinates-verification.json'),JSON.stringify({panels,coordinateAccuracy:'passed',percentUnits:'passed',compactNeutralCard:'passed',observationsVersusInterpolation:'passed',surfaceMapCells:6,allFiveLaboratorySeries:'passed'},null,2));
 console.log(panels+' chart panels: coordinate accuracy, percentage units, card bounds, five-series laboratory hover passed');await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});


