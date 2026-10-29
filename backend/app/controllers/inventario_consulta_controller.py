import asyncio
from typing import Literal
from fastapi import APIRouter, Depends, Response, HTTPException
from app.dependencies.dependencies import require_empresa, require_empresa_u_operario
from app.dto.auth_dto import UsuarioActual
from app.dto.inventario_consulta_dto import InventarioFiltros, ReporteSolicitud, ReporteConfirmacion
from app.services.inventario_consulta_service import consultar_inventario
from app.services.inventario_reportes_service import InventarioReportesService, preparar_datos, destinatario, publico
from app.services.inventario_reportes_archivos import generar_archivo
from app.services.jerarquia_service import JerarquiaService
from app.services.acceso_service import AccesoService

router = APIRouter(tags=['Plano y reportes de inventario'])
reportes = InventarioReportesService()

@router.get('/inventario-consultas/resumen')
async def resumen(filtros: InventarioFiltros = Depends(), pagina: int = 1, limite: int = 25, user: UsuarioActual = Depends(require_empresa_u_operario)):
    if pagina < 1 or limite < 1 or limite > 100: raise HTTPException(422, 'Paginación no válida')
    data = await consultar_inventario(user, filtros)
    offset = (pagina - 1) * limite
    return {k:data[k] for k in ('generado_en','filtros','resumen','alertas')} | {'productos':data['productos'][offset:offset+limite], 'total':len(data['productos']), 'pagina':pagina,'limite':limite,'ubicaciones':data['ubicaciones']}

@router.get('/almacenes/{id_almacen}/plano')
async def plano(id_almacen: str, user: UsuarioActual = Depends(require_empresa_u_operario)):
    data = await consultar_inventario(user, InventarioFiltros(id_almacen=id_almacen))
    return {'almacen':data['almacenes'][0], 'zonas':data['zonas'], 'racks':data['racks'], 'niveles':data['niveles'],
            'inventario':data['ubicaciones'],'alertas':data['alertas'],'resumen':data['resumen'],'generado_en':data['generado_en'],'esquema_sin_escala':True}

@router.get('/niveles/{id_nivel}/inventario')
async def nivel(id_nivel: str, user: UsuarioActual = Depends(require_empresa_u_operario)):
    data = await consultar_inventario(user, InventarioFiltros(id_nivel=id_nivel))
    return {'ubicaciones':data['ubicaciones'],'productos':data['productos'],'alertas':data['alertas'],'resumen':data['resumen']}

@router.post('/racks/{id_rack}/habilitar-niveles')
async def habilitar(id_rack: str, user: UsuarioActual = Depends(require_empresa)):
    rack = await AccesoService.verificar_rack(user, id_rack)
    return await JerarquiaService.asegurar_niveles(rack)

@router.get('/inventario-reportes/exportar')
async def exportar(formato: Literal['xlsx','pdf'], filtros: InventarioFiltros = Depends(), user: UsuarioActual = Depends(require_empresa_u_operario)):
    data = await preparar_datos(user, filtros)
    try: blob, mime, filename = await asyncio.to_thread(generar_archivo, data, formato)
    except ValueError as error: raise HTTPException(413, str(error)) from error
    return Response(blob, media_type=mime, headers={'Content-Disposition':f'attachment; filename="{filename}"','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

@router.get('/inventario-reportes/destinatario')
async def correo(user: UsuarioActual = Depends(require_empresa)):
    return {'correo':await destinatario(user)}

@router.post('/inventario-reportes/solicitudes', status_code=201)
async def solicitar(data: ReporteSolicitud, user: UsuarioActual = Depends(require_empresa)):
    return await reportes.solicitar(user, data)

@router.get('/inventario-reportes/envios/{identifier}')
async def estado(identifier: str, user: UsuarioActual = Depends(require_empresa)):
    return publico(await reportes.obtener(user, identifier))

@router.post('/inventario-reportes/envios/{identifier}/confirmar')
async def confirmar(identifier: str, data: ReporteConfirmacion, user: UsuarioActual = Depends(require_empresa)):
    return await reportes.confirmar(user, identifier)

@router.post('/inventario-reportes/envios/{identifier}/cancelar')
async def cancelar(identifier: str, user: UsuarioActual = Depends(require_empresa)):
    return await reportes.cancelar(user, identifier)
