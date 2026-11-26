"""Shared helpers for the Frequência Zero asset pipeline.

Art rules (docs/art-direction/ART_DIRECTION.md): 2:1 isometric, terrain cell 128x64, SBS wall module 64x96 at 1:1,
light from the upper left (-0.55, -0.65, 0.55), 1 px darkened outline on organic shapes, soft contact shadow,
muted earthy palette sampled from the SBS sheets.
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PROD = ROOT / 'assets' / 'production'
LIGHT = np.array([-.55, -.65, .55]); LIGHT = LIGHT / np.linalg.norm(LIGHT)
TILE_W, TILE_H = 128, 64

def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)

def ramp(stops, t):
    t = np.clip(t, 0, 1); xs = np.linspace(0, 1, len(stops)); cs = np.array([hexc(s) for s in stops])
    return np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], -1)

def lit(height, strength=1.0):
    gy, gx = np.gradient(height * strength)
    nx, ny, nz = -gx, -gy, np.ones_like(height)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.clip((nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / n, 0, 1)

def edge_mask(m):
    inner = m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
    return m & ~inner

def vnoise(shape, scale, seed):
    r = np.random.default_rng(seed)
    gh, gw = int(shape[0] / scale) + 3, int(shape[1] / scale) + 3
    g = r.random((gh, gw))
    y = np.arange(shape[0]) / scale; x = np.arange(shape[1]) / scale
    yi = y.astype(int); xi = x.astype(int); fy = (y - yi)[:, None]; fx = (x - xi)[None, :]
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    a = g[yi][:, xi]; b = g[yi][:, xi + 1]; c = g[yi + 1][:, xi]; d = g[yi + 1][:, xi + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy

def fbm(shape, seed, scales=(64, 24, 9, 4), weights=(.45, .3, .15, .1)):
    return sum(w * vnoise(shape, s, seed + i) for i, (s, w) in enumerate(zip(scales, weights)))

def rgba(rgb, a):
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.clip(a, 0, 255)]).astype(np.uint8), 'RGBA')

def contact_shadow(w, h, cx, cy, rx, ry, alpha=95):
    yy, xx = np.mgrid[0:h, 0:w]
    d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    return np.where(d < 1, alpha * np.clip(1 - d, 0, 1) ** .7, 0)

def compose_over(base_rgb, base_a, rgb, a):
    """Alpha-over in numpy (a, base_a in 0..255)."""
    t = (a / 255.0)[..., None]
    out_rgb = rgb * t + base_rgb * (1 - t)
    out_a = np.maximum(base_a, a)
    return out_rgb, out_a

class Sprite:
    def __init__(self, name, im, anchor, category, source='original (Frequência Zero pipeline)', collision=None, **meta):
        self.name, self.im, self.anchor, self.category, self.source = name, im, tuple(int(v) for v in anchor), category, source
        self.collision = collision; self.meta = meta
