"""Integration coverage for complete no-DB Ayana migration, never touching project storage."""
from pathlib import Path
import json, os, shutil, subprocess, tempfile, urllib.request, urllib.error, time
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    base=Path(tmp); storage=base/'storage';storage.mkdir()
    for name in ('articles','books','verses','sections','exams','notes','chapters'):
        shutil.copy(root/'server/storage'/f'{name}.json',storage/f'{name}.json')
    chapter={'book_id':'sushruta-samhita','section_slug':'sutrasthanam','chapter_slug':'vedotpattyadhyayah',
             'title':'Vedotpatti','source_url':'https://ayanaayurveda.com/learn/classical-texts/sushruta-samhita/',
             'passages':[{'reference':'1.1','text_devanagari':'अथातो वेदोत्पत्तिमध्यायं व्याख्यास्यामः ॥',
                          'text_iast':'athāto vedotpattim adhyāyaṃ vyākhyāsyāmaḥ','translation_en':'Test-only gloss',
                          'commentary':'Test-only commentary','key_terms':[{'term':'Veda','definition':'Knowledge'}]}]}
    note={'slug':'test-note','title':'Test editorial note','subject':'Shalya Tantra','level':'BAMS','body':'Test only','source_url':'https://ayanaayurveda.com/learn/notes/'}
    questions=[{'id':f'aiapget-2017-{i+1}','question':f'TEST ONLY — question {i+1}',
                'options':['Option A','Option B','Option C','Option D'],'answer':i%4,
                'explanation':'TEST ONLY','subject':'General'} for i in range(100)]
    manifest=base/'export.json';manifest.write_text(json.dumps({'format':'ayursutra-ay-1','chapters':[chapter],
                          'papers':[{'id':'aiapget-2017','questions':questions}],'notes':[note]},ensure_ascii=False))
    cmd=['python3',str(root/'scripts/migrate-ayana.py'),str(manifest),'--storage',str(storage)]
    def run(*args):return subprocess.run(cmd+list(args),capture_output=True,text=True)
    dry=run();assert dry.returncode==0 and json.loads(dry.stdout)['records']=={'chapters':1,'papers':1,'notes':1}
    assert json.loads((storage/'chapters.json').read_text())==[]
    applied=run('--apply');assert applied.returncode==0,applied.stderr+applied.stdout
    state=json.loads(applied.stdout);assert state['counts']['chapters']['new']==1
    assert state['counts']['papers']['updated_draft']==1
    assert Path(state['backup_path']).exists()
    again=run('--apply');assert again.returncode==0;assert json.loads(again.stdout)['counts']['chapters']['unchanged']==1
    bad=json.loads(manifest.read_text());bad['papers'][0]['questions']=bad['papers'][0]['questions'][:3]
    manifest.write_text(json.dumps(bad,ensure_ascii=False))
    invalid=run('--apply');assert invalid.returncode==1 and 'expected 100 complete' in invalid.stdout
    assert len(json.loads((storage/'exams.json').read_text())[0]['questions'])==100
    token='migration-secret-token-'+'x'*35
    env=dict(os.environ,AYURSUTRA_ADMIN_TOKEN=token,AYURSUTRA_STORAGE_PATH=str(storage))
    server=subprocess.Popen(['php','-S','127.0.0.1:8168','-t','server/public','server/public/router.php'],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def api(path,method='GET',body=None,auth=False):
        headers={'Authorization':'Bearer '+token} if auth else {}
        if body is not None:headers['Content-Type']='application/json'
        request=urllib.request.Request('http://127.0.0.1:8168/api/v1/'+path,
            method=method,data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None,headers=headers)
        try:
            with urllib.request.urlopen(request,timeout=4) as response:return response.status,json.load(response)
        except urllib.error.HTTPError as error:return error.code,json.load(error)
    try:
        for _ in range(50):
            try:api('status');break
            except Exception:time.sleep(.1)
        code,private=api('chapters/sushruta-samhita/sutrasthanam/vedotpattyadhyayah');assert code==404
        code,unauth=api('admin/chapters');assert code==401
        code,stats=api('admin/import-status',auth=True);assert code==200 and stats['data']['chapters']['draft']==1
        code,rejected=api('admin/chapters/publish','POST',{'id':'sushruta-samhita/sutrasthanam/vedotpattyadhyayah'},True);assert code==422
        code,published=api('admin/chapters/publish','POST',{'id':'sushruta-samhita/sutrasthanam/vedotpattyadhyayah','review':{'reviewer':'Test Editor','edition':'Synthetic test edition','notes':'Smoke validation','text_checked':True,'rights_confirmed':True}},True);assert code==200
        code,public=api('chapters/sushruta-samhita/sutrasthanam/vedotpattyadhyayah');assert code==200
        assert public['data']['passages'][0]['reference']=='1.1' and public['data']['passages'][0]['commentary']=='Test-only commentary'
        code,index=api('sections?book_id=sushruta-samhita');assert code==200 and index['data'][0]['chapters'][0]['status']=='published'
        code,overwritten=api('admin/chapters/import','POST',chapter,True);assert code==409
        code,exams=api('exams/aiapget-2017');assert code==200 and exams['data']['questions']==[]
        code,notebook=api('notes');assert code==200 and notebook['data']==[]
        manifest.write_text(json.dumps({'format':'ayursutra-ay-1','chapters':[chapter]},ensure_ascii=False))
        rerun=run('--apply');assert rerun.returncode==0 and json.loads(rerun.stdout)['counts']['chapters']['preserved_published']==1
    finally:
        server.terminate();server.wait(timeout=5)
    print('PASS: dry run, staged import, idempotency, backups, strict full papers, draft protection, chapter publish, admin auth, no answer leakage')
