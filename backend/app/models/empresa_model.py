from datetime import datetime, timezone
from typing import TypedDict


class EmpresaDocument(TypedDict):
    id: str
    nombre: str
    sector: str
    correo: str
    telefono: str
    password_hash: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime


def create_empresa_document(
    id_empresa: str,
    nombre: str,
    sector: str,
    correo: str,
    telefono: str,
    password_hash: str
) -> EmpresaDocument:

    ahora = datetime.now(timezone.utc)

    return EmpresaDocument(
        id=id_empresa,
        nombre=nombre,
        sector=sector,
        correo=correo,
        telefono=telefono,
        password_hash=password_hash,
        fecha_creacion=ahora,
        fecha_actualizacion=ahora
    )