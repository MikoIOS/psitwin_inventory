"""Live transport/model smoke. Uses no MongoDB, does not execute stock tools."""
import argparse
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from dotenv import dotenv_values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8100')
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    config = dotenv_values(Path.home() / 'psitwin-ai/service.env')
    key = config['AI_SERVICE_API_KEY']
    model = config['OLLAMA_MODEL']
    for headers in [{}, {'Authorization': 'Bearer invalid'}]:
        try:
            with urlopen(Request(base + '/health', headers=headers), timeout=15):
                raise RuntimeError('El servicio permitió acceso sin una clave válida')
        except HTTPError as exc:
            if exc.code != 401:
                raise
    print('PASS: acceso sin clave o con clave incorrecta rechazado')

    def request(path, payload=None):
        req = Request(base + path, data=json.dumps(payload).encode() if payload is not None else None,
                      headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        return urlopen(req, timeout=300)

    with request('/health') as response:
        assert json.load(response)['status'] == 'ok'
    with request('/api/tags') as response:
        assert model in [item['name'] for item in json.load(response)['models']]
    print('PASS: API autenticada y modelo descargado')
    payload = {'model': model, 'messages': [{'role': 'user', 'content': '¿Cuánto es 2+2? Responde solo el número.'}],
               'think': False, 'stream': False, 'options': {'num_predict': 256}}
    with request('/api/chat', payload) as response:
        result = json.load(response)
    assert result['done_reason'] == 'stop' and result['message']['content'].strip() == '4', result
    print('PASS: inferencia real devuelve 4 y termina sin truncarse')
    payload['messages'] = [{'role': 'user', 'content':
        'Consulta el stock de producto-prueba usando consultar_stock. No inventes el resultado.'}]
    payload['tools'] = [{'type': 'function', 'function': {'name': 'consultar_stock',
        'description': 'Consulta stock registrado de un producto.', 'parameters': {
            'type': 'object', 'properties': {'id_producto': {'type': 'string'}}, 'required': ['id_producto']}}}]
    with request('/api/chat', payload) as response:
        result = json.load(response)
    calls = result.get('message', {}).get('tool_calls', [])
    assert any(call['function']['name'] == 'consultar_stock' and
               call['function']['arguments'].get('id_producto') == 'producto-prueba' for call in calls), result
    print('PASS: llamada a herramienta con argumentos correctos (sin ejecutar herramienta)')
    payload.pop('tools')
    payload['messages'] = [{'role': 'user', 'content': 'Responde únicamente: Hola'}]
    payload['stream'] = True
    content, done = [], False
    with request('/api/chat', payload) as response:
        for index, line in enumerate(response):
            if index > 2048:
                raise RuntimeError('Stream excesivo')
            if not line.strip():
                continue
            chunk = json.loads(line)
            content.append(chunk.get('message', {}).get('content', ''))
            if chunk.get('done'):
                assert chunk.get('done_reason') == 'stop', chunk
                done = True
                break
    assert done and ''.join(content).strip()
    print('PASS: streaming real completo')
    with request('/forecast/status') as response:
        status = json.load(response)
    print('AutoGluon:', status.get('estado'), '; validado:', status.get('validado'))
    if not status.get('validado'):
        print('PENDIENTE: instalar y validar los artefactos originales de AutoGluon.')


if __name__ == '__main__':
    main()
