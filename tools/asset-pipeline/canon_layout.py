"""Vale do Cedro, canon edition. Same grid and gameplay cells as layout.py; canon buildings cover ~2x2 cells
visually (the site/house cell is the FRONT cell, the building extends over x-1 and y-1 behind it)."""
import re
from pathlib import Path
import layout as L

N = L.N
SITES = L.SITES
SITE_SPRITE = {'radio': 'b-uncle', 'clinic': 'b-clinic', 'rail': 'b-station', 'guard': 'b-guard', 'future': 'b-radio'}
SITE_SIGN = {}

ROADS = {
    'cobble': [('row', 6, 2, 17), ('col', 5, -5, 18)],
    'plaza':  [('rect', 4, 5, 6, 7)],
    'dirt':   [('row', 4, 4, 10), ('row', 10, 5, 10), ('col', 2, 7, 8), ('col', 9, -5, 0)],
}

# decor buildings: (sprite, front cell x, y, label for docs)
DECOR_BUILDINGS = [
    ('b-archive', 2, 8, 'Arquivo municipal'),
    ('h-bento', 2, 1, 'Casa e relojoaria de Bento'), ('h-helena', 4, 11, 'Casa de Helena'),
    ('h-celina', 10, 8, 'Casa e ateliê de Celina'), ('h-red', 9, 1, 'Residência'), ('h-teal', 12, 1, 'Residência'),
    ('h-slate', 8, 13, 'Residência'), ('h-brown', 2, 13, 'Residência'), ('h-ruin', 2, 11, 'Casa abandonada'),
]
DECOR_BLOCK = [
    ('tree-green', 4, 0), ('tree-autumn', 13, 7), ('tree-pink', 13, 5), ('tree-green', 13, 3), ('tree-pine', 0, 12),
    ('tree-pink', 6, 9), ('tree-autumn', 10, 12), ('tree-green', 12, 8), ('tree-pine', 13, 1), ('tree-green', 6, 13),
    ('tree-autumn', 3, 7), ('rock', 12, 5),
]
PROPS = [
    # plaza market + furniture
    ('stall', 4, 5, 0, -.6), ('kiosk', 6, 5, .6, -.6), ('bench', 4, 7, -.4, .8), ('bench-b', 6, 7, .8, .4),
    ('flowers', 5, 7, 1.0, 1.1), ('flowers', 4, 6, -1.1, 1.0), ('bin', 6, 6, 1.2, -1.1), ('notice', 5, 5, -1.2, -1.2),
    ('hydrant', 7, 6, 0, 1.3), ('bike', 3, 5, -.5, .6), ('signpost', 5, 8, 1.2, 0),
    # street lamps
    ('lamp', 2, 6, 0, -1.3), ('lamp', 4, 6, 0, 1.3), ('lamp', 7, 6, 0, -1.3), ('lamp', 10, 6, 0, 1.3), ('lamp', 12, 6, 0, -1.3),
    ('lamp', 5, 2, -1.3, 0), ('lamp', 5, 10, 1.3, 0), ('lamp', 9, 10, 0, 1.3), ('lamp', 0, 3, 1.0, .9),
    # direction signs (canon)
    ('sign-estacao', 3, 6, 0, -1.2), ('sign-clinica', 7, 4, 0, -1.2), ('sign-radio', 6, 10, 1.1, 0), ('sign-centro', 5, 4, -1.2, 0),
    # houses: fences, gardens
    ('fence-wood', 3, 1, 0, .9), ('flowers', 3, 2, .6, .6), ('barrel', 1, 2, .5, .8), ('bush', 4, 11, -.5, .4),
    ('fence-wood', 11, 8, 0, .9), ('flowers', 11, 9, -.6, -.6), ('bush', 9, 2, 1.0, 0), ('fence-wood', 12, 2, 0, .2),
    ('bush', 8, 12, -.5, 0), ('bike', 9, 13, 0, 0), ('wall-stone', 2, 13, 0, .6), ('flowers', 1, 12, 1, 1),
    # station side: crates, barrels
    ('crate-a', 0, 4, .7, -.9), ('crate-b', 0, 8, .8, .7), ('barrel-b', 0, 9, .6, .2), ('cabinet', 2, 7, -.6, -.9),
    # guard post / clinic / radio details
    ('crate-a', 12, 4, .2, .9), ('barrel', 11, 5, 1.0, .9), ('bench', 9, 4, 0, -1.0), ('flowers', 9, 3, .8, .9),
    ('bin', 8, 11, -.6, -.6), ('flowers', 7, 12, -.4, .5),
    # abandoned corner + lake shore + nature
    ('branches', 2, 10, .2, .2), ('log', 1, 10, 0, .4), ('grass-tall', 2, 9, .9, .9), ('grass-bush', 0, 10, .6, .6),
    ('grass-tall', 10, 9, .8, .8), ('grass-tall', 10, 11, .9, -.2), ('grass-bush', 10, 10, 1.0, 1.0), ('rock', 9, 12, .5, .5),
    ('bush', 3, 12, .5, 0), ('grass-bush', 7, 0, 0, 0), ('bush', 1, 4, -.5, -.6), ('grass-tall', 12, 3, 0, 0), ('flowers', 8, 0, 0, 0),
]
LIGHTS = [(p[1], p[2], p[3], p[4], 3.0, 150, 'lamp') for p in PROPS if p[0] == 'lamp'] + [(0, 6, .5, 0, 3.0, 170, 'lamp'), (11, 4, -1, -1, 3.5, 190, 'lamp')]

def footprint(x, y):
    return [(x, y), (x - 1, y), (x, y - 1), (x - 1, y - 1)]

def blocked_cells(index_html=None):
    used, near_sites, test_paths = _protected(index_html)
    cells = {}
    for s, x, y, _ in DECOR_BUILDINGS:
        for c in footprint(x, y):
            if c == (x, y) or (_free(c, used, near_sites, test_paths)): cells[c] = s
    for (site, (x, y)) in SITES.items():
        for c in footprint(x, y)[1:]:
            if _free(c, used, near_sites, test_paths): cells[c] = 'site:' + site
    for s, x, y in DECOR_BLOCK: cells[(x, y)] = s
    return cells

def _free(c, used, near_sites, test_paths):
    x, y = c
    return 0 <= x < N and 0 <= y < N and c not in used and c not in near_sites and c not in test_paths and c not in SITES.values() and not (x > 10 and y > 8)

_cache = {}
def _protected(index_html=None):
    key = str(index_html)
    if key in _cache: return _cache[key]
    src = Path(index_html or (L.ROOT / 'index.html')).read_text(encoding='utf-8')
    used = {(int(a), int(b)) for a, b in re.findall(r'x:(\d+),y:(\d+)', src)}
    used |= {(int(b), int(c)) for a, b, c in re.findall(r'\[(\d+),(\d+),(\d+)\]', src)}
    near_sites = {(sx + dx, sy + dy) for sx, sy in SITES.values() for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
    test_paths = {(7, y) for y in range(4, 11)} | {(x, 4) for x in range(2, 8)} | {(6, 5), (2, 5), (2, 6), (3, 4), (3, 5), (4, 5)}
    _cache[key] = (used, near_sites, test_paths); return _cache[key]

def validate(index_html):
    used, near_sites, test_paths = _protected(index_html)
    errors = []
    fronts = {(x, y): s for s, x, y, _ in DECOR_BUILDINGS} | {(x, y): s for s, x, y in DECOR_BLOCK}
    for (x, y), s in fronts.items():
        if not _free((x, y), used, near_sites, test_paths): errors.append(f'{s} front cell {x},{y} is protected')
    # visual footprints must not overlap each other, sites, the rail column or the cobble streets
    vis = {}
    for s, x, y, _ in DECOR_BUILDINGS: vis[s + f'@{x},{y}'] = footprint(x, y)
    for site, (x, y) in SITES.items(): vis['site:' + site] = footprint(x, y)
    seen = {}
    for k, cells in vis.items():
        for c in cells:
            if c in seen and not k.startswith('site:rail'): errors.append(f'{k} overlaps {seen[c]} at {c}')
            seen[c] = k
            if not k.startswith('site:') and (c[1] == 6 or c[0] == 5 or c[0] <= 0): errors.append(f'{k} covers street/rail at {c}')
    for s, x, y in DECOR_BLOCK:
        if (x, y) in seen: errors.append(f'{s} at {x},{y} inside {seen[(x, y)]}')
    blk = set(blocked_cells(index_html))
    base_ok = lambda x, y: 0 <= x < N and 0 <= y < N and not (x > 10 and y > 8) and (x, y) not in SITES.values()
    start = (5, 5); reach = {start}; q = [start]
    while q:
        x, y = q.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in reach and base_ok(*n) and n not in blk: reach.add(n); q.append(n)
    for p in used:
        if base_ok(*p) and p not in blk and p not in reach: errors.append(f'NPC cell {p} unreachable')
    for p in near_sites:
        if base_ok(*p) and p not in reach: errors.append(f'site doorstep {p} unreachable')
    return errors
