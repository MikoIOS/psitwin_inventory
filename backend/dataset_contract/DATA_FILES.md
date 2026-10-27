# DATA_FILES - archivos y columnas exactas

CSV UTF-8, coma, cabecera exacta/orden indicado, RFC4180, decimales con punto y sin miles; int base 10, float finito, bool true/false, datetime ISO8601 UTC con Z, date YYYY-MM-DD. Celda vacia=null solamente si nullable; nunca string None/NaN. dict/list son JSON escapado en celda CSV. IDs strings estables UUIDv5 (namespace en manifest); ejemplos abreviados pedagogicos.

Exportaciones de intercambio nuevas sobre entidades reales: no son cuerpos POST ni importador existente. Aplicar restricciones Create y servicios ademas de Response. Empresa usa fechas strings ISO; el resto datetime se convierte a BSON Date para MongoDB. No generar secretos. Provision de cuentas fuera del dataset: los CSV sin password no satisfacen EmpresaRegisterRequest/OperarioCreate y no autentican por si solos. Nunca marcar tiene_cuenta=true sin una credencial valida provisionada externamente.

## empresas.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: EmpresaResponse y repositorio correspondiente. PK: id_empresa. Registros estimados: 1. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_empresa,nombre,ruc,sector,correo,telefono,correo_verificado,fecha_verificacion_correo,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| ruc | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| sector | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| correo | EmailStr | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| telefono | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| correo_verificado | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_verificacion_correo | Optional[str] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_creacion | str | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | str | No | ISO8601 UTC; cronologia GENERATION_RULES |

## almacenes.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: AlmacenResponse y repositorio correspondiente. PK: id. Registros estimados: 3. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id,id_empresa,nombre,longitud,latitud,area_m2,aforo,tipo_almacen,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| longitud | Decimal | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| latitud | Decimal | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| area_m2 | float | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| aforo | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tipo_almacen | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## zonas.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: ZonaResponse y repositorio correspondiente. PK: id. Registros estimados: 6. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id,id_almacen,id_empresa,nombre,tipo_zona,refrigerada,temperatura_min,temperatura_max,capacidad,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id | str | No | Clave/referencia RELATIONSHIPS |
| id_almacen | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tipo_zona | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| refrigerada | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_min | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_max | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| capacidad | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## racks.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: RackResponse y repositorio correspondiente. PK: id_rack. Registros estimados: 30. Omitidos de Response: carga_kg, libre_kg. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_rack,id_zona,codigo,nivel,capacidad,estado,temperatura_min,temperatura_max,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_rack | str | No | Clave/referencia RELATIONSHIPS |
| id_zona | str | No | Clave/referencia RELATIONSHIPS |
| codigo | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| nivel | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| capacidad | float | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado | EstadoRack | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_min | float &#124; None | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_max | float &#124; None | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## proveedores.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: ProveedorResponse y repositorio correspondiente. PK: id_proveedor. Registros estimados: 3. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_proveedor,id_empresa,nombre,ruc,correo,tiene_cuenta,debe_cambiar_password,correo_verificado,fecha_verificacion_correo,telefono,direccion,tiempo_entrega_estimado_dias,estado,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_proveedor | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| ruc | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| correo | Optional[EmailStr] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tiene_cuenta | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| debe_cambiar_password | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| correo_verificado | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_verificacion_correo | Optional[datetime] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| telefono | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| direccion | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tiempo_entrega_estimado_dias | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado | EstadoProveedor | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## productos.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: ProductoResponse y repositorio correspondiente. PK: id_producto. Registros estimados: 30. Omitidos de Response: stock. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_producto,id_empresa,id_proveedor,id_rack,nombre,categoria,familia,marca,peso,volumen,requiere_refrigeracion,temperatura_min_almacenamiento,temperatura_max_almacenamiento,lead_time_dias,vida_util_dias,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_producto | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| id_proveedor | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| id_rack | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| categoria | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| familia | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| marca | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| peso | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| volumen | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| requiere_refrigeracion | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_min_almacenamiento | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| temperatura_max_almacenamiento | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| lead_time_dias | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| vida_util_dias | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## operarios.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: OperarioResponse y repositorio correspondiente. PK: id_operario. Registros estimados: 6. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_operario,id_empresa,nombre,apellido,cargo,turno,estado,id_almacen,correo_verificado,fecha_verificacion_correo,correo,tiene_cuenta,debe_cambiar_password,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_operario | str | No | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| nombre | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| apellido | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| cargo | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| turno | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| id_almacen | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| correo_verificado | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_verificacion_correo | Optional[datetime] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| correo | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| tiene_cuenta | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| debe_cambiar_password | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## inventario.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: InventarioResponse y repositorio correspondiente. PK: id_inventario. Registros estimados: 90. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_inventario,id_producto,id_rack,stock_actual,stock_minimo,stock_maximo,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_inventario | str | No | Clave/referencia RELATIONSHIPS |
| id_producto | str | No | Clave/referencia RELATIONSHIPS |
| id_rack | str | No | Clave/referencia RELATIONSHIPS |
| stock_actual | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| stock_minimo | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| stock_maximo | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## ordenes_reposicion.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: OrdenReposicionResponse y repositorio correspondiente. PK: id_orden_reposicion. Registros estimados: 20.000..40.000. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_orden_reposicion,id_recomendacion,id_empresa,id_almacen,id_proveedor,origen,estado,fecha_orden,fecha_estimada_recepcion,observacion,id_operario_solicitante,comentario_empresa,despacho,fecha_despacho,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_orden_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_recomendacion | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| id_empresa | str | No | Clave/referencia RELATIONSHIPS |
| id_almacen | str | No | Clave/referencia RELATIONSHIPS |
| id_proveedor | str | No | Clave/referencia RELATIONSHIPS |
| origen | OrigenOrden | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado | EstadoOrdenReposicion | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_orden | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_estimada_recepcion | Optional[datetime] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| observacion | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| id_operario_solicitante | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| comentario_empresa | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| despacho | Optional[dict] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_despacho | Optional[datetime] | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## detalles_reposicion.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: DetalleReposicionResponse y repositorio correspondiente. PK: id_detalle_reposicion. Registros estimados: 20.000..40.000. Omitidos de Response: ninguno. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_detalle_reposicion,id_orden_reposicion,id_producto,cantidad_solicitada,costo_unitario,fecha_creacion,fecha_actualizacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_detalle_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_orden_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_producto | str | No | Clave/referencia RELATIONSHIPS |
| cantidad_solicitada | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| costo_unitario | Optional[float] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| fecha_actualizacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## recepciones.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: RecepcionMercaderiaResponse y repositorio correspondiente. PK: id_recepcion. Registros estimados: 20.000..40.000. Omitidos de Response: detalles. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_recepcion,id_orden_reposicion,id_operario,fecha_recepcion,observaciones_generales,fecha_creacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_recepcion | str | No | Clave/referencia RELATIONSHIPS |
| id_orden_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_operario | str | No | Clave/referencia RELATIONSHIPS |
| fecha_recepcion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |
| observaciones_generales | str &#124; None | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## detalles_recepcion.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: DetalleRecepcionResponse y repositorio correspondiente. PK: id_detalle_recepcion. Registros estimados: 20.000..40.000. Omitidos de Response: riesgo_antes, riesgo_despues, notificacion_final. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_detalle_recepcion,id_recepcion,id_detalle_reposicion,id_inventario,cantidad_recibida,cantidad_rechazada,cantidad_aceptada,lote,fecha_vencimiento,temperatura_recepcion,estado_recepcion,comentario_recepcion,motivo_rechazo,id_movimiento,ubicado,fecha_creacion
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_detalle_recepcion | str | No | Clave/referencia RELATIONSHIPS |
| id_recepcion | str | No | Clave/referencia RELATIONSHIPS |
| id_detalle_reposicion | str | No | Clave/referencia RELATIONSHIPS |
| id_inventario | str | No | Clave/referencia RELATIONSHIPS |
| cantidad_recibida | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| cantidad_rechazada | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| cantidad_aceptada | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| lote | str | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_vencimiento | datetime &#124; None | Si | ISO8601 UTC; cronologia GENERATION_RULES |
| temperatura_recepcion | float &#124; None | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| estado_recepcion | EstadoRecepcion | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| comentario_recepcion | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| motivo_rechazo | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| id_movimiento | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| ubicado | bool | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_creacion | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## movimientos.csv

Estado: entidad implementada, exportacion nueva. Consumidor logico: MovimientoResponse y repositorio correspondiente. PK: id_movimiento. Registros estimados: ~217.000..240.000. Omitidos de Response: operario_nombre, id_zona. Restricciones/relaciones en DTO_SCHEMA y RELATIONSHIPS. Ejemplo de entidad en DTO_SCHEMA, proyectar las columnas siguientes (recepcion: separar detalles).

Cabecera exacta:

```csv
id_movimiento,id_inventario,id_detalle_recepcion,id_producto,id_rack,id_operario,tipo_movimiento,motivo_movimiento,cantidad,stock_anterior,stock_nuevo,observacion,fecha_hora
```

| Columna | Tipo exacto DTO | Nulo | Dominio / generacion |
|---|---|---|---|
| id_movimiento | str | No | Clave/referencia RELATIONSHIPS |
| id_inventario | str | No | Clave/referencia RELATIONSHIPS |
| id_detalle_recepcion | Optional[str] | Si | Clave/referencia RELATIONSHIPS |
| id_producto | str | No | Clave/referencia RELATIONSHIPS |
| id_rack | str | No | Clave/referencia RELATIONSHIPS |
| id_operario | str | No | Clave/referencia RELATIONSHIPS |
| tipo_movimiento | TipoMovimiento | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| motivo_movimiento | MotivoMovimiento | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| cantidad | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| stock_anterior | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| stock_nuevo | int | No | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| observacion | Optional[str] | Si | DTO_SCHEMA / DEFAULT_OPTIONS y reglas GENERATION_RULES |
| fecha_hora | datetime | No | ISO8601 UTC; cronologia GENERATION_RULES |

## Ejemplos de registros base (JSON equivalente a filas CSV)

### Registro empresas.csv

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

### Registro almacenes.csv

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

### Registro zonas.csv

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

### Registro racks.csv

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
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro productos.csv

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
  "requiere_refrigeracion": false,
  "temperatura_min_almacenamiento": null,
  "temperatura_max_almacenamiento": null,
  "lead_time_dias": 3,
  "vida_util_dias": 365,
  "fecha_creacion": "2019-12-01T00:00:00Z",
  "fecha_actualizacion": "2025-12-31T23:59:59Z"
}
```

### Registro inventario.csv

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

### Registro operarios.csv

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

### Registro proveedores.csv

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

### Registro movimientos.csv

```json
{
  "id_movimiento": "MOV-001",
  "id_inventario": "INV-001",
  "id_producto": "PRO-001",
  "id_rack": "RAC-001",
  "id_operario": "OPE-001",
  "id_detalle_recepcion": null,
  "tipo_movimiento": "SALIDA",
  "motivo_movimiento": "VENTA",
  "cantidad": 10,
  "stock_anterior": 110,
  "stock_nuevo": 100,
  "observacion": "Movimiento sintetico",
  "fecha_hora": "2025-12-31T12:00:00Z"
}
```

### Registro ordenes_reposicion.csv

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

### Registro detalles_reposicion.csv

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

### Registro detalles_recepcion.csv

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
  "fecha_creacion": "2025-12-23T10:00:00Z"
}
```

### Registro recepciones.csv

```json
{
  "id_recepcion": "REC-001",
  "id_orden_reposicion": "ORD-001",
  "id_operario": "OPE-001",
  "fecha_recepcion": "2025-12-23T10:00:00Z",
  "observaciones_generales": null,
  "fecha_creacion": "2025-12-23T10:00:00Z"
}
```

## Archivos complementarios y auditoria

Tipos date/datetime segun convencion comun; todas las FKs apuntan a archivos base y mantienen empresa. simulado siempre true en extensiones. Todo int de ventas/cantidades/stock>=0 excepto delta_ajustes. No hay columnas adicionales tacitas.

### ventas_diarias.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 197280. PK: fecha+id_almacen+id_producto. Regla/consumidor: Fuente para evaluacion nueva; ningun consumidor backend CSV. Ventas=sum SALIDA/VENTA; latente>=ventas; perdidas=latente-ventas; stockout=perdidas>0.

```csv
fecha,id_empresa,id_almacen,id_producto,id_inventario,ventas_observadas,demanda_latente,ventas_perdidas,stockout,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha | date | No |
| id_empresa | str | No |
| id_almacen | str | No |
| id_producto | str | No |
| id_inventario | str | No |
| ventas_observadas | int | No |
| demanda_latente | int | No |
| ventas_perdidas | int | No |
| stockout | bool | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha": "2025-12-31",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_producto": "PRO-001",
  "id_inventario": "INV-001",
  "ventas_observadas": 10,
  "demanda_latente": 12,
  "ventas_perdidas": 2,
  "stockout": true,
  "simulado": true
}
```

### inventario_diario.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 197280. PK: fecha+id_inventario. Regla/consumidor: Auditoria replay: final=inicial+entradas-venta-otras+delta_ajustes. delta_ajustes puede ser firmado; stock/cantidades no negativos. Delta se calcula nuevo-anterior de AJUSTE absoluto.

```csv
fecha,id_inventario,stock_inicial,entradas,salidas_venta,salidas_otras,delta_ajustes,stock_final,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha | date | No |
| id_inventario | str | No |
| stock_inicial | int | No |
| entradas | int | No |
| salidas_venta | int | No |
| salidas_otras | int | No |
| delta_ajustes | int | No |
| stock_final | int | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha": "2025-12-31",
  "id_inventario": "INV-001",
  "stock_inicial": 110,
  "entradas": 0,
  "salidas_venta": 10,
  "salidas_otras": 0,
  "delta_ajustes": 0,
  "stock_final": 100,
  "simulado": true
}
```

### saldos_iniciales.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 90. PK: id_inventario. Regla/consumidor: Apertura antes de primer movimiento, no ENTRADA ficticia ni snapshot de cierre. Stock>=0.

```csv
fecha_hora,id_inventario,stock_inicial,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha_hora | datetime | No |
| id_inventario | str | No |
| stock_inicial | int | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha_hora": "2020-01-01T00:00:00Z",
  "id_inventario": "INV-001",
  "stock_inicial": 110,
  "simulado": true
}
```

### calendario.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 2199. PK: fecha. Regla/consumidor: 2020-01-01..2026-01-07. dayofweek lunes=0; semana ISO. Year ano calendario, aunque semana ISO pertenezca a otro ano. month1..12/day1..31/week1..53/quarter1..4/dayofyear1..366. Flags0/1. event_name {NINGUNO,FIN_ANIO,VERANO,INVIERNO}, event_type {NINGUNO,CAMPANIA}; has_event=algun nombre distinto de NINGUNO. snap=0. Calendario/campanas prepublicados antes del uso; conocido_en=2019-12-01.

```csv
fecha,year,month,day,dayofweek,weekofyear,quarter,dayofyear,is_weekend,is_month_start,is_month_end,has_event,event_name_1,event_type_1,event_name_2,event_type_2,snap,conocido_en,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha | date | No |
| year | int | No |
| month | int | No |
| day | int | No |
| dayofweek | int | No |
| weekofyear | int | No |
| quarter | int | No |
| dayofyear | int | No |
| is_weekend | int | No |
| is_month_start | int | No |
| is_month_end | int | No |
| has_event | int | No |
| event_name_1 | str | No |
| event_type_1 | str | No |
| event_name_2 | str | No |
| event_type_2 | str | No |
| snap | int | No |
| conocido_en | datetime | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha": "2025-12-31",
  "year": 2025,
  "month": 12,
  "day": 31,
  "dayofweek": 2,
  "weekofyear": 1,
  "quarter": 4,
  "dayofyear": 365,
  "is_weekend": 0,
  "is_month_start": 0,
  "is_month_end": 1,
  "has_event": 1,
  "event_name_1": "FIN_ANIO",
  "event_type_1": "CAMPANIA",
  "event_name_2": "NINGUNO",
  "event_type_2": "NINGUNO",
  "snap": 0,
  "conocido_en": "2019-12-01T00:00:00Z",
  "simulado": true
}
```

### precios.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 197910. PK: fecha+id_almacen+id_producto. Regla/consumidor: 2199 fechas*90 series. Precio>0, 2 decimales; moneda PEN. Plan mensual publicado primer dia a 00:00 UTC, antes del origen que lo usa. price_available siempre true en base; null de precio no admitido. No es costo compra. Precios enero 2026 se prepublican 2025-12-31 para horizonte al corte; no asumir conocidos antes de publicacion.

```csv
fecha,id_almacen,id_producto,sell_price,moneda,price_available,conocido_en,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| fecha | date | No |
| id_almacen | str | No |
| id_producto | str | No |
| sell_price | float | No |
| moneda | str | No |
| price_available | bool | No |
| conocido_en | datetime | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "fecha": "2025-12-31",
  "id_almacen": "ALM-001",
  "id_producto": "PRO-001",
  "sell_price": 4.5,
  "moneda": "PEN",
  "price_available": true,
  "conocido_en": "2025-12-01T00:00:00Z",
  "simulado": true
}
```

### series_mapping.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 90. PK: id_inventario; producto+almacen unico. Regla/consumidor: Adaptador futuro: item por SKU, dept=familia normalizada, cat=ALIMENTOS, store DEMO_LIMA/DEMO_AREQUIPA/DEMO_TRUJILLO, state LIMA/AREQUIPA/LA_LIBERTAD. IDs FK verificadas por rack/zona. Codigos semanticos nuevos, no vocabulario M5 garantizado.

```csv
id_inventario,id_empresa,id_almacen,id_producto,item_id,dept_id,cat_id,store_id,state_id,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| id_inventario | str | No |
| id_empresa | str | No |
| id_almacen | str | No |
| id_producto | str | No |
| item_id | str | No |
| dept_id | str | No |
| cat_id | str | No |
| store_id | str | No |
| state_id | str | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "id_inventario": "INV-001",
  "id_empresa": "EMP-001",
  "id_almacen": "ALM-001",
  "id_producto": "PRO-001",
  "item_id": "SKU_001",
  "dept_id": "CEREALES",
  "cat_id": "ALIMENTOS",
  "store_id": "DEMO_LIMA",
  "state_id": "LIMA",
  "simulado": true
}
```

### escenarios_inventario.csv

Estado: EXTENSION propuesta; sin DTO/consumidor backend implementado. Registros: 90. PK: id_inventario. Regla/consumidor: escenario {NORMAL,BAJO_STOCK,SIN_STOCK,SOBRESTOCK,SIN_CONSUMO,REFRIGERADO}; politica {NORMAL,REPOSICION_RETRASADA,COBERTURA_ALTA,INTERMITENTE}; explicacion no vacia, derivada de ledger. Etiquetas de simulacion, no enums backend.

```csv
id_inventario,fecha_corte,escenario,politica,explicacion,simulado
```

| Columna | Tipo | Nulo |
|---|---|---|
| id_inventario | str | No |
| fecha_corte | date | No |
| escenario | str | No |
| politica | str | No |
| explicacion | str | No |
| simulado | bool | No |

Ejemplo de registro:

```json
{
  "id_inventario": "INV-001",
  "fecha_corte": "2025-12-31",
  "escenario": "BAJO_STOCK",
  "politica": "REPOSICION_RETRASADA",
  "explicacion": "Stock bajo tras retraso de entrega y ventas recientes",
  "simulado": true
}
```

### inventario_historial.csv

Estado: coleccion existente, exportacion nueva. Registros: 90 minimo. PK: id_inventario+fecha+accion. Regla/consumidor: Coleccion existente; InventarioRepository e InventarioHistorialResponse (proyeccion sin id_inventario). CREAR por inventario, EDITAR_LIMITES solo si se simulan; antes/despues snapshots de campos afectados, no espejo de movimientos.

```csv
id_inventario,id_operario,accion,antes,despues,fecha
```

| Columna | Tipo | Nulo |
|---|---|---|
| id_inventario | str | No |
| id_operario | str | Si |
| accion | str | No |
| antes | dict | Si |
| despues | dict | Si |
| fecha | datetime | No |

Ejemplo de registro:

```json
{
  "id_inventario": "INV-001",
  "id_operario": null,
  "accion": "CREAR",
  "antes": null,
  "despues": {
    "id_producto": "PRO-001",
    "id_rack": "RAC-001",
    "stock_actual": 110,
    "stock_minimo": 40,
    "stock_maximo": 500
  },
  "fecha": "2019-12-06T00:00:00Z"
}
```

## Reglas particulares de archivos base

- empresas: una empresa ficticia, RUC string sintetico (no validar existencia SUNAT); correo example.com, correo_verificado=false/fecha_verificacion=null. Fechas ISO strings. Sin password.
- almacenes: nombres/ubicaciones ficticios, coordenadas hasta 6 decimales en rangos DTO, area1200/aforo25/tipo_almacen Mixto (valor elegido, no enum).
- zonas: seca/refrigerada por almacen; nombre/tipo_zona strings Seco/Refrigerado elegidos, capacidad5; flag refrigerada coherente. Rangos null seca, 2..6 refrigerada.
- racks: 5 niveles por zona, codigo unico por zona, 5000kg de diseno; estado DISPONIBLE base. No deducir LLENO de stock arbitrariamente; estado es dato operativo, carga/libre se calculan al consultar.
- proveedores: 3 activos, lead2/4/7; RUC11 caracteres unico, correos null o example.com, flags cuenta=false sin credential.
- productos: 15 secos/15 refrigerados, nombres alimenticios, peso kg>0, volumen null, lead del proveedor, vida_util>=1; categoria/familia/marca elegidas sin catalogo backend. id_rack referencia a una ubicacion principal (por ejemplo Lima), no sustituye otros inventarios. Restriccion de agregados legacy advertida.
- operarios: 2 por almacen, ACTIVO, cargo Almacenero, turnos Manana/Tarde como valores de demo; correo example.com unico; sin credential/tiene_cuenta=false.
- inventario: 90 cierres; min/max politica fija, stock resultante de replay. No copiar stock de Producto.
- ordenes/detalles/recepciones: una linea por orden y una recepcion conforme cuando entregada, MANUAL, sin recomendacion; suma aceptada determina estado. Conteos estimados dependen de politica/ruido, no cuota forzada. No generar recepciones posteriores al corte. Campos despacho/comentario se dejan null base si no se simulan.
- detalles_recepcion: lote sintetico, vencimiento coherente con vida util, temperatura dentro de rango si refrigerado; estado CONFORME, rechazadas0/aceptadas=recibidas, ubicado=true, FK a entrada. Riesgo/notificacion son resultados omitidos, reconstruir null al validar Response.
- movimientos: ventas diarias positivas agregadas + entradas aceptadas; aproximadamente hasta197280 SALIDA mas20k..40k entradas; menos filas si ventas0. El numero no es criterio de aceptacion fijo. Otras salidas/ajustes0 base. No IDs ficticios de pedido cliente.

## Auxiliares obligatorios

manifest.json (1 registro): schema_version str=1.0; dataset_id str; simulated bool=true; seed int=20261010; generator_version str; source_contract_sha256 objeto archivo -> hash; parameters objeto configuracion exacta; history_start/history_end/reference_date date (2020-01-01/2025-12-31/2025-12-31); timezone str=UTC; id_namespace str UUID; splits objeto TRAIN/VALID/TEST -> {target_start:date,target_end:date}; files lista {path:str,rows:int,sha256:str}; exclusions lista str; limitations lista str. No hash autorreferente del manifest.

validation_report.json (1): schema_version str, dataset_id str, passed bool, checks lista {name:str,passed:bool,failures:int,examples:list}, counts objeto, warnings lista str. schema.json: archivosi{columns:lista {name:str,type:str,nullable:bool,allowed_values:list|null},primary_key:lista str,foreign_keys:lista {columns:list,target_file:str,target_columns:list}}. README_GENERATOR.md: comandos, seed/versiones/config, mediciones reales y limites. No credenciales en ejemplos.

Ejemplo minimo de manifest (completar listas/huellas al generar):

```json
{"schema_version":"1.0","dataset_id":"psitwin-demo-v1","simulated":true,"seed":20261010,"generator_version":"1.0.0","source_contract_sha256":{},"parameters":{},"history_start":"2020-01-01","history_end":"2025-12-31","reference_date":"2025-12-31","timezone":"UTC","id_namespace":"a1d188f7-265c-5ebc-894a-b65ea36c236f","splits":{"TRAIN":{"target_start":"2020-01-01","target_end":"2023-12-31"},"VALID":{"target_start":"2024-01-01","target_end":"2024-12-31"},"TEST":{"target_start":"2025-01-01","target_end":"2025-12-31"}},"files":[],"exclusions":["credenciales","predicciones"],"limitations":["Sin importador CSV actual"]}
```

Exportaciones mongo/*.jsonl para13 entidades base+inventario_historial: mismas columnas persistentes de CSV, datetime transformados a Extended JSON {"$date":"..."}, excepto strings fecha de empresa; Decimal coordenadas se persiste float finito con6 decimales. Sin _id/credenciales. Recepciones no guardan lista detalles en cabecera: unir detalles al construir Response. No cargar automaticamente.

## Excluidos

No pedidos.csv: no existe pedido cliente. No alertas.csv/recomendaciones.csv/forecast precalculado: son resultados del backend, sus contratos estan documentados. No cuentas/secretos/email_verifications/notificaciones_email. No matriz features/pickle entrenable obligatoria: fuentes completas bastan para posterior ML. Si una futura exposicion exige pedidos comerciales o FEFO persistente, definir extension de cabeceras/lineas/lotes previamente y versionar contrato.

### Ejemplos de auxiliares de validacion/esquema

Ejemplo ilustrativo de validation_report.json (checks reales deben cubrir todo VALIDATION_CHECKLIST):

```json
{"schema_version":"1.0","dataset_id":"psitwin-demo-v1","passed":true,"checks":[{"name":"referencias","passed":true,"failures":0,"examples":[]}],"counts":{"empresas":1},"warnings":["Sin importador CSV actual"]}
```

Ejemplo parcial de schema.json (completar todos archivos/columnas al generar):

```json
{"saldos_iniciales.csv":{"columns":[{"name":"fecha_hora","type":"datetime","nullable":false,"allowed_values":null},{"name":"id_inventario","type":"str","nullable":false,"allowed_values":null},{"name":"stock_inicial","type":"int","nullable":false,"allowed_values":null},{"name":"simulado","type":"bool","nullable":false,"allowed_values":[true]}],"primary_key":["id_inventario"],"foreign_keys":[{"columns":["id_inventario"],"target_file":"inventario.csv","target_columns":["id_inventario"]}]}}
```
