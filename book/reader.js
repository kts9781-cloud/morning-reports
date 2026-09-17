'use strict';
(() => {
 const root=document.documentElement, $=id=>document.getElementById(id), key='autonomy-book-v1';
 let data={};try{data=JSON.parse(localStorage.getItem(key)||'{}')||{};}catch{};
 if(typeof data!=='object'||Array.isArray(data))data={};
 let size=Math.max(16,Math.min(26,Number(data.size)||19));
 let theme=['light','dark'].includes(data.theme)?data.theme:(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
 let saving=false, timer, notifyTimer;
 const stored=(data.position&&typeof data.position.id==='string'&&/^p\d+$/.test(data.position.id)&&$(data.position.id))?data.position:null;
 function persist(){try{localStorage.setItem(key,JSON.stringify(data));}catch{}}
 function apply(){root.style.setProperty('--size',size+'px');root.dataset.theme=theme;$('size').textContent=size;$('smaller').disabled=size<=16;$('larger').disabled=size>=26;$('theme').textContent=theme==='dark'?'낮 모드':'밤 모드';$('theme').setAttribute('aria-pressed',String(theme==='dark'));data.size=size;data.theme=theme;persist();}
 apply();
 const blocks=[...document.querySelectorAll('#book [data-reading]')];
 function position(){let active=null;for(const e of blocks){if(e.getBoundingClientRect().top<=105)active=e;else break;}if(!active)return null;const r=active.getBoundingClientRect();return {id:active.id,ratio:Math.max(0,Math.min(1,(90-r.top)/Math.max(1,r.height)))};}
 function go(p){const e=$(p.id);if(!e)return;const ratio=Math.max(0,Math.min(1,Number(p.ratio)||0));scrollTo(0,scrollY+e.getBoundingClientRect().top+e.getBoundingClientRect().height*ratio-90);}
 function progress(){const book=$('book'),start=scrollY+book.getBoundingClientRect().top,end=start+book.offsetHeight-innerHeight+90;const pct=Math.max(0,Math.min(100,Math.round((scrollY-start+90)/Math.max(1,end-start)*100)));$('percent').textContent=pct+'%';$('progress').style.width=pct+'%';const p=position();if(p){const section=$(p.id).closest('section');$('current').textContent=section?section.querySelector('h2').textContent:'모바일 웹북';if(saving){data.position=p;persist();$('resume').hidden=false;}}else $('current').textContent='모바일 웹북';}
 function resize(delta){const p=position();size=Math.max(16,Math.min(26,size+delta));apply();if(p)go(p);progress();}
 $('smaller').onclick=()=>resize(-1);$('larger').onclick=()=>resize(1);
 $('theme').onclick=()=>{theme=theme==='dark'?'light':'dark';apply();};
 const dialog=$('toc');$('toc-open').onclick=()=>{dialog.showModal();document.body.style.overflow='hidden';};
 function close(){dialog.close();document.body.style.overflow='';}
 $('toc-close').onclick=close;dialog.addEventListener('close',()=>{document.body.style.overflow='';});
 dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)close();}});
 dialog.querySelectorAll('a').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const id=a.hash.slice(1);close();history.replaceState(null,'','#'+id);go({id,ratio:0});saving=true;progress();}));
 document.querySelector('.start').addEventListener('click',()=>{saving=true;});
 if(stored)$('resume').hidden=false;
 $('resume').onclick=()=>{const p=data.position||stored;if(p){go(p);saving=true;progress();}};
 for(const event of ['wheel','touchstart','keydown','pointerdown'])addEventListener(event,()=>{saving=true;},{once:true,passive:true});
 addEventListener('scroll',()=>{clearTimeout(timer);timer=setTimeout(progress,160);},{passive:true});
 addEventListener('pagehide',()=>{if(saving){const p=position();if(p){data.position=p;persist();}}});
 // A link into a chapter takes priority over the saved place. Restoration is explicit.
 Promise.all([document.fonts.ready,new Promise(resolve=>{if(document.readyState==='complete')resolve();else addEventListener('load',resolve,{once:true});})]).then(()=>{if(location.hash&&$(location.hash.slice(1)))go({id:location.hash.slice(1),ratio:0});progress();});
})();
