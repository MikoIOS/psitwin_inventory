"""TLS connection arguments; never contacts a real broker."""
import asyncio
import ssl
from unittest.mock import Mock
import pytest
from app.services.sensores import monitoreo_service as module

@pytest.mark.parametrize('enabled', [False, True])
def test_mqtt_tls_keeps_certificate_validation(monkeypatch, enabled):
    captured = {}
    class CancelledClient:
        def __init__(self, **kwargs): captured.update(kwargs)
        async def __aenter__(self): raise asyncio.CancelledError()
        async def __aexit__(self, *args): pass
    monkeypatch.setattr(module.aiomqtt, 'Client', CancelledClient)
    monkeypatch.setattr(module.settings, 'mqtt_tls', enabled)
    monkeypatch.setattr(module.settings, 'mqtt_ca_file', None)
    async def run():
        with pytest.raises(asyncio.CancelledError):
            await module.MonitoreoService()._consumir_mqtt()
    asyncio.run(run())
    context = captured['tls_context']
    if enabled:
        assert isinstance(context, ssl.SSLContext)
        assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
    else:
        assert context is None

def test_mqtt_uses_the_configured_ca_file(monkeypatch):
    context = ssl.create_default_context()
    factory = Mock(return_value=context)
    captured = {}
    class CancelledClient:
        def __init__(self, **kwargs): captured.update(kwargs)
        async def __aenter__(self): raise asyncio.CancelledError()
        async def __aexit__(self, *args): pass
    monkeypatch.setattr(module.aiomqtt, 'Client', CancelledClient)
    monkeypatch.setattr(module.ssl, 'create_default_context', factory)
    monkeypatch.setattr(module.settings, 'mqtt_tls', True)
    monkeypatch.setattr(module.settings, 'mqtt_ca_file', 'authorized-ca.pem')
    async def run():
        with pytest.raises(asyncio.CancelledError):
            await module.MonitoreoService()._consumir_mqtt()
    asyncio.run(run())
    factory.assert_called_once_with(cafile='authorized-ca.pem')
    assert captured['tls_context'] is context
