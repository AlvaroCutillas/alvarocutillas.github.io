/* Offline EN/ES text rendering. Equations, code and numerical data stay intact. */
(() => {
 'use strict';
 const payload=JSON.parse(document.getElementById('portfolio-language-data').textContent);
 const catalogue=payload.es||{},fragments=payload.fragments||{};
 const normalize=value=>value.replace(/\s+/g,' ').trim();
 const escape=value=>value.replace(/[.*+?^{}$()|[\]\\]/g,'\\$&');
 const fragmentKeys=Object.keys(fragments).sort((a,b)=>b.length-a.length);
 const fragmentLookup=new Map(fragmentKeys.map(k=>[k.toLowerCase(),fragments[k]]));
 const pattern=fragmentKeys.length?new RegExp('(?<![A-Za-z])(?:'+fragmentKeys.map(escape).join('|')+')(?![A-Za-z])','gi'):null;
 const textRecords=new WeakMap(),attributeRecords=new WeakMap(),linkRecords=new WeakMap(),svgRecords=new WeakMap();
 const missing=new Set();
 let language='en',observer=null,active=false,explicit=false;
 function translate(value){
  if(language==='en'||!value)return value;
  const key=normalize(value),exact=catalogue[key];
  if(exact!==undefined)return value.match(/^\s*/)[0]+exact+value.match(/\s*$/)[0];
  if(!/[a-zA-Z]{2}/.test(key))return value;
  const translated=pattern?value.replace(pattern,m=>fragmentLookup.get(m.toLowerCase())):value;
  if(translated===value)missing.add(key);
  return translated;
 }
 function excluded(element){
  return !element||element.closest('script,style,pre,code,kbd,samp,.brand,.references li,.formula,.language-switch,[translate="no"]')||
   element.closest('math')||element.closest('svg metadata');
 }
 function renderText(node){
  if(excluded(node.parentElement))return;
  let record=textRecords.get(node);
  if(!record){record={english:node.data,last:node.data};textRecords.set(node,record);}
  else if(node.data!==record.last){record.english=node.data;}
  let result=translate(record.english);
  if(language==='es'&&node.parentElement.closest('h1')&&payload.heading){
   const h1=document.querySelector('h1'),nodes=[...h1.childNodes].flatMap(n=>n.nodeType===3?[n]:n.nodeType===1?[...n.childNodes].filter(c=>c.nodeType===3):[]).filter(n=>normalize(n.data));
   const index=nodes.indexOf(node);if(index>=0&&payload.heading[index])result=payload.heading[index];
  }
  record.last=result;if(node.data!==result)node.data=result;
 }
 function renderAttributes(element){
  if(excluded(element))return;
  let record=attributeRecords.get(element);if(!record){record=new Map();attributeRecords.set(element,record);}
  for(const attr of ['aria-label','title','placeholder','alt',...(element.matches('meta[name="description"]')?['content']:[])]){
   const value=element.getAttribute(attr);if(value===null)continue;
   let item=record.get(attr);
   if(!item){item={english:value,last:value};record.set(attr,item);}else if(value!==item.last){item.english=value;}
   item.last=translate(item.english);if(value!==item.last)element.setAttribute(attr,item.last);
  }
 }
 function fitSVG(root){
  const texts=root.matches?.('svg text')?[root]:[...(root.querySelectorAll?.('svg text')||[])];
  for(const text of texts){
   if(!text.isConnected||!text.getComputedTextLength)continue;
   let record=svgRecords.get(text);
   if(!record){const size=parseFloat(getComputedStyle(text).fontSize);record={size,length:text.getComputedTextLength()};svgRecords.set(text,record);}
   text.style.fontSize=record.size+'px';
   if(language==='es'&&record.length>65){
    const translated=text.getComputedTextLength();if(translated>record.length*1.12)text.style.fontSize=(record.size*Math.max(.78,record.length*1.12/translated))+'px';
   }
  }
 }
 function walk(root){
  if(root.nodeType===3){renderText(root);return;}
  if(root.nodeType!==1&&root.nodeType!==9)return;
  if(root.nodeType===1&&excluded(root))return;
  if(root.nodeType===1)renderAttributes(root);
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  while(walker.nextNode())renderText(walker.currentNode);
  for(const element of root.querySelectorAll?.('[aria-label],[title],[placeholder],[alt],meta[name="description"]')||[])renderAttributes(element);
 }
 function links(root=document){
  if(!explicit&&language==='en')return;
  for(const anchor of root.querySelectorAll?.('a[href]')||[]){
   let original=linkRecords.get(anchor);if(original===undefined){original=anchor.getAttribute('href');linkRecords.set(anchor,original);}
   if(!original||original.startsWith('#')||/^(mailto:|tel:|javascript:)/i.test(original))continue;
   try{
    const url=new URL(original,location.href);
    if(url.protocol!==location.protocol||url.host!==location.host||!/(?:\.html|\/)$/i.test(url.pathname))continue;
    url.searchParams.set('lang',language);
    anchor.setAttribute('href',url.href);
   }catch(_){}
  }
 }
 function updateControls(){
  const select=document.querySelector('.language-switch select');if(!select)return;
  select.value=language;
  select.setAttribute('aria-label',language==='es'?'Idioma de la página':'Page language');
 }
 function observe(){observer?.observe(document.documentElement,{subtree:true,childList:true,characterData:true});}
 function change(next,{persist=true}={}){
  if(next!=='en'&&next!=='es')return;
  observer?.disconnect();language=next;document.documentElement.lang=next;
  if(persist){
   explicit=true;
   try{const url=new URL(location.href);url.searchParams.set('lang',next);history.replaceState(history.state,'',url);}catch(_){}
  }
  walk(document.documentElement);fitSVG(document);links();updateControls();
  window.ChartCoordinates?.hide();
  observe();window.dispatchEvent(new CustomEvent('portfolio:languagechange',{detail:{language:next}}));
 }
 const select=document.querySelector('.language-switch select');
 select?.addEventListener('change',()=>change(select.value));
 observer=new MutationObserver(records=>{
  if(active)return;active=true;observer.disconnect();
  const roots=new Set();
  for(const record of records){
   if(record.type==='characterData')roots.add(record.target);
   else for(const node of record.addedNodes)if(node.nodeType===1||node.nodeType===3)roots.add(node);
  }
  for(const root of roots)if(root.isConnected){if(root.nodeType===1)fitSVG(root);walk(root);if(root.nodeType===1){fitSVG(root);links(root);}}
  active=false;observe();
 });
 let chosen=new URL(location.href).searchParams.get('lang');
 if(chosen==='en'||chosen==='es')explicit=true;
 // Bare URLs always open in English; explicit language links retain the reader's choice.
 const nav=document.querySelector('nav');
 if(nav&&window.ResizeObserver)new ResizeObserver(()=>document.documentElement.style.setProperty('--portfolio-nav-height',nav.getBoundingClientRect().height+'px')).observe(nav);
 window.PortfolioI18n={setLanguage:change,t:translate,get language(){return language;},get missing(){return [...missing];},locale:()=>language==='es'?'es-ES':'en-US'};
 fitSVG(document);change(chosen==='es'?'es':'en',{persist:false});
})();
