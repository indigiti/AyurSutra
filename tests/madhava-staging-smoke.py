"""Synthetic 68+2 heading fixture; protects against publishing bogus or truncated sections."""
import importlib.util,json,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('madhava_stage',root/'scripts/stage-madhava-wikisource.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as temp:
    output=Path(temp)/'private'/'madhava-drafts.json'
    text=''.join('== अध्यायः '+str(n)+' ==\n:प्रथमपङ्क्तिः\n:द्वितीयपङ्क्तिः\n:तृतीयपङ्क्तिः\n' for n in range(1,69))
    text+='== विषयानुक्रमणिका ==\nIndex\n== स्रोतः ==\nSource\n'
    details=module.stage(text,10001,output)
    payload=json.loads(output.read_text())
    assert details['staged_draft_chapters']==67
    assert len(payload['chapters'])==67
    assert payload['chapters'][0]['chapter_slug']=='chapter-02'
    assert payload['chapters'][-1]['chapter_slug']=='chapter-68'
    assert payload['chapters'][0]['passages'][0]['reference']=='source-line-0001'
    assert payload['chapters'][0]['passages'][0]['text_devanagari']=='प्रथमपङ्क्तिः'
    try:module.stage(text,10001,output);raise AssertionError('Overwrote unreviewed content')
    except FileExistsError:pass
    try:module.stage(text.replace('== स्रोतः ==','== another =='),10001,Path(temp)/'reject.json');raise AssertionError('Accepted wrong source structure')
    except ValueError:pass
    print('PASS: Madhava 68 diagnostic sections plus two appendices; 67 additional staged chapters, no publication')
