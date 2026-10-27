from typing import Optional

import jwt

from fastapi import (
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.repositories.operario_repository import (
    OperarioRepository
)

from app.repositories.proveedor_repository import (
    ProveedorRepository
)

from app.utils.security import (
    ROL_EMPRESA,
    ROL_OPERARIO,
    ROL_PROVEEDOR,
    decode_access_token
)


# auto_error=False: sin token respondemos 401
# (y no el 403 por defecto de HTTPBearer).
bearer_scheme = HTTPBearer(
    auto_error=False
)


# ============================================================
# EXCEPCION: CAMBIO DE PASSWORD OBLIGATORIO
#
# Se transforma en main.py en:
#
# 403 {"detail": "Debe cambiar su contraseña",
#      "code": "PASSWORD_CHANGE_REQUIRED"}
# ============================================================

class PasswordChangeRequired(Exception):

    detail = "Debe cambiar su contraseña"

    code = "PASSWORD_CHANGE_REQUIRED"


def _no_autorizado(
    detalle: str
) -> HTTPException:

    return HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail=detalle,
        headers={
            "WWW-Authenticate":
                "Bearer"
        }
    )


def _prohibido(
    detalle: str
) -> HTTPException:

    return HTTPException(
        status_code=(
            status.HTTP_403_FORBIDDEN
        ),
        detail=detalle
    )


# ============================================================
# GET CURRENT USER
#
# Decodifica el JWT. Tokens antiguos sin "rol"
# se tratan como EMPRESA (compatibilidad).
#
# Para OPERARIO y PROVEEDOR se relee el documento: así
# el estado, el almacén y debe_cambiar_password están
# siempre al día aunque el token sea anterior.
# ============================================================

async def get_current_user(
    credentials: Optional[
        HTTPAuthorizationCredentials
    ] = Depends(
        bearer_scheme
    )
) -> UsuarioActual:

    if (
        credentials is None
        or
        not credentials.credentials
    ):

        raise _no_autorizado(
            "No autenticado"
        )

    try:

        payload = decode_access_token(
            credentials.credentials
        )

    except jwt.ExpiredSignatureError:

        raise _no_autorizado(
            "Token expirado"
        )

    except jwt.InvalidTokenError:

        raise _no_autorizado(
            "Token inválido"
        )

    sub = payload.get(
        "sub"
    )

    if not sub:

        raise _no_autorizado(
            "Token inválido"
        )

    rol = payload.get(
        "rol"
    )

    # --------------------------------------------------------
    # TOKEN ANTIGUO / EMPRESA
    # --------------------------------------------------------

    if rol is None:

        if payload.get("type") not in (
            None,
            "empresa"
        ):

            raise _no_autorizado(
                "Token inválido"
            )

        rol = ROL_EMPRESA

    if rol == ROL_EMPRESA:

        return UsuarioActual(
            rol=ROL_EMPRESA,
            id_empresa=(
                payload.get("id_empresa")
                or
                sub
            )
        )

    # --------------------------------------------------------
    # OPERARIO
    # --------------------------------------------------------

    if rol == ROL_OPERARIO:

        operario = await (
            OperarioRepository
            .obtener_por_id(
                sub
            )
        )

        if not operario:

            raise _no_autorizado(
                "Operario no encontrado"
            )

        if (
            str(operario.get("estado", "")).upper()
            != "ACTIVO"
        ):

            raise _prohibido(
                "Operario inactivo"
            )

        return UsuarioActual(

            rol=ROL_OPERARIO,

            id_empresa=
                operario["id_empresa"],

            id_operario=
                operario["id_operario"],

            id_almacen=
                operario.get("id_almacen"),

            debe_cambiar_password=bool(
                operario.get(
                    "debe_cambiar_password",
                    False
                )
            )
        )

    # --------------------------------------------------------
    # PROVEEDOR
    # --------------------------------------------------------

    if rol == ROL_PROVEEDOR:

        proveedor = await (
            ProveedorRepository()
            .obtener_por_id(
                sub
            )
        )

        if not proveedor:

            raise _no_autorizado(
                "Proveedor no encontrado"
            )

        if (
            str(proveedor.get("estado", "")).upper()
            != "ACTIVO"
        ):

            raise _prohibido(
                "Proveedor inactivo"
            )

        return UsuarioActual(

            rol=ROL_PROVEEDOR,

            id_empresa=
                proveedor["id_empresa"],

            id_proveedor=
                proveedor["id_proveedor"],

            debe_cambiar_password=bool(
                proveedor.get(
                    "debe_cambiar_password",
                    False
                )
            )
        )

    raise _no_autorizado(
        "Token inválido"
    )


# ============================================================
# USUARIO ACTIVO
#
# Igual que get_current_user pero bloquea al operario /
# proveedor que aún no cambió su contraseña temporal.
# Usado por TODOS los endpoints salvo:
#
# GET   /auth/me
# PATCH /auth/me/password
# ============================================================

async def get_usuario_activo(
    user: UsuarioActual = Depends(
        get_current_user
    )
) -> UsuarioActual:

    if user.debe_cambiar_password:

        raise PasswordChangeRequired()

    return user


# ============================================================
# REQUIRE ROLES
#
# Uso: Depends(require_roles("EMPRESA", "OPERARIO"))
# ============================================================

def require_roles(*roles: str):

    async def dependencia(
        user: UsuarioActual = Depends(
            get_usuario_activo
        )
    ) -> UsuarioActual:

        if user.rol not in roles:

            raise _prohibido(
                "Su rol no puede realizar esta acción"
            )

        return user

    return dependencia


require_empresa = require_roles(ROL_EMPRESA)

require_operario = require_roles(ROL_OPERARIO)

require_proveedor = require_roles(ROL_PROVEEDOR)

require_empresa_u_operario = require_roles(
    ROL_EMPRESA,
    ROL_OPERARIO
)


# ============================================================
# COMPATIBILIDAD
#
# Devuelve solo el id_empresa de una sesión EMPRESA.
# ============================================================

async def get_current_empresa_id(
    user: UsuarioActual = Depends(
        require_empresa
    )
) -> str:

    return user.id_empresa
