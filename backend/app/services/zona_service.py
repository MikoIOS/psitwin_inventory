from datetime import (
    datetime,
    timezone
)

from uuid import uuid4

from typing import (
    Dict,
    Any,
    List
)

from fastapi import (
    HTTPException,
    status
)

from app.dto.zona_dto import (
    ZonaCreate,
    ZonaUpdate
)

from app.repositories.zona_repository import (
    ZonaRepository
)

from app.repositories.almacen_repository import (
    AlmacenRepository
)


class ZonaService:

    # ============================================================
    # NORMALIZAR ZONA
    #
    # Corrige documentos antiguos que puedan tener:
    #
    # id_zona en vez de id
    #
    # y documentos que no tengan id_empresa.
    # ============================================================

    @staticmethod
    async def normalizar_zona(
        zona: Dict[str, Any]
    ) -> Dict[str, Any]:

        if not zona:

            return zona

        result = dict(
            zona
        )

        # --------------------------------------------------------
        # ID ANTIGUO
        # --------------------------------------------------------

        if (
            "id" not in result
            and
            "id_zona" in result
        ):

            result["id"] = (
                result["id_zona"]
            )

        # --------------------------------------------------------
        # COMPLETAR ID_EMPRESA DESDE ALMACEN
        # --------------------------------------------------------

        if (
            not result.get("id_empresa")
            and
            result.get("id_almacen")
        ):

            almacen = await (
                AlmacenRepository.obtener_por_id(
                    result["id_almacen"]
                )
            )

            if almacen:

                result["id_empresa"] = (
                    almacen.get(
                        "id_empresa"
                    )
                )

        return result


    # ============================================================
    # CREAR
    # ============================================================

    @staticmethod
    async def crear(
        data: ZonaCreate
    ) -> Dict[str, Any]:

        almacen = await (
            AlmacenRepository.obtener_por_id(
                data.id_almacen
            )
        )

        if not almacen:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "El almacén especificado "
                    "no existe"
                )
            )

        if (
            data.temperatura_min is not None
            and
            data.temperatura_max is not None
            and
            data.temperatura_min
            >
            data.temperatura_max
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "La temperatura mínima "
                    "no puede ser mayor "
                    "que la máxima"
                )
            )

        now = datetime.now(
            timezone.utc
        )

        zona = {

            "id": str(
                uuid4()
            ),

            "id_almacen":
                data.id_almacen,

            "id_empresa":
                almacen[
                    "id_empresa"
                ],

            "nombre":
                data.nombre.strip(),

            "tipo_zona":
                data.tipo_zona.strip(),

            "refrigerada":
                data.refrigerada,

            "temperatura_min":
                data.temperatura_min,

            "temperatura_max":
                data.temperatura_max,

            "capacidad":
                data.capacidad,

            "fecha_creacion":
                now,

            "fecha_actualizacion":
                now
        }

        created = await (
            ZonaRepository.crear(
                zona
            )
        )

        return await (
            ZonaService.normalizar_zona(
                created
            )
        )


    # ============================================================
    # OBTENER TODAS
    # ============================================================

    @staticmethod
    async def obtener_todas() -> List[Dict[str, Any]]:

        zonas = await (
            ZonaRepository.obtener_todas()
        )

        result = []

        for zona in zonas:

            zona_normalizada = await (
                ZonaService.normalizar_zona(
                    zona
                )
            )

            result.append(
                zona_normalizada
            )

        return result


    # ============================================================
    # OBTENER POR ID
    # ============================================================

    @staticmethod
    async def obtener_por_id(
        id_zona: str
    ) -> Dict[str, Any]:

        zona = await (
            ZonaRepository.obtener_por_id(
                id_zona
            )
        )

        if not zona:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Zona no encontrada"
                )
            )

        return await (
            ZonaService.normalizar_zona(
                zona
            )
        )


    # ============================================================
    # OBTENER POR ALMACEN
    # ============================================================

    @staticmethod
    async def obtener_por_almacen(
        id_almacen: str
    ) -> List[Dict[str, Any]]:

        almacen = await (
            AlmacenRepository.obtener_por_id(
                id_almacen
            )
        )

        if not almacen:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Almacén no encontrado"
                )
            )

        zonas = await (
            ZonaRepository.obtener_por_almacen(
                id_almacen
            )
        )

        result = []

        for zona in zonas:

            zona_normalizada = await (
                ZonaService.normalizar_zona(
                    zona
                )
            )

            result.append(
                zona_normalizada
            )

        return result


    # ============================================================
    # ACTUALIZAR
    # ============================================================

    @staticmethod
    async def actualizar(
        id_zona: str,
        data: ZonaUpdate
    ) -> Dict[str, Any]:

        zona_actual = await (
            ZonaRepository.obtener_por_id(
                id_zona
            )
        )

        if not zona_actual:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Zona no encontrada"
                )
            )

        update_data = (
            data.model_dump(
                exclude_unset=True
            )
        )

        if not update_data:

            return await (
                ZonaService.normalizar_zona(
                    zona_actual
                )
            )

        temperatura_min = (
            update_data.get(
                "temperatura_min",
                zona_actual.get(
                    "temperatura_min"
                )
            )
        )

        temperatura_max = (
            update_data.get(
                "temperatura_max",
                zona_actual.get(
                    "temperatura_max"
                )
            )
        )

        if (
            temperatura_min is not None
            and
            temperatura_max is not None
            and
            temperatura_min
            >
            temperatura_max
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "La temperatura mínima "
                    "no puede ser mayor "
                    "que la máxima"
                )
            )

        updated = await (
            ZonaRepository.actualizar(
                id_zona,
                update_data
            )
        )

        if not updated:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Zona no encontrada"
                )
            )

        return await (
            ZonaService.normalizar_zona(
                updated
            )
        )


    # ============================================================
    # ELIMINAR
    # ============================================================

    @staticmethod
    async def eliminar(
        id_zona: str
    ) -> Dict[str, str]:

        zona = await (
            ZonaRepository.obtener_por_id(
                id_zona
            )
        )

        if not zona:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Zona no encontrada"
                )
            )

        from app.repositories.rack_repository import RackRepository
        if await RackRepository.obtener_por_zona(id_zona):
            raise HTTPException(409,"La zona tiene racks; no puede eliminarse")
        deleted = await (
            ZonaRepository.eliminar(
                id_zona
            )
        )

        if not deleted:

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "No se pudo eliminar "
                    "la zona"
                )
            )

        return {
            "mensaje":
                "Zona eliminada correctamente"
        }