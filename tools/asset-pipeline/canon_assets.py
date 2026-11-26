"""Canon asset extraction: halo cleanup for the approved crops and component extraction from the canon sheets
(dark board background). Nothing here is redrawn: pixels come from frequencia-zero-canon.zip."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

CANON = Path(__file__).resolve().parents[2] / 'assets' / 'source' / 'canon'

def is_board_bg(rgb):
    """Dark, low-saturation purple/navy of the canon board."""
    mx = rgb.max(-1); mn = rgb.min(-1)
    return (mx < 78) & (mx - mn < 40) & (rgb[..., 2] >= rgb[..., 0] - 4)

def dehalo(im):
    """Approved crops: drop board-background pixels connected to transparency (purple fringe)."""
    a = np.array(im.convert('RGBA')).astype(int)
    al = a[..., 3] > 0; bg = is_board_bg(a[..., :3])
    H, W = al.shape
    for _ in range(3):
        edge = np.zeros_like(al)
        edge[1:] |= ~al[:-1]; edge[:-1] |= ~al[1:]; edge[:, 1:] |= ~al[:, :-1]; edge[:, :-1] |= ~al[:, 1:]
        kill = al & edge & bg
        if not kill.any(): break
        al &= ~kill
    a[..., 3] = np.where(al, 255, 0)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')

def components(path, min_px=30, merge=1, core_mx=100, core_sat=55, grow=2):
    """Objects on a canon sheet: everything that is not board background, grouped by 8-connectivity,
    boxes closer than `merge` px merged. Returns [(box, RGBA image)]."""
    a = np.array((Image.open(path) if not isinstance(path, Image.Image) else path).convert('RGBA')).astype(int)
    rgb = a[..., :3]; mx = rgb.max(-1); mn = rgb.min(-1)
    core = (mx >= core_mx) | (mx - mn >= core_sat)                      # clearly an object pixel
    bg_loose = (mx < 62) & (mx - mn < 34) & (rgb[..., 2] >= rgb[..., 0] - 6)
    H, W = core.shape
    reg = core.copy()
    for _ in range(grow):
        g = reg.copy(); g[1:] |= reg[:-1]; g[:-1] |= reg[1:]; g[:, 1:] |= reg[:, :-1]; g[:, :-1] |= reg[:, 1:]; reg = g
    fg = reg & ~bg_loose
    lab = np.zeros((H, W), int); boxes = []
    for y0 in range(H):
        for x0 in range(W):
            if fg[y0, x0] and not lab[y0, x0]:
                st = [(y0, x0)]; lab[y0, x0] = len(boxes) + 1; ys = []; xs = []
                while st:
                    y, x = st.pop(); ys.append(y); xs.append(x)
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < H and 0 <= xx < W and fg[yy, xx] and not lab[yy, xx]: lab[yy, xx] = len(boxes) + 1; st.append((yy, xx))
                boxes.append([min(xs), min(ys), max(xs) + 1, max(ys) + 1, len(xs)])
    boxes = [b for b in boxes if b[4] >= min_px]
    changed = True
    while changed:
        changed = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                A, B = boxes[i], boxes[j]
                if A[0] - merge <= B[2] and B[0] - merge <= A[2] and A[1] - merge <= B[3] and B[1] - merge <= A[3]:
                    boxes[i] = [min(A[0], B[0]), min(A[1], B[1]), max(A[2], B[2]), max(A[3], B[3]), A[4] + B[4]]; del boxes[j]; changed = True; break
            if changed: break
    out = []
    for b in sorted(boxes, key=lambda b: (b[1] // 20, b[0])):
        x0, y0, x1, y1, _ = b
        crop = a[y0:y1, x0:x1].copy(); crop[..., 3] = np.where(fg[y0:y1, x0:x1], 255, 0)
        out.append(((x0, y0, x1, y1), Image.fromarray(crop.astype(np.uint8), 'RGBA')))
    return out

def label_sheet(path, out):
    comps = components(path)
    base = Image.open(path).convert('RGBA'); sc = 3
    im = base.resize((base.width * sc, base.height * sc), Image.NEAREST); d = ImageDraw.Draw(im)
    for i, ((x0, y0, x1, y1), _) in enumerate(comps):
        d.rectangle([x0 * sc, y0 * sc, x1 * sc, y1 * sc], outline=(255, 255, 0)); d.text((x0 * sc + 2, y0 * sc + 1), str(i), fill=(255, 80, 80))
    im.save(out); return comps

def components_split(path, big=6000, **kw):
    """components(), re-segmenting oversized blobs (glow/haze bridges) with a stricter threshold."""
    out = []
    for box, im in components(path, **kw):
        w, h = im.size
        if w * h > big:
            sub = components(im, core_mx=150, core_sat=80, grow=1)
            if len(sub) > 1:
                for (x0, y0, x1, y1), s in sub: out.append(((box[0] + x0, box[1] + y0, box[0] + x1, box[1] + y1), s))
                continue
        out.append((box, im))
    return out

def cutout(sheet_rgba, box, pad=3):
    """Cut one object from a sheet box: keep strong pixels + dark outline pixels within 2 px of them, drop the
    board background and the soft glow haze."""
    a = np.array(sheet_rgba.convert('RGBA')).astype(int)
    x0, y0, x1, y1 = box; H, W = a.shape[:2]
    x0, y0, x1, y1 = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    r = a[y0:y1, x0:x1].copy(); rgb = r[..., :3]; mx = rgb.max(-1); mn = rgb.min(-1)
    core = (mx >= 88) | (mx - mn >= 50)
    near = core.copy()
    for _ in range(2):
        g = near.copy(); g[1:] |= near[:-1]; g[:-1] |= near[1:]; g[:, 1:] |= near[:, :-1]; g[:, :-1] |= near[:, 1:]; near = g
    bg = (mx < 58) & (mx - mn < 30) & (rgb[..., 2] >= rgb[..., 0] - 6)
    haze = (mx < 120) & (rgb[..., 0] > rgb[..., 2] + 10) & (mx - mn < 70) & ~core
    keep = near & ~bg & ~haze
    # fill holes: interior pixels surrounded by kept pixels on both axes
    rows_any = keep.any(1)
    for y in range(keep.shape[0]):
        xs = np.nonzero(keep[y])[0]
        if len(xs) > 1:
            span = np.zeros_like(keep[y]); span[xs[0]:xs[-1] + 1] = True
            keep[y] |= span & ~bg[y]
    r[..., 3] = np.where(keep, 255, 0)
    im = Image.fromarray(r.astype(np.uint8), 'RGBA')
    bb = im.getbbox(); return im.crop(bb) if bb else im
