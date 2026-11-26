"""V4 export: creatures atlas (sliced strips + single models), items atlas, puzzle panels, manifest, and the
generated /*V4:BEGIN*/ block in index.html.   python tools/asset-pipeline/v4_build.py"""
import json, re, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image
import v4_assets as V
from export import pack_atlases
from common import ROOT, PROD, Sprite

APPROVED_CREATURES = {'eco_humanoide', 'anomalia_esferica'}   # visually reviewed: clean frames, no labels
def nonempty(im): return im.getbbox() is not None and (np.array(im)[..., 3] > 0).sum() > 25

def main():
    an = V.creature_anims(); singles = V.single_sprites(); items = V.items(); panels = V.panels()
    sprites = []; frames = {}; manifest = {'source': 'fz-monstros-itens-enigmas-v4-completo.zip', 'creatures': {}, 'items': {}, 'puzzles': {}}
    for cr, acts in an.items():
        frames[cr] = {}
        for act, fr in acts.items():
            good = [f for f in fr if nonempty(f)]
            names = []
            for i, f in enumerate(good):
                n = f'{cr}:{act}:{i}'; w, h = f.size
                sprites.append(Sprite(n, f, (w // 2, h - 1), 'creatures')); names.append(n)
            frames[cr][act] = names
        manifest['creatures'][cr] = {'state': 'PRODUCTION' if cr in APPROVED_CREATURES else 'REVIEW',
                                     'animations': {a: len(v) for a, v in frames[cr].items()},
                                     'note': 'sliced from the V4 strips by minimum-occupancy columns' + ('' if cr in APPROVED_CREATURES else '; residues of sheet labels/cell borders, not promoted')}
    for k, im in singles.items():
        if nonempty(im): sprites.append(Sprite('single:' + k, im, (im.width // 2, im.height - 1), 'creatures'))
        manifest['creatures'].setdefault(k, {'state': 'REVIEW', 'animations': {}, 'note': 'single model or portrait'})
    for k, im in items.items():
        sprites.append(Sprite('item:' + k, im, (im.width // 2, im.height // 2), 'items'))
        manifest['items'][k] = {'state': 'PRODUCTION', 'size': list(im.size), 'source': 'inventario/' + k + '.png (alpha candidate, borders and label fragments removed)'}
    atl = pack_atlases(sprites, max_w=1024, max_h=2048)
    out = PROD / 'v4'; out.mkdir(parents=True, exist_ok=True)
    rects = {}; files = []
    for i, (im, r) in enumerate(atl):
        fn = f'assets/production/v4/atlas-{i}.png'; im.save(ROOT / fn, optimize=True); files.append(fn)
        for n, (x, y, w, h) in r.items(): rects[n] = [i, x, y, w, h]
    pz = {}
    for k, im in panels.items():
        fn = f'assets/production/v4/puzzle-{k}.png'; im.save(ROOT / fn, optimize=True); pz[k] = {'file': fn, 'w': im.width, 'h': im.height}
        manifest['puzzles'][k] = {'state': 'PRODUCTION (static panel art; moving parts drawn by the puzzle engine)', 'file': fn}
    data = {'atlases': files, 'atlasW': [im.width for im, _ in atl], 'rects': rects,
            'creatures': {cr: {a: [rects[n] for n in ns] for a, ns in acts.items()} for cr, acts in frames.items() if cr in APPROVED_CREATURES},
            'items': {k: rects['item:' + k] for k in items}, 'singles': {k[7:]: v for k, v in rects.items() if k.startswith('single:')}, 'panels': pz}
    for f in files: manifest.setdefault('atlas_sha256', {})[f] = hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
    (ROOT / 'assets' / 'manifests' / 'v4.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    js = 'var V4=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';'
    if '/*V4:BEGIN*/' in html: html = re.sub(r'/\*V4:BEGIN\*/.*?/\*V4:END\*/', lambda m: '/*V4:BEGIN*/' + js + '/*V4:END*/', html, flags=re.S)
    else:
        i = html.index('/*ART:END*/') + len('/*ART:END*/'); html = html[:i] + '/*V4:BEGIN*/' + js + '/*V4:END*/' + html[i:]
    (ROOT / 'index.html').write_text(html, encoding='utf-8', newline='\n')
    print('v4 atlases', files, 'sprites', len(sprites), 'items', len(items), 'panels', len(pz))

if __name__ == '__main__':
    main()
