from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, Dict, Any, List

from app.database.mongodb import get_database


class OperarioRepository:

    COLLECTION_NAME = "operarios"

    # IMPORTANTE:
    # Los documentos devueltos incluyen password_hash.
    # El service debe sanitizarlos antes de responder.

    @staticmethod
    def collection():
        return get_database()[
            OperarioRepository.COLLECTION_NAME
        ]


    @staticmethod
    async def crear(
        data: Dict[str, Any]
    ) -> Dict[str, Any]:

        now = datetime.now(
            timezone.utc
        )

        operario = {
            "id_operario": str(uuid4()),
            "id_empresa": data["id_empresa"],
            "id_almacen": data.get("id_almacen"),

            "nombre": data["nombre"],
            "apellido": data["apellido"],
            "cargo": data["cargo"],
            "turno": data["turno"],
            "estado": data["estado"],

            "correo": data.get("correo"),
            "correo_verificado": data.get("correo_verificado", False),
            "fecha_verificacion_correo": data.get("fecha_verificacion_correo"),
            "password_hash": data.get("password_hash"),
            "debe_cambiar_password": data.get(
                "debe_cambiar_password",
                False
            ),

            "fecha_creacion": now,
            "fecha_actualizacion": now
        }

        await (
            OperarioRepository
            .collection()
            .insert_one(operario)
        )

        return await (
            OperarioRepository
            .obtener_por_id(
                operario["id_operario"]
            )
        )


    @staticmethod
    async def obtener_todos(
    ) -> List[Dict[str, Any]]:

        cursor = (
            OperarioRepository
            .collection()
            .find(
                {},
                {"_id": 0}
            )
        )

        return await cursor.to_list(
            length=None
        )


    @staticmethod
    async def obtener_por_id(
        id_operario: str
    ) -> Optional[Dict[str, Any]]:

        return await (
            OperarioRepository
            .collection()
            .find_one(
                {
                    "id_operario":
                        id_operario
                },
                {
                    "_id": 0
                }
            )
        )


    # ============================================================
    # OBTENER POR CORREO (LOGIN)
    # ============================================================

    @staticmethod
    async def obtener_por_correo(
        correo: str
    ) -> Optional[Dict[str, Any]]:

        return await (
            OperarioRepository
            .collection()
            .find_one(
                {
                    "correo":
                        correo.lower().strip()
                },
                {
                    "_id": 0
                }
            )
        )


    # ============================================================
    # NOMBRES POR IDS
    #
    # {id_operario: "Nombre Apellido"} para historiales.
    # ============================================================

    @staticmethod
    async def nombres_por_ids(
        ids_operario: List[Optional[str]]
    ) -> Dict[str, str]:

        ids = list(
            {
                id_operario
                for id_operario in ids_operario
                if id_operario
            }
        )

        if not ids:
            return {}

        cursor = (
            OperarioRepository
            .collection()
            .find(
                {
                    "id_operario": {
                        "$in": ids
                    }
                },
                {
                    "_id": 0,
                    "id_operario": 1,
                    "nombre": 1,
                    "apellido": 1
                }
            )
        )

        return {
            operario["id_operario"]: (
                f"{operario.get('nombre', '')} "
                f"{operario.get('apellido', '')}"
            ).strip()
            for operario in await cursor.to_list(
                length=None
            )
        }


    @staticmethod
    async def obtener_por_empresa(
        id_empresa: str
    ) -> List[Dict[str, Any]]:

        cursor = (
            OperarioRepository
            .collection()
            .find(
                {
                    "id_empresa":
                        id_empresa
                },
                {
                    "_id": 0
                }
            )
        )

        return await cursor.to_list(
            length=None
        )


    @staticmethod
    async def obtener_por_estado(
        estado: str
    ) -> List[Dict[str, Any]]:

        cursor = (
            OperarioRepository
            .collection()
            .find(
                {
                    "estado": {
                        "$regex":
                            f"^{estado}$",
                        "$options":
                            "i"
                    }
                },
                {
                    "_id": 0
                }
            )
        )

        return await cursor.to_list(
            length=None
        )


    @staticmethod
    async def obtener_por_turno(
        turno: str
    ) -> List[Dict[str, Any]]:

        cursor = (
            OperarioRepository
            .collection()
            .find(
                {
                    "turno": {
                        "$regex":
                            f"^{turno}$",
                        "$options":
                            "i"
                    }
                },
                {
                    "_id": 0
                }
            )
        )

        return await cursor.to_list(
            length=None
        )


    @staticmethod
    async def actualizar(
        id_operario: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        data = dict(
            data
        )

        data[
            "fecha_actualizacion"
        ] = datetime.now(
            timezone.utc
        )

        result = await (
            OperarioRepository
            .collection()
            .update_one(
                {
                    "id_operario":
                        id_operario
                },
                {
                    "$set":
                        data
                }
            )
        )

        if result.matched_count == 0:
            return None

        return await (
            OperarioRepository
            .obtener_por_id(
                id_operario
            )
        )


    # ============================================================
    # ACTUALIZAR PASSWORD
    # ============================================================

    @staticmethod
    async def actualizar_password(
        id_operario: str,
        password_hash: str,
        debe_cambiar_password: bool
    ) -> Optional[Dict[str, Any]]:

        return await (
            OperarioRepository
            .actualizar(
                id_operario,
                {
                    "password_hash":
                        password_hash,

                    "debe_cambiar_password":
                        debe_cambiar_password
                }
            )
        )


    @staticmethod
    async def eliminar(
        id_operario: str
    ) -> bool:

        result = await (
            OperarioRepository
            .collection()
            .delete_one(
                {
                    "id_operario":
                        id_operario
                }
            )
        )

        return (
            result.deleted_count > 0
        )
