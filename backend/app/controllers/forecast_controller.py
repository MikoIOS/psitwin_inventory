from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from app.dependencies.dependencies import require_empresa
from app.dto.auth_dto import UsuarioActual
from app.dto.forecast_dto import ForecastResponse, Horizonte
from app.services.acceso_service import AccesoService
from app.services.forecast_service import ForecastService
from app.repositories.inventario_repository import InventarioRepository

router = APIRouter(prefix="/forecast", tags=["Forecast"])
service = ForecastService()

@router.get("/almacenes/{id_almacen}/productos/{id_producto}", response_model=ForecastResponse)
async def predecir_producto(
    id_almacen: str, id_producto: str, horizonte_dias: int = Query(7, ge=1, le=90, json_schema_extra={"enum":[1,7,30,90]}),
    fecha_corte: date | None = None, dias: int = Query(400, ge=7, le=500),
    user: UsuarioActual = Depends(require_empresa)
):
    almacen = await AccesoService.verificar_almacen(user, id_almacen)
    producto = await AccesoService.verificar_producto(user, id_producto)
    if producto.get("id_empresa") != almacen.get("id_empresa"):
        raise HTTPException(403, "Producto y almacén incompatibles")
    await InventarioRepository().verificar_esquema()
    return await service.predecir(id_almacen, id_producto, horizonte_dias, fecha_corte, dias)

@router.get("/predict-7-days/{id_inventario}", response_model=ForecastResponse, deprecated=True)
async def predict_7_days(
    id_inventario: str, id_producto: str, dias: int = Query(400, ge=7, le=500),
    fecha_corte: date | None = None, user: UsuarioActual = Depends(require_empresa)
):
    header = await AccesoService.verificar_inventario(user, id_inventario)
    return await predecir_producto(header["id_almacen"], id_producto, 7, fecha_corte, dias, user)
