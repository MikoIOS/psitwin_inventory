#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# != 1 || ! $1 =~ ^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$ ]]; then
  echo "Uso: bash scripts/prepare-prod.sh IP_O_DOMINIO" >&2
  exit 1
fi
python3 - "$1" <<'PY'
import os
from pathlib import Path
import secrets
import sys
os.umask(0o077)
domain = sys.argv[1]
root = Path('.env.prod')
backend = Path('backend/.env.prod')
if not root.exists():
    root.write_text(f'DOMAIN={domain}\nNGINX_CONFIG=http\n')
if not backend.exists():
    template = Path('backend/.env.prod.example').read_text()
    template = template.replace('tudominio.com', domain)
    template = template.replace('GENERA_UNA_CLAVE_LARGA_Y_ALEATORIA', secrets.token_hex(32))
    template = template.replace('GENERA_UNA_CLAVE_MQTT', secrets.token_hex(32))
    backend.write_text(template)
PY
mkdir -p nginx/certs nginx/www
if [[ ! -e nginx/mosquitto/passwd ]]; then
  docker run --rm --user "$(id -u):$(id -g)" \
    --env-file backend/.env.prod \
    -v "$PWD/nginx/mosquitto:/config" \
    eclipse-mosquitto:2 sh -ec \
    'umask 022; mosquitto_passwd -b -c /config/passwd "$MQTT_USER" "$MQTT_PASSWORD"; chmod 644 /config/passwd'
fi
echo 'Configuración preparada. Revisa .env.prod y backend/.env.prod antes de iniciar.'
