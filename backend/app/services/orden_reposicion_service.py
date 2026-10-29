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

    async def crear(self, data, id_operario_solicitante=None):
        from app.services.abastecimiento_service import AbastecimientoService
        return await AbastecimientoService.crear(data, id_operario_solicitante)

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

    async def actualizar(self, id_orden, data):
        from app.services.stock_lock import bloqueo_orden
        async with bloqueo_orden(id_orden):
            order = await self.obtener_por_id(id_orden)
            if order['estado'] not in {'PENDIENTE', 'OBSERVADA'}:
                raise HTTPException(409, 'La solicitud ya no puede modificarse')
            changes = data.model_dump(exclude_unset=True)
            if changes.get('id_proveedor') and changes['id_proveedor'] != order['id_proveedor']:
                if await self.detalle_repository.obtener_por_orden(id_orden):
                    raise HTTPException(409, 'No se puede cambiar el proveedor de líneas reservadas')
                provider = await self.proveedor_repository.obtener_por_id(changes['id_proveedor'])
                if not provider or provider['id_empresa'] != order['id_empresa'] or provider.get('estado') != 'ACTIVO':
                    raise HTTPException(404, 'Proveedor activo no encontrado')
            return await self.repository.actualizar(id_orden, changes)

    # ========================================================
    # VALIDAR (EMPRESA) -> ENVIADA
    #
    # PENDIENTE (o APROBADA, órdenes antiguas) -> ENVIADA.
    # La orden queda visible para el proveedor.
    # El correo es un aviso opcional: NUNCA bloquea.
    # ========================================================

    async def validar(self, id_orden, user=None):
        from app.services.abastecimiento_service import AbastecimientoService
        result = await AbastecimientoService.transicion(id_orden, {'PENDIENTE', 'APROBADA'}, 'ENVIADA', user)
        try:
            await self.notification_service.enviar_orden_proveedor(id_orden)
        except Exception:
            import logging
            logging.getLogger(__name__).warning('order_notification_failed')
        return result

    # Alias antiguos: se conservan para no romper
    # (recomendaciones usa aprobar).

    async def aprobar(self, id_orden: str):
        return await self.validar(id_orden)

    async def enviar(self, id_orden: str):
        return await self.validar(id_orden)

    # ========================================================
    # DEVOLVER CON COMENTARIO (EMPRESA) -> OBSERVADA
    # ========================================================

    async def devolver(self, id_orden, comentario, user=None):
        from app.services.abastecimiento_service import AbastecimientoService
        return await AbastecimientoService.transicion(id_orden, {'PENDIENTE'}, 'OBSERVADA', user, comentario)

    # ========================================================
    # REENVIAR (OPERARIO): OBSERVADA -> PENDIENTE
    # ========================================================

    async def reenviar(self, id_orden, user=None):
        from app.services.abastecimiento_service import AbastecimientoService
        return await AbastecimientoService.transicion(id_orden, {'OBSERVADA'}, 'PENDIENTE', user)

    # ========================================================
    # CANCELAR (EMPRESA)
    # ========================================================

    async def cancelar(self, id_orden, user=None, motivo='Cancelación de solicitud'):
        from app.services.abastecimiento_service import AbastecimientoService
        return await AbastecimientoService.transicion(id_orden, {'PENDIENTE', 'OBSERVADA', 'APROBADA'}, 'CANCELADA', user, motivo)

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

    async def registrar_despacho(self, id_orden, data, user=None):
        from app.services.abastecimiento_service import AbastecimientoService
        return await AbastecimientoService.despacho(id_orden, data, user)

    # ========================================================
    # ELIMINAR (OPERARIO): solo PENDIENTE
    # ========================================================

    async def eliminar(self, id_orden, user=None):
        from app.services.abastecimiento_service import AbastecimientoService
        await AbastecimientoService.transicion(id_orden, {'PENDIENTE'}, 'CANCELADA', user, 'Solicitud retirada por el operario')
        return {'mensaje': 'Solicitud cancelada; se conserva su historial'}
