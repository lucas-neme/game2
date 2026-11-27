"""V6 sheet segmentation by projection: rows = bands of non-empty scanlines, sprites = runs of non-empty columns
inside a band, groups = runs of sprites separated by wider gaps (a sequence)."""
import numpy as np
from PIL import Image

def runs(v, gap):
    out = []; start = None; last = None
    for i, on in enumerate(v):
        if on:
            if start is None: start = i
            elif i - last > gap + 1: out.append((start, last)); start = i
            last = i
    if start is not None: out.append((start, last))
    return out

def segment(path, alpha=40, row_gap=6, col_gap=3, min_px=150):
    a = np.array(Image.open(path).convert('RGBA'))
    m = a[..., 3] > alpha
    rows = []
    for y0, y1 in runs(m.any(1), row_gap):
        band = m[y0:y1 + 1]
        sprites = []
        for x0, x1 in runs(band.any(0), col_gap):
            sub = band[:, x0:x1 + 1]
            if sub.sum() < min_px: continue
            ys = np.nonzero(sub.any(1))[0]
            sprites.append((x0, y0 + ys.min(), x1, y0 + ys.max()))
        if not sprites: continue
        gaps = [b[0] - a_[2] for a_, b in zip(sprites, sprites[1:])]
        med = float(np.median(gaps)) if gaps else 0
        groups = [[sprites[0]]]
        for g, s in zip(gaps, sprites[1:]):
            if med and g > med * 1.8 + 6: groups.append([s])
            else: groups[-1].append(s)
        rows.append({'y': (y0, y1), 'groups': groups})
    return a, rows

def split_wide(a, rows, alpha=40):
    """Split blobs that are much wider than the sheet's typical sprite at minimum-occupancy columns."""
    m = a[..., 3] > alpha
    ws = sorted(s[2] - s[0] + 1 for r in rows for g in r['groups'] for s in g)
    med = ws[len(ws) // 2]
    for r in rows:
        for gi, g in enumerate(r['groups']):
            out = []
            for (x0, y0, x1, y1) in g:
                w = x1 - x0 + 1; k = int(round(w / med))
                if w > med * 1.45 and k >= 2:
                    occ = m[y0:y1 + 1, x0:x1 + 1].sum(0)
                    cuts = []
                    for j in range(1, k):
                        c = int(w * j / k); lo, hi = max(1, c - int(med * .3)), min(w - 1, c + int(med * .3))
                        cuts.append(lo + int(np.argmin(occ[lo:hi])))
                    edges = [0] + cuts + [w]
                    for e0, e1 in zip(edges, edges[1:]):
                        sub = m[y0:y1 + 1, x0 + e0:x0 + e1]
                        ys = np.nonzero(sub.any(1))[0]
                        if len(ys): out.append((x0 + e0, y0 + ys.min(), x0 + e1 - 1, y0 + ys.max()))
                else:
                    out.append((x0, y0, x1, y1))
            r['groups'][gi] = out
    return rows

def split_tall(a, rows, alpha=40):
    """Split blobs much taller than the sheet's typical sprite (stacked rows touching) at minimum-occupancy lines."""
    m = a[..., 3] > alpha
    hs = sorted(s[3] - s[1] + 1 for r in rows for g in r['groups'] for s in g)
    med = hs[len(hs) // 2]
    for r in rows:
        for gi, g in enumerate(r['groups']):
            out = []
            for (x0, y0, x1, y1) in g:
                h = y1 - y0 + 1; k = int(round(h / med))
                if h > med * 1.5 and k >= 2:
                    occ = m[y0:y1 + 1, x0:x1 + 1].sum(1); edges = [0]
                    for j in range(1, k):
                        c = int(h * j / k); lo, hi = c - int(med * .3), c + int(med * .3)
                        edges.append(lo + int(np.argmin(occ[lo:hi])))
                    edges.append(h)
                    for e0, e1 in zip(edges, edges[1:]):
                        sub = m[y0 + e0:y0 + e1, x0:x1 + 1]; xs = np.nonzero(sub.any(0))[0]; ys = np.nonzero(sub.any(1))[0]
                        if len(xs): out.append((x0 + xs.min(), y0 + e0 + ys.min(), x0 + xs.max(), y0 + e0 + ys.max()))
                else:
                    out.append((x0, y0, x1, y1))
            r['groups'][gi] = out
    # re-split stacked groups into separate rows by vertical position
    new = []
    for r in rows:
        bands = {}
        for g in r['groups']:
            for s in g:
                key = min(bands, key=lambda k: abs(k - s[3]), default=None)
                if key is None or abs(key - s[3]) > med * .5: bands[s[3]] = [s]
                else: bands[key].append(s)
        if len(bands) == 1: new.append(r); continue
        for k in sorted(bands):
            ss = sorted(bands[k]); gaps = [b[0] - a_[2] for a_, b in zip(ss, ss[1:])]
            md = float(np.median(gaps)) if gaps else 0; grp = [[ss[0]]]
            for gp, s in zip(gaps, ss[1:]):
                if md and gp > md * 1.8 + 6: grp.append([s])
                else: grp[-1].append(s)
            new.append({'y': (min(s[1] for s in ss), max(s[3] for s in ss)), 'groups': grp})
    rows[:] = new
    return rows
