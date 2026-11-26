// Full playthrough in real Chromium against a deployed URL.
// Usage: BASE=https://wampa.com.br/game2/ node tests/playtest-full.mjs
// Plays two routes with opposite NPC decisions and checks assets, audio, dialogue,
// puzzles, save/reload, divergent consequences and the four-scene ending.
import {chromium} from 'playwright';
import {mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';

const BASE=process.env.BASE||'http://127.0.0.1:8092/game2/';
const OUT=process.env.OUT||'browser-evidence/public';
// Optional: HOST_MAP="wampa.com.br 104.21.x.x" pins DNS (e.g. to force IPv4 on flaky networks).
const launchArgs=process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[];
await mkdir(OUT,{recursive:true});
const browser=await chromium.launch({headless:true,args:['--autoplay-policy=no-user-gesture-required',...launchArgs]});
const log=(...a)=>console.log(...a);
// HUD helpers: title screen, journal drawer and pause menu (the game keeps its element ids)
async function start(page){await page.locator('#loading').waitFor({state:'detached',timeout:20000}).catch(()=>{});await page.locator('#startGame').click();await page.waitForFunction(()=>UI.started)}
const J=(page,open)=>page.evaluate(o=>uiJournal(o),open);
const pause=(page,open)=>page.evaluate(o=>uiPause(o),open);

async function open(tag){
  const ctx=await browser.newContext({viewport:{width:1366,height:900}});
  const page=await ctx.newPage();
  const problems=[],assets={};
  page.on('pageerror',e=>problems.push('pageerror: '+e.message));
  page.on('console',m=>{if(m.type()==='error')problems.push('console: '+m.text())});
  page.on('requestfailed',r=>problems.push('requestfailed: '+r.url()+' '+r.failure()?.errorText));
  page.on('response',r=>{const u=r.url();if(u.endsWith('favicon.ico'))return;if(r.status()>=400)problems.push(r.status()+' '+u);if(u.includes('/assets/')&&!assets[u.split('/').pop()])assets[u.split('/').pop()]={status:r.status(),type:r.headers()['content-type']}});
  const res=await page.goto(BASE,{waitUntil:'networkidle'});
  assert.equal(res.status(),200,'page status');
  await page.evaluate(()=>localStorage.clear());
  await page.reload({waitUntil:'networkidle'});
  await page.locator('#world').waitFor();
  await start(page);
  return {ctx,page,problems,assets,tag};
}
const st=page=>page.evaluate(()=>({x:s.x,y:s.y,t:s.t,room:s.room,clues:[...s.clues],decisions:{...s.decisions},fates:{...s.fates},solved:[...s.solved],end:s.end,events:[...s.events]}));
const blur=page=>page.evaluate(()=>document.activeElement?.blur());
const KEY={'1,0':'ArrowRight','-1,0':'ArrowLeft','0,1':'ArrowDown','0,-1':'ArrowUp'};

// BFS over the town grid with the game's own passability rule.
async function walkNextTo(page,target,maxSteps=60){
  await blur(page);
  for(let n=0;n<maxSteps;n++){
    const info=await page.evaluate(target=>{const t=typeof target==='string'?residents().find(p=>p.id===target):target;return {me:[s.x,s.y],t:t&&[t.x,t.y],blocked:(()=>{const b=[];for(let x=0;x<14;x++)for(let y=0;y<14;y++)if(!walkable(x,y))b.push(x+','+y);return b})()}},target);
    if(!info.t)throw new Error('target not found '+JSON.stringify(target));
    const [tx,ty]=info.t,[mx,my]=info.me;
    if(Math.abs(tx-mx)+Math.abs(ty-my)<=1)return true;
    const blocked=new Set(info.blocked),ok=(x,y)=>x>=0&&y>=0&&x<14&&y<14&&!(x>10&&y>8)&&!blocked.has(x+','+y);
    const prev=new Map([[mx+','+my,null]]),q=[[mx,my]];let goal=null;
    while(q.length){const [x,y]=q.shift();if(Math.abs(tx-x)+Math.abs(ty-y)<=1&&!(x===tx&&y===ty)){goal=[x,y];break}
      for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){const k=(x+dx)+','+(y+dy);if(!prev.has(k)&&ok(x+dx,y+dy)){prev.set(k,[x,y]);q.push([x+dx,y+dy])}}}
    if(!goal)throw new Error('no path to '+JSON.stringify(info.t));
    let cur=goal,first=goal;while(prev.get(cur[0]+','+cur[1])&&(prev.get(cur[0]+','+cur[1])[0]!==mx||prev.get(cur[0]+','+cur[1])[1]!==my)){cur=prev.get(cur[0]+','+cur[1])}first=cur;
    await page.keyboard.press(KEY[(first[0]-mx)+','+(first[1]-my)]);
  }
  throw new Error('walk did not arrive');
}
// Wait in 1h steps until the NPC accepts a conversation (shows its speaker banner).
async function talkTo(page,id,name,maxHours=30){
  for(let h=0;h<maxHours;h++){
    await walkNextTo(page,id);
    await page.keyboard.press('e');
    const who=await page.locator('#dialog .speaker strong').first().textContent({timeout:500}).catch(()=>null);
    if(who===name){
      const bg=await page.locator('#dialog .portrait').first().evaluate(e=>getComputedStyle(e).backgroundImage);
      assert.match(bg,/portraits\.png/,'portrait asset on '+name);
      return;
    }
    await page.locator('#wait').click();await blur(page);
  }
  throw new Error(name+' never became available');
}
const clickDialog=(page,label)=>page.locator('#dialog').getByRole('button',{name:label,exact:true}).click();

async function core(page){
  // Uncle's study: tape + safe keypad (wrong code first, then 0317).
  for(const k of ['a','a','w','e'])await page.keyboard.press(k);
  assert.equal((await st(page)).room,'radio');
  assert.match(await page.locator('#roomart').evaluate(e=>getComputedStyle(e).backgroundImage),/interiors\/study\.png/);
  await page.getByRole('button',{name:'Fita cassete',exact:true}).click();
  await page.getByRole('button',{name:'Cofre de aço',exact:true}).click();
  for(const n of ['1','2','3','4','Abrir'])await page.locator('#puzzle').getByRole('button',{name:n,exact:true}).click();
  assert(!(await st(page)).clues.includes('safe'),'wrong code must not open the safe');
  for(const n of ['0','3','1','7','Abrir'])await page.locator('#puzzle').getByRole('button',{name:n,exact:true}).click();
  assert((await st(page)).clues.includes('safe'),'safe opened');
  await page.locator('#leave').click();
  // Station: rails, clock, manifest, signal cabinet dial puzzle.
  for(const k of ['a','s','s','e'])await page.keyboard.press(k);
  assert.equal((await st(page)).room,'rail');
  assert.match(await page.locator('#roomart').evaluate(e=>getComputedStyle(e).backgroundImage),/interiors\/station\.png/);
  for(const n of ['Trilhos','Relógio parado','Manifesto rasgado'])await page.getByRole('button',{name:n,exact:true}).click();
  await page.getByRole('button',{name:'Armário de sinalização',exact:true}).click();
  const d=page.locator('.dialrow button');await d.nth(0).click();await d.nth(0).click();await d.nth(1).click();
  await page.getByRole('button',{name:'Testar mecanismo'}).click();
  assert((await st(page)).clues.includes('switchlog'),'cabinet opened');
  await page.screenshot({path:`${OUT}/station.png`});
  await page.locator('#leave').click();
  // Radio: tune and solve the prime-number prediction (wrong answer first).
  await J(page,true);
  await page.locator('#freq').evaluate(e=>{e.value='103.7';e.dispatchEvent(new Event('input',{bubbles:true}))});
  await page.locator('#tune').click();
  assert((await st(page)).clues.includes('warning'),'signal captured');
  await page.locator('#signalAnswer').fill('12');await page.locator('#signalCheck').click();
  assert(!(await st(page)).clues.includes('primepattern'));
  await page.locator('#signalAnswer').fill('13');await page.locator('#signalCheck').click();
  assert((await st(page)).clues.includes('primepattern'),'prime pattern solved');
  // Evidence table: tape + stopped clock.
  await page.locator('#compare').getByRole('button',{name:'Fita cassete',exact:true}).click();
  await page.locator('#compare').getByRole('button',{name:'Relógio parado',exact:true}).click();
  await page.locator('#combine').click();
  assert((await st(page)).clues.includes('confirmedtime'),'evidence comparison');
  const chips=await page.locator('#compare button').allTextContents();
  await J(page,false);
  assert(!chips.some(t=>/^[a-z_]+$/.test(t.trim())),'raw ids in evidence chips: '+chips.join('|'));
  await blur(page);
}

async function finale(page,tag){
  await J(page,true);await page.locator('#cases').getByRole('button',{name:'A ferrovia pode estar ativa clandestinamente.',exact:true}).click();await J(page,false);
  assert((await st(page)).solved.includes('train'));
  await walkNextTo(page,{x:1,y:6});
  await page.locator('#night').click();
  await J(page,true);await page.locator('#final').click();await J(page,false);
  await page.locator('#cinema').waitFor();
  assert.match(await page.locator('#cinema img').evaluate(i=>i.complete&&i.naturalWidth>0?i.src:''),/night-train\.svg/);
  const titles=[];
  for(let i=0;i<4;i++){titles.push(await page.locator('#cinemaTitle').textContent());if(i===3){assert.match(await page.locator('#cinemaText').textContent(),/quem antecipou a sequência/);await page.screenshot({path:`${OUT}/${tag}-finale.png`})}await page.locator('#cinemaNext').click()}
  assert.deepEqual(titles,['03h17','O passageiro','O aviso','Frequência Zero']);
  assert.match((await st(page)).end,/FIM DO CAPÍTULO I/);
}

// ---------- Route A: support Nora's broadcast + warn Raul; Lia keeps a copy ----------
{
  const {ctx,page,problems,assets}=await open('A');
  await page.screenshot({path:`${OUT}/A-town.png`});
  // Audio: real AudioContext running.
  await pause(page,true);await page.locator('#audio').click();
  await page.waitForFunction(()=>audio&&audio.state==='running',null,{timeout:5000});
  assert.equal(await page.locator('#audio').getAttribute('aria-pressed'),'true');await pause(page,false);
  log('A audio running');
  await core(page);
  log('A puzzles ok');
  await talkTo(page,'future','Nora');
  await clickDialog(page,'Apoiar a transmissão pública');
  await talkTo(page,'clinic','Lia');
  await clickDialog(page,'Mostrar a fita do tio');
  await clickDialog(page,'Proteger a fonte e guardar uma cópia');
  await talkTo(page,'guard','Raul');
  await clickDialog(page,'Perguntar sobre a ferrovia');
  await clickDialog(page,'Alertar Raul para evitar a ronda');
  let A=await st(page);
  assert.deepEqual(Object.fromEntries(Object.entries(A.decisions).map(([k,v])=>[k,v.choice])),{future:'public',clinic:'protect',guard:'warn'});
  log('A dialogue + decisions ok at t='+A.t);
  // Save, reload, keep going from the restored state.
  await pause(page,true);await page.locator('#save').click();await pause(page,false);
  await page.reload({waitUntil:'networkidle'});await start(page);
  const R=await st(page);
  assert.deepEqual(R.clues.sort(),A.clues.sort(),'clues persisted');
  assert.equal(R.t,A.t,'time persisted');
  assert.equal(R.decisions.guard.choice,'warn','decision persisted');
  log('A save/reload ok');
  while((await st(page)).t<2600){await page.locator('#wait').click()}
  A=await st(page);
  assert.equal(A.fates.exchange,'relocated');assert.equal(A.fates.lia,'protected');
  const evA=await page.locator('#events').textContent();
  await J(page,true);await page.locator('#clues').scrollIntoViewIfNeeded();
  await page.screenshot({path:`${OUT}/A-consequences.png`});
  await J(page,false);
  await finale(page,'A');
  for(const f of ['ground.webp','atlas-0.png','ch-hero.png','ch-lia.png','ch-raul.png','ch-nora.png','portraits.png','icons.png','logo.png','study.png','station.png','night-train.svg']){assert.equal(assets[f]?.status,200,f);assert.match(assets[f].type,/^image\//,f)}
  assert.equal(problems.length,0,problems.join('\n'));
  log('A PASS fates',JSON.stringify(A.fates),'| events:',evA.slice(0,160));
  await ctx.close();
}

// ---------- Route B: keep the recording private, observe, Lia reports ----------
{
  const {ctx,page,problems}=await open('B');
  await core(page);
  await talkTo(page,'future','Nora');
  await clickDialog(page,'Preservar a gravação em sigilo');
  await talkTo(page,'clinic','Lia');
  await clickDialog(page,'Incentivar Lia a protocolar a denúncia');
  await talkTo(page,'guard','Raul');
  await clickDialog(page,'Pedir que mantenha a ronda e observe');
  while((await st(page)).t<2600){await page.locator('#wait').click()}
  const B=await st(page);
  assert.equal(B.fates.exchange,'delivered');assert.equal(B.fates.lia,'reviewed');
  assert(B.events.some(e=>e.includes('O relatório chegou à rádio sem interferência.')));
  assert(B.events.some(e=>e.includes('Lia apresentou os prontuários à direção')));
  await finale(page,'B');
  assert.equal(problems.length,0,problems.join('\n'));
  log('B PASS fates',JSON.stringify(B.fates));
  await ctx.close();
}

// ---------- Mobile/touch layout on the same URL ----------
{
  const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  const page=await ctx.newPage();await page.goto(BASE,{waitUntil:'networkidle'});await start(page);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'no horizontal page scroll');
  await page.locator('#controls button[data-m="-1,0"]').tap();
  await page.screenshot({path:`${OUT}/mobile.png`,fullPage:false});
  log('mobile PASS');await ctx.close();
}
await browser.close();
console.log('PASS: full playtest at '+BASE);
