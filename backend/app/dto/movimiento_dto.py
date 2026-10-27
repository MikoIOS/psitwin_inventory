from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TipoMovimiento(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"


class MotivoMovimiento(str, Enum):
    RECEPCION = "RECEPCION"
    REPOSICION = "REPOSICION"
    VENTA = "VENTA"
    MERMA = "MERMA"
    VENCIMIENTO = "VENCIMIENTO"
    DEVOLUCION = "DEVOLUCION"
    CONTEO_FISICO = "CONTEO_FISICO"
    OTRO = "OTRO"


class MovimientoCreate(BaseModel):
    id_inventario: str
    id_detalle_inventario: str

    # Se fuerza al operario del token (puede omitirse).
    id_operario: Optional[str] = None

    # Interno: idempotencia de la entrada por recepción.
    id_detalle_recepcion: Optional[str] = None

    tipo_movimiento: TipoMovimiento
    motivo_movimiento: MotivoMovimiento

    cantidad: int = Field(..., gt=0)

    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )


class MovimientoResponse(BaseModel):
    id_movimiento: str
    id_almacen: str

    id_inventario: str
    id_detalle_inventario: str
    id_detalle_recepcion: Optional[str] = None
    id_producto: str
    id_rack: str
    id_operario: str

    # Historial: autor y zona del rack
    operario_nombre: Optional[str] = None
    id_zona: Optional[str] = None

    tipo_movimiento: TipoMovimiento
    motivo_movimiento: MotivoMovimiento

    cantidad: int

    stock_anterior: int
    stock_nuevo: int

    observacion: Optional[str] = None

    fecha_hora: datetime