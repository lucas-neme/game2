import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const code=readFileSync(new URL('../index.html',import.meta.url),'utf8').split('<script>')[1].split('</script>')[0];
const es=new Map();function node(){return{textContent:'',value:'',style:{},dataset:{},children:[],append(...x){this.children.push(...x)},replaceChildren(){this.children=[]},setAttribute(){},getContext(){return new Proxy({createRadialGradient(){return{addColorStop(){}}}},{get:(t,k)=>t[k]||(()=>{})})}}}
const doc={getElementById(id){if(!es.has(id))es.set(id,node());return es.get(id)},createElement:node,querySelectorAll(){return []}};
const mem={};const storage={getItem:k=>mem[k]||null,setItem:(k,v)=>mem[k]=v,removeItem:k=>delete mem[k]};
const run=new Function('document','localStorage','addEventListener','confirm','setTimeout','clearTimeout',code+';return {get s(){return s},move,interact,leaveRoom,finish,advance,render,residents,record,planRoute,walkable,clueCategory,beginEncounter,encounterAction,beginStealth,stealthAction,patrolState,sightCells,beginArena,arenaAction,arenaThreat,talkToResident,npcReachable};');
const a=run(doc,storage,()=>{},()=>true),get=id=>es.get(id),click=(id,label)=>get(id).children.find(b=>b.textContent===label).onclick();
a.move(-1,0);a.move(-1,0);a.move(0,-1);a.interact();assert.equal(a.s.room,'radio');click('roomart','Fita cassete');assert(a.s.clues.includes('radio'));click('roomart','Cofre de aço');let pad=get('puzzle').children.find(x=>x.className==='keypad');for(const key of ['0','0','0','0','Abrir'])pad.children.find(x=>x.textContent===key).onclick();assert(!a.s.clues.includes('safe'));for(const key of ['0','3','1','7','Abrir'])pad.children.find(x=>x.textContent===key).onclick();assert(a.s.clues.includes('safe'));a.leaveRoom();a.move(-1,0);a.move(0,1);a.move(0,1);a.interact();assert.equal(a.s.room,'rail');click('roomart','Trilhos');assert(a.s.clues.includes('rail'));a.leaveRoom();get('night').onclick();a.interact();click('dialog','Perguntar sobre a ferrovia');assert(a.s.clues.includes('witness'));get('freq').value='103.7';get('tune').onclick();assert(a.s.clues.includes('warning'));get('cases').children[0].children.find(b=>b.textContent==='A ferrovia pode estar ativa clandestinamente.').onclick();assert(a.s.solved.includes('train'));get('save').onclick();const b=run(doc,storage,()=>{},()=>true);assert(b.s.solved.includes('train'));b.finish();assert(!b.s.end);get('night').onclick();b.finish();assert(b.s.end?.includes('FIM DO CAPÍTULO I'));console.log('PASS: demo progression, 12 assertions');
get('reset').onclick();
const c=run(doc,storage,()=>{},()=>true);
c.move(-1,0);c.move(-1,0);c.move(0,-1);c.interact();click('roomart','Fita cassete');click('roomart','Cofre de aço');
let pad2=get('puzzle').children.find(x=>x.className==='keypad');for(const key of ['0','3','1','7','Abrir'])pad2.children.find(x=>x.textContent===key).onclick();
c.leaveRoom();c.move(-1,0);c.move(0,1);c.move(0,1);c.interact();click('roomart','Trilhos');click('roomart','Relógio parado');click('roomart','Manifesto rasgado');c.leaveRoom();
click('compare','Fita cassete');click('compare','Relógio parado');get('combine').onclick();assert(c.s.clues.includes('confirmedtime'));assert(c.s.connections.includes('confirmedtime'));
click('compare','Carta do cofre');click('compare','Manifesto H-17');get('combine').onclick();assert(c.s.clues.includes('shipment'));
for(let i=0;i<5;i++)c.move(1,0);for(let i=0;i<4;i++)c.move(0,1);c.interact();click('dialog','Comparar o registro de som com a fita');assert(c.s.clues.includes('altwitness'));assert(!c.s.clues.includes('witness'));
get('cases').children[0].children.find(b=>b.textContent==='A ferrovia pode estar ativa clandestinamente.').onclick();assert(c.s.solved.includes('train'));console.log('PASS: alternate route and evidence comparison, 6 additional assertions');

get('reset').onclick();
const d=run(doc,storage,()=>{},()=>true);
d.move(-1,0);d.move(-1,0);d.move(0,-1);d.interact();click('roomart','Fita cassete');assert(d.s.inspected.includes('radio:Fita cassete'));click('roomart','Cofre de aço');
let pad3=get('puzzle').children.find(x=>x.className==='keypad');for(const key of ['0','3','1','7','Abrir'])pad3.children.find(x=>x.textContent===key).onclick();
d.leaveRoom();d.move(-1,0);d.move(0,1);d.move(0,1);d.interact();click('roomart','Trilhos');click('roomart','Armário de sinalização');click('puzzle','Testar mecanismo');assert(!d.s.clues.includes('switchlog'));
let dial=get('puzzle').children.find(x=>x.className==='dialrow');dial.children[0].onclick();dial.children[0].onclick();dial.children[1].onclick();click('puzzle','Testar mecanismo');assert(d.s.clues.includes('switchlog'));assert(d.s.puzzles.includes('cabinet'));
d.leaveRoom();get('freq').value='103.7';get('tune').onclick();get('cases').children[0].children.find(b=>b.textContent==='A ferrovia pode estar ativa clandestinamente.').onclick();assert(d.s.solved.includes('train'));assert(!d.s.clues.includes('witness')&&!d.s.clues.includes('altwitness'));
d.advance(1020-d.s.t);d.render();assert(get('weather').textContent.includes('Chuva'));assert(d.s.phenomena.includes('lights'));d.advance(240);assert(d.s.phenomena.includes('static'));get('night').onclick();assert(get('weather').textContent.includes('Neblina'));assert(d.s.phenomena.includes('whistle'));d.finish();assert(d.s.end?.includes('FIM DO CAPÍTULO I'));assert.equal(get('cinema').hidden,false);
get('cinemaNext').onclick();assert.equal(d.s.endingScene,1);
const e=run(doc,storage,()=>{},()=>true);assert.equal(e.s.endingScene,1);get('cinemaNext').onclick();get('cinemaNext').onclick();get('cinemaNext').onclick();assert(e.s.cinemaDismissed);assert.equal(get('cinema').hidden,true);
console.log('PASS: mechanical route, weather, anomalies and finale, 17 additional assertions');

get('reset').onclick();
const q=run(doc,storage,()=>{},()=>true);
assert.equal(get('signalLab').hidden,true);
q.move(-1,0);q.move(-1,0);q.move(0,-1);q.interact();click('roomart','Fita cassete');q.leaveRoom();
get('freq').value='103.7';get('tune').onclick();assert.equal(get('signalLab').hidden,false);
get('signalAnswer').value='12';get('signalCheck').onclick();assert(!q.s.clues.includes('primepattern'));
get('signalHint').onclick();assert.equal(q.s.signalHints,1);
get('signalAnswer').value='13';get('signalCheck').onclick();assert(q.s.clues.includes('primepattern'));assert.equal(q.s.signalAttempts,2);assert(get('signalCheck').disabled);
get('save').onclick();const z=run(doc,storage,()=>{},()=>true);assert(z.s.clues.includes('primepattern'));assert.equal(z.s.signalHints,1);
console.log('PASS: scientific signal puzzle and persistence, 9 additional assertions');

function branchNora(label){
 get('reset').onclick();const p=run(doc,storage,()=>{},()=>true);
 p.move(-1,0);p.move(-1,0);p.move(0,-1);p.interact();click('roomart','Fita cassete');p.leaveRoom();
 get('freq').value='103.7';get('tune').onclick();
 p.advance(600-p.s.t);
 for(let i=0;i<4;i++)p.move(1,0);for(let i=0;i<6;i++)p.move(0,1);
 p.interact();click('dialog',label);return p;
}
const pub=branchNora('Apoiar a transmissão pública');
assert.equal(pub.s.decisions.future.choice,'public');assert(!pub.s.worldFlags.scrutiny);
pub.advance(180);pub.render();assert(pub.s.worldFlags.scrutiny);assert(pub.s.consequences.some(x=>x.id==='public:response'));
pub.advance(1440+8*60-pub.s.t);pub.render();assert.equal(pub.residents().find(x=>x.id==='future').activity,'Apresenta programa sobre a gravação');
get('save').onclick();const pubReload=run(doc,storage,()=>{},()=>true);assert.equal(pubReload.s.decisions.future.choice,'public');assert(pubReload.s.worldFlags.scrutiny);
const priv=branchNora('Preservar a gravação em sigilo');assert.equal(priv.s.decisions.future.choice,'private');
priv.advance(1440+8*60-priv.s.t);priv.render();assert.equal(priv.residents().find(x=>x.id==='future').activity,'Investiga em sigilo na praça');assert(!priv.s.worldFlags.scrutiny);assert(!priv.s.consequences.some(x=>x.id==='public:response'));
priv.advance(2580-priv.s.t);priv.render();assert(priv.s.npcMeetings.includes('exchange:raul:nora'));assert.equal(priv.s.consequences.filter(x=>x.id==='exchange').length,1);
priv.advance(100);priv.render();assert.equal(priv.s.consequences.filter(x=>x.id==='exchange').length,1);
console.log('PASS: branching NPC decisions, delayed consequences and persistence, 14 additional assertions');

const intercepted=branchNora('Apoiar a transmissão pública');
intercepted.advance(2580-intercepted.s.t);intercepted.render();
assert.equal(intercepted.s.fates.exchange,'intercepted');assert.equal(intercepted.s.fates.raul,'questioned');assert.equal(intercepted.s.fates.lia,'alone');
assert.equal(intercepted.residents().find(x=>x.id==='guard').activity,'Reage à apreensão do relatório');
assert.equal(intercepted.residents().find(x=>x.id==='future').x,7);
get('save').onclick();const reloadedFate=run(doc,storage,()=>{},()=>true);assert.equal(reloadedFate.s.fates.exchange,'intercepted');
reloadedFate.s.decisions.guard={choice:'warn',at:2581};reloadedFate.advance(120);assert.equal(reloadedFate.s.fates.exchange,'intercepted');
const relocated=branchNora('Apoiar a transmissão pública');
relocated.s.decisions.guard={choice:'warn',at:relocated.s.t};relocated.advance(2580-relocated.s.t);relocated.render();
assert.equal(relocated.s.fates.exchange,'relocated');assert.equal(relocated.s.fates.raul,'free');assert.equal(relocated.residents().find(x=>x.id==='guard').x,7);
get('reset').onclick();const autonomous=run(doc,storage,()=>{},()=>true);autonomous.advance(2580-autonomous.s.t);autonomous.render();
assert.equal(autonomous.s.fates.exchange,'delivered');assert.equal(autonomous.s.fates.lia,'alone');assert.equal(autonomous.s.consequences.filter(x=>x.id==='fate:exchange').length,1);
console.log('PASS: autonomous fates, divergent encounters and deadline persistence, 13 additional assertions');

const socialPublic=branchNora('Apoiar a transmissão pública');const broadcastAt=socialPublic.s.decisions.future.at;
socialPublic.advance(broadcastAt+60-socialPublic.s.t);assert(socialPublic.s.rumors.future.broadcast);assert(!socialPublic.s.rumors.clinic?.broadcast);
socialPublic.advance(60);assert.equal(socialPublic.s.rumors.clinic.broadcast.via,'rádio');assert(!socialPublic.s.rumors.guard?.broadcast);
socialPublic.advance(60);assert(socialPublic.s.rumors.guard.official);assert.equal(socialPublic.s.social['future:guard'],-1);
socialPublic.advance(60);assert.equal(socialPublic.s.rumors.clinic.official.via,'pacientes');
socialPublic.advance(2580-socialPublic.s.t);assert.equal(socialPublic.s.social['future:guard'],-3);assert(socialPublic.s.rumors.future.missing);
socialPublic.advance(120);assert(socialPublic.s.rumors.clinic.missing);socialPublic.render();assert.equal(socialPublic.s.social['future:guard'],-3);
get('save').onclick();const socialReload=run(doc,storage,()=>{},()=>true);assert.equal(socialReload.s.social['future:guard'],-3);assert.equal(socialReload.s.rumors.clinic.missing.via,'Nora');
const socialPrivate=branchNora('Preservar a gravação em sigilo');socialPrivate.advance(2700-socialPrivate.s.t);assert.equal(socialPrivate.s.social['future:guard'],2);assert(socialPrivate.s.rumors.future.alliance);assert(!socialPrivate.s.rumors.clinic?.official);
console.log('PASS: rumor timing, divergent social bonds, provenance and persistence, 16 additional assertions');

get('reset').onclick();const witness=run(doc,storage,()=>{},()=>true);
witness.move(-1,0);witness.move(-1,0);witness.move(0,-1);witness.interact();click('roomart','Fita cassete');witness.leaveRoom();witness.move(-1,0);witness.move(0,1);witness.move(0,1);witness.interact();click('roomart','Trilhos');witness.leaveRoom();get('night').onclick();witness.interact();
click('dialog','Registrar versão dos acontecimentos');assert(witness.s.clues.includes('statement_guard'));
click('dialog','Apresentar: Fita cassete');assert(!witness.s.confrontations.guard);
click('dialog','Apresentar: Marcas nos trilhos');assert.equal(witness.s.confrontations.guard.evidence,'rail');assert(witness.s.clues.includes('contradiction_guard'));assert.equal(witness.s.relations.guard,1);
get('save').onclick();const witnessReload=run(doc,storage,()=>{},()=>true);assert(witnessReload.s.testimonies.guard);assert(witnessReload.s.confrontations.guard);
console.log('PASS: testimony confrontation and persistence, 7 additional assertions');

get('reset').onclick();const nav=run(doc,storage,()=>{},()=>true);
for(const [tx,ty] of [[3,3],[8,3],[11,4],[1,6],[7,11]]){const path=nav.planRoute(5,5,tx,ty);assert(Array.isArray(path));let x=5,y=5;for(const [dx,dy] of path){x+=dx;y+=dy;if(!nav.walkable(x,y))throw Error('route crosses obstacle')}assert(Math.abs(x-tx)+Math.abs(y-ty)<=1)}
assert.equal(nav.planRoute(5,5,99,99),null);
get('destination').value='radio';get('routeGo').onclick();assert(Math.abs(nav.s.x-3)+Math.abs(nav.s.y-3)<=1);assert(nav.s.t>480);nav.interact();click('roomart','Fita cassete');nav.leaveRoom();nav.record('statement_guard');nav.record('primepattern');nav.render();
assert.equal(nav.clueCategory('statement_guard'),'statement');assert.equal(nav.clueCategory('primepattern'),'analysis');assert.equal(nav.clueCategory('radio'),'physical');
get('clueFilter').value='analysis';get('clueFilter').onchange();assert.equal(get('clues').children.length,1);assert.equal(get('clues').children[0].children[0].textContent,'Padrão de pulsos');
get('clueFilter').value='statement';get('clueFilter').onchange();assert.equal(get('clues').children.length,1);get('clueFilter').value='all';get('clueFilter').onchange();assert.equal(get('clues').children.length,3);
console.log('PASS: navigation and categorized journal');
function setupEcho(tune=false){get('reset').onclick();const p=run(doc,storage,()=>{},()=>true);assert(get('encounterStart').hidden);p.move(-1,0);p.move(-1,0);p.move(0,-1);p.interact();click('roomart','Fita cassete');p.leaveRoom();p.move(-1,0);p.move(0,1);p.move(0,1);p.interact();click('roomart','Trilhos');p.leaveRoom();if(tune){get('freq').value='103.7';get('tune').onclick()}assert(!get('encounterStart').hidden);get('encounterStart').onclick();assert(p.s.encounter);return p}
const sneaky=setupEcho();const before=sneaky.s.t;const x0=sneaky.s.x;sneaky.move(1,0);assert.equal(sneaky.s.x,x0);get('wait').onclick();assert.equal(sneaky.s.t,before);
click('encounterActions','Observar o padrão');for(let i=0;i<3;i++)click('encounterActions','Avançar em silêncio');assert.equal(sneaky.s.encounterOutcome,'stealth');assert(sneaky.s.clues.includes('echoTrace'));assert(!sneaky.s.worldFlags.echoDisturbed);
const contact=setupEcho(true);click('encounterActions','Observar o padrão');click('encounterActions','Reproduzir o sinal da fita');assert.equal(contact.s.encounterOutcome,'contact');assert(contact.s.clues.includes('echoMessage'));assert(!contact.s.worldFlags.echoDisturbed);
const combat=setupEcho();click('encounterActions','Ativar contrafase');click('encounterActions','Ativar contrafase');click('encounterActions','Preparar-se para o pulso');click('encounterActions','Ativar contrafase');assert.equal(combat.s.encounterOutcome,'combat');assert(combat.s.worldFlags.echoDisturbed);assert(combat.s.clues.includes('echoShock'));
combat.advance(1275-combat.s.t);combat.render();assert.equal(combat.residents().find(x=>x.id==='guard').activity,'Investiga o clarão da plataforma');
get('save').onclick();const reEcho=run(doc,storage,()=>{},()=>true);assert.equal(reEcho.s.encounterOutcome,'combat');assert(get('encounterStart').hidden);
const retreat=setupEcho();click('encounterActions','Recuar');assert.equal(retreat.s.encounterOutcome,'retreat');assert(retreat.s.clues.includes('echoLoss'));
const mid=setupEcho(true);click('encounterActions','Observar o padrão');get('save').onclick();const midReload=run(doc,storage,()=>{},()=>true);assert(midReload.s.encounter.observed);click('encounterActions','Reproduzir o sinal da fita');assert.equal(midReload.s.encounterOutcome,'contact');
console.log('PASS: stealth, contact, combat, retreat, NPC response and save/resume');

get('reset').onclick();const memory=run(doc,storage,()=>{},()=>true);memory.move(-1,0);memory.move(-1,0);memory.move(0,-1);memory.interact();click('roomart','Fotografia');click('puzzle','Prometer trazer meu tio de volta');assert.equal(memory.s.personalPromise,'return');assert(memory.s.clues.includes('portrait'));get('save').onclick();const memoryReload=run(doc,storage,()=>{},()=>true);assert.equal(memoryReload.s.personalPromise,'return');
const injured=setupEcho();click('encounterActions','Ativar contrafase');for(let i=0;i<3;i++){click('encounterActions','Preparar-se para o pulso');click('encounterActions','Ativar contrafase')}assert.equal(injured.s.encounterOutcome,'injured');assert(injured.s.worldFlags.echoInjury);assert(injured.s.clues.includes('echoLoss'));assert(!injured.s.end);console.log('PASS: personal memory and persistent promise');

function setupYard(){get('reset').onclick();const p=run(doc,storage,()=>{},()=>true);p.move(-1,0);p.move(-1,0);p.move(0,-1);p.interact();click('roomart','Fita cassete');p.leaveRoom();p.move(-1,0);p.move(0,1);p.move(0,1);p.interact();click('roomart','Trilhos');p.leaveRoom();assert(!get('stealthStart').hidden);get('stealthStart').onclick();assert(p.s.stealthRun);return p}
const yard=setupYard();assert.equal(get('stealthGrid').children.length,42);assert.equal(yard.s.stealthRun.x,0);assert.equal(yard.s.stealthRun.y,5);const yardStart=yard.s.t;yard.stealthAction('move',-1,0);assert.equal(yard.s.t,yardStart);assert.equal(yard.s.stealthRun.turn,0);yard.stealthAction('observe');assert(yard.s.clues.includes('yardObserved'));assert.equal(yard.s.stealthRun.turn,0);for(let i=0;i<6;i++)yard.stealthAction('move',1,0);assert(yard.s.stealthRun.document);assert(!yard.s.clues.includes('yardRecord'));get('save').onclick();const yardReload=run(doc,storage,()=>{},()=>true);assert(yardReload.s.stealthRun.document);for(let i=0;i<6;i++)yardReload.stealthAction('move',-1,0);assert.equal(yardReload.s.stealthOutcome,'success');assert(yardReload.s.clues.includes('yardRecord'));assert(!yardReload.s.worldFlags.yardAlert);
const caught=setupYard();caught.stealthAction('stance');for(const [dx,dy] of [[1,0],[1,0],[1,0],[1,0],[1,0],[0,-1],[0,-1],[0,-1],[0,-1]]){if(caught.s.stealthRun)caught.stealthAction('move',dx,dy)}if(caught.s.stealthRun){for(let i=0;i<8&&caught.s.stealthRun;i++)caught.stealthAction('wait')}assert.equal(caught.s.stealthOutcome,'caught');assert(caught.s.worldFlags.yardAlert);assert(!caught.s.clues.includes('yardRecord'));assert(!caught.s.end);assert(caught.s.clues.includes('yardCaught'));
const abandon=setupYard();abandon.stealthAction('leave');assert.equal(abandon.s.stealthOutcome,'retreat');assert(!abandon.s.worldFlags.yardAlert);assert(!abandon.s.end);
console.log('PASS: spatial stealth, cover, evidence extraction, capture and persistence');

function setupArena(prime=false){const p=setupYard();assert(get('arenaStart').hidden);for(let i=0;i<6;i++)p.stealthAction('move',1,0);for(let i=0;i<6;i++)p.stealthAction('move',-1,0);assert(p.s.clues.includes('yardRecord'));assert(get('arenaStart').hidden);get('freq').value='103.7';get('tune').onclick();if(prime){get('signalAnswer').value='13';get('signalCheck').onclick()}assert(!get('arenaStart').hidden);get('arenaStart').onclick();assert(p.s.arena);return p}
function approachArena(p){p.arenaAction('move',-1,0);p.arenaAction('move',0,-1);p.arenaAction('move',1,0);p.arenaAction('move',1,0);p.arenaAction('move',0,-1);assert.equal(p.s.arena.focus,3);assert.equal(p.s.arena.turn,5)}
const core=setupArena();assert.equal(get('arenaGrid').children.length,42);assert(core.arenaThreat(core.s.arena,3,5));assert(!core.arenaThreat(core.s.arena,2,5));const coreTime=core.s.t;core.arenaAction('move',0,1);assert.equal(core.s.t,coreTime);core.arenaAction('pulse');assert.equal(core.s.arena.turn,0);assert.equal(core.s.arena.stamina,3);approachArena(core);core.arenaAction('observe');core.arenaAction('guard');core.arenaAction('guard');core.arenaAction('listen');assert.equal(core.s.arena.resonance,1);get('save').onclick();const coreReload=run(doc,storage,()=>{},()=>true);assert.equal(coreReload.s.arena.resonance,1);coreReload.arenaAction('guard');coreReload.arenaAction('guard');coreReload.arenaAction('listen');assert.equal(coreReload.s.arenaOutcome,'contact');assert(coreReload.s.clues.includes('coreContact'));assert(coreReload.s.worldFlags.coreQuiet);assert(!coreReload.s.worldFlags.coreAlarm);
const fastCore=setupArena(true);approachArena(fastCore);fastCore.arenaAction('observe');fastCore.arenaAction('guard');fastCore.arenaAction('guard');fastCore.arenaAction('listen');assert.equal(fastCore.s.arenaOutcome,'contact');
const fight=setupArena();approachArena(fight);fight.arenaAction('pulse');for(let i=0;i<2;i++){fight.arenaAction('guard');fight.arenaAction('guard');fight.arenaAction('pulse')}assert.equal(fight.s.arenaOutcome,'combat');assert(fight.s.worldFlags.coreAlarm);assert(fight.s.clues.includes('coreAlarm'));assert(!fight.s.clues.includes('coreContact'));
const loss=setupArena();for(let i=0;i<5;i++)loss.arenaAction('observe');assert.equal(loss.s.arenaOutcome,'injured');assert(!loss.s.end);assert(loss.s.clues.includes('coreRetreat'));
const escape=setupArena();escape.arenaAction('leave');assert.equal(escape.s.arenaOutcome,'retreat');assert(!escape.s.worldFlags.coreAlarm);assert(!escape.s.end);
console.log('PASS: spatial combat, telegraph, defense, contact, retreat and persistence');

const locked=setupArena();const lockTime=locked.s.t;get('signalAnswer').value='13';get('signalCheck').onclick();assert(!locked.s.clues.includes('primepattern'));assert.equal(locked.s.t,lockTime);locked.arenaAction('leave');get('signalCheck').onclick();assert(locked.s.clues.includes('primepattern'));
locked.record('stationclock');locked.render();click('compare','Registro do pátio');click('compare','Relógio parado');get('combine').onclick();assert(locked.s.clues.includes('clockManipulation'));locked.record('coreContact');locked.record('echoMessage');locked.render();click('compare','Resposta do núcleo');click('compare','Advertência do eco');get('combine').onclick();assert(locked.s.clues.includes('corroboratedWarning'));
console.log('PASS: encounter isolation and linked deductions');

function setMode(mode){get('combatMode').value=mode;get('combatMode').onchange()}
setMode('story');const story=setupArena();assert.equal(story.s.combatMode,'story');assert.equal(story.s.arena.focus,5);assert.equal(story.s.arena.stamina,4);assert.equal(story.s.arena.integrity,2);assert(get('combatMode').disabled);
setMode('challenge');assert.equal(story.s.combatMode,'story');assert.equal(get('combatMode').value,'story');story.arenaAction('observe');assert.equal(story.s.arena.focus,5);story.arenaAction('move',0,-1);story.arenaAction('leave');assert.equal(story.s.arenaOutcome,'retreat');assert(!story.s.worldFlags.coreAlarm);assert(!get('combatMode').disabled);
get('save').onclick();const storyReload=run(doc,storage,()=>{},()=>true);assert.equal(storyReload.s.combatMode,'story');
setMode('challenge');const hard=setupArena();assert.equal(hard.s.arena.focus,3);assert.equal(hard.s.arena.stamina,2);assert.equal(hard.s.arena.integrity,4);hard.arenaAction('guard');hard.arenaAction('guard');assert.equal(hard.s.arena.stamina,1);hard.arenaAction('move',0,-1);hard.arenaAction('move',-1,0);assert.equal(hard.s.arena.charge,1);assert.equal(hard.s.arena.stamina,2);hard.arenaAction('move',0,-1);assert.equal(hard.s.arena.charge,2);assert.equal(hard.s.arena.dodges,2);assert.equal(hard.s.arena.focus,3);hard.arenaAction('precise');assert.equal(hard.s.arena.integrity,2);assert.equal(hard.s.arena.charge,0);assert.equal(hard.s.arena.stamina,1);
hard.arenaAction('move',1,0);hard.arenaAction('move',0,-1);hard.arenaAction('precise');assert.equal(hard.s.arenaOutcome,'combat');assert(hard.s.clues.includes('coreAlarm'));
setMode('normal');const recovery=setupArena();recovery.arenaAction('observe');assert.equal(recovery.s.arena.focus,2);recovery.arenaAction('guard');assert.equal(recovery.s.arena.turn,2);recovery.arenaAction('recenter');assert.equal(recovery.s.arena.focus,3);assert(recovery.s.arena.recentered);recovery.arenaAction('observe');recovery.arenaAction('guard');const t0=recovery.s.t;recovery.arenaAction('recenter');assert.equal(recovery.s.t,t0);assert.equal(recovery.s.arena.focus,2);
get('save').onclick();const recoveryReload=run(doc,storage,()=>{},()=>true);assert(recoveryReload.s.arena.recentered);assert.equal(recoveryReload.s.arena.mode,'normal');
console.log('PASS: difficulty profiles, accessible retreat, rewarded dodges, precise attacks and one-time recovery');

function freshPeople(){get('reset').onclick();return run(doc,storage,()=>{},()=>true)}
function visitResident(p,id){const n=p.residents().find(x=>x.id===id);const path=p.planRoute(p.s.x,p.s.y,n.x,n.y);if(!path)throw Error('no resident route');for(const [dx,dy] of path)p.move(dx,dy);const now=p.residents().find(x=>x.id===id);if(Math.abs(now.x-p.s.x)+Math.abs(now.y-p.s.y)>1){p.s.x=now.x;p.s.y=now.y;p.render()}click('nearbyPeople','Conversar com '+now.name)}
const expanded=freshPeople();assert.equal(expanded.residents().length,6);expanded.record('cargo');expanded.record('stationclock');expanded.record('patient');expanded.render();
visitResident(expanded,'helena');assert(expanded.s.npcKnown.includes('helena'));click('dialog','Conhecer sua história');assert(expanded.s.npcMeetings.includes('bio:helena'));click('dialog','Guardar uma cópia com Nora');assert.equal(expanded.s.personalCases.helena.choice,'copy');assert(!expanded.s.clues.includes('archiveCopy'));
visitResident(expanded,'bento');click('dialog','Ajudar Bento a comparar os relógios');assert.equal(expanded.s.personalCases.bento.choice,'share');
visitResident(expanded,'celina');click('dialog','Pedir uma verificação discreta com Lia');assert.equal(expanded.s.personalCases.celina.choice,'lia');
expanded.advance(1980-expanded.s.t);expanded.render();assert.equal(expanded.s.personalCases.helena.outcome,'copy');assert.equal(expanded.s.social['future:helena'],2);assert(!expanded.s.personalCases.bento.outcome);
expanded.advance(2100-expanded.s.t);assert.equal(expanded.residents().find(x=>x.id==='helena').activity,'Revisa a cópia com Nora');
expanded.advance(2380-expanded.s.t);expanded.render();assert.equal(expanded.s.personalCases.bento.outcome,'share');assert.equal(expanded.s.personalCases.celina.outcome,'lia');assert.equal(expanded.s.social['bento:guard'],1);assert.equal(expanded.s.social['celina:clinic'],2);assert.equal(expanded.residents().find(x=>x.id==='celina').activity,'Aguarda Lia na clínica');assert.equal(expanded.residents().find(x=>x.id==='bento').activity,'Compara os relógios ferroviários');
visitResident(expanded,'celina');click('dialog','Receber o resultado');assert(expanded.s.clues.includes('patientInquiry'));assert(!get('dialog').children.some(x=>x.textContent==='Receber o resultado'));
get('save').onclick();const expandedReload=run(doc,storage,()=>{},()=>true);assert.equal(expandedReload.s.personalCases.helena.outcome,'copy');assert(expandedReload.s.clues.includes('patientInquiry'));assert.equal(expandedReload.s.social['celina:clinic'],2);
const ignored=freshPeople();ignored.advance(2400-ignored.s.t);ignored.render();for(const id of ['helena','bento','celina'])assert.equal(ignored.s.personalCases[id].outcome,'alone');ignored.record('cargo');visitResident(ignored,'helena');assert(!get('dialog').children.some(x=>x.textContent==='Guardar uma cópia com Nora'));assert(!ignored.s.clues.includes('archiveCopy'));
console.log('PASS: six residents, interconnected personal quests, autonomous outcomes, rewards and persistence');

// All modular interiors must be navigable, including connected railway zones.
const roomConfig=JSON.parse(code.match(/const FZ_ROOMS=(.*?);\nconst FZ_R=/s)[1]);
const roomCore=new Function('FZ_ROOMS',code.slice(code.indexOf('function fzRoomSolid('),code.indexOf('function fzRoomDoor('))+'return {fzRoomSolid,fzRoomMove,fzRoomTarget}')(roomConfig);
let roomAssertions=0;
for(const [id,R] of Object.entries(roomConfig.layouts)){
 const step=.25,[sx,sy]=R.start,q=[[sx,sy]],visited=new Set(['0,0']),found=new Set();
 assert(!roomCore.fzRoomSolid(R,sx,sy),id+' spawn');roomAssertions++;
 assert(roomCore.fzRoomSolid(R,-1,sy),id+' wall');roomAssertions++;
 for(let j=0;j<q.length;j++){const [x,y]=q[j],t=roomCore.fzRoomTarget(R,{x,y});if(t)found.add(t.label);
 for(const [dx,dy] of [[step,0],[-step,0],[0,step],[0,-step]]){const nx=x+dx,ny=y+dy,k=Math.round((nx-sx)/step)+','+Math.round((ny-sy)/step);if(!visited.has(k)&&!roomCore.fzRoomSolid(R,nx,ny)){visited.add(k);q.push([nx,ny])}}}
 const expected=[...R.obj.filter(o=>o[3]).map(o=>o[3]),...(R.portals||[]).map(p=>p[2]),R.returnTo?'Voltar':'Sair pela porta'];
 for(const label of expected){assert(found.has(label),id+' unreachable '+label);roomAssertions++}
 for(const o of R.obj){if(o[0]==='rail'||o[0]==='platform')continue;assert(roomCore.fzRoomSolid(R,o[1],o[2]),id+' missing collision '+o[0]);roomAssertions++}
 for(const p of R.portals||[]){assert(roomConfig.layouts[p[3]]?.returnTo===id,id+' portal return');roomAssertions++}
}
const rp={x:1,y:1},empty={size:[5,5],obj:[]};roomCore.fzRoomMove(empty,rp,-20,0);assert(rp.x>=.18);roomAssertions++;
console.log('PASS: modular rooms, swept movement, all interaction locations and railway links: '+roomAssertions+' assertions');
