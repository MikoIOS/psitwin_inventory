# Registro Gmail sin Google OAuth — configuración vigente

Esta guía sustituye los flujos OAuth descritos en los informes anteriores.

## Flujo final

1. En `/registro`, completa empresa, CEO (solo nombre), RUC, sector, teléfono,
   Gmail, contraseña y confirmación. La contraseña de PsiTwin exige 8–128 caracteres.
2. Registrar empresa crea una cuenta empresarial pendiente con hash Argon2id.
   Todavía no permite iniciar sesión. No se abren páginas de Google.
3. Abre el enlace recibido por correo y pulsa **Verificar correo y activar cuenta**.
   Esta confirmación evita que un escáner automático consuma el enlace.
4. Se activa la cuenta y se programa la bienvenida HTML con el nombre del CEO.
5. Inicia sesión con Gmail y contraseña de PsiTwin y accede al dashboard.

No se requiere Client ID, Client Secret, pantalla de consentimiento ni configuración
de Google Cloud. Los campos históricos de identidad Google no se borran; el router
OAuth ya no está publicado. Se retiraron el callback y las tarjetas OAuth del perfil.
El login de empresas antiguas, operarios y proveedores mantiene sus correos y roles,
incluidos dominios distintos de Gmail. No se revocó retroactivamente su verificación.

El Gmail nuevo se valida, recorta y normaliza a minúsculas. RUC valida 11 dígitos,
prefijo y dígito de control, sin afirmar que exista o esté activo en SUNAT.
Referencia sobre identificación y consulta: [SUNAT](https://centrovirtual.sunat.gob.pe/tramites/inscribete-ruc),
[consulta de RUC](https://www.gob.pe/565-consulta-de-ruc).

## Endpoints

- `POST /api/v1/auth/register`: datos empresariales, `correo`, `password` y
  `password_confirmation`; devuelve 201 sin sesión. Duplicados: 409.
- **Nuevo** `POST /api/v1/auth/verification/confirm`: `{ "token": "..." }`.
  Activa una cuenta pendiente; rechaza tokens falsos, caducados o reutilizados.
- **Nuevo** `POST /api/v1/auth/verification/resend`: `{ "correo": "..." }`.
  Respuesta genérica 202 para no revelar cuentas; máximo un envío por cuenta
  durante el intervalo configurado, incluso con solicitudes concurrentes.
- `POST /api/v1/auth/login`: comprueba contraseña y verificación solo para cuentas
  nuevas marcadas como pendientes; las cuentas antiguas conservan acceso.
- `/auth/me`, `/empresas/me` y reintentos de bienvenida mantienen sus permisos.
- `/auth/google/*`: retirados de la aplicación pública; responden 404.

El enlace lleva el token en el fragmento URL, que no se envía a los logs HTTP.
La pantalla lo retira de la barra de direcciones y lo mantiene solo en memoria.
No se almacenan contraseñas en localStorage, sessionStorage ni URLs.

## MongoDB y consistencia

Se reutilizan `empresas`, `email_verifications` y `bienvenidas_email`.
La cuenta CEO sigue siendo el documento empresarial con rol EMPRESA; no se crea
una colección paralela de usuarios. Los nuevos documentos incorporan
`requiere_verificacion_registro=true`, `correo_verificado=false` y posteriormente
`fecha_verificacion_correo`. La inserción de cuenta y empresa es un único documento.
No se modifican los registros existentes.

Se mantienen índices únicos de correo (sin distinguir mayúsculas) y RUC. La
verificación utiliza SHA-256 de un token aleatorio de 48 bytes, fecha de expiración,
marca de consumo e índice TTL. El token en claro solo se envía al destinatario.
Existe índice único disperso de `token_hash`. Un reenvío sustituye el enlace anterior;
el cambio atómico de estado impide activar dos veces la misma empresa.

El outbox existente identifica la bienvenida por empresa para impedir duplicados.
Un fallo SMTP conserva la empresa pendiente y permite reenviar el enlace después
del intervalo. Un fallo de bienvenida conserva la cuenta activa y puede reintentarse
desde el perfil. La incertidumbre de entrega SMTP no se reintenta ciegamente.

## Configuración SMTP privada

La configuración real actual ya tiene EMAIL_ENABLED, usuario y contraseña de
aplicación disponibles; **no es necesario configurar OAuth**. No copies secretos
al frontend ni al repositorio. Variables consumidas por el backend:

```dotenv
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USE_TLS=true
SMTP_USER=psitwin2026@gmail.com
SMTP_APP_PASSWORD=REEMPLAZAR_POR_LA_CONTRASENA_DE_APLICACION_PRIVADA
SMTP_FROM=psitwin2026@gmail.com
SMTP_FROM_NAME=PsiTwin Inventory
FRONTEND_URL=http://localhost:5173
EMAIL_VERIFICATION_TTL_MINUTES=10
EMAIL_VERIFICATION_COOLDOWN_SECONDS=60
```

No reemplaces una contraseña válida por el marcador del ejemplo. El backend lee
`.env` de la raíz y después `backend/.env`, si existe. `SMTP_PASSWORD` es la
alternativa histórica; `SMTP_APP_PASSWORD` tiene prioridad. Puerto 465 usa SSL
implícito; 587 usa STARTTLS. FRONTEND_URL controla tanto el enlace de activación
como el botón de bienvenida. Para usuarios en otros equipos usa una URL accesible
para ellos; localhost solo funciona en el equipo que ejecuta PsiTwin.

En Git Bash, desde la raíz:

```bash
./iniciar.cmd -Detener
./iniciar.cmd
```

## Pruebas y limitaciones

Resultados finales: **359 pruebas backend aprobadas, 3 omitidas y 26 subpruebas
aprobadas; 48 pruebas frontend aprobadas; 4 escenarios Playwright aprobados**
(dos escenarios completos en escritorio y móvil).

La instancia habitual se reinició y se comprobó con Edge en `localhost:5173`:
formulario completo, Gmail editable, ausencia de botones Google, `/health` 200
y antiguo inicio OAuth 404. No se crearon datos de producción en esta comprobación.
Una consulta de conteo, sin exponer datos personales, confirmó que la base local
no contiene cuentas con `password_local_habilitada=false` dependientes solo de OAuth.

Se ejecutaron pruebas con FastAPI y MongoDB temporal real, captura SMTP y Edge
mediante Playwright. Cubren registro, Gmail, confirmación de contraseña, RUC,
cuenta pendiente, hash Argon2id, enlace falso/caducado/usado, reenvío y cooldown,
fallo SMTP, bienvenida personalizada, login, perfil BSON, dashboard, recarga,
logout, duplicados, roles antiguos y separación de empresas.

La compilación TypeScript/Vite pasó. Se mantiene un aviso previo de tamaño del
bundle de audio, ajeno a autenticación. Las pruebas de navegador pueden mostrar
avisos del proxy WebSocket al recargar; el flujo de autenticación se comprueba.

**Prueba real SMTP ejecutada:** Gmail aceptó un correo HTML de prueba, identificado
como prueba técnica, desde y hacia `psitwin2026@gmail.com`, con SSL en 465.
No se crearon empresas de producción. No se inspeccionó la bandeja de entrada;
aceptación SMTP no equivale a recepción verificada. Revisa Inbox/Spam para confirmarla.
No se enviaron mensajes de prueba a clientes ni destinatarios externos.

Script opcional para repetir esa prueba (envía un correo, no solo diagnostica):

```bash
./.runtime.local/python/python.exe backend/scripts/probar_smtp_registro.py
```

Evidencias: `artifacts/auth-email-links.xml`,
`artifacts/auth-browser.local/results.json`, capturas `registro-smtp-desktop.png`
y `registro-smtp-mobile.png`. Las zonas magenta son máscaras de las contraseñas.

## Archivos de esta actualización

- `backend/app/controllers/empresa_controller.py`: registro directo y endpoints de enlaces.
- `backend/app/services/registration_link_service.py`: enlaces seguros y SMTP existente.
- `backend/app/services/{auth_service,empresa_service,email_verification_service}.py`:
  estado pendiente, bloqueo de acceso y compatibilidad.
- `backend/app/main.py`: router OAuth retirado; se conserva saneamiento de errores.
- `backend/.env.example`: SMTP sin credenciales OAuth obligatorias.
- `backend/scripts/probar_smtp_registro.py`: prueba real sin exponer secretos.
- `backend/tests/{test_registration_links,test_google_auth,test_welcome_email,browser_auth_app}.py`.
- `frontend/src/features/auth/{RegistroPage,VerifyEmailPage}.tsx` y prueba de RegistroPage.
- `frontend/src/features/perfil/PerfilPage.tsx`: tarjetas OAuth retiradas.
- `frontend/src/api/{auth,types}.ts`, `frontend/src/routes.tsx`.
- `frontend/e2e/auth.spec.ts`, `frontend/playwright.config.ts` y documentación.

No se instalaron dependencias adicionales. No se cambiaron inventario, sensores,
AutoGluon ni Saiki. Los archivos OAuth antiguos quedan sin rutas públicas para
preservar temporalmente el historial y sus pruebas; no participan en el registro.
