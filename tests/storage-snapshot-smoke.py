"""Exercises immutable backup + checksum verification + disposable restore."""
from pathlib import Path
import json,shutil,subprocess,tempfile
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as t:
    home=Path(t); storage=home/'application-storage';storage.mkdir()
    for n in ('articles','books','chapters','exams','notes','sections','verses'):
        shutil.copyfile(root/'server/storage'/f'{n}.json',storage/f'{n}.json')
    (storage/'private/audit').mkdir(parents=True)
    (storage/'private/audit/events.jsonl').write_text('{"event":"test"}\n')
    archive=home/'private-backup'/'snapshot.tar.gz'
    def run(*args):
        return subprocess.run(['python3','scripts/storage-snapshot.py','--archive',str(archive),*args],
                              cwd=root,capture_output=True,text=True)
    one=run('--snapshot','--storage',str(storage))
    assert one.returncode==0,one.stderr+one.stdout
    assert archive.exists()
    assert run('--snapshot','--storage',str(storage)).returncode!=0,"must never overwrite backup"
    verified=run('--verify')
    assert verified.returncode==0,verified.stderr+verified.stdout
    drill=run('--simulate-restore')
    assert drill.returncode==0,drill.stderr+drill.stdout
    assert json.loads(drill.stdout)['simulated_restore'] is True
    archive.write_bytes(archive.read_bytes()[:45])
    bad=run('--verify')
    assert bad.returncode!=0,"truncated backup must fail"
    print('PASS: exclusive private snapshot, authenticated hashes, bounded extraction and isolated restore drill')
