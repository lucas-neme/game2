"""Hand-reviewed classification of the V5 NPC sheets (row.index from each npcs/<id>/manifest.json).
Reviewed visually on labelled grids (browser-evidence/v5/grids). Frames cut at the source are excluded.
'side' sequences are drawn facing SIDE_FACES[npc]; the opposite direction is the horizontal mirror.
Missing art is listed in MISSING and not faked."""
def r(row, a, b): return [(row, i) for i in range(a, b + 1)]

SEQ = {
 'lia': {'idle:south': r(1, 1, 4), 'idle:north': r(3, 1, 4), 'idle:side': r(2, 1, 4),
         'walk:side': r(2, 5, 8), 'walk:north': r(3, 5, 8), 'talk:south': r(5, 1, 4), 'talk:side': r(6, 1, 4),
         'sit': r(9, 1, 8), 'stand': r(9, 9, 12)},
 'raul': {'idle:south': r(1, 1, 4), 'idle:north': r(1, 5, 6), 'idle:side': r(1, 9, 12),
          'walk:south': r(2, 1, 6), 'walk:north': [(3, 2), (3, 3), (3, 4), (3, 5), (3, 8), (3, 9), (3, 10), (3, 11)],
          'walk:side': r(4, 1, 8), 'talk:south': r(5, 1, 4), 'talk:side': r(5, 9, 12), 'sit': r(7, 1, 6), 'stand': r(7, 9, 12)},
 'nora': {'idle:south': r(1, 1, 4), 'idle:side': r(2, 1, 4), 'idle:north': r(4, 1, 4),
          'walk:south': r(5, 1, 8), 'walk:side': r(6, 1, 8), 'walk:north': r(8, 1, 8),
          'talk:south': r(9, 1, 4), 'talk:side': r(10, 1, 4), 'sit': r(13, 1, 6), 'stand': r(13, 7, 8)},
 'helena': {'idle:south': r(1, 1, 4), 'walk:south': r(1, 9, 12), 'idle:north': r(2, 1, 4), 'walk:north': r(2, 8, 11),
            'idle:side': r(3, 1, 4), 'walk:side': r(4, 5, 12), 'talk:south': r(5, 1, 4), 'talk:side': r(7, 1, 4),
            'sit': r(9, 1, 8), 'stand': r(9, 9, 13)},
 'bento': {'idle:south': r(1, 1, 4), 'walk:south': r(2, 1, 4), 'idle:side': r(1, 5, 8), 'walk:side': r(3, 5, 12),
           'idle:north': r(1, 13, 16), 'walk:north': r(2, 16, 21), 'talk:south': r(5, 1, 4), 'work:side': r(4, 5, 12),
           'sit': r(6, 1, 8), 'stand': r(6, 11, 13)},
 'celina': {'idle:south': r(1, 1, 4), 'walk:south': r(2, 1, 8), 'idle:side': r(1, 5, 8), 'walk:side': r(4, 1, 8),
            'idle:north': r(1, 13, 16), 'walk:north': r(5, 1, 8), 'talk:south': r(6, 1, 4), 'work:side': r(6, 5, 12),
            'sit': r(10, 1, 8), 'stand': r(10, 9, 12)},
}
# relative height vs the protagonist (1.0 = same apparent height); natural variation, never stretched
HEIGHT = {'lia': .97, 'raul': 1.04, 'nora': .95, 'helena': .96, 'bento': .94, 'celina': .95}
SIDE_FACES = {}      # filled by measurement in v5_build (verified on the preview)
MISSING = {
 'lia': ['walk:south (sheet has no front walk cycle; idle front frames are used while walking south)'],
 'raul': [], 'nora': [], 'helena': [], 'bento': [], 'celina': [],
 'all': ['diagonal views', 'use-item / examine poses per profession (Bento clocks: only work:side; Lia, Nora, Helena: none drawn)',
         'sit facing south/north (all sit frames are side views)']}
