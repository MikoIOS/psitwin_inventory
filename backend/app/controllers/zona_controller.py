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

from app.dto.zona_dto import (
    ZonaCreate,
    ZonaUpdate,
    ZonaResponse
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.zona_service import (
    ZonaService
)


router = APIRouter(
    prefix="/zonas",
    tags=[
        "Zonas"
    ]
)


# ============================================================
# CREAR (EMPRESA)
# ============================================================

@router.post(
    "",
    response_model=ZonaResponse,
    status_code=(
        status.HTTP_201_CREATED
    )
)
async def crear_zona(
    data: ZonaCreate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_almacen(
        user,
        data.id_almacen
    )

    return await (
        ZonaService.crear(
            data
        )
    )


# ============================================================
# OBTENER TODAS (DEL ALCANCE DEL USUARIO)
# ============================================================

@router.get(
    "",
    response_model=List[
        ZonaResponse
    ]
)
async def obtener_zonas(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    zonas = await (
        AccesoService.zonas_visibles(
            user
        )
    )

    return [
        await ZonaService.normalizar_zona(
            zona
        )
        for zona in zonas
    ]


# ============================================================
# OBTENER POR ALMACEN
#
# Debe ir antes de /{id_zona}
# ============================================================

@router.get(
    "/almacen/{id_almacen}",
    response_model=List[
        ZonaResponse
    ]
)
async def obtener_zonas_por_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    return await (
        ZonaService.obtener_por_almacen(
            id_almacen
        )
    )


# ============================================================
# OBTENER POR ID
# ============================================================

@router.get(
    "/{id_zona}",
    response_model=ZonaResponse
)
async def obtener_zona(
    id_zona: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_zona(
        user,
        id_zona
    )

    return await (
        ZonaService.obtener_por_id(
            id_zona
        )
    )


# ============================================================
# ACTUALIZAR (EMPRESA)
# ============================================================

@router.put(
    "/{id_zona}",
    response_model=ZonaResponse
)
async def actualizar_zona(
    id_zona: str,
    data: ZonaUpdate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_zona(
        user,
        id_zona
    )

    return await (
        ZonaService.actualizar(
            id_zona,
            data
        )
    )


# ============================================================
# ELIMINAR (EMPRESA)
# ============================================================

@router.delete(
    "/{id_zona}",
    status_code=(
        status.HTTP_200_OK
    )
)
async def eliminar_zona(
    id_zona: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_zona(
        user,
        id_zona
    )

    return await (
        ZonaService.eliminar(
            id_zona
        )
    )
