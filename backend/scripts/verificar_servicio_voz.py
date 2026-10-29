"""Real local worker behind authenticated FastAPI routes; no production database writes."""
import asyncio
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['HF_HUB_OFFLINE'] = '1'
from fastapi import FastAPI
import httpx
from app.config.settings import settings
from app.config.paths import runtime_path
from app.controllers.local_voice_controller import router
from app.dependencies.dependencies import require_empresa
from app.dto.auth_dto import UsuarioActual
from app.services.local_voice_service import voice_service


async def main():
    settings.saiki_voice_python = sys.executable
    settings.saiki_voice_site_packages = str(runtime_path('.voice.local/Lib/site-packages'))
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_empresa] = lambda: UsuarioActual(rol='EMPRESA', id_empresa='voice-smoke-test')
    results = {'offline': True, 'event_loop': type(asyncio.get_running_loop()).__name__, 'worker_transport': 'subprocess pipes in thread'}
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test', timeout=180) as client:
            sample = None
            for name in ('em_santa', 'em_alex'):
                start = time.perf_counter()
                response = await client.post('/saiki/voice/synthesize', json={'voice': name, 'speed': 1,
                    'text': 'Hola, soy Saiki. Puedo ayudarte a consultar las lecturas de tus sensores.'})
                results[name] = {'status': response.status_code, 'bytes': len(response.content), 'seconds': round(time.perf_counter() - start, 3)}
                if response.status_code == 200:
                    assert response.content[:4] == b'RIFF'
                    sample = response.content
                print(name, results[name], flush=True)
            if sample:
                start = time.perf_counter()
                response = await client.post('/saiki/voice/transcribe', content=sample, headers={'Content-Type': 'audio/wav'})
                results['stt'] = {'status': response.status_code, 'result': response.json(), 'seconds': round(time.perf_counter() - start, 3)}
                print('stt', results['stt'], flush=True)
    finally:
        await voice_service.close()
        (ROOT / 'artifacts').mkdir(exist_ok=True)
        (ROOT / 'artifacts/voz-http-validacion.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    assert all(results.get(name, {}).get('status') == 200 for name in ('em_santa', 'em_alex', 'stt'))


if sys.platform == 'win32':
    asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
else:
    asyncio.run(main())
