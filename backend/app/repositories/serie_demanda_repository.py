from datetime import datetime, time, timedelta, timezone
from app.database.mongodb import get_database

class SerieDemandaRepository:
    """Toda SALIDA, sin filtrar motivo, agregada por producto y almacén UTC."""
    async def diarios(self, id_almacen, fecha_inicio, fecha_fin, ids_productos=None):
        query = {
            "id_almacen": id_almacen, "tipo_movimiento": "SALIDA",
            "fecha_hora": {"$gte": datetime.combine(fecha_inicio, time.min, timezone.utc),
                           "$lte": min(datetime.combine(fecha_fin, time.max, timezone.utc), datetime.now(timezone.utc))}
        }
        if ids_productos is not None:
            query["id_producto"] = {"$in": list(ids_productos)}
        pipeline = [
            {"$match": query},
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$fecha_hora", "timezone": "UTC"}},
                        "demanda": {"$sum": "$cantidad"}}},
            {"$project": {"_id": 0, "fecha": "$_id", "demanda": 1}}, {"$sort": {"fecha": 1}}
        ]
        return await get_database()["movimientos"].aggregate(pipeline).to_list(length=None)

    async def primera_salida(self, id_almacen, id_producto, corte):
        return await get_database()["movimientos"].find_one(
            {"id_almacen": id_almacen, "id_producto": id_producto, "tipo_movimiento": "SALIDA",
             "fecha_hora": {"$lte": min(datetime.combine(corte, time.max, timezone.utc), datetime.now(timezone.utc))}},
            {"_id": 0, "fecha_hora": 1}, sort=[("fecha_hora", 1)])

    async def productos_almacen(self, id_almacen):
        header = await get_database()["inventarios"].find_one({"id_almacen": id_almacen}, {"_id": 0})
        ids = set()
        if header:
            ids.update(await get_database()["detalles_inventario"].distinct(
                "id_producto", {"id_inventario": header["id_inventario"]}))
        ids.update(await get_database()["movimientos"].distinct("id_producto", {"id_almacen": id_almacen}))
        return await get_database()["productos"].find({"id_producto": {"$in": list(ids)}}, {"_id": 0}).to_list(length=None)
