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


class ZonaRepository:

    COLLECTION_NAME = "zonas"


    # ============================================================
    # COLLECTION
    # ============================================================

    @staticmethod
    def collection():

        database = get_database()

        return database[
            ZonaRepository.COLLECTION_NAME
        ]


    # ============================================================
    # CREAR
    # ============================================================

    @staticmethod
    async def crear(
        zona: Dict[str, Any]
    ) -> Dict[str, Any]:

        collection = (
            ZonaRepository.collection()
        )

        await collection.insert_one(
            zona
        )

        return await (
            ZonaRepository.obtener_por_id(
                zona["id"]
            )
        )


    # ============================================================
    # OBTENER TODAS
    # ============================================================

    @staticmethod
    async def obtener_todas() -> List[Dict[str, Any]]:

        collection = (
            ZonaRepository.collection()
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
    # id_zona
    # ============================================================

    @staticmethod
    async def obtener_por_id(
        id_zona: str
    ) -> Optional[Dict[str, Any]]:

        collection = (
            ZonaRepository.collection()
        )

        return await collection.find_one(
            {
                "$or": [
                    {
                        "id": id_zona
                    },
                    {
                        "id_zona": id_zona
                    }
                ]
            },
            {
                "_id": 0
            }
        )


    # ============================================================
    # OBTENER POR ALMACEN
    # ============================================================

    @staticmethod
    async def obtener_por_almacen(
        id_almacen: str
    ) -> List[Dict[str, Any]]:

        collection = (
            ZonaRepository.collection()
        )

        cursor = collection.find(
            {
                "id_almacen": id_almacen
            },
            {
                "_id": 0
            }
        )

        return await cursor.to_list(
            length=None
        )


    # ============================================================
    # OBTENER POR VARIOS ALMACENES
    #
    # Usado para calcular el alcance (empresa / operario).
    # ============================================================

    @staticmethod
    async def obtener_por_almacenes(
        ids_almacen: List[str]
    ) -> List[Dict[str, Any]]:

        collection = (
            ZonaRepository.collection()
        )

        cursor = collection.find(
            {
                "id_almacen": {
                    "$in": list(ids_almacen)
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
        id_zona: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        collection = (
            ZonaRepository.collection()
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
                        "id": id_zona
                    },
                    {
                        "id_zona": id_zona
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
            ZonaRepository.obtener_por_id(
                id_zona
            )
        )


    # ============================================================
    # ELIMINAR
    # ============================================================

    @staticmethod
    async def eliminar(
        id_zona: str
    ) -> bool:

        collection = (
            ZonaRepository.collection()
        )

        result = await collection.delete_one(
            {
                "$or": [
                    {
                        "id": id_zona
                    },
                    {
                        "id_zona": id_zona
                    }
                ]
            }
        )

        return (
            result.deleted_count > 0
        )