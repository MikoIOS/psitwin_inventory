from app.services.inventario_integridad import validar_referencia
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.dto.recomendacion_dto import (
    RecomendacionCreate,
    RecomendacionEstadoUpdate,
    EstadoRecomendacion,
    EmpresaAprobacionRequest,
    EmpresaCambiosRequest,
    EmpresaRechazoRequest,
    PropuestaRecomendacionUpdate,
)

from app.dto.orden_reposicion_dto import (
    OrdenReposicionCreate,
    OrigenOrden
)

from app.dto.detalle_reposicion_dto import (
    DetalleReposicionCreate
)

from app.repositories.recomendacion_repository import (
    RecomendacionRepository
)

from app.services.orden_reposicion_service import (
    OrdenReposicionService
)

from app.services.detalle_reposicion_service import (
    DetalleReposicionService
)

from app.services.notification_service import (
    NotificationService
)


class RecomendacionService:

    def __init__(self):

        self.repository = (
            RecomendacionRepository()
        )

        self.orden_reposicion_service = (
            OrdenReposicionService()
        )

        self.detalle_reposicion_service = (
            DetalleReposicionService()
        )

        self.notification_service = NotificationService()

    # ========================================================
    # CREAR RECOMENDACION
    # ========================================================

    async def _crear(
        self,
        data: RecomendacionCreate
    ) -> dict:

        ahora = datetime.now(
            timezone.utc
        )

        recomendacion_existente = (
            await self.repository.buscar_pendiente(
                id_inventario=
                    data.id_inventario,

                tipo_recomendacion=
                    data.tipo_recomendacion.value,
                id_producto=data.id_producto,
                id_detalle_inventario=data.id_detalle_inventario
            )
        )

        if recomendacion_existente:

            datos_actualizados = {
                "nivel_riesgo":
                    data.nivel_riesgo.value,

                "id_alerta":
                    data.id_alerta,

                "cantidad_minima":
                    data.cantidad_minima,

                "cantidad_recomendada":
                    data.cantidad_recomendada,

                "cantidad_segura":
                    data.cantidad_segura,

                "forecast_7d":
                    data.forecast_7d,

                "explicacion":
                    data.explicacion,

                "origen":
                    data.origen,

                "fecha_actualizacion":
                    ahora
            }

            return (
                await self.repository.actualizar(
                    recomendacion_existente[
                        "id_recomendacion"
                    ],
                    datos_actualizados
                )
            )

        recomendacion = {
            "id_recomendacion":
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

            "id_alerta":
                data.id_alerta,

            "tipo_recomendacion":
                data.tipo_recomendacion.value,

            "nivel_riesgo":
                data.nivel_riesgo.value,

            "cantidad_minima":
                data.cantidad_minima,

            "cantidad_recomendada":
                data.cantidad_recomendada,

            "cantidad_segura":
                data.cantidad_segura,

            "forecast_7d":
                data.forecast_7d,

            "explicacion":
                data.explicacion,

            "origen":
                data.origen,

            "estado":
                EstadoRecomendacion
                .PENDIENTE.value,

            "fecha_creacion":
                ahora,

            "fecha_actualizacion":
                ahora,

            "fecha_aplicacion":
                None
        }

        return (
            await self.repository.crear(
                recomendacion
            )
        )

    # ========================================================
    # OBTENER
    # ========================================================

    async def obtener(
        self,
        id_recomendacion: str
    ) -> dict:

        recomendacion = (
            await self.repository.obtener_por_id(
                id_recomendacion
            )
        )

        if recomendacion is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Recomendación "
                    "no encontrada"
                )
            )

        return recomendacion

    # ========================================================
    # LISTAR
    # ========================================================

    async def listar(self):

        return (
            await self.repository.listar()
        )

    async def listar_por_empresa(
        self,
        id_empresa: str
    ):

        return (
            await self.repository
            .listar_por_empresa(
                id_empresa
            )
        )

    async def listar_por_almacen(
        self,
        id_almacen: str
    ):

        return (
            await self.repository
            .listar_por_almacen(
                id_almacen
            )
        )

    async def listar_por_producto(
        self,
        id_producto: str
    ):

        return (
            await self.repository
            .listar_por_producto(
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

    async def solicitar_cambios(
        self,
        id_recomendacion: str,
        data: EmpresaCambiosRequest,
    ) -> dict:
        recomendacion = await self.obtener(id_recomendacion)
        if recomendacion.get("id_empresa") != data.id_empresa:
            raise HTTPException(status_code=403, detail="Empresa no autorizada")
        if recomendacion["estado"] not in {
            EstadoRecomendacion.VALIDADA_OPERARIO.value,
            EstadoRecomendacion.CAMBIOS_SOLICITADOS.value,
        }:
            raise HTTPException(status_code=409, detail="La recomendación no está pendiente de decisión")

        ahora = datetime.now(timezone.utc)
        return await self.repository.actualizar(
            id_recomendacion,
            {
                "estado": EstadoRecomendacion.CAMBIOS_SOLICITADOS.value,
                "solicitud_cambios": {
                    "id_empresa": data.id_empresa,
                    "comentario": data.comentario.strip(),
                    "estado_anterior": recomendacion["estado"],
                    "estado_nuevo": EstadoRecomendacion.CAMBIOS_SOLICITADOS.value,
                    "fecha": ahora,
                },
                "fecha_actualizacion": ahora,
            },
        )

    async def rechazar_por_empresa(
        self,
        id_recomendacion: str,
        data: EmpresaRechazoRequest,
    ) -> dict:
        recomendacion = await self.obtener(id_recomendacion)
        if recomendacion.get("id_empresa") != data.id_empresa:
            raise HTTPException(status_code=403, detail="Empresa no autorizada")
        if recomendacion["estado"] not in {
            EstadoRecomendacion.VALIDADA_OPERARIO.value,
            EstadoRecomendacion.CAMBIOS_SOLICITADOS.value,
        }:
            raise HTTPException(status_code=409, detail="La recomendación no está pendiente de decisión")

        ahora = datetime.now(timezone.utc)
        return await self.repository.actualizar(
            id_recomendacion,
            {
                "estado": EstadoRecomendacion.RECHAZADA.value,
                "decision_empresa": {
                    "id_empresa": data.id_empresa,
                    "decision": EstadoRecomendacion.RECHAZADA.value,
                    "comentario": data.comentario.strip(),
                    "estado_anterior": recomendacion["estado"],
                    "fecha": ahora,
                },
                "fecha_actualizacion": ahora,
            },
        )

    async def actualizar_propuesta(
        self,
        id_recomendacion: str,
        data: PropuestaRecomendacionUpdate,
        id_operario: str | None = None,
    ) -> dict:
        recomendacion = await self.obtener(id_recomendacion)
        if recomendacion["estado"] != EstadoRecomendacion.CAMBIOS_SOLICITADOS.value:
            raise HTTPException(status_code=409, detail="No hay cambios solicitados para esta recomendación")

        cambios = data.model_dump(exclude_unset=True, exclude_none=True)
        if not cambios:
            raise HTTPException(status_code=400, detail="Debe indicar al menos un cambio permitido")
        cambios["fecha_actualizacion"] = datetime.now(timezone.utc)
        await self.repository.actualizar(id_recomendacion, cambios)
        return await self.cambiar_estado(
            id_recomendacion,
            RecomendacionEstadoUpdate(
                estado=EstadoRecomendacion.VALIDADA_OPERARIO
            ),
            id_operario,
        )

    async def aprobar_por_empresa(
        self,
        id_recomendacion: str,
        data: EmpresaAprobacionRequest,
    ) -> dict:
        recomendacion = await self.obtener(id_recomendacion)
        if recomendacion.get("id_empresa") != data.id_empresa:
            raise HTTPException(status_code=403, detail="Empresa no autorizada")
        if recomendacion["estado"] != EstadoRecomendacion.VALIDADA_OPERARIO.value:
            raise HTTPException(status_code=409, detail="La recomendación debe estar validada por Operario")

        existing_order = await self.orden_reposicion_service.repository.obtener_por_recomendacion(
            id_recomendacion
        )
        if existing_order:
            if existing_order.get("estado") == "PENDIENTE":
                existing_order = await self.orden_reposicion_service.aprobar(
                    existing_order["id_orden_reposicion"]
                )
            return {
                "recomendacion": recomendacion,
                "orden": existing_order,
            }

        ahora = datetime.now(timezone.utc)
        await self.repository.actualizar(
            id_recomendacion,
            {
                "estado": EstadoRecomendacion.APROBADA_EMPRESA.value,
                "decision_empresa": {
                    "id_empresa": data.id_empresa,
                    "decision": EstadoRecomendacion.APROBADA_EMPRESA.value,
                    "fecha": ahora,
                    "id_proveedor": data.id_proveedor,
                    "costo_unitario": data.costo_unitario,
                },
                "fecha_actualizacion": ahora,
            },
        )

        result = await self.crear_orden_desde_recomendacion(
            id_recomendacion,
            data.id_proveedor,
            data.costo_unitario,
            data.fecha_estimada_recepcion,
            data.observacion,
        )
        orden = await self.orden_reposicion_service.aprobar(
            result["orden"]["id_orden_reposicion"]
        )
        result["orden"] = orden
        return result

    # ========================================================
    # CAMBIAR ESTADO
    # ========================================================

    async def cambiar_estado(
        self,
        id_recomendacion: str,
        data: RecomendacionEstadoUpdate,
        id_operario: str | None = None
    ) -> dict:

        recomendacion = await self.obtener(
            id_recomendacion
        )

        estado_actual = recomendacion["estado"]

        transiciones_validas = {
            EstadoRecomendacion.PENDIENTE.value: {
                EstadoRecomendacion.VALIDADA_OPERARIO.value,
                EstadoRecomendacion.RECHAZADA.value,
            },
            EstadoRecomendacion.VALIDADA_OPERARIO.value: {
                EstadoRecomendacion.APROBADA_EMPRESA.value,
                EstadoRecomendacion.CAMBIOS_SOLICITADOS.value,
                EstadoRecomendacion.RECHAZADA.value,
            },
            EstadoRecomendacion.CAMBIOS_SOLICITADOS.value: {
                EstadoRecomendacion.VALIDADA_OPERARIO.value,
                EstadoRecomendacion.RECHAZADA.value,
            },
            EstadoRecomendacion.APROBADA_EMPRESA.value: {
                EstadoRecomendacion.APLICADA.value,
            },
        }

        if data.estado.value not in transiciones_validas.get(
            estado_actual,
            set()
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"No se puede cambiar una recomendación "
                    f"{estado_actual} a {data.estado.value}"
                )
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
            == EstadoRecomendacion.APLICADA
        ):

            datos[
                "fecha_aplicacion"
            ] = ahora

        resultado = await self.repository.actualizar(
            id_recomendacion,
            datos
        )

        if data.estado == EstadoRecomendacion.VALIDADA_OPERARIO:
            try:
                notificacion = await (
                    self.notification_service
                    .enviar_solicitud_aprobacion(
                        id_recomendacion,
                        id_operario
                    )
                )
            except Exception as exc:
                notificacion = {
                    "status": "PENDIENTE",
                    "reason": str(exc)
                }

            resultado = await self.repository.actualizar(
                id_recomendacion,
                {
                    "notificacion_aprobacion": notificacion
                }
            )

        return resultado

    # ========================================================
    # CREAR ORDEN DESDE RECOMENDACION IA
    # ========================================================

    async def crear_orden_desde_recomendacion(
        self,
        id_recomendacion: str,
        id_proveedor: str,
        costo_unitario: float,
        fecha_estimada_recepcion=None,
        observacion: str | None = None,
    ) -> dict:

        # ----------------------------------------------------
        # 1. OBTENER RECOMENDACION
        # ----------------------------------------------------

        recomendacion = (
            await self.obtener(
                id_recomendacion
            )
        )

        # ----------------------------------------------------
        # 2. VALIDAR ESTADO
        # ----------------------------------------------------

        if (
            recomendacion.get("estado")
            != EstadoRecomendacion.APROBADA_EMPRESA.value
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "La recomendación debe estar aprobada "
                    "por la empresa antes de generar la orden"
                )
            )

        # ----------------------------------------------------
        # 3. VALIDAR TIPO
        # ----------------------------------------------------

        if (
            recomendacion.get(
                "tipo_recomendacion"
            )
            != "REABASTECER"
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Solo una recomendación de "
                    "REABASTECER puede generar "
                    "una orden de reposición"
                )
            )

        # ----------------------------------------------------
        # 4. DATOS NECESARIOS
        # ----------------------------------------------------

        id_empresa = (
            recomendacion.get(
                "id_empresa"
            )
        )

        id_almacen = (
            recomendacion.get(
                "id_almacen"
            )
        )

        id_producto = (
            recomendacion.get(
                "id_producto"
            )
        )

        cantidad_recomendada = (
            recomendacion.get(
                "cantidad_recomendada"
            )
        )

        if not id_empresa:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La recomendación no tiene "
                    "id_empresa"
                )
            )

        if not id_almacen:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La recomendación no tiene "
                    "id_almacen"
                )
            )

        if not id_producto:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La recomendación no tiene "
                    "id_producto"
                )
            )

        if (
            cantidad_recomendada is None
            or cantidad_recomendada <= 0
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "La recomendación no contiene "
                    "una cantidad de reposición válida"
                )
            )

        # ----------------------------------------------------
        # 5. CREAR ORDEN PENDIENTE
        # ----------------------------------------------------

        orden_data = OrdenReposicionCreate(
            clave_idempotencia='recomendacion-' + id_recomendacion,
            lineas=[DetalleReposicionCreate(id_producto=id_producto, cantidad_solicitada=cantidad_recomendada)],

            id_recomendacion=
                id_recomendacion,

            id_empresa=
                id_empresa,

            id_almacen=
                id_almacen,

            id_proveedor=
                id_proveedor,

            fecha_estimada_recepcion=
                fecha_estimada_recepcion,

            origen=
                OrigenOrden.RECOMENDACION_IA,

            observacion=observacion or (
                "Orden generada desde la "
                f"recomendación IA "
                f"{id_recomendacion}"
            )
        )

        orden = (
            await self.orden_reposicion_service
            .crear(
                orden_data
            )
        )

        id_orden = (
            orden.get(
                "id_orden_reposicion"
            )
        )

        if not id_orden:

            raise HTTPException(
                status_code=500,
                detail=(
                    "La orden fue creada pero no "
                    "se obtuvo id_orden_reposicion"
                )
            )

        # Header, reserved offer and price snapshot are created together. Never
        # round kilograms to integer units or create an empty procurement request.
        from app.database.mongodb import get_database
        detalle = await get_database()['detalles_reposicion'].find_one({'id_orden_reposicion': id_orden}, {'_id': 0})

        # ----------------------------------------------------
        # 7. MARCAR RECOMENDACION COMO APLICADA
        # ----------------------------------------------------

        recomendacion_actualizada = (
            await self.cambiar_estado(

                id_recomendacion=
                    id_recomendacion,

                data=
                    RecomendacionEstadoUpdate(
                        estado=
                            EstadoRecomendacion.APLICADA
                    )
            )
        )

        # ----------------------------------------------------
        # 8. RESPONSE
        # ----------------------------------------------------

        return {

            "mensaje":
                (
                    "Orden de reposición creada "
                    "desde la recomendación IA"
                ),

            "id_recomendacion":
                id_recomendacion,

            "recomendacion":
                recomendacion_actualizada,

            "orden":
                orden,

            "detalle":
                detalle
        }
    async def crear(self, data):
        await validar_referencia(data)
        from app.services.stock_lock import bloqueo_recurso
        key = ":".join(("decision",data.id_inventario,data.id_producto,
                        data.id_detalle_inventario or "general",data.tipo_recomendacion.value))
        async with bloqueo_recurso(key):
            return await self._crear(data)
