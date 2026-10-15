"""Local disk player and daily synchronizer. Python standard library only."""
import hashlib,json,os,re,threading,time,urllib.request,urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data';DATA.mkdir(exist_ok=True)
LOCK=threading.Lock()
def config():return json.loads((ROOT/'config.json').read_text())
def state():
 try:return json.loads((DATA/'state.json').read_text())
 except FileNotFoundError:return {}
def atomic_json(path,obj):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj));os.replace(tmp,path)
def sync():
 if not LOCK.acquire(False):return {'message':'Ya hay una descarga en curso'}
 try:
  c=config();base=c['server'].rstrip('/');id=c['shop_id'];token=c['player_token']
  if not base.startswith('https://') and not base.startswith(('http://127.0.0.1:','http://localhost:')):raise ValueError('Usá HTTPS salvo en pruebas locales')
  def request(url):return urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':'Bearer '+token}),timeout=120)
  with request(base+'/api/'+urllib.parse.quote(id,safe='')+'/manifest') as r:m=json.load(r)
  if not isinstance(m.get('sha256'),str) or not re.fullmatch(r'[a-f0-9]{64}',m['sha256']):raise ValueError('Hash inválido')
  old=state()
  if m['version']==old.get('version') or m['version']==old.get('pending',{}).get('version'):return {'message':'Sin cambios'}
  if not 0<m['size']<=100000000:raise ValueError('Tamaño inválido')
  name=m['sha256']+'.mp4';tmp=DATA/(name+'.part');h=hashlib.sha256();size=0
  try:
   with request(base+'/api/'+urllib.parse.quote(id,safe='')+'/video?version='+urllib.parse.quote(m['version'],safe='')) as r, tmp.open('wb') as f:
    while chunk:=r.read(1024*1024):
     size+=len(chunk)
     if size>m['size']:raise ValueError('Archivo excede el tamaño publicado')
     h.update(chunk);f.write(chunk)
   if size!=m['size'] or h.hexdigest()!=m['sha256']:raise ValueError('Archivo incompleto o checksum incorrecto')
   os.replace(tmp,DATA/name)
  finally:tmp.unlink(missing_ok=True)
  entry={'version':m['version'],'file':name}
  if old.get('file'):old['pending']=entry
  else:old=entry
  atomic_json(DATA/'state.json',old)
  return {'message':'Video descargado y verificado'}
 finally:LOCK.release()
def activate():
 with LOCK:
  s=state()
  if 'pending' in s:
   previous=s.get('file');s=s['pending'];atomic_json(DATA/'state.json',s)
   if previous and previous!=s['file']:(DATA/previous).unlink(missing_ok=True)
  return s
PAGE=r"""<!doctype html><html><meta charset="utf-8"><style>html,body{margin:0;background:black;width:100%;height:100%;overflow:hidden}video{width:100vw;height:100vh;object-fit:contain}body.r90 video,body.r270 video{position:absolute;width:100vh;height:100vw;left:50%;top:50%}body.r90 video{transform:translate(-50%,-50%) rotate(90deg)}body.r270 video{transform:translate(-50%,-50%) rotate(270deg)}</style><video muted autoplay playsinline></video><script>
const v=document.querySelector('video');let file='';const rotation=new URLSearchParams(location.search).get('rotation');if(['90','270'].includes(rotation))document.body.className='r'+rotation;
async function load(activate=false){const r=await fetch(activate?'/activate':'/state',{method:activate?'POST':'GET'});const s=await r.json();if(s.file&&s.file!==file){file=s.file;v.src='/media/'+file;v.play().catch(()=>{});}else if(activate&&file){v.currentTime=0;v.play().catch(()=>{});}}
v.onended=()=>load(true);v.onerror=()=>setTimeout(()=>{if(file)v.load();},5000);load();setInterval(()=>{if(!file)load();},3000);
</script></html>"""
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  path=urllib.parse.urlparse(self.path).path
  if path=='/':return self.reply(PAGE.encode(),'text/html')
  if path=='/state':return self.reply(json.dumps(state()).encode(),'application/json')
  if path=='/maintenance':return self.reply(b'<h1>Mantenimiento local</h1><button onclick="fetch(\'/sync\',{method:\'POST\'}).then(r=>r.text()).then(t=>document.querySelector(\'pre\').textContent=t)">Buscar actualizacion ahora</button><pre></pre>','text/html')
  if path.startswith('/media/'):
   name=path.split('/')[-1]
   if len(name)!=68 or not name.endswith('.mp4') or any(c not in '0123456789abcdef' for c in name[:-4]):return self.send_error(404)
   f=DATA/name
   if not f.exists():return self.send_error(404)
   size=f.stat().st_size;start,end=0,size-1;status=200
   if self.headers.get('Range'):
    try:
     a,b=self.headers['Range'].removeprefix('bytes=').split('-');start=int(a);end=min(int(b) if b else end,end)
     if start<0 or start>end:raise ValueError()
     status=206
    except:return self.send_error(416)
   self.send_response(status);self.send_header('Content-Type','video/mp4');self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes')
   if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
   self.end_headers()
   try:
    with f.open('rb') as stream:
     stream.seek(start);remaining=end-start+1
     while remaining:
      chunk=stream.read(min(1048576,remaining));self.wfile.write(chunk);remaining-=len(chunk)
   except (BrokenPipeError,ConnectionResetError):pass
   return
  self.send_error(404)
 def do_POST(self):
  origin=self.headers.get('Origin')
  if origin and origin!='http://127.0.0.1:8080':return self.send_error(403)
  try:
   if self.path=='/activate':obj=activate()
   elif self.path=='/sync':obj=sync()
   else:return self.send_error(404)
   self.reply(json.dumps(obj).encode(),'application/json')
  except Exception as e:self.reply(json.dumps({'error':str(e)}).encode(),'application/json',503)
 def reply(self,b,kind,status=200):
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
def daily():
 while True:
  try:print(sync(),flush=True)
  except Exception as e:print('Sin actualización:',e,flush=True)
  time.sleep(86400)
if __name__=='__main__':
 config();threading.Thread(target=daily,daemon=True).start();print('Reproductor: http://127.0.0.1:8080',flush=True);ThreadingHTTPServer(('127.0.0.1',8080),Handler).serve_forever()
