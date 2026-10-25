#!/usr/bin/env python3
"""Create the exact public/ private/ artifact layout consumed by DigiOps ReleaseManager.

The managed private/ payload is deployable code and *immutable seeds only*. Runtime state is
initialized at request time and remains under private_html/ayursutra/runtime/ across releases.
"""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COLLECTIONS=("articles","books","chapters","exams","notes","sections","verses")
CODE=("StoreInterface.php","FileStore.php","CorpusStore.php","SearchService.php",
      "AdminAuthLimiter.php","AdminIdentity.php","AuditTrail.php","SeedStorage.php","Api.php")
def copy(src,dst):
 if not src.is_file():raise ValueError("Missing deployable source: "+str(src))
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
def package(dist:Path,out:Path):
 if out.exists():raise FileExistsError("Release output must not overwrite an existing directory")
 if not (dist/"index.html").is_file():raise ValueError("Build with VITE_BASE_PATH=/ayursutra/ first")
 html=(dist/"index.html").read_text(encoding="utf-8")
 if "/ayursutra/assets/" not in html or 'href="/ayursutra/icon.svg"' not in html:
  raise ValueError("Staging frontend is not built with the expected /ayursutra/ base")
 public=out/"public";private=out/"private"
 try:
  shutil.copytree(dist,public)
  for name in CODE:copy(ROOT/"server/src"/name,private/"src"/name)
  for name in COLLECTIONS:copy(ROOT/"server/storage"/f"{name}.json",private/"seeds"/f"{name}.json")
  shutil.copytree(ROOT/"server/storage/corpus",private/"seeds/corpus")
  copy(ROOT/"deploy/digiops-api-index.php",public/"api/index.php")
  copy(ROOT/"deploy/cloudways-htaccess.txt",public/".htaccess")
  # Ship a prebuilt source search index: no live hosting cron/console required.
  subprocess.run(["python3",str(ROOT/"scripts/build-search-index.py"),
     "--corpus",str(private/"seeds/corpus"),"--output",str(private/"seeds/search-index")],
     check=True,capture_output=True,text=True)
  forbidden=("private/runtime/","public/server/","public/storage/","public/private/",
             "public/.env","private/.env")
  result={}
  for file in sorted(out.rglob("*")):
   if not file.is_file():continue
   name=file.relative_to(out).as_posix()
   if name.startswith(forbidden) or "/.git/" in name or "/node_modules/" in name:
    raise ValueError("Unexpected runtime/private contents inside packaged release: "+name)
   blob=file.read_bytes()
   result[name]={"size":len(blob),"sha256":hashlib.sha256(blob).hexdigest()}
  manifest={"schema":"AYURSUTRA-DIGIOPS-STAGING/1","public":"public","private":"private",
    "appPath":"/ayursutra/","private_runtime_included":False,
    "source_revision":"Sanskrit Wikisource 75848, unproofread",
    "files":result}
  (out/"RELEASE.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
  return {"files":len(result),"manifest":str(out/"RELEASE.json"),"public":len(list(public.rglob("*")))}
 except Exception:
  if out.exists():shutil.rmtree(out)
  raise
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--dist",type=Path,default=ROOT/"dist")
 p.add_argument("--out",type=Path,default=ROOT/"release")
 args=p.parse_args()
 print(json.dumps(package(args.dist,args.out),indent=2))
if __name__=="__main__":main()
