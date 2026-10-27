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


class MovimientoRepository:

    COLLECTION_NAME = "movimientos"


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

        documento = dict(data)

        documento[
            "id_movimiento"
        ] = str(
            uuid4()
        )

        # Si el servicio no envía fecha_hora,
        # utilizamos la fecha actual.
        if not documento.get(
            "fecha_hora"
        ):

            documento[
                "fecha_hora"
            ] = datetime.now(
                timezone.utc
            )

        await self.collection().insert_one(
            documento
        )

        return await self.obtener_por_id(
            documento[
                "id_movimiento"
            ]
        )


    # ============================================================
    # OBTENER TODOS
    # ============================================================

    async def obtener_todos(
        self
    ) -> List[Dict[str, Any]]:

        cursor = (
            self.collection()
            .find(
                {},
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR ID
    # ============================================================

    async def obtener_por_id(
        self,
        id_movimiento: str
    ) -> Optional[Dict[str, Any]]:

        return await self.collection().find_one(
            {
                "id_movimiento":
                    id_movimiento
            },
            {
                "_id": 0
            }
        )

    async def obtener_por_detalle_recepcion(
        self,
        id_detalle_recepcion: str
    ) -> Optional[Dict[str, Any]]:
        return await self.collection().find_one(
            {
                "id_detalle_recepcion":
                    id_detalle_recepcion
            },
            {
                "_id": 0
            }
        )

    async def eliminar(
        self,
        id_movimiento: str
    ) -> bool:
        resultado = await self.collection().delete_one(
            {
                "id_movimiento": id_movimiento
            }
        )
        return resultado.deleted_count > 0


    # ============================================================
    # OBTENER POR INVENTARIO
    # ============================================================

    async def obtener_por_inventario(
        self,
        id_inventario: str
    ) -> List[Dict[str, Any]]:

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
                "fecha_hora",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR PRODUCTO
    # ============================================================

    async def obtener_por_producto(
        self,
        id_producto: str
    ) -> List[Dict[str, Any]]:

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
                "fecha_hora",
                -1
            )
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

        cursor = (
            self.collection()
            .find(
                {
                    "id_rack":
                        id_rack
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR OPERARIO
    # ============================================================

    async def obtener_por_operario(
        self,
        id_operario: str
    ) -> List[Dict[str, Any]]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_operario":
                        id_operario
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR TIPO
    # ============================================================

    async def obtener_por_tipo(
        self,
        tipo_movimiento: str
    ) -> List[Dict[str, Any]]:

        cursor = (
            self.collection()
            .find(
                {
                    "tipo_movimiento":
                        tipo_movimiento
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR MOTIVO
    # ============================================================

    async def obtener_por_motivo(
        self,
        motivo_movimiento: str
    ) -> List[Dict[str, Any]]:

        cursor = (
            self.collection()
            .find(
                {
                    "motivo_movimiento":
                        motivo_movimiento
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                -1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # MOVIMIENTOS POR RANGO DE FECHAS
    # ============================================================

    async def obtener_por_rango_fechas(
        self,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[Dict[str, Any]]:

        cursor = (
            self.collection()
            .find(
                {
                    "fecha_hora": {
                        "$gte":
                            fecha_inicio,

                        "$lte":
                            fecha_fin
                    }
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # MOVIMIENTOS DE INVENTARIO POR RANGO
    # ============================================================

    async def obtener_por_inventario_y_rango(
        self,
        id_inventario: str,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[Dict[str, Any]]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_inventario":
                        id_inventario,

                    "fecha_hora": {
                        "$gte":
                            fecha_inicio,

                        "$lte":
                            fecha_fin
                    }
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # MOVIMIENTOS DE PRODUCTO POR RANGO
    # ============================================================

    async def obtener_por_producto_y_rango(
        self,
        id_producto: str,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[Dict[str, Any]]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_producto":
                        id_producto,

                    "fecha_hora": {
                        "$gte":
                            fecha_inicio,

                        "$lte":
                            fecha_fin
                    }
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # SALIDAS DE INVENTARIO POR RANGO
    #
    # Esta será una de las consultas principales para ML.
    #
    # Para forecasting nos interesa el consumo/demanda.
    #
    # Por ello filtramos:
    #
    # tipo_movimiento = SALIDA
    # ============================================================

    async def obtener_salidas_inventario_por_rango(
        self,
        id_inventario: str,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[Dict[str, Any]]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_inventario":
                        id_inventario,

                    "tipo_movimiento":
                        "SALIDA",

                    "fecha_hora": {
                        "$gte":
                            fecha_inicio,

                        "$lte":
                            fecha_fin
                    }
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # SALIDAS DE PRODUCTO POR RANGO
    # ============================================================

    async def obtener_salidas_producto_por_rango(
        self,
        id_producto: str,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[Dict[str, Any]]:

        cursor = (
            self.collection()
            .find(
                {
                    "id_producto":
                        id_producto,

                    "tipo_movimiento":
                        "SALIDA",

                    "fecha_hora": {
                        "$gte":
                            fecha_inicio,

                        "$lte":
                            fecha_fin
                    }
                },
                {
                    "_id": 0
                }
            )
            .sort(
                "fecha_hora",
                1
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # CONSUMO AGREGADO POR DIA DE UN INVENTARIO
    #
    # MongoDB agrupa las SALIDAS por fecha.
    #
    # Resultado:
    #
    # [
    #     {
    #         "fecha": "2026-09-20",
    #         "cantidad": 15,
    #         "numero_movimientos": 2
    #     }
    # ]
    # ============================================================

    async def obtener_consumo_diario_inventario(
        self,
        id_inventario: str,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[Dict[str, Any]]:

        pipeline = [

            # ----------------------------------------------------
            # FILTRAR
            # ----------------------------------------------------

            {
                "$match": {

                    "id_inventario":
                        id_inventario,

                    "tipo_movimiento":
                        "SALIDA",

                    "fecha_hora": {
                        "$gte":
                            fecha_inicio,

                        "$lte":
                            fecha_fin
                    }
                }
            },

            # ----------------------------------------------------
            # AGRUPAR POR DIA
            # ----------------------------------------------------

            {
                "$group": {

                    "_id": {
                        "$dateToString": {
                            "format":
                                "%Y-%m-%d",

                            "date":
                                "$fecha_hora",

                            "timezone":
                                "UTC"
                        }
                    },

                    "cantidad": {
                        "$sum":
                            "$cantidad"
                    },

                    "numero_movimientos": {
                        "$sum":
                            1
                    }
                }
            },

            # ----------------------------------------------------
            # ORDENAR
            # ----------------------------------------------------

            {
                "$sort": {
                    "_id":
                        1
                }
            },

            # ----------------------------------------------------
            # FORMATO DE SALIDA
            # ----------------------------------------------------

            {
                "$project": {

                    "_id":
                        0,

                    "fecha":
                        "$_id",

                    "cantidad":
                        1,

                    "numero_movimientos":
                        1
                }
            }
        ]

        cursor = self.collection().aggregate(
            pipeline
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # CONSUMO AGREGADO POR DIA DE UN PRODUCTO
    #
    # NUEVO PARA ML
    #
    # A diferencia de:
    #
    # obtener_consumo_diario_inventario()
    #
    # aquí agrupamos todas las SALIDAS del mismo producto,
    # independientemente del inventario/rack donde se encuentre.
    #
    # Esto nos permitirá construir:
    #
    # item_total_lag_1
    # item_total_lag_7
    # item_total_lag_28
    #
    # ============================================================

    async def obtener_consumo_diario_producto(
        self,
        id_producto: str,
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[Dict[str, Any]]:

        pipeline = [

            # ----------------------------------------------------
            # FILTRAR
            # ----------------------------------------------------

            {
                "$match": {

                    "id_producto":
                        id_producto,

                    "tipo_movimiento":
                        "SALIDA",

                    "fecha_hora": {
                        "$gte":
                            fecha_inicio,

                        "$lte":
                            fecha_fin
                    }
                }
            },

            # ----------------------------------------------------
            # AGRUPAR POR DIA
            # ----------------------------------------------------

            {
                "$group": {

                    "_id": {
                        "$dateToString": {

                            "format":
                                "%Y-%m-%d",

                            "date":
                                "$fecha_hora",

                            "timezone":
                                "UTC"
                        }
                    },

                    "cantidad": {
                        "$sum":
                            "$cantidad"
                    },

                    "numero_movimientos": {
                        "$sum":
                            1
                    }
                }
            },

            # ----------------------------------------------------
            # ORDENAR
            # ----------------------------------------------------

            {
                "$sort": {

                    "_id":
                        1
                }
            },

            # ----------------------------------------------------
            # FORMATO
            # ----------------------------------------------------

            {
                "$project": {

                    "_id":
                        0,

                    "fecha":
                        "$_id",

                    "cantidad":
                        1,

                    "numero_movimientos":
                        1
                }
            }
        ]

        cursor = (
            self.collection()
            .aggregate(
                pipeline
            )
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # CONSUMO AGREGADO POR DIA DE VARIOS PRODUCTOS
    #
    # NUEVO PARA ML
    #
    # Recibe una lista:
    #
    # [
    #     "id_producto_1",
    #     "id_producto_2",
    #     "id_producto_3"
    # ]
    #
    # y suma las SALIDAS de TODOS esos productos por día.
    #
    # Esta función será reutilizada para:
    #
    # 1. PRODUCTOS DEL ALMACEN
    #
    #       -> store_sales_*
    #
    # 2. PRODUCTOS DE LA MISMA CATEGORIA
    #
    #       -> dept_sales_*
    #
    # ============================================================

    async def obtener_consumo_diario_productos(
        self,
        ids_productos: List[str],
        fecha_inicio: datetime,
        fecha_fin: datetime
    ) -> List[Dict[str, Any]]:

        # --------------------------------------------------------
        # VALIDAR LISTA
        # --------------------------------------------------------

        if not ids_productos:

            return []

        # Eliminar:
        #
        # None
        # strings vacíos
        # duplicados
        #
        # Manteniendo IDs como string.

        ids_limpios = list(
            dict.fromkeys(
                str(id_producto)
                for id_producto in ids_productos
                if id_producto
            )
        )

        if not ids_limpios:

            return []

        # --------------------------------------------------------
        # PIPELINE
        # --------------------------------------------------------

        pipeline = [

            # ----------------------------------------------------
            # FILTRAR PRODUCTOS + SALIDAS + FECHA
            # ----------------------------------------------------

            {
                "$match": {

                    "id_producto": {
                        "$in":
                            ids_limpios
                    },

                    "tipo_movimiento":
                        "SALIDA",

                    "fecha_hora": {
                        "$gte":
                            fecha_inicio,

                        "$lte":
                            fecha_fin
                    }
                }
            },

            # ----------------------------------------------------
            # AGRUPAR TODOS LOS PRODUCTOS POR DIA
            # ----------------------------------------------------

            {
                "$group": {

                    "_id": {
                        "$dateToString": {

                            "format":
                                "%Y-%m-%d",

                            "date":
                                "$fecha_hora",

                            "timezone":
                                "UTC"
                        }
                    },

                    "cantidad": {
                        "$sum":
                            "$cantidad"
                    },

                    "numero_movimientos": {
                        "$sum":
                            1
                    },

                    # Cantidad de productos diferentes
                    # que tuvieron movimiento ese día.

                    "productos_con_movimiento": {
                        "$addToSet":
                            "$id_producto"
                    }
                }
            },

            # ----------------------------------------------------
            # ORDENAR
            # ----------------------------------------------------

            {
                "$sort": {

                    "_id":
                        1
                }
            },

            # ----------------------------------------------------
            # FORMATO
            # ----------------------------------------------------

            {
                "$project": {

                    "_id":
                        0,

                    "fecha":
                        "$_id",

                    "cantidad":
                        1,

                    "numero_movimientos":
                        1,

                    "numero_productos": {
                        "$size":
                            "$productos_con_movimiento"
                    }
                }
            }
        ]

        cursor = (
            self.collection()
            .aggregate(
                pipeline
            )
        )

        return await cursor.to_list(
            length=None
        )