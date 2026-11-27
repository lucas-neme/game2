/* CAMPAIGN_RUNTIME:BEGIN */
var VALLEY=createValleyCampaign(VALLEY_DATA);
var valleyInstalled=false,valleyGround=null,valleyBase={sites:sites.slice(),places:ART.place.slice(),lights:ART.lights.slice(),colliders:STATIC.slice(),cam:ART.world.cam.slice(),buildings:FZ_ROOMS.buildings.slice(),roomKeys:new Set(Object.keys(FZ_ROOMS.layouts)),npcKeys:new Set(Object.keys(NPC_SHEET))};
var valleyBaseResidents=residents,valleyBaseWalk=walkable,valleyBaseRender=render,valleyBaseAdvance=advance,valleyBaseInteract=interact,valleyBaseTalk=talkToResident,valleyBaseFinish=finish,valleyBaseRoomAction=fzRoomAction,valleyBaseCinema=$('cinemaNext').onclick;
var valleyActorsCache={key:null,rows:null};
function valleyActive(){return !!s.campaign}
function valleyState(){return s.campaign}
function valleyLocation(id){return VALLEY.data.locations[id]}
function valleyIsNew(p){return p.x>=14}
function valleyHash(x,y,z=0){let n=Math.imul(x+71,374761393)^Math.imul(y+39,668265263)^Math.imul(z+11,1274126177);n=Math.imul(n^(n>>>13),1274126177);return (n^(n>>>16))>>>0}
function valleyRoad(x,y){return y===4||y===7||y===10||[17,21,25].includes(x)}
function valleyRail(x,y){return y===0||y===1&&x>=23}
function valleyRehash(){SHASH.clear();for(const c of STATIC){const ex=c.t?c.r:c.hx,ey=c.t?c.r:c.hy;for(let i=Math.floor(c.x-ex);i<=Math.floor(c.x+ex);i++)for(let j=Math.floor(c.y-ey);j<=Math.floor(c.y+ey);j++){const key=(i+64)*256+j+64;if(!SHASH.has(key))SHASH.set(key,[]);SHASH.get(key).push(c)}}}
function valleyRestoreWorld(){if(!valleyInstalled)return;sites.splice(0,sites.length,...valleyBase.sites);ART.place.splice(0,ART.place.length,...valleyBase.places);ART.lights.splice(0,ART.lights.length,...valleyBase.lights);STATIC.splice(0,STATIC.length,...valleyBase.colliders);FZ_ROOMS.buildings.splice(0,FZ_ROOMS.buildings.length,...valleyBase.buildings);for(const id of Object.keys(FZ_ROOMS.layouts))if(!valleyBase.roomKeys.has(id))delete FZ_ROOMS.layouts[id];ART.world.cam=valleyBase.cam.slice();PHYS.maxX=13.45;valleyRehash();valleyInstalled=false;valleyActorsCache.key=null;valleyGround=null;valleyIndoorCache.clear();valleyDestinations()}
function valleyDestinations(){const el=$('destination');if(!el)return;el.replaceChildren();for(const a of sites){const opt=document.createElement('option');opt.value=a.id;opt.textContent=a.name;el.append(opt)}}
function valleyRoom(id,p){const obj={
 village:[["bed",2,1.5],["wardrobe",6.8,1],["table",3,4],["chair",3,5.2],["desk",7,3,"Caderno dos ferroviários"]],
 sawmill:[["workbench",2,1.3,"Bancada de corte"],["rack",5,1],["crate",7,1.3],["crate",7,3],["desk",2,4,"Registro de cargas"]],
 observatory:[["signal",2,1.2,"Receptor"],["radio",4.5,1.2],["desk",7,2,"Registro astronômico"],["bookcase",1,4],["clock",7,5]],
 substation:[["signal",2,1,"Painel elétrico"],["signal",4,1],["locker",6.8,1],["workbench",2,4,"Bancada de medição"],["crate",7,4]],
 farm:[["kitchen",2,1],["stove",4,1],["fridge",7,1],["table",2,4,"Registro de criação"],["bed",7,4]],
 horizon:[["desk",2,1.3,"Ordem de operação"],["signal",4.5,1.1],["rack",7,1],["safe",7,3.5],["monitor",2,4],["radio",6.8,5.4]],
 bunker:[["locker",2,1],["exam",5,1.5],["monitor",7,1],["desk",2,4,"Prontuário de confinamento"],["signal",7,4]],
 shelter:[["bed",2,1],["bed",5,1],["medicine",7,1],["table",2,4,"Lista de famílias"],["bench",7,4]],
 tunnel:[["rail",2,2],["rail",5.5,2],["signal",7,3.8],["crate",1.5,4],["desk",7,5.5,"Mapa de manutenção"]]
 }[id];return {title:p.name,size:[9,8],floor:p.room,wall:p.room==='wood'?'#8d7862':'#767d74',start:[4.5,7.2],exit:[4.5,7.6],obj:obj||[["desk",2,1.5,"Registro local"],["rack",6.5,1]]}}
function valleyInstallWorld(){if(valleyInstalled||!valleyActive())return;valleyInstalled=true;PHYS.maxX=27.45;ART.world.cam=[valleyBase.cam[0],valleyBase.cam[1],3500,1940];
 for(const [id,p] of Object.entries(VALLEY.data.locations)){if(!sites.some(a=>a.id===id))sites.push({id,name:p.name,x:p.x,y:p.y,type:p.room?'house':'tower',text:p.name+' — consulte as evidências disponíveis.'});if(!valleyIsNew(p))continue;
  const bld=!!p.room;ART.place.push([p.art,p.x,p.y,0,id,bld?1:0]);if(bld){STATIC.push({t:0,x:p.x,y:p.y,hx:.48,hy:.48});FZ_ROOMS.buildings.push([id,p.x,p.y]);FZ_ROOMS.layouts[id]=valleyRoom(id,p);ART.lights.push([p.x,p.y,0,75,'lamp'])}}
 for(let x=14;x<28;x++)for(let y=0;y<14;y++){if(valleyRoad(x,y)||valleyRail(x,y)||Object.values(VALLEY.data.locations).some(p=>Math.hypot(x-p.x,y-p.y)<1.4))continue;const n=valleyHash(x,y)%100;if(n<25){ART.place.push([n<12?29:27,x,y,0,0,0]);STATIC.push({t:1,x,y,r:.19})}else if(n<45)ART.place.push([n<34?43:55,x+.1,y+.12,0,0,0])}
 valleyRehash();valleyDestinations();valleyActorsCache.key=null;
}
function valleyActivate(){if(!s.campaign)s.campaign=VALLEY.fresh();else s.campaign=VALLEY.normalize(s.campaign);valleyInstallWorld();valleyTick();return s.campaign}
walkable=function(x,y){if(!valleyActive()||x<14)return valleyBaseWalk(x,y);return Number.isInteger(x)&&Number.isInteger(y)&&x>=14&&x<28&&y>=0&&y<14&&!solidAt(x,y,PHYS.heroR)};
function valleyNearbyCell(loc,n,used=new Set()){const p=valleyLocation(loc);if(!p)return [5,5];const dirs=[[0,1],[1,0],[-1,0],[0,-1],[1,1],[-1,1],[1,-1],[-1,-1],[0,2],[2,0],[-2,0],[0,-2]],offset=n%dirs.length;
 for(let i=0;i<dirs.length;i++){const d=dirs[(i+offset)%dirs.length],x=p.x+d[0],y=p.y+d[1];if(!used.has(x+','+y)&&walkable(x,y)&&!solidAt(x,y,PHYS.npcR))return [x,y]}
 for(let radius=1;radius<5;radius++)for(let x=Math.max(0,p.x-radius);x<=Math.min(27,p.x+radius);x++)for(let y=Math.max(0,p.y-radius);y<=Math.min(13,p.y+radius);y++)if(!used.has(x+','+y)&&walkable(x,y)&&!solidAt(x,y,PHYS.npcR))return [x,y];return [5,5]}
for(const p of VALLEY.data.npcs){if(valleyBase.npcKeys.has(p.id))continue;NPC_SHEET[p.id]=p.sprite;MORT_NAMES[p.id]=p.name;socialNames[p.id]=p.name;personalStories[p.id]={bio:p.bio,goal:p.bio,routine:[],events:[]}}
residents=function(){if(!valleyActive()||!valleyInstalled)return valleyBaseResidents();
 const c=valleyState(),key=[s.t,c.train,Object.values(c.choices).map(x=>x.id+':'+x.at).join(','),Object.keys(mortState().npcs).filter(isDead).join(','),JSON.stringify(s.fates),JSON.stringify(s.personalCases)].join('|');if(valleyActorsCache.key===key)return valleyActorsCache.rows;
 const old=new Map(valleyBaseResidents().map(p=>[p.id,p])),rows=[],used=new Set();
 for(let i=0;i<VALLEY.data.npcs.length;i++){const n=VALLEY.data.npcs[i];if(isDead(n.id))continue;const a=VALLEY.schedule(n.id,s.t,c);if(!a)continue;
  const legacy=old.get(n.id),personalEvent=legacy&&!c.train&&day()<=5&&(alteredRoutine(n.id)||personalStories[n.id].events.some(e=>s.t>=e.at&&s.t<e.until));if(personalEvent&&!used.has(legacy.x+','+legacy.y)){rows.push({...legacy,loc:null,inside:null});used.add(legacy.x+','+legacy.y);continue}
  const [x,y]=valleyNearbyCell(a.loc,i,used);used.add(x+','+y);rows.push({...legacy,id:n.id,name:n.name,color:'#c7b892',x,y,npc:true,activity:a.activity,loc:a.loc,changed:a.changed,reason:a.reason,meeting:a.meeting,inside:valleyIndoorLocation(a)})}
 valleyActorsCache={key,rows};return rows
};

var valleyIndoorCache=new Map();
function valleyIndoorLocation(a){if(!FZ_ROOMS.layouts[a.loc])return null;
 if(/vigia|ronda|trilha|corta lenha|rastreia|observa as luzes|confere vagões|inspeciona a ferrovia|locomotiva|embarque/i.test(a.activity))return null;
 if(a.loc==='rail'&&a.minute===0)return null;
 return a.loc
}
function valleyIndoorActors(id){if(!valleyInstalled||!valleyActive()||!id)return [];const R=FZ_ROOMS.layouts[id];if(!R)return [];
 const rows=residents().filter(p=>p.inside===id),key=rows.map(p=>p.id).join(','),saved=valleyIndoorCache.get(id);if(saved?.key===key)return saved.rows.map(v=>({...rows.find(p=>p.id===v.id),x:v.x,y:v.y}));
 const placed=[],points=[];
 for(let y=1;y<R.size[1]-1;y+=.7)for(let x=1;x<R.size[0]-1;x+=.7){if(fzRoomSolid(R,x,y,.35)||Math.hypot(x-R.start[0],y-R.start[1])<1.4||(R.portals||[]).some(p=>Math.hypot(x-p[0],y-p[1])<1.0))continue;points.push([x,y])}
 for(const p of rows){const seed=valleyHash(p.id.length,p.name.length);const available=points.filter(([x,y])=>!placed.some(q=>Math.hypot(q.x-x,q.y-y)<.85));if(!available.length)continue;const [x,y]=available[seed%available.length];placed.push({...p,x,y})}
 valleyIndoorCache.set(id,{key,rows:placed});return placed
}
function valleyRoomLine(R,a,b){const d=Math.hypot(a.x-b.x,a.y-b.y);for(let i=.1;i<d-.08;i+=.1)if(fzRoomSolid(R,a.x+(b.x-a.x)*i/d,a.y+(b.y-a.y)*i/d,.03))return false;return true}
var valleyLegacyReach=npcReachable,valleyLegacyNearby=nearbyNpc,valleyLegacyPeople=nearbyPeoplePanel;
npcReachable=function(id){if(!valleyActive())return valleyLegacyReach(id);if(s.end||dangerActive()||isDead(id))return false;
 if(s.room){const a=valleyIndoorActors(s.room).find(p=>p.id===id),R=FZ_ROOMS.layouts[s.room];return !!a&&Math.hypot(FZ_R.x-a.x,FZ_R.y-a.y)<=1.0&&valleyRoomLine(R,FZ_R,a)}
 const p=residents().find(p=>p.id===id);if(!p||p.inside)return false;const v=HAS_DOM?(npcVis[id]||p):p,hx=Number.isFinite(s.px)?s.px:s.x,hy=Number.isFinite(s.py)?s.py:s.y,d=Math.hypot(v.x-hx,v.y-hy);
 if(d>1.35)return false;for(let i=.1;i<d-.04;i+=.1)for(const c of nearStatic(hx+(v.x-hx)*i/d,hy+(v.y-hy)*i/d,.025))if(penetration(hx+(v.x-hx)*i/d,hy+(v.y-hy)*i/d,.025,c))return false;return true
};
nearbyNpc=function(){if(!valleyActive())return valleyLegacyNearby();if(s.room)return null;const p=residents().find(p=>npcReachable(p.id));if(!p)return null;const v=HAS_DOM?(npcVis[p.id]||p):p;return {...p,x:v.x,y:v.y}};
nearbyPeoplePanel=function(){if(!valleyActive())return valleyLegacyPeople();const el=$('nearbyPeople');el.replaceChildren();if(s.end||dangerActive())return;for(const p of residents().filter(p=>npcReachable(p.id)))valleyButton(el,'Conversar com '+p.name,()=>talkToResident(p.id))};
var valleyLegacyBodies=dynamicBodies;dynamicBodies=function(){const bodies=valleyLegacyBodies();if(!valleyActive())return bodies;const hidden=new Set(residents().filter(p=>p.inside).map(p=>npcVis[p.id]));return bodies.filter(v=>!hidden.has(v))};
var valleyLegacyTarget=fzRoomTarget;fzRoomTarget=function(R,p){const base=valleyLegacyTarget(R,p);if(!valleyActive()||!s.room||R!==FZ_ROOMS.layouts[s.room]||p!==FZ_R)return base;
 const people=valleyIndoorActors(s.room).filter(a=>Math.hypot(a.x-p.x,a.y-p.y)<.95&&valleyRoomLine(R,p,a)).sort((a,b)=>Math.hypot(a.x-p.x,a.y-p.y)-Math.hypot(b.x-p.x,b.y-p.y));const a=people[0];if(a&&(!base||Math.hypot(a.x-p.x,a.y-p.y)<.65))return {kind:'npc',id:a.id,x:a.x,y:a.y,label:'Conversar com '+a.name};return base};
var valleyLegacyRoomMove=fzRoomMove;fzRoomMove=function(R,p,dx,dy){if(!valleyActive()||p!==FZ_R)return valleyLegacyRoomMove(R,p,dx,dy);const people=valleyIndoorActors(s.room),n=Math.max(1,Math.ceil(Math.hypot(dx,dy)/.075));for(let i=0;i<n;i++){const x=p.x,y=p.y;valleyLegacyRoomMove(R,p,dx/n,dy/n);if(people.some(a=>Math.hypot(p.x-a.x,p.y-a.y)<.44&&Math.hypot(p.x-a.x,p.y-a.y)<Math.hypot(x-a.x,y-a.y))){p.x=x;p.y=y}}};
function valleyDrawIndoorActor(k,a,isoR,sc,t){const [X,Y]=isoR(a.x,a.y),key=NPC_SHEET[a.id],D=typeof V5!=='undefined'&&V5[key];
 k.save();k.fillStyle='rgba(12,9,8,.28)';k.beginPath();k.ellipse(X,Y,9*sc,4*sc,0,0,Math.PI*2);k.fill();
 if(D){const im=v5img(key),A=D.anims['idle:south']||Object.values(D.anims)[0];if(A&&ready(im)){const hs=60*sc/D.ref_h,frame=Math.floor(t*2)%A.frames;k.drawImage(im,frame*D.fw,A.row*D.fh,D.fw,D.fh,X-D.ax*hs,Y-D.ay*hs,D.fw*hs,D.fh*hs)}}else{const f=charFrame(key,'idle','se',t),im=CHAR_IMG[key];if(f&&ready(im)){const d=f.ch,hs=60*sc/Math.max(1,d.fh-6);k.drawImage(im,f.col*d.fw,f.row*d.fh,d.fw,d.fh,X-d.ax*hs,Y-d.ay*hs,d.fw*hs,d.fh*hs)}}
 if(Math.hypot(a.x-FZ_R.x,a.y-FZ_R.y)<2){k.font=Math.max(10,11*sc)+'px Georgia';k.textAlign='center';k.fillStyle='#f5e3bb';k.fillText(a.name,X,Y-68*sc)}k.restore()
}

function valleySourceKey(m,i){return 'valley_'+m.id+'_'+i}
for(const m of VALLEY.data.missions)for(let i=0;i<m.sources.length;i++)notes[valleySourceKey(m,i)]=m.sources[i].label+': '+m.sources[i].truth;
function valleyNear(id){const p=valleyLocation(id);if(!p)return false;const x=Number.isFinite(s.px)?s.px:s.x,y=Number.isFinite(s.py)?s.py:s.y;if(Math.hypot(x-p.x,y-p.y)>1.55)return false;
 const tx=Math.max(p.x-.48,Math.min(x,p.x+.48)),ty=Math.max(p.y-.48,Math.min(y,p.y+.48)),d=Math.hypot(tx-x,ty-y);for(let i=.10;i<d-.03;i+=.10)for(const c of nearStatic(x+(tx-x)*i/d,y+(ty-y)*i/d,.025)){if(c.t===0&&c.x===p.x&&c.y===p.y)continue;if(penetration(x+(tx-x)*i/d,y+(ty-y)*i/d,.025,c))return false}return true}
function valleyArchiveAllowed(e,m){return !!e.actor&&(isDead(e.actor)||day()>=VALLEY.data.chapters[m.chapter-1].days[0]+2)}
function valleyCollect(m,i,via,loc){if(!valleyActive()||s.end||dangerActive())return false;const e=m.sources[i];
 if(via==='actor'&&(!e.actor||!npcReachable(e.actor)))return false;
 if(via==='archive'&&(!valleyArchiveAllowed(e,m)||!(s.room===loc||valleyNear(loc))))return false;
 if(via==='site'&&(e.actor||loc!==e.place||(valleyIsNew(valleyLocation(loc))&&FZ_ROOMS.layouts[loc]?s.room!==loc:!(s.room===loc||valleyNear(loc)))))return false;
 if(!VALLEY.collect(valleyState(),s.t,m.id,i,via))return false;record(valleySourceKey(m,i));advance(12);say(e.truth+(via==='archive'?' (Cópia preservada no registro local.)':''));render();valleySave();return true}
function valleyButton(el,label,fn){const b=document.createElement('button');b.textContent=label;b.onclick=fn;el.append(b);return b}
function valleySitePanel(id,inside=false){if(!valleyActive()||s.end||dangerActive())return false;const c=valleyState(),p=valleyLocation(id);if(!p)return false;const el=$('dialog');const entries=[];
 for(const m of VALLEY.available(c,s.t))for(let i=0;i<m.sources.length;i++){const e=m.sources[i];if(c.evidence[m.id+':'+i]||e.place!==id)continue;if(!e.actor&&(!valleyIsNew(p)||!FZ_ROOMS.layouts[id]||inside))entries.push([e.label,()=>valleyCollect(m,i,'site',id)]);else if(e.actor&&valleyArchiveAllowed(e,m))entries.push(['Consultar cópia: '+e.label,()=>valleyCollect(m,i,'archive',id)])}
 if(c.solved.rescue&&id==='bunker'&&inside&&!c.uncle&&c.choices.rescue?.id==='rescue-uncle')entries.push(['Retirar o tio pela saída de serviço',()=>{if(s.room!==id)return;if(VALLEY.resolveAction(c,s.t,'rescue')){advance(90);say('Seu tio está vivo. Sérgio deixou o caminho de manutenção livre.');render();valleySave()}}]);
 if(c.solved.evacuation&&['shelter','village','rail'].includes(id)&&!c.evacuation&&c.choices.evacuation)entries.push(['Confirmar a organização dos moradores',()=>{if(!(s.room===id||valleyNear(id)))return;if(VALLEY.resolveAction(c,s.t,'evacuation')){advance(90);say('A lista de famílias foi conferida. '+c.evacuation+'.');render();valleySave()}}]);
 if(id==='horizon'&&inside&&VALLEY.endings(c,s.t).length)entries.push(['Operar o emissor',()=>valleyFinalPanel()]);
 if(!entries.length&&!valleyIsNew(p))return false;
 if(!inside)el.replaceChildren();if(!inside&&FZ_ROOMS.layouts[id])valleyButton(el,'Entrar — '+p.name,()=>{if(valleyNear(id))fzEnterRoom(id)});
 for(const [label,fn] of entries)valleyButton(el,label,fn);
 if(!inside)say(p.name+(entries.length?' — há indícios disponíveis.':' — explore o local; ainda não há novas evidências.'));
 return true
}
talkToResident=function(id){if(!valleyActive())return valleyBaseTalk(id);if(s.end||!npcReachable(id))return;const n=VALLEY.byId[id];if(!n)return valleyBaseTalk(id);if(valleyBase.npcKeys.has(id))valleyBaseTalk(id);else{stopRoute();if(!s.npcKnown.includes(id)){s.npcKnown.push(id);advance(5)}$('dialog').replaceChildren();say(n.name+': '+n.bio);render()}
 const el=$('dialog'),c=valleyState(),a=VALLEY.schedule(id,s.t,c);if(a?.meeting&&VALLEY.witness(c,s.t,a.meeting,npcReachable(id))){s.events.push('Você acompanhou um encontro: '+a.activity+' — '+valleyLocation(a.loc).name+'.');valleySave()}if(a?.storyReaction&&a.dialogue)valleyButton(el,'Conversar sobre as consequências',()=>{if(!npcReachable(id))return;const current=VALLEY.schedule(id,s.t,c);if(current?.storyReaction!==a.storyReaction)return;c.storySeen??={};if(!c.storySeen[a.storyReaction]){c.storySeen[a.storyReaction]={at:s.t,npc:id};s.events.push(a.dialogue);valleySave()}say(a.dialogue);render()});for(const m of VALLEY.available(c,s.t))m.sources.forEach((e,i)=>{if(e.actor===id&&!c.evidence[m.id+':'+i])valleyButton(el,'Perguntar: '+e.label,()=>valleyCollect(m,i,'actor',e.place))});
 if(!valleyBase.npcKeys.has(id))valleyButton(el,'Conhecer sua rotina',()=>{if(!npcReachable(id))return;const a=VALLEY.schedule(id,s.t,c);say(n.name+' — '+a.activity+'. '+n.bio);if(!s.npcMeetings.includes('bio:'+id))s.npcMeetings.push('bio:'+id);render()});
};
interact=function(){if(!valleyActive()||s.room||s.end||dangerActive())return valleyBaseInteract();const near=nearbyNpc();if(near&&VALLEY.byId[near.id]&&(!valleyBase.npcKeys.has(near.id)||valleyState().train)){talkToResident(near.id);return}
 const loc=Object.entries(VALLEY.data.locations).filter(([id])=>valleyNear(id)).sort((a,b)=>Math.hypot(a[1].x-s.x,a[1].y-s.y)-Math.hypot(b[1].x-s.x,b[1].y-s.y))[0];
 if(loc&&(valleyIsNew(loc[1])||valleyState().train)&&valleySitePanel(loc[0]))return;return valleyBaseInteract()};
fzRoomAction=function(){const id=s.room,R=FZ_ROOMS.layouts[id],t=R&&fzRoomTarget(R,FZ_R);if(valleyActive()&&t?.kind==='npc'&&!s.end&&!dangerActive()&&$('pzModal').hidden&&$('invModal').hidden){talkToResident(t.id);return true}const result=valleyBaseRoomAction();if(valleyActive()&&id===s.room&&t?.kind==='obj'&&(!$('puzzle').children.length)&&$('pzModal').hidden)valleySitePanel(id,true);return result};
function valleyTick(){if(!valleyActive())return;const c=valleyState();for(const e of VALLEY.tick(c,s.t))s.events.push('Dia '+e.day+' — '+e.text);for(const e of VALLEY.settleMeetings(c,s.t,id=>mortState().npcs[id]?.t??null))s.events.push('Encontro '+e.status+' em '+valleyLocation(e.loc).name+': '+e.activity+(e.redirected?' (local alterado)':'')+'.');for(const e of VALLEY.settleStory(c,s.t,id=>mortState().npcs[id]?.t??null))s.events.push(VALLEY.byId[e.npc].name+' — '+e.status+': '+e.result);if(VALLEY.deadline(c,s.t))s.end='Silêncio absoluto — o prazo se encerrou. O Vale perdeu contato com o mundo.'}
var valleySavedAt=-1;advance=function(n){valleyBaseAdvance(n);valleyTick();if(valleyActive()&&(s.end||s.t-valleySavedAt>=30||s.t<valleySavedAt))valleySave()};
function valleySave(){if(!valleyActive())return;try{localStorage.setItem('fz-demo-v2',JSON.stringify(s));valleySavedAt=s.t}catch{}}
function valleyContinue(){if(!s.end?.includes('FIM DO CAPÍTULO I'))return false;valleyActivate();s.campaign.train=true;s.end=null;s.cinemaDismissed=true;$('cinema').hidden=true;$('world').hidden=false;stopRoute();say('O trem desapareceu, mas a investigação continua. Consulte o diário e siga a remessa H-17.');render();valleySave();return true}
finish=function(){if(!valleyActive()||!valleyState().train){return valleyBaseFinish()}if(s.room==='horizon'&&!s.end&&!dangerActive())return valleyFinalPanel();say('A decisão final acontece no Complexo Horizonte, a partir do dia 28. Consulte as missões no diário.');render()};
function valleyFinalPanel(){const c=valleyState();if(!c||s.end||dangerActive()||s.room!=='horizon')return;const el=$('dialog');el.replaceChildren();const choices=VALLEY.endings(c,s.t);if(!choices.length){say('Ainda não há condições para operar o emissor.');return}say('O painel está pronto. Nenhuma das inteligências revelou completamente sua intenção. Esta decisão é definitiva.');
 for(const [id,label] of choices)valleyButton(el,label,()=>{if(s.room!=='horizon'||s.end||!confirm('Confirmar a decisão final?'))return;if(!VALLEY.finish(c,s.t,id))return;const texts={shutdown:'O emissor foi desligado. O sinal permanece sem amplificação.',horizon:'A amplificação foi autorizada. Uma nova consciência começa a se formar.',zero:'A componente sincronizante foi interrompida pela onda de oposição.',contact:'O contato limitado foi estabelecido. A intenção da voz ainda é desconhecida.',truth:'O emissor foi desligado e as provas foram enviadas para fora do Vale.',sacrifice:'A contramedida foi mantida manualmente. Alguém precisou ficar para trás.'};s.end=texts[id]+' Tio: '+c.outcome.uncle+'. Moradores: '+c.outcome.evacuation+'.';if(s.room)leaveRoom();say(s.end);render();valleySave()})
}
var valleyJournalKey=null;function valleyJournal(){if(!HAS_DOM)return;const el=$('valleyCampaign');if(!el)return;const key=JSON.stringify([valleyState(),s.end,s.cinemaDismissed,Math.floor(s.t/30),s.npcKnown,Object.keys(mortState().npcs)]);if(key===valleyJournalKey)return;valleyJournalKey=key;el.replaceChildren();if(!valleyActive()){el.hidden=true;if(s.end?.includes('FIM DO CAPÍTULO I')&&s.cinemaDismissed){el.hidden=false;valleyButton(el,'Continuar campanha de 30 dias',valleyContinue)}return}el.hidden=false;
 const c=valleyState(),ch=VALLEY.chapter(c,s.t),phase=VALLEY.phase(day()),title=document.createElement('h3');title.textContent='Campanha · Capítulo '+ch+' — '+VALLEY.data.chapters[ch-1].title;el.append(title);
 const desc=document.createElement('p');desc.textContent='Dia '+day()+'/30 · '+Object.keys(c.solved).length+'/'+VALLEY.data.missions.length+' casos adicionais resolvidos.';el.append(desc);
 if(c.outcome){const p=document.createElement('p');p.textContent=s.end||c.outcome.id;el.append(p);for(const e of VALLEY.storyEpilogue(c)){const row=document.createElement('p');row.textContent=e.name+' — '+e.result+(e.witnessed?' (você presenciou a preparação)':'');el.append(row)}return}
 if(!c.train){const p=document.createElement('p');p.textContent='Investigue o trem para abrir a campanha. As novas regiões já podem ser visitadas.';el.append(p);if(s.end?.includes('FIM DO CAPÍTULO I')&&s.cinemaDismissed)valleyButton(el,'Continuar após o trem',valleyContinue);return}
 const available=VALLEY.available(c,s.t);
 for(const m of available){const card=document.createElement('section'),t=document.createElement('strong');t.textContent=m.title;card.append(t);const p=document.createElement('p');p.textContent=m.summary;card.append(p);m.sources.forEach((e,i)=>{const v=c.evidence[m.id+':'+i],row=document.createElement('p');row.textContent=(v?'✓ ':'○ ')+e.label+' — '+(e.actor&&!v?VALLEY.byId[e.actor].name+(valleyArchiveAllowed(e,m)?' ou registro em '+valleyLocation(e.place).name:''):valleyLocation(e.place).name)+(v?' · '+v.via:'');card.append(row)});if(m.sources.every((_,i)=>c.evidence[m.id+':'+i])){const q=document.createElement('p');q.textContent=m.question;card.append(q);m.options.forEach((o,i)=>valleyButton(card,o,()=>{if(s.end||dangerActive()||!VALLEY.solve(c,s.t,m.id,i)){say('A conclusão não corresponde às evidências.');return}say('Caso concluído: '+m.title);render();valleySave()}))}el.append(card)}
 for(const m of VALLEY.data.missions){if(!c.solved[m.id]||c.choices[m.id]||!m.choices.length)continue;const card=document.createElement('section'),p=document.createElement('p');p.textContent='Decisão: '+m.title+' (altera rotinas futuras)';card.append(p);for(const [id,label] of m.choices)valleyButton(card,label,()=>{if(s.end||dangerActive()||!VALLEY.choose(c,s.t,m.id,id))return;valleyActorsCache.key=null;advance(15);say('Decisão registrada. Os moradores reagirão a partir da próxima hora.');render();valleySave()});el.append(card)}
 if(!available.length&&phase<5&&!s.end){const target=VALLEY.data.chapters[phase].days[0];valleyButton(el,'Aguardar até o dia '+target,()=>{if(s.room||s.end||dangerActive())return;advance(Math.max(0,(target-1)*1440+480-s.t));render()})}
 if(c.solved.last&&day()>=28){const p=document.createElement('p');p.textContent='Entre no Complexo Horizonte e examine o painel para decidir o destino do sinal.';el.append(p)}
 const calendar=document.createElement('details'),sum=document.createElement('summary');sum.textContent='Agenda prevista dos moradores conhecidos';calendar.append(sum);
 for(const n of VALLEY.data.npcs){if(!s.npcKnown.includes(n.id)||isDead(n.id))continue;const p=document.createElement('p'),a=VALLEY.schedule(n.id,s.t,c);p.textContent=n.name+' · '+valleyLocation(a.loc).name+' · '+a.activity+(a.changed?' (rota alterada)':'');calendar.append(p);const next=n.days[Math.min(29,day()-1)].slots.find(q=>q.minute>VALLEY.minute(s.t));if(next){const hint=document.createElement('small');hint.textContent='Próximo compromisso previsto: '+String(Math.floor(next.minute/60)).padStart(2,'0')+':'+String(next.minute%60).padStart(2,'0')+' — '+valleyLocation(next.loc).name;calendar.append(hint)}}el.append(calendar)
}
render=function(){if(valleyActive()){valleyInstallWorld();valleyTick()}else if(valleyInstalled)valleyRestoreWorld();valleyBaseRender();if(valleyActive()&&valleyState().train&&!s.end){const ch=VALLEY.chapter(valleyState(),s.t),m=VALLEY.available(valleyState(),s.t)[0];$('objective').textContent=s.room?'Explore o interior e examine os objetos.':m?m.title+' — consulte as evidências no diário (J).':valleyState().solved.last?'Vá ao Complexo Horizonte.':'Acompanhe o calendário e o diário.';$('theory').textContent='Capítulo '+ch+' • '+VALLEY.data.chapters[ch-1].title}valleyJournal()};
function campaignDrawTerrain(ctx){if(!valleyInstalled||!HAS_DOM||!ctx?.drawImage)return;if(!valleyGround){const min=iso(14,13),max=iso(27,0),top=iso(14,0),bottom=iso(27,13),x0=min[0]-64,y0=top[1]-32,w=max[0]-min[0]+128,h=bottom[1]-top[1]+64,cv=document.createElement('canvas');cv.width=w;cv.height=h;const k=cv.getContext('2d');k.imageSmoothingEnabled=false;
 const P=(x,y)=>{const a=iso(x,y);return[a[0]-x0,a[1]-y0]};
 for(let x=14;x<28;x++)for(let y=0;y<14;y++){const [X,Y]=P(x,y),road=valleyRoad(x,y),rail=valleyRail(x,y),n=valleyHash(x,y);k.save();k.beginPath();k.moveTo(X,Y-32);k.lineTo(X+64,Y);k.lineTo(X,Y+32);k.lineTo(X-64,Y);k.closePath();k.clip();k.fillStyle=rail?'#635f54':road?'#98816a':['#677a38','#71833d','#65753a','#778640'][n%4];k.fillRect(X-64,Y-32,128,64);
 for(let i=0;i<85;i++){const r=valleyHash(x,y,i),px=X-64+r%128,py=Y-32+(r>>>8)%64;k.fillStyle=rail?'#777161':road?['#ac967b','#7c6b59','#bdab8c'][r%3]:['#526832','#879443','#667936','#a0a45b'][r%4];k.globalAlpha=.35+(r%3)*.12;k.fillRect(px,py,2+(r>>>16)%7,2+(r>>>22)%4)}k.restore();
 if(rail){k.save();k.strokeStyle='#403a31';k.lineWidth=5;for(let i=-2;i<=2;i++){k.beginPath();k.moveTo(X+i*20-13,Y+i*10+7);k.lineTo(X+i*20+13,Y+i*10-7);k.stroke()}for(const o of [-7,7]){k.strokeStyle='#a2a09a';k.lineWidth=2;k.beginPath();k.moveTo(X-64,Y-32+o);k.lineTo(X+64,Y+32+o);k.stroke()}k.restore()}}
 valleyGround={cv,x:x0,y:y0,w,h}}
 const z=valleyGround;if(ctx===g){const x=Math.max(z.x,Math.floor(cam.x-c.width/(2*cam.z))-4),y=Math.max(z.y,Math.floor(cam.y-c.height/(2*cam.z))-4),X=Math.min(z.x+z.w,Math.ceil(cam.x+c.width/(2*cam.z))+4),Y=Math.min(z.y+z.h,Math.ceil(cam.y+c.height/(2*cam.z))+4);if(X>x&&Y>y)ctx.drawImage(z.cv,x-z.x,y-z.y,X-x,Y-y,x,y,X-x,Y-y)}
}
if(HAS_DOM){
 const panel=document.createElement('section');panel.id='valleyCampaign';panel.className='valley-campaign';$('journal').prepend(panel);
 const start=document.createElement('button');start.id='valleyStart';start.textContent='Nova campanha completa (30 dias)';start.onclick=()=>{if(!confirm('Iniciar uma nova campanha? O progresso atual será substituído.'))return;uiStart(true);valleyActivate();render();valleySave()};$('startGame').parentElement.append(start);
 $('cinemaNext').onclick=()=>{const done=s.endingScene>=3&&s.end?.includes('FIM DO CAPÍTULO I');valleyBaseCinema();if(done&&valleyActive())valleyContinue();else if(done){const b=document.createElement('button');b.textContent='Continuar campanha de 30 dias';b.onclick=valleyContinue;$('dialog').append(b)}};
 $('act').onclick=()=>interact();$('final').onclick=()=>finish();
 const oldReset=$('reset').onclick;$('reset').onclick=()=>{oldReset();if(!valleyActive())valleyRestoreWorld()};
 if(valleyActive()){valleyActivate();if(s.end?.includes('FIM DO CAPÍTULO I')&&s.cinemaDismissed)valleyContinue();else render()}
 window.FZ_CAMPAIGN=()=>({active:valleyActive(),chapter:valleyActive()?VALLEY.chapter(valleyState(),s.t):1,day:day(),world:valleyActive()?[28,14]:[14,14],residents:residents().map(p=>({id:p.id,name:p.name,x:p.x,y:p.y,activity:p.activity,location:p.loc,changed:p.changed,inside:p.inside})),state:valleyActive()?JSON.parse(JSON.stringify(valleyState())):null});window.FZ_AGENDA=(id,d)=>{const n=VALLEY.byId[id];if(!n||d<1||d>30)return null;return {name:n.name,day:d,slots:n.days[d-1].slots.map(q=>({...q,location:valleyLocation(q.loc).name})),meetings:VALLEY.data.appointments.filter(e=>e.day===d&&e.actors.includes(id))}};
}
/* CAMPAIGN_RUNTIME:END */
