from typing import List

from fastapi import APIRouter, Depends, status

from app.dependencies.dependencies import (
    require_empresa_u_operario,
    require_operario
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.recepcion_mercaderia_dto import (
    RecepcionMercaderiaCreate,
    RecepcionMercaderiaResponse
)

from app.repositories.orden_reposicion_repository import (
    OrdenReposicionRepository
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.recepcion_mercaderia_service import (
    RecepcionMercaderiaService
)


router = APIRouter(
    prefix="/recepciones",
    tags=["Recepciones de Mercaderia"]
)

service = RecepcionMercaderiaService()


# ============================================================
# REGISTRAR RECEPCION (solo OPERARIO, órdenes de su almacén)
# ============================================================

@router.post(
    "",
    response_model=RecepcionMercaderiaResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear(
    data: RecepcionMercaderiaCreate,
    user: UsuarioActual = Depends(require_operario)
):
    return await service.crear(data, user)


# ============================================================
# LISTAR
#
# EMPRESA  -> recepciones de sus órdenes
# OPERARIO -> recepciones de las órdenes de su almacén
# ============================================================

@router.get(
    "",
    response_model=List[RecepcionMercaderiaResponse]
)
async def obtener_todos(
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    ordenes = await (
        OrdenReposicionRepository()
        .obtener_por_empresa(user.id_empresa)
    )

    return await service.obtener_por_ordenes(
        [
            orden["id_orden_reposicion"]
            for orden in ordenes
            if (
                user.es_empresa
                or orden.get("id_almacen") == user.id_almacen
            )
        ]
    )


@router.get(
    "/orden/{id_orden}",
    response_model=List[RecepcionMercaderiaResponse]
)
async def obtener_por_orden(
    id_orden: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.obtener_por_orden(id_orden)


@router.get(
    "/operario/{id_operario}",
    response_model=List[RecepcionMercaderiaResponse]
)
async def obtener_por_operario(
    id_operario: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_operario(user, id_operario)

    return await service.obtener_por_operario(
        id_operario
    )


@router.get(
    "/{id_recepcion}",
    response_model=RecepcionMercaderiaResponse
)
async def obtener_por_id(
    id_recepcion: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_recepcion(
        user,
        id_recepcion
    )

    return await service.obtener_por_id(id_recepcion)
