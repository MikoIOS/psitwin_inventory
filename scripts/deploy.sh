#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# != 1 ]]; then
  echo 'Uso: bash scripts/deploy.sh IP_O_DOMINIO' >&2
  exit 1
fi
bash scripts/prepare-prod.sh "$1"
compose=(docker compose --env-file .env.prod -f docker-compose.prod.yml)
"${compose[@]}" config --quiet
"${compose[@]}" up -d --build --wait --wait-timeout 300
ready=false
for attempt in {1..30}; do
  if "${compose[@]}" exec -T ollama ollama list >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
done
if [[ $ready != true ]]; then
  echo 'Ollama no está listo. Revisa los logs con docker compose.' >&2
  exit 1
fi
model=$("${compose[@]}" exec -T backend python -c 'from app.config.settings import settings; print(settings.ollama_model)')
"${compose[@]}" exec -T ollama ollama pull "$model"
"${compose[@]}" exec -T nginx nginx -t
"${compose[@]}" ps
printf '\nAplicación desplegada. Abre la IP o dominio configurado en .env.prod (HTTP por defecto).\n'
