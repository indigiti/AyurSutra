#!/usr/bin/env python3
"""Build a deterministic, private, read-only sharded index of attributed Sanskrit source tokens.

Run after corpus import, with the same private paths the PHP API uses.
It does not index editorial drafts, translations, notes, or exam answer keys.
"""
import argparse, hashlib, json, re, unicodedata
from collections import defaultdict
from pathlib import Path

MAPPING=str.maketrans({'ā':'a','ī':'i','ū':'u','ṛ':'r','ṝ':'r','ḷ':'l','ḹ':'l',
 'ṅ':'n','ñ':'n','ṇ':'n','ṭ':'t','ḍ':'d','ś':'s','ṣ':'s','ṃ':'m','ṁ':'m','ḥ':'h','ḻ':'l'})
def tokens(s):
    s=s.lower().translate(MAPPING)
    word=''
    for c in s:
        if unicodedata.category(c)[:1] in ('L','M','N'):word+=c
        elif word:
            yield word;word=''
    if word:yield word

def build(corpus,output):
    manifest_path=corpus/'manifest.json'
    if not manifest_path.is_file():raise SystemExit('Missing corpus manifest')
    # Extract only source records; catalogue metadata is never treated as source text.
    files=sorted(p for p in corpus.glob('*.json') if p.name!='manifest.json')
    files+=sorted((corpus/'sections').glob('*.json')) if (corpus/'sections').is_dir() else []
    postings=defaultdict(set);chapters_count=0;passage_count=0
    for file in files:
        payload=json.loads(file.read_text(encoding='utf-8'))
        bid=payload['book_id']
        for chapter in payload.get('chapters',[]):
            key='/'.join([bid,chapter['section_slug'],chapter['chapter_slug']])
            chapters_count+=1
            for passage in chapter.get('passages',[]):
                passage_count+=1
                for token in set(tokens((passage.get('text_iast') or '')+' '+(passage.get('text_devanagari') or ''))):
                    postings[(hashlib.sha256(token.encode()).hexdigest()[:2],token)].add(key)
    output.mkdir(parents=True,exist_ok=True)
    shards=defaultdict(dict)
    for (prefix,term),ids in postings.items():shards[prefix][term]=sorted(ids)
    for shard in range(256):
        key=f'{shard:02x}'
        path=output/(key+'.json')
        path.write_text(json.dumps(shards.get(key,{}),ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    # Publish meta LAST, so PHP never reads a half-built index as current.
    meta={'schema':1,'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
          'chapters':chapters_count,'passages':passage_count,'tokens':len(postings)}
    (output/'meta.json').write_text(json.dumps(meta,sort_keys=True)+'\n',encoding='utf-8')
    print('PASS: built',len(postings),'search terms across',chapters_count,'source chapters,',passage_count,'passages')
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--corpus',type=Path,default=Path('server/storage/corpus'))
    parser.add_argument('--output',type=Path,default=Path('server/storage/search-index'))
    a=parser.parse_args();build(a.corpus,a.output)
