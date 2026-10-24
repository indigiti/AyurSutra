"""Public academy search regression: source text, drafts, multilingual and answer privacy."""
from pathlib import Path
import json,os,shutil,subprocess,tempfile,time,urllib.request,urllib.error
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temp:
    storage=Path(temp)
    for name in ('books','verses','sections','chapters','notes','exams','articles'):
        shutil.copyfile(root/'server/storage'/f'{name}.json',storage/f'{name}.json')
    chapters=json.loads((storage/'chapters.json').read_text())
    passages=[{'id':'test-passage','reference':'1.2','text_devanagari':'शल्यस्थानं परीक्षणम्','text_iast':'shalya test',
      'translation_en':'Unique study content for public search','commentary':'Traditional commentary',
      'key_terms':[{'term':'vraṇa','definition':'Wound'}]}]
    base={'id':'sushruta-samhita/sutrasthanam/vedotpattyadhyayah','book_id':'sushruta-samhita',
      'section_slug':'sutrasthanam','chapter_slug':'vedotpattyadhyayah','title':'Vedotpatti Reviewed Chapter',
      'status':'published','passages':passages}
    chapters.append(base)
    chapters.append({**base,'id':'sushruta-samhita/sutrasthanam/second-test','chapter_slug':'second-test',
                     'title':'PrivateMint Chapter','status':'draft',
                     'passages':[{**passages[0],'translation_en':'SecretMint material'}]})
    (storage/'chapters.json').write_text(json.dumps(chapters,ensure_ascii=False))
    notes=[{'id':'n1','slug':'my-available-note','title':'Shalya published note','subject':'Shalya',
            'body':'UniqueNote studies','status':'published'},
           {'id':'n2','slug':'secret-note','title':'PrivateMint study note','subject':'Shalya',
            'body':'SecretMint appendix','status':'draft'}]
    (storage/'notes.json').write_text(json.dumps(notes))
    exams=json.loads((storage/'exams.json').read_text())
    exam=next(e for e in exams if e['id']=='aiapget-2017')
    exam.update({'status':'published','questions':[{'id':'q1','question':'SuperSecretQuestion','answer':0,'options':['A','B','C','D'],
      'explanation':'TopSecretExplanation'}],'published_count':1})
    (storage/'exams.json').write_text(json.dumps(exams))
    env=dict(os.environ,AYURSUTRA_STORAGE_PATH=str(storage))
    server=subprocess.Popen(['php','-S','127.0.0.1:8175','-t','server/public','server/public/router.php'],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def fetch(query):
        u='http://127.0.0.1:8175/api/v1/search?'+urllib.parse.urlencode(query)
        try:
            with urllib.request.urlopen(u,timeout=5) as res:return res.status,json.load(res)
        except urllib.error.HTTPError as err:return err.code,json.load(err)
    try:
        for _ in range(50):
            try:status,_=fetch({'q':'charaka'});break
            except Exception:time.sleep(.1)
        assert status==200
        status,result=fetch({'q':'अथातो','type':'texts'})
        assert status==200 and any(r['type']=='verse' for r in result['data']),result
        status,result=fetch({'q':'vraṇa','type':'texts'})
        assert status==200 and any(r['type']=='passage' for r in result['data']),result
        status,result=fetch({'q':'UniqueNote','type':'notes'})
        assert status==200 and len(result['data'])==1 and result['data'][0]['type']=='note',result
        status,result=fetch({'q':'AIAPGET','type':'exams'})
        assert status==200 and len(result['data'])==1
        assert 'answer' not in json.dumps(result) and 'SuperSecretQuestion' not in json.dumps(result)
        status,result=fetch({'q':'PrivateMint'})
        assert status==200 and result['total']==0,result
        status,result=fetch({'q':'SecretMint'})
        assert status==200 and result['total']==0,result
        status,result=fetch({'q':'x'*121})
        assert status==422,result
        status,result=fetch({'q':'AIAPGET','type':'typo'})
        assert status==422,result
        print('PASS: Unicode verse search, key terms, published chapter/notes/exams, draft isolation, answer privacy and validation')
    finally:
        server.terminate();server.wait(timeout=5)
