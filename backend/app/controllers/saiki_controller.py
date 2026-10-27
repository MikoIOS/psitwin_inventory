import logging
import time
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.routing import APIRoute

from app.dependencies.dependencies import require_empresa
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
