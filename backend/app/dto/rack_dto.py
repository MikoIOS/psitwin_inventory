from datetime import datetime
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator
)


class EstadoRack(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    LLENO = "LLENO"
    MANTENIMIENTO = "MANTENIMIENTO"
    INACTIVO = "INACTIVO"
    ARCHIVADO = "ARCHIVADO"


def _validar_rango(modelo):

    if (
        modelo.temperatura_min is not None
        and modelo.temperatura_max is not None
        and modelo.temperatura_min > modelo.temperatura_max
    ):
        raise ValueError(
            "La temperatura mínima no puede "
            "ser mayor que la máxima"
        )

    return modelo


# ============================================================
# CREAR RACK (EMPRESA)
#
# capacidad -> carga máxima en KG.
# nivel     -> 1..zona.capacidad; un rack por nivel.
# temperatura_min/max -> solo (y obligatorias) si la
#                        zona es refrigerada.
# estado no se pide: nace DISPONIBLE.
# ============================================================

class RackCreate(BaseModel):
    tipo_rack: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator('tipo_rack')
    @classmethod
    def validar_tipo(cls, value):
        if value is not None and not value.strip():
            raise ValueError('Indique un tipo de rack válido')
        return value.strip() if value else value
    max_niveles: int = Field(default=1, ge=1, le=1000)
    id_zona: str

    codigo: str = Field(
        min_length=1,
        max_length=50
    )

    nivel: int = Field(default=1,
        ge=1
    )

    capacidad: float = Field(
        gt=0
    )

    temperatura_min: float | None = None

    temperatura_max: float | None = None

    estado: EstadoRack = EstadoRack.DISPONIBLE

    @model_validator(mode="after")
    def validar(self):
        return _validar_rango(self)


# ============================================================
# EDITAR RACK (OPERARIO de ese almacén)
#
# Solo estado y temperatura.
# ============================================================

class RackUpdate(BaseModel):
    tipo_rack: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator('tipo_rack')
    @classmethod
    def validar_tipo(cls, value):
        return RackCreate.validar_tipo(value)
    max_niveles: int | None = Field(default=None, ge=1, le=1000)

    estado: EstadoRack | None = None

    temperatura_min: float | None = None

    temperatura_max: float | None = None

    @model_validator(mode="after")
    def validar(self):
        return _validar_rango(self)


class RackResponse(BaseModel):
    tipo_rack: str | None = None
    max_niveles: int = 1
    id_rack: str
    id_zona: str

    codigo: str

    nivel: int

    # Carga máxima en kg
    capacidad: float

    estado: EstadoRack

    # Racks antiguos / zonas no refrigeradas -> null
    temperatura_min: float | None = None

    temperatura_max: float | None = None

    # Σ stock_actual × peso del producto
    carga_kg: float = 0

    # capacidad - carga_kg
    libre_kg: float = 0

    fecha_creacion: datetime

    fecha_actualizacion: datetime


# ============================================================
# RACK DISPONIBLE
#
# GET /racks/disponibles?id_almacen=&id_producto=&cantidad=
# ============================================================

class RackDisponibleResponse(RackResponse):

    id_almacen: str

    nombre_zona: str | None = None
