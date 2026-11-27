import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const html=read('index.html'), runtime=read('src/campaign/browser.js'), data=JSON.parse(read('content/campaign/valley-v1.json'));
assert.ok(html.includes(runtime.trim()),'embedded world runtime must match source');
const start=html.indexOf('const ART=')+10;
const art=JSON.parse(html.slice(start,html.indexOf(';',start)));
function extract(src,name){
 const start=src.indexOf('function '+name+'(');assert.ok(start>=0,name);
 let i=src.indexOf('{',start),depth=1;
 for(let j=i+1;j<src.length;j++){if(src[j]==='{')depth++;if(src[j]==='}')depth--;if(!depth)return src.slice(start,j+1)}
 throw Error(name);
}
const code=['penetration','nearStatic','solidAt','clearLine'].map(n=>extract(html,n)).concat(['valleyHash','valleyRoad','valleyRail','valleyRehash','valleyIsNew','valleyInstallWorld'].map(n=>extract(runtime,n))).join('\n');
const check=new Function('ART','VALLEY',`
 const PHYS={minX:-.45,maxX:13.45,minY:-.45,maxY:13.45,heroR:.22}, STATIC=ART.colliders.map(c=>c[0]===0?{t:0,x:c[1],y:c[2],hx:c[3],hy:c[4]}:{t:1,x:c[1],y:c[2],r:c[3]}),SHASH=new Map();
 let valleyInstalled=false;const valleyActive=()=>true,valleyBase={cam:ART.world.cam.slice()},sites=[],FZ_ROOMS={buildings:[],layouts:{}},valleyRoom=()=>({}),valleyDestinations=()=>{},valleyActorsCache={};
 const iso=(x,y)=>[ART.world.ox+(x-y)*64,ART.world.oy+(x+y)*32];
 ${code}
 valleyInstallWorld();
 const seen=new Set(['5,5']),q=[[5,5]];
 for(let i=0;i<q.length;i++){const [x,y]=q[i];for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){const nx=x+dx,ny=y+dy,k=nx+','+ny;if(nx<0||nx>=28||ny<0||ny>=14||seen.has(k)||solidAt(nx,ny,.22)||!clearLine({x,y},[nx,ny],.22))continue;seen.add(k);q.push([nx,ny])}}
 return {maxX:PHYS.maxX,reachable:q.length,east:q.filter(p=>p[0]>=14).length,furthest:Math.max(...q.map(p=>p[0])),unreachable:Object.entries(VALLEY.data.locations).filter(([id,p])=>!q.some(([x,y])=>Math.abs(x-p.x)+Math.abs(y-p.y)<=1)).map(([id])=>id)};
`);
const result=check(art,{data});
assert.equal(result.maxX,27.45);
assert.equal(result.furthest,27);
assert.ok(result.east>=150);
assert.deepEqual(result.unreachable,[]);
console.log('Expanded world connectivity:',JSON.stringify(result));
