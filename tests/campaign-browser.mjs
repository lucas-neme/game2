import {chromium} from 'playwright';
import {createServer} from 'node:http';
import {readFile,mkdir} from 'node:fs/promises';
import {resolve,extname,sep} from 'node:path';
import assert from 'node:assert/strict';
const root=resolve('.');
const types={'.html':'text/html; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.json':'application/json','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8'};
const server=createServer(async(req,res)=>{try{const p=resolve(root,'.'+new URL(req.url,'http://localhost').pathname.replace(/^\/$/,'/index.html'));if(!p.startsWith(root+sep))throw Error('path');const b=await readFile(p);res.setHeader('Content-Type',types[extname(p)]||'application/octet-stream');res.end(b)}catch{res.writeHead(404);res.end()}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const browser=await chromium.launch({headless:true});await mkdir('browser-evidence',{recursive:true});
const journal=(page,open)=>page.evaluate(o=>uiJournal(o),open);
// Navigate the actual collision model in small swept steps, then activate the visible contextual action.
const roomGo=async(page,label)=>{
 await page.evaluate(label=>{const R=FZ_ROOMS.layouts[s.room];if(!R)throw Error('not in modular room');const step=.25,start=[FZ_R.x,FZ_R.y],q=[{p:start,prev:-1}],seen=new Set(['0,0']);let end=-1;
 for(let i=0;i<q.length;i++){const {p:[x,y]}=q[i];if(fzRoomTarget(R,{x,y})?.label===label){end=i;break}
 for(const [dx,dy] of [[step,0],[-step,0],[0,step],[0,-step]]){const nx=x+dx,ny=y+dy,k=Math.round((nx-start[0])/step)+','+Math.round((ny-start[1])/step);if(!seen.has(k)&&!fzRoomSolid(R,nx,ny)){seen.add(k);q.push({p:[nx,ny],prev:i})}}}
 if(end<0)throw Error('unreachable '+label);const path=[];for(let i=end;i>0;i=q[i].prev)path.unshift(q[i].p);for(const [x,y] of path)fzRoomMove(R,FZ_R,x-FZ_R.x,y-FZ_R.y);
 if(fzRoomTarget(R,FZ_R)?.label!==label)throw Error('collision prevented approach '+label);
 },label);
 await page.locator('#fzRoomAction').filter({hasText:'E · '+label}).click();
};

try{
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.ico'))errors.push(r.status()+' '+r.url())});
 page.on('dialog',d=>d.accept());
 await page.goto('http://127.0.0.1:'+server.address().port);
 await page.locator('#loading').waitFor({state:'detached',timeout:15000});await page.locator('#valleyStart').click();await page.waitForTimeout(750);
 assert.equal(await page.evaluate(()=>FZ_CAMPAIGN().active),true);
 assert.equal(await page.evaluate(()=>FZ_CAMPAIGN().residents.length),16);
 assert.deepEqual(await page.evaluate(()=>FZ_CAMPAIGN().world),[28,14]);
 // The existing chapter-I browser test verifies clue acquisition; seed that verified state
 // here to isolate the cinematic continuation and expanded campaign.
 await page.evaluate(()=>{s.x=s.px=2;s.y=s.py=6;s.t=1440+197;for(const id of ['safe','warning','rail','witness'])record(id);s.solved.push('train');finish()});
 await page.locator('#cinema').waitFor({state:'visible'});for(let i=0;i<4;i++)await page.locator('#cinemaNext').click();
 assert(await page.evaluate(()=>s.campaign.train&&!s.end),'campaign continues after train');
 await page.evaluate(()=>{advance(5*1440+480-s.t);render()});
 await journal(page,true);await page.locator('#valleyCampaign').getByText('A rota H-17',{exact:true}).waitFor();await journal(page,false);
 // Travel through the physical map using the same route/movement functions as the game.
 await page.evaluate(()=>{const target=VALLEY.data.locations.sawmill,path=planRoute(s.x,s.y,target.x,target.y);if(!path)throw Error('No route');for(const [dx,dy] of path){move(dx,dy);s.px=s.x;s.py=s.y}render()});
 assert(await page.evaluate(()=>s.x>=14),'crossed the original world boundary');
 await page.waitForTimeout(450);await page.screenshot({path:'browser-evidence/campaign-01-expansion.png'});
 await page.keyboard.press('f');await page.locator('#roomart.modular-room').waitFor();
 assert.equal(await page.evaluate(()=>s.room),'sawmill');
 await roomGo(page,'Registro de cargas');
 await page.locator('#dialog').getByRole('button',{name:'Guia de carga',exact:true}).click();
 assert(await page.evaluate(()=>!!s.campaign.evidence['cargo:0']),'physical campaign evidence collected');
 await page.screenshot({path:'browser-evidence/campaign-02-sawmill.png'});
 await page.locator('#leave').click();
 await journal(page,true);await page.screenshot({path:'browser-evidence/campaign-03-journal.png'});await journal(page,false);
 await page.evaluate(()=>valleySave());await page.reload();await page.locator('#loading').waitFor({state:'detached',timeout:15000});
 assert(await page.evaluate(()=>s.campaign.train&&s.x>=14&&!!s.campaign.evidence['cargo:0']),'expanded save and clue survive reload');
 assert.deepEqual(errors,[]);console.log('PASS: campaign browser start, chapter continuation, expanded route, indoor evidence and save reload');
}finally{await browser.close();server.close()}
