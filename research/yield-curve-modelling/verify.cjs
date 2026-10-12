const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=__dirname,url=pathToFileURL(path.resolve(root,'../../projects/yield-curve-modelling.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
 const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
 await page.route('http://**/*',r=>r.abort());await page.route('https://**/*',r=>r.abort());
 await page.goto(url);await page.waitForFunction(()=>window.YieldLab?.last);
 const structure=await page.evaluate(()=>({sections:document.querySelectorAll('article>section').length,figures:document.querySelectorAll('figure').length,math:document.querySelectorAll('math').length,exercises:document.querySelectorAll('details').length,toc:document.querySelectorAll('.toc-chapters a').length,badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash),dupes:[...document.querySelectorAll('[id]')].map(e=>e.id).filter((v,i,a)=>a.indexOf(v)!==i),external:[...document.querySelectorAll('script[src],link[href],img[src]')].map(e=>e.outerHTML)}));
 assert.equal(structure.sections,30);assert.equal(structure.figures,19);assert.equal(structure.math,286);assert.equal(structure.exercises,14);assert.equal(structure.toc,30);assert.deepEqual(structure.badAnchors,[]);assert.deepEqual(structure.dupes,[]);assert.deepEqual(structure.external,[]);
 const initial=await page.evaluate(()=>YieldLab.last);
 assert.ok(Math.abs(initial.b.price-103.66010584851593)<1e-10);
 assert.ok(Math.abs(initial.b.ytm-.032019859530417825)<1e-10);
 assert.ok(Math.abs(initial.shocked.price-99.01734558659587)<1e-10);
 const cases=JSON.parse(fs.readFileSync(path.join(root,'reference-cases.json'),'utf8'));
 const diffs=await page.evaluate(cases=>cases.map(c=>{
  if(!c.bond){const r=YieldLab.sample(c.T,c.p,c.model);return Math.max(...['z','f','d'].map(k=>Math.abs(r[k]-c[k])));}
  const v=c.bond,r=YieldLab.valueBond(c.p,v.T,v.c,v.m,v.N,0,c.model),keys=['price','ytm','duration','convexity','dv01'];
  return Math.max(...keys.map(k=>Math.abs(r[k]-c.result[k])/Math.max(1,Math.abs(c.result[k]))),Math.abs(YieldLab.par(v.T,c.p,v.m,c.model)-c.par));
 }),cases);
 assert.ok(Math.max(...diffs)<1e-10,'Python/JavaScript mismatch '+Math.max(...diffs));
 const fitResults=[];
 for(const model of ['ns','nss']){
  await page.locator('#input-model').selectOption(model);await page.locator('#fit-quotes').click();
  const fit=await page.evaluate(()=>({fit:YieldLab.fit,training:YieldLab.last.calibration.training,holdout:YieldLab.last.calibration.holdout}));
  assert.ok(fit.fit);assert.ok(fit.training<(model==='ns'?2.322:.244));assert.ok(fit.holdout<(model==='ns'?2.76:.62));fitResults.push(fit);
 }
 assert.equal(await page.locator('#quote-table tbody tr').count(),16);assert.equal(await page.locator('#cash-table tbody tr').count(),10);
 await page.locator('#reset-inputs').click();
 await page.locator('#input-tau2').fill('0');await page.locator('#input-model').selectOption('ns');await page.locator('#calculate').click();
 assert.equal(await page.locator('#calc-error').innerText(),'');assert.equal(await page.evaluate(()=>YieldLab.last.o.model),'ns');
 await page.locator('#reset-inputs').click();
 async function submit(values){for(const [name,value] of Object.entries(values)){const el=page.locator('#input-'+name);if(name==='frequency'||name==='model')await el.selectOption(String(value));else await el.fill(String(value));}await page.locator('#calculate').click();}
 await submit({face:200});assert.ok(Math.abs(await page.evaluate(()=>YieldLab.last.b.price)-2*initial.b.price)<1e-10);
 await submit({maturity:5.3});assert.match(await page.locator('#calc-error').innerText(),/integer/);
 await submit({maturity:31});assert.match(await page.locator('#calc-error').innerText(),/horizon/);
 await page.locator('#reset-inputs').click();
 await submit({coupon:0});const zb=await page.evaluate(()=>YieldLab.last);assert.ok(Math.abs(zb.b.duration-5)<1e-12);assert.ok(Math.abs(zb.b.convexity-25)<1e-12);
 await page.locator('#reset-inputs').click();
 await submit({b0:.5,b1:-2,b2:.8,b3:0,tau1:2});assert.match(await page.locator('#curve-status').innerText(),/Negative forwards/);
 await page.locator('#reset-inputs').click();
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-curve').click()]);await download.saveAs(path.join(root,'verified-curve.csv'));
 const csv=fs.readFileSync(path.join(root,'verified-curve.csv'),'utf8').trim().split(/\r?\n/);assert.equal(csv.length,602);assert.equal(csv[0].split(',').length,13);
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();await page.locator('#live-plot svg').focus();await page.keyboard.press('End');assert.equal(await page.locator('#chart-coordinate-tooltip .chart-tooltip-row').count(),3);
 await page.keyboard.press('ArrowDown');assert.equal(await page.locator('#chart-coordinate-tooltip .chart-tooltip-row').count(),2);await page.keyboard.press('Escape');assert.ok(!(await page.locator('#chart-coordinate-tooltip').isVisible()));
 await page.locator('#shock-plot svg').scrollIntoViewIfNeeded();await page.locator('#shock-plot svg').focus();await page.keyboard.press('Home');assert.equal(await page.locator('#chart-coordinate-tooltip .chart-tooltip-row').count(),3);await page.keyboard.press('Escape');
 const sizes=[];
 await page.evaluate(()=>document.querySelectorAll('details').forEach(d=>d.open=true));
 for(const width of [320,390,768,978,1440]){
  await page.setViewportSize({width,height:850});
  const r=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,tocColumns:getComputedStyle(document.querySelector('.toc-columns')).gridTemplateColumns.split(' ').length}));
  assert.ok(r.documentWidth<=width+1,'Overflow at '+width);assert.equal(r.tocColumns,width<=760?1:3);sizes.push(r);
 }
 await page.setViewportSize({width:978,height:850});await page.goto(url);await page.screenshot({path:path.join(root,'hero-desktop.png')});
 for(const [name,selector] of [['contents','.toc'],['formulas','#svensson'],['laboratory','#yield-notebook'],['curves','#live-plot'],['examples','#worked-study']]){
  await page.locator(selector).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,name+'-desktop.png')});
 }
 await page.setViewportSize({width:390,height:844});await page.goto(url);await page.screenshot({path:path.join(root,'hero-mobile.png')});await page.locator('#yield-notebook').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,'laboratory-mobile.png')});
 await page.emulateMedia({media:'print'});assert.equal(await page.locator('.eq math').first().evaluate(e=>getComputedStyle(e).color),'rgb(17, 17, 17)');
 const offline=await browser.newPage({javaScriptEnabled:false});await offline.goto(url);assert.equal(await offline.locator('article>section').count(),30);assert.equal(await offline.locator('figure').count(),19);assert.ok(await offline.locator('noscript').isVisible());
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify({structure,referenceCases:cases.length,maxRelativeDifference:Math.max(...diffs),fitResults,sizes,errors,externalRequests:requests},null,2));
 console.log('Structure, 96 reference cases, two calibrations, bond risk, controls, CSV, keyboard, responsive, print and offline checks passed');await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
