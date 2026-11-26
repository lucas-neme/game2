"""Tiny isometric modeller for props, furniture and interiors.

Units are metres. Projection matches the SBS pack: one terrain cell (128x64 px) is 3 m x 3 m and one storey
(64 px) is 3 m high, so 1 m = 21.33 px horizontally along an axis step and 21.33 px up.
Faces visible from the camera: top, +y face (screen left, lit) and +x face (screen right, shaded).
"""
import numpy as np
from PIL import Image, ImageDraw
from common import hexc, rgba, edge_mask, vnoise, contact_shadow

PX = 64 / 3.0  # px per metre along a grid axis (screen x component) and per metre of height

def proj(x, y, z):
    return (x - y) * PX, (x + y) * PX / 2 - z * PX

FACE_SHADE = {'top': 1.0, 'left': .80, 'right': .60}

class Material:
    def __init__(self, color, tex='noise', amp=.10, scale=2.0, stripe=None, stripe_dark=.82, tint=None):
        self.c = hexc(color); self.tex, self.amp, self.scale, self.stripe, self.stripe_dark = tex, amp, scale, stripe, stripe_dark

M = {
    'wood':      Material('8a6644', amp=.10, stripe=4.0),
    'wood_dark': Material('5c412c', amp=.10, stripe=4.0),
    'wood_pale': Material('a88a64', amp=.08, stripe=4.0),
    'iron':      Material('3c3f3e', amp=.06),
    'steel':     Material('7d8482', amp=.07),
    'rust':      Material('7a4a32', amp=.16, scale=1.4),
    'concrete':  Material('8f8a7f', amp=.10, scale=1.6),
    'stone':     Material('77736a', amp=.14, scale=1.3),
    'paint_red': Material('9c3b31', amp=.06), 'paint_green': Material('3f5f46', amp=.06),
    'paint_cream': Material('d8ccb0', amp=.05), 'paint_blue': Material('3d5670', amp=.06),
    'fabric':    Material('6d5a48', amp=.08, scale=1.0), 'paper': Material('e4dcc6', amp=.04),
    'glass':     Material('8fb0b4', amp=.03), 'lamp':  Material('f0d79a', amp=.02),
    'black':     Material('262626', amp=.05), 'brass': Material('b08b45', amp=.08),
    'leaves':    Material('4f6030', amp=.2, scale=1.0), 'soil': Material('5a4634', amp=.15, scale=1.0),
    'tile':      Material('a39c8c', amp=.05), 'yellow': Material('c9a640', amp=.08),
}

class Model:
    def __init__(self):
        self.prims = []  # (sortkey, kind, data)
    def box(self, x0, y0, z0, x1, y1, z1, mat, faces=('top', 'left', 'right')):
        self.prims.append(('box', (x0, y0, z0, x1, y1, z1), M[mat] if isinstance(mat, str) else mat, faces)); return self
    def cyl(self, cx, cy, z0, z1, r, mat, sides=20, cap=True):
        self.prims.append(('cyl', (cx, cy, z0, z1, r, sides), M[mat] if isinstance(mat, str) else mat, cap)); return self
    def poly(self, pts3, mat, shade=1.0):
        self.prims.append(('poly', (pts3, shade), M[mat] if isinstance(mat, str) else mat, None)); return self

    def _key(self, p):
        kind, d = p[0], p[1]
        if kind == 'box': x0, y0, z0, x1, y1, z1 = d; return (x1 + y1, z0, x0 + y0)
        if kind == 'cyl': cx, cy, z0, z1, r, _ = d; return (cx + cy + r, z0, 0)
        pts = d[0]; return (max(p[0] + p[1] for p in pts), min(p[2] for p in pts), 0)

    @staticmethod
    def _bounds(p):
        kind, d = p[0], p[1]
        if kind == 'box': return d
        if kind == 'cyl': cx, cy, z0, z1, r, _ = d; return (cx - r, cy - r, z0, cx + r, cy + r, z1)
        xs = [q[0] for q in d[0]]; ys = [q[1] for q in d[0]]; zs = [q[2] for q in d[0]]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

    def ordered(self):
        """Painter's order: P before Q when they are separated along an axis with P on the far/low side
        (x1<=x0', y1<=y0' or z1<=z0'). Topological sort, ties broken by the simple depth key."""
        ps = sorted(self.prims, key=self._key); n = len(ps); B = [self._bounds(p) for p in ps]
        eps = 1e-6
        def before(a, b):
            A, Bb = B[a], B[b]
            return A[3] <= Bb[0] + eps or A[4] <= Bb[1] + eps or A[5] <= Bb[2] + eps
        indeg = [0] * n; out = [[] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j and before(i, j) and not before(j, i):
                    out[i].append(j); indeg[j] += 1
        ready = [i for i in range(n) if indeg[i] == 0]; res = []
        while ready:
            ready.sort(); i = ready.pop(0); res.append(ps[i])
            for j in out[i]:
                indeg[j] -= 1
                if indeg[j] == 0: ready.append(j)
        if len(res) < n:  # cycle: fall back for the rest
            seen = set(map(id, res)); res += [p for p in ps if id(p) not in seen]
        return res

    def render(self, pad=6, shadow=True, outline=True, seed=0, scale=1.0):
        pts = []
        for kind, d, _, _ in self.prims:
            if kind == 'box':
                x0, y0, z0, x1, y1, z1 = d
                pts += [proj(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
            elif kind == 'cyl':
                cx, cy, z0, z1, r, _ = d
                pts += [proj(cx + dx, cy + dy, z) for dx in (-r, r) for dy in (-r, r) for z in (z0, z1)]
            else:
                pts += [proj(*p) for p in d[0]]
        pts.append(proj(0, 0, 0))
        shadow_polys = []
        for kind, d, _, _ in self.prims:
            if kind == 'box':
                x0, y0, z0, x1, y1, z1 = d; corners = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
            elif kind == 'cyl':
                cx, cy, z0, z1, rr, _ = d; corners = [(cx + dx, cy + dy, z) for dx in (-rr, 0, rr) for dy in (-rr, 0, rr) for z in (z0, z1)]
            else:
                corners = list(d[0])
            sp = [proj(x + z * .55, y + z * .15, 0) for (x, y, z) in corners]
            shadow_polys.append(sp); pts += sp
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        minx, maxx, miny, maxy = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad + 6
        W, H = int(np.ceil(maxx - minx)), int(np.ceil(maxy - miny))
        ox, oy = -minx, -miny
        rgb = np.zeros((H, W, 3)); a = np.zeros((H, W))
        r = np.random.default_rng(seed)
        nz = vnoise((H, W), 1.3, seed) * .6 + vnoise((H, W), 4, seed + 1) * .4
        yy, xx = np.mgrid[0:H, 0:W].astype(float)
        def fill(poly2d, mat, shade, axis=None):
            im = Image.new('L', (W, H)); ImageDraw.Draw(im).polygon([(x + ox, y + oy) for x, y in poly2d], fill=255)
            mk = np.array(im) > 0
            c = mat.c * shade * (1 + (nz[mk] - .5)[:, None] * 2 * mat.amp)
            if mat.stripe and axis is not None:
                # planks: stripes across the face's length direction
                u = (xx[mk] * axis[0] + yy[mk] * axis[1]) / mat.stripe
                c *= np.where((u % 1) < .16, mat.stripe_dark, 1.0)[:, None]
            rgb[mk] = c; a[mk] = 255
        for p in self.ordered():
            kind, d, mat, faces = p
            if kind == 'box':
                x0, y0, z0, x1, y1, z1 = d
                if 'left' in faces:   # +y face
                    fill([proj(x0, y1, z0), proj(x1, y1, z0), proj(x1, y1, z1), proj(x0, y1, z1)], mat, FACE_SHADE['left'], (0, 1) if (z1 - z0) < (x1 - x0) else (1, .5))
                if 'right' in faces:  # +x face
                    fill([proj(x1, y0, z0), proj(x1, y1, z0), proj(x1, y1, z1), proj(x1, y0, z1)], mat, FACE_SHADE['right'], (0, 1) if (z1 - z0) < (y1 - y0) else (1, -.5))
                if 'top' in faces:
                    fill([proj(x0, y0, z1), proj(x1, y0, z1), proj(x1, y1, z1), proj(x0, y1, z1)], mat, FACE_SHADE['top'], (1, .5) if (x1 - x0) > (y1 - y0) else (1, -.5))
            elif kind == 'cyl':
                cx, cy, z0, z1, rad, sides = d
                sx0, sy0 = proj(cx, cy, z0); sx1, sy1 = proj(cx, cy, z1)
                rx = rad * PX * 1.414; ry = rx / 2
                # side surface = between the front arcs of the top and bottom ellipses
                dx = (xx - (sx0 + ox)) / rx
                arc = ry * np.sqrt(np.clip(1 - dx * dx, 0, 1))
                mk = (np.abs(dx) <= 1) & (yy >= sy1 + oy + arc - .5) & (yy <= sy0 + oy + arc + .5)
                u = np.clip((xx[mk] - (sx0 + ox - rx)) / (2 * rx), 0, 1)
                sh = .95 - .45 * u + .12 * np.sin(u * np.pi)
                rgb[mk] = mat.c * sh[:, None] * (1 + (nz[mk] - .5)[:, None] * 2 * mat.amp); a[mk] = 255
                top = Image.new('L', (W, H)); ImageDraw.Draw(top).ellipse([sx1 + ox - rx, sy1 + oy - ry, sx1 + ox + rx, sy1 + oy + ry], fill=255)
                tm = (np.array(top) > 0) & bool(faces)
                rgb[tm] = mat.c * 1.02 * (1 + (nz[tm] - .5)[:, None] * 2 * mat.amp); a[tm] = 255
            else:
                pts3, shade = d
                fill([proj(*q) for q in pts3], mat, shade)
        solid = a > 0
        if outline:
            e = edge_mask(solid); rgb[e] *= .55
        if shadow:
            from PIL import ImageFilter
            sim = Image.new('L', (W, H)); sd = ImageDraw.Draw(sim)
            for sp in shadow_polys:
                pts2 = np.array([(x + ox, y + oy) for x, y in sp])
                # convex hull of the projected corners
                c = pts2[np.lexsort((pts2[:, 1], pts2[:, 0]))]
                def half(pp):
                    h = []
                    for q in pp:
                        while len(h) >= 2 and ((h[-1][0]-h[-2][0])*(q[1]-h[-2][1])-(h[-1][1]-h[-2][1])*(q[0]-h[-2][0])) <= 0: h.pop()
                        h.append(q)
                    return h
                hull = half(c)[:-1] + half(c[::-1])[:-1]
                if len(hull) >= 3: sd.polygon([tuple(q) for q in hull], fill=255)
            sh = np.array(sim.filter(ImageFilter.GaussianBlur(1.6))).astype(float) * (78 / 255)
            a = np.where(solid, 255, sh)
        im = rgba(np.where(solid[..., None], rgb, 0), a)
        if scale != 1.0:
            im = im.resize((round(W * scale), round(H * scale)), Image.LANCZOS)
            return im, (round((gx + ox) * scale), round((gy + oy) * scale))
        gx, gy = proj(0, 0, 0)
        return im, (round(gx + ox), round(gy + oy))
