from pydantic import (
    BaseModel,
    EmailStr,
    Field
)
from pydantic import field_validator

from typing import Optional
from datetime import datetime


# ============================================================
# REGISTER
# ============================================================

class EmpresaRegisterRequest(BaseModel):

    nombre_ceo: str = Field(..., min_length=1, max_length=100)

    @field_validator('nombre_ceo', mode='before')
    @classmethod
    def validar_nombre_ceo(cls, value):
        return value.strip() if isinstance(value, str) else value

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    ruc: str = Field(
        ...,
        min_length=8,
        max_length=20
    )

    sector: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    correo: EmailStr

    telefono: str = Field(
        ...,
        min_length=6,
        max_length=20
    )

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# LOGIN
# ============================================================

class EmpresaLoginRequest(BaseModel):

    correo: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# ACTUALIZAR PERFIL
# ============================================================

class EmpresaUpdateRequest(BaseModel):

    nombre_ceo: Optional[str] = Field(default=None, min_length=1, max_length=100)

    @field_validator('nombre_ceo', mode='before')
    @classmethod
    def validar_nombre_ceo(cls, value):
        return value.strip() if isinstance(value, str) else value

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    ruc: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=20
    )

    sector: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    correo: Optional[EmailStr] = None

    telefono: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=20
    )


# ============================================================
# CAMBIAR PASSWORD
# ============================================================

class EmpresaChangePasswordRequest(BaseModel):

    password_actual: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    password_nueva: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# ELIMINAR EMPRESA
#
# Pedimos password como confirmacion.
# ============================================================

class EmpresaDeleteRequest(BaseModel):

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# RESPONSE EMPRESA
# ============================================================

class EmpresaResponse(BaseModel):
    password_local_habilitada: bool = True

    nombre_ceo: Optional[str] = None

    id_empresa: str

    nombre: str

    ruc: str

    sector: str

    correo: EmailStr

    telefono: str

    correo_verificado: bool = False

    fecha_verificacion_correo: Optional[str] = None

    @field_validator('fecha_verificacion_correo', 'fecha_creacion', 'fecha_actualizacion', mode='before')
    @classmethod
    def serialize_verification_date(cls, value):
        return value.isoformat() if isinstance(value, datetime) else value

    fecha_creacion: str

    fecha_actualizacion: str


# ============================================================
# LOGIN RESPONSE
# ============================================================

class EmpresaLoginResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    empresa: EmpresaResponse


# ============================================================
# MESSAGE
# ============================================================

class MessageResponse(BaseModel):

    mensaje: str
