/* Deterministic campaign state; no DOM or wall clock dependencies. */
function createValleyCampaign(data){
 const byId=Object.fromEntries(data.npcs.map(n=>[n.id,n]));
 const missions=Object.fromEntries(data.missions.map(m=>[m.id,m]));
 const phase=d=>data.chapters.find(c=>d>=c.days[0]&&d<=c.days[1])?.id||5;
 const day=t=>Math.max(1,Math.min(30,1+Math.floor(t/1440)));
 const minute=t=>((Math.floor(t)%1440)+1440)%1440;
 const fresh=()=>({version:1,train:false,solved:{},evidence:{},choices:{},events:{},outcome:null,uncle:null,evacuation:null});
 const normalize=c=>Object.assign(fresh(),c||{});
 function chapter(c,t){if(!c.train)return 1;const cap=phase(day(t));for(let ch=2;ch<=5;ch++){if(ch>cap)return cap;if(data.missions.some(m=>m.chapter===ch&&!c.solved[m.id]))return ch}return 5}
 function available(c,t){return c.train&&!c.outcome?data.missions.filter(m=>m.chapter<=chapter(c,t)&&m.chapter<=phase(day(t))&&!c.solved[m.id]):[]}
 function schedule(id,t,c,dead=false){if(dead||!byId[id])return null;const n=byId[id],d=day(t),m=minute(t),row=n.days[d-1],base=row.slots.findLast(x=>x.minute<=m)||row.slots[0];let result={...base,day:d,id,name:n.name,sprite:n.sprite,changed:false};
  const changes=data.rules.filter(r=>r.npc===id&&m>=r.from&&m<r.to&&Object.values(c.choices).some(x=>x.id===r.choice&&x.at+60<=t));
  changes.sort((a,b)=>Object.values(c.choices).find(x=>x.id===b.choice).at-Object.values(c.choices).find(x=>x.id===a.choice).at);
  if(changes.length){const z=changes[0];result={...result,loc:z.loc,activity:z.activity,changed:true,reason:z.choice}}
  return result;
 }
 function collect(c,t,id,index,via){const m=missions[id],e=m?.sources[index];if(!e||!available(c,t).includes(m))return false;const key=id+':'+index;if(c.evidence[key])return false;if(e.actor?!['actor','archive'].includes(via):via!=='site')return false;c.evidence[key]={at:t,via};return true}
 function solve(c,t,id,answer){const m=missions[id];if(!m||!available(c,t).includes(m)||!m.sources.every((_,i)=>c.evidence[id+':'+i])||answer!==m.answer)return false;c.solved[id]={at:t};return true}
 function choose(c,t,id,choice){const m=missions[id];if(c.outcome||!m||!c.solved[id]||c.choices[id]||!m.choices.some(q=>q[0]===choice))return false;c.choices[id]={id:choice,at:t};return true}
 function tick(c,t){const added=[];for(const e of data.events){const at=(e.day-1)*1440+e.minute;if(at<=t&&!c.events[e.day]){c.events[e.day]=at;added.push(e)}}return added}
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
 return {data,byId,missions,phase,day,minute,fresh,normalize,chapter,available,schedule,collect,solve,choose,tick,endings,finish,deadline,resolveAction};
}
