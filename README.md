# PsiTwin Inventory

Evaluación para tienda: [informe de pruebas](docs/INFORME_PRUEBAS_INTEGRALES_PSITWIN.md),
[guía de visita](docs/GUIA_VISITA_TIENDA_PSITWIN.md),
[checklist](docs/CHECKLIST_DATOS_TIENDA.md),
[entrevista](docs/PREGUNTAS_DUENO_TIENDA.md) y
[plantillas Excel/CSV](docs/plantillas_tienda/LEEME.md).
El bloqueo de inventario detectado en la evaluacion ya fue corregido: consulta
[la correccion y pruebas](docs/CORRECCION_INVENTARIO_FRONTEND.md). Los demas
hallazgos pendientes permanecen documentados en el informe.

Registro vigente: Gmail y contraseña de PsiTwin, activación por enlace de correo
y bienvenida mediante Gmail SMTP, sin Google OAuth. Consulta la
[configuración y pruebas](docs/REGISTRO_GMAIL_SMTP.md). En Git Bash inicia con
`./iniciar.cmd`.

Sistema de inventario inteligente para equipos de frío: backend (FastAPI + MongoDB + MQTT) y frontend (React + Vite).

## Estructura

```
.
├── backend/     API FastAPI, modelos ML, sensores MQTT, tests
├── frontend/    App React + TypeScript (Vite)
├── docs/        Especificaciones, contratos API y documentación de Saiki/sensores
└── README.md
```

## Actualización de autenticación, sensores y Saiki

Se integraron los cambios locales en `backend/` y `frontend/`. Consulta la
[guía de configuración y voz local](docs/ACTUALIZACION_SISTEMA_VOZ_LOCAL.md) y el
[informe de integración](docs/INTEGRACION_ACTUALIZACION.md).

En Windows, desde la raíz, ejecuta `.\iniciar.cmd`. Para iniciar por separado:

```powershell
# Terminal del backend; MongoDB debe estar disponible.
cd backend
..\.venv\Scripts\python.exe -m app.run --host 127.0.0.1 --port 8000
# Si .venv apunta a un Python eliminado:
# ..\.runtime.local\python\python.exe -m app.run --host 127.0.0.1 --port 8000

# Otra terminal, desde la raíz:
npm.cmd --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

Se carga `.env` de la raíz y después `backend/.env`, que tiene prioridad.
Los entornos y modelos existentes en la raíz se reutilizan. El lanzador guarda
logs en `artifacts/run.local/`; `iniciar.cmd -Detener` detiene los procesos que creó.

Pruebas: `npm.cmd --prefix frontend run build` y `npm.cmd --prefix frontend run test:ui`.
Desde `backend/`: `python -m pytest -q`, usando el intérprete del entorno.

## Arranque rápido

Requisitos: Python 3.11+, Node 20+, Docker, MongoDB.

```bash
# 0) Entorno Python (una sola vez, en la raíz del repo)
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

# 1) Servicios
docker start psitwin-mongo
docker start psitwin-mosquitto      # sensores (opcional para trabajar solo con inventario)

# 2) Backend  → http://localhost:8000
cd backend
cp .env.example .env
../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3) Frontend → http://localhost:5173 (Vite reenvía /api al backend)
cd frontend
cp .env.example .env
npm install
npm run dev
```

Pruebas del backend:

```bash
cd backend
../.venv/bin/python -m unittest discover -s tests
```

## Documentación

| Documento | Contenido |
|---|---|
| [`backend/README.md`](backend/README.md) | Roles, autenticación, flujo de reposición, credenciales demo, sensores |
| [`docs/ROLES.md`](docs/ROLES.md) | Contrato de roles backend ↔ frontend |
| [`docs/SENSORES.md`](docs/SENSORES.md) | Contrato de sensores (MQTT, alertas, WebSocket) |
| [`docs/ESPECIFICACION_COMPLETA_PSITWIN.md`](docs/ESPECIFICACION_COMPLETA_PSITWIN.md) | Especificación funcional completa |
| [`docs/`](docs/) | Resto de especificaciones, diccionarios y documentación de Saiki |

## Credenciales demo

| Rol | Correo | Contraseña |
|---|---|---|
| EMPRESA | demo@psitwin.com | demo123 |
| OPERARIO | operario1@psitwin.com | oper123 |
| PROVEEDOR | proveedor1@psitwin.com | prov123 |

Más detalles en [`backend/README.md`](backend/README.md).

## Despliegue en Render

El [Blueprint](render.yaml) crea la API Docker y el frontend estático con rutas SPA.
Sigue [la guía de Render y GitHub](docs/RENDER.md) para configurar MongoDB Atlas,
las URLs públicas y publicar con un único autor.

## Despliegue en VPS

Con Docker instalado en el VPS, ejecuta desde la raíz (sustituye la IP):

```bash
bash scripts/deploy.sh 123.123.123.123
```

Abre `http://123.123.123.123`. Incluye API, frontend, MongoDB, sensores MQTT y Ollama. Consulta [la guía de despliegue](docs/DEPLOYMENT.md) para sensores, voz, correo y HTTPS opcional.
