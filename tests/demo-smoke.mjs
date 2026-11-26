import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const code=readFileSync(new URL('../index.html',import.meta.url),'utf8').split('<script>')[1].split('</script>')[0];
const es=new Map();function node(){return{textContent:'',value:'',style:{},dataset:{},children:[],append(...x){this.children.push(...x)},replaceChildren(){this.children=[]},setAttribute(){},getContext(){return new Proxy({createRadialGradient(){return{addColorStop(){}}}},{get:(t,k)=>t[k]||(()=>{})})}}}
const doc={getElementById(id){if(!es.has(id))es.set(id,node());return es.get(id)},createElement:node,querySelectorAll(){return []}};
const mem={};const storage={getItem:k=>mem[k]||null,setItem:(k,v)=>mem[k]=v,removeItem:k=>delete mem[k]};
const run=new Function('document','localStorage','addEventListener','confirm','setTimeout','clearTimeout',code+';return {get s(){return s},move,interact,leaveRoom,finish,advance,render,residents,record,planRoute,walkable,clueCategory,beginEncounter,encounterAction};');
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
const injured=setupEcho();click('encounterActions','Ativar contrafase');click('encounterActions','Avançar em silêncio');click('encounterActions','Ativar contrafase');click('encounterActions','Ativar contrafase');assert(injured.s.encounter||injured.s.encounterOutcome);console.log('PASS: personal memory and persistent promise');
