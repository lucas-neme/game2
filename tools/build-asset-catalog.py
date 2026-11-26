#!/usr/bin/env python3
"""Build assets/manifests/catalog.json: one entry per tracked graphic file under assets/.

Fields: id, path, github/raw URL, category, character, animation, direction, frame, size,
anchor, scale, sha256, origin, version, approval state, current use in the game.
Facts come from the existing manifests (production.json, v4.json, v5.json and the import
manifest); everything else is derived from the path. Unknown values stay null rather than guessed.
Run after any asset change:  python tools/build-asset-catalog.py
"""
import hashlib, json, pathlib, re, struct, subprocess
P = pathlib.Path
root = P(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
REPO = "lucas-neme/game2"
IMG = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
man = root / "assets" / "manifests"
out = man / "catalog.json"


def load(p):
    p = root / p
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


prod, v4, v5 = load("assets/manifests/production.json"), load("assets/manifests/v4.json"), load("assets/manifests/v5.json")
imp = load("assets/review/chatgpt-import/import-manifest.json")

# Per-file facts declared by the manifests: any dict with a "file" key pointing at an asset.
facts = {}


def walk(o, ctx):
    if isinstance(o, dict):
        f = o.get("file")
        if isinstance(f, str) and f.startswith("assets/"):
            facts.setdefault(f, {}).update({k: o[k] for k in ("anchor", "draw_scale", "frame", "state", "w", "h") if k in o}, manifest=ctx)
        for v in o.values():
            walk(v, ctx)
    elif isinstance(o, list):
        for v in o:
            walk(v, ctx)
    elif isinstance(o, str) and o.startswith("assets/production/"):
        facts.setdefault(o, {}).setdefault("manifest", ctx)


for name, d in (("production.json", prod), ("v4.json", v4), ("v5.json", v5)):
    walk(d, name)

# V5 frame labels: "row.col" -> (animation, direction, index)
v5_frames = {}
for npc, d in (v5.get("npcs") or {}).items():
    for key, anim in (d.get("animations") or {}).items():
        a, _, direction = key.partition(":")
        for i, rc in enumerate(anim.get("source_frames") or []):
            v5_frames[(npc, rc)] = (a, direction or None, i)

origins = {}
for e in imp.get("files", []):
    origins.setdefault(e["stored_at"], set()).add(e["package"])
rejected = set((prod.get("rejected_packs") or {}).keys())

# Current use in the game: literal references in the runtime files.
runtime = "\n".join((root / f).read_text(encoding="utf-8", errors="replace")
                    for f in ("index.html", "campaign.html") if (root / f).exists())

CHARS = ["protagonista", "hero", "lia", "raul", "nora", "helena", "bento", "celina", "samuel", "miguel",
         "padre_antonio", "ferroviario", "crianca", "comerciante", "guarda", "medico", "professor",
         "investigator", "eco_humanoide", "eco_corrompido", "sombra_ressonante", "vigia_projeto",
         "mutante_floresta", "anomalia_esferica", "sentinela_drone", "enxame", "echo", "pulse"]
HUMANS = set(CHARS[:17])
DIRS = {"north": "north", "south": "south", "east": "east", "west": "west", "front": "south", "back": "north",
        "left": "west", "right": "east", "side": "side", "ne": "north-east", "nw": "north-west",
        "se": "south-east", "sw": "south-west"}
ANIMS = {"idle": "idle", "walk": "walk", "run": "run", "sit": "sit", "stand": "stand", "attack": "attack",
         "ataque": "attack", "movimento": "move", "move": "move", "dano": "hurt", "hurt": "hurt",
         "dissipacao": "death", "death": "death", "morte": "death", "interact": "interact", "talk": "talk",
         "sequence": "sequence"}
CATS = [("characters", r"personagens|npcs?[/-]|characters|protagonista|moradores|ch-|hero|walk-v"),
        ("creatures", r"monstros|criaturas|creatures|eco_|sombra_|vigia_|mutante_|anomalia_|enxame|drone"),
        ("weapons", r"rifle|besta|revolver|pistola|espingarda|faca|machado|arma"),
        ("items", r"inventario|chave|item|disco_dados|objeto"),
        ("puzzles", r"enigma|puzzle|cofre|relogio|alavanca|lentes|engrenagen|painel|mapa_frag"),
        ("vegetation", r"vegeta|arvore|pinheiro|arbusto|flor|natureza|rocha"),
        ("interiors", r"interior|cutaway|quarto|escritorio|study|station|laboratorio"),
        ("furniture", r"mobiliario|banco|cadeira|mesa|fogao|chaleira|sofa|cama|poste|lixeira|hidrante|cerca"),
        ("buildings", r"construc|arquitetura|casa|cabana|escola|oficina|subestacao|bunker|building|roof|b-"),
        ("effects", r"efeito|effects|clima|fog|ceu|particula"),
        ("ui", r"/ui/|hud|icon|logo|portrait|retrato|dialogo"),
        ("environment", r"environment|terreno|ground|cidade|trilho|sinaliza|atlas|tile"),
        ("reference", r"referencia|reference|preview|catalogo|folha|scene|sheet")]


def size(b, ext):
    try:
        if ext == ".png" and b[:8] == b"\x89PNG\r\n\x1a\n":
            return list(struct.unpack(">II", b[16:24]))
        if ext in (".jpg", ".jpeg"):
            i = 2
            while i < len(b):
                if b[i] != 0xFF:
                    break
                m, ln = b[i + 1], struct.unpack(">H", b[i + 2:i + 4])[0]
                if m in (0xC0, 0xC1, 0xC2):
                    h, w = struct.unpack(">HH", b[i + 5:i + 9])
                    return [w, h]
                i += 2 + ln
        if ext == ".webp" and b[12:16] == b"VP8X":
            return [int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1]
    except Exception:
        pass
    return None


entries = []
files = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z", "--", "assets"], text=True).split("\0")
files += subprocess.check_output(["git", "-C", str(root), "ls-files", "-z", "--others", "--exclude-standard", "--", "assets"], text=True).split("\0")
for rel in sorted(set(f for f in files if f)):
    p = root / rel
    ext = p.suffix.lower()
    if ext not in IMG or not p.is_file():
        continue
    b = p.read_bytes()
    low = rel.lower()
    parts = low.split("/")
    stem = p.stem.lower()
    tokens = re.split(r"[^a-z0-9]+", low)
    character = next((c for c in CHARS if c in parts or c in tokens or stem.startswith(c + "_") or f"ch-{c}" in stem or f"ch-m-{c}" in stem), None)
    if character is None and re.search(r"npcs?[/-]", low) and parts[-2] == "recortes":
        character = stem
    if character == "protagonista":
        character = "hero"
    animation = next((ANIMS[t] for t in tokens if t in ANIMS), None)
    direction = next((DIRS[t] for t in tokens if t in DIRS), None)
    m = re.search(r"(?:_|-)(\d+)$", stem)
    frame = int(m.group(1)) if m and (animation or direction) else None
    mv5 = re.search(r"npcs/([a-z_]+)/frames/r(\d+)_(\d+)\.png$", low)
    if mv5 and (mv5.group(1), f"{int(mv5.group(2))}.{int(mv5.group(3))}") in v5_frames:
        animation, direction, frame = v5_frames[(mv5.group(1), f"{int(mv5.group(2))}.{int(mv5.group(3))}")]
    category = next((c for c, rx in CATS if re.search(rx, low)), "other")
    if character in HUMANS and category in ("other", "reference"):
        category = "characters"
    if parts[1] == "atlases" or "atlas" in stem:
        category = "atlases"
    f = facts.get(rel, {})
    pk = sorted(origins.get(rel, []))
    ver = re.search(r"(?:^|[-_/])v(\d)(?:[-_/.]|$)", low) or (re.search(r"v(\d)", " ".join(pk)) if pk else None)
    if parts[1] == "production":
        state = (f.get("state") or "PRODUCTION").split(" ")[0]
    elif parts[1] == "review":
        state = "REJECTED" if any(x in rejected for x in pk) else "REVIEW"
    elif parts[1] == "source":
        state = "SOURCE"
    else:
        state = "LEGACY"
    in_game = rel in runtime
    entries.append({
        "id": re.sub(r"[^a-z0-9]+", "-", low.removeprefix("assets/").rsplit(".", 1)[0]).strip("-"),
        "path": rel,
        "github_url": f"https://github.com/{REPO}/blob/main/{rel}",
        "raw_url": f"https://raw.githubusercontent.com/{REPO}/main/{rel}",
        "category": category, "character": character, "animation": animation, "direction": direction,
        "frame": frame, "size": size(b, ext) or ([f["w"], f["h"]] if "w" in f else None),
        "anchor": f.get("anchor"), "scale": f.get("draw_scale"),
        "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b),
        "origin": pk or [parts[1] + ("/" + parts[2] if len(parts) > 3 else "")],
        "version": f"v{ver.group(1)}" if ver else None,
        "state": state,
        "in_game": in_game or bool(f.get("manifest")) and parts[1] == "production",
        "declared_in": f.get("manifest"),
    })

summary = {}
for e in entries:
    summary.setdefault(e["state"], 0)
    summary[e["state"]] += 1
out.write_text(json.dumps({
    "schema": 1,
    "repo": REPO,
    "how_to_use": "Every graphic asset of Frequencia Zero, one entry per file. state: PRODUCTION/APPROVED = shipped; "
                  "SOURCE = canonical originals; REVIEW = imported candidates, never deployed until promoted; "
                  "REJECTED = known defects. Byte provenance of every ZIP member: assets/review/chatgpt-import/import-manifest.json. "
                  "Regenerate with: python tools/build-asset-catalog.py",
    "scale": prod.get("scale"),
    "counts": {"files": len(entries), "unique_sha256": len({e['sha256'] for e in entries}), "by_state": summary},
    "assets": entries}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"files": len(entries), "unique": len({e['sha256'] for e in entries}), "by_state": summary}))
