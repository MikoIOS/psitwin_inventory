"""Supply workflow on the existing order/detail collections. No automatic purchases."""
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4
from fastapi import HTTPException
from pymongo import ReturnDocument
from app.database.mongodb import get_database
from app.services.stock_lock import bloqueo_orden, bloqueo_recurso
from app.services.oferta_service import OfertaService, miles


def event(old, new, user=None, role='EMPRESA', actor=None, reason=None, quantities=None):
    return {'id_evento': str(uuid4()), 'anterior': old, 'nuevo': new,
            'usuario': (user.id_operario or user.id_proveedor or user.id_empresa) if user else actor,
            'rol': user.rol if user else role, 'fecha': datetime.now(timezone.utc),
            'observacion': reason, 'cantidades': quantities or []}


class AbastecimientoService:
    @staticmethod
    async def obtener(identifier):
        row = await get_database()["ordenes_reposicion"].find_one({'id_orden_reposicion': identifier}, {'_id': 0})
        if not row:
            raise HTTPException(404, 'Solicitud no encontrada')
        return row

    @staticmethod
    async def crear(data, operator=None):
        db = get_database()
        warehouse = await db["almacenes"].find_one({'id_empresa': data.id_empresa, '$or': [{'id': data.id_almacen}, {'id_almacen': data.id_almacen}]})
        provider = await db["proveedores"].find_one({'id_empresa': data.id_empresa, 'id_proveedor': data.id_proveedor, 'estado': 'ACTIVO'})
        if not warehouse or not provider:
            raise HTTPException(404, 'Almacén o proveedor autorizado no encontrado')
        if not data.lineas:
            raise HTTPException(422, 'La solicitud debe contener al menos un producto ofertado')
        if len({line.id_producto for line in data.lineas}) != len(data.lineas):
            raise HTTPException(409, 'Hay productos repetidos en la solicitud')
        key = sha256(f'{data.id_empresa}:{operator}:{data.clave_idempotencia or uuid4()}'.encode()).hexdigest()
        async with bloqueo_recurso('solicitud-clave:' + key):
            previous = await db["ordenes_reposicion"].find_one({'creacion_clave': key}, {'_id': 0})
            if previous:
                if previous.get('creacion_firma') != data.model_dump_json(exclude={'clave_idempotencia'}):
                    raise HTTPException(409, 'La clave de idempotencia ya corresponde a otra solicitud')
                return previous
            identifier = str(uuid4())
            reserved = []
            try:
                for line in data.lineas:
                    snapshot = await OfertaService.reservar(data.id_empresa, data.id_proveedor, line.id_producto,
                        line.cantidad_solicitada, str(uuid4()), line.id_oferta)
                    snapshot.update(id_detalle_reposicion=str(uuid4()), id_orden_reposicion=identifier,
                                    fecha_creacion=datetime.now(timezone.utc), fecha_actualizacion=datetime.now(timezone.utc))
                    reserved.append(snapshot)
                if sum(d['subtotal_centimos'] for d in reserved) > 9007199254740991:
                    raise HTTPException(422, 'El total supera el máximo monetario admitido')
                now = datetime.now(timezone.utc)
                row = {**data.model_dump(exclude={'lineas', 'clave_idempotencia'}), 'origen': data.origen.value,
                       'id_orden_reposicion': identifier, 'id_operario_solicitante': operator,
                       'estado': 'PENDIENTE', 'fecha_orden': now, 'fecha_creacion': now, 'fecha_actualizacion': now,
                       'creacion_clave': key, 'creacion_firma': data.model_dump_json(exclude={'clave_idempotencia'}),
                       'total_centimos': sum(d['subtotal_centimos'] for d in reserved), 'moneda': 'PEN',
                       'historial_estados': [event(None, 'PENDIENTE', role='OPERARIO' if operator else 'EMPRESA', actor=operator or data.id_empresa)], 'despachos': []}
                # Details are durable before the order becomes visible. On a process crash
                # reservations remain fail-closed; migration/reconciliation never frees live locks.
                await db["detalles_reposicion"].insert_many(reserved)
                await db["ordenes_reposicion"].insert_one(row)
            except BaseException:
                persisted = await db["ordenes_reposicion"].find_one({'id_orden_reposicion': identifier}, {'_id': 0})
                if persisted:
                    return persisted
                for detail in reserved:
                    await OfertaService.liberar(detail)
                await db["detalles_reposicion"].delete_many({'id_orden_reposicion': identifier})
                raise
            return await AbastecimientoService.obtener(identifier)

    @staticmethod
    async def transicion(identifier, allowed, target, user=None, reason=None):
        db = get_database()
        async with bloqueo_orden(identifier):
            row = await AbastecimientoService.obtener(identifier)
            if row['estado'] not in allowed:
                raise HTTPException(409, 'Transición no válida para el estado actual de la solicitud')
            details = await db["detalles_reposicion"].find({'id_orden_reposicion': identifier}, {'_id': 0}).to_list(length=1000)
            if target == 'ENVIADA' and not details:
                raise HTTPException(409, 'No se puede aprobar una solicitud sin productos')
            changes = {'estado': target, 'fecha_actualizacion': datetime.now(timezone.utc)}
            if reason:
                changes['comentario_empresa'] = reason
            result = await db["ordenes_reposicion"].find_one_and_update({'id_orden_reposicion': identifier, 'estado': row['estado']},
                {'$set': changes, '$push': {'historial_estados': event(row['estado'], target, user, actor=row['id_empresa'], reason=reason)}},
                return_document=ReturnDocument.AFTER, projection={'_id': 0})
            if not result:
                raise HTTPException(409, 'La solicitud cambió durante la operación')
            if target == 'CANCELADA':
                for detail in details:
                    await OfertaService.liberar(detail)
            return result

    @staticmethod
    async def despacho(identifier, data, user=None):
        db = get_database()
        async with bloqueo_orden(identifier):
            order = await AbastecimientoService.obtener(identifier)
            if order['estado'] not in {'ENVIADA', 'PARCIAL'} or not data.conformidad:
                raise HTTPException(409, 'Debe aceptar una solicitud aprobada para registrar el despacho')
            if (order.get('resolucion_pendiente') or {}).get('decision') == 'CERRAR':
                raise HTTPException(409, 'La empresa cerró el pendiente de esta solicitud')
            key = data.clave_idempotencia or sha256(data.model_dump_json(exclude={'clave_idempotencia'}).encode()).hexdigest()
            if any(d.get('clave') == key for d in order.get('despachos', [])):
                return order
            pending = order.get('despacho_en_proceso')
            if pending and pending.get('clave') != key:
                raise HTTPException(409, 'Existe un despacho en proceso; reintente la misma operación para reconciliarlo')
            details = {d['id_detalle_reposicion']: d for d in await db["detalles_reposicion"].find({'id_orden_reposicion': identifier}, {'_id': 0}).to_list(length=1000)}
            if len({line.id_detalle_reposicion for line in data.lineas}) != len(data.lineas):
                raise HTTPException(409, 'Líneas de despacho duplicadas')
            shipped = {}
            for dispatch in order.get('despachos', []):
                for line in dispatch['lineas']:
                    shipped[line['id_detalle_reposicion']] = round(shipped.get(line['id_detalle_reposicion'], 0) + line['cantidad'], 3)
            lines = []
            for line in data.lineas:
                detail = details.get(line.id_detalle_reposicion)
                if not detail:
                    raise HTTPException(409, 'El producto no pertenece a la solicitud')
                amount = miles(line.cantidad, detail.get('unidad', 'unidad'))
                if amount + miles(shipped.get(line.id_detalle_reposicion, 0)) > miles(detail['cantidad_solicitada']):
                    raise HTTPException(409, 'El despacho acumulado supera la cantidad aprobada')
                lines.append({**line.model_dump(), 'id_producto': detail['id_producto'], 'unidad': detail.get('unidad', 'unidad')})
            # All business checks precede consumption. Per-order Mongo locks serialize
            # retries; a durable journal allows idempotent retry after a partial write.
            now = datetime.now(timezone.utc)
            dispatch = pending or {'id_despacho': str(uuid4()), 'clave': key, 'fecha': now, 'lineas': lines,
                        'observacion': data.observacion, 'id_proveedor': order['id_proveedor'], 'conformidad': True}
            if pending and pending['lineas'] != lines:
                raise HTTPException(409, 'La clave de despacho ya corresponde a otras cantidades')
            await db["ordenes_reposicion"].update_one({'id_orden_reposicion': identifier}, {'$set': {'despacho_en_proceso': dispatch}})
            for line in dispatch['lineas']:
                detail = details[line['id_detalle_reposicion']]
                operation = sha256(f"{dispatch['id_despacho']}:{detail['id_detalle_reposicion']}".encode()).hexdigest()
                await OfertaService.consumir(detail, line['cantidad'], operation)
            await db["ordenes_reposicion"].update_one({'id_orden_reposicion': identifier},
                {'$set': {'despacho': dispatch, 'fecha_despacho': dispatch['fecha'], 'aceptada_proveedor': True},
                 '$unset': {'despacho_en_proceso': ''},
                 '$push': {'despachos': dispatch, 'historial_estados': event(order['estado'], order['estado'], user,
                    role='PROVEEDOR', actor=order['id_proveedor'], reason='Despacho registrado', quantities=lines)}})
            return await AbastecimientoService.obtener(identifier)

    @staticmethod
    async def pendientes(user):
        from app.services.acceso_service import AccesoService
        db = get_database()
        orders = await db["ordenes_reposicion"].find({'id_empresa': user.id_empresa}, {'_id': 0}).to_list(length=10000)
        if user.es_operario:
            orders = [o for o in orders if o['id_almacen'] == user.id_almacen]
        if user.es_proveedor:
            orders = [o for o in orders if o['id_proveedor'] == user.id_proveedor and o['estado'] in {'ENVIADA', 'PARCIAL', 'RECIBIDA'}]
        result = []
        for order in orders:
            details = await db["detalles_reposicion"].find({'id_orden_reposicion': order['id_orden_reposicion']}, {'_id': 0}).to_list(length=1000)
            supplier = await db["proveedores"].find_one({'id_proveedor': order['id_proveedor'], 'id_empresa': user.id_empresa}, {'_id': 0}) or {}
            for detail in details:
                receipts = await db["detalles_recepcion"].find({'id_detalle_reposicion': detail['id_detalle_reposicion']}, {'_id': 0}).to_list(length=10000)
                accepted = sum(r.get('cantidad_aceptada', 0) for r in receipts)
                received = sum(r.get('cantidad_recibida', 0) for r in receipts)
                rejected = sum(r.get('cantidad_rechazada', 0) for r in receipts)
                dispatched = sum(line['cantidad'] for d in order.get('despachos', [order['despacho']] if order.get('despacho') else []) for line in d['lineas'] if line['id_detalle_reposicion'] == detail['id_detalle_reposicion'])
                result.append({'id_orden': order['id_orden_reposicion'], 'estado': order['estado'], **detail,
                    'id_proveedor': order['id_proveedor'], 'id_almacen': order['id_almacen'], 'proveedor': supplier.get('nombre'), 'telefono': supplier.get('telefono') if user.es_empresa else None,
                    'solicitada': detail['cantidad_solicitada'], 'despachada': dispatched, 'recibida': received,
                    'aceptada': accepted, 'rechazada': rejected, 'faltante': max(0, detail['cantidad_solicitada'] - accepted),
                    'diferencia_despacho': dispatched - received,
                    'motivos': [r.get('motivo_rechazo') or r.get('comentario_recepcion') for r in receipts if r.get('cantidad_rechazada')],
                    'resolucion': order.get('resolucion_pendiente'), 'fecha': order.get('fecha_orden') or order.get('fecha_creacion')})
        return result

    @staticmethod
    async def resolver(identifier, data, user):
        from app.services.acceso_service import AccesoService
        await AccesoService.verificar_orden(user, identifier)
        if not data.motivo.strip():
            raise HTTPException(422, 'El motivo es obligatorio')
        async with bloqueo_orden(identifier):
            order = await AbastecimientoService.obtener(identifier)
            if order['estado'] not in {'ENVIADA', 'PARCIAL'}:
                raise HTTPException(409, 'La solicitud no tiene una recepción pendiente de resolución')
            if order.get('despacho_en_proceso'):
                raise HTTPException(409, 'Hay un despacho pendiente de completar; reinténtelo antes de resolver la solicitud')
            resolution = {'decision': data.decision, 'motivo': data.motivo.strip(), 'fecha': datetime.now(timezone.utc), 'usuario': user.id_empresa}
            await get_database()["ordenes_reposicion"].update_one({'id_orden_reposicion': identifier},
                {'$set': {'resolucion_pendiente': resolution}, '$push': {'historial_estados': event(order['estado'], order['estado'], user, reason=data.decision + ': ' + data.motivo)}})
            if data.decision == 'CERRAR':
                for detail in await get_database()["detalles_reposicion"].find({'id_orden_reposicion': identifier}).to_list(length=1000):
                    await OfertaService.liberar(detail)
            return await AbastecimientoService.obtener(identifier)
