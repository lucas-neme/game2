// V5 harmonized creatures in real Chromium: every integrated species and action draws from the V5 atlas, the echo keeps
// the V4 on-screen height, and a contact sheet of the real renderer is saved. BASE=... node tests/creatures-v5-chromium.mjs
import assert from 'node:assert/strict';import {chromium} from 'playwright';import {mkdir,writeFile} from 'node:fs/promises';
const BASE=process.env.BASE||'http://127.0.0.1:8092/game2/';const OUT=process.env.OUT||'browser-evidence/creatures';
await mkdir(OUT,{recursive:true});const browser=await chromium.launch({args:process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[]});
const page=await browser.newPage();const errs=[];page.on('pageerror',e=>errs.push(String(e)));
await page.goto(BASE,{waitUntil:'networkidle'});
const res=await page.evaluate(async()=>{const ix=V4.atlases.findIndex(a=>/creatures\/v5\/atlas/.test(a));const im=v4img(ix);
 await new Promise(r=>{const w=()=>ready(im)?r():setTimeout(w,50);w()});
 const species=Object.keys(V4.creatures).filter(c=>V4.creatures[c].idle?.[0]?.[0]===ix);const acts=['idle','movimento','ataque','dano','dissipacao'];
 const cv=document.createElement('canvas');cv.width=acts.length*110;cv.height=species.length*110;const k=cv.getContext('2d');k.fillStyle='#4f7a3a';k.fillRect(0,0,cv.width,cv.height);
 const drawn={};species.forEach((c,y)=>acts.forEach((a,x)=>{drawCreature(k,c,a,.3,x*110+55,y*110+100,2);drawn[c+':'+a]=!!V4.creatures[c][a]?.length}));
 const e=V4.creatures.eco_humanoide.idle[0];return {ix,file:V4.atlases[ix],species,drawn,echoH:e[4]*e[5],png:cv.toDataURL('image/png')}});
assert(res.ix>0&&/creatures\/v5\/atlas\.png/.test(res.file),'V5 atlas '+res.file);
assert(res.species.includes('eco_humanoide')&&res.species.includes('anomalia_esferica'),'encounter/arena species use V5 '+res.species);
assert(Object.values(res.drawn).every(Boolean),'all actions present');
assert(Math.abs(res.echoH-36)<1.5,'echo keeps the V4 on-screen height: '+res.echoH);
await writeFile(OUT+'/creatures-v5.png',Buffer.from(res.png.split(',')[1],'base64'));
console.log('PASS: V5 creatures from',res.file,res.species.join(','));
assert.equal(errs.length,0,errs.join('\n'));await browser.close();console.log('ALL CREATURE CHECKS PASSED');
