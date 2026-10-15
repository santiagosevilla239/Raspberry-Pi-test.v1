"""Reproductor Linux sin navegador. Comparte sincronizador y formato con el panel."""
import json, os, re, select, shutil, socket, subprocess, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'player'))
import player as core

def validate(path):
    result = subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
        '-show_entries','stream=codec_name,width,height,avg_frame_rate',
        '-of','json',str(path)],capture_output=True,text=True,timeout=30,check=True)
    streams = json.loads(result.stdout).get('streams',[])
    if not streams or streams[0].get('codec_name') != 'h264':
        raise ValueError('El video debe usar H.264 dentro del MP4')
    return streams[0]

def safe_path(entry):
    name = entry.get('file','')
    if not re.fullmatch(r'[a-f0-9]{64}\.mp4', name): raise ValueError('Nombre de video inválido')
    return core.DATA / name

def select_video():
    """Solo llamar al arrancar o tras EOF; conserva un respaldo en disco."""
    with core.LOCK:
        s = core.state()
        pending = s.get('pending')
        if pending:
            try: validate(safe_path(pending))
            except Exception as e:
                print('Nueva versión rechazada:',e,flush=True)
                s.pop('pending',None)
                core.atomic_json(core.DATA/'state.json',s)
            else:
                previous = {k:s[k] for k in ('file','version') if k in s}
                s = dict(pending)
                if previous: s['backup'] = previous
                core.atomic_json(core.DATA/'state.json',s)
        if s.get('file'): return safe_path(s)

def rollback():
    with core.LOCK:
        s = core.state()
        if s.get('backup'):
            restored = s['backup']
            restored['rejected_version'] = s.get('version')
            core.atomic_json(core.DATA/'state.json',restored)
            return True
    return False

def synchronize():
    try:
        print(core.sync(),flush=True)
    except Exception as e:
        # No URL ni claves en el registro.
        print('No se pudo actualizar; se conserva el video local.',type(e).__name__,flush=True)

def daily():
    path = core.DATA/'schedule.json'
    try: last = json.loads(path.read_text()).get('last_attempt',0)
    except (FileNotFoundError,ValueError): last = 0
    while True:
        now = time.time()
        if now < last or now-last >= 86400:
            last = now
            core.atomic_json(path,{'last_attempt':last})
            synchronize()
        force = core.DATA/'consultar-ahora'
        if force.exists():
            force.unlink(missing_ok=True)
            synchronize()
        time.sleep(5)

def play():
    cfg = core.config()
    rotation = int(cfg.get('rotation',0))
    if rotation not in (0,90,180,270): raise ValueError('Giro inválido')
    parent, child = socket.socketpair()
    args = ['mpv','--no-config','--idle=yes','--force-window=yes','--fs',
        '--no-osc','--osd-level=0','--no-audio','--no-input-default-bindings',
        '--input-terminal=no','--cursor-autohide=always','--hwdec=auto',
        '--video-rotate='+str(rotation),'--input-ipc-client=fd://'+str(child.fileno())]
    if cfg.get('console',True): args += ['--vo=gpu','--gpu-context=drm']
    proc = subprocess.Popen(args,pass_fds=(child.fileno(),))
    child.close()
    def send(command): parent.sendall(json.dumps({'command':command}).encode()+b'\n')
    loaded = None
    buffer = b''
    try:
        while proc.poll() is None:
            if loaded is None:
                loaded = select_video()
                if loaded and loaded.exists():
                    validate(loaded)
                    send(['loadfile',str(loaded),'replace'])
                else: loaded = None
            if not select.select([parent],[],[],1)[0]: continue
            chunk = parent.recv(65536)
            if not chunk: break
            buffer += chunk
            while b'\n' in buffer:
                line,buffer = buffer.split(b'\n',1)
                event = json.loads(line)
                if event.get('event') == 'end-file':
                    reason = event.get('reason')
                    if reason == 'eof': loaded = None
                    elif reason == 'error':
                        print('MPV no pudo reproducir el archivo; intentando respaldo.',flush=True)
                        rollback();loaded = None;time.sleep(3)
                if event.get('error') not in (None,'success'):
                    raise RuntimeError('MPV rechazó un comando: '+event['error'])
        raise RuntimeError('El reproductor se cerró')
    finally:
        parent.close()
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: proc.kill();proc.wait()

if __name__ == '__main__':
    if '--consultar-ahora' in sys.argv:
        (core.DATA/'consultar-ahora').touch()
        print('Consulta solicitada al servicio. Debe estar ejecutándose.')
        sys.exit(0)
    if not shutil.which('mpv') or not shutil.which('ffprobe'):
        sys.exit('Faltan mpv y ffmpeg. Consultá EMPEZAR.md.')
    core.config()
    threading.Thread(target=daily,daemon=True).start()
    try: play()
    except KeyboardInterrupt: pass
