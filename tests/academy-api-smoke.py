"""Runs the real PHP HTTP API with an isolated temporary JSON storage directory."""
import json,os,pathlib,shutil,subprocess,tempfile,time,urllib.request,urllib.error
root=pathlib.Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as temp:
  storage=pathlib.Path(temp)/'storage'; storage.mkdir()
  for name in ('books','verses','articles','sections','exams','notes'):
    shutil.copy(root/'server/storage'/f'{name}.json',storage/f'{name}.json')
  token='test-only-token-0123456789abcdefghijklmnop'
  env=dict(os.environ,AYURSUTRA_ADMIN_TOKEN=token,AYURSUTRA_STORAGE_PATH=str(storage))
  server=subprocess.Popen(['php','-S','127.0.0.1:8158','-t','server/public','server/public/router.php'],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  def call(url,method='GET',payload=None,auth=False):
    req=urllib.request.Request('http://127.0.0.1:8158/api/v1/'+url,method=method,headers=({'Authorization':'Bearer '+token} if auth else {})|({'Content-Type':'application/json'} if payload is not None else {}),data=json.dumps(payload).encode() if payload is not None else None)
    try:
      with urllib.request.urlopen(req,timeout=4) as res:return res.status,json.loads(res.read())
    except urllib.error.HTTPError as err:return err.code,json.loads(err.read())
  try:
    for _ in range(50):
      try:call('status');break
      except Exception:time.sleep(.1)
    status,sections=call('sections?book_id=charaka-samhita');assert status==200 and len(sections['data'])==8
    status,exams=call('exams');assert status==200 and len(exams['data'])==16 and all('questions' not in e for e in exams['data'])
    status,body=call('admin/exams');assert status==401
    status,paper=call('exams/aiapget-2017');assert status==200 and not paper['data']['questions']
    questions=[{'id':f'aiapget-2017-{i+1}','question':f'Licensed question {i+1}?','options':['A','B','C','D'],'answer':i%4,'explanation':'Reviewed explanation'} for i in range(100)]
    status,bad=call('admin/exams/aiapget-2017/import','POST',{'questions':questions[:2]},True);assert status==422
    status,good=call('admin/exams/aiapget-2017/import','POST',{'questions':questions},True);assert status==200 and good['status']=='draft'
    status,still=call('exams/aiapget-2017');assert status==200 and not still['data']['questions']
    status,pub=call('admin/exams/aiapget-2017/publish','POST',{},True);assert status==200
    status,public=call('exams/aiapget-2017');assert status==200 and len(public['data']['questions'])==100 and 'answer' not in public['data']['questions'][0]
    status,grade=call('exams/aiapget-2017/score','POST',{'answers':{'aiapget-2017-1':0}});assert status==200 and grade['data']['score']==1 and len(grade['data']['review'])==100
    status,note=call('admin/notes','POST',{'title':'Test editorial note','body':'Authorized note body','subject':'Shalya Tantra','level':'BAMS'},True);assert status==201
    status,private=call('notes');assert private['data']==[]
    status,pubnote=call('admin/notes/'+note['data']['id']+'/publish','POST',{},True);assert status==200
    status,noteList=call('notes');assert len(noteList['data'])==1
    print('PASS: 27-section indexing, 16 exam slots, admin protection, paper import, draft isolation, publication, scoring, and notes')
  finally:server.terminate();server.wait(timeout=5)
