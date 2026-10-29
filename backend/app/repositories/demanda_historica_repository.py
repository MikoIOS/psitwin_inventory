"""Dataset observations, isolated by tenant; never writes inventory or movements."""
from datetime import date, timedelta

from app.database.mongodb import get_database


class DemandaHistoricaRepository:
    def collection(self):
        return get_database()['demanda_historica']

    async def catalog(self, tenant):
        rows = await self.collection().aggregate([
            {'$match': {'id_empresa': tenant}},
            {'$group': {'_id': {'almacen': '$id_almacen', 'producto': '$id_producto'},
                        'producto_original': {'$first': '$producto_original'}}},
            {'$sort': {'_id.almacen': 1, '_id.producto': 1}},
        ]).to_list(length=None)
        return rows

    async def history(self, tenant, warehouse, product, cutoff=None):
        query = {'id_empresa': tenant, 'id_almacen': warehouse, 'id_producto': product}
        if cutoff:
            query['fecha'] = {'$lte': cutoff.isoformat()}
        return await self.collection().find(query, {'_id': 0}).sort('fecha', 1).to_list(length=None)

    async def report(self, tenant, warehouse=None, product=None, start=None, end=None,
                     frequency='diaria', offset=0, limit=100):
        query = {'id_empresa': tenant}
        if warehouse: query['id_almacen'] = warehouse
        if product: query['id_producto'] = product
        if start or end:
            query['fecha'] = {}
            if start: query['fecha']['$gte'] = start.isoformat()
            if end: query['fecha']['$lte'] = end.isoformat()
        # Daily totals and per-series ranking are computed in MongoDB, not in the LLM.
        daily = await self.collection().aggregate([
            {'$match': query}, {'$group': {'_id': '$fecha', 'cantidad': {'$sum': '$cantidad'}}},
            {'$sort': {'_id': 1}},
        ]).to_list(length=None)
        buckets = {}
        for row in daily:
            day = date.fromisoformat(row['_id'])
            bucket = day.replace(day=1) if frequency == 'mensual' else day - timedelta(days=day.weekday()) if frequency == 'semanal' else day
            key = bucket.isoformat()
            buckets[key] = buckets.get(key, 0) + row['cantidad']
        ranking = await self.collection().aggregate([
            {'$match': query},
            {'$group': {'_id': {'id_almacen': '$id_almacen', 'id_producto': '$id_producto'},
                        'cantidad': {'$sum': '$cantidad'}, 'registros': {'$sum': 1}}},
            {'$sort': {'cantidad': -1, '_id.id_producto': 1, '_id.id_almacen': 1}}, {'$limit': 20},
        ]).to_list(length=None)
        products = await self.collection().aggregate([
            {'$match': query}, {'$group': {'_id': '$id_producto', 'cantidad': {'$sum': '$cantidad'}}},
            {'$sort': {'cantidad': -1, '_id': 1}}, {'$limit': 20},
        ]).to_list(length=None)
        count = await self.collection().count_documents(query)
        records = await self.collection().find(query, {'_id': 0}).sort([
            ('fecha', 1), ('id_almacen', 1), ('id_producto', 1)]).skip(offset).limit(limit).to_list(length=limit)
        total = sum(row['cantidad'] for row in daily)
        midpoint = len(daily) // 2
        first = sum(r['cantidad'] for r in daily[:midpoint]) / midpoint if midpoint else None
        last = sum(r['cantidad'] for r in daily[midpoint:]) / (len(daily) - midpoint) if midpoint else None
        return {'id_empresa': tenant, 'frecuencia': frequency, 'total': total,
                'promedio_diario': total / len(daily) if daily else None,
                'dias_observados': len(daily), 'documentos': count, 'offset': offset, 'limite': limit,
                'fecha_inicio': daily[0]['_id'] if daily else None,
                'fecha_fin': daily[-1]['_id'] if daily else None,
                'serie': [{'fecha': k, 'cantidad': v} for k, v in buckets.items()],
                'ranking': [{**r['_id'], 'cantidad': r['cantidad'], 'registros': r['registros']} for r in ranking],
                'ranking_productos': [{'id_producto': r['_id'], 'cantidad': r['cantidad']} for r in products],
                'tendencia': {'promedio_primera_mitad': first, 'promedio_segunda_mitad': last},
                'registros': records,
                'advertencias': ['Demanda del CSV, incluye observaciones marcadas es_imputado. No representa stock.',
                                 'Promedio por fechas presentes; no se agregan días ausentes. Tendencia descriptiva, no pronóstico.']}
