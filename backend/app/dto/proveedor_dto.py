from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EstadoProveedor(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class ProveedorCreate(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    ruc: str = Field(
        ...,
        min_length=11,
        max_length=11
    )

    correo: Optional[EmailStr] = None

    telefono: Optional[str] = Field(
        default=None,
        max_length=20
    )

    direccion: Optional[str] = Field(
        default=None,
        max_length=250
    )

    tiempo_entrega_estimado_dias: int = Field(
        default=1,
        ge=0
    )

    estado: EstadoProveedor = EstadoProveedor.ACTIVO

    # Cuenta de acceso (rol PROVEEDOR). Requiere correo.
    # Queda con debe_cambiar_password = true.
    password_temporal: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=128
    )


class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    correo: Optional[EmailStr] = None

    telefono: Optional[str] = Field(
        default=None,
        max_length=20
    )

    direccion: Optional[str] = Field(
        default=None,
        max_length=250
    )

    tiempo_entrega_estimado_dias: Optional[int] = Field(
        default=None,
        ge=0
    )

    estado: Optional[EstadoProveedor] = None


class ProveedorResponse(BaseModel):
    id_proveedor: str
    id_empresa: str

    nombre: str
    ruc: str

    correo: Optional[EmailStr] = None
    tiene_cuenta: bool = False
    debe_cambiar_password: bool = False
    correo_verificado: bool = False
    fecha_verificacion_correo: Optional[datetime] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

    tiempo_entrega_estimado_dias: int

    estado: EstadoProveedor

    fecha_creacion: datetime
    fecha_actualizacion: datetime