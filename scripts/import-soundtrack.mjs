import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
const {soundtrack}=JSON.parse(await fs.readFile('content/campaign/valley-v1.json','utf8'));
await fs.mkdir('assets/music',{recursive:true});
const manifest=[];
for(const q of soundtrack){
 if(!q.download.startsWith('https://www.scottbuckley.com.au/library/wp-content/uploads/')||!/^assets\/music\/[a-z-]+\.mp3$/.test(q.file))throw Error('Invalid source');
 const tmp=q.file+'.tmp';
 const result=spawnSync('curl',['--fail','--location','--retry','3','--max-time','180','--proto','=https','--output',tmp,q.download],{stdio:'inherit'});
 if(result.status!==0)throw Error('Download failed: '+q.id);
 const bytes=await fs.readFile(tmp);
 if(bytes.length<100000||!(bytes.subarray(0,3).toString()==='ID3'||bytes[0]===255&&(bytes[1]&224)===224))throw Error('Not MP3: '+q.id);
 const probe=spawnSync('ffprobe',['-v','error','-show_entries','format=duration','-of','csv=p=0',tmp],{encoding:'utf8'});
 if(probe.status!==0||Number(probe.stdout)<30)throw Error('Invalid duration '+q.id);
 await fs.rename(tmp,q.file);manifest.push({id:q.id,file:q.file,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex'),duration:Number(probe.stdout),license:q.license,source:q.download});
}
await fs.writeFile('assets/music/manifest.json',JSON.stringify(manifest,null,2)+'\n');
