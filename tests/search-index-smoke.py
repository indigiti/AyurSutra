"""Functional regression for transliteration-tolerant source index."""
import json,os,subprocess,tempfile,time,urllib.parse,urllib.request,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    dest=Path(td);storage=dest/'storage';storage.mkdir()
    for col in ('books','verses','sections','chapters','notes','exams','articles'):
        shutil.copy(root/'server/storage'/f'{col}.json',storage/f'{col}.json')
    corpus=storage/'corpus';corpus.mkdir()
    sample={'book_id':'charaka-samhita','chapters':[{'section_slug':'sutrasthanam','chapter_slug':'dirghanjivitiya','title':'Synthetic','source_title':'Synthetic',
      'passages':[{'id':'one','reference':'1.1','text_iast':'Āyurveda śāstra','text_devanagari':'आयुर्वेद शास्त्र'}]}]}
    (corpus/'charaka-samhita.json').write_text(json.dumps(sample,ensure_ascii=False))
    (corpus/'manifest.json').write_text(json.dumps({'books':[{'id':'charaka-samhita','sections':[{'slug':'sutrasthanam'}]}]}))
    index=storage/'search-index'
    subprocess.run(['python3','scripts/build-search-index.py','--corpus',str(corpus),'--output',str(index)],cwd=root,check=True)
    assert json.loads((index/'meta.json').read_text())['passages']==1
    env={**os.environ,'AYURSUTRA_STORAGE_PATH':str(storage),'AYURSUTRA_SEARCH_INDEX_PATH':str(index)}
    p=subprocess.Popen(['php','-S','127.0.0.1:8367','-t','server/public','server/public/router.php'],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def search(q):
        with urllib.request.urlopen('http://127.0.0.1:8367/api/v1/search?'+urllib.parse.urlencode({'q':q,'type':'texts'}),timeout=5) as r:return json.load(r)
    try:
        for _ in range(50):
            try:search('ayurveda');break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('PHP did not start')
        for query in ('ayurveda','āyurveda','आयुर्वेद'):
            results=search(query)['data']
            assert any(x['status']=='source-edition' for x in results),query
        print('PASS: sharded source index, IAST transliteration and Devanagari search')
    finally:p.terminate();p.wait(timeout=5)
