import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const read=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
const data=JSON.parse(read('content/campaign/valley-v1.json'));
const campaign=vm.runInNewContext(read('src/campaign/core.js')+'\ncreateValleyCampaign(data)',{data});
for(const p of Object.values(data.locations))assert.ok(p.purpose);
for(const r of data.storyReactions){
 const t=(r.day-1)*1440+r.from, c=campaign.fresh();
 for(const [i,id] of r.choices.entries())c.choices['test'+i]={id,at:t-61};
 assert.equal(campaign.storyReaction(r.npc,t,c)?.id,r.id);
 delete c.choices.test0;
 assert.notEqual(campaign.storyReaction(r.npc,t,c)?.id,r.id);
 c.choices.test0={id:r.choices[0],at:t-59};
 assert.notEqual(campaign.storyReaction(r.npc,t,c)?.id,r.id);
 c.choices.test0.at=t-60;
 assert.equal(campaign.storyReaction(r.npc,t,c)?.id,r.id);
 assert.notEqual(campaign.storyReaction(r.npc,(r.day-1)*1440+r.to,c)?.id,r.id);
 assert.equal(campaign.schedule(r.npc,t,c,true),null);
 const scheduled=campaign.schedule(r.npc,t,c);
 if(!scheduled.meeting){assert.equal(scheduled.loc,r.loc);assert.equal(scheduled.dialogue,r.dialogue)}
 assert.equal(campaign.storyReaction(r.npc,t-1440,c),null);
}
console.log('Narrative purpose and combined-choice reaction checks passed.');
