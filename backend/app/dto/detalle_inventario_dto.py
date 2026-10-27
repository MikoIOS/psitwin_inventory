from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class DetalleInventarioCreate(BaseModel):
    id_inventario: str
    id_producto: str
    id_rack: str
    stock_actual: int = Field(ge=0)
    stock_minimo: int = Field(default=0, ge=0)
    stock_maximo: int = Field(ge=0)

    @model_validator(mode="after")
    def validar_stocks(self):
        if self.stock_minimo > self.stock_maximo:
            raise ValueError("El stock mínimo no puede superar el máximo")
        return self


class DetalleInventarioUpdate(BaseModel):
    stock_minimo: int | None = Field(default=None, ge=0)
    stock_maximo: int | None = Field(default=None, ge=0)


class DetalleInventarioResponse(BaseModel):
    id_detalle_inventario: str
    id_inventario: str
    id_producto: str
    id_rack: str
    stock_actual: int
    stock_minimo: int
    stock_maximo: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
