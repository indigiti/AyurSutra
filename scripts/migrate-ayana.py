#!/usr/bin/env python3
"""Offline, repeatable Ayana content migration from an owner's JSON export.

Dry-run is the default; --apply stages approved *records* as unpublished drafts.
No website scraping, fake past papers, or externally reachable admin key is needed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.parse import urlparse
import fcntl

ROOT=Path(__file__).resolve().parents[1]
COLLECTIONS=('sections','chapters','exams','notes')

def text(value, max_length=250000):
    if not isinstance(value,str) or not value.strip() or len(value)>max_length:
        raise ValueError('expected nonempty text (max %s characters)'%max_length)
    return value.strip()

def slug(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',value):
        raise ValueError('invalid slug: '+repr(value))
    return value

def https_url(value, optional=False):
    if optional and not value:return ''
    value=text(value,2000)
    url=urlparse(value)
    if url.scheme!='https' or not url.hostname or url.username or url.password:
        raise ValueError('source URL must be HTTPS')
    return value

def read_collection(storage,name):
    path=storage/(name+'.json')
    data=json.loads(path.read_text('utf-8')) if path.exists() else []
    if not isinstance(data,list):raise ValueError('invalid collection: '+name)
    return data

def make_slug(value):
    return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',value.lower())).strip('-')

def normalize(source, sections, exams):
    if not isinstance(source,dict) or source.get('format')!='ayursutra-ay-1':
        raise ValueError('Expected format: ayursutra-ay-1')
    for key in ('chapters','papers','notes'):
        if not isinstance(source.get(key,[]),list):raise ValueError(f'{key} must be an array')
    allowed_sections={(s['book_id'],s['slug']):s for s in sections}
    allowed_papers={e['id']:e for e in exams}
    chapters=[];papers=[];notes=[];errors=[]
    for number,raw in enumerate(source.get('chapters',[]),1):
        try:
            if not isinstance(raw,dict):raise ValueError('expected object')
            book=slug(raw.get('book_id'));sth=slug(raw.get('section_slug'));chapter_slug=slug(raw.get('chapter_slug'))
            section=allowed_sections.get((book,sth))
            if not section:raise ValueError('unknown book/Sthana')
            entry=next((c for c in section['chapters'] if c['slug']==chapter_slug),None)
            if not entry:raise ValueError('unknown chapter; use the indexed slug')
            source_url=https_url(raw.get('source_url'))
            if not isinstance(raw.get('passages'),list) or not raw['passages']:raise ValueError('passages must be a nonempty array')
            if len(raw['passages'])>3000:raise ValueError('too many passages in chapter')
            passages=[]
            for i,p in enumerate(raw['passages']):
                if not isinstance(p,dict):raise ValueError('passage must be an object')
                ref=text(p.get('reference'),100)
                deva=p.get('text_devanagari','');iast=p.get('text_iast','')
                if not deva and not iast:raise ValueError('passage needs Sanskrit original or IAST text')
                if deva:deva=text(deva,40000)
                if iast:iast=text(iast,40000)
                commentary=p.get('commentary','')
                if commentary:commentary=text(commentary,120000)
                translation=p.get('translation_en','')
                if translation:translation=text(translation,15000)
                terms=p.get('key_terms',[])
                if not isinstance(terms,list) or len(terms)>50:raise ValueError('key_terms must be <= 50 entries')
                terms_clean=[]
                for term in terms:
                    if not isinstance(term,dict):raise ValueError('key term must be an object')
                    terms_clean.append({'term':text(term.get('term'),200),'definition':text(term.get('definition'),2000)})
                passages.append({'id':hashlib.sha256((book+'/'+sth+'/'+chapter_slug+'/'+str(i)+'/'+ref).encode()).hexdigest()[:20],
                    'reference':ref,'text_devanagari':deva,'text_iast':iast,'translation_en':translation,
                    'commentary':commentary,'key_terms':terms_clean})
            canonical=book+'/'+sth+'/'+chapter_slug
            chapters.append({'id':canonical,'book_id':book,'section_slug':sth,'chapter_slug':chapter_slug,
                'title':text(raw.get('title') or entry.get('title') or 'Chapter '+str(entry['number']),240),
                'chapter_number':entry['number'],'source_url':source_url,'passages':passages,
                'source_hash':hashlib.sha256(json.dumps(passages,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                'status':'draft'})
        except (ValueError,TypeError,KeyError) as e:errors.append(f'chapters[{number}]: {e}')
    for number,raw in enumerate(source.get('papers',[]),1):
        try:
            if not isinstance(raw,dict):raise ValueError('expected object')
            paper_id=slug(raw.get('id'));index=allowed_papers.get(paper_id)
            if not index:raise ValueError('paper not indexed')
            qs=raw.get('questions')
            if not isinstance(qs,list) or len(qs)!=index['expected_count']:
                raise ValueError(f'expected {index["expected_count"]} complete questions')
            normalized=[];seen=set()
            for i,q in enumerate(qs):
                if not isinstance(q,dict):raise ValueError(f'question {i+1} not an object')
                key=slug(q.get('id') or f'{paper_id}-{i+1}')
                if key in seen:raise ValueError('duplicate question ID: '+key)
                seen.add(key)
                options=q.get('options')
                if not isinstance(options,list) or len(options)!=4:raise ValueError(f'question {i+1} needs four options')
                answer=q.get('answer')
                if type(answer)!=int or answer not in (0,1,2,3):raise ValueError(f'question {i+1} has invalid answer')
                normalized.append({'id':key,'question':text(q.get('question'),4000),
                    'options':[text(o,2000) for o in options],'answer':answer,
                    'explanation':text(q.get('explanation'),8000),
                    'subject':text(q.get('subject') or 'General',80)})
            papers.append({'id':paper_id,'questions':normalized,'status':'draft',
                'source_hash':hashlib.sha256(json.dumps(normalized,ensure_ascii=False,sort_keys=True).encode()).hexdigest()})
        except (ValueError,TypeError,KeyError) as e:errors.append(f'papers[{number}]: {e}')
    for number,raw in enumerate(source.get('notes',[]),1):
        try:
            if not isinstance(raw,dict):raise ValueError('expected object')
            title=text(raw.get('title'),240);note_slug=slug(raw.get('slug') or make_slug(title))
            level=text(raw.get('level'),12)
            if level not in ('BAMS','MD','MS'):raise ValueError('invalid level')
            source_url=https_url(raw.get('source_url'),optional=True)
            note={'id':hashlib.sha256(('ayana:'+note_slug).encode()).hexdigest()[:20],'slug':note_slug,'title':title,
                 'subject':text(raw.get('subject'),120),'level':level,'body':text(raw.get('body'),250000),
                 'source_url':source_url,'status':'draft','source_hash':hashlib.sha256(raw['body'].encode()).hexdigest()}
            notes.append(note)
        except (ValueError,TypeError,KeyError) as e:errors.append(f'notes[{number}]: {e}')
    for label,items in [('chapter',chapters),('paper',papers),('note',notes)]:
        seen=set()
        for item in items:
            if item['id'] in seen:errors.append('duplicate '+label+': '+item['id'])
            seen.add(item['id'])
    return {'chapters':chapters,'papers':papers,'notes':notes},errors

def merge(data, storage):
    counts={}
    existing={key:read_collection(storage,key) for key in ('chapters','exams','notes')}
    for key in ('chapters','papers','notes'):
        target='exams' if key=='papers' else key
        items=existing[target]
        id_to_pos={v['id']:i for i,v in enumerate(items)}
        counts[key]={'new':0,'updated_draft':0,'unchanged':0,'preserved_published':0}
        for incoming in data[key]:
            old=items[id_to_pos[incoming['id']]] if incoming['id'] in id_to_pos else None
            if old and old.get('status')=='published':
                counts[key]['preserved_published']+=1;continue
            fresh={**old,**incoming} if old else incoming
            if key=='papers':
                fresh['published_count']=0;fresh['imported_count']=len(incoming['questions'])
            if old:
                if all(old.get(k)==v for k,v in fresh.items()):counts[key]['unchanged']+=1
                else:counts[key]['updated_draft']+=1
                items[id_to_pos[incoming['id']]]=fresh
            else:
                counts[key]['new']+=1;id_to_pos[incoming['id']]=len(items);items.append(fresh)
    return existing,counts

def save_all(storage,collections):
    storage.mkdir(parents=True,exist_ok=True)
    lock=storage/'.migration.lock'
    with lock.open('a+') as file_lock:
        fcntl.flock(file_lock,fcntl.LOCK_EX)
        backups={}
        try:
            # Store recoverable copies before updating any collection.
            timestamp=time.strftime('%Y%m%d-%H%M%S',time.gmtime())
            backup_dir=storage/'backups'/('ayana-'+timestamp+'-'+str(os.getpid()))
            backup_dir.mkdir(parents=True,exist_ok=False)
            for kind in ('chapters','exams','notes'):
                old=storage/(kind+'.json')
                backups[kind]=old.read_bytes() if old.exists() else None
                if old.exists():(backup_dir/(kind+'.json')).write_bytes(backups[kind])
            for kind in ('chapters','exams','notes'):
                fd,temp=tempfile.mkstemp(prefix='.ayana-',suffix='.tmp',dir=storage)
                try:
                    with os.fdopen(fd,'w',encoding='utf-8') as stream:
                        json.dump(collections[kind],stream,ensure_ascii=False,indent=2)
                        stream.write('\n');stream.flush();os.fsync(stream.fileno())
                    os.chmod(temp,0o640);os.replace(temp,storage/(kind+'.json'))
                finally:
                    if os.path.exists(temp):os.unlink(temp)
            return str(backup_dir)
        except BaseException:
            for kind,contents in backups.items():
                path=storage/(kind+'.json')
                if contents is None:path.unlink(missing_ok=True)
                else:path.write_bytes(contents)
            raise
        finally:fcntl.flock(file_lock,fcntl.LOCK_UN)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('export',type=Path,help='Owner-provided Ayana JSON export')
    ap.add_argument('--apply',action='store_true',help='Write validated records as draft JSON collections')
    ap.add_argument('--storage',type=Path,default=ROOT/'server/storage',help='Storage directory')
    ap.add_argument('--report',type=Path,help='Write machine-readable migration report')
    a=ap.parse_args()
    try:
        source=json.loads(a.export.read_text('utf-8'))
        data,errors=normalize(source,read_collection(a.storage,'sections'),read_collection(a.storage,'exams'))
        if errors:
            report={'ok':False,'mode':'validation','errors':errors,'imported':False}
        else:
            merged,counts=merge(data,a.storage)
            report={'ok':True,'mode':'apply' if a.apply else 'dry-run','counts':counts,'imported':a.apply,
                    'records':{key:len(data[key]) for key in data},'backup_path':save_all(a.storage,merged) if a.apply else None}
    except (ValueError,OSError,json.JSONDecodeError) as err:
        report={'ok':False,'mode':'validation','errors':[str(err)],'imported':False}
    rendered=json.dumps(report,indent=2,ensure_ascii=False)
    print(rendered)
    if a.report:a.report.write_text(rendered+'\n',encoding='utf-8')
    return 0 if report['ok'] else 1
if __name__=='__main__':sys.exit(main())
