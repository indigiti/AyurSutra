"""Pinned source conversion must retain every original chapter and guard source-line counts."""
import json,subprocess,tempfile,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 directory=Path(tmp)/"storage";(directory/"corpus/sections").mkdir(parents=True)
 for path in ["books.json","corpus/manifest.json","corpus/sections/madhava-nidana-madhavanidana.json"]:
  source=root/"server/storage"/path
  dest=directory/path
  shutil.copyfile(source,dest)
 # Synthetic test reproduces the one-chapter pre-migration fixture without altering repository sources.
 corpus_file=directory/"corpus/sections/madhava-nidana-madhavanidana.json"
 old=json.loads(corpus_file.read_text())
 old["chapters"]=old["chapters"][:1]
 corpus_file.write_text(json.dumps(old,ensure_ascii=False))
 manifest_file=directory/"corpus/manifest.json"
 manifest=json.loads(manifest_file.read_text())
 record=next(b for b in manifest["books"] if b["id"]=="madhava-nidana")
 record["sections"][0]["chapters"]=record["sections"][0]["chapters"][:1]
 record["chapters"]=1;record["passages"]=len(old["chapters"][0]["passages"])
 manifest_file.write_text(json.dumps(manifest,ensure_ascii=False))
 draft={"format":"ayursutra-ay-1","chapters":[]}
 for n in range(2,69):
  draft["chapters"].append({"book_id":"madhava-nidana","section_slug":"madhavanidana",
   "chapter_slug":f"chapter-{n:02d}","title":f"अध्यायः {n}",
   "source_url":"https://sa.wikisource.org/wiki/माधवनिदानम्?oldid=75848",
   "passages":[{"reference":f"source-line-{i:04d}","text_devanagari":"सङ्केतपाठः "+str(i)}
     for i in range(1,(49 if n<=50 else 48)+1)]})
 # 49 chapters x 49 lines, 18 chapters x 48 lines => 3265 synthetic source lines.
 (Path(tmp)/"draft.json").write_text(json.dumps(draft,ensure_ascii=False))
 cmd=["python3","scripts/promote-madhava-source.py","--draft",str(Path(tmp)/"draft.json"),"--storage",str(directory),
      "--source-sha256","d726be9abd42def48814c5dec748b295e6a887cc9697c9df3deec8e41bacd44b"]
 run=subprocess.run(cmd,cwd=root,capture_output=True,text=True);assert run.returncode==0,run.stderr
 assert len(json.load(open(directory/"corpus/sections/madhava-nidana-madhavanidana.json"))["chapters"])==1
 run=subprocess.run(cmd+["--apply"],cwd=root,capture_output=True,text=True)
 assert run.returncode==0,run.stderr
 chapters=json.load(open(directory/"corpus/sections/madhava-nidana-madhavanidana.json"))["chapters"]
 assert len(chapters)==68 and sum(len(c["passages"]) for c in chapters)==3286
 assert chapters[1]["verification"].startswith("Unproofread")
 run=subprocess.run(cmd+["--apply"],cwd=root,capture_output=True,text=True)
 assert run.returncode==0,"Idempotent import must verify existing pinned source"
 assert json.loads(run.stdout)["already_imported"] is True
 print("PASS: pinned 67-chapter conversion, no dry-run writes, 68 chapter count, unproofread warnings")
