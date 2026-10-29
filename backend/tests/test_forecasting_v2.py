"""Forecast API compatibility, real repository scoping, no alternative engine."""
import asyncio
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException
from app.services.forecast_service import ForecastService
from app.repositories.serie_demanda_repository import SerieDemandaRepository
from app.services.saiki_responses import forecast_answer
from app.services.saiki_tools import ForecastArgs
from app.repositories.almacen_repository import AlmacenRepository
from app.dto.analisis_dto import DemandAnalysis
from test_inventario_v2 import db, run, Collection, Cursor


@pytest.fixture
def analysis(monkeypatch):
    monkeypatch.setattr(AlmacenRepository, 'obtener_por_id', AsyncMock(return_value={'id': 'a', 'id_empresa': 'tenant'}))
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=1)
    result = DemandAnalysis(estado='DISPONIBLE', id_empresa='tenant', id_almacen='a', id_producto='p',
        series_id='a_p', fecha_corte=cutoff,
        historico=[{'fecha': cutoff-timedelta(days=i), 'cantidad': 2} for i in range(100)],
        predicciones=[{'fecha': cutoff+timedelta(days=i), 'cantidad': 3, 'q10': 1, 'q50': 3, 'q90': 5} for i in range(1, 91)])
    return SimpleNamespace(series=AsyncMock(return_value=result)), result


@pytest.mark.parametrize('horizon', [1, 7, 30, 90])
def test_forecast_uses_shared_analysis_and_exact_horizon(analysis, horizon):
    shared, base = analysis
    result = run(ForecastService(shared).predecir('a', 'p', horizon))
    assert result.estado == 'DISPONIBLE'
    assert len(result.predicciones_diarias) == horizon
    assert result.demanda_total_estimada == 3*horizon
    assert result.predicciones_diarias[0].fecha == base.fecha_corte+timedelta(days=1)
    assert result.fecha_fin == base.fecha_corte+timedelta(days=horizon)
    call = shared.series.call_args
    assert call.args[0].id_empresa == 'tenant'
    assert call.kwargs == {'wait': True, 'cutoff': base.fecha_corte}


@pytest.mark.parametrize('state', ['SIN_HISTORIAL', 'HISTORIAL_INSUFICIENTE', 'MODELO_NO_DISPONIBLE', 'ERROR_MODELO'])
def test_unavailable_predictions_never_use_fallback(analysis, state):
    shared, base = analysis
    base.estado = state
    result = run(ForecastService(shared).predecir('a', 'p', 90))
    assert not result.predicciones_diarias
    assert result.demanda_total_estimada is None
    assert result.estado == ('HISTORIAL_INSUFICIENTE' if state in {'SIN_HISTORIAL', 'HISTORIAL_INSUFICIENTE'} else 'MODELO_NO_DISPONIBLE')


def test_completed_cutoff_and_unsupported_horizon(analysis):
    shared, _ = analysis
    service = ForecastService(shared)
    for cutoff, horizon in [(datetime.now(timezone.utc).date(), 7), (None, 14)]:
        with pytest.raises(HTTPException):
            run(service.predecir('a', 'p', horizon, cutoff))
    shared.series.assert_not_called()


def test_real_repository_query_aggregates_racks_and_isolates_warehouse(db,monkeypatch):
    def aggregate(collection,pipeline):
        query=pipeline[0]["$match"]
        assert query["id_almacen"]=="a"
        assert query["id_producto"]=={"$in":["p"]}
        assert query["tipo_movimiento"]=="SALIDA" and "motivo_movimiento" not in query
        from test_inventario_v2 import matches
        rows=[r for r in collection.rows if matches(r,query)]
        totals={}
        for row in rows:
            key=row["fecha_hora"].date().isoformat()
            totals[key]=totals.get(key,0)+row["cantidad"]
        return Cursor([{"fecha":k,"demanda":v} for k,v in sorted(totals.items())])
    monkeypatch.setattr(Collection,"aggregate",aggregate,raising=False)
    def movement(warehouse,product,rack,quantity,kind="SALIDA",day=12):
        return {"id_almacen":warehouse,"id_producto":product,"id_rack":rack,"tipo_movimiento":kind,
                "fecha_hora":datetime(2026,10,day,tzinfo=timezone.utc),"cantidad":quantity,"motivo_movimiento":"VENCIMIENTO"}
    db["movimientos"].rows=[
        movement("a","p","r1",3),movement("a","p","r2",5),
        movement("b","p","rb",50),movement("a","q","r1",20),
        movement("a","p","r1",100,"ENTRADA"),movement("a","p","r1",90,day=13)]
    rows=run(SerieDemandaRepository().diarios("a",date(2026,10,1),date(2026,10,12),["p"]))
    assert rows==[{"fecha":"2026-10-12","demanda":8}]


def test_llm_contract_requires_product_and_supports_explicit_long_status():
    from pydantic import ValidationError
    with pytest.raises(ValidationError): ForecastArgs(id_inventario="header")
    assert ForecastArgs(id_inventario="header",id_producto="p",horizonte_dias=90).horizonte_dias==90
