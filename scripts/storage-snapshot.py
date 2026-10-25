#!/usr/bin/env python3
"""Verified private JSON-store snapshot and *isolated* restore drill.

No production-storage restore function exists. Never place snapshots in public_html.
"""
from __future__ import annotations
import argparse,datetime,hashlib,io,json,os,pathlib,sys,tarfile,tempfile

COLLECTIONS={"articles","books","chapters","exams","notes","sections","verses"}
MAX_BYTES=256*1024*1024
def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def valid_name(name:str)->bool:
    p=pathlib.PurePosixPath(name)
    return name.startswith("storage/") and len(p.parts)>1 and not p.is_absolute() and ".." not in p.parts and "\\" not in name
def snapshot(storage:pathlib.Path,archive:pathlib.Path)->dict:
    storage=storage.resolve()
    archive=archive.expanduser().absolute()
    if not storage.is_dir():raise ValueError("Private storage directory does not exist")
    if "public_html" in archive.parts:raise ValueError("Never write backups into public_html")
    if storage in archive.parents:raise ValueError("Archive must be outside application storage")
    content={}
    for path in sorted(storage.rglob("*")):
        if path.is_symlink():raise ValueError("Symlink prohibited: "+str(path))
        if not path.is_file():continue
        if "backups" in path.relative_to(storage).parts:continue
        if path.suffix not in (".json",".jsonl"):continue
        rel="storage/"+path.relative_to(storage).as_posix()
        if not valid_name(rel):raise ValueError("Invalid snapshot path")
        content[rel]=path.read_bytes()
    if not COLLECTIONS.issubset({pathlib.PurePosixPath(p).stem for p in content if len(pathlib.PurePosixPath(p).parts)==2}):
        raise ValueError("Required data collections missing")
    total=sum(map(len,content.values()))
    if total>MAX_BYTES:raise ValueError("Snapshot exceeds 256 MiB bound")
    manifest={"version":1,"created_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "items":{p:{"bytes":len(blob),"sha256":sha(blob)} for p,blob in content.items()}}
    archive.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(archive,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"wb") as sink,tarfile.open(fileobj=sink,mode="w:gz") as tar:
            for name,blob in content.items():
                item=tarfile.TarInfo(name);item.size=len(blob);item.mode=0o600
                tar.addfile(item,io.BytesIO(blob))
            m=json.dumps(manifest,ensure_ascii=False,sort_keys=True).encode()
            item=tarfile.TarInfo("snapshot-manifest.json");item.size=len(m);item.mode=0o600
            tar.addfile(item,io.BytesIO(m))
    except Exception:
        archive.unlink(missing_ok=True)
        raise
    return {"items":len(content),"bytes":total,"sha256":sha(archive.read_bytes()),"archive":str(archive)}
def verify(archive:pathlib.Path,simulate:bool=False)->dict:
    content={};manifest=None
    with tarfile.open(archive,"r:gz") as tar:
        for member in tar:
            if not member.isfile() or member.size>MAX_BYTES or member.name in content:
                raise ValueError("Unexpected archive member")
            if member.name!="snapshot-manifest.json" and not valid_name(member.name):
                raise ValueError("Unsafe archive member")
            file=tar.extractfile(member)
            if file is None:raise ValueError("Missing data")
            blob=file.read(MAX_BYTES+1)
            if len(blob)!=member.size:raise ValueError("Incorrect archive size")
            if member.name=="snapshot-manifest.json":
                if manifest is not None:raise ValueError("Duplicate manifest")
                manifest=json.loads(blob)
            else:
                content[member.name]=blob
        if manifest is None or manifest.get("version")!=1:raise ValueError("Missing snapshot manifest")
        claims=manifest.get("items",{})
        if set(claims)!=set(content):raise ValueError("Snapshot file list mismatch")
        if sum(map(len,content.values()))>MAX_BYTES:raise ValueError("Snapshot too large")
        for name,blob in content.items():
            if claims[name]["sha256"]!=sha(blob) or claims[name]["bytes"]!=len(blob):
                raise ValueError("Snapshot checksum mismatch: "+name)
            if name.endswith(".json"):
                record=json.loads(blob)
                if name.count("/")==1 and pathlib.PurePosixPath(name).stem in COLLECTIONS:
                    if not isinstance(record,list):raise ValueError("Invalid data collection shape: "+name)
        if not COLLECTIONS.issubset({pathlib.PurePosixPath(p).stem for p in content if p.count("/")==1}):
            raise ValueError("Missing required data collection")
    if simulate:
        with tempfile.TemporaryDirectory(prefix="ayursutra-restore-check-") as td:
            directory=pathlib.Path(td)
            for name,blob in content.items():
                path=directory/name
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(blob)
                if sha(path.read_bytes())!=sha(blob):raise ValueError("Isolated restore failed")
    return {"verified":True,"simulated_restore":simulate,"items":len(content),
            "bytes":sum(map(len,content.values())),"snapshot_sha256":sha(archive.read_bytes())}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--storage",type=pathlib.Path)
    p.add_argument("--archive",type=pathlib.Path,required=True)
    p.add_argument("--snapshot",action="store_true")
    p.add_argument("--verify",action="store_true")
    p.add_argument("--simulate-restore",action="store_true")
    args=p.parse_args()
    if sum((args.snapshot,args.verify,args.simulate_restore))!=1:
        p.error("Choose one of --snapshot, --verify, or --simulate-restore")
    try:
        if args.snapshot:
            if not args.storage:p.error("--storage is required to create a snapshot")
            report=snapshot(args.storage,args.archive)
        else:report=verify(args.archive,simulate=args.simulate_restore)
        print(json.dumps({"ok":True,**report},indent=2))
    except (OSError,ValueError,KeyError,json.JSONDecodeError,tarfile.TarError) as err:
        print(json.dumps({"ok":False,"error":str(err)}));sys.exit(1)
if __name__=="__main__":main()
