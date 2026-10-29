from app.dto.cantidad import Cantidad
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    model_validator
)



class EstadoRecepcion(str, Enum):
    CONFORME = "CONFORME"
    RECHAZADO = "RECHAZADO"
    EN_EVALUACION = "EN_EVALUACION"


class DetalleRecepcionCreate(BaseModel):
    id_nivel: str | None = None
    id_detalle_reposicion: str
    id_inventario: str
    id_detalle_inventario: str | None = None

    id_rack: str | None = None
    stock_minimo: Cantidad = Field(default=0, ge=0)
    stock_maximo: Cantidad | None = Field(default=None, ge=0)

    cantidad_recibida: Cantidad = Field(
        ...,
        gt=0
    )

    cantidad_rechazada: Cantidad = Field(
        default=0,
        ge=0
    )

    lote: str = Field(
        default="SIN_LOTE",
        min_length=1,
        max_length=100
    )

    fecha_vencimiento: datetime | None = None

    temperatura_recepcion: float | None = None

    estado_recepcion: EstadoRecepcion = (
        EstadoRecepcion.CONFORME
    )

    comentario_recepcion: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    motivo_rechazo: Optional[str] = Field(
        default=None,
        max_length=500
    )

    @model_validator(mode="after")
    def validar_cantidades(self):
        if self.estado_recepcion == EstadoRecepcion.RECHAZADO:
            self.cantidad_rechazada = self.cantidad_recibida

        self.lote = self.lote.strip()

        if self.comentario_recepcion is not None:
            self.comentario_recepcion = (
                self.comentario_recepcion.strip()
            )

        if (
            self.cantidad_rechazada
            > self.cantidad_recibida
        ):
            raise ValueError(
                "La cantidad rechazada no puede "
                "ser mayor que la recibida"
            )

        if (
            self.cantidad_rechazada > 0
            and not self.motivo_rechazo
            and not self.comentario_recepcion
        ):
            raise ValueError(
                "Debe indicar el motivo u observación del rechazo"
            )

        if (
            self.estado_recepcion
            in {
                EstadoRecepcion.RECHAZADO,
                EstadoRecepcion.EN_EVALUACION
            }
            and not self.comentario_recepcion
            and not self.motivo_rechazo
        ):
            raise ValueError(
                "Debe indicar el motivo de la recepción"
            )

        return self


class DetalleRecepcionResponse(BaseModel):
    id_detalle_recepcion: str
    id_recepcion: str
    id_detalle_reposicion: str
    id_inventario: str
    id_detalle_inventario: str | None = None

    cantidad_recibida: Cantidad
    cantidad_rechazada: Cantidad
    cantidad_aceptada: Cantidad

    lote: str = "SIN_LOTE"
    fecha_vencimiento: datetime | None = None
    temperatura_recepcion: float | None = None
    estado_recepcion: EstadoRecepcion = (
        EstadoRecepcion.CONFORME
    )
    comentario_recepcion: Optional[str] = None

    motivo_rechazo: Optional[str] = None

    id_movimiento: Optional[str] = None

    ubicado: bool = True

    riesgo_antes: Optional[str] = None
    riesgo_despues: Optional[str] = None
    notificacion_final: Optional[dict] = None

    fecha_creacion: datetime
