import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const html=read('index.html'),runtime=read('src/campaign/browser.js');
assert.ok(html.includes(runtime.trim()),'campaign source and embedded runtime must match');
function fn(src,name){const i=src.indexOf('function '+name+'(');assert.ok(i>=0,name);let d=0,j=src.indexOf('{',i);for(let k=j;k<src.length;k++){if(src[k]==='{')d++;if(src[k]==='}')d--;if(!d)return src.slice(i,k+1)}throw Error(name)}
const geometry=new Function(['valleyRoad','valleyRail','valleyTerrainEdges'].map(n=>fn(runtime,n)).join('\n')+';return {valleyRoad,valleyRail,valleyTerrainEdges}')();
for(const predicate of [geometry.valleyRoad,geometry.valleyRail])for(let x=14;x<28;x++)for(let y=0;y<14;y++)if(predicate(x,y))for(const [dx,dy] of geometry.valleyTerrainEdges(x,y,predicate)){
 if(x+dx<14)continue;
 assert.ok(geometry.valleyTerrainEdges(x+dx,y+dy,predicate).some(([a,b])=>a===-dx&&b===-dy),'shared edge must be reciprocal')
}
assert.ok(geometry.valleyTerrainEdges(14,6,geometry.valleyRoad).some(([dx,dy])=>dx===-1&&dy===0));
const timing=html.match(/const FZ_FIGHT_TIMING=[^;]+;/)[0];
const combat=new Function(timing+fn(html,'fzFightEvent')+fn(html,'fzFightPhase')+';return {fzFightEvent,fzFightPhase}')();
let q={turn:0,integrity:5,focus:4,stamina:4},e=combat.fzFightEvent(null,q,0);
e=combat.fzFightEvent(e,{...q,turn:1,stamina:3,lastAction:'pulse'},1);
assert.equal(e.hit,false,'spending stamina is not damage');
e=combat.fzFightEvent(e,{...q,turn:2,integrity:4,lastAction:'pulse'},2);
assert.equal(e.hit,true);assert.equal(combat.fzFightPhase(e,2.34).impact,true);
assert.equal(combat.fzFightPhase(e,3).active,false);
e=combat.fzFightEvent(e,{...q,turn:3,integrity:4,focus:3,lastAction:'guard'},3);
assert.equal(e.hurt,true);assert.equal(e.hit,false);
console.log('Terrain connectivity and combat presentation contracts passed');
