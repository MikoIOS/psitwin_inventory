from datetime import datetime, timezone
from uuid import uuid4

from app.database.mongodb import get_database


class OrdenReposicionRepository:

    COLLECTION_NAME = "ordenes_reposicion"

    def collection(self):
        return get_database()[self.COLLECTION_NAME]

    async def crear(self, data: dict):

        ahora = datetime.now(timezone.utc)

        documento = data.copy()

        documento["id_orden_reposicion"] = str(uuid4())
        documento["fecha_orden"] = ahora
        documento["fecha_creacion"] = ahora
        documento["fecha_actualizacion"] = ahora

        await self.collection().insert_one(documento)

        return await self.obtener_por_id(
            documento["id_orden_reposicion"]
        )

    async def obtener_todos(self):

        cursor = self.collection().find(
            {},
            {"_id": 0}
        ).sort("fecha_orden", -1)

        return await cursor.to_list(length=None)

    async def obtener_por_id(
        self,
        id_orden_reposicion: str
    ):

        return await self.collection().find_one(
            {
                "id_orden_reposicion":
                    id_orden_reposicion
            },
            {"_id": 0}
        )

    async def obtener_por_empresa(
        self,
        id_empresa: str
    ):

        cursor = self.collection().find(
            {"id_empresa": id_empresa},
            {"_id": 0}
        ).sort("fecha_orden", -1)

        return await cursor.to_list(length=None)

    async def obtener_por_almacen(
        self,
        id_almacen: str
    ):

        cursor = self.collection().find(
            {"id_almacen": id_almacen},
            {"_id": 0}
        ).sort("fecha_orden", -1)

        return await cursor.to_list(length=None)

    async def obtener_por_proveedor(
        self,
        id_proveedor: str
    ):

        cursor = self.collection().find(
            {"id_proveedor": id_proveedor},
            {"_id": 0}
        ).sort("fecha_orden", -1)

        return await cursor.to_list(length=None)

    async def obtener_por_proveedor_y_estados(
        self,
        id_proveedor: str,
        estados: list
    ):

        cursor = self.collection().find(
            {
                "id_proveedor": id_proveedor,
                "estado": {"$in": estados}
            },
            {"_id": 0}
        ).sort("fecha_orden", -1)

        return await cursor.to_list(length=None)

    async def obtener_por_recomendacion(
        self,
        id_recomendacion: str,
    ):
        return await self.collection().find_one(
            {"id_recomendacion": id_recomendacion},
            {"_id": 0},
        )

    async def obtener_por_estado(
        self,
        estado: str
    ):

        cursor = self.collection().find(
            {"estado": estado},
            {"_id": 0}
        ).sort("fecha_orden", -1)

        return await cursor.to_list(length=None)

    async def actualizar(
        self,
        id_orden_reposicion: str,
        data: dict
    ):

        cambios = data.copy()

        cambios["fecha_actualizacion"] = (
            datetime.now(timezone.utc)
        )

        await self.collection().update_one(
            {
                "id_orden_reposicion":
                    id_orden_reposicion
            },
            {"$set": cambios}
        )

        return await self.obtener_por_id(
            id_orden_reposicion
        )

    async def cambiar_estado(
        self,
        id_orden_reposicion: str,
        estado: str
    ):

        return await self.actualizar(
            id_orden_reposicion,
            {"estado": estado}
        )

    async def eliminar(
        self,
        id_orden_reposicion: str
    ):

        resultado = await self.collection().delete_one(
            {
                "id_orden_reposicion":
                    id_orden_reposicion
            }
        )

        return resultado.deleted_count > 0