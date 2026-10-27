from datetime import datetime, timedelta, timezone
from app.services.forecast_service import ForecastService
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.detalle_inventario_repository import DetalleInventarioRepository

class DemandHistory:
    """Compatibilidad segura: una cabecera requiere seleccionar producto."""
    def __init__(self, **kwargs):
        self.service = ForecastService()

    async def obtener_historial(self, id_inventario=None, dias=400, fecha_fin=None, *, id_almacen=None, id_producto=None):
        if id_inventario:
            header = await InventarioRepository().obtener_por_id(id_inventario)
            if not header:
                raise ValueError("Inventario general no encontrado")
            id_almacen = header["id_almacen"]
        if not id_almacen or not id_producto:
            raise ValueError("La serie requiere id_almacen e id_producto")
        corte = fecha_fin or datetime.now(timezone.utc).date()
        if isinstance(corte, datetime):
            corte = corte.date()
        return await self.service.historial(id_almacen,id_producto,corte,dias)

    async def obtener_ultimos_dias(self, **kwargs):
        return (await self.obtener_historial(**kwargs)).to_dict("records")
