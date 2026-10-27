from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from app.dependencies.dependencies import (
    get_usuario_activo,
    require_empresa_u_operario,
    require_proveedor,
    require_roles
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.producto_dto import (
    ProductoCreate,
    ProductoUpdate,
    ProductoResponse
)

from app.repositories.detalle_inventario_repository import (
    DetalleInventarioRepository
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.producto_service import (
    ProductoService
)


# ============================================================
# PRODUCTOS
#
# PROVEEDOR -> crea / edita / borra los suyos; ve solo los suyos.
# OPERARIO  -> lee los de la empresa; edita solo id_rack
#              (rack de referencia, de su almacén).
# EMPRESA   -> solo lectura.
# ============================================================

def _visibles(
    user: UsuarioActual,
    productos: list
) -> list:

    productos = AccesoService.filtrar_empresa(
        user,
        productos
    )

    if user.es_proveedor:

        productos = [
            producto
            for producto in productos
            if producto.get("id_proveedor")
            == user.id_proveedor
        ]

    return productos


router = APIRouter(
    prefix="/productos",
    tags=[
        "Productos"
    ]
)


# ============================================================
# CREAR (PROVEEDOR)
#
# id_proveedor e id_empresa se toman del token.
# Sin rack: el rack de referencia lo asigna el operario.
# ============================================================

@router.post(
    "",
    response_model=ProductoResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Crear producto"
)
async def crear_producto(
    data: ProductoCreate,
    user: UsuarioActual = Depends(
        require_proveedor
    )
):

    data.id_empresa = user.id_empresa

    data.id_proveedor = user.id_proveedor

    data.id_rack = None

    return await (
        ProductoService.crear(
            data
        )
    )


# ============================================================
# OBTENER TODOS (DE LA EMPRESA)
# ============================================================

@router.get(
    "",
    response_model=List[
        ProductoResponse
    ],
    summary="Obtener productos"
)
async def obtener_productos(
    user: UsuarioActual = Depends(
        get_usuario_activo
    )
):

    return _visibles(
        user,
        await (
            ProductoService
            .obtener_todos()
        )
    )


# ============================================================
# REFRIGERADOS
#
# IMPORTANTE:
# antes de /{id_producto}
# ============================================================

@router.get(
    "/refrigerados",
    response_model=List[
        ProductoResponse
    ],
    summary=(
        "Obtener productos refrigerados"
    )
)
async def obtener_productos_refrigerados(
    user: UsuarioActual = Depends(
        get_usuario_activo
    )
):

    return _visibles(
        user,
        await (
            ProductoService
            .obtener_refrigerados()
        )
    )


# ============================================================
# POR ALMACEN
# ============================================================

@router.get(
    "/almacen/{id_almacen}",
    response_model=List[
        ProductoResponse
    ],
    summary=(
        "Obtener productos por almacén"
    )
)
async def obtener_productos_por_almacen(
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
        ProductoService
        .obtener_por_almacen(
            id_almacen
        )
    )


# ============================================================
# POR RACK
# ============================================================

@router.get(
    "/rack/{id_rack}",
    response_model=List[
        ProductoResponse
    ],
    summary=(
        "Obtener productos por rack"
    )
)
async def obtener_productos_por_rack(
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
        ProductoService
        .obtener_por_rack(
            id_rack
        )
    )


# ============================================================
# POR CATEGORIA
# ============================================================

@router.get(
    "/categoria/{categoria}",
    response_model=List[
        ProductoResponse
    ],
    summary=(
        "Obtener productos por categoría"
    )
)
async def obtener_productos_por_categoria(
    categoria: str,
    user: UsuarioActual = Depends(
        get_usuario_activo
    )
):

    return _visibles(
        user,
        await (
            ProductoService
            .obtener_por_categoria(
                categoria
            )
        )
    )


# ============================================================
# POR ID
#
# DEBE IR DESPUES DE LAS RUTAS ESPECIALES
# ============================================================

@router.get(
    "/{id_producto}",
    response_model=ProductoResponse,
    summary="Obtener producto por ID"
)
async def obtener_producto(
    id_producto: str,
    user: UsuarioActual = Depends(
        get_usuario_activo
    )
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    return await (
        ProductoService
        .obtener_por_id(
            id_producto
        )
    )


# ============================================================
# ACTUALIZAR
#
# PROVEEDOR: sus productos (id_rack se ignora).
# OPERARIO : solo id_rack (rack de referencia).
# ============================================================

@router.put(
    "/{id_producto}",
    response_model=ProductoResponse,
    summary="Actualizar producto"
)
async def actualizar_producto(
    id_producto: str,
    data: ProductoUpdate,
    user: UsuarioActual = Depends(
        require_roles(
            "PROVEEDOR",
            "OPERARIO"
        )
    )
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    if user.es_operario:

        if data.model_fields_set - {"id_rack"}:

            raise HTTPException(
                status_code=403,
                detail=(
                    "El operario solo puede cambiar "
                    "el rack de referencia (id_rack)"
                )
            )

        if data.id_rack:

            await AccesoService.verificar_rack(
                user,
                data.id_rack
            )

    else:

        # El proveedor no gestiona racks: se conserva
        # el rack de referencia actual.
        data = ProductoUpdate(
            **data.model_dump(
                exclude_unset=True,
                exclude={"id_rack"}
            )
        )

    return await (
        ProductoService.actualizar(
            id_producto,
            data
        )
    )


# ============================================================
# ELIMINAR (PROVEEDOR, los suyos)
# ============================================================

@router.delete(
    "/{id_producto}",
    status_code=(
        status.HTTP_200_OK
    ),
    summary="Eliminar producto"
)
async def eliminar_producto(
    id_producto: str,
    user: UsuarioActual = Depends(
        require_proveedor
    )
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    # Un producto con inventario no se borra
    # (dejaría stock huérfano en los racks).
    if await DetalleInventarioRepository().obtener_por_producto(
        id_producto
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "El producto tiene inventarios; "
                "no puede eliminarse"
            )
        )

    return await (
        ProductoService.eliminar(
            id_producto
        )
    )
