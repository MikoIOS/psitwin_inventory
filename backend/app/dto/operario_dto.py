from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field
)


# ============================================================
# CREAR OPERARIO
#
# Solo EMPRESA. id_empresa se toma del token
# (si se envía, se ignora).
# ============================================================

class OperarioCreate(BaseModel):

    id_empresa: Optional[str] = None

    id_almacen: str

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    apellido: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    correo: EmailStr

    cargo: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    turno: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    estado: str = Field(
        default="ACTIVO",
        min_length=2,
        max_length=50
    )

    correo: EmailStr

    password_temporal: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# ACTUALIZAR OPERARIO
# ============================================================

class OperarioUpdate(BaseModel):

    id_almacen: Optional[str] = None

    correo: Optional[EmailStr] = None

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    apellido: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    correo: Optional[EmailStr] = None

    cargo: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    turno: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    estado: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50
    )


# ============================================================
# RESET PASSWORD (EMPRESA)
#
# POST /operarios/{id}/reset-password
# ============================================================

class OperarioResetPassword(BaseModel):

    password_temporal: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    # Opcional: permite dar correo a un operario
    # antiguo sin cuenta en la misma llamada.
    correo: Optional[EmailStr] = None


# ============================================================
# RESPONSE
#
# Nunca incluye el hash de la contraseña.
# id_almacen / correo son opcionales para operarios
# antiguos creados antes de las cuentas.
# ============================================================

class OperarioResponse(BaseModel):

    id_operario: str
    id_empresa: str

    nombre: str
    apellido: str
    cargo: str
    turno: str
    estado: str

    id_almacen: Optional[str] = None
    correo_verificado: bool = False
    fecha_verificacion_correo: Optional[datetime] = None

    correo: Optional[str] = None

    tiene_cuenta: bool = False

    debe_cambiar_password: bool = False

    fecha_creacion: datetime
    fecha_actualizacion: datetime
