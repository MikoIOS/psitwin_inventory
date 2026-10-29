# Actualización de PsiTwin: autenticación, monitoreo y voz local

## Estructura después de integrar el remoto

El código reside ahora en `backend/app` y `frontend/src`. Las referencias a `app/`,
`scripts/`, `tests/` y `requirements*.txt` de esta guía son relativas a `backend/`;
las referencias a `src/` son relativas a `frontend/`. Los informes anteriores se
conservan como evidencia histórica. Consulta los resultados de esta integración en
[INTEGRACION_ACTUALIZACION.md](INTEGRACION_ACTUALIZACION.md).

Se conserva el `.env` de la raíz sin copiar secretos. `backend/.env` tiene prioridad.
Las rutas de modelos y entornos buscan primero en `backend/` y reutilizan los archivos
existentes de la raíz. Para una instalación nueva, crea los entornos dentro de `backend/`.

## Ejecutar en este equipo

El Python al que apuntaban `.venv`, `venv` y `.venv-1` ya no estaba disponible. Se descargó Python 3.12.10 desde python.org dentro de `.runtime.local/python`, se instalaron las dependencias del backend allí y se creó `.voice.local` para las dependencias de voz. No se cambiaron los entornos de AutoGluon.

Desde la raíz del proyecto, en terminales separadas:

```powershell
# MongoDB y Mosquitto deben estar disponibles según .env.
# Ollama ya puede estar en ejecución: no inicies una segunda instancia.
ollama serve
ollama list
# Solo si falta el modelo configurado:
ollama pull qwen3:4b

# Backend con bucle compatible con aiomqtt en Windows.
cd backend
../.runtime.local/python/python.exe -m app.run --host 127.0.0.1 --port 8000

# Frontend: abre http://localhost:5173, también para comenzar Google OAuth.
# Desde la raíz, en otra terminal:
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

`iniciar.cmd` conserva su función y ahora puede utilizar el Python portable si `.venv` falla. Usa `app.run` y abre `http://localhost:5173`. Un servidor que ya estaba abierto debe reiniciarse para recoger los cambios; el lanzador conserva su comportamiento de reutilizar servidores existentes. No se reinició una instancia de producción durante las pruebas.

La voz se inicia automáticamente, bajo demanda, como un proceso hijo oculto del backend. No hace falta abrir otro servidor TTS. El modelo se conserva mientras el proceso siga vivo. Solo se admite una inferencia de voz simultánea; una segunda recibe HTTP 429. Detener una operación termina ese proceso y libera la inferencia; la siguiente solicitud vuelve a cargar los modelos.

El `.env` local quedó con estas claves nuevas, sin mostrar ni modificar contraseñas:

```dotenv
SAIKI_TTS_ENABLED=true
SAIKI_TTS_PROVIDER=kokoro
SAIKI_TTS_MODEL=hexgrad/Kokoro-82M
SAIKI_TTS_VOICE=em_santa
SAIKI_TTS_LANGUAGE=es
SAIKI_TTS_SPEED=1.0
SAIKI_VOICE_PYTHON=.runtime.local/python/python.exe
SAIKI_VOICE_SITE_PACKAGES=.voice.local/Lib/site-packages
SAIKI_VOICE_TIMEOUT_SECONDS=120
SAIKI_STT_ENABLED=true
SAIKI_STT_MODEL=base
SENSOR_DISCONNECT_SECONDS=5
SENSOR_MAX_READING_AGE_SECONDS=5
```

Para una instalación normal con Python 3.12, desde `backend/`:

```powershell
py -3.12 -m venv .voice.local
.voice.local/Scripts/python.exe -m pip install -r requirements-voice.txt
.voice.local/Scripts/python.exe scripts/verificar_voz_local.py
```

En ese caso usa `SAIKI_VOICE_PYTHON=.voice.local/Scripts/python.exe` y deja `SAIKI_VOICE_SITE_PACKAGES` vacío. En este equipo, el intérprete portable con el directorio de paquetes separado fue la combinación comprobada mediante HTTP. Los modelos se almacenan en `.voice.local/cache`. La primera preparación necesita Internet para descargar archivos de los repositorios oficiales; la síntesis y transcripción posteriores se ejecutan en el equipo. Para exigir uso sin red, después de preparar los modelos puedes iniciar el backend con `HF_HUB_OFFLINE=1`.

La descarga de Whisper `small` se interrumpió. Se eligió `base`, CPU/int8, como configuración inicial más ligera; se puede volver a `small` mediante `SAIKI_STT_MODEL`. No se sustituyó Kokoro ni se utilizaron archivos de ElevenLabs.

## Cambios de autenticación y bienvenida

Tras integrar el remoto, el registro antiguo solicita verificación y la bienvenida
solo se envía con `correo_verificado=true`. La confirmación activa el envío; los
reintentos también exigen el correo verificado y conservan la idempotencia.

Dependencias principales instaladas para voz: Kokoro 0.9.4, faster-whisper 1.2.1, Torch 2.8.0, Transformers 4.57.6, soundfile 0.13.1 y espeakng-loader 0.2.4. Los rangos de compatibilidad están en `requirements-voice.txt`; el backend conserva `requirements.txt`.

- Se conservó Google OIDC existente: autorización mediante código, PKCE S256, estado de un solo uso, nonce, firma RS256, audiencia, emisor, expiración, correo verificado y vinculación por `sub`.
- Se reforzó la unicidad del correo y RUC para impedir carreras entre registros de Google y registros locales. No se vinculan cuentas por una coincidencia de correo. Las cuentas antiguas se vinculan desde Perfil, después de comprobar su contraseña.
- `EmpresaResponse` acepta fechas BSON también en creación y actualización; el campo de verificación ya tenía conversión. La base actual contiene fechas BSON en `fecha_verificacion_correo`, por lo que esa compatibilidad es necesaria.
- Las contraseñas nuevas usan Argon2. Se siguen verificando hashes bcrypt antiguos. Se eliminó la duplicación del hash empresarial que podía fallar con contraseñas de más de 72 bytes.
- Se corrigió la inconsistencia local entre `FRONTEND_URL` en puerto 3000, Vite en 5173 y el origen `127.0.0.1` frente a `localhost`. El cliente rechaza iniciar OAuth si no regresará al mismo origen que conserva el estado en sessionStorage.
- Registro conserva `nombre_ceo`, el placeholder `Nombre`, el sector `Alimentos` y las validaciones empresariales. Los documentos antiguos pueden carecer de `nombre_ceo`.
- Se conservaron la bienvenida HTML, los recursos JPEG optimizados, el escape del nombre, el CTA basado en `FRONTEND_URL` y la cola idempotente. Las pruebas verifican HTML menor de 20 KB y MIME menor de 100 KB. No se envió un mensaje real ni se comprobó su presentación final en Gmail.
- Los endpoints anteriores de códigos permanecen disponibles hasta validar el consentimiento oficial de Google. La sesión continúa usando el Bearer token y el mecanismo de persistencia existente del frontend; el logout del frontend elimina el token local. No se añadió una lista de revocación de JWT del lado del servidor.

**Pendiente:** configurar `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` privados. Registrar exactamente `http://localhost:5173/auth/google/callback` como URI de redirección y utilizar el mismo origen al abrir la aplicación. SMTP tiene configuración local, pero falta validar el envío y la recepción real. Las credenciales no se imprimieron.

## Monitoreo, historia y alertas

En Monitoreo se añadió selección de almacén → zona → rack, obtenida del backend. Los racks muestran tipos observados y persistidos por los dispositivos, o `Sin sensores` cuando no hay dispositivos. Un dispositivo sin lecturas se identifica como tipos aún desconocidos; no se deducen sensores a partir de límites predeterminados.

Los botones solo muestran tipos disponibles. Se puede elegir el dispositivo si hay más de uno del mismo tipo. La ficha diferencia conexión, antigüedad de la lectura y estado de medición, e incluye identificador, ubicación, unidad, fecha y límites efectivos. Un parámetro ausente nunca se muestra como normal.

El nuevo historial incluye hora, 24 horas, 7 y 30 días, rango personalizado, gráfico y tabla paginados. Se consulta una página en MongoDB; los extremos y promedios se calculan sobre los acumulados del periodo completo, sin usar solo los puntos de la página. Los promedios se ponderan por el número de mediciones. Las estadísticas usan buckets por minuto, no una precisión de segundos en los extremos del rango. Las lecturas originales conservan su retención existente de 7 días; los acumulados por minuto no tienen TTL. No se reconstruyen datos originales que ya expiraron.

Se corrigió el índice único de alertas: antes, sensores diferentes con IDs de inventario nulos podían colisionar. Ahora incluye dispositivo y parámetro. El arranque sustituye solo ese índice conocido y conserva todos los incidentes. Los umbrales de temperatura/humedad/corriente siguen procediendo de la configuración existente y del rack.

Se añadió `LECTURA_DESACTUALIZADA`, con episodio de apertura/resolución independiente de `SENSOR_SIN_DATOS`. Un dispositivo que sigue transmitiendo fechas antiguas mantiene su estado de conexión y genera el incidente de actualidad; esas mediciones no se evalúan como valores actuales para generar alertas de rango. Los tiempos de desconexión y actualidad se configuran mediante las dos variables `SENSOR_*`; ajustarlas al periodo real de publicación de los equipos. Los incidentes nuevos guardan referencia `id_lectura`; los antiguos no se rellenan con referencias inventadas.

El WebSocket existente sigue distribuyendo alertas sin depender del chat. Saiki conserva notificaciones visuales y puede hablar los incidentes nuevos si se habilitaron voz y avisos de sensores, dentro de una sesión iniciada por el usuario. No reproduce incidentes antiguos al cargar ni repite un incidente durante la misma sesión. La supresión visual existente se mantiene en almacenamiento local.

**Operación:** el consumidor MQTT y su estado en memoria requieren una sola instancia de backend para esta arquitectura. No se validó despliegue con varios workers ni sensores físicos; la base actual no tiene dispositivos registrados.

## Saiki y controles de voz

- Se mantuvieron Ollama/Qwen y AutoGluon. Las consultas operativas usan servicios autorizados; no se entrega MongoDB al LLM.
- La herramienta existente `get_sensor_status` acepta una pregunta acotada, dispositivo y almacén. El servicio resuelve rack, tipos, desconexión, alertas e historia; interpreta ayer, semana, mes y madrugada en `America/Lima`, calcula extremos/promedios y compara medias de las dos mitades cuando hay datos suficientes.
- La pregunta genérica por alertas activas incluye ahora sensores aunque la empresa no tenga inventarios. Sigue separada por empresa. Las consultas vinculadas expresamente a un inventario conservan ese alcance.
- Se actualizó la base de conocimiento con los controles reales de Monitoreo e Historial. Los saludos, identidad y ayuda no consultan MongoDB. La herramienta de operarios conserva su consulta específica y distingue un error de un resultado vacío.
- `Saiki Cálido` = `em_santa`; `Saiki Natural` = `em_alex`. Ambas fueron cargadas y sintetizadas con Kokoro 0.9.4. No son clones de Antonio.
- Hay selección, prueba, velocidad, volumen, activación, detención y avisos hablados. Las preferencias se guardan localmente por empresa. La respuesta hablada empieza desactivada hasta la elección del usuario.
- El audio se genera por fragmentos secuenciales. Se cancela la petición activa y el proceso CPU al detenerla. No se sintetiza de nuevo un fragmento dentro de una reproducción. Los últimos 80 mensajes escritos se guardan localmente por empresa y se recuperan al recargar, con un máximo de 8000 caracteres por mensaje recuperado, sin leerlos en voz alta. No se añadió sincronización de conversaciones entre equipos.
- El micrófono usa MediaRecorder y envía la grabación únicamente al backend configurado. Máximo 30 segundos y 4 MB; se rechazan formatos no admitidos, audios excesivos y transcripciones vacías. Whisper usa VAD para silencio/ruido. El botón **Enviar grabación** evita esperar al límite de tiempo; Detener/Pausar cancela y libera las pistas del micrófono.
- El orbe distingue reposo, escucha, preparación/pensamiento, habla y alerta. El habla utiliza RMS obtenido de Web Audio sobre la reproducción real. Se respeta reducción de movimiento. No se usan servicios de reconocimiento ni síntesis del navegador en el flujo predeterminado.
- Se conservó la cancelación del chat y el descarte de respuestas tardías. Si una operación de plazo más largo pasa 10 segundos sin novedades, el frontend lo informa sin interrumpir los fragmentos que avanzan. La carga de voz también informa si demora más de 10 segundos. Ollama tiene un límite configurable de generación `SAIKI_MODEL_MAX_TOKENS=512` y los timeouts existentes.

### Piper opcional

No se activa automáticamente. Si Kokoro falla por recursos, instala `piper-tts` en el entorno de voz, descarga desde el proyecto oficial una voz masculina española y su `.onnx.json`, y configura:

```dotenv
SAIKI_TTS_PROVIDER=piper
SAIKI_PIPER_MODEL=C:/ruta/al/modelo-espanol.onnx
```

Reinicia el backend. El panel identifica Piper y conserva velocidad, volumen y detención. Esta alternativa quedó implementada pero no se instaló ni probó un modelo Piper en este equipo.

## Endpoints

Todos los endpoints de voz requieren una sesión EMPRESA:

| Método y ruta bajo `/api/v1` | Función |
|---|---|
| `GET /saiki/voice/config` | Proveedor, voces configuradas y presencia del intérprete; no sustituye la prueba de carga |
| `POST /saiki/voice/probe/{voice}` | Cargar/verificar `em_santa` o `em_alex` en Kokoro |
| `POST /saiki/voice/synthesize` | JSON `text`, `voice`, `speed` → WAV, sin caché pública |
| `POST /saiki/voice/transcribe` | Cuerpo binario audio/webm, ogg, wav o mp4 → texto español |

Se ampliaron rutas existentes, sin duplicarlas:

- `GET /dispositivos`: filtros `id_almacen`, `id_zona`, `id_rack`, `tipo`.
- `GET /dispositivos/{id}/lecturas`: `desde`, `hasta`, `pagina`, `limite` (máximo 2000), `tipo`. Respuesta con `hay_mas`, resolución y `resumen`. Empresa derivada de la sesión; dispositivo autorizado antes de consultar historia. Rango máximo 366 días.
- `/saiki/events` y `/ws/monitoreo` conservan sus responsabilidades de progreso y eventos.
- Las rutas Google, perfil y reintento de bienvenida ya existían en el árbol recibido; se revisaron y conservaron.

## Cambios en MongoDB

- `empresas`: índices únicos de `google_sub`, `google_registration_ruc`, correo sin distinción de mayúsculas y RUC. Si existen duplicados históricos, deben revisarse antes de crear esos índices; no se fusionan ni borran cuentas.
- `dispositivos`: tipos observados `parametros_disponibles`, última referencia `ultima_lectura_id`.
- `lecturas`: `id_lectura` en documentos nuevos; índice empresa/dispositivo/fecha.
- `lecturas_minuto`: índice empresa/dispositivo/minuto; se conservó el índice único dispositivo/minuto.
- `alertas`: referencia opcional `id_lectura`, nuevo tipo de actualidad, índice único corregido e índices para empresa/estado/fecha y empresa/dispositivo/fecha.
- Se mantuvieron las colecciones OAuth temporales y la outbox `bienvenidas_email`.

Los cambios de esquema se aplican al iniciar los servicios correspondientes. Las pruebas escribieron únicamente en bases temporales identificadas y eliminadas al terminar; no se insertaron lecturas ficticias en producción.

## Archivos de esta actualización

| Área | Archivos |
|---|---|
| Seguridad y Google | `app/utils/security.py`, `app/services/empresa_service.py`, `app/services/google_auth_service.py`, `app/dto/empresa_dto.py`, `app/models/empresa_model.py`, `src/features/auth/googleAuth.ts` |
| Backend de voz | `app/controllers/local_voice_controller.py`, `app/services/local_voice_service.py`, `app/services/local_voice_worker.py`, `app/main.py`, `app/config/settings.py`, `requirements-voice.txt` |
| Historial y alertas | `app/controllers/dispositivo_controller.py`, `app/services/dispositivo_service.py`, `app/repositories/lectura_repository.py`, `app/database/mongodb.py`, `app/services/sensores/monitoreo_service.py`, `motor_alertas.py`, `app/dto/dispositivo_dto.py`, `alerta_dto.py`, `app/repositories/alerta_repository.py`, `app/services/alerta_service.py` |
| Saiki | `app/services/saiki_sensor_queries.py`, `saiki_sensors.py`, `saiki_tools.py`, `saiki_intent_router.py`, `saiki_service.py`, `saiki_responses.py`, `saiki_knowledge.py`, `app/knowledge/psitwin.json` |
| Interfaz | `src/api/dispositivos.ts`, `src/api/saiki.ts`, `src/features/monitoreo/RackMonitor.tsx`, `HistorialSensor.tsx`, `MonitoreoPage.tsx`, `DispositivoDetallePage.tsx`, `monitoreoUtils.ts`, `src/features/saiki/localVoice.ts`, `ttsProvider.ts`, `useSaikiVoice.ts`, `SaikiVoiceSettings.tsx`, `SaikiSession.tsx`, `SaikiPresence.tsx`, `SaikiSensors.tsx`, `src/components/ui/Icon.tsx`, `src/index.css` |
| Ejecución y pruebas | `app/run.py`, `scripts/iniciar.ps1`, `scripts/verificar_voz_local.py`, `scripts/verificar_servicio_voz.py`, `.env.example`, `.env` local, `tests/test_system_upgrade.py`, adaptadores de pruebas de Saiki, `src/features/saiki/localVoice.test.ts`, `useSaikiVoice.test.tsx`, `src/features/monitoreo/RackMonitor.test.ts` |

El repositorio contenía numerosos cambios previos, incluidos autenticación Google, correo, análisis y visualizador. Se conservaron; esta tabla no atribuye todas las modificaciones del estado Git a esta sesión. Inventario ya tenía superficies suaves por estado y Análisis ya evitaba el título visible «de AutoGluon».

## Evidencia y limitaciones

- Pruebas automatizadas de autenticación con intercambio Google controlado, firma RSA, persistencia del frontend, perfil y callbacks. No hubo consentimiento real porque faltan las credenciales OAuth.
- Pruebas de bienvenida con SMTP controlado: personalización/escape, HTML/MIME, CTA, idempotencia, fallo y reintento. No se envió un correo real a Gmail.
- Pruebas contra MongoDB temporal: paginación, aislamiento de empresas, estadísticas completas, índices de incidentes simultáneos y conservación de resueltos. Pruebas del motor de rangos y ciclo de lectura desactualizada.
- Pruebas de voz HTTP con modelos reales y `HF_HUB_OFFLINE=1`: ambas voces y STT devolvieron 200. `artifacts/voz-http-validacion.json` y `artifacts/voz-local-validacion.json` contienen las mediciones. Muestras en `artifacts/saiki-em_santa.wav` y `artifacts/saiki-em_alex.wav`.
- En la primera prueba, em_santa tardó 163,199 s incluyendo descarga/carga; em_alex 7,581 s. Con el backend y archivos en caché, el ensayo HTTP inicial midió 33,361 s para Santa (arranque del proceso incluido), 6,198 s para Alex y 3,955 s para STT de una frase. El rendimiento depende de carga y equipo; no se promete tiempo real. Preparar los modelos antes de activar voz evita el coste de descarga dentro de la primera petición, cuyo límite normal es 120 s.
- Whisper transcribió la frase de prueba, pero confundió nombres propios como Saiki y PsiTwin. No se confirmó precisión con voces humanas, ruido físico ni micrófono real.
- Ollama/Qwen produjo progreso real; el ensayo conversacional abierto se detuvo al límite de 90 s sin respuesta completa. Véase `artifacts/ollama-actualizacion-validacion.json`. Esto sigue siendo una limitación de rendimiento, no un éxito de respuesta completa.
- La herramienta de control de navegador detuvo la revisión porque no pudo determinar con suficiente confianza la URL actual de Edge. No se continuó con acciones UI; queda pendiente comprobación visual y de permisos físicos del micrófono.
- No se entrenó ni se modificó el modelo AutoGluon. La prueba de predicción real es optativa y no se habilitó. Piper y despliegue con varios workers no fueron probados.
- El build conserva una advertencia de tamaño del visualizador LiveKit existente.

La comprobación final de voz se repitió con `WindowsSelectorEventLoop`, necesario para MQTT, y los tres endpoints devolvieron 200: Santa 47,753 s (incluye arranque del proceso), Alex 9,560 s y STT 5,026 s. El servicio usa tuberías de `subprocess.Popen` atendidas en un hilo para funcionar con ese bucle; la inferencia permanece fuera del event loop y se puede terminar al cancelar.

También se conservó un ensayo bajo carga simultánea en `artifacts/voz-http-carga-validacion.json`: Santa alcanzó 504 a los 120,294 s, mientras Alex y STT completaron. La repetición aislada pasó tras terminar las suites y liberar el modelo utilizado en la prueba de Ollama. No se garantiza esa misma latencia con otras aplicaciones o generaciones simultáneas. `OLLAMA_NUM_THREADS=4` limita su paralelismo; en equipos con memoria escasa se puede configurar `OLLAMA_KEEP_ALIVE=0s` para liberar Qwen después de cada respuesta, a cambio de volver a cargarlo en la siguiente pregunta.

Los resultados finales de las suites están en `artifacts/actualizacion-pruebas.md`.

## Fuentes de voz

- Kokoro: https://huggingface.co/hexgrad/Kokoro-82M y https://github.com/hexgrad/kokoro
- Voces oficiales: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
- Transcripción: https://github.com/SYSTRAN/faster-whisper
- Alternativa explícita: https://github.com/OHF-Voice/piper1-gpl
