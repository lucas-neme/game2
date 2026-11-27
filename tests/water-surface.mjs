import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
const code=readFileSync(new URL('../assets/production/environment/water/surface-worker.js',import.meta.url),'utf8');
const {lakeMask,lakeFrame}=new Function(code+';return {lakeMask,lakeFrame}')();
const w=96,h=64,src=new Uint8ClampedArray(w*h*4);
for(let y=0;y<h;y++)for(let x=0;x<w;x++){const k=(y*w+x)*4,water=x>=12&&x<84&&y>=10&&y<54;src[k]=water?20+Math.round(7*Math.sin(x*.3)):80;src[k+1]=water?70+Math.round(15*Math.cos(y*.37+x*.17)):100;src[k+2]=water?125+Math.round(18*Math.sin(x*.4+y*.21)):35;src[k+3]=255}
const M=lakeMask(src,w,h),A=lakeFrame(src,w,h,M,0,48),B=lakeFrame(src,w,h,M,12,48),C=lakeFrame(src,w,h,M,48,48);
let changed=0,water=0,leaked=0;
for(let i=0;i<w*h;i++){const k=i*4;if(M.mask[i]){water++;if(A[k]!==B[k]||A[k+1]!==B[k+1]||A[k+2]!==B[k+2])changed++}else if(A[k+3]||B[k+3])leaked++}
assert.equal(water,3168);assert(changed/water>=.95);assert.equal(leaked,0);assert.deepEqual(A,C);
console.log('PASS: lake mask, moving surface, no land spill, seamless temporal loop');
