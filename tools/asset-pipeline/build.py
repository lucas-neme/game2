"""Frequência Zero asset pipeline.

    python tools/asset-pipeline/build.py <sbs_-_isometric_town_pack.zip> [--postcard out.png]

Produces assets/production/{environment,characters,lighting}/ atlases + assets/manifests/production.json and
rewrites the generated block between /*ART:BEGIN*/ and /*ART:END*/ in index.html (sprite table, layout,
collisions). See docs/art-direction/ART_DIRECTION.md.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from PIL import Image
import numpy as np
import buildings, nature, props, layout, ground
from common import ROOT, PROD

def collect(zip_path):
    pack = buildings.Pack(zip_path)
    sp = {}
    for s in buildings.all_buildings(pack) + nature.all_vegetation() + props.all_props():
        sp[s.name] = s
    return pack, sp

def placements():
    """Everything drawn by the engine in the playable area: (sprite, gx, gy, depth_bias)."""
    out = []
    for site, (x, y) in layout.SITES.items():
        out.append((layout.SITE_SPRITE[site], x, y, 0, site))
        if site in layout.SITE_SIGN: out.append((layout.SITE_SIGN[site], x, y, .01, 'sign'))
    for s, x, y, sign in layout.DECOR_BUILDINGS:
        out.append((s, x, y, 0, None))
        if sign: out.append((sign, x, y, .01, 'sign'))
    for s, x, y in layout.DECOR_BLOCK: out.append((s, x, y, 0, None))
    for s, x, y, dx, dy in layout.PROPS: out.append((s, x + dx / 3, y + dy / 3, 0, None))
    return out

def screen_pos(sp, gx, gy, kind):
    cx, cy = ground.iso(gx, gy)
    if kind == 'sign':  # on the building's +y (left) face, 2.2 m up
        return cx - 32 - sp.anchor[0], cy + 16 - 47 - sp.anchor[1]
    return cx - sp.anchor[0], cy - sp.anchor[1]

def postcard(sprites, base, night=False):
    im = base.copy()
    items = sorted(placements(), key=lambda p: (p[1] + p[2] + p[3]))
    for name, gx, gy, bias, kind in items:
        sp = sprites.get(name)
        if not sp: print('missing sprite', name); continue
        x, y = screen_pos(sp, gx, gy, kind)
        im.alpha_composite(sp.im, (int(x), int(y)))
    return im

def main():
    zip_path = sys.argv[1]
    errs = layout.validate(ROOT / 'index.html')
    if errs: raise SystemExit('layout errors:\n' + '\n'.join(errs))
    pack, sprites = collect(zip_path)
    base = ground.render_ground(sprites)
    if '--postcard' in sys.argv:
        out = Path(sys.argv[sys.argv.index('--postcard') + 1])
        pc = postcard(sprites, base)
        pc.save(out); print('postcard', out, pc.size)
        return
    import export
    export.export(sprites, base, pack, placements())

if __name__ == '__main__':
    main()
