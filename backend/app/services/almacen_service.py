from datetime import (
    datetime,
    timezone
)

from decimal import Decimal

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

from app.dto.almacen_dto import (
    AlmacenCreate,
    AlmacenUpdate
)

from app.repositories.almacen_repository import (
    AlmacenRepository
)

from app.repositories.empresa_repository import (
    EmpresaRepository
)


class AlmacenService:

    # ============================================================
    # CONVERTIR DECIMAL PARA MONGODB
    # ============================================================

    @staticmethod
    def convertir_decimal(
        data: Dict[str, Any]
    ) -> Dict[str, Any]:

        data = dict(
            data
        )

        for campo in [
            "latitud",
            "longitud"
        ]:

            if (
                campo in data
                and
                isinstance(
                    data[campo],
                    Decimal
                )
            ):

                data[campo] = float(
                    data[campo]
                )

        return data


    # ============================================================
    # CREAR
    # ============================================================

    @staticmethod
    async def _crear(
        data: AlmacenCreate
    ) -> Dict[str, Any]:

        # --------------------------------------------------------
        # VALIDAR EMPRESA
        # --------------------------------------------------------

        empresa = await (
            EmpresaRepository.obtener_por_id(
                data.id_empresa
            )
        )

        if not empresa:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "La empresa especificada "
                    "no existe"
                )
            )

        now = datetime.now(
            timezone.utc
        )

        almacen_data = (
            data.model_dump()
        )

        almacen_data = (
            AlmacenService.convertir_decimal(
                almacen_data
            )
        )

        almacen = {
            "id":
                str(
                    uuid4()
                ),

            **almacen_data,

            "fecha_creacion":
                now,

            "fecha_actualizacion":
                now
        }

        from app.repositories.inventario_repository import InventarioRepository
        created = await AlmacenRepository.crear(almacen)
        try:
            await InventarioRepository().garantizar(created["id"])
        except Exception:
            # No successful warehouse creation without its inventory header.
            await AlmacenRepository.eliminar(created["id"])
            raise
        return created


    # ============================================================
    # OBTENER TODOS
    # ============================================================

    @staticmethod
    async def obtener_todos() -> List[Dict[str, Any]]:

        return await (
            AlmacenRepository.obtener_todos()
        )


    # ============================================================
    # OBTENER POR ID
    # ============================================================

    @staticmethod
    async def obtener_por_id(
        id_almacen: str
    ) -> Dict[str, Any]:

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

        return almacen


    # ============================================================
    # OBTENER POR EMPRESA
    # ============================================================

    @staticmethod
    async def obtener_por_empresa(
        id_empresa: str
    ) -> List[Dict[str, Any]]:

        empresa = await (
            EmpresaRepository.obtener_por_id(
                id_empresa
            )
        )

        if not empresa:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Empresa no encontrada"
                )
            )

        return await (
            AlmacenRepository.obtener_por_empresa(
                id_empresa
            )
        )


    # ============================================================
    # ACTUALIZAR
    # ============================================================

    @staticmethod
    async def _actualizar(
        id_almacen: str,
        data: AlmacenUpdate
    ) -> Dict[str, Any]:

        almacen_actual = await (
            AlmacenRepository.obtener_por_id(
                id_almacen
            )
        )

        if not almacen_actual:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Almacén no encontrado"
                )
            )

        update_data = (
            data.model_dump(
                exclude_unset=True
            )
        )

        if not update_data:

            return almacen_actual

        update_data = (
            AlmacenService.convertir_decimal(
                update_data
            )
        )

        updated = await (
            AlmacenRepository.actualizar(
                id_almacen,
                update_data
            )
        )

        if not updated:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Almacén no encontrado"
                )
            )

        return updated


    # ============================================================
    # ELIMINAR
    # ============================================================

    @staticmethod
    async def _eliminar(
        id_almacen: str
    ) -> Dict[str, str]:

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

        from app.database.mongodb import get_database
        from app.repositories.inventario_repository import InventarioRepository
        db = get_database()
        header = await InventarioRepository().obtener_por_almacen(id_almacen)
        for collection in ("zonas","operarios","ordenes_reposicion","movimientos","inventario_historial"):
            if await db[collection].find_one({"id_almacen":id_almacen},{"_id":1}):
                raise HTTPException(409,"El almacén tiene estructura, operaciones o auditoría asociada")
        if header and await db["detalles_inventario"].find_one({"id_inventario":header["id_inventario"]},{"_id":1}):
            raise HTTPException(409,"El almacén tiene detalles de inventario")
        deleted = await (
            AlmacenRepository.eliminar(
                id_almacen
            )
        )

        if not deleted:

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "No se pudo eliminar "
                    "el almacén"
                )
            )

        if header:
            await db["inventarios"].delete_one({"id_inventario":header["id_inventario"]})
        return {
            "mensaje":
                "Almacén eliminado correctamente"
        }

    @staticmethod
    async def crear(data):
        from app.services.jerarquia_service import JerarquiaService
        return await JerarquiaService.guardar_almacen(data)

    @staticmethod
    async def actualizar(identifier, data):
        from app.services.jerarquia_service import JerarquiaService
        return await JerarquiaService.guardar_almacen(data, identifier)

    @staticmethod
    async def eliminar(identifier):
        from app.services.stock_lock import bloqueo_recurso
        async with bloqueo_recurso('almacen:' + identifier):
            return await AlmacenService._eliminar(identifier)


# ============================================================
# FUNCIONES DE COMPATIBILIDAD
# ============================================================

async def crear_almacen(
    data: AlmacenCreate
):

    return await (
        AlmacenService.crear(
            data
        )
    )


async def obtener_almacenes():

    return await (
        AlmacenService.obtener_todos()
    )


async def obtener_almacen(
    id_almacen: str
):

    return await (
        AlmacenService.obtener_por_id(
            id_almacen
        )
    )


async def obtener_almacenes_por_empresa(
    id_empresa: str
):

    return await (
        AlmacenService.obtener_por_empresa(
            id_empresa
        )
    )


async def actualizar_almacen(
    id_almacen: str,
    data: AlmacenUpdate
):

    return await (
        AlmacenService.actualizar(
            id_almacen,
            data
        )
    )


async def eliminar_almacen(
    id_almacen: str
):

    return await (
        AlmacenService.eliminar(
            id_almacen
        )
    )