# app/main.py

from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from app.utils.log_redaction import install_auth_log_redaction

install_auth_log_redaction()

from fastapi import (
    Depends,
    FastAPI,
    Request
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from fastapi.responses import (
    JSONResponse
)

from app.config.settings import (
    get_settings
)

from app.dependencies.dependencies import (
    PasswordChangeRequired,
    get_usuario_activo,
    require_empresa
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.services.acceso_service import (
    AccesoService
)

from app.database.mongodb import (
    connect_to_mongo,
    close_mongo_connection,
    get_database
)


# ============================================================
# CONTROLLERS
# ============================================================

from app.controllers.empresa_controller import (
    router as empresa_router
)

from app.controllers.almacen_controller import (
    router as almacen_router
)

from app.controllers.zona_controller import (
    router as zona_router
)

from app.controllers.rack_controller import (
    router as rack_router
)

from app.controllers.producto_controller import (
    router as producto_router
)

from app.controllers.inventario_controller import (
    router as inventario_router
)

from app.controllers.operario_controller import (
    router as operario_router
)

from app.controllers.movimiento_controller import (
    router as movimiento_router
)

from app.controllers.proveedor_controller import (
    router as proveedor_router
)

from app.controllers.orden_reposicion_controller import (
    router as orden_reposicion_router
)

from app.controllers.detalle_reposicion_controller import (
    router as detalle_reposicion_router
)

from app.controllers.recepcion_mercaderia_controller import (
    router as recepcion_mercaderia_router
)

from app.controllers.detalle_recepcion_controller import (
    router as detalle_recepcion_router
)

from app.controllers.alerta_controller import (
    router as alerta_router
)

from app.controllers.recomendacion_controller import (
    router as recomendacion_router
)

from app.controllers.inventory_risk_controller import (
    router as inventory_risk_router
)

from app.controllers.dispositivo_controller import (
    router as dispositivo_router
)

from app.controllers.monitoreo_ws_controller import (
    router as monitoreo_ws_router
)

from app.services.sensores.monitoreo_service import (
    monitoreo
)

from app.controllers.saiki_controller import (
    router as saiki_router
)
from app.controllers.analisis_controller import router as analisis_router

# NUEVO:
# Controller temporal para probar el historial
# de demanda que posteriormente utilizará ML.
from app.controllers.forecast_controller import (
    router as forecast_router
)


# ============================================================
# SETTINGS
# ============================================================

settings = get_settings()


# ============================================================
# LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI
):

    # --------------------------------------------------------
    # INICIO DE LA APLICACION
    # --------------------------------------------------------

    await connect_to_mongo()

    # Sensores: consumidor MQTT + motor de alertas.
    # Si el broker no está, reintenta en segundo plano.
    await monitoreo.iniciar()

    yield

    await monitoreo.detener()
    from app.services.local_voice_service import voice_service
    await voice_service.close()

    # --------------------------------------------------------
    # CIERRE DE LA APLICACION
    # --------------------------------------------------------

    await close_mongo_connection()


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(

    title=
        settings.app_name,

    version=
        "2.0.0",

    description=(
        "API de gestión inteligente de inventario, "
        "almacenes, movimientos, reposición, "
        "recepción de mercadería, alertas, "
        "recomendaciones, evaluación de riesgo "
        "y predicción de demanda para PsiTwin."
    ),

    lifespan=
        lifespan
)

@app.exception_handler(RequestValidationError)
async def private_auth_validation_errors(request: Request, exc: RequestValidationError):
    if '/auth/' in request.url.path or request.url.path.endswith('/password'):
        # Pydantic's default "input" may contain an entire password-bearing body.
        return JSONResponse(status_code=422, content={'detail': [
            {key: item[key] for key in ('loc', 'msg', 'type') if key in item}
            for item in exc.errors()
        ]})
    return await request_validation_exception_handler(request, exc)

# Google OAuth routes retired. Existing identity fields remain untouched.


# ============================================================
# CORS
#
# Orígenes configurables: CORS_ORIGINS en .env
# (separados por comas). Default: http://localhost:5173
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=
        settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# OPERARIO CON CONTRASEÑA TEMPORAL
#
# 403 {"detail": "...", "code": "PASSWORD_CHANGE_REQUIRED"}
# ============================================================

@app.exception_handler(
    PasswordChangeRequired
)
async def password_change_required_handler(
    request: Request,
    exc: PasswordChangeRequired
):

    return JSONResponse(
        status_code=403,
        content={
            "detail":
                exc.detail,
            "code":
                exc.code
        }
    )


# ============================================================
# PROTECCION GLOBAL
#
# Todo /api/v1/* exige token salvo auth/login y
# auth/register (router de empresa, que protege
# /empresas/me por endpoint). Cada controller aplica
# además el rol y el aislamiento por empresa.
#
# Excepciones al bloqueo por contraseña temporal:
# GET /auth/me y PATCH /auth/me/password.
# ============================================================

PROTEGIDO = [
    Depends(get_usuario_activo)
]

# ------------------------------------------------------------
# FORECAST: solo EMPRESA y solo sobre inventarios propios.
#
# Se aplica como dependencia del router para no tocar
# forecast_controller: valida {id_inventario} de la ruta.
# ------------------------------------------------------------

async def verificar_forecast(
    request: Request,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    id_inventario = request.path_params.get(
        "id_inventario"
    )

    if id_inventario:

        await AccesoService.verificar_inventario(
            user,
            id_inventario
        )


FORECAST = [
    Depends(verificar_forecast)
]


# ============================================================
# ROOT
#
# GET /
# ============================================================

@app.get(
    "/",
    tags=["Sistema"]
)
async def root():

    return {

        "mensaje":
            "PsiTwin Inventory API funcionando",

        "version":
            "2.0.0",

        "modulos": [

            "Empresa",
            "Almacen",
            "Zona",
            "Rack",
            "Producto",
            "Inventario",
            "DetalleInventario",
            "Operario",
            "Movimiento",

            "Proveedor",
            "OrdenReposicion",
            "DetalleReposicion",
            "RecepcionMercaderia",
            "DetalleRecepcion",

            "Alertas",
            "Recomendaciones",

            "InventoryRisk",

            "Forecast"
        ]
    }


# ============================================================
# HEALTH
#
# GET /health
#
# Comprueba:
#
# FastAPI
# +
# MongoDB
# ============================================================

@app.get(
    "/health",
    tags=["Sistema"],
    summary="Health check"
)
async def health():

    try:

        database = (
            get_database()
        )

        await database.command(
            "ping"
        )

        return {

            "status":
                "healthy",

            "api":
                "ok",

            "database":
                "ok",

            "database_name":
                settings.mongodb_database,

            "version":
                "2.0.0"
        }

    except Exception as exc:

        return {

            "status":
                "unhealthy",

            "api":
                "ok",

            "database":
                "error",

            "detail":
                str(exc),

            "version":
                "2.0.0"
        }


# ============================================================
# ARQUITECTURA GENERAL
# ============================================================
#
# EMPRESA
#   ↓
# ALMACEN
#   ↓
# ZONA
#   ↓
# RACK
#
#
# PRODUCTO
#   ↓
# INVENTARIO
#   ↓
# MOVIMIENTO
#
#
# PROVEEDOR
#   ↓
# ORDEN REPOSICION
#   ↓
# DETALLE REPOSICION
#   ↓
# RECEPCION MERCADERIA
#   ↓
# DETALLE RECEPCION
#   ↓
# MOVIMIENTO AUTOMATICO
#   ↓
# INVENTARIO
#
#
# ============================================================
# CAPA DE INTELIGENCIA
# ============================================================
#
# MOVIMIENTOS
#      ↓
# DEMAND HISTORY
#      ↓
# CALENDARIO
#      ↓
# AUTOGLUON
# D+1 ... D+90
#      ↓
# FORECAST
#      ↓
# INVENTORY RISK
#      ↓
# ALERTA
#      ↓
# RECOMENDACION
#      ↓
# LLM
#
# ============================================================


# ============================================================
# EMPRESA
# ============================================================

app.include_router(
    empresa_router,
    prefix=settings.api_prefix
)


# ============================================================
# ALMACEN
# ============================================================

app.include_router(
    almacen_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# ZONA
# ============================================================

app.include_router(
    zona_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# RACK
# ============================================================

app.include_router(
    rack_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# PRODUCTO
# ============================================================

app.include_router(
    producto_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# INVENTARIO
# ============================================================

app.include_router(
    inventario_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# OPERARIO
# ============================================================

app.include_router(
    operario_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# MOVIMIENTO
# ============================================================

app.include_router(
    movimiento_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# PROVEEDOR
# ============================================================

app.include_router(
    proveedor_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# ORDEN REPOSICION
# ============================================================

app.include_router(
    orden_reposicion_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# DETALLE REPOSICION
# ============================================================

app.include_router(
    detalle_reposicion_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# RECEPCION MERCADERIA
# ============================================================

app.include_router(
    recepcion_mercaderia_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# DETALLE RECEPCION
# ============================================================

app.include_router(
    detalle_recepcion_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# ALERTAS
# ============================================================

app.include_router(
    alerta_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# RECOMENDACIONES
# ============================================================

app.include_router(
    recomendacion_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# INVENTORY RISK
# ============================================================

app.include_router(
    inventory_risk_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)


# ============================================================
# FORECAST
#
# Movimiento -> Historial completo -> Calendario
# -> AutoGluon -> D+1 ... D+90
#
# Solo EMPRESA, sobre inventarios propios.
# ============================================================

app.include_router(
    forecast_router,
    prefix=settings.api_prefix,
    dependencies=FORECAST
)

# Saiki: solo EMPRESA (lo exige cada endpoint del controller).
app.include_router(
    saiki_router,
    prefix=settings.api_prefix
)

from app.controllers.local_voice_controller import router as local_voice_router
app.include_router(local_voice_router, prefix=settings.api_prefix)

from app.controllers.abastecimiento_controller import router as abastecimiento_router
app.include_router(abastecimiento_router, prefix=settings.api_prefix, dependencies=PROTEGIDO)

app.include_router(analisis_router, prefix=settings.api_prefix, dependencies=PROTEGIDO)

from app.controllers.detalle_inventario_controller import router as detalle_inventario_router
app.include_router(detalle_inventario_router, prefix=settings.api_prefix, dependencies=PROTEGIDO)

# ============================================================
# DISPOSITIVOS / SENSORES
#
# REST con token obligatorio. El WebSocket se autentica
# con el JWT en la query (?token=), por eso va sin la
# dependencia HTTP del router.
# ============================================================

app.include_router(
    dispositivo_router,
    prefix=settings.api_prefix,
    dependencies=PROTEGIDO
)

app.include_router(
    monitoreo_ws_router,
    prefix=settings.api_prefix
)

from app.controllers.inventario_consulta_controller import router as inventario_consulta_router
app.include_router(inventario_consulta_router, prefix=settings.api_prefix, dependencies=PROTEGIDO)
