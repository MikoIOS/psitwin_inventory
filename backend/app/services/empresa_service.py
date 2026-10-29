from datetime import (
    datetime,
    timedelta,
    timezone
)

from uuid import uuid4

from typing import (
    Dict,
    Any
)

import bcrypt
import jwt

from jwt import (
    ExpiredSignatureError,
    InvalidTokenError
)

from fastapi import (
    HTTPException,
    status
)

from app.config.settings import (
    settings
)

from app.dto.empresa_dto import (
    EmpresaRegisterRequest,
    EmpresaLoginRequest,
    EmpresaUpdateRequest,
    EmpresaChangePasswordRequest,
    EmpresaDeleteRequest
)

from app.repositories import (
    empresa_repository
)

from app.services.cuenta_service import (
    validar_correo_disponible
)

from app.utils import (
    security
)


# ============================================================
# PASSWORD
# ============================================================

def hash_password(
    password: str
) -> str:

    return security.hash_password(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return security.verify_password(plain_password, hashed_password)


# ============================================================
# SANITIZAR
# ============================================================

def sanitize_empresa(
    empresa: Dict[str, Any]
) -> Dict[str, Any]:

    safe_empresa = dict(
        empresa
    )

    safe_empresa.pop(
        "password",
        None
    )

    safe_empresa.pop(
        "_id",
        None
    )

    return safe_empresa


# ============================================================
# JWT
# ============================================================

def create_access_token(
    id_empresa: str
) -> str:

    # Delegado a app.utils.security: el token
    # incluye ahora rol = EMPRESA e id_empresa.

    return security.create_access_token(
        sub=id_empresa,
        rol=security.ROL_EMPRESA,
        id_empresa=id_empresa
    )


def decode_access_token(
    token: str
) -> str:

    try:

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[
                settings.algorithm
            ]
        )

        id_empresa = payload.get(
            "sub"
        )

        token_type = payload.get(
            "type"
        )

        if (
            not id_empresa
            or
            token_type != "empresa"
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail="Token inválido",
                headers={
                    "WWW-Authenticate":
                        "Bearer"
                }
            )

        return id_empresa

    except ExpiredSignatureError:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Token expirado",
            headers={
                "WWW-Authenticate":
                    "Bearer"
            }
        )

    except InvalidTokenError:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Token inválido",
            headers={
                "WWW-Authenticate":
                    "Bearer"
            }
        )


# ============================================================
# REGISTER
# ============================================================

async def register_empresa(
    data: EmpresaRegisterRequest
) -> Dict[str, Any]:

    correo = (
        str(data.correo)
        .lower()
        .strip()
    )

    ruc = (
        data.ruc
        .strip()
    )

    existing_email = (
        await empresa_repository
        .find_by_email(
            correo
        )
    )

    if existing_email:

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Ya existe una empresa "
                "registrada con ese correo"
            )
        )

    # Único entre empresas, operarios y proveedores
    await validar_correo_disponible(
        correo
    )

    existing_ruc = (
        await empresa_repository
        .find_by_ruc(
            ruc
        )
    )

    if existing_ruc:

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Ya existe una empresa "
                "registrada con ese RUC"
            )
        )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    empresa = {
        "requiere_verificacion_registro": True,

        "id_empresa":
            str(
                uuid4()
            ),

        "nombre":
            data.nombre.strip(),

        "nombre_ceo": data.nombre_ceo,

        "ruc":
            ruc,

        "sector":
            data.sector.strip(),

        "correo":
            correo,

        "correo_verificado":
            False,

        "fecha_verificacion_correo":
            None,

        "telefono":
            data.telefono.strip(),

        "password":
            hash_password(
                data.password
            ),

        "fecha_creacion":
            now,

        "fecha_actualizacion":
            now
    }

    created = (
        await empresa_repository
        .create_empresa(
            empresa
        )
    )

    from app.services.welcome_email_service import WelcomeEmailService
    import logging
    try:
        await WelcomeEmailService().enqueue(created)
    except Exception:
        logging.getLogger(__name__).error('welcome_enqueue_failed empresa=%s', created['id_empresa'])
    return sanitize_empresa(created)


# ============================================================
# LOGIN
# ============================================================

async def login_empresa(
    data: EmpresaLoginRequest
) -> Dict[str, Any]:

    correo = (
        str(data.correo)
        .lower()
        .strip()
    )

    empresa = (
        await empresa_repository
        .find_by_email(
            correo
        )
    )

    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Correo o contraseña incorrectos"
            )
        )

    stored_password = (
        empresa.get(
            "password"
        )
    )

    if (
        not stored_password
        or
        not verify_password(
            data.password,
            stored_password
        )
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Correo o contraseña incorrectos"
            )
        )

    if empresa.get('requiere_verificacion_registro') is True and empresa.get('correo_verificado') is not True:
        raise HTTPException(403, 'Verifica tu correo antes de iniciar sesión.')

    token = create_access_token(
        empresa[
            "id_empresa"
        ]
    )

    return {

        "access_token":
            token,

        "token_type":
            "bearer",

        "empresa":
            sanitize_empresa(
                empresa
            )
    }


# ============================================================
# GET PERFIL
# ============================================================

async def get_empresa_profile(
    id_empresa: str
) -> Dict[str, Any]:

    empresa = (
        await empresa_repository
        .find_by_id(
            id_empresa
        )
    )

    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

    return sanitize_empresa(
        empresa
    )


# ============================================================
# UPDATE PERFIL
# ============================================================

async def update_empresa_profile(
    id_empresa: str,
    data: EmpresaUpdateRequest
) -> Dict[str, Any]:

    current = (
        await empresa_repository
        .find_by_id(
            id_empresa
        )
    )

    if not current:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

    update_data = (
        data.model_dump(
            exclude_unset=True
        )
    )

    if not update_data:

        return sanitize_empresa(
            current
        )

    # ========================================================
    # CORREO
    # ========================================================

    if "correo" in update_data:

        correo = (
            str(
                update_data[
                    "correo"
                ]
            )
            .lower()
            .strip()
        )

        existing = (
            await empresa_repository
            .find_by_email(
                correo
            )
        )

        if (
            existing
            and
            existing[
                "id_empresa"
            ]
            !=
            id_empresa
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "El correo ya está registrado"
                )
            )

        await validar_correo_disponible(
            correo,
            id_empresa
        )

        if current.get("correo") and current.get("correo").lower() != correo:
            update_data["correo_verificado"] = False
            update_data["fecha_verificacion_correo"] = None

        update_data[
            "correo"
        ] = correo


    # ========================================================
    # RUC
    # ========================================================

    if "ruc" in update_data:

        ruc = (
            update_data[
                "ruc"
            ]
            .strip()
        )

        existing = (
            await empresa_repository
            .find_by_ruc(
                ruc
            )
        )

        if (
            existing
            and
            existing[
                "id_empresa"
            ]
            !=
            id_empresa
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "El RUC ya está registrado"
                )
            )

        update_data[
            "ruc"
        ] = ruc


    # ========================================================
    # NORMALIZAR TEXTOS
    # ========================================================

    for field in [
        "nombre",
        "nombre_ceo",
        "sector",
        "telefono"
    ]:

        if (
            field in update_data
            and
            update_data[field]
        ):

            update_data[
                field
            ] = (
                update_data[
                    field
                ]
                .strip()
            )


    updated = (
        await empresa_repository
        .update_empresa(
            id_empresa,
            update_data
        )
    )

    if not updated:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

    return sanitize_empresa(
        updated
    )


# ============================================================
# PATCH PASSWORD
# ============================================================

async def change_empresa_password(
    id_empresa: str,
    data: EmpresaChangePasswordRequest
) -> Dict[str, str]:

    empresa = (
        await empresa_repository
        .find_by_id(
            id_empresa
        )
    )

    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

    current_hash = (
        empresa.get(
            "password"
        )
    )

    if (
        not current_hash
        or
        not verify_password(
            data.password_actual,
            current_hash
        )
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "La contraseña actual "
                "es incorrecta"
            )
        )

    if (
        data.password_actual
        ==
        data.password_nueva
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "La nueva contraseña debe "
                "ser diferente a la actual"
            )
        )

    new_hash = hash_password(
        data.password_nueva
    )

    success = (
        await empresa_repository
        .update_password(
            id_empresa,
            new_hash
        )
    )

    if not success:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "No se pudo actualizar "
                "la contraseña"
            )
        )

    return {
        "mensaje":
            "Contraseña actualizada correctamente"
    }


# ============================================================
# DELETE EMPRESA
# ============================================================

async def delete_empresa_profile(
    id_empresa: str,
    data: EmpresaDeleteRequest
) -> Dict[str, str]:

    empresa = (
        await empresa_repository
        .find_by_id(
            id_empresa
        )
    )

    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

    stored_password = (
        empresa.get(
            "password"
        )
    )

    if (
        not stored_password
        or
        not verify_password(
            data.password,
            stored_password
        )
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Contraseña incorrecta"
            )
        )

    deleted = (
        await empresa_repository
        .delete_empresa(
            id_empresa
        )
    )

    if not deleted:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "No se pudo eliminar "
                "la empresa"
            )
        )

    return {
        "mensaje":
            "Empresa eliminada correctamente"
    }
