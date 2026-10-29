> Flujo sustituido: consulta [Registro Gmail por SMTP, sin OAuth](REGISTRO_GMAIL_SMTP.md). Este documento conserva detalles historicos.

> Informe historico: sustituido por [Registro unico Gmail](REGISTRO_UNICO_GMAIL.md). El login actual no ofrece Google y el registro tiene una sola pagina.

# Corrección de registro y autenticación — 27 de octubre de 2026

## Resultado

Se restauró el formulario empresarial a partir del historial Git y se implementó
el orden solicitado: **datos empresariales → Google → contraseña PsiTwin → sesión y dashboard**.
Se reiniciaron los procesos identificados por el lanzador local y se comprobó
con Playwright que `http://localhost:5173/registro` muestra el formulario completo.
El backend habitual respondió 200 en `/health`.

El consentimiento real de Google sigue pendiente: no hay Client ID ni Client Secret
configurados. Las pruebas completas de navegador usaron un proveedor Google
simulado y SMTP capturado, con servicios FastAPI/Vite reales y MongoDB temporal.
No deben presentarse como un consentimiento real ni como recepción real en Gmail.

## Campos y flujo

Se recuperaron nombre de empresa, RUC, sector, teléfono y el atributo de correo;
se conserva nombre del CEO. CEO admite «Carlos», sin apellido; placeholder `Nombre`.
Sector muestra `Alimentos`. El correo lo proporciona Google verificado y aparece
como atributo de solo lectura. La contraseña se solicita después de Google.

1. El formulario valida nombre, CEO, RUC de 11 dígitos, sector y teléfono.
2. `/auth/google/start` conserva el documento empresarial en MongoDB temporal.
   El borrador de la pestaña conserva también los campos para recuperarlos ante
   un error. No se crea empresa ni se solicita contraseña en este paso.
3. Google autentica; el backend valida OIDC y devuelve un ticket de registro de
   corta duración ligado a la pestaña, el correo verificado y la copia empresarial.
4. La pantalla **Crear contraseña de PsiTwin** solicita contraseña nueva y
   confirmación: 8–128 caracteres, coincidencia obligatoria. No solicita Gmail password.
5. **Finalizar registro** valida el ticket y los datos. La copia empresarial
   conservada por el backend tiene prioridad sobre campos alterados en el cliente.
   El documento `empresas` se inserta con `google_sub`, `nombre_ceo` y hash Argon2id.
6. Se establece la sesión, se encola y despacha la bienvenida y se navega a `/`.
   El dashboard puede mostrar una empresa sin almacenes sin fallar ni inventar datos.

En la arquitectura existente, la cuenta empresarial de rol EMPRESA es el acceso
administrador del CEO: `id_empresa` identifica ese acceso, `nombre_ceo` personaliza
el perfil y `google_sub` vincula su identidad. No se creó una colección de usuarios
paralela que duplicase al CEO.

## Login, dashboard y correo

El login ofrece **correo y contraseña de PsiTwin** e **Iniciar sesión con Google**.
Ambos acceden al mismo `id_empresa`. La identidad Google se busca por `sub`; una
coincidencia de correo no basta para apropiarse de una empresa. Las identidades
sin cuenta reciben un ticket para completar registro, no acceso a una empresa ajena.
Un registro repetido de una identidad vinculada se rechaza claramente.

El error anterior de perfil se debía a fechas BSON `datetime` frente a campos de
respuesta que esperaban texto. Se conservó la conversión a ISO del DTO y se probó
de nuevo con fechas BSON reales en creación, actualización y verificación: perfil,
login, recarga y dashboard funcionaron sin respuestas HTTP 500.

Se conserva la plantilla HTML, imágenes optimizadas, escape del nombre y CTA de
`FRONTEND_URL`. La bienvenida usa `psitwin2026@gmail.com`; los ensayos comprobaron
«Carlos» y ausencia de `{{nombre}}`. Un fallo SMTP conserva la empresa y permite
login. La outbox y su reintento existentes mantienen un único envío confirmado.

## Seguridad y configuración

Se mantienen código de autorización, PKCE S256, estado de un solo uso, binding de
pestaña, nonce, firma RS256, audiencia, emisor, expiración, `azp`, correo verificado
y vinculación por `sub`. El secreto OAuth permanece en backend. Los índices únicos
impiden duplicar correo, RUC o identidad Google; el ticket final se consume atómicamente.
Las pruebas incluyen replay, concurrencia, firma y claims inválidos y alteración
de datos empresariales tras Google.

Se detectó que el entorno local usaba la clave JWT de ejemplo. Se generó una clave
privada persistente en `.env`, ignorado por Git. Las sesiones anteriores necesitan
login de nuevo al cargar la configuración nueva. Los logs de Uvicorn ahora ocultan
`token`, `code` y `state` de las cadenas de consulta sin romper su formato estructurado.

La sesión mantiene el mecanismo JWT Bearer existente y su persistencia local del
frontend. Logout limpia la sesión y protege las rutas del navegador. No se cambió
a cookies ni se añadió una lista de revocación de JWT del servidor.

El diagnóstico local confirmó:

- `GOOGLE_CLIENT_ID`: vacío.
- `GOOGLE_CLIENT_SECRET`: vacío.
- Callback: `http://localhost:5173/auth/google/callback`.
- `FRONTEND_URL`: `http://localhost:5173`.
- CORS permite `http://localhost:5173`; el proxy Vite conserva mismo origen.
- La configuración efectiva se carga desde `backend/app/config/settings.py`.
  `.env` de la raíz se lee primero y `backend/.env`, si existe, tiene prioridad.
  El archivo antiguo `app/config/settings.py` no configura el backend actual.

Para comprobarlo sin imprimir secretos:

```powershell
.runtime.local/python/python.exe backend/scripts/verificar_google_oauth.py
```

En Google Cloud Console, crear/configurar el consentimiento y un cliente OAuth
**Aplicación web**. Durante desarrollo agregar el Gmail autorizado como usuario
de prueba. Registrar exactamente el callback anterior como URI de redirección.
Configurar los valores reales en `.env` de la raíz o `backend/.env`:

```dotenv
GOOGLE_CLIENT_ID=ID_REAL_DEL_CLIENTE_WEB
GOOGLE_CLIENT_SECRET=SECRETO_REAL_DEL_CLIENTE_WEB
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
```

No son la contraseña de Gmail ni `SMTP_APP_PASSWORD`. No publicar los valores.
Después de guardarlos, reiniciar con `./iniciar.cmd -Detener` y `./iniciar.cmd`.
La consola externa de Google no se modificó ni se verificó con una cuenta real.

Referencia: [Google OIDC](https://developers.google.com/identity/openid-connect/openid-connect).

## Archivos y endpoints

| Archivos | Cambio |
|---|---|
| `frontend/src/features/auth/RegistroPage.tsx` | Formulario restaurado y pantalla separada de contraseña |
| `googleAuth.ts`, `GoogleCallbackPage.tsx` | Propósito registro/login, borrador y recuperación del documento validado |
| `LoginPage.tsx` | Ambos métodos de acceso |
| `backend/app/controllers/google_auth_controller.py` | Propósito de autorización y contraseña obligatoria solo al finalizar |
| `backend/app/services/google_auth_service.py` | Ticket intermedio; empresa únicamente al finalizar; copia empresarial del servidor |
| `backend/app/utils/log_redaction.py`, `backend/app/main.py` | Ocultación de credenciales de consulta en logs |
| `backend/scripts/verificar_google_oauth.py` | Diagnóstico sin secretos |
| Tests de auth, `frontend/e2e/auth.spec.ts`, `frontend/playwright.config.ts`, `backend/tests/browser_auth_app.py` | Regresión unitaria y navegador con servicios reales aislados |
| `frontend/package.json`, `package-lock.json` | Playwright y comando `test:e2e` |

Se corrigieron rutas existentes bajo `/api/v1`: POST `/auth/google/start`,
`/auth/google/complete`, `/auth/google/register`. Se conservaron login por contraseña,
perfil, vinculación segura y bienvenida. No se añadieron endpoints de prueba a la
aplicación productiva: el servidor de pruebas exige un marcador de entorno y usa
su propia base temporal.

No se modificaron AutoGluon, Saiki, sensores, inventario ni sus pantallas.

## Pruebas realizadas y pendientes

- **2 escenarios Playwright aprobados en Edge headless**, con FastAPI y Vite
  arrancados en puertos 18080 y 15173 y una base MongoDB temporal eliminada al terminar.
- Formulario completo, nombre simple, sugerencia Alimentos, inicio OAuth, ausencia
  de empresa antes de finalizar, datos conservados tras redirección/recarga,
  contraseña segura, creación en MongoDB, bienvenida capturada y Argon2id comprobados.
- Login por contraseña y Google acceden a la misma empresa, sin duplicados ni
  segunda bienvenida. Se comprobó rechazo de registro repetido.
- Perfil con BSON, dashboard, recarga, logout, rutas privadas y fallo SMTP probados.
- **47 pruebas frontend aprobadas**; TypeScript y build aprobados.
- **352 pruebas backend aprobadas**, 3 omitidas y 26 subpruebas aprobadas.
- **18 pruebas específicas de Google/auth** aprobadas después del ajuste de logs.
- Smoke del servidor habitual: formulario visible en `localhost:5173` y health 200.

Evidencia: `artifacts/auth-browser.local/results.json`, captura
`artifacts/auth-browser.local/registro-restaurado.png` y
`artifacts/auth-final-regression.xml`.

Repetir las pruebas de navegador en este equipo:

```powershell
npm.cmd --prefix frontend run test:e2e
```

Playwright usa Edge instalado y un perfil aislado. El proveedor de Google y la
entrega SMTP se simulan únicamente en el servidor de pruebas; la base real no se
usa para crear cuentas de ensayo. El test cubre la red local, frontend, backend,
sesión y persistencia; las pruebas RSA aparte cubren las validaciones OIDC.

Pendientes: consentimiento real con credenciales de desarrollo autorizadas y
recepción/renderizado real en Gmail. Las 3 omisiones backend pertenecen a pruebas
optativas de AutoGluon, MongoDB adicional y Ollama. Se conservan las advertencias
previas de tamaño del visualizador y de versión de Node; no se actualizaron otros
módulos por esos avisos. Durante navegación/recarga aparecieron avisos de cierre
de conexiones WebSocket de Vite; no hubo respuestas HTTP 500 de las APIs del flujo.
