const MAX=100_000_000;
const json=(v,status=200)=>Response.json(v,{status,headers:{'Cache-Control':'no-store'}});
export const backend = {async fetch(req,env){
 const u=new URL(req.url),parts=u.pathname.split('/').filter(Boolean);
 if(parts[0]!=='api')return new Response('API del totem lista');
 const token=req.headers.get('Authorization')?.replace(/^Bearer /,'');
 const admin=!!env.ADMIN_TOKEN&&token===env.ADMIN_TOKEN;
 const player=!!env.PLAYER_TOKEN&&token===env.PLAYER_TOKEN;
 if(!admin&&!player)return json({error:'Acceso no autorizado'},401);
 try{
 if(u.pathname==='/api/shops'&&req.method==='GET'&&admin){
 const list=await env.VIDEOS.list({prefix:'manifests/'});
 return json(await Promise.all(list.objects.map(async o=>(await env.VIDEOS.get(o.key)).json())));
 }
 const id=parts[1];if(!id||!/^[-a-z0-9]{1,50}$/.test(id))return json({error:'Identificador inválido'},400);
 const key=`manifests/${id}.json`;
 if(parts[2]==='manifest'&&req.method==='GET'){
 const o=await env.VIDEOS.get(key);return o?json(await o.json()):json({error:'Comercio sin video publicado'},404);
 }
 if(parts[2]==='upload'&&req.method==='PUT'&&admin){
 const size=Number(req.headers.get('Content-Length'));
 const hash=req.headers.get('X-SHA256'),name=req.headers.get('X-Shop-Name')||id;
 if(!Number.isInteger(size)||size<=0||size>MAX||req.headers.get('Content-Type')!=='video/mp4'||!/^[a-f0-9]{64}$/.test(hash||''))return json({error:'MP4 inválido o supera 100 MB'},400);
 const version=crypto.randomUUID(),videoKey=`videos/${id}/${version}.mp4`;
 await env.VIDEOS.put(videoKey,req.body,{httpMetadata:{contentType:'video/mp4'},customMetadata:{sha256:hash}});
 const o=await env.VIDEOS.head(videoKey);
 if(o.size!==size){await env.VIDEOS.delete(videoKey);return json({error:'Carga incompleta'},400);}
 return json({id,name:decodeURIComponent(name),version,videoKey,size,sha256:hash});
 }
 if(parts[2]==='publish'&&req.method==='POST'&&admin){
 const m=await req.json();
 if(m.id!==id||!m.version||m.videoKey!==`videos/${id}/${m.version}.mp4`)return json({error:'Versión inválida'},400);
 const o=await env.VIDEOS.head(m.videoKey);
 if(!o||o.size!==m.size||o.customMetadata.sha256!==m.sha256)return json({error:'El archivo no está completo'},400);
 const old=await env.VIDEOS.get(key),prev=old?await old.json():null;
 const next={id,name:String(m.name).slice(0,100),version:m.version,videoKey:m.videoKey,size:m.size,sha256:m.sha256,publishedAt:new Date().toISOString(),previous:prev?.videoKey||null};
 await env.VIDEOS.put(key,JSON.stringify(next),{httpMetadata:{contentType:'application/json'}});
 // Retain current and previous; cleanup is explicit to avoid racing readers.
 return json(next);
 }
 if(parts[2]==='video'&&req.method==='GET'){
 const mObj=await env.VIDEOS.get(key);if(!mObj)return json({error:'Sin video'},404);
 const m=await mObj.json(),version=u.searchParams.get('version');
 const videoKey=version?`videos/${id}/${version}.mp4`:m.videoKey;
 if(videoKey!==m.videoKey&&videoKey!==m.previous)return json({error:'Versión no disponible'},404);
 const o=await env.VIDEOS.get(videoKey);if(!o)return json({error:'Sin archivo'},404);
 return new Response(o.body,{headers:{'Content-Type':'video/mp4','Content-Length':String(o.size),'Cache-Control':'no-store'}});
 }
 return json({error:'Ruta no disponible'},404);
 }catch(e){return json({error:'No se pudo completar la operación'},500);}
}};

// Vercel aloja el panel; el MP4 viaja directamente desde el navegador a este Worker.
export default {async fetch(req, env) {
 const origin = req.headers.get('Origin');
 const allowed = (env.ADMIN_ORIGINS || '').split(',').map(s=>s.trim()).filter(Boolean);
 if (origin && !allowed.includes(origin)) return new Response('Origen no permitido', {status:403});
 const cors = origin ? {'Access-Control-Allow-Origin':origin,'Vary':'Origin','Access-Control-Allow-Methods':'GET,PUT,POST,OPTIONS','Access-Control-Allow-Headers':'Authorization,Content-Type,X-SHA256,X-Shop-Name','Access-Control-Max-Age':'600'} : {};
 if (req.method === 'OPTIONS') return new Response(null,{status:204,headers:cors});
 const response = await backend.fetch(req,env);
 const headers = new Headers(response.headers);
 for (const [key,value] of Object.entries(cors)) headers.set(key,value);
 return new Response(response.body,{status:response.status,headers});
}};
