from typing import (
    List,
    Optional
)

from app.database.mongodb import (
    get_database
)


class AlertaRepository:

    COLLECTION_NAME = "alertas"

    # ============================================================
    # COLLECTION
    #
    # IMPORTANTE:
    # No obtenemos MongoDB en __init__.
    #
    # La conexión se obtiene únicamente cuando realmente
    # se ejecuta una operación del repositorio.
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
        alerta: dict
    ) -> dict:

        documento = alerta.copy()

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
        id_alerta: str
    ) -> Optional[dict]:

        return await self.collection().find_one(
            {
                "id_alerta":
                    id_alerta
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
    # LISTAR POR NIVEL DE RIESGO
    # ============================================================

    async def listar_por_nivel(
        self,
        nivel_riesgo: str
    ) -> List[dict]:

        cursor = (
            self.collection()
            .find(
                {
                    "nivel_riesgo":
                        nivel_riesgo
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
    # BUSCAR ALERTA ACTIVA
    # ============================================================

    async def buscar_activa(
        self,
        id_inventario: str,
        tipo_alerta: str,
        id_producto: str | None = None,
        id_detalle_inventario: str | None = None
    ) -> Optional[dict]:

        return await self.collection().find_one(
            {
                "id_inventario":
                    id_inventario,

                "id_producto": id_producto,
                "id_detalle_inventario": id_detalle_inventario,
                "tipo_alerta":
                    tipo_alerta,

                "estado": {
                    "$in": [
                        "ACTIVA",
                        "VISTA"
                    ]
                }
            },
            {
                "_id": 0
            }
        )

    # ============================================================
    # SENSORES: ALERTAS ABIERTAS
    #
    # origen = SENSOR y estado ACTIVA / VISTA.
    # ids_dispositivo = None -> todas.
    # ============================================================

    async def listar_abiertas_sensores(
        self,
        ids_dispositivo: Optional[List[str]] = None
    ) -> List[dict]:

        filtro = {
            "origen": "SENSOR",
            "estado": {
                "$in": [
                    "ACTIVA",
                    "VISTA"
                ]
            }
        }

        if ids_dispositivo is not None:
            filtro["id_dispositivo"] = {
                "$in": list(ids_dispositivo)
            }

        cursor = self.collection().find(
            filtro,
            {
                "_id": 0
            }
        ).sort(
            "inicio",
            -1
        )

        return await cursor.to_list(
            length=None
        )

    # ============================================================
    # ACTUALIZAR
    # ============================================================

    async def actualizar(
        self,
        id_alerta: str,
        datos: dict
    ) -> Optional[dict]:

        resultado = (
            await self.collection().update_one(
                {
                    "id_alerta":
                        id_alerta
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
            id_alerta
        )

    # ============================================================
    # ELIMINAR
    # ============================================================

    async def eliminar(
        self,
        id_alerta: str
    ) -> bool:

        resultado = (
            await self.collection().delete_one(
                {
                    "id_alerta":
                        id_alerta
                }
            )
        )

        return (
            resultado.deleted_count > 0
        )