from datetime import (
    datetime,
    timezone
)

from typing import (
    Optional,
    Dict,
    Any,
    List
)

from app.database.mongodb import (
    get_database
)


class RackRepository:

    COLLECTION_NAME = "racks"


    # ============================================================
    # COLLECTION
    # ============================================================

    @staticmethod
    def collection():

        database = get_database()

        return database[
            RackRepository.COLLECTION_NAME
        ]


    # ============================================================
    # CREAR
    # ============================================================

    @staticmethod
    async def crear(
        rack: Dict[str, Any]
    ) -> Dict[str, Any]:

        collection = (
            RackRepository.collection()
        )

        await collection.insert_one(
            rack
        )

        id_rack = (
            rack.get("id")
            or
            rack.get("id_rack")
        )

        return await (
            RackRepository.obtener_por_id(
                id_rack
            )
        )


    # ============================================================
    # OBTENER TODOS
    # ============================================================

    @staticmethod
    async def obtener_todos() -> List[Dict[str, Any]]:

        collection = (
            RackRepository.collection()
        )

        cursor = collection.find(
            {},
            {
                "_id": 0
            }
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR ID
    #
    # Compatible con:
    #
    # id
    # id_rack
    # ============================================================

    @staticmethod
    async def obtener_por_id(
        id_rack: str
    ) -> Optional[Dict[str, Any]]:

        collection = (
            RackRepository.collection()
        )

        return await collection.find_one(
            {
                "$or": [
                    {
                        "id": id_rack
                    },
                    {
                        "id_rack": id_rack
                    }
                ]
            },
            {
                "_id": 0
            }
        )


    # ============================================================
    # OBTENER POR ZONA
    # ============================================================

    @staticmethod
    async def obtener_por_zona(
        id_zona: str
    ) -> List[Dict[str, Any]]:

        collection = (
            RackRepository.collection()
        )

        cursor = collection.find(
            {
                "id_zona": id_zona
            },
            {
                "_id": 0
            }
        )

        return await cursor.to_list(
            length=None
        )

    @staticmethod
    async def obtener_por_codigo_nivel_y_zona(
        codigo: str,
        nivel: int,
        id_zona: str
    ) -> Optional[Dict[str, Any]]:
        return await RackRepository.collection().find_one(
            {
                "codigo": codigo,
                "nivel": nivel,
                "id_zona": id_zona
            },
            {
                "_id": 0
            }
        )


    # ============================================================
    # OBTENER POR VARIAS ZONAS
    #
    # Usado para calcular el alcance y para
    # GET /racks/disponibles.
    # ============================================================

    @staticmethod
    async def obtener_por_zonas(
        ids_zona: List[str]
    ) -> List[Dict[str, Any]]:

        collection = (
            RackRepository.collection()
        )

        cursor = collection.find(
            {
                "id_zona": {
                    "$in": list(ids_zona)
                }
            },
            {
                "_id": 0
            }
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # ACTUALIZAR
    # ============================================================

    @staticmethod
    async def actualizar(
        id_rack: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        collection = (
            RackRepository.collection()
        )

        data[
            "fecha_actualizacion"
        ] = datetime.now(
            timezone.utc
        )

        result = await collection.update_one(
            {
                "$or": [
                    {
                        "id": id_rack
                    },
                    {
                        "id_rack": id_rack
                    }
                ]
            },
            {
                "$set": data
            }
        )

        if result.matched_count == 0:

            return None

        return await (
            RackRepository.obtener_por_id(
                id_rack
            )
        )


    # ============================================================
    # ELIMINAR
    # ============================================================

    @staticmethod
    async def eliminar(
        id_rack: str
    ) -> bool:

        collection = (
            RackRepository.collection()
        )

        result = await collection.delete_one(
            {
                "$or": [
                    {
                        "id": id_rack
                    },
                    {
                        "id_rack": id_rack
                    }
                ]
            }
        )

        return (
            result.deleted_count > 0
        )


# ============================================================
# FUNCIONES DE COMPATIBILIDAD
# ============================================================

async def create_rack(
    rack: Dict[str, Any]
):

    return await (
        RackRepository.crear(
            rack
        )
    )


async def find_all():

    return await (
        RackRepository.obtener_todos()
    )


async def find_by_id(
    id_rack: str
):

    return await (
        RackRepository.obtener_por_id(
            id_rack
        )
    )


async def find_by_zona(
    id_zona: str
):

    return await (
        RackRepository.obtener_por_zona(
            id_zona
        )
    )


async def update_rack(
    id_rack: str,
    data: Dict[str, Any]
):

    return await (
        RackRepository.actualizar(
            id_rack,
            data
        )
    )


async def delete_rack(
    id_rack: str
):

    return await (
        RackRepository.eliminar(
            id_rack
        )
    )