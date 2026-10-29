from fastapi import (
    APIRouter,
    Depends,
    status
)

from app.dependencies.dependencies import (
    require_empresa_u_operario,
    require_operario
)
from app.dependencies.dependencies import require_empresa

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.detalle_inventario_dto import (
    DetalleInventarioCreate,
    DetalleInventarioUpdate,
    DetalleInventarioResponse
)

from app.dto.inventario_dto import InventarioHistorialResponse

from app.services.acceso_service import (
    AccesoService
)

from app.services.detalle_inventario_service import (
    DetalleInventarioService
)


router = APIRouter(
    prefix="/detalles-inventario",
    tags=["Inventario"]
)


service = DetalleInventarioService()


async def _filtrar_alcance(
    user: UsuarioActual,
    inventarios: list
) -> list:

    return AccesoService.filtrar(
        inventarios,
        "id_rack",
        await AccesoService.ids_racks(
            user
        )
    )


# =============================================================
# CREAR INVENTARIO (OPERARIO, racks de su almacén)
#
# EMPRESA: solo lectura.
# =============================================================

@router.post(
    "",
    response_model=DetalleInventarioResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear_inventario(
    data: DetalleInventarioCreate,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):
    if data.stock_actual != 0:
        from fastapi import HTTPException
        raise HTTPException(403, 'El stock inicial debe ser cero; las entradas aceptadas se registran mediante recepción')
    if user.es_operario and (data.stock_minimo != 0 or data.stock_maximo != 0 or data.stock_actual != 0):
        from fastapi import HTTPException
        raise HTTPException(403, 'El operario solo crea ubicaciones vacías; los umbrales los administra la empresa y las entradas se registran por recepción')

    await AccesoService.verificar_inventario(user, data.id_inventario)

    await AccesoService.verificar_rack(
        user,
        data.id_rack
    )

    await AccesoService.verificar_producto(
        user,
        data.id_producto
    )

    return await service.crear_inventario(
        data,
        user.id_operario
    )


# =============================================================
# OBTENER TODO
# =============================================================

@router.get(
    "",
    response_model=list[
        DetalleInventarioResponse
    ]
)
async def obtener_inventarios(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_inventarios()
    )


# =============================================================
# STOCK BAJO
# =============================================================

@router.get(
    "/stock-bajo",
    response_model=list[
        DetalleInventarioResponse
    ]
)
async def obtener_stock_bajo(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_stock_bajo()
    )


# =============================================================
# SIN STOCK
# =============================================================

@router.get(
    "/sin-stock",
    response_model=list[
        DetalleInventarioResponse
    ]
)
async def obtener_sin_stock(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_sin_stock()
    )


# =============================================================
# SOBRE STOCK
# =============================================================

@router.get(
    "/sobre-stock",
    response_model=list[
        DetalleInventarioResponse
    ]
)
async def obtener_sobre_stock(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_sobre_stock()
    )


# =============================================================
# POR PRODUCTO
# =============================================================

@router.get(
    "/producto/{id_producto}",
    response_model=list[
        DetalleInventarioResponse
    ]
)
async def obtener_inventario_producto(
    id_producto: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    return await _filtrar_alcance(
        user,
        await service.obtener_por_producto(
            id_producto
        )
    )


# =============================================================
# POR RACK
# =============================================================

@router.get(
    "/rack/{id_rack}",
    response_model=list[
        DetalleInventarioResponse
    ]
)
async def obtener_inventario_rack(
    id_rack: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await (
        service.obtener_por_rack(
            id_rack
        )
    )


# =============================================================
# POR ID
# =============================================================

@router.get(
    "/{id_detalle_inventario}",
    response_model=DetalleInventarioResponse
)
async def obtener_inventario(
    id_detalle_inventario: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await (
        AccesoService.verificar_detalle_inventario(
            user,
            id_detalle_inventario
        )
    )


# =============================================================
# ACTUALIZAR LIMITES (OPERARIO)
# =============================================================

@router.put(
    "/{id_detalle_inventario}",
    response_model=DetalleInventarioResponse
)
async def actualizar_inventario(
    id_detalle_inventario: str,
    data: DetalleInventarioUpdate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_detalle_inventario(
        user,
        id_detalle_inventario
    )

    return await (
        service.actualizar_inventario(
            id_detalle_inventario,
            data,
            None
        )
    )


# =============================================================
# HISTORIAL DE CAMBIOS (EMPRESA / OPERARIO)
# =============================================================

@router.get(
    "/{id_detalle_inventario}/historial",
    response_model=list[
        InventarioHistorialResponse
    ]
)
async def obtener_historial(
    id_detalle_inventario: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_detalle_inventario(
        user,
        id_detalle_inventario
    )

    return await (
        service.obtener_historial(
            id_detalle_inventario
        )
    )


# =============================================================
# ELIMINAR (OPERARIO, sin stock)
# =============================================================

@router.delete(
    "/{id_detalle_inventario}",
    status_code=status.HTTP_200_OK
)
async def eliminar_inventario(
    id_detalle_inventario: str,
    user: UsuarioActual = Depends(
        require_operario
    )
):

    await AccesoService.verificar_detalle_inventario(
        user,
        id_detalle_inventario
    )

    return await (
        service.eliminar_inventario(
            id_detalle_inventario
        )
    )
