from datetime import datetime, timezone
from uuid import uuid4
from fastapi import HTTPException
from app.database.mongodb import get_database
from app.services.stock_lock import bloqueo_orden
from app.services.oferta_service import OfertaService, subtotal
from app.services.abastecimiento_service import AbastecimientoService, event


async def editable(identifier):
    order = await AbastecimientoService.obtener(identifier)
    if order['estado'] not in {'PENDIENTE', 'OBSERVADA'}:
        raise HTTPException(409, 'Solo se modifican líneas de solicitudes pendientes u observadas')
    return order


async def audit(order, action, user, quantities):
    db = get_database()
    rows = await db["detalles_reposicion"].find({'id_orden_reposicion': order['id_orden_reposicion']}).to_list(length=1000)
    await db["ordenes_reposicion"].update_one({'id_orden_reposicion': order['id_orden_reposicion']},
        {'$set': {'total_centimos': sum(d.get('subtotal_centimos', 0) for d in rows)},
         '$push': {'historial_estados': event(order['estado'], order['estado'], user,
             role='OPERARIO', actor=order.get('id_operario_solicitante'), reason=action, quantities=quantities)}})


class LineaAbastecimientoService:
    @staticmethod
    async def crear(identifier, data, user=None):
        db = get_database()
        async with bloqueo_orden(identifier):
            order = await editable(identifier)
            if await db["detalles_reposicion"].find_one({'id_orden_reposicion': identifier, 'id_producto': data.id_producto}):
                raise HTTPException(409, 'El producto ya está incluido en esta solicitud')
            snapshot = await OfertaService.reservar(order['id_empresa'], order['id_proveedor'], data.id_producto,
                data.cantidad_solicitada, str(uuid4()), data.id_oferta)
            from app.repositories.detalle_reposicion_repository import DetalleReposicionRepository
            try:
                row = await DetalleReposicionRepository().crear({**snapshot, 'id_orden_reposicion': identifier})
            except BaseException:
                await OfertaService.liberar(snapshot)
                raise
            await audit(order, 'Producto agregado', user, [snapshot])
            return row

    @staticmethod
    async def actualizar(identifier, data, user=None):
        db = get_database()
        detail = await db["detalles_reposicion"].find_one({'id_detalle_reposicion': identifier}, {'_id': 0})
        if not detail:
            raise HTTPException(404, 'Línea no encontrada')
        async with bloqueo_orden(detail['id_orden_reposicion']):
            order = await editable(detail['id_orden_reposicion'])
            if 'costo_unitario' in data.model_fields_set and data.costo_unitario != detail.get('costo_unitario'):
                raise HTTPException(403, 'El precio acordado no puede editarse desde la solicitud')
            if 'cantidad_solicitada' in data.model_fields_set:
                if data.cantidad_solicitada is None:
                    raise HTTPException(422, 'La cantidad no puede ser nula')
                await OfertaService.cambiar_cantidad(detail, data.cantidad_solicitada)
                await db["detalles_reposicion"].update_one({'id_detalle_reposicion': identifier},
                    {'$set': {'cantidad_solicitada': data.cantidad_solicitada,
                              'subtotal_centimos': subtotal(data.cantidad_solicitada, detail['precio_centimos']),
                              'fecha_actualizacion': datetime.now(timezone.utc)}})
            await audit(order, 'Cantidad solicitada modificada', user, [data.model_dump(exclude_unset=True)])
            return await db["detalles_reposicion"].find_one({'id_detalle_reposicion': identifier}, {'_id': 0})

    @staticmethod
    async def eliminar(identifier, user=None):
        db = get_database()
        detail = await db["detalles_reposicion"].find_one({'id_detalle_reposicion': identifier}, {'_id': 0})
        if not detail:
            raise HTTPException(404, 'Línea no encontrada')
        async with bloqueo_orden(detail['id_orden_reposicion']):
            order = await editable(detail['id_orden_reposicion'])
            await OfertaService.liberar(detail)
            await db["detalles_reposicion"].delete_one({'id_detalle_reposicion': identifier})
            await audit(order, 'Producto retirado; reserva liberada', user, [detail])
            return {'mensaje': 'Línea retirada y reserva liberada'}
