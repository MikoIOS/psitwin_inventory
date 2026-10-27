from datetime import (
    datetime,
    timezone
)

from typing import (
    Any,
    Dict,
    List,
    Optional
)

from app.database.mongodb import (
    get_database
)


class DispositivoRepository:

    COLLECTION_NAME = "dispositivos"

    # IMPORTANTE:
    # Los documentos incluyen token_hash.
    # El service debe quitarlo antes de responder.

    @staticmethod
    def collection():

        return get_database()[
            DispositivoRepository.COLLECTION_NAME
        ]


    @staticmethod
    async def crear(
        dispositivo: Dict[str, Any]
    ) -> Dict[str, Any]:

        await (
            DispositivoRepository
            .collection()
            .insert_one(
                dict(dispositivo)
            )
        )

        return await (
            DispositivoRepository.obtener_por_id(
                dispositivo["id_dispositivo"]
            )
        )


    @staticmethod
    async def obtener_por_id(
        id_dispositivo: str
    ) -> Optional[Dict[str, Any]]:

        return await (
            DispositivoRepository
            .collection()
            .find_one(
                {
                    "id_dispositivo":
                        id_dispositivo
                },
                {
                    "_id": 0
                }
            )
        )


    @staticmethod
    async def listar(
        filtro: Dict[str, Any]
    ) -> List[Dict[str, Any]]:

        cursor = (
            DispositivoRepository
            .collection()
            .find(
                filtro,
                {
                    "_id": 0
                }
            )
            .sort(
                "nombre",
                1
            )
        )

        return await cursor.to_list(
            length=None
        )


    @staticmethod
    async def actualizar(
        id_dispositivo: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        data = dict(data)

        data[
            "fecha_actualizacion"
        ] = datetime.now(
            timezone.utc
        )

        await (
            DispositivoRepository
            .collection()
            .update_one(
                {
                    "id_dispositivo":
                        id_dispositivo
                },
                {
                    "$set": data
                }
            )
        )

        return await (
            DispositivoRepository.obtener_por_id(
                id_dispositivo
            )
        )


    # ============================================================
    # ULTIMA LECTURA (en bloque, desde el consumidor)
    # ============================================================

    @staticmethod
    async def actualizar_ultimas_lecturas(
        ultimas: Dict[str, datetime]
    ) -> None:

        for id_dispositivo, ts in ultimas.items():

            await (
                DispositivoRepository
                .collection()
                .update_one(
                    {
                        "id_dispositivo":
                            id_dispositivo
                    },
                    {
                        "$set": {
                            "ultima_lectura_ts": ts
                        }
                    }
                )
            )


    @staticmethod
    async def eliminar(
        id_dispositivo: str
    ) -> bool:

        resultado = await (
            DispositivoRepository
            .collection()
            .delete_one(
                {
                    "id_dispositivo":
                        id_dispositivo
                }
            )
        )

        return resultado.deleted_count > 0
