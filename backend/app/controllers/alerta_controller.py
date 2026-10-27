from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies.dependencies import (
    require_empresa
)

from app.dto.auth_dto import (
    UsuarioActual
)

from app.dto.alerta_dto import (
    AlertaCreate,
    AlertaResponse,
    EstadoAlerta,
    TipoAlerta,
    AlertaEstadoUpdate
)

from app.services.acceso_service import (
    AccesoService
)

from app.services.alerta_service import (
    AlertaService
)


# ============================================================
# ALERTAS: solo EMPRESA, filtradas a su empresa.
# ============================================================

router = APIRouter(
    prefix="/alertas",
    tags=["Alertas"]
)

service = AlertaService()


async def _verificar(
    user: UsuarioActual,
    id_item: str
):
    item = await service.obtener(id_item)

    if item.get("id_empresa") != user.id_empresa:
        raise HTTPException(
            status_code=404,
            detail="Alerta no encontrada"
        )

    return item


@router.post(
    "",
    response_model=AlertaResponse,
    status_code=201
)
async def crear_alerta(
    data: AlertaCreate,
    user: UsuarioActual = Depends(require_empresa)
):
    data.id_empresa = user.id_empresa
    await AccesoService.verificar_almacen(user, data.id_almacen)
    return await service.crear(data)


@router.get(
    "",
    response_model=List[AlertaResponse]
)
async def listar(
    tipo_alerta: Optional[TipoAlerta] = Query(default=None),
    estado: Optional[EstadoAlerta] = Query(default=None),
    origen: Optional[str] = Query(
        default=None,
        description="INVENTARIO | SENSOR"
    ),
    id_dispositivo: Optional[str] = Query(default=None),
    user: UsuarioActual = Depends(require_empresa)
):
    alertas = await service.listar_por_empresa(
        user.id_empresa
    )

    # Filtros opcionales (incluye los tipos de sensores)
    return [
        alerta
        for alerta in alertas
        if (tipo_alerta is None or alerta.get("tipo_alerta") == tipo_alerta.value)
        and (estado is None or alerta.get("estado") == estado.value)
        and (origen is None or alerta.get("origen", "INVENTARIO") == origen)
        and (id_dispositivo is None or alerta.get("id_dispositivo") == id_dispositivo)
    ]


@router.get(
    "/activas",
    response_model=List[AlertaResponse]
)
async def listar_activas(
    user: UsuarioActual = Depends(require_empresa)
):
    return AccesoService.filtrar_empresa(
        user,
        await service.listar_activas()
    )

@router.get(
    "/empresa/{id_empresa}",
    response_model=List[AlertaResponse]
)
async def listar_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa)
):
    AccesoService.verificar_empresa(user, id_empresa)
    return await service.listar_por_empresa(id_empresa)


@router.get(
    "/almacen/{id_almacen}",
    response_model=List[AlertaResponse]
)
async def listar_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_almacen(user, id_almacen)
    return await service.listar_por_almacen(id_almacen)


@router.get(
    "/producto/{id_producto}",
    response_model=List[AlertaResponse]
)
async def listar_producto(
    id_producto: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_producto(user, id_producto)
    return AccesoService.filtrar_empresa(
        user,
        await service.listar_por_producto(id_producto)
    )


@router.get(
    "/inventario/{id_inventario}",
    response_model=List[AlertaResponse]
)
async def listar_inventario(
    id_inventario: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_inventario(user, id_inventario)
    return AccesoService.filtrar_empresa(
        user,
        await service.listar_por_inventario(id_inventario)
    )


@router.get(
    "/nivel/{nivel_riesgo}",
    response_model=List[AlertaResponse]
)
async def listar_nivel(
    nivel_riesgo: str,
    user: UsuarioActual = Depends(require_empresa)
):
    return AccesoService.filtrar_empresa(
        user,
        await service.listar_por_nivel(nivel_riesgo)
    )

@router.get(
    "/{id_item}",
    response_model=AlertaResponse
)
async def obtener(
    id_item: str,
    user: UsuarioActual = Depends(require_empresa)
):
    return await _verificar(user, id_item)


@router.patch(
    "/{id_item}/estado",
    response_model=AlertaResponse
)
async def cambiar_estado(
    id_item: str,
    data: AlertaEstadoUpdate,
    user: UsuarioActual = Depends(require_empresa)
):
    await _verificar(user, id_item)
    return await service.cambiar_estado(id_item, data)
