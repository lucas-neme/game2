"""Vale do Cedro layout: the single source for the baked ground and for the engine's decor + collisions.

Grid: playable cells 0..13 (index.html), lake where x>10 and y>8, rail on column x=0, station platform on the
east half of x=0 for y 4..8. World = grid -5..18; outside 0..13 everything is scenery baked into the ground.
Placements: (sprite, x, y, dx, dy) with dx/dy in metres from the cell centre (cells are 3 m).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
N = 14
SITES = {'radio': (3, 3), 'clinic': (8, 3), 'rail': (1, 6), 'guard': (11, 4), 'future': (7, 11)}
SITE_SPRITE = {'radio': 'b-uncle', 'clinic': 'b-clinic', 'rail': 'b-station', 'guard': 'b-guard', 'future': 'b-radio'}
SITE_SIGN = {'clinic': 'sign-clinic', 'future': 'sign-radio', 'guard': 'sign-guard', 'rail': 'sign-station'}

# roads (visual only): cobble main street y=6, cobble avenue x=5, plaza 4..6 x 5..7, dirt lanes
ROADS = {
    'cobble': [('row', 6, 1, 17), ('col', 5, -5, 18), ('rect', 4, 5, 6, 7)],
    'dirt':   [('row', 4, 1, 10), ('row', 10, 5, 10), ('col', 2, 7, 13), ('row', 12, 2, 5), ('col', 9, -5, 0)],
}

# blocking decor buildings (cell)  -> sprite, optional sign
DECOR_BUILDINGS = [
    ('b-archive', 4, 8, 'sign-archive'),
    ('b-bento-home', 1, 2, None), ('b-bento-shop', 1, 3, 'sign-watch'),
    ('b-helena-home', 3, 10, None),
    ('b-celina-shop', 9, 5, 'sign-tailor'), ('b-celina-home', 10, 7, None),
    ('b-grocery', 8, 5, 'sign-grocery'), ('b-bar', 8, 7, 'sign-bar'),
    ('b-workshop', 12, 7, 'sign-workshop'),
    ('b-abandoned', 1, 9, None),
    ('b-house-a', 9, 1, None), ('b-house-b', 7, 1, None), ('b-house-c', 12, 1, None),
    ('b-house-d', 6, 12, None), ('b-house-e', 2, 12, None), ('b-house-f', 4, 1, None),
]
# blocking vegetation / objects (cell)
DECOR_BLOCK = [
    ('tree-oak-a', 2, 0), ('tree-mango', 11, 0), ('tree-ipe', 13, 5), ('tree-jacaranda', 10, 2),
    ('tree-oak-a', 13, 4), ('tree-cypress', 3, 7), ('tree-ipe', 2, 8), ('tree-mango', 10, 12), ('tree-oak-b', 8, 12),
    ('tree-dead', 1, 11), ('tree-dry', 0, 13), ('tree-oak-a', 4, 13), ('tree-jacaranda', 8, 10),
    ('transformer', 9, 9), ('pylon', 8, 9), ('statue', 4, 7), ('crates', 13, 8), ('tree-oak-b', 6, 9),
    ('well', 12, 2),
]
# non-blocking props: sprite, x, y, dx, dy (metres)
PROPS = [
    # station platform: canopy over (0,4..8), clock, benches, crates, signal
    ('canopy', 0, 3, 0, 0), ('canopy', 0, 4, 0, 0), ('canopy', 0, 5, 0, 0), ('canopy', 0, 6, 0, 0), ('canopy', 0, 7, 0, 0), ('canopy-end', 0, 8, 0, 0),
    ('station-clock', 0, 6, 1.1, 1.3), ('bench-y', 0, 5, .9, .3), ('bench-y', 0, 7, .9, -.2), ('crates', 0, 4, .7, -.9),
    ('signal', 0, 10, .6, 0), ('barrels', 0, 9, .8, .2), ('lamp', 0, 3, 1.0, .9),
    # main street lamps (north/south kerbs) and plaza furniture
    ('lamp', 2, 6, 0, -1.3), ('lamp', 4, 6, 0, 1.3), ('lamp', 7, 6, 0, -1.3), ('lamp', 10, 6, 0, 1.3), ('lamp', 12, 6, 0, -1.3),
    ('lamp', 5, 2, -1.3, 0), ('lamp', 5, 9, 1.3, 0), ('lamp', 5, 12, -1.3, 0), ('lamp', 6, 4, 0, -1.3), ('lamp', 9, 10, 0, 1.3),
    ('bench-x', 6, 5, .2, -1.1), ('bench-x', 4, 5, 0, -1.1), ('bench-y', 6, 7, 1.1, 0), ('planter-red', 6, 6, 1.1, -1.0),
    ('planter-white', 4, 6, -1.1, 1.1), ('bin', 5, 7, 1.2, 1.2), ('mailbox', 6, 4, 1.1, 1.0),
    # houses: fences, gardens, everyday clutter
    ('fence-x+', 1, 1, 0, 0), ('fence-y-', 2, 1, 0, 0), ('shrub-flower-red', 2, 1, 0, .4), ('bin', 2, 3, -1.2, -.6),
    ('fence-x+', 3, 11, 0, 0), ('shrub-flower-white', 4, 11, -.4, 0), ('planter-red', 3, 9, -.9, 1.0),
    ('fence-y+', 11, 7, 0, 0), ('shrub-a', 11, 8, 0, -.6), ('barrels', 11, 6, .3, -1.0),
    ('fence-x+', 9, 0, 0, 0), ('fence-x+', 12, 0, 0, 0), ('shrub-b', 8, 1, 0, 0), ('shrub-flower-red', 6, 0, 0, 0),
    ('fence-x-', 6, 13, 0, 0), ('grass-a', 7, 13, 0, 0), ('shrub-a', 1, 13, .3, 0),
    # clinic / radio / guard post details
    ('bench-x', 8, 4, -.6, -.6), ('planter-white', 7, 3, .8, .8), ('antenna', 8, 11, -.6, -.9), ('bin', 7, 12, -.9, 0),
    ('barrier', 10, 4, .2, -.4), ('floodlight', 12, 4, -.9, -.8), ('crates', 11, 5, 1.0, .8), ('mailbox', 2, 4, .9, -1.2),
    # substation yard fence, workshop yard
    ('chain-x-', 8, 9, 0, 0), ('chain-x-', 9, 9, 0, 0), ('chain-y+', 9, 9, 0, 0), ('chain-x+', 9, 9, 0, 0), ('chain-x+', 8, 9, 0, 0),
    ('tires', 13, 7, .2, -.2), ('barrels', 12, 6, .9, 1.0), ('crate', 13, 6, 0, .9),
    # abandoned corner
    ('grass-b', 1, 10, 0, 0), ('grass-a', 2, 9, 0, .5), ('crate', 1, 8, -.6, .9), ('reeds-a', 10, 9, .8, .8), ('reeds-a', 10, 11, .9, -.2),
    ('grass-a', 3, 1, .5, .5), ('grass-b', 11, 3, 0, 0), ('grass-a', 6, 10, 0, 0), ('grass-b', 12, 5, 0, 0),
    ('shrub-b', 3, 12, .5, 0), ('shrub-flower-white', 13, 3, -.3, 0), ('grass-a', 0, 12, .7, 0),
]
# lights: (x, y, dx, dy, height m, radius px, kind)
LIGHTS = [(p[1], p[2], p[3], p[4], 3.1, 150, 'lamp') for p in PROPS if p[0] == 'lamp'] + [
    (0, 6, .5, 0, 3.0, 170, 'lamp'), (0, 4, .5, 0, 3.0, 140, 'lamp'), (12, 4, -.9, -.8, 4.0, 210, 'flood')]

# ---- baked scenery outside the playable 14x14 ----
OUTER = []
def _outer():
    import random
    r = random.Random(1998)
    trees = ['tree-oak-a', 'tree-oak-b', 'tree-mango', 'tree-cypress', 'tree-oak-a', 'tree-oak-b', 'tree-mango', 'tree-dry', 'tree-oak-a', 'tree-mango', 'tree-ipe']
    for x in range(-5, 19):
        for y in range(-5, 19):
            if 0 <= x < N and 0 <= y < N: continue
            if x in (0, -1, -2) or (x == 5 and y < 0) or (x == 9 and y < 0) or (y == 6 and x >= N): continue  # rail, roads
            back = x < 0 or y < 0
            if back and not (x > 10 and y > 8):
                if r.random() < .72:
                    OUTER.append((r.choice(trees), x, y, r.uniform(-.8, .8), r.uniform(-.8, .8)))
            elif not back and not (x > 10 and y > 8):
                if (x + y) % 3 == 0 and r.random() < .35: OUTER.append(('shrub-a', x, y, r.uniform(-1, 1), r.uniform(-1, 1)))
    OUTER.extend([('water-tower', -2, 4, 0, 0), ('boxcar', -2, 10, 0, 0), ('signal', -1, 2, .6, 0), ('crates', -2, 7, 0, 0),
                  ('pylon', 7, -2, 0, 0), ('pylon', 10, -2, 0, 0), ('pylon', 13, -2, 0, 0), ('pylon', 16, -2, 0, 0),
                  ('b-house-e', 15, 3, 0, 0), ('b-house-a', 16, 5, 0, 0), ('b-house-f', 15, 7, 0, 0), ('fence-x+', 14, 3, 0, 0),
                  ('b-house-c', 3, 15, 0, 0), ('b-house-b', 6, 16, 0, 0)])
_outer()

def blocked_cells():
    cells = {(x, y): s for s, x, y, _ in DECOR_BUILDINGS}
    cells.update({(x, y): s for s, x, y in DECOR_BLOCK})
    return cells

def validate(index_html):
    """Decor must not sit on NPC/event coordinates, roads, site doorsteps, test paths or the lake,
    and every cell that was walkable before must stay reachable from the start cell (5,5)."""
    src = Path(index_html).read_text(encoding='utf-8')
    used = {(int(a), int(b)) for a, b in re.findall(r'x:(\d+),y:(\d+)', src)}
    used |= {(int(b), int(c)) for a, b, c in re.findall(r'\[(\d+),(\d+),(\d+)\]', src)}
    test_paths = {(7, y) for y in range(4, 11)} | {(x, 4) for x in range(2, 8)} | {(6, 5), (2, 5), (2, 6), (3, 4), (3, 5), (4, 5)}
    near_sites = {(sx + dx, sy + dy) for sx, sy in SITES.values() for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
    errors = []
    for (x, y), s in blocked_cells().items():
        if not (0 <= x < N and 0 <= y < N): errors.append(f'{s} {x},{y} outside')
        if (x, y) in used: errors.append(f'{s} {x},{y} on an NPC/event cell')
        if (x, y) in near_sites: errors.append(f'{s} {x},{y} on a site doorstep')
        if (x, y) in test_paths: errors.append(f'{s} {x},{y} on a regression-test path')
        if (x, y) in SITES.values(): errors.append(f'{s} {x},{y} on a site')
        if x > 10 and y > 8: errors.append(f'{s} {x},{y} in the lake')
    if len(blocked_cells()) != len(DECOR_BUILDINGS) + len(DECOR_BLOCK): errors.append('two decor objects share a cell')
    base_ok = lambda x, y: 0 <= x < N and 0 <= y < N and not (x > 10 and y > 8) and (x, y) not in SITES.values()
    blk = set(blocked_cells())
    seen = {(5, 5)}; q = [(5, 5)]
    while q:
        x, y = q.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and base_ok(*n) and n not in blk: seen.add(n); q.append(n)
    unreachable = [(x, y) for x in range(N) for y in range(N) if base_ok(x, y) and (x, y) not in blk and (x, y) not in seen]
    if unreachable: errors.append(f'unreachable cells: {unreachable}')
    for p in used:
        if base_ok(*p) and p not in seen: errors.append(f'NPC cell {p} unreachable')
    return errors
