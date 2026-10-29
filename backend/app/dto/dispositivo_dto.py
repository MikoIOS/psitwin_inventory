from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    model_validator
)

from app.dto.alerta_dto import (
    AlertaResponse
)


# ============================================================
# LIMITES
#
# Sin min/max -> el parámetro no se vigila.
# t_int sin min/max y con id_rack -> se usan
# temperatura_min / temperatura_max del rack.
# duracion_s por defecto: t_int 120, t_amb 300, hum 300,
# corriente 30. puerta.max_abierta_s por defecto 60.
# ============================================================

class LimiteRango(BaseModel):

    min: Optional[float] = None

    max: Optional[float] = None

    duracion_s: Optional[int] = Field(
        default=None,
        ge=0
    )

    @model_validator(mode="after")
    def validar(self):

        if (
            self.min is not None
            and self.max is not None
            and self.min > self.max
        ):
            raise ValueError(
                "min no puede ser mayor que max"
            )

        return self


class LimitePuerta(BaseModel):

    max_abierta_s: int = Field(
        default=60,
        ge=1
    )

    max_aperturas_hora: Optional[int] = Field(
        default=None,
        ge=1
    )


class Limites(BaseModel):

    t_int: Optional[LimiteRango] = None

    t_amb: Optional[LimiteRango] = None

    hum: Optional[LimiteRango] = None

    corriente: Optional[LimiteRango] = None

    puerta: Optional[LimitePuerta] = None


# ============================================================
# CREAR / EDITAR (EMPRESA)
# ============================================================

class DispositivoCreate(BaseModel):

    id_almacen: str

    id_zona: str

    id_rack: Optional[str] = None
    id_nivel: Optional[str] = None

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    limites: Limites = Limites()


class DispositivoUpdate(BaseModel):

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    # null -> sin rack
    id_rack: Optional[str] = None
    id_nivel: Optional[str] = None

    activo: Optional[bool] = None

    limites: Optional[Limites] = None


# ============================================================
# ESTADO EN VIVO
# ============================================================

class LecturaActual(BaseModel):

    ts: datetime

    t_int: Optional[float] = None

    puerta: Optional[bool] = None

    t_amb: Optional[float] = None

    hum: Optional[float] = None

    corriente: Optional[float] = None


class EstadoDispositivo(BaseModel):
    max_edad_lectura_s: float = 5

    # recibió datos en los últimos 5 s
    conectado: bool = False

    ultima_lectura: Optional[LecturaActual] = None

    puerta_abierta_desde: Optional[datetime] = None

    alertas_abiertas: list[AlertaResponse] = []


class DispositivoResponse(BaseModel):

    parametros_disponibles: list[str] = []

    id_dispositivo: str

    id_empresa: str

    id_almacen: str

    id_zona: str

    id_rack: Optional[str] = None
    id_nivel: Optional[str] = None

    nombre: str

    activo: bool

    # tal como se configuraron
    limites: dict = {}

    # los que aplica el motor (rack + defaults)
    limites_efectivos: dict = {}

    ultima_lectura_ts: Optional[datetime] = None

    estado: EstadoDispositivo = EstadoDispositivo()

    fecha_creacion: datetime

    fecha_actualizacion: datetime


class DispositivoConToken(DispositivoResponse):

    # En claro UNA sola vez (al crear o regenerar).
    token: str


class TokenResponse(BaseModel):

    token: str


# ============================================================
# LECTURAS
#
# resolucion "cruda": puntos = [{ts, t_int, puerta, t_amb,
#                                hum, corriente}]
# resolucion "minuto": puntos = [{ts, t_int: {min, max, prom},
#                                 t_amb, hum, corriente: ídem,
#                                 puerta: {fraccion_abierta}}]
# ============================================================

class LecturasResponse(BaseModel):

    pagina: int = 1
    limite: int = 2000
    hay_mas: bool = False
    resumen: dict = {}

    id_dispositivo: str

    desde: datetime

    hasta: datetime

    resolucion: str

    puntos: list[dict]
