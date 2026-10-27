from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.dto.detalle_reposicion_dto import (
    DetalleReposicionCreate
)


class EstadoOrdenReposicion(str, Enum):
    PENDIENTE = "PENDIENTE"
    # Devuelta por la empresa con comentario
    OBSERVADA = "OBSERVADA"
    # Solo órdenes antiguas: hoy validar pasa directo a ENVIADA
    APROBADA = "APROBADA"
    ENVIADA = "ENVIADA"
    PARCIAL = "PARCIAL"
    RECIBIDA = "RECIBIDA"
    CANCELADA = "CANCELADA"


class OrigenOrden(str, Enum):
    MANUAL = "MANUAL"
    RECOMENDACION_IA = "RECOMENDACION_IA"


class OrdenReposicionCreate(BaseModel):
    id_recomendacion: Optional[str] = None
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    # OPERARIO: se fuerza a su almacén (puede omitirse).
    id_almacen: Optional[str] = None
    id_proveedor: str

    # Líneas iniciales (opcional; también se pueden
    # agregar con POST /ordenes-reposicion/{id}/detalles)
    lineas: list[DetalleReposicionCreate] = []

    fecha_estimada_recepcion: Optional[datetime] = None

    origen: OrigenOrden = OrigenOrden.MANUAL

    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )


class OrdenReposicionUpdate(BaseModel):
    id_proveedor: Optional[str] = None
    fecha_estimada_recepcion: Optional[datetime] = None
    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )


class OrdenReposicionResponse(BaseModel):
    id_orden_reposicion: str
    id_recomendacion: Optional[str] = None

    id_empresa: str
    id_almacen: str
    id_proveedor: str

    origen: OrigenOrden
    estado: EstadoOrdenReposicion

    fecha_orden: datetime
    fecha_estimada_recepcion: Optional[datetime] = None

    observacion: Optional[str] = None

    # Solicitud de reposición (órdenes antiguas -> null)
    id_operario_solicitante: Optional[str] = None
    comentario_empresa: Optional[str] = None

    # Despacho registrado por el proveedor
    despacho: Optional[dict] = None
    fecha_despacho: Optional[datetime] = None

    fecha_creacion: datetime
    fecha_actualizacion: datetime


# ============================================================
# DEVOLVER CON COMENTARIO (EMPRESA)
#
# PATCH /ordenes-reposicion/{id}/devolver
# ============================================================

class DevolverOrdenRequest(BaseModel):
    comentario: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )


# ============================================================
# DESPACHO (PROVEEDOR)
#
# POST /ordenes-reposicion/{id}/despacho
# ============================================================

class LineaDespacho(BaseModel):
    id_detalle_reposicion: str

    cantidad: int = Field(
        ...,
        gt=0
    )

    fecha_vencimiento: Optional[datetime] = None

    temperatura: Optional[float] = None


class DespachoRequest(BaseModel):
    lineas: list[LineaDespacho] = Field(
        min_length=1
    )

    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )
