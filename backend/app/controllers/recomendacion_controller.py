from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.dependencies import (
    require_empresa,
    require_empresa_u_operario,
    require_operario
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.services.acceso_service import (
    AccesoService
)

from pydantic import (
    BaseModel,
    Field
)

from app.dto.recomendacion_dto import (
    RecomendacionCreate,
    RecomendacionResponse,
    RecomendacionEstadoUpdate,
        EstadoRecomendacion,
        EmpresaAprobacionRequest,
        EmpresaCambiosRequest,
        EmpresaRechazoRequest,
        PropuestaRecomendacionUpdate,
)

from app.services.recomendacion_service import (
    RecomendacionService
)


# ============================================================
# REQUEST PARA CONVERTIR RECOMENDACION EN ORDEN
# ============================================================

class CrearOrdenDesdeRecomendacionRequest(
    BaseModel
):

    id_proveedor: str

    costo_unitario: float = Field(
        ge=0
    )

    fecha_estimada_recepcion: Optional[
        datetime
    ] = None


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/recomendaciones",
    tags=["Recomendaciones"]
)

service = RecomendacionService()


# ============================================================
# ACCESO
#
# EMPRESA  -> recomendaciones de su empresa; decide
#             (aprobar / solicitar cambios / rechazar).
# OPERARIO -> lee las de su almacén, valida y
#             actualiza la propuesta.
# PROVEEDOR -> sin acceso.
# ============================================================

async def _verificar(
    user: UsuarioActual,
    id_recomendacion: str
):
    recomendacion = await service.obtener(
        id_recomendacion
    )

    if recomendacion.get("id_empresa") != user.id_empresa:
        raise HTTPException(
            status_code=404,
            detail="Recomendación no encontrada"
        )

    if (
        user.es_operario
        and recomendacion.get("id_almacen")
        != user.id_almacen
    ):
        raise HTTPException(
            status_code=403,
            detail="No tiene acceso a esta recomendación"
        )

    return recomendacion


# ============================================================
# CREAR RECOMENDACION
# ============================================================

@router.post(
    "",
    response_model=RecomendacionResponse,
    status_code=201
)
async def crear_recomendacion(
    data: RecomendacionCreate,
    user: UsuarioActual = Depends(require_empresa)
):

    data.id_empresa = user.id_empresa

    await AccesoService.verificar_almacen(
        user,
        data.id_almacen
    )

    return await service.crear(
        data
    )


# ============================================================
# LISTAR
# ============================================================

@router.get(
    "",
    response_model=List[
        RecomendacionResponse
    ]
)
async def listar_recomendaciones(
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    if user.es_operario:

        if not user.id_almacen:
            return []

        return await service.listar_por_almacen(
            user.id_almacen
        )

    return await service.listar_por_empresa(
        user.id_empresa
    )


# ============================================================
# POR EMPRESA
# ============================================================

@router.get(
    "/empresa/{id_empresa}",
    response_model=List[
        RecomendacionResponse
    ]
)
async def listar_recomendaciones_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa)
):

    AccesoService.verificar_empresa(
        user,
        id_empresa
    )

    return await service.listar_por_empresa(
        id_empresa
    )


# ============================================================
# POR ALMACEN
# ============================================================

@router.get(
    "/almacen/{id_almacen}",
    response_model=List[
        RecomendacionResponse
    ]
)
async def listar_recomendaciones_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    return await service.listar_por_almacen(
        id_almacen
    )


# ============================================================
# POR PRODUCTO
# ============================================================

@router.get(
    "/producto/{id_producto}",
    response_model=List[
        RecomendacionResponse
    ]
)
async def listar_recomendaciones_producto(
    id_producto: str,
    user: UsuarioActual = Depends(require_empresa)
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    return AccesoService.filtrar_empresa(
        user,
        await service.listar_por_producto(
            id_producto
        )
    )


# ============================================================
# POR INVENTARIO
# ============================================================

@router.get(
    "/inventario/{id_inventario}",
    response_model=List[
        RecomendacionResponse
    ]
)
async def listar_recomendaciones_inventario(
    id_inventario: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    await AccesoService.verificar_inventario(
        user,
        id_inventario
    )

    return await service.listar_por_inventario(
        id_inventario
    )


# ============================================================
# CREAR ORDEN DESDE RECOMENDACION
#
# IMPORTANTE:
# Debe estar antes de /{id_recomendacion}
# ============================================================

@router.post(
    "/{id_recomendacion}/crear-orden",
    status_code=201
)
async def crear_orden_desde_recomendacion(
    id_recomendacion: str,
    data: CrearOrdenDesdeRecomendacionRequest,
    user: UsuarioActual = Depends(require_empresa)
):

    await _verificar(user, id_recomendacion)

    await AccesoService.verificar_proveedor(
        user,
        data.id_proveedor
    )

    return (
        await service
        .crear_orden_desde_recomendacion(

            id_recomendacion=
                id_recomendacion,

            id_proveedor=
                data.id_proveedor,

            costo_unitario=
                data.costo_unitario,

            fecha_estimada_recepcion=
                data.fecha_estimada_recepcion
        )
    )


# ============================================================
# OBTENER RECOMENDACION
# ============================================================

@router.get(
    "/{id_recomendacion}",
    response_model=RecomendacionResponse
)
async def obtener_recomendacion(
    id_recomendacion: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    return await _verificar(
        user,
        id_recomendacion
    )


# ============================================================
# CAMBIAR ESTADO
# ============================================================

@router.patch(
    "/{id_recomendacion}/estado",
    response_model=RecomendacionResponse
)
async def cambiar_estado_recomendacion(
    id_recomendacion: str,
    data: RecomendacionEstadoUpdate,
    user: UsuarioActual = Depends(require_empresa)
):

    await _verificar(user, id_recomendacion)

    return await service.cambiar_estado(
        id_recomendacion,
        data
    )


@router.patch(
    "/{id_recomendacion}/validar-operario",
    response_model=RecomendacionResponse
)
async def validar_por_operario(
    id_recomendacion: str,
    user: UsuarioActual = Depends(require_operario)
):
    # id_operario: siempre el del token
    await _verificar(user, id_recomendacion)
    id_operario = user.id_operario
    return await service.cambiar_estado(
        id_recomendacion,
        RecomendacionEstadoUpdate(
            estado=EstadoRecomendacion.VALIDADA_OPERARIO
        ),
        id_operario
    )


@router.patch(
    "/{id_recomendacion}/aprobar-empresa",
)
async def aprobar_por_empresa(
    id_recomendacion: str,
    data: EmpresaAprobacionRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await _verificar(user, id_recomendacion)
    await AccesoService.verificar_proveedor(user, data.id_proveedor)
    data.id_empresa = user.id_empresa
    return await service.aprobar_por_empresa(
        id_recomendacion,
        data,
    )


@router.patch(
    "/{id_recomendacion}/solicitar-cambios",
    response_model=RecomendacionResponse,
)
async def solicitar_cambios(
    id_recomendacion: str,
    data: EmpresaCambiosRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await _verificar(user, id_recomendacion)
    data.id_empresa = user.id_empresa
    return await service.solicitar_cambios(id_recomendacion, data)


@router.patch(
    "/{id_recomendacion}/rechazar-empresa",
    response_model=RecomendacionResponse,
)
async def rechazar_por_empresa(
    id_recomendacion: str,
    data: EmpresaRechazoRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await _verificar(user, id_recomendacion)
    data.id_empresa = user.id_empresa
    return await service.rechazar_por_empresa(id_recomendacion, data)


@router.patch(
    "/{id_recomendacion}/actualizar-propuesta",
    response_model=RecomendacionResponse,
)
async def actualizar_propuesta(
    id_recomendacion: str,
    data: PropuestaRecomendacionUpdate,
    user: UsuarioActual = Depends(require_operario)
):
    # id_operario: siempre el del token
    await _verificar(user, id_recomendacion)
    id_operario = user.id_operario
    return await service.actualizar_propuesta(
        id_recomendacion,
        data,
        id_operario,
    )