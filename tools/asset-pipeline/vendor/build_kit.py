from PIL import Image,ImageDraw,ImageFilter
from pathlib import Path
import random, math,json,zipfile,hashlib,shutil
ROOT=Path('/mnt/data/frequencia-zero-kit');ROOT.mkdir(exist_ok=True)
SRC=Path('/mnt/data/sbs_pack'); A=ROOT/'assets'/'sbs';A.mkdir(parents=True,exist_ok=True)
manifest=[]
def save(im,cat,name,anchor=None,source='original procedural',collision=False):
 p=A/cat/(name+'.png');p.parent.mkdir(exist_ok=True);im.save(p,optimize=True);manifest.append(dict(id=name,category=cat,file=str(p.relative_to(ROOT)),size=list(im.size),anchor=anchor or [im.width//2,im.height-1],collision=collision,source=source))
def keyed(im):
 im=im.convert('RGBA');im.putdata([(r,g,b,0 if (r,g,b)==(0,128,128) else 255) for r,g,b,a in im.getdata()]);return im
walls=[keyed(Image.open(SRC/'Building Tiles'/f'Isometric Buildings {i} - 64x96.png')) for i in range(1,4)]
roofs=keyed(Image.open(SRC/'Roof Tiles'/'Isometric Town Roofing - 143x92.png'))
def wall(s,n):
 n-=1;x=n%18*64;y=n//18*96;return walls[s-1].crop((x,y,x+64,y+96))
def roof(n):
 n-=1;x=n%3*144;y=n//3*92;return roofs.crop((x,y,x+144,y+92))
for name,s,l,r,rf in [('uncle',1,121,122,1),('clinic',1,79,80,5),('station',1,77,78,11),('guard',1,109,110,4),('radio',2,61,62,2),('bento',1,37,38,1),('helena',1,115,116,2),('celina',1,39,40,1)]:
 im=Image.new('RGBA',(144,164));im.alpha_composite(wall(s,l),(8,62));im.alpha_composite(wall(s,r),(72,62));im.alpha_composite(roof(rf),(0,0));save(im,'architecture',name,[72,158],f'SBS CC0 B{s}-{l}/{r} R{rf}',True)
# texture applied only to opaque pixels, seeded, with restrained palette
P={'grass':(82,104,65),'dirt':(131,111,80),'stone':(111,116,108),'water':(54,83,91),'asphalt':(74,78,78),'sand':(156,139,102),'brick':(131,83,65),'gravel':(116,110,96)}
def shade(c,v):return tuple(max(0,min(255,x+v)) for x in c)
def texture(im,rng,amp=13):
 px=im.load()
 for y in range(im.height):
  for x in range(im.width):
   r,g,b,a=px[x,y]
   if a: px[x,y]=(*shade((r,g,b),rng.randint(-amp,amp)),a)
 return im
def diamond(d,x,y,w,h,c):d.polygon([(x,y-h//2),(x+w//2,y),(x,y+h//2),(x-w//2,y)],fill=c)
def cube(d,x,y,w,h,z,c):
 a=(x-w//2,y-h//2-z);b=(x,y-z);cc=(x+w//2,y-h//2-z);top=(x,y-h-z)
 d.polygon([a,b,(x,y),(x-w//2,y-h//2)],fill=shade(c,-18));d.polygon([b,cc,(x+w//2,y-h//2),(x,y)],fill=shade(c,-35));d.polygon([a,top,cc,b],fill=shade(c,17))
def make(cat,name,i):
 rng=random.Random(f'{cat}:{name}'); size={'terrain':(128,64),'vegetation':(96,128),'urban':(64,96),'rail':(128,96),'interior':(64,96),'characters':(64,96),'creatures':(96,128),'effects':(64,96),'icons':(48,48),'signs':(64,96)}[cat];w,h=size;im=Image.new('RGBA',size);d=ImageDraw.Draw(im);x=w//2;y=h-6;c=(130,117,91)
 if cat=='terrain':
  c=P[name.rsplit('_',1)[0]];diamond(d,64,32,128,64,c)
  for k in range(260):
   xx=rng.randrange(w);yy=rng.randrange(h)
   if abs(xx-64)/64+abs(yy-32)/32<.94:
    col=shade(c,rng.randrange(-24,25));d.line((xx,yy,xx+rng.randrange(1,5),yy),fill=col)
  if name.startswith('water'):
   for k in range(12):
    xx=rng.randrange(28,99);yy=rng.randrange(18,46);d.line((xx,yy,xx+8,yy),fill=(78,112,115))
 elif cat=='vegetation':
  d.ellipse((x-28,y-9,x+29,y+3),fill=(25,39,31,100)); trunk= name.startswith(('oak','pine','birch','dead'))
  if trunk:d.polygon([(x-5,y),(x+5,y),(x+3,y-72),(x-3,y-72)],fill=(91,68,45));d.line((x-2,y-4,x-1,y-62),fill=(154,116,75),width=2)
  height=65 if trunk else 25; cy=y-height
  for k in range(55 if trunk else 28):
   ang=rng.random()*math.tau;rad=rng.random()**.5;xx=x+math.cos(ang)*30*rad;yy=cy+math.sin(ang)*height*.55*rad;rr=rng.randrange(4,13);base=(72,95,53) if not name.startswith('dead') else (110,94,66);d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=shade(base,rng.randrange(-24,27)))
  if name.startswith('flowers'):
   for k in range(14):xx=rng.randrange(25,72);yy=rng.randrange(y-29,y-10);d.ellipse((xx,yy,xx+3,yy+3),fill=(185,151,99))
 elif cat in ('urban','rail','interior','signs'):
  d.ellipse((x-22,y-8,x+22,y+3),fill=(22,29,27,90)); base= name.split('_')[0]; c= (124,104,76) if base in ('crate','bench','fence','desk','shelf','table','chair','door','platform','sleeper') else (100,108,104)
  if cat=='signs' or base in ('lamp','pole','signal'):
   d.rectangle((x-2,y-68,x+2,y),fill=(92,92,78));cube(d,x,y-54,40,18,16,(138,129,100));d.line((x-12,y-67,x+10,y-57),fill=(220,209,169),width=2)
   if base=='lamp':d.ellipse((x-9,y-76,x+9,y-61),fill=(226,194,118))
  elif base in ('barrel','bin','pot','tank'):
   d.rectangle((x-13,y-35,x+13,y-7),fill=c);d.ellipse((x-13,y-43,x+13,y-27),fill=shade(c,25));d.ellipse((x-13,y-15,x+13,y),fill=shade(c,-15));d.line((x-13,y-18,x+13,y-18),fill=shade(c,-35),width=3)
  elif base in ('rail','track','sleeper','platform'):
   diamond(d,x,y-18,min(w-4,120),48,(116,107,88));
   for k in range(-3,4):d.line((x-42+k*10,y-31+k*3,x-4+k*10,y-12+k*3),fill=(82,64,49),width=4)
   d.line((x-46,y-38,x+42,y+0),fill=(174,176,160),width=3);d.line((x-28,y-46,x+58,y-8),fill=(174,176,160),width=3)
  elif base in ('bench','chair','table','desk','bed'):
   for dx in (-15,12):d.rectangle((x+dx,y-28,x+dx+4,y),fill=shade(c,-28))
   cube(d,x,y-23,43,22,8,c)
   if base in ('bench','chair','bed'):cube(d,x-8,y-36,33,14,20,c)
  else:
   cube(d,x,y, min(w-8,48),24,28+i%3*7,c);d.line((x-14,y-28,x,y-21,x+14,y-28),fill=shade(c,35),width=2)
   if base in ('radio','monitor','console','cabinet','locker'):d.rectangle((x-9,y-35,x+8,y-25),fill=(42,63,63));d.line((x-6,y-30,x+5,y-30),fill=(142,177,129),width=2)
 elif cat=='characters':
  skin=(159+i%4*17,113+i%4*12,86+i%3*13);coat=[(92,110,116),(123,103,74),(123,83,91),(99,111,81),(104,98,123),(158,151,128)][i%6];hair=(52+i%4*18,44+i%4*13,37+i%4*9)
  d.ellipse((x-18,y-8,x+18,y+2),fill=(20,31,28,100));d.polygon([(x-12,y-34),(x+13,y-34),(x+11,y-6),(x+2,y-6),(x,y-24),(x-3,y-6),(x-12,y-6)],fill=(59,64,64));d.rectangle((x-14,y-9,x-3,y),fill=(39,41,40));d.rectangle((x+2,y-9,x+13,y),fill=(39,41,40));d.polygon([(x-15,y-61),(x+13,y-61),(x+19,y-36),(x+10,y-31),(x-11,y-31),(x-19,y-38)],fill=coat);d.line((x-9,y-60,x-11,y-34),fill=shade(coat,26),width=3);d.ellipse((x-12,y-82,x+12,y-55),fill=skin);d.polygon([(x-14,y-72),(x-12,y-83),(x+8,y-85),(x+14,y-75),(x+10,y-69),(x-7,y-76)],fill=hair);d.rectangle((x-5,y-70,x-3,y-68),fill=(38,40,39));d.rectangle((x+5,y-70,x+7,y-68),fill=(38,40,39));d.line((x,y-62,x+5,y-62),fill=shade(skin,-35),width=1)
 elif cat=='creatures':
  col=[(133,170,153),(151,145,183),(105,143,163),(188,154,114)][i%4];d.ellipse((x-30,y-8,x+30,y+3),fill=(41,64,66,85));pts=[(x,y-112),(x+16,y-84),(x+12,y-64),(x+28,y-39),(x+9,y-10),(x,y-33),(x-11,y-10),(x-25,y-42),(x-12,y-64),(x-17,y-84)];d.polygon(pts,fill=(*col,210));d.line(pts+[pts[0]],fill=(*shade(col,35),230),width=2);d.ellipse((x-6,y-79,x+6,y-67),fill=(220,226,192));
 elif cat=='effects':
  col=[(132,189,171),(183,166,115),(151,141,192),(170,110,91)][i%4];
  for k in range(8):r=5+k*3;d.ellipse((x-r,h//2-r,x+r,h//2+r),outline=(*col,max(15,230-k*25)),width=2)
  for k in range(7):a=rng.random()*math.tau;r=rng.randrange(10,28);xx=x+math.cos(a)*r;yy=h//2+math.sin(a)*r;d.rectangle((xx,yy,xx+2,yy+2),fill=(*col,220))
 else:
  # inventory silhouettes, differentiated by item family
  base=name.split('_')[0];d.rounded_rectangle((8,8,40,40),radius=4,fill=(72,76,66),outline=(156,146,110),width=2)
  if base in ('key','tool'):d.ellipse((11,11,25,25),outline=(207,183,120),width=4);d.line((22,22,37,37),fill=(207,183,120),width=5);d.line((30,30,36,25),fill=(207,183,120),width=3)
  elif base in ('letter','document','photo','map'):d.polygon([(13,11),(34,11),(38,16),(38,37),(13,37)],fill=(200,186,147));
  else:d.ellipse((15,15,33,33),fill=(129+i%3*18,143,120),outline=(206,191,147),width=2);d.line((17,24,31,24),fill=(49,65,61),width=2)
 return texture(im,rng,9 if cat!='terrain' else 5)
sets={'terrain':[(k+'_'+str(i+1)) for k in P for i in range(4)],'vegetation':[f'{k}_{i+1}' for k in ['oak','pine','birch','dead','bush','flowers'] for i in range(4)],'urban':[f'{k}_{i+1}' for k in ['bench','fence','lamp','pole','bin','crate','barrel','pot'] for i in range(4)],'rail':[f'{k}_{i+1}' for k in ['rail','track','sleeper','platform','signal','tank'] for i in range(4)],'interior':[f'{k}_{i+1}' for k in ['desk','shelf','table','chair','door','bed','radio','monitor','console','cabinet','locker','crate'] for i in range(4)],'characters':['npc_'+str(i+1).zfill(2) for i in range(24)],'creatures':['echo_'+str(i+1) for i in range(8)],'effects':[f'{k}_{i+1}' for k in ['pulse','shield','contact','impact','fog','spark'] for i in range(4)],'icons':[f'{k}_{i+1}' for k in ['key','tool','letter','document','photo','map','tape','radio','watch','fragment'] for i in range(4)],'signs':[f'{k}_{i+1}' for k in ['street','station','clinic','warning'] for i in range(4)]}
for cat,names in sets.items():
 for i,name in enumerate(names):save(make(cat,name,i),cat,cat+'_'+name,collision=cat in ('urban','vegetation','interior'))
assert sum(len(v) for v in sets.values())==272
# atlas by category, original dimensions and slots
for cat in ['architecture',*sets]:
 entries=[m for m in manifest if m['category']==cat];cw,ch=entries[0]['size'];cols=min(8,len(entries));rows=math.ceil(len(entries)/cols);atlas=Image.new('RGBA',(cols*cw,rows*ch))
 for i,m in enumerate(entries):
  x=i%cols*cw;y=i//cols*ch;atlas.alpha_composite(Image.open(ROOT/m['file']),(x,y));m['atlas']={'file':f'assets/sbs/atlases/{cat}.png','rect':[x,y,cw,ch]}
 p=A/'atlases'/f'{cat}.png';p.parent.mkdir(exist_ok=True);atlas.save(p,optimize=True)
(A/'manifest.json').write_text(json.dumps({'version':1,'tile':[128,64],'assets':manifest,'note':'Procedural draft complements, not artist-approved. Architecture derived from SBS CC0.'},ensure_ascii=False,indent=2));shutil.copy(SRC/'License.txt',A/'SBS-LICENSE.txt');shutil.copy('/mnt/data/build_kit.py',ROOT/'build_kit.py')
(ROOT/'README.txt').write_text('Frequência Zero — 272 complementos procedurais + 8 construções derivadas do SBS. PNG RGBA, atlas por categoria, manifesto de âncoras e dimensões. Rascunho artístico, não homologado no motor. Copie assets/sbs para o repositório.\n')
with zipfile.ZipFile('/mnt/data/frequencia-zero-kit.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in ROOT.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(ROOT))
print(len(manifest),len(list(A.rglob('*.png'))))
