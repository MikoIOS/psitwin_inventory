from fastapi import APIRouter, Depends, Query
from app.database.mongodb import get_database
from app.dependencies.dependencies import get_usuario_activo, require_empresa, require_empresa_u_operario, require_proveedor
from app.dto.auth_dto import UsuarioActual
from app.dto.abastecimiento_dto import OfertaRequest, NivelRequest, NivelUpdate, DecisionPendiente
from app.services.oferta_service import OfertaService
from app.services.abastecimiento_service import AbastecimientoService
from app.services.jerarquia_service import JerarquiaService
from app.services.acceso_service import AccesoService

router = APIRouter(prefix='/abastecimiento', tags=['Abastecimiento'])


@router.get('/catalogo')
async def catalogo(user: UsuarioActual = Depends(get_usuario_activo)):
    return await get_database().productos.find({'id_empresa': user.id_empresa}, {'_id': 0}).to_list(length=10000)


@router.get('/clasificacion')
async def clasificacion(user: UsuarioActual = Depends(get_usuario_activo)):
    from app.services.clasificacion_service import CATALOGO
    return CATALOGO


@router.get('/ofertas')
async def ofertas(solo_disponibles: bool = False, id_proveedor: str | None = None, user: UsuarioActual = Depends(get_usuario_activo)):
    return await OfertaService.listar(user, solo_disponibles, id_proveedor)


@router.put('/ofertas')
async def guardar_oferta(data: OfertaRequest, user: UsuarioActual = Depends(require_proveedor)):
    return await OfertaService.guardar(data, user)


@router.get('/racks/{id_rack}/niveles')
async def niveles(id_rack: str, user: UsuarioActual = Depends(require_empresa_u_operario)):
    return await JerarquiaService.niveles(user, id_rack)


@router.post('/racks/{id_rack}/niveles', status_code=201)
async def crear_nivel(id_rack: str, data: NivelRequest, user: UsuarioActual = Depends(require_empresa)):
    return await JerarquiaService.crear_nivel(user, id_rack, data)


@router.delete('/niveles/{id_nivel}')
async def eliminar_nivel(id_nivel: str, user: UsuarioActual = Depends(require_empresa)):
    return await JerarquiaService.eliminar_nivel(user, id_nivel)


@router.patch('/niveles/{id_nivel}')
async def actualizar_nivel(id_nivel: str, data: NivelUpdate, user: UsuarioActual = Depends(require_empresa)):
    return await JerarquiaService.actualizar_nivel(user, id_nivel, data)


@router.get('/seguimiento')
async def seguimiento(user: UsuarioActual = Depends(get_usuario_activo)):
    return await AbastecimientoService.pendientes(user)


@router.patch('/solicitudes/{id_orden}/pendiente')
async def decidir(id_orden: str, data: DecisionPendiente, user: UsuarioActual = Depends(require_empresa)):
    return await AbastecimientoService.resolver(id_orden, data, user)


@router.patch('/solicitudes/{id_orden}/rechazar')
async def rechazar(id_orden: str, data: DecisionPendiente, user: UsuarioActual = Depends(require_empresa)):
    await AccesoService.verificar_orden(user, id_orden)
    from fastapi import HTTPException
    if not data.motivo.strip():
        raise HTTPException(422, 'Debe explicar el rechazo')
    return await AbastecimientoService.transicion(id_orden, {'PENDIENTE', 'OBSERVADA'}, 'CANCELADA', user, data.motivo.strip())


@router.get('/historial-pedidos')
async def historial(id_producto: str | None = None, id_proveedor: str | None = None,
                    desde: str | None = None, hasta: str | None = None, incluir_canceladas: bool = False,
                    user: UsuarioActual = Depends(require_empresa_u_operario)):
    from app.services.pedidos_history_service import historial_pedidos
    return await historial_pedidos(user, id_producto, id_proveedor, desde, hasta, incluir_canceladas)
