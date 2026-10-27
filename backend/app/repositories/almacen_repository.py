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


class AlmacenRepository:

    COLLECTION_NAME = "almacenes"


    # ============================================================
    # COLLECTION
    # ============================================================

    @staticmethod
    def collection():

        database = get_database()

        return database[
            AlmacenRepository.COLLECTION_NAME
        ]


    # ============================================================
    # CREAR
    # ============================================================

    @staticmethod
    async def crear(
        almacen: Dict[str, Any]
    ) -> Dict[str, Any]:

        collection = (
            AlmacenRepository.collection()
        )

        await collection.insert_one(
            almacen
        )

        return await (
            AlmacenRepository.obtener_por_id(
                almacen["id"]
            )
        )


    # ============================================================
    # OBTENER TODOS
    # ============================================================

    @staticmethod
    async def obtener_todos() -> List[Dict[str, Any]]:

        collection = (
            AlmacenRepository.collection()
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
    # ============================================================

    @staticmethod
    async def obtener_por_id(
        id_almacen: str
    ) -> Optional[Dict[str, Any]]:

        collection = (
            AlmacenRepository.collection()
        )

        return await collection.find_one(
            {
                "id": id_almacen
            },
            {
                "_id": 0
            }
        )


    # ============================================================
    # OBTENER POR EMPRESA
    # ============================================================

    @staticmethod
    async def obtener_por_empresa(
        id_empresa: str
    ) -> List[Dict[str, Any]]:

        collection = (
            AlmacenRepository.collection()
        )

        cursor = collection.find(
            {
                "id_empresa": id_empresa
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
        id_almacen: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        collection = (
            AlmacenRepository.collection()
        )

        data[
            "fecha_actualizacion"
        ] = datetime.now(
            timezone.utc
        )

        result = await collection.update_one(
            {
                "id": id_almacen
            },
            {
                "$set": data
            }
        )

        if result.matched_count == 0:

            return None

        return await (
            AlmacenRepository.obtener_por_id(
                id_almacen
            )
        )


    # ============================================================
    # ELIMINAR
    # ============================================================

    @staticmethod
    async def eliminar(
        id_almacen: str
    ) -> bool:

        collection = (
            AlmacenRepository.collection()
        )

        result = await collection.delete_one(
            {
                "id": id_almacen
            }
        )

        return (
            result.deleted_count > 0
        )


# ============================================================
# ALIASES
#
# Se dejan para compatibilidad por si otro archivo utiliza
# funciones en lugar de la clase.
# ============================================================

async def create_almacen(
    almacen: Dict[str, Any]
):

    return await (
        AlmacenRepository.crear(
            almacen
        )
    )


async def find_all():

    return await (
        AlmacenRepository.obtener_todos()
    )


async def find_by_id(
    id_almacen: str
):

    return await (
        AlmacenRepository.obtener_por_id(
            id_almacen
        )
    )


async def find_by_empresa(
    id_empresa: str
):

    return await (
        AlmacenRepository.obtener_por_empresa(
            id_empresa
        )
    )


async def update_almacen(
    id_almacen: str,
    data: Dict[str, Any]
):

    return await (
        AlmacenRepository.actualizar(
            id_almacen,
            data
        )
    )


async def delete_almacen(
    id_almacen: str
):

    return await (
        AlmacenRepository.eliminar(
            id_almacen
        )
    )