/* Full-surface lake animation. Source: existing ground.webp, not an overlay of stripes.
   Worker computes loop sprites once; the main thread only composites cached bitmaps.
   The water mask is the largest connected blue region in a bounded crop, with
   a conservative antialiased fringe; land is never sampled into the water. */
function lakeMask(src,w,h){
 const n=w*h,cand=new Uint8Array(n),seen=new Uint8Array(n),q=new Int32Array(n);let best=[];
 for(let i=0;i<n;i++){const k=i*4,R=src[k],G=src[k+1],B=src[k+2];cand[i]=src[k+3]>0&&B>40&&B-R>12&&B>G+2&&B>R*1.12?1:0}
 for(let i=0;i<n;i++){if(!cand[i]||seen[i])continue;let end=1;q[0]=i;seen[i]=1;for(let j=0;j<end;j++){const v=q[j],x=v%w,y=(v/w)|0;for(const u of [x>0?v-1:-1,x<w-1?v+1:-1,y>0?v-w:-1,y<h-1?v+w:-1]){if(u>=0&&cand[u]&&!seen[u]){seen[u]=1;q[end++]=u}}}if(end>best.length)best=q.slice(0,end)}
 const mask=new Uint8Array(n);for(const i of best)mask[i]=255;
 // Close small holes inside the water (highlights/foam), not along the land boundary.
 for(let y=1;y<h-1;y++)for(let x=1;x<w-1;x++){const i=y*w+x;if(!mask[i]&&mask[i-1]&&mask[i+1]&&mask[i-w]&&mask[i+w])mask[i]=255}
 const dist=new Uint16Array(n);for(let i=0;i<n;i++)dist[i]=mask[i]?4095:0;
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x;if(!mask[i])continue;dist[i]=Math.min(dist[i],x?dist[i-1]+3:4095,y?dist[i-w]+3:4095,x&&y?dist[i-w-1]+4:4095,x<w-1&&y?dist[i-w+1]+4:4095)}
 for(let y=h-1;y>=0;y--)for(let x=w-1;x>=0;x--){const i=y*w+x;if(!mask[i])continue;dist[i]=Math.min(dist[i],x<w-1?dist[i+1]+3:4095,y<h-1?dist[i+w]+3:4095,x<w-1&&y<h-1?dist[i+w+1]+4:4095,x&&y<h-1?dist[i+w-1]+4:4095)}
 return {mask,dist,count:best.length};
}
function lakeFrame(src,w,h,M,frame,count){
 const out=new Uint8ClampedArray(w*h*4),phase=2*Math.PI*frame/count;
 const sx1=new Float32Array(w),sx2=new Float32Array(w),sy1=new Float32Array(h),sy2=new Float32Array(h);
 for(let x=0;x<w;x++){sx1[x]=Math.sin(x*.047-phase);sx2[x]=Math.sin(x*.022+phase*2)}
 for(let y=0;y<h;y++){sy1[y]=Math.sin(y*.071-phase*2);sy2[y]=Math.cos(y*.039+phase)}
 const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
 for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x,k=i*4;if(!M.mask[i])continue;
  const edge=M.dist[i]/3,amp=Math.min(1,edge/5);
  // Two travelling waves and a long swell; every visible pixel is resampled.
  const dx=(sx1[x]*2.6+sy1[y]*3.3+sx2[x]*sy2[y]*2.1)*amp;
  const dy=(sy2[y]*2.1+sx2[x]*1.6+sx1[x]*sy1[y]*1.4)*amp;
  const X=clamp(x+dx,0,w-1),Y=clamp(y+dy,0,h-1),u=Math.floor(X),v=Math.floor(Y),u1=Math.min(w-1,u+1),v1=Math.min(h-1,v+1);
  const ids=[v*w+u,v*w+u1,v1*w+u,v1*w+u1],fx=X-u,fy=Y-v,weights=[(1-fx)*(1-fy),fx*(1-fy),(1-fx)*fy,fx*fy];
  let R=0,G=0,B=0,weight=0;for(let j=0;j<4;j++){if(!M.mask[ids[j]])continue;const a=weights[j],p=ids[j]*4;R+=src[p]*a;G+=src[p+1]*a;B+=src[p+2]*a;weight+=a}
  if(weight>.001){R/=weight;G/=weight;B/=weight}else{R=src[k];G=src[k+1];B=src[k+2]}
  // Preserve deep blue and the existing authored texture. Shallow wash follows the actual shore.
  const shimmer=(sx1[x]*sy2[y]+sy1[y]*.55)*2.8*amp;
  const shoreline=edge<9?Math.exp(-Math.pow((edge-(2.8+1.35*sx1[x]+.6*sy2[y]))/1.25,2))*(.40+.30*sx2[x]+.20*sy1[y]):0;
  const fade=clamp((B-30)/55,0,1),foam=Math.max(0,shoreline)*fade*18;
  out[k]=R+shimmer+foam*.75;out[k+1]=G+shimmer+foam;out[k+2]=B+shimmer*.8+foam*.95;out[k+3]=edge<1.4?Math.round(190+edge*45):255;
 }return out;
}
if(typeof self!=='undefined'&&typeof self.postMessage==='function')self.onmessage=async e=>{
 const {pixels,w,h,count}=e.data,src=new Uint8ClampedArray(pixels),M=lakeMask(src,w,h);
 if(M.count<100){self.postMessage({error:'Water region not found'});return}
 self.postMessage({maskPixels:M.count});
 for(let i=0;i<count;i++){
  const data=lakeFrame(src,w,h,M,i,count);
  if(typeof createImageBitmap==='function'&&typeof ImageData==='function'){try{const bitmap=await createImageBitmap(new ImageData(data,w,h));self.postMessage({i,bitmap},[bitmap]);continue}catch{}}
  self.postMessage({i,pixels:data.buffer},[data.buffer]);
 }
 self.postMessage({done:true});
};
