from datetime import datetime, timezone
from uuid import uuid4

from app.database.mongodb import get_database


class DetalleRecepcionRepository:

    COLLECTION_NAME = "detalles_recepcion"

    def collection(self):
        return get_database()[self.COLLECTION_NAME]

    async def crear(self, data):

        documento = data.copy()

        documento["id_detalle_recepcion"] = str(uuid4())
        documento["fecha_creacion"] = (
            datetime.now(timezone.utc)
        )

        await self.collection().insert_one(documento)

        return await self.obtener_por_id(
            documento["id_detalle_recepcion"]
        )

    async def obtener_por_id(self, id_detalle):

        return await self.collection().find_one(
            {"id_detalle_recepcion": id_detalle},
            {"_id": 0}
        )

    async def obtener_por_recepcion(
        self,
        id_recepcion
    ):

        cursor = self.collection().find(
            {"id_recepcion": id_recepcion},
            {"_id": 0}
        )

        return await cursor.to_list(length=None)

    async def obtener_por_detalle_reposicion(
        self,
        id_detalle_reposicion
    ):

        cursor = self.collection().find(
            {
                "id_detalle_reposicion":
                    id_detalle_reposicion
            },
            {"_id": 0}
        )

        return await cursor.to_list(length=None)

    async def actualizar_movimiento(
        self,
        id_detalle_recepcion,
        id_movimiento
    ):

        await self.collection().update_one(
            {
                "id_detalle_recepcion":
                    id_detalle_recepcion
            },
            {
                "$set": {
                    "id_movimiento":
                        id_movimiento
                }
            }
        )

        return await self.obtener_por_id(
            id_detalle_recepcion
        )

    async def actualizar(
        self,
        id_detalle_recepcion,
        cambios
    ):
        await self.collection().update_one(
            {
                "id_detalle_recepcion":
                    id_detalle_recepcion
            },
            {
                "$set": cambios
            }
        )

        return await self.obtener_por_id(
            id_detalle_recepcion
        )

    async def eliminar(
        self,
        id_detalle_recepcion
    ):
        resultado = await self.collection().delete_one(
            {
                "id_detalle_recepcion":
                    id_detalle_recepcion
            }
        )
        return resultado.deleted_count > 0