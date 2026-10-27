from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.dependencies import (
    get_usuario_activo,
    require_empresa,
    require_empresa_u_operario
)

from app.dto.auth_dto import (
    ResetPasswordRequest,
    UsuarioActual
)

from app.dto.proveedor_dto import (
    ProveedorCreate,
    ProveedorUpdate,
    ProveedorResponse,
    EstadoProveedor
)
from app.dto.email_verification_dto import (
    EmailVerificationCodeRequest,
    EmailVerificationResponse,
    EmailVerificationSendResponse,
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.cuenta_service import (
    sanitizar_cuenta
)

from app.services.proveedor_service import (
    ProveedorService
)
from app.services.email_verification_service import EmailVerificationService


# ============================================================
# PROVEEDORES
#
# EMPRESA   -> CRUD + cuentas (contraseña temporal).
# OPERARIO  -> solo lectura (elige proveedor al crear
#              una solicitud de reposición).
# PROVEEDOR -> solo puede leer el suyo.
# ============================================================

router = APIRouter(
    prefix="/proveedores",
    tags=["Proveedores"]
)

service = ProveedorService()
email_verification_service = EmailVerificationService()


def _lista(proveedores):
    return [
        sanitizar_cuenta(proveedor)
        for proveedor in proveedores
    ]


@router.post(
    "",
    response_model=ProveedorResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear(
    data: ProveedorCreate,
    user: UsuarioActual = Depends(require_empresa)
):
    data.id_empresa = user.id_empresa
    return sanitizar_cuenta(await service.crear(data))


@router.get(
    "",
    response_model=List[ProveedorResponse]
)
async def obtener_todos(
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return _lista(
        await service.obtener_por_empresa(
            user.id_empresa
        )
    )


@router.get(
    "/empresa/{id_empresa}",
    response_model=List[ProveedorResponse]
)
async def obtener_por_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    AccesoService.verificar_empresa(user, id_empresa)
    return _lista(await service.obtener_por_empresa(id_empresa))


@router.get(
    "/estado/{estado}",
    response_model=List[ProveedorResponse]
)
async def obtener_por_estado(
    estado: EstadoProveedor,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return _lista(
        AccesoService.filtrar_empresa(
            user,
            await service.obtener_por_estado(
                estado.value
            )
        )
    )


@router.get(
    "/{id_proveedor}",
    response_model=ProveedorResponse
)
async def obtener_por_id(
    id_proveedor: str,
    user: UsuarioActual = Depends(get_usuario_activo)
):
    if (
        user.es_proveedor
        and id_proveedor != user.id_proveedor
    ):
        raise HTTPException(
            status_code=403,
            detail="Solo puede consultar su propio proveedor"
        )

    return sanitizar_cuenta(
        await AccesoService.verificar_proveedor(
            user,
            id_proveedor
        )
    )


@router.put(
    "/{id_proveedor}",
    response_model=ProveedorResponse
)
async def actualizar(
    id_proveedor: str,
    data: ProveedorUpdate,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return sanitizar_cuenta(
        await service.actualizar(
            id_proveedor,
            data
        )
    )


# ============================================================
# RESET PASSWORD (EMPRESA)
#
# Crea o restablece la cuenta del proveedor.
# ============================================================

@router.post(
    "/{id_proveedor}/reset-password",
    response_model=ProveedorResponse
)
async def reset_password(
    id_proveedor: str,
    data: ResetPasswordRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return sanitizar_cuenta(
        await service.reset_password(
            id_proveedor,
            data.password_temporal,
            str(data.correo) if data.correo else None
        )
    )


@router.delete("/{id_proveedor}")
async def eliminar(
    id_proveedor: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return await service.eliminar(id_proveedor)


@router.post(
    "/{id_proveedor}/correo/enviar-verificacion",
    response_model=EmailVerificationSendResponse,
    summary="Enviar verificación de correo de proveedor",
)
async def send_proveedor_email_verification(
    id_proveedor: str,
    user: UsuarioActual = Depends(require_empresa),
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return await email_verification_service.request_entity_verification(
        "proveedor",
        id_proveedor,
    )


@router.post(
    "/{id_proveedor}/correo/verificar",
    response_model=EmailVerificationResponse,
    summary="Verificar correo de proveedor",
)
async def verify_proveedor_email(
    id_proveedor: str,
    data: EmailVerificationCodeRequest,
    user: UsuarioActual = Depends(require_empresa),
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return await email_verification_service.verify_entity_code(
        "proveedor",
        id_proveedor,
        data.codigo,
    )
