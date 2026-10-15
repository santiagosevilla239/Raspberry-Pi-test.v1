# Panel de tótems preparado para Vercel

## Abrirlo por un enlace ahora

1. El proyecto está en https://github.com/santiagosevilla239/Raspberry-Pi-test.v1 con package.json en la raíz.
2. En Vercel: Add New → Project → elegí ese repositorio.
3. Framework: Vite. Build Command: npm run build. Output: dist. Usá Node.js 22.
4. Para la primera prueba no agregues variables de entorno. Pulsá Deploy.
5. Abrí el enlace de Vercel: el panel entra en MODO DEMO sin contraseña. Cargá tu MP4, mirá la vista previa, escribí el comercio y guardá la publicación demo.

La demo guarda una copia del MP4 en IndexedDB, dentro de ese navegador y esa dirección de Vercel. Conservá los originales: borrar datos del navegador, usar otro navegador, incógnito u otra URL puede perder o separar esos datos. No se envía publicidad a la Raspberry ni se comparte entre dispositivos. El rótulo de demo permanece visible.

## Editarlo y seguir trabajando

Vercel publica y ejecuta la web; el código lo editás en GitHub o Visual Studio Code. Cuando guardás y enviás cambios al repositorio conectado, Vercel hace un despliegue nuevo. No tenés que ejecutar Python para ver el panel demo en Vercel.

Desde tu computadora: instalá Node.js 22, abrí esta carpeta en VS Code, ejecutá npm install y luego npm run dev. Abrí la dirección indicada por Vite. Validá los cambios y enviá el código a GitHub.

## Conectar el funcionamiento real, conservando Cloudflare R2

La pantalla está preparada para Vercel y los videos siguen en R2, como elegimos. Los MP4 se suben directamente desde el navegador al Worker, sin atravesar las funciones de Vercel. Se evita así su límite de carga de 4,5 MB. No hace falta Vercel Blob.

1. Activá R2 en tu cuenta de Cloudflare. Puede requerir facturación y generar cargos por excedentes.
2. En una terminal en la raíz del proyecto:

   npx wrangler@4 login

   npx wrangler@4 r2 bucket create totem-videos

3. Editá cloudflare/wrangler.jsonc: ADMIN_ORIGINS debe ser el origen exacto del panel, por ejemplo https://mi-panel.vercel.app, sin barra final. Si usás más de un origen, separalos por comas. No uses comodines. Las URLs nuevas de preview de Vercel requieren autorización explícita en esta lista.
4. Definí dos claves distintas y largas; no las escribas en archivos públicos:

   npx wrangler@4 secret put ADMIN_TOKEN --config cloudflare/wrangler.jsonc

   npx wrangler@4 secret put PLAYER_TOKEN --config cloudflare/wrangler.jsonc

5. Desplegá la API:

   npx wrangler@4 deploy --config cloudflare/wrangler.jsonc

6. En Vercel → Project → Settings → Environment Variables, agregá VITE_API_BASE_URL con la URL HTTPS del Worker (sin /api). Hacé un redeploy. La URL es pública y no es una contraseña. No agregues ADMIN_TOKEN ni PLAYER_TOKEN con prefijo VITE_: las variables VITE_ son visibles en el navegador.
7. El panel cambia de demo a conexión Cloudflare. Ingresá la clave ADMIN_TOKEN y publicá un video. Las publicaciones demo no se migran solas: cargá los originales en el modo online.
8. En player/config.json de la Raspberry usá esa misma URL de Worker, identificador del comercio y PLAYER_TOKEN. Ver raspberry/ y LEEME_RASPBERRY.md. No apuntes el sincronizador a la URL del panel Vercel.

## Qué incluye / qué falta

- Panel adaptable a computadora y teléfono: comercios, vista previa, límite de 100 MB decimales, progreso de carga, publicación y cierre de sesión. La clave se mantiene solo en memoria hasta cerrar sesión o recargar.
- Demo funcional con guardado local y API Cloudflare preparada con CORS restringido al panel.
- Código del reproductor Windows de prueba y reproductor Linux MPV para la Pi 3 A+.
- No hay credenciales configuradas ni despliegues realizados desde este paquete. El código está cargado en el repositorio de GitHub indicado arriba.
- No se confirma reproducción en el tótem desde este panel; publicar confirma que el servicio recibió el contenido, no que la Raspberry ya lo descargó.
- El Worker usa una clave para administrar y otra compartida por reproductores. Antes de varios clientes, agregar credenciales por dispositivo y controles de acceso más completos.
- No hay limpieza automática de versiones en R2 ni del respaldo local; vigilar almacenamiento.
- El servidor comprueba tamaño y metadatos de la carga; el sincronizador verifica SHA256. Probar siempre el video real y la placa antes de instalar en comercio.
- En modo online la vista previa es la del archivo seleccionado; en demo también permite ver el último archivo guardado al elegir un comercio. No es monitoreo en vivo.

## Condiciones del hosting

Vercel Hobby está destinado a uso personal no comercial. Esta publicación demo sirve para desarrollar y probar; para un servicio comercial verificá el plan adecuado o alojá también el panel en Cloudflare. No se promete hosting comercial gratuito en Vercel.

Referencias: https://vercel.com/docs/plans/hobby ; https://vercel.com/docs/functions/limitations
