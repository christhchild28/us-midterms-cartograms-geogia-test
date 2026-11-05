const {chromium}=require('playwright');const fs=require('fs');
const W=720,H=900,STEP=50;
(async()=>{const b=await chromium.launch();
const ctx=await b.newContext({viewport:{width:W,height:H},deviceScaleFactor:1,colorScheme:'light'});
const p=await ctx.newPage();
await p.addInitScript(()=>{let now=0,id=0;let cbs=[];let timers=[];
 window.__vt={step(ms){now+=ms;const q=cbs;cbs=[];q.forEach(f=>f(now));const due=timers.filter(t=>t.t<=now);timers=timers.filter(t=>t.t>now);due.forEach(t=>t.f(...t.a));}};
 performance.now=()=>now;window.requestAnimationFrame=f=>{cbs.push(f);return ++id};window.cancelAnimationFrame=()=>{};
 window.setTimeout=(f,ms,...a)=>{timers.push({t:now+(ms||0),f,a});return ++id};});
await p.goto('file:///tmp/ga/gif/capture.html');
await p.waitForFunction(()=>!document.getElementById('bLens').disabled,{timeout:15000});
await p.addStyleTag({content:`
 body{padding:0!important;overflow:hidden}
 .wrap{max-width:none!important;margin:0!important}
 .wrap>*:not(.grid){display:none!important}
 .grid>aside{display:none!important}
 .grid{display:block!important}
 .tip{display:none!important}
 .mapwrap{position:absolute;left:0;right:0;top:206px;height:640px;max-width:none!important}
 svg.map{width:100%!important;height:100%!important}
 .ov{position:absolute;left:36px;right:36px;font-family:"Archivo","Helvetica Neue",Arial,sans-serif;z-index:9}
 .ov .k{font:500 15px/1 "IBM Plex Mono",ui-monospace,Menlo,monospace;letter-spacing:.09em;text-transform:uppercase;color:#75746f;top:0}
 .ov .h{font-weight:800;font-size:46px;line-height:1.02;letter-spacing:-.02em;color:#0b0b0b;margin:12px 0 10px}
 .ov .s{font-size:23px;line-height:1.3;color:#52514e}
 .ov.top{top:34px}
 .ov.bot{bottom:20px;display:flex;justify-content:space-between;align-items:center;font-size:14px;color:#75746f}
 .dots{display:flex;gap:16px}.dots i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}
`});
await p.evaluate(()=>{
 document.getElementById('tips').click();
 const top=document.createElement('div');top.className='ov top';top.innerHTML='<div class="k">Georgia · 2026 U.S. Senate</div><div class="h" id="oh"></div><div class="s" id="os"></div>';document.body.appendChild(top);
 const bot=document.createElement('div');bot.className='ov bot';bot.innerHTML='<div class="dots"><span><i style="background:#2a78d6"></i>Ossoff</span><span><i style="background:#d04a49"></i>Collins</span></div><div>AJC county results, 99% reporting · Census 2019</div>';document.body.appendChild(bot);
 window.__stage=(h,s)=>{document.getElementById('oh').textContent=h;document.getElementById('os').textContent=s};
});
let n=0;
async function shot(){await p.screenshot({path:`frames/f${String(n++).padStart(4,'0')}.png`});}
async function run(ms){for(let t=0;t<ms;t+=STEP){await p.evaluate(s=>window.__vt.step(s),STEP);await shot();}}
const stage=(h,s)=>p.evaluate(([h,s])=>window.__stage(h,s),[h,s]);
const S1=['By land area','Ossoff carried just 23% of Georgia.'];
await stage(...S1);await p.evaluate(s=>window.__vt.step(s),STEP);await run(1400);
await stage('Magnify the people','Atlanta swells as the lens passes over it.');
await p.evaluate(()=>window.__ga.setView('lens'));await run(1000);
const ch=await p.evaluate(()=>{const c=window.__ga.C.find(x=>x.name==='Chatham');return [c.cx,c.cy]});
await p.evaluate(([x,y])=>{window.__ga.lens.tx=x;window.__ga.lens.ty=y;window.__ga.lensKick();},ch);await run(1300);
await stage('Sized by residents','Every county, resized by population.');
await p.evaluate(()=>document.querySelector('#lsize button[data-s="2"]').click());await run(2500);
await stage('One hex = 10,000 people','59% of Georgians live in counties Ossoff won.');
await p.evaluate(()=>window.__ga.setView('pop'));await run(2800);
await stage(...S1);
await p.evaluate(()=>window.__ga.setView('land'));await run(1000);
console.log('frames',n);
await b.close()})();
