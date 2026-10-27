# Broker MQTT (Mosquitto) — sensores PsiTwin

Contenedor `psitwin-mosquitto`, puerto 1883, sin anónimos.

| Archivo | Qué es |
|---|---|
| `mosquitto.conf` | listener 1883, `allow_anonymous false`, password + ACL |
| `passwd` | usuarios (hash PBKDF2 de Mosquitto) |
| `acl` | qué puede hacer cada usuario |

Usuarios (desarrollo, una tienda):

| Usuario | Contraseña | Permiso |
|---|---|---|
| `psitwin-backend` | `backend-dev-123` | lee `psitwin/dispositivos/#` (lo usa el backend: `MQTT_USER` / `MQTT_PASSWORD`) |
| `psitwin-dispositivo` | `dispositivo-dev-123` | publica en `psitwin/dispositivos/+/lecturas` (ESP32 y simulador) |

Cada dispositivo además manda su propio `token` en el mensaje; el backend lo valida contra el hash guardado
(`POST /api/v1/dispositivos` lo devuelve una sola vez). En la nube: usuario/ACL por dispositivo y TLS.

## Levantar

```bash
cd ~/Documentos/PsiTwin_inventory
docker run -d --name psitwin-mosquitto --restart unless-stopped -p 1883:1883 \
  -v "$PWD/infra/mosquitto:/mosquitto/config:ro,z" eclipse-mosquitto:2
# luego: docker start psitwin-mosquitto
```

(`:z` es por SELinux en Fedora/Nobara.)

## Cambiar / agregar contraseñas

```bash
docker run --rm -v "$PWD/infra/mosquitto:/mosquitto/config:z" eclipse-mosquitto:2 \
  mosquitto_passwd -b /mosquitto/config/passwd psitwin-dispositivo NUEVA_CLAVE
docker restart psitwin-mosquitto
```

Mosquitto 2 avisa que `passwd` es legible por todos (montado desde el repo); funciona igual. En producción,
copiar la config dentro de la imagen con permisos `0700` y dueño `mosquitto`.
