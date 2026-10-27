# DTO_SCHEMA - entidades y contratos exactos

Auditoria estatica del codigo local. Obligatorio significa presencia, nullable significa que el tipo admite null: no son equivalentes. Response no aplica todas las restricciones de Create. IDs son strings, no UUID validados por DTO; generacion UUIDv5 propuesta. Cada declaracion exacta incluye validadores, defaults y herencia; un DTO heredado conserva campos del padre. Claves/relaciones en RELATIONSHIPS. Ejemplos de entidades al final, sin credenciales.

## TipoAlerta

Fuente: `app/dto/alerta_dto.py`.


Declaracion y validadores exactos:

```python
class TipoAlerta(str, Enum):
    RIESGO_STOCKOUT = "RIESGO_STOCKOUT"
    STOCK_BAJO = "STOCK_BAJO"
    SOBRESTOCK = "SOBRESTOCK"
    CONSUMO_ANOMALO = "CONSUMO_ANOMALO"
    PROXIMO_VENCIMIENTO = "PROXIMO_VENCIMIENTO"
```

## NivelRiesgo

Fuente: `app/dto/alerta_dto.py`.


Declaracion y validadores exactos:

```python
class NivelRiesgo(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"
```

## EstadoAlerta

Fuente: `app/dto/alerta_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoAlerta(str, Enum):
    ACTIVA = "ACTIVA"
    VISTA = "VISTA"
    RESUELTA = "RESUELTA"
    IGNORADA = "IGNORADA"
```

## AlertaCreate

Fuente: `app/dto/alerta_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| tipo_alerta | TipoAlerta | Obligatorio | Sin default |
| nivel_riesgo | NivelRiesgo | Obligatorio | Sin default |
| titulo | str | Obligatorio | Field( min_length=3, max_length=150 ) |
| mensaje | str | Obligatorio | Field( min_length=3, max_length=1000 ) |
| stock_actual | float | Obligatorio | Field(ge=0) |
| dias_cobertura | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| stock_seguridad | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| punto_reposicion | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| forecast_7d | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class AlertaCreate(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    id_almacen: str
    id_inventario: str
    id_producto: str

    tipo_alerta: TipoAlerta
    nivel_riesgo: NivelRiesgo

    titulo: str = Field(
        min_length=3,
        max_length=150
    )

    mensaje: str = Field(
        min_length=3,
        max_length=1000
    )

    stock_actual: float = Field(ge=0)

    dias_cobertura: Optional[float] = Field(
        default=None,
        ge=0
    )

    stock_seguridad: Optional[float] = Field(
        default=None,
        ge=0
    )

    punto_reposicion: Optional[float] = Field(
        default=None,
        ge=0
    )

    forecast_7d: Optional[float] = Field(
        default=None,
        ge=0
    )
```

## AlertaResponse

Fuente: `app/dto/alerta_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_alerta | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| tipo_alerta | TipoAlerta | Obligatorio | Sin default |
| nivel_riesgo | NivelRiesgo | Obligatorio | Sin default |
| titulo | str | Obligatorio | Sin default |
| mensaje | str | Obligatorio | Sin default |
| stock_actual | float | Obligatorio | Sin default |
| dias_cobertura | Optional[float] | Omitible; nullable | None |
| stock_seguridad | Optional[float] | Omitible; nullable | None |
| punto_reposicion | Optional[float] | Omitible; nullable | None |
| forecast_7d | Optional[float] | Omitible; nullable | None |
| estado | EstadoAlerta | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |
| fecha_resolucion | Optional[datetime] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class AlertaResponse(BaseModel):
    id_alerta: str

    id_empresa: str
    id_almacen: str
    id_inventario: str
    id_producto: str

    tipo_alerta: TipoAlerta
    nivel_riesgo: NivelRiesgo

    titulo: str
    mensaje: str

    stock_actual: float
    dias_cobertura: Optional[float] = None
    stock_seguridad: Optional[float] = None
    punto_reposicion: Optional[float] = None
    forecast_7d: Optional[float] = None

    estado: EstadoAlerta

    fecha_creacion: datetime
    fecha_actualizacion: datetime
    fecha_resolucion: Optional[datetime] = None
```

## AlertaEstadoUpdate

Fuente: `app/dto/alerta_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| estado | EstadoAlerta | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class AlertaEstadoUpdate(BaseModel):
    estado: EstadoAlerta
```

## AlmacenCreate

Fuente: `app/dto/almacen_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| longitud | Decimal | Obligatorio | Field( ..., ge=Decimal("-180.000000"), le=Decimal("180.000000"), max_digits=9, decimal_places=6 ) |
| latitud | Decimal | Obligatorio | Field( ..., ge=Decimal("-90.000000"), le=Decimal("90.000000"), max_digits=8, decimal_places=6 ) |
| area_m2 | float | Obligatorio | Field( ..., gt=0 ) |
| aforo | int | Obligatorio | Field( ..., ge=0 ) |
| tipo_almacen | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |

Declaracion y validadores exactos:

```python
class AlmacenCreate(BaseModel):

    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    longitud: Decimal = Field(
        ...,
        ge=Decimal("-180.000000"),
        le=Decimal("180.000000"),
        max_digits=9,
        decimal_places=6
    )

    latitud: Decimal = Field(
        ...,
        ge=Decimal("-90.000000"),
        le=Decimal("90.000000"),
        max_digits=8,
        decimal_places=6
    )

    area_m2: float = Field(
        ...,
        gt=0
    )

    aforo: int = Field(
        ...,
        ge=0
    )

    tipo_almacen: str = Field(
        ...,
        min_length=2,
        max_length=100
    )


# ============================================================
# ACTUALIZAR ALMACEN
# ============================================================
```

## AlmacenUpdate

Fuente: `app/dto/almacen_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| longitud | Optional[Decimal] | Omitible; nullable | Field( default=None, ge=Decimal("-180.000000"), le=Decimal("180.000000"), max_digits=9, decimal_places=6 ) |
| latitud | Optional[Decimal] | Omitible; nullable | Field( default=None, ge=Decimal("-90.000000"), le=Decimal("90.000000"), max_digits=8, decimal_places=6 ) |
| area_m2 | Optional[float] | Omitible; nullable | Field( default=None, gt=0 ) |
| aforo | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| tipo_almacen | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |

Declaracion y validadores exactos:

```python
class AlmacenUpdate(BaseModel):

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    longitud: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-180.000000"),
        le=Decimal("180.000000"),
        max_digits=9,
        decimal_places=6
    )

    latitud: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-90.000000"),
        le=Decimal("90.000000"),
        max_digits=8,
        decimal_places=6
    )

    area_m2: Optional[float] = Field(
        default=None,
        gt=0
    )

    aforo: Optional[int] = Field(
        default=None,
        ge=0
    )

    tipo_almacen: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )


# ============================================================
# RESPONSE
#
# Acepta temporalmente:
#
# id
# o
# id_almacen
#
# Pero la API siempre devuelve "id".
# ============================================================
```

## AlmacenResponse

Fuente: `app/dto/almacen_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id | str | Obligatorio | Field( validation_alias=AliasChoices( "id", "id_almacen" ) ) |
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| longitud | Decimal | Obligatorio | Sin default |
| latitud | Decimal | Obligatorio | Sin default |
| area_m2 | float | Obligatorio | Sin default |
| aforo | int | Obligatorio | Sin default |
| tipo_almacen | str | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class AlmacenResponse(BaseModel):

    id: str = Field(
        validation_alias=AliasChoices(
            "id",
            "id_almacen"
        )
    )

    id_empresa: str

    nombre: str

    longitud: Decimal

    latitud: Decimal

    area_m2: float

    aforo: int

    tipo_almacen: str

    fecha_creacion: datetime

    fecha_actualizacion: datetime
```

## LoginRequest

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| correo | EmailStr | Obligatorio | Sin default |
| password | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class LoginRequest(BaseModel):

    correo: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )
```

## LoginResponse

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| access_token | str | Obligatorio | Sin default |
| token_type | str | Omitible | "bearer" |
| rol | Literal[ "EMPRESA", "OPERARIO", "PROVEEDOR" ] | Obligatorio | Sin default |
| empresa | EmpresaResponse | Obligatorio | Sin default |
| operario | Optional[ OperarioResponse ] | Omitible; nullable | None |
| proveedor | Optional[ ProveedorResponse ] | Omitible; nullable | None |
| debe_cambiar_password | bool | Omitible | False |

Declaracion y validadores exactos:

```python
class LoginResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    rol: Literal[
        "EMPRESA",
        "OPERARIO",
        "PROVEEDOR"
    ]

    # Siempre presente. Para OPERARIO:
    # la empresa a la que pertenece.
    empresa: EmpresaResponse

    operario: Optional[
        OperarioResponse
    ] = None

    proveedor: Optional[
        ProveedorResponse
    ] = None

    debe_cambiar_password: bool = False


# ============================================================
# GET /auth/me
# ============================================================
```

## MeResponse

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| rol | Literal[ "EMPRESA", "OPERARIO", "PROVEEDOR" ] | Obligatorio | Sin default |
| empresa | EmpresaResponse | Obligatorio | Sin default |
| operario | Optional[ OperarioResponse ] | Omitible; nullable | None |
| proveedor | Optional[ ProveedorResponse ] | Omitible; nullable | None |
| debe_cambiar_password | bool | Omitible | False |

Declaracion y validadores exactos:

```python
class MeResponse(BaseModel):

    rol: Literal[
        "EMPRESA",
        "OPERARIO",
        "PROVEEDOR"
    ]

    empresa: EmpresaResponse

    operario: Optional[
        OperarioResponse
    ] = None

    proveedor: Optional[
        ProveedorResponse
    ] = None

    debe_cambiar_password: bool = False


# ============================================================
# PATCH /auth/me/password (OPERARIO / PROVEEDOR)
# ============================================================
```

## CambiarPasswordRequest

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password_actual | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |
| password_nueva | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class CambiarPasswordRequest(BaseModel):

    password_actual: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    password_nueva: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# RESET PASSWORD (EMPRESA)
#
# POST /operarios/{id}/reset-password
# POST /proveedores/{id}/reset-password
# ============================================================
```

## ResetPasswordRequest

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password_temporal | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class ResetPasswordRequest(BaseModel):

    password_temporal: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    # Opcional: da correo a una cuenta antigua sin correo.
    correo: Optional[EmailStr] = None


# ============================================================
# USUARIO AUTENTICADO
#
# Resultado de get_current_user.
# ============================================================
```

## UsuarioActual

Fuente: `app/dto/auth_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| rol | Literal[ "EMPRESA", "OPERARIO", "PROVEEDOR" ] | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| id_operario | Optional[str] | Omitible; nullable | None |
| id_almacen | Optional[str] | Omitible; nullable | None |
| id_proveedor | Optional[str] | Omitible; nullable | None |
| debe_cambiar_password | bool | Omitible | False |

Declaracion y validadores exactos:

```python
class UsuarioActual(BaseModel):

    rol: Literal[
        "EMPRESA",
        "OPERARIO",
        "PROVEEDOR"
    ]

    id_empresa: str

    id_operario: Optional[str] = None

    id_almacen: Optional[str] = None

    id_proveedor: Optional[str] = None

    debe_cambiar_password: bool = False

    @property
    def es_proveedor(self) -> bool:

        return self.rol == "PROVEEDOR"

    @property
    def es_empresa(self) -> bool:

        return self.rol == "EMPRESA"

    @property
    def es_operario(self) -> bool:

        return self.rol == "OPERARIO"
```

## EstadoRecepcion

Fuente: `app/dto/detalle_recepcion_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoRecepcion(str, Enum):
    CONFORME = "CONFORME"
    RECHAZADO = "RECHAZADO"
    EN_EVALUACION = "EN_EVALUACION"
```

## DetalleRecepcionCreate

Fuente: `app/dto/detalle_recepcion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_detalle_reposicion | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| cantidad_recibida | int | Obligatorio | Field( ..., gt=0 ) |
| cantidad_rechazada | int | Omitible | Field( default=0, ge=0 ) |
| lote | str | Omitible | Field( default="SIN_LOTE", min_length=1, max_length=100 ) |
| fecha_vencimiento | datetime &#124; None | Omitible; nullable | None |
| temperatura_recepcion | float &#124; None | Omitible; nullable | None |
| estado_recepcion | EstadoRecepcion | Omitible | ( EstadoRecepcion.CONFORME ) |
| comentario_recepcion | Optional[str] | Omitible; nullable | Field( default=None, max_length=1000 ) |
| motivo_rechazo | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
class DetalleRecepcionCreate(BaseModel):
    id_detalle_reposicion: str
    id_inventario: str

    cantidad_recibida: int = Field(
        ...,
        gt=0
    )

    cantidad_rechazada: int = Field(
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
```

## DetalleRecepcionResponse

Fuente: `app/dto/detalle_recepcion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_detalle_recepcion | str | Obligatorio | Sin default |
| id_recepcion | str | Obligatorio | Sin default |
| id_detalle_reposicion | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| cantidad_recibida | int | Obligatorio | Sin default |
| cantidad_rechazada | int | Obligatorio | Sin default |
| cantidad_aceptada | int | Obligatorio | Sin default |
| lote | str | Omitible | "SIN_LOTE" |
| fecha_vencimiento | datetime &#124; None | Omitible; nullable | None |
| temperatura_recepcion | float &#124; None | Omitible; nullable | None |
| estado_recepcion | EstadoRecepcion | Omitible | ( EstadoRecepcion.CONFORME ) |
| comentario_recepcion | Optional[str] | Omitible; nullable | None |
| motivo_rechazo | Optional[str] | Omitible; nullable | None |
| id_movimiento | Optional[str] | Omitible; nullable | None |
| ubicado | bool | Omitible | True |
| riesgo_antes | Optional[str] | Omitible; nullable | None |
| riesgo_despues | Optional[str] | Omitible; nullable | None |
| notificacion_final | Optional[dict] | Omitible; nullable | None |
| fecha_creacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class DetalleRecepcionResponse(BaseModel):
    id_detalle_recepcion: str
    id_recepcion: str
    id_detalle_reposicion: str
    id_inventario: str

    cantidad_recibida: int
    cantidad_rechazada: int
    cantidad_aceptada: int

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
```

## DetalleReposicionCreate

Fuente: `app/dto/detalle_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_producto | str | Obligatorio | Sin default |
| cantidad_solicitada | int | Obligatorio | Field( ..., gt=0 ) |
| costo_unitario | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class DetalleReposicionCreate(BaseModel):
    id_producto: str

    cantidad_solicitada: int = Field(
        ...,
        gt=0
    )

    costo_unitario: Optional[float] = Field(
        default=None,
        ge=0
    )
```

## DetalleReposicionUpdate

Fuente: `app/dto/detalle_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| cantidad_solicitada | Optional[int] | Omitible; nullable | Field( default=None, gt=0 ) |
| costo_unitario | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class DetalleReposicionUpdate(BaseModel):
    cantidad_solicitada: Optional[int] = Field(
        default=None,
        gt=0
    )

    costo_unitario: Optional[float] = Field(
        default=None,
        ge=0
    )
```

## DetalleReposicionResponse

Fuente: `app/dto/detalle_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_detalle_reposicion | str | Obligatorio | Sin default |
| id_orden_reposicion | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| cantidad_solicitada | int | Obligatorio | Sin default |
| costo_unitario | Optional[float] | Omitible; nullable | None |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class DetalleReposicionResponse(BaseModel):
    id_detalle_reposicion: str
    id_orden_reposicion: str
    id_producto: str

    cantidad_solicitada: int
    costo_unitario: Optional[float] = None

    fecha_creacion: datetime
    fecha_actualizacion: datetime
```

## EmailVerificationCodeRequest

Fuente: `app/dto/email_verification_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| codigo | str | Obligatorio | Field( ..., min_length=6, max_length=6, pattern=r"^\d{6}$", ) |

Declaracion y validadores exactos:

```python
class EmailVerificationCodeRequest(BaseModel):
    codigo: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )
```

## EmailVerificationSendResponse

Fuente: `app/dto/email_verification_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| status | str | Obligatorio | Sin default |
| email | str &#124; None | Omitible; nullable | None |
| remaining_seconds | int &#124; None | Omitible; nullable | None |
| reason | str &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class EmailVerificationSendResponse(BaseModel):
    status: str
    email: str | None = None
    remaining_seconds: int | None = None
    reason: str | None = None
```

## EmailVerificationResponse

Fuente: `app/dto/email_verification_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| verified | bool | Obligatorio | Sin default |
| status | str | Obligatorio | Sin default |
| email | str &#124; None | Omitible; nullable | None |
| attempts | int &#124; None | Omitible; nullable | None |
| remaining_attempts | int &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class EmailVerificationResponse(BaseModel):
    verified: bool
    status: str
    email: str | None = None
    attempts: int | None = None
    remaining_attempts: int | None = None
```

## EmpresaRegisterRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| ruc | str | Obligatorio | Field( ..., min_length=8, max_length=20 ) |
| sector | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| correo | EmailStr | Obligatorio | Sin default |
| telefono | str | Obligatorio | Field( ..., min_length=6, max_length=20 ) |
| password | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class EmpresaRegisterRequest(BaseModel):

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    ruc: str = Field(
        ...,
        min_length=8,
        max_length=20
    )

    sector: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    correo: EmailStr

    telefono: str = Field(
        ...,
        min_length=6,
        max_length=20
    )

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# LOGIN
# ============================================================
```

## EmpresaLoginRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| correo | EmailStr | Obligatorio | Sin default |
| password | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class EmpresaLoginRequest(BaseModel):

    correo: EmailStr

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# ACTUALIZAR PERFIL
# ============================================================
```

## EmpresaUpdateRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| ruc | Optional[str] | Omitible; nullable | Field( default=None, min_length=8, max_length=20 ) |
| sector | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| telefono | Optional[str] | Omitible; nullable | Field( default=None, min_length=6, max_length=20 ) |

Declaracion y validadores exactos:

```python
class EmpresaUpdateRequest(BaseModel):

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    ruc: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=20
    )

    sector: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    correo: Optional[EmailStr] = None

    telefono: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=20
    )


# ============================================================
# CAMBIAR PASSWORD
# ============================================================
```

## EmpresaChangePasswordRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password_actual | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |
| password_nueva | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class EmpresaChangePasswordRequest(BaseModel):

    password_actual: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    password_nueva: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# ELIMINAR EMPRESA
#
# Pedimos password como confirmacion.
# ============================================================
```

## EmpresaDeleteRequest

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class EmpresaDeleteRequest(BaseModel):

    password: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# RESPONSE EMPRESA
# ============================================================
```

## EmpresaResponse

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| ruc | str | Obligatorio | Sin default |
| sector | str | Obligatorio | Sin default |
| correo | EmailStr | Obligatorio | Sin default |
| telefono | str | Obligatorio | Sin default |
| correo_verificado | bool | Omitible | False |
| fecha_verificacion_correo | Optional[str] | Omitible; nullable | None |
| fecha_creacion | str | Obligatorio | Sin default |
| fecha_actualizacion | str | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class EmpresaResponse(BaseModel):

    id_empresa: str

    nombre: str

    ruc: str

    sector: str

    correo: EmailStr

    telefono: str

    correo_verificado: bool = False

    fecha_verificacion_correo: Optional[str] = None

    fecha_creacion: str

    fecha_actualizacion: str


# ============================================================
# LOGIN RESPONSE
# ============================================================
```

## EmpresaLoginResponse

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| access_token | str | Obligatorio | Sin default |
| token_type | str | Omitible | "bearer" |
| empresa | EmpresaResponse | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class EmpresaLoginResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    empresa: EmpresaResponse


# ============================================================
# MESSAGE
# ============================================================
```

## MessageResponse

Fuente: `app/dto/empresa_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| mensaje | str | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class MessageResponse(BaseModel):

    mensaje: str
```

## InventarioCreate

Fuente: `app/dto/inventario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_producto | str | Obligatorio | Sin default |
| id_rack | str | Obligatorio | Sin default |
| stock_actual | int | Obligatorio | Field( ..., ge=0 ) |
| stock_minimo | int | Omitible | Field( default=0, ge=0 ) |
| stock_maximo | int | Obligatorio | Field( ..., ge=0 ) |

Declaracion y validadores exactos:

```python
class InventarioCreate(BaseModel):

    id_producto: str

    id_rack: str

    stock_actual: int = Field(
        ...,
        ge=0
    )

    stock_minimo: int = Field(
        default=0,
        ge=0
    )

    stock_maximo: int = Field(
        ...,
        ge=0
    )

    @model_validator(mode="after")
    def validar_stocks(self):

        if self.stock_minimo > self.stock_maximo:

            raise ValueError(
                "El stock mínimo no puede ser mayor "
                "que el stock máximo"
            )

        return self


# ============================================================
# ACTUALIZAR INVENTARIO
# ============================================================
```

## InventarioUpdate

Fuente: `app/dto/inventario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| stock_minimo | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| stock_maximo | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class InventarioUpdate(BaseModel):

    # Solo límites: el stock cambia únicamente por
    # movimientos y recepciones; el rack no se cambia.

    stock_minimo: Optional[int] = Field(
        default=None,
        ge=0
    )

    stock_maximo: Optional[int] = Field(
        default=None,
        ge=0
    )


# ============================================================
# RESPONSE
# ============================================================
```

## InventarioResponse

Fuente: `app/dto/inventario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| id_rack | str | Obligatorio | Sin default |
| stock_actual | int | Obligatorio | Sin default |
| stock_minimo | int | Obligatorio | Sin default |
| stock_maximo | int | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class InventarioResponse(BaseModel):

    id_inventario: str

    id_producto: str

    id_rack: str

    stock_actual: int

    stock_minimo: int

    stock_maximo: int

    fecha_creacion: datetime

    fecha_actualizacion: datetime


# ============================================================
# HISTORIAL DE CAMBIOS
#
# GET /inventarios/{id}/historial
# ============================================================
```

## InventarioHistorialResponse

Fuente: `app/dto/inventario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| fecha | datetime | Obligatorio | Sin default |
| id_operario | Optional[str] | Omitible; nullable | None |
| operario_nombre | Optional[str] | Omitible; nullable | None |
| accion | str | Obligatorio | Sin default |
| antes | Optional[dict] | Omitible; nullable | None |
| despues | Optional[dict] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class InventarioHistorialResponse(BaseModel):

    fecha: datetime

    id_operario: Optional[str] = None

    operario_nombre: Optional[str] = None

    # CREAR | EDITAR_LIMITES
    accion: str

    antes: Optional[dict] = None

    despues: Optional[dict] = None
```

## ConsumoInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| promedio_7d | float | Obligatorio | Field( ge=0 ) |
| promedio_14d | float | Obligatorio | Field( ge=0 ) |
| promedio_28d | float | Obligatorio | Field( ge=0 ) |
| tendencia_porcentaje | float | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class ConsumoInfo(BaseModel):
    promedio_7d: float = Field(
        ge=0
    )

    promedio_14d: float = Field(
        ge=0
    )

    promedio_28d: float = Field(
        ge=0
    )

    tendencia_porcentaje: float
```

## CoberturaInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| dias | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class CoberturaInfo(BaseModel):
    dias: Optional[float] = Field(
        default=None,
        ge=0
    )
```

## ForecastDiario

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| fecha | datetime | Obligatorio | Sin default |
| demanda_predicha | float | Obligatorio | Field( ge=0 ) |

Declaracion y validadores exactos:

```python
class ForecastDiario(BaseModel):
    fecha: datetime

    demanda_predicha: float = Field(
        ge=0
    )
```

## ForecastInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| demanda_7d | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| fecha_quiebre_estimada | Optional[ datetime ] | Omitible; nullable | None |
| predicciones_diarias | list[ ForecastDiario ] | Omitible | Field( default_factory=list ) |

Declaracion y validadores exactos:

```python
class ForecastInfo(BaseModel):
    demanda_7d: Optional[float] = Field(
        default=None,
        ge=0
    )

    fecha_quiebre_estimada: Optional[
        datetime
    ] = None

    predicciones_diarias: list[
        ForecastDiario
    ] = Field(
        default_factory=list
    )
```

## SeguridadInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| stock_seguridad | float | Obligatorio | Field( ge=0 ) |
| punto_reposicion | float | Obligatorio | Field( ge=0 ) |

Declaracion y validadores exactos:

```python
class SeguridadInfo(BaseModel):
    stock_seguridad: float = Field(
        ge=0
    )

    punto_reposicion: float = Field(
        ge=0
    )
```

## RiesgoInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nivel | NivelRiesgo | Obligatorio | Sin default |
| score | float | Obligatorio | Field( ge=0, le=100 ) |

Declaracion y validadores exactos:

```python
class RiesgoInfo(BaseModel):
    nivel: NivelRiesgo

    score: float = Field(
        ge=0,
        le=100
    )
```

## ReposicionInfo

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| cantidad_minima | int | Obligatorio | Field( ge=0 ) |
| cantidad_recomendada | int | Obligatorio | Field( ge=0 ) |
| cantidad_segura | int | Obligatorio | Field( ge=0 ) |

Declaracion y validadores exactos:

```python
class ReposicionInfo(BaseModel):
    cantidad_minima: int = Field(
        ge=0
    )

    cantidad_recomendada: int = Field(
        ge=0
    )

    cantidad_segura: int = Field(
        ge=0
    )
```

## InventoryRiskResponse

Fuente: `app/dto/inventory_risk_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | str | Obligatorio | Sin default |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| stock_actual | float | Obligatorio | Field( ge=0 ) |
| consumo | ConsumoInfo | Obligatorio | Sin default |
| cobertura | CoberturaInfo | Obligatorio | Sin default |
| lead_time_dias | int | Obligatorio | Field( ge=0 ) |
| forecast | ForecastInfo | Obligatorio | Sin default |
| seguridad | SeguridadInfo | Obligatorio | Sin default |
| riesgo | RiesgoInfo | Obligatorio | Sin default |
| reposicion | Optional[ ReposicionInfo ] | Omitible; nullable | None |
| explicacion | Optional[str] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class InventoryRiskResponse(BaseModel):
    id_empresa: str
    id_almacen: str
    id_inventario: str
    id_producto: str

    stock_actual: float = Field(
        ge=0
    )

    consumo: ConsumoInfo

    cobertura: CoberturaInfo

    lead_time_dias: int = Field(
        ge=0
    )

    forecast: ForecastInfo

    seguridad: SeguridadInfo

    riesgo: RiesgoInfo

    reposicion: Optional[
        ReposicionInfo
    ] = None

    explicacion: Optional[str] = None
```

## TipoMovimiento

Fuente: `app/dto/movimiento_dto.py`.


Declaracion y validadores exactos:

```python
class TipoMovimiento(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"
```

## MotivoMovimiento

Fuente: `app/dto/movimiento_dto.py`.


Declaracion y validadores exactos:

```python
class MotivoMovimiento(str, Enum):
    RECEPCION = "RECEPCION"
    REPOSICION = "REPOSICION"
    VENTA = "VENTA"
    MERMA = "MERMA"
    VENCIMIENTO = "VENCIMIENTO"
    DEVOLUCION = "DEVOLUCION"
    CONTEO_FISICO = "CONTEO_FISICO"
    OTRO = "OTRO"
```

## MovimientoCreate

Fuente: `app/dto/movimiento_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_inventario | str | Obligatorio | Sin default |
| id_operario | Optional[str] | Omitible; nullable | None |
| id_detalle_recepcion | Optional[str] | Omitible; nullable | None |
| tipo_movimiento | TipoMovimiento | Obligatorio | Sin default |
| motivo_movimiento | MotivoMovimiento | Obligatorio | Sin default |
| cantidad | int | Obligatorio | Field(..., gt=0) |
| observacion | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
class MovimientoCreate(BaseModel):
    id_inventario: str

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
```

## MovimientoResponse

Fuente: `app/dto/movimiento_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_movimiento | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_detalle_recepcion | Optional[str] | Omitible; nullable | None |
| id_producto | str | Obligatorio | Sin default |
| id_rack | str | Obligatorio | Sin default |
| id_operario | str | Obligatorio | Sin default |
| operario_nombre | Optional[str] | Omitible; nullable | None |
| id_zona | Optional[str] | Omitible; nullable | None |
| tipo_movimiento | TipoMovimiento | Obligatorio | Sin default |
| motivo_movimiento | MotivoMovimiento | Obligatorio | Sin default |
| cantidad | int | Obligatorio | Sin default |
| stock_anterior | int | Obligatorio | Sin default |
| stock_nuevo | int | Obligatorio | Sin default |
| observacion | Optional[str] | Omitible; nullable | None |
| fecha_hora | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class MovimientoResponse(BaseModel):
    id_movimiento: str

    id_inventario: str
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
```

## OperarioCreate

Fuente: `app/dto/operario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_almacen | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| apellido | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| correo | EmailStr | Obligatorio | Sin default |
| cargo | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| turno | str | Obligatorio | Field( ..., min_length=2, max_length=50 ) |
| estado | str | Omitible | Field( default="ACTIVO", min_length=2, max_length=50 ) |
| correo | EmailStr | Obligatorio | Sin default |
| password_temporal | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class OperarioCreate(BaseModel):

    id_empresa: Optional[str] = None

    id_almacen: str

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    apellido: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    correo: EmailStr

    cargo: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    turno: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    estado: str = Field(
        default="ACTIVO",
        min_length=2,
        max_length=50
    )

    correo: EmailStr

    password_temporal: str = Field(
        ...,
        min_length=6,
        max_length=128
    )


# ============================================================
# ACTUALIZAR OPERARIO
# ============================================================
```

## OperarioUpdate

Fuente: `app/dto/operario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_almacen | Optional[str] | Omitible; nullable | None |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| apellido | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| cargo | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| turno | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=50 ) |
| estado | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=50 ) |

Declaracion y validadores exactos:

```python
class OperarioUpdate(BaseModel):

    id_almacen: Optional[str] = None

    correo: Optional[EmailStr] = None

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    apellido: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    correo: Optional[EmailStr] = None

    cargo: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    turno: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    estado: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50
    )


# ============================================================
# RESET PASSWORD (EMPRESA)
#
# POST /operarios/{id}/reset-password
# ============================================================
```

## OperarioResetPassword

Fuente: `app/dto/operario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| password_temporal | str | Obligatorio | Field( ..., min_length=6, max_length=128 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class OperarioResetPassword(BaseModel):

    password_temporal: str = Field(
        ...,
        min_length=6,
        max_length=128
    )

    # Opcional: permite dar correo a un operario
    # antiguo sin cuenta en la misma llamada.
    correo: Optional[EmailStr] = None


# ============================================================
# RESPONSE
#
# Nunca incluye el hash de la contraseña.
# id_almacen / correo son opcionales para operarios
# antiguos creados antes de las cuentas.
# ============================================================
```

## OperarioResponse

Fuente: `app/dto/operario_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_operario | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| apellido | str | Obligatorio | Sin default |
| cargo | str | Obligatorio | Sin default |
| turno | str | Obligatorio | Sin default |
| estado | str | Obligatorio | Sin default |
| id_almacen | Optional[str] | Omitible; nullable | None |
| correo_verificado | bool | Omitible | False |
| fecha_verificacion_correo | Optional[datetime] | Omitible; nullable | None |
| correo | Optional[str] | Omitible; nullable | None |
| tiene_cuenta | bool | Omitible | False |
| debe_cambiar_password | bool | Omitible | False |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class OperarioResponse(BaseModel):

    id_operario: str
    id_empresa: str

    nombre: str
    apellido: str
    cargo: str
    turno: str
    estado: str

    id_almacen: Optional[str] = None
    correo_verificado: bool = False
    fecha_verificacion_correo: Optional[datetime] = None

    correo: Optional[str] = None

    tiene_cuenta: bool = False

    debe_cambiar_password: bool = False

    fecha_creacion: datetime
    fecha_actualizacion: datetime
```

## EstadoOrdenReposicion

Fuente: `app/dto/orden_reposicion_dto.py`.


Declaracion y validadores exactos:

```python
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
```

## OrigenOrden

Fuente: `app/dto/orden_reposicion_dto.py`.


Declaracion y validadores exactos:

```python
class OrigenOrden(str, Enum):
    MANUAL = "MANUAL"
    RECOMENDACION_IA = "RECOMENDACION_IA"
```

## OrdenReposicionCreate

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_recomendacion | Optional[str] | Omitible; nullable | None |
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_almacen | Optional[str] | Omitible; nullable | None |
| id_proveedor | str | Obligatorio | Sin default |
| lineas | list[DetalleReposicionCreate] | Omitible | [] |
| fecha_estimada_recepcion | Optional[datetime] | Omitible; nullable | None |
| origen | OrigenOrden | Omitible | OrigenOrden.MANUAL |
| observacion | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
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
```

## OrdenReposicionUpdate

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_proveedor | Optional[str] | Omitible; nullable | None |
| fecha_estimada_recepcion | Optional[datetime] | Omitible; nullable | None |
| observacion | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
class OrdenReposicionUpdate(BaseModel):
    id_proveedor: Optional[str] = None
    fecha_estimada_recepcion: Optional[datetime] = None
    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )
```

## OrdenReposicionResponse

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_orden_reposicion | str | Obligatorio | Sin default |
| id_recomendacion | Optional[str] | Omitible; nullable | None |
| id_empresa | str | Obligatorio | Sin default |
| id_almacen | str | Obligatorio | Sin default |
| id_proveedor | str | Obligatorio | Sin default |
| origen | OrigenOrden | Obligatorio | Sin default |
| estado | EstadoOrdenReposicion | Obligatorio | Sin default |
| fecha_orden | datetime | Obligatorio | Sin default |
| fecha_estimada_recepcion | Optional[datetime] | Omitible; nullable | None |
| observacion | Optional[str] | Omitible; nullable | None |
| id_operario_solicitante | Optional[str] | Omitible; nullable | None |
| comentario_empresa | Optional[str] | Omitible; nullable | None |
| despacho | Optional[dict] | Omitible; nullable | None |
| fecha_despacho | Optional[datetime] | Omitible; nullable | None |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
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
```

## DevolverOrdenRequest

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| comentario | str | Obligatorio | Field( ..., min_length=1, max_length=1000 ) |

Declaracion y validadores exactos:

```python
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
```

## LineaDespacho

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_detalle_reposicion | str | Obligatorio | Sin default |
| cantidad | int | Obligatorio | Field( ..., gt=0 ) |
| fecha_vencimiento | Optional[datetime] | Omitible; nullable | None |
| temperatura | Optional[float] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class LineaDespacho(BaseModel):
    id_detalle_reposicion: str

    cantidad: int = Field(
        ...,
        gt=0
    )

    fecha_vencimiento: Optional[datetime] = None

    temperatura: Optional[float] = None
```

## DespachoRequest

Fuente: `app/dto/orden_reposicion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| lineas | list[LineaDespacho] | Obligatorio | Field( min_length=1 ) |
| observacion | Optional[str] | Omitible; nullable | Field( default=None, max_length=500 ) |

Declaracion y validadores exactos:

```python
class DespachoRequest(BaseModel):
    lineas: list[LineaDespacho] = Field(
        min_length=1
    )

    observacion: Optional[str] = Field(
        default=None,
        max_length=500
    )
```

## ProductoCreate

Fuente: `app/dto/producto_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_proveedor | Optional[str] | Omitible; nullable | None |
| id_rack | Optional[str] | Omitible; nullable | None |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=150 ) |
| categoria | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| familia | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| marca | Optional[str] | Omitible; nullable | None |
| peso | float | Obligatorio | Field( ..., gt=0 ) |
| volumen | Optional[float] | Omitible; nullable | Field( default=None, gt=0 ) |
| stock | int | Omitible | Field( default=0, ge=0 ) |
| requiere_refrigeracion | bool | Omitible | False |
| temperatura_min_almacenamiento | Optional[float] | Omitible; nullable | None |
| temperatura_max_almacenamiento | Optional[float] | Omitible; nullable | None |
| lead_time_dias | int | Obligatorio | Field( ..., ge=0 ) |
| vida_util_dias | int | Obligatorio | Field( ..., ge=1 ) |

Declaracion y validadores exactos:

```python
class ProductoCreate(BaseModel):

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
        gt=0
    )

    volumen: Optional[float] = Field(
        default=None,
        gt=0
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
```

## ProductoUpdate

Fuente: `app/dto/producto_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_rack | Optional[str] | Omitible; nullable | None |
| nombre | Optional[str] | Omitible; nullable | None |
| categoria | Optional[str] | Omitible; nullable | None |
| familia | Optional[str] | Omitible; nullable | None |
| marca | Optional[str] | Omitible; nullable | None |
| peso | Optional[float] | Omitible; nullable | None |
| volumen | Optional[float] | Omitible; nullable | None |
| stock | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| requiere_refrigeracion | Optional[bool] | Omitible; nullable | None |
| temperatura_min_almacenamiento | Optional[float] | Omitible; nullable | None |
| temperatura_max_almacenamiento | Optional[float] | Omitible; nullable | None |
| lead_time_dias | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| vida_util_dias | Optional[int] | Omitible; nullable | Field( default=None, ge=1 ) |

Declaracion y validadores exactos:

```python
class ProductoUpdate(BaseModel):

    id_rack: Optional[str] = None

    nombre: Optional[str] = None
    categoria: Optional[str] = None
    familia: Optional[str] = None
    marca: Optional[str] = None

    peso: Optional[float] = None
    volumen: Optional[float] = None

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
```

## ProductoResponse

Fuente: `app/dto/producto_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_producto | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| id_proveedor | Optional[str] | Omitible; nullable | None |
| id_rack | Optional[str] | Omitible; nullable | None |
| nombre | str | Obligatorio | Sin default |
| categoria | str | Obligatorio | Sin default |
| familia | str | Obligatorio | Sin default |
| marca | Optional[str] | Omitible; nullable | None |
| peso | Optional[float] | Omitible; nullable | None |
| volumen | Optional[float] | Omitible; nullable | None |
| stock | int | Omitible | 0 |
| requiere_refrigeracion | bool | Omitible | False |
| temperatura_min_almacenamiento | Optional[float] | Omitible; nullable | None |
| temperatura_max_almacenamiento | Optional[float] | Omitible; nullable | None |
| lead_time_dias | int | Obligatorio | Sin default |
| vida_util_dias | int | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class ProductoResponse(BaseModel):

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
```

## EstadoProveedor

Fuente: `app/dto/proveedor_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoProveedor(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
```

## ProveedorCreate

Fuente: `app/dto/proveedor_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=150 ) |
| ruc | str | Obligatorio | Field( ..., min_length=11, max_length=11 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| telefono | Optional[str] | Omitible; nullable | Field( default=None, max_length=20 ) |
| direccion | Optional[str] | Omitible; nullable | Field( default=None, max_length=250 ) |
| tiempo_entrega_estimado_dias | int | Omitible | Field( default=1, ge=0 ) |
| estado | EstadoProveedor | Omitible | EstadoProveedor.ACTIVO |
| password_temporal | Optional[str] | Omitible; nullable | Field( default=None, min_length=6, max_length=128 ) |

Declaracion y validadores exactos:

```python
class ProveedorCreate(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    ruc: str = Field(
        ...,
        min_length=11,
        max_length=11
    )

    correo: Optional[EmailStr] = None

    telefono: Optional[str] = Field(
        default=None,
        max_length=20
    )

    direccion: Optional[str] = Field(
        default=None,
        max_length=250
    )

    tiempo_entrega_estimado_dias: int = Field(
        default=1,
        ge=0
    )

    estado: EstadoProveedor = EstadoProveedor.ACTIVO

    # Cuenta de acceso (rol PROVEEDOR). Requiere correo.
    # Queda con debe_cambiar_password = true.
    password_temporal: Optional[str] = Field(
        default=None,
        min_length=6,
        max_length=128
    )
```

## ProveedorUpdate

Fuente: `app/dto/proveedor_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=150 ) |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| telefono | Optional[str] | Omitible; nullable | Field( default=None, max_length=20 ) |
| direccion | Optional[str] | Omitible; nullable | Field( default=None, max_length=250 ) |
| tiempo_entrega_estimado_dias | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| estado | Optional[EstadoProveedor] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    correo: Optional[EmailStr] = None

    telefono: Optional[str] = Field(
        default=None,
        max_length=20
    )

    direccion: Optional[str] = Field(
        default=None,
        max_length=250
    )

    tiempo_entrega_estimado_dias: Optional[int] = Field(
        default=None,
        ge=0
    )

    estado: Optional[EstadoProveedor] = None
```

## ProveedorResponse

Fuente: `app/dto/proveedor_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_proveedor | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| ruc | str | Obligatorio | Sin default |
| correo | Optional[EmailStr] | Omitible; nullable | None |
| tiene_cuenta | bool | Omitible | False |
| debe_cambiar_password | bool | Omitible | False |
| correo_verificado | bool | Omitible | False |
| fecha_verificacion_correo | Optional[datetime] | Omitible; nullable | None |
| telefono | Optional[str] | Omitible; nullable | None |
| direccion | Optional[str] | Omitible; nullable | None |
| tiempo_entrega_estimado_dias | int | Obligatorio | Sin default |
| estado | EstadoProveedor | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class ProveedorResponse(BaseModel):
    id_proveedor: str
    id_empresa: str

    nombre: str
    ruc: str

    correo: Optional[EmailStr] = None
    tiene_cuenta: bool = False
    debe_cambiar_password: bool = False
    correo_verificado: bool = False
    fecha_verificacion_correo: Optional[datetime] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None

    tiempo_entrega_estimado_dias: int

    estado: EstadoProveedor

    fecha_creacion: datetime
    fecha_actualizacion: datetime
```

## EstadoRack

Fuente: `app/dto/rack_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoRack(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    LLENO = "LLENO"
    MANTENIMIENTO = "MANTENIMIENTO"
```

## RackCreate

Fuente: `app/dto/rack_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_zona | str | Obligatorio | Sin default |
| codigo | str | Obligatorio | Field( min_length=1, max_length=50 ) |
| nivel | int | Obligatorio | Field( ge=1 ) |
| capacidad | float | Obligatorio | Field( gt=0 ) |
| temperatura_min | float &#124; None | Omitible; nullable | None |
| temperatura_max | float &#124; None | Omitible; nullable | None |
| estado | EstadoRack | Omitible | EstadoRack.DISPONIBLE |

Declaracion y validadores exactos:

```python
class RackCreate(BaseModel):
    id_zona: str

    codigo: str = Field(
        min_length=1,
        max_length=50
    )

    nivel: int = Field(
        ge=1
    )

    capacidad: float = Field(
        gt=0
    )

    temperatura_min: float | None = None

    temperatura_max: float | None = None

    estado: EstadoRack = EstadoRack.DISPONIBLE

    @model_validator(mode="after")
    def validar(self):
        return _validar_rango(self)


# ============================================================
# EDITAR RACK (OPERARIO de ese almacén)
#
# Solo estado y temperatura.
# ============================================================
```

## RackUpdate

Fuente: `app/dto/rack_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| estado | EstadoRack &#124; None | Omitible; nullable | None |
| temperatura_min | float &#124; None | Omitible; nullable | None |
| temperatura_max | float &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class RackUpdate(BaseModel):

    estado: EstadoRack | None = None

    temperatura_min: float | None = None

    temperatura_max: float | None = None

    @model_validator(mode="after")
    def validar(self):
        return _validar_rango(self)
```

## RackResponse

Fuente: `app/dto/rack_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_rack | str | Obligatorio | Sin default |
| id_zona | str | Obligatorio | Sin default |
| codigo | str | Obligatorio | Sin default |
| nivel | int | Obligatorio | Sin default |
| capacidad | float | Obligatorio | Sin default |
| estado | EstadoRack | Obligatorio | Sin default |
| temperatura_min | float &#124; None | Omitible; nullable | None |
| temperatura_max | float &#124; None | Omitible; nullable | None |
| carga_kg | float | Omitible | 0 |
| libre_kg | float | Omitible | 0 |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class RackResponse(BaseModel):
    id_rack: str
    id_zona: str

    codigo: str

    nivel: int

    # Carga máxima en kg
    capacidad: float

    estado: EstadoRack

    # Racks antiguos / zonas no refrigeradas -> null
    temperatura_min: float | None = None

    temperatura_max: float | None = None

    # Σ stock_actual × peso del producto
    carga_kg: float = 0

    # capacidad - carga_kg
    libre_kg: float = 0

    fecha_creacion: datetime

    fecha_actualizacion: datetime


# ============================================================
# RACK DISPONIBLE
#
# GET /racks/disponiblesiid_almacen=&id_producto=&cantidad=
# ============================================================
```

## RackDisponibleResponse

Fuente: `app/dto/rack_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_almacen | str | Obligatorio | Sin default |
| nombre_zona | str &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class RackDisponibleResponse(RackResponse):

    id_almacen: str

    nombre_zona: str | None = None
```

## RecepcionMercaderiaCreate

Fuente: `app/dto/recepcion_mercaderia_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_orden_reposicion | str | Obligatorio | Sin default |
| id_operario | str &#124; None | Omitible; nullable | None |
| fecha_recepcion | datetime &#124; None | Omitible; nullable | None |
| observaciones_generales | str &#124; None | Omitible; nullable | Field( default=None, max_length=1000 ) |
| detalles | list[ DetalleRecepcionCreate ] | Obligatorio | Field(min_length=1) |

Declaracion y validadores exactos:

```python
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
```

## RecepcionMercaderiaResponse

Fuente: `app/dto/recepcion_mercaderia_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_recepcion | str | Obligatorio | Sin default |
| id_orden_reposicion | str | Obligatorio | Sin default |
| id_operario | str | Obligatorio | Sin default |
| fecha_recepcion | datetime | Obligatorio | Sin default |
| observaciones_generales | str &#124; None | Obligatorio; nullable | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| detalles | list[ DetalleRecepcionResponse ] | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
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
```

## UbicarDetalleRecepcion

Fuente: `app/dto/recepcion_mercaderia_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_rack | str | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class UbicarDetalleRecepcion(BaseModel):

    id_rack: str
```

## ResolverEvaluacion

Fuente: `app/dto/recepcion_mercaderia_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_operario | str &#124; None | Omitible; nullable | None |
| estado_recepcion | EstadoRecepcion | Obligatorio | Sin default |
| comentario_resolucion | str | Obligatorio | Field( min_length=1, max_length=1000 ) |
| cantidad_aceptada | int &#124; None | Omitible; nullable | Field( default=None, ge=0 ) |
| cantidad_rechazada | int &#124; None | Omitible; nullable | Field( default=None, ge=0 ) |
| id_inventario | str &#124; None | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
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
```

## TipoRecomendacion

Fuente: `app/dto/recomendacion_dto.py`.


Declaracion y validadores exactos:

```python
class TipoRecomendacion(str, Enum):
    REABASTECER = "REABASTECER"
    NO_REABASTECER = "NO_REABASTECER"
    REDUCIR_REPOSICION = "REDUCIR_REPOSICION"
    TRASLADAR_STOCK = "TRASLADAR_STOCK"
    REVISAR_CONSUMO = "REVISAR_CONSUMO"
    REVISAR_INVENTARIO = "REVISAR_INVENTARIO"
```

## EstadoRecomendacion

Fuente: `app/dto/recomendacion_dto.py`.


Declaracion y validadores exactos:

```python
class EstadoRecomendacion(str, Enum):
    PENDIENTE = "PENDIENTE"
    VALIDADA_OPERARIO = "VALIDADA_OPERARIO"
    CAMBIOS_SOLICITADOS = "CAMBIOS_SOLICITADOS"
    APROBADA_EMPRESA = "APROBADA_EMPRESA"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    APLICADA = "APLICADA"
    EXPIRADA = "EXPIRADA"
```

## RecomendacionCreate

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| id_alerta | Optional[str] | Omitible; nullable | None |
| tipo_recomendacion | ( TipoRecomendacion ) | Obligatorio | Sin default |
| nivel_riesgo | NivelRiesgo | Obligatorio | Sin default |
| cantidad_minima | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| cantidad_recomendada | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| cantidad_segura | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |
| forecast_7d | Optional[float] | Omitible; nullable | Field( default=None, ge=0 ) |
| explicacion | str | Obligatorio | Field( min_length=3, max_length=3000 ) |
| origen | str | Omitible | Field( default="PSITWIN", min_length=2, max_length=100 ) |

Declaracion y validadores exactos:

```python
class RecomendacionCreate(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    id_almacen: str
    id_inventario: str
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
```

## RecomendacionResponse

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_recomendacion | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| id_almacen | str | Obligatorio | Sin default |
| id_inventario | str | Obligatorio | Sin default |
| id_producto | str | Obligatorio | Sin default |
| id_alerta | Optional[str] | Omitible; nullable | None |
| tipo_recomendacion | ( TipoRecomendacion ) | Obligatorio | Sin default |
| nivel_riesgo | NivelRiesgo | Obligatorio | Sin default |
| cantidad_minima | Optional[int] | Omitible; nullable | None |
| cantidad_recomendada | Optional[int] | Omitible; nullable | None |
| cantidad_segura | Optional[int] | Omitible; nullable | None |
| forecast_7d | Optional[float] | Omitible; nullable | None |
| explicacion | str | Obligatorio | Sin default |
| origen | str | Obligatorio | Sin default |
| estado | EstadoRecomendacion | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |
| fecha_aplicacion | Optional[datetime] | Omitible; nullable | None |
| notificacion_aprobacion | Optional[dict] | Omitible; nullable | None |

Declaracion y validadores exactos:

```python
class RecomendacionResponse(BaseModel):
    id_recomendacion: str

    id_empresa: str
    id_almacen: str
    id_inventario: str
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
```

## RecomendacionEstadoUpdate

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| estado | EstadoRecomendacion | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class RecomendacionEstadoUpdate(
    BaseModel
):
    estado: EstadoRecomendacion
```

## EmpresaCambiosRequest

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| comentario | str | Obligatorio | Field(..., min_length=1, max_length=1000) |

Declaracion y validadores exactos:

```python
class EmpresaCambiosRequest(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    comentario: str = Field(..., min_length=1, max_length=1000)
```

## EmpresaRechazoRequest

Fuente: `app/dto/recomendacion_dto.py`.


Declaracion y validadores exactos:

```python
class EmpresaRechazoRequest(EmpresaCambiosRequest):
    pass
```

## EmpresaAprobacionRequest

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_empresa | Optional[str] | Omitible; nullable | None |
| id_proveedor | str | Obligatorio | Sin default |
| costo_unitario | float | Obligatorio | Field(..., ge=0) |
| fecha_estimada_recepcion | Optional[datetime] | Omitible; nullable | None |
| observacion | Optional[str] | Omitible; nullable | Field(default=None, max_length=500) |

Declaracion y validadores exactos:

```python
class EmpresaAprobacionRequest(BaseModel):
    # Se ignora: se toma del token.
    id_empresa: Optional[str] = None
    id_proveedor: str
    costo_unitario: float = Field(..., ge=0)
    fecha_estimada_recepcion: Optional[datetime] = None
    observacion: Optional[str] = Field(default=None, max_length=500)
```

## PropuestaRecomendacionUpdate

Fuente: `app/dto/recomendacion_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| cantidad_recomendada | Optional[int] | Omitible; nullable | Field(default=None, ge=1) |
| explicacion | Optional[str] | Omitible; nullable | Field(default=None, min_length=3, max_length=3000) |

Declaracion y validadores exactos:

```python
class PropuestaRecomendacionUpdate(BaseModel):
    cantidad_recomendada: Optional[int] = Field(default=None, ge=1)
    explicacion: Optional[str] = Field(default=None, min_length=3, max_length=3000)
```

## SaikiAskRequest

Fuente: `app/dto/saiki_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| message | str &#124; None | Omitible; nullable | Field(default=None, min_length=1) |
| question | str &#124; None | Omitible; nullable | Field( default=None, min_length=1, description="Alias legacy de message. No es necesario para nuevas consultas.", ) |
| id_inventario | str &#124; None | Omitible; nullable | None |
| id_producto | str &#124; None | Omitible; nullable | None |
| page | int | Omitible | Field(default=1, ge=1, description="Página del detalle de inventario.") |
| page_size | int | Omitible | Field(default=25, ge=1, le=100) |
| context | dict[str, Any] | Omitible | Field( default_factory=dict, description="Contexto técnico opcional; normalmente debe omitirse.", ) |
| history | list[dict[str, Any]] | Omitible | Field( default_factory=list, description="Historial opcional de mensajes previos.", ) |

Declaracion y validadores exactos:

```python
class SaikiAskRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["message"],
            "examples": [
                {
                    "message": "Hola Saiki, ¿cómo está mi inventario?"
                },
                {
                    "message": "¿Qué productos tienen riesgo de quedarse sin stock?"
                },
            ],
        }
    )

    message: str | None = Field(default=None, min_length=1)
    question: str | None = Field(
        default=None,
        min_length=1,
        description="Alias legacy de message. No es necesario para nuevas consultas.",
    )
    id_inventario: str | None = None
    id_producto: str | None = None
    page: int = Field(default=1, ge=1, description="Página del detalle de inventario.")
    page_size: int = Field(default=25, ge=1, le=100)
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto técnico opcional; normalmente debe omitirse.",
    )
    history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Historial opcional de mensajes previos.",
    )

    @model_validator(mode="after")
    def require_message(self):
        if not self.message and not self.question:
            raise ValueError("Debe indicar message o question.")
        if self.message and self.question and self.message != self.question:
            raise ValueError("message y question no pueden ser diferentes.")
        if not self.message:
            self.message = self.question
        if not self.message.strip():
            raise ValueError("message no puede contener solo espacios.")
        if len(self.history) > 40:
            raise ValueError("El historial admite hasta 40 mensajes.")
        for item in self.history:
            if item.get("role") not in {"user", "assistant"} or not isinstance(item.get("content"), str):
                raise ValueError("El historial solo admite mensajes de usuario y asistente con contenido textual.")
            if len(item["content"]) > 8000:
                raise ValueError("Un mensaje del historial supera el límite de tamaño.")
            if set(item) - {"role", "content"}:
                raise ValueError("El historial no admite instrucciones de herramientas.")
        return self
```

## SaikiAskResponse

Fuente: `app/dto/saiki_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| answer | str | Obligatorio | Sin default |
| model | str | Obligatorio | Sin default |
| base_url | str | Obligatorio | Sin default |
| source | str | Omitible | "ollama" |
| context | dict[str, Any] | Omitible | Field(default_factory=dict) |
| warnings | list[str] | Omitible | Field(default_factory=list) |
| data | dict[str, Any] | Omitible | Field(default_factory=dict) |
| visualization | dict[str, Any] | Omitible | Field( default_factory=lambda: {"type": "none"} ) |
| sources | list[str] | Omitible | Field(default_factory=list) |

Declaracion y validadores exactos:

```python
class SaikiAskResponse(BaseModel):
    answer: str
    model: str
    base_url: str
    source: str = "ollama"
    context: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    visualization: dict[str, Any] = Field(
        default_factory=lambda: {"type": "none"}
    )
    sources: list[str] = Field(default_factory=list)
```

## ZonaCreate

Fuente: `app/dto/zona_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id_almacen | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| tipo_zona | str | Obligatorio | Field( ..., min_length=2, max_length=100 ) |
| refrigerada | bool | Omitible | False |
| temperatura_min | Optional[float] | Omitible; nullable | None |
| temperatura_max | Optional[float] | Omitible; nullable | None |
| capacidad | int | Obligatorio | Field( ..., ge=0 ) |

Declaracion y validadores exactos:

```python
class ZonaCreate(BaseModel):

    id_almacen: str

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    tipo_zona: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    # Lo decide la empresa al crear la zona.
    # Solo los racks de zonas refrigeradas tienen temperatura.
    refrigerada: bool = False

    temperatura_min: Optional[float] = None

    temperatura_max: Optional[float] = None

    # Cantidad de niveles (un rack por nivel).
    capacidad: int = Field(
        ...,
        ge=0
    )


# ============================================================
# ACTUALIZAR ZONA
# ============================================================
```

## ZonaUpdate

Fuente: `app/dto/zona_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| nombre | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| tipo_zona | Optional[str] | Omitible; nullable | Field( default=None, min_length=2, max_length=100 ) |
| refrigerada | Optional[bool] | Omitible; nullable | None |
| temperatura_min | Optional[float] | Omitible; nullable | None |
| temperatura_max | Optional[float] | Omitible; nullable | None |
| capacidad | Optional[int] | Omitible; nullable | Field( default=None, ge=0 ) |

Declaracion y validadores exactos:

```python
class ZonaUpdate(BaseModel):

    nombre: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    tipo_zona: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    refrigerada: Optional[bool] = None

    temperatura_min: Optional[float] = None

    temperatura_max: Optional[float] = None

    capacidad: Optional[int] = Field(
        default=None,
        ge=0
    )


# ============================================================
# RESPONSE
#
# Acepta:
#
# id
# id_zona
#
# pero siempre responde como:
#
# id
# ============================================================
```

## ZonaResponse

Fuente: `app/dto/zona_dto.py`.

| Campo | Tipo exacto | Presencia | Default / restricciones Field |
|---|---|---|---|
| id | str | Obligatorio | Field( validation_alias=AliasChoices( "id", "id_zona" ) ) |
| id_almacen | str | Obligatorio | Sin default |
| id_empresa | str | Obligatorio | Sin default |
| nombre | str | Obligatorio | Sin default |
| tipo_zona | str | Obligatorio | Sin default |
| refrigerada | bool | Omitible | False |
| temperatura_min | Optional[float] | Omitible; nullable | None |
| temperatura_max | Optional[float] | Omitible; nullable | None |
| capacidad | int | Obligatorio | Sin default |
| fecha_creacion | datetime | Obligatorio | Sin default |
| fecha_actualizacion | datetime | Obligatorio | Sin default |

Declaracion y validadores exactos:

```python
class ZonaResponse(BaseModel):

    id: str = Field(
        validation_alias=AliasChoices(
            "id",
            "id_zona"
        )
    )

    id_almacen: str

    id_empresa: str

    nombre: str

    tipo_zona: str

    # Documentos antiguos sin el campo -> False
    refrigerada: bool = False

    temperatura_min: Optional[float] = None

    temperatura_max: Optional[float] = None

    capacidad: int

    fecha_creacion: datetime

    fecha_actualizacion: datetime
```

## Ejemplos JSON de las 14 entidades reales

Validos por forma/declaracion Response; revision estatica, no ejecucion Pydantic. Ejemplos aislados, no un ledger reconciliado ni datos generados. No se entregan credenciales.

### EmpresaResponse

```json
{
  "id_empresa": "EMP-001",
  "nombre": "Alimentos Demo",
  "ruc": "20999999991",
  "sector": "Alimentos",
  "correo": "empresa@example.com",
  "telefono": "51999999001",
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### AlmacenResponse

```json
{
  "id": "ALM-001",
  "id_empresa": "EMP-001",
  "nombre": "Central Lima",
  "longitud": "-77.042800",
  "latitud": "-12.046400",
  "area_m2": 1200,
  "aforo": 25,
  "tipo_almacen": "Mixto",
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### ZonaResponse

```json
{
  "id": "ZON-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "nombre": "Zona seca",
  "tipo_zona": "Seca",
  "refrigerada": false,
  "temperatura_min": null,
  "temperatura_max": null,
  "capacidad": 5,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### RackResponse

```json
{
  "id_rack": "RAC-001",
  "id_zona": "ZON-001",
  "codigo": "SECO-01",
  "nivel": 1,
  "capacidad": 5000,
  "estado": "DISPONIBLE",
  "temperatura_min": null,
  "temperatura_max": null,
  "carga_kg": 100,
  "libre_kg": 4900,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### ProductoResponse

```json
{
  "id_producto": "PRO-001",
  "id_empresa": "EMP-001",
  "id_proveedor": "PRV-001",
  "id_rack": "RAC-001",
  "nombre": "Arroz 1 kg",
  "categoria": "Abarrotes",
  "familia": "Cereales",
  "marca": "Demo",
  "peso": 1,
  "volumen": null,
  "stock": 0,
  "requiere_refrigeracion": false,
  "temperatura_min_almacenamiento": null,
  "temperatura_max_almacenamiento": null,
  "lead_time_dias": 3,
  "vida_util_dias": 365,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### InventarioResponse

```json
{
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "id_rack": "RAC-001",
  "stock_actual": 100,
  "stock_minimo": 40,
  "stock_maximo": 500,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### OperarioResponse

```json
{
  "id_operario": "OPE-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "nombre": "Carlos",
  "apellido": "Demo",
  "cargo": "Almacenero",
  "turno": "Manana",
  "estado": "ACTIVO",
  "correo": "operario1@example.com",
  "tiene_cuenta": false,
  "debe_cambiar_password": false,
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### ProveedorResponse

```json
{
  "id_proveedor": "PRV-001",
  "id_empresa": "EMP-001",
  "nombre": "Distribuidora Demo",
  "ruc": "20999999992",
  "correo": null,
  "telefono": null,
  "direccion": null,
  "tiempo_entrega_estimado_dias": 3,
  "estado": "ACTIVO",
  "tiene_cuenta": false,
  "debe_cambiar_password": false,
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### MovimientoResponse

```json
{
  "id_movimiento": "MOV-001",
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "id_rack": "RAC-001",
  "id_operario": "OPE-001",
  "id_detalle_recepcion": null,
  "operario_nombre": "Carlos Demo",
  "id_zona": "ZON-001",
  "tipo_movimiento": "SALIDA",
  "motivo_movimiento": "VENTA",
  "cantidad": 10,
  "stock_anterior": 110,
  "stock_nuevo": 100,
  "observacion": "Movimiento sintetico",
  "fecha_hora": "2025-12-31T12:00:00Z"
}
```

### OrdenReposicionResponse

```json
{
  "id_orden_reposicion": "ORD-001",
  "id_recomendacion": null,
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_proveedor": "PRV-001",
  "origen": "MANUAL",
  "estado": "RECIBIDA",
  "fecha_orden": "2025-12-20T09:00:00Z",
  "fecha_estimada_recepcion": "2025-12-23T09:00:00Z",
  "observacion": "Orden sintetica",
  "id_operario_solicitante": "OPE-001",
  "comentario_empresa": null,
  "despacho": null,
  "fecha_despacho": null,
  "fecha_creacion": "2025-12-20T09:00:00Z",
  "fecha_actualizacion": "2025-12-23T10:00:00Z"
}
```

### DetalleReposicionResponse

```json
{
  "id_detalle_reposicion": "DOR-001",
  "id_orden_reposicion": "ORD-001",
  "id_producto": "PRO-001",
  "cantidad_solicitada": 100,
  "costo_unitario": 3,
  "fecha_creacion": "2025-12-20T09:00:00Z",
  "fecha_actualizacion": "2025-12-20T09:00:00Z"
}
```

### DetalleRecepcionResponse

```json
{
  "id_detalle_recepcion": "DRE-001",
  "id_recepcion": "REC-001",
  "id_detalle_reposicion": "DOR-001",
  "id_inventario": "INV-001",
  "cantidad_recibida": 100,
  "cantidad_rechazada": 0,
  "cantidad_aceptada": 100,
  "lote": "DEMO-20251223",
  "fecha_vencimiento": "2026-12-23T00:00:00Z",
  "temperatura_recepcion": null,
  "estado_recepcion": "CONFORME",
  "comentario_recepcion": null,
  "motivo_rechazo": null,
  "id_movimiento": "MOV-ENT-001",
  "ubicado": true,
  "riesgo_antes": null,
  "riesgo_despues": null,
  "notificacion_final": null,
  "fecha_creacion": "2025-12-23T10:00:00Z"
}
```

### AlertaResponse

```json
{
  "id_alerta": "ALE-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "tipo_alerta": "STOCK_BAJO",
  "nivel_riesgo": "ALTO",
  "titulo": "Stock bajo demo",
  "mensaje": "Stock cercano al minimo",
  "stock_actual": 20,
  "dias_cobertura": null,
  "stock_seguridad": null,
  "punto_reposicion": null,
  "forecast_7d": null,
  "estado": "ACTIVA",
  "fecha_creacion": "2025-12-31T23:59:59Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z",
  "fecha_resolucion": null
}
```

### RecomendacionResponse

```json
{
  "id_recomendacion": "RECO-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "id_alerta": null,
  "tipo_recomendacion": "REABASTECER",
  "nivel_riesgo": "ALTO",
  "cantidad_minima": 85,
  "cantidad_recomendada": 100,
  "cantidad_segura": 115,
  "forecast_7d": null,
  "explicacion": "Ejemplo sintetico de contrato, no inferencia ejecutada",
  "origen": "DEMO_SINTETICO",
  "estado": "PENDIENTE",
  "fecha_creacion": "2025-12-31T23:59:59Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z",
  "fecha_aplicacion": null,
  "notificacion_aprobacion": null
}
```

### RecepcionMercaderiaResponse

```json
{
  "id_recepcion": "REC-001",
  "id_orden_reposicion": "ORD-001",
  "id_operario": "OPE-001",
  "fecha_recepcion": "2025-12-23T10:00:00Z",
  "observaciones_generales": null,
  "fecha_creacion": "2025-12-23T10:00:00Z",
  "detalles": [
    {
      "id_detalle_recepcion": "DRE-001",
      "id_recepcion": "REC-001",
      "id_detalle_reposicion": "DOR-001",
      "id_inventario": "INV-001",
      "cantidad_recibida": 100,
      "cantidad_rechazada": 0,
      "cantidad_aceptada": 100,
      "lote": "DEMO-20251223",
      "fecha_vencimiento": "2026-12-23T00:00:00Z",
      "temperatura_recepcion": null,
      "estado_recepcion": "CONFORME",
      "comentario_recepcion": null,
      "motivo_rechazo": null,
      "id_movimiento": "MOV-ENT-001",
      "ubicado": true,
      "riesgo_antes": null,
      "riesgo_despues": null,
      "notificacion_final": null,
      "fecha_creacion": "2025-12-23T10:00:00Z"
    }
  ]
}
```

## Colecciones auxiliares y estructuras no autonomas

El registro `email_verifications` incluye también **cooldown_until: datetime** (now+cooldown_seconds). Su clave de upsert/consulta es entity_type+entity_id+email. status es string de flujo, sin enum Pydantic. No generar estos registros de seguridad.

- inventario_historial (InventarioRepository): id_inventario str FK, id_operario str|null FK, accion str (CREAR/EDITAR_LIMITES), antes dict|null, despues dict|null, fecha datetime. PK Mongo _id, no PK negocio; Response omite id_inventario. Ejemplo: {"id_inventario":"INV-001","id_operario":null,"accion":"CREAR","antes":null,"despues":{"stock_actual":100},"fecha":"2019-12-06T00:00:00Z"}.
- notificaciones_email (NotificationService._record): event_id str unico; id_empresa str FK, recipient str|null, subject str, status str, error str|null, fecha_creacion/fecha_actualizacion datetime. Sin DTO propio. Ejemplo: {"event_id":"APROBACION:RECO-001","id_empresa":"EMP-001","recipient":null,"subject":"Demo","status":"PENDIENTE","error":null,"fecha_creacion":"2025-12-31T00:00:00Z","fecha_actualizacion":"2025-12-31T00:00:00Z"}. No generar/enviar notificaciones.
- email_verifications (EmailVerificationService): entity_type str, entity_id str, email str, code_hash str, expires_at datetime, attempts int=0, max_attempts int por settings, used bool=false, created_at/updated_at datetime, status str inicial PENDING. Consulta por entidad/email; no asumir indice unique. No generar ni exportar codigos/hashes. Ejemplo publico valido EmailVerificationResponse: {"verified":false,"status":"NOT_FOUND"}. Los campos internos son de seguridad, no extensiones de ventas.
- Cuenta no tiene coleccion independiente comprobada; cuenta_service/auth_service gestionan credenciales en empresa/operario/proveedor. Login/UsuarioActual no son registros del dataset; tokens jamas se exportan.
- ConsumoInfo/CoberturaInfo/ForecastInfo/SeguridadInfo/RiesgoInfo/ReposicionInfo e InventoryRiskResponse son proyecciones calculadas sin repositorio de resultados de riesgo. Saiki DTO describe conversacion/visualizaciones, no entidades historicas del generador.
