// Continuous movement and collision in real Chromium (keyboard, analog, d-pad).
// Usage: BASE=http://127.0.0.1:8099/game2/ node tests/motion-chromium.mjs
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const BASE=process.env.BASE||'http://127.0.0.1:8099/game2/';const OUT=process.env.OUT||'browser-evidence/motion';
const args=process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[];
await mkdir(OUT,{recursive:true});
const browser=await chromium.launch({headless:true,args});const results=[];
const ok=(name,extra='')=>{results.push(name);console.log('PASS:',name,extra)};
const HELPERS=()=>{window.__place=(x,y)=>{s.x=Math.round(x);s.y=Math.round(y);s.px=x;s.py=y;heroVis.x=x;heroVis.y=y;MOT.vx=MOT.vy=0;INPUT.keys.clear();INPUT.touch=null;INPUT.sneakToggle=false;$('dialog').replaceChildren();$('puzzle').replaceChildren()};
  window.__pen=()=>{let m=0;for(const c of nearStatic(s.px,s.py,PHYS.heroR)){const p=penetration(s.px,s.py,PHYS.heroR,c);if(p)m=Math.max(m,Math.hypot(p[0],p[1]))}return m};
  window.__free=(rad0)=>{for(const rad of [rad0,1.1,.95,.8,.6]){const out=[];for(let x=0;x<14;x++)for(let y=0;y<14;y++){let ok=true;for(let a=0;a<16&&ok;a++){for(const d of [.4,.8,rad]){if(solidAt(x+Math.cos(a/16*6.283)*d,y+Math.sin(a/16*6.283)*d,PHYS.heroR)){ok=false;break}}}if(ok)out.push([x,y])}if(out.length>=1)return out}return []}};
async function open(vp={width:1280,height:760}){const ctx=await browser.newContext({viewport:vp,...(vp.width<500?{isMobile:true,hasTouch:true}:{})});const page=await ctx.newPage();const errs=[];page.on('pageerror',e=>errs.push(e.message));
 await page.goto(BASE,{waitUntil:'networkidle'});await page.evaluate(()=>localStorage.clear());await page.reload({waitUntil:'networkidle'});await page.locator('#loading').waitFor({state:'detached',timeout:20000}).catch(()=>{});
 await page.evaluate(HELPERS);
 if(vp.width<500)await page.locator('#startGame').tap();else await page.locator('#startGame').click();await page.waitForFunction(()=>UI.started);await page.waitForTimeout(300);return {ctx,page,errs}}
async function hold(page,keys,ms,sample){for(const k of keys)await page.keyboard.down(k);const samples=[];const t0=Date.now();while(Date.now()-t0<ms){await page.waitForTimeout(40);if(sample)samples.push(await page.evaluate(sample))}for(const k of keys)await page.keyboard.up(k);await page.waitForTimeout(120);return samples}
const pos=()=>({x:s.px,y:s.py,cx:s.x,cy:s.y,pen:__pen(),vx:MOT.vx,vy:MOT.vy,anim:heroVis.anim,t:s.t});

const {ctx,page,errs}=await open();
const free=await page.evaluate(()=>__free(1.3));assert(free.length>=1,'need open ground for the tests: '+free.length);const F=free[Math.floor(free.length/2)];
// 1. continuous walking, not cell steps
await page.evaluate(([x,y])=>__place(x,y),F);let sm=await hold(page,['d'],700,pos);
const fr=sm.filter(p=>Math.abs(p.x-Math.round(p.x))>.05&&Math.abs(p.y-Math.round(p.y))>.05).length;
const dist=Math.hypot(sm.at(-1).x-F[0],sm.at(-1).y-F[1]);
assert(fr>=5,'positions between cells: '+fr);assert(dist>.6&&dist<2.2,'walked distance '+dist);assert(Math.max(...sm.map(p=>p.pen))<.02,'penetration');assert(sm.some(p=>p.anim==='walk'),'walk animation while moving');
await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>heroVis.anim),'idle','stops naturally');ok('continuous walking',`${dist.toFixed(2)} cells in 0.7 s, ${fr} off-grid samples`);
// 2. eight directions, normalized diagonal, screen heading matches input
const dirs=[[['d'],[1,0]],[['a'],[-1,0]],[['w'],[0,-1]],[['s'],[0,1]],[['w','d'],[1,-1]],[['w','a'],[-1,-1]],[['s','d'],[1,1]],[['s','a'],[-1,1]]];
for(const [keys,[sx,sy]] of dirs){await page.evaluate(([x,y])=>__place(x,y),F);await page.waitForTimeout(60);for(const k of keys)await page.keyboard.down(k);await page.waitForTimeout(420);
 const v=await page.evaluate(()=>[MOT.vx,MOT.vy]);for(const k of keys)await page.keyboard.up(k);await page.waitForTimeout(150);
 const sp=Math.hypot(v[0],v[1]);assert(Math.abs(sp-2.4)<.2,keys+' speed '+sp);
 const scr=[v[0]-v[1],(v[0]+v[1])/2],ang=Math.atan2(scr[1],scr[0]),want=Math.atan2(sy,sx);let da=Math.abs(ang-want);if(da>Math.PI)da=2*Math.PI-da;assert(da<.12,keys+' heading off by '+da)}
ok('eight directions','speed 2.4 cells/s on all 8, diagonal normalized, screen heading = input');
// 3. run and sneak
await page.evaluate(([x,y])=>__place(x,y),F);await page.keyboard.down('Shift');await page.keyboard.down('a');let vr=[0,'idle'];for(let i=0;i<9;i++){await page.waitForTimeout(42);const r=await page.evaluate(()=>[Math.hypot(MOT.vx,MOT.vy),heroVis.anim]);vr=[Math.max(vr[0],r[0]),vr[1]==='run'?'run':r[1]]}await page.keyboard.up('a');await page.keyboard.up('Shift');await page.waitForTimeout(200);
await page.evaluate(([x,y])=>__place(x,y),F);await page.keyboard.press('c');await page.keyboard.down('d');let vs=[0,'idle'];for(let i=0;i<10;i++){await page.waitForTimeout(45);const r=await page.evaluate(()=>[Math.hypot(MOT.vx,MOT.vy),heroVis.anim]);vs=[Math.max(vs[0],r[0]),vs[1]==='sneak'?'sneak':r[1]]}await page.keyboard.up('d');await page.keyboard.press('c');
assert(Math.abs(vr[0]-4.3)<.3&&vr[1]==='run','run '+vr);assert(Math.abs(vs[0]-1.15)<.15&&vs[1]==='sneak','sneak '+vs);ok('run and sneak',`run ${vr[0].toFixed(2)}, sneak ${vs[0].toFixed(2)} cells/s`);
// 4. building wall: no penetration, slides along the face and goes around the corner
await page.evaluate(()=>{s.t=1200;s.worldClock=Math.max(s.worldClock,1200);render()});await page.waitForTimeout(400);await page.evaluate(()=>__place(8.8,4.3));sm=await hold(page,['w'],1600,pos);
const maxPen=Math.max(...sm.map(p=>p.pen));const onFace=sm.filter(p=>Math.abs(p.y-3.72)<.04);
assert(maxPen<.02,'penetration '+maxPen);assert(onFace.length>=3,'slides on the clinic face');assert(onFace.at(-1).x<onFace[0].x-.2,'slid along x');assert(sm.at(-1).y<3.5,'went around the corner: y='+sm.at(-1).y);
await page.screenshot({path:`${OUT}/wall-slide.png`});ok('building collision + sliding + contour',`max penetration ${maxPen.toFixed(3)}`);
// 5. tree trunk and prop bases
const tree=await page.evaluate(()=>{const c=STATIC.find(c=>c.t===1&&c.r===.2&&c.x>1&&c.y>1&&!solidAt(c.x+.9,c.y+.9,.22)&&!solidAt(c.x+.45,c.y+.45,.22));return c&&[c.x,c.y]});
assert(tree,'tree for test');await page.evaluate(([x,y])=>__place(x+.9,y+.82),tree);sm=await hold(page,['w'],1300,pos);
assert(Math.max(...sm.map(p=>p.pen))<.01,'tree penetration');assert(sm.every(p=>Math.hypot(p.x-tree[0],p.y-tree[1])>=.42-.01),'kept out of the trunk');
ok('tree trunk collision','canopy does not collide, trunk r=0.20');
const prop=await page.evaluate(()=>{const c=STATIC.find(c=>c.t===1&&c.r===.26&&!solidAt(c.x+.8,c.y+.8,.22));return c&&[c.x,c.y,c.r]});
if(prop){await page.evaluate(([x,y])=>__place(x+.8,y+.8),prop);sm=await hold(page,['w'],800,pos);assert(sm.every(p=>Math.hypot(p.x-prop[0],p.y-prop[1])>=prop[2]+.22-.01),'bench penetration');ok('furniture collision','bench base r=0.26')}
// 6. tunnelling: run head-on into a lamp post (r=0.09)
const lamp=await page.evaluate(()=>{const c=STATIC.find(c=>c.t===1&&c.r===.09&&!solidAt(c.x+1.2,c.y+1.2,.22)&&!solidAt(c.x+.6,c.y+.6,.22));return c&&[c.x,c.y]});
if(lamp){await page.evaluate(([x,y])=>__place(x+1.2,y+1.2),lamp);await page.keyboard.down('Shift');sm=await hold(page,['w'],700,pos);await page.keyboard.up('Shift');
 assert(sm.every(p=>Math.hypot(p.x-lamp[0],p.y-lamp[1])>=.31-.01),'ran through the lamp');ok('no tunnelling at run speed','sub-steps of 0.07 cells')}
// 7. NPC collision (analog input aimed at a resident)
const npc=await page.evaluate(()=>{const v=Object.entries(npcVis).find(([id,v])=>!v.path?.length&&!solidAt(v.x+1.1,v.y+.2,.22));return v&&[v[0],v[1].x,v[1].y]});
if(npc){await page.evaluate(([id,x,y])=>{__place(x+1.1,y+.2);const v=npcVis[id];window.__npc=id;const dx=v.x-s.px,dy=v.y-s.py;INPUT.touch=[(dx-dy),(dx+dy)/2].map((c,i,a)=>c/Math.hypot(a[0],a[1]))},npc);
 const ds=[];for(let i=0;i<20;i++){await page.waitForTimeout(50);ds.push(await page.evaluate(()=>{const v=npcVis[__npc];return Math.hypot(v.x-s.px,v.y-s.py)}))}await page.evaluate(()=>INPUT.touch=null);
 assert(Math.min(...ds)>=.44-.02,'overlapped NPC: '+Math.min(...ds));ok('hero vs NPC collision',`min distance ${Math.min(...ds).toFixed(2)} (radii sum 0.44)`)}
// 8. NPCs crossing: no overlap over time, and they actually walk
let minPair=9,walked=0;await page.evaluate(()=>{const ids=Object.keys(npcVis).slice(0,2);const A=npcVis[ids[0]],B=npcVis[ids[1]];for(const v of [A,B]){if(v.seat){v.seat.occ=null;v.seat=null}}A.x=4;A.y=6;B.x=7;B.y=6;A.path=[[7,6]];B.path=[[4,6]];A.goal=[7,6];B.goal=[4,6]});const p0=await page.evaluate(()=>dynamicBodies().map(b=>[b.x,b.y]));
for(let i=0;i<60;i++){await page.waitForTimeout(100);const r=await page.evaluate(()=>{const b=dynamicBodies();let m=9;for(let i=0;i<b.length;i++)for(let j=i+1;j<b.length;j++)m=Math.min(m,Math.hypot(b[i].x-b[j].x,b[i].y-b[j].y));return [m,b.map(q=>[q.x,q.y])]});minPair=Math.min(minPair,r[0]);if(i===59)walked=r[1].filter((q,k)=>p0[k]&&Math.hypot(q[0]-p0[k][0],q[1]-p0[k][1])>.5).length}
assert(minPair>=.40,'NPC overlap '+minPair);assert(walked>=1,'nobody walked');ok('NPC vs NPC separation',`min pair distance ${minPair.toFixed(2)} over 6 s, ${walked} residents walked`);
// 9. time follows distance walked (8 min per cell), not key repeats or frames
await page.evaluate(([x,y])=>__place(x,y),F);const t0=await page.evaluate(()=>[s.t,s.distAcc||0,MOT.total||0]);await hold(page,['s'],900);await hold(page,['w'],900);
const t1=await page.evaluate(()=>[s.t,s.distAcc||0,MOT.total||0]);const walkedD=t1[2]-t0[2];assert.equal(t1[0]-t0[0],8*Math.floor(t0[1]+walkedD+1e-9),'time vs distance');
ok('time equivalence',`${walkedD.toFixed(2)} cells walked = ${t1[0]-t0[0]} min (old engine: ~${Math.round(1.8*30)*8} min for the same key hold)`);
// 10. interaction blocked by a wall
const blocked=await page.evaluate(()=>{__place(8,4.25);const box={t:0,x:8,y:3.62,hx:.4,hy:.03};STATIC.push(box);const k=(8+64)*256+(3+64);SHASH.get(k)?.push(box)||SHASH.set(k,[box]);const r=losBlocked();interact();const res=[r,!s.room,$('log').textContent];STATIC.pop();SHASH.get(k).pop();return res});
assert(blocked[0]&&blocked[1]&&/bloqueando/.test(blocked[2]),'interaction through a wall: '+blocked);const free2=await page.evaluate(()=>{__place(8,4.25);return losBlocked()});assert(!free2,'clear line must allow');ok('interaction needs line of sight');
// 11. interior: walk inside the station and investigate by proximity
await page.evaluate(()=>{__place(2,6);interact()});await page.locator('#interior').waitFor();await page.waitForTimeout(300);
const r0=await page.evaluate(()=>[RH.x,RH.y]);await hold(page,['d'],2300);const r1=await page.evaluate(()=>[RH.x,RH.y,RH.near?.textContent]);
assert(r1[0]>r0[0]+20,'walked in the room '+r1);await page.screenshot({path:`${OUT}/interior-walk.png`});
await hold(page,['d'],1500);const near=await page.evaluate(()=>RH.near?.textContent);await page.keyboard.press('e');await page.waitForTimeout(200);
const got=await page.evaluate(()=>s.clues.slice());assert(near,'a hotspot is highlighted near the hero');assert(got.length>0,'E investigated '+near);
const inside=await page.evaluate(()=>{const R=ROOMS.station;return R.cols.every(c=>!(RH.x>c[0]-2&&RH.x<c[2]+2&&RH.y>c[1]&&RH.y<c[3]+.8))});assert(inside,'hero inside furniture');
await page.locator('#leave').click();ok('walkable interior',`hotspot "${near}" by proximity, clues ${got.join(',')}`);
// 12. debug hitboxes + camera follow
await page.keyboard.press('F3');await page.evaluate(([x,y])=>__place(x,y),F);await hold(page,['d'],500);await page.waitForTimeout(900);
const cam=await page.evaluate(()=>{const [x,y]=iso(s.px,s.py);return [Math.abs(cam.x-x),Math.abs(cam.y-(y-40)),MOT.debug]});assert(cam[2],'debug on');assert(cam[0]<6&&cam[1]<6,'camera follows '+cam);
await page.screenshot({path:`${OUT}/hitboxes.png`});await page.keyboard.press('F3');ok('camera follow + hitbox debug view');
// 13. save migration from grid saves (no px/py)
await page.evaluate(()=>{const o=JSON.parse(JSON.stringify(s));delete o.px;delete o.py;delete o.distAcc;o.x=3;o.y=4;localStorage.setItem('fz-demo-v2',JSON.stringify(o))});
await page.reload({waitUntil:'networkidle'});await page.locator('#startGame').click();await page.waitForTimeout(400);const mig=await page.evaluate(()=>[s.x,s.y,s.px,s.py]);await page.evaluate(HELPERS);
assert.deepEqual(mig,[3,4,3,4],'migration '+mig);ok('save migration','grid save loads at its cell centre');
// 14. performance while walking
await page.evaluate(([x,y])=>{__place(x,y);MOT.perf.length=0},F);await hold(page,['d'],1800);await hold(page,['a'],1800);
const perf=await page.evaluate(()=>{const a=MOT.perf.filter(x=>x>0).slice().sort((p,q)=>p-q);const avg=a.reduce((p,q)=>p+q,0)/a.length;return {n:a.length,fps:1/avg,p95:a[Math.floor(a.length*.95)]*1000,worst:a.at(-1)*1000}});
assert(perf.fps>45,'fps '+perf.fps);ok('performance',`${perf.fps.toFixed(1)} fps avg, p95 frame ${perf.p95.toFixed(1)} ms, worst ${perf.worst.toFixed(1)} ms (${perf.n} frames)`);
assert.equal(errs.length,0,errs.join('\n'));await ctx.close();
// 15. mobile d-pad (hold)
{const {ctx,page}=await open({width:390,height:844});const free=await page.evaluate(()=>__free(1.3));const F=free[0];await page.evaluate(([x,y])=>__place(x,y),F);
 const b=page.locator('#controls button[data-m="1,0"]');const box=await b.boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();await page.waitForTimeout(600);await page.mouse.up();await page.waitForTimeout(150);
 const d=await page.evaluate(([x,y])=>Math.hypot(s.px-x,s.py-y),F);assert(d>.4,'mobile d-pad hold moved '+d);await page.screenshot({path:`${OUT}/mobile.png`});ok('mobile d-pad hold',`${d.toFixed(2)} cells`);await ctx.close()}
await browser.close();console.log(`ALL ${results.length} MOTION CHECKS PASSED`);
