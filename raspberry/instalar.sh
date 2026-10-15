#!/bin/bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "$0")/.." && pwd)"
if [[ "$project_root" == *' '* ]]; then echo 'Copiá el proyecto a una ruta sin espacios.'; exit 1; fi
if [[ $EUID -eq 0 ]]; then echo 'Ejecutá como usuario normal; se pedirá sudo para instalar.'; exit 1; fi
if [[ ! -f "$project_root/player/config.json" ]]; then echo 'Primero prepará player/config.json según EMPEZAR.md.'; exit 1; fi
sudo apt-get update
sudo apt-get install -y python3 mpv ffmpeg
task_user="$(id -un)"
sudo tee /etc/systemd/system/totem.service >/dev/null <<EOF
[Unit]
Description=Totem con reproductor nativo
After=systemd-user-sessions.service
Conflicts=getty@tty1.service
[Service]
User=$task_user
SupplementaryGroups=video render input
WorkingDirectory=$project_root
ExecStart=/usr/bin/python3 $project_root/raspberry/reproducir.py
Restart=always
RestartSec=5
StandardInput=tty-force
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
StandardOutput=journal
StandardError=journal
UMask=0077
[Install]
WantedBy=multi-user.target
EOF
chmod 600 "$project_root/player/config.json"
sudo systemctl daemon-reload
sudo systemctl enable totem.service
echo 'Servicio preparado. Para probar: sudo systemctl start totem'
echo 'Ver errores: journalctl -u totem -n 50 --no-pager'
echo 'Detener: sudo systemctl stop totem'
echo 'Desactivar arranque: sudo systemctl disable --now totem'
