"""Named canon sprites for production (state APPROVED unless noted). Source: frequencia-zero-canon.zip only.
Each entry: name -> (PIL RGBA, anchor (x, y) at the ground contact point, category, source, state, note)."""
import numpy as np
from PIL import Image
import canon_assets as A

C = A.CANON

def keep_main(im, min_frac=.04):
    """Drop stray fragments of neighbouring cells: keep components with >= min_frac of the largest."""
    a = np.array(im.convert('RGBA')); m = a[..., 3] > 0; H, W = m.shape
    lab = np.zeros((H, W), int); sizes = []
    for y0 in range(H):
        for x0 in range(W):
            if m[y0, x0] and not lab[y0, x0]:
                sizes.append(0); k = len(sizes); st = [(y0, x0)]; lab[y0, x0] = k
                while st:
                    y, x = st.pop(); sizes[k - 1] += 1
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < H and 0 <= xx < W and m[yy, xx] and not lab[yy, xx]: lab[yy, xx] = k; st.append((yy, xx))
    if not sizes: return im
    big = max(sizes); keep = {i + 1 for i, s in enumerate(sizes) if s >= big * min_frac}
    a[..., 3] = np.where(np.isin(lab, list(keep)), a[..., 3], 0)
    out = Image.fromarray(a); return out.crop(out.getbbox())

def deglow(im):
    """Remove the dim warm halo around lit lamps (keeps glass, metal and outline)."""
    a = np.array(im.convert('RGBA')).astype(int); rgb = a[..., :3]; mx = rgb.max(-1); mn = rgb.min(-1)
    halo = (rgb[..., 0] > rgb[..., 1]) & (rgb[..., 1] > rgb[..., 2]) & (mx < 165) & (mx - mn > 22) & (mx - mn < 95)
    a[..., 3] = np.where(halo, 0, a[..., 3])
    out = Image.fromarray(a.astype(np.uint8)); return keep_main(out, .15)

def base_anchor(im, frac=.5):
    """Ground point: bottom-most opaque row, horizontally centred on that row's span."""
    a = np.array(im)[..., 3] > 0
    ys = np.nonzero(a.any(1))[0]; y = ys[-1]
    xs = np.nonzero(a[max(0, y - 2):y + 1].any(0))[0]
    return (int(xs.min() + (xs.max() - xs.min()) * frac), int(y))

def obj(name, rel, cat, anchor=None, fix=None, state='APPROVED', note=''):
    im = A.dehalo(Image.open(C / rel)); im = keep_main(im, .08)
    if fix: im = fix(im)
    return name, (im, anchor or base_anchor(im), cat, f'canon:{rel}', state, note)

def sheet_obj(name, sheet, idx, cat, cut=True, fix=None, state='APPROVED', note=''):
    path = C / 'folhas' / f'{sheet}.png'
    comps = A.components_split(path)
    box, im = comps[idx]
    if cut: im = A.cutout(Image.open(path), box)
    im = keep_main(im, .05)
    if fix: im = fix(im)
    return name, (im, base_anchor(im), cat, f'canon:folhas/{sheet}.png#{idx}', state, note)

def building(name, rel, front_frac=.5, note=''):
    im = keep_main(A.dehalo(Image.open(C / 'construcoes' / rel)), .02)
    return name, (im, base_anchor(im, front_frac), 'architecture', f'canon:construcoes/{rel}', 'APPROVED', note)

def grid_icons(rel, n, cat, names):
    """Icons laid out in equal slots (inventory/weather strips)."""
    im = Image.open(C / rel).convert('RGBA'); W, H = im.size; out = []
    for i in range(n):
        x0 = int(W * i / n); x1 = int(W * (i + 1) / n)
        sub = im.crop((x0, 0, x1, H))
        a = np.array(sub).astype(int); rgb = a[..., :3]; mx = rgb.max(-1); mn = rgb.min(-1)
        a[..., 3] = np.where((mx < 62) & (mx - mn < 32), 0, 255)
        s = Image.fromarray(a.astype(np.uint8)); s = keep_main(s, .1)
        out.append((names[i], (s, (s.width // 2, s.height), cat, f'canon:{rel}#{i}', 'APPROVED', '')))
    return out

def catalog():
    items = dict([
        building('b-uncle', 'casa_tio.png'), building('b-radio', 'radio.png'), building('b-clinic', 'clinica.png'),
        building('b-guard', 'posto.png'), building('b-station', 'estacao.png', .55), building('b-archive', 'arquivo.png'),
        obj('tree-green', 'objetos/arvore_verde.png', 'vegetation'), obj('tree-autumn', 'objetos/arvore_outono.png', 'vegetation'),
        obj('tree-pink', 'objetos/arvore_rosa.png', 'vegetation'), obj('tree-pine', 'objetos/pinheiro.png', 'vegetation'),
        obj('bush', 'objetos/arbusto.png', 'vegetation'), obj('flowers', 'objetos/flores.png', 'vegetation'),
        obj('rock', 'objetos/rocha.png', 'vegetation'), obj('log', 'objetos/tronco.png', 'vegetation'), obj('branches', 'objetos/galhos.png', 'vegetation'),
        obj('bench', 'objetos/banco.png', 'props'), obj('barrel', 'objetos/barril.png', 'props'), obj('bike', 'objetos/bicicleta.png', 'props'),
        obj('hydrant', 'objetos/hidrante.png', 'props'), obj('bin', 'objetos/lixeira.png', 'props'),
        obj('sign-centro', 'objetos/placa_centro.png', 'signs'), obj('sign-clinica', 'objetos/placa_clinica.png', 'signs'),
        obj('sign-estacao', 'objetos/placa_estacao.png', 'signs'), obj('sign-radio', 'objetos/placa_radio.png', 'signs'),
        sheet_obj('lamp', 'mobiliario', 0, 'props', cut=False, fix=deglow),
        sheet_obj('bench-b', 'mobiliario', 3, 'props'), sheet_obj('barrel-b', 'mobiliario', 5, 'props'),
        sheet_obj('cabinet', 'mobiliario', 6, 'props'), sheet_obj('kiosk', 'mobiliario', 7, 'props'),
        sheet_obj('stall', 'mobiliario', 10, 'props'), sheet_obj('notice', 'mobiliario', 11, 'props'),
        sheet_obj('fence-wood', 'mobiliario', 12, 'props'), sheet_obj('wall-stone', 'mobiliario', 13, 'props'),
        sheet_obj('crate-a', 'mobiliario', 14, 'props'), sheet_obj('crate-b', 'mobiliario', 15, 'props'),
        sheet_obj('signpost', 'mobiliario', 18, 'props'),
        sheet_obj('board', 'sinalizacao', 1, 'signs'), sheet_obj('booth', 'sinalizacao', 2, 'signs'),
        sheet_obj('grass-tall', 'efeitos_ambiente', 2, 'vegetation'), sheet_obj('grass-bush', 'efeitos_ambiente', 3, 'vegetation'),
        sheet_obj('portal-a', 'efeitos_ambiente', 4, 'effects'), sheet_obj('portal-b', 'efeitos_ambiente', 5, 'effects'),
        sheet_obj('orb', 'efeitos_ambiente', 6, 'effects'), sheet_obj('sparks', 'efeitos_ambiente', 7, 'effects'),
        sheet_obj('smoke', 'efeitos_ambiente', 8, 'effects'),
    ])
    for i in range(4): items[f'cr-big-{i}'] = sheet_obj('', 'criaturas', i, 'creatures')[1]
    for i, k in enumerate((4, 5)): items[f'cr-burst-{i}'] = sheet_obj('', 'criaturas', k, 'creatures')[1]
    items['cr-shadow'] = sheet_obj('', 'criaturas', 6, 'creatures')[1]
    for i in range(6): items[f'cr-small-{i}'] = sheet_obj('', 'criaturas', 7 + i, 'creatures')[1]
    for i in range(5): items[f'cr-mat-{i}'] = sheet_obj('', 'criaturas', 13 + i, 'creatures')[1]
    return items

def portrait(path):
    im = A.dehalo(Image.open(C / path)); return keep_main(im, .05)
