#!/usr/bin/env python3
"""Asset tools shared by the Wampa games (Ashen Kingdoms, Frequencia Zero). Behaviour per repository comes from
assets/manifests/registry-config.json; the two games never share assets.

  import <dir> [--dest D]       safe extraction of every *.zip in <dir> (one folder per pack), SHA-256 deduplicated
                                against everything already tracked; provenance in assets/manifests/import-ledger.json
  archive-branch <ref> [--dest] copy the graphic files that exist only on another branch into assets/archived/<ref>/
  registry                      assets/manifests/asset-registry.json + .csv + animation-index.json
  audit                         assets/manifests/audit-report.json: corrupt/empty/opaque images, duplicates,
                                broken runtime references, frame gaps
  sheet <out.png> <files...>    contact sheet (checkerboard background)    gif <out.gif> <frames...> [--fps N]

Nothing is ever moved or overwritten: runtime paths stay valid. Pillow is needed for audit/sheet/gif only.
"""
import argparse, csv, hashlib, io, json, pathlib, re, struct, subprocess, sys, zipfile
P = pathlib.Path
IMG = {".png", ".webp", ".jpg", ".jpeg", ".gif", ".svg"}
AUDIO = {".ogg", ".mp3", ".wav", ".m4a"}
KEEP = IMG | AUDIO | {".json", ".txt", ".md", ".csv"}


def git(*a, binary=False):
    out = subprocess.check_output(["git", "-C", str(ROOT), *a])
    return out if binary else out.decode("utf-8", "replace").strip()


ROOT = P(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
CFGF = ROOT / "assets" / "manifests" / "registry-config.json"
CFG = json.loads(CFGF.read_text(encoding="utf-8"))
MAN = ROOT / "assets" / "manifests"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def tracked(prefixes=None):
    files = git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
    out = [f for f in files if f and (ROOT / f).is_file()]
    return [f for f in out if not prefixes or f.startswith(tuple(prefixes))]


def known_hashes():
    k = {}
    for f in tracked():
        if P(f).suffix.lower() in KEEP and not f.startswith("assets/manifests/"):
            k.setdefault(sha((ROOT / f).read_bytes()), f)
    return k


def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


# ----------------------------------------------------------------------------------------------------------- import
def cmd_import(a):
    src = P(a.dir); dest = ROOT / a.dest
    known = known_hashes(); ledger_p = MAN / "import-ledger.json"
    ledger = json.loads(ledger_p.read_text(encoding="utf-8")) if ledger_p.exists() else {"files": []}
    seen = {(e["package"], e["member"]) for e in ledger["files"]}
    written = dedup = 0; packs = sorted(src.rglob("*.zip"))
    for pack in packs:
        with zipfile.ZipFile(pack) as z:
            if z.testzip() is not None:
                sys.exit("corrupt archive " + pack.name)
            for i in z.infolist():
                if i.is_dir():
                    continue
                rel = pathlib.PurePosixPath(i.filename.replace("\\", "/"))
                if rel.is_absolute() or ".." in rel.parts or any(":" in x for x in rel.parts):
                    sys.exit("unsafe member " + i.filename)
                if rel.suffix.lower() not in KEEP or rel.parts[0] == "__MACOSX":
                    continue
                data = z.read(i); h = sha(data)
                target = dest / pack.stem / P(*rel.parts)
                if not target.resolve().is_relative_to(dest.resolve()):
                    sys.exit("unsafe target " + str(target))
                tpath = target.relative_to(ROOT).as_posix()
                if h in known:
                    stored = known[h]; dedup += 1
                else:
                    if target.exists() and target.read_bytes() != data:
                        sys.exit("refusing to overwrite different file " + tpath)
                    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
                    known[h] = stored = tpath; written += 1
                if (pack.name, rel.as_posix()) not in seen:
                    ledger["files"].append({"package": pack.name, "package_dir": pack.parent.name, "member": rel.as_posix(),
                                            "stored_at": stored, "deduplicated": stored != tpath, "sha256": h, "bytes": len(data)})
                    seen.add((pack.name, rel.as_posix()))
    ledger["files"].sort(key=lambda e: (e["package"], e["member"]))
    ledger["note"] = "One entry per ZIP member; stored_at is the single repository copy of those bytes (SHA-256)."
    write_json(ledger_p, ledger)
    print(f"{len(packs)} packs, {written} files written, {dedup} members deduplicated")


# --------------------------------------------------------------------------------------------------- archive-branch
def cmd_archive(a):
    ref = a.ref; slug = re.sub(r"[^A-Za-z0-9._-]+", "-", ref.split("/", 1)[-1] if ref.startswith("origin/") else ref)
    dest = ROOT / a.dest / slug; known = known_hashes(); n = d = 0
    ledger_p = MAN / "archive-ledger.json"
    ledger = json.loads(ledger_p.read_text(encoding="utf-8")) if ledger_p.exists() else {"files": []}
    commit = git("rev-parse", ref)
    for line in git("ls-tree", "-r", ref).splitlines():
        meta, path = line.split("\t", 1)
        if path.startswith('"'):
            path = path[1:-1].encode("latin-1").decode("unicode_escape").encode("latin-1").decode("utf-8")
        if P(path).suffix.lower() not in IMG | AUDIO:
            continue
        data = git("cat-file", "blob", meta.split()[2], binary=True); h = sha(data)
        if h in known:
            stored = known[h]; d += 1
        else:
            t = dest / P(path); t.parent.mkdir(parents=True, exist_ok=True); t.write_bytes(data)
            stored = known[h] = t.relative_to(ROOT).as_posix(); n += 1
        ledger["files"].append({"ref": ref, "commit": commit, "path": path, "stored_at": stored, "sha256": h})
    write_json(ledger_p, ledger)
    print(f"{ref}: {n} archived, {d} already present")


# --------------------------------------------------------------------------------------------------------- registry
def img_size(b, ext):
    try:
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            return list(struct.unpack(">II", b[16:24]))
        if ext in (".jpg", ".jpeg"):
            i = 2
            while i < len(b) and b[i] == 0xFF:
                m, ln = b[i + 1], struct.unpack(">H", b[i + 2:i + 4])[0]
                if m in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", b[i + 5:i + 9]); return [w, h]
                i += 2 + ln
        if ext == ".webp" and b[12:16] == b"VP8X":
            return [int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1]
        if ext == ".webp" and b[12:16] == b"VP8L":
            v = int.from_bytes(b[21:25], "little"); return [(v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1]
        if ext == ".webp" and b[12:16] == b"VP8 ":
            return [int.from_bytes(b[26:28], "little") & 0x3FFF, int.from_bytes(b[28:30], "little") & 0x3FFF]
        if ext == ".gif":
            return list(struct.unpack("<HH", b[6:10]))
    except Exception:
        pass
    return None


def manifest_facts():
    """Facts that manifests declare about a file: anchor, scale, collider, frames, cell, atlas."""
    facts = {}
    keys = ("anchor", "anchorX", "anchorY", "draw_scale", "scale", "pixelScale", "collision", "collider", "frame", "cell",
            "frames", "frameCount", "fps", "state", "status", "worldHeight")
    for mf in CFG.get("fact_manifests", []):
        mp = ROOT / mf
        if not mp.exists():
            continue
        base = mp.parent
        doc = json.loads(mp.read_text(encoding="utf-8"))

        def walk(o, ctx):
            if isinstance(o, dict):
                ctx = {**ctx, **{k: o[k] for k in keys if k in o and not isinstance(o[k], (dict, list)) or k in ("anchor", "cell", "frame") and k in o}}
                for v in o.values():
                    walk(v, ctx)
            elif isinstance(o, list):
                for v in o:
                    walk(v, ctx)
            elif isinstance(o, str) and P(o.split("?")[0]).suffix.lower() in IMG:
                s = o.split("?")[0].lstrip("./")
                for cand in (ROOT / s, base / s):
                    if cand.is_file():
                        rel = cand.resolve().relative_to(ROOT.resolve()).as_posix()
                        f = facts.setdefault(rel, {"declared_in": []})
                        f.update({k: v for k, v in ctx.items() if k not in f})
                        if mf not in f["declared_in"]:
                            f["declared_in"].append(mf)
                        break
        walk(doc, {})
    return facts


def runtime_text():
    parts = []
    for pat in CFG.get("runtime_globs", []):
        for f in sorted(ROOT.glob(pat)):
            if f.is_file() and "node_modules" not in f.parts:
                parts.append(f.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def used_in(rel, text):
    segs = rel.split("/")
    for k in range(0, max(1, len(segs) - 1)):
        tail = "/".join(segs[k:])
        if tail.count("/") < 1 and len(segs) > 1:
            break
        if tail in text:
            return tail
    return None


def first(regexes, low):
    for name, rx in regexes:
        if re.search(rx, low):
            return name
    return None


def frame_labels():
    """Optional: label frames from a manifest that maps "row.col" source frames to animation:direction sequences."""
    out = []
    for spec in CFG.get("frame_labels", []):
        mp = ROOT / spec["manifest"]
        if not mp.exists():
            continue
        lab = {}
        for ch, d in (json.loads(mp.read_text(encoding="utf-8")).get(spec["root_key"]) or {}).items():
            for key, an in (d.get(spec["anims_key"]) or {}).items():
                anim, _, direction = key.partition(":"); anim = CFG["animations"].get(anim, anim)
                for i, rc in enumerate(an.get(spec["src_key"]) or []):
                    lab[(ch, rc)] = (anim, direction or None, i)
        out.append((re.compile(spec["path_regex"]), lab))
    return out


LABELS = None


def classify(rel, b, facts, text, origins):
    global LABELS
    if LABELS is None:
        LABELS = frame_labels()
    low = rel.lower(); ext = P(rel).suffix.lower(); stem = P(low).stem
    tokens = [t for t in re.split(r"[^a-z0-9]+", low) if t]
    C = CFG
    character = next((c for c, al in C["characters"].items() if any(x in tokens or f"/{x}/" in low or stem.startswith(x + "_") or stem.startswith(x + "-") for x in [c, *al])), None)
    cls = next((c for c, al in C.get("classes", {}).items() if any(x in tokens for x in [c, *al])), None)
    variant = next((v for v, al in C.get("variants", {}).items() if any(x in tokens for x in [v, *al])), None)
    animation = next((C["animations"][t] for t in tokens if t in C["animations"]), None)
    if animation is None:
        animation = next((v for k, v in C["animations"].items() if "-" in k and k in low), None)
    direction = next((C["directions"][t] for t in tokens if t in C["directions"]), None)
    if direction is None and animation and C.get("default_direction"):
        direction = C["default_direction"]
    m = re.search(r"(?:^|[_\-])(?:f|frame)?(\d{1,3})$", stem)
    frame = int(m.group(1)) if m and (animation or direction) else None
    for rx, lab in LABELS:
        mm = rx.search(low)
        if mm and (mm.group(1), f"{int(mm.group(2))}.{int(mm.group(3))}") in lab:
            animation, direction, frame = lab[(mm.group(1), f"{int(mm.group(2))}.{int(mm.group(3))}")]
            character = character or mm.group(1)
    category = first(C["categories"], low) or ("audio" if ext in AUDIO else "other")
    state = first(C["states"], low) or "SOURCE"
    f = facts.get(rel, {})
    use = used_in(rel, text)
    ver = re.search(r"(?:^|[-_/])v(\d{1,2})(?:[-_/.]|$)", low)
    anchor = f.get("anchor") or ([f["anchorX"], f["anchorY"]] if "anchorX" in f and "anchorY" in f else None)
    size = img_size(b, ext) if ext in IMG else None
    atlas = None
    if re.search(r"(?:^|[_\-])\d{1,3}$", stem):
        cand = re.sub(r"[_\-]\d{1,3}$", "", P(rel).name.rsplit(".", 1)[0])
        for c in (P(rel).with_name(cand + ext), P(rel).parent.with_suffix(ext)):
            if (ROOT / c).is_file():
                atlas = c.as_posix(); break
    if state in ("SOURCE", "APPROVED") and use and C.get("used_means_production", True):
        state = "PRODUCTION"
    return {
        "id": re.sub(r"[^a-z0-9]+", "-", low.rsplit(".", 1)[0]).strip("-"),
        "name": P(rel).stem, "category": category, "path": rel,
        "github_url": f"https://github.com/{C['repo']}/blob/{C.get('branch', 'main')}/{rel}",
        "raw_url": f"https://raw.githubusercontent.com/{C['repo']}/{C.get('branch', 'main')}/{rel}",
        "character": character, "class": cls, "variant": variant, "animation": animation, "direction": direction,
        "frame": frame, "size": size, "original_resolution": size,
        "anchor": anchor, "scale": f.get("draw_scale") or f.get("pixelScale") or f.get("scale"),
        "collider": f.get("collider") or f.get("collision"), "cell": f.get("cell") or f.get("frame"),
        "sha256": sha(b), "bytes": len(b), "origin": origins.get(rel) or "/".join(rel.split("/")[:2]),
        "license": next((v for k, v in C.get("licenses", {}).items() if low.startswith(k.lower())), C.get("default_license")),
        "version": f"v{ver.group(1)}" if ver else None, "state": state,
        "spritesheet": atlas, "atlas": atlas, "dependencies": f.get("declared_in", []),
        "in_game": bool(use or (state == "PRODUCTION" and f.get("declared_in"))), "runtime_reference": use,
    }


def origins_map():
    o = {}
    for led, key in (("import-ledger.json", "package"), ("archive-ledger.json", "ref")):
        p = MAN / led
        if p.exists():
            for e in json.loads(p.read_text(encoding="utf-8"))["files"]:
                o.setdefault(e["stored_at"], []).append(e[key])
    for extra in CFG.get("origin_ledgers", []):
        p = ROOT / extra["file"]
        if p.exists():
            for e in json.loads(p.read_text(encoding="utf-8"))["files"]:
                o.setdefault(e[extra.get("stored", "stored_at")], []).append(e[extra.get("source", "package")])
    return {k: sorted(set(v)) for k, v in o.items()}


def cmd_registry(a):
    facts = manifest_facts(); text = runtime_text(); origins = origins_map(); rows = []
    for rel in sorted(tracked(CFG["scan"])):
        ext = P(rel).suffix.lower()
        if ext not in IMG | AUDIO or any(rel.startswith(x) for x in CFG.get("exclude", [])):
            continue
        rows.append(classify(rel, (ROOT / rel).read_bytes(), facts, text, origins))
    by_sha = {}
    for r in rows:
        by_sha.setdefault(r["sha256"], []).append(r["path"])
    for r in rows:
        r["identical_copies"] = [p for p in by_sha[r["sha256"]] if p != r["path"]]
    counts = {"files": len(rows), "unique_sha256": len(by_sha)}
    for k in ("state", "category"):
        counts["by_" + k] = {}
        for r in rows:
            counts["by_" + k][r[k]] = counts["by_" + k].get(r[k], 0) + 1
    write_json(MAN / "asset-registry.json", {"schema": 1, "repo": CFG["repo"], "game": CFG["game"],
               "states": ["SOURCE", "REVIEW", "APPROVED", "PRODUCTION", "ARCHIVED", "REJECTED"],
               "how_to_use": CFG["how_to_use"], "counts": counts, "assets": rows})
    cols = ["id", "name", "category", "path", "character", "class", "variant", "animation", "direction", "frame", "size",
            "anchor", "scale", "collider", "sha256", "origin", "license", "version", "state", "atlas", "in_game", "github_url"]
    with open(MAN / "asset-registry.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(cols)
        for r in rows:
            w.writerow([";".join(map(str, r[c])) if isinstance(r[c], list) else ("" if r[c] is None else r[c]) for c in cols])
    # animation index: character -> animation -> direction -> frames (+ missing against the expected list)
    idx = {}
    for r in rows:
        if r["character"] and r["animation"] and r["category"] in CFG.get("animated_categories", ["characters", "creatures", "enemies", "bosses"]):
            key = r["character"] + (f"/{r['variant']}" if r["variant"] else "")
            d = idx.setdefault(key, {}).setdefault(r["animation"], {}).setdefault(r["direction"] or "any", [])
            d.append({"frame": r["frame"], "path": r["path"], "state": r["state"]})
    exp = CFG.get("expected_animations", {})
    out = {}
    for ch, anims in sorted(idx.items()):
        for a_ in anims.values():
            for lst in a_.values():
                lst.sort(key=lambda x: (x["frame"] is None, x["frame"] or 0, x["path"]))
        base = ch.split("/")[0]
        wanted = exp.get(base) or exp.get("_humans" if base in CFG.get("humans", []) else "_creatures", [])
        out[ch] = {"available": {k: {d: len(v) for d, v in dd.items()} for k, dd in sorted(anims.items())},
                   "missing": [x for x in wanted if x not in anims], "frames": anims}
    # animations that exist only inside runtime atlases, as declared by the manifests
    for spec in CFG.get("atlas_animations", []):
        mp = ROOT / spec["manifest"]
        if not mp.exists():
            continue
        for ch, d in (json.loads(mp.read_text(encoding="utf-8")).get(spec["root_key"]) or {}).items():
            if spec.get("skip") and re.search(spec["skip"], ch):
                continue
            ch = spec.get("rename", {}).get(ch, ch)
            e = out.setdefault(ch, {"available": {}, "missing": [], "frames": {}})
            for key, val in (d.get(spec["anims_key"]) or {}).items():
                anim, _, direction = key.partition(":"); anim = CFG["animations"].get(anim, anim)
                n = val if isinstance(val, int) else (val or {}).get("frames")
                e["available"].setdefault(anim, {})[(direction or "any") + " (atlas)"] = n
            e.setdefault("atlas", d.get("file") or spec.get("atlas", {}).get(ch))
    for ch, e in out.items():
        base = ch.split("/")[0]
        wanted = exp.get(base) or exp.get("_humans" if base in CFG.get("humans", []) else "_creatures", [])
        e["missing"] = [x for x in wanted if x not in e["available"]]
    for ch in CFG["characters"]:
        if not any(k.split("/")[0] == ch for k in out):
            wanted = exp.get(ch) or exp.get("_humans" if ch in CFG.get("humans", []) else "_creatures", [])
            out[ch] = {"available": {}, "missing": wanted, "frames": {}}
    write_json(MAN / "animation-index.json", {"schema": 1, "game": CFG["game"],
               "note": "available = frames per direction found in the repository (any state); missing = expected animations with no file.",
               "characters": out})
    if CFG.get("animation_doc"):
        L = [f"# Registro de animações — {CFG['game']}", "",
             "Gerado por `python tools/assets/asset_tools.py registry` a partir dos arquivos do repositório (não editar à mão).",
             "Disponível = frames encontrados por direção, em qualquer estado (PRODUCTION, REVIEW, ARCHIVED...). Os caminhos de",
             "cada frame estão em `assets/manifests/animation-index.json`.", "",
             "| Personagem | Disponível (animação: direção×frames) | Faltando |", "|---|---|---|"]
        for ch, v in out.items():
            av = "; ".join(f"{k}: " + ", ".join(f"{d}×{n}" for d, n in dd.items()) for k, dd in v["available"].items()) or "—"
            L.append(f"| {ch} | {av} | {', '.join(v['missing']) or '—'} |")
        nl = chr(10)
        (ROOT / CFG["animation_doc"]).write_text(nl.join(L) + nl, encoding="utf-8", newline=nl)
    print(json.dumps(counts, ensure_ascii=False))


# ------------------------------------------------------------------------------------------------------------ audit
def cmd_audit(a):
    from PIL import Image
    reg = json.loads((MAN / "asset-registry.json").read_text(encoding="utf-8"))["assets"]
    rep = {"corrupt": [], "empty": [], "no_alpha_sprites": [], "duplicates": [], "broken_runtime_references": [],
           "frame_gaps": [], "unused_production": []}
    for r in reg:
        if not r["path"].lower().endswith((".png", ".webp", ".gif")):
            continue
        try:
            im = Image.open(ROOT / r["path"]); im.load()
        except Exception as e:
            rep["corrupt"].append({"path": r["path"], "error": str(e)}); continue
        if im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info:
            al = im.convert("RGBA").getchannel("A")
            if al.getbbox() is None:
                rep["empty"].append(r["path"])
        elif r["category"] in ("characters", "creatures", "enemies", "bosses") and r["frame"] is not None:
            rep["no_alpha_sprites"].append(r["path"])
        if r["state"] == "PRODUCTION" and not r["in_game"]:
            rep["unused_production"].append(r["path"])
    seen = {}
    for r in reg:
        seen.setdefault(r["sha256"], []).append(r["path"])
    rep["duplicates"] = [v for v in seen.values() if len(v) > 1]
    text = runtime_text()
    for m in sorted(set(re.findall(CFG.get("reference_regex", r"assets/[A-Za-z0-9_./-]+\.(?:png|webp|jpg|svg|gif)"), text))):
        if not any((ROOT / base / m).is_file() for base in CFG.get("reference_bases", [""])):
            rep["broken_runtime_references"].append(m)
    groups = {}
    for r in reg:
        if r["frame"] is not None:
            groups.setdefault(re.sub(r"(?:f|frame)?\d{1,3}(\.\w+)$", r"#\1", r["path"]), []).append(r["frame"])
    for g, fr in groups.items():
        fr = sorted(set(fr)); lo = fr[0]
        gaps = [i for i in range(lo, fr[-1] + 1) if i not in fr]
        if gaps:
            rep["frame_gaps"].append({"pattern": g, "missing": gaps})
    rep["summary"] = {k: len(v) for k, v in rep.items() if isinstance(v, list)}
    write_json(MAN / "audit-report.json", rep)
    print(json.dumps(rep["summary"]))


def checker(w, h, s=8):
    from PIL import Image
    bg = Image.new("RGBA", (w, h), (200, 200, 200, 255)); px = bg.load()
    for y in range(h):
        for x in range(w):
            if (x // s + y // s) % 2:
                px[x, y] = (150, 150, 150, 255)
    return bg


def cmd_sheet(a):
    from PIL import Image
    ims = [Image.open(f).convert("RGBA") for f in a.files]
    cw = max(i.width for i in ims); ch = max(i.height for i in ims); cols = min(len(ims), a.cols)
    rows = (len(ims) + cols - 1) // cols
    out = checker(cw * cols, ch * rows)
    for k, im in enumerate(ims):
        out.alpha_composite(im, ((k % cols) * cw, (k // cols) * ch))
    out.save(a.out); print(a.out)


def cmd_gif(a):
    from PIL import Image
    ims = [Image.open(f).convert("RGBA") for f in a.frames]
    w = max(i.width for i in ims); h = max(i.height for i in ims); fr = []
    for im in ims:
        c = checker(w, h); c.alpha_composite(im, ((w - im.width) // 2, h - im.height)); fr.append(c.convert("P"))
    fr[0].save(a.out, save_all=True, append_images=fr[1:], duration=int(1000 / a.fps), loop=0); print(a.out)


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sp = ap.add_subparsers(dest="cmd", required=True)
x = sp.add_parser("import"); x.add_argument("dir"); x.add_argument("--dest", default="assets/review/packs"); x.set_defaults(fn=cmd_import)
x = sp.add_parser("archive-branch"); x.add_argument("ref"); x.add_argument("--dest", default="assets/archived"); x.set_defaults(fn=cmd_archive)
sp.add_parser("registry").set_defaults(fn=cmd_registry)
sp.add_parser("audit").set_defaults(fn=cmd_audit)
x = sp.add_parser("sheet"); x.add_argument("out"); x.add_argument("files", nargs="+"); x.add_argument("--cols", type=int, default=8); x.set_defaults(fn=cmd_sheet)
x = sp.add_parser("gif"); x.add_argument("out"); x.add_argument("frames", nargs="+"); x.add_argument("--fps", type=float, default=8); x.set_defaults(fn=cmd_gif)
a = ap.parse_args(); a.fn(a)
