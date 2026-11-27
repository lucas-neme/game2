"""V6 characters (fz-personagens-v6-morte-review) -> individual frames, production atlases and runtime data.

    python tools/asset-pipeline/v6_build.py [--frames-only]

Source sheets (REVIEW, never modified): assets/review/chatgpt-import/fz-personagens-v6-morte-review/characters/<c>/
  actions.png  idle (4 views x 4), walk (4 views x up to 8), talk (3 views x 4), sit-down / seated / stand-up with a
               drawn bench or chair
  death.png    4 rows (south, north, side, side) x 6 poses: stagger, stagger, kneel, kneel, fall, lying

Steps
 1. segment by projection (v6_segment.py), classify every sequence (view/facing from the visible skin, furniture,
    length, order: first short sequence of a view = idle, later ones = talk);
 2. clean alpha without touching interior pixels (only the largest component and the pieces that touch it are kept);
 3. remove the drawn furniture from sit frames: colours that never occur in the character's standing frames are
    furniture; the furniture outline left behind is peeled; the game draws its own bench;
 4. export every frame individually to assets/source/v6/<c>/<anim>/<dir>/NN.png (GitHub-browsable) and one atlas per
    character to assets/production/characters/v6/<c>.png with its manifest (assets/manifests/v6.json).
"""
import json, sys, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
import v6_segment as SEG
import v5_npcs as V

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'assets/review/chatgpt-import/fz-personagens-v6-morte-review'
FRAMES = ROOT / 'assets/source/v6'
PROD = ROOT / 'assets/production/characters/v6'
# rows with the drawn bench/chair, counted from the end of each actions sheet (checked visually)
FURNITURE_ROWS = {'hero': 1, 'lia': 2, 'raul': 2, 'nora': 2, 'helena': 1, 'bento': 1, 'celina': 1}
NAMES = ['hero', 'lia', 'raul', 'nora', 'helena', 'bento', 'celina']


def crop(a, box, pad=2):
    x0, y0, x1, y1 = box
    sub = a[max(0, y0 - pad):y1 + pad + 1, max(0, x0 - pad):x1 + pad + 1].copy()
    return sub


def clean(sub):
    """Binary alpha; keep the main body and the pieces close to it; interior pixels are never dropped."""
    al = sub[..., 3] > 40
    keep = V.main_component(al)
    out = sub.copy(); out[..., 3] = np.where(keep, 255, 0); out[~keep, :3] = 0
    return out


def furniture_rows(a, rows):
    """A row has furniture when its frames are much wider than tall-normal or show the wood palette in the lower band."""
    res = []
    for r in rows:
        y0, y1 = r['y']; band = a[y0:y1 + 1]
        lower = band[int((y1 - y0) * .55):]
        rgb = lower[..., :3].astype(int); m = lower[..., 3] > 40
        R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        wood = m & (R > 95) & (R - B > 55) & (R - G > 25)
        res.append(wood.sum() / max(1, m.sum()) > .12)
    return res


def furniture_groups(a, r, alpha=40):
    """Sit rows: groups separated by wide gaps, 4 frames each (cells of equal width inside a group)."""
    y0, y1 = r['y']; m = a[y0:y1 + 1, :, 3] > alpha
    gr = SEG.runs(m.any(0), 14)
    widths = [g[1] - g[0] + 1 for g in gr]; base = min(widths) / 4 if widths else 1
    groups = []
    for (x0, x1), w in zip(gr, widths):
        n = max(1, int(round(w / base)))
        n = 4 * max(1, int(round(n / 4)))
        cells = []
        for j in range(n):
            cx0 = x0 + int(w * j / n); cx1 = x0 + int(w * (j + 1) / n) - 1
            sub = m[:, cx0:cx1 + 1]; ys = np.nonzero(sub.any(1))[0]
            if len(ys): cells.append((cx0, y0 + ys.min(), cx1, y0 + ys.max()))
        groups.append(cells)
    return groups


def bins(f):
    """Colour bin per opaque pixel (HSV-like: 6 bits)."""
    rgb = f[..., :3].astype(int) // 32
    return rgb[..., 0] * 64 + rgb[..., 1] * 8 + rgb[..., 2]


def hist(frames):
    h = np.zeros(512)
    for f in frames:
        b = bins(f)[f[..., 3] > 0]; h += np.bincount(b, minlength=512)
    return h / max(1, h.sum())


def furniture_sample(f):
    """Pixels that can only be furniture: lower 40% of a seated frame, away from the body column."""
    m = f[..., 3] > 0; ys, xs = np.nonzero(m)
    if not len(ys): return np.zeros_like(m)
    top, h = ys.min(), ys.max() - ys.min() + 1
    up = m[top:top + int(h * .4)]; cols = np.nonzero(up.any(0))[0]
    c0, c1 = cols.min(), cols.max(); pad = int((c1 - c0) * .15)
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    return m & (yy > top + h * .6) & ((xx < c0 - pad) | (xx > c1 + pad))


def palette(standing, sitting):
    """P(colour | furniture sample) / P(colour | standing character): high = furniture."""
    hs = hist(standing)
    hf = np.zeros(512)
    for f in sitting:
        smp = furniture_sample(f); hf += np.bincount(bins(f)[smp], minlength=512)
    hf = hf / max(1, hf.sum())
    return hf / (hs + 5e-4)


def strip_furniture(f, pal):
    a = f.copy(); m = a[..., 3] > 0; H, W = m.shape
    alien = m & (pal[bins(a)] > 4)
    # furniture outline / shadow left around removed regions: peel dark pixels with no body colour next to them
    dark = m & (a[..., :3].max(-1) < 70)
    kill = alien.copy()
    for _ in range(3):
        nb = np.zeros_like(kill)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nb |= np.roll(np.roll(kill, dy, 0), dx, 1)
        body = m & ~kill & ~dark
        nbody = np.zeros_like(body)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nbody |= np.roll(np.roll(body, dy, 0), dx, 1)
        kill |= dark & nb & ~nbody
    a[..., 3] = np.where(kill, 0, a[..., 3])
    keep = V.main_component(a[..., 3] > 0)
    a[..., 3] = np.where(keep, a[..., 3], 0); a[a[..., 3] == 0, :3] = 0
    return a


def classify_seq(frames):
    feats = [V.features(Image.fromarray(f)) for f in frames]
    feats = [x for x in feats if x]
    if not feats: return None, None
    views = [x['view'] for x in feats]; view = max(set(views), key=views.count)
    facing = None
    if view == 'side':
        fac = [x['facing'] for x in feats if x['facing']]; facing = max(set(fac), key=fac.count) if fac else 'right'
    return view, facing


def extract(name):
    seqs = []  # (kind, view, facing, [frames])
    a, rows = SEG.segment(SRC / 'characters' / name / 'actions.png')
    nf = FURNITURE_ROWS[name]
    normal, sit = rows[:-nf], rows[-nf:]
    SEG.split_wide(a, normal); SEG.split_tall(a, normal)
    rows = normal + sit; furn = [False] * len(normal) + [True] * len(sit)
    sit_sprites = []
    for r, f in zip(rows, furn):
        if f:
            rr = [dict(r, groups=[list(g) for g in r['groups']])]
            SEG.split_wide(a, rr)
            flat = [b for g in rr[0]['groups'] for b in g]
            if len(flat) % 4 or len(flat) > 12:
                flat = [b for g in furniture_groups(a, r) for b in g]
            sit_sprites += flat
            continue
        groups = [h for g in r['groups'] for h in ([g[:len(g) // 2], g[len(g) // 2:]] if len(g) >= 10 else [g])]
        for g in groups:
            seqs.append({'furniture': False, 'frames': [clean(crop(a, b)) for b in g]})
    for i in range(0, min(12, len(sit_sprites)), 4):
        seqs.append({'furniture': True, 'frames': [clean(crop(a, b)) for b in sit_sprites[i:i + 4]]})
    standing = [fr for s in seqs if not s['furniture'] for fr in s['frames']]
    pal = None
    out = []
    plain = [x for x in seqs if not x['furniture']]
    assert len(plain) == len(ORDER), (name, len(plain))
    for (kind, view), x in zip(ORDER, plain):
        out.append(dict(kind=kind, view=view, frames=x['frames']))
    sit_order = ['sit', 'seated', 'stand']; si = 0
    for x in seqs:
        if not x['furniture'] or si >= 3: continue
        frames = x['frames']  # drawn bench/chair kept: the engine hides the map seat while occupied
        out.append(dict(kind=sit_order[si], view='side', frames=frames)); si += 1
    d, drows = SEG.segment(SRC / 'characters' / name / 'death.png')
    for i, r in enumerate(drows[:4]):
        frames = [clean(crop(d, b, pad=3)) for g in r['groups'] for b in g]
        out.append(dict(kind='death', view=['south', 'north', 'side', 'side'][i], frames=frames))
    for x in out:
        x['frames'] = [tight(f) for f in x['frames']]
        x['facing'] = seq_facing(x['frames']) if x['view'] == 'side' else None
    return out


ORDER = [('idle', 'south'), ('idle', 'north'), ('idle', 'side'), ('idle', 'side'), ('walk', 'south'), ('walk', 'north'),
         ('walk', 'side'), ('walk', 'side'), ('talk', 'south'), ('talk', 'side'), ('talk', 'side')]


def facing(f):
    """+1 = looks right, -1 = looks left: the skin of the face sits on the side the character looks at."""
    a = f.astype(int); m = a[..., 3] > 0; ys, xs = np.nonzero(m)
    if not len(ys): return 0
    top, h = ys.min(), ys.max() - ys.min() + 1
    band = slice(top + int(h * .06), top + int(h * .34))
    R, G, B = a[band, :, 0], a[band, :, 1], a[band, :, 2]; mb = m[band]
    skin = mb & (R > 140) & (R - B > 35) & (G > 85) & (R - G < 90) & (R >= G)
    cols = np.nonzero(mb.any(0))[0]
    if not skin.sum() or not len(cols): return 0
    cx = (cols.min() + cols.max()) / 2; sx = np.nonzero(skin)[1].mean()
    return (sx - cx) / max(1, (cols.max() - cols.min()) / 2)


def seq_facing(frames):
    v = float(np.mean([facing(f) for f in frames]))
    return 'right' if v >= 0 else 'left'


def tight(f):
    bb = Image.fromarray(f).getbbox()
    return f[bb[1]:bb[3], bb[0]:bb[2]] if bb else f


def resize(f, k):
    if abs(k - 1) < .03: return f
    im = Image.fromarray(f); w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    a = np.array(im.resize((w, h), Image.LANCZOS if k < 1 else Image.NEAREST))
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0); a[a[..., 3] == 0, :3] = 0
    return a


def normalise(seqs):
    """Same body size across sequences: every sequence is scaled to the idle-south standing height; death and sit
    rows by their first (still standing) pose; the seated row uses the sit row's factor."""
    ref = float(np.median([f.shape[0] for f in seqs[0]['frames']]))
    for x in seqs:
        hs = [f.shape[0] for f in x['frames']]
        if x['kind'] == 'seated':
            k = next(y for y in seqs if y['kind'] == 'sit')['k']
        else:
            h = hs[0] if x['kind'] in ('death', 'sit') else (max(hs) if x['kind'] == 'stand' else float(np.median(hs)))
            k = ref / h
        x['k'] = k
        x['frames'] = [resize(f, k) for f in x['frames']]
    return ref


def face_right(x):
    """Side sequences are stored looking right (the engine mirrors for the left)."""
    if x['view'] == 'side' and x['facing'] == 'left':
        x['frames'] = [f[:, ::-1].copy() for f in x['frames']]; x['facing'] = 'right'


def body_center(f):
    m = f[..., 3] > 0; ys, xs = np.nonzero(m); top = ys.min(); h = ys.max() - top + 1
    band = m[top + int(h * .15):top + int(h * .55)]; cols = np.nonzero(band.any(0))[0]
    w = band.sum(0)[cols]; return float((cols * w).sum() / w.sum())


def export_frames(name, seqs):
    base = FRAMES / name; seen = {}
    for x in seqs:
        d = x['view'] if x['view'] != 'side' else 'east'
        key = (x['kind'], d); seen[key] = seen.get(key, 0) + 1
        sub = d if seen[key] == 1 else f'{d}-alt{seen[key] - 1}'
        for i, f in enumerate(x['frames']):
            p = base / x['kind'] / sub / f'{i + 1:02d}.png'
            p.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(f).save(p, optimize=True)


def pick(seqs, kind, view):
    c = [x for x in seqs if x['kind'] == kind and x['view'] == view]
    if not c: return None
    # two side variants exist: keep the one whose frames are the most consistent in height (fewer cut-outs)
    return min(c, key=lambda x: float(np.std([f.shape[0] for f in x['frames']])) - .01 * len(x['frames']))


def atlas(keys):
    """keys: list of (anim key, seq). One row per anim, frames padded to a common cell, feet on a baseline."""
    allf = [f for _, x in keys for f in x['frames']]
    FW = int(max(f.shape[1] for f in allf) * 1.1) + 8; FH = max(f.shape[0] for f in allf) + 6
    AX, AY = FW // 2, FH - 3
    rows, meta = [], {}
    for key, x in keys:
        strip = Image.new('RGBA', (FW * len(x['frames']), FH))
        for i, f in enumerate(x['frames']):
            cx = body_center(f) if x['kind'] != 'death' else body_center(x['frames'][0]) * 0 + f.shape[1] / 2
            strip.alpha_composite(Image.fromarray(f), (int(round(i * FW + AX - cx)), AY - f.shape[0] + 1))
        meta[key] = {'row': len(rows), 'frames': len(x['frames']), 'k': 1}
        rows.append(strip)
    sheet = Image.new('RGBA', (max(r.width for r in rows), FH * len(rows)))
    for i, r in enumerate(rows): sheet.alpha_composite(r, (0, i * FH))
    return sheet, FW, FH, AX, AY, meta


NPC_KEYS = [('idle:south', 'idle', 'south'), ('idle:north', 'idle', 'north'), ('idle:side', 'idle', 'side'),
            ('walk:south', 'walk', 'south'), ('walk:north', 'walk', 'north'), ('walk:side', 'walk', 'side'),
            ('talk:south', 'talk', 'south'), ('talk:side', 'talk', 'side'), ('sit', 'sit', 'side'),
            ('seated', 'seated', 'side'), ('stand', 'stand', 'side'),
            ('death:south', 'death', 'south'), ('death:north', 'death', 'north'), ('death:side', 'death', 'side')]


def hero_v2_height():
    WV2 = ROOT / 'assets/source/protagonista-walk-v2/game/south/walk_01.png'
    m = np.array(Image.open(WV2))[..., 3] > 0; ys = np.nonzero(m.any(1))[0]; return int(ys.max() - ys.min() + 1)


def build():
    import v5_map as M
    hh = hero_v2_height(); PROD.mkdir(parents=True, exist_ok=True)
    data, man = {}, {'source': 'fz-personagens-v6-morte-review.zip', 'hero_v2_height_px': hh, 'npcs': {},
                     'note': 'Side sequences stored looking right (the engine mirrors). Death: 6 poses, play once, hold the last.'}
    for n in NAMES:
        seqs = extract(n)
        for x in seqs: face_right(x)
        ref = normalise(seqs)
        export_frames(n, seqs)
        keys = [(k, pick(seqs, kind, view)) for k, kind, view in NPC_KEYS]
        sheet, FW, FH, AX, AY, meta = atlas(keys)
        fn = f'assets/production/characters/v6/{n}.png'; sheet.save(ROOT / fn, optimize=True)
        rel = 1.0 if n == 'hero' else M.HEIGHT[n]
        scale = round(.5 * hh * rel / ref, 4)
        hs = round(hh / ref, 4)
        data[n] = {'hscale': hs, 'fw': FW, 'fh': FH, 'ax': AX, 'ay': AY, 'ref_h': round(ref, 1), 'face': 'right', 'file': fn, 'scale': scale, 'anims': meta}
        man['npcs'][n] = {'file': fn, 'sha256': hashlib.sha256((ROOT / fn).read_bytes()).hexdigest(), 'frame': [FW, FH],
                          'anchor': [AX, AY], 'draw_scale': scale, 'relative_height': rel, 'drawn_side': 'right',
                          'frames_dir': f'assets/source/v6/{n}/', 'state': 'PRODUCTION',
                          'animations': {k: {'frames': v['frames']} for k, v in meta.items()}}
    (ROOT / 'assets/manifests/v6.json').write_text(json.dumps(man, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    npcs = {k: v for k, v in data.items() if k != 'hero'}
    js = 'var V5=' + json.dumps(npcs, ensure_ascii=False, separators=(',', ':')) + ';var V6H=' + json.dumps(data['hero'], ensure_ascii=False, separators=(',', ':')) + ';'
    import re
    html = re.sub(r'/\*V5:BEGIN\*/.*?/\*V5:END\*/', lambda m: '/*V5:BEGIN*/' + js + '/*V5:END*/', html, count=1, flags=re.S)
    (ROOT / 'index.html').write_text(html, encoding='utf-8', newline=chr(10))
    return data


if __name__ == '__main__':
    data = build()
    for n, d in data.items():
        print(n, d['fw'], d['fh'], d['ref_h'], d['scale'], {k: v['frames'] for k, v in d['anims'].items()})
