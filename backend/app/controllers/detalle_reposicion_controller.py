from typing import List

from fastapi import APIRouter, Depends, status

from app.dependencies.dependencies import (
    get_usuario_activo,
    require_operario
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.detalle_reposicion_dto import (
    DetalleReposicionCreate,
    DetalleReposicionUpdate,
    DetalleReposicionResponse
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.detalle_reposicion_service import (
    DetalleReposicionService
)


# Líneas de la solicitud: las gestiona el OPERARIO
# (orden PENDIENTE u OBSERVADA de su almacén).
# Lectura: EMPRESA, OPERARIO y PROVEEDOR con acceso a la orden.

router = APIRouter(
    tags=["Detalles de Reposicion"]
)

service = DetalleReposicionService()


async def _verificar_detalle(
    user: UsuarioActual,
    id_detalle: str
):
    detalle = await service.obtener_por_id(id_detalle)

    await AccesoService.verificar_orden(
        user,
        detalle["id_orden_reposicion"]
    )

    return detalle


@router.post(
    "/ordenes-reposicion/{id_orden}/detalles",
    response_model=DetalleReposicionResponse,
    status_code=status.HTTP_201_CREATED
)
async def crear(
    id_orden: str,
    data: DetalleReposicionCreate,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    await AccesoService.verificar_producto(user, data.id_producto)
    return await service.crear(id_orden, data, user)


# EMPRESA, OPERARIO (su almacén) o PROVEEDOR (enviada a él)
@router.get(
    "/ordenes-reposicion/{id_orden}/detalles",
    response_model=List[DetalleReposicionResponse]
)
async def obtener_por_orden(
    id_orden: str,
    user: UsuarioActual = Depends(get_usuario_activo)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.obtener_por_orden(id_orden)


@router.get(
    "/detalles-reposicion/{id_detalle}",
    response_model=DetalleReposicionResponse
)
async def obtener_por_id(
    id_detalle: str,
    user: UsuarioActual = Depends(get_usuario_activo)
):
    return await _verificar_detalle(user, id_detalle)


@router.put(
    "/detalles-reposicion/{id_detalle}",
    response_model=DetalleReposicionResponse
)
async def actualizar(
    id_detalle: str,
    data: DetalleReposicionUpdate,
    user: UsuarioActual = Depends(require_operario)
):
    await _verificar_detalle(user, id_detalle)
    return await service.actualizar(
        id_detalle,
        data, user
    )


@router.delete(
    "/detalles-reposicion/{id_detalle}"
)
async def eliminar(
    id_detalle: str,
    user: UsuarioActual = Depends(require_operario)
):
    await _verificar_detalle(user, id_detalle)
    return await service.eliminar(id_detalle, user)
