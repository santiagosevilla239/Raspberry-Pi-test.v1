import {test} from 'node:test';
import assert from 'node:assert/strict';
import {validateShop,validateFile,manifest} from '../src/model.js';
import worker from '../cloudflare/worker.mjs';
test('Valida archivos reales dentro del límite y rechaza vacíos/excesos',()=>{
 validateFile({name:'publicidad.mp4',size:80_000_000});
 for(const file of [{name:'a.mp4',size:0},{name:'a.mp4',size:100_000_001},{name:'a.txt',size:10}])assert.throws(()=>validateFile(file));
 validateShop('open-sport','Open Sport');assert.throws(()=>validateShop('../otro','Otro'));
 const m=manifest('open','Open',{size:80},'a'.repeat(64));assert.equal(m.id,'open');assert.ok(m.version);
});
test('CORS restringido y autorización independiente del origen',async()=>{
 const env={ADMIN_ORIGINS:'https://panel.vercel.app',ADMIN_TOKEN:'admin',PLAYER_TOKEN:'player'};
 const call=(origin,method='OPTIONS',token='')=>worker.fetch(new Request('https://api.test/api/shops',{method,headers:{Origin:origin,Authorization:'Bearer '+token}}),env);
 assert.equal((await call('https://otro.test')).status,403);
 const r=await call('https://panel.vercel.app');assert.equal(r.status,204);assert.equal(r.headers.get('Access-Control-Allow-Origin'),'https://panel.vercel.app');
 const denied=await call('https://panel.vercel.app','GET','incorrecto');assert.equal(denied.status,401);assert.equal(denied.headers.get('Access-Control-Allow-Origin'),'https://panel.vercel.app');
});
test('Publicación online simulada conserva la anterior ante carga incompleta',async()=>{
 const store=new Map();
 const env={ADMIN_TOKEN:'admin',PLAYER_TOKEN:'player',VIDEOS:{
 async put(k,body,meta={}){const data=Buffer.from(await new Response(body).arrayBuffer());store.set(k,{data,...meta});},
 async get(k){const o=store.get(k);return o?{body:o.data,size:o.data.length,customMetadata:o.customMetadata,json:async()=>JSON.parse(o.data)}:null;},
 async head(k){return this.get(k);},async delete(k){store.delete(k);},async list({prefix}){return {objects:[...store.keys()].filter(k=>k.startsWith(prefix)).map(key=>({key}))};}}};
 const call=(route,method='GET',body,headers={})=>worker.fetch(new Request('https://api.test/api/'+route,{method,body,headers:{Authorization:'Bearer admin',...headers}}),env);
 const a=await (await call('open/upload','PUT','video1',{'Content-Type':'video/mp4','Content-Length':'6','X-SHA256':'a'.repeat(64)})).json();
 assert.equal((await call('open/publish','POST',JSON.stringify(a))).status,200);
 const failed=await call('open/upload','PUT','cut',{'Content-Type':'video/mp4','Content-Length':'100','X-SHA256':'b'.repeat(64)});assert.equal(failed.status,400);
 assert.equal((await (await call('open/manifest')).json()).version,a.version);
 assert.equal(await (await call('open/video')).text(),'video1');
});
