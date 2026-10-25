"""Source-edition regression with isolated file storage."""
from pathlib import Path
import json,os,shutil,subprocess,tempfile,time,urllib.parse,urllib.request
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    storage=Path(tmp)/'storage';storage.mkdir()
    for name in ('books','verses','sections','chapters','notes','exams','articles'):
        shutil.copyfile(root/'server/storage'/f'{name}.json',storage/f'{name}.json')
    section=json.loads((storage/'sections.json').read_text())[0]
    book,sth,ch=section['book_id'],section['slug'],section['chapters'][0]['slug']
    corpus=storage/'corpus';corpus.mkdir()
    sample={'id':book+'/'+sth+'/'+ch,'book_id':book,'section_slug':sth,'chapter_slug':ch,
        'title':'Source chapter','status':'source-edition',
        'passages':[{'id':'synthetic-source-1','reference':'1.1','text_iast':'āyurveda source unique'}]}
    (corpus/(book+'.json')).write_text(json.dumps({'book_id':book,'chapters':[sample]}))
    (corpus/'manifest.json').write_text(json.dumps({'books':[{'id':book,'sections':[{
        'slug':sth,'chapters':[{'slug':ch,'passage_count':1,'source_title':'Source chapter'}]}]}]}))
    p=subprocess.Popen(['php','-S','127.0.0.1:8361','-t','server/public','server/public/router.php'],
      cwd=root,env={**os.environ,'AYURSUTRA_STORAGE_PATH':str(storage)},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def get(route):
        with urllib.request.urlopen('http://127.0.0.1:8361/api/v1/'+route,timeout=4) as r:
            return json.load(r)
    try:
        for _ in range(50):
            try:get('status');break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('PHP did not start')
        assert len(get('corpus/status')['data']['books'])==1
        assert get('chapters/'+sample['id'])['data']['status']=='source-edition'
        assert get('sections?book_id='+book)['data'][0]['chapters'][0]['passage_count']==1
        q=urllib.parse.urlencode({'q':'āyurveda','type':'texts'})
        assert any(x['status']=='source-edition' for x in get('search?'+q)['data'])
        editorial={**sample,'status':'published','title':'Approved edition','passages':[{'id':'approved','text_iast':'editorial'}]}
        (storage/'chapters.json').write_text(json.dumps([editorial]))
        assert get('chapters/'+sample['id'])['data']['title']=='Approved edition'
        print('PASS: source edition lookup, public search, status, sections and editorial override')
    finally:
        p.terminate();p.wait(timeout=5)
