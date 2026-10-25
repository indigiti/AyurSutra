#!/usr/bin/env python3
"""Produce a deployable staging ZIP with strictly separate public/private directories.

No environment secrets, test fixtures, or live editor data are packaged. The private JSON
collections here are known repository seeds, not a backup of a running application.
"""
import argparse,hashlib,json,os,shutil,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
API_CLASSES=("StoreInterface.php","FileStore.php","CorpusStore.php","SearchService.php",
 "AdminAuthLimiter.php","AdminIdentity.php","AuditTrail.php","Api.php")
COLLECTIONS=("articles","books","chapters","exams","notes","sections","verses")
def copy(src,dst):
 if not src.is_file():raise ValueError("Missing release input: "+str(src))
 dst.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(src,dst)
def create(dist:Path,output:Path):
 if not dist.is_dir() or not (dist/"index.html").exists():raise ValueError("Build dist/ first with npm run build")
 if output.exists():raise FileExistsError("Release archive already exists (do not overwrite)")
 output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix="ayursutra-release-") as td:
  root=Path(td)
  public=root/"public_html";private=root/"private_app"
  shutil.copytree(dist,public)
  for file in API_CLASSES:copy(ROOT/"server/src"/file,private/"src"/file)
  for collection in COLLECTIONS:copy(ROOT/"server/storage"/(collection+".json"),private/"storage"/(collection+".json"))
  shutil.copytree(ROOT/"server/storage/corpus",private/"storage/corpus")
  copy(ROOT/"deploy/cloudways-api-index.php",public/"api/index.php")
  copy(ROOT/"deploy/cloudways-htaccess.txt",public/".htaccess")
  if "\\n#" in (public/".htaccess").read_text():raise ValueError("Apache configuration has an invalid literal newline token")
  # Never package runtime audit logs, secrets, existing unreviewed drafts, cache indexes, or backups.
  files=[p for p in root.rglob("*") if p.is_file()]
  for file in files:
   rel=file.relative_to(root).as_posix()
   if any(part in ("private","backups","staging",".git","node_modules") for part in file.parts if part not in ("private_app",)):
    raise ValueError("Unexpected private data: "+rel)
   if rel.startswith("public_html/server") or rel.startswith("public_html/storage"):
    raise ValueError("Private PHP or JSON storage leaked to public webroot: "+rel)
  manifest={"schema":1,"artifact":"AyurSutra Cloudways staging package","runtime_secrets_included":False,
    "source_corpus_included":True,"immutable_repository_seeds_only":True,
    "layout":{"public":"public_html/","private":"private_app/"},"files":{}}
  for file in sorted(files):
   rel=file.relative_to(root).as_posix()
   manifest["files"][rel]={"bytes":file.stat().st_size,
     "sha256":hashlib.sha256(file.read_bytes()).hexdigest()}
  (root/"release-checksums.json").write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
  with zipfile.ZipFile(output,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
   for file in sorted(root.rglob("*")):
    if file.is_file():archive.write(file,file.relative_to(root).as_posix())
 return {"file":str(output),"included_files":len(files),"zip_sha256":hashlib.sha256(output.read_bytes()).hexdigest()}
def main():
 p=argparse.ArgumentParser();p.add_argument("--dist",type=Path,default=ROOT/"dist")
 p.add_argument("--output",type=Path,required=True);args=p.parse_args()
 print(json.dumps(create(args.dist,args.output),indent=2))
if __name__=="__main__":main()
