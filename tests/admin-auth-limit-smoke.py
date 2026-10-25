"""Verify that repeated bad admin tokens are rate limited with isolated storage."""
import json,os,subprocess,tempfile,time,urllib.error,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    token='test-token-abcdefghijklmnop0123456789abcd'
    env={**os.environ,'AYURSUTRA_STORAGE_PATH':tmp,'AYURSUTRA_ADMIN_TOKEN':token}
    p=subprocess.Popen(['php','-S','127.0.0.1:8364','-t','server/public','server/public/router.php'],cwd=root,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def check(auth=None):
        headers={'Authorization':'Bearer '+auth} if auth else {}
        req=urllib.request.Request('http://127.0.0.1:8364/api/v1/admin/status',headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=4) as res:return res.status
        except urllib.error.HTTPError as err:return err.code
    try:
        for _ in range(50):
            try:check();break
            except Exception:time.sleep(.1)
        else:raise RuntimeError('API server failed to start')
        assert check(token)==200,'valid admin token refused'
        for _ in range(10):assert check('incorrect')==401
        assert check('incorrect')==429,'no throttle after 10 failures'
        assert check(token)==429,'throttle must not be bypassed by trying a valid credential'
        print('PASS: valid token, failure counting, and 15-minute brute-force lockout')
    finally:p.terminate();p.wait(timeout=5)
