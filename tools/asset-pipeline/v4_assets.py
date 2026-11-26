"""V4 pack (monsters, items, puzzles): cleanup and slicing. Source pixels only; nothing is redrawn.
Creature strips are cut at the emptiest columns near the nominal frame boundaries (frame count from the manifest),
then each cell loses the board background, the thin cell borders and stray fragments."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
import canon_catalog as K

V4 = Path(r'D:/Projetos/game2-insumos/v4')

def board_alpha(a):
    rgb = a[..., :3].astype(int); mx = rgb.max(-1); mn = rgb.min(-1)
    core = (mx >= 95) | (mx - mn >= 55)
    near = core.copy()
    for _ in range(2):
        g = near.copy(); g[1:] |= near[:-1]; g[:-1] |= near[1:]; g[:, 1:] |= near[:, :-1]; g[:, :-1] |= near[:, 1:]; near = g
    bg = (mx < 60) & (mx - mn < 34) & (rgb[..., 2] >= rgb[..., 0] - 8)
    return near & ~bg

def strip_borders(m):
    """Remove the thin rounded cell frames of the sheet: long, 1-2 px wide vertical/horizontal runs."""
    H, W = m.shape; m = m.copy()
    for x in range(W):
        col = m[:, x]
        if col.sum() > H * .6 and (x == 0 or m[:, x - 1].sum() < H * .3) and (x == W - 1 or m[:, x + 1].sum() < H * .3): m[:, x] = False
    for y in range(H):
        row = m[y]
        if row.sum() > W * .6 and (y == 0 or m[y - 1].sum() < W * .3) and (y == H - 1 or m[y + 1].sum() < W * .3): m[y] = False
    return m

def clean_cell(arr, keep=.06):
    a = arr.copy(); m = strip_borders(board_alpha(a)); a[..., 3] = np.where(m, 255, 0)
    im = K.keep_main(Image.fromarray(a.astype(np.uint8), 'RGBA'), keep)
    return im

def slice_strip(path, n, keep=.15):
    a = np.array(Image.open(path).convert('RGBA'))
    a[-4:] = 0; a[:, :3] = 0; a[:, -3:] = 0          # rounded cell frame of the sheet
    H, W = a.shape[:2]; m = strip_borders(board_alpha(a)); occ = m.sum(0)
    cuts = [0]
    for k in range(1, n):
        c = int(round(k * W / n)); r = max(2, W // (3 * n))
        lo, hi = max(cuts[-1] + 4, c - r), min(W - 4, c + r)
        cuts.append(lo + int(np.argmin(occ[lo:hi + 1])) if hi > lo else c)
    cuts.append(W)
    return [clean_cell(a[:, cuts[i]:cuts[i + 1]], keep) for i in range(n)]

def creature_anims():
    m = json.loads((V4 / 'monstros' / 'manifest.json').read_text(encoding='utf-8'))['assets']
    counts = {}
    for f in m:
        if f['kind'] == 'frame': counts[(f['creature'], f['action'])] = max(counts.get((f['creature'], f['action']), 0), f['index'])
    out = {}
    for s in m:
        if s['kind'] != 'faixa': continue
        cr, act = s['id'][:-len('_faixa')].rsplit('_', 1)
        n = counts.get((cr, act))
        if not n: continue
        out.setdefault(cr, {})[act] = slice_strip(V4 / 'monstros' / s['file'], n, .03 if act == 'dissipacao' else .15)
    return out

def single_sprites():
    m = json.loads((V4 / 'monstros' / 'manifest.json').read_text(encoding='utf-8'))['assets']
    out = {}
    for s in m:
        if s['kind'] in ('sprite', 'retrato'):
            src = V4 / 'monstros' / s['file']
            out[s['id']] = clean_cell(np.array(Image.open(src).convert('RGBA')))
    return out

def items():
    m = json.loads((V4 / 'inventario' / 'manifest.json').read_text(encoding='utf-8'))['assets']
    out = {}
    for s in m:
        a = np.array(Image.open(V4 / 'inventario' / s['alpha_candidate']).convert('RGBA'))
        m_ = strip_borders(a[..., 3] > 0); a[..., 3] = np.where(m_, a[..., 3], 0)
        im = K.keep_main(Image.fromarray(a), .12)
        # labels under the icons are small separate text blobs: keep_main drops most; crop to the largest blob's rows
        out[s['id']] = im
    return out

def panels():
    m = json.loads((V4 / 'enigmas' / 'manifest.json').read_text(encoding='utf-8'))['assets']
    return {s['id']: Image.open(V4 / 'enigmas' / s['file']).convert('RGBA') for s in m}
