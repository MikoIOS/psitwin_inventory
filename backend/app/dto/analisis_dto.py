from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class DemandPoint(BaseModel):
    fecha: date
    cantidad: float = Field(ge=0)


class ForecastPoint(DemandPoint):
    q10: float | None = None
    q50: float | None = None
    q90: float | None = None


class HorizonTotal(BaseModel):
    horizonte_dias: Literal[1, 7, 30, 90]
    demanda_acumulada: float = Field(ge=0)
    demanda_del_dia: float = Field(ge=0)


class DemandAnalysis(BaseModel):
    fuente_demanda: str = 'SALIDAS'
    unidad: str | None = None
    model_config = ConfigDict(validate_assignment=True)
    estado: Literal['DISPONIBLE', 'CALCULANDO', 'SIN_HISTORIAL', 'HISTORIAL_INSUFICIENTE', 'MODELO_NO_DISPONIBLE', 'ERROR_MODELO']
    id_empresa: str
    id_almacen: str
    id_producto: str
    series_id: str
    modelo: str = 'WeightedEnsemble'
    motor: str = 'AutoGluon TimeSeries 1.6.1'
    tipo_modelo: str = 'EVALUACION_NO_REENTRENADO'
    fecha_corte: date
    historico: list[DemandPoint] = Field(default_factory=list)
    predicciones: list[ForecastPoint] = Field(default_factory=list)
    horizontes: list[HorizonTotal] = Field(default_factory=list)
    stock_actual: float | None = None
    cache: bool = False
    advertencias: list[str] = Field(default_factory=list)
    detalle: str | None = None
