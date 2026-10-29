# app/services/auth_service.py

from typing import (
    Any,
    Dict
)

from fastapi import (
    HTTPException,
    status
)

from app.dto.auth_dto import (
    CambiarPasswordRequest,
    LoginRequest,
    UsuarioActual
)

from app.repositories.empresa_repository import (
    EmpresaRepository
)

from app.repositories.operario_repository import (
    OperarioRepository
)

from app.repositories.proveedor_repository import (
    ProveedorRepository
)

from app.services.cuenta_service import (
    sanitizar_cuenta
)

from app.services.empresa_service import (
    sanitize_empresa
)

from app.utils.security import (
    ROL_EMPRESA,
    ROL_OPERARIO,
    ROL_PROVEEDOR,
    create_access_token,
    hash_password,
    verify_password
)


def _credenciales_invalidas() -> HTTPException:

    return HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail=(
            "Correo o contraseña incorrectos"
        )
    )


def _password_ok(
    password: str,
    documento: Dict[str, Any] | None,
    campo: str
) -> bool:

    return bool(
        documento
        and
        documento.get(campo)
        and
        verify_password(
            password,
            documento[campo]
        )
    )


async def _empresa_de(
    id_empresa: str
) -> Dict[str, Any]:

    empresa = await (
        EmpresaRepository.obtener_por_id(
            id_empresa
        )
    )

    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "La empresa de la cuenta no existe"
            )
        )

    return sanitize_empresa(
        empresa
    )


# ============================================================
# LOGIN UNICO
#
# Busca el correo en EMPRESA -> OPERARIO -> PROVEEDOR.
# El correo es único entre los tres.
# ============================================================

async def login(
    data: LoginRequest
) -> Dict[str, Any]:

    correo = (
        str(data.correo)
        .lower()
        .strip()
    )

    # --------------------------------------------------------
    # EMPRESA
    # --------------------------------------------------------

    empresa = await (
        EmpresaRepository.obtener_por_correo(
            correo
        )
    )

    if empresa:

        if not _password_ok(
            data.password,
            empresa,
            "password"
        ):

            raise _credenciales_invalidas()

        if empresa.get('requiere_verificacion_registro') is True and empresa.get('correo_verificado') is not True:
            raise HTTPException(403, 'Verifica tu correo antes de iniciar sesión. Solicita otro enlace desde Registrar empresa si lo necesitas.')

        return {

            "access_token":
                create_access_token(
                    sub=empresa["id_empresa"],
                    rol=ROL_EMPRESA,
                    id_empresa=empresa["id_empresa"]
                ),

            "token_type":
                "bearer",

            "rol":
                ROL_EMPRESA,

            "empresa":
                sanitize_empresa(
                    empresa
                ),

            "operario":
                None,

            "proveedor":
                None,

            "debe_cambiar_password":
                False
        }

    # --------------------------------------------------------
    # OPERARIO
    # --------------------------------------------------------

    operario = await (
        OperarioRepository.obtener_por_correo(
            correo
        )
    )

    if operario:

        if not _password_ok(
            data.password,
            operario,
            "password_hash"
        ):

            raise _credenciales_invalidas()

        if (
            str(operario.get("estado", "")).upper()
            != "ACTIVO"
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail="Operario inactivo"
            )

        operario = sanitizar_cuenta(
            operario
        )

        return {

            "access_token":
                create_access_token(
                    sub=operario["id_operario"],
                    rol=ROL_OPERARIO,
                    id_empresa=operario["id_empresa"],
                    id_almacen=operario.get(
                        "id_almacen"
                    )
                ),

            "token_type":
                "bearer",

            "rol":
                ROL_OPERARIO,

            "empresa":
                await _empresa_de(
                    operario["id_empresa"]
                ),

            "operario":
                operario,

            "proveedor":
                None,

            "debe_cambiar_password":
                operario[
                    "debe_cambiar_password"
                ]
        }

    # --------------------------------------------------------
    # PROVEEDOR
    # --------------------------------------------------------

    proveedor = await (
        ProveedorRepository()
        .obtener_por_correo_con_cuenta(
            correo
        )
    )

    if not _password_ok(
        data.password,
        proveedor,
        "password_hash"
    ):

        raise _credenciales_invalidas()

    if (
        str(proveedor.get("estado", "")).upper()
        != "ACTIVO"
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Proveedor inactivo"
        )

    proveedor = sanitizar_cuenta(
        proveedor
    )

    return {

        "access_token":
            create_access_token(
                sub=proveedor["id_proveedor"],
                rol=ROL_PROVEEDOR,
                id_empresa=proveedor["id_empresa"],
                id_proveedor=proveedor["id_proveedor"]
            ),

        "token_type":
            "bearer",

        "rol":
            ROL_PROVEEDOR,

        "empresa":
            await _empresa_de(
                proveedor["id_empresa"]
            ),

        "operario":
            None,

        "proveedor":
            proveedor,

        "debe_cambiar_password":
            proveedor[
                "debe_cambiar_password"
            ]
    }


# ============================================================
# ME
#
# GET /auth/me (cualquier rol; permitido aunque
# deba cambiar la contraseña)
# ============================================================

async def me(
    user: UsuarioActual
) -> Dict[str, Any]:

    operario = None

    proveedor = None

    if user.es_operario:

        operario = sanitizar_cuenta(
            await OperarioRepository.obtener_por_id(
                user.id_operario
            )
        )

    if user.es_proveedor:

        proveedor = sanitizar_cuenta(
            await ProveedorRepository().obtener_por_id(
                user.id_proveedor
            )
        )

    return {

        "rol":
            user.rol,

        "empresa":
            await _empresa_de(
                user.id_empresa
            ),

        "operario":
            operario,

        "proveedor":
            proveedor,

        "debe_cambiar_password":
            user.debe_cambiar_password
    }


# ============================================================
# CAMBIAR PASSWORD (OPERARIO / PROVEEDOR)
#
# PATCH /auth/me/password
# ============================================================

async def cambiar_password(
    user: UsuarioActual,
    data: CambiarPasswordRequest
) -> Dict[str, str]:

    if user.es_operario:

        cuenta = await OperarioRepository.obtener_por_id(
            user.id_operario
        )

    elif user.es_proveedor:

        cuenta = await ProveedorRepository().obtener_por_id(
            user.id_proveedor
        )

    else:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "La empresa cambia su contraseña "
                "en /empresas/me/password"
            )
        )

    if not _password_ok(
        data.password_actual,
        cuenta,
        "password_hash"
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

    cambios = {

        "password_hash":
            hash_password(
                data.password_nueva
            ),

        "debe_cambiar_password":
            False
    }

    if user.es_operario:

        await OperarioRepository.actualizar(
            user.id_operario,
            cambios
        )

    else:

        await ProveedorRepository().actualizar(
            user.id_proveedor,
            cambios
        )

    return {
        "mensaje":
            "Contraseña actualizada correctamente"
    }
