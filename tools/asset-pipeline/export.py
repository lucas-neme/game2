"""Export step: atlases, ground, characters, effects, manifest, licences and the generated ART block in index.html."""
import json, re
from datetime import date
import numpy as np
from PIL import Image
from common import ROOT, PROD, vnoise
import layout, ground

def pack_atlases(items, max_w=2048, max_h=2048, pad=2):
    """Shelf packer (tallest first). Returns [(Image, {name: (x, y, w, h)})]."""
    items = sorted(items, key=lambda s: (-s.im.height, -s.im.width))
    by_name = {s.name: s for s in items}
    atlases = [{'shelves': [], 'y': 0, 'rects': {}}]
    for s in items:
        cur = atlases[-1]; w, h = s.im.width + pad, s.im.height + pad
        for sh in cur['shelves']:
            if sh['h'] >= h and sh['x'] + w <= max_w:
                cur['rects'][s.name] = (sh['x'], sh['y'], s.im.width, s.im.height); sh['x'] += w; break
        else:
            if cur['y'] + h > max_h:
                cur = {'shelves': [], 'y': 0, 'rects': {}}; atlases.append(cur)
            cur['shelves'].append({'x': w, 'y': cur['y'], 'h': h})
            cur['rects'][s.name] = (0, cur['y'], s.im.width, s.im.height); cur['y'] += h
    out = []
    for a in atlases:
        W = max(sh['x'] for sh in a['shelves'])
        im = Image.new('RGBA', (W, a['y']))
        for name, (x, y, w, h) in a['rects'].items(): im.paste(by_name[name].im, (x, y))
        out.append((im, a['rects']))
    return out

def fog_texture(size=512, seed=7):
    """Tileable soft fog: periodic noise built from integer-frequency sines with random phases."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size] / size * 2 * np.pi
    t = np.zeros((size, size))
    for k in range(40):
        fx, fy = r.integers(1, 7), r.integers(1, 7); amp = 1 / (fx + fy)
        t += amp * np.sin(fx * xx + fy * yy * (1 if r.random() < .5 else -1) + r.uniform(0, 6.3))
    t = (t - t.min()) / (t.max() - t.min())
    al = np.clip((t - .38) * 1.7, 0, 1) * 160
    rgb = np.full((size, size, 3), 214.0)
    return Image.fromarray(np.dstack([rgb, al]).astype(np.uint8), 'RGBA')

def export(sprites, base, pack, placements):
    env_dir = PROD / 'environment'; ch_dir = PROD / 'characters'; fx_dir = PROD / 'effects'; man_dir = ROOT / 'assets' / 'manifests'
    for d in (env_dir, ch_dir, fx_dir, man_dir): d.mkdir(parents=True, exist_ok=True)
    base.convert('RGB').save(env_dir / 'ground.webp', quality=88, method=6)
    env = [s for s in sprites.values() if s.category != 'characters']
    atl = pack_atlases(env)
    table, files = {}, []
    for i, (im, rects) in enumerate(atl):
        fn = f'assets/production/environment/atlas-{i}.png'; im.save(ROOT / fn, optimize=True); files.append(fn)
        for name, r in rects.items():
            s = sprites[name]
            table[name] = {'atlas': i, 'rect': list(r), 'anchor': [s.anchor[0], s.anchor[1]], 'category': s.category,
                           'collision': s.collision, 'source': s.source}
    import characters
    chars = {}
    for s in characters.all_characters():
        fn = f'assets/production/characters/{s.name}.png'; s.im.save(ROOT / fn, optimize=True)
        chars[s.name[3:]] = {'file': fn, 'fw': s.meta['frame'][0], 'fh': s.meta['frame'][1], 'ax': s.anchor[0], 'ay': s.anchor[1], 'anims': s.meta['anims']}
    fog_texture().save(fx_dir / 'fog.png', optimize=True)
    import interiors
    int_dir = PROD / 'interiors'; int_dir.mkdir(parents=True, exist_ok=True)
    hotspots = {}
    for key, fn in (('study', interiors.study), ('station', interiors.station_hall)):
        im, pins = fn(); im.convert('RGB').save(int_dir / f'{key}.webp', quality=90, method=6); hotspots.update(pins)
    names = list(table); idx = {n: i for i, n in enumerate(names)}
    place = [[idx[n], round(gx, 3), round(gy, 3), bias, kind or 0] for n, gx, gy, bias, kind in placements]
    iso = ground.iso
    world = {'ox': ground.OX, 'oy': ground.OY, 'w': ground.W, 'h': ground.H, 'tile': [128, 64],
             'cam': [iso(-2, 15)[0], iso(-2, -2)[1] - 170, iso(15, -2)[0], iso(15, 15)[1] + 80]}
    lights = [[round(x + dx / 3, 3), round(y + dy / 3, 3), z, r, k] for (x, y, dx, dy, z, r, k) in layout.LIGHTS]
    blocked = sorted(f'{x},{y}' for (x, y) in layout.blocked_cells())
    lake = [iso(10.5, 8.5), iso(18.5, 8.5), iso(18.5, 18.5), iso(10.5, 18.5)]
    night = {k: idx['n-' + v[2:]] for k, v in layout.SITE_SPRITE.items()}
    night.update({f'{x},{y}': idx['n-' + s[2:]] for s, x, y, _ in layout.DECOR_BUILDINGS})
    data = {'v': 1, 'world': world, 'ground': 'assets/production/environment/ground.webp', 'atlases': files,
            'fog': 'assets/production/effects/fog.png', 'names': names,
            'sprites': [[table[n]['atlas'], *table[n]['rect'], *table[n]['anchor']] for n in names],
            'place': place, 'sites': {k: idx[v] for k, v in layout.SITE_SPRITE.items()}, 'night': night,
            'blocked': blocked, 'lights': lights, 'lake': [[round(a), round(b)] for a, b in lake], 'chars': chars}
    manifest = {'version': 1, 'generated': str(date.today()),
                'scale': {'terrain': [128, 64], 'wall_module': [64, 96], 'roof': [143, 92], 'character_frame': [64, 96], 'metre_px': 64 / 3},
                'licenses': {'sbs': 'assets/licenses/SBS-Isometric-Town-Pack-CC0.txt', 'original': 'assets/licenses/FREQUENCIA-ZERO-ORIGINAL.txt'},
                'world': world, 'ground': data['ground'], 'atlases': files, 'sprites': table, 'characters': chars,
                'layout': {'placements': len(place), 'blocked': blocked, 'lights': len(lights)}}
    (man_dir / 'production.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
    lic = ROOT / 'assets' / 'licenses'; lic.mkdir(exist_ok=True)
    (lic / 'SBS-Isometric-Town-Pack-CC0.txt').write_text(
        'SBS - Isometric Town Pack, Screaming Brain Studios.\n' + pack.license.strip() +
        '\nUsed: building wall modules (64x96) and roofs (143x92). The exact tiles of each building are listed in\n'
        'assets/manifests/production.json (field "source").\n', encoding='utf-8')
    (lic / 'FREQUENCIA-ZERO-ORIGINAL.txt').write_text(
        'Ground, vegetation, props, signs, characters and effects in assets/production are original work generated by\n'
        'tools/asset-pipeline for Frequência Zero. Buildings combine original composition with the CC0 SBS tiles.\n', encoding='utf-8')
    js = 'const ART=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    if '/*ART:BEGIN*/' not in html: raise SystemExit('index.html has no /*ART:BEGIN*/ marker')
    for label, (x, y) in hotspots.items():
        html, n = re.subn(r"\['" + re.escape(label) + r"',[0-9.]+,[0-9.]+,", f"['{label}',{x},{y},", html)
        if n != 1: raise SystemExit(f'hotspot {label!r} not found once in index.html ({n})')
    html = re.sub(r'/\*ART:BEGIN\*/.*?/\*ART:END\*/', lambda m: '/*ART:BEGIN*/' + js + '/*ART:END*/', html, flags=re.S)
    (ROOT / 'index.html').write_text(html, encoding='utf-8', newline='\n')
    print('atlases', [(f, Image.open(ROOT / f).size) for f in files], '| sprites', len(names), '| placements', len(place), '| chars', list(chars))
