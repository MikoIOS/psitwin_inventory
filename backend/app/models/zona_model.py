from datetime import datetime, timezone
from typing import TypedDict


class ZonaDocument(TypedDict):
    id: str
    id_almacen: str
    id_empresa: str

    nombre: str
    tipo_zona: str

    temperatura_min: float | None
    temperatura_max: float | None

    capacidad: int

    fecha_creacion: datetime
    fecha_actualizacion: datetime


def create_zona_document(
    id_zona: str,
    id_almacen: str,
    id_empresa: str,
    nombre: str,
    tipo_zona: str,
    temperatura_min: float | None,
    temperatura_max: float | None,
    capacidad: int
) -> ZonaDocument:

    ahora = datetime.now(
        timezone.utc
    )

    return ZonaDocument(
        id=id_zona,
        id_almacen=id_almacen,
        id_empresa=id_empresa,
        nombre=nombre,
        tipo_zona=tipo_zona,
        temperatura_min=temperatura_min,
        temperatura_max=temperatura_max,
        capacidad=capacidad,
        fecha_creacion=ahora,
        fecha_actualizacion=ahora
    )