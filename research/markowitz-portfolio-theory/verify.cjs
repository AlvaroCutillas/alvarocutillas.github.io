const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=__dirname,url=pathToFileURL(path.resolve(root,'../../projects/markowitz-portfolio-theory.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:978,height:850}}),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://**/*',r=>{requests.push(r.request().url());return r.abort()});await page.goto(url);
 assert.equal(await page.locator('#calc-error').innerText(),'');
 const structure=await page.evaluate(()=>{
  const ids=[...document.querySelectorAll('[id]')].map(x=>x.id);
  return {sections:document.querySelectorAll('.article>section').length,figures:document.querySelectorAll('figure').length,
   equations:document.querySelectorAll('.eq').length,math:document.querySelectorAll('math').length,
   duplicateIds:ids.filter((x,i)=>ids.indexOf(x)!==i),
   badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(x=>!document.getElementById(x.hash.slice(1))).map(x=>x.hash),
   chartReaders:document.querySelectorAll('figure svg.has-coordinate-reader').length,
   eqColor:getComputedStyle(document.querySelector('.eq')).backgroundColor};
 });
 assert.equal(structure.sections,30);assert.equal(structure.figures,16);assert.equal(structure.equations,62);assert.equal(structure.math,252);
 assert.deepEqual(structure.duplicateIds,[]);assert.deepEqual(structure.badAnchors,[]);assert.equal(structure.chartReaders,16);assert.equal(structure.eqColor,'rgba(11, 16, 13, 0.75)');
 const read=async id=>Number((await page.locator('#result-'+id).innerText()).replace(/[% ,]/g,''));
 assert.ok(Math.abs(await read('gmv-mean')-6.9937394415)<.000051);assert.ok(Math.abs(await read('gmv-vol')-9.3151135556)<.000051);
 assert.ok(Math.abs(await read('target-vol')-13.6797895328)<.000051);assert.ok(Math.abs(await read('sharpe')-.614361127812)<.00000051);
 const submit=async changes=>{
  for(const [name,value] of Object.entries(changes)){
   const el=page.locator('[name="'+name+'"]');if(name==='mode')await el.selectOption(value);else await el.fill(String(value));
  }
  await page.locator('#calculate').click();
 };
 const cases=JSON.parse(fs.readFileSync(path.join(root,'reference-cases.json'),'utf8'));
 for(const c of cases){
  const inputs={target:c.target*100,mode:c.mode};
  for(let i=0;i<3;i++){inputs['mu-'+'abc'[i]]=c.mu[i]*100;inputs['vol-'+'abc'[i]]=c.vol[i]*100;inputs['rho-'+['ab','ac','bc'][i]]=c.rho[i];}
  await submit(inputs);assert.equal(await page.locator('#calc-error').innerText(),'');
  const weights=await page.locator('#lab-weights tr').evaluateAll(rows=>rows.map(r=>Number(r.children[2].textContent.replace('%',''))/100));
  for(let i=0;i<3;i++)assert.ok(Math.abs(weights[i]-c.weights[i])<.00000051,'Weight versus independent reference');
  assert.ok(Math.abs(await read('target-vol')/100-c.volatility)<.00000051);
 }
 await page.locator('#reset-inputs').click();
 await submit({mode:'longonly',target:15});assert.equal(await page.locator('#result-classification').innerText(),'Infeasible');assert.equal(await page.locator('#result-target-vol').innerText(),'—');
 await submit({target:14});assert.equal(await page.locator('#result-classification').innerText(),'Efficient branch');assert.ok(Math.abs(await read('target-vol')-28)<.000051);
 await submit({target:6.5});assert.equal(await page.locator('#result-classification').innerText(),'Dominated lower branch');
 await submit({mode:'unrestricted',rf:8});assert.equal(await page.locator('#result-sharpe').innerText(),'—');assert.match(await page.locator('#notebook-note').innerText(),/positive-budget tangency is unavailable/);
 await submit({mode:'longonly'});assert.notEqual(await page.locator('#result-sharpe').innerText(),'—');
 await submit({rf:15});assert.equal(await page.locator('#result-sharpe').innerText(),'—');
 await submit({'mu-a':8,'mu-b':8,'mu-c':8,target:8,rf:2});assert.match(await page.locator('#notebook-note').innerText(),/frontier collapses/);
 await submit({target:9});assert.equal(await page.locator('#result-classification').innerText(),'Infeasible');
 await page.locator('#reset-inputs').click();
 await submit({'rho-ab':.9,'rho-ac':.9,'rho-bc':-.9});assert.match(await page.locator('#calc-error').innerText(),/positive-definite/);
 await page.locator('#reset-inputs').click();
 // Equal independent volatility gives equal GMV weights.
 await submit({'vol-a':20,'vol-b':20,'vol-c':20,'rho-ab':0,'rho-ac':0,'rho-bc':0});
 const gmv=await page.locator('#lab-weights tr').evaluateAll(rows=>rows.map(r=>Number(r.children[1].textContent.replace('%',''))));
 gmv.forEach(x=>assert.ok(Math.abs(x-100/3)<.000051));await page.locator('#reset-inputs').click();
 const sizes=[];
 for(const width of [320,390,768,978,1440]){
  await page.setViewportSize({width,height:850});
  const m=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,
   tocColumns:getComputedStyle(document.querySelector('.toc-columns')).gridTemplateColumns.split(' ').length}));
  assert.ok(m.documentWidth<=width+1,'Body overflow at '+width);assert.equal(m.tocColumns,width<=760?1:3);sizes.push(m);
 }
 await page.setViewportSize({width:978,height:850});await page.goto(url);
 await page.screenshot({path:path.join(root,'hero-desktop.png')});
 for(const [name,selector] of [['contents','.toc'],['formula','#lagrange'],['laboratory','#frontier-notebook'],['examples','#examples']]){
  await page.locator(selector).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,name+'-desktop.png')});
 }
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();await page.locator('#live-plot svg').focus();await page.keyboard.press('Home');
 assert.ok(await page.locator('#chart-coordinate-tooltip').isVisible());await page.keyboard.press('Escape');
 await page.setViewportSize({width:390,height:844});await page.goto(url);await page.screenshot({path:path.join(root,'hero-mobile.png')});
 await page.locator('#frontier-notebook').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,'laboratory-mobile.png')});
 const context=await browser.newContext({javaScriptEnabled:false}),staticPage=await context.newPage();await staticPage.goto(url);
 assert.equal(await staticPage.locator('figure svg').count(),16);assert.equal(await staticPage.locator('math').count(),252);await context.close();
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 const report={structure,independentReferenceCases:cases.length,limitsAndDegeneracy:'passed',sizes,errors,externalRuntimeRequests:requests};
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
