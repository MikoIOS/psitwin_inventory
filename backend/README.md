# PsiTwin — Backend

API FastAPI + MongoDB + MQTT (sensores). Documentación compartida del repo en [`../docs`](../docs).

## Ejecutar

Desde esta carpeta (`backend/`):

```bash
docker start psitwin-mongo            # MongoDB en localhost:27017
docker start psitwin-mosquitto        # broker MQTT de sensores (ver abajo)
../.venv/bin/pip install -r requirements.txt
cp .env.example .env                  # y ajustar variables
../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
../.venv/bin/python -m unittest discover -s tests
```

Variables en `backend/.env` (ver `backend/.env.example`). `CORS_ORIGINS` = orígenes del frontend separados por comas
(default `http://localhost:5173`). El correo (SMTP) es opcional: si no está configurado, ninguna acción se bloquea.

## Roles y autenticación

Todo `/api/v1/*` exige `Authorization: Bearer <token>` salvo `POST /auth/login` y `POST /auth/register`.
`POST /auth/login {correo, password}` sirve para los tres roles y devuelve
`{access_token, token_type, rol, empresa, operario, proveedor, debe_cambiar_password}`.
Contrato completo con el frontend: [`../docs/ROLES.md`](../docs/ROLES.md).

| Rol | Cómo nace | Qué hace |
|---|---|---|
| **EMPRESA** | `POST /auth/register` | CRUD de almacenes y zonas; crea/borra racks; crea cuentas de operario y proveedor; valida, devuelve o cancela solicitudes de reposición; lee inventario, movimientos (historial con autor), recepciones, alertas, recomendaciones, riesgo y forecast. |
| **OPERARIO** | Lo crea la empresa (`POST /operarios`, con almacén, correo y contraseña temporal) | Solo su almacén: edita racks (estado, temperatura), asigna rack de referencia a productos, crea inventarios y edita límites, registra SALIDAS (venta, vencimiento), crea solicitudes de reposición, registra recepciones y resuelve evaluaciones, valida recomendaciones. |
| **PROVEEDOR** | Lo crea la empresa (`POST /proveedores` con `password_temporal`, o `POST /proveedores/{id}/reset-password`) | Crea y edita sus productos; ve las órdenes ENVIADAS a él y registra el despacho. |

Operario y proveedor deben cambiar la contraseña temporal en su primer ingreso (`PATCH /auth/me/password`); hasta entonces
todo salvo `GET /auth/me` responde `403 {"detail": "Debe cambiar su contraseña", "code": "PASSWORD_CHANGE_REQUIRED"}`.

Flujo de reposición: operario crea la solicitud (`PENDIENTE`) → empresa `validar` (`ENVIADA`) o `devolver` con comentario
(`OBSERVADA` → el operario corrige y `reenviar`) → proveedor registra `despacho` → operario registra la recepción
(`PARCIAL` / `RECIBIDA`).

Racks: `capacidad` es la carga máxima en kg; un rack por nivel de la zona; temperatura solo en zonas refrigeradas.
Un producto solo entra a un rack DISPONIBLE, con kg libres y (si es refrigerado) con un rango de temperatura dentro del suyo.

### Credenciales demo

| Rol | Correo | Contraseña |
|---|---|---|
| EMPRESA (Empresa Demo) | demo@psitwin.com | demo123 |
| OPERARIO (Carlos Ramos, Almacén Central Lima) | operario1@psitwin.com | oper123 |
| OPERARIO (Lucía Torres, Almacén Central Lima) | operario2@psitwin.com | oper234 |
| PROVEEDOR (Distribuidora Andina SAC) | proveedor1@psitwin.com | prov123 |
| PROVEEDOR (Lácteos del Sur SAC) | proveedor2@psitwin.com | prov234 |

## Sensores (MQTT + monitoreo en tiempo real)

Contrato con el frontend: [`../docs/SENSORES.md`](../docs/SENSORES.md). Config del broker: [`infra/mosquitto/README.md`](infra/mosquitto/README.md).

Desde `backend/`:

```bash
# 1. Broker (la primera vez crea el contenedor; luego basta `docker start psitwin-mosquitto`)
docker run -d --name psitwin-mosquitto --restart unless-stopped -p 1883:1883 \
  -v "$PWD/infra/mosquitto:/mosquitto/config:ro,z" eclipse-mosquitto:2

# 2. Backend (el consumidor MQTT arranca en el lifespan; si el broker no está, la API funciona igual
#    y el consumidor reintenta cada 1..30 s)
../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Simulador (tokens de los dispositivos demo en ~/Documentos/PsiTwin_dispositivos_demo.json, fuera del repo)
../.venv/bin/python tools/simulador_sensores.py --archivo ~/Documentos/PsiTwin_dispositivos_demo.json --escenario normal
../.venv/bin/python tools/simulador_sensores.py --archivo ~/Documentos/PsiTwin_dispositivos_demo.json --solo "Cámara" --escenario falla_compresor
../.venv/bin/python tools/simulador_sensores.py --archivo ~/Documentos/PsiTwin_dispositivos_demo.json --solo Vitrina --escenario puerta_olvidada
../.venv/bin/python tools/simulador_sensores.py --archivo ~/Documentos/PsiTwin_dispositivos_demo.json --solo Vitrina --escenario tienda
../.venv/bin/python tools/simulador_sensores.py --archivo ~/Documentos/PsiTwin_dispositivos_demo.json --solo Ambiente --escenario desconexion
```

Un proceso de simulador por dispositivo y escenario (dos simuladores sobre el mismo equipo mezclan sus lecturas).
Cuando el simulador se detiene, a los 5 s se abre `SENSOR_SIN_DATOS` para esos equipos y se resuelve al volver.

Dispositivos demo (Empresa Demo, Almacén Central Lima):

| Dispositivo | Zona / rack | Límites |
|---|---|---|
| Cámara Fría 1 · Rack F-01 | Cámara Fría 1 / F-01 | t_int heredado del rack (2–5 °C), corriente 1–8 A, puerta 60 s |
| Vitrina Tienda 1 | Tienda (sin rack) | t_int 0–5 °C, corriente 0.5–6 A, puerta 20 s, máx. 30 aperturas/h |
| Ambiente Zona Secos A | Zona Secos A | t_amb 15–28 °C, hum 30–70 % |
