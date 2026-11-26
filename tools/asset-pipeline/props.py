"""Props, street furniture, station pieces, signs. Built with isomodel (metres; cell = 3 m x 3 m).
Anchor = model origin (0,0,0) = the cell centre the prop stands on, unless noted."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from isomodel import Model, M, Material, proj, PX
from common import Sprite, rgba

FONT_PATHS = ['C:/Windows/Fonts/bahnschrift.ttf', 'C:/Windows/Fonts/georgiab.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']

def font(size):
    for p in FONT_PATHS:
        try: return ImageFont.truetype(p, size)
        except OSError: pass
    return ImageFont.load_default()

def S(name, model, category='props', collision=None, seed=0, **kw):
    im, anc = model.render(seed=seed, **kw)
    return Sprite(name, im, anc, category, collision=collision)

def lamp_post(lit=False):
    m = Model()
    m.box(-.18, -.18, 0, .18, .18, .35, 'iron')
    m.cyl(0, 0, .35, 3.4, .06, 'iron')
    m.box(-.05, -.05, 3.3, .05, .55, 3.38, 'iron')
    m.box(-.16, .40, 2.95, .16, .72, 3.28, Material('f2d593', amp=.02) if lit else Material('b9b39a', amp=.03))
    m.box(-.2, .36, 3.28, .2, .76, 3.36, 'iron')
    return m

def bench(axis='x'):
    m = Model()
    L = 1.6
    def B(x0, y0, z0, x1, y1, z1, mat):
        if axis == 'x': m.box(x0, y0, z0, x1, y1, z1, mat)
        else: m.box(y0, x0, z0, y1, x1, z1, mat)
    for lx in (-L / 2 + .1, L / 2 - .2):
        B(lx, -.2, 0, lx + .1, .25, .45, 'iron'); B(lx, -.25, .45, lx + .1, -.18, .95, 'iron')
    for k in range(3):
        B(-L / 2, -.2 + k * .15, .45, L / 2, -.08 + k * .15, .52, 'wood')
    for k in range(2):
        B(-L / 2, -.27, .62 + k * .16, L / 2, -.2, .72 + k * .16, 'wood')
    return m

def crate(size=.8):
    m = Model(); m.box(-size / 2, -size / 2, 0, size / 2, size / 2, size, 'wood_pale')
    m.box(-size / 2 - .01, size / 2 - .01, .08, size / 2 + .01, size / 2 + .01, .16, 'wood_dark', faces=('left',))
    m.box(-size / 2 - .01, size / 2 - .01, size - .16, size / 2 + .01, size / 2 + .01, size - .08, 'wood_dark', faces=('left',))
    return m

def crate_stack():
    m = Model()
    for (x, y, z, s) in ((-.5, -.3, 0, .8), (.35, -.35, 0, .7), (-.2, .45, 0, .75), (-.45, -.3, .8, .7)):
        m.box(x - s / 2, y - s / 2, z, x + s / 2, y + s / 2, z + s, 'wood_pale' if (x + y) > 0 else 'wood')
    return m

def barrel(mat='rust'):
    m = Model(); m.cyl(0, 0, 0, .95, .3, mat)
    for z in (.18, .72): m.cyl(0, 0, z, z + .05, .305, 'iron', cap=False)
    return m

def barrels():
    m = Model()
    for (x, y, mat) in ((-.35, -.3, 'rust'), (.3, -.25, 'paint_blue'), (-.1, .38, 'rust')):
        m.cyl(x, y, 0, .95, .3, mat); m.cyl(x, y, .7, .75, .305, 'iron', cap=False)
    return m

def trash_bin():
    m = Model(); m.cyl(0, 0, 0, .85, .25, 'paint_green'); m.cyl(0, 0, .85, .9, .27, 'iron'); return m

def mailbox():
    m = Model(); m.box(-.06, -.06, 0, .06, .06, 1.0, 'iron'); m.box(-.25, -.2, 1.0, .25, .2, 1.55, 'yellow'); return m

def planter(flower='c0503c'):
    m = Model(); m.box(-.6, -.35, 0, .6, .35, .45, 'stone'); m.box(-.55, -.3, .45, .55, .3, .5, 'soil')
    r = np.random.default_rng(3)
    for _ in range(14):
        x, y = r.uniform(-.5, .5), r.uniform(-.25, .25)
        m.cyl(x, y, .5, .62 + r.uniform(0, .1), .07, 'leaves')
        if r.random() < .6: m.cyl(x, y, .66, .72, .05, Material(flower, amp=.08))
    return m

def fence(edge='x+', mat='wood', posts=5):
    """Fence on one cell edge: 'x+' = edge at y=+1.5 running along x (screen lower-left edge),
    'y+' = edge at x=+1.5 running along y, 'x-'/'y-' the back edges."""
    m = Model(); h = 1.0
    off = 1.42 if edge.endswith('+') else -1.42
    for i in range(posts):
        t = -1.5 + 3 * i / (posts - 1)
        if edge[0] == 'x': m.box(t - .05, off - .05, 0, t + .05, off + .05, h + .08, 'wood_dark')
        else: m.box(off - .05, t - .05, 0, off + .05, t + .05, h + .08, 'wood_dark')
    for z in (.35, .78):
        if edge[0] == 'x': m.box(-1.5, off - .03, z, 1.5, off + .03, z + .1, mat)
        else: m.box(off - .03, -1.5, z, off + .03, 1.5, z + .1, mat)
    return m

def low_wall(edge='x+'):
    m = Model(); off = 1.38 if edge.endswith('+') else -1.38
    if edge[0] == 'x': m.box(-1.5, off - .12, 0, 1.5, off + .12, .6, 'stone')
    else: m.box(off - .12, -1.5, 0, off + .12, 1.5, .6, 'stone')
    return m

def canopy_segment(end=False):
    """Platform canopy over cell (0,k): platform occupies x in [-.1, 1.5] of that cell."""
    m = Model(); z = 3.3
    for (x, y) in ((.15, -1.2), (1.25, -1.2)) + (((.15, 1.2), (1.25, 1.2)) if end else ()):
        m.box(x - .07, y - .07, 0, x + .07, y + .07, z, 'iron')
        m.box(x - .2, y - .2, 0, x + .2, y + .2, .12, 'concrete')
    m.box(-.35, -1.5, z, 1.55, 1.5, z + .12, Material('7d5138', amp=.12, stripe=3.0, stripe_dark=.72))
    m.box(-.35, -1.5, z - .22, -.25, 1.5, z, 'paint_cream', faces=('left', 'right', 'top'))
    m.box(1.45, -1.5, z - .22, 1.55, 1.5, z, 'paint_cream', faces=('left', 'right', 'top'))
    return m

def station_clock():
    m = Model(); m.cyl(0, 0, 0, 2.9, .07, 'iron'); m.box(-.3, -.3, 0, .3, .3, .2, 'concrete')
    m.cyl(0, 0, 2.9, 3.0, .12, 'iron')
    m.box(-.36, -.08, 3.0, .36, .08, 3.62, 'black')
    m.box(-.32, .08, 3.04, .32, .1, 3.58, 'paint_cream', faces=('left',))
    return m

def signal_mast():
    m = Model(); m.box(-.25, -.25, 0, .25, .25, .3, 'concrete'); m.box(-.05, -.05, .3, .05, .05, 4.2, 'iron')
    m.box(-.18, .05, 3.3, .18, .14, 4.1, 'black')
    m.box(-.1, .14, 3.85, .1, .16, 4.0, Material('c44a3a', amp=.02), faces=('left',))
    m.box(-.1, .14, 3.5, .1, .16, 3.65, Material('5aa06a', amp=.02), faces=('left',))
    m.box(.05, -.05, 2.6, .9, .03, 2.75, 'paint_cream')
    return m

def water_tower():
    m = Model()
    for (x, y) in ((-.9, -.9), (.9, -.9), (-.9, .9), (.9, .9)):
        m.box(x - .1, y - .1, 0, x + .1, y + .1, 4.5, 'wood_dark')
    m.box(-1, -1, 2.2, 1, 1, 2.3, 'wood_dark')
    m.cyl(0, 0, 4.5, 7.0, 1.25, 'wood')
    for z in (4.9, 5.8, 6.6): m.cyl(0, 0, z, z + .08, 1.27, 'iron', cap=False)
    m.cyl(0, 0, 7.0, 7.35, 1.32, 'rust')
    return m

def boxcar():
    """Abandoned freight wagon lying along y over two cells (origin = centre of the first cell)."""
    m = Model()
    m.box(-1.0, -1.4, .3, 1.0, 4.4, .55, 'iron')
    for y in (-.8, .6, 2.4, 3.8): m.box(-.95, y - .3, 0, -.75, y + .3, .45, 'black'); m.box(.75, y - .3, 0, .95, y + .3, .45, 'black')
    m.box(-1.0, -1.4, .55, 1.0, 4.4, 3.2, 'rust')
    m.box(.98, .7, .7, 1.02, 2.3, 2.9, 'wood_dark', faces=('right',))
    m.box(-1.05, -1.45, 3.2, 1.05, 4.45, 3.35, 'iron')
    return m

def transformer():
    m = Model(); m.box(-.9, -.6, 0, .9, .6, .25, 'concrete'); m.box(-.7, -.45, .25, .7, .45, 1.6, 'steel')
    for k in range(5): m.box(.7, -.4 + k * .2, .4, .82, -.34 + k * .2, 1.45, 'steel', faces=('right', 'top'))
    for x in (-.4, 0, .4): m.cyl(x, 0, 1.6, 2.3, .07, Material('9a6b4a', amp=.05)); m.cyl(x, 0, 2.3, 2.38, .1, 'steel')
    return m

def pylon():
    m = Model()
    for (x, y) in ((-.5, -.5), (.5, -.5), (-.5, .5), (.5, .5)):
        m.box(x - .05, y - .05, 0, x + .05, y + .05, 6.0, 'steel')
    for z in (1.5, 3.0, 4.5, 6.0): m.box(-.55, -.55, z, .55, .55, z + .07, 'steel', faces=('left', 'right'))
    m.box(-1.6, -.08, 5.6, 1.6, .08, 5.75, 'steel')
    return m

def chainlink(edge='x+'):
    m = Model(); off = 1.4 if edge.endswith('+') else -1.4
    for i in range(4):
        t = -1.5 + i
        if edge[0] == 'x': m.box(t - .04, off - .04, 0, t + .04, off + .04, 2.0, 'steel')
        else: m.box(off - .04, t - .04, 0, off + .04, t + .04, 2.0, 'steel')
    for z in (.2, 1.0, 1.9):
        if edge[0] == 'x': m.box(-1.5, off - .01, z, 1.5, off + .01, z + .04, 'steel')
        else: m.box(off - .01, -1.5, z, off + .01, 1.5, z + .04, 'steel')
    return m

def tires():
    m = Model()
    for (x, y, z) in ((0, 0, 0), (0, 0, .25), (.7, -.2, 0)):
        m.cyl(x, y, z, z + .24, .38, 'black'); m.cyl(x, y, z + .24, z + .25, .18, Material('1b1b1b', amp=.02))
    return m

def barrier():
    m = Model(); m.box(-.15, -.15, 0, .15, .15, 1.1, 'paint_cream')
    for i in range(6):
        m.box(.15 + i * .38, -.05, .85, .53 + i * .38, .05, .97, 'paint_red' if i % 2 == 0 else 'paint_cream')
    return m

def floodlight():
    m = Model(); m.box(-.06, -.06, 0, .06, .06, 4.2, 'iron'); m.box(-.3, -.1, 4.0, .3, .25, 4.35, 'black')
    m.box(-.25, .25, 4.05, .25, .27, 4.3, 'lamp', faces=('left',))
    return m

def antenna():
    m = Model()
    for (x, y) in ((-.25, -.25), (.25, -.25), (-.25, .25), (.25, .25)):
        m.poly([(x, y, 0), (x * .2, y * .2, 6), (x * .2 + .02, y * .2, 6), (x + .04, y, 0)], 'steel', .9)
    for z in np.arange(.6, 6, .8): m.box(-.25 + z * .033, -.25 + z * .033, z, .25 - z * .033, .25 - z * .033, z + .04, 'steel', faces=('left', 'right'))
    m.cyl(0, 0, 6, 6.6, .03, 'steel'); m.cyl(0, 0, 6.6, 6.72, .08, Material('d04a36', amp=.02))
    return m

def well():
    m = Model(); m.cyl(0, 0, 0, .8, .75, 'stone'); m.cyl(0, 0, .8, .82, .6, Material('243a42', amp=.05))
    for x in (-.65, .65): m.box(x - .06, -.06, .8, x + .06, .06, 2.0, 'wood_dark')
    m.box(-.8, -.06, 1.95, .8, .06, 2.05, 'wood_dark')
    m.poly([(-.85, -.5, 2.0), (.85, -.5, 2.0), (.85, 0, 2.55), (-.85, 0, 2.55)], 'rust', .9)
    m.poly([(-.85, 0, 2.55), (.85, 0, 2.55), (.85, .5, 2.0), (-.85, .5, 2.0)], 'rust', .75)
    return m

def bandstand_statue():
    m = Model(); m.box(-.8, -.8, 0, .8, .8, .3, 'stone'); m.box(-.55, -.55, .3, .55, .55, 1.4, 'stone')
    m.box(-.62, -.62, 1.4, .62, .62, 1.52, 'stone')
    m.cyl(0, 0, 1.52, 2.5, .22, Material('5d6e62', amp=.12)); m.cyl(0, 0, 2.5, 2.85, .16, Material('5d6e62', amp=.12))
    return m

def text_sign(text, width_m=2.8, height_m=.8, board='5a3e2a', ink='efe2bd', facing='left'):
    """Painted board. facing 'left' = parallel to the x axis (on a building's +y face),
    'right' = parallel to the y axis (on the +x face). Returns a Sprite anchored at the board's bottom-centre point."""
    tw, th = int(width_m * 40), int(height_m * 40)
    im = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bc = tuple(int(board[i:i + 2], 16) for i in (0, 2, 4))
    d.rectangle([0, 0, tw - 1, th - 1], fill=bc + (255,), outline=tuple(int(c * .55) for c in bc) + (255,), width=2)
    size = th - 8
    f = font(size)
    while d.textlength(text, font=f) > tw - 10 and size > 8: size -= 1; f = font(size)
    ic = tuple(int(ink[i:i + 2], 16) for i in (0, 2, 4))
    d.text((tw / 2, th / 2 + 1), text, fill=ic + (255,), font=f, anchor='mm')
    # map the flat board onto the iso face: u along the face (metres -> px via proj), v up
    ux, uy = proj(1, 0, 0) if facing == 'left' else proj(0, -1, 0)
    sx = ux * width_m / tw; sy = uy * width_m / tw; vy = -PX * height_m / th
    W = int(abs(ux * width_m)) + 4; H = int(abs(uy * width_m) + PX * height_m) + 4
    oy = (abs(uy * width_m) if uy < 0 else 0) + PX * height_m + 2
    # inverse affine: output (X,Y) -> input (u,v):  X = sx*u + 2 ; Y = oy + sy*u + vy*(th - v)... solve
    a, b, c = 1 / sx, 0, -2 / sx
    # Y = oy + sy*u - PX*height*(1 - v/th)  ->  v = (Y - oy - sy*u)/(PX*height/th) + th
    k = PX * height_m / th
    d_, e_, f_ = -sy / (sx * k), 1 / k, th - (oy - sy * 2 / sx) / k
    out = im.transform((W, H), Image.AFFINE, (a, b, c, d_, e_, f_), resample=Image.BICUBIC)
    arr = np.array(out); arr[..., 3] = np.where(arr[..., 3] > 100, 255, 0)
    out = Image.fromarray(arr)
    return Sprite('sign', out, (W // 2, int(oy + sy * width_m / 2)), 'signs')

SIGNS = {
    'sign-clinic': ('CLÍNICA SÃO LUCAS', 2.4, '2c4a5e', 'f0ece0'),
    'sign-radio': ('RÁDIO VALE 103,7', 2.4, '6b2a24', 'f2dfb8'),
    'sign-guard': ('POSTO DE VIGILÂNCIA', 2.6, '2f3a2c', 'e9e2c8'),
    'sign-station': ('VALE DO CEDRO', 2.6, '24384a', 'f0e6c8'),
    'sign-archive': ('ARQUIVO MUNICIPAL', 2.6, '3b3326', 'eadbb3'),
    'sign-watch': ('RELOJOARIA', 2.0, '4a2f22', 'e8c98a'),
    'sign-grocery': ('MERCEARIA', 2.0, '2e4a2c', 'efe3be'),
    'sign-bar': ('BAR DO PONTO', 2.0, '5c2121', 'f3d9a0'),
    'sign-workshop': ('OFICINA', 2.0, '3a3a3a', 'e7c34a'),
    'sign-tailor': ('ATELIÊ DE COSTURA', 2.4, '5a2f45', 'f1dfd0'),
}

def all_props():
    out = [
        S('lamp', lamp_post(), collision=None), S('lamp-lit', lamp_post(True)),
        S('bench-x', bench('x')), S('bench-y', bench('y')),
        S('crate', crate()), S('crates', crate_stack(), collision='cell'), S('barrel', barrel()), S('barrels', barrels(), collision='cell'),
        S('bin', trash_bin()), S('mailbox', mailbox()), S('planter-red', planter()), S('planter-white', planter('e8e2cf')),
        S('fence-x+', fence('x+')), S('fence-y+', fence('y+')), S('fence-x-', fence('x-')), S('fence-y-', fence('y-')),
        S('wall-x+', low_wall('x+')), S('wall-y+', low_wall('y+')),
        S('canopy', canopy_segment()), S('canopy-end', canopy_segment(True)),
        S('station-clock', station_clock()), S('signal', signal_mast()), S('water-tower', water_tower(), collision='cell'),
        S('boxcar', boxcar(), collision='cells'), S('transformer', transformer(), collision='cell'), S('pylon', pylon(), collision='cell'),
        S('chain-x+', chainlink('x+')), S('chain-y+', chainlink('y+')), S('chain-x-', chainlink('x-')), S('chain-y-', chainlink('y-')),
        S('tires', tires()), S('barrier', barrier()), S('floodlight', floodlight()), S('antenna', antenna()),
        S('well', well(), collision='cell'), S('statue', bandstand_statue(), collision='cell'),
    ]
    for name, (txt, w, bg, ink) in SIGNS.items():
        sp = text_sign(txt, 2.8, .8, bg, ink, 'left'); sp.name = name; out.append(sp)
    return out
