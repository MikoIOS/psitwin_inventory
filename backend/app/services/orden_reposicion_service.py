from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.database.mongodb import get_database

from app.dto.orden_reposicion_dto import (
    OrdenReposicionCreate,
    OrdenReposicionUpdate,
    EstadoOrdenReposicion
)

from app.repositories.orden_reposicion_repository import (
    OrdenReposicionRepository
)

from app.repositories.proveedor_repository import (
    ProveedorRepository
)

from app.repositories.detalle_reposicion_repository import (
    DetalleReposicionRepository
)

from app.services.notification_service import NotificationService

from app.dto.orden_reposicion_dto import (
    DespachoRequest
)


class OrdenReposicionService:

    def __init__(self):
        self.repository = OrdenReposicionRepository()
        self.proveedor_repository = ProveedorRepository()
        self.notification_service = NotificationService()
        self.detalle_repository = DetalleReposicionRepository()

    # ========================================================
    # CREAR SOLICITUD
    #
    # id_operario_solicitante: operario que la crea
    # (None si nace de una recomendación aprobada).
    # ========================================================

    async def crear(
        self,
        data: OrdenReposicionCreate,
        id_operario_solicitante: str | None = None
    ):

        db = get_database()

        empresa = await db["empresas"].find_one(
            {
                "$or": [
                    {"id_empresa": data.id_empresa},
                    {"id": data.id_empresa}
                ]
            }
        )

        if not empresa:
            raise HTTPException(
                status_code=404,
                detail="Empresa no encontrada"
            )

        almacen = await db["almacenes"].find_one(
            {
                "$or": [
                    {"id_almacen": data.id_almacen},
                    {"id": data.id_almacen}
                ]
            }
        )

        if not almacen:
            raise HTTPException(
                status_code=404,
                detail="Almacén no encontrado"
            )

        if almacen.get("id_empresa") != data.id_empresa:
            raise HTTPException(
                status_code=400,
                detail="El almacén no pertenece a la empresa"
            )

        proveedor = (
            await self.proveedor_repository.obtener_por_id(
                data.id_proveedor
            )
        )

        if not proveedor:
            raise HTTPException(
                status_code=404,
                detail="Proveedor no encontrado"
            )

        if proveedor["id_empresa"] != data.id_empresa:
            raise HTTPException(
                status_code=400,
                detail="El proveedor no pertenece a la empresa"
            )

        if proveedor["estado"] != "ACTIVO":
            raise HTTPException(
                status_code=400,
                detail="El proveedor está inactivo"
            )

        documento = data.model_dump(
            exclude={"lineas"}
        )

        documento["origen"] = data.origen.value
        documento["estado"] = (
            EstadoOrdenReposicion.PENDIENTE.value
        )
        documento["id_operario_solicitante"] = (
            id_operario_solicitante
        )
        documento["comentario_empresa"] = None
        documento["despacho"] = None
        documento["fecha_despacho"] = None

        # ----------------------------------------------------
        # LINEAS INICIALES: validar antes de crear nada
        # ----------------------------------------------------

        ids_producto = [
            linea.id_producto
            for linea in data.lineas
        ]

        if len(set(ids_producto)) != len(ids_producto):
            raise HTTPException(
                status_code=409,
                detail="Hay productos repetidos en las líneas"
            )

        for id_producto in ids_producto:

            producto = await db["productos"].find_one(
                {"id_producto": id_producto}
            )

            if (
                not producto
                or producto.get("id_empresa")
                != data.id_empresa
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Producto no encontrado"
                )

        orden = await self.repository.crear(documento)

        for linea in data.lineas:

            detalle = linea.model_dump()

            detalle["id_orden_reposicion"] = (
                orden["id_orden_reposicion"]
            )

            await self.detalle_repository.crear(detalle)

        return orden

    async def obtener_todos(self):
        return await self.repository.obtener_todos()

    async def obtener_por_id(self, id_orden: str):

        orden = await self.repository.obtener_por_id(
            id_orden
        )

        if not orden:
            raise HTTPException(
                status_code=404,
                detail="Orden de reposición no encontrada"
            )

        return orden

    async def obtener_por_empresa(self, id_empresa):
        return await self.repository.obtener_por_empresa(
            id_empresa
        )

    async def obtener_por_almacen(self, id_almacen):
        return await self.repository.obtener_por_almacen(
            id_almacen
        )

    async def obtener_por_proveedor(self, id_proveedor):
        return await self.repository.obtener_por_proveedor(
            id_proveedor
        )

    async def obtener_por_estado(self, estado):
        return await self.repository.obtener_por_estado(
            estado
        )

    # ========================================================
    # EDITAR (OPERARIO): solo PENDIENTE u OBSERVADA
    # ========================================================

    async def actualizar(
        self,
        id_orden: str,
        data: OrdenReposicionUpdate
    ):

        orden = await self.obtener_por_id(id_orden)

        if orden["estado"] not in [
            "PENDIENTE",
            "OBSERVADA"
        ]:
            raise HTTPException(
                status_code=409,
                detail="La orden ya no puede modificarse"
            )

        cambios = data.model_dump(
            exclude_unset=True
        )

        if cambios.get("id_proveedor"):

            proveedor = (
                await self.proveedor_repository.obtener_por_id(
                    cambios["id_proveedor"]
                )
            )

            if (
                not proveedor
                or proveedor["id_empresa"] != orden["id_empresa"]
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Proveedor no encontrado"
                )

            if proveedor["estado"] != "ACTIVO":
                raise HTTPException(
                    status_code=400,
                    detail="El proveedor está inactivo"
                )

        else:

            cambios.pop("id_proveedor", None)

        return await self.repository.actualizar(
            id_orden,
            cambios
        )

    # ========================================================
    # VALIDAR (EMPRESA) -> ENVIADA
    #
    # PENDIENTE (o APROBADA, órdenes antiguas) -> ENVIADA.
    # La orden queda visible para el proveedor.
    # El correo es un aviso opcional: NUNCA bloquea.
    # ========================================================

    async def validar(self, id_orden: str):

        orden = await self.obtener_por_id(id_orden)

        if orden["estado"] not in [
            "PENDIENTE",
            "APROBADA"
        ]:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo una solicitud PENDIENTE "
                    "puede validarse"
                )
            )

        detalles = await self.detalle_repository.obtener_por_orden(
            id_orden
        )

        if not detalles:
            raise HTTPException(
                status_code=409,
                detail=(
                    "No se puede validar una solicitud "
                    "sin productos"
                )
            )

        resultado = await self.repository.cambiar_estado(
            id_orden,
            "ENVIADA"
        )

        try:
            await self.notification_service.enviar_orden_proveedor(
                id_orden
            )
        except Exception as exc:
            print(
                "Aviso al proveedor no enviado:",
                exc
            )

        return resultado

    # Alias antiguos: se conservan para no romper
    # (recomendaciones usa aprobar).

    async def aprobar(self, id_orden: str):
        return await self.validar(id_orden)

    async def enviar(self, id_orden: str):
        return await self.validar(id_orden)

    # ========================================================
    # DEVOLVER CON COMENTARIO (EMPRESA) -> OBSERVADA
    # ========================================================

    async def devolver(
        self,
        id_orden: str,
        comentario: str
    ):

        orden = await self.obtener_por_id(id_orden)

        if orden["estado"] != "PENDIENTE":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo una solicitud PENDIENTE "
                    "puede devolverse"
                )
            )

        return await self.repository.actualizar(
            id_orden,
            {
                "estado": "OBSERVADA",
                "comentario_empresa": comentario.strip()
            }
        )

    # ========================================================
    # REENVIAR (OPERARIO): OBSERVADA -> PENDIENTE
    # ========================================================

    async def reenviar(self, id_orden: str):

        orden = await self.obtener_por_id(id_orden)

        if orden["estado"] != "OBSERVADA":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo una solicitud OBSERVADA "
                    "puede reenviarse"
                )
            )

        return await self.repository.cambiar_estado(
            id_orden,
            "PENDIENTE"
        )

    # ========================================================
    # CANCELAR (EMPRESA)
    # ========================================================

    async def cancelar(self, id_orden: str):

        orden = await self.obtener_por_id(id_orden)

        if orden["estado"] not in [
            "PENDIENTE",
            "OBSERVADA",
            "APROBADA"
        ]:
            raise HTTPException(
                status_code=409,
                detail="La orden ya no puede cancelarse"
            )

        return await self.repository.cambiar_estado(
            id_orden,
            "CANCELADA"
        )

    # ========================================================
    # ORDENES DEL PROVEEDOR (ENVIADA / PARCIAL)
    # ========================================================

    async def obtener_para_proveedor(self, id_proveedor: str):

        return await (
            self.repository.obtener_por_proveedor_y_estados(
                id_proveedor,
                ["ENVIADA", "PARCIAL"]
            )
        )

    # ========================================================
    # REGISTRAR DESPACHO (PROVEEDOR)
    #
    # Queda en la orden: despacho + fecha_despacho.
    # El operario parte de estos datos al recibir.
    # ========================================================

    async def registrar_despacho(
        self,
        id_orden: str,
        data: DespachoRequest
    ):

        orden = await self.obtener_por_id(id_orden)

        if orden["estado"] not in [
            "ENVIADA",
            "PARCIAL"
        ]:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo se registra despacho de una "
                    "orden ENVIADA o PARCIAL"
                )
            )

        detalles = {
            detalle["id_detalle_reposicion"]: detalle
            for detalle in (
                await self.detalle_repository.obtener_por_orden(
                    id_orden
                )
            )
        }

        lineas = []

        for linea in data.lineas:

            detalle = detalles.get(
                linea.id_detalle_reposicion
            )

            if not detalle:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "La línea "
                        f"{linea.id_detalle_reposicion} "
                        "no pertenece a la orden"
                    )
                )

            item = linea.model_dump()

            item["id_producto"] = detalle["id_producto"]

            lineas.append(item)

        ahora = datetime.now(timezone.utc)

        return await self.repository.actualizar(
            id_orden,
            {
                "despacho": {
                    "lineas": lineas,
                    "observacion": data.observacion,
                    "fecha": ahora
                },
                "fecha_despacho": ahora
            }
        )

    # ========================================================
    # ELIMINAR (OPERARIO): solo PENDIENTE
    # ========================================================

    async def eliminar(self, id_orden: str):

        orden = await self.obtener_por_id(id_orden)

        if orden["estado"] != "PENDIENTE":
            raise HTTPException(
                status_code=409,
                detail="Solo una orden pendiente puede eliminarse"
            )

        await self.repository.eliminar(
            id_orden
        )

        return {
            "mensaje":
                "Orden de reposición eliminada correctamente"
        }
