from datetime import (
    datetime,
    timezone
)

from uuid import uuid4

from fastapi import (
    HTTPException,
    status
)

from app.dto.producto_dto import (
    ProductoCreate,
    ProductoUpdate
)

from app.repositories.producto_repository import (
    ProductoRepository
)

from app.repositories.empresa_repository import (
    EmpresaRepository
)

from app.repositories.rack_repository import (
    RackRepository
)

from app.repositories.almacen_repository import (
    AlmacenRepository
)


class ProductoService:

    # ============================================================
    # CREAR
    # ============================================================

    @staticmethod
    async def _crear(
        data: ProductoCreate
    ):
        from app.services.clasificacion_service import validar_clasificacion, normalizar
        from app.database.mongodb import get_database
        from app.services.stock_lock import bloqueo_recurso
        data.familia, data.categoria = await validar_clasificacion(data.id_empresa, data.familia, data.categoria)
        if data.unidad == 'kg':
            data.peso = 1
        # Canonical products can be offered by several providers; supplier prices
        # and stock never live in the master catalogue.
        existing = await get_database().productos.find({'id_empresa': data.id_empresa}, {'_id': 0}).to_list(length=10000)
        for row in existing:
            if data.codigo and (row.get('codigo') or '').strip().upper() == data.codigo.strip().upper() and normalizar(row['nombre']) != normalizar(data.nombre):
                raise HTTPException(409, 'El código del producto ya está registrado')
            if normalizar(row['nombre']) == normalizar(data.nombre) and normalizar(row.get('marca') or '') == normalizar(data.marca or ''):
                if row.get('unidad', 'unidad') != data.unidad or normalizar(row['familia']) != normalizar(data.familia) or normalizar(row['categoria']) != normalizar(data.categoria):
                    raise HTTPException(409, 'Producto ya registrado con otra clasificación o unidad; identifique la variante')
                return row

        # --------------------------------------------------------
        # VALIDAR EMPRESA
        # --------------------------------------------------------

        empresa = await (
            EmpresaRepository.obtener_por_id(
                data.id_empresa
            )
        )

        if not empresa:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Empresa no encontrada"
            )


        # --------------------------------------------------------
        # VALIDAR RACK
        # --------------------------------------------------------

        # El rack de referencia es opcional al crear.
        rack = (
            await RackRepository.obtener_por_id(
                data.id_rack
            )
            if data.id_rack
            else None
        )

        if data.id_rack and not rack:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Rack no encontrado"
            )


        # --------------------------------------------------------
        # VALIDAR REFRIGERACION
        # --------------------------------------------------------

        if data.requiere_refrigeracion:

            if (
                data.temperatura_min_almacenamiento
                is None
                or
                data.temperatura_max_almacenamiento
                is None
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Si el producto requiere refrigeración, "
                        "debe indicar temperatura mínima y máxima"
                    )
                )

            if (
                data.temperatura_min_almacenamiento
                >
                data.temperatura_max_almacenamiento
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "La temperatura mínima no puede ser "
                        "mayor que la temperatura máxima"
                    )
                )


        # --------------------------------------------------------
        # CONSTRUIR PRODUCTO
        # --------------------------------------------------------

        producto = (
            data.model_dump()
        )

        producto.pop("stock", None)


        # --------------------------------------------------------
        # LIMPIAR TEXTOS
        # --------------------------------------------------------

        producto["nombre"] = (
            producto[
                "nombre"
            ].strip()
        )

        producto["categoria"] = (
            producto[
                "categoria"
            ].strip()
        )

        producto["familia"] = (
            producto[
                "familia"
            ].strip()
        )

        if producto.get("marca"):

            producto["marca"] = (
                producto[
                    "marca"
                ].strip()
            )


        # --------------------------------------------------------
        # ID Y FECHAS
        # --------------------------------------------------------

        producto[
            "id_producto"
        ] = str(
            uuid4()
        )


        now = datetime.now(
            timezone.utc
        )


        producto[
            "fecha_creacion"
        ] = now

        producto[
            "fecha_actualizacion"
        ] = now


        # --------------------------------------------------------
        # GUARDAR
        # --------------------------------------------------------

        return await (
            ProductoRepository.crear(
                producto
            )
        )


    # ============================================================
    # OBTENER TODOS
    # ============================================================

    @staticmethod
    async def obtener_todos():

        return await (
            ProductoRepository
            .obtener_todos()
        )


    # ============================================================
    # OBTENER POR ID
    # ============================================================

    @staticmethod
    async def obtener_por_id(
        id_producto: str
    ):

        producto = await (
            ProductoRepository
            .obtener_por_id(
                id_producto
            )
        )

        if not producto:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )

        return producto


    # ============================================================
    # OBTENER POR RACK
    # ============================================================

    @staticmethod
    async def obtener_por_rack(
        id_rack: str
    ):

        rack = await (
            RackRepository.obtener_por_id(
                id_rack
            )
        )

        if not rack:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Rack no encontrado"
            )


        return await (
            ProductoRepository
            .obtener_por_rack(
                id_rack
            )
        )


    # ============================================================
    # OBTENER POR ALMACEN
    # ============================================================

    @staticmethod
    async def obtener_por_almacen(
        id_almacen: str
    ):

        almacen = await (
            AlmacenRepository.obtener_por_id(
                id_almacen
            )
        )

        if not almacen:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Almacén no encontrado"
            )


        return await (
            ProductoRepository
            .obtener_por_almacen(
                id_almacen
            )
        )


    # ============================================================
    # OBTENER POR CATEGORIA
    # ============================================================

    @staticmethod
    async def obtener_por_categoria(
        categoria: str
    ):

        categoria = (
            categoria.strip()
        )

        if not categoria:

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "La categoría no puede estar vacía"
                )
            )


        return await (
            ProductoRepository
            .obtener_por_categoria(
                categoria
            )
        )


    # ============================================================
    # OBTENER REFRIGERADOS
    # ============================================================

    @staticmethod
    async def obtener_refrigerados():

        return await (
            ProductoRepository
            .obtener_refrigerados()
        )


    # ============================================================
    # ACTUALIZAR
    # ============================================================

    @staticmethod
    async def _actualizar(
        id_producto: str,
        data: ProductoUpdate
    ):

        producto_actual = await (
            ProductoRepository
            .obtener_por_id(
                id_producto
            )
        )

        if not producto_actual:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )


        update_data = (
            data.model_dump(
                exclude_unset=True
            )
        )

        update_data.pop("stock", None)
        from app.services.clasificacion_service import normalizar
        from app.database.mongodb import get_database
        if producto_actual.get('unidad') == 'kg' and 'peso' in update_data:
            update_data['peso'] = 1
        if any(k in update_data for k in ('nombre', 'marca', 'codigo')):
            for other in await get_database()['productos'].find({'id_empresa': producto_actual['id_empresa'], 'id_producto': {'$ne': id_producto}}).to_list(length=None):
                code = update_data.get('codigo', producto_actual.get('codigo'))
                if code and (other.get('codigo') or '').strip().upper() == code.strip().upper():
                    raise HTTPException(409, 'El código del producto ya está registrado')
                if normalizar(other['nombre']) == normalizar(update_data.get('nombre', producto_actual['nombre'])) and normalizar(other.get('marca') or '') == normalizar(update_data.get('marca', producto_actual.get('marca')) or ''):
                    raise HTTPException(409, 'Ya existe un producto equivalente en el catálogo')

        from app.services.clasificacion_service import validar_clasificacion
        if 'familia' in update_data or 'categoria' in update_data:
            family, category = await validar_clasificacion(producto_actual['id_empresa'],
                update_data.get('familia', producto_actual['familia']), update_data.get('categoria', producto_actual['categoria']))
            update_data.update(familia=family, categoria=category)


        # --------------------------------------------------------
        # VALIDAR NUEVO RACK
        # --------------------------------------------------------

        if (
            "id_rack" in update_data
            and
            update_data[
                "id_rack"
            ] is not None
        ):

            rack = await (
                RackRepository.obtener_por_id(
                    update_data[
                        "id_rack"
                    ]
                )
            )

            if not rack:

                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail="Rack no encontrado"
                )


        # --------------------------------------------------------
        # REFRIGERACION RESULTANTE
        # --------------------------------------------------------

        requiere = (
            update_data.get(
                "requiere_refrigeracion",
                producto_actual.get(
                    "requiere_refrigeracion",
                    False
                )
            )
        )


        temperatura_min = (
            update_data.get(
                "temperatura_min_almacenamiento",
                producto_actual.get(
                    "temperatura_min_almacenamiento"
                )
            )
        )


        temperatura_max = (
            update_data.get(
                "temperatura_max_almacenamiento",
                producto_actual.get(
                    "temperatura_max_almacenamiento"
                )
            )
        )


        if requiere:

            if (
                temperatura_min is None
                or
                temperatura_max is None
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Un producto refrigerado debe tener "
                        "temperatura mínima y máxima"
                    )
                )


            if (
                temperatura_min
                >
                temperatura_max
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "La temperatura mínima no puede ser "
                        "mayor que la temperatura máxima"
                    )
                )


        # --------------------------------------------------------
        # SI YA NO REQUIERE REFRIGERACION
        # --------------------------------------------------------

        if (
            update_data.get(
                "requiere_refrigeracion"
            )
            is False
        ):

            update_data[
                "temperatura_min_almacenamiento"
            ] = None

            update_data[
                "temperatura_max_almacenamiento"
            ] = None


        # --------------------------------------------------------
        # LIMPIAR TEXTOS
        # --------------------------------------------------------

        for campo in [
            "nombre",
            "categoria",
            "familia",
            "marca"
        ]:

            if (
                campo in update_data
                and
                isinstance(
                    update_data[
                        campo
                    ],
                    str
                )
            ):

                update_data[
                    campo
                ] = (
                    update_data[
                        campo
                    ].strip()
                )


        if not update_data:

            return producto_actual


        producto_actualizado = await (
            ProductoRepository.actualizar(
                id_producto,
                update_data
            )
        )


        if not producto_actualizado:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )


        return producto_actualizado


    # ============================================================
    # ELIMINAR
    # ============================================================

    @staticmethod
    async def _eliminar(
        id_producto: str
    ):

        producto = await (
            ProductoRepository
            .obtener_por_id(
                id_producto
            )
        )

        if not producto:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )


        from app.database.mongodb import get_database
        db = get_database()
        for collection in ('ofertas_proveedor', 'detalles_reposicion', 'detalles_inventario', 'movimientos'):
            if await db[collection].find_one({'id_producto': id_producto}):
                await ProductoRepository.actualizar(id_producto, {'activo': False, 'fecha_actualizacion': datetime.now(timezone.utc)})
                return {'mensaje': 'Producto desactivado; se conserva su historial y sus referencias'}

        eliminado = await (
            ProductoRepository.eliminar(
                id_producto
            )
        )


        if not eliminado:

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "No se pudo eliminar el producto"
                )
            )


        return {
            "mensaje":
                "Producto eliminado correctamente"
        }

    @staticmethod
    async def crear(data):
        from app.services.stock_lock import bloqueo_recurso
        async with bloqueo_recurso('catalogo:' + str(data.id_empresa)):
            return await ProductoService._crear(data)

    @staticmethod
    async def actualizar(identifier, data):
        from app.services.stock_lock import bloqueo_recurso
        product = await ProductoService.obtener_por_id(identifier)
        async with bloqueo_recurso('catalogo:' + product['id_empresa']):
            return await ProductoService._actualizar(identifier, data)

    @staticmethod
    async def eliminar(identifier):
        from app.services.stock_lock import bloqueo_recurso
        product = await ProductoService.obtener_por_id(identifier)
        async with bloqueo_recurso('catalogo:' + product['id_empresa']):
            return await ProductoService._eliminar(identifier)
