// Builds actual, crawlable page HTML using the same React tree as the client.
import {build} from 'esbuild';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
import fs from 'node:fs/promises';
import path from 'node:path';
const root=process.cwd();
const entry=path.join(root,'dist','ayursutra-server-entry.cjs');
await build({
  entryPoints:[path.join(root,'src/entry-server.tsx')],
  outfile:entry,platform:'node',format:'cjs',target:'node22',
  bundle:true,external:['react','react-dom','react-dom/server'],
});
try {
 const {render}=require(entry);
 const dist=path.join(root,'dist');
 const template=await fs.readFile(path.join(dist,'index.html'),'utf8');
 const books=[['charaka-samhita','Charaka Samhita'],['sushruta-samhita','Sushruta Samhita'],['ashtanga-hridaya','Ashtanga Hridaya'],['ashtanga-sangraha','Ashtanga Sangraha'],['madhava-nidana','Madhava Nidana']];
 const routes=[['/','The Living Library of Ayurveda','Explore original Sanskrit, classical texts and daily Ayurveda learning.'],['/library','Classical Ayurveda Library','Explore five foundational Ayurveda texts.'],['/search','Search AyurSutra','Search published Sanskrit verses, classical chapters, Ayurveda notes and exam papers.'],['/learn','Daily Ayurveda Learning','Practice classical Ayurveda concepts with daily MCQs.'],['/mcq','AIAPGET Question Papers & MCQ Practice','Year-wise AIAPGET practice and verified question sets.'],['/mcq/demo','Sample Ayurveda MCQ Practice','Explore an interactive sample MCQ test with explanations.'],['/notes','Ayurveda Study Notes','Browse BAMS MS and MD Ayurveda learning notes by subject.'],['/viva','Ayurveda Viva Preparation','Review sample oral examination questions and explanations.'],['/research','Ayurveda Research & Insights','Source-aware reference guides and verified editorial research.'],['/membership','AyurSutra Membership','Discover free classical reading and planned advanced learning tools.'],...books.map(([id,name])=>['/library/'+id,name+' | Classical Text','Explore the Sanskrit source and verified passages of '+name+'.']),...Array.from({length:9},(_,i)=>['/mcq/aiapget-'+(2017+i),'AIAPGET '+(2017+i)+' Practice Paper','Verified Ayurveda postgraduate question papers are made available after editorial import.'])];
 const domain=(process.env.SITE_URL||'').replace(/\/$/,'');
 for(const [route,title,description] of routes){
   const page=render(route);
   const safe=(value)=>String(value).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
   const meta=`<title>${safe(title)} — AyurSutra</title><meta name="description" content="${safe(description)}"/>${domain?`<link rel="canonical" href="${domain+route}"/>`:''}<meta property="og:title" content="${safe(title)} — AyurSutra"/><meta property="og:description" content="${safe(description)}"/><meta property="og:type" content="website"/>`;
   let html=template.replace(/<title>[^<]*<\/title>/,'').replace(/<meta name="description"[^>]*>/,'').replace('</head>',`${meta}</head>`).replace('<div id="root"></div>',`<div id="root">${page}</div>`);
   const target=route==='/'?path.join(dist,'index.html'):path.join(dist,route.slice(1),'index.html');
   await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target,html);
 }
 if(domain){const sitemap='<?xml version="1.0" encoding="utf-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+routes.map(([r])=>`<url><loc>${domain}${r}</loc></url>`).join('')+'</urlset>';await fs.writeFile(path.join(dist,'sitemap.xml'),sitemap)}
 console.log(`Prerendered ${routes.length} public routes`);
} finally {await fs.rm(entry,{force:true})}
