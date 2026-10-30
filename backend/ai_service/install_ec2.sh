#!/usr/bin/env bash
# Installs only the inference API proxy/service. Does not modify Render or install models.
set -euo pipefail

ai_root="$HOME/psitwin-ai"
ai_backend="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PSITWIN_DEPLOY_BACKEND="$ai_backend"
ai_public_ip="35.171.142.151"
if [[ "$(id -un)" != ubuntu || ! -f "$ai_root/service.env" || ! -x "$ai_root/api/bin/uvicorn" ]]; then
  echo 'Ejecutar como ubuntu, después de instalar la API y crear service.env.' >&2
  exit 1
fi
if [[ -e /etc/nginx/conf.d/psitwin-ai.conf || -e /etc/systemd/system/psitwin-ai.service ]]; then
  echo 'Ya existe configuración psitwin-ai; detener y revisar antes de reemplazarla.' >&2
  exit 1
fi
if [[ -n "$(sudo ss -H -ltn '( sport = :80 or sport = :443 )')" ]]; then
  echo 'Los puertos 80/443 ya están ocupados; revisar antes de modificar el servidor.' >&2
  exit 1
fi

# Validate ownership of the process before stopping the manually launched API.
python3 - <<'PY'
import os
from pathlib import Path
root = Path.home() / 'psitwin-ai'
matches = []
for proc in Path('/proc').glob('[0-9]*'):
    try:
        cmd = (proc / 'cmdline').read_bytes().decode()
        if 'ai_service.main:app' in cmd and (proc / 'cwd').resolve() in {root / 'backend', Path(os.environ['PSITWIN_DEPLOY_BACKEND'])}:
            matches.append(int(proc.name))
    except (OSError, UnicodeError):
        pass
if len(matches) != 1:
    raise SystemExit(f'Esperaba una API manual activa; encontré {matches}. Detener y revisar.')
(root / 'manual-api.pid').write_text(str(matches[0]))
PY

sudo apt-get update
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y nginx python3-venv ca-certificates
sudo python3 -m venv /opt/psitwin-certbot
sudo /opt/psitwin-certbot/bin/python -m pip install 'certbot>=5.4,<6'
sudo /opt/psitwin-certbot/bin/certbot --version

sudo install -d -m 0755 /var/lib/psitwin-acme/.well-known/acme-challenge
sudo tee /etc/nginx/conf.d/psitwin-ai.conf >/dev/null <<'NGINX'
server {
    listen 80;
    server_name 35.171.142.151;
    location ^~ /.well-known/acme-challenge/ { root /var/lib/psitwin-acme; }
    location / { return 404; }
}
NGINX
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx

# Failure here leaves the API on localhost and only ACME validation available on HTTP.
# Certificates are publicly logged; no inference data or service key is sent to the CA.
sudo /opt/psitwin-certbot/bin/certbot certonly \
  --non-interactive --agree-tos --register-unsafely-without-email \
  --preferred-profile shortlived --webroot --webroot-path /var/lib/psitwin-acme \
  --ip-address "$ai_public_ip" --cert-name psitwin-ai-ip

sudo tee -a /etc/nginx/conf.d/psitwin-ai.conf >/dev/null <<'NGINX'
server {
    listen 443 ssl;
    server_name 35.171.142.151;
    ssl_certificate /etc/letsencrypt/live/psitwin-ai-ip/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/psitwin-ai-ip/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    client_max_body_size 2m;
    location / {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Authorization $http_authorization;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_read_timeout 360s;
        proxy_send_timeout 360s;
    }
}
NGINX
sudo nginx -t
sudo systemctl reload nginx

chmod 600 "$ai_root/service.env"
sudo tee /etc/systemd/system/psitwin-ai.service >/dev/null <<UNIT
[Unit]
Description=PsiTwin AI inference API
After=network-online.target ollama.service
Wants=network-online.target

[Service]
User=ubuntu
WorkingDirectory=$ai_backend
EnvironmentFile=$ai_root/service.env
ExecStart=$ai_root/api/bin/uvicorn ai_service.main:app --host 127.0.0.1 --port 8100 --workers 1
Restart=on-failure
RestartSec=5
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
UNIT

python3 - <<'PY'
import os
import signal
import time
from pathlib import Path
root = Path.home() / 'psitwin-ai'
pid = int((root / 'manual-api.pid').read_text())
proc = Path(f'/proc/{pid}')
if proc.exists():
    cmd = (proc / 'cmdline').read_bytes().decode()
    if 'ai_service.main:app' not in cmd or (proc / 'cwd').resolve() not in {root / 'backend', Path(os.environ['PSITWIN_DEPLOY_BACKEND'])}:
        raise SystemExit('El proceso cambió; no se detuvo nada.')
    os.kill(pid, signal.SIGTERM)
    for _ in range(100):
        try:
            if (proc / 'stat').read_text().split(') ', 1)[1].startswith('Z'):
                break
        except FileNotFoundError:
            break
        time.sleep(0.1)
    else:
        raise SystemExit('La API anterior no se detuvo; revisar antes de arrancar systemd.')
PY
sudo systemctl daemon-reload
sudo systemctl enable --now ollama psitwin-ai

sudo tee /etc/systemd/system/psitwin-certbot-renew.service >/dev/null <<'UNIT'
[Unit]
Description=Renew PsiTwin IP TLS certificate
After=network-online.target nginx.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/opt/psitwin-certbot/bin/certbot renew --quiet --deploy-hook "/usr/sbin/nginx -t && /bin/systemctl reload nginx"
UNIT
sudo tee /etc/systemd/system/psitwin-certbot-renew.timer >/dev/null <<'UNIT'
[Unit]
Description=Check PsiTwin certificate renewal twice a day

[Timer]
OnBootSec=5min
OnUnitActiveSec=12h
RandomizedDelaySec=15min
Persistent=true

[Install]
WantedBy=timers.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now psitwin-certbot-renew.timer
sudo systemctl is-active ollama psitwin-ai nginx
sudo systemctl list-timers psitwin-certbot-renew.timer --no-pager
printf 'Instalación terminada. Comprobar HTTPS y autenticación desde fuera de EC2.\n'
