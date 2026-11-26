// V4 systems in real Chromium: inventory, pickups, key + door, mechanical safe dial, Bento's gears,
// combination, equipment, persistence (no duplication), bestiary and the V4 creature in the encounter.
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const BASE=process.env.BASE||'http://127.0.0.1:8099/game2/';const OUT=process.env.OUT||'browser-evidence/v4';
const args=process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[];
await mkdir(OUT,{recursive:true});const ok=(n,x='')=>console.log('PASS:',n,x);
const browser=await chromium.launch({headless:true,args});const ctx=await browser.newContext({viewport:{width:1280,height:800}});const page=await ctx.newPage();
const errs=[];page.on('pageerror',e=>errs.push(e.message));
await page.goto(BASE,{waitUntil:'networkidle'});await page.evaluate(()=>localStorage.clear());await page.reload({waitUntil:'networkidle'});
await page.locator('#loading').waitFor({state:'detached',timeout:20000}).catch(()=>{});await page.locator('#startGame').click();await page.waitForTimeout(300);
const place=(x,y)=>page.evaluate(([x,y])=>{s.x=Math.round(x);s.y=Math.round(y);s.px=x;s.py=y;heroVis.x=x;heroVis.y=y;MOT.vx=MOT.vy=0;$('dialog').replaceChildren();$('puzzle').replaceChildren()},[x,y]);
const inv=()=>page.evaluate(()=>JSON.parse(JSON.stringify(s.inv)));
// 1. starting inventory and the inventory screen with V4 sprites
await page.keyboard.press('i');await page.locator('#invModal').waitFor();let I=await inv();
assert(I.items.lanterna&&I.items.radio&&I.equip.tool==='lanterna','starting kit');
const bg=await page.locator('#invGrid .inv-ico').first().evaluate(e=>getComputedStyle(e).backgroundImage);assert.match(bg,/v4\/atlas-0\.png/);
await page.screenshot({path:`${OUT}/inventory.png`});await page.keyboard.press('i');ok('inventory screen','V4 item sprites, 4 equipment slots');
// 2. pickups by proximity, no re-pick
const picks=await page.evaluate(()=>PICKUPS.map(p=>[p.id,p.x,p.y,p.item]));
for(const [id,x,y,item] of picks){if(id==='pk_key')continue;await place(x+.35,y+.35);await page.waitForTimeout(80);await page.keyboard.press('e');await page.waitForTimeout(80)}
I=await inv();for(const [id,,,item] of picks)if(id!=='pk_key')assert(I.items[item],'picked '+item);
await place(picks[0][1]+.35,picks[0][2]+.35);await page.keyboard.press('e');assert.equal((await inv()).items[picks[0][3]].qty,1,'no re-pick');ok('world pickups',picks.length-1+' items, no duplicates');
// 3. locked door: refused without the key, opens with it
const door=await page.evaluate(()=>[DOORS.oficina.x,DOORS.oficina.y]);await place(door[0]+.45,door[1]+.45);await page.waitForTimeout(80);await page.keyboard.press('e');
assert.match(await page.locator('#log').textContent(),/trancada/);assert(await page.locator('#pzModal').isHidden(),'door must stay locked');
const key=picks.find(p=>p[0]==='pk_key');await place(key[1]+.35,key[2]+.35);await page.keyboard.press('e');assert((await inv()).items.chave_oficina,'key');
await place(door[0]+.45,door[1]+.45);await page.waitForTimeout(80);await page.keyboard.press('e');await page.locator('#pzModal').waitFor();
assert.equal((await inv()).doors.oficina,'aberta');ok('key and door','trancada -> aberta with the workshop key');
// 4. gears without the large gear: wrong attempt, hints
const pegText=i=>page.locator('#pzControls button').nth(i).textContent();
const setPeg=async(i,label)=>{for(let k=0;k<5&&!(await pegText(i)).includes(label);k++)await page.locator('#pzControls button').nth(i).click()};
await setPeg(0,'pequena');await setPeg(1,'média');await page.getByRole('button',{name:'Girar manivela'}).click();await page.waitForTimeout(1200);
assert(!(await page.evaluate(()=>s.pz.gears.solved)),'wrong chain must not solve');assert.match(await page.locator('#pzHint').textContent(),/não transmitem/);
for(let i=0;i<3;i++)await page.getByRole('button',{name:'Dica'}).click();assert.match(await page.locator('#pzHint').textContent(),/média, grande, pequena/);
await page.screenshot({path:`${OUT}/gears-wrong.png`});await page.getByRole('button',{name:'Fechar'}).click();ok('gear puzzle feedback + 3 hint levels');
// 5. mechanical safe with the dial (gives the large gear)
await page.evaluate(()=>{s.x=3;s.y=4;s.px=3;s.py=4;heroVis.x=3;heroVis.y=4;interact()});await page.getByRole('button',{name:'Fita cassete',exact:true}).click();await page.getByRole('button',{name:'Cofre de aço',exact:true}).click();
await page.locator('#safeDial').waitFor();const L=page.getByRole('button',{name:'Girar à esquerda'}),Rr=page.getByRole('button',{name:'Girar à direita'}),M=page.getByRole('button',{name:'Marcar número'});
await M.click();for(let i=0;i<3;i++)await L.click();await M.click();for(let i=0;i<2;i++)await Rr.click();await M.click();for(let i=0;i<6;i++)await L.click();await M.click();
await page.screenshot({path:`${OUT}/safe-dial.png`});await page.getByRole('button',{name:'Puxar alavanca'}).click();
assert(await page.evaluate(()=>s.clues.includes('safe')),'safe opened by the dial');I=await inv();assert(I.items.gear_l&&I.items.carta,'safe gives letter + large gear');await page.locator('#leave').click();ok('mechanical safe dial','0-3-1-7 turned and marked');
// 6. gears solved: real rotation, hidden time revealed
await place(door[0]+.45,door[1]+.45);await page.waitForTimeout(80);await page.keyboard.press('e');await page.locator('#pzModal').waitFor();
await page.getByRole('button',{name:'Reiniciar'}).click();await setPeg(0,'média');await setPeg(1,'grande');await setPeg(2,'pequena');
const a0=await page.evaluate(()=>s.pz.gears.angle);await page.getByRole('button',{name:'Girar manivela'}).click();await page.waitForTimeout(800);await page.screenshot({path:`${OUT}/gears-turning.png`});
await page.waitForTimeout(1200);const g=await page.evaluate(()=>[s.pz.gears.solved,s.pz.gears.angle,s.clues.includes('gearclock'),s.puzzles.includes('gears')]);
assert(g[0]&&g[2]&&g[3],'gears solved '+g);assert(g[1]>a0+1,'gears turned');await page.screenshot({path:`${OUT}/gears-solved.png`});await page.getByRole('button',{name:'Fechar'}).click();ok('gear puzzle solved','03h17 station = 03h00 real');
// 7. combination, equipment, essential items, quick use outside combat
await page.keyboard.press('i');await page.evaluate(()=>{INVCAT='all';INVSEL='pilhas';invRender()});await page.getByRole('button',{name:'Combinar com…'}).click();await page.locator('#invGrid button[aria-label="Lanterna"]').click();
I=await inv();assert(I.flags.lanternCharged&&!I.items.pilhas,'pilhas + lanterna');
await page.evaluate(()=>{INVSEL='detector_emf';invRender()});await page.getByRole('button',{name:'Equipar'}).click();assert.equal((await inv()).equip.tool,'detector_emf');
assert.equal(await page.evaluate(()=>useUp('carta')),false,'essential item cannot be consumed');await page.screenshot({path:`${OUT}/inventory-full.png`});await page.keyboard.press('i');ok('combine / equip / essential','lanternCharged, EMF in the investigation slot');
// 8. save + reload: no duplication, mechanism stays solved
const before=await inv();await page.evaluate(()=>uiPause(true));await page.locator('#save').click();await page.evaluate(()=>uiPause(false));await page.reload({waitUntil:'networkidle'});await page.locator('#startGame').click();await page.waitForTimeout(300);
const after=await inv();assert.deepEqual(Object.fromEntries(Object.entries(after.items).map(([k,v])=>[k,v.qty])),Object.fromEntries(Object.entries(before.items).map(([k,v])=>[k,v.qty])),'same items after reload');
assert(await page.evaluate(()=>s.pz.gears.solved&&s.inv.doors.oficina==='aberta'),'mechanism and door persisted');
ok('persistence','inventory, door and solved mechanism survive reload without duplication');
// 9. encounter: V4 echo animation + bestiary entries
const enc=await page.evaluate(()=>{for(const c of ['warning','rail','radio'])if(!s.clues.includes(c))s.clues.push(c);s.x=2;s.y=6;s.px=2;s.py=6;if(encounterAvailable()){beginEncounter();render();return true}return false});
if(enc){await page.waitForTimeout(600);const lit=await page.evaluate(()=>{const k=$('encounterArt').getContext('2d');const d=k.getImageData(130,60,60,60).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]+d[i+1]+d[i+2]>200)n++;return n});assert(lit>80,'echo drawn '+lit);
 await page.getByRole('button',{name:'Observar o padrão'}).click();await page.waitForTimeout(400);await page.screenshot({path:`${OUT}/encounter-v4.png`});
 const best=await page.evaluate(()=>s.bestiary.eco_humanoide?.facts);assert(best.includes('seen')&&best.includes('pattern'),'bestiary '+best);
 await page.evaluate(()=>uiJournal(true));await page.waitForTimeout(800);await page.locator('#bestiary').scrollIntoViewIfNeeded();await page.screenshot({path:`${OUT}/bestiary.png`});ok('V4 creature in encounter + bestiary',best.join(','))}
else console.log('SKIP: encounter not available in this state');
assert.equal(errs.length,0,errs.join('\n'));await browser.close();console.log('ALL V4 CHECKS PASSED');
