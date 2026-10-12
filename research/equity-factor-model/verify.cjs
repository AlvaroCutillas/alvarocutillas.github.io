const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=__dirname,url=pathToFileURL(path.resolve(root,'../../projects/equity-factor-model.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
 const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
 await page.goto(url);await page.waitForFunction(()=>window.FactorLab?.last&&window.FactorLab?.sort);
 const structure=await page.evaluate(()=>({sections:document.querySelectorAll('article>section').length,figures:document.querySelectorAll('figure').length,math:document.querySelectorAll('math').length,exercises:document.querySelectorAll('details').length,toc:document.querySelectorAll('.toc-chapters a').length,badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash),dupes:[...document.querySelectorAll('[id]')].map(e=>e.id).filter((v,i,a)=>a.indexOf(v)!==i),external:[...document.querySelectorAll('script[src],link[href],img[src]')].map(e=>e.outerHTML)}));
 assert.equal(structure.sections,30);assert.equal(structure.figures,19);assert.equal(structure.math,155);assert.equal(structure.exercises,14);assert.equal(structure.toc,30);assert.deepEqual(structure.badAnchors,[]);assert.deepEqual(structure.dupes,[]);assert.deepEqual(structure.external,[]);
 const cases=JSON.parse(fs.readFileSync(path.join(root,'reference-cases.json'),'utf8'));
 const differences=await page.evaluate(cases=>{
  let max=0;function compare(a,b){if(Array.isArray(a))a.forEach((x,i)=>compare(x,b[i]));else max=Math.max(max,Math.abs(a-b)/Math.max(1,Math.abs(b)));}
  for(const c of cases.attribution){const a=FactorLab.analyze(c.o);for(const k of ['b','hac_se','classic_se','r2','rmse','system','specific','variance','contributions','volatility'])compare(a[k],c.result[k]);compare(a.predAll,c.result.all_pred);}
  for(const c of cases.sorts){const a=FactorLab.crossSection(c.o);for(const k of ['weights','gross','net','turnover','deciles','exposure','ic'])compare(a[k],c.result[k]);compare(a.sectorNet,c.result.sector_net);compare(a.rankIC,c.result.rank_ic);}
  return max;
 },cases);
 assert.ok(differences<1e-10,'Python/JS mismatch '+differences);
 const initial=await page.evaluate(()=>FactorLab.last);
 assert.ok(Math.abs(initial.b[0]+.002545350568283081)<1e-12);
 await page.locator('#input-lags').fill('12');await page.locator('#calculate').click();
 const changed=await page.evaluate(()=>FactorLab.last);assert.deepEqual(changed.b,initial.b);assert.notEqual(changed.hac_se[0],initial.hac_se[0]);
 await page.locator('#input-noise').fill('0');await page.locator('#calculate').click();
 const perfect=await page.evaluate(()=>FactorLab.last);
 perfect.b.forEach((b,i)=>assert.ok(Math.abs(b-[.0004,1.05,.35,.25,.45,.20][i])<1e-12));assert.ok(perfect.rmse<1e-12);
 assert.equal(await page.locator('#result-t').innerText(),'Undefined');
 await page.locator('#reset-inputs').click();await page.locator('#input-model').selectOption('capm');await page.locator('#calculate').click();assert.equal(await page.locator('#coefficient-table tbody tr').count(),2);
 await page.locator('#input-signal').selectOption('3');await page.locator('#input-neutral').selectOption('unrestricted');await page.locator('#input-tail').selectOption('10');await page.locator('#input-cost').fill('100');await page.locator('#build-sort').click();
 const s=await page.evaluate(()=>FactorLab.sort);assert.equal(s.weights.filter(x=>x>0).length,16);assert.ok(Math.abs(s.gross-s.net-.02)<1e-12);
 await page.locator('#reset-inputs').click();
 for(const [button,file,rows,cols] of [['#download-returns','verified-returns.csv',241,10],['#download-stocks','verified-stocks.csv',161,8]]){
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator(button).click()]);await download.saveAs(path.join(root,file));
  const csv=fs.readFileSync(path.join(root,file),'utf8').trim().split(/\r?\n/);assert.equal(csv.length,rows);assert.equal(csv[0].split(',').length,cols);
 }
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();await page.locator('#live-plot svg').focus();await page.keyboard.press('End');assert.equal(await page.locator('#chart-coordinate-tooltip .chart-tooltip-row').count(),2);await page.keyboard.press('Escape');
 await page.locator('#sort-plot svg').scrollIntoViewIfNeeded();await page.locator('#sort-plot svg').focus();await page.keyboard.press('Home');assert.equal(await page.locator('#chart-coordinate-tooltip .chart-tooltip-row').count(),1);await page.keyboard.press('Escape');
 const sizes=[];await page.evaluate(()=>document.querySelectorAll('details').forEach(d=>d.open=true));
 for(const width of [320,390,768,978,1440]){
  await page.setViewportSize({width,height:850});
  const r=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,tocColumns:getComputedStyle(document.querySelector('.toc-columns')).gridTemplateColumns.split(' ').length}));
  if(r.documentWidth>width+1){console.log(await page.evaluate(()=>[...document.querySelectorAll('math')].filter(e=>!e.closest('.eq-scroll')&&e.getBoundingClientRect().right>innerWidth).map(e=>({text:e.textContent,section:e.closest('section')?.id,width:e.getBoundingClientRect().width}))));}
  assert.ok(r.documentWidth<=width+1,'Overflow at '+width);assert.equal(r.tocColumns,width<=760?1:3);sizes.push(r);
 }
 await page.setViewportSize({width:978,height:850});await page.goto(url);await page.screenshot({path:path.join(root,'hero-desktop.png')});
 for(const [name,selector] of [['contents','.toc'],['formulas','#risk-attribution'],['laboratory','#factor-notebook'],['curves','#live-plot'],['examples','#worked-study']]){
  const el=page.locator(selector);if(await el.count()){await el.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,name+'-desktop.png')});}
 }
 await page.setViewportSize({width:390,height:844});await page.goto(url);await page.screenshot({path:path.join(root,'hero-mobile.png')});await page.locator('#factor-notebook').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,'laboratory-mobile.png')});
 await page.emulateMedia({media:'print'});assert.equal(await page.locator('.eq math').first().evaluate(e=>getComputedStyle(e).color),'rgb(17, 17, 17)');
 const offline=await browser.newPage({javaScriptEnabled:false});await offline.goto(url);assert.equal(await offline.locator('article>section').count(),30);assert.equal(await offline.locator('figure').count(),19);assert.ok(await offline.locator('noscript').isVisible());
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify({structure,referenceCases:cases.attribution.length,stockSorts:cases.sorts.length,maxRelativeDifference:differences,sizes,errors,externalRequests:requests},null,2));
 console.log('Structure, 36 reference regressions, 24 sorts, controls, CSV, keyboard, responsive, print and offline checks passed');await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
