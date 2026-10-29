from datetime import (
    datetime,
    timedelta,
    timezone
)

from typing import (
    Any,
    Dict,
    Optional
)

import bcrypt
import jwt
from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()

from app.config.settings import (
    settings
)


# ============================================================
# ROLES
# ============================================================

ROL_EMPRESA = "EMPRESA"

ROL_OPERARIO = "OPERARIO"

ROL_PROVEEDOR = "PROVEEDOR"


# ============================================================
# PASSWORD
#
# bcrypt: mismo esquema que ya usaban las empresas,
# ahora compartido con los operarios.
# ============================================================

def hash_password(
    password: str
) -> str:

    return _password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    try:

        if hashed_password.startswith('$argon2'):
            return _password_hash.verify(plain_password, hashed_password)

        return bcrypt.checkpw(
            plain_password.encode(
                "utf-8"
            ),
            hashed_password.encode(
                "utf-8"
            )
        )

    except Exception:

        return False


# ============================================================
# JWT
#
# Payload:
#
# sub            -> id_empresa o id_operario
# rol            -> EMPRESA | OPERARIO
# id_empresa
# id_almacen     -> solo OPERARIO
# id_proveedor   -> solo PROVEEDOR
# type           -> "empresa" | "operario" (compatibilidad)
# ============================================================

def create_access_token(
    sub: str,
    rol: str = ROL_EMPRESA,
    id_empresa: Optional[str] = None,
    id_almacen: Optional[str] = None,
    id_proveedor: Optional[str] = None
) -> str:

    now = datetime.now(
        timezone.utc
    )

    expiration = (
        now
        +
        timedelta(
            minutes=(
                settings
                .access_token_expire_minutes
            )
        )
    )

    payload: Dict[str, Any] = {

        "sub": sub,

        "rol": rol,

        "type": rol.lower(),

        "id_empresa": (
            id_empresa
            or
            sub
        ),

        "iat": now,

        "exp": expiration
    }

    if rol == ROL_OPERARIO:

        payload[
            "id_almacen"
        ] = id_almacen

    if rol == ROL_PROVEEDOR:

        payload[
            "id_proveedor"
        ] = id_proveedor

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm
    )


def decode_access_token(
    token: str
) -> Dict[str, Any]:

    # Lanza jwt.ExpiredSignatureError /
    # jwt.InvalidTokenError; quien llama
    # decide el HTTP status.

    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[
            settings.algorithm
        ]
    )
