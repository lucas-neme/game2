"""Vegetation in the SBS look: broadleaf trees from clustered, lit foliage (no cones), flowering ipês,
columnar cypress, a dead tree, shrubs, flower beds, grass tufts and reeds."""
import numpy as np
from common import ramp, lit, edge_mask, rgba, contact_shadow, Sprite, vnoise

PALETTES = {
    'oak':     ('1f2814', '34421f', '4f6030', '72803f', '9aa35a'),
    'mango':   ('17230f', '2a3c1a', '425a28', '627a36', '8a9b4e'),
    'ipe':     ('3d2a0e', '7a5a14', 'b98f1f', 'dcb83a', 'f1dc7a'),
    'jacaranda': ('231a2f', '3e2f55', '5f4a7e', '8470a3', 'aa98c4'),
    'dry':     ('2c2617', '4a3f25', '6c5e38', '8f8150', 'aea072'),
    'shrub':   ('1d2913', '31431f', '4b5f2d', '6d7d3e', '919c58'),
}

def _foliage(w, h, clusters, palette, seed, holes=.06, clump=(3.2, 6.0)):
    """Crown = many small leaf clumps scattered inside large volumes. Each clump is a tiny lit dome sitting
    on the macro volume, so the silhouette is leafy and the light reads top-left; colours are posterized to
    the palette steps like the SBS sheets."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    macro = np.zeros((h, w))
    for (cx, cy, rad) in clusters:
        d = ((xx - cx) ** 2 + (yy - cy) ** 2) / rad ** 2
        macro = np.maximum(macro, np.where(d < 1, np.sqrt(np.clip(1 - d, 0, 1)) * rad, 0))
    inside = np.argwhere(macro > 0)
    hgt = np.zeros((h, w)); cid = np.zeros((h, w))
    n = int(len(inside) / 14)
    pick = inside[r.integers(0, len(inside), n)]
    for i, (py, px) in enumerate(pick):
        rad = r.uniform(*clump)
        y0, y1 = int(max(0, py - rad - 1)), int(min(h, py + rad + 2)); x0, x1 = int(max(0, px - rad - 1)), int(min(w, px + rad + 2))
        sy, sx = yy[y0:y1, x0:x1], xx[y0:y1, x0:x1]
        d = ((sx - px) ** 2 + (sy - py) ** 2) / rad ** 2
        dome = np.where(d < 1, np.sqrt(np.clip(1 - d, 0, 1)) * rad * .9 + macro[py, px], 0)
        sub = hgt[y0:y1, x0:x1]; better = dome > sub
        sub[better] = dome[better]; cid[y0:y1, x0:x1][better] = i
    m = hgt > 0
    m &= ~((r.random((h, w)) < holes * .3) & (hgt - macro < .5) & (macro > 4))
    micro = lit(hgt, 1.0)
    # macro light: where on the crown the clump sits (top-left bright, bottom-right in shadow)
    ys, xs = np.nonzero(m)
    if len(ys):
        u = (xx - xs.mean()) / (np.ptp(xs) / 2 + 1); v = (yy - ys.mean()) / (np.ptp(ys) / 2 + 1)
    else:
        u = v = np.zeros((h, w))
    macro_l = np.clip(.55 - .28 * u - .38 * v, 0, 1)
    crevice = np.clip((hgt - macro) / 3.0, 0, 1)
    t = micro * .45 + macro_l * .55
    t = t * (.55 + .45 * crevice)
    t = np.round(t * 6) / 6 + (r.random((h, w)) - .5) * .06
    rgb = ramp(palette, t)
    e = edge_mask(m); rgb[e] *= .5
    return rgb, m

def broadleaf(name, kind='oak', w=96, h=128, seed=0, trunk_h=34, spread=1.0, crown_y=None, lean=0):
    r = np.random.default_rng(seed)
    cx = w / 2 + lean; base_y = h - 10
    cy = crown_y or (base_y - trunk_h - 30)
    clusters = [(cx + r.normal(0, 4), cy, 26 * spread)]
    for k in range(9):
        a = r.uniform(0, 2 * np.pi); d = r.uniform(.35, 1.0)
        clusters.append((cx + np.cos(a) * 28 * spread * d, cy + np.sin(a) * 18 * d - 4, r.uniform(12, 19) * spread))
    for k in range(6):
        a = r.uniform(np.pi * 1.05, np.pi * 1.95)
        clusters.append((cx + np.cos(a) * 20 * spread, cy + np.sin(a) * 22 - 6, r.uniform(10, 15) * spread))
    rgb, m = _foliage(w, h, clusters, PALETTES[kind], seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    # tapered trunk with root flare, plus three limbs reaching into the crown (visible through gaps)
    off = (yy - base_y) * lean / 60
    half = 3.2 + np.clip((base_y - 6 - yy), -6, 0) * -.9 + np.clip((base_y - yy) / (base_y - cy), 0, 1) * -1.2
    trunk = (np.abs(xx - cx - off) < half) & (yy > cy + 4) & (yy < base_y + 1)
    for sgn, ln in ((-1, 18), (1, 16), (0, 0)):
        if not ln: continue
        t = np.clip((cy + 22 - yy) / 26, 0, 1)
        limb = (np.abs(xx - (cx + sgn * t * ln)) < 2.4 - t * 1.2) & (yy > cy - 6) & (yy < cy + 24)
        trunk |= limb
    behind = trunk & m
    trunk_vis = trunk & ~m
    side = np.clip((xx - (cx + off) + 4) / 8, 0, 1)
    bark = ramp(('1e1510', '3b2a1f', '5d4635', '7f6650'), 1 - side * .9 + (vnoise((h, w), 1.5, seed + 9) - .5) * .35)
    rgb = np.where(trunk_vis[..., None], bark, rgb)
    trunk = trunk_vis
    e = edge_mask(trunk | m) & trunk; rgb[e] *= .6
    solid = m | trunk
    e = edge_mask(trunk) & trunk; rgb[e] *= .6
    sh = contact_shadow(w, h, cx + 6, base_y, 30 * spread, 9, 105)
    alpha = np.where(solid, 255, sh)
    rgb = np.where(solid[..., None], rgb, 0)
    return Sprite(name, rgba(rgb, alpha), (cx, base_y), 'vegetation', collision='cell')

def cypress(name, w=48, h=128, seed=0):
    r = np.random.default_rng(seed)
    cx = w / 2; base = h - 10
    clusters = [(cx + r.normal(0, 2), base - 18 - k * 9, 11 - abs(k - 4) * .9 + r.uniform(-1, 1)) for k in range(11)]
    rgb, m = _foliage(w, h, clusters, PALETTES['mango'], seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    trunk = (np.abs(xx - cx) < 2.5) & (yy > base - 14) & (yy < base) & ~m
    rgb[trunk] = ramp(('2b1f16', '5a4331'), .5)
    solid = m | trunk
    sh = contact_shadow(w, h, cx + 4, base, 15, 6)
    return Sprite(name, rgba(np.where(solid[..., None], rgb, 0), np.where(solid, 255, sh)), (cx, base), 'vegetation', collision='cell')

def dead_tree(name, w=96, h=120, seed=0):
    from PIL import Image, ImageDraw
    r = np.random.default_rng(seed)
    im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    base = (w // 2, h - 10)
    def branch(x, y, ang, ln, wd, depth):
        if depth == 0 or ln < 5: return
        x2 = x + np.cos(ang) * ln; y2 = y - np.sin(ang) * ln
        d.line([(x, y), (x2, y2)], fill=(58 + depth * 6, 46 + depth * 5, 36 + depth * 4), width=max(1, int(wd)))
        for s in (-1, 1):
            branch(x2, y2, ang + s * r.uniform(.3, .7), ln * r.uniform(.55, .75), wd * .65, depth - 1)
    branch(*base, np.pi / 2 + r.uniform(-.08, .08), 40, 7, 6)
    a = np.array(im).astype(float)
    sh = contact_shadow(w, h, base[0] + 6, base[1], 24, 7)
    solid = a[..., 3] > 0
    a[..., 3] = np.where(solid, 255, sh)
    return Sprite(name, rgba(a[..., :3], a[..., 3]), base, 'vegetation', collision='cell')

def shrub(name, kind='shrub', w=56, h=48, seed=0, flowers=None):
    r = np.random.default_rng(seed)
    cx = w / 2; base = h - 8
    clusters = [(cx + r.normal(0, 9), base - 14 + r.normal(0, 3), r.uniform(9, 13)) for _ in range(7)]
    rgb, m = _foliage(w, h, clusters, PALETTES[kind], seed)
    if flowers:
        pts = r.random((h, w)) > .955
        fl = pts & m & (np.roll(m, 2, 0))
        from common import hexc
        rgb[fl] = hexc(flowers) * (0.85 + .3 * r.random((fl.sum(), 1)))
    sh = contact_shadow(w, h, cx + 4, base + 1, w * .42, 7)
    return Sprite(name, rgba(np.where(m[..., None], rgb, 0), np.where(m, 255, sh)), (cx, base), 'vegetation')

def grass_tuft(name, w=32, h=24, seed=0, color=('3d4a22', '6c7a3a', 'a2a463')):
    from PIL import Image, ImageDraw
    r = np.random.default_rng(seed); im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    for _ in range(18):
        x = r.uniform(5, w - 5); top = r.uniform(3, h - 10); c = ramp(color, r.random())
        d.line([(x, h - 4), (x + r.uniform(-4, 4), top)], fill=tuple(int(v) for v in c) + (255,))
    return Sprite(name, im, (w // 2, h - 4), 'vegetation')

def reeds(name, w=40, h=48, seed=0):
    from PIL import Image, ImageDraw
    r = np.random.default_rng(seed); im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    for _ in range(16):
        x = r.uniform(6, w - 6); top = r.uniform(4, 22); c = ramp(('4b5426', '7b8a43', 'a9ad6a'), r.random())
        d.line([(x, h - 5), (x + r.uniform(-3, 3), top)], fill=tuple(int(v) for v in c) + (255,), width=1)
        if r.random() < .35: d.line([(x, top), (x, top + 5)], fill=(88, 60, 36, 255), width=2)
    return Sprite(name, im, (w // 2, h - 5), 'vegetation')

def all_vegetation():
    return [
        broadleaf('tree-oak-a', 'oak', seed=11), broadleaf('tree-oak-b', 'oak', seed=12, spread=1.08, lean=-3),
        broadleaf('tree-mango', 'mango', 104, 120, seed=13, trunk_h=26, spread=1.15),
        broadleaf('tree-ipe', 'ipe', seed=14, spread=.95), broadleaf('tree-jacaranda', 'jacaranda', seed=15, spread=.98, lean=2),
        broadleaf('tree-dry', 'dry', 88, 116, seed=16, spread=.85),
        cypress('tree-cypress', seed=17), dead_tree('tree-dead', seed=18),
        shrub('shrub-a', seed=21), shrub('shrub-b', seed=22, w=48, h=40),
        shrub('shrub-flower-red', seed=23, flowers='c0503c'), shrub('shrub-flower-white', seed=24, flowers='e8e2cf'),
        grass_tuft('grass-a', seed=31), grass_tuft('grass-b', seed=32, color=('4a4a24', '7c7a3e', 'b0a86a')),
        reeds('reeds-a', seed=33),
    ]
