# Saiki: voz, conversación y validación

Actualización de recuperación de voz (28/10/2026): se mantienen eliminados «Enviar grabación», el panel de edición de voz y los controles de velocidad. Jorge (México) tiene prioridad cuando está instalado; para que la ausencia o el fallo de esa voz no deje a Saiki en silencio, se usa una voz española realmente disponible y se muestra su nombre. Ante `synthesis-failed` o bloqueo del navegador, se recupera con Kokoro `em_alex` local. Esta actualización sustituye la restricción anterior de no reproducir nada si Jorge faltaba.

Actualización del 29/10: el micrófono usa primero `getUserMedia` + MediaRecorder + Whisper local para evitar sesiones de Edge que muestran «Te escucho» sin entregar resultados. Solo recurre al reconocimiento nativo si falla el servicio local. Se añadió un medidor de entrada con «Recibiendo sonido» / «Esperando sonido» y se redujo el umbral de detección para habla baja. La captura sigue deteniéndose durante las respuestas. El cierre de habla del reconocimiento nativo fuerza resultados definitivos; las transcripciones parciales no se envían. «Escuchar respuesta» puede activar el audio incluso si se había silenciado o pausado el micrófono.

Comprobación real adicional del 29/10: la voz masculina em_alex generó 139244 bytes WAV y transcribió «Abre mi inventario y muestra los sensores.». Se verificó que localhost:5173 sirve una compilación que incluye captura local y medidor, y que la API devuelve HTTP 200.

Comprobación anterior: el motor local generó 135644 bytes WAV y volvió a transcribir «Abre mi inventario y muestra los sensores.». Dentro del sandbox una DLL de CFFI devuelve acceso denegado; la misma comprobación fuera de esa restricción funciona. En Edge de pruebas las voces nativas existen pero la síntesis devuelve `synthesis-failed`; por eso también se cubre recuperación hacia audio local. No se afirma haber escuchado físicamente los altavoces ni haber hablado al micrófono real. Las secciones posteriores conservan el diagnóstico y las pruebas de la versión previa.

Validación de esta corrección: 98 pruebas React correctas, 13 pruebas HTTP de voz correctas y 8 casos de Saiki en Edge correctos. El caso de síntesis nativa comprueba la recuperación con un WAV sintético de prueba, y el caso de fallo STT comprueba captura, envío, transcripción y siguiente turno con servicios simulados. TypeScript y compilación de producción correctos. La API local fue reiniciada y su OpenAPI ya expone las rutas actuales de voz y abastecimiento.

Fecha: 28 de octubre de 2026. Se conserva React, FastAPI, MongoDB, Ollama, la sesión del layout y el tema oscuro. No se escribieron registros ficticios en la base de la aplicación ni se añadieron servicios de pago.

## Diagnóstico comprobado

- El STT existente es **faster-whisper, modelo `base`, CPU/int8**. Su caché contiene modelo, configuración, vocabulario y tokenizador. Se cargó sin conexión y transcribió un WAV sintético español existente. No se demostró una ausencia del modelo.
- La captura local usa MediaRecorder, contenedores WebM/Opus, Ogg/Opus o MP4 según soporte. PyAV decodifica y convierte a PCM mono de 16 kHz antes de Whisper. La captura ahora solicita mono y 16 kHz como preferencias; la conversión del backend sigue siendo necesaria porque el navegador puede entregar otra frecuencia.
- Los logs existentes contienen transcripciones HTTP 200, silencios HTTP 422, un HTTP 401 al transcribir y un HTTP 429 al sintetizar. El frontend convertía los fallos de autenticación, formato, saturación y servidor en el mismo error de instalación local. **El último fallo de transcripción registrado era una sesión expirada (401)**, no prueba de un modelo ausente.
- STT y TTS locales comparten un worker con exclusión mutua: puede devolver 429 cuando está ocupado. Se conserva ese límite; ahora se distingue del error de instalación y se pausa la sesión sin reintentos infinitos. El modo predeterminado de navegador no utiliza ese worker.
- El TTS Kokoro se reprodujo como fallo en este entorno de ejecución: `ImportError`, DLL `_cffi_backend`, «Acceso denegado». No se atribuye este bloqueo del sandbox al micrófono del usuario. Hay un informe anterior de síntesis local correcta, por lo que no se afirma que Kokoro esté roto en todos los entornos.
- MongoDB respondió a `ping`. En la base configurada había **2 dispositivos, 0 productos, 0 detalles de inventario y 0 alertas**. Son conteos globales de lectura, no los conteos de una empresa autenticada. Los vacíos de catálogo e inventario son compatibles con esa ausencia real; la visibilidad de los dos dispositivos depende del alcance de la empresa. No se utilizó una cuenta real para atribuirlos a una sesión concreta.

## Motores y voz

El modo predeterminado usa **Web Speech API** para reconocimiento y `speechSynthesis` para reproducción. No necesita modelos Python adicionales ni créditos por intervención. Whisper local y Kokoro/Piper configurado siguen siendo opciones explícitas en **Voz de Saiki**. Cambiar de motor pausa una sesión activa para evitar dos micrófonos.

El navegador puede enviar el audio de reconocimiento a su proveedor. Se informa antes de activar el micrófono y en los ajustes. Su disponibilidad varía entre versiones de Chrome y Edge; detectar la API no garantiza que el servicio remoto esté habilitado. No se cambia silenciosamente del modo local al servicio del navegador. Se requiere HTTPS o localhost.

La selección TTS respeta una voz elegida por el usuario. En automático prioriza Jorge de México si aparece realmente en `getVoices()`, después voces masculinas latinoamericanas conocidas y otras alternativas españolas. La interfaz muestra el nombre real, incluidos los cambios por `voiceschanged`. No se renombra otra voz como Jorge.

En el Edge real de este entorno solo aparecieron estas voces españolas locales: **Microsoft Helena - Spanish (Spain)**, **Microsoft Laura - Spanish (Spain)** y **Microsoft Pablo - Spanish (Spain)**. Se verificó que Saiki selecciona **Microsoft Pablo - Spanish (Spain), `es-ES`** entre ellas. No hay una voz mexicana disponible en ese catálogo. La naturalidad y la audición física quedan pendientes de prueba humana.

### FreeTTS y Edge TTS

[FreeTTS publica una API oficial](https://freetts.org/developers) y [ofrece Jorge en su página española](https://freetts.org/text-to-speech/spanish). La documentación específica de la API exige clave y limita el nivel gratuito a uso personal no comercial, con marca de audio; indica pago para uso comercial. Sus cifras de cuotas son inconsistentes entre secciones. No se integró para producción ni se afirma que Jorge esté activa. Una prueba personal autorizada con clave sería posible, pero no garantiza una integración comercial gratuita.

No se usa scraping ni endpoints privados. Se evaluó [edge-tts](https://github.com/rany2/edge-tts): es un cliente de terceros del servicio de lectura de Edge, no una API oficial contratada para esta aplicación. Se eligió la interfaz pública del navegador, cuya exposición de voces puede diferir de «Leer en voz alta» de Edge. Referencia de reconocimiento y limitaciones: [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition).

## Comportamiento corregido

- Los resultados parciales no se envían a la IA. El adaptador recoge segmentos definitivos por índice, admite una pausa corta y entrega un turno una sola vez. Descarta callbacks tardíos y pendientes al cancelar.
- La pregunta definitiva aparece en el chat antes de la petición. La respuesta escrita se añade al recibirla y se lee si la voz está habilitada, incluso si la pregunta se escribió y el micrófono está apagado.
- El micrófono se aborta durante peticiones y reproducción. Se retoma después de la respuesta solo si la sesión continua está activa. Se puede interrumpir, pausar, reanudar o salir.
- Un segundo envío mientras una petición está bloqueada no abre otra petición ni libera prematuramente el micrófono.
- Se conservan el historial por empresa y el proveedor del layout durante navegación SPA. Se muestran los últimos mensajes de ambos interlocutores en la mini ventana, con minimizar, mostrar, ampliar y cerrar voz.
- Se admiten «abre inventario», «muéstrame los sensores», «quiero ver mi inventario», «llévame a sensores» y «abre la sección de productos». Solo se usan las rutas reales `/inventario`, `/monitoreo` y `/productos`.
- Se quitaron los controles de velocidad y se ignoran las velocidades guardadas anteriormente: reproducción a velocidad 1. Se conserva volumen y cancelación interna.
- Los estados informan activación/permisos, escucha, transcripción, procesamiento, preparación de audio, habla, pausa y error. Se distinguen sesión expirada, falta de permisos, audio incompatible, conexión, saturación y tiempo agotado.
- Hay límites de espera para la preparación/reproducción y el transporte local; una operación colgada no bloquea indefinidamente la conversación.
- El equipo y periodo seleccionados llegan a la consulta de sensores. Se incluyen umbrales y se indica cuándo no hay datos suficientes para una tendencia. Producto e inventario se conservan y se envían cuando están seleccionados.
- Una respuesta malformada no se convierte en una lista vacía. Errores de carga y actualización de opciones se distinguen de ausencia de registros. Los logs de voz registran operación, estado HTTP o tipo de dependencia, sin audio, tokens ni transcripciones del usuario.
- No se guardan grabaciones del micrófono. Los blobs locales son transitorios; las URLs de reproducción se revocan. El historial escrito sigue la persistencia preexistente de la aplicación.

## Archivos modificados o añadidos

| Archivo | Cambio |
| --- | --- |
| `frontend/src/features/saiki/browserRecognition.ts` | Adaptador Web Speech: segmentos definitivos, pausa, deduplicación y cancelación. |
| `frontend/src/features/saiki/useSaikiVoice.ts` | Selección de motores, permisos, estados, exclusión escucha/habla, recuperación y velocidad natural. |
| `frontend/src/features/saiki/ttsProvider.ts` | Selección real de voces, preferencia masculina, eventos y retención del utterance. |
| `frontend/src/features/saiki/localVoice.ts` | Conserva STT/TTS locales; errores HTTP diferenciados, formato, timeout, captura y liberación de recursos. |
| `frontend/src/features/saiki/SaikiVoiceSettings.tsx` | Motores explícitos, privacidad, nombre de voz real y eliminación del ajuste de velocidad. |
| `frontend/src/features/saiki/SaikiSession.tsx` | TTS para texto, bloqueo de duplicados, historial/contexto y estados de sesión. |
| `frontend/src/features/saiki/SaikiPresence.tsx` | Aviso previo del reconocimiento, interrupción durante preparación y controles de sesión. |
| `frontend/src/features/saiki/SaikiMini.tsx` | Mensajes de ambos interlocutores, minimizar, mostrar y cerrar voz. |
| `frontend/src/features/saiki/SaikiPage.tsx` | Texto de cada mensaje en un elemento semántico independiente. |
| `frontend/src/features/saiki/saikiGuidance.ts` | Variación natural «quiero ver» sobre la lista de rutas existente. |
| `frontend/src/features/saiki/SaikiEvidence.tsx` | Selector de equipos diferencia carga/error; conserva el contexto del explorador. |
| `frontend/src/features/saiki/SaikiSensors.tsx` | Historial no disponible y error técnico separados de historial vacío. |
| `frontend/src/components/selects/AsyncSelect.tsx` | Error visible incluso con lista vacía cacheada; aviso al conservar opciones antiguas. |
| `frontend/src/api/normalize.ts` | Validación explícita de listas. |
| `frontend/src/api/productos.ts` | Valida el catálogo usado por el contexto. |
| `frontend/src/api/inventarios.ts` | Valida inventarios del producto seleccionado. |
| `frontend/src/api/dispositivos.ts` | Valida dispositivos y alertas. |
| `backend/app/services/local_voice_worker.py` | Diagnóstico por operación y dependencia sin registrar contenido de audio. |
| `backend/app/services/local_voice_service.py` | Nombres exactos de voces locales y logs de fallo útiles. |
| `backend/app/services/saiki_sensor_queries.py` | Respeta horas seleccionadas; umbrales y tendencia basada en evidencia. |
| `backend/app/services/saiki_service.py` | Propaga el periodo del dispositivo seleccionado. |
| `backend/app/services/saiki_intent_router.py` | Ayuda del explorador y de voz sin consultar datos innecesarios. |
| `backend/app/services/saiki_knowledge.py` | Resuelve preguntas de micrófono y voz con instrucciones de la plataforma. |
| `backend/app/knowledge/psitwin.json` | Instrucciones del explorador y nuevo artículo de voz. |
| `backend/scripts/diagnosticar_saiki.py` | Diagnóstico de modelos cacheados y conexión/conteos MongoDB, solo lectura. |
| `backend/requirements-stt.txt` | Instalación opcional de Whisper sin instalar Kokoro/Torch. |
| `frontend/src/features/saiki/{browserRecognition,ttsProvider}.test.ts` | Nuevas pruebas de reconocimiento definitivo y selección real de voz. |
| `frontend/src/features/saiki/{useSaikiVoice,SaikiSession}.test.tsx` | Continuidad, permisos, duplicados, interrupciones y contexto. |
| `frontend/src/features/saiki/{localVoice,saikiGuidance}.test.ts` | Transporte, estados HTTP y comandos naturales. |
| `frontend/src/api/requireList.test.ts` | Formatos inválidos frente a listas vacías reales. |
| `frontend/e2e/saiki.spec.ts` | Conversación y navegación en Edge, estados de datos y catálogo de voces nativo. |
| `frontend/playwright.saiki.config.ts` | Ejecución aislada sin escribir en la base real. |
| `backend/tests/test_saiki_voice_http.py` | Formatos, autenticación, silencio, errores y audio dinámico no cacheado. |
| `backend/tests/test_saiki_sensor_review.py` | Periodos del explorador y ayuda de sensores. |
| `backend/tests/test_saiki_platform.py` | Ayuda de voz sin MongoDB ni modelo conversacional. |

Los cambios que ya estaban presentes en el árbol de trabajo se conservaron y se ampliaron; no se hizo reset ni limpieza de archivos ajenos.

## Instalación y ejecución

No hay dependencias nuevas obligatorias para el modo de voz del navegador. Con el entorno existente, desde la raíz:

```powershell
.\iniciar.cmd
```

Para instalar las dependencias frontend en una copia nueva:

```powershell
cd frontend
npm ci
npm run dev
```

Mantener el backend, MongoDB y Ollama configurados según el README existente. El `.venv` antiguo de esta máquina apunta a un Python que ya no existe; para las comprobaciones se utilizó el Python portátil existente en `.runtime.local/python/python.exe`. No se sobrescribió ese entorno.

Si se desea Whisper local en una instalación nueva, crear un entorno Python 3.12 separado e instalar `backend/requirements-stt.txt`. Configurar `SAIKI_VOICE_PYTHON` al ejecutable de ese entorno y `SAIKI_STT_MODEL=base`. El modelo debe descargarse una vez antes de usarlo sin conexión. `backend/requirements-voice.txt` sigue disponible para quien elija además Kokoro. No es necesario instalarlo para el modo predeterminado.

```powershell
# Ejemplo para una instalación nueva con Python 3.12 disponible:
py -3.12 -m venv .voice.local
.\.voice.local\Scripts\python.exe -m pip install -r backend/requirements-stt.txt
```

No ejecutar el ejemplo de creación sobre el entorno `.voice.local` existente si se desea conservarlo.

Diagnóstico de solo lectura con el entorno portátil actual:

```powershell
cd backend
..\.runtime.local\python\python.exe scripts/diagnosticar_saiki.py
```

## Pruebas automatizadas

```powershell
cd frontend
npm run build
npm run test:ui
```

Edge con servicios de IA/STT/TTS simulados y catálogo nativo comprobado. En Windows se recomienda servidor externo para evitar la demora del cierre del servidor hijo de Playwright:

```powershell
# Terminal 1, desde frontend:
npm run dev -- --host 127.0.0.1 --port 15473 --strictPort

# Terminal 2, desde frontend:
$env:SAIKI_TEST_EXTERNAL_SERVER='1'
npx playwright test --config playwright.saiki.config.ts
```

Pruebas backend desde `backend`:

```powershell
..\.runtime.local\python\python.exe -m pytest tests/test_saiki_voice_http.py tests/test_saiki_sensors.py tests/test_saiki_sensor_review.py tests/test_saiki_platform.py -q
```

Resultados: build y TypeScript correctos; **86 pruebas frontend aprobadas** en la suite completa; **56 pruebas backend aprobadas**; **7 pruebas de Edge aprobadas**. La explicación de sensores también reconoce «incidentes» y separa la última lectura de las estadísticas históricas. Los comandos hablados de pausa y salida también permanecen escritos en el historial.

Las pruebas Edge cubren mensaje definitivo en español, resultado parcial ignorado, duplicado ignorado, respuesta escrita y TTS, micrófono apagado durante reproducción, siguiente turno, navegación a inventario/sensores, historial tras cambio de ruta y recarga, mini ventana y controles, texto sin micrófono, denegación de permisos, ausencia de velocidad, datos vacíos/errores y contexto de producto/inventario/equipo/periodo. Los servicios externos están simulados salvo la inspección del catálogo TTS nativo. No equivalen a una prueba humana de micrófono.

## Prueba manual pendiente

1. Abrir PsiTwin por `http://localhost:5173` o HTTPS en Chrome y Edge, iniciar una sesión EMPRESA real y entrar en Saiki.
2. Revisar el nombre mostrado en **Voz seleccionada**, elegir una voz masculina latinoamericana si está instalada y pulsar **Probar voz**. Comprobar físicamente sonido, volumen y pronunciación.
3. Activar el micrófono, aceptar el permiso y decir «abre inventario». Verificar una sola transcripción, navegación y mini ventana, respuesta escrita y hablada, y retorno automático a escucha.
4. Decir «muéstrame los sensores» y después «¿hay alertas?». Repetir varias veces; comprobar que no aparecen frases de la propia voz de Saiki como mensajes del usuario.
5. Interrumpir una respuesta larga, volver a hablar, minimizar/ampliar y cerrar la voz. Comprobar que el indicador de micrófono del navegador se apaga al salir.
6. Escribir otra pregunta sin activar el micrófono. Comprobar respuesta escrita y reproducción con voz habilitada; desactivar voz y comprobar que el texto sigue funcionando.
7. Seleccionar un producto/inventario y un equipo real si existen. Cambiar el periodo y pedir la explicación. Contrastar los datos con el equipo autorizado de la misma empresa.
8. Denegar permiso y probar reanudación; desconectar la red; comprobar mensajes específicos sin perder historial. Si se elige Local, probar sesión caducada y el diagnóstico de Whisper.

Pendiente: captura y audición con hardware físico; voz masculina mexicana en este sistema; prueba humana de exactitud STT y ruido real; compatibilidad del servicio remoto de reconocimiento de la versión de Chrome/Edge del usuario; validación del alcance de los dos dispositivos con la cuenta real. No se promete funcionamiento sin conexión del reconocimiento del navegador. Kokoro queda como alternativa opcional y su DLL bloqueada en este sandbox no se dio por reparada.
