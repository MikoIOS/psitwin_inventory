from fastapi import HTTPException

from app.database.mongodb import get_database

from app.dto.detalle_reposicion_dto import (
    DetalleReposicionCreate,
    DetalleReposicionUpdate
)

from app.repositories.detalle_reposicion_repository import (
    DetalleReposicionRepository
)

from app.repositories.orden_reposicion_repository import (
    OrdenReposicionRepository
)


class DetalleReposicionService:

    def __init__(self):
        self.repository = DetalleReposicionRepository()
        self.orden_repository = OrdenReposicionRepository()

    async def crear(self, id_orden, data, user=None):
        from app.services.linea_abastecimiento_service import LineaAbastecimientoService
        return await LineaAbastecimientoService.crear(id_orden, data, user)

    async def obtener_por_orden(self, id_orden):

        return await self.repository.obtener_por_orden(
            id_orden
        )

    async def obtener_por_id(self, id_detalle):

        detalle = await self.repository.obtener_por_id(
            id_detalle
        )

        if not detalle:
            raise HTTPException(
                status_code=404,
                detail="Detalle no encontrado"
            )

        return detalle

    async def actualizar(self, id_detalle, data, user=None):
        from app.services.linea_abastecimiento_service import LineaAbastecimientoService
        return await LineaAbastecimientoService.actualizar(id_detalle, data, user)

    async def eliminar(self, id_detalle, user=None):
        from app.services.linea_abastecimiento_service import LineaAbastecimientoService
        return await LineaAbastecimientoService.eliminar(id_detalle, user)
