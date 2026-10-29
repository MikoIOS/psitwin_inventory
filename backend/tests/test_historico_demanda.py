import asyncio
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from app.controllers import analisis_controller
from app.dependencies.dependencies import get_usuario_activo
from app.dto.auth_dto import UsuarioActual
from app.repositories import demanda_historica_repository as repository


def test_report_groups_only_observed_dates_and_scopes_every_query(monkeypatch):
    queries = []
    daily = [{'_id': '2025-01-01', 'cantidad': 4}, {'_id': '2025-01-03', 'cantidad': 8},
             {'_id': '2025-02-01', 'cantidad': 6}]
    class Cursor:
        def sort(self, *args): return self
        def skip(self, *args): return self
        def limit(self, *args): return self
        async def to_list(self, length): return []
    class Collection:
        def aggregate(self, pipeline):
            queries.append(pipeline[0]['$match'])
            data = daily if pipeline[1]['$group']['_id'] == '$fecha' else []
            return SimpleNamespace(to_list=AsyncMock(return_value=data))
        async def count_documents(self, query): queries.append(query); return 3
        def find(self, query, projection): queries.append(query); return Cursor()
    monkeypatch.setattr(repository, 'get_database', lambda: {'demanda_historica': Collection()})
    async def run():
        repo = repository.DemandaHistoricaRepository()
        for frequency in ('diaria', 'semanal', 'mensual'):
            report = await repo.report('e', 'w', 'p', date(2025, 1, 1), date(2025, 2, 1), frequency)
            assert report['total'] == sum(p['cantidad'] for p in report['serie']) == 18
            assert report['promedio_diario'] == 6 and report['dias_observados'] == 3
            if frequency == 'mensual': assert report['serie'] == [{'fecha': '2025-01-01', 'cantidad': 12}, {'fecha': '2025-02-01', 'cantidad': 6}]
            if frequency == 'diaria': assert len(report['serie']) == 3  # No invented Jan 2 observation.
        assert all(q['id_empresa'] == 'e' and q['id_almacen'] == 'w' and q['id_producto'] == 'p' for q in queries)
    asyncio.run(run())


def test_historical_http_auth_ranges_pagination_and_tenant(monkeypatch):
    report = AsyncMock(return_value={'total': 0})
    monkeypatch.setattr(analisis_controller.DemandaHistoricaRepository, 'report', report)
    app = FastAPI()
    app.include_router(analisis_controller.router)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            assert (await client.get('/analisis/historico')).status_code in (401, 403)
            app.dependency_overrides[get_usuario_activo] = lambda: UsuarioActual(rol='EMPRESA', id_empresa='e')
            assert (await client.get('/analisis/historico?id_empresa=other')).status_code == 403
            assert (await client.get('/analisis/historico?fecha_inicio=2025-02-01&fecha_fin=2025-01-01')).status_code == 422
            assert (await client.get('/analisis/historico?frecuencia=anual')).status_code == 422
            assert (await client.get('/analisis/historico?offset=-1')).status_code == 422
            assert (await client.get('/analisis/historico?limite=1001')).status_code == 422
            report.assert_not_awaited()
            assert (await client.get('/analisis/historico?id_almacen=w&limite=25&offset=25')).status_code == 200
            assert report.call_args.args == ('e', 'w', None, None, None, 'diaria', 25, 25)
            app.dependency_overrides[get_usuario_activo] = lambda: UsuarioActual(rol='OPERARIO', id_empresa='e')
            assert (await client.get('/analisis/historico')).status_code == 403
    asyncio.run(run())


def test_saiki_historical_and_future_intents_are_separate():
    from app.services.saiki_intent_router import SaikiIntentRouter
    for question in ('demanda histórica', 'productos con mayor demanda', 'tendencias observadas de demanda'):
        assert SaikiIntentRouter.classify(question).kind == 'historical_demand'
    for question in ('demanda proyectada a 30 días', 'demanda futura', 'demanda en 7 días'):
        assert SaikiIntentRouter.classify(question).kind != 'historical_demand'


def test_saiki_top_demand_is_not_misread_as_the_month_of_may(monkeypatch):
    from app.services import saiki_demand
    report = {'documentos': 1, 'fecha_inicio': '2025-01-01', 'fecha_fin': '2025-01-01',
              'total': 7, 'promedio_diario': 7, 'dias_observados': 1,
              'ranking': [], 'ranking_productos': [{'id_producto': 'p', 'cantidad': 7}],
              'tendencia': {'promedio_primera_mitad': None, 'promedio_segunda_mitad': None}}
    filters = AsyncMock(return_value={'productos': [{'id': 'p', 'nombre': 'Producto CSV 123'}], 'almacenes': []})
    monkeypatch.setattr(saiki_demand.service, 'filters', filters)
    lookup = AsyncMock(return_value=report)
    monkeypatch.setattr(repository.DemandaHistoricaRepository, 'report', lookup)
    async def run():
        answer, _ = await saiki_demand.historical_answer(SimpleNamespace(id_empresa='e'), message='Que productos tienen mayor demanda historica?')
        assert 'Productos con mayor demanda' in answer and '7.00' in answer
        assert lookup.await_count == 1
        answer, _ = await saiki_demand.historical_answer(SimpleNamespace(id_empresa='e'), message='demanda en mayo')
        assert 'AAAA-MM-DD' in answer and lookup.await_count == 1
    asyncio.run(run())
