const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=__dirname,url=pathToFileURL(path.resolve(root,'../../projects/implied-volatility-surface.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:978,height:850}}),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));await page.route('https://**/*',r=>{requests.push(r.request().url());return r.abort()});await page.goto(url);
 assert.equal(await page.locator('#calc-error').innerText(),'');assert.deepEqual(errors,[]);
 const structure=await page.evaluate(()=>{
  const ids=[...document.querySelectorAll('[id]')].map(x=>x.id);
  return {sections:document.querySelectorAll('.article>section').length,figures:document.querySelectorAll('figure').length,equations:document.querySelectorAll('.eq').length,math:document.querySelectorAll('math').length,
  duplicateIds:ids.filter((x,i)=>ids.indexOf(x)!==i),badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(x=>!document.getElementById(x.hash.slice(1))).map(x=>x.hash),
  chartReaders:document.querySelectorAll('figure svg.has-coordinate-reader').length,eqColor:getComputedStyle(document.querySelector('.eq')).backgroundColor,
  badPaths:[...document.querySelectorAll('#live-plot path')].filter(x=>/NaN|undefined/.test(x.getAttribute('d'))).length};
 });
 assert.equal(structure.sections,30);assert.equal(structure.figures,19);assert.equal(structure.equations,43);assert.equal(structure.math,316);
 assert.deepEqual(structure.duplicateIds,[]);assert.deepEqual(structure.badAnchors,[]);assert.equal(structure.chartReaders,19);assert.equal(structure.eqColor,'rgba(11, 16, 13, 0.75)');assert.equal(structure.badPaths,0);
 const ref=JSON.parse(fs.readFileSync(path.join(root,'reference-cases.json'),'utf8'));
 const numerics=await page.evaluate(ref=>{
  let cdfError=0,priceError=0,ivError=0,surfaceError=0,vegaError=0;
  for(const [x,y] of ref.cdf)cdfError=Math.max(cdfError,Math.abs(SurfaceLab.cdf(x)-y));
  for(const c of ref.prices){
   const got=SurfaceLab.black(c.F,c.K,c.D,c.T,c.sigma,c.put);priceError=Math.max(priceError,Math.abs(got-c.price));
   ivError=Math.max(ivError,Math.abs(SurfaceLab.implied(c.price,c.F,c.K,c.D,c.T,c.put)-c.sigma));
   vegaError=Math.max(vegaError,Math.abs(SurfaceLab.vega(c.F,c.K,c.D,c.T,c.sigma)-c.vega));
  }
  for(const c of ref.surface){
   const got=SurfaceLab.sample(c.k,c.T,c.p);
   for(const key of Object.keys(c.expected)){if(c.expected[key]===null){if(got[key]!==null)throw Error(key+' should be null');}else surfaceError=Math.max(surfaceError,Math.abs(got[key]-c.expected[key]));}
  }
  return {cdfError,priceError,ivError,surfaceError,vegaError};
 },ref);
 assert.ok(numerics.cdfError<1e-14);assert.ok(numerics.priceError<1e-9);assert.ok(numerics.ivError<1e-8);assert.ok(numerics.surfaceError<1e-10);assert.ok(numerics.vegaError<1e-10);
 const initial=await page.evaluate(()=>SurfaceLab.last);
 assert.ok(Math.abs(initial.contract.call-8.769299394030059)<1e-10);assert.ok(Math.abs(initial.recovered-initial.contract.sigma)<1e-10);
 assert.match(await page.locator('#surface-status').innerText(),/Global sufficient bounds pass/);
 const submit=async values=>{for(const [name,value] of Object.entries(values))await page.locator('#surface-form [name="'+name+'"]').fill(String(value));await page.locator('#calculate').click();assert.equal(await page.locator('#calc-error').innerText(),'');};
 await submit({eta:12});assert.match(await page.locator('#surface-status').innerText(),/inconsistency found/);assert.ok((await page.evaluate(()=>SurfaceLab.last.minG))<0);
 await page.locator('#reset-inputs').click();await submit({eta:0,rate:-3,yield:2,maturity:.5,k:.2});
 assert.ok(await page.evaluate(()=>SurfaceLab.last.cells.filter(c=>c.row===10).every(c=>Math.abs(c.sigma-SurfaceLab.last.cells.find(x=>x.row===10).sigma)<1e-14)));
 const parity=await page.evaluate(()=>{const c=SurfaceLab.last.contract;return Math.abs(c.call-c.put-c.D*(c.F-c.K));});assert.ok(parity<1e-10);
 await page.locator('#input-kind').selectOption('put');assert.match(await page.locator('#inversion-result').innerText(),/Recovered Black IV/);
 await page.locator('#input-premium').fill('0');await page.locator('#recover-iv').click();assert.match(await page.locator('#inversion-result').innerText(),/Premium must be/);
 await page.locator('#use-surface-price').click();assert.ok(Math.abs(await page.evaluate(()=>SurfaceLab.last.recovered-SurfaceLab.last.contract.sigma))<1e-9);
 await page.locator('#reset-inputs').click();await submit({spot:200});
 assert.ok(Math.abs((await page.evaluate(()=>SurfaceLab.last.contract.call))-2*initial.contract.call)<1e-10);
 assert.ok(Math.abs((await page.evaluate(()=>SurfaceLab.last.contract.sigma))-initial.contract.sigma)<1e-14);
 await page.locator('#reset-inputs').click();
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-surface').click()]);await download.saveAs(path.join(root,'verified-surface.csv'));
 const csv=fs.readFileSync(path.join(root,'verified-surface.csv'),'utf8').trim().split(/\r?\n/);assert.equal(csv.length,1226);assert.equal(csv[0].split(',').length,11);
 await page.locator('#surface-map svg').scrollIntoViewIfNeeded();await page.locator('#surface-map svg').focus();await page.keyboard.press('Home');
 assert.ok(await page.locator('#surface-cell-tooltip').isVisible());assert.equal(await page.locator('#surface-cell-tooltip .chart-tooltip-row').count(),4);
 const before=await page.locator('#surface-cell-tooltip').innerText();await page.keyboard.press('ArrowUp');assert.notEqual(await page.locator('#surface-cell-tooltip').innerText(),before);
 await page.screenshot({path:path.join(root,'map-keyboard.png')});await page.keyboard.press('Escape');assert.ok(!(await page.locator('#surface-cell-tooltip').isVisible()));
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();await page.locator('#live-plot svg').focus();await page.keyboard.press('Home');assert.ok(await page.locator('#chart-coordinate-tooltip').isVisible());assert.equal(await page.locator('#chart-coordinate-tooltip .chart-tooltip-row').count(),5);
 await page.keyboard.press('ArrowDown');assert.match(await page.locator('#chart-coordinate-tooltip').innerText(),/Butterfly diagnostic/);await page.keyboard.press('Escape');
 const sizes=[];
 for(const width of [320,390,768,978,1440]){
  await page.setViewportSize({width,height:850});const m=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,tocColumns:getComputedStyle(document.querySelector('.toc-columns')).gridTemplateColumns.split(' ').length}));
  assert.ok(m.documentWidth<=width+1,'Body overflow '+width);assert.equal(m.tocColumns,width<=760?1:3);sizes.push(m);
 }
 await page.setViewportSize({width:978,height:850});await page.goto(url);await page.screenshot({path:path.join(root,'hero-desktop.png')});
 for(const [name,selector] of [['contents','.toc'],['formula','#ssvi'],['laboratory','#surface-notebook'],['map','#surface-map'],['examples','#worked-study']]){await page.locator(selector).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,name+'-desktop.png')});}
 await page.setViewportSize({width:390,height:844});await page.goto(url);await page.screenshot({path:path.join(root,'hero-mobile.png')});await page.locator('#surface-notebook').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,'laboratory-mobile.png')});
 const touch=await browser.newContext({hasTouch:true,isMobile:true,viewport:{width:390,height:844}}),tp=await touch.newPage();await tp.goto(url);await tp.locator('#surface-map svg').scrollIntoViewIfNeeded();
 const rect=await tp.locator('#surface-map svg').boundingBox();await tp.touchscreen.tap(rect.x+190,rect.y+100);assert.ok(await tp.locator('#surface-cell-tooltip').isVisible());await tp.screenshot({path:path.join(root,'map-touch.png')});await touch.close();
 const context=await browser.newContext({javaScriptEnabled:false}),staticPage=await context.newPage();await staticPage.goto(url);assert.equal(await staticPage.locator('figure svg').count(),19);assert.equal(await staticPage.locator('math').count(),316);await context.close();
 await page.evaluate(()=>window.print=()=>{});await page.locator('.print-button').click();assert.equal(await page.locator('details:not([open])').count(),0);await page.emulateMedia({media:'print'});assert.equal(await page.locator('.notebook').isVisible(),false);
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 const report={structure,numerics,downloadedSurfaceRows:csv.length-1,invalidShapeAndQuoteDetection:'passed',keyboardAndTouch:'passed',sizes,errors,externalRuntimeRequests:requests};
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
