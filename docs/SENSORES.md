# Monitoreo con sensores — contrato backend ↔ frontend (2026-10-09)

Backend: `backend/` (este repo). Una sola tienda por ahora: un proceso de backend, estado de alertas en
memoria (sin Redis; ver "Nube" al final). Si al implementar hay que desviarse, anotarlo en "Desviaciones".

## Sensores (un ESP32 por equipo de frío: cámara, vitrina, congelador)
| Campo del mensaje | Qué mide | Unidad |
|---|---|---|
| `t_int` | Temperatura interna del equipo de refrigeración / congelación | °C |
| `puerta` | Puerta abierta (`true`) o cerrada (`false`) | bool |
| `t_amb` | Temperatura ambiental | °C |
| `hum` | Humedad ambiental | % |
| `corriente` | Corriente eléctrica del equipo | A |

Cada campo es opcional (un equipo puede no tener todos los sensores; `null` = sin sensor o lectura inválida).

## Transporte: MQTT
- Broker Mosquitto en Docker (`psitwin-mosquitto`, puerto 1883). Un usuario para los dispositivos y otro para el backend.
- Tema: `psitwin/dispositivos/{id_dispositivo}/lecturas`. Un mensaje **cada 0,5 s** con todo junto:
  `{"token": "<token del dispositivo>", "ts": "2026-10-09T12:00:00.500Z", "t_int": 4.2, "puerta": false, "t_amb": 22.1, "hum": 55, "corriente": 2.3}`
  (`ts` opcional: si falta, se usa la hora de llegada).
- El backend valida `token` contra el hash guardado en el dispositivo; descarta mensajes de dispositivos desconocidos,
  inactivos o con token inválido, y valores físicamente imposibles (se tratan como `null`).
- ponytail: auth por token en el mensaje + usuario compartido del broker; en la nube, ACL por dispositivo en el broker.

## Colecciones nuevas
- `dispositivos`: `{id_dispositivo, id_empresa, id_almacen, id_zona, id_rack|null, nombre, activo, token_hash,
  limites: {t_int:{min,max,duracion_s}, t_amb:{…}, hum:{…}, corriente:{min,max,duracion_s},
  puerta:{max_abierta_s, max_aperturas_hora|null}}, ultima_lectura_ts}`.
  Si `limites.t_int` no tiene min/max y hay `id_rack`, se usan `temperatura_min/max` del rack.
  Defaults: `duracion_s` t_int 120, t_amb 300, hum 300, corriente 30; `puerta.max_abierta_s` 60 (**configurable**,
  p. ej. 20 s en vitrinas de tienda).
- `lecturas` (time-series de MongoDB, TTL 7 días) y `lecturas_minuto` (min/máx/promedio por minuto y campo; sin TTL).
- `alertas` (existente): tipos nuevos `TEMPERATURA_FUERA_RANGO`, `HUMEDAD_FUERA_RANGO`, `CORRIENTE_FUERA_RANGO`,
  `PUERTA_ABIERTA`, `APERTURAS_EXCESIVAS`, `SENSOR_SIN_DATOS`; con `id_dispositivo`, `parametro`, `valor`, `limite`,
  `inicio`, `fin`, `duracion_s`, `valor_extremo`. Una alerta por episodio.

## Motor de alertas (en memoria, por dispositivo y parámetro)
- `NORMAL → FUERA` (sale del rango) `→ ALERTA` (si sigue fuera `duracion_s`) → al volver dentro **con margen**
  (t° 0,5 °C, hum 2 %, corriente 0,2 A) se resuelve. Si vuelve antes de `duracion_s`, no hay alerta.
- Puerta: alerta si sigue abierta más de `max_abierta_s`; al cerrar se resuelve. Si `max_aperturas_hora` está
  configurado, alerta `APERTURAS_EXCESIVAS` al superarlo (ventana móvil de 1 h).
- `SENSOR_SIN_DATOS`: sin mensajes 5 s; se resuelve al volver.
- Al arrancar se cargan las alertas de sensores abiertas para no duplicarlas.
- Alertas críticas (`TEMPERATURA_FUERA_RANGO` de `t_int`, `CORRIENTE_FUERA_RANGO`, `SENSOR_SIN_DATOS`) → correo con
  el notification_service existente (best effort, nunca bloquea).

## Escritura
El consumidor acumula lecturas y escribe en bloque cada 1 s (no una inserción por mensaje).

## API REST (todo bajo `/api/v1`, token obligatorio)
| Endpoint | Rol | Notas |
|---|---|---|
| `POST /dispositivos` | EMPRESA | `{id_almacen, id_zona, id_rack?, nombre, limites?}` → dispositivo + **`token` en claro una sola vez** |
| `GET /dispositivos` | EMPRESA (todos los suyos), OPERARIO (su almacén) | incluye `estado` en vivo (abajo) |
| `GET /dispositivos/{id}` | EMPRESA, OPERARIO de su almacén | |
| `PUT /dispositivos/{id}` | EMPRESA | `{nombre?, id_rack?, activo?, limites?}` |
| `DELETE /dispositivos/{id}` | EMPRESA | |
| `POST /dispositivos/{id}/token` | EMPRESA | regenera el token → `{token}` |
| `GET /dispositivos/{id}/lecturas?desde=&hasta=` | EMPRESA, OPERARIO | ≤ 24 h → crudo (submuestreado a ≤ 2000 puntos); > 24 h → por minuto |
| `GET /alertas?…` / `PATCH /alertas/{id}/estado` | existentes | filtrables por los tipos nuevos |

`estado` en vivo: `{conectado: bool, ultima_lectura: {ts, t_int, puerta, t_amb, hum, corriente} | null,
puerta_abierta_desde: ts | null, alertas_abiertas: [alerta…]}`.

## Tiempo real: WebSocket
`GET /api/v1/ws/monitoreo?token=<JWT>&id_zona=<opcional>` (EMPRESA u OPERARIO; operario limitado a su almacén).
Mensajes del servidor (JSON):
- al conectar: `{"tipo":"snapshot","dispositivos":[{id_dispositivo, nombre, id_zona, estado}]}`
- `{"tipo":"lectura","id_dispositivo":…,"ts":…,"t_int":…,"puerta":…,"t_amb":…,"hum":…,"corriente":…}` — como máximo
  1 por segundo por dispositivo.
- `{"tipo":"alerta","evento":"ABIERTA"|"RESUELTA","alerta":{…}}` — inmediato.

## Simulador
`backend/tools/simulador_sensores.py` publica por MQTT cada 0,5 s para N dispositivos registrados (lee sus tokens de argumentos
o de un archivo). Escenarios: `normal`, `tienda` (aperturas frecuentes de vitrina), `falla_compresor` (la corriente cae
y `t_int` sube), `puerta_olvidada`, `desconexion`.

## Nube (después)
Estado del motor y última lectura → Redis; ACL por dispositivo en el broker; TLS en MQTT.

## Desviaciones
(el agente del backend anota aquí lo que cambie)

Implementado el 2026-10-09 (backend sin commits). Precisiones y cambios respecto a lo de arriba:

**Alertas**
- `AlertaResponse` (para todas las alertas) ahora tiene `id_inventario`, `id_producto` y `stock_actual` **opcionales**
  (null en sensores) y añade: `origen` (`"INVENTARIO"` | `"SENSOR"`; alertas antiguas → `"INVENTARIO"`), `id_dispositivo`, `id_zona`,
  `id_rack`, `parametro`, `valor`, `limite`, `inicio`, `fin`, `duracion_s`, `valor_extremo`.
- `parametro`: `t_int` | `t_amb` | `hum` | `corriente` | `puerta` | `aperturas_hora` | `conexion`. `t_amb` usa también
  `TEMPERATURA_FUERA_RANGO` (no crítica). `valor` = valor al abrir (puerta: segundos abierta; aperturas: cantidad en la última hora;
  conexión: segundos sin datos) y no cambia; al resolver se completan `fin`, `duracion_s` (desde `inicio`, que es cuando salió del
  rango) y `valor_extremo` (el peor valor del episodio; null en puerta/conexión).
- `nivel_riesgo`: `CRITICO` para las críticas (t_int, corriente, sin datos), `ALTO` para el resto. Estado `ACTIVA` → `RESUELTA`
  automáticamente; "abierta" = `ACTIVA` o `VISTA` (marcarla VISTA no la cierra). `titulo` = "<tipo>: <nombre del dispositivo>".
- `GET /alertas` acepta filtros por query: `tipo_alerta`, `estado`, `origen`, `id_dispositivo`. **Sigue siendo solo EMPRESA**;
  el operario ve las alertas abiertas de su almacén en `GET /dispositivos` (`estado.alertas_abiertas`) y en el WebSocket.

**Motor**
- `SENSOR_SIN_DATOS` solo vigila equipos que ya enviaron datos alguna vez (`ultima_lectura_ts` no null): un dispositivo recién
  registrado que nunca se conectó no genera alerta. Tras reiniciar el backend, los equipos con datos previos se vigilan desde el arranque.
- Si el rango es más angosto que 2 × margen, el margen se reduce a la mitad del rango (para que siempre pueda resolverse).
- Valores físicamente imposibles → null: t_int/t_amb fuera de −60..100 °C, hum fuera de 0..100 %, corriente fuera de 0..200 A,
  `puerta` que no sea booleano.
- Correo de críticas: `notify_owner` con `event_id = "SENSOR:<id_alerta>"` (solo si `EMAIL_ENABLED`; queda en `notificaciones_email`).

**Dispositivos (REST)**
- `DispositivoResponse`: `{id_dispositivo, id_empresa, id_almacen, id_zona, id_rack, nombre, activo, limites (tal como se configuraron),
  limites_efectivos (los que aplica el motor; t_int heredado lleva "origen":"rack"), ultima_lectura_ts, estado, fecha_creacion,
  fecha_actualizacion}`. Nunca el hash. `POST` añade `token` (32 caracteres, solo esa vez).
- `GET /dispositivos?id_zona=` filtra por zona. `PUT limites` reemplaza el objeto completo. Desactivar (`activo:false`) hace que se
  descarten sus mensajes (las alertas abiertas quedan abiertas hasta reactivarlo). `DELETE` conserva lecturas y alertas históricas.
- Validaciones: almacén de otra empresa → 404; zona que no es del almacén → 404 `"Zona no encontrada en el almacén"`; rack que no es de
  la zona → 404; `min > max` → 422. OPERARIO de otro almacén → 403; PROVEEDOR → 403.
- `GET /dispositivos/{id}/lecturas`: sin `desde`/`hasta` = última hora. Respuesta `{id_dispositivo, desde, hasta, resolucion: "cruda"|"minuto",
  puntos}`. Crudo: `[{ts, t_int, puerta, t_amb, hum, corriente}]`. Por minuto: `[{ts, t_int:{min,max,prom}|null, t_amb…, hum…, corriente…,
  puerta:{fraccion_abierta}|null}]`. Las fechas que vienen de Mongo salen sin zona horaria (son UTC), como en el resto de la API.

**WebSocket**
- Rechazo: se acepta y se cierra con código **4401** (sin token / token inválido o expirado) o **4403** (rol PROVEEDOR o contraseña
  temporal sin cambiar). El cliente no necesita enviar nada.
- `snapshot.dispositivos[]` añade `id_rack` y `activo`. Fechas como ISO 8601 (`…+00:00`). Las lecturas sanean igual que REST (null).
- Cliente lento: cola de 500 mensajes; si se llena, se descartan mensajes nuevos para ese cliente.

**Infra**
- Usuarios del broker: `psitwin-backend` / `backend-dev-123` (lee) y `psitwin-dispositivo` / `dispositivo-dev-123` (publica). Config en
  `backend/infra/mosquitto/`. Variables `MQTT_ENABLED`, `MQTT_HOST`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASSWORD`.
- Hash del token de dispositivo: SHA-256 (no bcrypt: se valida en cada mensaje, 2 por segundo por equipo).
- Si Mongo falla al escribir, se pierde ese segundo de lecturas (el motor sigue en memoria).
- El rack F-01 de "Cámara Fría 1" está en 2–5 °C (se editó antes), así que el dispositivo demo hereda 2–5 °C, no 2–6.
