# Ejemplos documentales de contratos PsiTwin

Fecha de auditoría: 2026-10-13 (America/Lima). Inspección estática del workspace real. No se ejecutó el backend, no se importó app.main, no se abrió una conexión a MongoDB, no se entrenaron modelos, no se generaron registros ni datasets. Los JSON son ejemplos documentales ilustrativos. IMPLEMENTADO significa presencia y trazabilidad en código; no acredita ejecución exitosa ni datos desplegados. NO DEFINIDA significa ausencia de restricción declarada en ese contrato; NO VERIFICABLE significa falta de evidencia de ejecución o del despliegue. INFERIDO se reserva para cardinalidades y efectos deducidos. PARCIALMENTE IMPLEMENTADO distingue código existente con componentes faltantes. NO IMPLEMENTADO se limita al alcance inspeccionado.

Todos los valores son ilustrativos. Los IDs UUID sustituyen los generados por API y referencias a registros existentes. $date/$oid es Extended JSON de BSON, no body API. Los placeholders de hashes no son credenciales válidas y no deben insertarse. Cada ejemplo es independiente: una orden con lineas ya crea sus detalles y una recepción con detalles ya los crea. No ejecutar ejemplos como lote. Las cantidades predictivas ilustran contratos; no son resultados calculados.

## Empresa / empresas

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "nombre": "Empresa Ejemplo",
  "ruc": "20123456789",
  "sector": "Alimentos",
  "correo": "empresa@example.com",
  "telefono": "999000111",
  "password": "Ejemplo_documental_2026"
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Empresa Ejemplo",
  "ruc": "20123456789",
  "sector": "Alimentos",
  "correo": "empresa@example.com",
  "telefono": "999000111",
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z",
  "password": "<HASH_BCRYPT_OMITIDO>",
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Empresa Ejemplo",
  "ruc": "20123456789",
  "sector": "Alimentos",
  "correo": "empresa@example.com",
  "telefono": "999000111",
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "nombre": "Empresa Actualizada"
}
```

## Almacen / almacenes

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "nombre": "Almacen Central",
  "longitud": "-77.042800",
  "latitud": "-12.046400",
  "area_m2": 500,
  "aforo": 20,
  "tipo_almacen": "Seco"
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Almacen Central",
  "longitud": -77.0428,
  "latitud": -12.0464,
  "area_m2": 500,
  "aforo": 20,
  "tipo_almacen": "Seco",
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id": "22222222-2222-4222-8222-222222222222",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Almacen Central",
  "longitud": "-77.042800",
  "latitud": "-12.046400",
  "area_m2": 500,
  "aforo": 20,
  "tipo_almacen": "Seco",
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "nombre": "Almacen Actualizado"
}
```

## Zona / zonas

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "nombre": "Zona A",
  "tipo_zona": "Seca",
  "refrigerada": false,
  "temperatura_min": null,
  "temperatura_max": null,
  "capacidad": 3
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id": "33333333-3333-4333-8333-333333333333",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Zona A",
  "tipo_zona": "Seca",
  "refrigerada": false,
  "temperatura_min": null,
  "temperatura_max": null,
  "capacidad": 3,
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id": "33333333-3333-4333-8333-333333333333",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Zona A",
  "tipo_zona": "Seca",
  "refrigerada": false,
  "temperatura_min": null,
  "temperatura_max": null,
  "capacidad": 3,
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "nombre": "Zona Actualizada"
}
```

## Rack / racks

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_zona": "33333333-3333-4333-8333-333333333333",
  "codigo": "A-01",
  "nivel": 1,
  "capacidad": 500,
  "temperatura_min": null,
  "temperatura_max": null,
  "estado": "DISPONIBLE"
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_rack": "44444444-4444-4444-8444-444444444444",
  "id_zona": "33333333-3333-4333-8333-333333333333",
  "codigo": "A-01",
  "nivel": 1,
  "capacidad": 500,
  "estado": "DISPONIBLE",
  "temperatura_min": null,
  "temperatura_max": null,
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_rack": "44444444-4444-4444-8444-444444444444",
  "id_zona": "33333333-3333-4333-8333-333333333333",
  "codigo": "A-01",
  "nivel": 1,
  "capacidad": 500,
  "estado": "DISPONIBLE",
  "temperatura_min": null,
  "temperatura_max": null,
  "carga_kg": 0,
  "libre_kg": 500,
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "estado": "MANTENIMIENTO"
}
```

## Producto / productos

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "nombre": "Arroz Ejemplo",
  "categoria": "Alimentos",
  "familia": "Granos",
  "marca": "Ejemplo",
  "peso": 1,
  "volumen": 0.001,
  "requiere_refrigeracion": false,
  "temperatura_min_almacenamiento": null,
  "temperatura_max_almacenamiento": null,
  "lead_time_dias": 2,
  "vida_util_dias": 365
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "id_proveedor": "88888888-8888-4888-8888-888888888888",
  "id_rack": null,
  "nombre": "Arroz Ejemplo",
  "categoria": "Alimentos",
  "familia": "Granos",
  "marca": "Ejemplo",
  "peso": 1,
  "volumen": 0.001,
  "requiere_refrigeracion": false,
  "temperatura_min_almacenamiento": null,
  "temperatura_max_almacenamiento": null,
  "lead_time_dias": 2,
  "vida_util_dias": 365,
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "id_proveedor": "88888888-8888-4888-8888-888888888888",
  "id_rack": null,
  "nombre": "Arroz Ejemplo",
  "categoria": "Alimentos",
  "familia": "Granos",
  "marca": "Ejemplo",
  "peso": 1,
  "volumen": 0.001,
  "stock": 0,
  "requiere_refrigeracion": false,
  "temperatura_min_almacenamiento": null,
  "temperatura_max_almacenamiento": null,
  "lead_time_dias": 2,
  "vida_util_dias": 365,
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "nombre": "Arroz Actualizado"
}
```

## Inventario / inventarios

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_rack": "44444444-4444-4444-8444-444444444444",
  "stock_actual": 10,
  "stock_minimo": 5,
  "stock_maximo": 100
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_rack": "44444444-4444-4444-8444-444444444444",
  "stock_actual": 10,
  "stock_minimo": 5,
  "stock_maximo": 100,
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_rack": "44444444-4444-4444-8444-444444444444",
  "stock_actual": 10,
  "stock_minimo": 5,
  "stock_maximo": 100,
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "stock_minimo": 6,
  "stock_maximo": 120
}
```

## Operario / operarios

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "nombre": "Ana",
  "apellido": "Ejemplo",
  "correo": "operario@example.com",
  "cargo": "Almacenero",
  "turno": "DIA",
  "estado": "ACTIVO",
  "password_temporal": "Temporal_documental_2026"
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_operario": "77777777-7777-4777-8777-777777777777",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Ana",
  "apellido": "Ejemplo",
  "cargo": "Almacenero",
  "turno": "DIA",
  "estado": "ACTIVO",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "correo": "operario@example.com",
  "debe_cambiar_password": true,
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "password_hash": "<HASH_BCRYPT_OMITIDO>",
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_operario": "77777777-7777-4777-8777-777777777777",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Ana",
  "apellido": "Ejemplo",
  "cargo": "Almacenero",
  "turno": "DIA",
  "estado": "ACTIVO",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "correo": "operario@example.com",
  "tiene_cuenta": true,
  "debe_cambiar_password": true,
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "cargo": "Operador"
}
```

## Movimiento / movimientos

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "tipo_movimiento": "SALIDA",
  "motivo_movimiento": "VENTA",
  "cantidad": 2,
  "observacion": "Salida ilustrativa"
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_movimiento": "99999999-9999-4999-8999-999999999999",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_detalle_recepcion": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_rack": "44444444-4444-4444-8444-444444444444",
  "id_operario": "77777777-7777-4777-8777-777777777777",
  "tipo_movimiento": "SALIDA",
  "motivo_movimiento": "VENTA",
  "cantidad": 2,
  "stock_anterior": 10,
  "stock_nuevo": 8,
  "observacion": "Salida ilustrativa",
  "fecha_hora": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_movimiento": "99999999-9999-4999-8999-999999999999",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_detalle_recepcion": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_rack": "44444444-4444-4444-8444-444444444444",
  "id_operario": "77777777-7777-4777-8777-777777777777",
  "operario_nombre": "Ana Ejemplo",
  "id_zona": "33333333-3333-4333-8333-333333333333",
  "tipo_movimiento": "SALIDA",
  "motivo_movimiento": "VENTA",
  "cantidad": 2,
  "stock_anterior": 10,
  "stock_nuevo": 8,
  "observacion": "Salida ilustrativa",
  "fecha_hora": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

## Proveedor / proveedores

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "nombre": "Proveedor Ejemplo",
  "ruc": "20987654321",
  "correo": "proveedor@example.com",
  "telefono": "999000222",
  "direccion": "Direccion ilustrativa",
  "tiempo_entrega_estimado_dias": 2,
  "estado": "ACTIVO",
  "password_temporal": "Temporal_documental_2026"
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_proveedor": "88888888-8888-4888-8888-888888888888",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Proveedor Ejemplo",
  "ruc": "20987654321",
  "correo": "proveedor@example.com",
  "debe_cambiar_password": true,
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "telefono": "999000222",
  "direccion": "Direccion ilustrativa",
  "tiempo_entrega_estimado_dias": 2,
  "estado": "ACTIVO",
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "password_hash": "<HASH_BCRYPT_OMITIDO>",
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_proveedor": "88888888-8888-4888-8888-888888888888",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "nombre": "Proveedor Ejemplo",
  "ruc": "20987654321",
  "correo": "proveedor@example.com",
  "tiene_cuenta": true,
  "debe_cambiar_password": true,
  "correo_verificado": false,
  "fecha_verificacion_correo": null,
  "telefono": "999000222",
  "direccion": "Direccion ilustrativa",
  "tiempo_entrega_estimado_dias": 2,
  "estado": "ACTIVO",
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "nombre": "Proveedor Actualizado"
}
```

## OrdenReposicion / ordenes_reposicion

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_proveedor": "88888888-8888-4888-8888-888888888888",
  "lineas": [
    {
      "id_producto": "55555555-5555-4555-8555-555555555555",
      "cantidad_solicitada": 5,
      "costo_unitario": 3
    }
  ],
  "fecha_estimada_recepcion": "2026-10-15T12:00:00Z",
  "origen": "MANUAL",
  "observacion": "Pedido ilustrativo"
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_orden_reposicion": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "id_recomendacion": "ffffffff-ffff-4fff-8fff-ffffffffffff",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_proveedor": "88888888-8888-4888-8888-888888888888",
  "origen": "MANUAL",
  "estado": "PENDIENTE",
  "fecha_orden": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_estimada_recepcion": {
    "$date": "2026-10-15T12:00:00Z"
  },
  "observacion": "Pedido ilustrativo",
  "id_operario_solicitante": "77777777-7777-4777-8777-777777777777",
  "comentario_empresa": null,
  "despacho": null,
  "fecha_despacho": null,
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_orden_reposicion": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "id_recomendacion": "ffffffff-ffff-4fff-8fff-ffffffffffff",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_proveedor": "88888888-8888-4888-8888-888888888888",
  "origen": "MANUAL",
  "estado": "PENDIENTE",
  "fecha_orden": "2026-10-13T12:00:00Z",
  "fecha_estimada_recepcion": "2026-10-15T12:00:00Z",
  "observacion": "Pedido ilustrativo",
  "id_operario_solicitante": "77777777-7777-4777-8777-777777777777",
  "comentario_empresa": null,
  "despacho": null,
  "fecha_despacho": null,
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "observacion": "Observacion actualizada"
}
```

## DetalleReposicion / detalles_reposicion

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "cantidad_solicitada": 5,
  "costo_unitario": 3
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_detalle_reposicion": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "id_orden_reposicion": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "cantidad_solicitada": 5,
  "costo_unitario": 3,
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_detalle_reposicion": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "id_orden_reposicion": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "cantidad_solicitada": 5,
  "costo_unitario": 3,
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

```json
{
  "cantidad_solicitada": 6
}
```

## RecepcionMercaderia / recepciones_mercaderia

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_orden_reposicion": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "fecha_recepcion": "2026-10-13T12:00:00Z",
  "observaciones_generales": "Recepción ilustrativa",
  "detalles": [
    {
      "id_detalle_reposicion": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      "id_inventario": "66666666-6666-4666-8666-666666666666",
      "cantidad_recibida": 5,
      "cantidad_rechazada": 0,
      "lote": "LOTE-EJEMPLO",
      "fecha_vencimiento": "2027-10-13T12:00:00Z",
      "temperatura_recepcion": null,
      "estado_recepcion": "CONFORME",
      "comentario_recepcion": "Conforme",
      "motivo_rechazo": null
    }
  ]
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_recepcion": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
  "id_orden_reposicion": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "id_operario": "77777777-7777-4777-8777-777777777777",
  "fecha_recepcion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "observaciones_generales": "Recepción ilustrativa",
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "_id": {
    "$oid": "0123456789abcdef01234567"
  },
  "detalles": [
    {
      "id_detalle_reposicion": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      "id_inventario": "66666666-6666-4666-8666-666666666666",
      "cantidad_recibida": 5,
      "cantidad_rechazada": 0,
      "lote": "LOTE-EJEMPLO",
      "fecha_vencimiento": {
        "$date": "2027-10-13T12:00:00Z"
      },
      "temperatura_recepcion": null,
      "estado_recepcion": "CONFORME",
      "comentario_recepcion": "Conforme",
      "motivo_rechazo": null
    }
  ]
}
```

### C. Respuesta/consulta API

```json
{
  "id_recepcion": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
  "id_orden_reposicion": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "id_operario": "77777777-7777-4777-8777-777777777777",
  "fecha_recepcion": "2026-10-13T12:00:00Z",
  "observaciones_generales": "Recepción ilustrativa",
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "detalles": [
    {
      "id_detalle_recepcion": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
      "id_recepcion": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      "id_detalle_reposicion": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      "id_inventario": "66666666-6666-4666-8666-666666666666",
      "cantidad_recibida": 5,
      "cantidad_rechazada": 0,
      "cantidad_aceptada": 5,
      "lote": "LOTE-EJEMPLO",
      "fecha_vencimiento": "2027-10-13T12:00:00Z",
      "temperatura_recepcion": null,
      "estado_recepcion": "CONFORME",
      "comentario_recepcion": "Conforme",
      "motivo_rechazo": null,
      "id_movimiento": "99999999-9999-4999-8999-999999999999",
      "ubicado": true,
      "riesgo_antes": null,
      "riesgo_despues": null,
      "notificacion_final": null,
      "fecha_creacion": "2026-10-13T12:00:00Z"
    }
  ]
}
```

### D. Actualización API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

## DetalleRecepcion / detalles_recepcion

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_detalle_reposicion": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "cantidad_recibida": 5,
  "cantidad_rechazada": 0,
  "lote": "LOTE-EJEMPLO",
  "fecha_vencimiento": "2027-10-13T12:00:00Z",
  "temperatura_recepcion": null,
  "estado_recepcion": "CONFORME",
  "comentario_recepcion": "Conforme",
  "motivo_rechazo": null
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_detalle_recepcion": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  "id_recepcion": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
  "id_detalle_reposicion": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "cantidad_recibida": 5,
  "cantidad_rechazada": 0,
  "cantidad_aceptada": 5,
  "lote": "LOTE-EJEMPLO",
  "fecha_vencimiento": {
    "$date": "2027-10-13T12:00:00Z"
  },
  "temperatura_recepcion": null,
  "estado_recepcion": "CONFORME",
  "comentario_recepcion": "Conforme",
  "motivo_rechazo": null,
  "id_movimiento": "99999999-9999-4999-8999-999999999999",
  "ubicado": true,
  "riesgo_antes": null,
  "riesgo_despues": null,
  "notificacion_final": null,
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "id_rack": "44444444-4444-4444-8444-444444444444",
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_detalle_recepcion": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  "id_recepcion": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
  "id_detalle_reposicion": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "cantidad_recibida": 5,
  "cantidad_rechazada": 0,
  "cantidad_aceptada": 5,
  "lote": "LOTE-EJEMPLO",
  "fecha_vencimiento": "2027-10-13T12:00:00Z",
  "temperatura_recepcion": null,
  "estado_recepcion": "CONFORME",
  "comentario_recepcion": "Conforme",
  "motivo_rechazo": null,
  "id_movimiento": "99999999-9999-4999-8999-999999999999",
  "ubicado": true,
  "riesgo_antes": null,
  "riesgo_despues": null,
  "notificacion_final": null,
  "fecha_creacion": "2026-10-13T12:00:00Z"
}
```

### D. Actualización API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

## Alerta / alertas

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "tipo_alerta": "RIESGO_STOCKOUT",
  "nivel_riesgo": "ALTO",
  "titulo": "Riesgo ilustrativo",
  "mensaje": "Ejemplo documental de contrato; no es una evaluación real.",
  "stock_actual": 10,
  "dias_cobertura": 2,
  "stock_seguridad": 2,
  "punto_reposicion": 12,
  "forecast_7d": 35
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_alerta": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "tipo_alerta": "RIESGO_STOCKOUT",
  "nivel_riesgo": "ALTO",
  "titulo": "Riesgo ilustrativo",
  "mensaje": "Ejemplo documental de contrato; no es una evaluación real.",
  "stock_actual": 10,
  "dias_cobertura": 2,
  "stock_seguridad": 2,
  "punto_reposicion": 12,
  "forecast_7d": 35,
  "estado": "ACTIVA",
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_resolucion": null,
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_alerta": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "tipo_alerta": "RIESGO_STOCKOUT",
  "nivel_riesgo": "ALTO",
  "titulo": "Riesgo ilustrativo",
  "mensaje": "Ejemplo documental de contrato; no es una evaluación real.",
  "stock_actual": 10,
  "dias_cobertura": 2,
  "stock_seguridad": 2,
  "punto_reposicion": 12,
  "forecast_7d": 35,
  "estado": "ACTIVA",
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z",
  "fecha_resolucion": null
}
```

### D. Actualización API

```json
{
  "estado": "VISTA"
}
```

## Recomendacion / recomendaciones

Ejemplo documental individual; referencias y IDs ilustrativos, no dataset ni secuencia ejecutada.

### A. Creación API

```json
{
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_alerta": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
  "tipo_recomendacion": "REABASTECER",
  "nivel_riesgo": "ALTO",
  "cantidad_minima": 10,
  "cantidad_recomendada": 12,
  "cantidad_segura": 14,
  "forecast_7d": 35,
  "explicacion": "Ejemplo documental; no es una decisión ni predicción ejecutada.",
  "origen": "PSITWIN"
}
```

### B. Documento MongoDB (Extended JSON)

```json
{
  "id_recomendacion": "ffffffff-ffff-4fff-8fff-ffffffffffff",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_alerta": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
  "tipo_recomendacion": "REABASTECER",
  "nivel_riesgo": "ALTO",
  "cantidad_minima": 10,
  "cantidad_recomendada": 12,
  "cantidad_segura": 14,
  "forecast_7d": 35,
  "explicacion": "Ejemplo documental; no es una decisión ni predicción ejecutada.",
  "origen": "PSITWIN",
  "estado": "PENDIENTE",
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_aplicacion": null,
  "notificacion_aprobacion": null,
  "_id": {
    "$oid": "0123456789abcdef01234567"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "id_recomendacion": "ffffffff-ffff-4fff-8fff-ffffffffffff",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "id_almacen": "22222222-2222-4222-8222-222222222222",
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_producto": "55555555-5555-4555-8555-555555555555",
  "id_alerta": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
  "tipo_recomendacion": "REABASTECER",
  "nivel_riesgo": "ALTO",
  "cantidad_minima": 10,
  "cantidad_recomendada": 12,
  "cantidad_segura": 14,
  "forecast_7d": 35,
  "explicacion": "Ejemplo documental; no es una decisión ni predicción ejecutada.",
  "origen": "PSITWIN",
  "estado": "PENDIENTE",
  "fecha_creacion": "2026-10-13T12:00:00Z",
  "fecha_actualizacion": "2026-10-13T12:00:00Z",
  "fecha_aplicacion": null,
  "notificacion_aprobacion": null
}
```

### D. Actualización API

```json
{
  "estado": "VALIDADA_OPERARIO"
}
```

## inventario_historial / inventario_historial

Producido por servicio, sin CRUD público independiente.

### A. Creación API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

### B. Documento MongoDB (Extended JSON)

```json
{
  "_id": {
    "$oid": "0123456789abcdef01234567"
  },
  "id_inventario": "66666666-6666-4666-8666-666666666666",
  "id_operario": null,
  "accion": "CREAR",
  "antes": null,
  "despues": {
    "id_producto": "55555555-5555-4555-8555-555555555555",
    "id_rack": "44444444-4444-4444-8444-444444444444",
    "stock_actual": 10,
    "stock_minimo": 5,
    "stock_maximo": 100
  },
  "fecha": {
    "$date": "2026-10-13T12:00:00Z"
  }
}
```

### C. Respuesta/consulta API

```json
{
  "fecha": "2026-10-13T12:00:00Z",
  "id_operario": null,
  "operario_nombre": null,
  "accion": "CREAR",
  "antes": null,
  "despues": {
    "id_producto": "55555555-5555-4555-8555-555555555555",
    "id_rack": "44444444-4444-4444-8444-444444444444",
    "stock_actual": 10,
    "stock_minimo": 5,
    "stock_maximo": 100
  }
}
```

### D. Actualización API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

## email_verifications / email_verifications

Producido por servicio, sin CRUD público independiente.

### A. Creación API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

### B. Documento MongoDB (Extended JSON)

```json
{
  "_id": {
    "$oid": "0123456789abcdef01234567"
  },
  "entity_type": "empresa",
  "entity_id": "11111111-1111-4111-8111-111111111111",
  "email": "empresa@example.com",
  "code_hash": "<HASH_SHA256_OMITIDO>",
  "expires_at": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "attempts": 0,
  "max_attempts": 5,
  "cooldown_until": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "used": false,
  "status": "PENDING",
  "created_at": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "updated_at": {
    "$date": "2026-10-13T12:00:00Z"
  }
}
```

### C. Respuesta/consulta API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

### D. Actualización API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

## notificaciones_email / notificaciones_email

Producido por servicio, sin CRUD público independiente.

### A. Creación API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

### B. Documento MongoDB (Extended JSON)

```json
{
  "_id": {
    "$oid": "0123456789abcdef01234567"
  },
  "event_id": "evento-documental",
  "id_empresa": "11111111-1111-4111-8111-111111111111",
  "recipient": null,
  "subject": "Ejemplo",
  "status": "OMITIDO",
  "error": "EMAIL_ENABLED=false",
  "fecha_actualizacion": {
    "$date": "2026-10-13T12:00:00Z"
  },
  "fecha_creacion": {
    "$date": "2026-10-13T12:00:00Z"
  }
}
```

### C. Respuesta/consulta API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

### D. Actualización API

NO IMPLEMENTADO como CRUD independiente; ver operaciones especializadas.

## Operaciones especializadas

POST /api/v1/auth/login:

```json
{"correo":"operario@example.com","password":"Temporal_documental_2026"}
```

PATCH /api/v1/auth/me/password:

```json
{"password_actual":"Temporal_documental_2026","password_nueva":"Nueva_documental_2026"}
```

POST /api/v1/saiki/ask (EMPRESA):

```json
{"message":"¿Cómo está mi inventario?","page":1,"page_size":25}
```

PATCH /api/v1/recomendaciones/{id_recomendacion}/aprobar-empresa (VALIDADA_OPERARIO):

```json
{
  "id_proveedor": "88888888-8888-4888-8888-888888888888",
  "costo_unitario": 3,
  "fecha_estimada_recepcion": "2026-10-15T12:00:00Z"
}
```

POST /api/v1/detalles-recepcion/{id_detalle}/resolver (EN_EVALUACION):

```json
{"estado_recepcion":"CONFORME","comentario_resolucion":"Inspección conforme","cantidad_aceptada":5,"cantidad_rechazada":0}
```

ProductoUpdate mostrado es PROVEEDOR; OPERARIO solo cambia id_rack, PROVEEDOR lo tiene excluido. Inventario modifica límites. Movimiento/Recepción no tienen API de update/delete general. Recomendación se valida como OPERARIO vía /validar-operario; /estado es EMPRESA y verifica grafo. Para consultar use las rutas GET del siguiente catálogo; los cuerpos C son objetos retornados, las listas retornan arrays de dichos objetos.

## Contratos completos por endpoint

### POST /api/v1/alertas

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 201. Entrada: AlertaCreate. Salida: AlertaResponse. Evidencia: app/controllers/alerta_controller.py:60.

Firma:

```python
async def crear_alerta( data: AlertaCreate, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_alerta(
    data: AlertaCreate,
    user: UsuarioActual = Depends(require_empresa)
):
    data.id_empresa = user.id_empresa
    await AccesoService.verificar_almacen(user, data.id_almacen)
    return await service.crear(data)


```

### GET /api/v1/alertas

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[AlertaResponse]. Evidencia: app/controllers/alerta_controller.py:73.

Firma:

```python
async def listar( user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar(
    user: UsuarioActual = Depends(require_empresa)
):
    return await service.listar_por_empresa(
        user.id_empresa
    )


```

### GET /api/v1/alertas/activas

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[AlertaResponse]. Evidencia: app/controllers/alerta_controller.py:85.

Firma:

```python
async def listar_activas( user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_activas(
    user: UsuarioActual = Depends(require_empresa)
):
    return AccesoService.filtrar_empresa(
        user,
        await service.listar_activas()
    )

```

### GET /api/v1/alertas/empresa/{id_empresa}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[AlertaResponse]. Evidencia: app/controllers/alerta_controller.py:97.

Firma:

```python
async def listar_empresa( id_empresa: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa)
):
    AccesoService.verificar_empresa(user, id_empresa)
    return await service.listar_por_empresa(id_empresa)


```

### GET /api/v1/alertas/almacen/{id_almacen}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[AlertaResponse]. Evidencia: app/controllers/alerta_controller.py:109.

Firma:

```python
async def listar_almacen( id_almacen: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_almacen(user, id_almacen)
    return await service.listar_por_almacen(id_almacen)


```

### GET /api/v1/alertas/producto/{id_producto}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[AlertaResponse]. Evidencia: app/controllers/alerta_controller.py:121.

Firma:

```python
async def listar_producto( id_producto: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_producto(
    id_producto: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_producto(user, id_producto)
    return AccesoService.filtrar_empresa(
        user,
        await service.listar_por_producto(id_producto)
    )


```

### GET /api/v1/alertas/inventario/{id_inventario}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[AlertaResponse]. Evidencia: app/controllers/alerta_controller.py:136.

Firma:

```python
async def listar_inventario( id_inventario: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_inventario(
    id_inventario: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_inventario(user, id_inventario)
    return AccesoService.filtrar_empresa(
        user,
        await service.listar_por_inventario(id_inventario)
    )


```

### GET /api/v1/alertas/nivel/{nivel_riesgo}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[AlertaResponse]. Evidencia: app/controllers/alerta_controller.py:151.

Firma:

```python
async def listar_nivel( nivel_riesgo: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_nivel(
    nivel_riesgo: str,
    user: UsuarioActual = Depends(require_empresa)
):
    return AccesoService.filtrar_empresa(
        user,
        await service.listar_por_nivel(nivel_riesgo)
    )

```

### GET /api/v1/alertas/{id_item}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: AlertaResponse. Evidencia: app/controllers/alerta_controller.py:164.

Firma:

```python
async def obtener( id_item: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener(
    id_item: str,
    user: UsuarioActual = Depends(require_empresa)
):
    return await _verificar(user, id_item)


```

### PATCH /api/v1/alertas/{id_item}/estado

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: AlertaEstadoUpdate. Salida: AlertaResponse. Evidencia: app/controllers/alerta_controller.py:175.

Firma:

```python
async def cambiar_estado( id_item: str, data: AlertaEstadoUpdate, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def cambiar_estado(
    id_item: str,
    data: AlertaEstadoUpdate,
    user: UsuarioActual = Depends(require_empresa)
):
    await _verificar(user, id_item)
    return await service.cambiar_estado(id_item, data)

```

### POST /api/v1/almacenes

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: status.HTTP_201_CREATED. Entrada: AlmacenCreate. Salida: AlmacenResponse. Evidencia: app/controllers/almacen_controller.py:88.

Firma:

```python
async def crear_almacen( data: AlmacenCreate, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_almacen(
    data: AlmacenCreate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    data.id_empresa = user.id_empresa

    return await (
        AlmacenService.crear(
            data
        )
    )


# ============================================================
# OBTENER TODOS
#
# GET /api/v1/almacenes
# ============================================================

```

### GET /api/v1/almacenes

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: status.HTTP_200_OK. Entrada: sin DTO body. Salida: List[ AlmacenResponse ]. Evidencia: app/controllers/almacen_controller.py:120.

Firma:

```python
async def obtener_almacenes( user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_almacenes(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _almacenes_visibles(
        user
    )


# ============================================================
# OBTENER POR EMPRESA
#
# IMPORTANTE:
# Esta ruta debe ir ANTES de /{id_almacen}
#
# GET /api/v1/almacenes/empresa/{id_empresa}
# ============================================================

```

### GET /api/v1/almacenes/empresa/{id_empresa}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: status.HTTP_200_OK. Entrada: sin DTO body. Salida: List[ AlmacenResponse ]. Evidencia: app/controllers/almacen_controller.py:152.

Firma:

```python
async def obtener_almacenes_por_empresa( id_empresa: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_almacenes_por_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    AccesoService.verificar_empresa(
        user,
        id_empresa
    )

    return await _almacenes_visibles(
        user
    )


# ============================================================
# OBTENER POR ID
#
# GET /api/v1/almacenes/{id_almacen}
# ============================================================

```

### GET /api/v1/almacenes/{id_almacen}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: status.HTTP_200_OK. Entrada: sin DTO body. Salida: AlmacenResponse. Evidencia: app/controllers/almacen_controller.py:183.

Firma:

```python
async def obtener_almacen( id_almacen: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await (
        AccesoService.verificar_almacen(
            user,
            id_almacen
        )
    )


# ============================================================
# ACTUALIZAR (EMPRESA)
#
# PUT /api/v1/almacenes/{id_almacen}
# ============================================================

```

### PUT /api/v1/almacenes/{id_almacen}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: status.HTTP_200_OK. Entrada: AlmacenUpdate. Salida: AlmacenResponse. Evidencia: app/controllers/almacen_controller.py:212.

Firma:

```python
async def actualizar_almacen( id_almacen: str, data: AlmacenUpdate, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar_almacen(
    id_almacen: str,
    data: AlmacenUpdate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    return await (
        AlmacenService.actualizar(
            id_almacen,
            data
        )
    )


# ============================================================
# ELIMINAR (EMPRESA)
#
# DELETE /api/v1/almacenes/{id_almacen}
# ============================================================

```

### DELETE /api/v1/almacenes/{id_almacen}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: status.HTTP_200_OK. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/almacen_controller.py:246.

Firma:

```python
async def eliminar_almacen( id_almacen: str, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def eliminar_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    return await (
        AlmacenService.eliminar(
            id_almacen
        )
    )

```

### POST /api/v1/recepciones/{id_recepcion}/detalles

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: status.HTTP_201_CREATED. Entrada: DetalleRecepcionCreate. Salida: DetalleRecepcionResponse. Evidencia: app/controllers/detalle_recepcion_controller.py:64.

Firma:

```python
async def crear( id_recepcion: str, data: DetalleRecepcionCreate, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear(
    id_recepcion: str,
    data: DetalleRecepcionCreate,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_recepcion(
        user,
        id_recepcion
    )

    await AccesoService.verificar_inventario(
        user,
        data.id_inventario
    )

    return await service.crear(
        id_recepcion,
        data,
        user
    )


```

### GET /api/v1/recepciones/{id_recepcion}/detalles

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[DetalleRecepcionResponse]. Evidencia: app/controllers/detalle_recepcion_controller.py:90.

Firma:

```python
async def obtener_por_recepcion( id_recepcion: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_recepcion(
    id_recepcion: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_recepcion(
        user,
        id_recepcion
    )

    return await service.obtener_por_recepcion(
        id_recepcion
    )


```

### GET /api/v1/detalles-recepcion/{id_detalle}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: DetalleRecepcionResponse. Evidencia: app/controllers/detalle_recepcion_controller.py:108.

Firma:

```python
async def obtener_por_id( id_detalle: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_id(
    id_detalle: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return await _verificar_detalle(user, id_detalle)


# ============================================================
# RESOLVER EVALUACION (solo OPERARIO)
# ============================================================

```

### POST /api/v1/detalles-recepcion/{id_detalle}/resolver

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: ResolverEvaluacion. Salida: DetalleRecepcionResponse. Evidencia: app/controllers/detalle_recepcion_controller.py:123.

Firma:

```python
async def resolver_evaluacion( id_detalle: str, data: ResolverEvaluacion, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def resolver_evaluacion(
    id_detalle: str,
    data: ResolverEvaluacion,
    user: UsuarioActual = Depends(require_operario)
):
    await _verificar_detalle(user, id_detalle)

    if data.id_inventario:

        await AccesoService.verificar_inventario(
            user,
            data.id_inventario
        )

    return await service.resolver_evaluacion(
        id_detalle,
        data,
        user
    )

```

### POST /api/v1/ordenes-reposicion/{id_orden}/detalles

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: status.HTTP_201_CREATED. Entrada: DetalleReposicionCreate. Salida: DetalleReposicionResponse. Evidencia: app/controllers/detalle_reposicion_controller.py:59.

Firma:

```python
async def crear( id_orden: str, data: DetalleReposicionCreate, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear(
    id_orden: str,
    data: DetalleReposicionCreate,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    await AccesoService.verificar_producto(user, data.id_producto)
    return await service.crear(id_orden, data)


# EMPRESA, OPERARIO (su almacén) o PROVEEDOR (enviada a él)
```

### GET /api/v1/ordenes-reposicion/{id_orden}/detalles

Estado IMPLEMENTADO. Auth: get_usuario_activo. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[DetalleReposicionResponse]. Evidencia: app/controllers/detalle_reposicion_controller.py:74.

Firma:

```python
async def obtener_por_orden( id_orden: str, user: UsuarioActual = Depends(get_usuario_activo) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_orden(
    id_orden: str,
    user: UsuarioActual = Depends(get_usuario_activo)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.obtener_por_orden(id_orden)


```

### GET /api/v1/detalles-reposicion/{id_detalle}

Estado IMPLEMENTADO. Auth: get_usuario_activo. Éxito HTTP: 200. Entrada: sin DTO body. Salida: DetalleReposicionResponse. Evidencia: app/controllers/detalle_reposicion_controller.py:86.

Firma:

```python
async def obtener_por_id( id_detalle: str, user: UsuarioActual = Depends(get_usuario_activo) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_id(
    id_detalle: str,
    user: UsuarioActual = Depends(get_usuario_activo)
):
    return await _verificar_detalle(user, id_detalle)


```

### PUT /api/v1/detalles-reposicion/{id_detalle}

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: DetalleReposicionUpdate. Salida: DetalleReposicionResponse. Evidencia: app/controllers/detalle_reposicion_controller.py:97.

Firma:

```python
async def actualizar( id_detalle: str, data: DetalleReposicionUpdate, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar(
    id_detalle: str,
    data: DetalleReposicionUpdate,
    user: UsuarioActual = Depends(require_operario)
):
    await _verificar_detalle(user, id_detalle)
    return await service.actualizar(
        id_detalle,
        data
    )


```

### DELETE /api/v1/detalles-reposicion/{id_detalle}

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/detalle_reposicion_controller.py:112.

Firma:

```python
async def eliminar( id_detalle: str, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def eliminar(
    id_detalle: str,
    user: UsuarioActual = Depends(require_operario)
):
    await _verificar_detalle(user, id_detalle)
    return await service.eliminar(id_detalle)

```

### POST /api/v1/auth/register

Estado IMPLEMENTADO. Auth: PÚBLICO. Éxito HTTP: status.HTTP_201_CREATED. Entrada: EmpresaRegisterRequest. Salida: EmpresaResponse. Evidencia: app/controllers/empresa_controller.py:79.

Firma:

```python
async def register( data: EmpresaRegisterRequest ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def register(
    data: EmpresaRegisterRequest
):

    return await (
        empresa_service
        .register_empresa(
            data
        )
    )


# ============================================================
# LOGIN
#
# POST /api/v1/auth/login
# ============================================================

```

### POST /api/v1/auth/login

Estado IMPLEMENTADO. Auth: PÚBLICO. Éxito HTTP: status.HTTP_200_OK. Entrada: LoginRequest. Salida: ( LoginResponse ). Evidencia: app/controllers/empresa_controller.py:110.

Firma:

```python
async def login( data: LoginRequest ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def login(
    data: LoginRequest
):

    return await (
        auth_service
        .login(
            data
        )
    )


# ============================================================
# ME (CUALQUIER ROL)
#
# GET /api/v1/auth/me
#
# Permitido aunque deba cambiar la contraseña.
# ============================================================

```

### GET /api/v1/auth/me

Estado IMPLEMENTADO. Auth: get_current_user. Éxito HTTP: 200. Entrada: sin DTO body. Salida: MeResponse. Evidencia: app/controllers/empresa_controller.py:135.

Firma:

```python
async def me( user: UsuarioActual = Depends( get_current_user ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def me(
    user: UsuarioActual = Depends(
        get_current_user
    )
):

    return await auth_service.me(
        user
    )


# ============================================================
# CAMBIAR PASSWORD (OPERARIO / PROVEEDOR)
#
# PATCH /api/v1/auth/me/password
# ============================================================

```

### PATCH /api/v1/auth/me/password

Estado IMPLEMENTADO. Auth: get_current_user. Éxito HTTP: 200. Entrada: CambiarPasswordRequest. Salida: MessageResponse. Evidencia: app/controllers/empresa_controller.py:160.

Firma:

```python
async def cambiar_mi_password( data: CambiarPasswordRequest, user: UsuarioActual = Depends( get_current_user ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def cambiar_mi_password(
    data: CambiarPasswordRequest,
    user: UsuarioActual = Depends(
        get_current_user
    )
):

    return await auth_service.cambiar_password(
        user,
        data
    )


# ============================================================
# GET PERFIL
#
# GET /api/v1/empresas/me
# ============================================================

```

### GET /api/v1/empresas/me

Estado IMPLEMENTADO. Auth: get_current_empresa_id. Éxito HTTP: 200. Entrada: sin DTO body. Salida: EmpresaResponse. Evidencia: app/controllers/empresa_controller.py:186.

Firma:

```python
async def get_my_empresa( id_empresa: str = Depends( get_current_empresa_id ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def get_my_empresa(
    id_empresa: str = Depends(
        get_current_empresa_id
    )
):

    return await (
        empresa_service
        .get_empresa_profile(
            id_empresa
        )
    )


# ============================================================
# UPDATE PERFIL
#
# PUT /api/v1/empresas/me
# ============================================================

```

### PUT /api/v1/empresas/me

Estado IMPLEMENTADO. Auth: get_current_empresa_id. Éxito HTTP: 200. Entrada: EmpresaUpdateRequest. Salida: EmpresaResponse. Evidencia: app/controllers/empresa_controller.py:213.

Firma:

```python
async def update_my_empresa( data: EmpresaUpdateRequest, id_empresa: str = Depends( get_current_empresa_id ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def update_my_empresa(
    data: EmpresaUpdateRequest,

    id_empresa: str = Depends(
        get_current_empresa_id
    )
):

    return await (
        empresa_service
        .update_empresa_profile(
            id_empresa,
            data
        )
    )


# ============================================================
# PATCH PASSWORD
#
# PATCH /api/v1/empresas/me/password
# ============================================================

```

### PATCH /api/v1/empresas/me/password

Estado IMPLEMENTADO. Auth: get_current_empresa_id. Éxito HTTP: status.HTTP_200_OK. Entrada: EmpresaChangePasswordRequest. Salida: MessageResponse. Evidencia: app/controllers/empresa_controller.py:246.

Firma:

```python
async def change_my_password( data: EmpresaChangePasswordRequest, id_empresa: str = Depends( get_current_empresa_id ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def change_my_password(
    data:
        EmpresaChangePasswordRequest,

    id_empresa: str = Depends(
        get_current_empresa_id
    )
):

    return await (
        empresa_service
        .change_empresa_password(
            id_empresa,
            data
        )
    )


# ============================================================
# DELETE EMPRESA
#
# DELETE /api/v1/empresas/me
# ============================================================

```

### DELETE /api/v1/empresas/me

Estado IMPLEMENTADO. Auth: get_current_empresa_id. Éxito HTTP: status.HTTP_200_OK. Entrada: EmpresaDeleteRequest. Salida: MessageResponse. Evidencia: app/controllers/empresa_controller.py:280.

Firma:

```python
async def delete_my_empresa( data: EmpresaDeleteRequest, id_empresa: str = Depends( get_current_empresa_id ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def delete_my_empresa(
    data: EmpresaDeleteRequest,

    id_empresa: str = Depends(
        get_current_empresa_id
    )
):

    return await (
        empresa_service
        .delete_empresa_profile(
            id_empresa,
            data
        )
    )


```

### POST /api/v1/empresas/{id_empresa}/correo/enviar-verificacion

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: EmailVerificationSendResponse. Evidencia: app/controllers/empresa_controller.py:302.

Firma:

```python
async def send_empresa_email_verification( id_empresa: str, user: UsuarioActual = Depends(require_empresa), ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def send_empresa_email_verification(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa),
):
    AccesoService.verificar_empresa(user, id_empresa)
    return await email_verification_service.request_entity_verification(
        "empresa",
        id_empresa,
    )


```

### POST /api/v1/empresas/{id_empresa}/correo/verificar

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: EmailVerificationCodeRequest. Salida: EmailVerificationResponse. Evidencia: app/controllers/empresa_controller.py:318.

Firma:

```python
async def verify_empresa_email( id_empresa: str, data: EmailVerificationCodeRequest, user: UsuarioActual = Depends(require_empresa), ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def verify_empresa_email(
    id_empresa: str,
    data: EmailVerificationCodeRequest,
    user: UsuarioActual = Depends(require_empresa),
):
    AccesoService.verificar_empresa(user, id_empresa)
    return await email_verification_service.verify_entity_code(
        "empresa",
        id_empresa,
        data.codigo,
    )
```

### GET /api/v1/forecast/debug-history/{id_inventario}

Estado IMPLEMENTADO. Auth: verificar_forecast -> require_empresa + verificar_inventario (app/main.py). Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/forecast_controller.py:242.

Firma:

```python
async def debug_history( id_inventario: str, dias: int = Query( default=30, ge=1, le=500 ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def debug_history(

    id_inventario: str,

    dias: int = Query(
        default=30,
        ge=1,
        le=500
    )

):

    try:

        demand_history = (
            DemandHistory()
        )

        historial = await (
            demand_history
            .obtener_ultimos_dias(

                id_inventario=
                    id_inventario,

                dias=
                    dias
            )
        )

        resumen = await (
            demand_history
            .obtener_resumen(

                id_inventario=
                    id_inventario,

                dias=
                    dias
            )
        )

        return {

            "mensaje":
                "Historial de demanda generado correctamente",

            "resumen":
                resumen,

            "historial":
                historial
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error generando historial "
                f"de demanda: {str(exc)}"
            )
        )


# ============================================================
# DEBUG CONTEXT
# ============================================================

```

### GET /api/v1/forecast/debug-context/{id_inventario}

Estado IMPLEMENTADO. Auth: verificar_forecast -> require_empresa + verificar_inventario (app/main.py). Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/forecast_controller.py:322.

Firma:

```python
async def debug_context( id_inventario: str ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def debug_context(

    id_inventario: str

):

    try:

        demand_history = (
            DemandHistory()
        )

        historial = await (
            demand_history
            .obtener_ultimos_dias(

                id_inventario=
                    id_inventario,

                dias=
                    30
            )
        )

        history_df = (
            _crear_history_dataframe(
                historial
            )
        )

        fecha_base = (
            _obtener_fecha_base(
                history_df
            )
        )

        context_builder = (
            MLContextBuilder()
        )

        resultado = await (
            context_builder.build(

                id_inventario=
                    id_inventario,

                fecha_base=
                    fecha_base.to_pydatetime()
            )
        )

        return {

            "mensaje":
                "Contexto ML generado correctamente",

            "id_inventario":
                id_inventario,

            "fecha_base_forecast":
                fecha_base.strftime(
                    "%Y-%m-%d"
                ),

            **resultado
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error construyendo contexto "
                f"ML: {str(exc)}"
            )
        )


# ============================================================
# DEBUG FEATURES
# ============================================================

```

### GET /api/v1/forecast/debug-features/{id_inventario}

Estado IMPLEMENTADO. Auth: verificar_forecast -> require_empresa + verificar_inventario (app/main.py). Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/forecast_controller.py:415.

Firma:

```python
async def debug_features( id_inventario: str, dias: int = Query( default=30, ge=1, le=500 ), horizon: int = Query( default=1, ge=1, le=7 ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def debug_features(

    id_inventario: str,

    dias: int = Query(
        default=30,
        ge=1,
        le=500
    ),

    horizon: int = Query(
        default=1,
        ge=1,
        le=7
    )

):

    try:

        # ========================================================
        # HISTORIAL
        # ========================================================

        demand_history = (
            DemandHistory()
        )

        historial = await (
            demand_history
            .obtener_ultimos_dias(

                id_inventario=
                    id_inventario,

                dias=
                    dias
            )
        )

        history_df = (
            _crear_history_dataframe(
                historial
            )
        )

        fecha_base = (
            _obtener_fecha_base(
                history_df
            )
        )

        fecha_objetivo = (

            fecha_base

            + pd.Timedelta(
                days=horizon
            )
        )


        # ========================================================
        # CONTEXTO ESPECIFICO DEL HORIZON
        # ========================================================

        context_builder = (
            MLContextBuilder()
        )

        context = await (
            context_builder
            .build_feature_context(

                id_inventario=
                    id_inventario,

                fecha_base=
                    fecha_base.to_pydatetime(),

                horizon=
                    horizon
            )
        )


        # ========================================================
        # FEATURES
        # ========================================================

        features = (
            feature_builder
            .build_demand_features(

                history=
                    history_df,

                horizon=
                    horizon,

                context=
                    context
            )
        )

        missing_features = (
            feature_builder
            .missing_features(
                features
            )
        )

        features_modelo = {

            feature:
                features.get(
                    feature
                )

            for feature
            in feature_builder.features
        }

        conteo = (
            _contar_features(
                features_modelo
            )
        )

        return {

            "mensaje":
                "Features generadas correctamente",

            "id_inventario":
                id_inventario,

            "configuracion": {

                "dias_historial":
                    dias,

                "horizon":
                    horizon,

                "fecha_base":
                    fecha_base.strftime(
                        "%Y-%m-%d"
                    ),

                "fecha_objetivo":
                    fecha_objetivo.strftime(
                        "%Y-%m-%d"
                    ),

                "future_effective_lag":
                    7 - horizon
            },

            "contexto_ml": {

                "cantidad":
                    len(
                        context
                    ),

                "features":
                    _features_to_json(
                        context
                    )
            },

            "resumen": {

                "features_modelo":
                    len(
                        feature_builder.features
                    ),

                "features_disponibles":
                    conteo[
                        "disponibles"
                    ],

                "features_sin_datos":
                    conteo[
                        "sin_datos"
                    ],

                "features_faltantes":
                    len(
                        missing_features
                    )
            },

            "missing_features":
                missing_features,

            "features":
                _features_to_json(
                    features_modelo
                )
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error construyendo features "
                f"ML: {str(exc)}"
            )
        )


# ============================================================
# DEBUG PREDICT
# ============================================================

```

### GET /api/v1/forecast/debug-predict/{id_inventario}

Estado IMPLEMENTADO. Auth: verificar_forecast -> require_empresa + verificar_inventario (app/main.py). Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/forecast_controller.py:645.

Firma:

```python
async def debug_predict( id_inventario: str, dias: int = Query( default=30, ge=1, le=500 ), horizon: int = Query( default=1, ge=1, le=7 ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def debug_predict(

    id_inventario: str,

    dias: int = Query(
        default=30,
        ge=1,
        le=500
    ),

    horizon: int = Query(
        default=1,
        ge=1,
        le=7
    )

):

    try:

        demand_history = (
            DemandHistory()
        )

        historial = await (
            demand_history
            .obtener_ultimos_dias(

                id_inventario=
                    id_inventario,

                dias=
                    dias
            )
        )

        history_df = (
            _crear_history_dataframe(
                historial
            )
        )

        fecha_base = (
            _obtener_fecha_base(
                history_df
            )
        )

        fecha_objetivo = (

            fecha_base

            + pd.Timedelta(
                days=horizon
            )
        )


        # ========================================================
        # CONTEXTO D+N
        # ========================================================

        context_builder = (
            MLContextBuilder()
        )

        context = await (
            context_builder
            .build_feature_context(

                id_inventario=
                    id_inventario,

                fecha_base=
                    fecha_base.to_pydatetime(),

                horizon=
                    horizon
            )
        )


        # ========================================================
        # FEATURES
        # ========================================================

        features = (
            feature_builder
            .build_demand_features(

                history=
                    history_df,

                horizon=
                    horizon,

                context=
                    context
            )
        )

        missing_features = (
            feature_builder
            .missing_features(
                features
            )
        )

        if missing_features:

            raise ValueError(
                "Faltan features requeridas "
                "por LightGBM: "
                + ", ".join(
                    missing_features
                )
            )

        features_modelo = {

            feature:
                features.get(
                    feature
                )

            for feature
            in feature_builder.features
        }

        conteo = (
            _contar_features(
                features_modelo
            )
        )


        # ========================================================
        # PREDICCION
        # ========================================================

        predictor = (
            DemandPredictor(
                loader=model_loader
            )
        )

        demanda_predicha = (
            predictor.predict_horizon(

                features=
                    features,

                horizon=
                    horizon
            )
        )

        return {

            "mensaje":
                "Predicción generada correctamente",

            "id_inventario":
                id_inventario,

            "modelo":
                "LightGBM Global",

            "horizon":
                horizon,

            "future_effective_lag":
                7 - horizon,

            "fecha_base":
                fecha_base.strftime(
                    "%Y-%m-%d"
                ),

            "fecha_objetivo":
                fecha_objetivo.strftime(
                    "%Y-%m-%d"
                ),

            "dias_historial":
                dias,

            "contexto_ml": {

                "cantidad":
                    len(
                        context
                    ),

                "features":
                    _features_to_json(
                        context
                    )
            },

            "features": {

                "total":
                    len(
                        feature_builder.features
                    ),

                "disponibles":
                    conteo[
                        "disponibles"
                    ],

                "sin_datos":
                    conteo[
                        "sin_datos"
                    ],

                "faltantes":
                    len(
                        missing_features
                    )
            },

            "demanda_predicha":
                round(
                    float(
                        demanda_predicha
                    ),
                    4
                )
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error realizando predicción "
                f"ML: {str(exc)}"
            )
        )


# ============================================================
# PREDICT 7 DAYS
# ============================================================

```

### GET /api/v1/forecast/predict-7-days/{id_inventario}

Estado IMPLEMENTADO. Auth: verificar_forecast -> require_empresa + verificar_inventario (app/main.py). Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/forecast_controller.py:903.

Firma:

```python
async def predict_7_days( id_inventario: str, dias: int = Query( default=30, ge=7, le=500 ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def predict_7_days(

    id_inventario: str,

    dias: int = Query(
        default=30,
        ge=7,
        le=500
    )

):

    try:

        # ========================================================
        # HISTORIAL
        # ========================================================

        demand_history = (
            DemandHistory()
        )

        historial = await (
            demand_history
            .obtener_ultimos_dias(

                id_inventario=
                    id_inventario,

                dias=
                    dias
            )
        )

        history_df = (
            _crear_history_dataframe(
                historial
            )
        )

        fecha_base = (
            _obtener_fecha_base(
                history_df
            )
        )


        # ========================================================
        # CONTEXTOS D+1 ... D+7
        #
        # Cada horizonte recibe:
        #
        # 13 features base
        # +
        # future_store_lag_7
        # +
        # future_dept_lag_7
        #
        # TOTAL = 15
        # ========================================================

        context_builder = (
            MLContextBuilder()
        )

        contexts_by_horizon = await (
            context_builder
            .build_feature_contexts_7_days(

                id_inventario=
                    id_inventario,

                fecha_base=
                    fecha_base.to_pydatetime()
            )
        )


        # ========================================================
        # FEATURES D+1 ... D+7
        # ========================================================

        features_by_horizon = {}

        features_por_horizonte = {}

        contexto_por_horizonte = {}

        for horizon in range(
            1,
            8
        ):

            context = (
                contexts_by_horizon[
                    horizon
                ]
            )

            features = (
                feature_builder
                .build_demand_features(

                    history=
                        history_df,

                    horizon=
                        horizon,

                    context=
                        context
                )
            )

            missing_features = (
                feature_builder
                .missing_features(
                    features
                )
            )

            if missing_features:

                raise ValueError(
                    f"D+{horizon}: faltan "
                    "features requeridas por "
                    "LightGBM: "
                    + ", ".join(
                        missing_features
                    )
                )

            features_by_horizon[
                horizon
            ] = features

            features_modelo = {

                feature:
                    features.get(
                        feature
                    )

                for feature
                in feature_builder.features
            }

            conteo = (
                _contar_features(
                    features_modelo
                )
            )

            features_por_horizonte[
                f"D+{horizon}"
            ] = {

                "disponibles":
                    conteo[
                        "disponibles"
                    ],

                "sin_datos":
                    conteo[
                        "sin_datos"
                    ]
            }

            contexto_por_horizonte[
                f"D+{horizon}"
            ] = {

                "effective_lag":
                    7 - horizon,

                "future_store_lag_7":
                    context.get(
                        "future_store_lag_7"
                    ),

                "future_dept_lag_7":
                    context.get(
                        "future_dept_lag_7"
                    )
            }


        # ========================================================
        # PREDICTOR
        # ========================================================

        predictor = (
            DemandPredictor(
                loader=model_loader
            )
        )

        forecast = (
            predictor.predict_7_days(

                features_by_horizon=
                    features_by_horizon,

                start_date=
                    fecha_base.date()
            )
        )


        # ========================================================
        # RESUMEN
        # ========================================================

        demanda_total_7d = float(
            forecast[
                "demanda_7d"
            ]
        )

        demanda_promedio_diaria = (

            demanda_total_7d

            / 7.0
        )

        fecha_desde = (

            fecha_base

            + pd.Timedelta(
                days=1
            )
        )

        fecha_hasta = (

            fecha_base

            + pd.Timedelta(
                days=7
            )
        )


        # ========================================================
        # RESPONSE
        # ========================================================

        return {

            "mensaje":
                "Forecast de 7 días generado correctamente",

            "id_inventario":
                id_inventario,

            "modelo":
                "LightGBM Direct Horizon",

            "modo_modelo":
                "global",

            "dias_historial":
                dias,

            "fecha_base":
                fecha_base.strftime(
                    "%Y-%m-%d"
                ),

            "periodo_forecast": {

                "desde":
                    fecha_desde.strftime(
                        "%Y-%m-%d"
                    ),

                "hasta":
                    fecha_hasta.strftime(
                        "%Y-%m-%d"
                    )
            },

            "contexto_ml": {

                "cantidad_features_por_horizonte":
                    15,

                "future_features":
                    contexto_por_horizonte
            },

            "features_por_horizonte":
                features_por_horizonte,

            "demanda_total_7d":
                round(
                    demanda_total_7d,
                    4
                ),

            "demanda_promedio_diaria":
                round(
                    demanda_promedio_diaria,
                    4
                ),

            "predicciones_diarias":
                forecast[
                    "predicciones_diarias"
                ]
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error generando forecast "
                f"de 7 días: {str(exc)}"
            )
        )


# ============================================================
# DEBUG FEATURE INFO
# ============================================================

```

### GET /api/v1/forecast/debug-feature-info

Estado IMPLEMENTADO. Auth: verificar_forecast -> require_empresa + verificar_inventario (app/main.py). Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/forecast_controller.py:1243.

Firma:

```python
async def debug_feature_info():
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def debug_feature_info():

    try:

        return (
            feature_builder.info()
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error obteniendo información "
                f"del FeatureBuilder: {str(exc)}"
            )
        )
```

### POST /api/v1/inventarios

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: status.HTTP_201_CREATED. Entrada: InventarioCreate. Salida: InventarioResponse. Evidencia: app/controllers/inventario_controller.py:66.

Firma:

```python
async def crear_inventario( data: InventarioCreate, user: UsuarioActual = Depends( require_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_inventario(
    data: InventarioCreate,
    user: UsuarioActual = Depends(
        require_operario
    )
):

    await AccesoService.verificar_rack(
        user,
        data.id_rack
    )

    await AccesoService.verificar_producto(
        user,
        data.id_producto
    )

    return await service.crear_inventario(
        data,
        user.id_operario
    )


# =============================================================
# OBTENER TODO
# =============================================================

```

### GET /api/v1/inventarios

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ InventarioResponse ]. Evidencia: app/controllers/inventario_controller.py:99.

Firma:

```python
async def obtener_inventarios( user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_inventarios(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_inventarios()
    )


# =============================================================
# STOCK BAJO
# =============================================================

```

### GET /api/v1/inventarios/stock-bajo

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ InventarioResponse ]. Evidencia: app/controllers/inventario_controller.py:121.

Firma:

```python
async def obtener_stock_bajo( user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_stock_bajo(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_stock_bajo()
    )


# =============================================================
# SIN STOCK
# =============================================================

```

### GET /api/v1/inventarios/sin-stock

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ InventarioResponse ]. Evidencia: app/controllers/inventario_controller.py:143.

Firma:

```python
async def obtener_sin_stock( user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_sin_stock(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_sin_stock()
    )


# =============================================================
# SOBRE STOCK
# =============================================================

```

### GET /api/v1/inventarios/sobre-stock

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ InventarioResponse ]. Evidencia: app/controllers/inventario_controller.py:165.

Firma:

```python
async def obtener_sobre_stock( user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_sobre_stock(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_sobre_stock()
    )


# =============================================================
# POR PRODUCTO
# =============================================================

```

### GET /api/v1/inventarios/producto/{id_producto}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ InventarioResponse ]. Evidencia: app/controllers/inventario_controller.py:187.

Firma:

```python
async def obtener_inventario_producto( id_producto: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_inventario_producto(
    id_producto: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    return await _filtrar_alcance(
        user,
        await service.obtener_por_producto(
            id_producto
        )
    )


# =============================================================
# POR RACK
# =============================================================

```

### GET /api/v1/inventarios/rack/{id_rack}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ InventarioResponse ]. Evidencia: app/controllers/inventario_controller.py:217.

Firma:

```python
async def obtener_inventario_rack( id_rack: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_inventario_rack(
    id_rack: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await (
        service.obtener_por_rack(
            id_rack
        )
    )


# =============================================================
# POR ID
# =============================================================

```

### GET /api/v1/inventarios/{id_inventario}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: InventarioResponse. Evidencia: app/controllers/inventario_controller.py:244.

Firma:

```python
async def obtener_inventario( id_inventario: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_inventario(
    id_inventario: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await (
        AccesoService.verificar_inventario(
            user,
            id_inventario
        )
    )


# =============================================================
# ACTUALIZAR LIMITES (OPERARIO)
# =============================================================

```

### PUT /api/v1/inventarios/{id_inventario}

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: InventarioUpdate. Salida: InventarioResponse. Evidencia: app/controllers/inventario_controller.py:267.

Firma:

```python
async def actualizar_inventario( id_inventario: str, data: InventarioUpdate, user: UsuarioActual = Depends( require_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar_inventario(
    id_inventario: str,
    data: InventarioUpdate,
    user: UsuarioActual = Depends(
        require_operario
    )
):

    await AccesoService.verificar_inventario(
        user,
        id_inventario
    )

    return await (
        service.actualizar_inventario(
            id_inventario,
            data,
            user.id_operario
        )
    )


# =============================================================
# HISTORIAL DE CAMBIOS (EMPRESA / OPERARIO)
# =============================================================

```

### GET /api/v1/inventarios/{id_inventario}/historial

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ InventarioHistorialResponse ]. Evidencia: app/controllers/inventario_controller.py:299.

Firma:

```python
async def obtener_historial( id_inventario: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_historial(
    id_inventario: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_inventario(
        user,
        id_inventario
    )

    return await (
        service.obtener_historial(
            id_inventario
        )
    )


# =============================================================
# ELIMINAR (OPERARIO, sin stock)
# =============================================================

```

### DELETE /api/v1/inventarios/{id_inventario}

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: status.HTTP_200_OK. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/inventario_controller.py:326.

Firma:

```python
async def eliminar_inventario( id_inventario: str, user: UsuarioActual = Depends( require_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def eliminar_inventario(
    id_inventario: str,
    user: UsuarioActual = Depends(
        require_operario
    )
):

    await AccesoService.verificar_inventario(
        user,
        id_inventario
    )

    return await (
        service.eliminar_inventario(
            id_inventario
        )
    )

```

### GET /api/v1/inventory-risk

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ InventoryRiskResponse ]. Evidencia: app/controllers/inventory_risk_controller.py:52.

Firma:

```python
async def evaluar_todos( generar_alertas: bool = Query( default=False, description=( "Si es true, crea o actualiza " "alertas y recomendaciones " "para inventarios con riesgo " "alto o crítico." ) ), user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def evaluar_todos(
    generar_alertas: bool = Query(
        default=False,
        description=(
            "Si es true, crea o actualiza "
            "alertas y recomendaciones "
            "para inventarios con riesgo "
            "alto o crítico."
        )
    ),
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await service.evaluar_todos(
        generar_alertas=
            generar_alertas,
        ids_inventario=
            await AccesoService.ids_inventarios(
                user
            )
    )


```

### GET /api/v1/inventory-risk/{id_inventario}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: InventoryRiskResponse. Evidencia: app/controllers/inventory_risk_controller.py:84.

Firma:

```python
async def evaluar_inventario( id_inventario: str, generar_alertas: bool = Query( default=True, description=( "Si es true, crea o actualiza " "automáticamente la alerta y " "la recomendación cuando existe " "riesgo alto o crítico." ) ), user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def evaluar_inventario(
    id_inventario: str,
    generar_alertas: bool = Query(
        default=True,
        description=(
            "Si es true, crea o actualiza "
            "automáticamente la alerta y "
            "la recomendación cuando existe "
            "riesgo alto o crítico."
        )
    ),
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_inventario(
        user,
        id_inventario
    )

    return await service.evaluar(
        id_inventario=
            id_inventario,
        generar_alertas=
            generar_alertas
    )

```

### POST /api/v1/movimientos

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: status.HTTP_201_CREATED. Entrada: MovimientoCreate. Salida: MovimientoResponse. Evidencia: app/controllers/movimiento_controller.py:79.

Firma:

```python
async def crear_movimiento( data: MovimientoCreate, user: UsuarioActual = Depends( require_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_movimiento(
    data: MovimientoCreate,
    user: UsuarioActual = Depends(
        require_operario
    )
):

    if (
        data.tipo_movimiento != TipoMovimiento.SALIDA
        or data.motivo_movimiento not in (
            MotivoMovimiento.VENTA,
            MotivoMovimiento.VENCIMIENTO
        )
    ):

        raise HTTPException(
            status_code=422,
            detail=(
                "Solo se pueden registrar SALIDAS "
                "por VENTA o VENCIMIENTO"
            )
        )

    await AccesoService.verificar_inventario(
        user,
        data.id_inventario
    )

    # Campo interno (recepciones): no se acepta del cliente.
    data.id_detalle_recepcion = None

    return (
        await service.enriquecer(
            [
                await service.crear_movimiento(
                    data,
                    user
                )
            ]
        )
    )[0]


# ============================================================
# OBTENER TODOS
# ============================================================

```

### GET /api/v1/movimientos

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[MovimientoResponse]. Evidencia: app/controllers/movimiento_controller.py:130.

Firma:

```python
async def obtener_movimientos( user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_movimientos(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_movimientos()
    )


# ============================================================
# POR INVENTARIO
# ============================================================

```

### GET /api/v1/movimientos/inventario/{id_inventario}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[MovimientoResponse]. Evidencia: app/controllers/movimiento_controller.py:150.

Firma:

```python
async def obtener_por_inventario( id_inventario: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_inventario(
    id_inventario: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_inventario(
        user,
        id_inventario
    )

    return await service.enriquecer(
        await service.obtener_por_inventario(
            id_inventario
        )
    )


# ============================================================
# POR PRODUCTO
# ============================================================

```

### GET /api/v1/movimientos/producto/{id_producto}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[MovimientoResponse]. Evidencia: app/controllers/movimiento_controller.py:177.

Firma:

```python
async def obtener_por_producto( id_producto: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_producto(
    id_producto: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    return await _filtrar_alcance(
        user,
        await service.obtener_por_producto(
            id_producto
        )
    )


# ============================================================
# POR RACK
# ============================================================

```

### GET /api/v1/movimientos/rack/{id_rack}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[MovimientoResponse]. Evidencia: app/controllers/movimiento_controller.py:205.

Firma:

```python
async def obtener_por_rack( id_rack: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_rack(
    id_rack: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await service.enriquecer(
        await service.obtener_por_rack(
            id_rack
        )
    )


# ============================================================
# POR OPERARIO
# ============================================================

```

### GET /api/v1/movimientos/operario/{id_operario}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[MovimientoResponse]. Evidencia: app/controllers/movimiento_controller.py:232.

Firma:

```python
async def obtener_por_operario( id_operario: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_operario(
    id_operario: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_operario(
        user,
        id_operario
    )

    return await _filtrar_alcance(
        user,
        await service.obtener_por_operario(
            id_operario
        )
    )


# ============================================================
# POR TIPO
# ============================================================

```

### GET /api/v1/movimientos/tipo/{tipo_movimiento}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[MovimientoResponse]. Evidencia: app/controllers/movimiento_controller.py:260.

Firma:

```python
async def obtener_por_tipo( tipo_movimiento: TipoMovimiento, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_tipo(
    tipo_movimiento: TipoMovimiento,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_por_tipo(
            tipo_movimiento
        )
    )


# ============================================================
# POR MOTIVO
# ============================================================

```

### GET /api/v1/movimientos/motivo/{motivo_movimiento}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[MovimientoResponse]. Evidencia: app/controllers/movimiento_controller.py:283.

Firma:

```python
async def obtener_por_motivo( motivo_movimiento: MotivoMovimiento, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_motivo(
    motivo_movimiento: MotivoMovimiento,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await _filtrar_alcance(
        user,
        await service.obtener_por_motivo(
            motivo_movimiento
        )
    )


# ============================================================
# POR ID
# IMPORTANTE: ESTA RUTA VA AL FINAL
# ============================================================

```

### GET /api/v1/movimientos/{id_movimiento}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: MovimientoResponse. Evidencia: app/controllers/movimiento_controller.py:307.

Firma:

```python
async def obtener_movimiento( id_movimiento: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_movimiento(
    id_movimiento: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    movimiento = await service.obtener_movimiento(
        id_movimiento
    )

    await AccesoService.verificar_rack(
        user,
        movimiento["id_rack"]
    )

    return (
        await service.enriquecer(
            [movimiento]
        )
    )[0]

```

### POST /api/v1/operarios

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: status.HTTP_201_CREATED. Entrada: OperarioCreate. Salida: OperarioResponse. Evidencia: app/controllers/operario_controller.py:61.

Firma:

```python
async def crear_operario( data: OperarioCreate, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_operario(
    data: OperarioCreate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.crear_operario(
            data,
            user
        )
    )


# ============================================================
# OBTENER TODOS (EMPRESA)
# ============================================================

```

### GET /api/v1/operarios

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[OperarioResponse]. Evidencia: app/controllers/operario_controller.py:85.

Firma:

```python
async def obtener_operarios( user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_operarios(
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_operarios(
            user
        )
    )


# ============================================================
# POR EMPRESA
# ============================================================

```

### GET /api/v1/operarios/empresa/{id_empresa}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[OperarioResponse]. Evidencia: app/controllers/operario_controller.py:107.

Firma:

```python
async def obtener_por_empresa( id_empresa: str, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_por_empresa(
            id_empresa,
            user
        )
    )


# ============================================================
# POR ESTADO
# ============================================================

```

### GET /api/v1/operarios/estado/{estado}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[OperarioResponse]. Evidencia: app/controllers/operario_controller.py:131.

Firma:

```python
async def obtener_por_estado( estado: str, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_estado(
    estado: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_por_estado(
            estado,
            user
        )
    )


# ============================================================
# POR TURNO
# ============================================================

```

### GET /api/v1/operarios/turno/{turno}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[OperarioResponse]. Evidencia: app/controllers/operario_controller.py:155.

Firma:

```python
async def obtener_por_turno( turno: str, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_turno(
    turno: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_por_turno(
            turno,
            user
        )
    )


# ============================================================
# POR ID
# ============================================================

```

### GET /api/v1/operarios/{id_operario}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: OperarioResponse. Evidencia: app/controllers/operario_controller.py:179.

Firma:

```python
async def obtener_operario( id_operario: str, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_operario(
    id_operario: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.obtener_operario(
            id_operario,
            user
        )
    )


# ============================================================
# ACTUALIZAR
# ============================================================

```

### PUT /api/v1/operarios/{id_operario}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: OperarioUpdate. Salida: OperarioResponse. Evidencia: app/controllers/operario_controller.py:203.

Firma:

```python
async def actualizar_operario( id_operario: str, data: OperarioUpdate, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar_operario(
    id_operario: str,
    data: OperarioUpdate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.actualizar_operario(
            id_operario,
            data,
            user
        )
    )


# ============================================================
# RESET PASSWORD (EMPRESA)
# ============================================================

```

### POST /api/v1/operarios/{id_operario}/reset-password

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: OperarioResetPassword. Salida: OperarioResponse. Evidencia: app/controllers/operario_controller.py:229.

Firma:

```python
async def reset_password( id_operario: str, data: OperarioResetPassword, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def reset_password(
    id_operario: str,
    data: OperarioResetPassword,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.reset_password(
            id_operario,
            data,
            user
        )
    )


```

### POST /api/v1/operarios/{id_operario}/correo/enviar-verificacion

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: EmailVerificationSendResponse. Evidencia: app/controllers/operario_controller.py:251.

Firma:

```python
async def send_operario_email_verification( id_operario: str, user: UsuarioActual = Depends(require_empresa), ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def send_operario_email_verification(
    id_operario: str,
    user: UsuarioActual = Depends(require_empresa),
):
    await AccesoService.verificar_operario(user, id_operario)
    return await email_verification_service.request_entity_verification(
        "operario",
        id_operario,
    )


```

### POST /api/v1/operarios/{id_operario}/correo/verificar

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: EmailVerificationCodeRequest. Salida: EmailVerificationResponse. Evidencia: app/controllers/operario_controller.py:267.

Firma:

```python
async def verify_operario_email( id_operario: str, data: EmailVerificationCodeRequest, user: UsuarioActual = Depends(require_empresa), ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def verify_operario_email(
    id_operario: str,
    data: EmailVerificationCodeRequest,
    user: UsuarioActual = Depends(require_empresa),
):
    await AccesoService.verificar_operario(user, id_operario)
    return await email_verification_service.verify_entity_code(
        "operario",
        id_operario,
        data.codigo,
    )


# ============================================================
# ELIMINAR
# ============================================================

```

### DELETE /api/v1/operarios/{id_operario}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: status.HTTP_200_OK. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/operario_controller.py:289.

Firma:

```python
async def eliminar_operario( id_operario: str, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def eliminar_operario(
    id_operario: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    return await (
        service.eliminar_operario(
            id_operario,
            user
        )
    )

```

### POST /api/v1/ordenes-reposicion

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: status.HTTP_201_CREATED. Entrada: OrdenReposicionCreate. Salida: OrdenReposicionResponse. Evidencia: app/controllers/orden_reposicion_controller.py:89.

Firma:

```python
async def crear( data: OrdenReposicionCreate, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear(
    data: OrdenReposicionCreate,
    user: UsuarioActual = Depends(require_operario)
):
    if not user.id_almacen:
        raise HTTPException(
            status_code=409,
            detail="El operario no tiene almacén asignado"
        )

    data.id_empresa = user.id_empresa
    data.id_almacen = user.id_almacen
    data.id_recomendacion = None

    return await service.crear(
        data,
        user.id_operario
    )


```

### GET /api/v1/ordenes-reposicion

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[OrdenReposicionResponse]. Evidencia: app/controllers/orden_reposicion_controller.py:113.

Firma:

```python
async def obtener_todos( user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_todos(
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return _alcance(
        user,
        await service.obtener_por_empresa(
            user.id_empresa
        )
    )


# ============================================================
# ORDENES ENVIADAS AL PROVEEDOR AUTENTICADO
#
# IMPORTANTE: antes de /proveedor/{id_proveedor}
# ============================================================

```

### GET /api/v1/ordenes-reposicion/proveedor/me

Estado IMPLEMENTADO. Auth: require_proveedor. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[OrdenReposicionResponse]. Evidencia: app/controllers/orden_reposicion_controller.py:134.

Firma:

```python
async def obtener_proveedor_me( user: UsuarioActual = Depends(require_proveedor) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_proveedor_me(
    user: UsuarioActual = Depends(require_proveedor)
):
    return await service.obtener_para_proveedor(
        user.id_proveedor
    )


```

### GET /api/v1/ordenes-reposicion/empresa/{id_empresa}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[OrdenReposicionResponse]. Evidencia: app/controllers/orden_reposicion_controller.py:146.

Firma:

```python
async def obtener_por_empresa( id_empresa: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    AccesoService.verificar_empresa(user, id_empresa)
    return _alcance(
        user,
        await service.obtener_por_empresa(id_empresa)
    )


```

### GET /api/v1/ordenes-reposicion/almacen/{id_almacen}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[OrdenReposicionResponse]. Evidencia: app/controllers/orden_reposicion_controller.py:161.

Firma:

```python
async def obtener_por_almacen( id_almacen: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_almacen(user, id_almacen)
    return await service.obtener_por_almacen(id_almacen)


```

### GET /api/v1/ordenes-reposicion/proveedor/{id_proveedor}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[OrdenReposicionResponse]. Evidencia: app/controllers/orden_reposicion_controller.py:173.

Firma:

```python
async def obtener_por_proveedor( id_proveedor: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_proveedor(
    id_proveedor: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return _alcance(
        user,
        await service.obtener_por_proveedor(id_proveedor)
    )


```

### GET /api/v1/ordenes-reposicion/estado/{estado}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[OrdenReposicionResponse]. Evidencia: app/controllers/orden_reposicion_controller.py:188.

Firma:

```python
async def obtener_por_estado( estado: EstadoOrdenReposicion, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_estado(
    estado: EstadoOrdenReposicion,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return _alcance(
        user,
        await service.obtener_por_estado(
            estado.value
        )
    )


# ============================================================
# VALIDAR (EMPRESA) -> ENVIADA
#
# aprobar / enviar: alias antiguos de validar.
# ============================================================

```

### PATCH /api/v1/ordenes-reposicion/{id_orden}/validar

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: OrdenReposicionResponse. Evidencia: app/controllers/orden_reposicion_controller.py:220.

Firma:

```python
async def validar( id_orden: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def validar(
    id_orden: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.validar(id_orden)


# ============================================================
# DEVOLVER CON COMENTARIO (EMPRESA) -> OBSERVADA
# ============================================================

```

### PATCH /api/v1/ordenes-reposicion/{id_orden}/aprobar

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: OrdenReposicionResponse, deprecated=True. Evidencia: app/controllers/orden_reposicion_controller.py:220.

Firma:

```python
async def validar( id_orden: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def validar(
    id_orden: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.validar(id_orden)


# ============================================================
# DEVOLVER CON COMENTARIO (EMPRESA) -> OBSERVADA
# ============================================================

```

### PATCH /api/v1/ordenes-reposicion/{id_orden}/enviar

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: OrdenReposicionResponse, deprecated=True. Evidencia: app/controllers/orden_reposicion_controller.py:220.

Firma:

```python
async def validar( id_orden: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def validar(
    id_orden: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.validar(id_orden)


# ============================================================
# DEVOLVER CON COMENTARIO (EMPRESA) -> OBSERVADA
# ============================================================

```

### PATCH /api/v1/ordenes-reposicion/{id_orden}/devolver

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: DevolverOrdenRequest. Salida: OrdenReposicionResponse. Evidencia: app/controllers/orden_reposicion_controller.py:236.

Firma:

```python
async def devolver( id_orden: str, data: DevolverOrdenRequest, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def devolver(
    id_orden: str,
    data: DevolverOrdenRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.devolver(
        id_orden,
        data.comentario
    )


# ============================================================
# REENVIAR (OPERARIO): OBSERVADA -> PENDIENTE
# ============================================================

```

### PATCH /api/v1/ordenes-reposicion/{id_orden}/reenviar

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: OrdenReposicionResponse. Evidencia: app/controllers/orden_reposicion_controller.py:256.

Firma:

```python
async def reenviar( id_orden: str, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def reenviar(
    id_orden: str,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.reenviar(id_orden)


```

### PATCH /api/v1/ordenes-reposicion/{id_orden}/cancelar

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: OrdenReposicionResponse. Evidencia: app/controllers/orden_reposicion_controller.py:268.

Firma:

```python
async def cancelar( id_orden: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def cancelar(
    id_orden: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.cancelar(id_orden)


# ============================================================
# REGISTRAR DESPACHO (PROVEEDOR)
# ============================================================

```

### POST /api/v1/ordenes-reposicion/{id_orden}/despacho

Estado IMPLEMENTADO. Auth: require_proveedor. Éxito HTTP: 200. Entrada: DespachoRequest. Salida: OrdenReposicionResponse. Evidencia: app/controllers/orden_reposicion_controller.py:284.

Firma:

```python
async def registrar_despacho( id_orden: str, data: DespachoRequest, user: UsuarioActual = Depends(require_proveedor) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def registrar_despacho(
    id_orden: str,
    data: DespachoRequest,
    user: UsuarioActual = Depends(require_proveedor)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.registrar_despacho(
        id_orden,
        data
    )


# EMPRESA, OPERARIO (su almacén) o PROVEEDOR (enviada a él)
```

### GET /api/v1/ordenes-reposicion/{id_orden}

Estado IMPLEMENTADO. Auth: get_usuario_activo. Éxito HTTP: 200. Entrada: sin DTO body. Salida: OrdenReposicionResponse. Evidencia: app/controllers/orden_reposicion_controller.py:301.

Firma:

```python
async def obtener_por_id( id_orden: str, user: UsuarioActual = Depends(get_usuario_activo) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_id(
    id_orden: str,
    user: UsuarioActual = Depends(get_usuario_activo)
):
    return await AccesoService.verificar_orden(
        user,
        id_orden
    )


```

### PUT /api/v1/ordenes-reposicion/{id_orden}

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: OrdenReposicionUpdate. Salida: OrdenReposicionResponse. Evidencia: app/controllers/orden_reposicion_controller.py:315.

Firma:

```python
async def actualizar( id_orden: str, data: OrdenReposicionUpdate, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar(
    id_orden: str,
    data: OrdenReposicionUpdate,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.actualizar(id_orden, data)


```

### DELETE /api/v1/ordenes-reposicion/{id_orden}

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/orden_reposicion_controller.py:325.

Firma:

```python
async def eliminar( id_orden: str, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def eliminar(
    id_orden: str,
    user: UsuarioActual = Depends(require_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.eliminar(id_orden)

```

### POST /api/v1/productos

Estado IMPLEMENTADO. Auth: require_proveedor. Éxito HTTP: status.HTTP_201_CREATED. Entrada: ProductoCreate. Salida: ProductoResponse. Evidencia: app/controllers/producto_controller.py:94.

Firma:

```python
async def crear_producto( data: ProductoCreate, user: UsuarioActual = Depends( require_proveedor ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_producto(
    data: ProductoCreate,
    user: UsuarioActual = Depends(
        require_proveedor
    )
):

    data.id_empresa = user.id_empresa

    data.id_proveedor = user.id_proveedor

    data.id_rack = None

    return await (
        ProductoService.crear(
            data
        )
    )


# ============================================================
# OBTENER TODOS (DE LA EMPRESA)
# ============================================================

```

### GET /api/v1/productos

Estado IMPLEMENTADO. Auth: get_usuario_activo. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ ProductoResponse ]. Evidencia: app/controllers/producto_controller.py:125.

Firma:

```python
async def obtener_productos( user: UsuarioActual = Depends( get_usuario_activo ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_productos(
    user: UsuarioActual = Depends(
        get_usuario_activo
    )
):

    return _visibles(
        user,
        await (
            ProductoService
            .obtener_todos()
        )
    )


# ============================================================
# REFRIGERADOS
#
# IMPORTANTE:
# antes de /{id_producto}
# ============================================================

```

### GET /api/v1/productos/refrigerados

Estado IMPLEMENTADO. Auth: get_usuario_activo. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ ProductoResponse ]. Evidencia: app/controllers/producto_controller.py:156.

Firma:

```python
async def obtener_productos_refrigerados( user: UsuarioActual = Depends( get_usuario_activo ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_productos_refrigerados(
    user: UsuarioActual = Depends(
        get_usuario_activo
    )
):

    return _visibles(
        user,
        await (
            ProductoService
            .obtener_refrigerados()
        )
    )


# ============================================================
# POR ALMACEN
# ============================================================

```

### GET /api/v1/productos/almacen/{id_almacen}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ ProductoResponse ]. Evidencia: app/controllers/producto_controller.py:184.

Firma:

```python
async def obtener_productos_por_almacen( id_almacen: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_productos_por_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    return await (
        ProductoService
        .obtener_por_almacen(
            id_almacen
        )
    )


# ============================================================
# POR RACK
# ============================================================

```

### GET /api/v1/productos/rack/{id_rack}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ ProductoResponse ]. Evidencia: app/controllers/producto_controller.py:217.

Firma:

```python
async def obtener_productos_por_rack( id_rack: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_productos_por_rack(
    id_rack: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await (
        ProductoService
        .obtener_por_rack(
            id_rack
        )
    )


# ============================================================
# POR CATEGORIA
# ============================================================

```

### GET /api/v1/productos/categoria/{categoria}

Estado IMPLEMENTADO. Auth: get_usuario_activo. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ ProductoResponse ]. Evidencia: app/controllers/producto_controller.py:250.

Firma:

```python
async def obtener_productos_por_categoria( categoria: str, user: UsuarioActual = Depends( get_usuario_activo ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_productos_por_categoria(
    categoria: str,
    user: UsuarioActual = Depends(
        get_usuario_activo
    )
):

    return _visibles(
        user,
        await (
            ProductoService
            .obtener_por_categoria(
                categoria
            )
        )
    )


# ============================================================
# POR ID
#
# DEBE IR DESPUES DE LAS RUTAS ESPECIALES
# ============================================================

```

### GET /api/v1/productos/{id_producto}

Estado IMPLEMENTADO. Auth: get_usuario_activo. Éxito HTTP: 200. Entrada: sin DTO body. Salida: ProductoResponse. Evidencia: app/controllers/producto_controller.py:279.

Firma:

```python
async def obtener_producto( id_producto: str, user: UsuarioActual = Depends( get_usuario_activo ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_producto(
    id_producto: str,
    user: UsuarioActual = Depends(
        get_usuario_activo
    )
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    return await (
        ProductoService
        .obtener_por_id(
            id_producto
        )
    )


# ============================================================
# ACTUALIZAR
#
# PROVEEDOR: sus productos (id_rack se ignora).
# OPERARIO : solo id_rack (rack de referencia).
# ============================================================

```

### PUT /api/v1/productos/{id_producto}

Estado IMPLEMENTADO. Auth: require_roles( "PROVEEDOR", "OPERARIO". Éxito HTTP: 200. Entrada: ProductoUpdate. Salida: ProductoResponse. Evidencia: app/controllers/producto_controller.py:311.

Firma:

```python
async def actualizar_producto( id_producto: str, data: ProductoUpdate, user: UsuarioActual = Depends( require_roles( "PROVEEDOR", "OPERARIO" ) ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar_producto(
    id_producto: str,
    data: ProductoUpdate,
    user: UsuarioActual = Depends(
        require_roles(
            "PROVEEDOR",
            "OPERARIO"
        )
    )
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    if user.es_operario:

        if data.model_fields_set - {"id_rack"}:

            raise HTTPException(
                status_code=403,
                detail=(
                    "El operario solo puede cambiar "
                    "el rack de referencia (id_rack)"
                )
            )

        if data.id_rack:

            await AccesoService.verificar_rack(
                user,
                data.id_rack
            )

    else:

        # El proveedor no gestiona racks: se conserva
        # el rack de referencia actual.
        data = ProductoUpdate(
            **data.model_dump(
                exclude_unset=True,
                exclude={"id_rack"}
            )
        )

    return await (
        ProductoService.actualizar(
            id_producto,
            data
        )
    )


# ============================================================
# ELIMINAR (PROVEEDOR, los suyos)
# ============================================================

```

### DELETE /api/v1/productos/{id_producto}

Estado IMPLEMENTADO. Auth: require_proveedor. Éxito HTTP: status.HTTP_200_OK. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/producto_controller.py:376.

Firma:

```python
async def eliminar_producto( id_producto: str, user: UsuarioActual = Depends( require_proveedor ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def eliminar_producto(
    id_producto: str,
    user: UsuarioActual = Depends(
        require_proveedor
    )
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    # Un producto con inventario no se borra
    # (dejaría stock huérfano en los racks).
    if await InventarioRepository().obtener_por_producto(
        id_producto
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "El producto tiene inventarios; "
                "no puede eliminarse"
            )
        )

    return await (
        ProductoService.eliminar(
            id_producto
        )
    )

```

### POST /api/v1/proveedores

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: status.HTTP_201_CREATED. Entrada: ProveedorCreate. Salida: ProveedorResponse. Evidencia: app/controllers/proveedor_controller.py:72.

Firma:

```python
async def crear( data: ProveedorCreate, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear(
    data: ProveedorCreate,
    user: UsuarioActual = Depends(require_empresa)
):
    data.id_empresa = user.id_empresa
    return sanitizar_cuenta(await service.crear(data))


```

### GET /api/v1/proveedores

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ProveedorResponse]. Evidencia: app/controllers/proveedor_controller.py:84.

Firma:

```python
async def obtener_todos( user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_todos(
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return _lista(
        await service.obtener_por_empresa(
            user.id_empresa
        )
    )


```

### GET /api/v1/proveedores/empresa/{id_empresa}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ProveedorResponse]. Evidencia: app/controllers/proveedor_controller.py:98.

Firma:

```python
async def obtener_por_empresa( id_empresa: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    AccesoService.verificar_empresa(user, id_empresa)
    return _lista(await service.obtener_por_empresa(id_empresa))


```

### GET /api/v1/proveedores/estado/{estado}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ProveedorResponse]. Evidencia: app/controllers/proveedor_controller.py:110.

Firma:

```python
async def obtener_por_estado( estado: EstadoProveedor, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_estado(
    estado: EstadoProveedor,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    return _lista(
        AccesoService.filtrar_empresa(
            user,
            await service.obtener_por_estado(
                estado.value
            )
        )
    )


```

### GET /api/v1/proveedores/{id_proveedor}

Estado IMPLEMENTADO. Auth: get_usuario_activo. Éxito HTTP: 200. Entrada: sin DTO body. Salida: ProveedorResponse. Evidencia: app/controllers/proveedor_controller.py:128.

Firma:

```python
async def obtener_por_id( id_proveedor: str, user: UsuarioActual = Depends(get_usuario_activo) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_id(
    id_proveedor: str,
    user: UsuarioActual = Depends(get_usuario_activo)
):
    if (
        user.es_proveedor
        and id_proveedor != user.id_proveedor
    ):
        raise HTTPException(
            status_code=403,
            detail="Solo puede consultar su propio proveedor"
        )

    return sanitizar_cuenta(
        await AccesoService.verificar_proveedor(
            user,
            id_proveedor
        )
    )


```

### PUT /api/v1/proveedores/{id_proveedor}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: ProveedorUpdate. Salida: ProveedorResponse. Evidencia: app/controllers/proveedor_controller.py:153.

Firma:

```python
async def actualizar( id_proveedor: str, data: ProveedorUpdate, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar(
    id_proveedor: str,
    data: ProveedorUpdate,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return sanitizar_cuenta(
        await service.actualizar(
            id_proveedor,
            data
        )
    )


# ============================================================
# RESET PASSWORD (EMPRESA)
#
# Crea o restablece la cuenta del proveedor.
# ============================================================

```

### POST /api/v1/proveedores/{id_proveedor}/reset-password

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: ResetPasswordRequest. Salida: ProveedorResponse. Evidencia: app/controllers/proveedor_controller.py:177.

Firma:

```python
async def reset_password( id_proveedor: str, data: ResetPasswordRequest, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def reset_password(
    id_proveedor: str,
    data: ResetPasswordRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return sanitizar_cuenta(
        await service.reset_password(
            id_proveedor,
            data.password_temporal,
            str(data.correo) if data.correo else None
        )
    )


```

### DELETE /api/v1/proveedores/{id_proveedor}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/proveedor_controller.py:193.

Firma:

```python
async def eliminar( id_proveedor: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def eliminar(
    id_proveedor: str,
    user: UsuarioActual = Depends(require_empresa)
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return await service.eliminar(id_proveedor)


```

### POST /api/v1/proveedores/{id_proveedor}/correo/enviar-verificacion

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: EmailVerificationSendResponse. Evidencia: app/controllers/proveedor_controller.py:206.

Firma:

```python
async def send_proveedor_email_verification( id_proveedor: str, user: UsuarioActual = Depends(require_empresa), ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def send_proveedor_email_verification(
    id_proveedor: str,
    user: UsuarioActual = Depends(require_empresa),
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return await email_verification_service.request_entity_verification(
        "proveedor",
        id_proveedor,
    )


```

### POST /api/v1/proveedores/{id_proveedor}/correo/verificar

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: EmailVerificationCodeRequest. Salida: EmailVerificationResponse. Evidencia: app/controllers/proveedor_controller.py:222.

Firma:

```python
async def verify_proveedor_email( id_proveedor: str, data: EmailVerificationCodeRequest, user: UsuarioActual = Depends(require_empresa), ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def verify_proveedor_email(
    id_proveedor: str,
    data: EmailVerificationCodeRequest,
    user: UsuarioActual = Depends(require_empresa),
):
    await AccesoService.verificar_proveedor(user, id_proveedor)
    return await email_verification_service.verify_entity_code(
        "proveedor",
        id_proveedor,
        data.codigo,
    )

```

### POST /api/v1/racks

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: status.HTTP_201_CREATED. Entrada: RackCreate. Salida: RackResponse. Evidencia: app/controllers/rack_controller.py:51.

Firma:

```python
async def crear_rack( data: RackCreate, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_rack(
    data: RackCreate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_zona(
        user,
        data.id_zona
    )

    return await service.crear_rack(
        data
    )


```

### GET /api/v1/racks

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ RackResponse ]. Evidencia: app/controllers/rack_controller.py:74.

Firma:

```python
async def obtener_racks( user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_racks(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    return await service.obtener_racks(
        await AccesoService.ids_zonas(
            user
        )
    )


# ============================================================
# RACKS DISPONIBLES PARA UN PRODUCTO
#
# GET /racks/disponibles?id_almacen=&id_producto=&cantidad=
#
# Racks DISPONIBLES del almacén donde caben `cantidad`
# unidades del producto (kg libres y temperatura).
#
# IMPORTANTE: antes de /{id_rack}
# OPERARIO: id_almacen se fuerza al suyo.
# ============================================================

```

### GET /api/v1/racks/disponibles

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ RackDisponibleResponse ]. Evidencia: app/controllers/rack_controller.py:105.

Firma:

```python
async def obtener_racks_disponibles( id_almacen: Optional[str] = Query( default=None ), id_producto: Optional[str] = Query( default=None ), cantidad: float = Query( default=0, ge=0 ), user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_racks_disponibles(
    id_almacen: Optional[str] = Query(
        default=None
    ),
    id_producto: Optional[str] = Query(
        default=None
    ),
    cantidad: float = Query(
        default=0,
        ge=0
    ),
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    if user.es_operario:

        id_almacen = user.id_almacen

        if not id_almacen:
            return []

    elif not id_almacen:

        raise HTTPException(
            status_code=422,
            detail=(
                "Debe indicar id_almacen"
            )
        )

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    producto = None

    if id_producto:

        producto = await (
            AccesoService.verificar_producto(
                user,
                id_producto
            )
        )

    return await service.obtener_disponibles(
        id_almacen,
        producto,
        cantidad
    )


```

### GET /api/v1/racks/zona/{id_zona}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: list[ RackResponse ]. Evidencia: app/controllers/rack_controller.py:166.

Firma:

```python
async def obtener_racks_zona( id_zona: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_racks_zona(
    id_zona: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_zona(
        user,
        id_zona
    )

    return await service.obtener_racks_zona(
        id_zona
    )


```

### GET /api/v1/racks/{id_rack}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: RackResponse. Evidencia: app/controllers/rack_controller.py:187.

Firma:

```python
async def obtener_rack( id_rack: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_rack(
    id_rack: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await service.obtener_rack(
        id_rack
    )


```

### PUT /api/v1/racks/{id_rack}

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: RackUpdate. Salida: RackResponse. Evidencia: app/controllers/rack_controller.py:208.

Firma:

```python
async def actualizar_rack( id_rack: str, data: RackUpdate, user: UsuarioActual = Depends( require_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar_rack(
    id_rack: str,
    data: RackUpdate,
    user: UsuarioActual = Depends(
        require_operario
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await service.actualizar_rack(
        id_rack,
        data
    )


```

### DELETE /api/v1/racks/{id_rack}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/rack_controller.py:230.

Firma:

```python
async def eliminar_rack( id_rack: str, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def eliminar_rack(
    id_rack: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_rack(
        user,
        id_rack
    )

    return await service.eliminar_rack(
        id_rack
    )

```

### POST /api/v1/recepciones

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: status.HTTP_201_CREATED. Entrada: RecepcionMercaderiaCreate. Salida: RecepcionMercaderiaResponse. Evidencia: app/controllers/recepcion_mercaderia_controller.py:49.

Firma:

```python
async def crear( data: RecepcionMercaderiaCreate, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear(
    data: RecepcionMercaderiaCreate,
    user: UsuarioActual = Depends(require_operario)
):
    return await service.crear(data, user)


# ============================================================
# LISTAR
#
# EMPRESA  -> recepciones de sus órdenes
# OPERARIO -> recepciones de las órdenes de su almacén
# ============================================================

```

### GET /api/v1/recepciones

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[RecepcionMercaderiaResponse]. Evidencia: app/controllers/recepcion_mercaderia_controller.py:67.

Firma:

```python
async def obtener_todos( user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_todos(
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    ordenes = await (
        OrdenReposicionRepository()
        .obtener_por_empresa(user.id_empresa)
    )

    return await service.obtener_por_ordenes(
        [
            orden["id_orden_reposicion"]
            for orden in ordenes
            if (
                user.es_empresa
                or orden.get("id_almacen") == user.id_almacen
            )
        ]
    )


```

### GET /api/v1/recepciones/orden/{id_orden}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[RecepcionMercaderiaResponse]. Evidencia: app/controllers/recepcion_mercaderia_controller.py:91.

Firma:

```python
async def obtener_por_orden( id_orden: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_orden(
    id_orden: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_orden(user, id_orden)
    return await service.obtener_por_orden(id_orden)


```

### GET /api/v1/recepciones/operario/{id_operario}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[RecepcionMercaderiaResponse]. Evidencia: app/controllers/recepcion_mercaderia_controller.py:103.

Firma:

```python
async def obtener_por_operario( id_operario: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_operario(
    id_operario: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_operario(user, id_operario)

    return await service.obtener_por_operario(
        id_operario
    )


```

### GET /api/v1/recepciones/{id_recepcion}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: RecepcionMercaderiaResponse. Evidencia: app/controllers/recepcion_mercaderia_controller.py:118.

Firma:

```python
async def obtener_por_id( id_recepcion: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_por_id(
    id_recepcion: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):
    await AccesoService.verificar_recepcion(
        user,
        id_recepcion
    )

    return await service.obtener_por_id(id_recepcion)

```

### POST /api/v1/recomendaciones

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 201. Entrada: RecomendacionCreate. Salida: RecomendacionResponse. Evidencia: app/controllers/recomendacion_controller.py:118.

Firma:

```python
async def crear_recomendacion( data: RecomendacionCreate, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_recomendacion(
    data: RecomendacionCreate,
    user: UsuarioActual = Depends(require_empresa)
):

    data.id_empresa = user.id_empresa

    await AccesoService.verificar_almacen(
        user,
        data.id_almacen
    )

    return await service.crear(
        data
    )


# ============================================================
# LISTAR
# ============================================================

```

### GET /api/v1/recomendaciones

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ RecomendacionResponse ]. Evidencia: app/controllers/recomendacion_controller.py:145.

Firma:

```python
async def listar_recomendaciones( user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_recomendaciones(
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    if user.es_operario:

        if not user.id_almacen:
            return []

        return await service.listar_por_almacen(
            user.id_almacen
        )

    return await service.listar_por_empresa(
        user.id_empresa
    )


# ============================================================
# POR EMPRESA
# ============================================================

```

### GET /api/v1/recomendaciones/empresa/{id_empresa}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ RecomendacionResponse ]. Evidencia: app/controllers/recomendacion_controller.py:173.

Firma:

```python
async def listar_recomendaciones_empresa( id_empresa: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_recomendaciones_empresa(
    id_empresa: str,
    user: UsuarioActual = Depends(require_empresa)
):

    AccesoService.verificar_empresa(
        user,
        id_empresa
    )

    return await service.listar_por_empresa(
        id_empresa
    )


# ============================================================
# POR ALMACEN
# ============================================================

```

### GET /api/v1/recomendaciones/almacen/{id_almacen}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ RecomendacionResponse ]. Evidencia: app/controllers/recomendacion_controller.py:198.

Firma:

```python
async def listar_recomendaciones_almacen( id_almacen: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_recomendaciones_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    return await service.listar_por_almacen(
        id_almacen
    )


# ============================================================
# POR PRODUCTO
# ============================================================

```

### GET /api/v1/recomendaciones/producto/{id_producto}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ RecomendacionResponse ]. Evidencia: app/controllers/recomendacion_controller.py:223.

Firma:

```python
async def listar_recomendaciones_producto( id_producto: str, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_recomendaciones_producto(
    id_producto: str,
    user: UsuarioActual = Depends(require_empresa)
):

    await AccesoService.verificar_producto(
        user,
        id_producto
    )

    return AccesoService.filtrar_empresa(
        user,
        await service.listar_por_producto(
            id_producto
        )
    )


# ============================================================
# POR INVENTARIO
# ============================================================

```

### GET /api/v1/recomendaciones/inventario/{id_inventario}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ RecomendacionResponse ]. Evidencia: app/controllers/recomendacion_controller.py:251.

Firma:

```python
async def listar_recomendaciones_inventario( id_inventario: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def listar_recomendaciones_inventario(
    id_inventario: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    await AccesoService.verificar_inventario(
        user,
        id_inventario
    )

    return await service.listar_por_inventario(
        id_inventario
    )


# ============================================================
# CREAR ORDEN DESDE RECOMENDACION
#
# IMPORTANTE:
# Debe estar antes de /{id_recomendacion}
# ============================================================

```

### POST /api/v1/recomendaciones/{id_recomendacion}/crear-orden

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 201. Entrada: CrearOrdenDesdeRecomendacionRequest. Salida: sin response_model. Evidencia: app/controllers/recomendacion_controller.py:277.

Firma:

```python
async def crear_orden_desde_recomendacion( id_recomendacion: str, data: CrearOrdenDesdeRecomendacionRequest, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_orden_desde_recomendacion(
    id_recomendacion: str,
    data: CrearOrdenDesdeRecomendacionRequest,
    user: UsuarioActual = Depends(require_empresa)
):

    await _verificar(user, id_recomendacion)

    await AccesoService.verificar_proveedor(
        user,
        data.id_proveedor
    )

    return (
        await service
        .crear_orden_desde_recomendacion(

            id_recomendacion=
                id_recomendacion,

            id_proveedor=
                data.id_proveedor,

            costo_unitario=
                data.costo_unitario,

            fecha_estimada_recepcion=
                data.fecha_estimada_recepcion
        )
    )


# ============================================================
# OBTENER RECOMENDACION
# ============================================================

```

### GET /api/v1/recomendaciones/{id_recomendacion}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: RecomendacionResponse. Evidencia: app/controllers/recomendacion_controller.py:317.

Firma:

```python
async def obtener_recomendacion( id_recomendacion: str, user: UsuarioActual = Depends(require_empresa_u_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_recomendacion(
    id_recomendacion: str,
    user: UsuarioActual = Depends(require_empresa_u_operario)
):

    return await _verificar(
        user,
        id_recomendacion
    )


# ============================================================
# CAMBIAR ESTADO
# ============================================================

```

### PATCH /api/v1/recomendaciones/{id_recomendacion}/estado

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: RecomendacionEstadoUpdate. Salida: RecomendacionResponse. Evidencia: app/controllers/recomendacion_controller.py:336.

Firma:

```python
async def cambiar_estado_recomendacion( id_recomendacion: str, data: RecomendacionEstadoUpdate, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def cambiar_estado_recomendacion(
    id_recomendacion: str,
    data: RecomendacionEstadoUpdate,
    user: UsuarioActual = Depends(require_empresa)
):

    await _verificar(user, id_recomendacion)

    return await service.cambiar_estado(
        id_recomendacion,
        data
    )


```

### PATCH /api/v1/recomendaciones/{id_recomendacion}/validar-operario

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: RecomendacionResponse. Evidencia: app/controllers/recomendacion_controller.py:354.

Firma:

```python
async def validar_por_operario( id_recomendacion: str, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def validar_por_operario(
    id_recomendacion: str,
    user: UsuarioActual = Depends(require_operario)
):
    # id_operario: siempre el del token
    await _verificar(user, id_recomendacion)
    id_operario = user.id_operario
    return await service.cambiar_estado(
        id_recomendacion,
        RecomendacionEstadoUpdate(
            estado=EstadoRecomendacion.VALIDADA_OPERARIO
        ),
        id_operario
    )


```

### PATCH /api/v1/recomendaciones/{id_recomendacion}/aprobar-empresa

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: EmpresaAprobacionRequest. Salida: sin response_model. Evidencia: app/controllers/recomendacion_controller.py:373.

Firma:

```python
async def aprobar_por_empresa( id_recomendacion: str, data: EmpresaAprobacionRequest, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def aprobar_por_empresa(
    id_recomendacion: str,
    data: EmpresaAprobacionRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await _verificar(user, id_recomendacion)
    await AccesoService.verificar_proveedor(user, data.id_proveedor)
    data.id_empresa = user.id_empresa
    return await service.aprobar_por_empresa(
        id_recomendacion,
        data,
    )


```

### PATCH /api/v1/recomendaciones/{id_recomendacion}/solicitar-cambios

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: EmpresaCambiosRequest. Salida: RecomendacionResponse,. Evidencia: app/controllers/recomendacion_controller.py:391.

Firma:

```python
async def solicitar_cambios( id_recomendacion: str, data: EmpresaCambiosRequest, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def solicitar_cambios(
    id_recomendacion: str,
    data: EmpresaCambiosRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await _verificar(user, id_recomendacion)
    data.id_empresa = user.id_empresa
    return await service.solicitar_cambios(id_recomendacion, data)


```

### PATCH /api/v1/recomendaciones/{id_recomendacion}/rechazar-empresa

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: EmpresaRechazoRequest. Salida: RecomendacionResponse,. Evidencia: app/controllers/recomendacion_controller.py:405.

Firma:

```python
async def rechazar_por_empresa( id_recomendacion: str, data: EmpresaRechazoRequest, user: UsuarioActual = Depends(require_empresa) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def rechazar_por_empresa(
    id_recomendacion: str,
    data: EmpresaRechazoRequest,
    user: UsuarioActual = Depends(require_empresa)
):
    await _verificar(user, id_recomendacion)
    data.id_empresa = user.id_empresa
    return await service.rechazar_por_empresa(id_recomendacion, data)


```

### PATCH /api/v1/recomendaciones/{id_recomendacion}/actualizar-propuesta

Estado IMPLEMENTADO. Auth: require_operario. Éxito HTTP: 200. Entrada: PropuestaRecomendacionUpdate. Salida: RecomendacionResponse,. Evidencia: app/controllers/recomendacion_controller.py:419.

Firma:

```python
async def actualizar_propuesta( id_recomendacion: str, data: PropuestaRecomendacionUpdate, user: UsuarioActual = Depends(require_operario) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar_propuesta(
    id_recomendacion: str,
    data: PropuestaRecomendacionUpdate,
    user: UsuarioActual = Depends(require_operario)
):
    # id_operario: siempre el del token
    await _verificar(user, id_recomendacion)
    id_operario = user.id_operario
    return await service.actualizar_propuesta(
        id_recomendacion,
        data,
        id_operario,
    )
```

### GET /api/v1/saiki/health

Estado IMPLEMENTADO. Auth: require_empresa (router). Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/saiki_controller.py:47.

Firma:

```python
async def health():
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def health():
    return await service.health()


```

### POST /api/v1/saiki/ask

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: SaikiAskRequest. Salida: SaikiAskResponse. Evidencia: app/controllers/saiki_controller.py:56.

Firma:

```python
async def ask( data: SaikiAskRequest, request: Request, user: UsuarioActual = Depends(require_empresa), ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def ask(
    data: SaikiAskRequest,
    request: Request,
    user: UsuarioActual = Depends(require_empresa),
):
    return await service.ask(data, user, request_id=request.state.saiki_request_id)


```

### POST /api/v1/saiki/chat

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: SaikiAskRequest. Salida: SaikiAskResponse. Evidencia: app/controllers/saiki_controller.py:69.

Firma:

```python
async def chat( data: SaikiAskRequest, request: Request, user: UsuarioActual = Depends(require_empresa), ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def chat(
    data: SaikiAskRequest,
    request: Request,
    user: UsuarioActual = Depends(require_empresa),
):
    return await service.ask(data, user, request_id=request.state.saiki_request_id)

```

### POST /api/v1/zonas

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: status.HTTP_201_CREATED. Entrada: ZonaCreate. Salida: ZonaResponse. Evidencia: app/controllers/zona_controller.py:52.

Firma:

```python
async def crear_zona( data: ZonaCreate, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def crear_zona(
    data: ZonaCreate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_almacen(
        user,
        data.id_almacen
    )

    return await (
        ZonaService.crear(
            data
        )
    )


# ============================================================
# OBTENER TODAS (DEL ALCANCE DEL USUARIO)
# ============================================================

```

### GET /api/v1/zonas

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ ZonaResponse ]. Evidencia: app/controllers/zona_controller.py:81.

Firma:

```python
async def obtener_zonas( user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_zonas(
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    zonas = await (
        AccesoService.zonas_visibles(
            user
        )
    )

    return [
        await ZonaService.normalizar_zona(
            zona
        )
        for zona in zonas
    ]


# ============================================================
# OBTENER POR ALMACEN
#
# Debe ir antes de /{id_zona}
# ============================================================

```

### GET /api/v1/zonas/almacen/{id_almacen}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: List[ ZonaResponse ]. Evidencia: app/controllers/zona_controller.py:113.

Firma:

```python
async def obtener_zonas_por_almacen( id_almacen: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_zonas_por_almacen(
    id_almacen: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_almacen(
        user,
        id_almacen
    )

    return await (
        ZonaService.obtener_por_almacen(
            id_almacen
        )
    )


# ============================================================
# OBTENER POR ID
# ============================================================

```

### GET /api/v1/zonas/{id_zona}

Estado IMPLEMENTADO. Auth: require_empresa_u_operario. Éxito HTTP: 200. Entrada: sin DTO body. Salida: ZonaResponse. Evidencia: app/controllers/zona_controller.py:140.

Firma:

```python
async def obtener_zona( id_zona: str, user: UsuarioActual = Depends( require_empresa_u_operario ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def obtener_zona(
    id_zona: str,
    user: UsuarioActual = Depends(
        require_empresa_u_operario
    )
):

    await AccesoService.verificar_zona(
        user,
        id_zona
    )

    return await (
        ZonaService.obtener_por_id(
            id_zona
        )
    )


# ============================================================
# ACTUALIZAR (EMPRESA)
# ============================================================

```

### PUT /api/v1/zonas/{id_zona}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: 200. Entrada: ZonaUpdate. Salida: ZonaResponse. Evidencia: app/controllers/zona_controller.py:167.

Firma:

```python
async def actualizar_zona( id_zona: str, data: ZonaUpdate, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def actualizar_zona(
    id_zona: str,
    data: ZonaUpdate,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_zona(
        user,
        id_zona
    )

    return await (
        ZonaService.actualizar(
            id_zona,
            data
        )
    )


# ============================================================
# ELIMINAR (EMPRESA)
# ============================================================

```

### DELETE /api/v1/zonas/{id_zona}

Estado IMPLEMENTADO. Auth: require_empresa. Éxito HTTP: status.HTTP_200_OK. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/controllers/zona_controller.py:198.

Firma:

```python
async def eliminar_zona( id_zona: str, user: UsuarioActual = Depends( require_empresa ) ):
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def eliminar_zona(
    id_zona: str,
    user: UsuarioActual = Depends(
        require_empresa
    )
):

    await AccesoService.verificar_zona(
        user,
        id_zona
    )

    return await (
        ZonaService.eliminar(
            id_zona
        )
    )

```

### GET /

Estado IMPLEMENTADO. Auth: PÚBLICO. Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/main.py:279.

Firma:

```python
async def root():
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def root():

    return {

        "mensaje":
            "PsiTwin Inventory API funcionando",

        "version":
            "1.2.0",

        "modulos": [

            "Empresa",
            "Almacen",
            "Zona",
            "Rack",
            "Producto",
            "Inventario",
            "Operario",
            "Movimiento",

            "Proveedor",
            "OrdenReposicion",
            "DetalleReposicion",
            "RecepcionMercaderia",
            "DetalleRecepcion",

            "Alertas",
            "Recomendaciones",

            "InventoryRisk",

            "Forecast"
        ]
    }


# ============================================================
# HEALTH
#
# GET /health
#
# Comprueba:
#
# FastAPI
# +
# MongoDB
# ============================================================

```

### GET /health

Estado IMPLEMENTADO. Auth: PÚBLICO. Éxito HTTP: 200. Entrada: sin DTO body. Salida: sin response_model. Evidencia: app/main.py:333.

Firma:

```python
async def health():
```

Parámetros entre llaves son ruta; Query/primitivas no dependientes restantes son query; data es body; Request/Depends son internos. Validaciones, retornos y errores directos:

```python
async def health():

    try:

        database = (
            get_database()
        )

        await database.command(
            "ping"
        )

        return {

            "status":
                "healthy",

            "api":
                "ok",

            "database":
                "ok",

            "database_name":
                settings.mongodb_database,

            "version":
                "1.2.0"
        }

    except Exception as exc:

        return {

            "status":
                "unhealthy",

            "api":
                "ok",

            "database":
                "error",

            "detail":
                str(exc),

            "version":
                "1.2.0"
        }


# ============================================================
# ARQUITECTURA GENERAL
# ============================================================
#
# EMPRESA
#   ↓
# ALMACEN
#   ↓
# ZONA
#   ↓
# RACK
#
#
# PRODUCTO
#   ↓
# INVENTARIO
#   ↓
# MOVIMIENTO
#
#
# PROVEEDOR
#   ↓
# ORDEN REPOSICION
#   ↓
# DETALLE REPOSICION
#   ↓
# RECEPCION MERCADERIA
#   ↓
# DETALLE RECEPCION
#   ↓
# MOVIMIENTO AUTOMATICO
#   ↓
# INVENTARIO
#
#
# ============================================================
# CAPA DE INTELIGENCIA
# ============================================================
#
# MOVIMIENTOS
#      ↓
# DEMAND HISTORY
#      ↓
# FEATURE BUILDER
#      ↓
# LIGHTGBM
# D+1 ... D+7
#      ↓
# FORECAST
#      ↓
# INVENTORY RISK
#      ↓
# ALERTA
#      ↓
# RECOMENDACION
#      ↓
# LLM
#
# ============================================================


# ============================================================
# EMPRESA
# ============================================================

```
