"""Bring non-canon art (SBS structures, modelled props, rendered rooms) into the canon pixel language:
nearest re-grid to the canon pixel density, quantize to a palette sampled from the canon art, warm grading,
1 px dark outline. Output must still be reviewed (state REVIEW) before promotion."""
import numpy as np
from PIL import Image
from canon_assets import CANON
import canon_assets as A

_PAL = None
def canon_palette(k=40):
    global _PAL
    if _PAL is not None: return _PAL
    px = []
    for rel in ('casa_tio', 'radio', 'clinica', 'posto', 'estacao', 'arquivo'):
        a = np.array(A.dehalo(Image.open(CANON / 'construcoes' / f'{rel}.png'))).reshape(-1, 4)
        px.append(a[a[:, 3] > 0, :3])
    px = np.concatenate(px).astype(float)
    r = np.random.default_rng(0); sel = px[r.choice(len(px), min(6000, len(px)), replace=False)]
    c = sel[r.choice(len(sel), k, replace=False)]
    for _ in range(18):
        lab = ((sel[:, None] - c[None]) ** 2).sum(-1).argmin(1)
        for j in range(k):
            m = lab == j
            if m.any(): c[j] = sel[m].mean(0)
    _PAL = c; return c

def canonize(im, target_w=None, grade=True, outline=True, k_pal=None):
    im = im.convert('RGBA')
    if target_w: im = im.resize((target_w, round(im.height * target_w / im.width)), Image.LANCZOS)
    a = np.array(im).astype(float); rgb = a[..., :3]; m = a[..., 3] > 110
    if grade:
        lum = rgb @ np.array([.3, .59, .11])
        rgb = rgb * 1.08 + np.array([10, 2, -10]) * (lum[..., None] / 255)   # warm, slightly lifted
        rgb = (rgb - 128) * 1.12 + 128                                      # canon contrast
    pal = canon_palette() if k_pal is None else k_pal
    flat = rgb.reshape(-1, 3); idx = ((flat[:, None] - pal[None]) ** 2).sum(-1).argmin(1)
    q = pal[idx].reshape(rgb.shape)
    out = np.zeros_like(a); out[..., :3] = q; out[..., 3] = np.where(m, 255, 0)
    if outline:
        ring = np.zeros_like(m)
        ring[1:] |= m[:-1]; ring[:-1] |= m[1:]; ring[:, 1:] |= m[:, :-1]; ring[:, :-1] |= m[:, 1:]
        ring &= ~m
        out[ring, :3] = [30, 22, 26]; out[ring, 3] = 255
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')
