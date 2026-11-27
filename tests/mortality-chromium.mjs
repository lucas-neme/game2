// Mortality in real Chromium: resident death (plays once, body stays, leaves routines/dialogue, persists across reload),
// recoverable defeat (injured -> downed -> wakes) and definitive hero death in Challenge mode (game over, survives reload,
// recover previous save). Usage: BASE=http://127.0.0.1:8099/game2/ node tests/mortality-chromium.mjs
import assert from 'node:assert/strict';import {chromium} from 'playwright';import {mkdir} from 'node:fs/promises';
const BASE=process.env.BASE||'http://127.0.0.1:8092/game2/';const OUT=process.env.OUT||'browser-evidence/mortality';
const launchArgs=process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[];
await mkdir(OUT,{recursive:true});const ok=(n,x='')=>console.log('PASS:',n,x);
const browser=await chromium.launch({args:launchArgs});const page=await browser.newPage({viewport:{width:1280,height:800}});
const errs=[];page.on('pageerror',e=>errs.push(String(e)));
async function start(){await page.locator('#loading').waitFor({state:'detached',timeout:60000}).catch(()=>{});await page.locator('#startGame').click();await page.waitForFunction(()=>UI.started)}
await page.goto(BASE,{waitUntil:'networkidle'});await page.evaluate(()=>localStorage.clear());await page.reload({waitUntil:'networkidle'});await start();
// manual save = the "previous save" offered after a death
await page.evaluate(()=>document.getElementById('save').click());
// --- resident death ------------------------------------------------------------------------------------------
const id=await page.evaluate(()=>{const p=residents().find(q=>q.id==='clinic')||residents()[0];const v=npcVis[p.id];s.px=v.x+.8;s.py=v.y+.8;heroVis.x=s.px;heroVis.y=s.py;return p.id});
await page.waitForTimeout(400);
await page.evaluate(id=>FZ_MORT.kill(id,'teste de homologação'),id);
const frames=[];for(let i=0;i<14;i++){await page.waitForTimeout(140);const r=await page.evaluate(id=>({anim:npcVis[id].v5anim,mort:npcVis[id].mort}),id);frames.push(r);
 const box=await page.evaluate(id=>{const v=npcVis[id];const [x,y]=iso(v.x,v.y);return worldToScreen(x,y)},id);
 await page.screenshot({path:`${OUT}/npc-death-${String(i).padStart(2,'0')}.png`,clip:{x:Math.max(0,box[0]-110),y:Math.max(0,box[1]-130),width:220,height:170}})}
assert(frames.some(f=>f.mort==='DYING')&&frames.at(-1).mort==='DEAD','dying then dead '+JSON.stringify(frames.map(f=>f.mort)));
assert(frames.every(f=>f.anim.startsWith('death')),'death animation '+JSON.stringify(frames.map(f=>f.anim)));
const diag=await page.evaluate(()=>FZ_DIAG());const dl=diag.find(r=>r.animacao.startsWith('death'));assert(dl&&/characters\/v6\//.test(dl.png),'V6 death png '+JSON.stringify(dl));
ok('resident death plays once and holds the last frame',JSON.stringify(dl));
const gone=await page.evaluate(id=>({res:residents().some(p=>p.id===id),fate:s.fates['dead_'+id],cons:s.consequences.some(c=>c.id==='death:'+id),case:s.personalCases[id]?.closed}),id);
assert(!gone.res&&gone.fate&&gone.cons&&gone.case==='death',JSON.stringify(gone));ok('dead resident leaves routines and dialogue; journal, fate and personal case updated',JSON.stringify(gone));
const pos1=await page.evaluate(id=>[npcVis[id].x,npcVis[id].y],id);await page.evaluate(()=>advance(120));await page.waitForTimeout(500);
const pos2=await page.evaluate(id=>[npcVis[id].x,npcVis[id].y],id);assert.deepEqual(pos1,pos2,'body does not move');ok('body stays where it fell after 2 h');
await page.reload({waitUntil:'networkidle'});await start();await page.waitForTimeout(600);
const after=await page.evaluate(id=>({st:s.mortality.npcs[id]?.state,res:residents().some(p=>p.id===id),anim:npcVis[id]?.v5anim}),id);
assert(after.st==='DEAD'&&!after.res&&after.anim?.startsWith('death'),'persists '+JSON.stringify(after));ok('death persists across reload',JSON.stringify(after));
// --- recoverable defeat (normal mode) ---------------------------------------------------------------------------
await page.evaluate(()=>{s.combatMode='normal';s.mortality.hero={state:'ALIVE',defeats:0}});
const n1=await page.evaluate(()=>FZ_MORT.defeat('teste'));const n2=await page.evaluate(()=>FZ_MORT.defeat('teste'));
assert.equal(n1,'INJURED');assert.equal(n2,'DOWNED');await page.waitForTimeout(400);
const hd=await page.evaluate(()=>FZ_DIAG().find(r=>r.personagem==='hero'));assert(hd.animacao.startsWith('death')&&hd.quadro===3,'downed pose '+JSON.stringify(hd));
await page.screenshot({path:`${OUT}/hero-downed.png`});
const n3=await page.evaluate(()=>FZ_MORT.defeat('teste'));assert.equal(n3,'DOWNED','normal mode never kills');
await page.waitForFunction(()=>s.mortality.hero.state==='INJURED',null,{timeout:8000});ok('recoverable defeat: injured -> downed -> wakes injured (normal mode never kills)');
// --- definitive death (challenge mode) --------------------------------------------------------------------------
await page.evaluate(()=>{s.combatMode='challenge';s.mortality.hero={state:'ALIVE',defeats:0};document.getElementById('save').click();localStorage.removeItem('fz-demo-v2-before-death')});
for(const want of ['INJURED','DOWNED','DYING'])assert.equal(await page.evaluate(()=>FZ_MORT.defeat('teste')),want);
for(let i=0;i<10;i++){await page.waitForTimeout(160);await page.screenshot({path:`${OUT}/hero-death-${String(i).padStart(2,'0')}.png`})}
await page.waitForSelector('#gameOver',{timeout:5000});assert.equal(await page.evaluate(()=>s.mortality.hero.state),'DEAD');
ok('hero death in Challenge mode ends the run');
await page.reload({waitUntil:'networkidle'});await page.waitForSelector('#gameOver',{timeout:5000});ok('reload does not revive the hero');
await page.screenshot({path:`${OUT}/game-over.png`});
await Promise.all([page.waitForNavigation({waitUntil:'networkidle'}),page.click('#goRecover')]);await start();
const rec=await page.evaluate(()=>s.mortality.hero.state);assert.equal(rec,'ALIVE','recovered previous save');ok('recover previous save restores the hero',rec);
assert.equal(errs.length,0,errs.join('\n'));await browser.close();console.log('ALL MORTALITY CHECKS PASSED');
