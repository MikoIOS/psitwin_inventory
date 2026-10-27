from datetime import datetime, timezone
from typing import TypedDict


class AlmacenDocument(TypedDict):
    id: str
    id_empresa: str
    nombre: str
    longitud: float
    latitud: float
    area_m2: float
    aforo: int
    tipo_almacen: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime


def create_almacen_document(
    id_almacen: str,
    id_empresa: str,
    nombre: str,
    longitud: float,
    latitud: float,
    area_m2: float,
    aforo: int,
    tipo_almacen: str
) -> AlmacenDocument:

    ahora = datetime.now(timezone.utc)

    return AlmacenDocument(
        id=id_almacen,
        id_empresa=id_empresa,
        nombre=nombre,
        longitud=longitud,
        latitud=latitud,
        area_m2=area_m2,
        aforo=aforo,
        tipo_almacen=tipo_almacen,
        fecha_creacion=ahora,
        fecha_actualizacion=ahora
    )