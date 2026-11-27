#!/usr/bin/env python3
"""Import the exact user-approved Valley expansion artwork (64 individual PNGs)."""
import argparse, hashlib, json, pathlib, subprocess, zipfile, struct

EXPECTED = "34ae3744e541da9686c03eedd99d7dbe0f6178204819da5059a5de9f249a3105"
DEST = "assets/review/expansion-secrets-of-the-valley"
COUNTS = {"buildings": 16, "environment": 16, "props": 16, "characters": 10, "creatures": 6}
def digest(b): return hashlib.sha256(b).hexdigest()
def git(*a): return subprocess.check_output(["git", *a], text=True).strip()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=pathlib.Path)
    p.add_argument("--push", action="store_true", help="commit and push to main after verification")
    a = p.parse_args()
    if digest(a.archive.read_bytes()) != EXPECTED:
        raise SystemExit("Unexpected ZIP SHA-256; use the exact approved archive.")
    root = pathlib.Path(git("rev-parse", "--show-toplevel"))
    if a.push:
        if git("branch", "--show-current") != "main" or git("status", "--porcelain"):
            raise SystemExit("Use a clean main checkout; preserve concurrent work.")
        git("fetch", "origin", "main")
        if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
            raise SystemExit("Synchronize main with origin/main before importing.")
    dest = root / DEST
    plan = {}
    with zipfile.ZipFile(a.archive) as z:
        if z.testzip(): raise SystemExit("Corrupt archive")
        names = z.namelist()
        if len(names) != len(set(names)): raise SystemExit("Duplicate members")
        m = json.loads(z.read("manifest.json"))
        entries = m["sprites"]
        counts = {k: 0 for k in COUNTS}
        paths = set()
        for e in entries:
            path = e["file"]
            category = e["category"]
            if category not in counts or path != f"sprites/{category}/{e['id']}.png":
                raise SystemExit("Invalid sprite path: " + path)
            if path in paths: raise SystemExit("Duplicate sprite: " + path)
            paths.add(path)
            data = z.read(path)
            if digest(data) != e["sha256"] or data[:8] != b"\x89PNG\r\n\x1a\n":
                raise SystemExit("Invalid PNG or hash: " + path)
            if struct.unpack(">II", data[16:24]) != (e["width"], e["height"]):
                raise SystemExit("Incorrect dimensions: " + path)
            counts[category] += 1
        if counts != COUNTS or len(entries) != 64:
            raise SystemExit("Wrong sprite inventory: " + str(counts))
        for path in names:
            rel = pathlib.PurePosixPath(path)
            if rel.is_absolute() or ".." in rel.parts or "\\" in path or ":" in path:
                raise SystemExit("Unsafe member: " + path)
            if path != "manifest.json" and path not in paths and not (len(rel.parts)==2 and rel.parts[0]=="source" and rel.suffix==".png"):
                raise SystemExit("Unexpected member: " + path)
            target = dest.joinpath(*rel.parts)
            if not target.resolve().is_relative_to(dest.resolve()):
                raise SystemExit("Unsafe destination")
            data = z.read(path)
            if target.exists() and target.read_bytes() != data:
                raise SystemExit("Refusing to overwrite different file: " + str(target))
            plan[target] = data
    for target, data in plan.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists(): target.write_bytes(data)
        if digest(target.read_bytes()) != digest(data):
            raise SystemExit("Write verification failed: " + str(target))
    print("64 approved sprite PNGs and 4 source PNGs verified individually; runtime not changed.")
    if a.push:
        git("add", "--", DEST)
        if git("diff", "--cached", "--name-only"):
            print(git("commit", "-m", "assets: import 64 user-approved Valley expansion sprites"))
        git("push", "origin", "main")
        git("fetch", "origin", "main")
        for target, data in plan.items():
            path = target.relative_to(root).as_posix()
            actual = subprocess.check_output(["git", "show", "origin/main:" + path])
            if digest(actual) != digest(data): raise SystemExit("Remote verification failed: " + path)
        print("Remote origin/main verified byte-for-byte:", git("rev-parse", "origin/main"))
if __name__ == "__main__": main()
