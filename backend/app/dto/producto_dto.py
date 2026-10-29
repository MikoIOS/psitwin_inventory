from datetime import datetime
from typing import Optional
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator
)


class ProductoCreate(BaseModel):
    codigo: str | None = Field(default=None, max_length=80)
    unidad: Literal['kg', 'unidad'] = 'unidad'
    activo: bool = True

    @field_validator('nombre', 'categoria', 'familia', mode='before')
    @classmethod
    def normalizar_texto(cls, value):
        return value.strip() if isinstance(value, str) else value

    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None

    # Se ignora: se toma del token del PROVEEDOR.
    id_proveedor: Optional[str] = None

    # Rack de referencia: lo asigna después el OPERARIO
    # (PUT /productos/{id} {id_rack}).
    id_rack: Optional[str] = None

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    categoria: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    familia: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    marca: Optional[str] = None

    # Obligatorio: kg por unidad (carga de los racks).
    peso: float = Field(
        ...,
        gt=0,
        allow_inf_nan=False
    )

    volumen: Optional[float] = Field(
        default=None,
        gt=0,
        allow_inf_nan=False
    )

    stock: int = Field(
        default=0,
        ge=0
    )

    requiere_refrigeracion: bool = False

    temperatura_min_almacenamiento: Optional[float] = None
    temperatura_max_almacenamiento: Optional[float] = None

    lead_time_dias: int = Field(
        ...,
        ge=0
    )

    vida_util_dias: int = Field(
        ...,
        ge=1
    )

    @model_validator(mode="after")
    def validar_refrigeracion(self):

        if self.requiere_refrigeracion:

            if (
                self.temperatura_min_almacenamiento is None
                or
                self.temperatura_max_almacenamiento is None
            ):

                raise ValueError(
                    "Si el producto requiere refrigeración, "
                    "debe indicar temperatura mínima y máxima"
                )

            if (
                self.temperatura_min_almacenamiento
                >
                self.temperatura_max_almacenamiento
            ):

                raise ValueError(
                    "La temperatura mínima no puede ser "
                    "mayor que la máxima"
                )

        return self


class ProductoUpdate(BaseModel):
    codigo: str | None = Field(default=None, max_length=80)
    activo: bool | None = None

    @field_validator('nombre', 'categoria', 'familia', mode='before')
    @classmethod
    def normalizar_texto(cls, value):
        return value.strip() if isinstance(value, str) else value

    id_rack: Optional[str] = None

    nombre: Optional[str] = Field(default=None, min_length=2, max_length=150)
    categoria: Optional[str] = Field(default=None, min_length=2, max_length=100)
    familia: Optional[str] = Field(default=None, min_length=2, max_length=100)
    marca: Optional[str] = None

    peso: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    volumen: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)

    stock: Optional[int] = Field(
        default=None,
        ge=0
    )

    requiere_refrigeracion: Optional[bool] = None

    temperatura_min_almacenamiento: Optional[float] = None
    temperatura_max_almacenamiento: Optional[float] = None

    lead_time_dias: Optional[int] = Field(
        default=None,
        ge=0
    )

    vida_util_dias: Optional[int] = Field(
        default=None,
        ge=1
    )

    @model_validator(mode='after')
    def preservar_campos_obligatorios(self):
        # Omitted fields are unchanged; explicit null must not corrupt a product
        # or turn a valid update into a response serialization error.
        required = {'nombre', 'categoria', 'familia', 'peso', 'requiere_refrigeracion', 'lead_time_dias', 'vida_util_dias'}
        for field in required & self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f'{field} no puede ser nulo')
        return self


class ProductoResponse(BaseModel):
    codigo: str | None = None
    unidad: Literal['kg', 'unidad'] = 'unidad'
    activo: bool = True

    id_producto: str

    id_empresa: str

    # Productos antiguos (creados por la empresa) -> null
    id_proveedor: Optional[str] = None

    # Rack de referencia (opcional)
    id_rack: Optional[str] = None

    nombre: str

    categoria: str

    familia: str

    marca: Optional[str] = None

    peso: Optional[float] = None

    volumen: Optional[float] = None

    # Para compatibilidad con registros antiguos
    stock: int = 0

    requiere_refrigeracion: bool = False

    temperatura_min_almacenamiento: Optional[float] = None

    temperatura_max_almacenamiento: Optional[float] = None

    lead_time_dias: int

    vida_util_dias: int

    fecha_creacion: datetime

    fecha_actualizacion: datetime
