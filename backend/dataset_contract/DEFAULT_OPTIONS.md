# DEFAULT_OPTIONS - enumeraciones y valores predeterminados

No hay frontend en este repositorio; no se verificaron sus selects. Strings libres no son enums aunque se elijan valores de demo. Las enumeraciones siguientes se validan en backend Pydantic al usarse en DTO.

## TipoAlerta

Archivo: `app/dto/alerta_dto.py`.

```python
class TipoAlerta(str, Enum):
    RIESGO_STOCKOUT = "RIESGO_STOCKOUT"
    STOCK_BAJO = "STOCK_BAJO"
    SOBRESTOCK = "SOBRESTOCK"
    CONSUMO_ANOMALO = "CONSUMO_ANOMALO"
    PROXIMO_VENCIMIENTO = "PROXIMO_VENCIMIENTO"
```

## NivelRiesgo

Archivo: `app/dto/alerta_dto.py`.

```python
class NivelRiesgo(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"
```

## EstadoAlerta

Archivo: `app/dto/alerta_dto.py`.

```python
class EstadoAlerta(str, Enum):
    ACTIVA = "ACTIVA"
    VISTA = "VISTA"
    RESUELTA = "RESUELTA"
    IGNORADA = "IGNORADA"
```

## EstadoRecepcion

Archivo: `app/dto/detalle_recepcion_dto.py`.

```python
class EstadoRecepcion(str, Enum):
    CONFORME = "CONFORME"
    RECHAZADO = "RECHAZADO"
    EN_EVALUACION = "EN_EVALUACION"
```

## TipoMovimiento

Archivo: `app/dto/movimiento_dto.py`.

```python
class TipoMovimiento(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"
```

## MotivoMovimiento

Archivo: `app/dto/movimiento_dto.py`.

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

## EstadoOrdenReposicion

Archivo: `app/dto/orden_reposicion_dto.py`.

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

Archivo: `app/dto/orden_reposicion_dto.py`.

```python
class OrigenOrden(str, Enum):
    MANUAL = "MANUAL"
    RECOMENDACION_IA = "RECOMENDACION_IA"
```

## EstadoProveedor

Archivo: `app/dto/proveedor_dto.py`.

```python
class EstadoProveedor(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
```

## EstadoRack

Archivo: `app/dto/rack_dto.py`.

```python
class EstadoRack(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    LLENO = "LLENO"
    MANTENIMIENTO = "MANTENIMIENTO"
```

## TipoRecomendacion

Archivo: `app/dto/recomendacion_dto.py`.

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

Archivo: `app/dto/recomendacion_dto.py`.

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

## Todos los defaults/restricciones declarados en DTO

| Archivo / DTO | Campo | Declaracion | Alcance |
|---|---|---|---|
| app/dto/alerta_dto.py / AlertaCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | titulo | Field( min_length=3, max_length=150 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | mensaje | Field( min_length=3, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | stock_actual | Field(ge=0) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | dias_cobertura | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | stock_seguridad | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | punto_reposicion | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaCreate | forecast_7d | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | dias_cobertura | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | stock_seguridad | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | punto_reposicion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | forecast_7d | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/alerta_dto.py / AlertaResponse | fecha_resolucion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | nombre | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | longitud | Field( ..., ge=Decimal("-180.000000"), le=Decimal("180.000000"), max_digits=9, decimal_places=6 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | latitud | Field( ..., ge=Decimal("-90.000000"), le=Decimal("90.000000"), max_digits=8, decimal_places=6 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | area_m2 | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | aforo | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenCreate | tipo_almacen | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | nombre | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | longitud | Field( default=None, ge=Decimal("-180.000000"), le=Decimal("180.000000"), max_digits=9, decimal_places=6 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | latitud | Field( default=None, ge=Decimal("-90.000000"), le=Decimal("90.000000"), max_digits=8, decimal_places=6 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | area_m2 | Field( default=None, gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | aforo | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenUpdate | tipo_almacen | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/almacen_dto.py / AlmacenResponse | id | Field( validation_alias=AliasChoices( "id", "id_almacen" ) ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginRequest | password | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginResponse | token_type | "bearer" | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginResponse | operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginResponse | proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / LoginResponse | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / MeResponse | operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / MeResponse | proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / MeResponse | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / CambiarPasswordRequest | password_actual | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / CambiarPasswordRequest | password_nueva | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / ResetPasswordRequest | password_temporal | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / ResetPasswordRequest | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / UsuarioActual | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / UsuarioActual | id_almacen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / UsuarioActual | id_proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/auth_dto.py / UsuarioActual | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | cantidad_recibida | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | cantidad_rechazada | Field( default=0, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | lote | Field( default="SIN_LOTE", min_length=1, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | fecha_vencimiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | temperatura_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | estado_recepcion | ( EstadoRecepcion.CONFORME ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | comentario_recepcion | Field( default=None, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionCreate | motivo_rechazo | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | lote | "SIN_LOTE" | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | fecha_vencimiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | temperatura_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | estado_recepcion | ( EstadoRecepcion.CONFORME ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | comentario_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | motivo_rechazo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | id_movimiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | ubicado | True | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | riesgo_antes | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | riesgo_despues | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_recepcion_dto.py / DetalleRecepcionResponse | notificacion_final | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionCreate | cantidad_solicitada | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionCreate | costo_unitario | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionUpdate | cantidad_solicitada | Field( default=None, gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionUpdate | costo_unitario | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/detalle_reposicion_dto.py / DetalleReposicionResponse | costo_unitario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationCodeRequest | codigo | Field( ..., min_length=6, max_length=6, pattern=r"^\d{6}$", ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationSendResponse | email | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationSendResponse | remaining_seconds | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationSendResponse | reason | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationResponse | email | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationResponse | attempts | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/email_verification_dto.py / EmailVerificationResponse | remaining_attempts | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | nombre | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | ruc | Field( ..., min_length=8, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | sector | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | telefono | Field( ..., min_length=6, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaRegisterRequest | password | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaLoginRequest | password | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | nombre | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | ruc | Field( default=None, min_length=8, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | sector | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaUpdateRequest | telefono | Field( default=None, min_length=6, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaChangePasswordRequest | password_actual | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaChangePasswordRequest | password_nueva | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaDeleteRequest | password | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaResponse | correo_verificado | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaResponse | fecha_verificacion_correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/empresa_dto.py / EmpresaLoginResponse | token_type | "bearer" | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioCreate | stock_actual | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioCreate | stock_minimo | Field( default=0, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioCreate | stock_maximo | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioUpdate | stock_minimo | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioUpdate | stock_maximo | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioHistorialResponse | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioHistorialResponse | operario_nombre | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioHistorialResponse | antes | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventario_dto.py / InventarioHistorialResponse | despues | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ConsumoInfo | promedio_7d | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ConsumoInfo | promedio_14d | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ConsumoInfo | promedio_28d | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / CoberturaInfo | dias | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ForecastDiario | demanda_predicha | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ForecastInfo | demanda_7d | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ForecastInfo | fecha_quiebre_estimada | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ForecastInfo | predicciones_diarias | Field( default_factory=list ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / SeguridadInfo | stock_seguridad | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / SeguridadInfo | punto_reposicion | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / RiesgoInfo | score | Field( ge=0, le=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ReposicionInfo | cantidad_minima | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ReposicionInfo | cantidad_recomendada | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / ReposicionInfo | cantidad_segura | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / InventoryRiskResponse | stock_actual | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / InventoryRiskResponse | lead_time_dias | Field( ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / InventoryRiskResponse | reposicion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/inventory_risk_dto.py / InventoryRiskResponse | explicacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoCreate | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoCreate | id_detalle_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoCreate | cantidad | Field(..., gt=0) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoCreate | observacion | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoResponse | id_detalle_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoResponse | operario_nombre | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoResponse | id_zona | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/movimiento_dto.py / MovimientoResponse | observacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | nombre | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | apellido | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | cargo | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | turno | Field( ..., min_length=2, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | estado | Field( default="ACTIVO", min_length=2, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioCreate | password_temporal | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | id_almacen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | nombre | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | apellido | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | cargo | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | turno | Field( default=None, min_length=2, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioUpdate | estado | Field( default=None, min_length=2, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResetPassword | password_temporal | Field( ..., min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResetPassword | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | id_almacen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | correo_verificado | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | fecha_verificacion_correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | tiene_cuenta | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/operario_dto.py / OperarioResponse | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | id_recomendacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | id_almacen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | lineas | [] | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | fecha_estimada_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | origen | OrigenOrden.MANUAL | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionCreate | observacion | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionUpdate | id_proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionUpdate | fecha_estimada_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionUpdate | observacion | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | id_recomendacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | fecha_estimada_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | observacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | id_operario_solicitante | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | comentario_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | despacho | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / OrdenReposicionResponse | fecha_despacho | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / DevolverOrdenRequest | comentario | Field( ..., min_length=1, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / LineaDespacho | cantidad | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / LineaDespacho | fecha_vencimiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / LineaDespacho | temperatura | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / DespachoRequest | lineas | Field( min_length=1 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/orden_reposicion_dto.py / DespachoRequest | observacion | Field( default=None, max_length=500 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | id_proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | id_rack | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | nombre | Field( ..., min_length=2, max_length=150 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | categoria | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | familia | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | marca | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | peso | Field( ..., gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | volumen | Field( default=None, gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | stock | Field( default=0, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | requiere_refrigeracion | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | temperatura_min_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | temperatura_max_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | lead_time_dias | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoCreate | vida_util_dias | Field( ..., ge=1 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | id_rack | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | nombre | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | categoria | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | familia | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | marca | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | peso | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | volumen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | stock | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | requiere_refrigeracion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | temperatura_min_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | temperatura_max_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | lead_time_dias | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoUpdate | vida_util_dias | Field( default=None, ge=1 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | id_proveedor | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | id_rack | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | marca | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | peso | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | volumen | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | stock | 0 | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | requiere_refrigeracion | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | temperatura_min_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/producto_dto.py / ProductoResponse | temperatura_max_almacenamiento | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | nombre | Field( ..., min_length=2, max_length=150 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | ruc | Field( ..., min_length=11, max_length=11 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | telefono | Field( default=None, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | direccion | Field( default=None, max_length=250 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | tiempo_entrega_estimado_dias | Field( default=1, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | estado | EstadoProveedor.ACTIVO | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorCreate | password_temporal | Field( default=None, min_length=6, max_length=128 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | nombre | Field( default=None, min_length=2, max_length=150 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | telefono | Field( default=None, max_length=20 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | direccion | Field( default=None, max_length=250 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | tiempo_entrega_estimado_dias | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorUpdate | estado | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | tiene_cuenta | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | debe_cambiar_password | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | correo_verificado | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | fecha_verificacion_correo | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | telefono | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/proveedor_dto.py / ProveedorResponse | direccion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | codigo | Field( min_length=1, max_length=50 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | nivel | Field( ge=1 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | capacidad | Field( gt=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackCreate | estado | EstadoRack.DISPONIBLE | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackUpdate | estado | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackUpdate | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackUpdate | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackResponse | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackResponse | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackResponse | carga_kg | 0 | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackResponse | libre_kg | 0 | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/rack_dto.py / RackDisponibleResponse | nombre_zona | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / RecepcionMercaderiaCreate | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / RecepcionMercaderiaCreate | fecha_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / RecepcionMercaderiaCreate | observaciones_generales | Field( default=None, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / RecepcionMercaderiaCreate | detalles | Field(min_length=1) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | id_operario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | comentario_resolucion | Field( min_length=1, max_length=1000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | cantidad_aceptada | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | cantidad_rechazada | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recepcion_mercaderia_dto.py / ResolverEvaluacion | id_inventario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | id_alerta | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | cantidad_minima | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | cantidad_recomendada | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | cantidad_segura | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | forecast_7d | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | explicacion | Field( min_length=3, max_length=3000 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionCreate | origen | Field( default="PSITWIN", min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | id_alerta | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | cantidad_minima | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | cantidad_recomendada | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | cantidad_segura | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | forecast_7d | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | fecha_aplicacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / RecomendacionResponse | notificacion_aprobacion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaCambiosRequest | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaCambiosRequest | comentario | Field(..., min_length=1, max_length=1000) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaAprobacionRequest | id_empresa | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaAprobacionRequest | costo_unitario | Field(..., ge=0) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaAprobacionRequest | fecha_estimada_recepcion | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / EmpresaAprobacionRequest | observacion | Field(default=None, max_length=500) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / PropuestaRecomendacionUpdate | cantidad_recomendada | Field(default=None, ge=1) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/recomendacion_dto.py / PropuestaRecomendacionUpdate | explicacion | Field(default=None, min_length=3, max_length=3000) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | message | Field(default=None, min_length=1) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | question | Field( default=None, min_length=1, description="Alias legacy de message. No es necesario para nuevas consultas.", ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | id_inventario | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | id_producto | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | page | Field(default=1, ge=1, description="Página del detalle de inventario.") | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | page_size | Field(default=25, ge=1, le=100) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | context | Field( default_factory=dict, description="Contexto técnico opcional; normalmente debe omitirse.", ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskRequest | history | Field( default_factory=list, description="Historial opcional de mensajes previos.", ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | source | "ollama" | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | context | Field(default_factory=dict) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | warnings | Field(default_factory=list) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | data | Field(default_factory=dict) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | visualization | Field( default_factory=lambda: {"type": "none"} ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/saiki_dto.py / SaikiAskResponse | sources | Field(default_factory=list) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | nombre | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | tipo_zona | Field( ..., min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | refrigerada | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaCreate | capacidad | Field( ..., ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | nombre | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | tipo_zona | Field( default=None, min_length=2, max_length=100 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | refrigerada | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaUpdate | capacidad | Field( default=None, ge=0 ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaResponse | id | Field( validation_alias=AliasChoices( "id", "id_zona" ) ) | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaResponse | refrigerada | False | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaResponse | temperatura_min | None | Backend DTO; tipo en DTO_SCHEMA |
| app/dto/zona_dto.py / ZonaResponse | temperatura_max | None | Backend DTO; tipo en DTO_SCHEMA |

## Opciones libres y defaults de servicios

| Campo / fuente | Valores, default y validacion |
|---|---|
| tipo_almacen, almacen_dto.py | string 2..100, obligatorio, sin catalogo backend/default; frontend no disponible |
| tipo_zona, zona_dto.py | string 2..100, obligatorio, sin catalogo/default |
| categoria/familia, producto_dto.py | string 2..100, obligatorio; sin catalogo/default |
| turno, operario_dto.py | string 2..50, obligatorio; sin enum |
| cargo, operario_dto.py | string 2..100, obligatorio |
| estado operario, operario_dto.py | string 2..50, default ACTIVO; movimientos upper()==ACTIVO; recepciones comparacion ACTIVO |
| prioridad/pedido cliente | No existe campo/DTO; no inventar |
| rol, auth_dto.py | Literal EMPRESA/OPERARIO/PROVEEDOR; backend |
| dias, demand_history.py | default 400; >0; resumen suficiente >=367 |
| dias, forecast_controller.py | default 30; 1..500 en debug-history/features/predict, 7..500 en predict-7-days |
| horizon, forecast_controller.py | default 1; 1..7 |
| ForecastArgs, saiki_tools.py | dias=30 (7..500), horizonte_dias=7 (solo 7) |
| inventory_risk_service.py | forecast_history_days=30, forecast_horizon=7, z_service_level=1.645 |
| inventory_risk_controller.py | generar_alertas=true, puede persistir salidas |
| alerta_service.py | estado inicial ACTIVA |
| recomendacion_service.py | estado inicial PENDIENTE |
| orden_reposicion_service.py | estado inicial PENDIENTE; aprobar/validar actual lleva ENVIADA |
| settings.py | api_prefix=/api/v1; email_enabled=false; verificacion TTL=10min, cooldown=60s, max_attempts=5 |

Riesgo en inventory_risk_service.py: stock<=0 CRITICO; cobertura null BAJO; cobertura<=lead positivo CRITICO; stock<=punto positivo ALTO; cobertura<=1.5*lead positivo MEDIO; resto BAJO. Seguridad=1.645*std poblacional28*sqrt(lead), consumo=max(historico reciente fallback7/14/28,forecast/7). Reposicion ceil(max(0,consumo*max(lead+7,7)+seguridad-stock)); minima ceil(0.85*q), segura ceil(1.15*q). Score combina cobertura (60/40/20 para ratio<=1/1.5/2) y stock/punto (40/30/15 para ratio<=0.5/1/1.25), maximo100.

APROBADA de orden y ACEPTADA de recomendacion son legacy; enum permitido no implica transicion valida. No hay evidencia de listas frontend. Seguridad/SMTP/Ollama/CORS no son parametros de generacion, no copiar credenciales.
