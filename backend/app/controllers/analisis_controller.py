from fastapi import APIRouter, Depends, Query
from datetime import date
from typing import Literal
from fastapi import HTTPException
from app.repositories.demanda_historica_repository import DemandaHistoricaRepository
from app.dependencies.dependencies import require_empresa_u_operario as require_empresa
from app.dto.auth_dto import UsuarioActual
from app.dto.analisis_dto import DemandAnalysis
from app.services.analisis_service import service

router = APIRouter(prefix='/analisis', tags=['Análisis de demanda'])


@router.get('/historico')
async def historical(fecha_inicio: date | None = None, fecha_fin: date | None = None,
                     frecuencia: Literal['diaria', 'semanal', 'mensual'] = 'diaria',
                     id_almacen: str | None = None, id_producto: str | None = None,
                     id_empresa: str | None = None, offset: int = Query(0, ge=0),
                     limite: int = Query(100, ge=1, le=1000), user: UsuarioActual = Depends(require_empresa)):
    if id_empresa and id_empresa != user.id_empresa: raise HTTPException(403, 'Empresa no autorizada')
    if user.es_operario:
        if not user.id_almacen:
            raise HTTPException(403, 'El operario no tiene un almacén asignado')
        if id_almacen and id_almacen != user.id_almacen:
            raise HTTPException(403, 'El operario solo puede consultar su almacén')
        id_almacen = user.id_almacen
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin: raise HTTPException(422, 'Rango de fechas inválido')
    return await DemandaHistoricaRepository().report(user.id_empresa, id_almacen, id_producto,
                fecha_inicio, fecha_fin, frecuencia, offset, limite)


@router.get('/modelo')
async def model_info(user: UsuarioActual = Depends(require_empresa)):
    return service.metadata()


@router.get('/filtros')
async def filters(user: UsuarioActual = Depends(require_empresa)):
    return await service.filters(user)


@router.get('/pronostico', response_model=DemandAnalysis)
async def forecast(id_almacen: str, id_producto: str, id_empresa: str | None = None,
                   fuente: Literal['salidas', 'solicitudes'] = 'salidas',
                   user: UsuarioActual = Depends(require_empresa)):
    await service.authorize(user, id_almacen, id_producto, id_empresa)
    return await service.series(user, id_almacen, id_producto, source=fuente)


@router.get('/resumen')
async def summary(horizonte_dias: int = Query(30, ge=1, le=90), id_almacen: str | None = None,
                  id_producto: str | None = None, id_empresa: str | None = None,
                  fuente: Literal['salidas', 'solicitudes'] = 'salidas',
                  limite: int = Query(50, ge=1, le=200), user: UsuarioActual = Depends(require_empresa)):
    await service.authorize(user, id_almacen, id_producto, id_empresa)
    return await service.summary(user, horizonte_dias, id_almacen, id_producto, limite, source=fuente)
