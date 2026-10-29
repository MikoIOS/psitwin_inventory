from app.dto.cantidad import Cantidad
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DetalleReposicionCreate(BaseModel):
    id_oferta: str | None = None
    id_producto: str

    cantidad_solicitada: Cantidad = Field(
        ...,
        gt=0
    )

    costo_unitario: Optional[float] = Field(
        default=None,
        ge=0
    )


class DetalleReposicionUpdate(BaseModel):
    cantidad_solicitada: Cantidad | None = Field(
        default=None,
        gt=0
    )

    costo_unitario: Optional[float] = Field(
        default=None,
        ge=0
    )


class DetalleReposicionResponse(BaseModel):
    id_oferta: str | None = None
    unidad: str = 'unidad'
    precio_centimos: int | None = None
    subtotal_centimos: int | None = None
    id_detalle_reposicion: str
    id_orden_reposicion: str
    id_producto: str

    cantidad_solicitada: Cantidad
    costo_unitario: Optional[float] = None

    fecha_creacion: datetime
    fecha_actualizacion: datetime
