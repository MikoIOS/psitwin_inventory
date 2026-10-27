# Despliegue en VPS Ubuntu 24.04

Ejecuta los comandos desde la raíz del repositorio. Necesitas la IP pública del VPS, Docker Engine con Compose y Python 3. No necesitas dominio ni certificado para usar HTTP. El despliegue usa CPU para Ollama; no requiere NVIDIA.

## Preparar el servidor

Instala Docker siguiendo https://docs.docker.com/engine/install/ubuntu/ y permite al usuario de despliegue usar Docker. Instala también `git`, `curl`, `python3` y `ufw`. Abre los puertos antes de habilitar el firewall:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw enable
```

Clona el repositorio en el VPS y entra en su carpeta.

## Despliegue simple por IP

Con Docker instalado, ejecuta en el VPS desde la raíz del proyecto (sustituye la IP):

```bash
bash scripts/deploy.sh 123.123.123.123
```

Prepara los secretos, construye e inicia todos los servicios, espera a la API, descarga el modelo configurado de Ollama y comprueba Nginx. Abre **http://123.123.123.123**. No hay que emitir certificados. La descarga del modelo puede tardar varios minutos.

Se conservan los módulos de la aplicación: usuarios y roles, inventario, almacenes, productos, proveedores, órdenes, recepciones, movimientos, pronósticos, alertas, monitoreo por WebSocket y Saiki con Ollama. Los datos y modelos de ML incluidos en el backend se copian con su Dockerfile. El VPS empieza con una base MongoDB nueva; si necesitas los datos locales debes migrarlos por separado.

El script crea `.env.prod`, `backend/.env.prod` y `nginx/mosquitto/passwd` si no existen, con secretos aleatorios para JWT y MQTT. Repetirlo conserva la configuración y los datos. Si ya preparaste una configuración HTTPS, edita `.env.prod` para usar `NGINX_CONFIG=http` y cambia `FRONTEND_URL` y `CORS_ORIGINS` en `backend/.env.prod` a `http://TU_IP` antes de ejecutar el despliegue. No cambies MQTT_PASSWORD sin actualizar también el password del broker.

HTTP no cifra el inicio de sesión ni los datos. HTTPS sigue disponible como opción más adelante.

### Voz de Saiki y correo

El dictado depende del reconocimiento de voz del navegador y sus permisos. El micrófono puede estar bloqueado en una IP remota por HTTP. Para probarlo sin certificado, ejecuta desde tu computadora:

```bash
ssh -N -L 8080:127.0.0.1:80 usuario@123.123.123.123
```

Mantén esa terminal abierta y abre **http://localhost:8080** en un navegador compatible con reconocimiento de voz. `localhost` se considera un contexto confiable: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts. No hace falta instalar LiveKit: el dictado y la lectura de respuestas actuales usan APIs del navegador.

El envío de correos requiere SMTP: configura `EMAIL_ENABLED=true`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` y `SMTP_FROM` en `backend/.env.prod` y recrea el backend. Por defecto el correo está desactivado; el comportamiento de autenticación sin correo es el que ya define la aplicación.

### Sensores MQTT

MongoDB, backend, frontend y Ollama solo son accesibles entre contenedores. MQTT se publica exclusivamente en `127.0.0.1:1883`; para sensores remotos usa una VPN o un túnel SSH y apunta el cliente al extremo local del túnel. No transmite TLS en este puerto. No abras 1883 directamente a Internet.

Para añadir el usuario de sensores, el comando solicita su contraseña de forma interactiva:

```bash
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "$PWD/nginx/mosquitto:/config" eclipse-mosquitto:2 \
  mosquitto_passwd /config/passwd psitwin-dispositivo
chmod 644 nginx/mosquitto/passwd
docker compose --env-file .env.prod -f docker-compose.prod.yml restart mosquitto
```

La ACL separa la lectura del backend y la publicación de sensores; cada dispositivo necesita además su token de aplicación.

Para un simulador MQTT en tu computadora, abre el túnel y conecta el simulador a `localhost:1883` con el usuario `psitwin-dispositivo` y la contraseña que elegiste:

```bash
ssh -N -L 1883:127.0.0.1:1883 usuario@123.123.123.123
```

Para sensores físicos ESP32, usa una puerta de enlace de la tienda conectada por VPN o que reenvíe MQTT por el túnel; el ESP32 no puede conectarse directamente al puerto de loopback del VPS.

## HTTPS opcional (solo con dominio)

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.prod -f docker-compose.prod.yml exec ollama ollama pull qwen3:4b
```

Nginx sirve la aplicación completa por HTTP y también el desafío ACME. El primer arranque del backend espera a que MongoDB esté disponible. Ollama guarda el modelo en un volumen; la descarga y las respuestas pueden tardar con CPU.

Para activar HTTPS, apunta un dominio al VPS, pon ese dominio en `DOMAIN` de `.env.prod` y permite también `sudo ufw allow 443/tcp`. Con DNS resuelto y puerto 80 accesible, sustituye dominio y correo:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot -w /var/www/certbot \
  --cert-name inventario.ejemplo.com -d inventario.ejemplo.com \
  --email administrador@ejemplo.com --agree-tos --no-eff-email
```

Se usa un único dominio. Si necesitas `www`, añade su DNS, un segundo `-d` al certificado y ese nombre al `server_name` de ambas plantillas.

Cambia `NGINX_CONFIG=http` por `NGINX_CONFIG=https` en `.env.prod`, actualiza `FRONTEND_URL` y `CORS_ORIGINS` a `https://TU_DOMINIO` en `backend/.env.prod` y recrea los servicios:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --force-recreate backend nginx
docker compose --env-file .env.prod -f docker-compose.prod.yml exec nginx nginx -t
curl -I https://inventario.ejemplo.com
```

## Operación

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml logs --tail=100 backend nginx
docker compose --env-file .env.prod -f docker-compose.prod.yml exec backend \
  python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"
```

Solo con HTTPS: `bash scripts/renew-certs.sh`.

Solo si activaste HTTPS, programa la renovación dos veces al día con `crontab -e` del usuario con acceso a Docker (ajusta la ruta absoluta):

```cron
17 3,15 * * * /bin/bash /home/tuusuario/psitwin/scripts/renew-certs.sh >> /home/tuusuario/psitwin/certbot-renew.log 2>&1
```

El script renueva por webroot, verifica Nginx y recarga los certificados. Conserva copias de seguridad de MongoDB, `.env.prod`, `backend/.env.prod`, `nginx/mosquitto/passwd` y `nginx/certs`. `docker compose down` conserva los volúmenes; `down -v` elimina los datos.

El servicio Certbot pertenece al perfil `tools`: se ejecuta con `run --rm` y no queda activo. Para GPU, añade un override con la reserva NVIDIA solo en un servidor que tenga GPU y NVIDIA Container Toolkit instalado.
