function open(){return new Promise((ok,no)=>{const r=indexedDB.open('totem-panel-demo-v1',1);r.onupgradeneeded=()=>r.result.createObjectStore('shops',{keyPath:'id'});r.onsuccess=()=>ok(r.result);r.onerror=()=>no(Error('El navegador no permite guardar la demo.'));});}
async function tx(mode,fn){const db=await open();try{return await new Promise((ok,no)=>{const t=db.transaction('shops',mode),r=fn(t.objectStore('shops'));let result;r.onsuccess=()=>result=r.result;t.oncomplete=()=>ok(result);t.onabort=t.onerror=()=>no(Error('No se pudo guardar. Revisá el espacio disponible del navegador.'));});}finally{db.close();}}
export const list=()=>tx('readonly',s=>s.getAll());
export const publish=(m,file)=>tx('readwrite',s=>s.put({...m,blob:file}));
