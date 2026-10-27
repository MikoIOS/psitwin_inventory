# app/repositories/inventory_risk_repository.py

from datetime import datetime

from typing import (
    List,
    Optional
)

from app.database.mongodb import (
    get_database
)


class InventoryRiskRepository:

    # ============================================================
    # NOMBRES DE COLECCIONES
    # ============================================================

    INVENTARIOS_COLLECTION = "inventarios"
    PRODUCTOS_COLLECTION = "productos"
    MOVIMIENTOS_COLLECTION = "movimientos"
    RACKS_COLLECTION = "racks"
    ZONAS_COLLECTION = "zonas"
    ALMACENES_COLLECTION = "almacenes"


    # ============================================================
    # DATABASE
    #
    # IMPORTANTE:
    #
    # No usamos:
    #
    # def __init__(self):
    #     self.db = get_database()
    #
    # porque InventoryRiskService se instancia durante la
    # importación de los controllers.
    #
    # En ese momento FastAPI todavía no ejecutó lifespan()
    # y MongoDB aún no fue conectado.
    #
    # Por eso obtenemos la base de datos solamente cuando
    # realmente se ejecuta una operación.
    # ============================================================

    def database(self):

        return get_database()


    # ============================================================
    # COLLECTIONS
    # ============================================================

    def inventarios_collection(self):

        return self.database()[
            self.INVENTARIOS_COLLECTION
        ]


    def productos_collection(self):

        return self.database()[
            self.PRODUCTOS_COLLECTION
        ]


    def movimientos_collection(self):

        return self.database()[
            self.MOVIMIENTOS_COLLECTION
        ]


    def racks_collection(self):

        return self.database()[
            self.RACKS_COLLECTION
        ]


    def zonas_collection(self):

        return self.database()[
            self.ZONAS_COLLECTION
        ]


    def almacenes_collection(self):

        return self.database()[
            self.ALMACENES_COLLECTION
        ]


    # ============================================================
    # OBTENER INVENTARIO
    # ============================================================

    async def obtener_inventario(self, id_inventario):
        from app.repositories.inventario_repository import InventarioRepository
        return await InventarioRepository().obtener_por_id(id_inventario)

    async def listar_inventarios(self):
        from app.repositories.inventario_repository import InventarioRepository
        return await InventarioRepository().obtener_todos()

    async def obtener_producto(
        self,
        id_producto: str
    ) -> Optional[dict]:

        return await (
            self.productos_collection()
            .find_one(
                {
                    "$or": [
                        {
                            "id_producto":
                                id_producto
                        },
                        {
                            "id":
                                id_producto
                        }
                    ]
                },
                {
                    "_id": 0
                }
            )
        )


    # ============================================================
    # OBTENER RACK
    # ============================================================

    async def obtener_rack(
        self,
        id_rack: str
    ) -> Optional[dict]:

        return await (
            self.racks_collection()
            .find_one(
                {
                    "$or": [
                        {
                            "id_rack":
                                id_rack
                        },
                        {
                            "id":
                                id_rack
                        }
                    ]
                },
                {
                    "_id": 0
                }
            )
        )


    # ============================================================
    # OBTENER ZONA
    # ============================================================

    async def obtener_zona(
        self,
        id_zona: str
    ) -> Optional[dict]:

        return await (
            self.zonas_collection()
            .find_one(
                {
                    "$or": [
                        {
                            "id_zona":
                                id_zona
                        },
                        {
                            "id":
                                id_zona
                        }
                    ]
                },
                {
                    "_id": 0
                }
            )
        )


    # ============================================================
    # OBTENER ALMACEN
    # ============================================================

    async def obtener_almacen(
        self,
        id_almacen: str
    ) -> Optional[dict]:

        return await (
            self.almacenes_collection()
            .find_one(
                {
                    "$or": [
                        {
                            "id_almacen":
                                id_almacen
                        },
                        {
                            "id":
                                id_almacen
                        }
                    ]
                },
                {
                    "_id": 0
                }
            )
        )


    # ============================================================
    # OBTENER SALIDAS DESDE UNA FECHA
    #
    # Utilizado por InventoryRiskService para calcular:
    #
    # - consumo reciente
    # - demanda promedio
    # - cobertura
    # - riesgo de quiebre
    # ============================================================

    async def obtener_salidas_desde(
        self,
        id_inventario: str,
        fecha_desde: datetime,
        id_producto: str
    ) -> List[dict]:

        cursor = (
            self.movimientos_collection()
            .find(
                {
                    "id_inventario":
                        id_inventario,

                    "tipo_movimiento":
                        "SALIDA",

                    "fecha_hora": {
                        "$gte":
                            fecha_desde
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