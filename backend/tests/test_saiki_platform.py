import asyncio
import json
import httpx
from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException, Request
from app.dto.auth_dto import UsuarioActual
from app.dto.saiki_dto import SaikiAskRequest
from app.services.saiki_service import SaikiService
from app.services.saiki_tools import NoArgs
from app.services.saiki_intent_router import SaikiIntentRouter
from app.controllers import saiki_controller
from tests.test_google_auth import isolated_database

@pytest.mark.parametrize('question', ['Hola', '¿Quién eres?', '¿Qué puedes hacer?', '¿Cómo me ayudas?', 'Gracias', 'Adiós', '¿Cómo puedo crear un producto?', '¿Cómo puedo crear un almacén?', '¿Cómo activo mi micrófono?', 'Explícame la voz de Saiki', '¿Puedes usar Jorge de FreeTTS?'])
def test_direct_and_help_do_not_query_mongo_or_model(monkeypatch, question):
    service = SaikiService()
    def forbidden(*a, **kw): pytest.fail('This question must not call databases or LLM')
    monkeypatch.setattr(service.tools, 'execute', forbidden)
    monkeypatch.setattr(service, '_call_ollama_chat', forbidden)
    response = asyncio.run(service.ask(SaikiAskRequest(message=question)))
    assert response['answer'] and response['source'] in {'router', 'knowledge'}
    if 'producto' in question:
        assert 'PROVEEDOR' in response['answer'] and 'Nuevo producto' in response['answer']
        assert response['data']['seccion'] == '/productos'

def test_workforce_and_locations_use_real_mongo_and_respect_company(monkeypatch):
    async def run():
        async with isolated_database(monkeypatch) as db:
            for tenant in ('a', 'b'):
                await db.almacenes.insert_one({'id': tenant + '-w', 'id_empresa': tenant, 'nombre': 'Warehouse-' + tenant})
                await db.zonas.insert_one({'id': tenant + '-z', 'id_almacen': tenant + '-w'})
                await db.racks.insert_one({'id_rack': tenant + '-r', 'id_zona': tenant + '-z'})
            await db.operarios.insert_many([
                {'id_operario': 'a1', 'id_empresa': 'a', 'estado': 'ACTIVO'},
                {'id_operario': 'a2', 'id_empresa': 'a', 'estado': 'INACTIVO'},
                {'id_operario': 'b1', 'id_empresa': 'b', 'estado': 'ACTIVO'},
            ])
            service = SaikiService()
            def forbidden(*a, **kw): pytest.fail('No product query or LLM needed')
            monkeypatch.setattr(service, '_call_ollama_chat', forbidden)
            a, b = (UsuarioActual(rol='EMPRESA', id_empresa=t) for t in ('a', 'b'))
            response = await service.ask(SaikiAskRequest(message='¿Cuántos operarios tengo?'), a)
            assert response['data']['get_workforce'] == {'total': 2, 'activos': 1, 'inactivos': 1, 'otros_estados': 0}
            assert 'productos' not in response['answer']
            warehouses = await service.ask(SaikiAskRequest(message='¿Cuántos almacenes tengo?'), a)
            assert warehouses['data']['get_locations']['total_almacenes'] == 1
            assert 'Warehouse-a' in warehouses['answer'] and 'Warehouse-b' not in warehouses['answer']
            assert (await service.ask(SaikiAskRequest(message='¿Cuántos operarios tengo?'), b))['data']['get_workforce']['total'] == 1
            empty = await service.ask(SaikiAskRequest(message='¿Cuántos operarios tengo?'), UsuarioActual(rol='EMPRESA', id_empresa='empty'))
            assert empty['answer'] == 'No tienes operarios registrados.'
            with pytest.raises(HTTPException) as exc:
                await service.tools.get_workforce(NoArgs(), UsuarioActual(rol='OPERARIO', id_empresa='a', id_operario='a1'))
            assert exc.value.status_code == 403
    asyncio.run(run())

def test_database_timeout_is_not_empty_result(monkeypatch):
    service = SaikiService()
    monkeypatch.setattr(service.settings, 'saiki_database_timeout_seconds', .02)
    async def blocked(*args): await asyncio.sleep(5)
    monkeypatch.setattr(service.tools, 'execute', blocked)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.ask(SaikiAskRequest(message='¿Cuántos operarios tengo?'), UsuarioActual(rol='EMPRESA', id_empresa='a')))
    assert exc.value.status_code == 504
    assert 'No tienes' not in exc.value.detail

def test_stream_disconnect_cancels_backend_task(monkeypatch):
    async def run():
        cancelled = asyncio.Event()
        async def blocked(*args, **kw):
            try: await asyncio.sleep(20)
            finally: cancelled.set()
        monkeypatch.setattr(saiki_controller.service, 'ask', blocked)
        request = Request({'type': 'http', 'state': {'saiki_request_id': 'cancellation-test'}})
        response = await saiki_controller.events(SaikiAskRequest(message='Hola'), request, UsuarioActual(rol='EMPRESA', id_empresa='a'))
        iterator = response.body_iterator
        event = json.loads(await anext(iterator))
        assert event['phase'] == 'thinking'
        await iterator.aclose()
        assert cancelled.is_set()
    asyncio.run(run())

def test_stream_idle_timeout(monkeypatch):
    async def run():
        monkeypatch.setattr(saiki_controller.service.settings, 'saiki_idle_timeout_seconds', .02)
        async def blocked(*args, **kw): await asyncio.sleep(20)
        monkeypatch.setattr(saiki_controller.service, 'ask', blocked)
        request = Request({'type': 'http', 'state': {'saiki_request_id': 'timeout-test'}})
        response = await saiki_controller.events(SaikiAskRequest(message='Hola'), request, UsuarioActual(rol='EMPRESA', id_empresa='a'))
        events = [json.loads(event) async for event in response.body_iterator]
        assert events[-1]['type'] == 'error' and events[-1]['status'] == 504
    asyncio.run(run())

def test_live_generation_renews_idle_deadline_and_preserves_original_messages(monkeypatch):
    async def run():
        original = httpx.AsyncClient
        class Chunks(httpx.AsyncByteStream):
            async def __aiter__(self):
                for word in ['Una ', 'explicación ', 'breve.']:
                    await asyncio.sleep(.08)
                    yield (json.dumps({'message': {'content': word}, 'done': False}) + '\n').encode()
                yield (json.dumps({'message': {}, 'done': True}) + '\n').encode()
        payloads = []
        def handler(request):
            payloads.append(json.loads(request.content))
            return httpx.Response(200, stream=Chunks())
        monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
        monkeypatch.setattr(saiki_controller.service.settings, 'saiki_idle_timeout_seconds', .2)
        monkeypatch.setattr(saiki_controller.service.settings, 'saiki_model_start_timeout_seconds', .5)
        monkeypatch.setattr(saiki_controller.service.settings, 'ollama_model', 'qwen3:4b')
        request = Request({'type': 'http', 'state': {'saiki_request_id': 'progress-test'}})
        response = await saiki_controller.events(SaikiAskRequest(message='Explica FIFO'), request, UsuarioActual(rol='EMPRESA', id_empresa='a'))
        events = [json.loads(event) async for event in response.body_iterator]
        assert events[-1]['type'] == 'result'
        assert events[-1]['result']['answer'] == 'Una explicación breve.'
        assert sum(event.get('phase') == 'generating' for event in events) >= 3
        assert payloads[0]['stream'] is True and payloads[0]['think'] is False
        assert '/no_think' in payloads[0]['messages'][0]['content']
        messages = [{'role': 'system', 'content': 'Original'}]
        assert '/no_think' in saiki_controller.service._inference_messages(messages)[0]['content']
        assert messages[0]['content'] == 'Original'
    asyncio.run(run())
