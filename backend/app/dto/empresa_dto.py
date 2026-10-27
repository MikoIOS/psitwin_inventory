from pydantic import (
    BaseModel,
    EmailStr,
    Field
)

from typing import Optional


# ============================================================
# REGISTER
# ============================================================

class EmpresaRegisterRequest(BaseModel):

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

    id_empresa: str

    nombre: str

    ruc: str

    sector: str

    correo: EmailStr

    telefono: str

    correo_verificado: bool = False

    fecha_verificacion_correo: Optional[str] = None

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