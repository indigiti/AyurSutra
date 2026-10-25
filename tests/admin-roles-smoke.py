"""Integration checks for named PHP editor roles, publish restrictions and private audit events."""
import hashlib,json,os,shutil,subprocess,tempfile,time,urllib.error,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
tokens={role:'test-'+role+'-'+('x'*40) for role in ('viewer','editor','publisher','admin')}
accounts=[{'id':role+'-test','role':role,'sha256':hashlib.sha256(secret.encode()).hexdigest()} for role,secret in tokens.items()]
with tempfile.TemporaryDirectory() as d:
    storage=Path(d)/'storage';storage.mkdir()
    for name in ('books','verses','articles','sections','chapters','exams','notes'):
        shutil.copyfile(root/'server/storage'/f'{name}.json',storage/f'{name}.json')
    env={**os.environ,'AYURSUTRA_ADMIN_TOKEN':'legacy-private-token-'+'z'*40,
        'AYURSUTRA_ADMIN_USERS_JSON':json.dumps(accounts),'AYURSUTRA_STORAGE_PATH':str(storage)}
    proc=subprocess.Popen(['php','-S','127.0.0.1:8372','-t','server/public','server/public/router.php'],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def call(path,role=None,method='GET',body=None):
        headers={'Authorization':'Bearer '+tokens[role]} if role else {}
        if body is not None:headers['Content-Type']='application/json'
        req=urllib.request.Request('http://127.0.0.1:8372/api/v1/'+path,
            headers=headers,method=method,data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(req,timeout=4) as res:return res.status,json.load(res)
        except urllib.error.HTTPError as error:return error.code,json.load(error)
    try:
        for i in range(50):
            try:call('status');break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('PHP failed to start')
        assert call('admin/status',None)[0]==401
        assert call('admin/status','viewer')[1]['role']=='viewer'
        assert call('admin/audit','viewer')[0]==403
        assert call('admin/articles','viewer')[0]==200
        note={'title':'Controlled title','body':'Authorized original text','subject':'Shalya Tantra','level':'BAMS'}
        assert call('admin/notes',role='viewer',method='POST',body=note)[0]==403
        code,created=call('admin/notes','editor','POST',note)
        assert code==201,(code,created)
        nid=created['data']['id']
        assert call('admin/notes/'+nid+'/publish','editor','POST',{})[0]==403
        assert call('admin/notes/'+nid+'/publish','publisher','POST',{})[0]==200
        assert len(call('notes')[1]['data'])==1
        code,events=call('admin/audit','admin')
        assert code==200 and len(events['data'])==2,events
        assert {x['actor'] for x in events['data']}=={'editor-test','publisher-test'}
        serialized=json.dumps(events)
        assert not any(t in serialized for t in tokens.values())
        assert call('admin/status',None)[0]==401
        print('PASS: named editor/viewer/publisher roles, admin-only audit, legacy-disable and secret-safe records')
    finally:proc.terminate();proc.wait(timeout=5)
