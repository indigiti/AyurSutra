import {FormEvent,useEffect,useState} from 'react';
import {Link,useSearchParams} from 'react-router-dom';
import {ArrowRight,BookOpen,FileQuestion,FileText,Search,ShieldCheck} from 'lucide-react';

type Result={type:string;status:string;title:string;description:string;path:string};
type Payload={data:Result[];query:string;total:number;limit:number};
const filters=[{id:'all',label:'All results'},{id:'texts',label:'Sanskrit & texts'},{id:'notes',label:'Study notes'},{id:'exams',label:'Exam papers'}] as const;
export default function SearchPage(){
 const [params,setParams]=useSearchParams();
 const current=params.get('q')||'';
 const type=filters.some(f=>f.id===params.get('type'))?params.get('type')||'all':'all';
 const [input,setInput]=useState(current);
 const [data,setData]=useState<Payload|null>(null);
 const [state,setState]=useState<'initial'|'loading'|'ready'|'error'>('initial');
 useEffect(()=>setInput(current),[current]);
 useEffect(()=>{
  if(current.trim().length<2){setData(null);setState('initial');return;}
  const controller=new AbortController();setState('loading');setData(null);
  fetch(`/api/v1/search?q=${encodeURIComponent(current.trim())}&type=${encodeURIComponent(type)}&limit=40`,{signal:controller.signal})
   .then(r=>{if(!r.ok)throw Error('Search API is unavailable');return r.json()})
   .then((response:Payload)=>{if(!controller.signal.aborted){setData(response);setState('ready')}})
   .catch(()=>{if(!controller.signal.aborted)setState('error')});
  return()=>controller.abort();
 },[current,type]);
 function submit(event:FormEvent){event.preventDefault();if(input.trim().length>=2)setParams({q:input.trim(),type})}
 function changeType(next:string){setParams(current?{q:current,type:next}:{type:next})}
 return <>
  <section className="page-hero"><div className="container"><div className="eyebrow"><span className="eyebrow-line"/> AYURSUTRA DISCOVERY</div><h1>Search the living library.</h1><p>Find Sanskrit passages, source-referenced chapters, published study notes and verified practice papers.</p></div></section>
  <section className="container section-short academy-search-page">
   <form className="academy-discovery-form" onSubmit={submit}><Search size={21}/><input value={input} onChange={e=>setInput(e.target.value)} placeholder="Try Charaka, अथातो, Shalya, or 1.1" aria-label="Search AyurSutra" minLength={2}/><button className="btn btn-dark" type="submit">Search <ArrowRight size={16}/></button></form>
   <div className="pill-switch academy-search-filters" aria-label="Result type">{filters.map(f=><button key={f.id} className={type===f.id?'active':''} onClick={()=>changeType(f.id)}>{f.label}</button>)}</div>
   {state==='loading'&&<p role="status" className="academy-discovery-state">Searching published resources…</p>}
   {state==='error'&&<div role="alert" className="academy-discovery-state"><strong>Search is temporarily unavailable.</strong><p>The PHP API must be online for complete-library search. You can still <Link to="/library">browse the classical catalogue</Link>.</p></div>}
   {state==='initial'&&<div className="academy-discovery-state"><BookOpen size={31}/><h2>One search across your studies.</h2><p>Search published original verses, English explanations, editorial notes and complete question-paper titles. Unpublished content is never listed.</p></div>}
   {state==='ready'&&<><p className="academy-discovery-count" role="status">{data?.total||0} verified or labelled catalogue matches for “{current}”{(data?.total||0)>(data?.data.length||0)?' · showing first 40':''}</p><div className="academy-search-results">{data?.data.map((r,i)=><Link key={`${r.path}-${i}`} to={r.path} className="academy-search-result"><span className="academy-result-icon">{r.type==='exam'?<FileQuestion size={20}/>:r.type==='note'?<FileText size={20}/>:<BookOpen size={20}/>}</span><span className="academy-result-detail"><span className="tag">{r.type.toUpperCase()} · {r.status.toUpperCase()}</span><strong>{r.title}</strong><small>{r.description}</small></span><ArrowRight size={17}/></Link>)}</div>{!data?.total&&<div className="academy-discovery-state"><Search size={25}/><h2>No published results yet</h2><p>Try another spelling, Sanskrit term, chapter reference or browse the book catalogue. Some chapters remain awaiting editorial import.</p><Link to="/library" className="text-link">Browse texts <ArrowRight size={16}/></Link></div>}</>}
   <p className="academy-notice"><ShieldCheck size={17}/> A catalogue entry is not a completed text. Results marked “sample” are starter passages; only published chapter imports appear as full chapter results.</p>
  </section>
 </>;
}
