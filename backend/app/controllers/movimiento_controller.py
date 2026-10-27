from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from app.dependencies.dependencies import (
    require_empresa_u_operario,
    require_operario
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.movimiento_dto import (
    MovimientoCreate,
    MovimientoResponse,
    TipoMovimiento,
    MotivoMovimiento
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.movimiento_service import (
    MovimientoService
)


router = APIRouter(
    prefix="/movimientos",
    tags=["Movimientos"]
)

service = MovimientoService()


# ============================================================
# ALCANCE
#
# EMPRESA  -> movimientos de racks de sus almacenes
# OPERARIO -> movimientos de racks de su almacén
# ============================================================

async def _filtrar_alcance(
    user: UsuarioActual,
    movimientos: list
) -> list:

    return await service.enriquecer(
        AccesoService.filtrar(
            movimientos,
            "id_rack",
            await AccesoService.ids_racks(
                user
            )
        )
    )


# ============================================================
# CREAR (OPERARIO)
#
# Solo SALIDA por VENTA o VENCIMIENTO, sobre inventarios
# de su almacén. Las ENTRADAS se generan únicamente
# desde la recepción de mercadería.
# ============================================================

@router.post(
    "",
    response_model=MovimientoResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear_movimiento(
    data: MovimientoCreate,
    user: UsuarioActual = Depends(
        require_operario
    )
):

    if (
        data.tipo_movimiento != TipoMovimiento.SALIDA
        or data.motivo_movimiento not in (
            MotivoMovimiento.VENTA,
            MotivoMovimiento.VENCIMIENTO
        )
    ):

        raise HTTPException(
            status_code=422,
            detail=(
                "Solo se pueden registrar SALIDAS "
                "por VENTA o VENCIMIENTO"
            )
        )

    await AccesoService.verificar_inventario(user, data.id_inventario)
    await AccesoService.verificar_detalle_inventario(user, data.id_detalle_inventario)

    # Campo interno (recepciones): no se acepta del cliente.
    data.id_detalle_recepcion = None

    return (
        await service.enriquecer(
            [
                await service.crear_movimiento(
                    data,
                    user
                )
            ]
        )
    )[0]


# ============================================================
# OBTENER TODOS
# ============================================================

@router.get(
    "",
    response_model=List[MovimientoResponse]
)
async def obtener_movimientos(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_movimientos()
    )


# ============================================================
# POR INVENTARIO
# ============================================================

@router.get(
    "/inventario/{id_inventario}",
    response_model=List[MovimientoResponse]
)
async def obtener_por_inventario(
    id_inventario: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_inventario(
        user,
        id_inventario
    )

    return await service.enriquecer(
        await service.obtener_por_inventario(
            id_inventario
        )
    )


# ============================================================
# POR PRODUCTO
# ============================================================

@router.get(
    "/producto/{id_producto}",
    response_model=List[MovimientoResponse]
)
async def obtener_por_producto(
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


# ============================================================
# POR RACK
# ============================================================

@router.get(
    "/rack/{id_rack}",
    response_model=List[MovimientoResponse]
)
async def obtener_por_rack(
    id_rack: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await service.enriquecer(
        await service.obtener_por_rack(
            id_rack
        )
    )


# ============================================================
# POR OPERARIO
# ============================================================

@router.get(
    "/operario/{id_operario}",
    response_model=List[MovimientoResponse]
)
async def obtener_por_operario(
    id_operario: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_operario(
        user,
        id_operario
    )

    return await _filtrar_alcance(
        user,
        await service.obtener_por_operario(
            id_operario
        )
    )


# ============================================================
# POR TIPO
# ============================================================

@router.get(
    "/tipo/{tipo_movimiento}",
    response_model=List[MovimientoResponse]
)
async def obtener_por_tipo(
    tipo_movimiento: TipoMovimiento,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_por_tipo(
            tipo_movimiento
        )
    )


# ============================================================
# POR MOTIVO
# ============================================================

@router.get(
    "/motivo/{motivo_movimiento}",
    response_model=List[MovimientoResponse]
)
async def obtener_por_motivo(
    motivo_movimiento: MotivoMovimiento,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_por_motivo(
            motivo_movimiento
        )
    )


# ============================================================
# POR ID
# IMPORTANTE: ESTA RUTA VA AL FINAL
# ============================================================

@router.get(
    "/{id_movimiento}",
    response_model=MovimientoResponse
)
async def obtener_movimiento(
    id_movimiento: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    movimiento = await service.obtener_movimiento(
        id_movimiento
    )

    await AccesoService.verificar_rack(
        user,
        movimiento["id_rack"]
    )

    return (
        await service.enriquecer(
            [movimiento]
        )
    )[0]
