# app/services/sensores/monitoreo_service.py

import asyncio
import hashlib
import hmac
import json
import time

from dataclasses import (
    dataclass,
    field
)
from datetime import (
    datetime,
    timezone
)
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional
)
from uuid import uuid4

import aiomqtt

from app.config.settings import (
    settings
)

from app.repositories.alerta_repository import (
    AlertaRepository
)

from app.repositories.dispositivo_repository import (
    DispositivoRepository
)

from app.repositories.lectura_repository import (
    CAMPOS_NUMERICOS,
    LecturaRepository
)

from app.repositories.rack_repository import (
    RackRepository
)

from app.services.notification_service import (
    NotificationService
)

from app.services.sensores.limites import (
    limites_efectivos
)

from app.services.sensores.motor_alertas import (
    SIN_DATOS_S,
    Evento,
    MotorAlertas,
    es_critica
)


# ============================================================
# MONITOREO DE SENSORES (un proceso, estado en memoria)
#
# MQTT (aiomqtt) -> validar token -> sanear valores
#   -> buffer (escritura en bloque cada 1 s: lecturas +
#      lecturas_minuto + ultima_lectura_ts)
#   -> motor de alertas -> colección alertas + WebSocket
#   -> WebSocket: lectura (máx. 1/s por dispositivo)
#
# Si el broker no está, la API sigue funcionando y el
# consumidor reintenta con espera creciente (1 s .. 30 s).
# ============================================================


TEMA_LECTURAS = "psitwin/dispositivos/+/lecturas"

# Fuera de estos rangos el valor se trata como null
RANGOS_FISICOS = {
    "t_int": (-60.0, 100.0),
    "t_amb": (-60.0, 100.0),
    "hum": (0.0, 100.0),
    "corriente": (0.0, 200.0),
}

TITULOS = {
    "TEMPERATURA_FUERA_RANGO": "Temperatura fuera de rango",
    "HUMEDAD_FUERA_RANGO": "Humedad fuera de rango",
    "CORRIENTE_FUERA_RANGO": "Corriente fuera de rango",
    "PUERTA_ABIERTA": "Puerta abierta demasiado tiempo",
    "APERTURAS_EXCESIVAS": "Aperturas de puerta excesivas",
    "SENSOR_SIN_DATOS": "Sensor sin datos",
}

UNIDADES = {
    "t_int": "°C",
    "t_amb": "°C",
    "hum": "%",
    "corriente": "A",
    "puerta": "s",
    "aperturas_hora": "aperturas/h",
    "conexion": "s",
}


def hash_token(
    token: str
) -> str:

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def _ahora() -> datetime:

    return datetime.now(
        timezone.utc
    )


def _parsear_ts(
    valor: Any
) -> Optional[datetime]:

    if not isinstance(valor, str):
        return None

    try:

        ts = datetime.fromisoformat(
            valor.replace("Z", "+00:00")
        )

    except ValueError:

        return None

    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    return ts


def sanear(
    data: Dict[str, Any]
) -> Dict[str, Any]:

    lectura: Dict[str, Any] = {}

    for campo, (minimo, maximo) in RANGOS_FISICOS.items():

        valor = data.get(campo)

        if (
            isinstance(valor, (int, float))
            and not isinstance(valor, bool)
            and minimo <= valor <= maximo
        ):
            lectura[campo] = float(valor)
        else:
            lectura[campo] = None

    puerta = data.get("puerta")

    lectura["puerta"] = (
        puerta
        if isinstance(puerta, bool)
        else None
    )

    return lectura


# eq=False: hashable por identidad (se guarda en un set)
@dataclass(eq=False)
class Suscriptor:

    # filtro(dispositivo) -> bool
    filtro: Callable[[Dict[str, Any]], bool]

    cola: asyncio.Queue = field(
        default_factory=lambda: asyncio.Queue(
            maxsize=500
        )
    )


class MonitoreoService:

    def __init__(self):

        self.motor = MotorAlertas()

        self.notificaciones = NotificationService()

        # id -> documento del dispositivo (con token_hash)
        self.dispositivos: Dict[str, Dict[str, Any]] = {}

        # id -> {ts, t_int, puerta, t_amb, hum, corriente}
        self.ultima: Dict[str, Dict[str, Any]] = {}

        # id -> hora de llegada del último mensaje válido
        self.ultimo_arribo: Dict[str, datetime] = {}

        # id -> time.monotonic() del último envío por WS
        self.ultimo_ws: Dict[str, float] = {}

        # (id, parametro) -> id_alerta abierta
        self.abiertas: Dict[tuple, str] = {}

        self.buffer: List[Dict[str, Any]] = []

        self.minutos: Dict[tuple, Dict[str, Any]] = {}

        self.suscriptores: set = set()

        self.tareas: List[asyncio.Task] = []

        self.mqtt_conectado = False

        self.descartados = 0


    # ============================================================
    # CICLO DE VIDA (lifespan)
    # ============================================================

    async def iniciar(self) -> None:

        try:

            await LecturaRepository.asegurar_colecciones()

            await self.cargar_dispositivos()

            await self._restaurar_alertas()

        except Exception as exc:

            print("Monitoreo: no se pudo inicializar:", exc, flush=True)

        self.tareas = [
            asyncio.create_task(self._bucle_escritura()),
            asyncio.create_task(self._bucle_tick()),
        ]

        if settings.mqtt_enabled:
            self.tareas.append(
                asyncio.create_task(self._consumir_mqtt())
            )


    async def detener(self) -> None:

        for tarea in self.tareas:
            tarea.cancel()

        await asyncio.gather(
            *self.tareas,
            return_exceptions=True
        )

        self.tareas = []

        try:
            await self._escribir()
        except Exception as exc:
            print("Monitoreo: escritura final fallida:", exc, flush=True)


    # ============================================================
    # DISPOSITIVOS EN MEMORIA
    # ============================================================

    async def cargar_dispositivos(self) -> None:

        for documento in await DispositivoRepository.listar(
            {"activo": True}
        ):
            await self._registrar(documento)


    async def recargar(
        self,
        id_dispositivo: str
    ) -> None:

        documento = await DispositivoRepository.obtener_por_id(
            id_dispositivo
        )

        if not documento or not documento.get("activo"):

            self.quitar(id_dispositivo)

            return

        await self._registrar(documento)

        # alertas abiertas de este dispositivo (p. ej. al
        # reactivarlo) para no duplicarlas
        for alerta in await AlertaRepository().listar_abiertas_sensores(
            [id_dispositivo]
        ):
            self._restaurar(alerta)


    def quitar(
        self,
        id_dispositivo: str
    ) -> None:

        self.dispositivos.pop(id_dispositivo, None)

        self.motor.quitar(id_dispositivo)


    async def _registrar(
        self,
        documento: Dict[str, Any]
    ) -> None:

        rack = (
            await RackRepository.obtener_por_id(
                documento["id_rack"]
            )
            if documento.get("id_rack")
            else None
        )

        self.dispositivos[documento["id_dispositivo"]] = documento

        self.motor.configurar(
            documento["id_dispositivo"],
            limites_efectivos(
                documento.get("limites"),
                rack
            ),
            # solo se vigila la conexión de equipos que ya
            # enviaron datos alguna vez
            vigilar_conexion=bool(
                documento.get("ultima_lectura_ts")
            )
        )


    async def _restaurar_alertas(self) -> None:

        for alerta in await AlertaRepository().listar_abiertas_sensores():
            self._restaurar(alerta)


    def _restaurar(
        self,
        alerta: Dict[str, Any]
    ) -> None:

        clave = (
            alerta.get("id_dispositivo"),
            alerta.get("parametro")
        )

        if clave[0] not in self.dispositivos:
            return

        inicio = alerta.get("inicio") or alerta.get("fecha_creacion")

        if inicio is not None and inicio.tzinfo is None:
            inicio = inicio.replace(tzinfo=timezone.utc)

        self.motor.restaurar(
            clave[0],
            clave[1],
            inicio or _ahora(),
            valor_extremo=alerta.get("valor_extremo"),
            limite=alerta.get("limite")
        )

        self.abiertas[clave] = alerta["id_alerta"]


    # ============================================================
    # CONSUMIDOR MQTT
    # ============================================================

    async def _consumir_mqtt(self) -> None:

        espera = 1

        while True:

            try:

                async with aiomqtt.Client(
                    hostname=settings.mqtt_host,
                    port=settings.mqtt_port,
                    username=settings.mqtt_user,
                    password=settings.mqtt_password
                ) as cliente:

                    await cliente.subscribe(TEMA_LECTURAS)

                    self.mqtt_conectado = True

                    espera = 1

                    print("Monitoreo: conectado al broker MQTT", flush=True)

                    async for mensaje in cliente.messages:

                        try:

                            await self.procesar_mensaje(
                                str(mensaje.topic),
                                mensaje.payload
                            )

                        except Exception as exc:

                            print("Monitoreo: mensaje no procesado:", exc, flush=True)

            except asyncio.CancelledError:

                raise

            except Exception as exc:

                if self.mqtt_conectado or espera == 1:
                    print(
                        "Monitoreo: broker MQTT no disponible "
                        f"({exc}); reintento en {espera} s",
                        flush=True
                    )

                self.mqtt_conectado = False

                await asyncio.sleep(espera)

                espera = min(espera * 2, 30)


    # ============================================================
    # PROCESAR UN MENSAJE
    #
    # Tema: psitwin/dispositivos/{id}/lecturas
    # Descarta: dispositivo desconocido / inactivo, token
    # inválido, JSON inválido.
    # ============================================================

    async def procesar_mensaje(
        self,
        tema: str,
        payload: Any
    ) -> bool:

        partes = tema.split("/")

        if len(partes) != 4 or partes[3] != "lecturas":
            return False

        id_dispositivo = partes[2]

        dispositivo = self.dispositivos.get(
            id_dispositivo
        )

        try:
            data = json.loads(payload)
        except (TypeError, ValueError):
            data = None

        token = (
            data.get("token")
            if isinstance(data, dict)
            else None
        )

        if (
            dispositivo is None
            or not isinstance(token, str)
            or not hmac.compare_digest(
                hash_token(token),
                dispositivo.get("token_hash", "")
            )
        ):
            self.descartados += 1
            return False

        llegada = _ahora()

        ts = _parsear_ts(data.get("ts")) or llegada

        lectura = sanear(data)

        self.ultima[id_dispositivo] = {
            "ts": ts,
            **lectura
        }

        self.ultimo_arribo[id_dispositivo] = llegada

        self._acumular(
            dispositivo,
            ts,
            lectura
        )

        await self._manejar_eventos(
            self.motor.procesar(
                id_dispositivo,
                lectura
            )
        )

        # ------------------------------------------------------------
        # WebSocket: como máximo 1 lectura por segundo
        # ------------------------------------------------------------

        ahora = time.monotonic()

        if ahora - self.ultimo_ws.get(id_dispositivo, 0) >= 1.0:

            self.ultimo_ws[id_dispositivo] = ahora

            self._difundir(
                dispositivo,
                {
                    "tipo": "lectura",
                    "id_dispositivo": id_dispositivo,
                    "ts": ts.isoformat(),
                    **lectura
                }
            )

        return True


    # ============================================================
    # ESCRITURA EN BLOQUE (cada 1 s)
    # ============================================================

    def _acumular(
        self,
        dispositivo: Dict[str, Any],
        ts: datetime,
        lectura: Dict[str, Any]
    ) -> None:

        id_dispositivo = dispositivo["id_dispositivo"]

        self.buffer.append(
            {
                "ts": ts,
                "meta": {
                    "id_dispositivo": id_dispositivo,
                    "id_empresa": dispositivo["id_empresa"]
                },
                **lectura
            }
        )

        minuto = ts.replace(
            second=0,
            microsecond=0
        )

        acumulado = self.minutos.setdefault(
            (id_dispositivo, minuto),
            {
                "id_empresa": dispositivo["id_empresa"],
                "campos": {},
                "puerta": {
                    "abiertas": 0,
                    "n": 0
                }
            }
        )

        for campo in CAMPOS_NUMERICOS:

            valor = lectura.get(campo)

            if valor is None:
                continue

            actual = acumulado["campos"].get(campo)

            if actual is None:

                acumulado["campos"][campo] = {
                    "min": valor,
                    "max": valor,
                    "suma": valor,
                    "n": 1
                }

            else:

                actual["min"] = min(actual["min"], valor)
                actual["max"] = max(actual["max"], valor)
                actual["suma"] += valor
                actual["n"] += 1

        if lectura.get("puerta") is not None:

            acumulado["puerta"]["n"] += 1

            if lectura["puerta"]:
                acumulado["puerta"]["abiertas"] += 1


    async def _escribir(self) -> None:

        if not self.buffer:
            return

        lecturas, self.buffer = self.buffer, []

        minutos, self.minutos = self.minutos, {}

        ultimas: Dict[str, datetime] = {}

        for documento in lecturas:
            ultimas[documento["meta"]["id_dispositivo"]] = documento["ts"]

        await LecturaRepository.insertar_lecturas(lecturas)

        await LecturaRepository.acumular_minutos(minutos)

        await DispositivoRepository.actualizar_ultimas_lecturas(ultimas)

        # a partir de ahora se vigila su conexión
        for id_dispositivo, ts in ultimas.items():

            documento = self.dispositivos.get(id_dispositivo)

            if documento is not None:
                documento["ultima_lectura_ts"] = ts


    async def _bucle_escritura(self) -> None:

        while True:

            await asyncio.sleep(1)

            try:

                await self._escribir()

            except Exception as exc:

                # ponytail: si Mongo no responde se pierde ese
                # segundo de lecturas (el motor sigue en memoria)
                print("Monitoreo: escritura de lecturas fallida:", exc, flush=True)


    async def _bucle_tick(self) -> None:

        while True:

            await asyncio.sleep(1)

            try:

                await self._manejar_eventos(
                    self.motor.tick()
                )

            except Exception as exc:

                print("Monitoreo: tick fallido:", exc, flush=True)


    # ============================================================
    # EVENTOS DEL MOTOR -> alertas + WebSocket + correo
    # ============================================================

    async def _manejar_eventos(
        self,
        eventos: List[Evento]
    ) -> None:

        for evento in eventos:

            dispositivo = self.dispositivos.get(
                evento.id_dispositivo
            )

            if dispositivo is None:
                continue

            clave = (
                evento.id_dispositivo,
                evento.parametro
            )

            if evento.evento == "ABIERTA":

                alerta = await AlertaRepository().crear(
                    self._documento_alerta(
                        dispositivo,
                        evento
                    )
                )

                self.abiertas[clave] = alerta["id_alerta"]

                if es_critica(evento.tipo, evento.parametro):
                    asyncio.create_task(
                        self._avisar_por_correo(
                            dispositivo,
                            alerta
                        )
                    )

            else:

                id_alerta = self.abiertas.pop(
                    clave,
                    None
                )

                if id_alerta is None:
                    continue

                ahora = evento.fin or _ahora()

                alerta = await AlertaRepository().actualizar(
                    id_alerta,
                    {
                        "estado": "RESUELTA",
                        "fin": evento.fin,
                        "duracion_s": evento.duracion_s,
                        "valor_extremo": evento.valor_extremo,
                        "fecha_resolucion": ahora,
                        "fecha_actualizacion": ahora
                    }
                )

                if alerta is None:
                    continue

            self._difundir(
                dispositivo,
                {
                    "tipo": "alerta",
                    "evento": evento.evento,
                    "alerta": _serializable(alerta)
                }
            )


    @staticmethod
    def _documento_alerta(
        dispositivo: Dict[str, Any],
        evento: Evento
    ) -> Dict[str, Any]:

        ahora = _ahora()

        unidad = UNIDADES.get(evento.parametro, "")

        if evento.parametro in ("puerta", "conexion"):
            detalle = (
                f"{evento.valor} {unidad} "
                f"(máximo {evento.limite} {unidad})"
            )
        elif evento.parametro == "aperturas_hora":
            detalle = (
                f"{evento.valor} aperturas en la última hora "
                f"(máximo {evento.limite})"
            )
        else:
            detalle = (
                f"{evento.parametro} = {evento.valor} {unidad} "
                f"(límite {evento.limite} {unidad})"
            )

        return {
            "id_alerta": str(uuid4()),
            "origen": "SENSOR",
            "id_empresa": dispositivo["id_empresa"],
            "id_almacen": dispositivo["id_almacen"],
            "id_zona": dispositivo.get("id_zona"),
            "id_rack": dispositivo.get("id_rack"),
            "id_dispositivo": dispositivo["id_dispositivo"],
            "id_inventario": None,
            "id_producto": None,
            "tipo_alerta": evento.tipo,
            "nivel_riesgo": (
                "CRITICO"
                if es_critica(evento.tipo, evento.parametro)
                else "ALTO"
            ),
            "titulo": (
                f"{TITULOS[evento.tipo]}: "
                f"{dispositivo['nombre']}"
            ),
            "mensaje": (
                f"{dispositivo['nombre']}: {detalle}, "
                f"desde {evento.inicio.isoformat(timespec='seconds')}"
            ),
            "parametro": evento.parametro,
            "valor": evento.valor,
            "limite": evento.limite,
            "inicio": evento.inicio,
            "fin": None,
            "duracion_s": None,
            "valor_extremo": evento.valor_extremo,
            "stock_actual": None,
            "estado": "ACTIVA",
            "fecha_creacion": ahora,
            "fecha_actualizacion": ahora,
            "fecha_resolucion": None
        }


    async def _avisar_por_correo(
        self,
        dispositivo: Dict[str, Any],
        alerta: Dict[str, Any]
    ) -> None:

        # Best effort: nunca bloquea ni rompe el consumidor.
        try:

            await self.notificaciones.notify_owner(
                f"SENSOR:{alerta['id_alerta']}",
                dispositivo["id_empresa"],
                f"[PsiTwin] {alerta['titulo']}",
                alerta["mensaje"]
            )

        except Exception as exc:

            print("Monitoreo: aviso por correo fallido:", exc, flush=True)


    # ============================================================
    # ESTADO EN VIVO
    # ============================================================

    def estado(
        self,
        id_dispositivo: str,
        alertas_abiertas: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:

        llegada = self.ultimo_arribo.get(id_dispositivo)

        return {
            "conectado": (
                llegada is not None
                and (_ahora() - llegada).total_seconds() <= SIN_DATOS_S
            ),
            "ultima_lectura": self.ultima.get(id_dispositivo),
            "puerta_abierta_desde": self.motor.puerta_abierta_desde(
                id_dispositivo
            ),
            "alertas_abiertas": alertas_abiertas or []
        }


    # ============================================================
    # WEBSOCKET (difusión)
    # ============================================================

    def suscribir(
        self,
        filtro: Callable[[Dict[str, Any]], bool]
    ) -> Suscriptor:

        suscriptor = Suscriptor(filtro=filtro)

        self.suscriptores.add(suscriptor)

        return suscriptor


    def desuscribir(
        self,
        suscriptor: Suscriptor
    ) -> None:

        self.suscriptores.discard(suscriptor)


    def _difundir(
        self,
        dispositivo: Dict[str, Any],
        mensaje: Dict[str, Any]
    ) -> None:

        for suscriptor in list(self.suscriptores):

            if not suscriptor.filtro(dispositivo):
                continue

            try:
                suscriptor.cola.put_nowait(mensaje)
            except asyncio.QueueFull:
                # cliente lento: se pierde ese mensaje
                pass


def _serializable(
    documento: Dict[str, Any]
) -> Dict[str, Any]:

    return {
        clave: (
            valor.isoformat()
            if isinstance(valor, datetime)
            else valor
        )
        for clave, valor in documento.items()
        if clave != "_id"
    }


# Instancia única del proceso
monitoreo = MonitoreoService()
