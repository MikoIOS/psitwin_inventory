from typing import List

from fastapi import APIRouter, Depends, status

from app.dependencies.dependencies import (
    require_empresa_u_operario,
    require_operario
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.detalle_recepcion_dto import (
    DetalleRecepcionCreate,
    DetalleRecepcionResponse
)

from app.dto.recepcion_mercaderia_dto import (
    ResolverEvaluacion
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.detalle_recepcion_service import (
    DetalleRecepcionService
)


router = APIRouter(
    tags=["Detalles de Recepcion"]
)

service = DetalleRecepcionService()


async def _verificar_detalle(
    user: UsuarioActual,
    id_detalle: str
):
    detalle = await service.obtener_por_id(
        id_detalle
    )

    await AccesoService.verificar_recepcion(
        user,
        detalle["id_recepcion"]
    )

    return detalle


# ============================================================
# INGRESO A INVENTARIO (solo OPERARIO)
# ============================================================

@router.post(
    "/recepciones/{id_recepcion}/detalles",
    response_model=DetalleRecepcionResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear(
    id_recepcion: str,
    data: DetalleRecepcionCreate,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_recepcion(
        user,
        id_recepcion
    )

    await AccesoService.verificar_inventario(
        user,
        data.id_inventario
    )

    if data.id_detalle_inventario:
        await AccesoService.verificar_detalle_inventario(user, data.id_detalle_inventario)

    return await service.crear(
        id_recepcion,
        data,
        user
    )


@router.get(
    "/recepciones/{id_recepcion}/detalles",
    response_model=List[DetalleRecepcionResponse]
)
async def obtener_por_recepcion(
    id_recepcion: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_recepcion(
        user,
        id_recepcion
    )

    return await service.obtener_por_recepcion(
        id_recepcion
    )


@router.get(
    "/detalles-recepcion/{id_detalle}",
    response_model=DetalleRecepcionResponse
)
async def obtener_por_id(
    id_detalle: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return await _verificar_detalle(user, id_detalle)


# ============================================================
# RESOLVER EVALUACION (solo OPERARIO)
# ============================================================

@router.post(
    "/detalles-recepcion/{id_detalle}/resolver",
    response_model=DetalleRecepcionResponse
)
async def resolver_evaluacion(
    id_detalle: str,
    data: ResolverEvaluacion,
    user: UsuarioActual = Depends(require_operario)
):
    await _verificar_detalle(user, id_detalle)

    if data.id_inventario:

        await AccesoService.verificar_inventario(
            user,
            data.id_inventario
        )

    if data.id_detalle_inventario:
        await AccesoService.verificar_detalle_inventario(user, data.id_detalle_inventario)

    return await service.resolver_evaluacion(
        id_detalle,
        data,
        user
    )
