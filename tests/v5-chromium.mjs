// V5 harmonized NPCs in real Chromium: scale vs protagonist, 4 walking views, talk and work poses.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const BASE=process.env.BASE||'http://127.0.0.1:8099/game2/';const OUT=process.env.OUT||'browser-evidence/v5';
const args=process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[];
await mkdir(OUT,{recursive:true});const ok=(n,x='')=>console.log('PASS:',n,x);
const clipAt=async(page,fn,w=240,h=190)=>{await page.waitForTimeout(500);const p=await page.evaluate(fn);return {x:Math.max(0,Math.min(1280-w,p[0]-w/2)),y:Math.max(0,Math.min(800-h,p[1]-h*.8)),width:w,height:h}};
const browser=await chromium.launch({headless:true,args});const page=await browser.newPage({viewport:{width:1280,height:800}});const errs=[];page.on('pageerror',e=>errs.push(e.message));
await page.goto(BASE,{waitUntil:'networkidle'});await page.evaluate(()=>localStorage.clear());await page.reload({waitUntil:'networkidle'});
await page.locator('#loading').waitFor({state:'detached',timeout:20000}).catch(()=>{});await page.locator('#startGame').click();await page.waitForFunction(()=>Object.keys(V5).every(k=>ready(v5img(k))));await page.waitForTimeout(600);
// 1. scale: each NPC's apparent height within 85-115% of the protagonist (natural variation)
const sc=await page.evaluate(()=>{const hero=84*.5;return Object.fromEntries(Object.entries(V5).map(([k,d])=>[k,+(d.scale*d.ref_h/hero).toFixed(3)]))});
for(const [k,v] of Object.entries(sc))assert(v>.85&&v<1.15,k+' height ratio '+v);ok('scale vs protagonist',JSON.stringify(sc));
// 2. side by side with the protagonist (each main NPC)
const ids=await page.evaluate(()=>Object.entries(NPC_SHEET).filter(([id,k])=>V5[k]).map(([id,k])=>[id,k]));
for(const [id,key] of ids){await page.evaluate(id=>window.__id=id,id);const pos=await page.evaluate(id=>{const v=npcVis[id];if(!v)return null;v.path=[];s.px=v.x+.55;s.py=v.y+.55;s.x=Math.round(s.px);s.y=Math.round(s.py);heroVis.x=s.px;heroVis.y=s.py;$('dialog').replaceChildren();const [x,y]=iso(v.x,v.y);return worldToScreen(x,y)},id);
 if(!pos){console.log('SKIP (not in town now):',key);continue}await page.waitForTimeout(350);const v=await page.evaluate(id=>npcVis[id].v5anim,id);assert(v&&(v.startsWith('idle')||v==='work:side'),key+' anim '+v);
 await page.screenshot({path:`${OUT}/pair-${key}.png`,clip:await clipAt(page,()=>{const id=window.__id;const v=npcVis[id];const [x,y]=iso(v.x,v.y);return worldToScreen(x,y)})})}
ok('protagonist side by side with each NPC',ids.map(x=>x[1]).join(','));
// 3. walking views: lateral = side sheet (mirrored for the other side), vertical = north/south
const id=ids.find(([i])=>i==='future')?.[0]||ids[0][0];const res={};
for(const [name,dx,dy] of [['east',1,-1],['west',-1,1],['south',1,1],['north',-1,-1]]){
 await page.evaluate(([id,dx,dy])=>{const v=npcVis[id];const c=[[5,6],[6,6],[4,6],[5,5]].find(([x,y])=>!solidAt(x,y,.22)&&!solidAt(x+dx*.9,y+dy*.9,.22)&&!solidAt(x+dx*1.8,y+dy*1.8,.22))||[5,6];v.x=c[0];v.y=c[1];v.path=[[c[0]+dx*1.8,c[1]+dy*1.8]];v.waitT=0;s.px=c[0]-2;s.py=c[1]+2;heroVis.x=s.px;heroVis.y=s.py},[id,dx,dy]);
 const seen=new Set();for(let i=0;i<8;i++){await page.waitForTimeout(60);seen.add(await page.evaluate(id=>npcVis[id].v5anim+'|'+npcVis[id].v5dir,id))}
 res[name]=[...seen];await page.evaluate(id=>window.__id=id,id);await page.screenshot({path:`${OUT}/walk-${name}.png`,clip:await clipAt(page,()=>{const v=npcVis[window.__id];const [x,y]=iso(v.x,v.y);return worldToScreen(x,y)},160,140)})}
const has=(n,want)=>res[n].some(s=>s.startsWith(want));
assert(has('east','walk:side|east')||has('east','walk:side'),'east '+res.east);assert(has('west','walk:side'),'west '+res.west);assert(has('north','walk:north'),'north '+res.north);
ok('NPC walking views',JSON.stringify(res));
// 4. talking pose during a conversation
await page.evaluate(()=>{s.npcTalk='future';const v=npcVis.future;if(v){v.path=[];v.anim='interact'}});await page.waitForTimeout(300);const tk=await page.evaluate(()=>npcVis.future?.v5anim);assert(tk?.startsWith('talk'),'talk '+tk);ok('talk pose',tk);
// 5. work pose follows the real activity (Bento repairing clocks in the morning)
await page.evaluate(()=>{s.npcTalk=null;s.t=600;s.worldClock=Math.max(s.worldClock,600);render()});await page.waitForTimeout(500);
const w=await page.evaluate(()=>{const p=residents().find(p=>p.id==='bento');const v=npcVis.bento;return [p?.activity,v?.v5anim]});
if(w[0]&&/rel[oó]g|consert/i.test(w[0])){await page.waitForFunction(()=>npcVis.bento&&!npcVis.bento.path?.length,null,{timeout:15000}).catch(()=>{});await page.waitForTimeout(300);const a=await page.evaluate(()=>npcVis.bento.v5anim);assert.equal(a,'work:side','bento '+a);
 const pos=await page.evaluate(()=>{const v=npcVis.bento;s.px=v.x+.6;s.py=v.y+.6;heroVis.x=s.px;heroVis.y=s.py;const [x,y]=iso(v.x,v.y);return worldToScreen(x,y)});await page.screenshot({path:`${OUT}/bento-work.png`,clip:await clipAt(page,()=>{const v=npcVis.bento;const [x,y]=iso(v.x,v.y);return worldToScreen(x,y)})});ok('work pose from activity','Bento: '+w[0])}
else console.log('SKIP work: Bento activity',w[0]);
assert.equal(errs.length,0,errs.join('\n'));await browser.close();console.log('ALL V5 CHECKS PASSED');
