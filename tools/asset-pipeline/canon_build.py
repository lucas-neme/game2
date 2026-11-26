"""Canon production build (frequencia-zero-canon.zip is the artistic authority).

    python tools/asset-pipeline/canon_build.py [--preview out.png]

States (docs/art-direction/PIPELINE.md): SOURCE (zip contents, untouched, outside git), REVIEW (generated, awaiting
visual approval), APPROVED, PRODUCTION (exported + referenced by the game), REJECTED (kept with reason, never exported).
Only APPROVED items are exported; the manifest records every item with its state.
"""
import json, re, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image, ImageDraw
from common import ROOT, PROD, vnoise
import canon_catalog as K, canon_chars as CC, canon_layout as L, canon_assets as A, canonize as CZ
import ground as G0

OX, OY, W, H = G0.OX, G0.OY, G0.W, G0.H
iso = G0.iso
REG = {}   # name -> dict(im, anchor, category, source, state, note, ...)

def put(name, im, anchor, category, source, state='APPROVED', note='', **kw):
    REG[name] = dict(im=im, anchor=tuple(int(v) for v in anchor), category=category, source=source, state=state, note=note, **kw)

# ---------- buildings: canon + canon-house variants ----------
ROOFS = {'red': None, 'blue': ('2e3f6e', '4361a8', '7c97d6'), 'teal': ('1f4a4a', '2f6d6a', '5aa39a'),
         'slate': ('262838', '3d4157', '667090'), 'brown': ('3b2416', '6a4126', 'a06a3e')}

def recolor_roof(im, stops):
    a = np.array(im).astype(float); rgb = a[..., :3]; Hh = a.shape[0]
    yy = np.arange(Hh)[:, None].repeat(a.shape[1], 1)
    roof = (a[..., 3] > 0) & (rgb[..., 0] > rgb[..., 1] + 28) & (rgb[..., 0] > rgb[..., 2] + 38) & (yy < Hh * .62) & (rgb[..., 1] < 150)
    lum = (rgb @ np.array([.3, .59, .11])) / 255
    t = np.clip((lum - .12) / .45, 0, 1)
    from common import ramp
    rgb[roof] = ramp(stops, t[roof]); a[..., :3] = rgb
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def ruin(im):
    a = np.array(im).astype(float); rgb = a[..., :3]
    lit = (rgb[..., 0] > 190) & (rgb[..., 1] > 140) & (rgb[..., 2] < 140)
    g = rgb @ np.array([.3, .59, .11]); rgb = rgb * .55 + g[..., None] * .45; rgb *= .78
    rgb[lit] = np.array([38, 44, 56])
    a[..., :3] = rgb; return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def window_glow(im):
    a = np.array(im).astype(float); rgb = a[..., :3]
    lit = (a[..., 3] > 0) & (rgb[..., 0] > 185) & (rgb[..., 1] > 135) & (rgb[..., 2] < 150) & (rgb[..., 0] > rgb[..., 2] + 60)
    # only real window panes: lit pixels with >= 5 lit neighbours (drops speckles on edges and foliage)
    nb = sum(np.roll(np.roll(lit, dy, 0), dx, 1).astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    core = lit & (nb >= 6)
    from PIL import ImageFilter
    m = Image.fromarray((core * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.6))
    al = np.array(m).astype(float)
    out = np.zeros_like(a); out[..., :3] = [255, 196, 104]; out[..., 3] = np.clip(al * 1.3, 0, 255)
    return Image.fromarray(out.astype(np.uint8))

def buildings(items):
    for k in ('b-uncle', 'b-radio', 'b-clinic', 'b-guard', 'b-station', 'b-archive'):
        im, anc, cat, src, st, note = items[k]
        if k == 'b-station':  # canon track runs along x; our rail runs along y -> mirror (same art, flipped)
            im = im.transpose(Image.FLIP_LEFT_RIGHT); anc = (im.width - 1 - anc[0], anc[1]); note = 'mirrored so its track follows the rail (y axis)'
        put(k, im, anc, 'architecture', src, note=note, collision='2x2 footprint')
        put('n-' + k[2:], window_glow(im), anc, 'lighting', src + ' (window mask)')
    house, anc = items['b-uncle'][0], items['b-uncle'][1]
    mir = house.transpose(Image.FLIP_LEFT_RIGHT); manc = (mir.width - 1 - anc[0], anc[1])
    variants = {'h-bento': (house, anc, 'brown'), 'h-helena': (mir, manc, 'slate'), 'h-celina': (house, anc, 'teal'),
                'h-red': (mir, manc, 'red'), 'h-teal': (house, anc, 'blue'), 'h-slate': (mir, manc, 'slate'), 'h-brown': (house, anc, 'brown')}
    for name, (im, a_, roof) in variants.items():
        v = im if roof == 'red' else recolor_roof(im, ROOFS[roof])
        put(name, v, a_, 'architecture', 'canon:construcoes/casa_tio.png (variant)', note=f'canon house, roof {roof}', collision='2x2 footprint')
        put('n-' + name[2:], window_glow(v), a_, 'lighting', 'derived window mask')
    r = ruin(mir); put('h-ruin', r, manc, 'architecture', 'canon:construcoes/casa_tio.png (variant)', note='abandoned: desaturated, windows dark')

def residents_and_chars():
    chars = {}
    for key in CC.CHARS:
        im, meta, b = CC.sheet(key)
        chars[key] = dict(im=im, meta=meta, source=f"canon:personagens/{CC.CHARS[key]['src']}/recortes/{CC.CHARS[key]['crop']}.png", portrait=f"personagens/{CC.CHARS[key]['src']}/retrato.png")
    for key, folder in (('medico', 'medico'), ('guarda', 'guarda'), ('comerciante', 'comerciante'), ('ferroviario', 'ferroviario'), ('professor', 'professor'), ('crianca', 'crianca')):
        sheet = Image.open(A.CANON / 'moradores' / folder / 'folha_original.png').convert('RGBA'); w, h = sheet.size
        cell = np.array(sheet.crop((0, 0, w // 2, h // 4))).astype(float)
        CC.CHARS['m-' + key] = dict(src=None, crop=None, array=cell)
        im, meta, b = CC.sheet('m-' + key)
        chars['m-' + key] = dict(im=im, meta=meta, source=f'canon:moradores/{folder}/folha_original.png (row 1, col 1)', portrait=f'moradores/{folder}/retrato.png')
    return chars

# ---------- ground with canon terrain ----------
def swatches():
    comps = A.components(A.CANON / 'folhas' / 'terrenos.png')
    sw = [np.array(im)[..., :3].astype(float) for box, im in comps[:12]]
    eff = A.components(A.CANON / 'folhas' / 'efeitos_ambiente.png')
    water, shore = np.array(eff[0][1])[..., :3].astype(float), np.array(eff[1][1])[..., :3].astype(float)
    t17 = np.array(comps[17][1])[..., :3].astype(float)
    def inner(a, m=4): return a[m:-m, m:-m]
    return {'grass1': inner(sw[0]), 'grass2': inner(sw[1]), 'dirt': inner(sw[2]), 'flag': inner(sw[3]), 'cobble': inner(sw[4]),
            'cobble2': inner(sw[5]), 'grass3': inner(sw[6]), 'pave': inner(sw[7]), 'pave2': inner(sw[8]), 'brick': inner(sw[9]),
            'water': inner(water, 6), 'shore': inner(shore, 6), 'dirtgrass': inner(t17)}

def sample(tex, u, v):
    """Mirrored-repeat lookup (seamless) of a swatch at continuous texel coords."""
    h, w = tex.shape[:2]
    def mir(x, n):
        x = np.floor(x).astype(int) % (2 * n); return np.where(x < n, x, 2 * n - 1 - x)
    return tex[mir(v, h), mir(u, w)]

def quilt(tex, u, v, block=9, seed=0):
    """Non-repeating lookup: every block x block texel cell reads from a random spot of the canon swatch."""
    h, w = tex.shape[:2]; r = np.random.default_rng(seed)
    bu = np.floor(u / block).astype(int); bv = np.floor(v / block).astype(int)
    hsh = (bu * 73856093 ^ bv * 19349663) & 0xFFFFFF
    ox = (hsh % 997) % max(1, w - block); oy = ((hsh // 997) % 991) % max(1, h - block)
    fu = np.floor(u).astype(int) - bu * block; fv = np.floor(v).astype(int) - bv * block
    return tex[(fv + oy) % h, (fu + ox) % w]

def render_ground(sprites):
    T = swatches()
    py, px = np.mgrid[0:H, 0:W].astype(float)
    u = (px - OX) / 64; v = (py - OY) / 32
    gx = (u + v) / 2; gy = (v - u) / 2
    S = 18.0  # texels per grid cell
    tu, tv = gx * S, gy * S
    n1 = vnoise((H, W), 90, 3); n2 = vnoise((H, W), 34, 4)
    ga = quilt(T['grass1'], tu, tv, 9, 1); gb = quilt(T['grass2'], tu, tv, 9, 2); gc = quilt(T['grass3'], tu, tv, 9, 3)
    w1 = np.clip((n1 - .4) / .25, 0, 1)[..., None]; w2 = np.clip((n2 - .66) / .15, 0, 1)[..., None] * .7
    g = ga * (1 - w1) + gb * w1; g = g * (1 - w2) + gc * w2
    # pixel-art dithering instead of smooth blends: snap the blended colour to the nearer source texel
    pick = np.where((np.abs(g - ga).sum(-1) < np.abs(g - gb).sum(-1))[..., None], ga, gb)
    g = np.where((w2 > .35), gc, pick)
    img = g
    edge = (vnoise((H, W), 10, 9) - .5) * .18
    def band(items, half):
        m = np.zeros((H, W), bool)
        for it in items:
            if it[0] == 'row': _, y, x0, x1 = it; m |= (np.abs(gy - y) < half + edge) & (gx > x0 - .5) & (gx < x1 + .5)
            elif it[0] == 'col': _, x, y0, y1 = it; m |= (np.abs(gx - x) < half + edge) & (gy > y0 - .5) & (gy < y1 + .5)
            else: _, x0, y0, x1, y1 = it; m |= (gx > x0 - .5 + edge) & (gx < x1 + .5 - edge) & (gy > y0 - .5 + edge) & (gy < y1 + .5 - edge)
        return m
    walk = band(L.ROADS['cobble'], .5); cob = band(L.ROADS['cobble'], .36)
    img = np.where(walk[..., None], sample(T['pave'], tu * 1.3, tv * 1.3), img)
    img = np.where(cob[..., None], sample(T['cobble'], tu * 1.4, tv * 1.4), img)
    kerb = walk & ~band(L.ROADS['cobble'], .47) | (cob & ~band(L.ROADS['cobble'], .33))
    img[kerb] *= .62
    plaza = band(L.ROADS['plaza'], 0)
    img = np.where(plaza[..., None], sample(T['flag'], tu * 1.2, tv * 1.2), img)
    pe = plaza & ~band(L.ROADS['plaza'], -.06); img[pe] *= .6
    dirt = band(L.ROADS['dirt'], .3) & ~walk & ~plaza
    img = np.where(dirt[..., None], sample(T['dirt'], tu * 1.1, tv * 1.1), img)
    de = band(L.ROADS['dirt'], .34) & ~band(L.ROADS['dirt'], .3) & ~walk & ~plaza
    img = np.where(de[..., None], sample(T['dirtgrass'], tu, tv), img)
    # lake + shore
    ld = np.minimum(gx - 10.5, gy - 8.5) + (vnoise((H, W), 40, 57) - .5) * .5
    water = ld > 0; shore = ~water & (ld > -.3)
    img = np.where(water[..., None], sample(T['water'], tu * 1.1, tv * 1.1) * (1 - np.clip(ld / 4, 0, .35))[..., None], img)
    img = np.where(shore[..., None], sample(T['shore'], tu * 1.4, tv * 1.4), img)
    img[water & (ld < .06)] *= .65
    # rail: two tracks on gravel (canon wood sleepers, steel rails), platform paving
    for cxr in (-.26, -1.6):
        bed = (np.abs(gx - cxr) < .3)
        img = np.where(bed[..., None], sample(T['cobble2'], tu * 2, tv * 2) * .8, img)
        sl = bed & (np.abs(((gy * 5) % 1) - .5) < .16) & (np.abs(gx - cxr) < .22)
        img[sl] = np.array([92, 58, 38])
        for o in (-.12, .12):
            img[bed & (np.abs(gx - cxr - o) < .02)] = np.array([196, 190, 178])
    plat = (gx > -.02) & (gx < .5) & (gy > 3.5) & (gy < 8.5)
    img = np.where(plat[..., None], sample(T['pave2'], tu * 1.3, tv * 1.3), img)
    img[plat & (gx < .05)] = np.array([214, 178, 66])
    # fields outside the town (canon dirt rows)
    field = (gy > 13.6) & (gx < 10) & (gx > -1) & ~dirt & ~walk
    rows = np.abs(((gx * 3) % 1) - .5) < .22
    img = np.where((field & rows)[..., None], sample(T['dirt'], tu, tv) * .85, img)
    # world-edge haze
    G0_, G1_ = -5, 18
    dist = np.maximum(np.maximum(G0_ + 1.5 - gx, gx - (G1_ - 1.5)), np.maximum(G0_ + 1.5 - gy, gy - (G1_ - 1.5)))
    fade = np.clip((dist + 1.5) / 3, 0, 1); bg = np.array([27, 24, 46])
    inside = (gx > G0_ - .5) & (gx < G1_ + .5) & (gy > G0_ - .5) & (gy < G1_ + .5)
    img = img * (1 - fade[..., None]) + bg * fade[..., None]
    img = np.where(inside[..., None], img, bg)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    # baked outer scenery: canon trees and houses outside the playable square, back to front
    r = np.random.default_rng(7); trees = ['tree-green', 'tree-green', 'tree-pine', 'tree-autumn', 'tree-green', 'tree-pink', 'tree-pine']
    outer = []
    for x in range(-5, 19):
        for y in range(-5, 19):
            if 0 <= x < 14 and 0 <= y < 14: continue
            if x in (0, -1, -2) or (x == 5) or (y == 6 and x >= 14) or (x > 10 and y > 8): continue
            if (x < 0 or y < 0) and r.random() < .8: outer.append((trees[r.integers(len(trees))], x + r.uniform(-.3, .3), y + r.uniform(-.3, .3)))
            elif (x >= 14 or y >= 14) and r.random() < .18: outer.append(('bush', x + r.uniform(-.3, .3), y + r.uniform(-.3, .3)))
    outer += [('h-red', 16, 4), ('h-brown', 15.5, 1.5), ('h-slate', 4, 16.5)]
    for name, x, y in sorted(outer, key=lambda t: t[1] + t[2]):
        s = REG[name]; cx, cy = iso(x, y)
        if name.startswith('h-'): cy += 32
        out.alpha_composite(s['im'], (int(cx - s['anchor'][0]), int(cy - s['anchor'][1])))
    hz = np.array(out).astype(float); hz[..., :3] = hz[..., :3] * (1 - fade[..., None] * .85) + bg * fade[..., None] * .85
    return Image.fromarray(np.clip(hz, 0, 255).astype(np.uint8), 'RGBA')

def placements():
    out = []
    for site, (x, y) in L.SITES.items(): out.append((L.SITE_SPRITE[site], x, y, 0, site, True))
    for s, x, y, _ in L.DECOR_BUILDINGS: out.append((s, x, y, 0, None, True))
    for s, x, y in L.DECOR_BLOCK: out.append((s, x, y, 0, None, False))
    for s, x, y, dx, dy in L.PROPS: out.append((s, x + dx / 3, y + dy / 3, 0, None, False))
    return out

def screen_pos(name, gx, gy, building):
    s = REG[name]; cx, cy = iso(gx, gy)
    if building: cy += 32          # canon buildings: base front corner on the cell's front vertex
    return cx - s['anchor'][0], cy - s['anchor'][1]

def postcard(base):
    im = base.copy()
    for name, gx, gy, bias, kind, bld in sorted(placements(), key=lambda p: p[1] + p[2] + p[3]):
        x, y = screen_pos(name, gx, gy, bld); im.alpha_composite(REG[name]['im'], (int(x), int(y)))
    return im

def ui_art():
    """Icons, weather and logo cut from referencia-canonica.png (the pack's strips are clipped)."""
    out = {}
    ref = Image.open(A.CANON / 'referencia-canonica.png').convert('RGBA')
    def strip(box, names):
        comps = [c for c in A.components(ref.crop(box), min_px=60, core_mx=125, core_sat=70, grow=1) if 18 <= c[1].width <= 60 and c[1].height >= 18]
        comps.sort(key=lambda c: c[0][0])
        return {n: im for n, (b, im) in zip(names, comps)}
    out.update({'icon-' + k: v for k, v in strip((22, 942, 708, 1004), ['backpack', 'notebook', 'radio', 'camera', 'flashlight', 'key', 'medkit', 'pill', 'papers', 'cassette', 'photo', 'coin', 'gear', 'crystal']).items()})
    out.update({'wx-' + k: v for k, v in strip((980, 940, 1272, 1004), ['sun', 'dawn', 'moon', 'rain', 'storm', 'fog']).items()})
    out['logo'] = ref.crop((1296, 908, 1536, 1024))
    return out

def station_scene():
    """'Estação abandonada' investigation scene composed only of canon art: station facade (with its clock),
    platform paving, tracks and canon props. 360x200 px, shown with nearest-neighbour scaling."""
    Wc, Hc = 360, 200
    T = swatches()
    yy, xx = np.mgrid[0:Hc, 0:Wc].astype(float)
    sky = np.zeros((Hc, Wc, 3)); top = np.array([18, 16, 34]); bot = np.array([44, 34, 70])
    sky[:] = (top + (bot - top) * (yy / Hc)[..., None])
    plat = yy > 120
    sky = np.where(plat[..., None], quilt(T['pave2'], xx * .9, yy * 1.6, 9, 11) * .8, sky)
    rails = (yy > 168)
    sky = np.where(rails[..., None], quilt(T['cobble2'], xx, yy * 2, 9, 12) * .55, sky)
    for x0 in range(0, Wc, 14): sky[170:196, x0:x0 + 6] = [84, 54, 36]
    for ry in (176, 189): sky[ry:ry + 2] = [200, 196, 186]
    sky[166:169] = [214, 178, 66]
    rng = np.random.default_rng(3)
    for _ in range(60):
        x, y = rng.integers(0, Wc), rng.integers(0, 90); sky[y, x] = [230, 225, 210]
    im = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    st = REG['b-station']['im'].transpose(Image.FLIP_LEFT_RIGHT)   # original canon orientation
    sx, sy = 24, 2
    im.alpha_composite(st, (sx, sy))
    a = np.array(st).astype(int); rgb = a[..., :3]
    cream = (a[..., 3] > 0) & (rgb.min(-1) > 170) & (np.arange(st.height)[:, None] < st.height * .45)
    ys, xs = np.nonzero(cream)
    clock = (sx + xs.mean(), sy + ys.mean()) if len(xs) else (sx + st.width * .52, sy + st.height * .25)
    def put_prop(name, x, y):
        s = REG[name]; im.alpha_composite(s['im'], (int(x - s['anchor'][0]), int(y - s['anchor'][1]))); return (x, y - s['im'].height * .55)
    bench = put_prop('bench-b', 52, 160)
    cab = put_prop('cabinet', 262, 158)
    crates = put_prop('crate-a', 300, 163); put_prop('crate-b', 322, 165)
    put_prop('barrel', 336, 150); put_prop('lamp', 236, 160)
    pins = {'Relógio parado': clock, 'Bilheteria': (sx + st.width * .66, sy + st.height * .62), 'Trilhos': (120, 184),
            'Manifesto rasgado': crates, 'Armário de sinalização': cab}
    return im, {k: (round(x / Wc * 100, 1), round(y / Hc * 100, 1)) for k, (x, y) in pins.items()}

def interiors():
    study = Image.open(A.CANON / 'interiores' / 'escritorio.png').convert('RGBA')
    study_pins = {'Fita cassete': (44.0, 74.0), 'Fotografia': (12.5, 22.0), 'Cofre de aço': (70.5, 21.0), 'Agenda': (36.5, 66.0)}
    hall, hall_pins = station_scene()
    return {'study': (study, study_pins, 'canon:interiores/escritorio.png', 'APPROVED'),
            'station': (hall, hall_pins, 'composition of canon art (station facade, props, terrain)', 'APPROVED')}

def main():
    errs = L.validate(ROOT / 'index.html')
    if errs: raise SystemExit('layout errors:\n' + '\n'.join(errs))
    items = K.catalog()
    buildings(items)
    for k, (im, anc, cat, src, st, note) in items.items():
        if k.startswith('b-'): continue
        put(k, im, anc, cat, src, state=st, note=note)
    REG['cr-shadow']['state'] = 'REJECTED'; REG['cr-shadow']['note'] = 'dark body equals the board background; needs a manual cut'
    if '--preview' in sys.argv:
        base = render_ground(None); pc = postcard(base); out = Path(sys.argv[sys.argv.index('--preview') + 1]); pc.save(out); print('preview', out); return
    export()

def export():
    import export as EX
    env = PROD / 'environment'; chd = PROD / 'characters'; fx = PROD / 'effects'; ui = PROD / 'ui'; intd = PROD / 'interiors'; man = ROOT / 'assets' / 'manifests'
    for d in (env, chd, fx, ui, intd, man): d.mkdir(parents=True, exist_ok=True)
    for old in env.glob('atlas-*.png'): old.unlink()
    for old in chd.glob('ch-*.png'): old.unlink()
    base = render_ground(None); base.convert('RGB').save(env / 'ground.webp', quality=92, method=6)
    from common import Sprite
    approved = [Sprite(n, d['im'], d['anchor'], d['category'], source=d['source']) for n, d in REG.items() if d['state'] == 'APPROVED']
    atl = EX.pack_atlases(approved)
    files = []; table = {}
    for i, (im, rects) in enumerate(atl):
        fn = f'assets/production/environment/atlas-{i}.png'; im.save(ROOT / fn, optimize=True); files.append(fn)
        for n, r in rects.items(): table[n] = dict(atlas=i, rect=list(r))
    chars = residents_and_chars(); chmeta = {}
    ports = []
    for key, c in chars.items():
        fn = f'assets/production/characters/ch-{key}.png'; c['im'].save(ROOT / fn, optimize=True)
        chmeta[key] = {'file': fn, 'fw': CC.FW, 'fh': CC.FH, 'ax': CC.FW // 2, 'ay': CC.FOOT_Y, 'anims': c['meta'], 'source': c['source'], 'state': 'APPROVED'}
        ports.append((key, K.portrait(c['portrait'])))
    PW, PH = 136, 112
    pat = Image.new('RGBA', (PW * len(ports), PH))
    for i, (k, p) in enumerate(ports): pat.alpha_composite(p, (i * PW + (PW - p.width) // 2, PH - p.height))
    pat.save(ui / 'portraits.png', optimize=True)
    u = ui_art()
    icon_names = [k for k in u if k != 'logo']
    IW = 64; iat = Image.new('RGBA', (IW * len(icon_names), IW))
    for i, k in enumerate(icon_names): im = u[k]; iat.alpha_composite(im, (i * IW + (IW - im.width) // 2, (IW - im.height) // 2))
    iat.save(ui / 'icons.png', optimize=True); u['logo'].save(ui / 'logo.png', optimize=True)
    rooms = interiors(); room_meta = {}
    for k, (im, pins, src, st) in rooms.items():
        fn = f'assets/production/interiors/{k}.png'; im.save(ROOT / fn, optimize=True); room_meta[k] = {'file': fn, 'w': im.width, 'h': im.height, 'source': src, 'state': st, 'hotspots': pins}
    EX.fog_texture().save(fx / 'fog.png', optimize=True)
    crd = PROD / 'creatures'; crd.mkdir(parents=True, exist_ok=True)
    REG['cr-small-0']['im'].save(crd / 'echo.png'); REG['orb']['im'].save(crd / 'pulse.png')
    for key, fn in (('hero', 'hero.png'), ('m-guarda', 'guard.png')):
        meta = chars[key]['meta']['idle:front']; chars[key]['im'].crop((0, meta['row'] * CC.FH, CC.FW, (meta['row'] + 1) * CC.FH)).save(crd / fn)
    names = list(table); idx = {n: i for i, n in enumerate(names)}
    place = [[idx[n], round(gx, 3), round(gy, 3), bias, kind or 0, 1 if bld else 0] for n, gx, gy, bias, kind, bld in placements()]
    world = {'ox': OX, 'oy': OY, 'w': W, 'h': H, 'tile': [128, 64], 'cam': [iso(-2, 15)[0], iso(-2, -2)[1] - 150, iso(15, -2)[0], iso(15, 15)[1] + 80]}
    lights = [[round(x + dx / 3, 3), round(y + dy / 3, 3), z, r_, k] for (x, y, dx, dy, z, r_, k) in L.LIGHTS]
    blocked = sorted(f'{x},{y}' for (x, y) in L.blocked_cells(ROOT / 'index.html'))
    night = {}
    for n, gx, gy, bias, kind, bld in placements():
        if bld and ('n-' + n[2:]) in idx: night[kind or f'{gx},{gy}'] = idx['n-' + n[2:]]
    # ---- collision shapes (world units = cells; feet plane). 0=box [cx,cy,hx,hy], 1=circle [cx,cy,r]
    PROP_R = {'lamp': .09, 'bench': .26, 'bench-b': .26, 'barrel': .17, 'barrel-b': .17, 'barrels': .3, 'hydrant': .12, 'bin': .13,
              'crate-a': .2, 'crate-b': .2, 'stall': .36, 'kiosk': .26, 'bike': .2, 'cabinet': .22, 'notice': .2, 'signpost': .1,
              'sign-estacao': .08, 'sign-clinica': .08, 'sign-radio': .08, 'sign-centro': .08, 'fence-wood': .28, 'wall-stone': .3}
    cols = []
    bset = {(int(c.split(',')[0]), int(c.split(',')[1])) for c in blocked}
    trees = {(x, y): s_ for s_, x, y in L.DECOR_BLOCK}
    for (x, y) in sorted(bset):
        if (x, y) in trees:
            cols.append([1, x, y, .27 if trees[(x, y)] == 'rock' else .2, 'trunk:' + trees[(x, y)]])
        else:
            cols.append([0, x, y, .5, .5, 'building'])
    for site, (x, y) in L.SITES.items(): cols.append([0, x, y, .5, .5, 'site:' + site])
    for s_, x, y, dx, dy in L.PROPS:
        if s_ in PROP_R and 0 <= x < 14 and 0 <= y < 14: cols.append([1, round(x + dx / 3, 3), round(y + dy / 3, 3), PROP_R[s_], 'prop:' + s_])
    cols.append([0, 12.5, 11.5, 2.0, 3.0, 'water'])
    data_cols = [c[:-1] for c in cols]
    data = {'v': 2, 'canon': True, 'colliders': data_cols, 'world': world, 'ground': 'assets/production/environment/ground.webp', 'atlases': files,
            'fog': 'assets/production/effects/fog.png', 'names': names,
            'sprites': [[table[n]['atlas'], *table[n]['rect'], *REG[n]['anchor']] for n in names],
            'place': place, 'night': night, 'blocked': blocked, 'lights': lights,
            'lake': [[round(a), round(b)] for a, b in (iso(10.5, 8.5), iso(18.5, 8.5), iso(18.5, 18.5), iso(10.5, 18.5))],
            'chars': chmeta, 'portraits': {'file': 'assets/production/ui/portraits.png', 'w': PW, 'h': PH, 'keys': [k for k, _ in ports]},
            'icons': {'file': 'assets/production/ui/icons.png', 'size': IW, 'keys': icon_names}, 'logo': 'assets/production/ui/logo.png',
            'rooms': {k: {kk: vv for kk, vv in v.items() if kk != 'hotspots'} for k, v in room_meta.items()},
            'creatures': {k: idx[k] for k in names if k.startswith('cr-')}}
    manifest = {'version': 2, 'generated': str(date.today()), 'authority': 'frequencia-zero-canon.zip (referencia-canonica.png)',
                'states': ['SOURCE', 'REVIEW', 'APPROVED', 'PRODUCTION', 'REJECTED'],
                'scale': {'cell': [128, 64], 'metre_px': 21.3, 'character_frame': [CC.FW, CC.FH], 'camera_zoom': 'pixel-art nearest, default ~2x'},
                'assets': {n: {'category': d['category'], 'source': d['source'], 'license': 'canon (project owner)' if d['source'].startswith('canon') else 'original',
                               'size': list(d['im'].size), 'anchor': list(d['anchor']), 'collision': d.get('collision'),
                               'state': ('PRODUCTION' if d['state'] == 'APPROVED' else d['state']), 'note': d['note']} for n, d in REG.items()},
                'characters': {k: {'source': v['source'], 'frame': [CC.FW, CC.FH], 'anchor': [CC.FW // 2, CC.FOOT_Y], 'views': ['front (SE, mirrored SW)', 'back (NE, mirrored NW)'],
                                   'animations': {a: n for a, n in CC.ANIMS}, 'state': 'PRODUCTION'} for k, v in chmeta.items()},
                'collision': {'units': 'grid cells (3 m); feet plane', 'hero_radius': .22, 'npc_radius': .22, 'shapes': cols,
                              'rules': 'buildings: ground footprint; trees/rocks: trunk circle; props: base circle; canopies and roofs never collide'},
                'interiors': room_meta, 'atlases': files, 'layout': {'placements': len(place), 'blocked': blocked}}
    (man / 'production.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    for room, meta in room_meta.items():
        for label, (x, y) in meta['hotspots'].items():
            html, n = re.subn(r"\['" + re.escape(label) + r"',[0-9.]+,[0-9.]+,", f"['{label}',{x},{y},", html)
            if n != 1: raise SystemExit(f'hotspot {label!r}: {n}')
    js = 'const ART=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'
    html = re.sub(r'/\*ART:BEGIN\*/.*?/\*ART:END\*/', lambda m: '/*ART:BEGIN*/' + js + '/*ART:END*/', html, flags=re.S)
    (ROOT / 'index.html').write_text(html, encoding='utf-8', newline='\n')
    print('exported', len(names), 'sprites,', len(chmeta), 'characters,', len(place), 'placements; rejected:', [n for n, d in REG.items() if d['state'] == 'REJECTED'])

if __name__ == '__main__':
    main()
