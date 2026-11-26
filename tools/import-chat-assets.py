#!/usr/bin/env python3
"""Import ChatGPT-created art packs as individual files; never deploy REVIEW art."""
import argparse, hashlib, json, pathlib, re, subprocess, zipfile
P=pathlib.Path
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument("source",type=P)
ap.add_argument("--commit",action="store_true")
ap.add_argument("--push",action="store_true")
a=ap.parse_args()
def git(*args):
    return subprocess.check_output(["git",*args],text=True).strip()
root=P(git("rev-parse","--show-toplevel"))
if a.push and not a.commit: ap.error("--push requires --commit")
if a.commit and git("status","--porcelain"): raise SystemExit("Working tree not clean; commit your own changes first.")
if a.commit and git("branch","--show-current")!="main": raise SystemExit("Use a clean main checkout.")
if a.commit:
    git("fetch","origin","main")
    if git("rev-parse","HEAD")!=git("rev-parse","origin/main"): raise SystemExit("Synchronize main using a safe fast-forward first.")
packs=sorted(p for p in a.source.glob("*.zip") if p.name.startswith(("fz-","frequencia-zero-")) and p.name!="frequencia-zero-kit.zip")
if not packs: raise SystemExit("No generated packs found.")
dest=root/"assets"/"review"/"chatgpt-import"
allowed={".png",".jpg",".jpeg",".webp",".gif",".svg",".json",".txt",".md"}
plan={}; catalog=[]
for pack in packs:
    with zipfile.ZipFile(pack) as z:
        if z.testzip() is not None: raise SystemExit("Corrupt archive: "+pack.name)
        for info in z.infolist():
            if info.is_dir(): continue
            rel=pathlib.PurePosixPath(info.filename.replace(chr(92),"/"))
            if rel.is_absolute() or ".." in rel.parts or any(":" in x for x in rel.parts): raise SystemExit("Unsafe member: "+info.filename)
            if rel.suffix.lower() not in allowed: continue
            target=dest/pack.stem/P(*rel.parts)
            if not target.resolve().is_relative_to(dest.resolve()): raise SystemExit("Unsafe target: "+str(target))
            data=z.read(info)
            digest=hashlib.sha256(data).hexdigest()
            if target in plan and plan[target]!=data: raise SystemExit("Conflicting archive entry: "+str(target))
            if target.exists() and target.read_bytes()!=data: raise SystemExit("Existing different file: "+str(target))
            plan[target]=data
            catalog.append({"package":pack.name,"path":target.relative_to(root).as_posix(),"sha256":digest,"bytes":len(data),"status":"REVIEW"})
for target,data in plan.items():
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists(): target.write_bytes(data)
idx=dest/"import-manifest.json"
old=json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else {"files":[]}
entries={e["path"]:e for e in old.get("files",[])}
entries.update({e["path"]:e for e in catalog})
idx.write_text(json.dumps({"status":"REVIEW","files":sorted(entries.values(),key=lambda e:e["path"])},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"{len(packs)} packages; {len(plan)} individual files; {len(set(e['sha256'] for e in catalog))} unique byte hashes")
if a.commit:
    git("add","--",str(dest.relative_to(root)))
    if git("diff","--cached","--name-only"):
        print(git("commit","-m","assets: import individual ChatGPT art sources and review frames"))
    else: print("No new changes.")
    if a.push: print(git("push","origin","main"))
