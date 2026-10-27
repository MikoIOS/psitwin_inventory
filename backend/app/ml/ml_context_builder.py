from datetime import datetime, timedelta, timezone
from app.services.forecast_service import ForecastService
from app.repositories.inventario_repository import InventarioRepository

class MLContextBuilder:
    """Agregados de SALIDA acotados a almacén y corte, sin IDs M5 inventados."""
    def __init__(self, **kwargs):
        self.service = ForecastService()

    async def build_feature_context(self, id_inventario=None, fecha_base=None, horizon=1, *, id_almacen=None, id_producto=None):
        if id_inventario:
            header = await InventarioRepository().obtener_por_id(id_inventario)
            if not header:
                raise ValueError("Inventario general no encontrado")
            id_almacen = header["id_almacen"]
        if not id_almacen or not id_producto:
            raise ValueError("La serie requiere id_almacen e id_producto")
        if horizon not in range(1,8):
            raise ValueError("Artefactos directos disponibles solo D+1..D+7")
        corte = fecha_base or datetime.now(timezone.utc).date()
        if isinstance(corte,datetime):
            corte = corte.date()
        return await self.service.contexto(id_almacen,id_producto,corte,horizon)

    async def build_feature_contexts_7_days(self, **kwargs):
        return {h: await self.build_feature_context(horizon=h,**kwargs) for h in range(1,8)}
