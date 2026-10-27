from fastapi import HTTPException
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.detalle_inventario_repository import DetalleInventarioRepository
from app.repositories.almacen_repository import AlmacenRepository
from app.repositories.producto_repository import ProductoRepository

async def validar_referencia(data):
    header = await InventarioRepository().obtener_por_id(data.id_inventario)
    warehouse = await AlmacenRepository.obtener_por_id(data.id_almacen)
    product = await ProductoRepository.obtener_por_id(data.id_producto)
    if not header or not warehouse or not product:
        raise HTTPException(404, "Referencia de inventario no encontrada")
    if header["id_almacen"] != data.id_almacen or warehouse["id_empresa"] != data.id_empresa or product.get("id_empresa") != data.id_empresa:
        raise HTTPException(409, "Empresa, almacén, inventario y producto incompatibles")
    if data.id_detalle_inventario:
        detail = await DetalleInventarioRepository().obtener_por_id(data.id_detalle_inventario)
        if not detail or detail["id_inventario"] != data.id_inventario or detail["id_producto"] != data.id_producto:
            raise HTTPException(409, "Detalle de inventario incompatible")

    if getattr(data,"id_alerta",None):
        from app.database.mongodb import get_database
        alert = await get_database()["alertas"].find_one({"id_alerta":data.id_alerta},{"_id":0})
        if not alert or any(alert.get(k) != getattr(data,k) for k in ("id_empresa","id_almacen","id_inventario","id_producto")):
            raise HTTPException(404,"Alerta no encontrada en el ámbito de la recomendación")

    aggregate_alert = getattr(getattr(data,"tipo_alerta",None),"value",None) == "RIESGO_STOCKOUT"
    aggregate_recommendation = getattr(getattr(data,"tipo_recomendacion",None),"value",None) == "REABASTECER"
    if aggregate_alert or aggregate_recommendation:
        data.id_detalle_inventario = None
        if aggregate_alert:
            details = await DetalleInventarioRepository().obtener_por_inventario(data.id_inventario)
            data.stock_actual = sum(d["stock_actual"] for d in details if d["id_producto"] == data.id_producto)
