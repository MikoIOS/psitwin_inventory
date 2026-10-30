"""Authenticated inference transport; authorization and tool execution stay in Render."""
from urllib.parse import urlsplit

import httpx


def service_headers(settings, url, *, required=True):
    key = getattr(settings, 'ai_service_api_key', '')
    if required and not key:
        raise ValueError('AI_SERVICE_API_KEY es obligatorio para inferencia remota')
    parsed = urlsplit(url)
    if key and (parsed.scheme != 'https' and not (
        parsed.scheme == 'http' and parsed.hostname in {'localhost', '127.0.0.1', '::1'}
    )):
        raise ValueError('La conexión con la IA requiere HTTPS')
    return {'Authorization': f'Bearer {key}'} if key else {}


class RemoteAutoGluonRuntime:
    def __init__(self, settings):
        self.settings = settings
        self.url = settings.autogluon_remote_url.rstrip('/')

    def _request(self, method, path, **kwargs):
        with httpx.Client(timeout=httpx.Timeout(
            self.settings.autogluon_timeout_seconds, connect=5), follow_redirects=False) as client:
            response = client.request(method, self.url + path,
                headers=service_headers(self.settings, self.url), **kwargs)
            response.raise_for_status()
            result = response.json()
            if not isinstance(result, dict):
                raise ValueError('Respuesta remota inválida')
            return result

    def status(self):
        try:
            state = self._request('GET', '/forecast/status')
            if not isinstance(state.get('validado'), bool):
                raise ValueError('Estado remoto inválido')
            return state
        except (httpx.HTTPError, ValueError):
            return {'estado': 'MODELO_NO_DISPONIBLE', 'validado': False,
                    'faltantes': ['No se pudo verificar AutoGluon en el servicio remoto'],
                    'model_fingerprint': None}

    def predict(self, tenant, identifier, history):
        from app.services.autogluon_runtime import ModelUnavailable
        try:
            result = self._request('POST', '/forecast', json={
                'tenant': str(tenant), 'identifier': identifier, 'history': history})
            predictions = result['result']['predictions'][identifier]
            if len(predictions) != 90 or not isinstance(result['cached'], bool):
                raise ValueError('Pronóstico incompleto')
            return result['result'], result['cached']
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise ModelUnavailable('Inferencia remota no disponible; no se generaron pronósticos alternativos') from exc
