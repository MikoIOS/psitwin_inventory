from datetime import datetime, time, timezone

from app.database.mongodb import get_database
from app.repositories.serie_demanda_repository import SerieDemandaRepository
from app.repositories.demanda_historica_repository import DemandaHistoricaRepository


class AnalisisRepository(SerieDemandaRepository):
    async def purchase_history(self, tenant, warehouse, product, cutoff):
        pipeline = [
            {'$match': {'id_empresa': tenant, 'id_almacen': warehouse, 'estado': {'$ne': 'CANCELADA'}}},
            {'$lookup': {'from': 'detalles_reposicion', 'localField': 'id_orden_reposicion', 'foreignField': 'id_orden_reposicion', 'as': 'lineas'}},
            {'$unwind': '$lineas'}, {'$match': {'lineas.id_producto': product}},
            {'$group': {'_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$fecha_orden', 'timezone': 'America/Lima'}}, 'demanda': {'$sum': '$lineas.cantidad_solicitada'}}},
            {'$match': {'_id': {'$lte': cutoff.isoformat(), '$ne': None}}},
            {'$project': {'_id': 0, 'fecha': '$_id', 'demanda': 1}}, {'$sort': {'fecha': 1}}]
        return await get_database()['ordenes_reposicion'].aggregate(pipeline).to_list(length=None)

    async def received_product(self, warehouse, product):
        return bool(await get_database()['movimientos'].find_one({'id_almacen': warehouse, 'id_producto': product,
            'tipo_movimiento': 'ENTRADA', 'motivo_movimiento': 'RECEPCION', 'cantidad': {'$gt': 0}}, {'_id': 1}))

    """Read-only views. Warehouse + product are always scoped to the authenticated tenant."""
    async def catalog(self, tenant):
        db = get_database()
        warehouses = await db['almacenes'].find({'id_empresa': tenant}, {'_id': 0}).to_list(length=None)
        owned_w = [w.get('id', w.get('id_almacen')) for w in warehouses]
        accepted = await db.movimientos.distinct('id_producto', {'id_almacen': {'$in': owned_w},
            'tipo_movimiento': 'ENTRADA', 'motivo_movimiento': 'RECEPCION', 'cantidad': {'$gt': 0}})
        products = await db['productos'].find({'id_empresa': tenant, 'id_producto': {'$in': accepted}}, {'_id': 0}).to_list(length=None)
        imported = await DemandaHistoricaRepository().catalog(tenant)
        known_w = {w.get('id', w.get('id_almacen')) for w in warehouses}
        known_p = {p['id_producto'] for p in products}
        for row in imported:
            w, p = row['_id']['almacen'], row['_id']['producto']
            if w not in known_w:
                warehouses.append({'id': w, 'nombre': f'Almacén CSV {w}', 'id_empresa': tenant})
                known_w.add(w)
            if p not in known_p:
                products.append({'id_producto': p, 'nombre': f"Producto CSV {row.get('producto_original') or p}", 'id_empresa': tenant})
                known_p.add(p)
        return warehouses, products

    async def dataset_history(self, tenant, warehouse, product, cutoff):
        return await DemandaHistoricaRepository().history(tenant, warehouse, product, cutoff)

    async def history(self, warehouse, product, cutoff):
        first = await self.primera_salida(warehouse, product, cutoff)
        if not first:
            return []
        return await self.diarios(warehouse, first['fecha_hora'].date(), cutoff, [product])

    async def pairs(self, tenant, warehouse=None, product=None):
        warehouses, products = await self.catalog(tenant)
        allowed_warehouses = {w.get('id', w.get('id_almacen')) for w in warehouses}
        allowed_products = {p['id_producto'] for p in products}
        if warehouse: allowed_warehouses &= {warehouse}
        if product: allowed_products &= {product}
        # Historical source dimensions are not proof of operational entity ownership.
        db = get_database()
        operational_w = {w.get('id', w.get('id_almacen')) for w in await db['almacenes'].find(
            {'id_empresa': tenant}, {'_id': 0}).to_list(length=None)} & allowed_warehouses
        operational_p = {p['id_producto'] for p in await db['productos'].find(
            {'id_empresa': tenant}, {'_id': 0}).to_list(length=None)} & allowed_products
        query = {'id_almacen': {'$in': list(operational_w)}}
        headers = await get_database()['inventarios'].find(query, {'_id': 0}).to_list(length=None)
        pairs = set()
        for row in await DemandaHistoricaRepository().catalog(tenant):
            w, p = row['_id']['almacen'], row['_id']['producto']
            if w in allowed_warehouses and p in allowed_products: pairs.add((w, p))
        for header in headers:
            ids = await get_database()['detalles_inventario'].distinct('id_producto', {'id_inventario': header['id_inventario']})
            pairs.update((header['id_almacen'], identifier) for identifier in ids if identifier in operational_p)
        for identifier in operational_w:
            ids = await get_database()['movimientos'].distinct('id_producto', {'id_almacen': identifier, 'tipo_movimiento': 'SALIDA'})
            pairs.update((identifier, p) for p in ids if p in operational_p)
        return sorted(pairs)

    async def stock(self, warehouse, product):
        db = get_database()
        header = await db['inventarios'].find_one({'id_almacen': warehouse}, {'_id': 0})
        if not header: return None
        rows = await db['detalles_inventario'].find({'id_inventario': header['id_inventario'], 'id_producto': product}, {'stock_actual': 1, '_id': 0}).to_list(length=None)
        return sum(row['stock_actual'] for row in rows) if rows else None

    async def stock_for_tenant(self, tenant, warehouse, product):
        db = get_database()
        owned_warehouse = await db['almacenes'].find_one({'id_empresa': tenant, '$or': [{'id': warehouse}, {'id_almacen': warehouse}]})
        owned_product = await db['productos'].find_one({'id_empresa': tenant, 'id_producto': product})
        if not owned_warehouse or not owned_product: return None
        return await self.stock(warehouse, product)
