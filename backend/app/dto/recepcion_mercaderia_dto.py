from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from app.dto.detalle_recepcion_dto import (
    DetalleRecepcionCreate,
    DetalleRecepcionResponse,
    EstadoRecepcion
)


class RecepcionMercaderiaCreate(BaseModel):

    id_orden_reposicion: str

    # OPERARIO: se fuerza al del token (puede omitirse).
    # EMPRESA: obligatorio.
    id_operario: str | None = None

    fecha_recepcion: datetime | None = None

    observaciones_generales: str | None = Field(
        default=None,
        max_length=1000
    )

    detalles: list[
        DetalleRecepcionCreate
    ] = Field(min_length=1)


class RecepcionMercaderiaResponse(BaseModel):

    id_recepcion: str

    id_orden_reposicion: str

    id_operario: str

    fecha_recepcion: datetime

    observaciones_generales: str | None

    fecha_creacion: datetime

    detalles: list[
        DetalleRecepcionResponse
    ]


class UbicarDetalleRecepcion(BaseModel):

    id_rack: str


class ResolverEvaluacion(BaseModel):

    # OPERARIO: se fuerza al del token (puede omitirse).
    # EMPRESA: obligatorio.
    id_operario: str | None = None

    estado_recepcion: EstadoRecepcion

    comentario_resolucion: str = Field(
        min_length=1,
        max_length=1000
    )

    cantidad_aceptada: int | None = Field(
        default=None,
        ge=0
    )

    cantidad_rechazada: int | None = Field(
        default=None,
        ge=0
    )

    id_inventario: str | None = None
    id_detalle_inventario: str | None = None
    id_rack: str | None = None
    stock_minimo: int = Field(default=0, ge=0)
    stock_maximo: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validar_estado(self):

        if self.estado_recepcion not in {
            EstadoRecepcion.CONFORME,
            EstadoRecepcion.RECHAZADO
        }:
            raise ValueError(
                "Una evaluación solo puede "
                "resolverse como CONFORME "
                "o RECHAZADO"
            )

        self.comentario_resolucion = (
            self.comentario_resolucion.strip()
        )

        return self