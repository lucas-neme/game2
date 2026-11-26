"""V5 harmonized NPCs -> production sheets + manifest + /*V5:BEGIN*/ block in index.html.
    python tools/asset-pipeline/v5_build.py [--preview out.png]
Frames keep their source pixels (no stretching): padded into one canvas per NPC, feet on a common baseline,
horizontally centred on the upper-body column (stable heads while walking). Drawn chairs are removed from the
sit frames (wood-coloured pixels behind the back and under the hips) so the game's own seat is used."""
import json, re, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image
import v5_npcs as V, v5_map as M
from common import ROOT, PROD

FACES = {'lia': 'right', 'raul': 'left', 'nora': 'left', 'helena': 'right', 'bento': 'left', 'celina': 'right'}

def strip_chair(im, face):
    a = np.array(im).astype(int); m = a[..., 3] > 0; H, W = m.shape
    rgb = a[..., :3]; R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    wood = m & (R > 70) & (R < 205) & (R - G > 32) & (G - B > 8) & (B < 95) & ((R + G + B) < 420)
    ys, xs = np.nonzero(m)
    top = ys.min(); h = ys.max() - top + 1
    up = m[top:top + int(h * .45)]; ux = np.nonzero(up.any(0))[0]; c0, c1 = ux.min(), ux.max()
    yy, xx = np.mgrid[0:H, 0:W]
    behind = (xx < c0 + (c1 - c0) * .2) if face == 'right' else (xx > c0 + (c1 - c0) * .8)
    low = yy > top + h * .62
    kill = wood & (behind | low)
    a[..., 3] = np.where(kill, 0, a[..., 3])
    out = Image.fromarray(a.astype(np.uint8)); mm = V.main_component(np.array(out)[..., 3] > 0)
    b = np.array(out); b[..., 3] = np.where(mm, b[..., 3], 0); out = Image.fromarray(b)
    return out.crop(out.getbbox())

def body_center(im):
    m = np.array(im)[..., 3] > 0; ys, xs = np.nonzero(m); top = ys.min(); h = ys.max() - top + 1
    band = m[top + int(h * .15):top + int(h * .55)]; cols = np.nonzero(band.any(0))[0]
    w = band.sum(0)[cols]; return float((cols * w).sum() / w.sum())

def build_npc(n):
    mf = json.loads((V.V5 / n / 'manifest.json').read_text(encoding='utf-8')); src = Image.open(V.V5 / n / 'source.png')
    idx = {(f['row'], f['index']): f['rect'] for f in mf['frames']}
    seqs = {}; dropped = []
    for key, frames in M.SEQ[n].items():
        ims = []
        for rc in frames:
            im, bb = V.cut(src, idx[rc]);
            if not bb: dropped.append((key, rc, 'empty')); continue
            im = im.crop(bb)
            if key in ('sit', 'stand'): im = strip_chair(im, FACES[n])
            ims.append((rc, im))
        hs = np.median([im.height for _, im in ims]); ws = np.median([im.width for _, im in ims])
        keep = []
        for rc, im in ims:
            if im.height > hs * 1.12 or im.width > ws * 1.45: dropped.append((key, rc, 'scale/cut outlier')); continue
            keep.append((rc, im))
        seqs[key] = keep
    ref = np.median([im.height for _, im in seqs['idle:south']])
    FW = int(max(im.width for s in seqs.values() for _, im in s) * 1.3) + 8; FH = int(max(im.height for s in seqs.values() for _, im in s)) + 6
    AX, AY = FW // 2, FH - 3
    rows = []; meta = {}
    for key, lst in seqs.items():
        strip = Image.new('RGBA', (FW * max(1, len(lst)), FH))
        for i, (rc, im) in enumerate(lst):
            cx = body_center(im); strip.alpha_composite(im, (int(round(i * FW + AX - cx)), AY - im.height + 1))
        mh = float(np.median([im.height for _, im in lst])) if lst else ref
        k = 1.0 if key in ('sit', 'stand') or abs(ref / mh - 1) < .08 else round(ref / mh, 3)
        meta[key] = {'row': len(rows), 'frames': len(lst), 'k': k, 'src': [f'{a}.{b}' for (a, b), _ in lst]}; rows.append(strip)
    sheet = Image.new('RGBA', (max(r.width for r in rows), FH * len(rows)))
    for i, r in enumerate(rows): sheet.alpha_composite(r, (0, i * FH))
    return sheet, {'fw': FW, 'fh': FH, 'ax': AX, 'ay': AY, 'ref_h': float(ref), 'face': FACES[n], 'anims': meta}, dropped

def hero_height():
    WV2 = ROOT / 'assets' / 'source' / 'protagonista-walk-v2' / 'game' / 'south' / 'walk_01.png'
    m = np.array(Image.open(WV2))[..., 3] > 0; ys = np.nonzero(m.any(1))[0]; return int(ys.max() - ys.min() + 1)

def main():
    out = PROD / 'characters' / 'v5'; out.mkdir(parents=True, exist_ok=True)
    hh = hero_height(); data = {}; man = {'source': 'fz-harmonizado-v5-completo.zip', 'hero_reference_height_px': hh, 'hero_draw_scale': .5, 'npcs': {}}
    sheets = {}
    for n in M.SEQ:
        sheet, meta, dropped = build_npc(n)
        fn = f'assets/production/characters/v5/{n}.png'; sheet.save(ROOT / fn, optimize=True); sheets[n] = sheet
        scale = round(.5 * hh * M.HEIGHT[n] / meta['ref_h'], 4)
        data[n] = {**meta, 'file': fn, 'scale': scale}
        man['npcs'][n] = {'file': fn, 'sha256': hashlib.sha256((ROOT / fn).read_bytes()).hexdigest(), 'frame': [meta['fw'], meta['fh']], 'anchor': [meta['ax'], meta['ay']],
                          'draw_scale': scale, 'relative_height': M.HEIGHT[n], 'drawn_side': meta['face'], 'animations': {k: {'frames': v['frames'], 'source_frames': v['src']} for k, v in meta['anims'].items()},
                          'dropped': [f'{k} {a}.{b}: {why}' for k, (a, b), why in dropped], 'missing': M.MISSING[n] + M.MISSING['all'], 'state': 'PRODUCTION'}
    (ROOT / 'assets' / 'manifests' / 'v5.json').write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding='utf-8')
    html = (ROOT / 'index.html').read_text(encoding='utf-8'); js = 'var V5=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'
    if '/*V5:BEGIN*/' in html: html = re.sub(r'/\*V5:BEGIN\*/.*?/\*V5:END\*/', lambda m: '/*V5:BEGIN*/' + js + '/*V5:END*/', html, flags=re.S)
    else: i = html.index('/*ART:END*/') + len('/*ART:END*/'); html = html[:i] + '/*V5:BEGIN*/' + js + '/*V5:END*/' + html[i:]
    (ROOT / 'index.html').write_text(html, encoding='utf-8', newline='\n')
    if '--preview' in sys.argv:
        p = Path(sys.argv[sys.argv.index('--preview') + 1]); cols = []
        for n, s in sheets.items():
            bg = Image.new('RGBA', s.size, (70, 90, 60, 255)); bg.alpha_composite(s); cols.append(bg)
        W = sum(c.width for c in cols) + 10 * len(cols); H = max(c.height for c in cols); o = Image.new('RGBA', (W, H), (20, 20, 20, 255)); x = 0
        for c in cols: o.alpha_composite(c, (x, 0)); x += c.width + 10
        o.save(p)
    print('v5 npcs', {n: (d['fw'], d['fh'], d['scale'], {k: v['frames'] for k, v in d['anims'].items()}) for n, d in data.items()}, 'hero h', hh)

if __name__ == '__main__':
    main()
