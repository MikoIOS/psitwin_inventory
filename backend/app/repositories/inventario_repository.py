from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from app.database.mongodb import get_database


class InventarioRepository:
    COLLECTION_NAME = "inventarios"

    def collection(self):
        return get_database()[self.COLLECTION_NAME]

    async def verificar_esquema(self):
        # Never reinterpret a legacy product/rack balance as a warehouse header.
        if await self.collection().find_one({"id_producto": {"$exists": True}}, {"_id": 1}):
            raise HTTPException(409, "MIGRACION_INVENTARIO_REQUERIDA: existen saldos del esquema anterior")

    async def garantizar(self, id_almacen: str) -> dict:
        await self.verificar_esquema()
        now = datetime.now(timezone.utc)
        document = {"id_inventario": str(uuid4()), "id_almacen": id_almacen,
                    "fecha_creacion": now, "fecha_actualizacion": now}
        try:
            await self.collection().update_one({"id_almacen": id_almacen},
                                              {"$setOnInsert": document}, upsert=True)
        except DuplicateKeyError:
            pass  # Concurrent creation won the unique warehouse index.
        result = await self.obtener_por_almacen(id_almacen)
        if result is None:
            raise RuntimeError("No se pudo garantizar el inventario del almacén")
        return result

    async def obtener_por_almacen(self, id_almacen):
        await self.verificar_esquema()
        return await self.collection().find_one({"id_almacen": id_almacen}, {"_id": 0})

    async def obtener_por_id(self, id_inventario):
        await self.verificar_esquema()
        return await self.collection().find_one({"id_inventario": id_inventario,
                                                 "id_almacen": {"$exists": True}}, {"_id": 0})

    async def obtener_todos(self):
        await self.verificar_esquema()
        return await self.collection().find({"id_almacen": {"$exists": True}}, {"_id": 0}).to_list(length=None)

    async def obtener_por_almacenes(self, ids):
        await self.verificar_esquema()
        return await self.collection().find({"id_almacen": {"$in": list(ids)}}, {"_id": 0}).to_list(length=None)

    async def obtener_historial(self, identifier):
        from app.repositories.historial_inventario import consultar_historial
        return await consultar_historial("id_inventario", identifier)
