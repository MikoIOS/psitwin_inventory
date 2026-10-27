from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    AliasChoices
)


# ============================================================
# CREAR ALMACEN
# ============================================================

class AlmacenCreate(BaseModel):

    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    longitud: Decimal = Field(
        ...,
        ge=Decimal("-180.000000"),
        le=Decimal("180.000000"),
        max_digits=9,
        decimal_places=6
    )

    latitud: Decimal = Field(
        ...,
        ge=Decimal("-90.000000"),
        le=Decimal("90.000000"),
        max_digits=8,
        decimal_places=6
    )

    area_m2: float = Field(
        ...,
        gt=0
    )

    aforo: int = Field(
        ...,
        ge=0
    )

    tipo_almacen: str = Field(
        ...,
        min_length=2,
        max_length=100
    )


# ============================================================
# ACTUALIZAR ALMACEN
# ============================================================

class AlmacenUpdate(BaseModel):

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    longitud: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-180.000000"),
        le=Decimal("180.000000"),
        max_digits=9,
        decimal_places=6
    )

    latitud: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-90.000000"),
        le=Decimal("90.000000"),
        max_digits=8,
        decimal_places=6
    )

    area_m2: Optional[float] = Field(
        default=None,
        gt=0
    )

    aforo: Optional[int] = Field(
        default=None,
        ge=0
    )

    tipo_almacen: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )


# ============================================================
# RESPONSE
#
# Acepta temporalmente:
#
# id
# o
# id_almacen
#
# Pero la API siempre devuelve "id".
# ============================================================

class AlmacenResponse(BaseModel):

    id: str = Field(
        validation_alias=AliasChoices(
            "id",
            "id_almacen"
        )
    )

    id_empresa: str

    nombre: str

    longitud: Decimal

    latitud: Decimal

    area_m2: float

    aforo: int

    tipo_almacen: str

    fecha_creacion: datetime

    fecha_actualizacion: datetime