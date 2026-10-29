# app/services/sensores/motor_alertas.py

from collections import deque
from dataclasses import (
    dataclass,
    field
)
from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple
)


# ============================================================
# MOTOR DE ALERTAS DE SENSORES (en memoria, sin I/O)
#
# Por dispositivo y parámetro:
#
#   NORMAL -> FUERA (sale del rango)
#          -> ALERTA (si sigue fuera duracion_s)
#          -> NORMAL (vuelve dentro CON MARGEN: se resuelve)
#
#   Si vuelve al rango antes de duracion_s: no hay alerta.
#
# Puerta: alerta si sigue abierta más de max_abierta_s;
#         se resuelve al cerrar. Aperturas por hora en
#         ventana móvil de 1 h (si está configurado).
# Conexión: SENSOR_SIN_DATOS tras 5 s sin mensajes.
#
# El motor solo emite Eventos; el servicio de monitoreo los
# persiste (colección alertas) y los difunde por WebSocket.
# El reloj es inyectable para las pruebas.
#
# ponytail: estado en memoria de un solo proceso; en la nube
# va a Redis (ver SENSORES.md, "Nube").
# ============================================================


from app.config.settings import settings
SIN_DATOS_S = settings.sensor_disconnect_seconds

VENTANA_APERTURAS_S = 3600

# parámetro de rango -> tipo de alerta
TIPOS_RANGO = {
    "t_int": "TEMPERATURA_FUERA_RANGO",
    "t_amb": "TEMPERATURA_FUERA_RANGO",
    "hum": "HUMEDAD_FUERA_RANGO",
    "corriente": "CORRIENTE_FUERA_RANGO",
}

# histéresis para resolver
MARGENES = {
    "t_int": 0.5,
    "t_amb": 0.5,
    "hum": 2.0,
    "corriente": 0.2,
}

DURACIONES_DEFAULT = {
    "t_int": 120,
    "t_amb": 300,
    "hum": 300,
    "corriente": 30,
}

MAX_ABIERTA_DEFAULT_S = 60

# críticas -> correo a la empresa
def es_critica(
    tipo: str,
    parametro: str
) -> bool:

    return (
        (tipo == "TEMPERATURA_FUERA_RANGO" and parametro == "t_int")
        or tipo in (
            "CORRIENTE_FUERA_RANGO",
            "SENSOR_SIN_DATOS"
        )
    )


@dataclass
class Evento:

    # ABIERTA | RESUELTA
    evento: str

    id_dispositivo: str

    tipo: str

    # t_int | t_amb | hum | corriente | puerta
    # | aperturas_hora | conexion
    parametro: str

    valor: Optional[float]

    limite: Optional[float]

    inicio: datetime

    fin: Optional[datetime] = None

    duracion_s: Optional[float] = None

    valor_extremo: Optional[float] = None


@dataclass
class _Estado:

    # NORMAL | FUERA | ALERTA
    fase: str = "NORMAL"

    inicio: Optional[datetime] = None

    extremo: Optional[float] = None

    limite: Optional[float] = None


@dataclass
class _Dispositivo:

    limites: Dict[str, Any]

    estados: Dict[str, _Estado] = field(
        default_factory=dict
    )

    puerta_desde: Optional[datetime] = None

    aperturas: deque = field(
        default_factory=deque
    )

    # None: nunca envió datos -> no se vigila la conexión
    ultimo_mensaje: Optional[datetime] = None


def _ahora() -> datetime:

    return datetime.now(
        timezone.utc
    )


class MotorAlertas:

    def __init__(
        self,
        reloj: Optional[Callable[[], datetime]] = None
    ):

        self.reloj = reloj or _ahora

        self.dispositivos: Dict[str, _Dispositivo] = {}


    # ============================================================
    # CONFIGURACION
    #
    # limites: ya "efectivos" (t_int heredado del rack y
    # defaults aplicados por el servicio).
    # vigilar_conexion: el dispositivo ya envió datos alguna
    # vez -> SENSOR_SIN_DATOS cuenta desde ahora.
    # ============================================================

    def configurar(
        self,
        id_dispositivo: str,
        limites: Dict[str, Any],
        vigilar_conexion: bool = False
    ) -> None:

        dispositivo = self.dispositivos.get(
            id_dispositivo
        )

        if dispositivo is None:

            dispositivo = _Dispositivo(
                limites=limites
            )

            self.dispositivos[id_dispositivo] = dispositivo

        dispositivo.limites = limites

        if (
            vigilar_conexion
            and dispositivo.ultimo_mensaje is None
        ):
            dispositivo.ultimo_mensaje = self.reloj()


    def quitar(
        self,
        id_dispositivo: str
    ) -> None:

        self.dispositivos.pop(
            id_dispositivo,
            None
        )


    # ============================================================
    # RESTAURAR ALERTA ABIERTA (al arrancar)
    #
    # Deja el parámetro en ALERTA para no duplicarla y
    # resolverla cuando corresponda.
    # ============================================================

    def restaurar(
        self,
        id_dispositivo: str,
        parametro: str,
        inicio: datetime,
        valor_extremo: Optional[float] = None,
        limite: Optional[float] = None
    ) -> None:

        dispositivo = self.dispositivos.get(
            id_dispositivo
        )

        if dispositivo is None:
            return

        dispositivo.estados[parametro] = _Estado(
            fase="ALERTA",
            inicio=inicio,
            extremo=valor_extremo,
            limite=limite
        )


    def alertas_abiertas(
        self,
        id_dispositivo: str
    ) -> List[str]:

        dispositivo = self.dispositivos.get(
            id_dispositivo
        )

        if dispositivo is None:
            return []

        return [
            parametro
            for parametro, estado in dispositivo.estados.items()
            if estado.fase == "ALERTA"
        ]


    def puerta_abierta_desde(
        self,
        id_dispositivo: str
    ) -> Optional[datetime]:

        dispositivo = self.dispositivos.get(
            id_dispositivo
        )

        return (
            dispositivo.puerta_desde
            if dispositivo
            else None
        )


    # ============================================================
    # PROCESAR UNA LECTURA
    #
    # lectura: {t_int, puerta, t_amb, hum, corriente}
    # (valores ya saneados; None = sin dato)
    # ============================================================

    def procesar(
        self,
        id_dispositivo: str,
        lectura: Dict[str, Any]
    ) -> List[Evento]:

        dispositivo = self.dispositivos.get(
            id_dispositivo
        )

        if dispositivo is None:
            return []

        ahora = self.reloj()

        dispositivo.ultimo_mensaje = ahora

        eventos: List[Evento] = []

        # --------------------------------------------------------
        # volvió a enviar datos
        # --------------------------------------------------------

        eventos += self._resolver_si_alerta(
            id_dispositivo,
            dispositivo,
            "conexion",
            ahora,
            valor=0
        )

        for parametro in TIPOS_RANGO:

            valor = lectura.get(parametro)

            if valor is None:
                continue

            eventos += self._rango(
                id_dispositivo,
                dispositivo,
                parametro,
                float(valor),
                ahora
            )

        puerta = lectura.get("puerta")

        if isinstance(puerta, bool):

            eventos += self._puerta(
                id_dispositivo,
                dispositivo,
                puerta,
                ahora
            )

        eventos += self._aperturas(
            id_dispositivo,
            dispositivo,
            ahora
        )

        return eventos


    # ============================================================
    # TICK (cada ~1 s)
    #
    # Conexión perdida y ventana de aperturas que caduca.
    # ============================================================

    def tick(self) -> List[Evento]:

        ahora = self.reloj()

        eventos: List[Evento] = []

        for id_dispositivo, dispositivo in self.dispositivos.items():

            eventos += self._aperturas(
                id_dispositivo,
                dispositivo,
                ahora
            )

            ultimo = dispositivo.ultimo_mensaje

            estado = dispositivo.estados.setdefault(
                "conexion",
                _Estado()
            )

            if (
                ultimo is not None
                and estado.fase != "ALERTA"
                and (ahora - ultimo).total_seconds() > SIN_DATOS_S
            ):

                estado.fase = "ALERTA"
                estado.inicio = ultimo
                estado.limite = SIN_DATOS_S

                eventos.append(
                    Evento(
                        evento="ABIERTA",
                        id_dispositivo=id_dispositivo,
                        tipo="SENSOR_SIN_DATOS",
                        parametro="conexion",
                        valor=round(
                            (ahora - ultimo).total_seconds(),
                            1
                        ),
                        limite=SIN_DATOS_S,
                        inicio=ultimo
                    )
                )

        return eventos


    # ============================================================
    # RANGOS (t_int, t_amb, hum, corriente)
    # ============================================================

    def _rango(
        self,
        id_dispositivo: str,
        dispositivo: _Dispositivo,
        parametro: str,
        valor: float,
        ahora: datetime
    ) -> List[Evento]:

        limites = dispositivo.limites.get(parametro) or {}

        minimo = limites.get("min")

        maximo = limites.get("max")

        estado = dispositivo.estados.setdefault(
            parametro,
            _Estado()
        )

        if minimo is None and maximo is None:

            # sin límites: no se vigila
            return self._resolver_si_alerta(
                id_dispositivo,
                dispositivo,
                parametro,
                ahora,
                valor
            )

        arriba = maximo is not None and valor > maximo

        abajo = minimo is not None and valor < minimo

        fuera = arriba or abajo

        if estado.fase == "NORMAL":

            if not fuera:
                return []

            estado.fase = "FUERA"
            estado.inicio = ahora
            estado.extremo = valor
            estado.limite = maximo if arriba else minimo

        if estado.fase == "FUERA":

            if not fuera:

                # volvió antes de duracion_s: sin alerta
                dispositivo.estados[parametro] = _Estado()

                return []

            estado.extremo = self._peor(
                estado,
                valor
            )

            duracion = limites.get(
                "duracion_s",
                DURACIONES_DEFAULT[parametro]
            )

            if (ahora - estado.inicio).total_seconds() < duracion:
                return []

            estado.fase = "ALERTA"

            return [
                Evento(
                    evento="ABIERTA",
                    id_dispositivo=id_dispositivo,
                    tipo=TIPOS_RANGO[parametro],
                    parametro=parametro,
                    valor=valor,
                    limite=estado.limite,
                    inicio=estado.inicio,
                    valor_extremo=estado.extremo
                )
            ]

        # ALERTA
        if fuera:

            if estado.limite is None:
                estado.limite = maximo if arriba else minimo

            estado.extremo = self._peor(
                estado,
                valor
            )

            return []

        margen = MARGENES[parametro]

        if minimo is not None and maximo is not None:
            margen = min(
                margen,
                (maximo - minimo) / 2
            )

        dentro_con_margen = (
            (minimo is None or valor >= minimo + margen)
            and
            (maximo is None or valor <= maximo - margen)
        )

        if not dentro_con_margen:
            return []

        return self._resolver_si_alerta(
            id_dispositivo,
            dispositivo,
            parametro,
            ahora,
            valor
        )


    @staticmethod
    def _peor(
        estado: _Estado,
        valor: float
    ) -> float:

        if estado.extremo is None:
            return valor

        if (
            estado.limite is not None
            and estado.extremo < estado.limite
        ):
            # episodio por debajo del mínimo
            return min(estado.extremo, valor)

        return max(estado.extremo, valor)


    # ============================================================
    # PUERTA
    # ============================================================

    def _puerta(
        self,
        id_dispositivo: str,
        dispositivo: _Dispositivo,
        abierta: bool,
        ahora: datetime
    ) -> List[Evento]:

        estado = dispositivo.estados.setdefault(
            "puerta",
            _Estado()
        )

        if not abierta:

            dispositivo.puerta_desde = None

            return self._resolver_si_alerta(
                id_dispositivo,
                dispositivo,
                "puerta",
                ahora,
                valor=0
            )

        if dispositivo.puerta_desde is None:

            dispositivo.puerta_desde = ahora

            dispositivo.aperturas.append(ahora)

        if estado.fase == "ALERTA":
            return []

        maximo = (
            dispositivo.limites.get("puerta") or {}
        ).get(
            "max_abierta_s",
            MAX_ABIERTA_DEFAULT_S
        )

        abierta_s = (
            ahora - dispositivo.puerta_desde
        ).total_seconds()

        if abierta_s <= maximo:
            return []

        estado.fase = "ALERTA"
        estado.inicio = dispositivo.puerta_desde
        estado.limite = maximo

        return [
            Evento(
                evento="ABIERTA",
                id_dispositivo=id_dispositivo,
                tipo="PUERTA_ABIERTA",
                parametro="puerta",
                valor=round(abierta_s, 1),
                limite=maximo,
                inicio=dispositivo.puerta_desde
            )
        ]


    def _aperturas(
        self,
        id_dispositivo: str,
        dispositivo: _Dispositivo,
        ahora: datetime
    ) -> List[Evento]:

        corte = ahora - timedelta(
            seconds=VENTANA_APERTURAS_S
        )

        while (
            dispositivo.aperturas
            and dispositivo.aperturas[0] < corte
        ):
            dispositivo.aperturas.popleft()

        maximo = (
            dispositivo.limites.get("puerta") or {}
        ).get("max_aperturas_hora")

        estado = dispositivo.estados.setdefault(
            "aperturas_hora",
            _Estado()
        )

        cantidad = len(dispositivo.aperturas)

        if maximo is None or cantidad <= maximo:

            return self._resolver_si_alerta(
                id_dispositivo,
                dispositivo,
                "aperturas_hora",
                ahora,
                valor=cantidad
            )

        if estado.fase == "ALERTA":

            estado.extremo = max(
                estado.extremo or 0,
                cantidad
            )

            return []

        estado.fase = "ALERTA"
        estado.inicio = ahora
        estado.limite = maximo
        estado.extremo = cantidad

        return [
            Evento(
                evento="ABIERTA",
                id_dispositivo=id_dispositivo,
                tipo="APERTURAS_EXCESIVAS",
                parametro="aperturas_hora",
                valor=cantidad,
                limite=maximo,
                inicio=ahora,
                valor_extremo=cantidad
            )
        ]


    # ============================================================
    # RESOLVER
    # ============================================================

    def _resolver_si_alerta(
        self,
        id_dispositivo: str,
        dispositivo: _Dispositivo,
        parametro: str,
        ahora: datetime,
        valor: Optional[float] = None
    ) -> List[Evento]:

        estado = dispositivo.estados.get(
            parametro
        )

        if estado is None or estado.fase != "ALERTA":

            if estado is not None:
                dispositivo.estados[parametro] = _Estado()

            return []

        dispositivo.estados[parametro] = _Estado()

        tipo = {
            "puerta": "PUERTA_ABIERTA",
            "aperturas_hora": "APERTURAS_EXCESIVAS",
            "conexion": "SENSOR_SIN_DATOS",
        }.get(
            parametro,
            TIPOS_RANGO.get(parametro)
        )

        inicio = estado.inicio or ahora

        return [
            Evento(
                evento="RESUELTA",
                id_dispositivo=id_dispositivo,
                tipo=tipo,
                parametro=parametro,
                valor=valor,
                limite=estado.limite,
                inicio=inicio,
                fin=ahora,
                duracion_s=round(
                    (ahora - inicio).total_seconds(),
                    1
                ),
                valor_extremo=estado.extremo
            )
        ]
