import logging

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
from fastapi import BackgroundTasks, HTTPException
from app.services.welcome_email_service import WelcomeEmailService
from app.services.registration_link_service import RegistrationLinkService
from app.database.mongodb import get_database
from pymongo.collation import Collation
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
import re

link_service = RegistrationLinkService()

class DirectRegistrationRequest(EmpresaRegisterRequest):
    password: str = Field(min_length=8, max_length=128, repr=False)
    password_confirmation: str = Field(min_length=8, max_length=128, repr=False)

    @field_validator('nombre', 'sector', mode='before')
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('correo', mode='before')
    @classmethod
    def gmail(cls, value):
        value = str(value).strip().lower()
        if not value.endswith('@gmail.com'):
            raise ValueError('Utiliza un correo @gmail.com')
        return value

    @field_validator('ruc')
    @classmethod
    def ruc_peru(cls, value):
        value = value.strip()
        if not re.fullmatch(r'(10|15|16|17|20)\d{9}', value):
            raise ValueError('El RUC debe tener 11 dígitos y un prefijo peruano válido')
        check = (11 - sum(int(n) * w for n, w in zip(value[:10], [5,4,3,2,7,6,5,4,3,2])) % 11) % 10
        if check != int(value[-1]):
            raise ValueError('El dígito de control del RUC no es válido; el formato no confirma su existencia')
        return value

    @field_validator('telefono')
    @classmethod
    def phone(cls, value):
        if not re.fullmatch(r'\+?[\d\s-]{6,20}', value.strip()):
            raise ValueError('Teléfono no válido')
        return value.strip()

    @model_validator(mode='after')
    def matching(self):
        if self.password != self.password_confirmation:
            raise ValueError('Las contraseñas no coinciden')
        return self

class LinkConfirmRequest(BaseModel):
    token: str = Field(min_length=40, max_length=256, repr=False)

class LinkResendRequest(BaseModel):
    correo: EmailStr


welcome_email_service = WelcomeEmailService()


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
    data: DirectRegistrationRequest,
    background_tasks: BackgroundTasks
):
    db = get_database()
    await db.empresas.create_index('correo', unique=True, partialFilterExpression={'correo': {'$type': 'string'}}, collation=Collation(locale='en', strength=2))
    await db.empresas.create_index('ruc', unique=True, partialFilterExpression={'ruc': {'$type': 'string'}})
    await db.email_verifications.create_index('expires_at', expireAfterSeconds=0)
    await db.email_verifications.create_index('token_hash', sparse=True, unique=True)
    try:
        company = await empresa_service.register_empresa(data)
    except DuplicateKeyError:
        raise HTTPException(409, 'El correo o RUC ya está registrado. Si tu cuenta está pendiente, solicita otro enlace.')
    background_tasks.add_task(send_registration_verification, company['id_empresa'])
    return company


async def send_registration_verification(company_id: str):
    try:
        company = await empresa_service.get_empresa_profile(company_id)
        await link_service.send(company['correo'])
    except Exception:
        logging.getLogger(__name__).error('registration_verification_failed empresa=%s', company_id)


@router.post('/auth/verification/resend', status_code=202)
async def resend_registration_link(data: LinkResendRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(link_service.send, str(data.correo).strip().lower())
    return {'message': 'Si hay una cuenta pendiente, recibirás un enlace. Revisa Spam y espera antes de solicitar otro.'}


@router.post('/auth/verification/confirm')
async def confirm_registration_link(data: LinkConfirmRequest, background_tasks: BackgroundTasks):
    company_id = await link_service.confirm(data.token)
    background_tasks.add_task(welcome_email_service.deliver_safely, company_id)
    return {'message': 'Correo verificado. Tu cuenta está activa; ya puedes iniciar sesión.'}


@router.get('/empresas/me/bienvenida')
async def welcome_status(user: UsuarioActual = Depends(require_empresa)):
    return await welcome_email_service.status(user.id_empresa)


@router.post('/empresas/me/bienvenida/reintentar', status_code=202)
async def retry_welcome(background_tasks: BackgroundTasks, user: UsuarioActual = Depends(require_empresa)):
    company = await empresa_service.get_empresa_profile(user.id_empresa)
    if company.get('correo_verificado') is not True: raise HTTPException(409, 'Verifica tu correo antes de recibir la bienvenida')
    if not company.get('nombre_ceo'): raise HTTPException(422, 'Guarda el nombre del CEO en tu perfil primero')
    await welcome_email_service.enqueue(company)
    state = await welcome_email_service.status(user.id_empresa)
    if state['status'] in ('ENVIANDO', 'REVISAR_ENVIO'):
        raise HTTPException(409, 'El envío requiere comprobar su resultado antes de reintentarlo')
    if state['status'] != 'ENVIADO': background_tasks.add_task(welcome_email_service.deliver_safely, user.id_empresa)
    return state


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
    deprecated=True,
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
    deprecated=True,
    response_model=EmailVerificationResponse,
    summary="Verificar correo de empresa",
)
async def verify_empresa_email(
    id_empresa: str,
    data: EmailVerificationCodeRequest,
    background_tasks: BackgroundTasks,
    user: UsuarioActual = Depends(require_empresa),
):
    AccesoService.verificar_empresa(user, id_empresa)
    result = await email_verification_service.verify_entity_code(
        "empresa",
        id_empresa,
        data.codigo,
    )
    if result.get('verified'):
        background_tasks.add_task(welcome_email_service.deliver_safely, id_empresa)
    return result
