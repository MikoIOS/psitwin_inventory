import asyncio
import base64
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from app.controllers import local_voice_controller as voice
from app.dependencies.dependencies import require_empresa_u_operario as require_empresa


def request(monkeypatch, path, content, content_type, result=None, error=None):
    app = FastAPI()
    app.include_router(voice.router)
    app.dependency_overrides[require_empresa] = lambda: object()
    monkeypatch.setattr(voice.settings, 'saiki_stt_enabled', True)
    monkeypatch.setattr(voice.settings, 'saiki_tts_enabled', True)
    monkeypatch.setattr(voice.settings, 'saiki_tts_provider', 'kokoro')
    execute = AsyncMock(return_value=result or {'text': 'Muéstrame los sensores'}, side_effect=error)
    monkeypatch.setattr(voice.voice_service, 'execute', execute)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            return await client.post(path, content=content, headers={'content-type': content_type})
    return asyncio.run(run()), execute


@pytest.mark.parametrize('content_type', ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/wav', 'audio/mp4'])
def test_supported_microphone_containers_reach_transcriber(monkeypatch, content_type):
    response, execute = request(monkeypatch, '/saiki/voice/transcribe', bytes(200), content_type)
    assert response.status_code == 200
    assert response.json() == {'text': 'Muéstrame los sensores'}
    payload = execute.await_args.args[0]
    assert payload['operation'] == 'transcribe'
    assert len(base64.b64decode(payload['audio'])) == 200


@pytest.mark.parametrize('size,content_type,status', [(10, 'audio/webm', 422), (200, 'text/plain', 415), (4 * 1024 * 1024 + 1, 'audio/webm', 413)], ids=['too-short', 'unsupported', 'too-large'])
def test_invalid_audio_does_not_reach_worker(monkeypatch, size, content_type, status):
    response, execute = request(monkeypatch, '/saiki/voice/transcribe', bytes(size), content_type)
    assert response.status_code == status
    execute.assert_not_awaited()


def test_silence_is_not_sent_as_a_chat_message(monkeypatch):
    response, _ = request(monkeypatch, '/saiki/voice/transcribe', bytes(200), 'audio/webm', {'text': ''})
    assert response.status_code == 422


@pytest.mark.parametrize('status', [429, 503, 504])
def test_worker_failures_remain_distinct_http_errors(monkeypatch, status):
    response, _ = request(monkeypatch, '/saiki/voice/transcribe', bytes(200), 'audio/webm', error=HTTPException(status, 'Controlled failure'))
    assert response.status_code == status


def test_dynamic_response_audio_is_not_cached(monkeypatch):
    response, execute = request(monkeypatch, '/saiki/voice/synthesize', '{"text":"Respuesta nueva de Saiki"}', 'application/json', {'audio': base64.b64encode(b'RIFFfixture').decode()})
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    assert response.content == b'RIFFfixture'
    assert execute.await_args.args[0]['text'] == 'Respuesta nueva de Saiki'


def test_voice_requires_authentication():
    app = FastAPI()
    app.include_router(voice.router)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            return await client.post('/saiki/voice/transcribe', content=bytes(200), headers={'content-type': 'audio/webm'})
    assert asyncio.run(run()).status_code in {401, 403}
