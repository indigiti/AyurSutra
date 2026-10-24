import json,pathlib
root=pathlib.Path('/mnt/data/AyurSutra')
# Counts are publicly observable Ayana Academy catalogue counts, not evidence of imported text.
sections = {
 'sushruta-samhita':[('sutrasthanam','Sūtrasthānam','सूत्रस्थानम्',46),('nidanasthanam','Nidānasthānam','निदानस्थानम्',16),('sharirasthanam','Śārīrasthānam','शारीरस्थानम्',10),('cikitsasthanam','Cikitsāsthānam','चिकित्सास्थानम्',40),('kalpasthanam','Kalpasthānam','कल्पस्थानम्',8),('uttaratantram','Uttaratantram','उत्तरतन्त्रम्',66)],
 'charaka-samhita':[('sutrasthanam','Sūtrasthānam','सूत्रस्थानम्',30),('nidanasthanam','Nidānasthānam','निदानस्थानम्',8),('vimanasthanam','Vimānasthānam','विमानस्थानम्',8),('sharirasthanam','Śārīrasthānam','शारीरस्थानम्',8),('indriyasthanam','Indriyasthānam','इन्द्रियस्थानम्',12),('cikitsasthanam','Cikitsāsthānam','चिकित्सास्थानम्',36),('kalpasthanam','Kalpasthānam','कल्पस्थानम्',12),('siddhisthanam','Siddhisthānam','सिद्धिस्थानम्',12)],
 'ashtanga-hridaya':[('sutrasthanam','Sūtrasthānam','सूत्रस्थानम्',30),('sharirasthanam','Śārīrasthānam','शारीरस्थानम्',6),('nidanasthanam','Nidānasthānam','निदानस्थानम्',16),('cikitsasthanam','Cikitsāsthānam','चिकित्सास्थानम्',22),('kalpasiddhisthanam','Kalpasiddhisthānam','कल्पसिद्धिस्थानम्',6),('uttarasthanam','Uttarasthānam','उत्तरस्थानम्',40)],
 'ashtanga-sangraha':[('sutrasthanam','Sūtrasthānam','सूत्रस्थानम्',40),('sharirasthanam','Śārīrasthānam','शारीरस्थानम्',12),('nidanasthanam','Nidānasthānam','निदानस्थानम्',16),('cikitsasthanam','Cikitsāsthānam','चिकित्सास्थानम्',24),('kalpasthanam','Kalpasthānam','कल्पस्थानम्',8),('uttarasthanam','Uttarasthānam','उत्तरस्थानम्',50)],
 'madhava-nidana':[('madhavanidana','Mādhavanidāna','माधवनिदान',70)]
}
rows=[]
for book, sec in sections.items():
 for idx,(sid,name,dev,count) in enumerate(sec,1):
  chapters=[{'number':n,'title':None,'slug':f'chapter-{n:02d}','status':'awaiting-import'} for n in range(1,count+1)]
  if book=='charaka-samhita' and sid=='sutrasthanam':chapters[0].update(title='Dīrghañjīvitīya',slug='dirghanjivitiya',status='sample')
  if book=='sushruta-samhita' and sid=='sutrasthanam':chapters[0].update(title='Vedotpatti',slug='vedotpattyadhyayah',status='sample')
  rows.append({'id':f'{book}:{sid}','book_id':book,'slug':sid,'name':name,'devanagari':dev,'chapter_count':count,'chapter_index_status':'reference-only','order':idx,'chapters':chapters,'source_url':f'https://ayanaayurveda.com/learn/classical-texts/{"ashtanga-hrudayam" if book=="ashtanga-hridaya" else book}/'})
assert len(rows)==27 and sum(r['chapter_count'] for r in rows)==652
if not (root/'server/storage/sections.json').exists():
 (root/'server/storage/sections.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
(root/'public/content').mkdir(parents=True,exist_ok=True)
(root/'public/content/sections.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n')
exam_specs=[(f'aiapget-{y}',f'AIAPGET {y}',100 if y<2020 else 120) for y in range(2017,2026)]+[
 ('delhi-pg-2003','Delhi PG 2003',100),('delhi-pg-2005','Delhi PG 2005',100),('delhi-pg-2008','Delhi PG 2008',150),('delhi-pg-2011','Delhi PG 2011',100),('jamnagar-pg','Jamnagar PG',100),('lucknow-pg','Lucknow PG',100),('md-ayu-2001','MD Ayu 2001',120)]
exams=[{'id':eid,'title':title,'expected_count':count,'status':'awaiting-import','questions':[],'source_url':f'https://ayanaayurveda.com/learn/mcq/{eid}/','source':'Ayana Ayurveda exam catalogue'} for eid,title,count in exam_specs]
if not (root/'server/storage/exams.json').exists():
 (root/'server/storage/exams.json').write_text(json.dumps(exams,ensure_ascii=False,indent=2)+'\n')
(root/'public/content/exam-catalog.json').write_text(json.dumps([{k:v for k,v in ex.items() if k!='questions'} for ex in exams],indent=2)+'\n')
if not (root/'server/storage/notes.json').exists():
 (root/'server/storage/notes.json').write_text('[]\n')
print('Generated',len(rows),'sections',sum(r['chapter_count'] for r in rows),'chapter indexes',len(exams),'exam slots; actual question corpus not imported')
