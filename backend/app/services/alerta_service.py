from app.services.inventario_integridad import validar_referencia
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.dto.alerta_dto import (
    AlertaCreate,
    AlertaEstadoUpdate,
    EstadoAlerta,
    TipoAlerta
)

from app.repositories.alerta_repository import (
    AlertaRepository
)


class AlertaService:
    async def listar_activas_por_empresa(self, id_empresa):
        return await self.repository.listar_activas_por_empresa(id_empresa)

    def __init__(self):
        self.repository = AlertaRepository()

    async def _crear(
        self,
        data: AlertaCreate
    ) -> dict:

        ahora = datetime.now(
            timezone.utc
        )

        alerta_existente = (
            await self.repository.buscar_activa(
                id_inventario=
                    data.id_inventario,

                tipo_alerta=
                    data.tipo_alerta.value,
                id_producto=data.id_producto,
                id_detalle_inventario=data.id_detalle_inventario
            )
        )

        if alerta_existente:

            datos_actualizados = {
                "nivel_riesgo":
                    data.nivel_riesgo.value,

                "titulo":
                    data.titulo,

                "mensaje":
                    data.mensaje,

                "stock_actual":
                    data.stock_actual,

                "dias_cobertura":
                    data.dias_cobertura,

                "stock_seguridad":
                    data.stock_seguridad,

                "punto_reposicion":
                    data.punto_reposicion,

                "forecast_7d":
                    data.forecast_7d,

                "fecha_actualizacion":
                    ahora
            }

            return (
                await self.repository.actualizar(
                    alerta_existente[
                        "id_alerta"
                    ],
                    datos_actualizados
                )
            )

        alerta = {
            "id_alerta":
                str(uuid4()),

            "id_empresa":
                data.id_empresa,

            "id_almacen":
                data.id_almacen,

            "id_inventario":
                data.id_inventario,

            "id_producto":
                data.id_producto,
            "id_detalle_inventario": data.id_detalle_inventario,

            "tipo_alerta":
                data.tipo_alerta.value,

            "nivel_riesgo":
                data.nivel_riesgo.value,

            "titulo":
                data.titulo,

            "mensaje":
                data.mensaje,

            "stock_actual":
                data.stock_actual,

            "dias_cobertura":
                data.dias_cobertura,

            "stock_seguridad":
                data.stock_seguridad,

            "punto_reposicion":
                data.punto_reposicion,

            "forecast_7d":
                data.forecast_7d,

            "estado":
                EstadoAlerta.ACTIVA.value,

            "fecha_creacion":
                ahora,

            "fecha_actualizacion":
                ahora,

            "fecha_resolucion":
                None
        }

        return await self.repository.crear(
            alerta
        )

    async def obtener(
        self,
        id_alerta: str
    ) -> dict:

        alerta = (
            await self.repository.obtener_por_id(
                id_alerta
            )
        )

        if alerta is None:
            raise HTTPException(
                status_code=404,
                detail="Alerta no encontrada"
            )

        return alerta

    async def listar(self):
        return await self.repository.listar()

    async def listar_por_empresa(
        self,
        id_empresa: str
    ):
        return (
            await self.repository.listar_por_empresa(
                id_empresa
            )
        )

    async def listar_por_almacen(
        self,
        id_almacen: str
    ):
        return (
            await self.repository.listar_por_almacen(
                id_almacen
            )
        )

    async def listar_por_producto(
        self,
        id_producto: str
    ):
        return (
            await self.repository.listar_por_producto(
                id_producto
            )
        )

    async def listar_por_inventario(
        self,
        id_inventario: str
    ):
        return (
            await self.repository
            .listar_por_inventario(
                id_inventario
            )
        )

    async def listar_activas(self):
        return (
            await self.repository.listar_por_estado(
                EstadoAlerta.ACTIVA.value
            )
        )

    async def listar_por_nivel(
        self,
        nivel_riesgo: str
    ):
        return (
            await self.repository.listar_por_nivel(
                nivel_riesgo
            )
        )

    async def cambiar_estado(
        self,
        id_alerta: str,
        data: AlertaEstadoUpdate
    ) -> dict:

        alerta = await self.obtener(
            id_alerta
        )

        ahora = datetime.now(
            timezone.utc
        )

        datos = {
            "estado":
                data.estado.value,

            "fecha_actualizacion":
                ahora
        }

        if (
            data.estado
            == EstadoAlerta.RESUELTA
        ):
            datos[
                "fecha_resolucion"
            ] = ahora

        elif (
            alerta.get(
                "fecha_resolucion"
            )
            is not None
        ):
            datos[
                "fecha_resolucion"
            ] = None

        alerta_actualizada = (
            await self.repository.actualizar(
                id_alerta,
                datos
            )
        )

        return alerta_actualizada

    async def resolver_activa_por_inventario(
        self,
        id_inventario: str,
        tipo_alerta: TipoAlerta,
        id_producto: str | None = None
    ):
        alerta = await self.repository.buscar_activa(
            id_inventario,
            tipo_alerta.value,
            id_producto=id_producto
        )

        if not alerta:
            return None

        return await self.cambiar_estado(
            alerta["id_alerta"],
            AlertaEstadoUpdate(
                estado=EstadoAlerta.RESUELTA
            )
        )
    async def crear(self, data):
        await validar_referencia(data)
        from app.services.stock_lock import bloqueo_recurso
        key = ":".join(("decision",data.id_inventario,data.id_producto,
                        data.id_detalle_inventario or "general",data.tipo_alerta.value))
        async with bloqueo_recurso(key):
            return await self._crear(data)
