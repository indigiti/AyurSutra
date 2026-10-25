// Scoped to the application folder; cannot cache other applications on this Cloudways host.
const BASE=new URL('./',self.location.href).pathname;
const CACHE='ayursutra-shell-v2-'+BASE.replace(/\W/g,'-');
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll([BASE,BASE+'manifest.webmanifest',BASE+'icon.svg'])));
  self.skipWaiting();
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('ayursutra-shell-')&&key!==CACHE).map(key=>caches.delete(key)))));
  self.clients.claim();
});
self.addEventListener('fetch',event=>{
  const req=event.request,url=new URL(req.url);
  if(req.method!=='GET'||url.origin!==self.location.origin||!url.pathname.startsWith(BASE))return;
  const sub=url.pathname.slice(BASE.length);
  if(sub.startsWith('api/')||sub.startsWith('admin')||sub.startsWith('my-library'))return;
  if(req.mode==='navigate')event.respondWith(
    fetch(req).then(response=>{
      if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(req,copy))}
      return response;
    }).catch(async()=>await caches.match(req)||await caches.match(BASE))
  );
  else if(/\.(?:js|css|svg|png|woff2?)$/.test(sub))event.respondWith(
    caches.match(req).then(hit=>hit||fetch(req).then(resp=>{
      if(resp.ok){const copy=resp.clone();caches.open(CACHE).then(cache=>cache.put(req,copy))}
      return resp;
    }))
  );
});
