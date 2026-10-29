from app.dto.cantidad import Cantidad
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class DetalleInventarioCreate(BaseModel):
    id_nivel: str | None = None
    id_inventario: str
    id_producto: str
    id_rack: str
    stock_actual: Cantidad = Field(ge=0)
    stock_minimo: Cantidad = Field(default=0, ge=0)
    stock_maximo: Cantidad = Field(ge=0)

    @model_validator(mode="after")
    def validar_stocks(self):
        if self.stock_minimo > self.stock_maximo:
            raise ValueError("El stock mínimo no puede superar el máximo")
        return self


class DetalleInventarioUpdate(BaseModel):
    stock_minimo: Cantidad | None = Field(default=None, ge=0)
    stock_maximo: Cantidad | None = Field(default=None, ge=0)


class DetalleInventarioResponse(BaseModel):
    id_nivel: str | None = None
    id_detalle_inventario: str
    id_inventario: str
    id_producto: str
    id_rack: str
    stock_actual: Cantidad
    stock_minimo: Cantidad
    stock_maximo: Cantidad
    fecha_creacion: datetime
    fecha_actualizacion: datetime
