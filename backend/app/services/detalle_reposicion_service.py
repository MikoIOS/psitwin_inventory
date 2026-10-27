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

    async def crear(
        self,
        id_orden: str,
        data: DetalleReposicionCreate
    ):

        orden = await self.orden_repository.obtener_por_id(
            id_orden
        )

        if not orden:
            raise HTTPException(
                status_code=404,
                detail="Orden no encontrada"
            )

        if orden["estado"] not in ("PENDIENTE", "OBSERVADA"):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo pueden agregarse productos "
                    "a una orden pendiente"
                )
            )

        db = get_database()

        producto = await db["productos"].find_one(
            {
                "$or": [
                    {"id_producto": data.id_producto},
                    {"id": data.id_producto}
                ]
            }
        )

        if not producto:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

        if (
            producto.get("id_empresa")
            and producto.get("id_empresa")
            != orden["id_empresa"]
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "El producto no pertenece "
                    "a la empresa de la orden"
                )
            )

        existente = (
            await self.repository.obtener_producto_en_orden(
                id_orden,
                data.id_producto
            )
        )

        if existente:
            raise HTTPException(
                status_code=409,
                detail=(
                    "El producto ya existe "
                    "en esta orden"
                )
            )

        documento = data.model_dump()

        documento["id_orden_reposicion"] = id_orden

        return await self.repository.crear(documento)

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

    async def actualizar(
        self,
        id_detalle,
        data: DetalleReposicionUpdate
    ):

        detalle = await self.obtener_por_id(id_detalle)

        orden = await self.orden_repository.obtener_por_id(
            detalle["id_orden_reposicion"]
        )

        if orden["estado"] not in ("PENDIENTE", "OBSERVADA"):
            raise HTTPException(
                status_code=409,
                detail=(
                    "El detalle ya no puede modificarse"
                )
            )

        cambios = data.model_dump(
            exclude_unset=True
        )

        return await self.repository.actualizar(
            id_detalle,
            cambios
        )

    async def eliminar(self, id_detalle):

        detalle = await self.obtener_por_id(id_detalle)

        orden = await self.orden_repository.obtener_por_id(
            detalle["id_orden_reposicion"]
        )

        if orden["estado"] not in ("PENDIENTE", "OBSERVADA"):
            raise HTTPException(
                status_code=409,
                detail="El detalle ya no puede eliminarse"
            )

        await self.repository.eliminar(id_detalle)

        return {
            "mensaje":
                "Detalle eliminado correctamente"
        }