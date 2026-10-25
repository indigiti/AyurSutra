import {apiBase} from './site-paths';
import {useEffect,useState} from 'react';
import {CheckCircle2,FileQuestion,FileText,Upload} from 'lucide-react';
type Exam={id:string;title:string;expected_count:number;imported_count:number;status:string};
type Note={id:string;title:string;subject:string;status:string;source_url?:string};
type ChapterDraft={id:string;title:string;book_id:string;section_slug:string;chapter_slug:string;status:string;source_url:string};
type ImportStats={chapters:{draft:number;published:number;total:number};exams:{draft:number;published:number;indexed:number};notes:{draft:number;published:number;total:number}};
export default function AcademyAdminTools({token,role}:{token:string;role:'viewer'|'editor'|'publisher'|'admin'}){
 const canPublish=role==='publisher'||role==='admin';
 const [exams,setExams]=useState<Exam[]>([]);const [notes,setNotes]=useState<Note[]>([]);
 const [chapterDrafts,setChapterDrafts]=useState<ChapterDraft[]>([]);const [importStats,setImportStats]=useState<ImportStats|null>(null);const [chapterFile,setChapterFile]=useState<File|null>(null);
 const [batchFile,setBatchFile]=useState<File|null>(null);const [batchBusy,setBatchBusy]=useState(false);
 const [examId,setExamId]=useState('aiapget-2017');const [paperFile,setPaperFile]=useState<File|null>(null);const [feedback,setFeedback]=useState('');
 const [title,setTitle]=useState('');const [subject,setSubject]=useState('Shalya Tantra');const [level,setLevel]=useState('BAMS');const [body,setBody]=useState('');const [source,setSource]=useState('');
 const [reviewer,setReviewer]=useState('');const [edition,setEdition]=useState('');const [reviewNotes,setReviewNotes]=useState('');
 const [textChecked,setTextChecked]=useState(false);const [rightsConfirmed,setRightsConfirmed]=useState(false);
 async function request(path:string,method='GET',payload?:unknown){const r=await fetch(apiBase+'admin/'+path,{method,headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},body:payload===undefined?undefined:JSON.stringify(payload)});const j=await r.json();if(!r.ok)throw new Error(j.error||'Request failed');return j}
 async function reload(){try{const [a,b,c,d]=await Promise.all([request('exams'),request('notes'),request('chapters'),request('import-status')]);setExams(a.data);setNotes(b.data);setChapterDrafts(c.data);setImportStats(d.data)}catch(e){setFeedback((e as Error).message)}}
 useEffect(()=>{void reload()},[token]);
 async function importChapter(){if(!chapterFile){setFeedback('Select an authorized chapter JSON file.');return}try{if(chapterFile.size>1400000)throw new Error('Use the bulk migration importer for chapters larger than 1.4 MB.');const data=JSON.parse(await chapterFile.text());const result=await request('chapters/import','POST',data);setFeedback(`Staged ${result.passage_count} original passages in ${result.id}. Publish after source review.`);await reload()}catch(e){setFeedback((e as Error).message)}}

 async function stageAuthorizedManifest(){
  if(!batchFile){setFeedback('Select an authorized ayursutra-ay-1 JSON manifest.');return}
  if(batchFile.size>20_000_000){setFeedback('Manifest exceeds the 20 MB browser import limit.');return}
  setBatchBusy(true);
  let done=0;
  try{
   const data:unknown=JSON.parse(await batchFile.text());
   if(!data || typeof data!=='object'||Array.isArray(data))throw new Error('Expected a JSON manifest object');
   const manifest=data as {format?:string;chapters?:unknown;papers?:unknown;notes?:unknown};
   if(manifest.format!=='ayursutra-ay-1')throw new Error('Expected format ayursutra-ay-1');
   const chapters=manifest.chapters??[];const papers=manifest.papers??[];const notesList=manifest.notes??[];
   if(!Array.isArray(chapters)||!Array.isArray(papers)||!Array.isArray(notesList)||
      chapters.length>700||papers.length>20||notesList.length>1500)
     throw new Error('Invalid or oversized manifest collections');
   for(const ch of chapters){
     if(!ch||typeof ch!=='object'||!Array.isArray(ch.passages)||!ch.passages.length||ch.passages.length>300||
        !/^https:\/\//.test(String(ch.source_url||''))||
        ![ch.book_id,ch.section_slug,ch.chapter_slug].every(s=>typeof s==='string'&&/^[a-z0-9-]+$/.test(s)))
       throw new Error('Every chapter requires valid canonical IDs, HTTPS provenance and 1–300 passages');
   }
   for(const paper of papers){
     const ex=exams.find(x=>x.id===paper?.id);
     if(!ex||!Array.isArray(paper.questions)||paper.questions.length!==ex.expected_count)
       throw new Error('Unknown or incomplete examination paper. No batch changes were made');
   }
   for(const note of notesList){
     if(!note||typeof note.title!=='string'||typeof note.subject!=='string'||
        typeof note.body!=='string'||!note.body.trim()||
        !['BAMS','MD','MS'].includes(note.level))
       throw new Error('Each study note requires title, subject, body and an approved programme');
   }
   const total=chapters.length+papers.length+notesList.length;
   if(!total)throw new Error('No importable records in manifest');
   setFeedback('Validated '+total+' source records. Beginning draft-only import; no publication will occur.');
   for(const ch of chapters){
     await request('chapters/import','POST',ch);done++;
     setFeedback('Staged '+done+'/'+total+' drafts. No content published.');
   }
   for(const paper of papers){
     await request('exams/'+encodeURIComponent(paper.id)+'/import','POST',{questions:paper.questions});done++;
     setFeedback('Staged '+done+'/'+total+' drafts. No content published.');
   }
   const existingNotes=new Set(notes.map(x=>x.title+'|'+(x.source_url||'')));
   for(const note of notesList){
     const identity=note.title+'|'+(note.source_url||'');
     if(!existingNotes.has(identity)){
       await request('notes','POST',{title:note.title,subject:note.subject,level:note.level,
         body:note.body,source_url:note.source_url||''});
       existingNotes.add(identity);
     }
     done++;setFeedback('Processed '+done+'/'+total+' drafts. No content published.');
   }
   setFeedback('Completed '+done+'/'+total+' authorized draft records. Review each before publication.');
   await reload();
  }catch(e){
   setFeedback('Batch stopped after '+done+' records. Partial drafts may exist. '+(e as Error).message);
   await reload();
  }finally{setBatchBusy(false)}
 }

 async function publishChapter(id:string){try{await request('chapters/publish','POST',{id,review:{reviewer,edition,notes:reviewNotes,text_checked:textChecked,rights_confirmed:rightsConfirmed}});setFeedback('Chapter published with an editorial review attestation.');await reload()}catch(e){setFeedback((e as Error).message)}}
 async function importPaper(){if(!paperFile){setFeedback('Select your authorized paper JSON export first.');return}try{const raw=JSON.parse(await paperFile.text());const questions=Array.isArray(raw)?raw:raw.questions;if(!Array.isArray(questions))throw new Error('Expected an array or {"questions":[...]}');const result=await request(`exams/${examId}/import`,'POST',{questions});setFeedback(`${result.imported_count} questions staged for review. They are not public yet.`);await reload()}catch(e){setFeedback((e as Error).message)}}
 async function publishExam(id:string){try{await request(`exams/${id}/publish`,'POST',{});setFeedback('Complete exam published.');await reload()}catch(e){setFeedback((e as Error).message)}}
 async function saveNote(){try{const result=await request('notes','POST',{title,subject,level,body,source_url:source});setFeedback(`Study note saved as draft: ${result.data.title}.`);setTitle('');setBody('');await reload()}catch(e){setFeedback((e as Error).message)}}
 async function publishNote(id:string){try{await request(`notes/${id}/publish`,'POST',{});setFeedback('Study note published.');await reload()}catch(e){setFeedback((e as Error).message)}}
 return <div className="academy-admin-tools"><h2>Learning content imports</h2><p className="academy-admin-help">Role: {role}. Only publisher/admin accounts may publish content. Import only material that Ayana authorizes. Exam answer keys remain private until a learner submits a completed practice attempt. Imports are drafts until published.</p><section><div className="admin-tool-head"><Upload size={19}/><strong>Bulk owner-authorized content staging</strong></div>
 <p className="academy-admin-help">Upload a format <code>ayursutra-ay-1</code> manifest containing original chapters, complete papers and/or licensed notes. All records are validated before upload, submitted sequentially and kept as unpublished drafts. The batch is not transactional; errors can leave some drafts staged. Verify imports before retrying. Maximum 20 MB and 700 chapters per batch.</p>
 <label>Authorized manifest JSON<input type="file" accept=".json,application/json" onChange={e=>setBatchFile(e.target.files?.[0]||null)} disabled={batchBusy}/></label>
 <button type="button" className="btn btn-light" onClick={stageAuthorizedManifest} disabled={batchBusy}>{batchBusy?'Staging drafts…':'Validate and stage entire manifest'}</button>
 </section>
 <section><div className="admin-tool-head"><FileText size={19}/><strong>Ayana content migration</strong></div>
 <p className="academy-admin-help">Import an authorized chapter export containing the exact indexed book, Sthāna, chapter slugs, source URL and Sanskrit passages. All imports remain drafts until reviewed and explicitly published. A bulk CLI importer is provided for complete Ayana data exports.</p>
 {importStats&&<div className="migration-stats"><span>Chapters: {importStats.chapters.published} published / {importStats.chapters.total} imported</span><span>Exams: {importStats.exams.published} / {importStats.exams.indexed} published</span><span>Notes: {importStats.notes.published} / {importStats.notes.total} published</span></div>}
 <label>Chapter JSON file<input type="file" accept=".json,application/json" onChange={e=>setChapterFile(e.target.files?.[0]||null)}/></label>
 <button className="btn btn-light" onClick={importChapter}><Upload size={16}/> Import chapter as draft</button>
 <p className="academy-admin-help">Required JSON fields: <code>book_id</code>, <code>section_slug</code>, <code>chapter_slug</code>, <code>source_url</code>, <code>passages</code> array. Each passage requires <code>reference</code> and original text. See <code>docs/AYANA-MIGRATION.md</code> for the format.</p>
 <div className="admin-review-fields"><h3>Editorial verification before publication</h3>
 <p className="academy-admin-help">Record your identity and the exact source edition. The checkboxes document the checks performed; they do not substitute for independent scholarly verification.</p>
 <label>Reviewer name<input value={reviewer} maxLength={120} onChange={e=>setReviewer(e.target.value)} required/></label>
 <label>Source edition / bibliographic reference<input value={edition} maxLength={240} onChange={e=>setEdition(e.target.value)} required/></label>
 <label>Review notes<textarea rows={3} maxLength={2000} value={reviewNotes} onChange={e=>setReviewNotes(e.target.value)}/></label>
 <label><input type="checkbox" checked={textChecked} onChange={e=>setTextChecked(e.target.checked)}/> I checked the source text, references and chapter ordering</label>
 <label><input type="checkbox" checked={rightsConfirmed} onChange={e=>setRightsConfirmed(e.target.checked)}/> I verified publication and reuse rights for this edition</label>
 </div>
 <div className="admin-publish-list">{chapterDrafts.map(c=><div key={c.id}><span>{c.title} · {c.id} · {c.status}</span>{c.status==='draft'&&canPublish&&<button onClick={()=>publishChapter(c.id)}><CheckCircle2 size={14}/> Publish reviewed chapter</button>}</div>)}</div>
 </section>
 <section><div className="admin-tool-head"><FileQuestion size={19}/><strong>Question-paper import</strong></div><label>Exam paper<select value={examId} onChange={e=>setExamId(e.target.value)}>{exams.map(e=><option key={e.id} value={e.id}>{e.title} — {e.imported_count||0}/{e.expected_count}</option>)}</select></label><label>Question JSON file<input type="file" accept="application/json,.json" onChange={e=>setPaperFile(e.target.files?.[0]||null)}/></label><button className="btn btn-light" onClick={importPaper}><Upload size={16}/> Import to draft</button><p className="academy-admin-help">Fields: <code>id</code>, <code>question</code>, <code>options</code> (four strings), <code>answer</code> (0–3), <code>explanation</code>, optional <code>subject</code>. Paper size must match the indexed count.</p><div className="admin-publish-list">{exams.filter(e=>e.status==='draft'||e.status==='published').map(e=><div key={e.id}><span>{e.title}: {e.imported_count}/{e.expected_count} · {e.status}</span>{e.status==='draft'&&canPublish&&<button onClick={()=>publishExam(e.id)}><CheckCircle2 size={14}/> Publish reviewed paper</button>}</div>)}</div></section><section><div className="admin-tool-head"><FileText size={19}/><strong>Study-note editor</strong></div><label>Title<input value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Programme<select value={level} onChange={e=>setLevel(e.target.value)}><option>BAMS</option><option>MD</option><option>MS</option></select></label><label>Subject<input value={subject} onChange={e=>setSubject(e.target.value)}/></label><label>Reference URL (optional)<input type="url" value={source} onChange={e=>setSource(e.target.value)}/></label><label>Note body<textarea rows={8} value={body} onChange={e=>setBody(e.target.value)} placeholder="Paste the authorized, reviewed study note"/></label><button className="btn btn-light" onClick={saveNote}>Save note as draft</button><div className="admin-publish-list">{notes.map(n=><div key={n.id}><span>{n.title} · {n.status}</span>{n.status==='draft'&&canPublish&&<button onClick={()=>publishNote(n.id)}><CheckCircle2 size={14}/> Publish reviewed note</button>}</div>)}</div></section>{feedback&&<p className="admin-status" role="status">{feedback}</p>}</div>
}
