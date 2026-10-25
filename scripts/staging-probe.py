#!/usr/bin/env python3
"""Read-only acceptance checks against an explicit HTTPS staging origin."""
import argparse,json,time,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone
from urllib.parse import urlparse
p=argparse.ArgumentParser()
p.add_argument('--base-url',required=True)
p.add_argument('--max-p95-ms',type=float,default=2500)
p.add_argument('--output',default='staging-health.json')
args=p.parse_args()
base=args.base_url.rstrip('/')
parsed=urlparse(base)
if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
    p.error('Use an HTTPS origin without credentials or query parameters')
routes=[
 ('/','html'),('/library','html'),('/library/charaka-samhita/sutrasthanam/dirghanjivitiya','html'),
 ('/mcq','html'),('/api/v1/status','json'),('/api/v1/books','json'),
 ('/api/v1/sections?book_id=charaka-samhita','json'),('/api/v1/corpus/status','json'),
 ('/api/v1/chapters/charaka-samhita/sutrasthanam/dirghanjivitiya','json'),
 ('/api/v1/search?'+urllib.parse.urlencode({'q':'āyurveda','type':'texts'}),'json'),
 ('/api/v1/admin/status','unauthorized')]
observed=[];failures=[]
for route,kind in routes:
    durations=[]
    for attempt in range(3 if route=='/api/v1/status' else 1):
        req=urllib.request.Request(base+route,headers={'User-Agent':'AyurSutra-staging-acceptance/1.0'},method='GET')
        start=time.perf_counter()
        try:
            with urllib.request.urlopen(req,timeout=12) as response:
                status=response.status;content_type=response.headers.get('Content-Type','')
                headers=dict(response.headers);payload=response.read(2_000_000)
        except urllib.error.HTTPError as error:
            status=error.code;content_type=error.headers.get('Content-Type','');headers=dict(error.headers);payload=error.read(2_000_000)
        except Exception as error:
            failures.append({'route':route,'failure':type(error).__name__});break
        ms=round((time.perf_counter()-start)*1000,2);durations.append(ms)
        expected=401 if kind=='unauthorized' else 200
        if status!=expected:failures.append({'route':route,'status':status,'expected':expected})
        if kind=='html' and 'text/html' not in content_type:failures.append({'route':route,'failure':'Content-Type not HTML'})
        if kind in ('json','unauthorized') and 'application/json' not in content_type:failures.append({'route':route,'failure':'Content-Type not JSON'})
        if kind=='json':
            try:
                d=json.loads(payload)
                if route.startswith('/api/v1/chapters/') and not d.get('data',{}).get('passages'):failures.append({'route':route,'failure':'source passages missing'})
            except Exception:failures.append({'route':route,'failure':'invalid JSON response'})
        if route=='/':
            for h in ('X-Content-Type-Options','X-Frame-Options'):
                if h not in headers:failures.append({'route':route,'failure':'missing '+h})
    observed.append({'route':route,'measurements_ms':durations,'max_ms':max(durations) if durations else None})
samples=sorted(t for x in observed for t in x['measurements_ms'])
p95=samples[max(0,int(len(samples)*0.95)-1)] if samples else None
if p95 is not None and p95>args.max_p95_ms:failures.append({'failure':'p95 over threshold','p95_ms':p95})
report={'site':base,'time_utc':datetime.now(timezone.utc).isoformat(),'checks':observed,
'p95_ms':p95,'max_p95_ms':args.max_p95_ms,'passed':not failures,'failures':failures}
with open(args.output,'w',encoding='utf-8') as f:json.dump(report,f,indent=2,ensure_ascii=False)
print(json.dumps({'passed':report['passed'],'p95_ms':p95,'checks':len(observed),'failures':failures},ensure_ascii=False))
raise SystemExit(0 if report['passed'] else 1)
