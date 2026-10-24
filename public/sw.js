const CACHE='ayursutra-shell-v1';
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(['/','/manifest.webmanifest','/icon.svg'])));self.skipWaiting()});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE&&key.startsWith('ayursutra-')).map(key=>caches.delete(key)))));self.clients.claim()});
self.addEventListener('fetch',event=>{
 const req=event.request;const url=new URL(req.url);
 if(req.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/')||url.pathname.startsWith('/admin')||url.pathname.startsWith('/my-library'))return;
 if(req.mode==='navigate')event.respondWith(fetch(req).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(req,copy))}return response}).catch(async()=>await caches.match(req)||await caches.match('/')));
 else if(/\.(?:js|css|svg|png|woff2?)$/.test(url.pathname))event.respondWith(caches.match(req).then(hit=>hit||fetch(req).then(resp=>{if(resp.ok){const copy=resp.clone();caches.open(CACHE).then(cache=>cache.put(req,copy))}return resp})));
});
