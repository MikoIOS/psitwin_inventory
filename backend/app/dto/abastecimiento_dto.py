from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from app.dto.cantidad import Cantidad


class OfertaRequest(BaseModel):
    id_producto: str
    unidad: Literal['kg', 'unidad']
    precio: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    cantidad_total: Cantidad
    activa: bool = True
    observaciones: str | None = Field(default=None, max_length=1000)

    @model_validator(mode='after')
    def indivisible(self):
        if self.unidad == 'unidad' and not self.cantidad_total.is_integer():
            raise ValueError('Una unidad indivisible no admite fracciones')
        return self


class NivelRequest(BaseModel):
    codigo: str = Field(min_length=1, max_length=50)
    numero: int = Field(ge=1)


class NivelUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    estado: Literal['ACTIVO', 'INACTIVO', 'ARCHIVADO'] | None = None


class DecisionPendiente(BaseModel):
    decision: Literal['MANTENER', 'CERRAR']
    motivo: str = Field(min_length=1, max_length=1000)
