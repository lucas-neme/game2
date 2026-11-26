#!/usr/bin/env python3
"""Import ChatGPT-created art packs as individual files; never deploy REVIEW art.

Every archive member becomes an individual file under assets/review/chatgpt-import/<pack>/.
Byte-identical content (SHA-256) is stored only once: if the same bytes are already tracked
anywhere under assets/ (source, production, an earlier pack), the member is recorded in the
import manifest with `stored_at` pointing to that existing file instead of being written again.
Existing files are never moved or rewritten, so current references keep working.
"""
import argparse, hashlib, json, pathlib, subprocess, zipfile
P = pathlib.Path
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("source", type=P)
ap.add_argument("--commit", action="store_true")
ap.add_argument("--push", action="store_true")
a = ap.parse_args()


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


root = P(git("rev-parse", "--show-toplevel"))
if a.push and not a.commit:
    ap.error("--push requires --commit")
if a.commit and git("status", "--porcelain", "--untracked-files=no"):
    raise SystemExit("Working tree not clean; commit your own changes first.")
if a.commit and git("branch", "--show-current") != "main":
    raise SystemExit("Use a clean main checkout.")
if a.commit:
    git("fetch", "origin", "main")
    # Local unpushed commits are fine as long as the push stays a fast-forward.
    if subprocess.run(["git", "merge-base", "--is-ancestor", "origin/main", "HEAD"]).returncode != 0:
        raise SystemExit("Synchronize main using a safe fast-forward first.")

packs = sorted(p for p in a.source.glob("*.zip")
               if p.name.startswith(("fz-", "frequencia-zero-")) and p.name != "frequencia-zero-kit.zip")
if not packs:
    raise SystemExit("No generated packs found.")
dest = root / "assets" / "review" / "chatgpt-import"
idx = dest / "import-manifest.json"
allowed = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".json", ".txt", ".md"}

# Content already tracked in the repository (excluding the manifest we rewrite).
known = {}
for rel in git("-C", str(root), "ls-files", "-z", "--", "assets").split("\0"):
    if not rel:
        continue
    f = root / rel
    if f == idx or not f.is_file():
        continue
    known.setdefault(hashlib.sha256(f.read_bytes()).hexdigest(), rel)

plan = {}
catalog = []
for pack in packs:
    with zipfile.ZipFile(pack) as z:
        if z.testzip() is not None:
            raise SystemExit("Corrupt archive: " + pack.name)
        for info in z.infolist():
            if info.is_dir():
                continue
            rel = pathlib.PurePosixPath(info.filename.replace(chr(92), "/"))
            if rel.is_absolute() or ".." in rel.parts or any(":" in x for x in rel.parts):
                raise SystemExit("Unsafe member: " + info.filename)
            if rel.suffix.lower() not in allowed:
                continue
            target = dest / pack.stem / P(*rel.parts)
            if not target.resolve().is_relative_to(dest.resolve()):
                raise SystemExit("Unsafe target: " + str(target))
            data = z.read(info)
            digest = hashlib.sha256(data).hexdigest()
            tpath = target.relative_to(root).as_posix()
            if digest in known:
                stored = known[digest]
            else:
                if target.exists() and target.read_bytes() != data:
                    raise SystemExit("Existing different file: " + str(target))
                plan[target] = data
                known[digest] = stored = tpath
            catalog.append({"package": pack.name, "member": rel.as_posix(), "path": tpath,
                            "stored_at": stored, "deduplicated": stored != tpath,
                            "sha256": digest, "bytes": len(data), "status": "REVIEW"})

for target, data in plan.items():
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_bytes(data)

old = json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else {"files": []}
entries = {(e["package"], e.get("member", e["path"])): e for e in old.get("files", [])}
entries.update({(e["package"], e["member"]): e for e in catalog})
idx.parent.mkdir(parents=True, exist_ok=True)
idx.write_text(json.dumps({
    "status": "REVIEW",
    "note": "One entry per archive member. stored_at is the single repository copy of those bytes "
            "(SHA-256 deduplication). REVIEW art is never deployed until promoted to assets/production.",
    "packages": [p.name for p in packs],
    "files": sorted(entries.values(), key=lambda e: (e["package"], e["member"]))},
    ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(f"{len(packs)} packages; {len(catalog)} archive members; {len(plan)} new files written; "
      f"{sum(e['deduplicated'] for e in catalog)} members deduplicated; "
      f"{len(set(e['sha256'] for e in catalog))} unique byte hashes")
if a.commit:
    git("-C", str(root), "add", "--", dest.relative_to(root).as_posix())
    if git("-C", str(root), "diff", "--cached", "--name-only"):
        print(git("-C", str(root), "commit", "-m",
                  "assets: import individual ChatGPT art sources and review frames (SHA-256 deduplicated)"))
    else:
        print("No new changes.")
    if a.push:
        print(git("-C", str(root), "push", "origin", "main"))
