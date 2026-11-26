"""Interiors rendered with the iso modeller (same light, palette and outline as the town).
Each room returns (image 1280x720, {hotspot label: (x%, y%)}) so the game's investigable objects sit on the props."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from isomodel import Model, Material, M, proj, PX
from props import font

W, H = 1280, 720

def mat(c, **k): return Material(c, **k)
PLASTER = mat('9c8f78', amp=.06, scale=3); PLASTER2 = mat('7d8a7a', amp=.06, scale=3)
WAINS = mat('5b3d29', amp=.08, stripe=3.0); FLOOR_WOOD = mat('6e4c33', amp=.10, stripe=3.2, stripe_dark=.78)
TILE = mat('8a8577', amp=.08); TILE2 = mat('6f6a5e', amp=.08)

def room_shell(m, X, Y, Hh, wall=PLASTER, floor=FLOOR_WOOD, wains=True, tiles=False):
    if tiles:
        for i in range(int(X)):
            for j in range(int(Y)):
                m.box(i, j, -.1, i + 1, j + 1, 0, TILE if (i + j) % 2 == 0 else TILE2, faces=('top',))
    else:
        m.box(0, 0, -.1, X, Y, 0, floor, faces=('top',))
    m.box(-.2, 0, 0, 0, Y, Hh, wall, faces=('right',))      # left back wall (x=0 plane)
    m.box(0, -.2, 0, X, 0, Hh, wall, faces=('left',))       # right back wall (y=0 plane)
    if wains:
        m.box(-.18, 0, 0, .02, Y, 1.0, WAINS, faces=('right', 'top'))
        m.box(0, -.18, 0, X, .02, 1.0, WAINS, faces=('left', 'top'))
    m.box(-.16, 0, 0, .04, Y, .12, M['wood_dark'], faces=('right',)); m.box(0, -.16, 0, X, .04, .12, M['wood_dark'], faces=('left',))

def window_left(m, y0, y1, z0, z1, night=True):
    m.box(-.15, y0 - .1, z0 - .1, .05, y1 + .1, z1 + .1, M['wood_dark'], faces=('right',))
    m.box(-.12, y0, z0, .06, y1, z1, mat('3d5b78' if night else '9fb6c0', amp=.05), faces=('right',))
    m.box(-.1, (y0 + y1) / 2 - .03, z0, .07, (y0 + y1) / 2 + .03, z1, M['wood_dark'], faces=('right',))
    m.box(-.1, y0, (z0 + z1) / 2 - .03, .07, y1, (z0 + z1) / 2 + .03, M['wood_dark'], faces=('right',))

def shelf_right(m, x0, x1, z, depth=.35):
    m.box(x0, 0, z, x1, depth, z + .05, M['wood'])
    r = np.random.default_rng(int(x0 * 10 + z * 7))
    x = x0 + .05
    while x < x1 - .1:
        w = r.uniform(.06, .14); h = r.uniform(.22, .36)
        m.box(x, .03, z + .05, x + w, depth - .05, z + .05 + h, mat(r.choice(['7a2f2a', '2f4f6a', '5a6a3a', '8a6a3a', '3a3a3a', 'b4a27a']), amp=.06))
        x += w + .01

def render_room(m, extra=None, light=None):
    im, anc = m.render(shadow=False, outline=True, pad=20)
    # fit into 1280x720 on a dark backdrop
    sc = min((W - 20) / im.width, (H - 4) / im.height) * 1.08
    im2 = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    out = Image.new('RGBA', (W, H), (14, 19, 19, 255))
    ox, oy = (W - im2.width) // 2, (H - im2.height) // 2 + 6
    out.alpha_composite(im2, (ox, oy))
    def to_screen(x, y, z):
        px, py = proj(x, y, z); return (anc[0] + px) * sc + ox, (anc[1] + py) * sc + oy
    if light:
        a = np.array(out).astype(float)
        yy, xx = np.mgrid[0:H, 0:W]
        for (lx, ly, lz, rad, col, k) in light:
            sx, sy = to_screen(lx, ly, lz)
            d = np.sqrt((xx - sx) ** 2 + ((yy - sy) * 1.4) ** 2) / rad
            g = np.clip(1 - d, 0, 1) ** 1.6 * k
            a[..., :3] += g[..., None] * np.array(col)
        vig = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .7)) ** 2)
        a[..., :3] *= np.clip(1.12 - vig * .55, .45, 1.05)[..., None]
        out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    if extra: extra(out, to_screen)
    return out, to_screen

def study():
    m = Model(); X, Y, Hh = 6.0, 5.0, 3.2
    room_shell(m, X, Y, Hh)
    window_left(m, 1.2, 2.6, 1.3, 2.6)
    # rug
    m.box(1.6, 1.4, 0, 4.4, 3.8, .02, mat('6b2e2a', amp=.12, stripe=2.2, stripe_dark=.8), faces=('top',))
    # desk with tape deck (left side, under the window) + chair + desk lamp
    m.box(.5, .9, .72, 1.55, 3.0, .8, M['wood_dark'])
    for (x, y) in ((.55, .95), (1.45, .95), (.55, 2.9), (1.45, 2.9)): m.box(x, y, 0, x + .08, y + .08, .72, M['wood_dark'])
    m.box(.6, 1.1, 0, 1.5, 1.8, .72, M['wood_dark'])  # drawers
    m.box(.75, 1.35, .8, 1.25, 1.95, .98, mat('2b2b2b', amp=.04))  # tape deck
    m.box(.8, 1.45, .98, 1.2, 1.85, 1.0, mat('8a8f8a', amp=.03))
    m.box(.9, 2.1, .8, 1.25, 2.55, .86, M['paper']); m.box(.88, 2.15, .86, 1.2, 2.5, .88, M['paper'])
    m.cyl(.85, 2.75, .8, 1.35, .03, 'iron'); m.box(.75, 2.65, 1.3, 1.0, 2.9, 1.42, mat('2f5a3a', amp=.04))
    m.box(1.75, 1.9, 0, 2.2, 2.35, .45, M['wood']); m.box(1.75, 1.9, .45, 2.2, 1.97, 1.0, M['wood'])  # chair
    # bookshelves on the right back wall + photo frame + cork board with red string
    m.box(.2, 0, 0, 2.2, .4, 2.2, M['wood_dark']); shelf_right(m, .25, 2.15, .4); shelf_right(m, .25, 2.15, 1.05); shelf_right(m, .25, 2.15, 1.7)
    m.box(3.6, -.02, 1.55, 4.3, .06, 2.35, mat('a07a3a', amp=.05), faces=('left',))
    m.box(3.68, .02, 1.63, 4.22, .08, 2.27, mat('c9b48a', amp=.08), faces=('left',))
    m.box(2.5, -.02, 1.2, 3.4, .05, 2.2, mat('9a7a52', amp=.15, scale=1.2), faces=('left',))  # cork board
    # agenda on a side table (front left)
    m.box(1.0, 3.7, 0, 1.8, 4.5, .6, M['wood']); m.box(1.15, 3.85, .6, 1.6, 4.3, .67, mat('7a2f2a', amp=.04))
    # safe (front right) + filing cabinet
    m.box(4.6, 3.4, 0, 5.5, 4.3, .95, mat('5f6966', amp=.07)); m.box(5.5, 3.55, .25, 5.53, 4.15, .75, mat('3c4442', amp=.04), faces=('right',))
    m.cyl(5.53, 3.85, .45, .5, .1, 'brass')
    m.box(5.2, .3, 0, 5.9, 1.1, 1.3, mat('6d7a72', amp=.06))
    m.box(2.3, 3.3, 0, 2.7, 3.7, .45, M['paper']); m.box(2.25, 3.25, 0, 2.75, 3.75, .02, M['paper'], faces=('top',))
    pins = {}
    def extra(out, S):
        d = ImageDraw.Draw(out)
        a, b = S(2.6, .06, 2.0), S(3.3, .06, 1.4); c_ = S(2.75, .06, 1.35)
        for p, q in ((a, b), (a, c_), (c_, S(3.2, .06, 2.05))): d.line([p, q], fill=(178, 40, 36), width=2)
        for p in (a, b, c_, S(3.2, .06, 2.05)): d.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=(200, 60, 50))
        for k, (x, y) in enumerate(((2.65, 1.85), (2.95, 1.55), (3.15, 1.9))):
            p = S(x, .07, y); d.rectangle([p[0] - 7, p[1] - 9, p[0] + 7, p[1] + 5], fill=(224, 214, 190))
        pins.update({'Fita cassete': S(1.0, 1.65, 1.0), 'Fotografia': S(3.95, .05, 1.95), 'Cofre de aço': S(5.05, 3.85, .95), 'Agenda': S(1.4, 4.1, .67)})
    out, _ = render_room(m, extra, light=[(.9, 2.8, 1.35, 260, (120, 95, 40), 1.0), (0, 1.9, 2.0, 340, (30, 45, 70), .8)])
    return out, {k: (round(x / W * 100, 1), round(y / H * 100, 1)) for k, (x, y) in pins.items()}

def station_hall():
    m = Model(); X, Y, Hh = 7.0, 5.5, 3.6
    room_shell(m, X, Y, Hh, wall=PLASTER2, wains=False, tiles=True)
    m.box(-.18, 0, 0, .02, Y, 1.1, mat('5d6b5e', amp=.06), faces=('right', 'top'))
    m.box(0, -.18, 0, X, .02, 1.1, mat('5d6b5e', amp=.06), faces=('left', 'top'))
    # platform edge opening on the front-left with rails (floor drops)
    m.box(-.1, 4.2, -.1, X, Y, 0, mat('4f4a40', amp=.15), faces=('top',))
    for k in range(9): m.box(k * .8, 4.55, 0, k * .8 + .25, 5.4, .05, mat('4b3b2c', amp=.1))
    for y in (4.75, 5.2): m.box(0, y - .03, .05, X, y + .03, .12, M['steel'])
    m.box(0, 4.1, 0, X, 4.2, .02, M['yellow'], faces=('top',))
    # ticket booth on the right back wall
    m.box(4.0, 0, 0, 6.2, 1.0, 2.6, M['wood_dark']); m.box(4.3, .98, 1.1, 5.9, 1.02, 2.1, mat('233340', amp=.04), faces=('left',))
    for k in range(6): m.box(4.35 + k * .3, .99, 1.1, 4.39 + k * .3, 1.04, 2.1, M['brass'], faces=('left',))
    m.box(4.2, 1.0, 1.0, 6.0, 1.35, 1.06, M['wood'])
    # clock on the left wall, timetable board, posters
    m.cyl(.02, 1.4, 2.35, 2.45, .02, 'iron')
    m.box(-.05, 3.0, 1.6, .06, 4.3, 2.7, mat('1d2a28', amp=.03), faces=('right',))
    # benches, cart, crates, signal cabinet (centre)
    for y in (1.0, 2.4):
        m.box(.4, y, .42, 1.0, y + 1.0, .5, M['wood']); m.box(.35, y, .5, .42, y + 1.0, 1.0, M['wood'])
        for dy in (.05, .9): m.box(.45, y + dy, 0, .95, y + dy + .06, .42, M['iron'])
    m.box(5.4, 2.8, .3, 6.5, 3.9, .38, M['wood']); m.cyl(5.5, 2.9, 0, .3, .12, 'black', cap=False); m.cyl(6.4, 3.8, 0, .3, .12, 'black', cap=False)
    m.box(5.6, 3.0, .38, 6.2, 3.6, .9, M['wood_pale']); m.box(5.55, 3.05, .9, 6.0, 3.5, 1.2, M['fabric'])
    m.box(4.7, 2.0, 0, 5.4, 2.7, .7, M['wood_pale']); m.box(4.8, 2.1, .7, 5.3, 2.6, .73, M['paper'])
    m.box(3.0, 1.9, 0, 3.8, 2.5, 1.7, mat('3f5a4c', amp=.06)); m.box(3.8, 1.98, .3, 3.83, 2.42, 1.5, mat('2c3f36', amp=.04), faces=('right',))
    for k, c in enumerate(('c44a3a', 'd9b04a', '6aa07a')):
        m.box(3.83, 2.05 + k * .13, 1.25, 3.9, 2.12 + k * .13, 1.38, mat(c, amp=.02), faces=('right', 'top'))
    for k in range(3): m.box(3.2 + k * .2, 2.2, 1.7, 3.25 + k * .2, 2.25, 2.2, M['iron'])
    pins = {}
    def extra(out, S):
        d = ImageDraw.Draw(out)
        cx, cy = S(.02, 1.4, 2.4); d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(226, 218, 196), outline=(40, 40, 36), width=3)
        d.line([(cx, cy), (cx + 3, cy - 18)], fill=(30, 30, 30), width=3); d.line([(cx, cy), (cx + 12, cy + 4)], fill=(30, 30, 30), width=2)
        f = font(13); p = S(-.05, 3.65, 2.55); d.text((p[0] - 30, p[1] + 4), 'PARTIDAS', fill=(230, 200, 120), font=f)
        for k in range(4):
            q = S(-.05, 3.65, 2.35 - k * .18); d.line([(q[0] - 40, q[1] + 6), (q[0] + 30, q[1] + 22)], fill=(150, 170, 150), width=2)
        pins.update({'Trilhos': S(2.0, 4.95, .1), 'Bilheteria': S(5.1, 1.0, 1.6), 'Relógio parado': (cx, cy), 'Manifesto rasgado': S(5.05, 2.35, .73), 'Armário de sinalização': S(3.85, 2.2, 1.3)})
    out, _ = render_room(m, extra, light=[(5.1, 1.2, 1.8, 300, (90, 80, 50), .9), (3.5, 5.0, .5, 420, (25, 40, 60), .7)])
    return out, {k: (round(x / W * 100, 1), round(y / H * 100, 1)) for k, (x, y) in pins.items()}
