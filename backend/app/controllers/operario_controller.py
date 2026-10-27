from fastapi import (
    APIRouter,
    Depends,
    status
)

from app.dependencies.dependencies import (
    require_empresa
)

from app.services.acceso_service import (
    AccesoService
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.empresa_dto import (
    MessageResponse
)

from app.dto.operario_dto import (
    OperarioCreate,
    OperarioUpdate,
    OperarioResetPassword,
    OperarioResponse
)
from app.dto.email_verification_dto import (
    EmailVerificationCodeRequest,
    EmailVerificationResponse,
    EmailVerificationSendResponse,
)

from app.services.operario_service import (
    OperarioService
)
from app.services.email_verification_service import EmailVerificationService


router = APIRouter(
    prefix="/operarios",
    tags=["Operarios"]
)


service = OperarioService()
email_verification_service = EmailVerificationService()


# ============================================================
# CREAR OPERARIO (EMPRESA)
# ============================================================

@router.post(
    "",
    response_model=OperarioResponse,
    status_code=
        status.HTTP_201_CREATED
)
async def crear_operario(
    data: OperarioCreate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.crear_operario(
            data,
            user
        )
    )


# ============================================================
# OBTENER TODOS (EMPRESA)
# ============================================================

@router.get(
    "",
    response_model=
        list[OperarioResponse]
)
async def obtener_operarios(
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_operarios(
            user
        )
    )


# ============================================================
# POR EMPRESA
# ============================================================

@router.get(
    "/empresa/{id_empresa}",
    response_model=
        list[OperarioResponse]
)
async def obtener_por_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_por_empresa(
            id_empresa,
            user
        )
    )


# ============================================================
# POR ESTADO
# ============================================================

@router.get(
    "/estado/{estado}",
    response_model=
        list[OperarioResponse]
)
async def obtener_por_estado(
    estado: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_por_estado(
            estado,
            user
        )
    )


# ============================================================
# POR TURNO
# ============================================================

@router.get(
    "/turno/{turno}",
    response_model=
        list[OperarioResponse]
)
async def obtener_por_turno(
    turno: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_por_turno(
            turno,
            user
        )
    )


# ============================================================
# POR ID
# ============================================================

@router.get(
    "/{id_operario}",
    response_model=
        OperarioResponse
)
async def obtener_operario(
    id_operario: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_operario(
            id_operario,
            user
        )
    )


# ============================================================
# ACTUALIZAR
# ============================================================

@router.put(
    "/{id_operario}",
    response_model=
        OperarioResponse
)
async def actualizar_operario(
    id_operario: str,
    data: OperarioUpdate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.actualizar_operario(
            id_operario,
            data,
            user
        )
    )


# ============================================================
# RESET PASSWORD (EMPRESA)
# ============================================================

@router.post(
    "/{id_operario}/reset-password",
    response_model=
        OperarioResponse
)
async def reset_password(
    id_operario: str,
    data: OperarioResetPassword,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.reset_password(
            id_operario,
            data,
            user
        )
    )


@router.post(
    "/{id_operario}/correo/enviar-verificacion",
    response_model=EmailVerificationSendResponse,
    summary="Enviar verificación de correo de operario",
)
async def send_operario_email_verification(
    id_operario: str,
    user: UsuarioActual = Depends(require_empresa),
):
    await AccesoService.verificar_operario(user, id_operario)
    return await email_verification_service.request_entity_verification(
        "operario",
        id_operario,
    )


@router.post(
    "/{id_operario}/correo/verificar",
    response_model=EmailVerificationResponse,
    summary="Verificar correo de operario",
)
async def verify_operario_email(
    id_operario: str,
    data: EmailVerificationCodeRequest,
    user: UsuarioActual = Depends(require_empresa),
):
    await AccesoService.verificar_operario(user, id_operario)
    return await email_verification_service.verify_entity_code(
        "operario",
        id_operario,
        data.codigo,
    )


# ============================================================
# ELIMINAR
# ============================================================

@router.delete(
    "/{id_operario}",
    status_code=
        status.HTTP_200_OK
)
async def eliminar_operario(
    id_operario: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.eliminar_operario(
            id_operario,
            user
        )
    )
