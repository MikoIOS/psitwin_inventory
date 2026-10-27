import re

from datetime import (
    datetime,
    timezone
)

from app.database.mongodb import (
    get_database
)


class ProductoRepository:

    COLLECTION_NAME = "productos"


    @staticmethod
    def collection():

        return get_database()[
            ProductoRepository.COLLECTION_NAME
        ]


    @staticmethod
    async def crear(
        producto: dict
    ):

        await (
            ProductoRepository
            .collection()
            .insert_one(
                producto
            )
        )

        return await (
            ProductoRepository.obtener_por_id(
                producto["id_producto"]
            )
        )


    @staticmethod
    async def obtener_todos():

        return await (
            ProductoRepository
            .collection()
            .find(
                {},
                {
                    "_id": 0
                }
            )
            .to_list(
                length=None
            )
        )


    @staticmethod
    async def obtener_por_id(
        id_producto: str
    ):

        return await (
            ProductoRepository
            .collection()
            .find_one(
                {
                    "id_producto":
                        id_producto
                },
                {
                    "_id": 0
                }
            )
        )


    # ============================================================
    # PRODUCTOS POR RACK
    # ============================================================

    @staticmethod
    async def obtener_por_rack(
        id_rack: str
    ):

        return await (
            ProductoRepository
            .collection()
            .find(
                {
                    "id_rack":
                        id_rack
                },
                {
                    "_id": 0
                }
            )
            .to_list(
                length=None
            )
        )


    # ============================================================
    # PRODUCTOS POR ALMACEN
    #
    # ALMACEN
    # ↓
    # ZONAS
    # ↓
    # RACKS
    # ↓
    # PRODUCTOS
    # ============================================================

    @staticmethod
    async def obtener_por_almacen(id_almacen: str):
        from app.repositories.inventario_repository import InventarioRepository
        from app.repositories.detalle_inventario_repository import DetalleInventarioRepository
        header = await InventarioRepository().obtener_por_almacen(id_almacen)
        if not header:
            return []
        details = await DetalleInventarioRepository().obtener_por_inventario(header["id_inventario"])
        product_ids = sorted({row["id_producto"] for row in details})
        return await ProductoRepository.collection().find(
            {"id_producto":{"$in":product_ids}},{"_id":0}).to_list(length=None)

    @staticmethod
    async def obtener_por_categoria(
        categoria: str
    ):

        categoria_segura = (
            re.escape(
                categoria.strip()
            )
        )

        return await (
            ProductoRepository
            .collection()
            .find(
                {
                    "categoria": {
                        "$regex":
                            f"^{categoria_segura}$",

                        "$options":
                            "i"
                    }
                },
                {
                    "_id": 0
                }
            )
            .to_list(
                length=None
            )
        )


    @staticmethod
    async def obtener_refrigerados():

        return await (
            ProductoRepository
            .collection()
            .find(
                {
                    "requiere_refrigeracion":
                        True
                },
                {
                    "_id": 0
                }
            )
            .to_list(
                length=None
            )
        )


    @staticmethod
    async def actualizar(
        id_producto: str,
        data: dict
    ):

        data[
            "fecha_actualizacion"
        ] = datetime.now(
            timezone.utc
        )


        result = await (
            ProductoRepository
            .collection()
            .update_one(
                {
                    "id_producto":
                        id_producto
                },
                {
                    "$set":
                        data
                }
            )
        )


        if result.matched_count == 0:

            return None


        return await (
            ProductoRepository
            .obtener_por_id(
                id_producto
            )
        )


    @staticmethod
    async def eliminar(
        id_producto: str
    ):

        result = await (
            ProductoRepository
            .collection()
            .delete_one(
                {
                    "id_producto":
                        id_producto
                }
            )
        )

        return (
            result.deleted_count > 0
        )