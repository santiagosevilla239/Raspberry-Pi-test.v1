# Tótem — adaptación para Raspberry Pi 3 Model A+

## Qué cambió

El panel web de tu computadora y Cloudflare se conservan. Para la Raspberry de 512 MB se agregó un reproductor nativo MPV controlado por Python: no abre Chromium, no tiene botones y lee los videos de la microSD. Todavía no está instalado ni validado en una Raspberry real. El cambio entre loops puede tener una pausa breve; no prometemos reproducción sin separación entre repeticiones.

## Panel en Vercel

Empezá por EMPEZAR_VERCEL.md. El panel en Vercel y el servicio Cloudflare son partes distintas. Para probar el reproductor con navegador en Windows hay que conectar primero su config.json con la API publicada.

## Cuando llegue la placa

1. Instalar Raspberry Pi OS Lite de 32 bits en microSD de 32 GB con Raspberry Pi Imager. No programamos el sistema operativo. Configurar usuario, Wi-Fi y SSH en Imager; conservar las claves en privado. Pi 3 A+ usa HDMI normal y alimentación micro-USB de 5 V / al menos 2,5 A.
2. Copiar esta carpeta a una ruta fija sin espacios. Copiar player/config.example.json a player/config.json, con la URL HTTPS del Worker publicado, shop_id y player_token. En la Raspberry, localhost NO es tu computadora: no sirve dejar la URL de prueba 127.0.0.1:8787.
3. Agregar al JSON: `"rotation": 90` (o 0/180/270 según montaje) y `"console": true`, separados del resto de campos por comas. No guardar secretos en GitHub.
4. Ejecutar `bash raspberry/instalar.sh` desde el usuario normal. Instala dependencias y prepara el arranque automático. No inicia el servicio todavía.
5. Probar `sudo systemctl start totem`. El televisor debe estar encendido y en la entrada HDMI correcta. El servicio usa la consola tty1 sin escritorio. Para regresar a una consola de mantenimiento usar SSH o Ctrl+Alt+F2 con teclado.
6. Revisar `journalctl -u totem -n 50 --no-pager`. La aceleración de video, salida DRM y giro se tienen que comprobar en esa placa y versión de Raspberry Pi OS. Si no funciona no comprar más placas: ajustar primero un equipo piloto.
7. Reiniciar con y sin Internet y verificar que el último video siga funcionando. Una microSD recién instalada sin un primer video descargado no puede reproducir publicidad offline.

## Video y actualizaciones

- Exportar MP4 con video H.264, preferentemente 1920×1080 a 30 fps o su orientación vertical equivalente (1080×1920 necesita prueba). Si la rotación o resolución exigen demasiado, se ajustará la exportación; 80 MB no mide por sí solo la dificultad de reproducción.
- El sincronizador verifica tamaño y SHA256. La versión pendiente se revisa con ffprobe antes de activarla al terminar el video. No se decodifica todo el archivo en esa comprobación; la compatibilidad real sigue requiriendo reproducción.
- La programación nativa persiste la última consulta y espera 24 h entre intentos, incluso tras reiniciar; consulta al arrancar si quedó pendiente. Si falla espera al siguiente intento. Manual: `python3 raspberry/reproducir.py --consultar-ahora` (el servicio debe estar activo). La consulta manual no cambia el plazo diario.
- Se mantiene una copia anterior como respaldo. Los archivos antiguos no se eliminan automáticamente en esta versión. No se garantiza consumo constante de almacenamiento hasta agregar limpieza segura. El límite por video es 100 MB decimales.
- No ejecutar simultáneamente player/player.py y raspberry/reproducir.py sobre la misma carpeta data; son dos alternativas de reproducción.
- El modo nativo no expone panel de administración ni puertos de red entrantes. Las descargas salen hacia Cloudflare. No hay que controlar el escritorio de la Raspberry desde tu casa.

## Estado de las pruebas

Hay pruebas automáticas del Worker/panel API, sincronización con servidor local, descarga incompleta, persistencia offline y cambio al terminar un video simulado. No se ha reproducido tu MP4 en la Raspberry. No se ha desplegado Cloudflare desde esta sesión. No se garantiza aún estabilidad de una jornada, aceleración por hardware ni giro en Pi 3 A+.

Manual MPV usado para la integración: https://mpv.io/manual/stable/ (JSON IPC, end-file, GPU DRM).
