from datetime import datetime
from typing import Optional, Literal

from pydantic import (
    BaseModel,
    Field,
    AliasChoices
)


# ============================================================
# CREAR ZONA
# ============================================================

class ZonaCreate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    descripcion: str | None = Field(default=None, max_length=1000)
    estado: Literal['ACTIVO', 'INACTIVO', 'ARCHIVADO'] = 'ACTIVO'
    max_racks: int | None = Field(default=None, ge=1)

    id_almacen: str

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    tipo_zona: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    # Lo decide la empresa al crear la zona.
    # Solo los racks de zonas refrigeradas tienen temperatura.
    refrigerada: bool = False

    temperatura_min: Optional[float] = None

    temperatura_max: Optional[float] = None

    # Cantidad de niveles (un rack por nivel).
    capacidad: int = Field(
        ...,
        ge=0
    )


# ============================================================
# ACTUALIZAR ZONA
# ============================================================

class ZonaUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    descripcion: str | None = Field(default=None, max_length=1000)
    estado: Literal['ACTIVO', 'INACTIVO', 'ARCHIVADO'] | None = None
    max_racks: int | None = Field(default=None, ge=1)

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    tipo_zona: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    refrigerada: Optional[bool] = None

    temperatura_min: Optional[float] = None

    temperatura_max: Optional[float] = None

    capacidad: Optional[int] = Field(
        default=None,
        ge=0
    )


# ============================================================
# RESPONSE
#
# Acepta:
#
# id
# id_zona
#
# pero siempre responde como:
#
# id
# ============================================================

class ZonaResponse(BaseModel):
    codigo: str | None = None
    descripcion: str | None = None
    estado: Literal['ACTIVO', 'INACTIVO', 'ARCHIVADO'] = 'ACTIVO'
    max_racks: int | None = None

    id: str = Field(
        validation_alias=AliasChoices(
            "id",
            "id_zona"
        )
    )

    id_almacen: str

    id_empresa: str

    nombre: str

    tipo_zona: str

    # Documentos antiguos sin el campo -> False
    refrigerada: bool = False

    temperatura_min: Optional[float] = None

    temperatura_max: Optional[float] = None

    capacidad: int

    fecha_creacion: datetime

    fecha_actualizacion: datetime
