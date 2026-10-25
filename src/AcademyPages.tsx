import {romanToDevanagari} from './reader-transliteration';
import {apiBase} from './site-paths';
import {useEffect,useMemo,useState} from 'react';
import {Link,useParams} from 'react-router-dom';
import {ArrowLeft,ArrowRight,Bookmark,BookmarkCheck,BookOpen,CheckCircle2,ChevronDown,ChevronRight,Clock3,ExternalLink,FileQuestion,GraduationCap,Library,Search,ShieldCheck,Timer,Upload,FileText} from 'lucide-react';
import {books,dailyQuestions} from './data';
import sectionsSeed from './content/sections.json';
import examSeed from './content/exam-catalog.json';

type Chapter={number:number;title:string|null;slug:string;status:string;entry_kind?:'text'|'index'|'bibliography'};
type Section={id:string;book_id:string;slug:string;name:string;devanagari:string;chapter_count:number;order:number;source_url:string;chapters:Chapter[]};
type PaperMeta={id:string;title:string;expected_count:number;status:string;available_count?:number;source_url:string};
type PaperQuestion={id:string;question:string;options:string[];subject?:string};
type Paper={id:string;title:string;expected_count:number;available_count:number;status:string;questions:PaperQuestion[]};
type Note={id:string;slug:string;title:string;subject:string;level:string;body:string;source_url?:string};
const sectionsInitial=sectionsSeed as Section[];
const examsInitial=examSeed as PaperMeta[];
function useData<T>(path:string,seed:T):T{const [value,setValue]=useState(seed);useEffect(()=>{let live=true;fetch(apiBase+''+path).then(r=>{if(!r.ok)throw Error('Unavailable');return r.json()}).then(j=>{if(live&&j.data!==undefined)setValue(j.data)}).catch(()=>{});return()=>{live=false}},[path]);return value}
function AcademyIntro({eyebrow,title,description}:{eyebrow:string;title:string;description:string}){return <section className="page-hero"><div className="container"><div className="eyebrow"><span className="eyebrow-line"/>{eyebrow}</div><h1>{title}</h1><p>{description}</p></div></section>}
export function BookSections({bookId}:{bookId:string}){const initial=sectionsInitial.filter(s=>s.book_id===bookId);const sections=useData<Section[]>('sections?book_id='+encodeURIComponent(bookId),initial);const [opened,setOpened]=useState<string|null>(sections[0]?.id||null);const [query,setQuery]=useState('');const rows=useMemo(()=>sections.map(s=>({...s,chapters:s.chapters.filter(c=>!query.trim()||`${c.number} ${c.title||''} ${s.name}`.toLowerCase().includes(query.toLowerCase()))})).filter(s=>s.chapters.length),[sections,query]);return <section className="academy-structure"><div className="section-head academy-structure-head"><div><div className="eyebrow"><span className="eyebrow-line"/> CHAPTER NAVIGATOR</div><h2>Explore the Sthānas.</h2><p>Browse available Sanskrit source editions and chapter indexes. Digital transcriptions are labelled separately from editorial translations.</p></div><span className="count-chip">{sections.reduce((n,s)=>n+s.chapter_count,0)} indexed entries</span></div><label className="academy-search"><Search size={18}/><input placeholder="Find a chapter number, title or Sthāna" value={query} onChange={e=>setQuery(e.target.value)} aria-label="Search chapter index"/></label><div className="academy-sections">{rows.map(s=><article key={s.id} className="academy-section"><button className="academy-section-title" onClick={()=>setOpened(opened===s.id?null:s.id)} aria-expanded={opened===s.id||!!query}><span className="academy-section-ordinal">{String(s.order).padStart(2,'0')}</span><span className="academy-section-name"><strong>{s.name} <span lang="sa">{s.devanagari}</span></strong><small>{s.chapter_count} chapters · reference index</small></span><ChevronDown className={opened===s.id||query?'turn':''} size={21}/></button>{(opened===s.id||!!query)&&<div className="academy-chapters">{s.chapters.map(c=><Link key={c.number} to={`/library/${bookId}/${s.slug}/${c.slug}`} className="academy-chapter"><span>{String(c.number).padStart(2,'0')}</span><div><strong>{c.title||`Chapter ${c.number}`}</strong><small>{c.status==='published'?`${(c as Chapter & {passage_count?:number}).passage_count??0} published passages`:c.status==='source-edition'?`${(c as Chapter & {passage_count?:number}).passage_count??0} Sanskrit source passages · unproofread`:c.entry_kind==='index'?'Appendix: subject index':c.entry_kind==='bibliography'?'Appendix: source references':c.status==='sample'?'Sample passage available':'Awaiting verified text import'}</small></div><ChevronRight size={16}/></Link>)}</div>}</article>)}{rows.length===0&&<p className="empty-inline">No indexed chapters match that search.</p>}</div><p className="academy-notice"><ShieldCheck size={17}/> Original Sanskrit passages from SARIT and Wikisource are attributed but not independently proofread. The two Madhava appendices remain reference-only.</p></section>}
type PublishedPassage={id:string;reference:string;text_devanagari:string;text_iast:string;translation_en:string;commentary:string;key_terms:{term:string;definition:string}[]};
type PublishedChapter={id:string;title:string;source_url:string;passages:PublishedPassage[];published_at:string};

export function ChapterPage({bookmarks,onToggle}:{bookmarks:string[];onToggle:(id:string)=>void}){
 const {id,section:sectionSlug,chapter:chapterSlug}=useParams();
 const book=books.find(b=>b.id===id);
 const sections=useData<Section[]>('sections?book_id='+encodeURIComponent(id||''),sectionsInitial.filter(s=>s.book_id===id));
 const section=sections.find(s=>s.book_id===id&&s.slug===sectionSlug);
 const chapter=section?.chapters.find(c=>c.slug===chapterSlug);
 const position=section?.chapters.findIndex(c=>c.slug===chapterSlug)??-1;
 const previous=position>0?section?.chapters[position-1]:null;
 const next=position>=0&&position+1<(section?.chapters.length||0)?section?.chapters[position+1]:null;
 const chapterKey='chapter:'+id+'/'+sectionSlug+'/'+chapterSlug;
 const [published,setPublished]=useState<PublishedChapter|null>(null);
 const [script,setScript]=useState<'deva'|'iast'>('deva');
 const [queryInput,setQueryInput]=useState('');
 const [query,setQuery]=useState('');
 const [showCommentary,setShowCommentary]=useState(false);
 const [expanded,setExpanded]=useState<string[]>([]);
 const [copyStatus,setCopyStatus]=useState<string|null>(null);
 useEffect(()=>{
  if(!id||!sectionSlug||!chapterSlug)return;
  let active=true;setPublished(null);setQuery('');setQueryInput('');setExpanded([]);setCopyStatus(null);setScript('deva');
  fetch(apiBase+'chapters/'+encodeURIComponent(id)+'/'+encodeURIComponent(sectionSlug)+'/'+encodeURIComponent(chapterSlug))
   .then(r=>r.ok?r.json():null).then(result=>{if(active&&result?.data)setPublished(result.data)}).catch(()=>{});
  return()=>{active=false};
 },[id,sectionSlug,chapterSlug]);
 const passages=published?.passages||[];
 const hasDeva=passages.some(p=>Boolean(p.text_devanagari?.trim()));
 const hasIast=passages.some(p=>Boolean(p.text_iast?.trim()));
 const canShowDeva=hasDeva||hasIast;
 const hasCommentary=passages.some(p=>Boolean(p.commentary?.trim()));
 const hasTranslations=passages.some(p=>Boolean(p.translation_en?.trim()));
 const hasTerms=passages.some(p=>(p.key_terms||[]).length>0);
 const filtered=useMemo(()=>{
  if(!query)return passages;
  const q=query.toLocaleLowerCase();
  return passages.filter(p=>[p.reference,p.text_iast,p.text_devanagari,p.translation_en,p.commentary,
   ...(p.key_terms||[]).flatMap(t=>[t.term,t.definition]),
   p.text_iast?romanToDevanagari(p.text_iast):''].some(x=>(x||'').toLocaleLowerCase().includes(q)));
 },[passages,query]);
 async function copyPassage(passage:PublishedPassage){
  const text=[passage.text_devanagari||passage.text_iast,passage.reference,published?.source_url].filter(Boolean).join('\n');
  try{await navigator.clipboard.writeText(text);setCopyStatus(passage.id)}
  catch{setCopyStatus(null)}
 }
 if(!book||!section||!chapter)return <section className="container section-short"><h1>Chapter not found</h1><Link to="/library">Browse the library</Link></section>;
 const sourceIsUnproofread=(published as PublishedChapter & {status?:string})?.status==='source-edition';
 const displayTitle=chapter.title||'Chapter '+chapter.number;
 const originalTitle=published?.title||displayTitle;
 const devaHeading=romanToDevanagari(displayTitle);
 return <section className="source-reader" aria-label="Classical Sanskrit reader">
  <div className="source-reader-inner">
   <nav className="source-breadcrumbs" aria-label="Breadcrumb">
    <Link to="/learn">Learn</Link><ChevronRight size={13}/><Link to="/library">Classical Texts</Link><ChevronRight size={13}/>
    <Link to={'/library/'+book.id}>{book.title}</Link><ChevronRight size={13}/><span>{section.name}</span>
   </nav>
   <header className="source-reader-heading">
    <p className="source-reader-overline">{book.title} / {section.name} · chapter {chapter.number}</p>
    <h1 lang={script==='deva'?'sa-Deva':'sa-Latn'}>{script==='deva'&&devaHeading!==displayTitle?chapter.number+'. '+devaHeading:chapter.number+'. '+displayTitle}</h1>
    <p className="source-reader-subtitle">{originalTitle} · Original Sanskrit source and editorial translations are kept distinct.</p>
   </header>
   <div className="source-language-tabs" role="group" aria-label="Text script">
    <button type="button" className={script==='deva'?'active':''} disabled={!canShowDeva}
     aria-pressed={script==='deva'} onClick={()=>setScript('deva')}>Devanagari{!hasDeva&&hasIast&&<span className="source-auto-symbol"> · auto</span>}</button>
    <button type="button" className={script==='iast'?'active':''} disabled={!hasIast}
     aria-pressed={script==='iast'} onClick={()=>setScript('iast')}>IAST (Roman)</button>
    {['Telugu','Tamil','Malayalam','Kannada','Gujarati','Bengali','Gurmukhi'].map(name=>
     <button type="button" key={name} disabled title={name+' transliteration is unavailable for this source edition'}>{name}</button>)}
   </div>
   <div className="source-reader-actions">
    <form className="source-search-form" role="search" onSubmit={e=>{e.preventDefault();setQuery(queryInput.trim())}}>
     <label htmlFor="source-chapter-search" className="visually-hidden">Search passage text, reference or commentary</label>
     <input id="source-chapter-search" value={queryInput} onChange={e=>{setQueryInput(e.target.value);if(!e.target.value.trim())setQuery('')}}
      placeholder="Search text, reference, or śloka..." />
     <button className="source-search-submit" type="submit"><Search size={16}/> Search</button>
     {query&&<button type="button" className="source-search-clear" onClick={()=>{setQuery('');setQueryInput('')}}>Clear</button>}
    </form>
    <div className="source-reader-action-right">
     <button type="button" onClick={()=>onToggle(chapterKey)} className="source-top-bookmark" aria-pressed={bookmarks.includes(chapterKey)}>
      {bookmarks.includes(chapterKey)?<BookmarkCheck size={16}/>:<Bookmark size={16}/>} {bookmarks.includes(chapterKey)?'Saved chapter':'Save chapter'}
     </button>
     {hasCommentary&&<button type="button" className="source-commentary-all" onClick={()=>setShowCommentary(x=>!x)}>
      {showCommentary?'Hide commentary':'Show commentary'}
     </button>}
    </div>
   </div>
   <nav className="source-reader-prevnext" aria-label="Chapter navigation">
    <span>{previous?<Link to={'/library/'+id+'/'+sectionSlug+'/'+previous.slug}><ArrowLeft size={16}/> Previous chapter</Link>:'First chapter'}</span>
    <Link className="source-index-link" to={'/library/'+id}>Browse Sthāna</Link>
    <span>{next?<Link to={'/library/'+id+'/'+sectionSlug+'/'+next.slug}>Next chapter <ArrowRight size={16}/></Link>:'Last chapter'}</span>
   </nav>
   {published&&passages.length>0?<>
    <div className="source-provenance">
     <div><span className="source-provenance-label">{sourceIsUnproofread?'DIGITAL SANSKRIT SOURCE · UNPROOFREAD':'EDITORIALLY PUBLISHED TEXT'}</span>
      <span>{passages.length} passages · {hasTranslations?'English meanings available':'No verified English meanings in this dataset'} · {hasTerms?'Glossary terms available':'Glossary pending'}</span></div>
     {published.source_url&&<a href={published.source_url} target="_blank" rel="noreferrer">View original source <ExternalLink size={14}/></a>}
    </div>
    <p className="source-reader-disclaimer">Original passage boundaries may not correspond to numbered ślokas. {script==='deva'&&!hasDeva?'Devanagari is automatically transliterated from the IAST source and is not independently proofread. ':''}This digital text is not medical advice. Translations, commentary, and glossary details appear only where sourced material is available.</p>
    {query&&<p className="source-match-count" role="status">{filtered.length} of {passages.length} passages match “{query}”.</p>}
    {filtered.length===0?<div className="source-reader-empty"><Search size={23}/><h2>No matching passages</h2><p>Try a Sanskrit word, reference, or a shorter phrase.</p><button onClick={()=>{setQuery('');setQueryInput('')}}>Show all passages</button></div>:
    <div className="source-shloka-list">
     {filtered.map((passage,index)=>{
      const passageKey='passage:'+id+'/'+sectionSlug+'/'+chapterSlug+'/'+passage.id;
      const text=script==='deva'
       ?(passage.text_devanagari||romanToDevanagari(passage.text_iast||''))
       :(passage.text_iast||passage.text_devanagari);
      const hasThisCommentary=Boolean(passage.commentary?.trim());
      const expandedHere=showCommentary||expanded.includes(passage.id);
      return <article key={passage.id||index} className="source-shloka-card" id={passage.id}>
       <div className="source-shloka-card-top">
        <span>{passage.reference?'PASSAGE · '+passage.reference:'PASSAGE · '+(index+1)}</span>
        <button type="button" aria-label={bookmarks.includes(passageKey)?'Remove saved passage':'Save passage'} aria-pressed={bookmarks.includes(passageKey)}
         title={bookmarks.includes(passageKey)?'Remove saved passage':'Save passage'}
         onClick={()=>onToggle(passageKey)}>{bookmarks.includes(passageKey)?<BookmarkCheck size={19}/>:<Bookmark size={19}/>}</button>
       </div>
       <p className={script==='deva'?'source-shloka-text source-shloka-devanagari':'source-shloka-text source-shloka-iast'}
        lang={script==='deva'?'sa-Deva':'sa-Latn'}>{text}</p>
       {passage.translation_en&&<div className="source-shloka-panel"><span>MEANING OF THE ŚLOKA</span><p>{passage.translation_en}</p></div>}
       <div className="source-shloka-utilities">
        <button type="button" onClick={()=>copyPassage(passage)}><BookOpen size={15}/>{copyStatus===passage.id?'Copied source passage':'Copy passage'}</button>
        {hasThisCommentary&&<button type="button" aria-expanded={expandedHere} onClick={()=>{
         if(showCommentary){setShowCommentary(false);setExpanded(list=>list.includes(passage.id)?list.filter(v=>v!==passage.id):[...list,passage.id]);}
         else setExpanded(list=>list.includes(passage.id)?list.filter(v=>v!==passage.id):[...list,passage.id]);
        }}>{expandedHere?'▾ Hide commentary':'▸ Show commentary'}</button>}
       </div>
       {hasThisCommentary&&expandedHere&&<div className="source-shloka-commentary"><span>CLASSICAL COMMENTARY</span><p>{passage.commentary}</p></div>}
       {(passage.key_terms||[]).length>0&&<div className="source-shloka-panel source-terms-panel"><span>KEY TERMS</span><div className="source-terms-grid">{passage.key_terms.map((term,i)=><div key={i}><strong>{term.term}</strong><p>{term.definition}</p></div>)}</div></div>}
      </article>;
     })}
    </div>}
   </>:<div className="source-reader-empty"><BookOpen size={28}/><h2>Source transcription not yet available</h2>
    <p>This chapter is indexed, but no approved source passages are available here yet.</p>
    {section.source_url&&<a href={section.source_url} target="_blank" rel="noreferrer">Consult the reference edition <ExternalLink size={14}/></a>}
   </div>}
  </div>
 </section>;
}

export function McqCatalogPage(){const exams=useData<PaperMeta[]>('exams',examsInitial);const [filter,setFilter]=useState<'All'|'AIAPGET'|'Other PG'>('All');const list=exams.filter(e=>filter==='All'||(filter==='AIAPGET'?e.id.startsWith('aiapget'):!e.id.startsWith('aiapget')));return <><AcademyIntro eyebrow="EXAM PREPARATION / MCQ CENTRE" title="Practice with purpose." description="Browse AIAPGET and postgraduate examination papers, follow a focused question flow, and review explanations. Papers become available after verified question imports."/><section className="container section-short"><div className="exam-summary-strip"><div><GraduationCap size={24}/><strong>16</strong><span>Exam sets indexed</span></div><div><FileQuestion size={24}/><strong>2017–2025</strong><span>AIAPGET catalogue</span></div><div><ShieldCheck size={24}/><strong>Source first</strong><span>No fabricated past papers</span></div></div><div className="academy-toolbar"><div className="pill-switch" role="group" aria-label="Filter exam papers">{(['All','AIAPGET','Other PG'] as const).map(k=><button key={k} className={filter===k?'active':''} onClick={()=>setFilter(k)}>{k}</button>)}</div><Link to="/mcq/demo" className="btn btn-dark">Try the sample exam <ArrowRight size={17}/></Link></div><div className="exam-card-grid">{list.map(ex=><Link key={ex.id} to={`/mcq/${ex.id}`} className="exam-set-card"><div className="exam-card-header"><span className="tag">{ex.id.startsWith('aiapget')?'AIAPGET':'PG PRACTICE'}</span><span className={ex.status==='published'?'ready-dot':'pending-dot'}>{ex.status==='published'?'READY':'IMPORT PENDING'}</span></div><div className="exam-symbol"><FileQuestion size={26}/></div><h3>{ex.title}</h3><p>{ex.status==='published'?`${ex.available_count??ex.expected_count} verified questions available`:`${ex.expected_count} questions listed at source · awaiting import`}</p><span className="exam-card-link">{ex.status==='published'?'Start exam':'View paper status'} <ArrowRight size={16}/></span></Link>)}</div><p className="academy-notice">The year-wise counts reflect Ayana's public catalogue. No 2017–2025 examination questions have been transferred into this build yet.</p></section></>}
export function ExamPage(){const {id}=useParams();const isDemo=id==='demo';const fromSeed=examsInitial.find(x=>x.id===id);const [paper,setPaper]=useState<Paper|null>(null);const [pos,setPos]=useState(0);const [answers,setAnswers]=useState<Record<string,number>>({});const [marked,setMarked]=useState<string[]>([]);const [finished,setFinished]=useState(false);const [review,setReview]=useState<{id:string;answer:number;explanation:string}[]>([]);const [elapsed,setElapsed]=useState(0);const [error,setError]=useState('');
 const progressKey='ayursutra.exam.progress.v1.'+(id||'');
 useEffect(()=>{
   setPos(0);setAnswers({});setMarked([]);setElapsed(0);setFinished(false);setReview([]);
   if(!id)return;
   try {
     const state=JSON.parse(localStorage.getItem('ayursutra.exam.progress.v1.'+id)||'null');
     if(!state || state.version!==1)return;
     if(Number.isInteger(state.pos)&&state.pos>=0&&state.pos<=250)setPos(state.pos);
     if(Number.isInteger(state.elapsed)&&state.elapsed>=0&&state.elapsed<=86400)setElapsed(state.elapsed);
     if(state.answers&&typeof state.answers==='object'&&!Array.isArray(state.answers)){
       setAnswers(Object.fromEntries(Object.entries(state.answers).filter(([,v])=>Number.isInteger(v)&&Number(v)>=0&&Number(v)<4)) as Record<string,number>);
     }
     if(Array.isArray(state.marked))setMarked(state.marked.filter((x:unknown)=>typeof x==='string').slice(0,250));
   } catch { /* Discard malformed local draft. */ }
 },[id]);
 useEffect(()=>{
   if(!id||finished)return;
   try{localStorage.setItem(progressKey,JSON.stringify({version:1,answers,marked,pos,elapsed,updatedAt:new Date().toISOString()}));}catch{/* Unavailable or full browser storage; keep the session usable. */}
 },[id,answers,marked,pos,elapsed,finished,progressKey]);
 function resetAttempt(){setAnswers({});setMarked([]);setPos(0);setElapsed(0);setFinished(false);setReview([]);localStorage.removeItem(progressKey)}
 const demo:Paper={id:'demo',title:'AyurSutra Demo Practice',expected_count:dailyQuestions.length,available_count:dailyQuestions.length,status:'published',questions:dailyQuestions.map(q=>({id:q.id,question:q.question,options:q.options,subject:'Classical Ayurveda'}))};const chosen=isDemo?demo:paper;useEffect(()=>{if(isDemo||!id)return;let ok=true;fetch(apiBase+'exams/'+id).then(r=>r.ok?r.json():Promise.reject(new Error('Paper unavailable'))).then(x=>{if(ok)setPaper(x.data)}).catch(e=>{if(ok)setError(String(e.message))});return()=>{ok=false}},[id,isDemo]);useEffect(()=>{if(!chosen?.questions.length||finished)return;const timer=window.setInterval(()=>setElapsed(t=>t+1),1000);return()=>window.clearInterval(timer)},[chosen?.id,chosen?.questions.length,finished]);if(!isDemo&&!fromSeed)return <div className="container section-short">Unknown paper. <Link to="/mcq">Browse exams</Link></div>;async function submit(){if(!chosen)return;try{
 let resolved:{id:string;answer:number;explanation:string}[];
 if(isDemo){resolved=dailyQuestions.map(q=>({id:q.id,answer:q.answer,explanation:q.explanation}))}
 else{const res=await fetch(apiBase+'exams/'+chosen.id+'/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({answers})});if(!res.ok)throw new Error('Could not score this paper');const j=await res.json();resolved=j.data.review}
 setReview(resolved);setFinished(true);localStorage.removeItem(progressKey);
 const score=resolved.reduce((n,r)=>n+(answers[r.id]===r.answer?1:0),0);
 const result={id:chosen.id,at:new Date().toISOString(),answered:Object.keys(answers).length,score,total:chosen.questions.length,elapsed};
 localStorage.setItem('ayursutra.exam.last',JSON.stringify(result));
 try{const previous=JSON.parse(localStorage.getItem('ayursutra.exam.history.v1')||'[]');localStorage.setItem('ayursutra.exam.history.v1',JSON.stringify([result,...(Array.isArray(previous)?previous:[])].slice(0,20)))}catch{/* Local history is optional. */}
 }catch(e){setError((e as Error).message)}}const questions=chosen?.questions||[];const q=questions[pos];const currentAnswer=q?answers[q.id]:undefined;const answered=Object.keys(answers).length;const score=review.reduce((sum,r)=>sum+(answers[r.id]===r.answer?1:0),0);return <><AcademyIntro eyebrow="MCQ / PRACTICE ROOM" title={chosen?.title||fromSeed?.title||'Loading paper'} description="Choose answers, flag questions for review and submit when ready. Your current attempt is stored in this browser only."/><section className="container section-short">{error&&<p className="exam-error" role="alert">{error}</p>}{!questions.length?<div className="import-pending-card"><Upload size={34}/><h2>Paper is awaiting verified import</h2><p>{fromSeed?.title} is listed in Ayana's catalogue with {fromSeed?.expected_count} questions. Its question text, options, answer key and explanations have not been imported into this version yet.</p><div className="pending-actions"><Link to="/mcq/demo" className="btn btn-dark">Try sample questions <ArrowRight size={16}/></Link><Link to="/mcq" className="btn btn-light">All exam sets</Link></div><p className="academy-notice">An editor can import and publish this paper from the admin dashboard using an authorized JSON export.</p></div>:finished?<div className="exam-results"><CheckCircle2 size={42}/><span className="tag">PRACTICE COMPLETE</span><h2>{score} / {questions.length}</h2><p>Correct answers · {answered} attempted · {questions.length-answered} unanswered</p><div className="review-list">{questions.map((x,i)=>{const r=review.find(item=>item.id===x.id);return <div className="review-row" key={x.id}><span>{i+1}.</span><div><strong>{x.question}</strong><p>Your answer: {answers[x.id]===undefined?'Not answered':x.options[answers[x.id]]}</p><p>Correct answer: {r?x.options[r.answer]:'Awaiting review'}</p>{r?.explanation&&<small>{r.explanation}</small>}</div></div>})}</div><Link className="btn btn-dark" to="/mcq">Back to exam catalogue <ArrowRight size={16}/></Link></div>:<div className="exam-room"><div className="exam-main"><div className="exam-question-top"><span>QUESTION {pos+1} OF {questions.length}</span><span><Timer size={16}/> {Math.floor(elapsed/60).toString().padStart(2,'0')}:{(elapsed%60).toString().padStart(2,'0')}</span></div><div className="exam-progress"><span style={{width:`${answered/questions.length*100}%`}}/></div><span className="tag">{q.subject||'General'}</span><h2>{q.question}</h2><div className="exam-options">{q.options.map((option,i)=><button key={i} className={currentAnswer===i?'selected':''} onClick={()=>setAnswers(prev=>({...prev,[q.id]:i}))}><span>{String.fromCharCode(65+i)}</span>{option}</button>)}</div><div className="exam-nav"><button className="btn btn-light" disabled={pos===0} onClick={()=>setPos(x=>x-1)}><ArrowLeft size={16}/> Previous</button><button className="bookmark-action" onClick={()=>setMarked(prev=>prev.includes(q.id)?prev.filter(x=>x!==q.id):[...prev,q.id])}><Bookmark size={17} fill={marked.includes(q.id)?'currentColor':'none'}/> {marked.includes(q.id)?'Marked':'Mark for review'}</button>{pos===questions.length-1?<button className="btn btn-dark" onClick={submit}>Submit exam <ArrowRight size={16}/></button>:<button className="btn btn-dark" onClick={()=>setPos(x=>x+1)}>Next <ArrowRight size={16}/></button>}</div></div><aside className="exam-navigation"><h3>Question palette</h3><p>{answered} answered · {marked.length} flagged</p><div className="exam-number-grid">{questions.map((x,i)=><button key={x.id} title={`Question ${i+1}`} className={`${answers[x.id]!==undefined?'answered':''} ${marked.includes(x.id)?'marked':''} ${i===pos?'current':''}`} onClick={()=>setPos(i)}>{i+1}</button>)}</div><button className="btn btn-dark" onClick={submit}>Finish & review answers</button><small>Progress autosaves in this browser; final results are kept for your last 20 attempts.</small><button type="button" className="btn btn-light" onClick={resetAttempt}>Reset attempt</button></aside></div>}</section></>}
export function NotesPage(){const notes=useData<Note[]>('notes',[]);const [query,setQuery]=useState('');const match=notes.filter(n=>`${n.title} ${n.subject} ${n.level}`.toLowerCase().includes(query.toLowerCase()));return <><AcademyIntro eyebrow="BAMS / MD / MS STUDY HUB" title="Study notes, thoughtfully organised." description="Browse verified subject notes and connect important concepts with their classical sources. More material will appear after editorial import."/><section className="container section-short"><div className="academy-notes-top"><div className="notes-category"><BookOpen size={28}/><div><span className="tag">3RD PROFESSIONAL</span><h3>Shalya Tantra — General Surgery</h3><p>Ayana currently lists three notes in this subject. Their content is not yet present in this repository.</p></div></div><label className="academy-search"><Search size={18}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search available notes" aria-label="Search study notes"/></label></div>{match.length?<div className="notes-grid">{match.map(n=><Link className="note-card" key={n.id} to={`/notes/${n.slug}`}><span className="tag">{n.level} · {n.subject}</span><h3>{n.title}</h3><span className="text-link">Read note <ArrowRight size={16}/></span></Link>)}</div>:<div className="import-pending-card"><FileText size={35}/><h2>Verified notes are awaiting import</h2><p>This module is ready for subject and programme-specific notes; no article content has been copied into it yet. An editor can create and publish notes from the private dashboard.</p><a className="text-link" href="https://ayanaayurveda.com/learn/notes/" target="_blank" rel="noreferrer">View reference catalogue <ExternalLink size={15}/></a></div>}</section></>}
export function NoteDetailPage(){const {slug}=useParams();const [note,setNote]=useState<Note|null>(null);useEffect(()=>{if(!slug)return;fetch(apiBase+'notes/'+slug).then(r=>r.ok?r.json():Promise.reject()).then(j=>setNote(j.data)).catch(()=>setNote(null))},[slug]);return <><AcademyIntro eyebrow="STUDY NOTE" title={note?.title||'Note unavailable'} description={note?`${note.level} · ${note.subject}`:'This note has not been published.'}/><section className="container section-short academy-note-reader"><Link className="text-link" to="/notes"><ArrowLeft size={17}/> All notes</Link>{note&&<article><div className="tag">EDITORIALLY REVIEWED NOTE</div><h2>{note.title}</h2>{note.body.split('\n').filter(x=>x.trim()).map((para,i)=><p key={i}>{para}</p>)}{note.source_url&&<a target="_blank" rel="noreferrer" href={note.source_url} className="text-link">Source reference <ExternalLink size={16}/></a>}</article>}</section></>}
export function VivaPage(){const cards=[{q:'Which text begins with Dīrghañjīvitīya?',a:'The Caraka Saṃhitā, Sūtrasthāna.'},{q:'Which classical work is closely associated with Shalya Tantra?',a:'The Suśruta Saṃhitā.'},{q:'What is the opening section of the Caraka Saṃhitā?',a:'Sūtrasthāna.'}];return <><AcademyIntro eyebrow="ORAL EXAM PREPARATION" title="Viva practice." description="Review foundational questions, reveal concise model answers and return to the original references."/><section className="container section-short"><div className="academy-notice">Starter practice cards only. Ayana's full viva bank has not been imported.</div><div className="viva-grid">{cards.map((c,i)=><VivaCard key={i} q={c.q} a={c.a} index={i+1}/>)}</div></section></>}
function VivaCard({q,a,index}:{q:string;a:string;index:number}){const [open,setOpen]=useState(false);return <article className="viva-card"><span className="tag">VIVA {String(index).padStart(2,'0')}</span><h3>{q}</h3><button onClick={()=>setOpen(x=>!x)} aria-expanded={open}>{open?'Hide answer':'Reveal answer'} <ChevronDown size={17}/></button>{open&&<p>{a}</p>}</article>}
