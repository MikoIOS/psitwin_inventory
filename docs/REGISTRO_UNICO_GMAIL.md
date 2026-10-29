> Flujo sustituido: consulta [Registro Gmail por SMTP, sin OAuth](REGISTRO_GMAIL_SMTP.md). Este documento conserva detalles historicos.

# Registro empresarial y acceso por contraseña — 27/10/2026

Esta guía sustituye las descripciones anteriores del flujo de autenticación.

## Resultado y errores encontrados

El login utiliza correo y contraseña de PsiTwin, sin botón de Google. El registro
muestra en una sola página nombre de empresa, CEO, RUC, sector, teléfono,
verificación Gmail, contraseña y confirmación. CEO admite un solo nombre;
el sector sugiere Alimentos. Se conservaron los cinco atributos empresariales
del formulario anterior. El RUC exige 11 dígitos; no se afirma su existencia.

Google verifica exclusivamente el correo del registro público. El backend conserva
los datos empresariales durante OAuth; el navegador mantiene además un borrador
sin contraseñas. Al regresar o cancelar se recupera el formulario. Las contraseñas
se descartan al salir hacia Google. El correo es de solo lectura y su estado se
consulta en el servidor, sin confiar en sessionStorage. Cambiar cuenta o editar
los datos después de verificar requiere una nueva verificación.

El diagnóstico real detectó **GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET vacíos**.
La URI, FRONTEND_URL y CORS coinciden con localhost:5173. El mensaje de configuración
no se ocultó: el consentimiento real requiere esas credenciales privadas.
También se eliminó el acceso público por Google y se corrigió la restricción
general a Gmail que impedía acceder a cuentas antiguas de otros dominios.
Los nuevos registros sí requieren Gmail verificado; las cuentas existentes,
operarios y proveedores conservan sus credenciales.

El error anterior del perfil estaba relacionado con fechas BSON y un DTO que
aceptaba únicamente texto. La normalización existente a ISO se conserva y se
volvió a comprobar con fechas reales de MongoDB en las pruebas.

## Seguridad, endpoints y MongoDB

- `POST /api/v1/auth/login`: correo y contraseña; conserva roles existentes.
- `POST /api/v1/auth/google/start`: exige datos empresariales y propósito registro.
- `POST /api/v1/auth/google/complete`: valida Google y entrega un ticket temporal;
  no inicia sesión pública con una identidad ya registrada.
- **Nuevo** `POST /api/v1/auth/google/registration/status`: comprueba ticket,
  vínculo al navegador, estado y caducidad; devuelve correo y datos del servidor.
- `POST /api/v1/auth/google/register`: exige contraseña y confirmación coincidentes,
  consume la verificación y crea cuenta y sesión.
- `/auth/me` y `/empresas/me`: recuperan identidad, empresa y perfil.

Se conservan Authorization Code, PKCE, state, nonce y validación de firma, issuer,
audience, expiración, email_verified y sub. Los errores de validación de autenticación
no devuelven los valores de contraseñas recibidos. No hay secretos en el frontend.
Los endpoints históricos de vinculación y recuperación de contraseña requieren
una sesión autenticada; no sustituyen al login público por contraseña.

La arquitectura existente representa al CEO como cuenta empresarial, rol EMPRESA,
en un único documento de `empresas`. Se guardan nombre_ceo, correo, google_sub y
hash Argon2id en ese documento; no se crea una segunda tabla de usuarios CEO.
Esta inserción única evita empresas sin cuenta administrativa. Se conservan índices
únicos de RUC, correo y Google sub, flujos OAuth temporales con TTL y tickets de un
solo uso. No se borraron ni migraron documentos empresariales existentes.

La bienvenida usa el outbox existente por empresa y el nombre real del CEO,
con HTML optimizado y remitente psitwin2026@gmail.com. Un fallo SMTP conserva
el registro y permite reintento controlado. La sesión existente usa JWT Bearer,
restauración desde almacenamiento del cliente y consulta de perfil. Logout borra
la sesión local y protege las rutas; no se añadió revocación central de JWT.

## Configuración exacta de Google

1. Abre Google Cloud Console y selecciona o crea un proyecto. En Google Auth
   Platform configura Branding: nombre de aplicación, soporte y contacto.
2. En Audience elige External si usarás cuentas externas. En modo Testing agrega
   cada Gmail autorizado en Test users. Solicita solamente `openid email profile`
   en Data Access. No necesitas Gmail API ni permisos de buzón.
3. En Clients crea un cliente OAuth de tipo **Web application**.
4. Registra exactamente esta Authorized redirect URI:
   `http://localhost:5173/auth/google/callback`.
   Puedes registrar `http://localhost:5173` en Authorized JavaScript origins;
   este flujo intercambia el código en el backend y no necesita el SDK JavaScript.
5. Copia los valores reales en el archivo privado `.env` de la raíz:

```dotenv
GOOGLE_CLIENT_ID=REEMPLAZAR_POR_EL_CLIENT_ID_REAL
GOOGLE_CLIENT_SECRET=REEMPLAZAR_POR_EL_CLIENT_SECRET_REAL
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback
GOOGLE_OAUTH_TTL_SECONDS=600
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
```

No uses los marcadores como credenciales. No uses `VITE_` para secretos. Se lee
primero `.env` de la raíz y después `backend/.env`, si existe; este último puede
sobrescribir valores. Conserva el SECRET_KEY privado ya configurado. El callback
es una ruta del frontend, no `/api/v1/auth/google/complete`. En producción usa
HTTPS y registra el dominio y callback exactos, con reescritura SPA.

Desde Git Bash, en la raíz, reinicia ambos procesos:

```bash
./iniciar.cmd -Detener
./iniciar.cmd
```

Diagnóstico sin revelar secretos:

```bash
./.runtime.local/python/python.exe backend/scripts/verificar_google_oauth.py
```

Después prueba consentimiento oficial, retorno al mismo formulario, registro,
dashboard, logout y acceso por correo y contraseña. Google no interviene en este
último acceso. No se puede completar el consentimiento real con claves vacías.

## Archivos y pruebas

Backend: `controllers/google_auth_controller.py`, `dto/auth_dto.py`, `main.py`,
`services/google_auth_service.py` y `tests/test_google_auth.py`, bajo `backend/app`
salvo las pruebas bajo `backend/tests`.

Frontend: `features/auth/{LoginPage,RegistroPage,GoogleCallbackPage,AuthLayout}.tsx`,
`features/auth/googleAuth.ts`, pruebas de LoginPage y RegistroPage, `index.css`,
`e2e/auth.spec.ts` y `playwright.config.ts`. Los estilos oscuros nuevos se limitan
a las páginas de autenticación. No se modificaron inventario, sensores, Saiki ni
AutoGluon. No se instalaron dependencias adicionales en esta corrección.

Validación ejecutada:

- Backend: **356 pruebas aprobadas, 3 omitidas y 26 subpruebas aprobadas**.
- Frontend: **48 pruebas aprobadas**, en 15 archivos.
- Instancia habitual reiniciada: Edge comprobó `localhost:5173/login` sin Google,
  registro completo con botón final bloqueado y backend `/health` con HTTP 200.
- Playwright en Edge: **8 escenarios aprobados**, escritorio y móvil, con FastAPI,
  Vite y MongoDB real en base temporal; Google y SMTP simulados.
- Se comprobaron orden del formulario, ausencia del botón Google en login,
  mostrar/ocultar contraseñas, bloqueo sin verificar, cancelación, conservación
  de datos, rechazo de tickets falsificados, duplicados, dashboard, recarga,
  logout, fallo SMTP, roles antiguos y aislamiento entre empresas.
- Compilación TypeScript y Vite aprobada; persiste el aviso previo de tamaño
  de un bundle del visualizador de audio, fuera de este cambio.

Evidencias locales: `artifacts/auth-single-form-regression.xml`,
`artifacts/auth-browser.local/results.json`, `registro-unico-desktop.png` y
`registro-unico-mobile.png` en esa misma carpeta. Las zonas magenta de las
capturas son máscaras de privacidad de Playwright sobre las contraseñas.

**Pendiente:** consentimiento con Google real y recepción SMTP real. Las pruebas
simuladas no demuestran que las credenciales externas estén autorizadas.

Referencia de configuración: https://developers.google.com/identity/openid-connect/openid-connect
