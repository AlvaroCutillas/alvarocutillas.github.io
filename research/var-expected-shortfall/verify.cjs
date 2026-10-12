const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=__dirname,url=pathToFileURL(path.resolve(root,'../../projects/var-expected-shortfall.html')).href;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage({viewport:{width:978,height:850}}),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));await page.route('https://**/*',r=>{requests.push(r.request().url());return r.abort()});await page.goto(url);
 assert.equal(await page.locator('#calc-error').innerText(),'');
 const structure=await page.evaluate(()=>{
  const ids=[...document.querySelectorAll('[id]')].map(x=>x.id);
  return {sections:document.querySelectorAll('.article>section').length,figures:document.querySelectorAll('figure').length,equations:document.querySelectorAll('.eq').length,math:document.querySelectorAll('math').length,duplicateIds:ids.filter((x,i)=>ids.indexOf(x)!==i),badAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(x=>!document.getElementById(x.hash.slice(1))).map(x=>x.hash),chartReaders:document.querySelectorAll('figure svg.has-coordinate-reader').length,eqColor:getComputedStyle(document.querySelector('.eq')).backgroundColor};
 });
 assert.equal(structure.sections,30);assert.equal(structure.figures,17);assert.equal(structure.equations,51);assert.equal(structure.math,246);
 assert.deepEqual(structure.duplicateIds,[]);assert.deepEqual(structure.badAnchors,[]);assert.equal(structure.chartReaders,17);assert.equal(structure.eqColor,'rgba(11, 16, 13, 0.75)');
 const cases=JSON.parse(fs.readFileSync(path.join(root,'reference-cases.json'),'utf8'));
 const results=await page.evaluate(cases=>cases.map(c=>window.RiskLab.analytical(c.alpha,c.mean,c.sd,c.distribution,c.nu)),cases);
 let maxRelativeError=0;
 results.forEach((r,i)=>r.forEach((v,j)=>{const err=Math.abs(v-cases[i].reference[j])/Math.max(1,Math.abs(cases[i].reference[j]));maxRelativeError=Math.max(maxRelativeError,err);assert.ok(err<1e-8,'Analytical reference '+i+' '+j+' '+err)}));
 const read=async id=>Number((await page.locator('#result-'+id).innerText()).replace(/[€ ,]/g,''));
 assert.ok(Math.abs(await read('var')-23263.47874040841)<.0051);assert.ok(Math.abs(await read('es')-26652.142203458054)<.0051);
 const submit=async values=>{for(const [name,value] of Object.entries(values)){const el=page.locator('[name="'+name+'"]');if(name==='distribution')await el.selectOption(value);else await el.fill(String(value));}await page.locator('#calculate').click();assert.equal(await page.locator('#calc-error').innerText(),'');};
 const initial=[await read('sample-var'),await read('sample-es')];
 await submit({wealth:2000000});assert.ok(Math.abs(await read('sample-var')-2*initial[0])<.011);assert.ok(Math.abs(await read('sample-es')-2*initial[1])<.011);
 await page.locator('#reset-inputs').click();assert.deepEqual([await read('sample-var'),await read('sample-es')],initial);
 await submit({seed:10});assert.notEqual(await read('sample-var'),initial[0]);assert.ok(Math.abs(await read('var')-23263.47874040841)<.0051);
 await submit({distribution:'student',nu:5});assert.ok(Math.abs(await read('var')-26064.63569384323)<.0051);assert.ok(Math.abs(await read('es')-34488.36760047854)<.0051);
 await submit({alpha:99.99,paths:100});assert.match(await page.locator('#notebook-note').innerText(),/highly unstable/);assert.equal(await read('sample-es'),await read('max'));
 await submit({sd:0,mean:-1});assert.equal(await read('var'),-10000);assert.equal(await read('es'),-10000);assert.equal(await read('sample-es'),-10000);assert.match(await page.locator('#result-breaches').innerText(),/^0 /);
 // Empirical definitions checked against an independently integrated quantile step function.
 const empiricalCases=[
 {x:[0,1,2,3,4,5,6,7,8,9],a:.85,ref:[8,26/3]},
 {x:[0,0,0,0,0,0,0,0,0,100],a:.95,ref:[100,100]},
 {x:[-10,-5],a:.95,ref:[-5,-5]},
 {x:Array(100).fill(7),a:.99,ref:[7,7]},
 {x:[1,2,3,4,5],a:.8,ref:[4,5]},
 {x:[1,2,3,4,5],a:.9,ref:[5,5]}
 ];
 for(const c of empiricalCases){const res=await page.evaluate(c=>RiskLab.empirical(c.x,c.a,RiskLab.suffixSum(c.x)),c);res.forEach((v,j)=>assert.ok(Math.abs(v-c.ref[j])<1e-8));}
 // Generator moments are an independent check on gamma/chi-square sampling.
 const moments=await page.evaluate(()=>{
  const r=RiskLab.random(47),n=150000;let sum=0,sumsq=0,normal=0,nsq=0;
  for(let i=0;i<n;i++){const x=r.student(5),y=r.normal();sum+=x;sumsq+=x*x;normal+=y;nsq+=y*y;}
  return {tMean:sum/n,tVariance:sumsq/n-(sum/n)**2,normalMean:normal/n,normalVariance:nsq/n-(normal/n)**2};
 });
 assert.ok(Math.abs(moments.tMean)<.025);assert.ok(Math.abs(moments.tVariance-5/3)<.08);assert.ok(Math.abs(moments.normalVariance-1)<.015);
 await page.locator('#reset-inputs').click();
 const sizes=[];
 for(const width of [320,390,768,978,1440]){
  await page.setViewportSize({width,height:850});
  const m=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,tocColumns:getComputedStyle(document.querySelector('.toc-columns')).gridTemplateColumns.split(' ').length}));
  assert.ok(m.documentWidth<=width+1,'Body overflow at '+width);assert.equal(m.tocColumns,width<=760?1:3);sizes.push(m);
 }
 await page.setViewportSize({width:978,height:850});await page.goto(url);await page.screenshot({path:path.join(root,'hero-desktop.png')});
 for(const [name,selector] of [['contents','.toc'],['formula','#expected-shortfall'],['laboratory','#risk-notebook'],['examples','#examples']]){
  await page.locator(selector).scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,name+'-desktop.png')});
 }
 let panels=0;
 const figs=page.locator('figure');
 for(let i=0;i<await figs.count();i++){
  const fig=figs.nth(i);await fig.scrollIntoViewIfNeeded();const axes=JSON.parse(await fig.locator('.chart-data').textContent()).axes;
  const svg=fig.locator('svg').first(),rect=await svg.boundingBox(),vb=await svg.getAttribute('viewBox'),dims=vb.split(' ').map(Number);
  for(const ax of axes){
   const a=ax.box,px=(a[0]+a[2]*.52)/dims[2]*rect.width+rect.x,py=(a[1]+a[3]*.45)/dims[3]*rect.height+rect.y;
   await page.mouse.move(px,py);assert.ok(await page.locator('#chart-coordinate-tooltip').isVisible(),'Hover figure '+i);
   const card=await page.locator('#chart-coordinate-tooltip').innerText();assert.ok(card.length>10);panels++;
  }
 }
 await page.locator('#live-plot svg').scrollIntoViewIfNeeded();await page.locator('#live-plot svg').focus();await page.keyboard.press('Home');assert.ok(await page.locator('#chart-coordinate-tooltip').isVisible());assert.match(await page.locator('#chart-coordinate-tooltip').innerText(),/%/);await page.keyboard.press('Escape');
 await page.setViewportSize({width:390,height:844});await page.goto(url);await page.screenshot({path:path.join(root,'hero-mobile.png')});await page.locator('#risk-notebook').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,'laboratory-mobile.png')});
 const touch=await browser.newContext({hasTouch:true,isMobile:true,viewport:{width:390,height:844}}),tp=await touch.newPage();await tp.goto(url);await tp.locator('#live-plot svg').scrollIntoViewIfNeeded();
 await tp.waitForTimeout(150);
 const rect=await tp.locator('#live-plot svg').boundingBox();
 await tp.touchscreen.tap(rect.x+200,rect.y+100);
 await tp.waitForFunction(()=>!document.getElementById('chart-coordinate-tooltip').hidden);
 await tp.screenshot({path:path.join(root,'laboratory-touch.png')});await touch.close();
 const context=await browser.newContext({javaScriptEnabled:false}),staticPage=await context.newPage();await staticPage.goto(url);assert.equal(await staticPage.locator('figure svg').count(),17);assert.equal(await staticPage.locator('math').count(),246);await context.close();
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 const report={structure,independentAnalyticalCases:cases.length,maxRelativeError,empiricalBoundaryCases:empiricalCases.length,generatorMoments:moments,hoverPanels:panels,keyboardAndTouch:'passed',sizes,errors,externalRuntimeRequests:requests};
 fs.writeFileSync(path.join(root,'verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
