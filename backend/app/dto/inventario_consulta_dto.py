from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class InventarioFiltros(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id_almacen: str | None = None
    id_zona: str | None = None
    id_rack: str | None = None
    id_nivel: str | None = None
    id_producto: str | None = None
    id_inventario: str | None = None
    busqueda: str = Field(default='', max_length=150)
    estado: Literal['todos', 'stock-bajo', 'sin-stock', 'sobre-stock', 'normal'] = 'todos'

class ReporteSolicitud(BaseModel):
    model_config = ConfigDict(extra='forbid')
    formato: Literal['pdf', 'xlsx'] | None = None
    filtros: InventarioFiltros = Field(default_factory=InventarioFiltros)
    clave_idempotencia: str = Field(min_length=8, max_length=100)

class ReporteConfirmacion(BaseModel):
    model_config = ConfigDict(extra='forbid')
    confirmar: Literal[True]
