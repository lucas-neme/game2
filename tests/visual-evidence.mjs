// Visual evidence in real Chromium: captures the states listed in docs/art-direction/HOMOLOGACAO.md.
// Usage: BASE=https://wampa.com.br/game2/ OUT=browser-evidence/visual node tests/visual-evidence.mjs
import {chromium} from 'playwright';
import {mkdir} from 'node:fs/promises';
const BASE=process.env.BASE||'http://127.0.0.1:8099/game2/';const OUT=process.env.OUT||'browser-evidence/visual';
const args=process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[];
await mkdir(OUT,{recursive:true});
const browser=await chromium.launch({headless:true,args});
const shots=[];const errors=[];
async function session(vp,fn){const ctx=await browser.newContext({viewport:vp,...(vp.width<500?{isMobile:true,hasTouch:true}:{})});const page=await ctx.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(BASE,{waitUntil:'networkidle'});await page.evaluate(()=>localStorage.clear());await page.reload({waitUntil:'networkidle'});await page.locator('#loading').waitFor({state:'detached',timeout:20000}).catch(()=>{});
 await fn(page);await ctx.close()}
const shot=async(page,name)=>{await page.waitForTimeout(450);await page.screenshot({path:`${OUT}/${name}.png`});shots.push(name)};
const town=page=>page.evaluate(()=>{if(s.room)leaveRoom();$('puzzle').replaceChildren();$('dialog').replaceChildren()});
const setT=(page,t,extra='')=>page.evaluate(([t,extra])=>{s.t=t;s.worldClock=Math.max(s.worldClock||0,t);if(extra)eval(extra);render()},[t,extra]);
await session({width:1366,height:820},async page=>{
 await shot(page,'00-title');await page.locator('#startGame').click();await page.waitForTimeout(800);
 await shot(page,'01-town-day');
 for(const k of ['d','d','s'])await page.keyboard.press(k);await page.waitForTimeout(120);await shot(page,'02-hero-walking');
 await town(page);await page.evaluate(()=>{const n=residents().find(p=>p.id==='future');s.x=n.x-1;s.y=n.y;heroVis.x=s.x;heroVis.y=s.y;render()});await page.keyboard.press('e');await shot(page,'03-dialogue-portrait');
 await page.evaluate(()=>{const a=AMB.list.find(a=>a.key==='m-comerciante');a.x=4;a.y=6;s.x=4;s.y=7;heroVis.x=4;heroVis.y=7;heroVis.x=s.x;heroVis.y=s.y;a.path=[];a.wait=99;render()});await page.waitForTimeout(200);await page.evaluate(()=>interact());await shot(page,'04-ambient-resident');await town(page);
 await page.evaluate(()=>{s.x=5;s.y=5;heroVis.x=5;heroVis.y=5;$('dialog').replaceChildren();render()});
 await town(page);await setT(page,1290);await page.waitForTimeout(500);await shot(page,'05-town-night');
 await setT(page,1080);await shot(page,'06-town-dusk');
 await setT(page,2280);await shot(page,'07-rain');
 await setT(page,1620);await shot(page,'08-fog-night');
 await setT(page,600);await page.evaluate(()=>uiJournal(true));await shot(page,'09-journal');await page.evaluate(()=>uiJournal(false));
 await page.evaluate(()=>uiMap(true));await shot(page,'10-map');await page.evaluate(()=>uiMap(false));
 await page.evaluate(()=>{s.x=2;s.y=4;heroVis.x=2;heroVis.y=4;render()});await page.keyboard.press('e');await shot(page,'11-interior-study');await page.locator('#leave').click().catch(()=>{});
 await town(page);await page.evaluate(()=>{s.x=2;s.y=6;heroVis.x=2;heroVis.y=6;render()});await page.keyboard.press('e');await shot(page,'12-interior-station');await page.locator('#leave').click().catch(()=>{});
 await town(page);const enc=await page.evaluate(()=>{try{s.clues.push('warning');s.x=1;s.y=7;heroVis.x=1;heroVis.y=7;render();if(typeof encounterAvailable==='function'&&encounterAvailable()){beginEncounter();render();return true}}catch(e){return String(e)}return false});
 await page.waitForTimeout(1200);await shot(page,'13-encounter-'+(enc===true?'live':'unavailable'));
});
await session({width:390,height:844},async page=>{await page.locator('#startGame').tap();await page.waitForTimeout(800);await shot(page,'14-mobile-town');await page.evaluate(()=>uiJournal(true));await shot(page,'15-mobile-journal')});
await browser.close();
console.log('shots',shots.join(' '));console.log('page errors',errors.length?errors.join(' | '):'none');
