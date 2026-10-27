from fastapi import HTTPException
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.detalle_inventario_repository import DetalleInventarioRepository
from app.repositories.almacen_repository import AlmacenRepository


class InventarioService:
    def __init__(self):
        self.repository = InventarioRepository()
        self.detalles = DetalleInventarioRepository()

    async def crear_inventario(self, data, id_operario=None):
        if not await AlmacenRepository.obtener_por_id(data.id_almacen):
            raise HTTPException(404, "Almacén no encontrado")
        return await self.repository.garantizar(data.id_almacen)

    async def obtener_inventarios(self):
        return await self.repository.obtener_todos()

    async def obtener_inventario(self, id_inventario):
        header = await self.repository.obtener_por_id(id_inventario)
        if not header:
            raise HTTPException(404, "Inventario general no encontrado")
        return header

    async def detalles_inventario(self, id_inventario, id_producto=None, id_rack=None, id_zona=None):
        await self.obtener_inventario(id_inventario)
        rows = await self.detalles.obtener_por_inventario(id_inventario)
        if id_zona:
            from app.repositories.rack_repository import RackRepository
            racks = await RackRepository.obtener_por_zona(id_zona)
            allowed = {r.get("id_rack") or r.get("id") for r in racks}
            rows = [r for r in rows if r["id_rack"] in allowed]
        return [r for r in rows if (not id_producto or r["id_producto"] == id_producto)
                and (not id_rack or r["id_rack"] == id_rack)]

    async def stock_por_producto(self, id_inventario):
        rows = await self.detalles_inventario(id_inventario)
        grouped = {}
        for row in rows:
            item = grouped.setdefault(row["id_producto"], {"id_inventario": id_inventario,
                "id_producto": row["id_producto"], "stock_actual": 0, "distribucion": []})
            item["stock_actual"] += row["stock_actual"]
            item["distribucion"].append(row)
        return list(grouped.values())

    async def obtener_historial(self, id_inventario):
        return await self.repository.obtener_historial(id_inventario)
