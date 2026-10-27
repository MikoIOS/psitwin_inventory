from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field

Horizonte = Literal[1, 7, 30, 90]

class PrediccionDiaria(BaseModel):
    fecha: date
    demanda_estimada: float = Field(ge=0)

class ForecastResponse(BaseModel):
    id_almacen: str
    id_producto: str
    fecha_generacion: datetime
    fecha_corte: date
    horizonte_dias: Horizonte
    fecha_inicio: date
    fecha_fin: date
    estado: Literal["DISPONIBLE", "HISTORIAL_INSUFICIENTE", "MODELO_NO_DISPONIBLE"]
    demanda_total_estimada: float | None = Field(default=None, ge=0)
    predicciones_diarias: list[PrediccionDiaria] = Field(default_factory=list)
    modelo: str | None = None
    version_modelo: str | None = None
    historial_suficiente: bool = False
    advertencias: list[str] = Field(default_factory=list)
