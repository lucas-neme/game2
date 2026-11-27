/* Deterministic campaign state; no DOM or wall clock dependencies. */
function createValleyCampaign(data){
 const byId=Object.fromEntries(data.npcs.map(n=>[n.id,n]));
 const missions=Object.fromEntries(data.missions.map(m=>[m.id,m]));
 const phase=d=>data.chapters.find(c=>d>=c.days[0]&&d<=c.days[1])?.id||5;
 const day=t=>Math.max(1,Math.min(30,1+Math.floor(t/1440)));
 const minute=t=>((Math.floor(t)%1440)+1440)%1440;
 const fresh=()=>({version:1,train:false,solved:{},evidence:{},choices:{},events:{},meetings:{},storyHistory:{},storySeen:{},personalTalks:{},socialHistory:{},socialSeen:{},infrastructure:{},departures:{},clearedRoutes:{},manifestHistory:{},mechanisms:{},cinemaArchive:{},outcome:null,uncle:null,evacuation:null});
 const normalize=c=>Object.assign(fresh(),c||{});
 function chapter(c,t){if(!c.train)return 1;const cap=phase(day(t));for(let ch=2;ch<=5;ch++){if(ch>cap)return cap;if(data.missions.some(m=>m.chapter===ch&&!c.solved[m.id]))return ch}return 5}
 function available(c,t){return c.train&&!c.outcome?data.missions.filter(m=>m.chapter<=chapter(c,t)&&m.chapter<=phase(day(t))&&!c.solved[m.id]):[]}
 function meetingVariant(e,c,t){const rules=(data.meetingRules||[]).filter(r=>r.meeting===e.id&&Object.values(c.choices).some(q=>q.id===r.choice&&q.at+60<=t));const r=rules.at(-1);return r?{...e,loc:r.loc,activity:r.activity,redirected:true}:e}
 // Each reaction has one deterministic appointment, moved around existing meetings.
 function reactionWindow(r,c){
  const choices=Object.values(c.choices||{}), selected=r.choices.map(key=>choices.find(q=>q.id===key));
  if(selected.some(q=>!q))return null;
  const prior=(r.requires||[]).map(id=>c.storyHistory?.[id]);
  if(prior.some(q=>q?.status!=='concluído'))return null;
  const ready=Math.max(...selected.map(q=>q.at+60),...prior.map(q=>q.end+60),(r.day-1)*1440);
  const duration=r.to-r.from;
  for(let d=Math.max(r.day,1+Math.floor(ready/1440));d<=30;d++){
   const at=(d-1)*1440+r.from,end=at+duration;
   if(at<ready||end>43200)continue;
   if((data.appointments||[]).some(e=>e.day===d&&e.actors.includes(r.npc)&&e.minute<r.to&&e.until>r.from))continue;
   // Earlier authored reactions reserve their own slots; dependencies are topologically ordered.
   const earlier=(data.storyReactions||[]).slice(0,(data.storyReactions||[]).indexOf(r));
   if(earlier.some(other=>{if(other.npc!==r.npc)return false;const w=c.storyHistory?.[other.id]||reactionWindow(other,c);return w&&w.at<end&&w.end>at}))continue;
   return {at,end};
  }
  return null;
 }
 function storyReaction(id,t,c){
  if(c.outcome)return null;
  return (data.storyReactions||[]).filter(r=>{if(r.npc!==id||c.storyHistory?.[r.id])return false;const w=reactionWindow(r,c);return w&&t>=w.at&&t<w.end}).at(-1)||null;
 }
 function settleStory(c,t,deadAt=()=>null){
  c.storyHistory??={};const added=[];
  const cutoff=Math.min(t,c.outcome?.at??43200);
  for(const r of data.storyReactions||[]){
   const w=reactionWindow(r,c);if(!w||w.end>cutoff||c.storyHistory[r.id])continue;
   const death=deadAt(r.npc),left=departureAt(c,r.npc),status=(death!=null&&death<w.end)||(left!=null&&left<w.end)?'cancelado':'concluído';
   const row={...w,npc:r.npc,loc:r.loc,causes:[...(r.requires||[])],status,result:status==='concluído'?r.result:'O responsável morreu ou deixou o Vale antes de concluir a tarefa.',witnessed:!!c.storySeen?.[r.id]};
   c.storyHistory[r.id]=row;added.push({id:r.id,...row});
  }
  return added.sort((a,b)=>a.end-b.end||a.id.localeCompare(b.id));
 }
 function storyEpilogue(c){
  return Object.entries(c.storyHistory||{}).sort((a,b)=>a[1].end-b[1].end||a[0].localeCompare(b[0])).map(([id,r])=>({id,npc:r.npc,name:byId[r.npc]?.name||r.npc,status:r.status,result:r.result,causes:r.causes||[],witnessed:r.witnessed}));
 }
 // State is derived from timestamped facts; no accumulated per-frame side effects.
 function psychology(id,t,c,deadAt=()=>null){
  const p=byId[id]?.psychology;if(!p)return null;
  let trust=p.trust,fear=p.fear,resolve=p.resolve;
  const memories=[];
  for(const q of Object.values(c.choices||{})){if(q.at+60>t)continue;const e=data.psychologyEffects?.[q.id]?.[id];if(!e)continue;trust+=e[0];fear+=e[1];resolve+=e[2];memories.push(q.id)}
  for(const [key,r] of Object.entries(c.storyHistory||{})){if(r.end>t||![id,p.ally].includes(r.npc))continue;if(r.status==='concluído'){fear-=4;resolve+=5}else{fear+=10;resolve-=4}memories.push(key)}
  const loss=deadAt(p.ally);if(loss!=null&&loss<=t){fear+=22;resolve-=12;memories.push('loss:'+p.ally)}
  fear+=day(t)>=21?15:day(t)>=13?7:0;
  const clamp=x=>Math.max(0,Math.min(100,x));
  trust=clamp(trust);fear=clamp(fear);resolve=clamp(resolve);
  const mood=fear>=75?'assustado':trust<30?'desconfiado':resolve>=80?'determinado':'cauteloso';
  return {trust,fear,resolve,mood,goal:p.goal,ally:p.ally,memories,dialogue:fear>=75?p.afraid:trust<30?'Ainda não sei se devo contar com você. '+p.calm:p.calm};
 }
 function personalTalk(c,t,id,deadAt=()=>null){
  if(c.outcome||!byId[id]||deadAt(id)!=null&&deadAt(id)<=t)return null;
  const p=psychology(id,t,c,deadAt);if(!p)return null;
  c.personalTalks??={};const key=id+':'+day(t);
  if(c.personalTalks[key])return {...p,recorded:false};
  c.personalTalks[key]={at:t,mood:p.mood,memories:p.memories.slice()};return {...p,recorded:true};
 }
 // Optional behavioral windows never override authored meetings, story tasks or explicit choices.
 function autonomousBehavior(id,t,c,deadAt=()=>null){
  if(!c.train||c.outcome||day(t)<13)return null;
  const m=minute(t),p=psychology(id,t,c,deadAt),b=byId[id]?.psychology?.behavior;
  if(!p||!b)return null;
  if(m>=480&&m<600&&p.fear>=75&&p.fear>p.resolve)return {loc:b.safe,activity:'Procura segurança e reorganiza seus pensamentos',reason:'fear',autonomous:true};
  if(m>=720&&m<780&&p.trust<30)return {loc:b.safe,activity:'Evita conversas públicas e reflete sobre as últimas decisões',reason:'distrust',autonomous:true};
  if(m>=1200&&m<1260&&p.resolve>=80&&p.resolve>=p.fear+10)return {loc:b.help,activity:b.activity,reason:'resolve',autonomous:true};
  return null;
 }
 // Social scenes reserve shared windows after all mission-related appointments.
 function socialWindow(e,c){
  const list=data.socialScenes||[],choices=Object.values(c.choices||{}),chosen=e.choices.map(id=>choices.find(q=>q.id===id)),prior=(e.requires||[]).map(id=>c.socialHistory?.[id]);
  if(chosen.some(q=>!q)||prior.some(q=>q?.status!=='concluído'))return null;
  const ready=Math.max((e.day-1)*1440,...chosen.map(q=>q.at+60),...prior.map(q=>q.end+60));
  for(let d=Math.max(e.day,1+Math.floor(ready/1440));d<=30;d++){
   const at=(d-1)*1440+e.from,end=(d-1)*1440+e.to;
   if(at<ready||end>43200)continue;
   if((data.appointments||[]).some(q=>q.day===d&&q.actors.some(id=>e.actors.includes(id))&&q.minute<e.to&&q.until>e.from))continue;
   if((data.storyReactions||[]).some(q=>{if(!e.actors.includes(q.npc))return false;const w=c.storyHistory?.[q.id]||reactionWindow(q,c);return w&&w.at<end&&w.end>at}))continue;
   if(list.slice(0,list.indexOf(e)).some(q=>{if(!q.actors.some(id=>e.actors.includes(id)))return false;const w=c.socialHistory?.[q.id]||socialWindow(q,c);return w&&w.at<end&&w.end>at}))continue;
   return {at,end};
  }return null;
 }
 function activeSocial(id,t,c,deadAt=()=>null){
  if(!c.train||c.outcome)return null;
  return (data.socialScenes||[]).find(e=>{if(!e.actors.includes(id)||c.socialHistory?.[e.id]||e.actors.some(a=>(deadAt(a)!=null&&deadAt(a)<=t)||departed(c,a,t)))return false;const w=socialWindow(e,c);return w&&t>=w.at&&t<w.end})||null;
 }
 function settleSocial(c,t,deadAt=()=>null){
  c.socialHistory??={};const added=[];if(!c.train)return added;
  for(const e of data.socialScenes||[]){if(c.socialHistory[e.id])continue;const w=socialWindow(e,c);if(!w||w.end>Math.min(t,c.outcome?.at??43200))continue;
   const cancelled=e.actors.some(id=>(deadAt(id)!=null&&deadAt(id)<w.end)||(departureAt(c,id)!=null&&departureAt(c,id)<w.end));
   const row={...w,actors:e.actors.slice(),loc:e.loc,status:cancelled?'cancelado':'concluído',delta:cancelled?0:e.delta,result:cancelled?'O encontro não pôde ser concluído devido à perda de um participante.':e.result,witnessed:!!c.socialSeen?.[e.id]};c.socialHistory[e.id]=row;added.push({id:e.id,...row});
  }return added.sort((a,b)=>a.end-b.end||a.id.localeCompare(b.id));
 }
 function relationship(a,b,t,c,deadAt=()=>null){
  if(!byId[a]||!byId[b]||a===b)return null;
  let score=50+(byId[a].psychology?.ally===b||byId[b].psychology?.ally===a?15:0);
  const memories=[];
  for(const [id,r] of Object.entries(c.socialHistory||{})){if(r.end<=t&&r.status==='concluído'&&r.actors.includes(a)&&r.actors.includes(b)){score+=r.delta;memories.push(id)}}
  score=Math.max(0,Math.min(100,score));const lost=[a,b].some(id=>deadAt(id)!=null&&deadAt(id)<=t);
  return {score,memories,status:lost?'vínculo interrompido':score>=75?'aliados':score<=40?'em conflito':'coexistência'};
 }
 function witnessSocial(c,t,id,actor,near,deadAt=()=>null){
  const e=activeSocial(actor,t,c,deadAt);if(!near||!e||e.id!==id)return false;c.socialSeen??={};if(c.socialSeen[id])return false;c.socialSeen[id]={at:t,actor};return true;
 }
 // Electrical conditions depend on the story clock and actual local intervention.
 function infrastructure(c,t){
  const d=day(t),m=minute(t),cfg=data.infrastructure;
  if(!c.train||!cfg)return {level:0,mode:'normal',west:'normal',east:'normal',project:'normal'};
  let level=0;
  for(const r of cfg.timeline){if(d>=r.day&&m>=r.from&&m<r.to)level=Math.max(level,r.level)}
  const action=c.infrastructure?.switchgear,done=action&&action.at<=t;
  let west=level>=2?'off':level===1?'unstable':'normal',east=level>=1?'off':'normal',project=level>=4?'unstable':'normal';
  if(done&&action.mode==='repair'&&level>=1){west='emergency';east='emergency'}
  if(done&&action.mode==='isolate'){project='off';if(level>=1){west='emergency';east=level>=3?'off':'unstable'}}
  return {level,mode:done?action.mode:'normal',west,east,project};
 }
 function districtAt(x,y){return x>=25&&y>=6?'project':x>=14?'east':'west'}
 function powerAt(c,t,x,y){
  const p=infrastructure(c,t),district=districtAt(x,y),status=p[district];
  if(status==='normal'||status==='unstable')return status;
  const near=(data.infrastructure?.districts[district].emergency||[]).some(id=>{const a=data.locations[id];return Math.hypot(a.x-x,a.y-y)<=1.1});
  return status==='emergency'&&near?'emergency':'off';
 }
 function operateGrid(c,t,mode){
  const chosen=mode==='repair'?'repair-grid':mode==='isolate'?'isolate-grid':null;
  if(!chosen||!c.train||c.outcome||!c.solved.power||c.choices.power?.id!==chosen||c.choices.power.at+60>t||c.infrastructure?.switchgear)return false;
  c.infrastructure??={};c.infrastructure.switchgear={mode,at:t};return true;
 }
 // Civilian departures happen only after the player confirms the withdrawal plan.
 function departureAt(c,id){
  if(!c.train||c.evacuation!=='retirada organizada'||!Number.isFinite(c.evacuationAt))return null;
  const cfg=data.civilDefense?.departures||[],slot=cfg.find(e=>e.actors.includes(id));if(!slot)return null;
  // A late confirmation rolls the group forward to the next evening.
  const ready=c.evacuationAt+120,base=(slot.day-1)*1440+slot.minute;
  const at=base>=ready?base:base+Math.ceil((ready-base)/1440)*1440;
  return at<43200?at:null;
 }
 function departed(c,id,t){const row=c.departures?.[id];return !!row&&row.status==='evacuado'&&row.at<=t}
 function settleDepartures(c,t,deadAt=()=>null){
  c.departures??={};const added=[],cutoff=Math.min(t,c.outcome?.at??43200);
  for(const n of data.npcs){const at=departureAt(c,n.id);if(at==null||at>cutoff||c.departures[n.id])continue;const death=deadAt(n.id);const row={at,status:death!=null&&death<=at?'não embarcou':'evacuado'};c.departures[n.id]=row;added.push({id:n.id,...row})}
  return added.sort((a,b)=>a.at-b.at||a.id.localeCompare(b.id));
 }
 function serviceStatus(c,t,id){
  const cfg=data.civilDefense?.services?.[id];if(!cfg||!c.train)return {open:true,label:'Acesso normal'};
  const m=minute(t),crisis=day(t)>=21,close=crisis?cfg.crisisTo:cfg.to;
  const open=m>=cfg.from&&m<close;return {open,label:open?'Atendimento em funcionamento':crisis?'Atendimento suspenso pela crise':'Fora do horário de atendimento',close};
 }
 // Small physical obstructions leave alternative approaches to every investigation site.
 function activeBarriers(c,t){
  if(!c.train)return [];
  return (data.routeBarriers||[]).filter(r=>day(t)>=r.day&&(!r.choice||Object.values(c.choices||{}).some(q=>q.id===r.choice&&q.at+60<=t))&&!(c.clearedRoutes?.[r.id]?.at<=t));
 }
 function clearBarrier(c,t,id){
  if(c.outcome||!activeBarriers(c,t).some(r=>r.id===id&&r.clear))return false;
  c.clearedRoutes??={};c.clearedRoutes[id]={at:t};return true;
 }
 function roleAssignments(c,t,deadAt=()=>null){
  if(!c.train||c.outcome||day(t)<21)return [];
  const unavailable=id=>{const death=deadAt(id);return (death!=null&&death<=t)||departed(c,id,t)};
  const used=new Set(),rows=[];
  for(const role of data.continuityRoles||[]){
   if(!unavailable(role.primary))continue;
   const actor=role.alternates.find(id=>!unavailable(id)&&!used.has(id));
   if(actor)used.add(actor);
   rows.push({...role,actor:actor||null});
  }return rows;
 }
 function signalStrength(c,t,loc){
 if(!c.train||!data.locations[loc])return 0;
 const d=day(t),m=minute(t),p=data.locations[loc],district=districtAt(p.x,p.y),grid=infrastructure(c,t);
 let v=d>=28?82:d>=25?65:d>=21?53:d>=17?42:d>=13?30:d>=6?18:5;
 v+=district==='project'?14:district==='east'?8:0;if(m<360||m>=1080)v+=8;v+=grid.level*2;
 if(grid.mode==='isolate')v-=district==='project'?16:8;if(grid.mode==='repair')v-=5;if(mechanismEffects(c,t).includes('counterwave-reference')&&district==='project')v-=6;
 return Math.max(0,Math.min(100,v));
 }
 function activeManifestations(c,t){
 if(!c.train||c.outcome||t>=43200)return [];
 const m=minute(t);return (data.manifestations||[]).filter(e=>day(t)>=e.day&&m>=e.from&&m<e.to&&!c.manifestHistory?.[e.id]?.resolved&&signalStrength(c,t,e.loc)>=e.min);
 }
 function manifestAction(c,t,id,action,frequency=null){
 const e=activeManifestations(c,t).find(q=>q.id===id);if(!e||!['observe','avoid','contact','disperse'].includes(action))return null;
 c.manifestHistory??={};const r=c.manifestHistory[id]??={attempts:[],observed:false,resolved:null};
 if(action==='observe'&&r.observed)return null;
 if(action==='avoid'&&r.attempts.some(q=>q.action==='avoid'&&day(q.at)===day(t)))return null;
 if((action==='contact'||action==='disperse')&&!r.observed)return null;
 if(action==='contact'&&(!Number.isFinite(frequency)||Math.abs(frequency-e.frequency)>.051)){if(r.attempts.some(q=>q.action==='contact-failed'&&q.at===t))return null;r.attempts.push({action:'contact-failed',at:t});return {ok:false,text:'A modulação não coincide com o vestígio.',minutes:10}}
 r.attempts.push({action,at:t});if(action==='observe')r.observed=true;
 if(action==='contact'||action==='disperse')r.resolved={action,at:t};
 return {ok:true,text:action==='avoid'?'Você se afasta sem perturbar a manifestação.':e[action],minutes:action==='observe'?10:action==='avoid'?5:20};
 }
 function manifestationAvoidance(id,t,c){
 const e=activeManifestations(c,t).find(q=>q.actor===id);if(!e||psychology(id,t,c)?.resolve>=80)return null;
 return {loc:e.refuge,activity:'Evita a região onde o sinal se manifesta',reason:'manifest:'+e.id,changed:true};
 }
 function mechanismReady(c,t,id){
  const e=(data.mechanisms||[]).find(q=>q.id===id);
  return !!e&&c.train&&!c.outcome&&t<43200&&phase(day(t))>=e.chapter&&!c.mechanisms?.[id]?.solved&&e.requires.every(k=>c.evidence[k]&&c.evidence[k].at<=t)&&(e.after||[]).every(k=>c.mechanisms?.[k]?.solved&&c.mechanisms[k].at<=t);
 }
 function mechanismAttempt(c,t,id,values){
  const e=(data.mechanisms||[]).find(q=>q.id===id);
  if(!mechanismReady(c,t,id)||!Array.isArray(values)||values.length!==e.controls.length||values.some((v,i)=>!Number.isInteger(v)||v<0||v>=e.controls[i].options.length))return null;
  c.mechanisms??={};const r=c.mechanisms[id]??={attempts:0,solved:false};
  r.attempts++;r.lastAt=t;const ok=values.every((v,i)=>v===e.answer[i]);
  if(ok){r.solved=true;r.at=t;r.effect=e.effect}
  return {ok,minutes:ok?15:10,text:ok?e.result:'A configuração não coincide com os registros. O equipamento volta à posição segura.'};
 }
 function mechanismEffects(c,t){return Object.values(c.mechanisms||{}).filter(r=>r.solved&&r.at<=t).map(r=>r.effect)}
 function schedule(id,t,c,dead=false,deadAt=()=>null){if(dead||!byId[id]||departed(c,id,t))return null;const n=byId[id],d=day(t),m=minute(t),row=n.days[d-1],base=row.slots.findLast(x=>x.minute<=m)||row.slots[0];let result={...base,day:d,id,name:n.name,sprite:n.sprite,changed:false};
  const departure=departureAt(c,id);if(departure!=null&&t>=departure-60&&t<departure)return {...result,loc:'rail',activity:'Aguarda o embarque para sair do Vale',changed:true,reason:'evacuation-boarding'};
  const meeting=(data.appointments||[]).find(e=>e.day===d&&m>=e.minute&&m<e.until&&e.actors.includes(id));if(meeting){const a=meetingVariant(meeting,c,(d-1)*1440+meeting.minute);return {...result,loc:a.loc,activity:a.activity,changed:!!a.redirected,reason:a.id,meeting:a.id}}
  const reaction=storyReaction(id,t,c);if(reaction)return {...result,loc:reaction.loc,activity:reaction.activity,changed:true,reason:reaction.id,storyReaction:reaction.id,dialogue:reaction.dialogue};
  const social=activeSocial(id,t,c,deadAt);if(social)return {...result,loc:social.loc,activity:social.activity,changed:true,reason:social.id,socialScene:social.id,dialogue:social.dialogue};
  const changes=data.rules.filter(r=>r.npc===id&&m>=r.from&&m<r.to&&Object.values(c.choices).some(x=>x.id===r.choice&&x.at+60<=t));
  changes.sort((a,b)=>Object.values(c.choices).find(x=>x.id===b.choice).at-Object.values(c.choices).find(x=>x.id===a.choice).at);
  if(changes.length){const z=changes[0];return {...result,loc:z.loc,activity:z.activity,changed:true,reason:z.choice}}
  const role=minute(t)>=660&&minute(t)<720?roleAssignments(c,t,deadAt).find(r=>r.actor===id):null;
  if(role)return {...result,loc:role.loc,activity:role.activity,changed:true,reason:'succession:'+role.id};
  const hazard=manifestationAvoidance(id,t,c);if(hazard)return {...result,...hazard};
  const autonomous=autonomousBehavior(id,t,c,deadAt);return autonomous?{...result,...autonomous,changed:true}:result;
 }
 function collect(c,t,id,index,via){const m=missions[id],e=m?.sources[index];if(!e||!available(c,t).includes(m))return false;const key=id+':'+index;if(c.evidence[key])return false;if(e.actor?!['actor','archive'].includes(via):via!=='site')return false;c.evidence[key]={at:t,via};return true}
 function solve(c,t,id,answer){const m=missions[id];if(!m||!available(c,t).includes(m)||!m.sources.every((_,i)=>c.evidence[id+':'+i])||answer!==m.answer)return false;c.solved[id]={at:t};return true}
 function choose(c,t,id,choice){const m=missions[id];if(c.outcome||!m||!c.solved[id]||c.choices[id]||!m.choices.some(q=>q[0]===choice))return false;c.choices[id]={id:choice,at:t};return true}
 function tick(c,t){const added=[];for(const e of data.events){const at=(e.day-1)*1440+e.minute;if(at<=Math.min(t,c.outcome?.at??43200)&&!c.events[e.day]){c.events[e.day]=at;added.push(e)}}return added}
 function settleMeetings(c,t,deadAt=()=>null){c.meetings??={};const added=[];for(const e of data.appointments||[]){const at=(e.day-1)*1440+e.minute,end=(e.day-1)*1440+e.until;if(end>Math.min(t,c.outcome?.at??43200)||c.meetings[e.id])continue;const a=meetingVariant(e,c,at),actors=e.actors.filter(id=>{const dead=deadAt(id);return (dead==null||dead>at)&&(departureAt(c,id)==null||departureAt(c,id)>at)});const row={at,end,loc:a.loc,activity:a.activity,actors,redirected:!!a.redirected,status:actors.length>=2?'realizado':'cancelado',witnessed:!!c.seenMeetings?.[e.id]};c.meetings[e.id]=row;added.push({id:e.id,...row})}return added}
 function witness(c,t,id,near){const e=(data.appointments||[]).find(e=>e.id===id);if(!e||!near)return false;const at=(e.day-1)*1440+e.minute,end=(e.day-1)*1440+e.until;if(t<at||t>=end)return false;c.seenMeetings??={};if(c.seenMeetings[id])return false;c.seenMeetings[id]={at:t,loc:meetingVariant(e,c,at).loc};return true}
 // Freeze only facts known at the final timestamp; never invent deaths or fulfilled personal goals.
 function residentEpilogues(c,deadAt=()=>null){
  if(!c.outcome)return [];
  const t=c.outcome.at;
  return data.npcs.map(n=>{
   const death=deadAt(n.id),left=departed(c,n.id,t),dead=death!=null&&death<=t;
   const status=dead?'morto':left?'evacuado':'presente no último registro';
   const tasks=Object.entries(c.storyHistory||{}).filter(([id,r])=>r.npc===n.id&&r.end<=t&&r.status==='concluído');
   const fulfilled=!!n.epilogue?.requires.some(id=>tasks.some(([k])=>k===id));
   const lines=[fulfilled?n.epilogue.achieved:n.epilogue?.pending||n.bio];
   const scenes=Object.entries(c.socialHistory||{}).filter(([id,r])=>r.end<=t&&r.status==='concluído'&&r.actors.includes(n.id)).sort((a,b)=>a[1].end-b[1].end);
   const partners=[...new Set(scenes.flatMap(([id,r])=>r.actors.filter(id=>id!==n.id)))];
   for(const other of partners){const rel=relationship(n.id,other,t,c,deadAt);lines.push('Vínculo com '+byId[other].name+': '+rel.status+'.')}
   if(n.id==='electrician'&&c.infrastructure?.switchgear?.at<=t)lines.push(c.infrastructure.switchgear.mode==='repair'?'O protagonista acionou a alimentação de emergência.':'O protagonista isolou os circuitos do Horizonte.');
   if(n.id==='watchman'&&c.outcome.uncle==='resgatado')lines.push('O tio do protagonista foi retirado do confinamento.');
   if(n.id==='bento'||n.id==='scientist'||n.id==='radio-technician'){if(mechanismEffects(c,t).includes('counterwave-reference'))lines.push('A contrafase foi calibrada antes do desfecho.')}
   if(n.id==='future'&&c.outcome.id==='truth')lines.push('O desfecho registra a divulgação das provas.');
   if(dead)lines.push('Sua morte foi registrada antes do encerramento da campanha.');
   else if(left)lines.push('Embarcou no trem de retirada; sua vida posterior não foi acompanhada.');
   else lines.push(data.endingEpilogues?.[c.outcome.id]||'O destino posterior permanece desconhecido.');
   return {id:n.id,name:n.name,status,fulfilled,tasks:tasks.map(([id,r])=>id),text:lines.join(' ')};
  });
 }
 function freezeEpilogues(c,deadAt=()=>null){
  if(!c.outcome)return [];
  if(!Array.isArray(c.outcome.residents))c.outcome.residents=residentEpilogues(c,deadAt);
  return c.outcome.residents;
 }
 function collectCinema(c,t){
 c.cinemaArchive??={};if(!c.train)return [];
 const cfg=data.cinema||{},cutoff=Math.min(t,c.outcome?.at??43200),added=[];
 const add=(id,at,title,frames)=>{if(c.cinemaArchive[id]||at>cutoff)return;const row={id,at,title,frames:frames.map(f=>f.slice())};c.cinemaArchive[id]=row;added.push(row)};
 for(const e of cfg.chapters||[]){const at=(e.day-1)*1440;if(at<=cutoff&&chapter(c,cutoff)>=Number(e.id.split('-')[1]))add(e.id,at,e.title,e.frames)}
 for(const e of cfg.choices||[]){const q=Object.values(c.choices||{}).find(q=>q.id===e.choice);if(q)add(e.id,q.at,e.title,e.frames)}
 for(const n of data.npcs){const r=c.departures?.[n.id];if(r?.status==='evacuado')add('departure:'+n.id,r.at,'Retirada de '+n.name,[['A estação',n.name+' embarcou no trem de retirada. O Vale ficou um pouco mais vazio.']])}
 if(c.outcome&&cfg.endings?.[c.outcome.id]){const frames=cfg.endings[c.outcome.id].map(f=>f.slice());frames.push(['O destino dos moradores','Tio: '+(c.outcome.uncle||'desconhecido')+'. Moradores: '+(c.outcome.evacuation||'não confirmada')+'.']);for(const e of c.outcome.residents||[])frames.push([e.name+' — '+e.status,e.text]);frames.push(['Frequência Zero','Fim da campanha. Roteiro, investigação e memória do Vale.']);add('ending:'+c.outcome.id,c.outcome.at,'Desfecho — '+c.outcome.id,frames)}
 return added.sort((a,b)=>a.at-b.at||a.id.localeCompare(b.id));
 }
 function cinemaArchive(c){return Object.values(c.cinemaArchive||{}).sort((a,b)=>a.at-b.at||a.id.localeCompare(b.id))}
 // Pure audio director: no playback or wall-clock state in saves.
 function soundtrackCue(c,t,loc,context={}){
 const ending={shutdown:'meanwhile',horizon:'void',zero:'echoes',contact:'shadows',truth:'reawakening',sacrifice:'unraveling',silence:'incantation'};
 const scene=context.scene||'';let id='long-dark';
 if(c.outcome)id=ending[c.outcome.id]||'long-dark';else if(context.danger)id=context.stealth?'nightfall':'void';else if(scene.startsWith('departure:')||scene==='evacuate'||loc==='shelter')id='moment';else if(scene==='chapter-4')id='nightfall';else if(scene==='chapter-5'||loc==='horizon'||loc==='bunker')id='void';else if(loc==='forest'||loc==='cemetery'||activeManifestations(c,t).some(e=>e.loc===loc))id='incantation';else if(loc==='clinic'||loc==='celina')id='unraveling';else if(loc==='radio'||loc==='observatory')id='meanwhile';else if(['archive','substation','tunnel'].includes(loc)||context.investigation)id='intervention';else if(signalStrength(c,t,loc)>=60)id='nightfall';else if(minute(t)>=1080||minute(t)<360)id='shadows';
 return data.soundtrack.find(q=>q.id===id);
 }
 function audioDirection(c,t,loc,cinema=false){
  const profiles=data.audioProfiles||{},strength=signalStrength(c,t,loc),grid=infrastructure(c,t);
  const site=data.locations[loc],power=site?powerAt(c,t,site.x,site.y):'normal';
  const anomaly=activeManifestations(c,t).some(e=>e.loc===loc);
  let mood=c.outcome?'ending':cinema?'cinema':strength>=80?'critical':strength>=60?'collapse':strength>=35||anomaly?'unease':day(t)>=6&&c.train?'investigation':'quiet';
  const p=profiles[mood]||profiles.quiet;
  return {mood,strength,power,anomaly,root:p.root,intervals:p.intervals.slice(),tempo:p.tempo,bed:p.bed,lead:p.lead};
 }
 function endings(c,t){if(!c.train||!c.solved.last||day(t)<28||t>=43200||c.outcome)return [];const selected=id=>Object.values(c.choices).some(x=>x.id===id);
  const out=[["shutdown","Desligar fisicamente o emissor"],["horizon","Autorizar a amplificação"]];
  if(c.solved.zero&&selected("test-counterwave"))out.push(["zero","Emitir a Frequência Zero"]);
  if(c.solved.zero&&c.solved.history)out.push(["contact","Estabelecer contato limitado"]);
  if(c.solved.horizon&&selected("secure-evidence"))out.push(["truth","Desligar e divulgar as provas"]);
  if(c.solved.rescue&&selected("rescue-uncle"))out.push(["sacrifice","Manter a contramedida manualmente"]);
  return out;
 }
 function finish(c,t,id){if(!endings(c,t).some(e=>e[0]===id))return false;const selected=x=>Object.values(c.choices).some(q=>q.id===x);c.outcome={id,at:t,uncle:c.uncle||"destino desconhecido",evacuation:c.evacuation||"não confirmada",prepared:{calibrations:mechanismEffects(c,t),grid:selected("repair-grid"),counterwave:selected("test-counterwave"),evacuation:selected("evacuate"),rescue:selected("rescue-uncle")}};return true}
 function resolveAction(c,t,id){if(c.outcome)return false;const chosen=x=>Object.values(c.choices).some(q=>q.id===x&&q.at<=t);if(id==="rescue"&&c.solved.rescue&&chosen("rescue-uncle")&&!c.uncle){c.uncle="resgatado";return true}if(id==="evacuation"&&c.solved.evacuation&&(!c.evacuation||(c.evacuation==='retirada organizada'&&!Number.isFinite(c.evacuationAt)))&&(chosen("evacuate")||chosen("shelter-in-place"))){c.evacuation=chosen("evacuate")?"retirada organizada":"abrigo reforçado";c.evacuationAt=t;return true}return false}
 function deadline(c,t){if(t>=43200&&!c.outcome){c.outcome={id:"silence",at:43200,uncle:c.uncle||"destino desconhecido",evacuation:c.evacuation||"não confirmada"};return true}return false}
 return {data,byId,missions,soundtrackCue,audioDirection,collectCinema,cinemaArchive,residentEpilogues,freezeEpilogues,mechanismReady,mechanismAttempt,mechanismEffects,signalStrength,activeManifestations,manifestAction,manifestationAvoidance,activeBarriers,clearBarrier,roleAssignments,departureAt,departed,settleDepartures,serviceStatus,infrastructure,powerAt,districtAt,operateGrid,psychology,personalTalk,autonomousBehavior,socialWindow,activeSocial,settleSocial,relationship,witnessSocial,storyReaction,reactionWindow,settleStory,storyEpilogue,phase,day,minute,fresh,normalize,chapter,available,schedule,collect,solve,choose,tick,settleMeetings,witness,meetingVariant,endings,finish,deadline,resolveAction};
}
