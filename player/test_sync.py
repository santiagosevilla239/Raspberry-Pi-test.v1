import unittest,tempfile,threading,json,hashlib,importlib.util
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
spec=importlib.util.spec_from_file_location('player',Path(__file__).with_name('player.py'));p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Test(unittest.TestCase):
 def test_sync_failure_and_restart(self):
  with tempfile.TemporaryDirectory() as temp:
   p.DATA=Path(temp);content=b'first-video';broken=False;version='1'
   class API(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
     nonlocal content,broken,version
     if self.path.endswith('/manifest'):b=json.dumps({'version':version,'size':len(content),'sha256':hashlib.sha256(content).hexdigest()}).encode()
     else:b=content[:-1] if broken else content
     self.send_response(200);self.end_headers();self.wfile.write(b)
   server=ThreadingHTTPServer(('127.0.0.1',0),API);threading.Thread(target=server.serve_forever,daemon=True).start()
   p.config=lambda:{'server':f'http://127.0.0.1:{server.server_port}','shop_id':'open','player_token':'test'}
   try:
    p.sync();self.assertEqual(p.state()['version'],'1');content=b'new-video';version='2';broken=True
    with self.assertRaises(ValueError):p.sync()
    self.assertEqual(p.state()['version'],'1');broken=False;p.sync();self.assertEqual(p.state()['version'],'1');self.assertEqual(p.state()['pending']['version'],'2');p.activate();self.assertEqual(p.state()['version'],'2')
    # A fresh read of disk state needs neither cloud nor browser cache.
    server.shutdown();server.server_close()
    with self.assertRaises(Exception):p.sync()
    self.assertEqual(p.state()['version'],'2');self.assertEqual((p.DATA/p.state()['file']).read_bytes(),content)
   finally:server.server_close()
if __name__=='__main__':unittest.main()
