"""V5 harmonized creatures (fz-harmonizado-v5-completo/monstros/<c>/sequence.png) -> frames, atlas, runtime block.

    python tools/asset-pipeline/v5_creatures.py

Transparent strips hold five sequences separated by wider gaps: idle, movimento, ataque, dano, dissipacao (the V4
action names). Strips that do not split into exactly five sequences, and the opaque block sheets (light background
with a grid), are reported and left to the V4 art. Frames keep their original resolution; each frame carries a draw
factor k so the on-screen height follows SCALE.creature (relative sizes: dog .4 ... colossus 3.2) and, for species
already animated in V4, the V4 on-screen height.
"""
import json, re, sys, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
import v6_segment as SEG
import v5_npcs as V

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'assets/review/chatgpt-import/fz-harmonizado-v5-completo/monstros'
FR = ROOT / 'assets/source/v5-creatures'
ATLAS = 'assets/production/creatures/v5/atlas.png'
ACTS = ['idle', 'movimento', 'ataque', 'dano', 'dissipacao']
# relative body size (SCALE.creature in index.html; echo = 1.05 is the reference humanoid)
SIZE = {'cao_anomalo': .4, 'inseto_fenda': .25, 'sombra_rasteira': .4, 'corvo_sombrio': .3, 'larva_eco': .25,
        'sentinela_drone': .55, 'eco_humanoide': 1.05, 'eco_corrompido': 1.0, 'mutante_floresta': 1.6,
        'guardiao_bunker': 1.9, 'colosso_ressonancia': 3.2, 'sombra_ressonante': .6, 'anomalia_esferica': .55,
        'anomalia_temporal': .8, 'cepa_esporal': .7, 'entidade_luz': .9, 'enxame': .5, 'espectro_infantil': .7,
        'mutacao_aquatica': 1.1}
ECHO_V4_H = 36  # on-screen height unit: the V4 echo frame (36 px) drawn at the panel scale


COUNTS = [5, 5, 5, 4, 6]  # frames per sequence in the V5 strips (idle, movimento, ataque, dano, dissipacao)


def frames_of(name):
    p = SRC / name / 'sequence.png'
    a = np.array(Image.open(p).convert('RGBA'))
    if (a[..., 3] > 200).mean() > .6:
        return None, 'opaque block sheet (background and grid need manual separation)'
    m = a[..., 3] > 40
    occ = m.sum(0)
    cols = np.nonzero(occ)[0]
    x0, x1 = cols.min(), cols.max()
    # empty column runs inside the strip; the four widest separate the five sequences
    runs, start = [], None
    for x in range(x0, x1 + 1):
        if occ[x] == 0 and start is None: start = x
        if occ[x] and start is not None: runs.append((start, x - 1)); start = None
    if len(runs) < 4:
        return None, 'sequences not separated'
    big = sorted(sorted(runs, key=lambda r: -(r[1] - r[0]))[:4])
    widths = sorted(r[1] - r[0] + 1 for r in runs)
    fifth = sorted(widths)[-5] if len(widths) >= 5 else 0
    narrow = min(r[1] - r[0] + 1 for r in big)
    if narrow < max(8, fifth * 1.3) and narrow < np.median(widths) * 1.5:
        return None, 'sequence boundaries not distinct'
    edges = [x0] + [v for r in big for v in (r[0], r[1] + 1)] + [x1 + 1]
    out = {}
    for act, n, (g0, g1) in zip(ACTS, COUNTS, zip(edges[0::2], edges[1::2])):
        w = g1 - g0; cuts = [0]
        for j in range(1, n):
            c = int(w * j / n); lo, hi = max(1, c - int(w / n * .3)), min(w - 1, c + int(w / n * .3))
            cuts.append(lo + int(np.argmin(occ[g0 + lo:g0 + hi])))
        cuts.append(w); fs = []
        for c0, c1 in zip(cuts, cuts[1:]):
            sub = a[:, g0 + c0:g0 + c1].copy(); sub[..., 3] = np.where(sub[..., 3] > 40, sub[..., 3], 0)
            bb = Image.fromarray(sub).getbbox()
            if not bb: return None, f'empty frame in {act}'
            sub = sub[bb[1]:bb[3], bb[0]:bb[2]]
            keep = V.main_component(sub[..., 3] > 0)  # drops slivers of the neighbouring frame, keeps particles over the body
            sub[..., 3] = np.where(keep, sub[..., 3], 0)
            bb = Image.fromarray(sub).getbbox(); fs.append(sub[bb[1]:bb[3], bb[0]:bb[2]])
        out[act] = fs
    return out, None


def main():
    data, report, rows = {}, {}, []
    V4 = json.loads(re.search(r'var V4=(\{.*?\});', (ROOT / 'index.html').read_text(encoding='utf-8'), re.S).group(1))
    for d in sorted(p.name for p in SRC.iterdir() if (p / 'sequence.png').exists()):
        fr, why = frames_of(d)
        if fr is None:
            report[d] = why; continue
        idle_h = float(np.median([f.shape[0] for f in fr['idle']]))
        v4 = V4['creatures'].get(d)
        target = (float(np.median([r[4] for r in v4['idle']])) if v4 else ECHO_V4_H * SIZE.get(d, 1.0) / 1.05)
        k = round(target / idle_h, 4)
        for act, fs in fr.items():
            for i, f in enumerate(fs):
                q = FR / d / act / f'{i + 1:02d}.png'; q.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(f).save(q, optimize=True)
            rows.append((d, act, fs))
        data[d] = {'k': k, 'frames': {a: len(f) for a, f in fr.items()}}
        report[d] = 'integrated'
    W = max(sum(f.shape[1] + 2 for f in fs) for _, _, fs in rows)
    H = sum(max(f.shape[0] for f in fs) + 2 for _, _, fs in rows)
    sheet = Image.new('RGBA', (W, H)); y = 0; creatures = {}
    for d, act, fs in rows:
        x = 0; h = max(f.shape[0] for f in fs); lst = []
        for f in fs:
            sheet.alpha_composite(Image.fromarray(f), (x, y + h - f.shape[0]))
            lst.append([-1, x, y + h - f.shape[0], f.shape[1], f.shape[0], data[d]['k']]); x += f.shape[1] + 2
        creatures.setdefault(d, {})[act] = lst; y += h + 2
    (ROOT / ATLAS).parent.mkdir(parents=True, exist_ok=True); sheet.save(ROOT / ATLAS, optimize=True)
    man = {'source': 'fz-harmonizado-v5-completo.zip (monstros/*/sequence.png)', 'atlas': ATLAS,
           'sha256': hashlib.sha256((ROOT / ATLAS).read_bytes()).hexdigest(), 'frames_dir': 'assets/source/v5-creatures/',
           'creatures': {d: {**v, 'state': 'PRODUCTION'} for d, v in data.items()},
           'not_integrated': {d: r for d, r in report.items() if r != 'integrated'}}
    (ROOT / 'assets/manifests/v5-creatures.json').write_text(json.dumps(man, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    js = ('(function(){if(typeof V4==="undefined")return;const ix=V4.atlases.push(' + json.dumps(ATLAS) + ')-1;const C='
          + json.dumps(creatures, separators=(',', ':')) + ';for(const c in C)for(const a in C[c])for(const r of C[c][a])r[0]=ix;Object.assign(V4.creatures,C)})();')
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    if '/*V5CR:BEGIN*/' in html:
        html = re.sub(r'/\*V5CR:BEGIN\*/.*?/\*V5CR:END\*/', lambda m: '/*V5CR:BEGIN*/' + js + '/*V5CR:END*/', html, flags=re.S)
    else:
        m = re.search(r'var V4=\{.*?\};', html, re.S); html = html[:m.end()] + '/*V5CR:BEGIN*/' + js + '/*V5CR:END*/' + html[m.end():]
    (ROOT / 'index.html').write_text(html, encoding='utf-8', newline=chr(10))
    for d, r in report.items(): print(f'{d:22} {r}')


if __name__ == '__main__':
    main()
