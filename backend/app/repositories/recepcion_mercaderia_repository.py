from datetime import datetime, timezone
from uuid import uuid4

from app.database.mongodb import get_database


class RecepcionMercaderiaRepository:

    COLLECTION_NAME = "recepciones_mercaderia"

    def collection(self):
        return get_database()[self.COLLECTION_NAME]

    async def crear(self, data):

        ahora = datetime.now(timezone.utc)

        documento = data.copy()

        documento["id_recepcion"] = str(uuid4())

        # Se respeta la fecha enviada; si no, ahora.
        documento["fecha_recepcion"] = (
            data.get("fecha_recepcion")
            or ahora
        )

        documento["fecha_creacion"] = ahora

        await self.collection().insert_one(documento)

        return await self.obtener_por_id(
            documento["id_recepcion"]
        )

    async def obtener_por_ordenes(self, ids_orden):

        cursor = self.collection().find(
            {"id_orden_reposicion": {"$in": list(ids_orden)}},
            {"_id": 0}
        ).sort("fecha_recepcion", -1)

        return await cursor.to_list(length=None)

    async def obtener_por_id(self, id_recepcion):

        return await self.collection().find_one(
            {"id_recepcion": id_recepcion},
            {"_id": 0}
        )

    async def obtener_todos(self):

        cursor = self.collection().find(
            {},
            {"_id": 0}
        ).sort("fecha_recepcion", -1)

        return await cursor.to_list(length=None)

    async def obtener_por_orden(self, id_orden):

        cursor = self.collection().find(
            {"id_orden_reposicion": id_orden},
            {"_id": 0}
        ).sort("fecha_recepcion", -1)

        return await cursor.to_list(length=None)

    async def obtener_por_operario(self, id_operario):

        cursor = self.collection().find(
            {"id_operario": id_operario},
            {"_id": 0}
        ).sort("fecha_recepcion", -1)

        return await cursor.to_list(length=None)