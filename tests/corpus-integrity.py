"""Check source chapter mapping, provenance, and catalog integrity without inventing missing content."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
sections=read('server/storage/sections.json')
manifest=read('server/storage/corpus/manifest.json')
source_registry={s['book_id']:s for s in read('docs/sources.json')}
expected={'charaka-samhita':120,'sushruta-samhita':186,'ashtanga-hridaya':120,'ashtanga-sangraha':150,'madhava-nidana':70}
assert sum(len(s['chapters']) for s in sections)==646
assert read('src/content/sections.json')==sections
assert read('public/content/sections.json')==sections
counts={}
for section in sections:
    assert section['chapter_count']==len(section['chapters']),section['id']
    key=(section['book_id'],section['slug'])
    assert len({c['slug'] for c in section['chapters']})==len(section['chapters']),key
    counts[section['book_id']]=counts.get(section['book_id'],0)+len(section['chapters'])
assert counts==expected,(counts,expected)
assert [x['entry_kind'] for x in next(s for s in sections if s['book_id']=='madhava-nidana')['chapters'][-2:]]==['index','bibliography']
lookup={(s['book_id'],s['slug']):s for s in sections}
imported={}
for book in manifest['books']:
    bid=book['id']
    assert bid in source_registry and source_registry[bid].get('url','').startswith('https://'),bid
    assert source_registry[bid].get('attribution'),bid
    for section in book['sections']:
        key=(bid,section['slug']);assert key in lookup,key
        catalog=lookup[key]['chapters']
        by_slug={c['slug']:c for c in catalog}
        for chapter in section['chapters']:
            assert chapter['slug'] in by_slug,key
            if 'number' in chapter: assert chapter['number']==by_slug[chapter['slug']]['number'],chapter
            assert chapter['passage_count']>=0,chapter
            imported[bid]=imported.get(bid,0)+1
assert imported in ({'charaka-samhita':120,'sushruta-samhita':186,'ashtanga-hridaya':120,'ashtanga-sangraha':150,'madhava-nidana':1},{'charaka-samhita':120,'sushruta-samhita':186,'ashtanga-hridaya':120,'ashtanga-sangraha':150,'madhava-nidana':68}),imported
print('PASS: 646 catalogue entries; source coverage',imported)
print('Madhava source coverage:',imported['madhava-nidana'],'of 68 diagnostic chapters. No claim of verified translations or scholarly review.')
