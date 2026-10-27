from app.database.mongodb import get_database

async def consultar_historial(key, identifier):
    db = get_database()
    history = await db["inventario_historial"].find({key:identifier},{"_id":0}).to_list(length=None)
    movements = await db["movimientos"].find({key:identifier},{"_id":0}).to_list(length=None)
    for movement in movements:
        history.append({
            **{k:movement.get(k) for k in ("id_inventario","id_detalle_inventario","id_almacen",
                "id_producto","id_rack","id_operario","cantidad","stock_anterior","stock_nuevo")},
            "id_movimiento":movement["id_movimiento"], "fecha":movement["fecha_hora"],
            "accion":movement["tipo_movimiento"],
            "antes":{"stock_actual":movement["stock_anterior"]},
            "despues":{"stock_actual":movement["stock_nuevo"]}
        })
    return sorted(history,key=lambda row:str(row["fecha"]),reverse=True)
