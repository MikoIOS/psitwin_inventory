"""Transport contracts: real routing/auth with mocked inference, never fake model readiness."""
import asyncio
from datetime import date, timedelta
from types import SimpleNamespace

import httpx
import pytest

from app.services.remote_ai import RemoteAutoGluonRuntime, service_headers
from app.services.autogluon_runtime import ModelUnavailable
from ai_service import main as gateway

KEY = 'a-test-service-key-at-least-32-characters'


def test_credentials_require_tls_except_loopback():
    settings = SimpleNamespace(ai_service_api_key=KEY)
    assert service_headers(settings, 'https://ai.example.com')['Authorization'] == 'Bearer ' + KEY
    assert service_headers(settings, 'http://127.0.0.1:8100')
    with pytest.raises(ValueError):
        service_headers(settings, 'http://35.171.142.151:8100')
    with pytest.raises(ValueError):
        service_headers(SimpleNamespace(), 'https://ai.example.com')
    assert service_headers(SimpleNamespace(), 'http://localhost:11434', required=False) == {}


def test_remote_predict_preserves_tenant_and_model_response(monkeypatch):
    settings = SimpleNamespace(ai_service_api_key=KEY, autogluon_remote_url='https://ai.example.com',
                               autogluon_timeout_seconds=300)
    runtime = RemoteAutoGluonRuntime(settings)
    calls = []
    def respond(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return {'result': {'predictions': {'series': [{}] * 90}}, 'cached': True}
    monkeypatch.setattr(runtime, '_request', respond)
    result, cached = runtime.predict('tenant-1', 'series', [{'fecha': '2026-01-01', 'cantidad': 1}])
    assert cached and len(result['predictions']['series']) == 90
    assert calls[0][2]['json']['tenant'] == 'tenant-1'
    monkeypatch.setattr(runtime, '_request', lambda *a, **kw: {'result': {}, 'cached': False})
    with pytest.raises(ModelUnavailable):
        runtime.predict('tenant-1', 'series', [])


def test_remote_failure_reports_unavailable(monkeypatch):
    runtime = RemoteAutoGluonRuntime(SimpleNamespace(autogluon_remote_url='https://ai.example.com'))
    def fail(*args, **kwargs):
        raise httpx.ConnectError('offline')
    monkeypatch.setattr(runtime, '_request', fail)
    assert runtime.status()['validado'] is False
    with pytest.raises(ModelUnavailable):
        runtime.predict('tenant', 'series', [])


def test_http_transport_sends_credentials_without_redirects(monkeypatch):
    real_client = httpx.Client
    def handler(request):
        assert request.headers['Authorization'] == 'Bearer ' + KEY
        assert str(request.url) == 'https://ai.example.com/forecast/status'
        return httpx.Response(200, json={'validado': True, 'model_fingerprint': 'real-model'})
    monkeypatch.setattr(httpx, 'Client', lambda **kw: real_client(
        transport=httpx.MockTransport(handler), **kw))
    runtime = RemoteAutoGluonRuntime(SimpleNamespace(ai_service_api_key=KEY,
        autogluon_remote_url='https://ai.example.com', autogluon_timeout_seconds=300))
    assert runtime.status()['model_fingerprint'] == 'real-model'


def test_gateway_auth_stream_tools_forecast_and_busy(monkeypatch):
    monkeypatch.setattr(gateway.settings, 'ai_service_api_key', KEY)
    real_client = httpx.Client
    observed = []
    def ollama(request):
        import json
        payload = json.loads(request.content)
        observed.append(payload)
        assert 'authorization' not in request.headers
        return httpx.Response(200, content=b'{"message":{"tool_calls":[{"function":{"name":"stock"}}]},"done":true}\n',
                              headers={'content-type': 'application/x-ndjson'})
    monkeypatch.setattr(gateway, 'upstream_client', lambda: real_client(
        base_url='http://localhost:11434', transport=httpx.MockTransport(ollama)))
    class Model:
        def status(self):
            return {'validado': False, 'faltantes': ['pesos ausentes']}
        def predict(self, tenant, identifier, history):
            assert tenant == 'company-1'
            assert len(history) == 91
            return {'predictions': {identifier: [{}] * 90}}, False
        def close(self):
            pass
    monkeypatch.setattr(gateway, 'model_runtime', Model())

    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway.app),
                                     base_url='http://test') as client:
            assert (await client.get('/health')).status_code == 401
            client.headers['Authorization'] = 'Bearer ' + KEY
            assert (await client.get('/health')).status_code == 200
            assert (await client.get('/forecast/status')).json()['validado'] is False
            payload = {'model': 'qwen3:4b', 'messages': [{'role': 'user', 'content': 'stock'}],
                       'tools': [{'type': 'function', 'function': {'name': 'stock'}}], 'stream': True}
            result = await client.post('/api/chat', json=payload)
            assert result.status_code == 200
            assert result.json()['message']['tool_calls'][0]['function']['name'] == 'stock'
            assert observed[0]['tools'] == payload['tools']
            assert observed[0]['keep_alive'] == 0
            assert observed[0]['options']['num_thread'] == 2
            assert not gateway.inference_lock.locked()
            assert (await client.post('/api/chat', json={**payload, 'model': 'other'})).status_code == 422
            gateway.inference_lock.acquire()
            try:
                assert (await client.post('/api/chat', json=payload)).status_code == 429
            finally:
                gateway.inference_lock.release()
            history = [{'fecha': (date(2026, 1, 1) + timedelta(days=i)).isoformat(), 'cantidad': 2}
                       for i in range(91)]
            body = {'tenant': 'company-1', 'identifier': 'series', 'history': history}
            prediction = await client.post('/forecast', json=body)
            assert prediction.status_code == 200
            assert len(prediction.json()['result']['predictions']['series']) == 90
            body['history'][1]['fecha'] = '2026-01-01'
            assert (await client.post('/forecast', json=body)).status_code == 422
            assert not gateway.inference_lock.locked()
            assert (await client.post('/api/chat', content=b' ' * 2_000_001)).status_code == 413
    asyncio.run(exercise())


def test_saiki_health_and_sync_chat_attach_service_key(monkeypatch):
    from app.services.saiki_service import SaikiService
    from app.services import saiki_service as module
    service = SaikiService()
    monkeypatch.setattr(service.settings, 'ai_service_api_key', KEY)
    monkeypatch.setattr(service.settings, 'ollama_base_url', 'https://ai.example.com')
    class Tags:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b'{"models":[{"name":"qwen3:4b"}]}'
    def urlopen(req, **kwargs):
        assert req.get_header('Authorization') == 'Bearer ' + KEY
        return Tags()
    monkeypatch.setattr(module.request, 'urlopen', urlopen)
    assert service._installed_models() == ['qwen3:4b']
    class Connection:
        sock = None
        def __init__(self, *args, **kwargs): pass
        def request(self, method, path, body, headers):
            assert path == '/api/chat'
            assert headers['Authorization'] == 'Bearer ' + KEY
        def getresponse(self):
            return SimpleNamespace(status=200, read=lambda: b'{"message":{"content":"ok"}}')
        def close(self): pass
    monkeypatch.setattr(module.http.client, 'HTTPSConnection', Connection)
    assert service._call_ollama_chat([{'role': 'user', 'content': 'hola'}])['message']['content'] == 'ok'


def test_gateway_upstream_error_releases_slot(monkeypatch):
    monkeypatch.setattr(gateway.settings, 'ai_service_api_key', KEY)
    real_client = httpx.Client
    monkeypatch.setattr(gateway, 'upstream_client', lambda: real_client(
        base_url='http://localhost:11434', transport=httpx.MockTransport(
            lambda req: httpx.Response(500, json={'error': 'private server error'}))))
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway.app),
                base_url='http://test', headers={'Authorization': 'Bearer ' + KEY}) as client:
            response = await client.post('/api/chat', json={'model': 'qwen3:4b', 'messages': []})
            assert response.status_code == 503
            assert 'private server error' not in response.text
            assert not gateway.inference_lock.locked()
    asyncio.run(exercise())


def test_instruct_model_does_not_get_hybrid_thinking_switch(monkeypatch):
    from app.services.saiki_service import SaikiService
    service = SaikiService()
    monkeypatch.setattr(service.settings, 'ollama_model', 'qwen3:4b-instruct')
    messages = [{'role': 'user', 'content': 'stock'}]
    assert service._inference_messages(messages) == messages


def test_network_setup_preserves_other_groups_and_scopes_ports(monkeypatch):
    from ai_service import configure_aws_network as setup
    calls = []
    def aws(*args):
        calls.append(args)
        if args[0] == 'describe-instances':
            return {'Reservations': [{'Instances': [{
                'Tags': [{'Key': 'Name', 'Value': 'psitwin'}],
                'PublicIpAddress': '35.171.142.151', 'VpcId': 'vpc-test',
                'SecurityGroups': [{'GroupId': 'sg-original'}]}]}]}
        if args[0] == 'describe-security-groups': return {'SecurityGroups': []}
        if args[0] == 'create-security-group': return {'GroupId': 'sg-new'}
        return {}
    monkeypatch.setattr(setup, 'aws', aws)
    setup.main()
    attach = next(call for call in calls if call[0] == 'modify-instance-attribute')
    assert attach[-3:] == ('--groups', 'sg-original', 'sg-new')
    assert attach[2] == setup.INSTANCE
    import json
    rules = [call for call in calls if call[0] == 'authorize-security-group-ingress']
    assert len(rules) == 2
    assert {json.loads(call[-1])[0]['FromPort'] for call in rules} == {80, 443}
    assert all(call[2] == 'sg-new' for call in rules)


def test_network_setup_rejects_other_instance_before_mutation(monkeypatch):
    from ai_service import configure_aws_network as setup
    calls = []
    def aws(*args):
        calls.append(args)
        return {'Reservations': [{'Instances': [{'Tags': [], 'PublicIpAddress': '1.2.3.4'}]}]}
    monkeypatch.setattr(setup, 'aws', aws)
    with pytest.raises(SystemExit): setup.main()
    assert len(calls) == 1 and calls[0][0] == 'describe-instances'
