> Flujo sustituido: consulta [Registro Gmail por SMTP, sin OAuth](REGISTRO_GMAIL_SMTP.md). Este documento conserva detalles historicos.

# Autenticación Google, bienvenida y Saiki

## Flujo vigente

Consulta [Registro unico Gmail](REGISTRO_UNICO_GMAIL.md) para el flujo actual,
las pruebas y la configuracion exacta. El registro muestra datos empresariales,
verificacion Gmail y ambas contrasenas en una sola pagina. El login publico
utiliza exclusivamente correo y contrasena de PsiTwin, sin boton de Google.

Si aparece `GOOGLE_NOT_CONFIGURED`, faltan las credenciales OAuth de la aplicación.
No son la contraseña de Gmail ni `SMTP_APP_PASSWORD`. En este equipo se comprobó
que el `.env` de la raíz existe pero no contiene valores para las dos claves, y
que `backend/.env` no existe. Configura en el `.env` de la raíz:

```dotenv
GOOGLE_CLIENT_ID=ID_DEL_CLIENTE_WEB_DE_GOOGLE
GOOGLE_CLIENT_SECRET=SECRETO_DEL_CLIENTE_WEB_DE_GOOGLE
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback
```

Los valores de ejemplo no funcionan: deben sustituirse por las credenciales del
proyecto propio en Google Cloud. Sigue la configuración de la sección siguiente
y reinicia el backend después de guardarlas. No publiques ni pegues el secreto
en el chat. El registro real permanece pendiente hasta disponer de esas credenciales.

## Diagnóstico y comportamiento

La verificación antigua guardaba `fecha_verificacion_correo` como `datetime` de MongoDB, mientras `EmpresaResponse` aceptaba únicamente texto. Tanto el perfil como `/auth/me` reutilizan ese modelo: el error de serialización impedía cargar la empresa e incluso responder al login posterior. La inspección de la base existente confirmó una empresa con ese campo de tipo BSON `date`; no se modificaron cuentas existentes. El DTO normaliza esa fecha a ISO 8601 sin migrar ni borrar documentos.

La aplicación usa JWT Bearer, con expiración `ACCESS_TOKEN_EXPIRE_MINUTES`. El cliente conserva token y sesión en `localStorage`, los restaura al recargar y sincroniza con `/auth/me`; cerrar sesión borra ambos y la caché. Un 401 de autenticación cierra la sesión; los fallos de MongoDB, correo o validación empresarial no se convierten en 401. No se utilizan cookies para OAuth. El callback vuelve al frontend y este intercambia el código con FastAPI mediante POST. El origen del frontend debe estar en `CORS_ORIGINS` cuando la API está en otro origen; el proxy de Vite permite usar `/api/v1` durante desarrollo.

Las cuentas antiguas de otros dominios conservan el acceso por contrasena,
incluidos operarios y proveedores. Los nuevos registros requieren Gmail verificado.

## Configuración manual de Google Cloud

1. En Google Cloud Console selecciona o crea el proyecto. Configura Google Auth Platform / pantalla de consentimiento: nombre, correo de soporte y audiencia. Para admitir cuentas Google externas utiliza la audiencia externa; durante pruebas agrega las cuentas Gmail autorizadas como usuarios de prueba. PsiTwin exige `@gmail.com` en los nuevos registros.
2. Crea un cliente OAuth de tipo **Aplicación web**. Solicita únicamente `openid email profile`; no se solicita Gmail API ni acceso a buzones.
3. Agrega como URI de redirección autorizada exactamente `http://localhost:5173/auth/google/callback` para desarrollo. En producción registra `https://TU-DOMINIO/auth/google/callback` y configura esa misma URI en el backend. Si cambias host o puerto, deben coincidir exactamente. No es `/api/v1/auth/google/complete`.
4. Copia manualmente en `.env` del backend:

```dotenv
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback
GOOGLE_OAUTH_TTL_SECONDS=600
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
```

5. Instala las dependencias de `requirements.txt` con el Python de tu backend; Google necesita `httpx` y `PyJWT[crypto]`. Reinicia FastAPI y Vite. No uses variables `VITE_` para el secreto. Mantén un `SECRET_KEY` privado para los JWT de PsiTwin.
6. En producción habilita la reescritura SPA para que `/auth/google/callback` devuelva `index.html`. Usa HTTPS. El callback elimina el código de la barra de direcciones y la aplicación usa `Referrer-Policy` mediante meta `no-referrer`.
7. Comprueba en el navegador registro, consentimiento oficial, entrada al dashboard, recarga, logout y acceso nuevamente con correo y contrasena. Prueba también cancelación del consentimiento y una cuenta sin empresa vinculada. Estos pasos requieren credenciales reales, que no se agregaron al repositorio.

Referencia oficial: [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect), [referencia OIDC de Google](https://developers.google.com/identity/openid-connect/reference).

## Seguridad e identidades existentes

- `/auth/google/start` guarda temporalmente en MongoDB un flujo de un solo uso. El frontend genera una vinculación aleatoria a la pestaña en `sessionStorage`; el servidor conserva su hash. `state` también se guarda como hash. El flujo incluye `nonce` y PKCE S256; el verificador nunca llega al navegador.
- `/auth/google/complete` consume atómicamente el flujo antes del intercambio. Valida firma RS256 con claves públicas de Google, emisor, audiencia, expiración, emisión, `nonce`, `azp` cuando corresponda y `email_verified === true`. La identidad permanente es `google_sub`, no el correo.
- Se descartan access token e ID token de Google tras validarlos; no se solicitan refresh tokens. El navegador recibe únicamente el JWT de PsiTwin.
- El índice único parcial de `google_sub` evita duplicar una identidad. Otro índice parcial de RUC protege los nuevos registros Google concurrentes. Los registros históricos no se reescriben ni se eliminan. Un callback repetido o expirado devuelve un error y requiere iniciar un flujo nuevo.
- Si una cuenta antigua ya tiene ese correo o RUC, no se vincula automáticamente. Debe iniciar sesión con su contraseña, abrir Perfil, confirmar esa contraseña y autorizar Google mediante **Vincular Google**. Una identidad ya vinculada a otra empresa se rechaza. El correo de contacto no se cambia silenciosamente; si coincide con el correo verificado de Google se marca verificado.
- El login Google sin vínculo entrega un ticket temporal, de un solo uso y ligado a la pestaña, para completar los datos empresariales. No crea una empresa vacía.
- Una cuenta antigua creada solo con Google puede configurar una contraseña desde Perfil confirmando nuevamente la identidad Google vinculada. Las empresas registradas con el formulario actual ya tienen la contraseña elegida habilitada después de verificar Google. Un intento de registro de una cuenta ya vinculada no reemplaza su contraseña existente.
- Los endpoints antiguos de códigos empresariales se conservan como obsoletos para compatibilidad hasta validar el consentimiento real de Google en el despliegue. No aparecen en Perfil ni se invocan al registrar. Los flujos de verificación de operarios/proveedores existentes no se eliminaron.

## Bienvenida

El HTML usa tablas y estilos inline, con adaptación de las cuatro tarjetas a móvil. Conserva encabezado ilustrado, marca, colores, saludo, explicación, promesa de valor, cuatro funciones, botón y pie. El nombre proviene de `nombre_ceo`, escapado con `html.escape`; el botón usa `FRONTEND_URL`, validado como HTTP(S).

La imagen original completa no se envía. Se utilizan dos recortes JPEG optimizados, adjuntos MIME relacionados mediante CID: cabecera y logotipo. El saludo y las secciones son HTML seleccionable, con alternativa de texto plano. No hay imágenes base64 dentro del HTML ni se necesita publicar gráficos o inventar un dominio HTTPS. Los CID permiten conservar los recursos locales sin exponer un servidor de imágenes.

La muestra `Carlos` contiene **4.284 bytes de HTML** y aproximadamente **71.098 bytes MIME totales**, incluidas las imágenes; las cabeceras pueden variar con remitente y destinatario. El constructor rechaza HTML mayor de 20 KB y marcadores sin sustituir. La vista previa está en `artifacts/Bienvenida-preview.html`. Esto verifica el tamaño generado; la visualización final y ausencia del aviso de recorte en Gmail necesitan un envío real y revisión de Gmail.

Configura separadamente:

```dotenv
EMAIL_ENABLED=true
SMTP_USER=psitwin2026@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USE_TLS=true
SMTP_APP_PASSWORD=
SMTP_FROM_NAME=PsiTwin Inventory
FRONTEND_URL=http://localhost:5173
```

OAuth de inicio de sesión y la contraseña de aplicación SMTP son credenciales diferentes. No se modificó `.env` ni se imprimieron secretos. El remitente configurado se mantiene en `psitwin2026@gmail.com`.

La outbox `bienvenidas_email` usa un identificador determinista por empresa. El reclamo de envío es atómico; un envío confirmado no se repite. Perfil permite consultar estado y reintentar fallos definitivos. Si se pierde la confirmación SMTP, el estado `REVISAR_ENVIO` bloquea el reintento automático para evitar duplicados. Un fallo de SMTP no revierte el registro ni invalida la sesión. SMTP no ofrece garantía absoluta de entrega exactamente una vez; los estados inciertos necesitan revisión antes de reintentar.

## Saiki y sus tiempos

La base mantenible `app/knowledge/psitwin.json` contiene sección, roles, fuentes de código y pasos reales. Al cambiar una pantalla o permiso, actualiza su artículo y las pruebas. En particular, **Nuevo producto pertenece al proveedor**, no a la empresa. Saiki explica esa restricción sin consultar productos.

El router distingue identidad/saludos/cortesía, ayuda, operarios, ubicaciones, inventario, demanda, sensores, conversación general y ambigüedad. Las primeras dos categorías no consultan MongoDB, Ollama ni AutoGluon. Las preguntas ambiguas piden aclaración; las explicaciones generales usan Ollama/Qwen sin herramientas ni contexto empresarial no verificado. Las preguntas sobre datos consultan solo herramientas autorizadas. Los pronósticos conservan AutoGluon.

`get_workforce` consulta el servicio de operarios de la empresa y devuelve total/activos/inactivos. `get_locations` recorre los almacenes de la empresa y sus zonas/racks. Las herramientas de catálogo, stock, alertas, movimientos y recomendaciones también restringen la consulta a las ubicaciones/empresa autorizadas antes de recuperar los resultados. Un error de conexión produce 503/504, no un resultado vacío.

El frontend usa `/saiki/events` (NDJSON) con estados de trabajo y resultado final. El servidor cancela la tarea al desconectarse el cliente; la conexión async con Ollama se cierra. Detener respuesta cancela `AbortController`, voz y estado de procesamiento; un número de generación impide insertar respuestas antiguas. La pregunta y respuesta de voz también quedan en el historial de texto. El motor AutoGluon usa un worker compartido: se cancela la espera de esta conversación, sin matar un proceso que podría estar atendiendo otras consultas.

Tiempos configurables:

```dotenv
SAIKI_IDLE_TIMEOUT_SECONDS=10
SAIKI_DATABASE_TIMEOUT_SECONDS=10
SAIKI_MODEL_START_TIMEOUT_SECONDS=45
SAIKI_REQUEST_TIMEOUT_SECONDS=360
```

La espera inactiva normal y las consultas de datos se limitan a 10 segundos. La inferencia tiene un plazo inicial explícito de 45 segundos para cargar/procesar el prompt; cada fragmento real de generación renueva después el plazo inactivo de 10 segundos. Los cálculos de pronóstico anuncian trabajo prolongado y tienen el máximo global configurable. No se emiten latidos falsos para prolongar una consulta bloqueada. Los logs registran identificador, intención, herramienta, error y duración, sin credenciales.

El límite global predeterminado de 360 segundos deja espacio al timeout de AutoGluon de 300 segundos y a la explicación posterior. Qwen3 recibe además `/no_think`, junto con `think: false`, siguiendo el [interruptor documentado por Qwen](https://qwen.readthedocs.io/en/stable/inference/transformers.html), para evitar razonamiento interno innecesario antes de responder. El historial original no se modifica para agregar esa instrucción al transporte.

La configuración de voz enumera `speechSynthesis.getVoices()` y escucha `voiceschanged`, ordena español primero y permite probar voz, velocidad, volumen y activar/desactivar lectura. Las preferencias se guardan por empresa en este navegador. `ttsProvider.ts` define el contrato para futuros proveedores; solo Web Speech está implementado, sin servicios de pago ni credenciales nuevas. Las pruebas de voz usan voces simuladas explícitas, no demuestran que un altavoz físico o una voz del sistema haya reproducido sonido.

## Verificación y pendientes externos

Se ejecutaron pruebas de FastAPI/JWT con MongoDB real en bases temporales de nombre aleatorio, que se limpiaron tras cada prueba. El proveedor Google se controla en pruebas: la firma RSA y la validación de claims son reales, pero no representan un consentimiento real contra Google. Las pruebas de SMTP comprueban composición, transporte TLS, ACK, outbox y reintentos con colaboradores controlados; no se envió correo a una dirección real.

Las pruebas de React cubren retorno del callback al dashboard, registro de identidad nueva, persistencia de sesión al remontar, logout, cancelación con respuesta tardía, transporte progresivo, timeout, selección de voz y opciones de reproducción. El build de producción y TypeScript se verificaron. Las suites concretas y el último resultado se resumen en `artifacts/validacion-auth-correo-saiki.md`.

Pendiente para cerrar la validación externa: configurar Google Cloud y `.env`, completar el consentimiento real en navegador, enviar/revisar la bienvenida en Gmail y escuchar/probar las voces disponibles en el navegador del usuario. El estado del ensayo de inferencia real de Ollama está en `artifacts/saiki-real-ollama-check.json`; no confundir disponibilidad del servicio con inferencia exitosa.
