import asyncio
import json

from typing import (
    Optional
)

from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect
)

from fastapi.security import (
    HTTPAuthorizationCredentials
)

from app.dependencies.dependencies import (
    get_current_user
)

from app.services.dispositivo_service import (
    DispositivoService
)

from app.services.sensores.monitoreo_service import (
    monitoreo
)


# ============================================================
# TIEMPO REAL: GET /api/v1/ws/monitoreo?token=<JWT>&id_zona=
#
# EMPRESA u OPERARIO (operario: solo su almacén).
# Cierra con 4401 (token inválido / sin token) o 4403
# (rol no permitido o contraseña temporal sin cambiar).
#
# Mensajes:
#   {"tipo":"snapshot","dispositivos":[...]}
#   {"tipo":"lectura", ...}            (máx. 1/s por dispositivo)
#   {"tipo":"alerta","evento":...,"alerta":{...}}
# ============================================================

router = APIRouter(
    tags=["Dispositivos / Sensores"]
)


@router.websocket(
    "/ws/monitoreo"
)
async def ws_monitoreo(
    websocket: WebSocket,
    token: Optional[str] = None,
    id_zona: Optional[str] = None
):

    try:

        user = await get_current_user(
            HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=token or ""
            )
        )

    except HTTPException as exc:

        # se acepta para poder enviar el código de cierre
        # (cerrar antes de aceptar = HTTP 403 genérico)
        await websocket.accept()

        await websocket.close(
            code=4401 if exc.status_code == 401 else 4403,
            reason=str(exc.detail)
        )

        return

    if (
        user.rol not in ("EMPRESA", "OPERARIO")
        or user.debe_cambiar_password
    ):

        await websocket.accept()

        await websocket.close(
            code=4403,
            reason="Su rol no puede usar el monitoreo"
        )

        return

    await websocket.accept()

    def filtro(dispositivo) -> bool:

        return (
            dispositivo.get("id_empresa") == user.id_empresa
            and (
                not user.es_operario
                or dispositivo.get("id_almacen") == user.id_almacen
            )
            and (
                not id_zona
                or dispositivo.get("id_zona") == id_zona
            )
        )

    suscriptor = monitoreo.suscribir(
        filtro
    )

    async def enviar(mensaje) -> None:

        await websocket.send_text(
            json.dumps(
                mensaje,
                default=str
            )
        )

    async def escuchar_cliente() -> None:

        # detecta el cierre del cliente
        while True:
            await websocket.receive_text()

    lector = asyncio.create_task(
        escuchar_cliente()
    )

    try:

        dispositivos = await DispositivoService.listar(
            user,
            id_zona
        )

        await enviar(
            {
                "tipo": "snapshot",
                "dispositivos": [
                    {
                        "id_dispositivo": dispositivo["id_dispositivo"],
                        "nombre": dispositivo["nombre"],
                        "id_zona": dispositivo["id_zona"],
                        "id_rack": dispositivo.get("id_rack"),
                        "activo": dispositivo["activo"],
                        "estado": dispositivo["estado"]
                    }
                    for dispositivo in dispositivos
                ]
            }
        )

        while not lector.done():

            obtener = asyncio.create_task(
                suscriptor.cola.get()
            )

            hecho, _ = await asyncio.wait(
                {obtener, lector},
                return_when=asyncio.FIRST_COMPLETED
            )

            if obtener in hecho:
                await enviar(obtener.result())
            else:
                obtener.cancel()

    except (WebSocketDisconnect, RuntimeError):

        pass

    finally:

        lector.cancel()

        if lector.done() and not lector.cancelled():
            lector.exception()

        monitoreo.desuscribir(
            suscriptor
        )
