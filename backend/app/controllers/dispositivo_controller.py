from datetime import datetime
from typing import (
    List,
    Optional
)

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status
)

from app.dependencies.dependencies import (
    require_empresa,
    require_empresa_u_operario
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.dispositivo_dto import (
    DispositivoConToken,
    DispositivoCreate,
    DispositivoResponse,
    DispositivoUpdate,
    LecturasResponse,
    TokenResponse
)

from app.dto.empresa_dto import (
    MessageResponse
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.dispositivo_service import (
    DispositivoService
)


# ============================================================
# DISPOSITIVOS (sensores ESP32)
#
# EMPRESA  -> CRUD, token, lecturas.
# OPERARIO -> lee los de su almacén y sus lecturas.
# PROVEEDOR -> 403.
# ============================================================

router = APIRouter(
    prefix="/dispositivos",
    tags=["Dispositivos / Sensores"]
)


@router.post(
    "",
    response_model=DispositivoConToken,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar dispositivo (devuelve el token una sola vez)"
)
async def crear_dispositivo(
    data: DispositivoCreate,
    user: UsuarioActual = Depends(require_empresa)
):

    await AccesoService.verificar_almacen(
        user,
        data.id_almacen
    )

    return await DispositivoService.crear(
        data,
        user
    )


@router.get(
    "",
    response_model=List[DispositivoResponse]
)
async def listar_dispositivos(
    id_zona: Optional[str] = Query(default=None),
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    return await DispositivoService.listar(
        user,
        id_zona
    )


@router.get(
    "/{id_dispositivo}",
    response_model=DispositivoResponse
)
async def obtener_dispositivo(
    id_dispositivo: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    return await DispositivoService.respuesta(
        await DispositivoService.obtener_documento(
            id_dispositivo,
            user
        )
    )


@router.put(
    "/{id_dispositivo}",
    response_model=DispositivoResponse
)
async def actualizar_dispositivo(
    id_dispositivo: str,
    data: DispositivoUpdate,
    user: UsuarioActual = Depends(require_empresa)
):

    return await DispositivoService.actualizar(
        id_dispositivo,
        data,
        user
    )


@router.delete(
    "/{id_dispositivo}",
    response_model=MessageResponse
)
async def eliminar_dispositivo(
    id_dispositivo: str,
    user: UsuarioActual = Depends(require_empresa)
):

    return await DispositivoService.eliminar(
        id_dispositivo,
        user
    )


@router.post(
    "/{id_dispositivo}/token",
    response_model=TokenResponse,
    summary="Regenerar token (el anterior deja de valer)"
)
async def regenerar_token(
    id_dispositivo: str,
    user: UsuarioActual = Depends(require_empresa)
):

    return await DispositivoService.regenerar_token(
        id_dispositivo,
        user
    )


@router.get(
    "/{id_dispositivo}/lecturas",
    response_model=LecturasResponse
)
async def obtener_lecturas(
    id_dispositivo: str,
    desde: Optional[datetime] = Query(default=None),
    hasta: Optional[datetime] = Query(default=None),
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    return await DispositivoService.lecturas(
        id_dispositivo,
        user,
        desde,
        hasta
    )
