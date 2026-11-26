// Records short videos of the movement scenarios (real Chromium, real keyboard input).
// Usage: BASE=... OUT=browser-evidence/motion/videos node tests/motion-videos.mjs
import {chromium} from 'playwright';
import {mkdir} from 'node:fs/promises';
const BASE=process.env.BASE||'http://127.0.0.1:8099/game2/';const OUT=process.env.OUT||'browser-evidence/motion/videos';
const args=process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[];
await mkdir(OUT,{recursive:true});
const browser=await chromium.launch({headless:true,args});
const trims={};async function scene(name,fn){const t0=Date.now();const ctx=await browser.newContext({viewport:{width:960,height:600},recordVideo:{dir:OUT+'/tmp',size:{width:960,height:600}}});const page=await ctx.newPage();
 await page.goto(BASE,{waitUntil:'networkidle'});await page.evaluate(()=>localStorage.clear());await page.reload({waitUntil:'networkidle'});await page.locator('#loading').waitFor({state:'detached',timeout:20000}).catch(()=>{});
 await page.locator('#startGame').click();await page.waitForTimeout(700);trims[name]=(Date.now()-t0)/1000;
 await page.evaluate(()=>{window.__place=(x,y)=>{s.x=Math.round(x);s.y=Math.round(y);s.px=x;s.py=y;heroVis.x=x;heroVis.y=y;MOT.vx=MOT.vy=0;$('dialog').replaceChildren();$('puzzle').replaceChildren()}});
 await fn(page);await page.waitForTimeout(300);const v=page.video();await ctx.close();await v.saveAs(`${OUT}/${name}.webm`);await v.delete();console.log('video',name)}
const hold=async(page,keys,ms)=>{for(const k of keys)await page.keyboard.down(k);await page.waitForTimeout(ms);for(const k of keys)await page.keyboard.up(k)};
await scene('1-free-walk',async p=>{await p.evaluate(()=>__place(5,5));for(const [k,ms] of [[['d'],900],[['s'],700],[['a'],900],[['w'],800],[['d'],600]])await hold(p,k,ms)});
await scene('2-diagonal',async p=>{await p.evaluate(()=>__place(6,8));for(const k of [['w','d'],['s','d'],['s','a'],['w','a']])await hold(p,k,700)});
await scene('3-around-a-house',async p=>{await p.evaluate(()=>{s.t=1200;render();__place(8.8,4.3)});await hold(p,['w'],1700);await hold(p,['a'],500);await hold(p,['s'],900)});
await scene('4-wall-collision',async p=>{await p.keyboard.press('F3');await p.evaluate(()=>{s.t=1200;render();__place(8.2,4.4)});await hold(p,['w','d'],1600);await hold(p,['w'],900)});
await scene('5-avoid-npc',async p=>{const id=await p.evaluate(()=>{const e=Object.entries(npcVis).find(([i,v])=>!v.path?.length);__place(e[1].x+1.2,e[1].y+.15);return e[0]});
 await p.evaluate(id=>{const v=npcVis[id];const dx=v.x-s.px,dy=v.y-s.py;const l=Math.hypot(dx-dy,(dx+dy)/2);INPUT.touch=[(dx-dy)/l,(dx+dy)/2/l]},id);await p.waitForTimeout(1500);await p.evaluate(()=>INPUT.touch=null);await hold(p,['w'],700)});
await scene('6-npcs-crossing',async p=>{await p.keyboard.press('F3');await p.evaluate(()=>{const a=AMB.list.find(a=>a.key==='m-guarda');__place(6,7);cam.user=.8});await p.waitForTimeout(6000)});
await scene('7-interior',async p=>{await p.evaluate(()=>{__place(2,6);interact()});await p.waitForTimeout(500);await hold(p,['d'],1800);await p.keyboard.press('e');await p.waitForTimeout(600);await hold(p,['a'],1500);await hold(p,['d'],600)});
await scene('8-run-and-sneak',async p=>{await p.evaluate(()=>__place(5,5));await p.keyboard.down('Shift');await hold(p,['d'],900);await p.keyboard.up('Shift');await p.waitForTimeout(200);await p.keyboard.press('c');await hold(p,['s'],1400);await p.keyboard.press('c');await hold(p,['a'],700)});
await browser.close();
const {writeFile}=await import('node:fs/promises');await writeFile(`${OUT}/trims.json`,JSON.stringify(trims));
