import {readFileSync,writeFileSync} from 'node:fs';
const url=p=>new URL('../'+p,import.meta.url);
const html=readFileSync(url('index.html'),'utf8'),data=JSON.stringify(JSON.parse(readFileSync(url('content/campaign/valley-v1.json'),'utf8'))),core=readFileSync(url('src/campaign/core.js'),'utf8').trimEnd(),runtime=readFileSync(url('src/campaign/browser.js'),'utf8').trim();
const start='/* CAMPAIGN_DATA:BEGIN */',end='/* CAMPAIGN_RUNTIME:END */',a=html.indexOf(start),b=html.indexOf(end);
if(a<0||b<a)throw Error('Missing campaign embed markers');
const block=start+'\nvar VALLEY_DATA='+data+';\n/* CAMPAIGN_DATA:END */\n'+core+'\n\n'+runtime;
const next=html.slice(0,a)+block+html.slice(b+end.length);
if(process.argv.includes('--check')){if(next!==html)throw Error('Campaign source drift; run node scripts/sync-campaign.mjs');console.log('Campaign source matches embedded runtime.')}else{writeFileSync(url('index.html'),next);console.log('Campaign sources embedded.')}
