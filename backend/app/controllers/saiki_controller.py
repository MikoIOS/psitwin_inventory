import logging
import time
import asyncio
import json
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from app.services.saiki_progress import sink, report
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.routing import APIRoute

from app.dependencies.dependencies import require_empresa_u_operario as require_empresa
from app.dto.auth_dto import UsuarioActual
from app.dto.saiki_dto import SaikiAskRequest, SaikiAskResponse
from app.services.saiki_service import SaikiService


logger = logging.getLogger(__name__)


class MeasuredSaikiRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def measured(request: Request):
            started = time.perf_counter()
            request_id = uuid4().hex
            request.state.saiki_request_id = request_id
            logger.info("saiki_endpoint_start request_id=%s path=%s revision=%s", request_id, request.url.path, service._code_revision())
            try:
                response = await handler(request)
                response.headers["X-Saiki-Request-ID"] = request_id
                response.headers["X-Saiki-Revision"] = service._code_revision()
                return response
            finally:
                logger.info("saiki_endpoint_complete request_id=%s path=%s duration_ms=%.3f", request_id, request.url.path, (time.perf_counter() - started) * 1000)

        return measured


router = APIRouter(
    prefix="/saiki",
    tags=["Saiki"],
    dependencies=[Depends(require_empresa)],
    route_class=MeasuredSaikiRoute,
)
service = SaikiService()

@router.post('/events', summary='Consulta cancelable con progreso')
async def events(data: SaikiAskRequest, request: Request, user: UsuarioActual = Depends(require_empresa)):
    async def stream():
        queue = asyncio.Queue()
        async def run():
            token = sink.set(queue.put_nowait)
            try:
                report('thinking', 'Pensando')
                result = await service.ask(data, user, request_id=request.state.saiki_request_id)
                await queue.put({'type': 'result', 'result': SaikiAskResponse(**result).model_dump(mode='json')})
            except HTTPException as exc:
                await queue.put({'type': 'error', 'status': exc.status_code, 'detail': exc.detail})
            except asyncio.CancelledError:
                logger.info('saiki_cancelled request_id=%s', request.state.saiki_request_id)
                raise
            except Exception:
                logger.exception('saiki_stream_failed request_id=%s', request.state.saiki_request_id)
                await queue.put({'type': 'error', 'status': 503, 'detail': 'No fue posible consultar la información. Puedes reintentar.'})
            finally:
                sink.reset(token)
        task = asyncio.create_task(run())
        timeout = service.settings.saiki_idle_timeout_seconds
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=timeout)
                except TimeoutError:
                    yield json.dumps({'type': 'error', 'status': 504, 'detail': 'La consulta dejó de responder. Puedes reintentar.'}) + '\n'
                    break
                if event['type'] == 'progress':
                    timeout = event['timeout_ms'] / 1000 if event.get('timeout_ms') else service.settings.saiki_request_timeout_seconds if event.get('long') else service.settings.saiki_idle_timeout_seconds
                    event['timeout_ms'] = round(timeout * 1000)
                    # Expose useful user-facing states, not internal tool identifiers.
                    event['detail'] = {'thinking': 'Pensando', 'consulting': 'Consultando información', 'generating': 'Generando respuesta'}.get(event['phase'], 'Preparando respuesta')
                yield json.dumps(event, ensure_ascii=False) + '\n'
                if event['type'] in {'result', 'error'}:
                    break
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    return StreamingResponse(stream(), media_type='application/x-ndjson', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})


@router.get("/health", summary="Comprobar disponibilidad de Ollama y Saiki")
async def health():
    return await service.health()


@router.post(
    "/ask",
    response_model=SaikiAskResponse,
    summary="Resolver una consulta operacional con datos de PsiTwin",
)
async def ask(
    data: SaikiAskRequest,
    request: Request,
    user: UsuarioActual = Depends(require_empresa),
):
    return await service.ask(data, user, request_id=request.state.saiki_request_id)


@router.post(
    "/chat",
    response_model=SaikiAskResponse,
    summary="Alias de consulta operacional de Saiki",
)
async def chat(
    data: SaikiAskRequest,
    request: Request,
    user: UsuarioActual = Depends(require_empresa),
):
    return await service.ask(data, user, request_id=request.state.saiki_request_id)
