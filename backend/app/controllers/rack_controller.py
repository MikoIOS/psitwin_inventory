from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)

from app.dependencies.dependencies import (
    require_empresa,
    require_empresa_u_operario,
    require_operario
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.rack_dto import (
    RackCreate,
    RackUpdate,
    RackResponse,
    RackDisponibleResponse
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.rack_service import (
    RackService
)


router = APIRouter(
    prefix="/racks",
    tags=["Rack"]
)


service = RackService()


@router.post(
    "",
    response_model=RackResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear_rack(
    data: RackCreate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_zona(
        user,
        data.id_zona
    )

    return await service.crear_rack(
        data
    )


@router.get(
    "",
    response_model=list[
        RackResponse
    ]
)
async def obtener_racks(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await service.obtener_racks(
        await AccesoService.ids_zonas(
            user
        )
    )


# ============================================================
# RACKS DISPONIBLES PARA UN PRODUCTO
#
# GET /racks/disponibles?id_almacen=&id_producto=&cantidad=
#
# Racks DISPONIBLES del almacén donde caben `cantidad`
# unidades del producto (kg libres y temperatura).
#
# IMPORTANTE: antes de /{id_rack}
# OPERARIO: id_almacen se fuerza al suyo.
# ============================================================

@router.get(
    "/disponibles",
    response_model=list[
        RackDisponibleResponse
    ]
)
async def obtener_racks_disponibles(
    id_almacen: Optional[str] = Query(
        default=None
    ),
    id_producto: Optional[str] = Query(
        default=None
    ),
    cantidad: float = Query(
        default=0,
        ge=0
    ),
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    if user.es_operario:

        id_almacen = user.id_almacen

        if not id_almacen:
            return []

    elif not id_almacen:

        raise HTTPException(
            status_code=422,
            detail=(
                "Debe indicar id_almacen"
            )
        )

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    producto = None

    if id_producto:

        producto = await (
            AccesoService.verificar_producto(
                user,
                id_producto
            )
        )

    return await service.obtener_disponibles(
        id_almacen,
        producto,
        cantidad
    )


@router.get(
    "/zona/{id_zona}",
    response_model=list[
        RackResponse
    ]
)
async def obtener_racks_zona(
    id_zona: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_zona(
        user,
        id_zona
    )

    return await service.obtener_racks_zona(
        id_zona
    )


@router.get(
    "/{id_rack}",
    response_model=RackResponse
)
async def obtener_rack(
    id_rack: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await service.obtener_rack(
        id_rack
    )


@router.put(
    "/{id_rack}",
    response_model=RackResponse
)
async def actualizar_rack(
    id_rack: str,
    data: RackUpdate,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):
    if not user.es_empresa and 'max_niveles' in data.model_fields_set:
        raise HTTPException(403, 'Solo la empresa puede modificar el máximo de niveles')

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await service.actualizar_rack(
        id_rack,
        data
    )


@router.delete(
    "/{id_rack}"
)
async def eliminar_rack(
    id_rack: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await service.eliminar_rack(
        id_rack
    )
