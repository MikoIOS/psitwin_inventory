# Integración de la actualización de PsiTwin

## Git y conservación del trabajo

El `pull` se detenía porque `origin/main` trasladó el código a `backend/` y
`frontend/`, mientras había cambios locales en las rutas anteriores.
Se guardaron en el commit `5f278e8` y en la rama
`backup/local-upgrade-before-restructure`. Se integró `origin/main` (`f92f092`),
conservando las implementaciones locales. No se usó `reset --hard` ni se publicaron commits.

Se mantuvo la migración local de pronósticos a AutoGluon y la eliminación previa
del antiguo predictor LightGBM. Los archivos antiguos siguen recuperables en Git.

## Implementación y archivos

La actualización local ya incluía Google OIDC, correo HTML, monitoreo por rack,
historial, alertas, herramientas de Saiki, Kokoro, faster-whisper y controles del orbe.
Se conservaron y ejecutaron sus pruebas después de integrarlos.
El inventario completo de archivos por funcionalidad está en
[ACTUALIZACION_SISTEMA_VOZ_LOCAL.md](ACTUALIZACION_SISTEMA_VOZ_LOCAL.md).

Correcciones específicas de esta integración:

- `backend/app/config/paths.py` y `settings.py`: configuración independiente del
  directorio de ejecución; `backend/.env` tiene prioridad sobre el `.env` anterior.
  Se reutilizan entornos y modelos existentes en la raíz, sin copiar secretos.
- `local_voice_service.py` y `autogluon_runtime.py`: rutas de workers, intérpretes
  y cachés adaptadas a la estructura nueva. Se corrigió además una carrera en
  la vigilancia de desconexión: una cancelación absorbida por el ámbito interno
  de Starlette podía bloquear la finalización de una petición de voz. Ahora
  una señal explícita termina el watcher; una prueba reproduce esa condición.
- `backend/scripts/`, `iniciar.cmd`, `frontend/vitest.config.ts`: arranque,
  compilación y pruebas desde las carpetas correctas. Se conserva el uso de
  dependencias npm existentes en la raíz hasta ejecutar `npm --prefix frontend ci`.
- `welcome_email_service.py`, `empresa_controller.py` y `PerfilPage.tsx`:
  la bienvenida requiere correo verificado. El registro antiguo solicita la
  verificación; confirmarla activa el envío. El reintento exige verificación y
  conserva la prevención de duplicados. Se añadieron pruebas de ese ciclo.
- `test_runtime_paths.py`: comprueba reutilización de entornos y prioridad de las
  rutas nuevas. Se ajustó también la prueba optativa de AutoGluon.

## Endpoints disponibles

Rutas bajo `/api/v1`; las de empresa y voz requieren sesión autorizada:

| Método y ruta | Función |
|---|---|
| POST `/auth/google/start` | Iniciar autorización con código y PKCE |
| POST `/auth/google/complete` | Validar identidad y crear sesión o ticket de registro |
| POST `/auth/google/register` | Completar datos empresariales tras Google |
| POST `/auth/google/link` | Vincular una cuenta existente autenticada y su contraseña |
| POST `/auth/google/password/start` | Confirmar identidad Google antes de habilitar contraseña |
| GET `/empresas/me/bienvenida` | Estado del envío |
| POST `/empresas/me/bienvenida/reintentar` | Reintento controlado sin crear otra empresa |
| GET `/saiki/voice/config` | Configuración de voz |
| POST `/saiki/voice/probe/{voice}` | Verificar carga de una voz |
| POST `/saiki/voice/synthesize` | Generar WAV local |
| POST `/saiki/voice/transcribe` | Transcribir grabación local |
| POST `/saiki/events` | Progreso y resultado del asistente |

Se ampliaron los endpoints existentes de dispositivos y lecturas para filtros,
paginación y estadísticas. Se conserva el WebSocket `/ws/monitoreo` para alertas.

## MongoDB y dependencias

Se conservan `nombre_ceo`, identidad `google_sub`, flujos OAuth temporales,
outbox `bienvenidas_email`, referencia `id_lectura`, tipos observados de sensores
e índices de empresa/dispositivo/fecha. El índice de incidentes activos separa
dispositivos y parámetros; los resueltos conservan su historial.
Los índices únicos de correo, RUC y Google requieren corregir duplicados históricos
si los hubiera; no se fusionan ni eliminan empresas automáticamente.
No se migraron datos operativos ni se generaron mediciones de producción.

No fue necesario instalar nuevas dependencias durante esta integración.
Se encontraron Kokoro 0.9.4, faster-whisper 1.2.1, Torch 2.8.0,
Transformers 4.57.6 y soundfile 0.13.1 en el entorno de voz existente.
Requisitos: `backend/requirements.txt`, `requirements-voice.txt` y
`requirements-autogluon.txt`. La voz y AutoGluon conservan entornos separados.

## Pruebas repetidas en esta integración

| Comprobación | Resultado |
|---|---|
| Backend | 330 aprobadas, 3 omitidas, 26 subpruebas aprobadas |
| Frontend | 42 aprobadas en 13 archivos |
| TypeScript y build | Aprobados; permanece advertencia del visualizador de 646 kB |
| Sintaxis Python | `compileall` aprobado |
| Lanzadores PowerShell | Ambos sin errores de parser |
| Git | Conflictos resueltos y comprobación de espacios aprobada |
| Kokoro real, `em_santa` | HTTP 200; WAV de 223244 bytes; 30,184 s, incluida carga |
| Kokoro real, `em_alex` | HTTP 200; WAV de 216044 bytes; 5,620 s, modelo reutilizado |
| faster-whisper real | HTTP 200; transcripción en 7,825 s |
| Ollama/Qwen | Servicio accesible y modelo configurado instalado; respuesta completa no validada |

El backend incluye pruebas contra MongoDB temporal: Google con intercambio
controlado y firma RSA, sesión/perfil, aislamiento empresarial, historial,
alertas e idempotencia del correo con transporte controlado.
Las tres omisiones corresponden a integraciones optativas de AutoGluon,
MongoDB adicional y Ollama. No equivalen a validaciones reales de esos modelos.
El XML de esta ejecución está en `artifacts/integracion-backend.xml`.

La voz se comprobó por los endpoints FastAPI con autenticación controlada,
modelos reales, `HF_HUB_OFFLINE=1` y el bucle Windows Selector compatible con MQTT.
El informe está en `backend/artifacts/voz-http-validacion.json`. El sandbox
inicial impedía cargar `_cffi_backend` por permisos; la prueba real se completó
fuera de esa restricción. Un ensayo anterior se bloqueó por la carrera descrita;
se detuvieron únicamente sus procesos de prueba antes de repetirla.
Whisper transcribió la frase, pero convirtió “Saiki” en “Syke”. No se midió precisión
con micrófono humano ni ruido, y estos tiempos no garantizan latencia en tiempo real.

El sondeo directo de Qwen recibió contenido en 21,93 s, pero era una respuesta
incompleta y no estaba en español; no se cuenta como conversación exitosa.
Un segundo ensayo con el adaptador de Saiki alcanzó el límite de 30 s. Ese ensayo
usó el adaptador síncrono de compatibilidad y su hilo pudo seguir esperando a Ollama
después de cancelar la espera asíncrona, hasta terminar su espera HTTP.
No se detuvo el servidor Ollama. El chat del frontend usa la ruta de progreso
asíncrona con cancelación del cliente HTTP. Queda pendiente validar calidad y
tiempo de respuesta de Qwen en una conversación completa con datos reales.

## Configuración y ejecución

Desde la raíz: `.\iniciar.cmd`. Alternativamente, abre terminales separadas:

```powershell
# Ollama: reutiliza la instancia existente si ya está iniciada.
ollama serve
# Solo si falta el modelo:
ollama pull qwen3:4b

# Backend, desde la raíz:
cd backend
..\.runtime.local\python\python.exe -m app.run --host 127.0.0.1 --port 8000

# Frontend, en otra terminal desde la raíz:
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

Kokoro se inicia bajo demanda como proceso local del backend y conserva el modelo
cargado entre solicitudes. Para una instalación nueva, desde `backend/`:

```powershell
py -3.12 -m venv .voice.local
.\.voice.local\Scripts\python.exe -m pip install -r requirements-voice.txt
.\.voice.local\Scripts\python.exe scripts/verificar_voz_local.py
```

Configura `SAIKI_VOICE_PYTHON=.voice.local/Scripts/python.exe`, proveedor `kokoro`,
modelo `hexgrad/Kokoro-82M`, idioma `es`, voz `em_santa` y alternativa `em_alex`.
En este equipo se conserva el intérprete portable con paquetes separados;
se añadió `backend/` a su archivo local `python312._pth`.
No se solicitaron claves de síntesis ni se usaron archivos de ElevenLabs.

Faltan `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`: registrar exactamente
`http://localhost:5173/auth/google/callback` y abrir el frontend en ese origen.
Las credenciales SMTP privadas existen, pero no se enviaron correos reales.
No se probaron permisos físicos del micrófono, altavoces ni sensores físicos.
La sesión mantiene el Bearer JWT existente; logout elimina el token del cliente,
sin una lista de revocación del servidor. Piper queda como alternativa explícita,
sin instalar ni probar un modelo de esa alternativa.

Fuentes oficiales consultadas:
[Google OIDC](https://developers.google.com/identity/openid-connect/openid-connect),
[voces Kokoro](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md),
[faster-whisper](https://github.com/SYSTRAN/faster-whisper).
