from fastapi import (
    APIRouter,
    Depends,
    status
)

from app.dependencies.dependencies import (
    get_current_empresa_id,
    get_current_user,
    require_empresa
)

from app.dto.auth_dto import (
    CambiarPasswordRequest,
    LoginRequest,
    LoginResponse,
    MeResponse,
    UsuarioActual
)

from app.services.acceso_service import (
    AccesoService
)

from app.dto.empresa_dto import (
    EmpresaRegisterRequest,
    EmpresaLoginRequest,
    EmpresaUpdateRequest,
    EmpresaChangePasswordRequest,
    EmpresaDeleteRequest,
    EmpresaResponse,
    EmpresaLoginResponse,
    MessageResponse
)
from app.dto.email_verification_dto import (
    EmailVerificationCodeRequest,
    EmailVerificationResponse,
    EmailVerificationSendResponse,
)

from app.services import (
    empresa_service,
    auth_service
)
from app.services.email_verification_service import EmailVerificationService


router = APIRouter(
    tags=[
        "Autenticación / Empresa"
    ]
)


# ============================================================
# AUTH
#
# get_current_empresa_id: solo sesiones EMPRESA
# (tokens antiguos sin rol incluidos).
# ============================================================

email_verification_service = EmailVerificationService()


# ============================================================
# REGISTER
#
# POST /api/v1/auth/register
# ============================================================

@router.post(
    "/auth/register",
    response_model=EmpresaResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
    summary="Registrar empresa"
)
async def register(
    data: EmpresaRegisterRequest
):

    return await (
        empresa_service
        .register_empresa(
            data
        )
    )


# ============================================================
# LOGIN
#
# POST /api/v1/auth/login
# ============================================================

@router.post(
    "/auth/login",
    response_model=(
        LoginResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Iniciar sesión "
        "(empresa u operario)"
    )
)
async def login(
    data: LoginRequest
):

    return await (
        auth_service
        .login(
            data
        )
    )


# ============================================================
# ME (CUALQUIER ROL)
#
# GET /api/v1/auth/me
#
# Permitido aunque deba cambiar la contraseña.
# ============================================================

@router.get(
    "/auth/me",
    response_model=MeResponse,
    summary="Sesión actual"
)
async def me(
    user: UsuarioActual = Depends(
        get_current_user
    )
):

    return await auth_service.me(
        user
    )


# ============================================================
# CAMBIAR PASSWORD (OPERARIO / PROVEEDOR)
#
# PATCH /api/v1/auth/me/password
# ============================================================

@router.patch(
    "/auth/me/password",
    response_model=MessageResponse,
    summary=(
        "Cambiar contraseña "
        "(operario o proveedor)"
    )
)
async def cambiar_mi_password(
    data: CambiarPasswordRequest,
    user: UsuarioActual = Depends(
        get_current_user
    )
):

    return await auth_service.cambiar_password(
        user,
        data
    )


# ============================================================
# GET PERFIL
#
# GET /api/v1/empresas/me
# ============================================================

@router.get(
    "/empresas/me",
    response_model=EmpresaResponse,
    summary=(
        "Obtener empresa autenticada"
    )
)
async def get_my_empresa(
    id_empresa: str = Depends(
        get_current_empresa_id
    )
):

    return await (
        empresa_service
        .get_empresa_profile(
            id_empresa
        )
    )


# ============================================================
# UPDATE PERFIL
#
# PUT /api/v1/empresas/me
# ============================================================

@router.put(
    "/empresas/me",
    response_model=EmpresaResponse,
    summary=(
        "Actualizar empresa autenticada"
    )
)
async def update_my_empresa(
    data: EmpresaUpdateRequest,

    id_empresa: str = Depends(
        get_current_empresa_id
    )
):

    return await (
        empresa_service
        .update_empresa_profile(
            id_empresa,
            data
        )
    )


# ============================================================
# PATCH PASSWORD
#
# PATCH /api/v1/empresas/me/password
# ============================================================

@router.patch(
    "/empresas/me/password",
    response_model=MessageResponse,
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Cambiar contraseña"
    )
)
async def change_my_password(
    data:
        EmpresaChangePasswordRequest,

    id_empresa: str = Depends(
        get_current_empresa_id
    )
):

    return await (
        empresa_service
        .change_empresa_password(
            id_empresa,
            data
        )
    )


# ============================================================
# DELETE EMPRESA
#
# DELETE /api/v1/empresas/me
# ============================================================

@router.delete(
    "/empresas/me",
    response_model=MessageResponse,
    status_code=(
        status.HTTP_200_OK
    ),
    summary=(
        "Eliminar empresa autenticada"
    )
)
async def delete_my_empresa(
    data: EmpresaDeleteRequest,

    id_empresa: str = Depends(
        get_current_empresa_id
    )
):

    return await (
        empresa_service
        .delete_empresa_profile(
            id_empresa,
            data
        )
    )


@router.post(
    "/empresas/{id_empresa}/correo/enviar-verificacion",
    response_model=EmailVerificationSendResponse,
    summary="Enviar verificación de correo de empresa",
)
async def send_empresa_email_verification(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa),
):
    AccesoService.verificar_empresa(user, id_empresa)
    return await email_verification_service.request_entity_verification(
        "empresa",
        id_empresa,
    )


@router.post(
    "/empresas/{id_empresa}/correo/verificar",
    response_model=EmailVerificationResponse,
    summary="Verificar correo de empresa",
)
async def verify_empresa_email(
    id_empresa: str,
    data: EmailVerificationCodeRequest,
    user: UsuarioActual = Depends(require_empresa),
):
    AccesoService.verificar_empresa(user, id_empresa)
    return await email_verification_service.verify_entity_code(
        "empresa",
        id_empresa,
        data.codigo,
    )