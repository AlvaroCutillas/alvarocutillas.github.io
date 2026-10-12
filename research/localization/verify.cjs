const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const site=path.resolve(__dirname,'../..');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const p=await b.newPage({viewport:{width:1440,height:900}}),errors=[],report=[];
 p.on('pageerror',e=>errors.push(e.message));
 for(const name of ['index.html',...fs.readdirSync(site+'/projects').filter(n=>n.endsWith('.html'))]){
  const url=pathToFileURL(path.join(site,name==='index.html'?'':'projects',name)).href;
  await p.goto(url);await p.waitForFunction(()=>window.PortfolioI18n);
  await p.evaluate(()=>localStorage.setItem('portfolio-language','es'));
  await p.reload();await p.waitForFunction(()=>window.PortfolioI18n);
  assert.equal(await p.locator('html').getAttribute('lang'),'en',name+' must ignore old Spanish preference');
  assert.equal(await p.locator('#page-language').inputValue(),'en');
  const original=await p.evaluate(()=>({h1:document.querySelector('h1').textContent,math:[...document.querySelectorAll('math,pre,code')].map(n=>n.outerHTML)}));
  await p.locator('#page-language').selectOption('es');
  assert.equal(await p.locator('html').getAttribute('lang'),'es');
  assert.match(p.url(),/lang=es/);
  assert.deepEqual(await p.evaluate(()=>[...document.querySelectorAll('math,pre,code')].map(n=>n.outerHTML)),original.math);
  await p.reload();await p.waitForFunction(()=>window.PortfolioI18n?.language==='es');
  for(const width of [320,390,978,1440]){
   await p.setViewportSize({width,height:900});
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),name+' overflow');
   assert.ok(await p.locator('#page-language').isVisible());
  }
  await p.locator('#page-language').selectOption('en');
  assert.equal(await p.locator('h1').textContent(),original.h1);
  await p.goto(url);await p.waitForFunction(()=>window.PortfolioI18n?.language==='en');
  report.push({name,defaultEnglish:true,switching:true,mobile:true,mathPreserved:true});
  console.log(name+' passed');
 }
 await p.goto(pathToFileURL(path.join(site,'index.html')).href);
 await p.locator('#page-language').selectOption('es');
 assert.equal(await p.locator('#contact h2').textContent(),'¿Buscas un perfil cuantitativo?');
 await p.setViewportSize({width:1440,height:900});await p.locator('#contact').scrollIntoViewIfNeeded();
 await p.screenshot({path:__dirname+'/dropdown-cta-es.png'});
 await p.locator('#quant-basics a.project-card').last().click();await p.waitForFunction(()=>window.PortfolioI18n?.language==='es');
 assert.equal(await p.locator('#page-language').inputValue(),'es');
 await p.locator('#input-train').fill('120');await p.locator('#calculate').click();await p.waitForTimeout(100);
 assert.match(await p.locator('#model-status').textContent(),/MCO en los meses 1–120/);
 await p.locator('#page-language').focus();await p.keyboard.press('Home');
 assert.equal(await p.evaluate(()=>PortfolioI18n.language),'en');
 await p.keyboard.press('End');assert.equal(await p.evaluate(()=>PortfolioI18n.language),'es');
 await p.emulateMedia({media:'print'});assert.equal(await p.locator('#page-language').isVisible(),false);
 await p.emulateMedia({media:'screen'});
 await p.goto(pathToFileURL(path.join(site,'index.html')).href);await p.setViewportSize({width:390,height:844});
 await p.screenshot({path:__dirname+'/dropdown-mobile-en.png'});
 assert.deepEqual(errors,[]);
 fs.writeFileSync(__dirname+'/dropdown-verification.json',JSON.stringify({pages:report,errors,navigation:true,dynamicLaboratory:true,keyboard:true,print:true},null,2));
 await b.close();console.log('All dropdown checks passed.');
})().catch(e=>{console.error(e);process.exit(1)});
