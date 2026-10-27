import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.controllers import saiki_controller
from app.services.saiki_intent_router import SaikiIntentRouter
from tests.test_saiki_http import http_app, post


QUESTIONS = [
    ('¿Cómo está mi inventario?', 'general'),
    ('Mencióname todos mis productos y sus cantidades.', 'product_quantities'),
    ('Quiero el detalle de mi inventario, con stock y ubicación por rack.', 'inventory_detail'),
    ('Analiza mi inventario y dime qué productos debo reponer y por qué.', 'analysis'),
]


@pytest.mark.parametrize('question,intent', QUESTIONS + [
    ('Enumera los productos con sus unidades.', 'product_quantities'),
    ('Dame todos mis productos y sus cantidades.', 'product_quantities'),
    ('Quiero ver mis productos con sus cantidades.', 'product_quantities'),
    ('Enumera todos mis productos.', 'product_quantities'),
    ('Dame un desglose de existencias por zona y rack.', 'inventory_detail'),
    ('Muéstrame qué productos tengo y dónde están.', 'inventory_detail'),
    ('Evalúa qué debo comprar y justifica tus recomendaciones.', 'analysis'),
    ('Explícame qué debería reponer.', 'analysis'),
])
def test_semantic_intents(question, intent):
    assert SaikiIntentRouter.classify(question).kind == intent


@pytest.mark.parametrize('question,intent', QUESTIONS)
def test_four_requests_have_complete_results(http_app, monkeypatch, question, intent):
    app, data = http_app
    data['productos'][0]['nombre'] = 'Arroz'
    data['almacenes'][0]['nombre'] = 'Principal'
    data['zonas'][0]['nombre'] = 'A'
    data['racks'][0]['codigo'] = 'A01'
    data['inventarios'][0]['stock_minimo'] = 5
    data['recomendaciones'][0].update(estado='PENDIENTE', cantidad_recomendada=5)
    calls, inferences = [], []
    real_execute = saiki_controller.service.tools.execute
    async def execute(name, args, user=None):
        calls.append(name)
        return await real_execute(name, args, user)
    monkeypatch.setattr(saiki_controller.service.tools, 'execute', execute)
    async def risk(**kwargs):
        assert kwargs['id_inventario'] == 'A-inventory'
        assert kwargs['generar_alertas'] is False
        return SimpleNamespace(model_dump=lambda **kw: {'riesgo': {'nivel': 'CRITICO'}, 'stock_actual': 3,
                                                       'cobertura': {'dias': 1}, 'lead_time_dias': 2})
    monkeypatch.setattr(saiki_controller.service.tools.risk_service, 'evaluar', risk)
    def model(messages, names=None):
        inferences.append(True)
        assert intent == 'analysis', 'Simple request must avoid Ollama'
        verified = json.loads(messages[-1]['content'].split('CONTEXTO PSI TWIN:\n')[1].split('\n\nPREGUNTA:')[0]) if not any(item.get('role') == 'tool' for item in messages) else None
        if verified is not None:
            evidence = verified['datos_verificados_analisis']
            assert evidence['get_warehouse_status']['stock_total_unidades'] == 3
            assert evidence['get_recommendations'][0]['cantidad_recomendada'] == 5
            return {'message': {'tool_calls': [{'function': {'name': 'get_inventory_risk', 'arguments': {'id_inventario': 'A-inventory'}}}]}}
        return {'message': {'content': 'Arroz requiere reposición: tiene 3 unidades y su cobertura de 1 día es menor que los 2 días de reposición. La recomendación registrada propone 5 unidades.'}}
    monkeypatch.setattr(saiki_controller.service, '_call_ollama_chat', model)
    response = asyncio.run(post(app, question))
    assert response.status_code == 200, response.text
    payload = response.json()
    assert all(key in payload for key in ('answer', 'data', 'visualization', 'sources', 'warnings', 'context'))
    assert 'B-product' not in json.dumps(payload)
    if intent == 'general':
        assert payload['data']['inventory_summary']['total_units'] == 3
    elif intent == 'product_quantities':
        assert payload['data']['product_quantities'][0]['stock'] == 3
        assert 'Arroz: 3 unidades' in payload['answer']
    elif intent == 'inventory_detail':
        assert all(text in payload['answer'] for text in ('Arroz', '3 unidades', 'Principal', 'A01'))
        assert payload['data']['inventory_summary']['rows'][0]['rack_name'] == 'A01'
    else:
        assert calls == ['get_warehouse_status', 'get_recommendations', 'get_inventory_risk']
        assert len(inferences) == 2
        assert 'get_inventory_risk' in payload['data']
    assert bool(inferences) == (intent == 'analysis')
    output = Path('venv/saiki-tests-py312/semantics-results.json')
    records = json.loads(output.read_text(encoding='utf-8')) if output.exists() and intent != 'general' else []
    records.append({'question': question, 'intent': intent, 'tools': calls, 'answer': payload['answer'],
                    'ollama_mock_calls': len(inferences), 'complete_in_simulation': True})


def test_list_preserves_products_without_inventory_and_all_rows(http_app, monkeypatch):
    app, data = http_app
    for i in range(8):
        data['productos'].append({'id_producto': f'A-extra-{i}', 'id_empresa': 'A', 'nombre': f'Producto {i}'})
    monkeypatch.setattr(saiki_controller.service, '_call_ollama_chat', lambda *args: pytest.fail('No Ollama'))
    payload = asyncio.run(post(app, QUESTIONS[1][0])).json()
    assert len(payload['data']['product_quantities']) == 9
    assert 'Producto 7: sin inventario registrado' in payload['answer']
    assert payload['data']['product_quantities'][-1]['stock'] is None
