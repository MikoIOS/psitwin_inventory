# app/services/cuenta_service.py

from typing import (
    Any,
    Dict,
    Optional
)

from fastapi import (
    HTTPException,
    status
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


# ============================================================
# CUENTAS (OPERARIO / PROVEEDOR)
#
# Utilidades compartidas por las cuentas que crea la empresa.
# ============================================================


# ============================================================
# SANITIZAR
#
# Nunca exponer password_hash. Calcula:
#
# tiene_cuenta          -> correo + contraseña
# debe_cambiar_password -> contraseña temporal vigente
# ============================================================

def sanitizar_cuenta(
    documento: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:

    if not documento:
        return documento

    result = dict(
        documento
    )

    password_hash = result.pop(
        "password_hash",
        None
    )

    result.pop(
        "_id",
        None
    )

    result[
        "tiene_cuenta"
    ] = bool(
        password_hash
        and
        result.get("correo")
    )

    result[
        "debe_cambiar_password"
    ] = bool(
        result.get(
            "debe_cambiar_password",
            False
        )
    )

    return result


# ============================================================
# CORREO UNICO
#
# Único entre empresas, operarios y proveedores.
# excluir: id del operario / proveedor / empresa que
# ya es dueño del correo (al editar).
# ============================================================

async def validar_correo_disponible(
    correo: str,
    excluir: Optional[str] = None
) -> str:

    correo = (
        str(correo)
        .lower()
        .strip()
    )

    empresa = await (
        EmpresaRepository
        .obtener_por_correo(
            correo
        )
    )

    operario = await (
        OperarioRepository
        .obtener_por_correo(
            correo
        )
    )

    proveedor = await (
        ProveedorRepository()
        .obtener_por_correo_con_cuenta(
            correo
        )
    )

    ocupado = (
        (
            empresa
            and
            empresa["id_empresa"] != excluir
        )
        or
        (
            operario
            and
            operario["id_operario"] != excluir
        )
        or
        (
            proveedor
            and
            proveedor["id_proveedor"] != excluir
        )
    )

    if ocupado:

        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,
            detail=
                "El correo ya está registrado"
        )

    return correo
