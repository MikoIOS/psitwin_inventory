#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
compose=(docker compose --env-file .env.prod -f docker-compose.prod.yml)
"${compose[@]}" run --rm certbot renew --webroot -w /var/www/certbot
"${compose[@]}" exec -T nginx nginx -t
"${compose[@]}" exec -T nginx nginx -s reload
