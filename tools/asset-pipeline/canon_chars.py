"""Canon characters: clean the approved crops into an on-model base sprite, then animate it.

Rules (docs/art-direction/CHARACTERS.md): the head (face, hair, accessories) is the canon pixels and never changes
between frames; torso keeps the canon jacket/shirt; feet and arms are redrawn per frame as pixel art in the
character's own colours with the canon dark outline. Frame 32x48, feet anchor (16, 45). Views: front (SE, mirrored
SW) and back (NE, mirrored NW).
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image

CANON = Path(r'D:/Projetos/game2-insumos/fz-canon')
FW, FH = 32, 48
FOOT_Y = 45

# per character: best front crop, rows where head ends and torso ends (fractions of crop height), notes
CHARS = {
    'hero':   dict(src='protagonista', crop='r1_c1', back_hair=None),
    'lia':    dict(src='lia', crop='r1_c1'),
    'raul':   dict(src='raul', crop='r1_c1'),
    'nora':   dict(src='nora', crop='r1_c2'),
    'helena': dict(src='helena', crop='r1_c5'),
    'bento':  dict(src='bento', crop='r1_c1'),
    'celina': dict(src='celina', crop='r1_c5'),
}
OUTLINE = np.array([28, 20, 24])

def load_crop(name, crop):
    return np.array(Image.open(CANON / 'personagens' / name / 'recortes' / f'{crop}.png').convert('RGBA')).astype(float)

def kmeans(px, k, seed=0, it=20):
    r = np.random.default_rng(seed)
    c = px[r.choice(len(px), k, replace=False)]
    for _ in range(it):
        d = ((px[:, None, :] - c[None]) ** 2).sum(-1); lab = d.argmin(1)
        for j in range(k):
            m = lab == j
            if m.any(): c[j] = px[m].mean(0)
    return c, lab

def strip_background(a):
    """Remove leftover board background (dark desaturated purple-blue) connected to the frame border."""
    rgb = a[..., :3]; al = a[..., 3] > 0
    bgish = (rgb.max(-1) < 85) & (np.abs(rgb[..., 2] - rgb[..., 0]) < 45) & (rgb[..., 2] >= rgb[..., 1] - 5)
    H, W = al.shape; seen = np.zeros_like(al); stack = [(y, x) for y in range(H) for x in (0, W - 1)] + [(y, x) for x in range(W) for y in (0, H - 1)]
    while stack:
        y, x = stack.pop()
        if not (0 <= y < H and 0 <= x < W) or seen[y, x]: continue
        seen[y, x] = True
        if al[y, x] and not bgish[y, x]: continue
        al[y, x] = False
        stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    a = a.copy(); a[..., 3] = np.where(al, 255, 0); return a

def clean(a, k=13, seed=0):
    """Palette-quantize + majority filter (keeps the canon colours, removes AI noise), then rebuild outline."""
    al = a[..., 3] > 0
    if al[0].any() and al[-1].any() and al[:, 0].any() and al[:, -1].any():  # crop still carries board background
        a = strip_background(a)
    m = a[..., 3] > 0
    c, lab = kmeans(a[..., :3][m], k, seed)
    idx = np.full(m.shape, -1); idx[m] = lab
    H, W = m.shape; out = idx.copy()
    for y in range(H):
        for x in range(W):
            if idx[y, x] < 0: continue
            win = idx[max(0, y - 1):y + 2, max(0, x - 1):x + 2].ravel(); win = win[win >= 0]
            vals, cnt = np.unique(win, return_counts=True)
            if cnt.max() >= 5 and (idx[y, x] not in vals[cnt >= 2]): out[y, x] = vals[cnt.argmax()]
    rgb = np.zeros((H, W, 3)); rgb[out >= 0] = c[out[out >= 0]]
    # isolated pixels outside the silhouette body get dropped
    solid = out >= 0
    nb = sum(shift(solid, dy, dx).astype(int) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) - solid
    solid &= nb >= 2
    # keep the main body: largest 8-connected component (+ anything touching it)
    lab = np.zeros(solid.shape, int); cur = 0; sizes = {}
    for y0 in range(H):
        for x0 in range(W):
            if solid[y0, x0] and not lab[y0, x0]:
                cur += 1; st = [(y0, x0)]; lab[y0, x0] = cur; n = 0
                while st:
                    y, x = st.pop(); n += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < H and 0 <= xx < W and solid[yy, xx] and not lab[yy, xx]: lab[yy, xx] = cur; st.append((yy, xx))
                sizes[cur] = n
    if sizes:
        keep = max(sizes, key=sizes.get); solid = lab == keep
    return rgb, solid, c

def shift(m, dy, dx):
    """Shift a boolean mask without wrap-around."""
    out = np.zeros_like(m); H, W = m.shape
    out[max(0, dy):H + min(0, dy), max(0, dx):W + min(0, dx)] = m[max(0, -dy):H + min(0, -dy), max(0, -dx):W + min(0, -dx)]
    return out

def with_outline(rgb, solid):
    H, W = solid.shape
    grown = solid.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)): grown |= shift(solid, dy, dx)
    ring = grown & ~solid
    out = np.zeros((H, W, 4)); out[solid, :3] = rgb[solid]; out[solid, 3] = 255
    out[ring, :3] = OUTLINE; out[ring, 3] = 255
    return out

class Base:
    """Canon character split into parts (in crop coordinates)."""
    def __init__(self, key):
        spec = CHARS[key]; self.key = key
        a = spec['array'] if spec.get('array') is not None else load_crop(spec['src'], spec['crop'])
        rgb, solid, pal = clean(a, seed=__import__("zlib").crc32(key.encode()) % 1000)
        ys, xs = np.nonzero(solid)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        self.rgb, self.solid = rgb[y0:y1 + 1, x0:x1 + 1], solid[y0:y1 + 1, x0:x1 + 1]
        self.h, self.w = self.solid.shape
        rows = self.solid.sum(1)
        # feet = bottom rows; torso ends where the silhouette narrows into feet
        self.feet_top = self.h - 5
        # head bottom: the neck is the narrowest row in the upper 40..70 % band
        band = range(int(self.h * .42), int(self.h * .68))
        self.neck = min(band, key=lambda r: rows[r] + (0 if r > self.h * .5 else 2))
        tr = self.solid[self.neck + 1:self.feet_top]
        cols = tr.any(0); cx0, cx1 = np.nonzero(cols)[0][[0, -1]]
        self.tx0, self.tx1 = cx0, cx1
        self.arm_w = max(2, (cx1 - cx0 + 1) // 5)
        # colours sampled from the canon pixels
        t = self.rgb[self.neck + 2:self.feet_top, cx0 + self.arm_w + 1:cx1 - self.arm_w]
        tm = self.solid[self.neck + 2:self.feet_top, cx0 + self.arm_w + 1:cx1 - self.arm_w]
        self.cloth = np.median(t[tm], 0)
        sl = self.rgb[self.neck + 2:self.feet_top - 1, cx0:cx0 + self.arm_w]; slm = self.solid[self.neck + 2:self.feet_top - 1, cx0:cx0 + self.arm_w]
        self.sleeve = np.median(sl[slm], 0) if slm.any() else self.cloth
        f = self.rgb[self.feet_top:, :]; fm = self.solid[self.feet_top:, :]
        self.shoe = np.percentile(f[fm], 35, axis=0) if fm.any() else np.array([60, 40, 30])
        lum = self.rgb @ np.array([.3, .59, .11])
        head = self.rgb[:self.neck]; hm = self.solid[:self.neck]
        warm = (head[..., 0] > head[..., 2] + 30) & (lum[:self.neck] > 120)
        self.skin = np.median(head[hm & warm], 0) if (hm & warm).any() else np.array([220, 170, 130])
        top = self.rgb[:max(3, self.neck // 3)]; tmk = self.solid[:max(3, self.neck // 3)]
        self.hair = np.median(top[tmk], 0)
        self.pants = self.shoe * 1.25

    def layer(self, part, view='front'):
        """RGBA arrays (crop coords) for 'head', 'torso' (no arms), 'armL', 'armR'."""
        H, W = self.h, self.w
        m = np.zeros((H, W), bool)
        if part == 'head': m[:self.neck + 1] = True
        elif part == 'torso':
            m[self.neck + 1:self.feet_top] = True; m[:, :self.tx0 + self.arm_w] = False; m[:, self.tx1 - self.arm_w + 1:] = False
        elif part == 'armL': m[self.neck + 1:self.feet_top, :self.tx0 + self.arm_w] = True
        elif part == 'armR': m[self.neck + 1:self.feet_top, self.tx1 - self.arm_w + 1:] = True
        m &= self.solid
        rgb = self.rgb.copy()
        if view == 'back' and part == 'head':
            rgb = back_head(self, rgb, m)
        if view == 'back' and part == 'torso':
            core = m.copy(); rgb[core] = self.cloth * (0.92 + .1 * ((np.arange(W)[None, :] - (self.tx0 + self.tx1) / 2) < 0))[core][..., None] if False else rgb[core]
            rgb[core] = self.sleeve * np.where(np.arange(W)[None, :].repeat(H, 0)[core] < (self.tx0 + self.tx1) / 2, 1.0, .86)[:, None]
        return rgb, m

def back_head(b, rgb, m):
    """Back of the head: the canon face area is covered by the character's own hair colours, keeping the outline
    shape, hats/scarves (non-skin pixels) untouched."""
    rgb = rgb.copy(); H, W = m.shape
    lum = rgb @ np.array([.3, .59, .11])
    skin = m & (np.abs(rgb - b.skin).sum(-1) < 90) & (lum > 90)
    # also eyes/mouth/glasses inside the face area
    ys, xs = np.nonzero(skin)
    if len(ys):
        face = np.zeros_like(m); face[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True; face &= m
        hair_dark = b.hair * .78
        yy = np.arange(H)[:, None].repeat(W, 1)
        stripes = ((np.arange(W)[None, :] + yy // 3) % 4 == 0)
        col = np.where(stripes[..., None], hair_dark[None, None], b.hair[None, None]) * (1 - (yy - ys.min()) / max(1, ys.max() - ys.min()) * .18)[..., None]
        rgb[face] = col[face]
    return rgb

def paste(canvas, rgb, m, ox, oy, flip=False):
    H, W = m.shape
    for y in range(H):
        for x in range(W):
            if m[y, x]:
                X, Y = ox + x, oy + y
                if 0 <= X < FW and 0 <= Y < FH: canvas[Y, X, :3] = rgb[y, x]; canvas[Y, X, 3] = 255

def draw_px(canvas, x, y, col):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < FW and 0 <= y < FH: canvas[y, x, :3] = col; canvas[y, x, 3] = 255

def draw_limb(canvas, p0, p1, width, col, end_col=None, end_len=2):
    """Pixel-art limb: filled thick line with a 2-tone shade, the last end_len px in end_col (hand/boot)."""
    (x0, y0), (x1, y1) = p0, p1
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / max(1, n); x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
        rem = np.hypot(x1 - x, y1 - y)
        c = end_col if (end_col is not None and rem < end_len) else col
        L = max(1e-6, np.hypot(x1 - x0, y1 - y0)); px_, py_ = -(y1 - y0) / L, (x1 - x0) / L  # perpendicular
        for k in range(width):
            o = k - (width - 1) / 2
            draw_px(canvas, x + px_ * o, y + py_ * o, c * (1.0 if k < width - 1 else .8))

def frame(b, view, pose):
    """pose: dict with bob, lean, feet [(dx, lift), (dx, lift)], arms [(dx, dy, mode), ...], crouch, flash."""
    cv = np.zeros((FH, FW, 4))
    ox = FW // 2 - b.w // 2 + pose.get('shift', 0); oy = FOOT_Y - b.h + 1
    crouch = pose.get('crouch', 0); bob = pose.get('bob', 0)
    body_y = oy + bob + crouch
    # feet (behind the body), drawn per frame
    fx = [ox + b.tx0 + b.arm_w + 1, ox + b.tx1 - b.arm_w - 1]
    for i, (dx, lift) in enumerate(pose['feet']):
        x = fx[i] + dx; ytop = body_y + b.feet_top - 1; ybot = FOOT_Y - lift
        draw_limb(cv, (x, ytop), (x, ybot), 3, b.pants, b.shoe * .9, end_len=2)
        draw_px(cv, x + (1 if i else -1) * 0 + (1.4 if view == 'front' else -.4), ybot, b.shoe * .75)
    # torso + head (canon pixels)
    for part, extra in (('torso', 0), ('head', pose.get('head_dy', 0))):
        rgb, m = b.layer(part, view)
        paste(cv, rgb, m, ox + pose.get('lean', 0) * (part == 'head'), body_y + extra)
    # arms: canon sleeves moved as limbs, or redrawn when raised
    sh = [(ox + b.tx0 + b.arm_w // 2, body_y + b.neck + 3), (ox + b.tx1 - b.arm_w // 2, body_y + b.neck + 3)]
    arm_len = b.feet_top - b.neck - 3
    for i, part in enumerate(('armL', 'armR')):
        a = pose['arms'][i]
        if a[2] == 'canon':
            rgb, m = b.layer(part, view); paste(cv, rgb, m, ox + a[0], body_y + a[1])
        else:
            sx, sy = sh[i]; ang = a[0]; L = arm_len
            ex = sx + np.sin(ang) * L * (1 if i else -1) * (-1 if a[2] == 'fwd' else 1) * 0 + a[1] * (1 if i else -1)
            ey = sy + np.cos(ang) * L
            if a[2] == 'up': ex, ey = sx + (2 if i else -2), sy - L + 2
            if a[2] == 'cross': ex, ey = sx + (3 if i == 0 else -3), sy + 2
            if a[2] == 'fwd': ex, ey = sx + (L - 1) * (1 if i else -1), sy + 1
            draw_limb(cv, (sx, sy), (ex, ey), 3, b.sleeve, b.skin, end_len=2)
    if pose.get('item'):
        x, y = sh[1][0] + 3, sh[1][1] - 2
        for dy in range(4):
            for dx in range(3): draw_px(cv, x + dx, y + dy, np.array([46, 46, 50]) if dy else np.array([120, 120, 130]))
        draw_px(cv, x + 1, y - 2, np.array([150, 150, 160])); draw_px(cv, x + 1, y + 1, np.array([230, 190, 90]))
    if pose.get('glow'):
        gx, gy = sh[1][0] + arm_len - 1, sh[1][1] + 1
        for r, col in ((3, np.array([150, 90, 230])), (2, np.array([200, 160, 255])), (1, np.array([255, 245, 255]))):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r: draw_px(cv, gx + dx, gy + dy, col)
    solid = cv[..., 3] > 0
    out = with_outline(cv[..., :3], solid)
    if pose.get('flash'):
        out[..., :3] = np.where(out[..., 3:4] > 0, out[..., :3] * .55 + np.array([255, 90, 80]) * .45, 0)
    if pose.get('mark'):
        for y in range(2, 8): out[y, FW - 5] = [255, 230, 120, 255]
        out[9, FW - 5] = [255, 230, 120, 255]
    # contact shadow
    for x in range(FW):
        for y in range(FOOT_Y - 1, FOOT_Y + 3):
            if out[y, x, 3] == 0 and ((x - FW / 2) / 9) ** 2 + ((y - FOOT_Y - .5) / 2) ** 2 < 1: out[y, x] = [0, 0, 0, 70]
    return out

def walk_feet(i, n, stride=2, lift=2):
    ph = 2 * np.pi * i / n
    l = (round(np.sin(ph) * stride), max(0, round(np.cos(ph) * lift)))
    r = (round(-np.sin(ph) * stride), max(0, round(-np.cos(ph) * lift)))
    return [l, r]

def poses(anim, n):
    out = []
    C = lambda dx=0, dy=0: (dx, dy, 'canon')
    for i in range(n):
        ph = 2 * np.pi * i / n
        if anim == 'idle':
            b = 1 if i in (1, 2) else 0
            out.append(dict(bob=b, feet=[(0, 0), (0, 0)], arms=[C(0, 0), C(0, 0)]))
        elif anim in ('walk', 'run', 'sneak'):
            st, lf = {'walk': (1, 2), 'run': (2, 3), 'sneak': (1, 1)}[anim]
            f = walk_feet(i, n, st, lf); sw = round(np.sin(ph) * (1 if anim == 'walk' else 2))
            bob = -1 if (i % (n // 2)) in (1, 2) and anim != 'sneak' else 0
            out.append(dict(bob=bob, crouch=2 if anim == 'sneak' else 0, feet=f, arms=[C(0, -abs(sw)), C(0, -abs(sw) if sw < 0 else 0)] if anim != 'run' else [C(-1 if sw > 0 else 0, -1), C(1 if sw < 0 else 0, -1)], lean=1 if anim == 'run' else 0))
        elif anim == 'interact':
            out.append(dict(feet=[(0, 0), (0, 0)], arms=[C(), (0, 0, 'fwd') if i in (1, 2) else C()]))
        elif anim == 'talk':
            out.append(dict(bob=1 if i % 2 else 0, feet=[(0, 0), (0, 0)], arms=[C(), (0, 0, 'fwd') if i == 2 else C()]))
        elif anim == 'use':
            out.append(dict(feet=[(0, 0), (0, 0)], arms=[C(), (0, 0, 'up') if i else C()], item=i > 0))
        elif anim == 'defend':
            out.append(dict(crouch=1, feet=[(-1, 0), (1, 0)], arms=[(0, 0, 'cross'), (0, 0, 'cross')]))
        elif anim == 'dodge':
            s = [0, 2, 4, 4, 2, 0][i]
            out.append(dict(shift=s, crouch=1 if 0 < i < 5 else 0, feet=[(-1, 1 if i in (1, 2) else 0), (1, 0)], arms=[C(-1, -1), C(1, -1)]))
        elif anim == 'attack':
            out.append(dict(feet=[(-1, 0), (1, 0)], arms=[C(), (0, 0, 'fwd') if i >= 2 else C(1, -1)], glow=i in (2, 3), lean=1 if i in (2, 3) else 0))
        elif anim == 'hurt':
            out.append(dict(shift=[-1, -2, -1][i], feet=[(0, 0), (0, 0)], arms=[C(0, -1), C(0, -1)], flash=i == 1, head_dy=1 if i == 1 else 0))
        elif anim == 'sit':  # stand -> half -> seated (body lowers onto the seat, shins stay)
            out.append(dict(crouch=[0, 2, 4][i], feet=[(0, 0), (0, 0)], arms=[C(0, 0), C(0, 0)]))
        elif anim == 'react':
            out.append(dict(bob=[-1, -2, -2, 0][i], feet=[(0, [1, 2, 2, 0][i]), (0, [1, 2, 2, 0][i])], arms=[(0, 0, 'up'), (0, 0, 'up')] if i in (1, 2) else [C(), C()], mark=i in (1, 2, 3)))
    return out

ANIMS = [('sit', 3), ('idle', 4), ('walk', 8), ('run', 8), ('sneak', 8), ('interact', 4), ('talk', 4), ('defend', 2), ('dodge', 6),
         ('attack', 6), ('hurt', 3), ('use', 4), ('react', 4)]

def sheet(key):
    b = Base(key)
    rows = []
    for anim, n in ANIMS:
        for view in ('front', 'back'):
            rows.append((anim, view, [frame(b, view, p) for p in poses(anim, n)]))
    im = np.zeros((len(rows) * FH, 8 * FW, 4))
    meta = {}
    for r, (anim, view, frames) in enumerate(rows):
        for i, f in enumerate(frames): im[r * FH:(r + 1) * FH, i * FW:(i + 1) * FW] = f
        meta[f'{anim}:{view}'] = {'row': r, 'frames': len(frames)}
    return Image.fromarray(im.astype(np.uint8), 'RGBA'), meta, b

def portrait(key):
    p = CANON / 'personagens' / CHARS[key]['src'] / 'retrato.png'
    return Image.open(p).convert('RGBA')
