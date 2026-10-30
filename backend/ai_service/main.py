"""Run from backend: uvicorn ai_service.main:app --host 127.0.0.1 --port 8100."""
from contextlib import asynccontextmanager
from datetime import date
import hmac
import threading

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.background import BackgroundTask

from app.config.settings import get_settings
from app.services.autogluon_runtime import AutoGluonRuntime, ModelUnavailable

settings = get_settings()
model_runtime = AutoGluonRuntime(settings)
inference_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app):
    if len(settings.ai_service_api_key) < 32:
        raise RuntimeError('Configure AI_SERVICE_API_KEY con al menos 32 caracteres')
    yield
    model_runtime.close()


def authenticate(authorization: str = Header(default='')):
    key = settings.ai_service_api_key
    if len(key) < 32 or not hmac.compare_digest(
        authorization.encode(), ('Bearer ' + key).encode()
    ):
        raise HTTPException(401, 'Credenciales del servicio inválidas')


app = FastAPI(title='PsiTwin Inference', lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None,
              dependencies=[Depends(authenticate)])


@app.middleware('http')
async def limit_body(request: Request, call_next):
    # Bound history/chat inputs before parsing. No arbitrary file or model paths.
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 2_000_000:
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail': 'Solicitud demasiado grande'}, status_code=413)
    request._body = bytes(body)
    return await call_next(request)


@app.get('/health')
def health():
    return {'status': 'ok'}


def upstream_client():
    return httpx.Client(base_url=settings.ai_ollama_local_url,
                        timeout=httpx.Timeout(180, connect=5), follow_redirects=False)


@app.get('/api/tags')
def tags():
    try:
        with upstream_client() as client:
            response = client.get('/api/tags')
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, 'Ollama no disponible') from exc


@app.post('/api/chat')
async def chat(request: Request):
    try:
        payload = await request.json()
        if not isinstance(payload, dict) or not isinstance(payload.get('messages'), list):
            raise ValueError()
        if payload.get('model') != settings.ollama_model:
            raise ValueError()
        options = payload.get('options') or {}
        if not isinstance(options, dict):
            raise ValueError()
        payload['options'] = {
            'num_ctx': 4096, 'num_thread': 2,
            'num_predict': max(32, min(1024, int(options.get('num_predict', 512)))),
        }
        # Release model memory after each request to leave room for AutoGluon.
        payload['keep_alive'] = 0
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, 'Modelo o mensajes inválidos') from exc
    if not inference_lock.acquire(blocking=False):
        raise HTTPException(429, 'La IA está ocupada; reintenta al terminar la consulta actual')
    # Run blocking network setup outside the event loop.
    from starlette.concurrency import run_in_threadpool
    client = None
    response = None
    cleaned = False

    def cleanup():
        nonlocal cleaned
        if cleaned:
            return
        cleaned = True
        if response is not None:
            response.close()
        if client is not None:
            client.close()
        inference_lock.release()

    def open_response():
        return client.send(client.build_request('POST', '/api/chat', json=payload), stream=True)

    try:
        client = upstream_client()
        response = await run_in_threadpool(open_response)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        cleanup()
        raise HTTPException(503, 'Ollama no disponible') from exc
    except BaseException:
        cleanup()
        raise

    def chunks():
        try:
            yield from response.iter_bytes()
        finally:
            cleanup()

    return StreamingResponse(chunks(), media_type=response.headers.get(
        'content-type', 'application/x-ndjson'), background=BackgroundTask(cleanup))


class HistoryRow(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    fecha: date
    cantidad: float = Field(ge=0)


class ForecastRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tenant: str = Field(min_length=1, max_length=200)
    identifier: str = Field(min_length=1, max_length=500)
    history: list[HistoryRow] = Field(min_length=91, max_length=20000)


@app.get('/forecast/status')
def forecast_status():
    return model_runtime.status()


@app.post('/forecast')
def forecast(data: ForecastRequest):
    dates = [row.fecha for row in data.history]
    if any((b - a).days != 1 for a, b in zip(dates, dates[1:])):
        raise HTTPException(422, 'El historial debe tener días consecutivos y ordenados')
    if not inference_lock.acquire(blocking=False):
        raise HTTPException(429, 'La IA está ocupada')
    try:
        result, cached = model_runtime.predict(data.tenant, data.identifier,
            [row.model_dump(mode='json') for row in data.history])
        return {'result': result, 'cached': cached}
    except ModelUnavailable as exc:
        raise HTTPException(503, 'Modelo AutoGluon no disponible o inferencia fallida') from exc
    finally:
        try:
            model_runtime.close()
        finally:
            inference_lock.release()
