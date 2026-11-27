/* Deterministic campaign state; no DOM or wall clock dependencies. */
function createValleyCampaign(data){
 const byId=Object.fromEntries(data.npcs.map(n=>[n.id,n]));
 const missions=Object.fromEntries(data.missions.map(m=>[m.id,m]));
 const phase=d=>data.chapters.find(c=>d>=c.days[0]&&d<=c.days[1])?.id||5;
 const day=t=>Math.max(1,Math.min(30,1+Math.floor(t/1440)));
 const minute=t=>((Math.floor(t)%1440)+1440)%1440;
 const fresh=()=>({version:1,train:false,solved:{},evidence:{},choices:{},events:{},meetings:{},storyHistory:{},storySeen:{},outcome:null,uncle:null,evacuation:null});
 const normalize=c=>Object.assign(fresh(),c||{});
 function chapter(c,t){if(!c.train)return 1;const cap=phase(day(t));for(let ch=2;ch<=5;ch++){if(ch>cap)return cap;if(data.missions.some(m=>m.chapter===ch&&!c.solved[m.id]))return ch}return 5}
 function available(c,t){return c.train&&!c.outcome?data.missions.filter(m=>m.chapter<=chapter(c,t)&&m.chapter<=phase(day(t))&&!c.solved[m.id]):[]}
 function meetingVariant(e,c,t){const rules=(data.meetingRules||[]).filter(r=>r.meeting===e.id&&Object.values(c.choices).some(q=>q.id===r.choice&&q.at+60<=t));const r=rules.at(-1);return r?{...e,loc:r.loc,activity:r.activity,redirected:true}:e}
 // Each reaction has one deterministic appointment, moved around existing meetings.
 function reactionWindow(r,c){
  const choices=Object.values(c.choices||{}), selected=r.choices.map(key=>choices.find(q=>q.id===key));
  if(selected.some(q=>!q))return null;
  const ready=Math.max(...selected.map(q=>q.at+60),(r.day-1)*1440);
  const duration=r.to-r.from;
  for(let d=Math.max(r.day,1+Math.floor(ready/1440));d<=30;d++){
   const at=(d-1)*1440+r.from,end=at+duration;
   if(at<ready||end>43200)continue;
   if((data.appointments||[]).some(e=>e.day===d&&e.actors.includes(r.npc)&&e.minute<r.to&&e.until>r.from))continue;
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
   const death=deadAt(r.npc),status=death!=null&&death<w.end?'cancelado':'concluído';
   const row={...w,npc:r.npc,loc:r.loc,status,result:status==='concluído'?r.result:'O responsável não sobreviveu para concluir a tarefa.',witnessed:!!c.storySeen?.[r.id]};
   c.storyHistory[r.id]=row;added.push({id:r.id,...row});
  }
  return added;
 }
 function storyEpilogue(c){
  return Object.entries(c.storyHistory||{}).sort((a,b)=>a[1].end-b[1].end||a[0].localeCompare(b[0])).map(([id,r])=>({id,npc:r.npc,name:byId[r.npc]?.name||r.npc,status:r.status,result:r.result,witnessed:r.witnessed}));
 }
 function schedule(id,t,c,dead=false){if(dead||!byId[id])return null;const n=byId[id],d=day(t),m=minute(t),row=n.days[d-1],base=row.slots.findLast(x=>x.minute<=m)||row.slots[0];let result={...base,day:d,id,name:n.name,sprite:n.sprite,changed:false};
  const meeting=(data.appointments||[]).find(e=>e.day===d&&m>=e.minute&&m<e.until&&e.actors.includes(id));if(meeting){const a=meetingVariant(meeting,c,(d-1)*1440+meeting.minute);return {...result,loc:a.loc,activity:a.activity,changed:!!a.redirected,reason:a.id,meeting:a.id}}
  const reaction=storyReaction(id,t,c);if(reaction)return {...result,loc:reaction.loc,activity:reaction.activity,changed:true,reason:reaction.id,storyReaction:reaction.id,dialogue:reaction.dialogue};
  const changes=data.rules.filter(r=>r.npc===id&&m>=r.from&&m<r.to&&Object.values(c.choices).some(x=>x.id===r.choice&&x.at+60<=t));
  changes.sort((a,b)=>Object.values(c.choices).find(x=>x.id===b.choice).at-Object.values(c.choices).find(x=>x.id===a.choice).at);
  if(changes.length){const z=changes[0];result={...result,loc:z.loc,activity:z.activity,changed:true,reason:z.choice}}
  return result;
 }
 function collect(c,t,id,index,via){const m=missions[id],e=m?.sources[index];if(!e||!available(c,t).includes(m))return false;const key=id+':'+index;if(c.evidence[key])return false;if(e.actor?!['actor','archive'].includes(via):via!=='site')return false;c.evidence[key]={at:t,via};return true}
 function solve(c,t,id,answer){const m=missions[id];if(!m||!available(c,t).includes(m)||!m.sources.every((_,i)=>c.evidence[id+':'+i])||answer!==m.answer)return false;c.solved[id]={at:t};return true}
 function choose(c,t,id,choice){const m=missions[id];if(c.outcome||!m||!c.solved[id]||c.choices[id]||!m.choices.some(q=>q[0]===choice))return false;c.choices[id]={id:choice,at:t};return true}
 function tick(c,t){const added=[];for(const e of data.events){const at=(e.day-1)*1440+e.minute;if(at<=t&&!c.events[e.day]){c.events[e.day]=at;added.push(e)}}return added}
 function settleMeetings(c,t,deadAt=()=>null){c.meetings??={};const added=[];for(const e of data.appointments||[]){const at=(e.day-1)*1440+e.minute,end=(e.day-1)*1440+e.until;if(end>t||c.meetings[e.id])continue;const a=meetingVariant(e,c,at),actors=e.actors.filter(id=>{const dead=deadAt(id);return dead==null||dead>at});const row={at,end,loc:a.loc,activity:a.activity,actors,redirected:!!a.redirected,status:actors.length>=2?'realizado':'cancelado',witnessed:!!c.seenMeetings?.[e.id]};c.meetings[e.id]=row;added.push({id:e.id,...row})}return added}
 function witness(c,t,id,near){const e=(data.appointments||[]).find(e=>e.id===id);if(!e||!near)return false;const at=(e.day-1)*1440+e.minute,end=(e.day-1)*1440+e.until;if(t<at||t>=end)return false;c.seenMeetings??={};if(c.seenMeetings[id])return false;c.seenMeetings[id]={at:t,loc:meetingVariant(e,c,at).loc};return true}
 function endings(c,t){if(!c.train||!c.solved.last||day(t)<28||t>=43200||c.outcome)return [];const selected=id=>Object.values(c.choices).some(x=>x.id===id);
  const out=[["shutdown","Desligar fisicamente o emissor"],["horizon","Autorizar a amplificação"]];
  if(c.solved.zero&&selected("test-counterwave"))out.push(["zero","Emitir a Frequência Zero"]);
  if(c.solved.zero&&c.solved.history)out.push(["contact","Estabelecer contato limitado"]);
  if(c.solved.horizon&&selected("secure-evidence"))out.push(["truth","Desligar e divulgar as provas"]);
  if(c.solved.rescue&&selected("rescue-uncle"))out.push(["sacrifice","Manter a contramedida manualmente"]);
  return out;
 }
 function finish(c,t,id){if(!endings(c,t).some(e=>e[0]===id))return false;const selected=x=>Object.values(c.choices).some(q=>q.id===x);c.outcome={id,at:t,uncle:c.uncle||"destino desconhecido",evacuation:c.evacuation||"não confirmada",prepared:{grid:selected("repair-grid"),counterwave:selected("test-counterwave"),evacuation:selected("evacuate"),rescue:selected("rescue-uncle")}};return true}
 function resolveAction(c,t,id){if(c.outcome)return false;const chosen=x=>Object.values(c.choices).some(q=>q.id===x&&q.at<=t);if(id==="rescue"&&c.solved.rescue&&chosen("rescue-uncle")&&!c.uncle){c.uncle="resgatado";return true}if(id==="evacuation"&&c.solved.evacuation&&!c.evacuation&&(chosen("evacuate")||chosen("shelter-in-place"))){c.evacuation=chosen("evacuate")?"retirada organizada":"abrigo reforçado";return true}return false}
 function deadline(c,t){if(t>=43200&&!c.outcome){c.outcome={id:"silence",at:43200,uncle:c.uncle||"destino desconhecido",evacuation:c.evacuation||"não confirmada"};return true}return false}
 return {data,byId,missions,storyReaction,reactionWindow,settleStory,storyEpilogue,phase,day,minute,fresh,normalize,chapter,available,schedule,collect,solve,choose,tick,settleMeetings,witness,meetingVariant,endings,finish,deadline,resolveAction};
}
