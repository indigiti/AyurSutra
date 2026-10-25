#!/usr/bin/env python3
"""Stage, but DO NOT publish, diagnostic chapters from an approved Wikisource wikitext export.

Fetches only from Sanskrit Wikisource or accepts operator-provided plain MediaWiki wikitext.
A mandatory editor must inspect chapter splits, transcription, references and CC BY-SA rights
before passing the resulting draft manifest to migrate-ayana.py.
"""
import argparse,hashlib,json,re,sys,urllib.parse,urllib.request
from pathlib import Path
SOURCE="https://sa.wikisource.org/wiki/माधवनिदानम्"
API="https://sa.wikisource.org/w/api.php"
START=re.compile(r'(?m)^={2,6}\s*(.*?)\s*={2,6}\s*$')
def fetch():
    params=urllib.parse.urlencode({'action':'parse','page':'माधवनिदानम्',
        'prop':'wikitext|revid','format':'json','formatversion':'2'})
    req=urllib.request.Request(API+'?'+params,headers={'User-Agent':'AyurSutra-Scholarly-Importer/1.0 (source attribution; staging only)'})
    with urllib.request.urlopen(req,timeout=30) as response:body=response.read(2_000_000)
    result=json.loads(body)
    if 'error' in result:raise ValueError(str(result['error']))
    page=result.get('parse') or {}
    body=page.get('wikitext')
    if isinstance(body,dict):body=body.get('*')
    if not isinstance(body,str):raise ValueError('Unexpected MediaWiki wikitext response')
    return body,page.get('revid')
def stage(text,revision,output):
    titles=[];matches=list(START.finditer(text))
    for i,heading in enumerate(matches):
        title=heading.group(1).strip()
        body=text[heading.end():matches[i+1].start() if i+1<len(matches) else len(text)]
        titles.append((title,body))
    if len(titles)!=70:raise ValueError(f'Expected 68 text headings and two appendix headings; found {len(titles)}')
    if 'विषयानुक्रमणिका' not in titles[-2][0] or 'स्रोत' not in titles[-1][0]:
        raise ValueError('Unexpected appendix boundaries. Manual reconciliation required.')
    chapters=[]
    for idx,(title,raw) in enumerate(titles[:68],start=1):
        if not title or len(title)>240:raise ValueError('Invalid chapter title')
        # Raw line groups preserve source ordering; they are NOT verified śloka or paragraph boundaries.
        lines=[line.strip() for line in raw.splitlines() if line.strip() and not line.strip().startswith(('{{','}}','<!--','[[Category:'))]
        if len(lines)<3:raise ValueError(f'Chapter {idx} has insufficient source text')
        if any(re.search(r'<script|<iframe',line,re.I) for line in lines):raise ValueError('Unsafe markup')
        passages=[{'reference':f'source-line-{n:04d}','text_devanagari':line,
           'text_iast':'','translation_en':'','commentary':'','key_terms':[]}
          for n,line in enumerate(lines,1)]
        chapters.append({'book_id':'madhava-nidana','section_slug':'madhavanidana',
         'chapter_slug':f'chapter-{idx:02d}','title':title,
         'source_url':SOURCE+(f'?oldid={revision}' if revision else ''),
         'passages':passages})
    data={'format':'ayursutra-ay-1','chapters':chapters[1:],'papers':[],'notes':[]}
    output=output.expanduser().absolute()
    if 'public_html' in output.parts:raise ValueError('Never write unreviewed extracts inside public_html')
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as file:json.dump(data,file,ensure_ascii=False,indent=2)
    return {'staged_draft_chapters':len(data['chapters']),
      'existing_chapter_kept_for_reconciliation':1,'appendices_not_published':2,
      'revision':revision,'source_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(),
      'passages':sum(len(x['passages']) for x in data['chapters']),
      'review_required':True}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    input_arg=parser.add_mutually_exclusive_group(required=True)
    input_arg.add_argument('--input',type=Path,help='Authorized wikitext export')
    input_arg.add_argument('--fetch',action='store_true',help='Read original source from Sanskrit Wikisource API')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--revision',type=int)
    args=parser.parse_args()
    try:
        text,revision=fetch() if args.fetch else (args.input.read_text(encoding='utf-8'),args.revision)
        print(json.dumps(stage(text,revision,args.output),ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,urllib.error.URLError) as error:
        print(f'ERROR: {error}',file=sys.stderr);raise SystemExit(1)
