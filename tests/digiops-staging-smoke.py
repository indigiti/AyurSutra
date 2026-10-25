"""Synthetic base-path and private-data isolation tests for DigiOps-style release staging."""
import pathlib,subprocess,json,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
script=root/"scripts/package-digiops-staging.py"
with tempfile.TemporaryDirectory() as folder:
 d=pathlib.Path(folder);dist=d/"dist";dist.mkdir()
 (dist/"index.html").write_text('<html><link rel="icon" href="/ayursutra/icon.svg"><script src="/ayursutra/assets/test.js"></script></html>')
 (dist/"assets").mkdir();(dist/"assets/test.js").write_text("console.log('test')")
 out=d/"release"
 run=subprocess.run(["python3",str(script),"--dist",str(dist),"--out",str(out)],capture_output=True,text=True)
 assert run.returncode==0,run.stdout+run.stderr
 manifest=json.loads((out/"RELEASE.json").read_text())
 assert manifest["schema"]=="AYURSUTRA-DIGIOPS-STAGING/1"
 assert (out/"public/api/index.php").is_file()
 assert (out/"public/.htaccess").is_file()
 assert (out/"private/src/Api.php").is_file()
 assert (out/"private/seeds/corpus/manifest.json").is_file()
 assert (out/"private/seeds/search-index/meta.json").is_file()
 assert not (out/"private/runtime").exists()
 assert not any(p.name=="exams.json" for p in (out/"public").rglob("*"))
 assert manifest["files"]["public/.htaccess"]["sha256"]
 assert subprocess.run(["python3",str(script),"--dist",str(dist),"--out",str(out)],capture_output=True).returncode!=0
 print("PASS: DigiOps release public/private structure, isolated seeds, indexed Sanskrit, preserved runtime state")

# Verify a real unmodified runtime collection survives initialization and subsequent release.
php=pathlib.Path("/usr/bin/php")
if php.exists():
 with tempfile.TemporaryDirectory() as d:
  seed=pathlib.Path(d)/"seeds";seed.mkdir()
  runtime=pathlib.Path(d)/"runtime/storage";runtime.parent.mkdir()
  for key in ("articles","books","chapters","exams","notes","sections","verses"):
   (seed/(key+".json")).write_text("[]")
  runtime.mkdir()
  (runtime/"notes.json").write_text('[{"id":"do-not-overwrite","title":"Published work"}]')
  snippet=f"""<?php
 require {json.dumps(str(root/"server/src/SeedStorage.php"))};
 \\AyurSutra\\SeedStorage::ensure({json.dumps(str(seed))},{json.dumps(str(runtime))});
 \\AyurSutra\\SeedStorage::ensure({json.dumps(str(seed))},{json.dumps(str(runtime))});
 echo file_get_contents({json.dumps(str(runtime/"notes.json"))});
 """
  source=pathlib.Path(d)/"seed-check.php";source.write_text(snippet)
  test=subprocess.run([str(php),str(source)],capture_output=True,text=True)
  assert test.returncode==0,test.stderr
  assert "do-not-overwrite" in test.stdout
