from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DetalleReposicionCreate(BaseModel):
    id_producto: str

    cantidad_solicitada: int = Field(
        ...,
        gt=0
    )

    costo_unitario: Optional[float] = Field(
        default=None,
        ge=0
    )


class DetalleReposicionUpdate(BaseModel):
    cantidad_solicitada: Optional[int] = Field(
        default=None,
        gt=0
    )

    costo_unitario: Optional[float] = Field(
        default=None,
        ge=0
    )


class DetalleReposicionResponse(BaseModel):
    id_detalle_reposicion: str
    id_orden_reposicion: str
    id_producto: str

    cantidad_solicitada: int
    costo_unitario: Optional[float] = None

    fecha_creacion: datetime
    fecha_actualizacion: datetime