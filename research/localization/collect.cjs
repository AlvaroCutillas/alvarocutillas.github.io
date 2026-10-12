const fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root=path.resolve(__dirname,'../..');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 const page=await browser.newPage(),result={};
 const files=[path.join(root,'index.html'),...fs.readdirSync(path.join(root,'projects')).filter(n=>n.endsWith('.html')).map(n=>path.join(root,'projects',n))];
 for(const file of files){
  await page.goto(pathToFileURL(file).href+'?lang=en');await page.waitForTimeout(120);
  result[path.basename(file)]=await page.evaluate(()=>{
   const values=new Set(),norm=t=>t.replace(/\s+/g,' ').trim();
   const ignored=e=>e.closest('script,style,pre,code,kbd,samp,.brand,.references li,.formula,.language-switch')||e.closest('math')||e.closest('svg metadata');
   const walker=document.createTreeWalker(document.documentElement,NodeFilter.SHOW_TEXT);
   while(walker.nextNode()){const n=walker.currentNode;if(!n.parentElement||ignored(n.parentElement))continue;const text=norm(n.data);if(/[a-zA-Z]{2}/.test(text))values.add(text);}
   for(const e of document.querySelectorAll('[aria-label],[title],[placeholder],[alt],meta[name="description"]')){
    if(ignored(e))continue;
    for(const a of ['aria-label','title','placeholder','alt',...(e.matches('meta')?['content']:[])]){const v=norm(e.getAttribute(a)||'');if(/[a-zA-Z]{2}/.test(v))values.add(v);}
   }
   return {values:[...values],h1:[...document.querySelector('h1').childNodes].flatMap(n=>n.nodeType===3?[n.textContent.trim()]:n.nodeType===1?[n.textContent.trim()]:[]).filter(Boolean)};
  });
  console.log(path.basename(file)+': '+result[path.basename(file)].values.length+' text units');
 }
 fs.writeFileSync(path.join(__dirname,'page-texts.json'),JSON.stringify(result,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
