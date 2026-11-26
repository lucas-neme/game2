"""V5 harmonized NPC sheets -> classified frames.
Each candidate frame (manifest rect on source.png) is re-cut from the source with the board removed, then classified:
 view   : front / back / side (facing right; left = mirror) from the skin visible in the head band and its symmetry;
 stride : foot spread in the bottom band (walk vs idle);
 chair  : wooden chair pixels under the hips (sit rows).
Frames are grouped by (row, block of consecutive same view) into sequences."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

V5 = Path(__file__).resolve().parents[2] / 'assets' / 'source' / 'v5-npcs'

def border_connected(m):
    """Pixels of m 4-connected to the image border."""
    H, W = m.shape; seen = np.zeros_like(m); st = [(y, x) for y in range(H) for x in (0, W - 1) if m[y, x]]
    st += [(y, x) for x in range(W) for y in (0, H - 1) if m[y, x]]
    for y, x in st: seen[y, x] = True
    while st:
        y, x = st.pop()
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not seen[yy, xx]: seen[yy, xx] = True; st.append((yy, xx))
    return seen

def alpha_of(a):
    rgb = a[..., :3].astype(int); mx = rgb.max(-1); mn = rgb.min(-1)
    dark = (mx < 38) & (mx - mn < 22)
    # Near-black pixels are only background when they belong to a dark board touching the crop border; the dark
    # outline, hair and trousers inside the silhouette are kept (dropping them punched holes in Helena's frames).
    m = (a[..., 3] > 40) & ~border_connected(dark & (a[..., 3] > 40))
    # dark-red halo left by the generator's matte
    halo = (rgb[..., 0] > rgb[..., 1] + 45) & (rgb[..., 0] > rgb[..., 2] + 45) & (mx < 150) & (a[..., 3] < 250)
    return m & ~halo

def main_component(m):
    H, W = m.shape; lab = np.zeros((H, W), int); sizes = [0]
    for y0 in range(H):
        for x0 in range(W):
            if m[y0, x0] and not lab[y0, x0]:
                sizes.append(0); k = len(sizes) - 1; st = [(y0, x0)]; lab[y0, x0] = k
                while st:
                    y, x = st.pop(); sizes[k] += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not lab[yy, xx]: lab[yy, xx] = k; st.append((yy, xx))
    if len(sizes) == 1: return m
    big = max(sizes); keep = [i for i, s in enumerate(sizes) if i and s >= big * .04]
    # keep only components overlapping the main one's columns (drops neighbours' fringes)
    main = int(np.argmax(sizes)); xs = np.nonzero((lab == main).any(0))[0]; x0, x1 = xs.min() - 3, xs.max() + 3
    keep = [k for k in keep if k == main or (np.nonzero((lab == k).any(0))[0].min() >= x0 and np.nonzero((lab == k).any(0))[0].max() <= x1)]
    return np.isin(lab, keep)

def cut(src, rect):
    x, y, w, h = rect
    a = np.array(src.crop((x, y, x + w, y + h)).convert('RGBA'))
    m = main_component(alpha_of(a)); a[..., 3] = np.where(m, 255, 0)
    im = Image.fromarray(a); bb = im.getbbox()
    return im, bb

def features(im):
    a = np.array(im).astype(int); m = a[..., 3] > 0
    ys, xs = np.nonzero(m)
    if len(ys) < 50: return None
    top, bot, left, right = ys.min(), ys.max(), xs.min(), xs.max(); H = bot - top + 1
    rgb = a[..., :3]
    skin = m & (rgb[..., 0] > 150) & (rgb[..., 0] > rgb[..., 2] + 40) & (rgb[..., 1] > 95) & (rgb[..., 0] - rgb[..., 1] < 80)
    hb = slice(top + int(H * .08), top + int(H * .34))
    hs = skin[hb]; hm = m[hb]
    sk = hs.sum() / max(1, hm.sum())
    cols = np.nonzero(hm.any(0))[0]; cx = (cols.min() + cols.max()) / 2 if len(cols) else 0
    sxs = np.nonzero(hs.any(0))[0]; scx = sxs.mean() if len(sxs) else cx
    asym = (scx - cx) / max(1, (cols.max() - cols.min()) / 2) if len(cols) else 0
    foot = m[bot - int(H * .1):bot + 1]; fcols = np.nonzero(foot.any(0))[0]
    stride = (fcols.max() - fcols.min()) / max(1, right - left) if len(fcols) else 0
    gaps = 0
    if len(fcols):
        occ = foot.any(0)[fcols.min():fcols.max() + 1]; gaps = int((~occ).sum())
    hs_ = slice(top + int(H * .62), top + int(H * .85)); hip = m[hs_]; hr = rgb[hs_]
    wood = hip & (hr[..., 0] > 90) & (hr[..., 0] < 170) & (hr[..., 1] < 90) & (hr[..., 2] < 60)
    view = 'back' if sk < .07 else ('side' if abs(asym) > .22 else 'front')
    return dict(view=view, facing=('right' if asym > 0 else 'left') if view == 'side' else None, skin=round(float(sk), 3), asym=round(float(asym), 2),
                stride=round(float(stride), 2), gaps=gaps, wood=round(float(wood.sum() / max(1, hip.sum())), 3), h=int(H), w=int(right - left + 1))

def analyse(name):
    m = json.loads((V5 / name / 'manifest.json').read_text(encoding='utf-8'))
    src = Image.open(V5 / name / 'source.png')
    out = []
    for f in m['frames']:
        im, bb = cut(src, f['rect'])
        if not bb: continue
        im = im.crop(bb); ft = features(im)
        if ft: out.append(dict(row=f['row'], index=f['index'], x=f['rect'][0], im=im, **ft))
    return out
