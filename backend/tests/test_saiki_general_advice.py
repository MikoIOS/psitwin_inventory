"""Regression: warehouse advice and its example must reach Qwen, not stock summaries."""
import asyncio
from unittest.mock import AsyncMock

import pytest

from app.dto.auth_dto import UsuarioActual
from app.dto.saiki_dto import SaikiAskRequest
from app.services.saiki_intent_router import SaikiIntentRouter
from app.services.saiki_service import SaikiService

QUESTION = 'Explica brevemente cómo organizar un almacén de alimentos'


@pytest.mark.parametrize('question', [QUESTION, '¿Cómo organizar un almacén?',
    'Dame consejos para conservar alimentos', 'Buenas prácticas para ordenar un almacén'])
def test_general_advice_routes_to_model_without_company_tools(question):
    intent = SaikiIntentRouter.classify(question)
    assert intent.kind == 'conversation'
    assert not intent.tool_names


@pytest.mark.parametrize('question', ['¿Cómo está mi inventario?',
    '¿Cuántos productos tengo?', '¿Cómo puedo crear un almacén?',
    '¿Qué productos tienen stock bajo?', '¿Cuánto stock tengo?'])
def test_existing_operational_queries_keep_their_routes(question):
    assert SaikiIntentRouter.classify(question).kind != 'conversation'


def test_example_continues_general_question_and_does_not_skip_newer_topic():
    history = [{'role': 'user', 'content': QUESTION},
               {'role': 'assistant', 'content': 'Actualmente tienes 3 productos y 45 unidades.'}]
    assert SaikiIntentRouter.classify('Dame un ejemplo práctico.', history).kind == 'conversation'
    history += [{'role': 'user', 'content': 'Dame un ejemplo práctico.'},
                {'role': 'assistant', 'content': 'Por ejemplo...'}]
    assert SaikiIntentRouter.classify('Otro ejemplo.', history).kind == 'conversation'
    assert SaikiIntentRouter.classify('Dame un ejemplo práctico.').kind == 'ambiguous'
    history += [{'role': 'user', 'content': '¿Cuánto stock tengo?'}]
    assert SaikiIntentRouter.classify('Dame un ejemplo práctico.', history).kind != 'conversation'


@pytest.mark.parametrize('role', ['EMPRESA', 'OPERARIO'])
@pytest.mark.parametrize('followup', [False, True])
def test_authenticated_advice_uses_qwen_and_preserves_history(monkeypatch, role, followup):
    service = SaikiService()
    history = ([{'role': 'user', 'content': QUESTION},
                {'role': 'assistant', 'content': 'Actualmente tienes 3 productos y 45 unidades.'}]
               if followup else [])
    message = 'Dame un ejemplo práctico.' if followup else QUESTION
    model = AsyncMock(return_value={'message': {'content': 'Ejemplo hipotético: separa secos y refrigerados.'}})
    monkeypatch.setattr(service, '_ollama_chat', model)
    def forbidden(*args, **kwargs):
        pytest.fail('General advice must not query inventory or reports')
    monkeypatch.setattr(service.tools, 'execute', forbidden)
    monkeypatch.setattr('app.services.saiki_reportes.report_answer', forbidden)
    monkeypatch.setattr('app.services.saiki_warehouse_map.respuesta_plano', forbidden)
    user = UsuarioActual(rol=role, id_empresa='company-1',
                         **({'id_operario': 'op-1', 'id_almacen': 'warehouse-1'} if role == 'OPERARIO' else {}))
    data = SaikiAskRequest(message=message, history=history)
    result = asyncio.run(service.ask(data, user))
    assert result['source'] == 'ollama'
    assert result['answer'].startswith('Ejemplo hipotético:')
    model.assert_awaited_once()
    messages, tools = model.call_args.args
    assert tools == frozenset()
    assert messages[1:-1] == history
    assert messages[-1] == {'role': 'user', 'content': message}
    assert 'hipotéticos' in messages[0]['content']


@pytest.mark.parametrize('question', [
    '¿Y si no tengo espacio suficiente?',
    '¿Puedes ampliar ese punto?',
    '¿Y eso cómo lo aplico?',
    'Continúa por favor',
    '¿Y después?',
])
@pytest.mark.parametrize('role', ['EMPRESA', 'OPERARIO'])
def test_unmatched_followups_consult_qwen_with_previous_answer(monkeypatch, question, role):
    service = SaikiService()
    history = [{'role': 'user', 'content': QUESTION},
               {'role': 'assistant', 'content': 'Separa los alimentos secos de los refrigerados.'}]
    model = AsyncMock(return_value={'message': {'content': 'Puedes empezar por separar las zonas disponibles.'}})
    monkeypatch.setattr(service, '_ollama_chat', model)
    monkeypatch.setattr('app.services.saiki_reportes.report_answer', AsyncMock(return_value=None))
    monkeypatch.setattr('app.services.saiki_warehouse_map.respuesta_plano', AsyncMock(return_value=None))
    def forbidden(*args, **kwargs):
        pytest.fail('A contextual followup must not silently become an inventory summary')
    monkeypatch.setattr(service.tools, 'execute', forbidden)
    monkeypatch.setattr('app.services.saiki_inventory_summary.inventory_summary', forbidden)
    user = UsuarioActual(rol=role, id_empresa='company-1',
                         **({'id_operario': 'op-1', 'id_almacen': 'warehouse-1'} if role == 'OPERARIO' else {}))
    response = asyncio.run(service.ask(SaikiAskRequest(message=question, history=history), user))
    assert response['source'] == 'ollama'
    model.assert_awaited_once()
    messages, tools = model.call_args.args
    assert messages[1:-1] == history
    assert messages[-1]['content'] == question
    assert tools == frozenset()


def test_ambiguous_report_confirmation_still_uses_existing_authorized_workflow(monkeypatch):
    service = SaikiService()
    report = AsyncMock(return_value=('El reporte está confirmado.', {'reporte_accion': {'estado': 'CONFIRMADO'}}))
    monkeypatch.setattr('app.services.saiki_reportes.report_answer', report)
    model = AsyncMock()
    monkeypatch.setattr(service, '_ollama_chat', model)
    data = SaikiAskRequest(message='Sí', context={'reporte_accion': 'report-1'})
    user = UsuarioActual(rol='EMPRESA', id_empresa='company-1')
    response = asyncio.run(service.ask(data, user))
    assert response['source'] == 'backend'
    assert response['answer'] == 'El reporte está confirmado.'
    report.assert_awaited_once_with(data, user)
    model.assert_not_awaited()
