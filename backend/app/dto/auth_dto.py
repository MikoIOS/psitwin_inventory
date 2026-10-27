from typing import (
    Literal,
    Optional
)

from pydantic import (
    BaseModel,
    EmailStr,
    Field
)

from app.dto.empresa_dto import (
    EmpresaResponse
)

from app.dto.operario_dto import (
    OperarioResponse
)

from app.dto.proveedor_dto import (
    ProveedorResponse
)


# ============================================================
# LOGIN UNIFICADO
#
# POST /api/v1/auth/login
# ============================================================

class LoginRequest(BaseModel):

    correo: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


class LoginResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    rol: Literal[
        "EMPRESA",
        "OPERARIO",
        "PROVEEDOR"
    ]

    # Siempre presente. Para OPERARIO:
    # la empresa a la que pertenece.
    empresa: EmpresaResponse

    operario: Optional[
        OperarioResponse
    ] = None

    proveedor: Optional[
        ProveedorResponse
    ] = None

    debe_cambiar_password: bool = False


# ============================================================
# GET /auth/me
# ============================================================

class MeResponse(BaseModel):

    rol: Literal[
        "EMPRESA",
        "OPERARIO",
        "PROVEEDOR"
    ]

    empresa: EmpresaResponse

    operario: Optional[
        OperarioResponse
    ] = None

    proveedor: Optional[
        ProveedorResponse
    ] = None

    debe_cambiar_password: bool = False


# ============================================================
# PATCH /auth/me/password (OPERARIO / PROVEEDOR)
# ============================================================

class CambiarPasswordRequest(BaseModel):

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
# RESET PASSWORD (EMPRESA)
#
# POST /operarios/{id}/reset-password
# POST /proveedores/{id}/reset-password
# ============================================================

class ResetPasswordRequest(BaseModel):

    password_temporal: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    # Opcional: da correo a una cuenta antigua sin correo.
    correo: Optional[EmailStr] = None


# ============================================================
# USUARIO AUTENTICADO
#
# Resultado de get_current_user.
# ============================================================

class UsuarioActual(BaseModel):

    rol: Literal[
        "EMPRESA",
        "OPERARIO",
        "PROVEEDOR"
    ]

    id_empresa: str

    id_operario: Optional[str] = None

    id_almacen: Optional[str] = None

    id_proveedor: Optional[str] = None

    debe_cambiar_password: bool = False

    @property
    def es_proveedor(self) -> bool:

        return self.rol == "PROVEEDOR"

    @property
    def es_empresa(self) -> bool:

        return self.rol == "EMPRESA"

    @property
    def es_operario(self) -> bool:

        return self.rol == "OPERARIO"
