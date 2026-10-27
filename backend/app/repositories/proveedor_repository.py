from datetime import datetime, timezone
from uuid import uuid4

from app.database.mongodb import get_database


class ProveedorRepository:

    COLLECTION_NAME = "proveedores"

    def collection(self):
        return get_database()[self.COLLECTION_NAME]

    async def crear(self, data: dict):

        ahora = datetime.now(timezone.utc)

        documento = data.copy()

        documento["id_proveedor"] = str(uuid4())
        documento["fecha_creacion"] = ahora
        documento["fecha_actualizacion"] = ahora

        await self.collection().insert_one(documento)

        return await self.obtener_por_id(
            documento["id_proveedor"]
        )

    async def obtener_todos(self):

        cursor = self.collection().find(
            {},
            {"_id": 0}
        )

        return await cursor.to_list(length=None)

    async def obtener_por_id(self, id_proveedor: str):

        return await self.collection().find_one(
            {"id_proveedor": id_proveedor},
            {"_id": 0}
        )

    # ========================================================
    # POR CORREO (LOGIN / UNICIDAD)
    #
    # Solo proveedores con cuenta: los proveedores antiguos
    # sin cuenta pueden compartir correo de contacto.
    # ========================================================

    async def obtener_por_correo_con_cuenta(self, correo: str):

        return await self.collection().find_one(
            {
                "correo": correo.lower().strip(),
                "password_hash": {"$type": "string"}
            },
            {"_id": 0}
        )

    async def obtener_por_ruc(self, ruc: str):

        return await self.collection().find_one(
            {"ruc": ruc},
            {"_id": 0}
        )

    async def obtener_por_empresa(self, id_empresa: str):

        cursor = self.collection().find(
            {"id_empresa": id_empresa},
            {"_id": 0}
        )

        return await cursor.to_list(length=None)

    async def obtener_por_estado(self, estado: str):

        cursor = self.collection().find(
            {"estado": estado},
            {"_id": 0}
        )

        return await cursor.to_list(length=None)

    async def actualizar(
        self,
        id_proveedor: str,
        data: dict
    ):

        cambios = data.copy()

        cambios["fecha_actualizacion"] = (
            datetime.now(timezone.utc)
        )

        await self.collection().update_one(
            {"id_proveedor": id_proveedor},
            {"$set": cambios}
        )

        return await self.obtener_por_id(id_proveedor)

    async def eliminar(self, id_proveedor: str):

        resultado = await self.collection().delete_one(
            {"id_proveedor": id_proveedor}
        )

        return resultado.deleted_count > 0