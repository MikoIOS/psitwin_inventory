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
