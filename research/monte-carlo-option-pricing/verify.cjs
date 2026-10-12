const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=__dirname,file=path.resolve(root,'../../projects/monte-carlo-option-pricing.html');
const url=pathToFileURL(file).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
 const errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://**/*',route=>{requests.push(route.request().url());return route.abort();});
 await page.goto(url);await page.waitForFunction(()=>document.getElementById('result-price').textContent!=='—'&&!document.getElementById('calculate').disabled);
 const structure=await page.evaluate(()=>{
  const ids=[...document.querySelectorAll('[id]')].map(x=>x.id);
  const missing=[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash);
  const math=[...document.querySelectorAll('math')];
  const leftovers=[...document.querySelectorAll('.article p')].filter(p=>{
   const copy=p.cloneNode(true);copy.querySelectorAll('math').forEach(x=>x.remove());return /\\[()[\]]|(?:mathbb|widehat|sigma)_|M_\{|int_0/.test(copy.textContent);
  }).map(p=>p.textContent.slice(0,160));
  return {sections:document.querySelectorAll('.article>section').length,figures:document.querySelectorAll('figure').length,
   display:document.querySelectorAll('.eq').length,math:math.length,duplicateIds:ids.filter((x,i)=>ids.indexOf(x)!==i),missing,leftovers,
   charts:document.querySelectorAll('figure svg.has-coordinate-reader').length,
   failedMath:math.filter(x=>x.getBoundingClientRect().height<5).length,eqBackground:getComputedStyle(document.querySelector('.eq')).backgroundColor};
 });
 assert.equal(structure.sections,28);assert.equal(structure.figures,16);assert.equal(structure.display,74);
 assert.equal(structure.math,308);assert.deepEqual(structure.duplicateIds,[]);assert.deepEqual(structure.missing,[]);
 assert.deepEqual(structure.leftovers,[]);assert.equal(structure.charts,16);assert.equal(structure.failedMath,0);
 assert.equal(structure.eqBackground,'rgba(11, 16, 13, 0.75)');
 const value=async id=>Number((await page.locator('#result-'+id).innerText()).replace(/,/g,''));
 const submit=async changes=>{
  for(const [name,val] of Object.entries(changes)){
   const el=page.locator('[name="'+name+'"]');
   if(['kind','method'].includes(name))await el.selectOption(String(val));else await el.fill(String(val));
  }
  await page.locator('#calculate').click();await page.waitForFunction(()=>!document.getElementById('calculate').disabled);
  assert.equal(await page.locator('#calc-error').innerText(),'');
  return {value:await value('price'),se:await value('se'),reference:await value('reference'),units:await value('units'),work:await value('work')};
 };
 const methods={};
 for(const method of ['plain','antithetic','control','combined']){
  methods[method]=await submit({method});
  const repeated=await submit({method});assert.deepEqual(repeated,methods[method]);
  assert.ok(Math.abs(repeated.reference-10.450583572185565)<1e-6);
  assert.ok(Math.abs(repeated.value-repeated.reference)<5*repeated.se,'Benchmark error within five SEs: '+method);
 }
 assert.equal(methods.plain.units,20000);assert.equal(methods.antithetic.units,10000);
 assert.equal(methods.control.work,21024);assert.equal(methods.combined.work,22048);
 assert.ok(methods.antithetic.se<methods.plain.se);assert.ok(methods.control.se<methods.plain.se);assert.ok(methods.combined.se<methods.control.se);
 // Independent distribution-level second moment for the discounted benchmark call.
 const theoreticalSE=Math.sqrt(216.660856798/20000);
 assert.ok(Math.abs(methods.plain.se/theoreticalSE-1)<.08);
 const yieldCall=await submit({method:'plain',yield:2});assert.ok(Math.abs(yieldCall.reference-9.227005508154036)<1e-6);
 const yieldPut=await submit({kind:'put'});assert.ok(Math.abs(yieldPut.reference-6.330080627549918)<1e-6);
 const sigmaZero=await submit({kind:'call',method:'combined',yield:0,vol:0});
 assert.equal(sigmaZero.se,0);assert.ok(Math.abs(sigmaZero.value-(100-100*Math.exp(-.05)))<1e-6);assert.equal(sigmaZero.work,20000);
 const expiry=await submit({spot:110,tau:0,vol:20});assert.equal(expiry.value,10);assert.equal(expiry.se,0);
 const negativeRate=await submit({spot:100,tau:1,rate:-2,method:'plain'});assert.ok(Math.abs(negativeRate.reference-7.07601917665)<1e-5);
 await submit({strike:10000,budget:100,rate:5});assert.equal(await value('price'),0);assert.match(await page.locator('#notebook-note').innerText(),/uninformative/);
 await page.locator('[name=method]').selectOption('antithetic');await page.locator('[name=budget]').fill('101');await page.locator('#calculate').click();
 assert.match(await page.locator('#calc-error').innerText(),/even production/);
 await page.locator('#reset-inputs').click();await page.waitForFunction(()=>!document.getElementById('calculate').disabled);
 assert.equal(await page.locator('[name=budget]').inputValue(),'20000');assert.equal(await page.locator('[name=method]').inputValue(),'plain');
 assert.equal(await value('price'),methods.plain.value);
 const sizes=[];
 for(const width of [320,390,768,978,1440]){
  await page.setViewportSize({width,height:1000});
  const metrics=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,bodyWidth:document.body.scrollWidth,
   columns:getComputedStyle(document.querySelector('.toc-columns')).gridTemplateColumns.split(' ').length}));
  assert.ok(metrics.documentWidth<=width+1,'Document overflow at '+width+': '+metrics.documentWidth);
  assert.equal(metrics.columns,width<=760?1:3);sizes.push(metrics);
 }
 await page.setViewportSize({width:978,height:850});await page.goto(url);await page.waitForFunction(()=>!document.getElementById('calculate').disabled);
 await page.screenshot({path:path.join(root,'hero-desktop.png')});
 for(const [name,selector] of [['contents','.toc'],['formulas','#estimators'],['asian','#asian'],['laboratory','#simulation-notebook']]){
  await page.locator(selector).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,name+'-desktop.png')});
 }
 await page.locator('figure svg').first().scrollIntoViewIfNeeded();
 const hover=await page.evaluate(()=>{
  const el=document.querySelector('figure'),svg=el.querySelector('svg'),data=JSON.parse(el.querySelector('.chart-data').textContent),ax=data.axes[0];
  const p=new DOMPoint(ax.box[0]+ax.box[2]*.67,ax.box[1]+ax.box[3]*.42).matrixTransform(svg.getScreenCTM());
  return {x:p.x,y:p.y,series:ax.series.length};
 });
 await page.mouse.move(hover.x,hover.y);await page.waitForTimeout(100);
 const tooltip=page.locator('#chart-coordinate-tooltip');assert.equal(await tooltip.locator('.chart-tooltip-row').count(),hover.series);
 assert.equal(hover.series,10);assert.ok(await tooltip.isVisible());
 await page.screenshot({path:path.join(root,'paths-hover.png')});
 await page.mouse.move(2,100);assert.ok(!(await tooltip.isVisible()));
 const keyboard=page.locator('figure svg').first();await keyboard.focus();await keyboard.press('Home');assert.ok(await tooltip.isVisible());
 await keyboard.press('ArrowRight');await keyboard.press('Escape');assert.ok(!(await tooltip.isVisible()));
 await page.setViewportSize({width:390,height:844});await page.goto(url);await page.waitForFunction(()=>!document.getElementById('calculate').disabled);
 await page.screenshot({path:path.join(root,'hero-mobile.png')});await page.locator('#simulation-notebook').scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(root,'laboratory-mobile.png')});
 const noJS=await browser.newContext({javaScriptEnabled:false});const staticPage=await noJS.newPage();await staticPage.goto(url);
 assert.equal(await staticPage.locator('figure svg').count(),16);assert.equal(await staticPage.locator('math').count(),308);
 assert.equal(await staticPage.locator('noscript').count(),1);await noJS.close();
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 const report={structure,methods,sizes,errors,externalRuntimeRequests:requests};
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
