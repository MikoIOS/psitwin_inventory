from typing import (
    List,
    Optional
)

from app.database.mongodb import (
    get_database
)


class RecomendacionRepository:

    COLLECTION_NAME = "recomendaciones"

    # ============================================================
    # COLLECTION
    #
    # MongoDB NO se obtiene durante __init__.
    #
    # Se obtiene cuando se ejecuta una operación, después de que
    # FastAPI haya ejecutado connect_to_mongo().
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
        recomendacion: dict
    ) -> dict:

        documento = (
            recomendacion.copy()
        )

        await self.collection().insert_one(
            documento
        )

        documento.pop(
            "_id",
            None
        )

        return documento

    # ============================================================
    # OBTENER POR ID
    # ============================================================

    async def obtener_por_id(
        self,
        id_recomendacion: str
    ) -> Optional[dict]:

        return await self.collection().find_one(
            {
                "id_recomendacion":
                    id_recomendacion
            },
            {
                "_id": 0
            }
        )

    # ============================================================
    # LISTAR TODAS
    # ============================================================

    async def listar(
        self
    ) -> List[dict]:

        cursor = (
            self.collection()
            .find(
                {},
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_creacion",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )

    # ============================================================
    # LISTAR POR EMPRESA
    # ============================================================

    async def listar_por_empresa(
        self,
        id_empresa: str
    ) -> List[dict]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_empresa":
                        id_empresa
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_creacion",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )

    # ============================================================
    # LISTAR POR ALMACEN
    # ============================================================

    async def listar_por_almacen(
        self,
        id_almacen: str
    ) -> List[dict]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_almacen":
                        id_almacen
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_creacion",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )

    # ============================================================
    # LISTAR POR PRODUCTO
    # ============================================================

    async def listar_por_producto(
        self,
        id_producto: str
    ) -> List[dict]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_producto":
                        id_producto
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_creacion",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )

    # ============================================================
    # LISTAR POR INVENTARIO
    # ============================================================

    async def listar_por_inventario(
        self,
        id_inventario: str
    ) -> List[dict]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_inventario":
                        id_inventario
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_creacion",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )

    # ============================================================
    # LISTAR POR ALERTA
    # ============================================================

    async def listar_por_alerta(
        self,
        id_alerta: str
    ) -> List[dict]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_alerta":
                        id_alerta
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_creacion",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )

    # ============================================================
    # LISTAR POR ESTADO
    # ============================================================

    async def listar_por_estado(
        self,
        estado: str
    ) -> List[dict]:

        cursor = (
            self.collection()
            .find(
                {
                    "estado":
                        estado
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_creacion",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )

    # ============================================================
    # BUSCAR RECOMENDACION PENDIENTE
    # ============================================================

    async def buscar_pendiente(
        self,
        id_inventario: str,
        tipo_recomendacion: str,
        id_producto: str | None = None,
        id_detalle_inventario: str | None = None
    ) -> Optional[dict]:

        return await self.collection().find_one(
            {
                "id_inventario":
                    id_inventario,

                "id_producto": id_producto,
                "id_detalle_inventario": id_detalle_inventario,
                "tipo_recomendacion":
                    tipo_recomendacion,

                "estado": {
                    "$in": [
                        "PENDIENTE",
                        "ACEPTADA"
                    ]
                }
            },
            {
                "_id": 0
            }
        )

    # ============================================================
    # ACTUALIZAR
    # ============================================================

    async def actualizar(
        self,
        id_recomendacion: str,
        datos: dict
    ) -> Optional[dict]:

        resultado = (
            await self.collection().update_one(
                {
                    "id_recomendacion":
                        id_recomendacion
                },
                {
                    "$set":
                        datos
                }
            )
        )

        if resultado.matched_count == 0:

            return None

        return await self.obtener_por_id(
            id_recomendacion
        )

    # ============================================================
    # ELIMINAR
    # ============================================================

    async def eliminar(
        self,
        id_recomendacion: str
    ) -> bool:

        resultado = (
            await self.collection().delete_one(
                {
                    "id_recomendacion":
                        id_recomendacion
                }
            )
        )

        return (
            resultado.deleted_count > 0
        )