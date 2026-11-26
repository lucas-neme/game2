"""Character sprite sheets (64x96 frames) from a 2.5D skeleton.

Body space: f = forward, l = left, z = up (pixels). Views: 'front' faces SE (+x on the grid; camera sees the front
and the left side), 'back' faces NE (-y; camera sees the back and the left side). SW/NW are horizontal mirrors.
Parts are capsules/spheres shaded with the pipeline's top-left light, sorted by distance to the camera.
Animations (frames): idle 4, walk 8, run 8, interact 4, sneak 8, defend 2, dodge 6, combat 6, use 4, hurt 3, react 4.
"""
import math
import numpy as np
from PIL import Image
from common import hexc, Sprite

FW, FH = 64, 96
FOOT = (32, 88)
ANIMS = [('idle', 4), ('walk', 8), ('run', 8), ('interact', 4), ('sneak', 8), ('defend', 2), ('dodge', 6),
         ('combat', 6), ('use', 4), ('hurt', 3), ('react', 4)]
K = .78  # horizontal projection factor

def project(view, f, l, z):
    if view == 'front':   # facing +x : grid gx = f, gy = l
        gx, gy = f, l
    else:                 # facing -y : forward = -gy, left = +gx
        gx, gy = l, -f
    return FOOT[0] + (gx - gy) * K, FOOT[1] + (gx + gy) * K / 2 - z, gx + gy  # last: depth toward camera

LIGHT2 = np.array([-.6, -.8]); LIGHT2 /= np.linalg.norm(LIGHT2)

class Canvas:
    def __init__(self):
        self.rgb = np.zeros((FH, FW, 3)); self.a = np.zeros((FH, FW)); self.z = np.full((FH, FW), -1e9)
        self.yy, self.xx = np.mgrid[0:FH, 0:FW].astype(float)
    def capsule(self, p0, p1, r0, r1, color, depth, flat=False, shade_k=1.0):
        (x0, y0), (x1, y1) = p0, p1
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy + 1e-9
        t = np.clip(((self.xx - x0) * dx + (self.yy - y0) * dy) / L2, 0, 1)
        cx = x0 + t * dx; cy = y0 + t * dy; r = r0 + (r1 - r0) * t
        ox, oy = self.xx - cx, self.yy - cy; d = np.sqrt(ox * ox + oy * oy)
        m = d <= r
        nx, ny = ox / np.maximum(r, .5), oy / np.maximum(r, .5)
        lam = np.clip(-(nx * LIGHT2[0] + ny * LIGHT2[1]) * .5 + .62, .25, 1.15) if not flat else np.full(d.shape, .9)
        lam = 1 + (lam - 1) * shade_k
        self._put(m, hexc(color) * lam[..., None], depth)
    def sphere(self, c, r, color, depth, squash=1.0):
        ox, oy = (self.xx - c[0]) / r, (self.yy - c[1]) / (r * squash); d2 = ox * ox + oy * oy
        m = d2 <= 1
        lam = np.clip(-(ox * LIGHT2[0] + oy * LIGHT2[1]) * .45 + .68, .3, 1.15)
        self._put(m, hexc(color) * lam[..., None], depth)
    def poly(self, pts, color, depth, shade=1.0):
        from PIL import ImageDraw
        im = Image.new('L', (FW, FH)); ImageDraw.Draw(im).polygon(pts, fill=255)
        m = np.array(im) > 0
        g = np.clip(.95 - (self.xx - min(p[0] for p in pts)) / 40, .6, 1.05) * shade
        self._put(m, hexc(color) * g[..., None], depth)
    def pixel(self, x, y, color, depth):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < FW and 0 <= y < FH and depth >= self.z[y, x] - 1e-3:
            self.rgb[y, x] = hexc(color); self.a[y, x] = 255; self.z[y, x] = depth
    def _put(self, m, col, depth):
        w = m & (depth >= self.z - 1e-6)
        self.rgb[w] = col[w]; self.a[w] = 255; self.z[w] = depth
    def image(self):
        solid = self.a > 0
        inner = solid & np.roll(solid, 1, 0) & np.roll(solid, -1, 0) & np.roll(solid, 1, 1) & np.roll(solid, -1, 1)
        e = solid & ~inner; rgb = self.rgb.copy(); rgb[e] *= .42
        # internal contour: depth jumps between parts get a darker line (reads like hand-drawn separation)
        dz = np.abs(self.z - np.roll(self.z, 1, 1)) > 2.5
        rgb[dz & solid & np.roll(solid, 1, 1)] *= .78
        yy, xx = self.yy, self.xx
        sh = ((xx - FOOT[0] - 2) / 13) ** 2 + ((yy - FOOT[1] - 1) / 4) ** 2 < 1
        a = np.where(solid, 255, np.where(sh, 80, 0))
        rgb = np.where(solid[..., None], rgb, 0)
        return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8), 'RGBA')

def pose(anim, i, n):
    """Joint angles/offsets for one frame. Returns dict of scalars (radians, pixels)."""
    ph = 2 * math.pi * i / n
    P = dict(footL=None, footR=None, bob=0, lean=0, crouch=0, legL=0, legR=0, kneeL=0, kneeR=0, armL=0, armR=0, elbL=.15, elbR=.15,
             armLside=0, armRside=0, head=0, twist=0, slide=0, reachR=0, recoil=0, glow=0, liftL=0, liftR=0)
    if anim == 'idle':
        P['bob'] = math.sin(ph) * .6; P['armL'] = P['armR'] = .05 + math.sin(ph) * .03
    elif anim in ('walk', 'run', 'sneak'):
        amp = {'walk': .5, 'run': .85, 'sneak': .35}[anim]
        S = {'walk': 8, 'run': 12, 'sneak': 6}[anim]; lift = {'walk': 4, 'run': 8, 'sneak': 2.5}[anim]
        for side, o in (('L', 0), ('R', math.pi)):
            q = (ph + o) % (2 * math.pi)
            P['foot' + side] = (S * math.cos(q), 0 if q < math.pi else lift * math.sin(q - math.pi))
        s = math.cos(ph)
        P['armL'] = -s * amp * .9; P['armR'] = s * amp * .9
        P['elbL'] = P['elbR'] = .35 if anim != 'walk' else .2
        P['bob'] = abs(math.cos(ph)) * (2.2 if anim == 'run' else 1.1)
        P['lean'] = {'walk': .05, 'run': .22, 'sneak': .32}[anim]
        if anim == 'sneak': P['crouch'] = 9; P['elbL'] = P['elbR'] = .9; P['armL'] = P['armR'] = .5
    elif anim == 'interact':
        t = [0, .5, 1, .6][i]; P['reachR'] = t; P['armR'] = .4 + 1.0 * t; P['elbR'] = .5 - .4 * t; P['lean'] = .08 * t
    elif anim == 'use':
        t = [0, .7, 1, 1][i]; P['armR'] = 1.9 * t; P['elbR'] = 1.9 * t; P['head'] = .12 * t; P['bob'] = .3 * (i % 2)
    elif anim == 'defend':
        P['armL'] = P['armR'] = 1.3; P['elbL'] = P['elbR'] = 1.7; P['crouch'] = 3 + i; P['lean'] = .1
    elif anim == 'dodge':
        t = [0, .5, 1, 1, .6, .2][i]; P['slide'] = 9 * t; P['crouch'] = 6 * math.sin(math.pi * t); P['lean'] = -.15 * t
        P['legL'] = .5 * t; P['legR'] = -.3 * t; P['armL'] = -.6 * t; P['armR'] = .7 * t
    elif anim == 'combat':
        t = [0, .4, .9, 1, .7, .2][i]; P['armR'] = 1.55 * t; P['elbR'] = .2; P['armL'] = .6 * t; P['elbL'] = .9
        P['lean'] = .12 * t; P['legL'] = .35 * t; P['legR'] = -.25 * t; P['glow'] = t if i in (2, 3) else 0
    elif anim == 'hurt':
        t = [.4, 1, .5][i]; P['recoil'] = t; P['lean'] = -.25 * t; P['head'] = -.2 * t; P['armL'] = .5 * t; P['armR'] = .4 * t; P['crouch'] = 2 * t
    elif anim == 'react':
        t = [.3, 1, 1, .6][i]; P['armL'] = P['armR'] = 1.0 * t; P['elbL'] = P['elbR'] = 1.4 * t; P['head'] = -.12 * t; P['bob'] = 1.2 * t
    return P

def draw_char(spec, view, anim, i, n):
    P = pose(anim, i, n)
    cv = Canvas()
    hip_z = 37 - P['crouch'] + P['bob'] * .5
    base_f = -P['recoil'] * 3; base_l = P['slide']
    lean = P['lean']
    def J(f, l, z):
        return project(view, base_f + f + lean * (z - 0) * .45 * (z > hip_z - 6), base_l + l, z)
    # skeleton (body space): hips, shoulders, head
    hipL, hipR = (0, 4.5, hip_z), (0, -4.5, hip_z)
    sh_z = hip_z + 19
    shL, shR = (0, 7.5, sh_z), (0, -7.5, sh_z)
    neck = (0, 0, sh_z + 2); head_c = (P['head'] * 3, 0, sh_z + 11)
    def leg(hip, swing, knee, lift):
        thigh = 18 - P['crouch'] * .2
        kf = hip[0] + math.sin(swing) * thigh; kz = hip[2] - math.cos(swing) * thigh + lift
        shin = 18
        af = kf + math.sin(swing - knee) * shin; az = max(1.5, kz - math.cos(swing - knee) * shin)
        return (kf, hip[1], kz), (af, hip[1], az)
    def ik(hip, target):
        L1 = L2 = 18.0
        tf, tz = target; dfv, dzv = tf - hip[0], tz + 1.5 - hip[2]
        d = min(math.hypot(dfv, dzv), L1 + L2 - .01)
        a = math.atan2(dzv, dfv); bend = math.acos(max(-1, min(1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
        kf = hip[0] + L1 * math.cos(a + bend); kz = hip[2] + L1 * math.sin(a + bend)  # knee bends forward
        af = hip[0] + d * math.cos(a); az = hip[2] + d * math.sin(a)
        return (kf, hip[1], kz), (af, hip[1], max(1.5, az))
    if P['footL'] is not None:
        kL, aL = ik(hipL, P['footL']); kR, aR = ik(hipR, P['footR'])
    else:
        kL, aL = leg(hipL, P['legL'], P['kneeL'], P['liftL']); kR, aR = leg(hipR, P['legR'], P['kneeR'], P['liftR'])
    def arm(sh, swing, elbow, side):
        up = 14
        ef = sh[0] + math.sin(swing) * up; ez = sh[2] - math.cos(swing) * up
        fo = 13; hf = ef + math.sin(swing + elbow) * fo; hz = ez - math.cos(swing + elbow) * fo
        return (ef, sh[1] + side, ez), (hf, sh[1] + side * 1.4, hz)
    eL, hL = arm(shL, P['armL'], P['elbL'], 1.2); eR, hR = arm(shR, P['armR'], P['elbR'], -1.2)
    def p2(q): x, y, d = J(*q); return (x, y), d
    def seg(a, b, r0, r1, col, bias=0, **kw):
        (pa, da), (pb, db) = p2(a), p2(b); cv.capsule(pa, pb, r0, r1, col, (da + db) / 2 + bias, **kw)
    C = spec
    # legs + shoes
    for (hip, k, a_, side) in ((hipL, kL, aL, 1), (hipR, kR, aR, -1)):
        seg(hip, k, 4.2, 3.6, C['pants']); seg(k, a_, 3.6, 3.0, C['pants'])
        toe = (a_[0] + 4.5, a_[1], 1.5)
        seg((a_[0] - 1, a_[1], 2), toe, 3.0, 2.6, C['shoes'], bias=.5)
    # torso (+ coat/skirt) — depth = 0 (body centre)
    (hp, hd) = p2((0, 0, hip_z)); (sp, sd) = p2((0, 0, sh_z))
    if C.get('coat'):
        lo = p2((0, 0, hip_z - C.get('coat_len', 14)))[0]
        w = 9.5
        cv.poly([(sp[0] - w, sp[1]), (sp[0] + w, sp[1]), (lo[0] + w + 2, lo[1]), (lo[0] - w - 2, lo[1])], C['coat'], 0.2)
    if C.get('skirt'):
        lo = p2((0, 0, hip_z - 16))[0]
        cv.poly([(hp[0] - 8, hp[1] - 2), (hp[0] + 8, hp[1] - 2), (lo[0] + 11, lo[1]), (lo[0] - 11, lo[1])], C['skirt'], .15)
    cv.capsule((hp[0], hp[1] - 1), (sp[0], sp[1] + 2), 8.2, 9.0, C['top'], 0)
    if C.get('vest'): cv.capsule((hp[0], hp[1] - 3), (sp[0], sp[1] + 3), 7.6, 8.2, C['vest'], .1)
    if C.get('coat'):
        cv.capsule((hp[0], hp[1] + 3), (sp[0], sp[1] + 2), 8.8, 9.6, C['coat'], .05)
        x, y = (hp[0] + sp[0]) / 2, (hp[1] + sp[1]) / 2
        if view == 'front': cv.capsule((sp[0] + 1, sp[1] + 2), (hp[0] + 1, hp[1]), 1.6, 1.6, C['top'], .3, flat=True)
    if C.get('belt'): cv.capsule((hp[0] - 7, hp[1] - 1), (hp[0] + 7, hp[1] - 1), 1.4, 1.4, C['belt'], .35, flat=True)
    if C.get('apron') and view == 'front':
        lo = p2((0, 0, hip_z - 12))[0]
        cv.poly([(sp[0] - 4, sp[1] + 6), (sp[0] + 6, sp[1] + 6), (lo[0] + 7, lo[1]), (lo[0] - 3, lo[1])], C['apron'], .4)
    if C.get('backpack'):
        bp, bd = p2((-7, 0, sh_z - 8))
        dpt = bd - .2 if view == 'front' else bd + 2
        x, y = bp
        cv.poly([(x - 6, y - 7), (x + 6, y - 7), (x + 6.5, y + 7), (x - 6.5, y + 7)], C['backpack'], dpt)
        cv.poly([(x - 5, y + 1), (x + 5, y + 1), (x + 5, y + 6), (x - 5, y + 6)], '4a3020', dpt + .01, shade=.9)
        if view == 'front':
            for o in (4.5, -4.5):
                a_, b_ = p2((0, o, sh_z + 1))[0], p2((1.5, o * .8, hip_z + 4))[0]
                cv.capsule(a_, b_, 1.0, 1.0, '3b2a1e', .32, flat=True)
    # arms (left arm nearer the camera in both views)
    for (sh, e, h, side) in ((shR, eR, hR, -1), (shL, eL, hL, 1)):
        sleeve = C.get('coat') or C['top']
        seg(sh, e, 3.4, 3.0, sleeve, bias=side * .4); seg(e, h, 3.0, 2.6, C.get('sleeve_lo', sleeve), bias=side * .4)
        ph_, dh = p2(h); cv.sphere(ph_, 2.6, C['skin'], dh + side * .4 + .1)
    if C.get('held') and view == 'front':
        ph_, dh = p2(hR); cv.capsule((ph_[0] - 1, ph_[1] - 4), (ph_[0] + 2, ph_[1] + 4), 3.2, 3.2, C['held'], dh + .6, flat=True)
    if P['glow']:
        ph_, dh = p2(hR)
        for rr, al in ((9, .25), (6, .5), (3.5, .95)):
            cv.sphere(ph_, rr * (0.7 + .3 * P['glow']), '9ff2c8' if rr < 5 else '58c49a', dh + 3 - rr * .1)
    # head
    hc, hdp = p2(head_c)
    cv.capsule(p2(neck)[0], (hc[0], hc[1] + 5), 2.6, 2.6, C['skin'], .2)
    cv.sphere(hc, 8.0, C['skin'], 1.0, squash=1.05)
    hair = C['hair']; hs = C.get('hair_style', 'short')
    if view == 'front':
        # hair cap over the back/top, face visible toward SE
        cv.sphere((hc[0] - 1.8, hc[1] - 2.2), 7.6, hair, 1.05, squash=.85)
        if hs in ('long', 'curly'):
            cv.capsule((hc[0] - 5, hc[1]), (hc[0] - 4, hc[1] + 10 + (4 if hs == 'long' else 1)), 4.2, 3.4, hair, .6)
        if hs == 'bun': cv.sphere((hc[0] - 5, hc[1] - 5), 3.2, hair, 1.1)
        cv.sphere((hc[0] + 2.0, hc[1] + 1.6), 5.8, C['skin'], 1.2)  # face plane (SE)
        ex = hc[0] + 3.8; ey = hc[1] + .6
        cv.pixel(ex, ey, '1d1612', 2); cv.pixel(ex - 3.2, ey - 1, '1d1612', 2)
        cv.pixel(ex - 1, ey + 3.8, C.get('mouth', '7a3b34'), 2)
        if C.get('brow'): cv.pixel(ex, ey - 2, hair, 2); cv.pixel(ex - 3.2, ey - 3, hair, 2)
        if C.get('glasses'):
            for gx_ in (ex, ex - 3.2):
                cv.pixel(gx_ - 1, ey, '2b2b2b', 2.1); cv.pixel(gx_ + 1, ey, '2b2b2b', 2.1)
            cv.pixel(ex - 1.6, ey - .5, '2b2b2b', 2.1)
        if C.get('moustache'): cv.pixel(ex - .5, ey + 2.6, hair, 2); cv.pixel(ex - 1.5, ey + 2.6, hair, 2); cv.pixel(ex - 2.5, ey + 2.4, hair, 2)
    else:
        cv.sphere((hc[0], hc[1] - .6), 8.1, hair, 1.3, squash=1.0)
        if hs in ('long', 'curly'): cv.capsule((hc[0], hc[1] + 2), (hc[0] - 1, hc[1] + 13 + (3 if hs == 'long' else 0)), 5.4, 4.2, hair, 1.25)
        if hs == 'bun': cv.sphere((hc[0], hc[1] - 6), 3.4, hair, 1.4)
    if C.get('cap'):
        cv.sphere((hc[0] - .5, hc[1] - 4), 8.2, C['cap'], 1.45, squash=.6)
        if view == 'front': cv.capsule((hc[0] + 3, hc[1] - 2.4), (hc[0] + 9, hc[1] - 1.2), 1.4, 1.2, C['cap'], 1.5, flat=True)
    if C.get('scarf'): cv.sphere((hc[0] - 1, hc[1] - 3.5), 8.4, C['scarf'], 1.42, squash=.55)
    if C.get('headphones'):
        cv.capsule(p2((0, 6, sh_z + 1))[0], p2((0, -6, sh_z + 1))[0], 1.6, 1.6, C['headphones'], .9, flat=True)
        cv.sphere(p2((0, 6, sh_z + 1))[0], 2.6, C['headphones'], 1.0)
    if C.get('stethoscope') and view == 'front':
        a_, b_ = p2((1, 5, sh_z - 1))[0], p2((1, -3, sh_z - 9))[0]
        cv.capsule(a_, b_, .8, .8, '2a2a2a', .5, flat=True); cv.sphere(b_, 1.6, 'b8bcbc', .55)
    if C.get('tape') and view == 'front':
        a_, b_ = p2((1, 6, sh_z))[0], p2((1, 4, sh_z - 12))[0]
        cv.capsule(a_, b_, 1.0, 1.0, 'd8c35a', .5, flat=True)
    return cv.image()

SPECS = {
    'hero':   dict(skin='c99a74', hair='4a3426', top='6b6a49', coat='5a6540', pants='343b4c', shoes='2d2520', backpack='5d4630', hair_style='short', brow=True, coat_len=4),
    'lia':    dict(skin='a8714f', hair='211814', top='4e8a86', coat='e9e7df', coat_len=18, pants='3a6c6a', shoes='e4e0d6', hair_style='bun', stethoscope=True),
    'raul':   dict(skin='8e5d3e', hair='1f1a17', top='4b5a3f', pants='3f4a35', shoes='1d1b18', belt='2b2620', cap='3a4632', moustache=True, held='2a2a2a'),
    'nora':   dict(skin='e0b394', hair='7a3e22', top='a1443a', pants='3a2f3f', skirt='4b3a52', shoes='3b2b22', hair_style='curly', headphones='2f2f33'),
    'helena': dict(skin='d6a688', hair='a7a29c', top='8b88a6', skirt='4f4c5f', pants='4f4c5f', shoes='3a3330', hair_style='short', glasses=True, held='c9b98c'),
    'bento':  dict(skin='b88462', hair='e8e4dc', top='e2d9c4', vest='6a5138', pants='4a4036', shoes='2d2620', brow=True, moustache=True, sleeve_lo='e2d9c4'),
    'celina': dict(skin='6b4431', hair='231a16', top='8a3f52', skirt='7a3446', pants='7a3446', shoes='3a2a24', apron='e8dfcf', scarf='c79a3a', tape=True, hair_style='bun'),
}

def sheet(key):
    rows = []
    for anim, n in ANIMS:
        for view in ('front', 'back'):
            rows.append((anim, view, [draw_char(SPECS[key], view, anim, i, n) for i in range(n)]))
    W = 8 * FW; H = len(rows) * FH
    im = Image.new('RGBA', (W, H)); meta = {}
    for r, (anim, view, frames) in enumerate(rows):
        for i, f in enumerate(frames): im.paste(f, (i * FW, r * FH))
        meta[f'{anim}:{view}'] = {'row': r, 'frames': len(frames)}
    return im, meta

def all_characters():
    out = []
    for key in SPECS:
        im, meta = sheet(key)
        out.append(Sprite('ch-' + key, im, FOOT, 'characters', frame=[FW, FH], anims=meta))
    return out
