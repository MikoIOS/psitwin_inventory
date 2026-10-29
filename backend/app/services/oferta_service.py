"""Supplier offers. Atomic integer milli-quantities prevent overselling on standalone MongoDB."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from fastapi import HTTPException
from pymongo import ReturnDocument
from app.database.mongodb import get_database
from app.services.stock_lock import bloqueo_recurso


def miles(value, unit='kg'):
    value = Decimal(str(value))
    if not value.is_finite() or value < 0 or value != value.quantize(Decimal('.001')):
        raise HTTPException(422, 'Cantidad no válida; máximo tres decimales')
    if unit == 'unidad' and value != value.to_integral_value():
        raise HTTPException(422, 'Las unidades indivisibles no admiten fracciones')
    return int(value * 1000)


def subtotal(quantity, cents):
    result = int((Decimal(str(quantity)) * cents).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    if result > 9007199254740991:
        raise HTTPException(422, 'El importe supera el máximo monetario admitido')
    return result


def public(offer):
    row = {k: v for k, v in offer.items() if k not in {'_id', 'reservas', 'consumos'}}
    row.update(cantidad_total=offer['total_miles'] / 1000,
               cantidad_reservada=offer['reservada_miles'] / 1000,
               cantidad_despachada=offer['despachada_miles'] / 1000,
               cantidad_disponible=(offer['total_miles'] - offer['reservada_miles'] - offer['despachada_miles']) / 1000,
               precio=offer['precio_centimos'] / 100, moneda='PEN')
    return row


class OfertaService:
    @staticmethod
    async def listar(user, solo_disponibles=False, id_proveedor=None):
        db = get_database()
        query = {'id_empresa': user.id_empresa}
        if user.es_proveedor:
            query['id_proveedor'] = user.id_proveedor
        elif id_proveedor:
            query['id_proveedor'] = id_proveedor
        rows = await db["ofertas_proveedor"].find(query, {'_id': 0}).to_list(length=2000)
        products = {p['id_producto']: p for p in await db["productos"].find({'id_empresa': user.id_empresa}, {'_id': 0}).to_list(length=10000)}
        providers = {p['id_proveedor']: p for p in await db["proveedores"].find({'id_empresa': user.id_empresa}, {'_id': 0}).to_list(length=10000)}
        result = []
        for offer in rows:
            product = products.get(offer['id_producto'])
            provider = providers.get(offer['id_proveedor'])
            if not product or not provider:
                continue
            row = public(offer)
            row.update(producto=product.get('nombre'), familia=product.get('familia'), categoria=product.get('categoria'), proveedor=provider.get('nombre'))
            valid = offer['activa'] and product.get('activo', True) and provider.get('estado') == 'ACTIVO' and row['cantidad_disponible'] > 0
            if not solo_disponibles or valid:
                result.append(row)
        return result

    @staticmethod
    async def guardar(data, user):
        db = get_database()
        product = await db["productos"].find_one({'id_producto': data.id_producto, 'id_empresa': user.id_empresa})
        if not product:
            raise HTTPException(404, 'Producto no encontrado')
        if data.unidad != product.get('unidad', 'unidad'):
            raise HTTPException(409, 'La unidad de oferta debe coincidir con el producto; no se convierten unidades automáticamente')
        identifier = sha256(f'{user.id_empresa}:{user.id_proveedor}:{data.id_producto}'.encode()).hexdigest()
        async with bloqueo_recurso('oferta:' + identifier):
            existing = await db["ofertas_proveedor"].find_one({'id_oferta': identifier})
            total = miles(data.cantidad_total, data.unidad)
            if existing and total < existing['reservada_miles'] + existing['despachada_miles']:
                raise HTTPException(409, 'La cantidad total no puede ser menor que lo reservado y despachado')
            now = datetime.now(timezone.utc)
            row = {'id_oferta': identifier, 'id_empresa': user.id_empresa, 'id_proveedor': user.id_proveedor,
                   'id_producto': data.id_producto, 'unidad': data.unidad,
                   'precio_centimos': int(data.precio * 100), 'total_miles': total,
                   'activa': data.activa, 'observaciones': data.observaciones, 'fecha_actualizacion': now}
            await db["ofertas_proveedor"].update_one({'id_oferta': identifier}, {'$set': row,
                '$setOnInsert': {'reservada_miles': 0, 'despachada_miles': 0, 'reservas': {}, 'fecha_creacion': now}}, upsert=True)
            return public(await db["ofertas_proveedor"].find_one({'id_oferta': identifier}))

    @staticmethod
    async def reservar(tenant, provider, product_id, quantity, key, offer_id=None):
        db = get_database()
        product = await db["productos"].find_one({'id_empresa': tenant, 'id_producto': product_id, 'activo': {'$ne': False}})
        supplier = await db["proveedores"].find_one({'id_empresa': tenant, 'id_proveedor': provider, 'estado': 'ACTIVO'})
        if not product or not supplier:
            raise HTTPException(404, 'Producto o proveedor activo no encontrado')
        query = {'id_empresa': tenant, 'id_proveedor': provider, 'id_producto': product_id, 'activa': True}
        if offer_id:
            query['id_oferta'] = offer_id
        offer = await db["ofertas_proveedor"].find_one(query)
        if not offer:
            raise HTTPException(409, 'El proveedor no tiene una oferta vigente de este producto')
        amount = miles(quantity, offer['unidad'])
        if amount <= 0:
            raise HTTPException(422, 'La cantidad debe ser positiva')
        async with bloqueo_recurso('oferta:' + offer['id_oferta']):
            current = await db['ofertas_proveedor'].find_one(query)
            if not current:
                raise HTTPException(409, 'La oferta dejó de estar disponible')
            line_total = subtotal(quantity, current['precio_centimos'])
            updated = await db["ofertas_proveedor"].find_one_and_update({**query,
                f'reservas.{key}': {'$exists': False},
                '$expr': {'$gte': [{'$subtract': ['$total_miles', {'$add': ['$reservada_miles', '$despachada_miles']}]}, amount]}},
                {'$inc': {'reservada_miles': amount}, '$set': {f'reservas.{key}': amount}}, return_document=ReturnDocument.AFTER)
            if not updated:
                raise HTTPException(409, 'Disponibilidad insuficiente u operación duplicada; actualiza las ofertas')
        return {'id_oferta': offer['id_oferta'], 'unidad': updated['unidad'], 'precio_centimos': updated['precio_centimos'],
                'costo_unitario': updated['precio_centimos'] / 100, 'subtotal_centimos': line_total,
                'reserva_clave': key, 'cantidad_solicitada': quantity, 'id_producto': product_id}

    @staticmethod
    async def liberar(detail):
        if not detail.get('id_oferta'):
            return
        db = get_database()
        key = detail['reserva_clave']
        async with bloqueo_recurso('oferta:' + detail['id_oferta']):
            offer = await db["ofertas_proveedor"].find_one({'id_oferta': detail['id_oferta']})
            amount = (offer or {}).get('reservas', {}).get(key, 0)
            if amount:
                await db["ofertas_proveedor"].update_one({'id_oferta': detail['id_oferta'], f'reservas.{key}': amount},
                    {'$inc': {'reservada_miles': -amount}, '$unset': {f'reservas.{key}': ''}})

    @staticmethod
    async def consumir(detail, quantity, operation=None):
        if not detail.get('id_oferta'):
            return  # Legacy orders retain their original, unreserved workflow.
        amount = miles(quantity, detail['unidad'])
        key = detail['reserva_clave']
        if operation:
            existing = await get_database()["ofertas_proveedor"].find_one({'id_oferta': detail['id_oferta'], f'consumos.{operation}': amount})
            if existing:
                return
        query = {'id_oferta': detail['id_oferta'], f'reservas.{key}': {'$gte': amount}}
        update = {'$inc': {'reservada_miles': -amount, 'despachada_miles': amount, f'reservas.{key}': -amount}}
        if operation:
            query[f'consumos.{operation}'] = {'$exists': False}
            update['$set'] = {f'consumos.{operation}': amount}
        result = await get_database()["ofertas_proveedor"].update_one(
            query, update)
        if result.modified_count != 1:
            raise HTTPException(409, 'La reserva de la línea no permite este despacho')

    @staticmethod
    async def cambiar_cantidad(detail, quantity):
        if not detail.get('id_oferta'):
            raise HTTPException(409, 'La línea antigua debe reemplazarse por una oferta vigente para modificar cantidades')
        amount = miles(quantity, detail.get('unidad', 'unidad'))
        previous = miles(detail['cantidad_solicitada'], detail.get('unidad', 'unidad'))
        delta = amount - previous
        query = {'id_oferta': detail['id_oferta'], f"reservas.{detail['reserva_clave']}": previous}
        if delta > 0:
            query.update(activa=True, **{'$expr': {'$gte': [{'$subtract': ['$total_miles', {'$add': ['$reservada_miles', '$despachada_miles']}]}, delta]}})
        async with bloqueo_recurso('oferta:' + detail['id_oferta']):
            result = await get_database()["ofertas_proveedor"].update_one(query,
                {'$inc': {'reservada_miles': delta, f"reservas.{detail['reserva_clave']}": delta}})
            if result.matched_count != 1:
                raise HTTPException(409, 'Disponibilidad insuficiente o reserva modificada')
