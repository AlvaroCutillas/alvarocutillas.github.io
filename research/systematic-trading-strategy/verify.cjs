const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=__dirname,url=pathToFileURL(path.resolve(root,'../../projects/systematic-trading-strategy.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:978,height:850}}),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));await page.route('https://**/*',r=>{requests.push(r.request().url());return r.abort()});await page.goto(url);
 assert.equal(await page.locator('#calc-error').innerText(),'');
 const structure=await page.evaluate(()=>{
  const ids=[...document.querySelectorAll('[id]')].map(x=>x.id);
  return {sections:document.querySelectorAll('.article>section').length,figures:document.querySelectorAll('figure').length,equations:document.querySelectorAll('.eq').length,math:document.querySelectorAll('math').length,
  duplicateIds:ids.filter((x,i)=>ids.indexOf(x)!==i),badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(x=>!document.getElementById(x.hash.slice(1))).map(x=>x.hash),
  chartReaders:document.querySelectorAll('figure svg.has-coordinate-reader').length,eqColor:getComputedStyle(document.querySelector('.eq')).backgroundColor,
  badPaths:[...document.querySelectorAll('#live-plot path')].filter(x=>/NaN|undefined/.test(x.getAttribute('d'))).length};
 });
 assert.equal(structure.sections,30);assert.equal(structure.figures,19);assert.equal(structure.equations,40);assert.equal(structure.math,156);
 assert.deepEqual(structure.duplicateIds,[]);assert.deepEqual(structure.badAnchors,[]);assert.equal(structure.chartReaders,19);assert.equal(structure.eqColor,'rgba(11, 16, 13, 0.75)');assert.equal(structure.badPaths,0);
 const cases=JSON.parse(fs.readFileSync(path.join(root,'reference-cases.json'),'utf8'));let maxError=0;
 for(const c of cases){
  const got=await page.evaluate(c=>{
   const prices=StrategyLab.market(c.sessions,c.seed,c.model),b=StrategyLab.run(prices,c.options);
   return {start:b.start,prices_head:Array.from(prices.slice(0,10)),wealth:c.indices.map(i=>b.equity[i]),metrics:b.metrics};
  },c);
  assert.equal(got.start,c.start);
  got.prices_head.forEach((v,i)=>assert.ok(Math.abs(v-c.prices_head[i])<1e-10));
  got.wealth.forEach((v,i)=>{const err=Math.abs(v-c.wealth_reference[i])/c.wealth_reference[i];maxError=Math.max(maxError,err);assert.ok(err<1e-10)});
  for(const [js,py] of [['cagr','cagr'],['volatility','volatility'],['sharpe','sharpe'],['maxDD','max_drawdown'],['annualTurnover','annual_turnover'],['totalFees','total_fees'],['averageExposure','average_exposure']]){
   if(c.metrics[py]===null)assert.equal(got.metrics[js],null);else assert.ok(Math.abs(got.metrics[js]-c.metrics[py])<1e-7*Math.max(1,Math.abs(c.metrics[py])),js);
  }
 }
 const read=async id=>Number((await page.locator('#result-'+id).innerText()).replace(/[%€ ,]/g,''));
 assert.ok(Math.abs(await read('wealth')-107651.7415141567)<.0051);assert.ok(Math.abs(await read('cagr')-1.291435479)<.0051);
 const initial=[await read('wealth'),await read('fees')];
 const submit=async values=>{for(const [name,value] of Object.entries(values)){const el=page.locator('[name="'+name+'"]');if(['rule','model','volmode'].includes(name))await el.selectOption(value);else await el.fill(String(value));}await page.locator('#calculate').click();assert.equal(await page.locator('#calc-error').innerText(),'');};
 await submit({capital:200000});assert.ok(Math.abs(await read('wealth')-2*initial[0])<.011);assert.ok(Math.abs(await read('fees')-2*initial[1])<.011);
 await page.locator('#reset-inputs').click();assert.deepEqual([await read('wealth'),await read('fees')],initial);
 await submit({cost:0});assert.equal(await read('fees'),0);
 const zero=await page.evaluate(()=>StrategyLab.last.accounts[0].equity.every((x,i)=>x===StrategyLab.last.accounts[1].equity[i]));assert.ok(zero);
 await submit({rule:'contrarian',model:'reversion',lookback:126,delay:5,volmode:'off'});assert.match(await page.locator('#notebook-note').innerText(),/close 131/);
 const valid=await page.evaluate(()=>StrategyLab.last.accounts[0].ledger.every(r=>r.asof===r.day-1-StrategyLab.last.options.delay&&r.asof<=r.day-2&&r.target>=0&&r.target<=1&&r.cash_after>=-1e-7));assert.ok(valid);
 const causality=await page.evaluate(()=>{
  const p=StrategyLab.market(800,4,'iid'),changed=Float64Array.from(p);for(let i=401;i<changed.length;i++)changed[i]*=2+i/100;
  const o={lookback:63,volControl:true,volTarget:.12,volWindow:20,costBps:10,cashAnnual:.02,delay:1,capital:100000,rule:'momentum',end:400};
  const a=StrategyLab.run(p,o),b=StrategyLab.run(changed,o);return a.equity.every((x,i)=>x===b.equity[i]);
 });assert.ok(causality);
 await page.locator('#reset-inputs').click();
 const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-ledger').click()]);
 await download.saveAs(path.join(root,'verified-ledger.csv'));
 const csv=fs.readFileSync(path.join(root,'verified-ledger.csv'),'utf8').trim().split(/\r?\n/);assert.equal(csv.length,1449);assert.equal(csv[0].split(',').length,13);assert.equal(Number(csv[1].split(',')[0]),65);
 const sizes=[];
 for(const width of [320,390,768,978,1440]){
  await page.setViewportSize({width,height:850});const m=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,tocColumns:getComputedStyle(document.querySelector('.toc-columns')).gridTemplateColumns.split(' ').length}));
  assert.ok(m.documentWidth<=width+1,'Body overflow '+width);assert.equal(m.tocColumns,width<=760?1:3);sizes.push(m);
 }
 await page.setViewportSize({width:978,height:850});await page.goto(url);await page.screenshot({path:path.join(root,'hero-desktop.png')});
 for(const [name,selector] of [['contents','.toc'],['formula','#accounting'],['laboratory','#strategy-notebook'],['examples','#worked-study']]){
  await page.locator(selector).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,name+'-desktop.png')});
 }
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();await page.locator('#live-plot svg').focus();await page.keyboard.press('Home');assert.ok(await page.locator('#chart-coordinate-tooltip').isVisible());assert.equal(await page.locator('.chart-tooltip-row').count(),4);
 await page.keyboard.press('ArrowDown');assert.match(await page.locator('#chart-coordinate-tooltip').innerText(),/%/);await page.keyboard.press('Escape');
 await page.setViewportSize({width:390,height:844});await page.goto(url);await page.screenshot({path:path.join(root,'hero-mobile.png')});await page.locator('#strategy-notebook').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,'laboratory-mobile.png')});
 const touch=await browser.newContext({hasTouch:true,isMobile:true,viewport:{width:390,height:844}}),tp=await touch.newPage();await tp.goto(url);await tp.locator('#live-plot svg').scrollIntoViewIfNeeded();await tp.waitForTimeout(150);
 const rect=await tp.locator('#live-plot svg').boundingBox();await tp.touchscreen.tap(rect.x+200,rect.y+100);await tp.waitForFunction(()=>!document.getElementById('chart-coordinate-tooltip').hidden);assert.equal(await tp.locator('.chart-tooltip-row').count(),4);await tp.screenshot({path:path.join(root,'laboratory-touch.png')});await touch.close();
 const context=await browser.newContext({javaScriptEnabled:false}),staticPage=await context.newPage();await staticPage.goto(url);assert.equal(await staticPage.locator('figure svg').count(),19);assert.equal(await staticPage.locator('math').count(),156);await context.close();
 await page.evaluate(()=>window.print=()=>{});await page.locator('.print-button').click();assert.equal(await page.locator('details:not([open])').count(),0);await page.emulateMedia({media:'print'});assert.equal(await page.locator('.notebook').isVisible(),false);
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 const report={structure,independentHoldingsCases:cases.length,maxRelativeWealthError:maxError,suffixCausality:'passed',cashAndEntryCosts:'passed',downloadedLedgerRows:csv.length-1,keyboardAndTouch:'passed',sizes,errors,externalRuntimeRequests:requests};
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
