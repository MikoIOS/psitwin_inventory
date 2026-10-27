"""Read-only visual summary; all scope comes from the authenticated user."""
import math

from fastapi import HTTPException

from app.repositories.almacen_repository import AlmacenRepository
from app.repositories.zona_repository import ZonaRepository
from app.repositories.rack_repository import RackRepository
from app.repositories.producto_repository import ProductoRepository
from app.repositories.detalle_inventario_repository import DetalleInventarioRepository


def identifier(row, key):
    return row.get(key) or row.get("id")


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


async def inventory_summary(user, page=1, page_size=25):
    if user is None:
        raise HTTPException(401, "Se requiere autenticación para consultar el inventario.")
    if user.es_proveedor:
        raise HTTPException(403, "No tiene acceso al inventario.")
    warehouses = await AlmacenRepository.obtener_por_empresa(user.id_empresa)
    if user.es_operario:
        warehouses = [row for row in warehouses if identifier(row, "id_almacen") == user.id_almacen]
    warehouse_map = {identifier(row, "id_almacen"): row for row in warehouses}
    zones = await ZonaRepository.obtener_por_almacenes(list(warehouse_map)) if warehouse_map else []
    zone_map = {identifier(row, "id_zona"): row for row in zones}
    racks = await RackRepository.obtener_por_zonas(list(zone_map)) if zone_map else []
    rack_map = {identifier(row, "id_rack"): row for row in racks}
    inventories = await DetalleInventarioRepository().obtener_por_racks(list(rack_map)) if rack_map else []
    products = await ProductoRepository.collection().find({"id_empresa": user.id_empresa}, {"_id": 0}).to_list(length=None)
    product_map = {row["id_producto"]: row for row in products}
    # A corrupted cross-company product reference must never expose its stock.
    inventories = [row for row in inventories if row.get("id_producto") in product_map]
    grouped = {}
    for item in inventories:
        stock = item.get("stock_actual")
        if not numeric(stock) or stock < 0:
            raise HTTPException(503, "No se pudo verificar el stock: existen cantidades inválidas.")
        key = (item["id_producto"], item["id_rack"])
        group = grouped.setdefault(key, {"stock": 0, "ids": [], "header_ids": [], "minimums": []})
        group["stock"] += stock
        group["ids"].append(item["id_detalle_inventario"])
        group["header_ids"].append(item["id_inventario"])
        group["minimums"].append(item.get("stock_minimo"))
    rows = []
    for (product_id, rack_id), group in grouped.items():
        rack = rack_map[rack_id]
        zone = zone_map[rack["id_zona"]]
        warehouse = warehouse_map[zone["id_almacen"]]
        stock = group["stock"]
        minimum = group["minimums"][0] if len(group["minimums"]) == 1 else None
        status = "Sin stock" if stock == 0 else "Sin determinar"
        if stock > 0 and numeric(minimum) and minimum >= 0:
            status = "Bajo stock" if stock <= minimum else "Disponible"
        rows.append({"id_producto": product_id, "product_name": product_map[product_id].get("nombre"),
                     "id_almacen": identifier(warehouse, "id_almacen"), "warehouse_name": warehouse.get("nombre"),
                     "id_zona": identifier(zone, "id_zona"), "zone_name": zone.get("nombre"),
                     "id_rack": rack_id, "rack_name": rack.get("codigo") or rack.get("nombre"),
                     "ids_detalles_inventario": sorted(group["ids"]),
                     "id_inventario": next(iter(set(group["header_ids"]))) if len(set(group["header_ids"])) == 1 else None, "stock": stock, "status_label": status})
    rows.sort(key=lambda row: (row["id_producto"], row["id_almacen"], row["id_zona"], row["id_rack"]))
    total_units = sum(row["stock"] for row in rows)
    positive_products = {row["id_producto"] for row in rows if row["stock"] > 0}
    state = ("sin_almacenes" if not warehouses else "almacen_sin_productos" if not products and not inventories
             else "productos_sin_inventario" if not inventories else "stock_cero" if total_units == 0 else "stock_positivo")
    summary = {"distinct_products": len(positive_products), "total_units": total_units,
               "warehouse_count": len(warehouses), "catalog_products": len(products), "inventory_state": state,
               "rows": rows[(page - 1) * page_size:page * page_size],
               "pagination": {"page": page, "page_size": page_size, "total_rows": len(rows),
                              "total_pages": math.ceil(len(rows) / page_size)}}
    visualization = {"type": "inventory_summary", "version": 1, "title": "Resumen de inventario",
                     "cards": [{"label": label, "value_path": "data.inventory_summary." + key}
                               for label, key in (("Productos", "distinct_products"), ("Unidades", "total_units"), ("Almacenes", "warehouse_count"))],
                     "table": {"rows_path": "data.inventory_summary.rows",
                               "columns": [{"key": key, "label": label} for key, label in
                                           (("product_name", "Producto"), ("stock", "Stock"), ("warehouse_name", "Almacén"),
                                            ("zone_name", "Zona"), ("rack_name", "Rack"), ("status_label", "Estado"))],
                               "pagination_path": "data.inventory_summary.pagination"}}
    stock_by_product = {}
    for row in rows:
        stock_by_product[row["id_producto"]] = stock_by_product.get(row["id_producto"], 0) + row["stock"]
    series = {}
    for item in inventories:
        warehouse_id = zone_map[rack_map[item["id_rack"]]["id_zona"]]["id_almacen"]
        key = (item["id_inventario"],item["id_producto"])
        total = series.setdefault(key,{"id_inventario":key[0],"id_producto":key[1],
            "id_almacen":warehouse_id,"stock_actual":0})
        total["stock_actual"] += item["stock_actual"]
    return {"stock_por_producto_almacen":list(series.values()), "inventory_summary": summary, "visualization": visualization,
            "estado_inventario": state, "total_almacenes": len(warehouses),
            "total_registros_inventario": len(inventories), "productos_distintos": len(stock_by_product),
            "stock_total_unidades": total_units, "almacenes": warehouses, "inventarios": inventories[:50],
            "stock_por_producto": [{"id_producto": key, "nombre": product_map[key].get("nombre"), "stock_actual": value}
                                   for key, value in stock_by_product.items()],
            "ubicaciones": [{"id_producto": row["id_producto"], "id_rack": row["id_rack"], "stock_actual": row["stock"],
                             "rack": rack_map[row["id_rack"]], "zona": zone_map[row["id_zona"]]} for row in rows]}
