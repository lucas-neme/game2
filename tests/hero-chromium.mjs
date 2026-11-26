// Protagonist views (walk V2) and physical seat interaction in real Chromium.
// Usage: BASE=http://127.0.0.1:8099/game2/ node tests/hero-chromium.mjs
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const BASE=process.env.BASE||'http://127.0.0.1:8099/game2/';const OUT=process.env.OUT||'browser-evidence/hero';
const args=process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[];
await mkdir(OUT,{recursive:true});
const browser=await chromium.launch({headless:true,args});const ok=(n,x='')=>console.log('PASS:',n,x);
const ctx=await browser.newContext({viewport:{width:1280,height:760}});const page=await ctx.newPage();const errs=[];page.on('pageerror',e=>errs.push(e.message));
await page.goto(BASE,{waitUntil:'networkidle'});await page.evaluate(()=>localStorage.clear());await page.reload({waitUntil:'networkidle'});
await page.locator('#loading').waitFor({state:'detached',timeout:20000}).catch(()=>{});await page.locator('#startGame').click();await page.waitForTimeout(400);
await page.evaluate(()=>{window.__place=(x,y)=>{s.x=Math.round(x);s.y=Math.round(y);s.px=x;s.py=y;heroVis.x=x;heroVis.y=y;MOT.vx=MOT.vy=0;INPUT.keys.clear();$('dialog').replaceChildren();$('puzzle').replaceChildren()};
 window.__heroShot=()=>{const [x,y]=iso(heroVis.x,heroVis.y);const [sx,sy]=worldToScreen(x,y-24);return [sx,sy]}});
const spot=await page.evaluate(()=>{for(let x=0;x<14;x++)for(let y=0;y<14;y++){let ok=true;for(let a=0;a<12&&ok;a++)if(solidAt(x+Math.cos(a/12*6.283)*.7,y+Math.sin(a/12*6.283)*.7,.22))ok=false;if(ok)return [x,y]}return [5,5]});
// 1. the view follows the on-screen direction; lateral movement uses the side views
const cases=[[['d'],'east'],[['a'],'west'],[['w'],'north'],[['s'],'south'],[['w','d'],'east'],[['w','a'],'west'],[['s','d'],'east'],[['s','a'],'west']];
for(const [keys,want] of cases){await page.evaluate(([x,y])=>__place(x,y),spot);for(const k of keys)await page.keyboard.down(k);await page.waitForTimeout(260);
 const r=await page.evaluate(()=>({dir4:heroVis.dir4,anim:heroVis.anim,ph:heroVis.ph,pos:__heroShot()}));
 await page.screenshot({path:`${OUT}/walk-${keys.join('')}.png`,clip:{x:Math.max(0,r.pos[0]-70),y:Math.max(0,r.pos[1]-90),width:140,height:150}});
 for(const k of keys)await page.keyboard.up(k);await page.waitForTimeout(150);assert.equal(r.dir4,want,keys.join('+')+' view');assert.equal(r.anim,'walk')}
ok('4 drawn views selected by screen direction','8 key directions -> east/west/north/south, never front/back for lateral moves');
// 2. frames advance with distance: 8 distinct frames over a walk cycle, idle uses the neutral frame
await page.evaluate(([x,y])=>{__place(x,y);heroVis.ph=0},spot);await page.keyboard.down('d');const cols=new Set();for(let i=0;i<14;i++){await page.waitForTimeout(45);cols.add(await page.evaluate(()=>Math.floor(heroVis.ph*H4.frames)%H4.frames))}await page.keyboard.up('d');
assert(cols.size>=6,'walk frames seen '+[...cols]);ok('walk cycle frames',`${cols.size} of 8 frames in 0.6 s`);
// 3. sit on a free bench, stay seated (movement blocked), stand up, seat released
const seat=await page.evaluate(()=>{const st=SEATS.find(q=>!q.occ);__place(st.x+.45,st.y+.45);resolve(HERO,PHYS.heroR,null);return [st.gx,st.gy]});
await page.waitForTimeout(200);const prompt=await page.evaluate(()=>seatPromptTarget()?.label);assert.equal(prompt,'Sentar','context action');
await page.keyboard.press('e');await page.waitForTimeout(600);let st=await page.evaluate(()=>({p:SEAT.hero?.phase,occ:!!SEAT.hero?.seat.occ,px:s.px,py:s.py}));
assert.equal(st.p,'seated');assert(st.occ,'seat occupied');const [hx,hy]=await page.evaluate(()=>__heroShot());
await page.screenshot({path:`${OUT}/seated.png`,clip:{x:hx-110,y:hy-110,width:220,height:200}});
await page.keyboard.down('Control');await page.keyboard.up('Control');await page.waitForTimeout(300);
const still=await page.evaluate(()=>[s.px,s.py,SEAT.hero?.phase]);assert(Math.abs(still[0]-st.px)<1e-6&&still[2]==='seated','stays seated');
await page.keyboard.press('e');await page.waitForTimeout(500);st=await page.evaluate(()=>({p:SEAT.hero,free:SEATS.every(q=>q.occ!=='hero'),pen:(()=>{let m=0;for(const c of nearStatic(s.px,s.py,.22)){const p=penetration(s.px,s.py,.22,c);if(p)m=Math.max(m,Math.hypot(...p))}return m})()}));
assert.equal(st.p,null,'stood up');assert(st.free,'seat released');assert(st.pen<.01,'not stuck in the bench');ok('sit / seated / stand up','seat claimed and released');
// 4. movement key also stands up; talk while seated
await page.evaluate(()=>{const st=SEATS.find(q=>!q.occ);heroSit(st)});await page.waitForTimeout(500);await page.keyboard.down('s');await page.waitForTimeout(450);await page.keyboard.up('s');
assert.equal(await page.evaluate(()=>SEAT.hero),null,'movement stands up');
const talk=await page.evaluate(()=>{const st=SEATS.find(q=>!q.occ);heroSit(st);const a=AMB.list[0];a.x=st.x+.6;a.y=st.y+.3;a.path=[];a.wait=99;return a.name});
await page.waitForTimeout(500);await page.keyboard.press('e');await page.waitForTimeout(300);const log=await page.evaluate(()=>[$('log').textContent,SEAT.hero?.phase]);
assert(log[0].startsWith(talk),'talked while seated: '+log[0]);assert.equal(log[1],'seated');await page.screenshot({path:`${OUT}/talk-seated.png`});ok('talk while seated',talk);
await page.evaluate(()=>{heroStand()});await page.waitForTimeout(500);
// 5. residents sit on benches near their stops
await page.evaluate(()=>{for(const a of AMB.list){a.seatTried=false}});let sat=null;for(let i=0;i<40&&!sat;i++){await page.waitForTimeout(500);sat=await page.evaluate(()=>{const a=AMB.list.find(a=>a.seat&&a.sitF>=1.9);return a&&a.name})}
assert(sat,'no resident sat');await page.evaluate(()=>{const a=AMB.list.find(a=>a.seat);__place(a.seat.x+1.2,a.seat.y+1.2)});await page.waitForTimeout(400);await page.screenshot({path:`${OUT}/npc-seated.png`});ok('resident sits on a bench',sat);
assert.equal(errs.length,0,errs.join('\n'));await browser.close();console.log('ALL HERO CHECKS PASSED');
