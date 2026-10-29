# Registro, bienvenida y voz de Saiki

## Variables locales

El archivo `.env` local conserva la contraseña de aplicación vacía. Completa manualmente:

```env
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=psitwin2026@gmail.com
SMTP_APP_PASSWORD=
SMTP_FROM_NAME=PsiTwin Inventory
FRONTEND_URL=
```

`SMTP_APP_PASSWORD` es una contraseña de aplicación de Gmail, no la contraseña
normal de la cuenta. `FRONTEND_URL` debe ser la dirección real HTTP(S) de tu web.
Para la demo local en este equipo puedes usar `http://127.0.0.1:5174`; para otros
destinatarios configura la dirección publicada y accesible de la aplicación.
Reinicia FastAPI después de guardar `.env`.

El puerto 465 usa SMTP con TLS implícito. El 587 sigue funcionando con STARTTLS
(`SMTP_USE_TLS=true`). `SMTP_PASSWORD` se conserva como alias de compatibilidad para
notificaciones anteriores; la bienvenida requiere explícitamente `SMTP_APP_PASSWORD`.
La nueva contraseña de aplicación tiene prioridad. No se exponen claves al frontend
ni se guardan respuestas SMTP que puedan incluirlas en el registro de bienvenida.

## Registro y empresas antiguas

El formulario pide «Nombre de la empresa», «Nombre del CEO» (placeholder `Nombre`)
y sugiere `Alimentos` en Sector. `nombre_ceo` es obligatorio únicamente para registros
nuevos, se recorta, admite de 1 a 100 caracteres y no exige apellido ni nombre completo.
Las demás validaciones se conservan. En empresas existentes es opcional y no requiere
migración. Puede añadirse desde Perfil sin impedir guardar los datos de una cuenta antigua.

El registro guarda la empresa y su nombre de CEO antes de solicitar la bienvenida.
FastAPI realiza el intento en una tarea posterior a la respuesta; SMTP se ejecuta fuera
del bucle asíncrono. Un fallo de SMTP nunca elimina la empresa ni cambia sus credenciales.

## Correo y diseño

El remitente es la cuenta SMTP configurada, con nombre visible `PsiTwin Inventory`.
El asunto es `¡Bienvenido a PsiTwin! 🚀`. La plantilla responsive está en
`app/templates/welcome.html`. Usa la ilustración y el logotipo de la imagen adjunta,
conservada sin modificar en `app/assets/email/welcome-reference.png`, como cabecera.
El saludo personalizado y la descripción de bienvenida son HTML, no texto incrustado
en una captura. La cabecera muestra solo la parte ilustrada de la referencia, sin el
marcador raster `{{nombre}}`. El cuerpo contiene el nombre escapado del CEO y un enlace
funcional «Ir a PsiTwin» a `FRONTEND_URL`. Se incluye también una versión de texto plano
completa y la ilustración como recurso CID; no depende de alojar imágenes en terceros.

Los clientes que bloquean imágenes mantienen el mensaje HTML y el enlace. Los clientes
con soporte limitado para imágenes de fondo pueden mostrar una cabecera azul sin la
ilustración; el texto personalizado y la bienvenida no dependen de esa imagen.

## Estados y reintentos

`bienvenidas_email` usa un `_id` determinista por empresa y una transición atómica antes
de SMTP. Dos tareas concurrentes no envían dos correos. Los estados son:

- `PENDIENTE`: registrado, aún no procesado.
- `CONFIGURACION_PENDIENTE`: correo deshabilitado o faltan credenciales.
- `ENVIANDO`: intento reclamado por una tarea.
- `ENVIADO`: SMTP confirmó la aceptación; no se vuelve a enviar.
- `ERROR`: fallo conocido, permite reintentar.
- `REVISAR_ENVIO`: la conexión se perdió sin confirmar el resultado de DATA.

En Perfil puedes ver el estado y pulsar «Reintentar bienvenida» tras corregir la
configuración. Para cuentas antiguas sin CEO, guarda primero ese nombre. Las rutas
`GET /api/v1/empresas/me/bienvenida` y
`POST /api/v1/empresas/me/bienvenida/reintentar` exigen sesión de EMPRESA y solo operan
sobre la empresa autenticada.

SMTP no ofrece una transacción común con MongoDB. Un proceso interrumpido después de
SMTP puede dejar `ENVIANDO`; una confirmación incierta deja `REVISAR_ENVIO`. Ambos
bloquean reintentos automáticos: revisa primero los enviados de Gmail y los logs.
Solo si confirmas que no se envió, un administrador puede cambiar ese evento a `ERROR`
en MongoDB para habilitar el reintento. No se debe forzar `ENVIADO` sin comprobarlo.
La respuesta del perfil no incluye destinatario, contraseña ni detalles del servidor.

## Saiki y la interfaz

Saiki conserva el flujo de FastAPI, predicciones y sensores. El menú utiliza Ψ,
«Saiki» y «Asistente IA». El orbe combina una esfera azul/morada, halos y el
visualizador existente. Sus estados vienen de escucha, petición pendiente y eventos
reales de reproducción. Los eventos de palabras de SpeechSynthesis modulan el orbe;
no se presenta esa señal como una medición de amplitud. Se respeta movimiento reducido.

El micrófono funciona con SpeechRecognition/webkitSpeechRecognition y solicita permiso
al iniciar. Las transcripciones finales usan el mismo envío que el texto y se guardan
en el historial. El reconocimiento se detiene durante peticiones y respuestas habladas
para no transcribir la propia voz de Saiki. La voz usa síntesis en español; puedes
desactivarla, detener una respuesta o pausar/salir de la sesión.

Si el navegador no soporta alguna API, el chat escrito permanece disponible con un
aviso. El permiso real de micrófono y la disponibilidad de voces deben comprobarse
en el navegador del usuario. Se descartan solo silencio, signos y ruido evidente;
las preguntas válidas que no coinciden con un intent siguen llegando al flujo de
Qwen y pueden recibir una aclaración. No se generan valores de inventario o demanda.

## Validación

Las pruebas de SMTP usan dobles de transporte; **no significan que se haya enviado
un correo real**. No es posible verificar entrega a Gmail hasta configurar la clave
y URL. Tras configurarlas, registra una empresa real o reintenta desde Perfil y
comprueba tanto el estado `ENVIADO` como la llegada al buzón.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_welcome_email.py tests/test_notification_service.py tests/test_saiki_input.py tests/test_saiki_http.py tests/test_saiki_request_semantics.py tests/test_saiki_sensors.py tests/test_analisis_demanda.py tests/test_saiki_grounding.py -q
npm.cmd run typecheck
npm.cmd run test:ui -- src/features/auth/RegistroPage.test.tsx src/features/saiki src/features/analisis
npm.cmd run build
```

## Archivos de esta actualización

- Configuración: `.env` (solo local), `.env.example`, `app/config/settings.py`.
- Registro y perfil: `app/dto/empresa_dto.py`, `app/models/empresa_model.py`,
  `app/services/empresa_service.py`, `app/controllers/empresa_controller.py`,
  `src/api/types.ts`, `src/features/auth/RegistroPage.tsx`,
  `src/features/perfil/PerfilPage.tsx`, `scripts/preparar_empresa_forecasting.py`.
- Correo: `app/services/welcome_email_service.py`, `app/services/smtp_transport.py`,
  `app/services/notification_service.py`, `app/services/email_verification_service.py`,
  `app/templates/welcome.html`, `app/assets/email/welcome-reference.png`.
- Interfaz: `src/components/layout/navigation.ts`, `src/components/layout/AppLayout.tsx`,
  `src/components/ui/Icon.tsx`, `src/features/inventario/InventarioPage.tsx`,
  `src/features/analisis/AnalisisPage.tsx`, `src/index.css`.
- Saiki: `app/services/saiki_input.py`, `app/services/saiki_service.py`,
  `src/features/saiki/saikiInput.ts`, `src/features/saiki/useSaikiVoice.ts`,
  `src/features/saiki/SaikiSession.tsx`, `src/features/saiki/SaikiPresence.tsx`,
  `src/features/saiki/SaikiPage.tsx`.
- Pruebas: `tests/test_welcome_email.py`, `tests/test_saiki_input.py`,
  `src/features/auth/RegistroPage.test.tsx`,
  `src/features/saiki/useSaikiVoice.test.tsx`, `src/features/saiki/SaikiSession.test.tsx`.
- Documentación: este archivo.
