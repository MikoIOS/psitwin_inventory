from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.dto.alerta_dto import NivelRiesgo


class TipoRecomendacion(str, Enum):
    REABASTECER = "REABASTECER"
    NO_REABASTECER = "NO_REABASTECER"
    REDUCIR_REPOSICION = "REDUCIR_REPOSICION"
    TRASLADAR_STOCK = "TRASLADAR_STOCK"
    REVISAR_CONSUMO = "REVISAR_CONSUMO"
    REVISAR_INVENTARIO = "REVISAR_INVENTARIO"


class EstadoRecomendacion(str, Enum):
    PENDIENTE = "PENDIENTE"
    VALIDADA_OPERARIO = "VALIDADA_OPERARIO"
    CAMBIOS_SOLICITADOS = "CAMBIOS_SOLICITADOS"
    APROBADA_EMPRESA = "APROBADA_EMPRESA"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    APLICADA = "APLICADA"
    EXPIRADA = "EXPIRADA"


class RecomendacionCreate(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    id_almacen: str
    id_inventario: str
    id_detalle_inventario: str | None = None
    id_producto: str

    id_alerta: Optional[str] = None

    tipo_recomendacion: (
        TipoRecomendacion
    )

    nivel_riesgo: NivelRiesgo

    cantidad_minima: Optional[int] = Field(
        default=None,
        ge=0
    )

    cantidad_recomendada: Optional[int] = Field(
        default=None,
        ge=0
    )

    cantidad_segura: Optional[int] = Field(
        default=None,
        ge=0
    )

    forecast_7d: Optional[float] = Field(
        default=None,
        ge=0
    )

    explicacion: str = Field(
        min_length=3,
        max_length=3000
    )

    origen: str = Field(
        default="PSITWIN",
        min_length=2,
        max_length=100
    )


class RecomendacionResponse(BaseModel):
    id_recomendacion: str

    id_empresa: str
    id_almacen: str
    id_inventario: str
    id_detalle_inventario: str | None = None
    id_producto: str

    id_alerta: Optional[str] = None

    tipo_recomendacion: (
        TipoRecomendacion
    )

    nivel_riesgo: NivelRiesgo

    cantidad_minima: Optional[int] = None
    cantidad_recomendada: Optional[int] = None
    cantidad_segura: Optional[int] = None
    forecast_7d: Optional[float] = None

    explicacion: str
    origen: str

    estado: EstadoRecomendacion

    fecha_creacion: datetime
    fecha_actualizacion: datetime
    fecha_aplicacion: Optional[datetime] = None

    notificacion_aprobacion: Optional[dict] = None


class RecomendacionEstadoUpdate(
    BaseModel
):
    estado: EstadoRecomendacion


class EmpresaCambiosRequest(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    comentario: str = Field(..., min_length=1, max_length=1000)


class EmpresaRechazoRequest(EmpresaCambiosRequest):
    pass


class EmpresaAprobacionRequest(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    id_proveedor: str
    costo_unitario: float = Field(..., ge=0)
    fecha_estimada_recepcion: Optional[datetime] = None
    observacion: Optional[str] = Field(default=None, max_length=500)


class PropuestaRecomendacionUpdate(BaseModel):
    cantidad_recomendada: Optional[int] = Field(default=None, ge=1)
    explicacion: Optional[str] = Field(default=None, min_length=3, max_length=3000)