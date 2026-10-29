from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.dependencies import (
    get_usuario_activo,
    require_empresa,
    require_empresa_u_operario,
    require_operario,
    require_proveedor
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.orden_reposicion_dto import (
    OrdenReposicionCreate,
    OrdenReposicionUpdate,
    OrdenReposicionResponse,
    EstadoOrdenReposicion,
    DevolverOrdenRequest,
    DespachoRequest
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.orden_reposicion_service import (
    OrdenReposicionService
)


# ============================================================
# SOLICITUD / ORDEN DE REPOSICION
#
# PENDIENTE -> (OBSERVADA <-> PENDIENTE) -> ENVIADA
#           -> PARCIAL -> RECIBIDA ; CANCELADA
#
# OPERARIO : crea y edita (PENDIENTE / OBSERVADA), reenvía;
#            lee las de su almacén.
# EMPRESA  : valida (-> ENVIADA), devuelve con comentario
#            (-> OBSERVADA), cancela; lee todas las suyas.
# PROVEEDOR: lee las ENVIADAS a él y registra el despacho.
# ============================================================

router = APIRouter(
    prefix="/ordenes-reposicion",
    tags=["Ordenes de Reposicion"]
)

service = OrdenReposicionService()


def _alcance(
    user: UsuarioActual,
    ordenes: list
) -> list:

    ordenes = AccesoService.filtrar_empresa(
        user,
        ordenes
    )

    if user.es_operario:

        ordenes = [
            orden
            for orden in ordenes
            if orden.get("id_almacen")
            == user.id_almacen
        ]

    return ordenes


# ============================================================
# CREAR SOLICITUD (OPERARIO)
#
# Almacén = el del operario. Queda PENDIENTE.
# ============================================================

@router.post(
    "",
    response_model=OrdenReposicionResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear(
    data: OrdenReposicionCreate,
    user: UsuarioActual = Depends(require_operario)
):
    if not user.id_almacen:
        raise HTTPException(
            status_code=409,
            detail="El operario no tiene almacén asignado"
        )

    data.id_empresa = user.id_empresa
    data.id_almacen = user.id_almacen
    data.id_recomendacion = None

    return await service.crear(
        data,
        user.id_operario
    )


@router.get(
    "",
    response_model=List[OrdenReposicionResponse]
)
async def obtener_todos(
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return _alcance(
        user,
        await service.obtener_por_empresa(
            user.id_empresa
        )
    )


# ============================================================
# ORDENES ENVIADAS AL PROVEEDOR AUTENTICADO
#
# IMPORTANTE: antes de /proveedor/{id_proveedor}
# ============================================================

@router.get(
    "/proveedor/me",
    response_model=List[OrdenReposicionResponse]
)
async def obtener_proveedor_me(
    user: UsuarioActual = Depends(require_proveedor)
):
    return await service.obtener_para_proveedor(
        user.id_proveedor
    )


@router.get(
    "/empresa/{id_empresa}",
    response_model=List[OrdenReposicionResponse]
)
async def obtener_por_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    AccesoService.verificar_empresa(user, id_empresa)
    return _alcance(
        user,
        await service.obtener_por_empresa(id_empresa)
    )


@router.get(
    "/almacen/{id_almacen}",
    response_model=List[OrdenReposicionResponse]
)
async def obtener_por_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_almacen(user, id_almacen)
    return await service.obtener_por_almacen(id_almacen)


@router.get(
    "/proveedor/{id_proveedor}",
    response_model=List[OrdenReposicionResponse]
)
async def obtener_por_proveedor(
    id_proveedor: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return _alcance(
        user,
        await service.obtener_por_proveedor(id_proveedor)
    )


@router.get(
    "/estado/{estado}",
    response_model=List[OrdenReposicionResponse]
)
async def obtener_por_estado(
    estado: EstadoOrdenReposicion,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return _alcance(
        user,
        await service.obtener_por_estado(
            estado.value
        )
    )


# ============================================================
# VALIDAR (EMPRESA) -> ENVIADA
#
# aprobar / enviar: alias antiguos de validar.
# ============================================================

@router.patch(
    "/{id_orden}/validar",
    response_model=OrdenReposicionResponse
)
@router.patch(
    "/{id_orden}/aprobar",
    response_model=OrdenReposicionResponse,
    deprecated=True
)
@router.patch(
    "/{id_orden}/enviar",
    response_model=OrdenReposicionResponse,
    deprecated=True
)
async def validar(
    id_orden: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.validar(id_orden, user)


# ============================================================
# DEVOLVER CON COMENTARIO (EMPRESA) -> OBSERVADA
# ============================================================

@router.patch(
    "/{id_orden}/devolver",
    response_model=OrdenReposicionResponse
)
async def devolver(
    id_orden: str,
    data: DevolverOrdenRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.devolver(
        id_orden,
        data.comentario, user
    )


# ============================================================
# REENVIAR (OPERARIO): OBSERVADA -> PENDIENTE
# ============================================================

@router.patch(
    "/{id_orden}/reenviar",
    response_model=OrdenReposicionResponse
)
async def reenviar(
    id_orden: str,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.reenviar(id_orden, user)


@router.patch(
    "/{id_orden}/cancelar",
    response_model=OrdenReposicionResponse
)
async def cancelar(
    id_orden: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.cancelar(id_orden, user)


# ============================================================
# REGISTRAR DESPACHO (PROVEEDOR)
# ============================================================

@router.post(
    "/{id_orden}/despacho",
    response_model=OrdenReposicionResponse
)
async def registrar_despacho(
    id_orden: str,
    data: DespachoRequest,
    user: UsuarioActual = Depends(require_proveedor)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.registrar_despacho(
        id_orden,
        data, user
    )


# EMPRESA, OPERARIO (su almacén) o PROVEEDOR (enviada a él)
@router.get(
    "/{id_orden}",
    response_model=OrdenReposicionResponse
)
async def obtener_por_id(
    id_orden: str,
    user: UsuarioActual = Depends(get_usuario_activo)
):
    return await AccesoService.verificar_orden(
        user,
        id_orden
    )


@router.put(
    "/{id_orden}",
    response_model=OrdenReposicionResponse
)
async def actualizar(
    id_orden: str,
    data: OrdenReposicionUpdate,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.actualizar(id_orden, data)


@router.delete("/{id_orden}")
async def eliminar(
    id_orden: str,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.eliminar(id_orden, user)
