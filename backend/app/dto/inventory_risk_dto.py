from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.dto.alerta_dto import (
    NivelRiesgo
)


class ConsumoInfo(BaseModel):
    promedio_7d: float = Field(
        ge=0
    )

    promedio_14d: float = Field(
        ge=0
    )

    promedio_28d: float = Field(
        ge=0
    )

    tendencia_porcentaje: float


class CoberturaInfo(BaseModel):
    dias: Optional[float] = Field(
        default=None,
        ge=0
    )


class ForecastDiario(BaseModel):
    fecha: datetime

    demanda_predicha: float = Field(
        ge=0
    )


class ForecastInfo(BaseModel):
    demanda_7d: Optional[float] = Field(
        default=None,
        ge=0
    )

    fecha_quiebre_estimada: Optional[
        datetime
    ] = None

    predicciones_diarias: list[
        ForecastDiario
    ] = Field(
        default_factory=list
    )


class SeguridadInfo(BaseModel):
    stock_seguridad: float = Field(
        ge=0
    )

    punto_reposicion: float = Field(
        ge=0
    )


class RiesgoInfo(BaseModel):
    nivel: NivelRiesgo

    score: float = Field(
        ge=0,
        le=100
    )


class ReposicionInfo(BaseModel):
    cantidad_minima: int = Field(
        ge=0
    )

    cantidad_recomendada: int = Field(
        ge=0
    )

    cantidad_segura: int = Field(
        ge=0
    )


class InventoryRiskResponse(BaseModel):
    id_empresa: str
    id_almacen: str
    id_inventario: str
    id_producto: str

    stock_actual: float = Field(
        ge=0
    )

    consumo: ConsumoInfo

    cobertura: CoberturaInfo

    lead_time_dias: int = Field(
        ge=0
    )

    forecast: ForecastInfo

    seguridad: SeguridadInfo | None = None

    riesgo: RiesgoInfo | None = None

    reposicion: Optional[
        ReposicionInfo
    ] = None

    explicacion: Optional[str] = None
    estado: str = "DISPONIBLE"
    advertencias: list[str] = Field(default_factory=list)
    pronosticos: dict[int, dict] = Field(default_factory=dict)
