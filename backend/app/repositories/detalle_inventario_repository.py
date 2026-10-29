from datetime import (
    datetime,
    timezone
)

from uuid import uuid4

from typing import (
    Optional,
    Dict,
    Any,
    List
)

from app.database.mongodb import (
    get_database
)


class DetalleInventarioRepository:

    COLLECTION_NAME = "detalles_inventario"


    # ============================================================
    # COLLECTION
    # ============================================================

    def collection(self):

        database = get_database()

        return database[
            self.COLLECTION_NAME
        ]


    # ============================================================
    # CREAR
    # ============================================================

    async def crear(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:

        now = datetime.now(
            timezone.utc
        )

        inventario = {

            "id_detalle_inventario":
                str(
                    uuid4()
                ),

            "id_inventario": data["id_inventario"],

            "id_producto":
                data["id_producto"],

            "id_rack":
                data["id_rack"],

            "stock_actual":
                data["stock_actual"],

            "stock_minimo":
                data["stock_minimo"],

            "stock_maximo":
                data["stock_maximo"],

            "fecha_creacion":
                now,

            "fecha_actualizacion":
                now
        }

        await self.collection().insert_one(
            inventario
        )

        return await self.obtener_por_id(
            inventario[
                "id_detalle_inventario"
            ]
        )


    # ============================================================
    # OBTENER TODOS
    # ============================================================

    async def obtener_todos(
        self
    ) -> List[Dict[str, Any]]:

        from app.repositories.inventario_repository import InventarioRepository
        await InventarioRepository().verificar_esquema()

        cursor = self.collection().find(
            {},
            {
                "_id": 0
            }
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR ID
    # ============================================================

    async def obtener_por_id(
        self,
        id_detalle_inventario: str
    ) -> Optional[Dict[str, Any]]:

        from app.repositories.inventario_repository import InventarioRepository
        await InventarioRepository().verificar_esquema()

        return await self.collection().find_one(
            {
                "id_detalle_inventario":
                    id_detalle_inventario
            },
            {
                "_id": 0
            }
        )


    # ============================================================
    # OBTENER POR PRODUCTO
    # ============================================================

    async def obtener_por_producto(
        self,
        id_producto: str
    ) -> List[Dict[str, Any]]:

        from app.repositories.inventario_repository import InventarioRepository
        await InventarioRepository().verificar_esquema()

        cursor = self.collection().find(
            {
                "id_producto":
                    id_producto
            },
            {
                "_id": 0
            }
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR RACK
    # ============================================================

    async def obtener_por_rack(
        self,
        id_rack: str
    ) -> List[Dict[str, Any]]:

        from app.repositories.inventario_repository import InventarioRepository
        await InventarioRepository().verificar_esquema()

        cursor = self.collection().find(
            {
                "id_rack":
                    id_rack
            },
            {
                "_id": 0
            }
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR VARIOS RACKS
    # ============================================================

    async def obtener_por_racks(
        self,
        ids_rack: List[str]
    ) -> List[Dict[str, Any]]:

        from app.repositories.inventario_repository import InventarioRepository
        await InventarioRepository().verificar_esquema()

        cursor = self.collection().find(
            {
                "id_rack": {
                    "$in": list(ids_rack)
                }
            },
            {
                "_id": 0
            }
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # ACTUALIZAR
    # ============================================================

    async def actualizar(
        self,
        id_detalle_inventario: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        data = dict(
            data
        )

        data[
            "fecha_actualizacion"
        ] = datetime.now(
            timezone.utc
        )

        result = await self.collection().update_one(
            {
                "id_detalle_inventario":
                    id_detalle_inventario
            },
            {
                "$set":
                    data
            }
        )

        if result.matched_count == 0:

            return None

        return await self.obtener_por_id(
            id_detalle_inventario
        )


    # ============================================================
    # ACTUALIZAR STOCK
    #
    # Este método nos servirá luego para Movimiento.
    # ============================================================

    async def actualizar_stock(
        self,
        id_detalle_inventario: str,
        nuevo_stock: int
    ) -> Optional[Dict[str, Any]]:

        await self.collection().update_one(
            {
                "id_detalle_inventario":
                    id_detalle_inventario
            },
            {
                "$set": {
                    "stock_actual":
                        nuevo_stock,

                    "fecha_actualizacion":
                        datetime.now(
                            timezone.utc
                        )
                }
            }
        )

        return await self.obtener_por_id(
            id_detalle_inventario
        )

    async def actualizar_stock_condicional(
        self,
        id_detalle_inventario: str,
        stock_anterior: int,
        nuevo_stock: int
    ) -> bool:
        resultado = await self.collection().update_one(
            {
                "id_detalle_inventario": id_detalle_inventario,
                "stock_actual": stock_anterior
            },
            {
                "$set": {
                    "stock_actual": nuevo_stock,
                    "fecha_actualizacion": datetime.now(
                        timezone.utc
                    )
                }
            }
        )
        return resultado.matched_count == 1


    # ============================================================
    # ELIMINAR
    # ============================================================

    async def eliminar(
        self,
        id_detalle_inventario: str
    ) -> bool:

        result = await self.collection().delete_one(
            {
                "id_detalle_inventario":
                    id_detalle_inventario
            }
        )

        return (
            result.deleted_count > 0
        )


    # ============================================================
    # HISTORIAL DE CAMBIOS (colección inventario_historial)
    # ============================================================

    async def registrar_historial(self, id_detalle_inventario, id_operario, accion, antes, despues):
        from app.repositories.inventario_repository import InventarioRepository
        detalle = await self.obtener_por_id(id_detalle_inventario)
        if not detalle:
            raise RuntimeError("Detalle no encontrado para registrar auditoría")
        header = await InventarioRepository().obtener_por_id(detalle["id_inventario"])
        await get_database()["inventario_historial"].insert_one({
            "id_inventario": detalle["id_inventario"],
            "id_detalle_inventario": id_detalle_inventario,
            "id_almacen": header["id_almacen"], "id_producto": detalle["id_producto"],
            "id_rack": detalle["id_rack"], "id_operario": id_operario,
            "accion": accion, "antes": antes, "despues": despues,
            "fecha": datetime.now(timezone.utc)})

    async def obtener_historial(self, identifier):
        from app.repositories.historial_inventario import consultar_historial
        return await consultar_historial("id_detalle_inventario", identifier)
    async def obtener_por_inventario(self, id_inventario):
        return await self.collection().find({"id_inventario": id_inventario}, {"_id": 0}).to_list(length=None)

    async def obtener_combinacion(self, id_inventario, id_producto, id_rack, id_nivel=None):
        return await self.collection().find_one({"id_inventario": id_inventario,
            "id_producto": id_producto, "id_rack": id_rack, 'id_nivel': id_nivel}, {"_id": 0})
