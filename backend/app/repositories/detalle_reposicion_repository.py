from datetime import datetime, timezone
from uuid import uuid4

from app.database.mongodb import get_database


class DetalleReposicionRepository:

    COLLECTION_NAME = "detalles_reposicion"

    def collection(self):
        return get_database()[self.COLLECTION_NAME]

    async def crear(self, data):

        ahora = datetime.now(timezone.utc)

        documento = data.copy()

        documento["id_detalle_reposicion"] = str(uuid4())
        documento["fecha_creacion"] = ahora
        documento["fecha_actualizacion"] = ahora

        await self.collection().insert_one(documento)

        return await self.obtener_por_id(
            documento["id_detalle_reposicion"]
        )

    async def obtener_por_id(self, id_detalle):

        return await self.collection().find_one(
            {"id_detalle_reposicion": id_detalle},
            {"_id": 0}
        )

    async def obtener_por_orden(self, id_orden):

        cursor = self.collection().find(
            {"id_orden_reposicion": id_orden},
            {"_id": 0}
        )

        return await cursor.to_list(length=None)

    async def obtener_producto_en_orden(
        self,
        id_orden,
        id_producto
    ):

        return await self.collection().find_one(
            {
                "id_orden_reposicion": id_orden,
                "id_producto": id_producto
            },
            {"_id": 0}
        )

    async def actualizar(self, id_detalle, cambios):

        cambios = cambios.copy()

        cambios["fecha_actualizacion"] = (
            datetime.now(timezone.utc)
        )

        await self.collection().update_one(
            {"id_detalle_reposicion": id_detalle},
            {"$set": cambios}
        )

        return await self.obtener_por_id(id_detalle)

    async def eliminar(self, id_detalle):

        result = await self.collection().delete_one(
            {"id_detalle_reposicion": id_detalle}
        )

        return result.deleted_count > 0