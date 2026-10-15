export const MAX=100_000_000;
export function validateShop(id,name){if(!/^[-a-z0-9]{1,50}$/.test(id)||!name.trim()||name.length>100)throw Error('Completá el nombre y un identificador en minúsculas, sin espacios.');}
export function validateFile(file){if(!file||!file.name.toLowerCase().endsWith('.mp4')||file.size<=0||file.size>MAX)throw Error('Elegí un MP4 de hasta 100 MB.');}
export function manifest(id,name,file,sha256){return {id,name:name.trim(),version:crypto.randomUUID(),size:file.size,sha256,publishedAt:new Date().toISOString()};}
