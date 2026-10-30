import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException
from app.dto.auth_dto import UsuarioActual
from app.dto.saiki_dto import SaikiAskRequest
from app.services.saiki_intent_router import SaikiIntentRouter
from app.services.saiki_service import SaikiService
from app.services import saiki_rack_occupancy as occupancy


@pytest.mark.parametrize('question', ['¿Qué racks están más llenos?', 'Que racks estan mas llenos',
    '¿Cuál es la ocupación de los racks?', 'Lista los racks menos ocupados', '¿Qué rack tiene más carga?'])
def test_occupancy_is_a_live_data_request(question):
    assert SaikiIntentRouter.classify(question).kind == 'rack_occupancy'


def setup(monkeypatch):
    result = {'filtros': {}, 'generado_en': '2026-10-30', 'niveles': [],
              'racks': [{'id_rack': 'r1', 'id_zona': 'z1', 'codigo': 'A', 'capacidad': 100},
                        {'id_rack': 'r2', 'id_zona': 'z1', 'codigo': 'B', 'capacidad': 1000},
                        {'id_rack': 'r3', 'id_zona': 'z1', 'codigo': 'C', 'capacidad': 100}],
              'ubicaciones': [{'id_rack': 'r1', 'id_producto': 'p1', 'stock_actual': 45},
                              {'id_rack': 'r2', 'id_producto': 'p2', 'stock_actual': 100},
                              {'id_rack': 'r3', 'id_producto': 'p3', 'stock_actual': 1}]}
    read = AsyncMock(return_value=result)
    monkeypatch.setattr(occupancy, 'inventario_contextual', read)
    weights = AsyncMock(return_value={'p1': 2, 'p2': 5})
    monkeypatch.setattr(occupancy, 'product_weights', weights)
    return result, read, weights


@pytest.mark.parametrize('role', ['EMPRESA', 'OPERARIO'])
def test_ranking_uses_weight_and_capacity_not_incomparable_units(monkeypatch, role):
    result, read, weights = setup(monkeypatch)
    service = SaikiService()
    model = AsyncMock(side_effect=AssertionError('Rack ranking must work even with Ollama offline'))
    monkeypatch.setattr(service, '_ollama_chat', model)
    user = UsuarioActual(rol=role, id_empresa='company-1',
                         **({'id_operario': 'o1', 'id_almacen': 'w1'} if role == 'OPERARIO' else {}))
    data = SaikiAskRequest(message='¿Qué racks están más llenos?')
    response = asyncio.run(service.ask(data, user))
    assert response['source'] == 'backend'
    rows = response['data']['ocupacion_racks']
    assert [(r['codigo'], r['ocupacion_pct']) for r in rows] == [('A', 90), ('B', 50)]
    assert response['data']['racks_sin_ocupacion_verificada'][0]['id_rack'] == 'r3'
    assert 'no se consideran vacíos' in response['answer']
    read.assert_awaited_once_with(data, user)
    model.assert_not_awaited()


def test_selected_rack_level_capacity_and_partial_stock(monkeypatch):
    result, _, weights = setup(monkeypatch)
    result['filtros'] = {'id_rack': 'r1', 'id_producto': 'p1'}
    result['niveles'] = [{'id_rack': 'r1', 'capacidad_kg': 50}, {'id_rack': 'r1', 'capacidad_kg': 150}]
    user = UsuarioActual(rol='EMPRESA', id_empresa='company-1')
    answer, evidence = asyncio.run(occupancy.rack_occupancy(SaikiAskRequest(message='racks más llenos'), user))
    assert evidence['ocupacion_racks'][0]['ocupacion_pct'] == 45
    assert len(evidence['ocupacion_racks']) == 1
    assert evidence['alcance_filtrado'] is True
    assert 'no representa la ocupación total' in answer
    assert weights.call_args.args[1] == {'p1'}


def test_weight_query_is_scoped_to_company_and_requested_products(monkeypatch):
    calls = []
    class Products:
        def find(self, query, projection):
            calls.append(query)
            return SimpleNamespace(to_list=AsyncMock(return_value=[{'id_producto': 'p1', 'peso': 2}]))
    monkeypatch.setattr(occupancy, 'get_database', lambda: {'productos': Products()})
    user = UsuarioActual(rol='EMPRESA', id_empresa='company-1')
    assert asyncio.run(occupancy.product_weights(user, {'p1'})) == {'p1': 2}
    assert calls == [{'id_empresa': 'company-1', 'id_producto': {'$in': ['p1']}}]


def test_missing_capacity_is_not_reported_as_zero_occupancy(monkeypatch):
    result, _, _ = setup(monkeypatch)
    result['racks'][0]['capacidad'] = 0
    user = UsuarioActual(rol='EMPRESA', id_empresa='company-1')
    _, evidence = asyncio.run(occupancy.rack_occupancy(SaikiAskRequest(message='racks más llenos'), user))
    unknown = {r['id_rack']: r for r in evidence['racks_sin_ocupacion_verificada']}
    assert unknown['r1']['ocupacion_pct'] is None


@pytest.mark.parametrize('user,status', [(None, 401), (UsuarioActual(rol='PROVEEDOR', id_empresa='c1', id_proveedor='p1'), 403)])
def test_rack_occupancy_requires_authorized_inventory_access(user, status):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(occupancy.rack_occupancy(SaikiAskRequest(message='racks llenos'), user))
    assert exc.value.status_code == status


def test_busy_model_is_reported_as_busy_instead_of_disconnected(monkeypatch):
    from app.services import saiki_service as module
    service = SaikiService()
    monkeypatch.setattr(service.settings, 'ollama_base_url', 'https://ai.example.com')
    closed = []
    class Connection:
        sock = None
        def __init__(self, *args, **kwargs): pass
        def request(self, *args, **kwargs): pass
        def getresponse(self): return SimpleNamespace(status=429)
        def close(self): closed.append(True)
    monkeypatch.setattr(module.http.client, 'HTTPSConnection', Connection)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.ask(SaikiAskRequest(message='Explica qué es FIFO')))
    assert exc.value.status_code == 429
    assert 'otra consulta' in exc.value.detail
    assert closed == [True]


def test_busy_streaming_model_keeps_http_429(monkeypatch):
    import httpx
    from app.services.saiki_progress import sink
    service = SaikiService()
    monkeypatch.setattr(service.settings, 'ollama_base_url', 'https://ai.example.com')
    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: real_client(
        transport=httpx.MockTransport(lambda request: httpx.Response(429, json={'detail': 'busy'})), **kwargs))
    async def exercise():
        token = sink.set(lambda event: None)
        try:
            with pytest.raises(HTTPException) as exc:
                await service._ollama_chat([{'role': 'user', 'content': 'Explica FIFO'}], frozenset())
            assert exc.value.status_code == 429
            assert 'otra consulta' in exc.value.detail
        finally:
            sink.reset(token)
    asyncio.run(exercise())


def test_empty_racks_query_does_not_list_nonempty_racks(monkeypatch):
    result, _, _ = setup(monkeypatch)
    result['racks'].append({'id_rack': 'empty', 'id_zona': 'z1', 'codigo': 'D', 'capacidad': 100})
    user = UsuarioActual(rol='EMPRESA', id_empresa='company-1')
    _, evidence = asyncio.run(occupancy.rack_occupancy(SaikiAskRequest(message='¿Qué racks están vacíos?'), user))
    assert [(r['codigo'], r['ocupacion_pct']) for r in evidence['ocupacion_racks']] == [('D', 0)]


@pytest.mark.parametrize('question', ['Explica qué es la capacidad de un rack', '¿Cómo se calcula la ocupación de racks?'])
def test_rack_concepts_remain_explanations_not_live_rankings(question):
    assert SaikiIntentRouter.classify(question).kind == 'conversation'
