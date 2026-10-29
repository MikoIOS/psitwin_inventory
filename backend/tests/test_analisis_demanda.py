import asyncio
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
import httpx
import pytest
from fastapi import FastAPI, HTTPException

from app.ml.autogluon_calendar import calendar_values, series_id
from app.services.analisis_service import AnalisisService
from app.services.acceso_service import AccesoService
from app.dto.auth_dto import UsuarioActual
from app.dependencies.dependencies import get_usuario_activo


class Repository:
    def __init__(self):
        self.cut = datetime.now(timezone.utc).date() - timedelta(days=1)
        self.rows = [{'fecha': str(self.cut - timedelta(days=99-i)), 'demanda': 2} for i in range(100)]
        self.stock_value = 10
    async def history(self, *args): return self.rows
    async def stock(self, *args): return self.stock_value
    async def catalog(self, tenant):
        return [{'id': 'a', 'nombre': 'Almacén', 'id_empresa': tenant}], [{'id_producto': 'p', 'nombre': 'Producto', 'id_empresa': tenant}]
    async def pairs(self, *args): return [('a', 'p')]


class Model:
    def __init__(self, valid=True): self.calls = 0; self.valid = valid
    def status(self): return {'validado': self.valid, 'faltantes': [] if self.valid else ['pesos de prueba ausentes'], 'model_fingerprint': 'fixture'}
    def predict(self, tenant, identifier, history):
        self.calls += 1
        cutoff = date.fromisoformat(history[-1]['fecha'])
        return {'predictions': {identifier: [{'fecha': str(cutoff + timedelta(days=i)), 'cantidad': 3, 'q10': 1, 'q50': 3, 'q90': 5} for i in range(1, 91)]}}, False


@pytest.fixture
def setup(monkeypatch):
    async def warehouse(user, identifier):
        if identifier != 'a': raise HTTPException(404, 'Almacén no encontrado')
        return {'id': 'a', 'id_empresa': user.id_empresa}
    async def product(user, identifier):
        if identifier != 'p': raise HTTPException(404, 'Producto no encontrado')
        return {'id_producto': 'p', 'id_empresa': user.id_empresa}
    monkeypatch.setattr(AccesoService, 'verificar_almacen', warehouse)
    monkeypatch.setattr(AccesoService, 'verificar_producto', product)
    return Repository(), Model(), UsuarioActual(rol='EMPRESA', id_empresa='e')


def test_exact_calendar_and_series_contract():
    assert series_id('warehouse', 'product') == 'warehouse_product'
    assert calendar_values(date(2026, 11, 30))['is_campana_navidena'] == 0
    assert calendar_values(date(2026, 12, 1))['is_campana_navidena'] == 1
    assert calendar_values(date(2027, 1, 1))['is_campana_navidena'] == 0
    assert calendar_values(date(2028, 2, 29))['dayofyear'] == 60
    assert calendar_values(date(2027, 1, 1))['weekofyear'] == 53


def test_full_history_90_predictions_cumulative_and_stock_not_target(setup):
    repo, model, user = setup
    async def run():
        service = AnalisisService(repo, model)
        result = await service.series(user, 'a', 'p', wait=True)
        assert len(result.historico) == 100 and len(result.predicciones) == 90
        assert [p.demanda_acumulada for p in result.horizontes] == [3, 21, 90, 270]
        assert result.stock_actual == 10
        assert result.predicciones[0].fecha == repo.cut + timedelta(days=1)
        assert result.historico[0].cantidad == 2
        again = await service.series(user, 'a', 'p', wait=True)
        assert again.cache and model.calls == 1
        repo.stock_value = 100
        again = await service.series(user, 'a', 'p', wait=True)
        assert again.stock_actual == 100 and model.calls == 1
        repo.rows[-1]['demanda'] = 4
        await service.series(user, 'a', 'p', wait=True)
        assert model.calls == 2
    asyncio.run(run())


def test_no_fabricated_predictions_if_weights_or_history_missing(setup):
    repo, _, user = setup
    async def run():
        model = Model(valid=False)
        service = AnalisisService(repo, model)
        result = await service.series(user, 'a', 'p', wait=True)
        assert result.estado == 'MODELO_NO_DISPONIBLE' and not result.predicciones
        repo.rows = []
        result = await service.series(user, 'a', 'p', wait=True)
        assert result.estado == 'SIN_HISTORIAL' and not result.horizontes
        assert model.calls == 0
    asyncio.run(run())


def test_inflight_job_reused_and_ranking_gaps_are_not_purchases(setup):
    repo, model, user = setup
    async def run():
        service = AnalisisService(repo, model)
        first = await service.series(user, 'a', 'p')
        second = await service.series(user, 'a', 'p')
        assert first.estado == second.estado == 'CALCULANDO'
        assert len(service.tasks) == 1
        await asyncio.gather(*list(service.tasks.values()))
        summary = await service.summary(user, 30)
        assert summary['filas'][0]['brecha_stock'] == 80
        assert model.calls == 1
    asyncio.run(run())


def test_tenant_check_happens_before_history_access(setup):
    repo, model, user = setup
    repo.history = AsyncMock()
    async def run():
        service = AnalisisService(repo, model)
        with pytest.raises(HTTPException) as error: await service.authorize(user, tenant='foreign')
        assert error.value.status_code == 403
        with pytest.raises(HTTPException): await service.series(user, 'foreign', 'p')
        repo.history.assert_not_awaited()
    asyncio.run(run())


def test_http_permissions_filters_and_invalid_horizons(setup, monkeypatch):
    from app.controllers import analisis_controller
    repo, model, user = setup
    monkeypatch.setattr(analisis_controller, 'service', AnalisisService(repo, model))
    app = FastAPI(); app.include_router(analisis_controller.router, prefix='/api/v1')
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            assert (await client.get('/api/v1/analisis/modelo')).status_code in (401, 403)
            app.dependency_overrides[get_usuario_activo] = lambda: UsuarioActual(rol='OPERARIO', id_empresa='e')
            assert (await client.get('/api/v1/analisis/modelo')).status_code == 200
            assert (await client.get('/api/v1/analisis/pronostico?id_almacen=foreign&id_producto=p')).status_code == 403
            app.dependency_overrides[get_usuario_activo] = lambda: user
            filters = await client.get('/api/v1/analisis/filtros')
            assert filters.json()['id_empresa'] == 'e'
            assert (await client.get('/api/v1/analisis/resumen?horizonte_dias=2')).status_code == 422
            assert (await client.get('/api/v1/analisis/resumen?id_empresa=foreign')).status_code == 403
            assert (await client.get('/api/v1/analisis/pronostico?id_almacen=foreign&id_producto=p')).status_code == 404
            metadata = (await client.get('/api/v1/analisis/modelo')).json()
            assert metadata['evaluation_only'] is True
            assert round(metadata['wape_accumulated_pct']['90'], 2) == 14.98
    asyncio.run(run())


def test_imported_history_uses_dataset_cutoff_without_stock_or_synthetic_tail(setup):
    repo, model, user = setup
    imported = [{'fecha': row['fecha'], 'cantidad': row['demanda']} for row in repo.rows[:-9]]
    repo.dataset_history = AsyncMock(return_value=imported)
    repo.history = AsyncMock(side_effect=AssertionError('No mezclar movimientos con CSV'))
    repo.stock = AsyncMock(side_effect=AssertionError('No inferir stock de dimensiones históricas'))
    async def run():
        result = await AnalisisService(repo, model).series(user, 'a', 'p', wait=True)
        assert result.estado == 'DISPONIBLE'
        assert len(result.historico) == 91
        assert result.fecha_corte == date.fromisoformat(imported[-1]['fecha'])
        assert result.predicciones[0].fecha == result.fecha_corte + timedelta(days=1)
        assert result.stock_actual is None
        repo.dataset_history.assert_awaited_once_with(user.id_empresa, 'a', 'p', repo.cut)
    asyncio.run(run())


def test_imported_gaps_never_become_fabricated_zeros(setup):
    repo, model, user = setup
    imported = [{'fecha': row['fecha'], 'cantidad': row['demanda']} for row in repo.rows]
    imported.pop(20)
    repo.dataset_history = AsyncMock(return_value=imported)
    async def run():
        result = await AnalisisService(repo, model).series(user, 'a', 'p', wait=True)
        assert result.estado == 'HISTORIAL_INSUFICIENTE'
        assert len(result.historico) == 99 and not result.predicciones
        assert all(p.cantidad == 2 for p in result.historico) and model.calls == 0
    asyncio.run(run())


def test_wrong_forecast_dates_are_rejected(setup):
    repo, model, user = setup
    original = model.predict
    def invalid(*args):
        output, cache = original(*args)
        output['predictions'][series_id('a', 'p')][0]['fecha'] = '2000-01-01'
        return output, cache
    model.predict = invalid
    async def run():
        result = await AnalisisService(repo, model).series(user, 'a', 'p', wait=True)
        assert result.estado == 'ERROR_MODELO' and not result.predicciones
    asyncio.run(run())


def test_imported_history_can_compare_with_owned_operational_stock(setup):
    repo, model, user = setup
    repo.dataset_history = AsyncMock(return_value=[{'fecha': r['fecha'], 'cantidad': r['demanda']} for r in repo.rows])
    repo.stock_for_tenant = AsyncMock(return_value=45)
    async def run():
        result = await AnalisisService(repo, model).series(user, 'a', 'p', wait=True)
        assert result.stock_actual == 45 and result.historico[0].cantidad == 2
        repo.stock_for_tenant.assert_awaited_once_with(user.id_empresa, 'a', 'p')
        repo.stock_for_tenant.return_value = 40
        result = await AnalisisService(repo, model).series(user, 'a', 'p', wait=True)
        assert result.stock_actual == 40
    asyncio.run(run())
