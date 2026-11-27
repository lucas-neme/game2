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
try{const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.ico'))errors.push(r.status()+' '+r.url())});
 await page.goto('http://127.0.0.1:'+server.address().port);await page.locator('#world').waitFor();await page.locator('#loading').waitFor({state:'detached',timeout:15000});
 await page.screenshot({path:'browser-evidence/00-title.png'});await page.locator('#startGame').click();await page.waitForTimeout(700);await page.screenshot({path:'browser-evidence/01-town.png'});
 await page.evaluate(()=>{move(-1,0);move(-1,0);move(0,-1);interact()});await page.locator('#fzRoomAction').waitFor();const before=await page.evaluate(()=>[FZ_R.x,FZ_R.y]);await page.keyboard.down('w');await page.waitForTimeout(250);await page.keyboard.up('w');assert(await page.evaluate(p=>Math.hypot(FZ_R.x-p[0],FZ_R.y-p[1])>.05,before),'indoor keyboard movement');await roomGo(page,'Fita cassete');await roomGo(page,'Cofre de aço');for(const n of ['0','3','1','7','Abrir'])await page.locator('#puzzle').getByRole('button',{name:n,exact:true}).click();await page.screenshot({path:'browser-evidence/02-study.png'});await page.locator('#leave').click();
 await page.evaluate(()=>{move(-1,0);move(0,1);move(0,1);interact()});await roomGo(page,'Relógio parado');await roomGo(page,'Manifesto rasgado');await roomGo(page,'Pátio ferroviário');await roomGo(page,'Trilhos');await page.screenshot({path:'browser-evidence/03-yard.png'});await roomGo(page,'Depósito de carga');await page.screenshot({path:'browser-evidence/03-depot.png'});await roomGo(page,'Voltar');await roomGo(page,'Voltar');await roomGo(page,'Armário de sinalização');const d=page.locator('.dialrow button');await d.nth(0).click();await d.nth(0).click();await d.nth(1).click();await page.getByRole('button',{name:'Testar mecanismo'}).click();await page.screenshot({path:'browser-evidence/03-station.png'});await page.locator('#leave').click();
 await journal(page,true);await page.locator('#freq').evaluate(e=>{e.value='103.7';e.dispatchEvent(new Event('input',{bubbles:true}))});await page.locator('#tune').click();await page.locator('#signalAnswer').fill('13');await page.locator('#signalCheck').click();await page.getByRole('button',{name:'A ferrovia pode estar ativa clandestinamente.',exact:true}).click();await page.screenshot({path:'browser-evidence/03b-journal.png'});await journal(page,false);
 await page.locator('#night').click();await journal(page,true);await page.locator('#final').click();await journal(page,false);await page.locator('#cinema').waitFor();await page.screenshot({path:'browser-evidence/04-finale.png'});assert.equal(errors.length,0,errors.join('\n'));console.log('PASS: real Chromium full demo mechanical route');
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});await mobile.goto('http://127.0.0.1:'+server.address().port);await mobile.locator('#loading').waitFor({state:'detached',timeout:15000});await mobile.locator('#startGame').tap();await mobile.waitForTimeout(700);await mobile.screenshot({path:'browser-evidence/05-mobile.png'});assert(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));console.log('PASS: mobile horizontal layout');
}finally{await browser.close();server.close()}
