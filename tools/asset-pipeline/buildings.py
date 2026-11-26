"""SBS buildings at 1:1 (footprint = one 128x64 cell). Faces are the pack's 64x96 wall modules (one face per
tile, 64 px per storey) keyed from the teal background; roofs are the 143x92 roof tiles, aligned by the measured
eave diamond (centre 71,55). Night variants light a seeded subset of the dark window pixels."""
import io, zipfile
import numpy as np
from PIL import Image
from common import Sprite

def key_teal(im):
    a = np.array(im.convert('RGBA')).astype(int)
    d = np.abs(a[..., 0]) + np.abs(a[..., 1] - 128) + np.abs(a[..., 2] - 128)
    a[..., 3] = np.where(d < 40, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')

class Pack:
    def __init__(self, zip_path):
        z = zipfile.ZipFile(zip_path)
        rd = lambda n: Image.open(io.BytesIO(z.read(n))).convert('RGB')
        self.sheets = {k: rd(f'Building Tiles/Isometric Buildings {k} - 64x96.png') for k in (1, 2, 3)}
        self.roofs = rd('Roof Tiles/Isometric Town Roofing - 143x92.png')
        self.license = z.read('License.txt').decode('utf-8', 'replace')
    def face(self, code):
        s, n = int(code[1]), int(code[3:]) - 1
        r, c = divmod(n, 18)
        return key_teal(self.sheets[s].crop((c * 64, r * 96, c * 64 + 64, r * 96 + 96)))
    def roof(self, code):
        n = int(code[1:]) - 1; r, c = divmod(n, 3)
        return key_teal(self.roofs.crop((c * 143, r * 92, c * 143 + 143, r * 92 + 92)))

def compose(pack, floors, roof):
    n = len(floors)
    W, H = 143, 39 + 64 * (n - 1) + 96
    im = Image.new('RGBA', (W, H))
    for i, (l, r) in enumerate(floors):
        y0 = 39 + (n - 1 - i) * 64
        im.alpha_composite(pack.face(l), (7, y0)); im.alpha_composite(pack.face(r), (71, y0))
    walls = im.copy()
    if roof: im.alpha_composite(pack.roof(roof), (0, 39 - 55))
    return im, walls, (71, 39 + (n - 1) * 64 + 63)

def night_glow(walls, seed):
    """Warm light for a seeded subset of window panes: dark, low-saturation pixels inside the wall area."""
    a = np.array(walls).astype(float); rgb = a[..., :3]; alpha = a[..., 3]
    lum = rgb @ np.array([.299, .587, .114])
    dark = (alpha > 0) & (lum < 62)
    # group panes by a coarse grid so whole windows light up together
    r = np.random.default_rng(seed)
    H, W = lum.shape; gy, gx = np.mgrid[0:H, 0:W]
    cell = (gx // 9) * 1000 + (gy // 11)
    lit_cells = {c for c in np.unique(cell[dark]) if r.random() < .42}
    m = dark & np.isin(cell, list(lit_cells))
    out = np.zeros((H, W, 4))
    warm = np.array([255, 196, 112]) * (0.75 + .25 * r.random((H, W, 1)))
    out[..., :3] = warm; out[..., 3] = np.where(m, 230, 0)
    return Image.fromarray(out.astype(np.uint8), 'RGBA')

# building id -> (floors ground-first, roof, curated source note)
BUILDINGS = {
    'uncle':    ([('B1-121', 'B1-122'), ('B1-123', 'B1-124')], 'R01', 'Casa do tio (curadoria B1-121..124 + R01)'),
    'radio':    ([('B2-061', 'B2-064'), ('B2-063', 'B2-062')], 'R02', 'Rádio comunitária (B2-061..064 + R02)'),
    'clinic':   ([('B1-079', 'B1-080'), ('B1-081', 'B1-082'), ('B1-083', 'B1-084')], 'R05', 'Clínica (B1-079..084 + R05)'),
    'guard':    ([('B1-111', 'B1-110'), ('B1-113', 'B1-114')], 'R04', 'Posto de vigilância (B1-109..114 + R04)'),
    'station':  ([('B1-077', 'B1-078'), ('B1-077', 'B1-078')], 'R11', 'Estação (B1-077/078 + R11) + cobertura/plataforma próprias'),
    'archive':  ([('B2-003', 'B2-004'), ('B2-001', 'B2-002')], 'R05', 'Arquivo municipal (B2-001..004 + R05)'),
    'bento-home': ([('B1-037', 'B1-038'), ('B1-037', 'B1-038')], 'R01', 'Casa de Bento (B1-037/038 + R01)'),
    'bento-shop': ([('B2-081', 'B2-082')], 'R04', 'Relojoaria de Bento (B2-081/082 + R04)'),
    'helena-home': ([('B1-115', 'B1-116'), ('B1-119', 'B1-120')], 'R02', 'Casa de Helena (B1-115..120 + R02)'),
    'celina-home': ([('B1-039', 'B1-040'), ('B1-039', 'B1-040')], 'R01', 'Casa de Celina (B1-039/040 + R01)'),
    'celina-shop': ([('B2-079', 'B2-080')], 'R02', 'Ateliê de costura (B2-079/080 + R02)'),
    'grocery':  ([('B2-083', 'B2-084'), ('B1-073', 'B1-074')], 'R03', 'Mercearia (B2-083/084, B1-073/074 + R03)'),
    'bar':      ([('B2-077', 'B2-078')], 'R02', 'Bar do Ponto (B2-077/078 + R02)'),
    'workshop': ([('B2-115', 'B2-116')], 'R11', 'Oficina (B2-115/116 + R11)'),
    'abandoned': ([('B3-007', 'B3-008'), ('B3-011', 'B3-012')], 'R06', 'Casa abandonada (B3-007/008, B3-011/012 + R06)'),
    'house-a':  ([('B1-073', 'B1-074')], 'R02', 'Residência (B1-073/074 + R02)'),
    'house-b':  ([('B1-075', 'B1-076'), ('B1-075', 'B1-076')], 'R04', 'Residência (B1-075/076 + R04)'),
    'house-c':  ([('B1-117', 'B1-118')], 'R01', 'Residência (B1-117/118 + R01)'),
    'house-d':  ([('B3-079', 'B3-080'), ('B3-079', 'B3-080')], 'R05', 'Residência (B3-079/080 + R05)'),
    'house-e':  ([('B3-003', 'B3-004')], 'R03', 'Residência (B3-003/004 + R03)'),
    'house-f':  ([('B3-001', 'B3-002')], 'R01', 'Residência (B3-001/002 + R01)'),
}

def all_buildings(pack):
    out = []
    for i, (key, (floors, roof, note)) in enumerate(BUILDINGS.items()):
        im, walls, anchor = compose(pack, floors, roof)
        faces = ', '.join(f'{l}/{r}' for l, r in floors)
        out.append(Sprite('b-' + key, im, anchor, 'architecture', source=f'SBS Isometric Town Pack (CC0): {faces} + {roof}', collision='cell', note=note))
        out.append(Sprite('n-' + key, night_glow(walls, 100 + i), anchor, 'lighting', source='derived from SBS faces (window mask)'))
    return out
