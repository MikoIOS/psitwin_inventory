from typing import List

from fastapi import (
    APIRouter,
    Depends,
    status
)

from app.dependencies.dependencies import (
    require_empresa,
    require_empresa_u_operario
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.almacen_dto import (
    AlmacenCreate,
    AlmacenUpdate,
    AlmacenResponse
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.almacen_service import (
    AlmacenService
)


router = APIRouter(
    prefix="/almacenes",
    tags=[
        "Almacenes"
    ]
)


# ============================================================
# LISTA VISIBLE
#
# EMPRESA  -> sus almacenes
# OPERARIO -> solo su almacén
# ============================================================

async def _almacenes_visibles(
    user: UsuarioActual
):

    if user.es_operario:

        if not user.id_almacen:
            return []

        return [
            await AccesoService.verificar_almacen(
                user,
                user.id_almacen
            )
        ]

    return await (
        AlmacenService
        .obtener_por_empresa(
            user.id_empresa
        )
    )


# ============================================================
# CREAR (EMPRESA)
#
# POST /api/v1/almacenes
#
# id_empresa se toma del token.
# ============================================================

@router.post(
    "",
    response_model=AlmacenResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Crear almacén"
)
async def crear_almacen(
    data: AlmacenCreate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    data.id_empresa = user.id_empresa

    return await (
        AlmacenService.crear(
            data
        )
    )


# ============================================================
# OBTENER TODOS
#
# GET /api/v1/almacenes
# ============================================================

@router.get(
    "",
    response_model=List[
        AlmacenResponse
    ],
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Obtener almacenes"
)
async def obtener_almacenes(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _almacenes_visibles(
        user
    )


# ============================================================
# OBTENER POR EMPRESA
#
# IMPORTANTE:
# Esta ruta debe ir ANTES de /{id_almacen}
#
# GET /api/v1/almacenes/empresa/{id_empresa}
# ============================================================

@router.get(
    "/empresa/{id_empresa}",
    response_model=List[
        AlmacenResponse
    ],
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Obtener almacenes por empresa"
    )
)
async def obtener_almacenes_por_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    AccesoService.verificar_empresa(
        user,
        id_empresa
    )

    return await _almacenes_visibles(
        user
    )


# ============================================================
# OBTENER POR ID
#
# GET /api/v1/almacenes/{id_almacen}
# ============================================================

@router.get(
    "/{id_almacen}",
    response_model=AlmacenResponse,
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Obtener almacén por ID"
)
async def obtener_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await (
        AccesoService.verificar_almacen(
            user,
            id_almacen
        )
    )


# ============================================================
# ACTUALIZAR (EMPRESA)
#
# PUT /api/v1/almacenes/{id_almacen}
# ============================================================

@router.put(
    "/{id_almacen}",
    response_model=AlmacenResponse,
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Actualizar almacén"
)
async def actualizar_almacen(
    id_almacen: str,
    data: AlmacenUpdate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    return await (
        AlmacenService.actualizar(
            id_almacen,
            data
        )
    )


# ============================================================
# ELIMINAR (EMPRESA)
#
# DELETE /api/v1/almacenes/{id_almacen}
# ============================================================

@router.delete(
    "/{id_almacen}",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Eliminar almacén"
)
async def eliminar_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    return await (
        AlmacenService.eliminar(
            id_almacen
        )
    )
