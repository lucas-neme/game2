"""Ground of Vale do Cedro at production scale (cell 128x64), world grid -5..18, plus baked outer scenery.
iso(x, y) = (OX + (x - y) * 64, OY + (x + y) * 32)."""
import numpy as np
from PIL import Image, ImageFilter
from common import hexc, fbm, vnoise
import layout

OX, OY = 1472, 480
W, H = 2944, 1680
G0, G1 = -5, 18

def iso(x, y): return OX + (x - y) * 64, OY + (x + y) * 32

def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]; return a * (1 - t) + b * t

def road_mask(gx, gy, items, noise, half=.42):
    m = np.zeros(gx.shape, bool)
    for it in items:
        if it[0] == 'row':
            _, y, x0, x1 = it; m |= (np.abs(gy - y) < half + noise) & (gx > x0 - .5) & (gx < x1 + .5)
        elif it[0] == 'col':
            _, x, y0, y1 = it; m |= (np.abs(gx - x) < half + noise) & (gy > y0 - .5) & (gy < y1 + .5)
        else:
            _, x0, y0, x1, y1 = it; m |= (gx > x0 - .5 - noise) & (gx < x1 + .5 + noise) & (gy > y0 - .5 - noise) & (gy < y1 + .5 + noise)
    return m

def render_ground(sprites):
    shp = (H, W)
    py, px = np.mgrid[0:H, 0:W].astype(float)
    u = (px - OX) / 64; v = (py - OY) / 32
    gx = (u + v) / 2; gy = (v - u) / 2
    rng = np.random.default_rng(1998)
    n1 = fbm(shp, 11, (160, 60, 22, 8)); n2 = fbm(shp, 23, (90, 30, 12, 5)); fine = vnoise(shp, 2.2, 5); grain = rng.random(shp)
    # grass: muted olive with dry and lush patches + blade grain
    img = mix(hexc('47522c'), hexc('6a7440'), n1 * 1.5 - .25)
    img = mix(img, hexc('8a7d52'), (n2 - .6) * 3.5)
    img = mix(img, hexc('3a4a26'), (n1 - .62) * 4)
    img *= (0.88 + .2 * fine[..., None]) * (0.96 + .08 * grain[..., None])
    blade = (grain > .975); img[blade] *= .78
    flower = (grain > .9975) & (n2 > .5); img[flower] = hexc('d9cf9a')
    edge = (fbm(shp, 41, (14, 6, 3), (.6, .3, .1)) - .5) * .16
    # sidewalks along cobble streets (concrete slabs), then cobble, then dirt
    cob = road_mask(gx, gy, layout.ROADS['cobble'], edge * 0, .36)
    walk = road_mask(gx, gy, layout.ROADS['cobble'], edge * 0, .5) & ~cob
    slab = (np.abs(((gx + gy) * 4) % 1 - .5) > .46) | (np.abs(((gx - gy) * 4) % 1 - .5) > .46)
    wc = mix(hexc('8b867a'), hexc('a49e8e'), fine) * (0.94 + .08 * grain[..., None]); wc[slab] *= .8
    img[walk] = wc[walk]
    curb = road_mask(gx, gy, layout.ROADS['cobble'], 0, .38) & ~road_mask(gx, gy, layout.ROADS['cobble'], 0, .345)
    sx = gx * 9; sy = gy * 9 + (np.floor(gx * 9) % 2) * .5
    sid = (np.floor(sx) * 37 + np.floor(sy) * 19) % 101 / 101
    mortar = (np.minimum(sx % 1, 1 - sx % 1) < .1) | (np.minimum(sy % 1, 1 - sy % 1) < .1)
    cc = mix(hexc('5f594f'), hexc('8d8372'), sid * .8 + fine * .3) * (0.9 + .14 * grain[..., None])
    hi = (sx % 1 < .3) & (sy % 1 < .3) & ~mortar; cc[hi] *= 1.08
    cc[mortar] *= .58
    # plaza: concentric pattern of paving around the statue
    pr = np.sqrt((gx - 5) ** 2 + (gy - 6) ** 2)
    plaza = road_mask(gx, gy, [layout.ROADS['cobble'][2]], 0, 0)
    ring = (np.abs((pr * 3.2) % 1 - .5) > .44)
    pc = mix(hexc('8f8676'), hexc('a99f8b'), sid) * (0.92 + .1 * grain[..., None]); pc[ring] *= .72
    cc = np.where(plaza[..., None], pc, cc)
    img[cob] = cc[cob]; img[curb & ~plaza] = hexc('6c675d') * .85
    dirt = road_mask(gx, gy, layout.ROADS['dirt'], edge, .33) & ~cob & ~walk
    dc = mix(hexc('66523c'), hexc('8c7454'), n2 * 1.3 - .1) * (0.9 + .18 * grain[..., None])
    rut = np.where(np.abs((gy % 1) - .5) < .5, np.abs(((gy + .5) % 1) - .5), 1)
    img[dirt] = dc[dirt]
    # lake (x>10, y>8 and beyond), shores, pier
    ld = np.minimum(gx - 10.5, gy - 8.5) + (fbm(shp, 57, (40, 16, 6), (.6, .3, .1)) - .5) * .5
    water = ld > 0
    depth = np.clip(ld / 2.5, 0, 1)
    wcol = mix(hexc('4d6f68'), hexc('1f3640'), depth) * (0.95 + .08 * fine[..., None])
    img[water] = wcol[water]
    shore = ~water & (ld > -.32)
    sc = mix(hexc('857a5e'), hexc('a59777'), grain) * (0.85 + .25 * fine[..., None]); sc[grain > .86] *= .7
    img[shore] = sc[shore]
    wet = water & (ld < .12); img[wet] *= .72
    pier = (gy > 9.72) & (gy < 10.28) & (gx > 10.3) & (gx < 12.6)
    plank = np.abs(((gx * 10) % 1) - .5) > .42
    pcol = hexc('7b5d40') * (0.85 + .25 * fine[..., None]); pcol[plank] *= .7
    img[pier] = pcol[pier]
    # rail: playable track (x=0, west half) + outer track (x=-1.6); gravel beds, sleepers, rails
    for cxr, lo, hi_ in ((-.26, -5, 18), (-1.6, -5, 18)):
        bed = (np.abs(gx - cxr) < .3) & (gy > lo - .5) & (gy < hi_ + .5)
        gc = mix(hexc('5a554c'), hexc('8a8478'), grain) * (0.85 + .2 * fine[..., None]); img[bed] = gc[bed]
        sl = bed & (np.abs(((gy * 5) % 1) - .5) < .17) & (np.abs(gx - cxr) < .22)
        img[sl] = hexc('4b3b2c') * (0.8 + .3 * grain[sl][..., None])
        for o in (-.12, .12):
            rl = bed & (np.abs(gx - cxr - o) < .016); img[rl] = hexc('c2beb4')
            rs = bed & (np.abs(gx - cxr - o - .022) < .01); img[rs] *= .55
    plat = (gx > -.02) & (gx < .5) & (gy > 3.5) & (gy < 8.5)
    ps = (np.abs((gy * 3) % 1 - .5) > .46) | (np.abs(((gx + .02) * 6) % 1 - .5) > .45)
    pcl = mix(hexc('8d887c'), hexc('a8a192'), fine) * (0.93 + .1 * grain[..., None]); pcl[ps] *= .8
    img[plat] = pcl[plat]
    img[plat & (gx < .06)] = hexc('c9a640') * .95
    lip = (gy > 8.5) & (gy < 8.62) & (gx > -.02) & (gx < .5); img[lip] = hexc('5e5a52')
    # fields south-west outside the town: plowed rows
    field = (gy > 13.6) & (gx < 10) & (gx > -1) & ~dirt & ~cob & ~walk
    rows = (np.abs(((gx * 3) % 1) - .5) < .22)
    fc = np.where(rows[..., None], hexc('5f4b34'), hexc('6e7a3a')) * (0.88 + .2 * fine[..., None])
    img[field] = fc[field]
    # soft occlusion under buildings and trees (cell diamonds blurred)
    ao = Image.new('L', (W, H)); from PIL import ImageDraw; d = ImageDraw.Draw(ao)
    for (x, y), s in list(layout.blocked_cells().items()) + [(v, k) for k, v in layout.SITES.items()]:
        cx, cy = iso(x, y); k = .58 if str(s).startswith('b-') or s in layout.SITES else .3
        d.polygon([(cx, cy - 32 * k * 1.8), (cx + 64 * k * 1.8, cy), (cx, cy + 32 * k * 1.8), (cx - 64 * k * 1.8, cy)], fill=120)
    aoa = np.array(ao.filter(ImageFilter.GaussianBlur(14))).astype(float) / 255
    img *= (1 - aoa[..., None] * .55)
    # world edge: fade far scenery into the night-green haze
    distx = np.maximum(np.maximum(G0 + 1.5 - gx, gx - (G1 - 1.5)), np.maximum(G0 + 1.5 - gy, gy - (G1 - 1.5)))
    fade = np.clip((distx + 1.5) / 3, 0, 1)
    img = mix(img, hexc('1b2524'), fade)
    inside = (gx > G0 - .5) & (gx < G1 + .5) & (gy > G0 - .5) & (gy < G1 + .5)
    bg = hexc('1b2524')
    img = np.where(inside[..., None], img, bg)
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')
    # baked scenery (outside the playable square), back to front
    for (name, x, y, dx, dy) in sorted(layout.OUTER, key=lambda p: p[1] + p[2] + (p[3] + p[4]) / 3):
        sp = sprites.get(name)
        if not sp: continue
        cx, cy = iso(x + dx / 3, y + dy / 3)
        out.alpha_composite(sp.im, (int(cx - sp.anchor[0]), int(cy - sp.anchor[1])))
    # power line between outer pylons
    d = ImageDraw.Draw(out)
    tops = [iso(x, y) for (n, x, y, _, _) in layout.OUTER if n == 'pylon']
    tops = [(a, b - 122) for a, b in sorted(tops)]
    for (a, b), (c, e) in zip(tops, tops[1:]):
        for o in (-30, 0, 30):
            pts = [(a + (c - a) * t + o, b + (e - b) * t + 14 * np.sin(np.pi * t)) for t in np.linspace(0, 1, 20)]
            d.line(pts, fill=(40, 44, 40, 200), width=1)
    # world-edge haze over the baked sprites as well
    haze = np.array(out).astype(float)
    haze[..., :3] = haze[..., :3] * (1 - fade[..., None] * .85) + bg * fade[..., None] * .85
    return Image.fromarray(np.clip(haze, 0, 255).astype(np.uint8), 'RGBA')
