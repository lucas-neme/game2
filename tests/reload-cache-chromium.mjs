// Returning player: the second and third loads come with every image already in the browser cache (immutable
// v/<hash>/ URLs in production), so the world can draw during the initial script run. No page error may happen and the
// game must start. Usage: BASE=... node tests/reload-cache-chromium.mjs
import assert from 'node:assert/strict';import {chromium} from 'playwright';
const BASE=process.env.BASE||'http://127.0.0.1:8092/game2/';
const browser=await chromium.launch({args:process.env.HOST_MAP?['--host-resolver-rules=MAP '+process.env.HOST_MAP]:[]});
const page=await browser.newPage();const errs=[];page.on('pageerror',e=>errs.push(String(e)));
for(let i=0;i<3;i++){
 if(i===0)await page.goto(BASE,{waitUntil:'networkidle',timeout:120000});else await page.reload({waitUntil:'networkidle',timeout:120000});
 await page.locator('#loading').waitFor({state:'detached',timeout:60000}).catch(()=>{});
 await page.locator('#startGame').click();await page.waitForFunction(()=>UI.started,null,{timeout:20000});
 await page.waitForTimeout(800);
 assert.equal(errs.length,0,'load '+(i+1)+': '+errs.join(' | '));console.log('PASS: load',i+1,'starts without page errors')}
await browser.close();console.log('ALL RELOAD CHECKS PASSED');
