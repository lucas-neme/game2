// Performance probe in real Chromium: FPS counted from requestAnimationFrame plus FZ_PERF() per scenario.
// Usage: BASE=https://wampa.com.br/game2/ HOST_MAP="wampa.com.br <IPv4>" node tests/perf-probe.mjs
// GPU=0 forces software rendering (worst case). OUT holds screenshots and perf.json.
import {chromium} from 'playwright';import {mkdir,writeFile} from 'node:fs/promises';
const BASE=process.env.BASE||'http://127.0.0.1:8092/game2/';const OUT=process.env.OUT||'browser-evidence/perf';
const args=[...(process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[]),...(process.env.GPU==='0'?['--disable-gpu']:['--enable-gpu','--ignore-gpu-blocklist','--use-angle=d3d11'])];
await mkdir(OUT,{recursive:true});const browser=await chromium.launch({args});const page=await browser.newPage({viewport:{width:1600,height:900}});
const errs=[];page.on('pageerror',e=>errs.push(String(e)));
const tl=Date.now();await page.goto(BASE,{waitUntil:'domcontentloaded',timeout:180000});await page.evaluate(()=>localStorage.clear());await page.reload({waitUntil:'domcontentloaded',timeout:180000});
await page.locator('#loading').waitFor({state:'detached',timeout:300000}).catch(()=>{});const loadMs=Date.now()-tl;console.log('time to playable (ms)',loadMs);await page.locator('#startGame').click();await page.waitForFunction(()=>UI.started);
const gpu=await page.evaluate(()=>{const c=document.createElement('canvas').getContext('webgl');const d=c&&c.getExtension('WEBGL_debug_renderer_info');return d?c.getParameter(d.UNMASKED_RENDERER_WEBGL):'no webgl'});
async function measure(name,setup,ms=5000,hold=[]){await page.evaluate(setup||(()=>{}));for(const k of hold)await page.keyboard.down(k);await page.waitForTimeout(800);
 const r=await page.evaluate(ms=>new Promise(res=>{const ts=[];let t0=performance.now();function f(t){ts.push(t);if(t-t0<ms)requestAnimationFrame(f);else{const d=ts.slice(1).map((v,i)=>v-ts[i]).sort((a,b)=>a-b);res({fps:+(1000*(ts.length-1)/(ts.at(-1)-ts[0])).toFixed(1),p95ms:+d[Math.floor(d.length*.95)].toFixed(1),worstMs:+d.at(-1).toFixed(1)})}}requestAnimationFrame(f)}),ms);
 for(const k of hold)await page.keyboard.up(k);
 const perf=await page.evaluate(()=>typeof FZ_PERF==='function'?FZ_PERF():null);
 await page.screenshot({path:`${OUT}/${name}.png`});console.log(name.padEnd(12),JSON.stringify(r),'FZ_PERF',JSON.stringify({fps:perf?.fps,p95:perf?.p95FrameMs,render:perf?.averageRenderMs,scale:perf?.scale,skipped:perf?.skipped,water:perf?.water?.status}));
 return {name,...r,perf}}
const tp=(x,y)=>`s.x=${x};s.y=${y};s.px=${x};s.py=${y};heroVis.x=${x};heroVis.y=${y};`;
const res=[];
res.push(await measure('town-idle',null));
res.push(await measure('walk',null,5000,['ArrowRight']));
res.push(await measure('run',null,5000,['Shift','ArrowDown']));
res.push(await measure('lake',new Function(tp(11,11))));
await page.waitForFunction(()=>FZ_PERF().water?.status==='ready',null,{timeout:60000}).catch(()=>{});
res.push(await measure('lake-anim',null));
res.push(await measure('railway',new Function(tp(1,4))));
res.push(await measure('night',new Function(tp(5,5)+'s.t=Math.floor(s.t/1440)*1440+1320;')));
res.push(await measure('rain',new Function('s.t=1440*2+800;')));
res.push(await measure('npcs-plaza',new Function(tp(6,6)+'s.t=Math.floor(s.t/1440)*1440+600;')));
await page.evaluate(()=>{s.t=480;s.x=5;s.y=5;s.px=5;s.py=5;heroVis.x=5;heroVis.y=5;move(-1,0);move(-1,0);move(0,-1);interact()});
res.push(await measure('interior',null));
res.push(await measure('interior-walk',null,5000,['ArrowLeft']));
const water=await page.evaluate(()=>FZ_PERF().water);
await writeFile(`${OUT}/perf.json`,JSON.stringify({base:BASE,loadMs,gpu,water,errors:errs,results:res},null,1));
const fps=res.map(r=>r.fps);console.log('GPU',gpu,'| water',JSON.stringify(water));
console.log('SUMMARY avg',(fps.reduce((a,b)=>a+b,0)/fps.length).toFixed(1),'min',Math.min(...fps),'errors',errs.length);
await browser.close();
