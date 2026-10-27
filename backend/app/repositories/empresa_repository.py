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


class EmpresaRepository:

    COLLECTION_NAME = "empresas"


    # ============================================================
    # COLLECTION
    # ============================================================

    @staticmethod
    def collection():

        database = get_database()

        return database[
            EmpresaRepository.COLLECTION_NAME
        ]


    # ============================================================
    # CREAR
    # ============================================================

    @staticmethod
    async def crear(
        empresa: Dict[str, Any]
    ) -> Dict[str, Any]:

        collection = (
            EmpresaRepository.collection()
        )

        await collection.insert_one(
            empresa
        )

        return await (
            EmpresaRepository.obtener_por_id(
                empresa["id_empresa"]
            )
        )


    # ============================================================
    # OBTENER TODAS
    # ============================================================

    @staticmethod
    async def obtener_todas() -> List[Dict[str, Any]]:

        collection = (
            EmpresaRepository.collection()
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
        id_empresa: str
    ) -> Optional[Dict[str, Any]]:

        collection = (
            EmpresaRepository.collection()
        )

        return await collection.find_one(
            {
                "id_empresa": id_empresa
            },
            {
                "_id": 0
            }
        )


    # ============================================================
    # OBTENER POR CORREO
    # ============================================================

    @staticmethod
    async def obtener_por_correo(
        correo: str
    ) -> Optional[Dict[str, Any]]:

        collection = (
            EmpresaRepository.collection()
        )

        return await collection.find_one(
            {
                "correo":
                    correo.lower().strip()
            },
            {
                "_id": 0
            }
        )


    # ============================================================
    # OBTENER POR RUC
    # ============================================================

    @staticmethod
    async def obtener_por_ruc(
        ruc: str
    ) -> Optional[Dict[str, Any]]:

        collection = (
            EmpresaRepository.collection()
        )

        return await collection.find_one(
            {
                "ruc": ruc.strip()
            },
            {
                "_id": 0
            }
        )


    # ============================================================
    # ACTUALIZAR
    # ============================================================

    @staticmethod
    async def actualizar(
        id_empresa: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        collection = (
            EmpresaRepository.collection()
        )

        data["fecha_actualizacion"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        result = await collection.update_one(
            {
                "id_empresa": id_empresa
            },
            {
                "$set": data
            }
        )

        if result.matched_count == 0:

            return None

        return await (
            EmpresaRepository.obtener_por_id(
                id_empresa
            )
        )


    # ============================================================
    # ACTUALIZAR PASSWORD
    # ============================================================

    @staticmethod
    async def actualizar_password(
        id_empresa: str,
        password_hash: str
    ) -> bool:

        collection = (
            EmpresaRepository.collection()
        )

        result = await collection.update_one(
            {
                "id_empresa": id_empresa
            },
            {
                "$set": {
                    "password":
                        password_hash,

                    "fecha_actualizacion":
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                }
            }
        )

        return (
            result.matched_count > 0
        )


    # ============================================================
    # ELIMINAR
    # ============================================================

    @staticmethod
    async def eliminar(
        id_empresa: str
    ) -> bool:

        collection = (
            EmpresaRepository.collection()
        )

        result = await collection.delete_one(
            {
                "id_empresa": id_empresa
            }
        )

        return (
            result.deleted_count > 0
        )


# ============================================================
# FUNCIONES COMPATIBLES CON EL NUEVO SERVICE
# ============================================================

async def find_by_id(
    id_empresa: str
):

    return await (
        EmpresaRepository.obtener_por_id(
            id_empresa
        )
    )


async def find_by_email(
    correo: str
):

    return await (
        EmpresaRepository.obtener_por_correo(
            correo
        )
    )


async def find_by_ruc(
    ruc: str
):

    return await (
        EmpresaRepository.obtener_por_ruc(
            ruc
        )
    )


async def create_empresa(
    empresa: Dict[str, Any]
):

    return await (
        EmpresaRepository.crear(
            empresa
        )
    )


async def update_empresa(
    id_empresa: str,
    data: Dict[str, Any]
):

    return await (
        EmpresaRepository.actualizar(
            id_empresa,
            data
        )
    )


async def update_password(
    id_empresa: str,
    password_hash: str
):

    return await (
        EmpresaRepository.actualizar_password(
            id_empresa,
            password_hash
        )
    )


async def delete_empresa(
    id_empresa: str
):

    return await (
        EmpresaRepository.eliminar(
            id_empresa
        )
    )