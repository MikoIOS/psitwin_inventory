from app.dto.cantidad import Cantidad
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class InventarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id_almacen: str


class InventarioResponse(BaseModel):
    id_inventario: str
    id_almacen: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime


class InventarioHistorialResponse(BaseModel):
    id_movimiento: str | None = None
    id_inventario: str
    id_detalle_inventario: str | None = None
    id_almacen: str | None = None
    id_producto: str | None = None
    id_rack: str | None = None
    fecha: datetime
    id_operario: str | None = None
    operario_nombre: str | None = None
    accion: str
    antes: dict | None = None
    despues: dict | None = None
    cantidad: Cantidad | None = None
    stock_anterior: Cantidad | None = None
    stock_nuevo: Cantidad | None = None
