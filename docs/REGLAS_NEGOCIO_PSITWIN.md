# Reglas de negocio, validaciones y acciones PsiTwin

Fecha de auditoría: 2026-10-13 (America/Lima). Inspección estática del workspace real. No se ejecutó el backend, no se importó app.main, no se abrió una conexión a MongoDB, no se entrenaron modelos, no se generaron registros ni datasets. Los JSON son ejemplos documentales ilustrativos. IMPLEMENTADO significa presencia y trazabilidad en código; no acredita ejecución exitosa ni datos desplegados. NO DEFINIDA significa ausencia de restricción declarada en ese contrato; NO VERIFICABLE significa falta de evidencia de ejecución o del despliegue. INFERIDO se reserva para cardinalidades y efectos deducidos. PARCIALMENTE IMPLEMENTADO distingue código existente con componentes faltantes. NO IMPLEMENTADO se limita al alcance inspeccionado.

## Reglas principales

| ID | Regla | Condición y acción real | Evidencia |
|---|---|---|---|
| RN-01 | Identidad y acceso | JWT rol/empresa y AccesoService; operario restringido a almacén; proveedor a sus productos y órdenes enviadas. | app/dependencies/dependencies.py:98 |
| RN-02 | Contraseña temporal | debe_cambiar_password bloquea get_usuario_activo con PasswordChangeRequired403; /auth/me y /auth/me/password usan get_current_user. | app/dependencies/dependencies.py:287 |
| RN-03 | Unicidad cuentas | Correo normalizado lower/strip, consulta empresa/operario/proveedor con cuenta. Empresa RUC y proveedor RUC verifican duplicado por aplicación. | app/services/cuenta_service.py:92 |
| RN-04 | Asignación por peso | Carga rack SUM(stock_actual*peso), libre=capacidad-carga. Si carga a ingresar > libre+1e-9 ->409. Asignación inicial exige DISPONIBLE; aumentos por Movimiento no lo exigen. | app/services/rack_service.py:188 |
| RN-05 | Refrigeración | Producto refrigerado exige rango; rack debe tener temperatura y su rango completo dentro del del producto. Racks en zona refrigerada requieren temperaturas; otras zonas no las admiten. | app/services/rack_service.py:230 |
| RN-06 | Nivel rack | nivel<=zona.capacidad (niveles), un rack por nivel y codigo uppercase único en zona; errores409. | app/services/rack_service.py:294 |
| RN-07 | Inventario inicial | Producto/rack existen, min<=max, no repetir pareja, inicial<=max y cabe en rack. Genera historial CREAR. Update solo límites, sin None, min<=max, historial EDITAR_LIMITES si cambia. | app/services/inventario_service.py:36 |
| RN-08 | Borrado inventario | stock_actual>0 ->400; rack/producto bloquean si hay cualquier inventario incluso stock0; no cascade integral. | app/services/inventario_service.py:440 |
| RN-09 | Movimiento | Operario requerido (token si aplica), ACTIVO; ENTRADA suma, SALIDA resta y no supera disponible, AJUSTE reemplaza cantidad>0. Error409 por stock insuficiente/cambio CAS; 400 por motivo incompatible. | app/services/movimiento_service.py:109 |
| RN-10 | Motivo movimiento | ENTRADA: RECEPCION/REPOSICION/DEVOLUCION/CONTEO_FISICO/OTRO. SALIDA: VENTA/MERMA/VENCIMIENTO/CONTEO_FISICO/OTRO. AJUSTE: CONTEO_FISICO/OTRO. | app/services/movimiento_service.py:41 |
| RN-11 | Idempotencia recepción | Si id_detalle_recepcion ya tiene movimiento devuelve existente; índice partial unique string declarado; no prueba instalación. | app/services/movimiento_service.py:117 |
| RN-12 | Orden | Empresa, almacén/proveedor de empresa y proveedor ACTIVO; productos pertenecen empresa; lineas no duplican producto. Nuevo PENDIENTE. Update PENDIENTE/OBSERVADA; validar PENDIENTE/APROBADA con detalles ->ENVIADA; devolver PENDIENTE->OBSERVADA; reenviar OBSERVADA->PENDIENTE; cancelar PENDIENTE/OBSERVADA/APROBADA; eliminar solo PENDIENTE. | app/services/orden_reposicion_service.py:47 |
| RN-13 | Detalle reposición | Solo agregar/editar/eliminar PENDIENTE/OBSERVADA; producto existe y empresa coherente cuando campo presente; no producto repetido por orden. | app/services/detalle_reposicion_service.py:25 |
| RN-14 | Recepción | Orden ENVIADA/PARCIAL del almacén operario ACTIVO; cada detalle pertenece orden; inventario corresponde producto y almacén; si refrigerado exige temperatura_recepcion. Prevalida kg acumulados. | app/services/recepcion_mercaderia_service.py:59 |
| RN-15 | Cantidad recepción | recibida>0, rechazada>=0<=recibida, rechazo/evaluación exige motivo/comentario. EN_EVALUACION aceptada0; resto recibida-rechazada. Acumulada aceptada<=solicitada en crear. Cantidad positiva crea ENTRADA RECEPCION. | app/services/detalle_recepcion_service.py:266 |
| RN-16 | Evaluación | Resolver solo CONFORME/RECHAZADO. aceptada+rechazada=recibida y no negativas; si movimiento previo devuelve existente. Actualiza auditoría resolución, ubicación, riesgo antes/después y notificación. | app/services/detalle_recepcion_service.py:455 |
| RN-17 | Estado orden por recepción | Total aceptado>=solicitado ->RECIBIDA; >0 ->PARCIAL; =0 no cambio. No calcula pendientes por lotes ni FEFO. | app/services/detalle_recepcion_service.py:696 |
| RN-18 | Alertas | Buscar activa por inventario+tipo; actualiza métricas si existe, si no uuid/ACTIVA. Cambio estado enum no tiene grafo restrictivo; RESUELTA fecha_resolucion, otro limpia fecha anterior. | app/services/alerta_service.py:23 |
| RN-19 | Recomendación | Buscar pendiente por inventario+tipo para actualizar; nueva PENDIENTE. Transiciones restringidas en tabla, aprobada solo REABASTECER y cantidad>0 genera orden+detalle y marca APLICADA. | app/services/recomendacion_service.py:411 |
| RN-20 | Riesgo/logística | Fórmulas stock seguridad, cobertura, riesgo, score y reposición tal como especificación forecasting. ALTO/CRITICO producen alertas si generar_alertasTrue; no ejecutan compra física. | app/services/inventory_risk_service.py:498 |
| RN-21 | Correo | Código6 dígitos regex; hash SHA256, TTL10min, cooldown60s, máximo5 intentos por defaults. Caducado/usado/bloqueado no verifica; éxito actualiza correo_verificado y fecha. | app/services/email_verification_service.py:171 |
| RN-22 | Email idempotente | event_id; ENVIADO/OMITIDO no se repiten, ERROR reintentable. Transporte SMTP configurable, defaults disabled; flujos de aprobación exigen verificación; no scheduler de reintentos localizado. | app/services/notification_service.py:27 |
| RN-23 | Saiki | Whitelist ocho tools, Pydantic argumentos, solo EMPRESA, IDs autorizados, history40/user-assistant/content<=8000/sin tool instrucciones; cuatro iteraciones; no escritura operativa. | app/services/saiki_tools.py:131 |

## Enumeraciones exactas

### TipoAlerta

RIESGO_STOCKOUT="RIESGO_STOCKOUT"; STOCK_BAJO="STOCK_BAJO"; SOBRESTOCK="SOBRESTOCK"; CONSUMO_ANOMALO="CONSUMO_ANOMALO"; PROXIMO_VENCIMIENTO="PROXIMO_VENCIMIENTO". Evidencia: app/dto/alerta_dto.py:8. La enumeración no prueba detector, transición ni automatismo.

### NivelRiesgo

BAJO="BAJO"; MEDIO="MEDIO"; ALTO="ALTO"; CRITICO="CRITICO". Evidencia: app/dto/alerta_dto.py:16. La enumeración no prueba detector, transición ni automatismo.

### EstadoAlerta

ACTIVA="ACTIVA"; VISTA="VISTA"; RESUELTA="RESUELTA"; IGNORADA="IGNORADA". Evidencia: app/dto/alerta_dto.py:23. La enumeración no prueba detector, transición ni automatismo.

### EstadoRecepcion

CONFORME="CONFORME"; RECHAZADO="RECHAZADO"; EN_EVALUACION="EN_EVALUACION". Evidencia: app/dto/detalle_recepcion_dto.py:13. La enumeración no prueba detector, transición ni automatismo.

### TipoMovimiento

ENTRADA="ENTRADA"; SALIDA="SALIDA"; AJUSTE="AJUSTE". Evidencia: app/dto/movimiento_dto.py:8. La enumeración no prueba detector, transición ni automatismo.

### MotivoMovimiento

RECEPCION="RECEPCION"; REPOSICION="REPOSICION"; VENTA="VENTA"; MERMA="MERMA"; VENCIMIENTO="VENCIMIENTO"; DEVOLUCION="DEVOLUCION"; CONTEO_FISICO="CONTEO_FISICO"; OTRO="OTRO". Evidencia: app/dto/movimiento_dto.py:14. La enumeración no prueba detector, transición ni automatismo.

### EstadoOrdenReposicion

PENDIENTE="PENDIENTE"; OBSERVADA="OBSERVADA"; APROBADA="APROBADA"; ENVIADA="ENVIADA"; PARCIAL="PARCIAL"; RECIBIDA="RECIBIDA"; CANCELADA="CANCELADA". Evidencia: app/dto/orden_reposicion_dto.py:12. La enumeración no prueba detector, transición ni automatismo.

### OrigenOrden

MANUAL="MANUAL"; RECOMENDACION_IA="RECOMENDACION_IA". Evidencia: app/dto/orden_reposicion_dto.py:24. La enumeración no prueba detector, transición ni automatismo.

### EstadoProveedor

ACTIVO="ACTIVO"; INACTIVO="INACTIVO". Evidencia: app/dto/proveedor_dto.py:8. La enumeración no prueba detector, transición ni automatismo.

### EstadoRack

DISPONIBLE="DISPONIBLE"; LLENO="LLENO"; MANTENIMIENTO="MANTENIMIENTO". Evidencia: app/dto/rack_dto.py:11. La enumeración no prueba detector, transición ni automatismo.

### TipoRecomendacion

REABASTECER="REABASTECER"; NO_REABASTECER="NO_REABASTECER"; REDUCIR_REPOSICION="REDUCIR_REPOSICION"; TRASLADAR_STOCK="TRASLADAR_STOCK"; REVISAR_CONSUMO="REVISAR_CONSUMO"; REVISAR_INVENTARIO="REVISAR_INVENTARIO". Evidencia: app/dto/recomendacion_dto.py:10. La enumeración no prueba detector, transición ni automatismo.

### EstadoRecomendacion

PENDIENTE="PENDIENTE"; VALIDADA_OPERARIO="VALIDADA_OPERARIO"; CAMBIOS_SOLICITADOS="CAMBIOS_SOLICITADOS"; APROBADA_EMPRESA="APROBADA_EMPRESA"; ACEPTADA="ACEPTADA"; RECHAZADA="RECHAZADA"; APLICADA="APLICADA"; EXPIRADA="EXPIRADA". Evidencia: app/dto/recomendacion_dto.py:19. La enumeración no prueba detector, transición ni automatismo.

## Validaciones de contrato por campo

### AlertaCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/alerta_dto.py:32 |
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:33 |
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:34 |
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:35 |
| tipo_alerta | TipoAlerta | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:37 |
| nivel_riesgo | NivelRiesgo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:38 |
| titulo | str | true | false | NO DEFINIDO | {"min_length":3,"max_length":150} | app/dto/alerta_dto.py:40 |
| mensaje | str | true | false | NO DEFINIDO | {"min_length":3,"max_length":1000} | app/dto/alerta_dto.py:45 |
| stock_actual | float | true | false | NO DEFINIDO | {"ge":0} | app/dto/alerta_dto.py:50 |
| dias_cobertura | Optional[float] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/alerta_dto.py:52 |
| stock_seguridad | Optional[float] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/alerta_dto.py:57 |
| punto_reposicion | Optional[float] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/alerta_dto.py:62 |
| forecast_7d | Optional[float] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/alerta_dto.py:67 |

### AlertaResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_alerta | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:74 |
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:76 |
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:77 |
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:78 |
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:79 |
| tipo_alerta | TipoAlerta | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:81 |
| nivel_riesgo | NivelRiesgo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:82 |
| titulo | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:84 |
| mensaje | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:85 |
| stock_actual | float | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:87 |
| dias_cobertura | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/alerta_dto.py:88 |
| stock_seguridad | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/alerta_dto.py:89 |
| punto_reposicion | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/alerta_dto.py:90 |
| forecast_7d | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/alerta_dto.py:91 |
| estado | EstadoAlerta | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:93 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:95 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:96 |
| fecha_resolucion | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/alerta_dto.py:97 |

### AlertaEstadoUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| estado | EstadoAlerta | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/alerta_dto.py:101 |

### AlmacenCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/almacen_dto.py:19 |
| nombre | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/almacen_dto.py:21 |
| longitud | Decimal | true | false | NO DEFINIDO | {"ge":{"expression":"Decimal(\"-180.000000\")"},"le":{"expression":"Decimal(\"180.000000\")"},"max_digits":9,"decimal_places":6} | app/dto/almacen_dto.py:27 |
| latitud | Decimal | true | false | NO DEFINIDO | {"ge":{"expression":"Decimal(\"-90.000000\")"},"le":{"expression":"Decimal(\"90.000000\")"},"max_digits":8,"decimal_places":6} | app/dto/almacen_dto.py:35 |
| area_m2 | float | true | false | NO DEFINIDO | {"gt":0} | app/dto/almacen_dto.py:43 |
| aforo | int | true | false | NO DEFINIDO | {"ge":0} | app/dto/almacen_dto.py:48 |
| tipo_almacen | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/almacen_dto.py:53 |

### AlmacenUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| nombre | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":100} | app/dto/almacen_dto.py:66 |
| longitud | Optional[Decimal] | false | true | NO DEFINIDA | {"default":null,"ge":{"expression":"Decimal(\"-180.000000\")"},"le":{"expression":"Decimal(\"180.000000\")"},"max_digits":9,"decimal_places":6} | app/dto/almacen_dto.py:72 |
| latitud | Optional[Decimal] | false | true | NO DEFINIDA | {"default":null,"ge":{"expression":"Decimal(\"-90.000000\")"},"le":{"expression":"Decimal(\"90.000000\")"},"max_digits":8,"decimal_places":6} | app/dto/almacen_dto.py:80 |
| area_m2 | Optional[float] | false | true | NO DEFINIDA | {"default":null,"gt":0} | app/dto/almacen_dto.py:88 |
| aforo | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/almacen_dto.py:93 |
| tipo_almacen | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":100} | app/dto/almacen_dto.py:98 |

### AlmacenResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id | str | true | false | NO DEFINIDO | {"validation_alias":{"expression":"AliasChoices( \"id\", \"id_almacen\" )"}} | app/dto/almacen_dto.py:119 |
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/almacen_dto.py:126 |
| nombre | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/almacen_dto.py:128 |
| longitud | Decimal | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/almacen_dto.py:130 |
| latitud | Decimal | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/almacen_dto.py:132 |
| area_m2 | float | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/almacen_dto.py:134 |
| aforo | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/almacen_dto.py:136 |
| tipo_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/almacen_dto.py:138 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/almacen_dto.py:140 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/almacen_dto.py:142 |

### LoginRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| correo | EmailStr | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/auth_dto.py:33 |
| password | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/auth_dto.py:35 |

### LoginResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| access_token | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/auth_dto.py:44 |
| token_type | str | false | false | bearer | NO DEFINIDAS | app/dto/auth_dto.py:46 |
| rol | Literal[ "EMPRESA", "OPERARIO", "PROVEEDOR" ] | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/auth_dto.py:48 |
| empresa | EmpresaResponse | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/auth_dto.py:56 |
| operario | Optional[ OperarioResponse ] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/auth_dto.py:58 |
| proveedor | Optional[ ProveedorResponse ] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/auth_dto.py:62 |
| debe_cambiar_password | bool | false | false | false | NO DEFINIDAS | app/dto/auth_dto.py:66 |

### MeResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| rol | Literal[ "EMPRESA", "OPERARIO", "PROVEEDOR" ] | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/auth_dto.py:75 |
| empresa | EmpresaResponse | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/auth_dto.py:81 |
| operario | Optional[ OperarioResponse ] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/auth_dto.py:83 |
| proveedor | Optional[ ProveedorResponse ] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/auth_dto.py:87 |
| debe_cambiar_password | bool | false | false | false | NO DEFINIDAS | app/dto/auth_dto.py:91 |

### CambiarPasswordRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| password_actual | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/auth_dto.py:100 |
| password_nueva | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/auth_dto.py:106 |

### ResetPasswordRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| password_temporal | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/auth_dto.py:122 |
| correo | Optional[EmailStr] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/auth_dto.py:129 |

### UsuarioActual

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| rol | Literal[ "EMPRESA", "OPERARIO", "PROVEEDOR" ] | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/auth_dto.py:140 |
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/auth_dto.py:146 |
| id_operario | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/auth_dto.py:148 |
| id_almacen | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/auth_dto.py:150 |
| id_proveedor | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/auth_dto.py:152 |
| debe_cambiar_password | bool | false | false | false | NO DEFINIDAS | app/dto/auth_dto.py:154 |

### DetalleRecepcionCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_detalle_reposicion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:20 |
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:21 |
| cantidad_recibida | int | true | false | NO DEFINIDO | {"gt":0} | app/dto/detalle_recepcion_dto.py:23 |
| cantidad_rechazada | int | false | false | 0 | {"default":0,"ge":0} | app/dto/detalle_recepcion_dto.py:28 |
| lote | str | false | false | SIN_LOTE | {"default":"SIN_LOTE","min_length":1,"max_length":100} | app/dto/detalle_recepcion_dto.py:33 |
| fecha_vencimiento | datetime &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:39 |
| temperatura_recepcion | float &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:41 |
| estado_recepcion | EstadoRecepcion | false | false | {"expression":"( EstadoRecepcion.CONFORME )"} | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:43 |
| comentario_recepcion | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":1000} | app/dto/detalle_recepcion_dto.py:47 |
| motivo_rechazo | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":500} | app/dto/detalle_recepcion_dto.py:52 |

### DetalleRecepcionResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_detalle_recepcion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:102 |
| id_recepcion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:103 |
| id_detalle_reposicion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:104 |
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:105 |
| cantidad_recibida | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:107 |
| cantidad_rechazada | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:108 |
| cantidad_aceptada | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:109 |
| lote | str | false | false | SIN_LOTE | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:111 |
| fecha_vencimiento | datetime &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:112 |
| temperatura_recepcion | float &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:113 |
| estado_recepcion | EstadoRecepcion | false | false | {"expression":"( EstadoRecepcion.CONFORME )"} | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:114 |
| comentario_recepcion | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:117 |
| motivo_rechazo | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:119 |
| id_movimiento | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:121 |
| ubicado | bool | false | false | true | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:123 |
| riesgo_antes | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:125 |
| riesgo_despues | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:126 |
| notificacion_final | Optional[dict] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:127 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_recepcion_dto.py:129 |

### DetalleReposicionCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_reposicion_dto.py:8 |
| cantidad_solicitada | int | true | false | NO DEFINIDO | {"gt":0} | app/dto/detalle_reposicion_dto.py:10 |
| costo_unitario | Optional[float] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/detalle_reposicion_dto.py:15 |

### DetalleReposicionUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| cantidad_solicitada | Optional[int] | false | true | NO DEFINIDA | {"default":null,"gt":0} | app/dto/detalle_reposicion_dto.py:22 |
| costo_unitario | Optional[float] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/detalle_reposicion_dto.py:27 |

### DetalleReposicionResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_detalle_reposicion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_reposicion_dto.py:34 |
| id_orden_reposicion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_reposicion_dto.py:35 |
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_reposicion_dto.py:36 |
| cantidad_solicitada | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_reposicion_dto.py:38 |
| costo_unitario | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/detalle_reposicion_dto.py:39 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_reposicion_dto.py:41 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/detalle_reposicion_dto.py:42 |

### EmailVerificationCodeRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| codigo | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":6,"pattern":{"expression":"r\"^\\d{6}$\""}} | app/dto/email_verification_dto.py:5 |

### EmailVerificationSendResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| status | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/email_verification_dto.py:14 |
| email | str &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/email_verification_dto.py:15 |
| remaining_seconds | int &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/email_verification_dto.py:16 |
| reason | str &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/email_verification_dto.py:17 |

### EmailVerificationResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| verified | bool | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/email_verification_dto.py:21 |
| status | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/email_verification_dto.py:22 |
| email | str &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/email_verification_dto.py:23 |
| attempts | int &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/email_verification_dto.py:24 |
| remaining_attempts | int &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/email_verification_dto.py:25 |

### EmpresaRegisterRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| nombre | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/empresa_dto.py:16 |
| ruc | str | true | false | NO DEFINIDO | {"min_length":8,"max_length":20} | app/dto/empresa_dto.py:22 |
| sector | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/empresa_dto.py:28 |
| correo | EmailStr | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:34 |
| telefono | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":20} | app/dto/empresa_dto.py:36 |
| password | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/empresa_dto.py:42 |

### EmpresaLoginRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| correo | EmailStr | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:55 |
| password | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/empresa_dto.py:57 |

### EmpresaUpdateRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| nombre | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":100} | app/dto/empresa_dto.py:70 |
| ruc | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":8,"max_length":20} | app/dto/empresa_dto.py:76 |
| sector | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":100} | app/dto/empresa_dto.py:82 |
| correo | Optional[EmailStr] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/empresa_dto.py:88 |
| telefono | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":6,"max_length":20} | app/dto/empresa_dto.py:90 |

### EmpresaChangePasswordRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| password_actual | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/empresa_dto.py:103 |
| password_nueva | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/empresa_dto.py:109 |

### EmpresaDeleteRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| password | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/empresa_dto.py:124 |

### EmpresaResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:137 |
| nombre | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:139 |
| ruc | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:141 |
| sector | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:143 |
| correo | EmailStr | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:145 |
| telefono | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:147 |
| correo_verificado | bool | false | false | false | NO DEFINIDAS | app/dto/empresa_dto.py:149 |
| fecha_verificacion_correo | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/empresa_dto.py:151 |
| fecha_creacion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:153 |
| fecha_actualizacion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:155 |

### EmpresaLoginResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| access_token | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:164 |
| token_type | str | false | false | bearer | NO DEFINIDAS | app/dto/empresa_dto.py:166 |
| empresa | EmpresaResponse | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:168 |

### MessageResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| mensaje | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/empresa_dto.py:177 |

### InventarioCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:17 |
| id_rack | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:19 |
| stock_actual | int | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventario_dto.py:21 |
| stock_minimo | int | false | false | 0 | {"default":0,"ge":0} | app/dto/inventario_dto.py:26 |
| stock_maximo | int | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventario_dto.py:31 |

### InventarioUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| stock_minimo | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/inventario_dto.py:58 |
| stock_maximo | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/inventario_dto.py:63 |

### InventarioResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:75 |
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:77 |
| id_rack | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:79 |
| stock_actual | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:81 |
| stock_minimo | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:83 |
| stock_maximo | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:85 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:87 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:89 |

### InventarioHistorialResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| fecha | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:100 |
| id_operario | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/inventario_dto.py:102 |
| operario_nombre | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/inventario_dto.py:104 |
| accion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventario_dto.py:107 |
| antes | Optional[dict] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/inventario_dto.py:109 |
| despues | Optional[dict] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/inventario_dto.py:111 |

### ConsumoInfo

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| promedio_7d | float | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:12 |
| promedio_14d | float | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:16 |
| promedio_28d | float | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:20 |
| tendencia_porcentaje | float | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:24 |

### CoberturaInfo

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| dias | Optional[float] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/inventory_risk_dto.py:28 |

### ForecastDiario

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| fecha | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:35 |
| demanda_predicha | float | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:37 |

### ForecastInfo

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| demanda_7d | Optional[float] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/inventory_risk_dto.py:43 |
| fecha_quiebre_estimada | Optional[ datetime ] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/inventory_risk_dto.py:48 |
| predicciones_diarias | list[ ForecastDiario ] | false | false | {"factory":{"expression":"list"}} | {"default_factory":{"expression":"list"}} | app/dto/inventory_risk_dto.py:52 |

### SeguridadInfo

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| stock_seguridad | float | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:60 |
| punto_reposicion | float | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:64 |

### RiesgoInfo

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| nivel | NivelRiesgo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:70 |
| score | float | true | false | NO DEFINIDO | {"ge":0,"le":100} | app/dto/inventory_risk_dto.py:72 |

### ReposicionInfo

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| cantidad_minima | int | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:79 |
| cantidad_recomendada | int | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:83 |
| cantidad_segura | int | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:87 |

### InventoryRiskResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:93 |
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:94 |
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:95 |
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:96 |
| stock_actual | float | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:98 |
| consumo | ConsumoInfo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:102 |
| cobertura | CoberturaInfo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:104 |
| lead_time_dias | int | true | false | NO DEFINIDO | {"ge":0} | app/dto/inventory_risk_dto.py:106 |
| forecast | ForecastInfo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:110 |
| seguridad | SeguridadInfo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:112 |
| riesgo | RiesgoInfo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/inventory_risk_dto.py:114 |
| reposicion | Optional[ ReposicionInfo ] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/inventory_risk_dto.py:116 |
| explicacion | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/inventory_risk_dto.py:120 |

### MovimientoCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:26 |
| id_operario | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/movimiento_dto.py:29 |
| id_detalle_recepcion | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/movimiento_dto.py:32 |
| tipo_movimiento | TipoMovimiento | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:34 |
| motivo_movimiento | MotivoMovimiento | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:35 |
| cantidad | int | true | false | NO DEFINIDO | {"gt":0} | app/dto/movimiento_dto.py:37 |
| observacion | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":500} | app/dto/movimiento_dto.py:39 |

### MovimientoResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_movimiento | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:46 |
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:48 |
| id_detalle_recepcion | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/movimiento_dto.py:49 |
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:50 |
| id_rack | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:51 |
| id_operario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:52 |
| operario_nombre | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/movimiento_dto.py:55 |
| id_zona | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/movimiento_dto.py:56 |
| tipo_movimiento | TipoMovimiento | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:58 |
| motivo_movimiento | MotivoMovimiento | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:59 |
| cantidad | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:61 |
| stock_anterior | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:63 |
| stock_nuevo | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:64 |
| observacion | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/movimiento_dto.py:66 |
| fecha_hora | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/movimiento_dto.py:68 |

### OperarioCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/operario_dto.py:20 |
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:22 |
| nombre | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/operario_dto.py:24 |
| apellido | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/operario_dto.py:30 |
| correo | EmailStr | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:36 |
| cargo | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/operario_dto.py:38 |
| turno | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":50} | app/dto/operario_dto.py:44 |
| estado | str | false | false | ACTIVO | {"default":"ACTIVO","min_length":2,"max_length":50} | app/dto/operario_dto.py:50 |
| correo | EmailStr | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:56 |
| password_temporal | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/operario_dto.py:58 |

### OperarioUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_almacen | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/operario_dto.py:71 |
| correo | Optional[EmailStr] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/operario_dto.py:73 |
| nombre | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":100} | app/dto/operario_dto.py:75 |
| apellido | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":100} | app/dto/operario_dto.py:81 |
| correo | Optional[EmailStr] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/operario_dto.py:87 |
| cargo | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":100} | app/dto/operario_dto.py:89 |
| turno | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":50} | app/dto/operario_dto.py:95 |
| estado | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":50} | app/dto/operario_dto.py:101 |

### OperarioResetPassword

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| password_temporal | str | true | false | NO DEFINIDO | {"min_length":6,"max_length":128} | app/dto/operario_dto.py:116 |
| correo | Optional[EmailStr] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/operario_dto.py:124 |

### OperarioResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_operario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:137 |
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:138 |
| nombre | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:140 |
| apellido | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:141 |
| cargo | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:142 |
| turno | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:143 |
| estado | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:144 |
| id_almacen | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/operario_dto.py:146 |
| correo_verificado | bool | false | false | false | NO DEFINIDAS | app/dto/operario_dto.py:147 |
| fecha_verificacion_correo | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/operario_dto.py:148 |
| correo | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/operario_dto.py:150 |
| tiene_cuenta | bool | false | false | false | NO DEFINIDAS | app/dto/operario_dto.py:152 |
| debe_cambiar_password | bool | false | false | false | NO DEFINIDAS | app/dto/operario_dto.py:154 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:156 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/operario_dto.py:157 |

### OrdenReposicionCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_recomendacion | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:30 |
| id_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:32 |
| id_almacen | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:34 |
| id_proveedor | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:35 |
| lineas | list[DetalleReposicionCreate] | false | false | [] | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:39 |
| fecha_estimada_recepcion | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:41 |
| origen | OrigenOrden | false | false | {"expression":"OrigenOrden.MANUAL"} | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:43 |
| observacion | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":500} | app/dto/orden_reposicion_dto.py:45 |

### OrdenReposicionUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_proveedor | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:52 |
| fecha_estimada_recepcion | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:53 |
| observacion | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":500} | app/dto/orden_reposicion_dto.py:54 |

### OrdenReposicionResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_orden_reposicion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:61 |
| id_recomendacion | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:62 |
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:64 |
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:65 |
| id_proveedor | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:66 |
| origen | OrigenOrden | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:68 |
| estado | EstadoOrdenReposicion | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:69 |
| fecha_orden | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:71 |
| fecha_estimada_recepcion | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:72 |
| observacion | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:74 |
| id_operario_solicitante | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:77 |
| comentario_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:78 |
| despacho | Optional[dict] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:81 |
| fecha_despacho | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:82 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:84 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:85 |

### DevolverOrdenRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| comentario | str | true | false | NO DEFINIDO | {"min_length":1,"max_length":1000} | app/dto/orden_reposicion_dto.py:95 |

### LineaDespacho

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_detalle_reposicion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:109 |
| cantidad | int | true | false | NO DEFINIDO | {"gt":0} | app/dto/orden_reposicion_dto.py:111 |
| fecha_vencimiento | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:116 |
| temperatura | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/orden_reposicion_dto.py:118 |

### DespachoRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| lineas | list[LineaDespacho] | true | false | NO DEFINIDO | {"min_length":1} | app/dto/orden_reposicion_dto.py:122 |
| observacion | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":500} | app/dto/orden_reposicion_dto.py:126 |

### ProductoCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:14 |
| id_proveedor | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:17 |
| id_rack | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:21 |
| nombre | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":150} | app/dto/producto_dto.py:23 |
| categoria | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/producto_dto.py:29 |
| familia | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/producto_dto.py:35 |
| marca | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:41 |
| peso | float | true | false | NO DEFINIDO | {"gt":0} | app/dto/producto_dto.py:44 |
| volumen | Optional[float] | false | true | NO DEFINIDA | {"default":null,"gt":0} | app/dto/producto_dto.py:49 |
| stock | int | false | false | 0 | {"default":0,"ge":0} | app/dto/producto_dto.py:54 |
| requiere_refrigeracion | bool | false | false | false | NO DEFINIDAS | app/dto/producto_dto.py:59 |
| temperatura_min_almacenamiento | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:61 |
| temperatura_max_almacenamiento | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:62 |
| lead_time_dias | int | true | false | NO DEFINIDO | {"ge":0} | app/dto/producto_dto.py:64 |
| vida_util_dias | int | true | false | NO DEFINIDO | {"ge":1} | app/dto/producto_dto.py:69 |

### ProductoUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_rack | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:106 |
| nombre | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:108 |
| categoria | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:109 |
| familia | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:110 |
| marca | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:111 |
| peso | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:113 |
| volumen | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:114 |
| stock | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/producto_dto.py:116 |
| requiere_refrigeracion | Optional[bool] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:121 |
| temperatura_min_almacenamiento | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:123 |
| temperatura_max_almacenamiento | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:124 |
| lead_time_dias | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/producto_dto.py:126 |
| vida_util_dias | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":1} | app/dto/producto_dto.py:131 |

### ProductoResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/producto_dto.py:139 |
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/producto_dto.py:141 |
| id_proveedor | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:144 |
| id_rack | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:147 |
| nombre | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/producto_dto.py:149 |
| categoria | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/producto_dto.py:151 |
| familia | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/producto_dto.py:153 |
| marca | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:155 |
| peso | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:157 |
| volumen | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:159 |
| stock | int | false | false | 0 | NO DEFINIDAS | app/dto/producto_dto.py:162 |
| requiere_refrigeracion | bool | false | false | false | NO DEFINIDAS | app/dto/producto_dto.py:164 |
| temperatura_min_almacenamiento | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:166 |
| temperatura_max_almacenamiento | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/producto_dto.py:168 |
| lead_time_dias | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/producto_dto.py:170 |
| vida_util_dias | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/producto_dto.py:172 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/producto_dto.py:174 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/producto_dto.py:176 |

### ProveedorCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/proveedor_dto.py:15 |
| nombre | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":150} | app/dto/proveedor_dto.py:17 |
| ruc | str | true | false | NO DEFINIDO | {"min_length":11,"max_length":11} | app/dto/proveedor_dto.py:23 |
| correo | Optional[EmailStr] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/proveedor_dto.py:29 |
| telefono | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":20} | app/dto/proveedor_dto.py:31 |
| direccion | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":250} | app/dto/proveedor_dto.py:36 |
| tiempo_entrega_estimado_dias | int | false | false | 1 | {"default":1,"ge":0} | app/dto/proveedor_dto.py:41 |
| estado | EstadoProveedor | false | false | {"expression":"EstadoProveedor.ACTIVO"} | NO DEFINIDAS | app/dto/proveedor_dto.py:46 |
| password_temporal | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":6,"max_length":128} | app/dto/proveedor_dto.py:50 |

### ProveedorUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| nombre | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":150} | app/dto/proveedor_dto.py:58 |
| correo | Optional[EmailStr] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/proveedor_dto.py:64 |
| telefono | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":20} | app/dto/proveedor_dto.py:66 |
| direccion | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":250} | app/dto/proveedor_dto.py:71 |
| tiempo_entrega_estimado_dias | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/proveedor_dto.py:76 |
| estado | Optional[EstadoProveedor] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/proveedor_dto.py:81 |

### ProveedorResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_proveedor | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/proveedor_dto.py:85 |
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/proveedor_dto.py:86 |
| nombre | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/proveedor_dto.py:88 |
| ruc | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/proveedor_dto.py:89 |
| correo | Optional[EmailStr] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/proveedor_dto.py:91 |
| tiene_cuenta | bool | false | false | false | NO DEFINIDAS | app/dto/proveedor_dto.py:92 |
| debe_cambiar_password | bool | false | false | false | NO DEFINIDAS | app/dto/proveedor_dto.py:93 |
| correo_verificado | bool | false | false | false | NO DEFINIDAS | app/dto/proveedor_dto.py:94 |
| fecha_verificacion_correo | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/proveedor_dto.py:95 |
| telefono | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/proveedor_dto.py:96 |
| direccion | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/proveedor_dto.py:97 |
| tiempo_entrega_estimado_dias | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/proveedor_dto.py:99 |
| estado | EstadoProveedor | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/proveedor_dto.py:101 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/proveedor_dto.py:103 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/proveedor_dto.py:104 |

### RackCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_zona | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:43 |
| codigo | str | true | false | NO DEFINIDO | {"min_length":1,"max_length":50} | app/dto/rack_dto.py:45 |
| nivel | int | true | false | NO DEFINIDO | {"ge":1} | app/dto/rack_dto.py:50 |
| capacidad | float | true | false | NO DEFINIDO | {"gt":0} | app/dto/rack_dto.py:54 |
| temperatura_min | float &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/rack_dto.py:58 |
| temperatura_max | float &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/rack_dto.py:60 |
| estado | EstadoRack | false | false | {"expression":"EstadoRack.DISPONIBLE"} | NO DEFINIDAS | app/dto/rack_dto.py:62 |

### RackUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| estado | EstadoRack &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/rack_dto.py:77 |
| temperatura_min | float &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/rack_dto.py:79 |
| temperatura_max | float &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/rack_dto.py:81 |

### RackResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_rack | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:89 |
| id_zona | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:90 |
| codigo | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:92 |
| nivel | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:94 |
| capacidad | float | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:97 |
| estado | EstadoRack | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:99 |
| temperatura_min | float &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/rack_dto.py:102 |
| temperatura_max | float &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/rack_dto.py:104 |
| carga_kg | float | false | false | 0 | NO DEFINIDAS | app/dto/rack_dto.py:107 |
| libre_kg | float | false | false | 0 | NO DEFINIDAS | app/dto/rack_dto.py:110 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:112 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:114 |

### RackDisponibleResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/rack_dto.py:125 |
| nombre_zona | str &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/rack_dto.py:127 |

### RecepcionMercaderiaCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_orden_reposicion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:13 |
| id_operario | str &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:17 |
| fecha_recepcion | datetime &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:19 |
| observaciones_generales | str &#124; None | false | true | NO DEFINIDA | {"default":null,"max_length":1000} | app/dto/recepcion_mercaderia_dto.py:21 |
| detalles | list[ DetalleRecepcionCreate ] | true | false | NO DEFINIDO | {"min_length":1} | app/dto/recepcion_mercaderia_dto.py:26 |

### RecepcionMercaderiaResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_recepcion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:33 |
| id_orden_reposicion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:35 |
| id_operario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:37 |
| fecha_recepcion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:39 |
| observaciones_generales | str &#124; None | true | true | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:41 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:43 |
| detalles | list[ DetalleRecepcionResponse ] | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:45 |

### UbicarDetalleRecepcion

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_rack | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:52 |

### ResolverEvaluacion

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_operario | str &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:59 |
| estado_recepcion | EstadoRecepcion | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:61 |
| comentario_resolucion | str | true | false | NO DEFINIDO | {"min_length":1,"max_length":1000} | app/dto/recepcion_mercaderia_dto.py:63 |
| cantidad_aceptada | int &#124; None | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/recepcion_mercaderia_dto.py:68 |
| cantidad_rechazada | int &#124; None | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/recepcion_mercaderia_dto.py:73 |
| id_inventario | str &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recepcion_mercaderia_dto.py:78 |

### RecomendacionCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:32 |
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:33 |
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:34 |
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:35 |
| id_alerta | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:37 |
| tipo_recomendacion | ( TipoRecomendacion ) | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:39 |
| nivel_riesgo | NivelRiesgo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:43 |
| cantidad_minima | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/recomendacion_dto.py:45 |
| cantidad_recomendada | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/recomendacion_dto.py:50 |
| cantidad_segura | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/recomendacion_dto.py:55 |
| forecast_7d | Optional[float] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/recomendacion_dto.py:60 |
| explicacion | str | true | false | NO DEFINIDO | {"min_length":3,"max_length":3000} | app/dto/recomendacion_dto.py:65 |
| origen | str | false | false | PSITWIN | {"default":"PSITWIN","min_length":2,"max_length":100} | app/dto/recomendacion_dto.py:70 |

### RecomendacionResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_recomendacion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:78 |
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:80 |
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:81 |
| id_inventario | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:82 |
| id_producto | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:83 |
| id_alerta | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:85 |
| tipo_recomendacion | ( TipoRecomendacion ) | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:87 |
| nivel_riesgo | NivelRiesgo | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:91 |
| cantidad_minima | Optional[int] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:93 |
| cantidad_recomendada | Optional[int] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:94 |
| cantidad_segura | Optional[int] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:95 |
| forecast_7d | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:96 |
| explicacion | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:98 |
| origen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:99 |
| estado | EstadoRecomendacion | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:101 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:103 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:104 |
| fecha_aplicacion | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:105 |
| notificacion_aprobacion | Optional[dict] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:107 |

### RecomendacionEstadoUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| estado | EstadoRecomendacion | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:113 |

### EmpresaCambiosRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:118 |
| comentario | str | true | false | NO DEFINIDO | {"min_length":1,"max_length":1000} | app/dto/recomendacion_dto.py:119 |

### EmpresaAprobacionRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_empresa | Optional[str] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:128 |
| id_proveedor | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/recomendacion_dto.py:129 |
| costo_unitario | float | true | false | NO DEFINIDO | {"ge":0} | app/dto/recomendacion_dto.py:130 |
| fecha_estimada_recepcion | Optional[datetime] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/recomendacion_dto.py:131 |
| observacion | Optional[str] | false | true | NO DEFINIDA | {"default":null,"max_length":500} | app/dto/recomendacion_dto.py:132 |

### PropuestaRecomendacionUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| cantidad_recomendada | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":1} | app/dto/recomendacion_dto.py:136 |
| explicacion | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":3,"max_length":3000} | app/dto/recomendacion_dto.py:137 |

### SaikiAskRequest

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| message | str &#124; None | false | true | NO DEFINIDA | {"default":null,"min_length":1} | app/dto/saiki_dto.py:21 |
| question | str &#124; None | false | true | NO DEFINIDA | {"default":null,"min_length":1,"description":"Alias legacy de message. No es necesario para nuevas consultas."} | app/dto/saiki_dto.py:22 |
| id_inventario | str &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/saiki_dto.py:27 |
| id_producto | str &#124; None | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/saiki_dto.py:28 |
| page | int | false | false | 1 | {"default":1,"ge":1,"description":"Página del detalle de inventario."} | app/dto/saiki_dto.py:29 |
| page_size | int | false | false | 25 | {"default":25,"ge":1,"le":100} | app/dto/saiki_dto.py:30 |
| context | dict[str, Any] | false | false | {"factory":{"expression":"dict"}} | {"default_factory":{"expression":"dict"},"description":"Contexto técnico opcional; normalmente debe omitirse."} | app/dto/saiki_dto.py:31 |
| history | list[dict[str, Any]] | false | false | {"factory":{"expression":"list"}} | {"default_factory":{"expression":"list"},"description":"Historial opcional de mensajes previos."} | app/dto/saiki_dto.py:35 |

### SaikiAskResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| answer | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/saiki_dto.py:63 |
| model | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/saiki_dto.py:64 |
| base_url | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/saiki_dto.py:65 |
| source | str | false | false | ollama | NO DEFINIDAS | app/dto/saiki_dto.py:66 |
| context | dict[str, Any] | false | false | {"factory":{"expression":"dict"}} | {"default_factory":{"expression":"dict"}} | app/dto/saiki_dto.py:67 |
| warnings | list[str] | false | false | {"factory":{"expression":"list"}} | {"default_factory":{"expression":"list"}} | app/dto/saiki_dto.py:68 |
| data | dict[str, Any] | false | false | {"factory":{"expression":"dict"}} | {"default_factory":{"expression":"dict"}} | app/dto/saiki_dto.py:69 |
| visualization | dict[str, Any] | false | false | {"factory":{"expression":"lambda: {\"type\": \"none\"}"}} | {"default_factory":{"expression":"lambda: {\"type\": \"none\"}"}} | app/dto/saiki_dto.py:70 |
| sources | list[str] | false | false | {"factory":{"expression":"list"}} | {"default_factory":{"expression":"list"}} | app/dto/saiki_dto.py:73 |

### ZonaCreate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/zona_dto.py:17 |
| nombre | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/zona_dto.py:19 |
| tipo_zona | str | true | false | NO DEFINIDO | {"min_length":2,"max_length":100} | app/dto/zona_dto.py:25 |
| refrigerada | bool | false | false | false | NO DEFINIDAS | app/dto/zona_dto.py:33 |
| temperatura_min | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/zona_dto.py:35 |
| temperatura_max | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/zona_dto.py:37 |
| capacidad | int | true | false | NO DEFINIDO | {"ge":0} | app/dto/zona_dto.py:40 |

### ZonaUpdate

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| nombre | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":100} | app/dto/zona_dto.py:52 |
| tipo_zona | Optional[str] | false | true | NO DEFINIDA | {"default":null,"min_length":2,"max_length":100} | app/dto/zona_dto.py:58 |
| refrigerada | Optional[bool] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/zona_dto.py:64 |
| temperatura_min | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/zona_dto.py:66 |
| temperatura_max | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/zona_dto.py:68 |
| capacidad | Optional[int] | false | true | NO DEFINIDA | {"default":null,"ge":0} | app/dto/zona_dto.py:70 |

### ZonaResponse

| Variable | Tipo | Obligatorio | Nullable | Default | Restricciones literales | Línea |
|---|---|---|---|---|---|---|
| id | str | true | false | NO DEFINIDO | {"validation_alias":{"expression":"AliasChoices( \"id\", \"id_zona\" )"}} | app/dto/zona_dto.py:91 |
| id_almacen | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/zona_dto.py:98 |
| id_empresa | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/zona_dto.py:100 |
| nombre | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/zona_dto.py:102 |
| tipo_zona | str | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/zona_dto.py:104 |
| refrigerada | bool | false | false | false | NO DEFINIDAS | app/dto/zona_dto.py:107 |
| temperatura_min | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/zona_dto.py:109 |
| temperatura_max | Optional[float] | false | true | NO DEFINIDA | NO DEFINIDAS | app/dto/zona_dto.py:111 |
| capacidad | int | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/zona_dto.py:113 |
| fecha_creacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/zona_dto.py:115 |
| fecha_actualizacion | datetime | true | false | NO DEFINIDO | NO DEFINIDAS | app/dto/zona_dto.py:117 |

## Registro exhaustivo de condiciones del código ejecutable

Incluye tanto reglas de dominio como ramificaciones técnicas de validación, seguridad, serialización y persistencia. No se afirma que cada if sea una regla de negocio independiente. Las condiciones y acciones conservan nombres/fórmulas/errores exactos; HTTPException.status_code y detail quedan visibles. Cada entrada muestra clase, función y línea. La totalidad de funciones auxiliares llamadas está reproducida en documento maestro/JSON.

### COND-0001: módulo._verificar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/alerta_controller.py:46. Condición: `if item.get("id_empresa") != user.id_empresa:`.

```python
    if item.get("id_empresa") != user.id_empresa:
        raise HTTPException(
            status_code=404,
            detail="Alerta no encontrada"
        )

```

### COND-0002: módulo._almacenes_visibles

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/almacen_controller.py:52. Condición: `if user.es_operario:`.

```python
    if user.es_operario:

        if not user.id_almacen:
            return []

        return [
            await AccesoService.verificar_almacen(
                user,
                user.id_almacen
            )
        ]

```

### COND-0003: módulo._almacenes_visibles

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/almacen_controller.py:54. Condición: `if not user.id_almacen:`.

```python
        if not user.id_almacen:
            return []

```

### COND-0004: módulo.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/detalle_recepcion_controller.py:130. Condición: `if data.id_inventario:`.

```python
    if data.id_inventario:

        await AccesoService.verificar_inventario(
            user,
            data.id_inventario
        )

```

### COND-0005: módulo._json_safe_value

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/forecast_controller.py:59. Condición: `if pd.isna(value):`.

```python
        if pd.isna(value):
            return None

```

### COND-0006: módulo._json_safe_value

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/forecast_controller.py:69. Condición: `if hasattr( value, "item" ):`.

```python
    if hasattr(
        value,
        "item"
    ):

        try:
            return value.item()

        except Exception:
            pass

```

### COND-0007: módulo._crear_history_dataframe

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/forecast_controller.py:151. Condición: `if not historial:`.

```python
    if not historial:

        raise ValueError(
            "No existe historial de demanda "
            "para el inventario indicado."
        )

```

### COND-0008: módulo._crear_history_dataframe

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/forecast_controller.py:162. Condición: `if history_df.empty:`.

```python
    if history_df.empty:

        raise ValueError(
            "El historial de demanda está vacío."
        )

```

### COND-0009: módulo._crear_history_dataframe

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/forecast_controller.py:182. Condición: `if missing_columns:`.

```python
    if missing_columns:

        raise ValueError(
            "DemandHistory no devolvió "
            "las columnas necesarias: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

```

### COND-0010: módulo._obtener_fecha_base

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/forecast_controller.py:222. Condición: `if pd.isna( fecha_base ):`.

```python
    if pd.isna(
        fecha_base
    ):

        raise ValueError(
            "No se pudo determinar "
            "la fecha base."
        )

```

### COND-0011: módulo.debug_predict

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/forecast_controller.py:753. Condición: `if missing_features:`.

```python
        if missing_features:

            raise ValueError(
                "Faltan features requeridas "
                "por LightGBM: "
                + ", ".join(
                    missing_features
                )
            )

```

### COND-0012: módulo.predict_7_days

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/forecast_controller.py:1024. Condición: `if missing_features:`.

```python
            if missing_features:

                raise ValueError(
                    f"D+{horizon}: faltan "
                    "features requeridas por "
                    "LightGBM: "
                    + ", ".join(
                        missing_features
                    )
                )

```

### COND-0013: módulo.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/movimiento_controller.py:86. Condición: `if ( data.tipo_movimiento != TipoMovimiento.SALIDA or data.motivo_movimiento not in ( MotivoMovimiento.VENTA, MotivoMovimiento.VENCIMIENTO ) ):`.

```python
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

```

### COND-0014: módulo._alcance

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/orden_reposicion_controller.py:66. Condición: `if user.es_operario:`.

```python
    if user.es_operario:

        ordenes = [
            orden
            for orden in ordenes
            if orden.get("id_almacen")
            == user.id_almacen
        ]

```

### COND-0015: módulo.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/orden_reposicion_controller.py:93. Condición: `if not user.id_almacen:`.

```python
    if not user.id_almacen:
        raise HTTPException(
            status_code=409,
            detail="El operario no tiene almacén asignado"
        )

```

### COND-0016: módulo._visibles

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/producto_controller.py:59. Condición: `if user.es_proveedor:`.

```python
    if user.es_proveedor:

        productos = [
            producto
            for producto in productos
            if producto.get("id_proveedor")
            == user.id_proveedor
        ]

```

### COND-0017: módulo.actualizar_producto

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/producto_controller.py:327. Condición: `if user.es_operario:`.

```python
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

```

### COND-0018: módulo.actualizar_producto

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/producto_controller.py:329. Condición: `if data.model_fields_set - {"id_rack"}:`.

```python
        if data.model_fields_set - {"id_rack"}:

            raise HTTPException(
                status_code=403,
                detail=(
                    "El operario solo puede cambiar "
                    "el rack de referencia (id_rack)"
                )
            )

```

### COND-0019: módulo.actualizar_producto

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/producto_controller.py:339. Condición: `if data.id_rack:`.

```python
        if data.id_rack:

            await AccesoService.verificar_rack(
                user,
                data.id_rack
            )

```

### COND-0020: módulo.eliminar_producto

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/producto_controller.py:390. Condición: `if await InventarioRepository().obtener_por_producto( id_producto ):`.

```python
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

```

### COND-0021: módulo.obtener_por_id

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/proveedor_controller.py:132. Condición: `if ( user.es_proveedor and id_proveedor != user.id_proveedor ):`.

```python
    if (
        user.es_proveedor
        and id_proveedor != user.id_proveedor
    ):
        raise HTTPException(
            status_code=403,
            detail="Solo puede consultar su propio proveedor"
        )

```

### COND-0022: módulo.obtener_racks_disponibles

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/rack_controller.py:121. Condición: `if user.es_operario:`.

```python
    if user.es_operario:

        id_almacen = user.id_almacen

        if not id_almacen:
            return []

```

### COND-0023: módulo.obtener_racks_disponibles

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/rack_controller.py:125. Condición: `if not id_almacen:`.

```python
        if not id_almacen:
            return []

```

### COND-0024: módulo.obtener_racks_disponibles

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/rack_controller.py:128. Condición: `elif not id_almacen:`.

```python
    elif not id_almacen:

        raise HTTPException(
            status_code=422,
            detail=(
                "Debe indicar id_almacen"
            )
        )

```

### COND-0025: módulo.obtener_racks_disponibles

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/rack_controller.py:144. Condición: `if id_producto:`.

```python
    if id_producto:

        producto = await (
            AccesoService.verificar_producto(
                user,
                id_producto
            )
        )

```

### COND-0026: módulo._verificar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/recomendacion_controller.py:90. Condición: `if recomendacion.get("id_empresa") != user.id_empresa:`.

```python
    if recomendacion.get("id_empresa") != user.id_empresa:
        raise HTTPException(
            status_code=404,
            detail="Recomendación no encontrada"
        )

```

### COND-0027: módulo._verificar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/recomendacion_controller.py:96. Condición: `if ( user.es_operario and recomendacion.get("id_almacen") != user.id_almacen ):`.

```python
    if (
        user.es_operario
        and recomendacion.get("id_almacen")
        != user.id_almacen
    ):
        raise HTTPException(
            status_code=403,
            detail="No tiene acceso a esta recomendación"
        )

```

### COND-0028: módulo.listar_recomendaciones

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/recomendacion_controller.py:149. Condición: `if user.es_operario:`.

```python
    if user.es_operario:

        if not user.id_almacen:
            return []

        return await service.listar_por_almacen(
            user.id_almacen
        )

```

### COND-0029: módulo.listar_recomendaciones

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/controllers/recomendacion_controller.py:151. Condición: `if not user.id_almacen:`.

```python
        if not user.id_almacen:
            return []

```

### COND-0030: módulo.connect_to_mongo

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/database/mongodb.py:31. Condición: `if AsyncIOMotorClient is None:`.

```python
    if AsyncIOMotorClient is None:
        raise RuntimeError(
            "El paquete 'motor' no está instalado. "
            "Instálalo con: pip install motor"
        ) from _motor_import_error

```

### COND-0031: módulo.close_mongo_connection

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/database/mongodb.py:106. Condición: `if client is not None:`.

```python
    if client is not None:

        client.close()

        client = None

        database = None

        print(
            "Conexión MongoDB cerrada"
        )


```

### COND-0032: módulo.get_database

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/database/mongodb.py:121. Condición: `if database is None:`.

```python
    if database is None:

        raise RuntimeError(
            "MongoDB no está conectado."
        )

```

### COND-0033: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:106. Condición: `if ( credentials is None or not credentials.credentials ):`.

```python
    if (
        credentials is None
        or
        not credentials.credentials
    ):

        raise _no_autorizado(
            "No autenticado"
        )

```

### COND-0034: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:138. Condición: `if not sub:`.

```python
    if not sub:

        raise _no_autorizado(
            "Token inválido"
        )

```

### COND-0035: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:152. Condición: `if rol is None:`.

```python
    if rol is None:

        if payload.get("type") not in (
            None,
            "empresa"
        ):

            raise _no_autorizado(
                "Token inválido"
            )

        rol = ROL_EMPRESA

```

### COND-0036: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:154. Condición: `if payload.get("type") not in ( None, "empresa" ):`.

```python
        if payload.get("type") not in (
            None,
            "empresa"
        ):

            raise _no_autorizado(
                "Token inválido"
            )

```

### COND-0037: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:165. Condición: `if rol == ROL_EMPRESA:`.

```python
    if rol == ROL_EMPRESA:

        return UsuarioActual(
            rol=ROL_EMPRESA,
            id_empresa=(
                payload.get("id_empresa")
                or
                sub
            )
        )

    # --------------------------------------------------------
    # OPERARIO
    # --------------------------------------------------------

```

### COND-0038: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:180. Condición: `if rol == ROL_OPERARIO:`.

```python
    if rol == ROL_OPERARIO:

        operario = await (
            OperarioRepository
            .obtener_por_id(
                sub
            )
        )

        if not operario:

            raise _no_autorizado(
                "Operario no encontrado"
            )

        if (
            str(operario.get("estado", "")).upper()
            != "ACTIVO"
        ):

            raise _prohibido(
                "Operario inactivo"
            )

        return UsuarioActual(

            rol=ROL_OPERARIO,

            id_empresa=
                operario["id_empresa"],

            id_operario=
                operario["id_operario"],

            id_almacen=
                operario.get("id_almacen"),

            debe_cambiar_password=bool(
                operario.get(
                    "debe_cambiar_password",
                    False
                )
            )
        )

    # --------------------------------------------------------
    # PROVEEDOR
    # --------------------------------------------------------

```

### COND-0039: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:189. Condición: `if not operario:`.

```python
        if not operario:

            raise _no_autorizado(
                "Operario no encontrado"
            )

```

### COND-0040: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:195. Condición: `if ( str(operario.get("estado", "")).upper() != "ACTIVO" ):`.

```python
        if (
            str(operario.get("estado", "")).upper()
            != "ACTIVO"
        ):

            raise _prohibido(
                "Operario inactivo"
            )

```

### COND-0041: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:229. Condición: `if rol == ROL_PROVEEDOR:`.

```python
    if rol == ROL_PROVEEDOR:

        proveedor = await (
            ProveedorRepository()
            .obtener_por_id(
                sub
            )
        )

        if not proveedor:

            raise _no_autorizado(
                "Proveedor no encontrado"
            )

        if (
            str(proveedor.get("estado", "")).upper()
            != "ACTIVO"
        ):

            raise _prohibido(
                "Proveedor inactivo"
            )

        return UsuarioActual(

            rol=ROL_PROVEEDOR,

            id_empresa=
                proveedor["id_empresa"],

            id_proveedor=
                proveedor["id_proveedor"],

            debe_cambiar_password=bool(
                proveedor.get(
                    "debe_cambiar_password",
                    False
                )
            )
        )

```

### COND-0042: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:238. Condición: `if not proveedor:`.

```python
        if not proveedor:

            raise _no_autorizado(
                "Proveedor no encontrado"
            )

```

### COND-0043: módulo.get_current_user

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:244. Condición: `if ( str(proveedor.get("estado", "")).upper() != "ACTIVO" ):`.

```python
        if (
            str(proveedor.get("estado", "")).upper()
            != "ACTIVO"
        ):

            raise _prohibido(
                "Proveedor inactivo"
            )

```

### COND-0044: módulo.get_usuario_activo

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:293. Condición: `if user.debe_cambiar_password:`.

```python
    if user.debe_cambiar_password:

        raise PasswordChangeRequired()

```

### COND-0045: PasswordChangeRequired.dependencia

Estado IMPLEMENTADO; autorización. Evidencia app/dependencies/dependencies.py:314. Condición: `if user.rol not in roles:`.

```python
        if user.rol not in roles:

            raise _prohibido(
                "Su rol no puede realizar esta acción"
            )

```

### COND-0046: DetalleRecepcionCreate.validar_cantidades

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/detalle_recepcion_dto.py:62. Condición: `if self.comentario_recepcion is not None:`.

```python
        if self.comentario_recepcion is not None:
            self.comentario_recepcion = (
                self.comentario_recepcion.strip()
            )

```

### COND-0047: DetalleRecepcionCreate.validar_cantidades

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/detalle_recepcion_dto.py:67. Condición: `if ( self.cantidad_rechazada > self.cantidad_recibida ):`.

```python
        if (
            self.cantidad_rechazada
            > self.cantidad_recibida
        ):
            raise ValueError(
                "La cantidad rechazada no puede "
                "ser mayor que la recibida"
            )

```

### COND-0048: DetalleRecepcionCreate.validar_cantidades

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/detalle_recepcion_dto.py:76. Condición: `if ( self.cantidad_rechazada > 0 and not self.motivo_rechazo and not self.comentario_recepcion ):`.

```python
        if (
            self.cantidad_rechazada > 0
            and not self.motivo_rechazo
            and not self.comentario_recepcion
        ):
            raise ValueError(
                "Debe indicar el motivo u observación del rechazo"
            )

```

### COND-0049: DetalleRecepcionCreate.validar_cantidades

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/detalle_recepcion_dto.py:85. Condición: `if ( self.estado_recepcion in { EstadoRecepcion.RECHAZADO, EstadoRecepcion.EN_EVALUACION } and not self.comentario_recepcion and not self.motivo_rechazo ):`.

```python
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

```

### COND-0050: InventarioCreate.validar_stocks

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/inventario_dto.py:39. Condición: `if self.stock_minimo > self.stock_maximo:`.

```python
        if self.stock_minimo > self.stock_maximo:

            raise ValueError(
                "El stock mínimo no puede ser mayor "
                "que el stock máximo"
            )

```

### COND-0051: ProductoCreate.validar_refrigeracion

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/producto_dto.py:77. Condición: `if self.requiere_refrigeracion:`.

```python
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

```

### COND-0052: ProductoCreate.validar_refrigeracion

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/producto_dto.py:79. Condición: `if ( self.temperatura_min_almacenamiento is None or self.temperatura_max_almacenamiento is None ):`.

```python
            if (
                self.temperatura_min_almacenamiento is None
                or
                self.temperatura_max_almacenamiento is None
            ):

                raise ValueError(
                    "Si el producto requiere refrigeración, "
                    "debe indicar temperatura mínima y máxima"
                )

```

### COND-0053: ProductoCreate.validar_refrigeracion

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/producto_dto.py:90. Condición: `if ( self.temperatura_min_almacenamiento > self.temperatura_max_almacenamiento ):`.

```python
            if (
                self.temperatura_min_almacenamiento
                >
                self.temperatura_max_almacenamiento
            ):

                raise ValueError(
                    "La temperatura mínima no puede ser "
                    "mayor que la máxima"
                )

```

### COND-0054: módulo._validar_rango

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/rack_dto.py:19. Condición: `if ( modelo.temperatura_min is not None and modelo.temperatura_max is not None and modelo.temperatura_min > modelo.temperatura_max ):`.

```python
    if (
        modelo.temperatura_min is not None
        and modelo.temperatura_max is not None
        and modelo.temperatura_min > modelo.temperatura_max
    ):
        raise ValueError(
            "La temperatura mínima no puede "
            "ser mayor que la máxima"
        )

```

### COND-0055: ResolverEvaluacion.validar_estado

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/recepcion_mercaderia_dto.py:83. Condición: `if self.estado_recepcion not in { EstadoRecepcion.CONFORME, EstadoRecepcion.RECHAZADO }:`.

```python
        if self.estado_recepcion not in {
            EstadoRecepcion.CONFORME,
            EstadoRecepcion.RECHAZADO
        }:
            raise ValueError(
                "Una evaluación solo puede "
                "resolverse como CONFORME "
                "o RECHAZADO"
            )

```

### COND-0056: SaikiAskRequest.require_message

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/saiki_dto.py:42. Condición: `if not self.message and not self.question:`.

```python
        if not self.message and not self.question:
            raise ValueError("Debe indicar message o question.")
```

### COND-0057: SaikiAskRequest.require_message

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/saiki_dto.py:44. Condición: `if self.message and self.question and self.message != self.question:`.

```python
        if self.message and self.question and self.message != self.question:
            raise ValueError("message y question no pueden ser diferentes.")
```

### COND-0058: SaikiAskRequest.require_message

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/saiki_dto.py:46. Condición: `if not self.message:`.

```python
        if not self.message:
            self.message = self.question
```

### COND-0059: SaikiAskRequest.require_message

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/saiki_dto.py:48. Condición: `if not self.message.strip():`.

```python
        if not self.message.strip():
            raise ValueError("message no puede contener solo espacios.")
```

### COND-0060: SaikiAskRequest.require_message

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/saiki_dto.py:50. Condición: `if len(self.history) > 40:`.

```python
        if len(self.history) > 40:
            raise ValueError("El historial admite hasta 40 mensajes.")
```

### COND-0061: SaikiAskRequest.require_message

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/saiki_dto.py:53. Condición: `if item.get("role") not in {"user", "assistant"} or not isinstance(item.get("content"), str):`.

```python
            if item.get("role") not in {"user", "assistant"} or not isinstance(item.get("content"), str):
                raise ValueError("El historial solo admite mensajes de usuario y asistente con contenido textual.")
```

### COND-0062: SaikiAskRequest.require_message

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/saiki_dto.py:55. Condición: `if len(item["content"]) > 8000:`.

```python
            if len(item["content"]) > 8000:
                raise ValueError("Un mensaje del historial supera el límite de tamaño.")
```

### COND-0063: SaikiAskRequest.require_message

Estado IMPLEMENTADO; validación de contrato. Evidencia app/dto/saiki_dto.py:57. Condición: `if set(item) - {"role", "content"}:`.

```python
            if set(item) - {"role", "content"}:
                raise ValueError("El historial no admite instrucciones de herramientas.")
```

### COND-0064: módulo.verificar_forecast

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/main.py:256. Condición: `if id_inventario:`.

```python
    if id_inventario:

        await AccesoService.verificar_inventario(
            user,
            id_inventario
        )


```

### COND-0065: DemandHistory._inicio_dia

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:80. Condición: `if isinstance( fecha, datetime ):`.

```python
        if isinstance(
            fecha,
            datetime
        ):

            fecha = fecha.date()

```

### COND-0066: DemandHistory._fin_dia

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:98. Condición: `if isinstance( fecha, datetime ):`.

```python
        if isinstance(
            fecha,
            datetime
        ):

            fecha = fecha.date()

```

### COND-0067: DemandHistory.obtener_historial

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:124. Condición: `if dias <= 0:`.

```python
        if dias <= 0:

            raise ValueError(
                "dias debe ser mayor que 0."
            )

        # --------------------------------------------------------
        # VALIDAR INVENTARIO
        # --------------------------------------------------------

```

### COND-0068: DemandHistory.obtener_historial

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:141. Condición: `if inventario is None:`.

```python
        if inventario is None:

            raise ValueError(
                "No existe el inventario "
                f"{id_inventario}."
            )

        # --------------------------------------------------------
        # FECHA FINAL
        # --------------------------------------------------------

```

### COND-0069: DemandHistory.obtener_historial

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:152. Condición: `if fecha_fin is None:`.

```python
        if fecha_fin is None:

            fecha_final_date = (
                datetime.now(
                    timezone.utc
                )
                .date()
            )

```

### COND-0070: DemandHistory.obtener_historial

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:161. Condición: `elif isinstance( fecha_fin, datetime ):`.

```python
        elif isinstance(
            fecha_fin,
            datetime
        ):

            fecha_final_date = (
                fecha_fin.date()
            )

```

### COND-0071: DemandHistory.obtener_historial

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:243. Condición: `if consumo:`.

```python
        if consumo:

            consumo_df = pd.DataFrame(
                consumo
            )

            consumo_df[
                "fecha"
            ] = pd.to_datetime(
                consumo_df[
                    "fecha"
                ]
            )

            consumo_df[
                "cantidad"
            ] = pd.to_numeric(
                consumo_df[
                    "cantidad"
                ],
                errors="coerce"
            ).fillna(
                0
            )

            consumo_df = (
                consumo_df[
                    [
                        "fecha",
                        "cantidad"
                    ]
                ]
                .rename(
                    columns={
                        "cantidad":
                            "demanda"
                    }
                )
            )

            # ----------------------------------------------------
            # MERGE
            # ----------------------------------------------------

            historial = (
                historial[
                    [
                        "fecha"
                    ]
                ]
                .merge(
                    consumo_df,
                    how="left",
                    on="fecha"
                )
            )

            historial[
                "demanda"
            ] = (
                historial[
                    "demanda"
                ]
                .fillna(
                    0
                )
                .astype(
                    float
                )
            )

        # --------------------------------------------------------
        # ORDEN
        # --------------------------------------------------------

```

### COND-0072: DemandHistory.obtener_historial_completo

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:346. Condición: `if inventario is None:`.

```python
        if inventario is None:

            raise ValueError(
                "Inventario no encontrado."
            )

```

### COND-0073: DemandHistory.obtener_historial_completo

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:377. Condición: `if not salidas:`.

```python
        if not salidas:

            return pd.DataFrame(
                columns=[
                    "fecha",
                    "demanda"
                ]
            )

```

### COND-0074: DemandHistory.obtener_resumen

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/demand_history.py:433. Condición: `if historial.empty:`.

```python
        if historial.empty:

            return {
                "id_inventario":
                    id_inventario,

                "dias":
                    0,

                "demanda_total":
                    0,

                "demanda_promedio":
                    0,

                "dias_con_demanda":
                    0,

                "dias_sin_demanda":
                    0,

                "historial_suficiente_ml":
                    False
            }

```

### COND-0075: FeatureBuilder._safe_float

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:98. Condición: `if np.isnan(result):`.

```python
            if np.isnan(result):

                return default

```

### COND-0076: FeatureBuilder._safe_float

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:102. Condición: `if np.isinf(result):`.

```python
            if np.isinf(result):

                return default

```

### COND-0077: FeatureBuilder._safe_divide

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:135. Condición: `if abs( denominator ) < cls.EPSILON:`.

```python
        if abs(
            denominator
        ) < cls.EPSILON:

            return default

```

### COND-0078: FeatureBuilder._prepare_history

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:155. Condición: `if not isinstance( history, pd.DataFrame ):`.

```python
        if not isinstance(
            history,
            pd.DataFrame
        ):

            raise TypeError(
                "history debe ser un pandas.DataFrame."
            )

```

### COND-0079: FeatureBuilder._prepare_history

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:164. Condición: `if history.empty:`.

```python
        if history.empty:

            raise ValueError(
                "El historial de demanda está vacío."
            )

```

### COND-0080: FeatureBuilder._prepare_history

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:180. Condición: `if missing:`.

```python
        if missing:

            raise ValueError(
                "El historial debe contener las columnas: "
                "fecha y demanda."
            )

```

### COND-0081: FeatureBuilder._prepare_history

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:231. Condición: `if df.empty:`.

```python
        if df.empty:

            raise ValueError(
                "No existen fechas válidas "
                "en el historial."
            )

```

### COND-0082: FeatureBuilder._lag

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:297. Condición: `if lag <= 0:`.

```python
        if lag <= 0:

            raise ValueError(
                "lag debe ser mayor que 0."
            )

```

### COND-0083: FeatureBuilder._lag

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:303. Condición: `if len(series) < lag:`.

```python
        if len(series) < lag:

            return np.nan

```

### COND-0084: FeatureBuilder._last_values

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:323. Condición: `if window <= 0:`.

```python
        if window <= 0:

            raise ValueError(
                "window debe ser mayor que 0."
            )

```

### COND-0085: FeatureBuilder._last_values

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:329. Condición: `if series.empty:`.

```python
        if series.empty:

            return pd.Series(
                dtype=float
            )

```

### COND-0086: FeatureBuilder._rolling_mean

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:359. Condición: `if len(values) < window:`.

```python
        if len(values) < window:

            return np.nan

```

### COND-0087: FeatureBuilder._rolling_std

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:383. Condición: `if len(values) < window:`.

```python
        if len(values) < window:

            return np.nan

```

### COND-0088: FeatureBuilder._rolling_max

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:409. Condición: `if len(values) < window:`.

```python
        if len(values) < window:

            return np.nan

```

### COND-0089: FeatureBuilder._ewma

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:428. Condición: `if series.empty:`.

```python
        if series.empty:

            return np.nan

```

### COND-0090: FeatureBuilder._zero_ratio

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:463. Condición: `if len(values) < window:`.

```python
        if len(values) < window:

            return np.nan

```

### COND-0091: FeatureBuilder._days_since_sale

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:482. Condición: `if series.empty:`.

```python
        if series.empty:

            return np.nan

```

### COND-0092: FeatureBuilder._days_since_sale

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:496. Condición: `if len( positive_indices ) == 0:`.

```python
        if len(
            positive_indices
        ) == 0:

            return float(
                len(values)
            )

```

### COND-0093: FeatureBuilder._sale_rate

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:530. Condición: `if len(values) < window:`.

```python
        if len(values) < window:

            return np.nan

```

### COND-0094: FeatureBuilder._growth_streak_3

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:555. Condición: `if len(values) < 4:`.

```python
        if len(values) < 4:

            return np.nan

```

### COND-0095: FeatureBuilder._peak_count_7

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:586. Condición: `if len(values) < 7:`.

```python
        if len(values) < 7:

            return np.nan

```

### COND-0096: FeatureBuilder._peak_count_7

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:595. Condición: `if np.isnan( mean_28 ):`.

```python
        if np.isnan(
            mean_28
        ):

            return np.nan

```

### COND-0097: FeatureBuilder._dow_mean

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:661. Condición: `if len( filtered ) < 1:`.

```python
        if len(
            filtered
        ) < 1:

            return np.nan

```

### COND-0098: FeatureBuilder._dow_std

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:702. Condición: `if len(filtered) < 2:`.

```python
        if len(filtered) < 2:

            return np.nan

```

### COND-0099: FeatureBuilder.build_demand_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:822. Condición: `if horizon < 1 or horizon > 7:`.

```python
        if horizon < 1 or horizon > 7:

            raise ValueError(
                "horizon debe estar entre 1 y 7."
            )

```

### COND-0100: FeatureBuilder.build_demand_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1173. Condición: `if len(series) >= 14:`.

```python
        if len(series) >= 14:

            recent_7 = (
                series.iloc[
                    -7:
                ].mean()
            )

            previous_7 = (
                series.iloc[
                    -14:-7
                ].mean()
            )

            result[
                "previous_7_mean"
            ] = float(
                previous_7
            )

            result[
                "recent7_vs_previous7"
            ] = self._safe_divide(
                recent_7,
                previous_7
            )

```

### COND-0101: FeatureBuilder.build_demand_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1349. Condición: `if effective_lag >= 1:`.

```python
            if effective_lag >= 1:

                value = self._lag(
                    series,
                    effective_lag
                )

```

### COND-0102: FeatureBuilder.build_demand_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1356. Condición: `elif effective_lag == 0:`.

```python
            elif effective_lag == 0:

                value = float(
                    series.iloc[-1]
                )

```

### COND-0103: FeatureBuilder.build_demand_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1489. Condición: `if feature not in result:`.

```python
            if feature not in result:

                result[
                    feature
                ] = np.nan

```

### COND-0104: FeatureBuilder.validate_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1546. Condición: `if not isinstance( data, dict ):`.

```python
        if not isinstance(
            data,
            dict
        ):

            raise TypeError(
                "data debe ser un diccionario."
            )

```

### COND-0105: FeatureBuilder.validate_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1566. Condición: `if missing:`.

```python
        if missing:

            raise ValueError(
                "Faltan features requeridas "
                "por LightGBM:\n\n"
                + "\n".join(
                    missing
                )
            )

    # ============================================================
    # FEATURES FALTANTES
    # ============================================================

```

### COND-0106: FeatureBuilder.build_dataframe

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1681. Condición: `if not rows:`.

```python
        if not rows:

            raise ValueError(
                "No se recibieron filas "
                "para construir features."
            )

```

### COND-0107: FeatureBuilder.prepare_dataframe

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1705. Condición: `if not isinstance( df, pd.DataFrame ):`.

```python
        if not isinstance(
            df,
            pd.DataFrame
        ):

            raise TypeError(
                "df debe ser un pandas.DataFrame."
            )

```

### COND-0108: FeatureBuilder.prepare_dataframe

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1714. Condición: `if df.empty:`.

```python
        if df.empty:

            raise ValueError(
                "El DataFrame está vacío."
            )

```

### COND-0109: FeatureBuilder.prepare_dataframe

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1737. Condición: `if missing:`.

```python
        if missing:

            raise ValueError(
                "El DataFrame no contiene "
                "todas las features requeridas:\n\n"
                + "\n".join(
                    missing
                )
            )

        # --------------------------------------------------------
        # ORDEN EXACTO DEL ENTRENAMIENTO
        # --------------------------------------------------------

```

### COND-0110: FeatureBuilder.prepare_dataframe

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/feature_builder.py:1767. Condición: `if column not in df.columns:`.

```python
            if column not in df.columns:

                continue

```

### COND-0111: MLContextBuilder._obtener_id

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:95. Condición: `if not documento:`.

```python
        if not documento:
            return None

```

### COND-0112: MLContextBuilder._obtener_id

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:104. Condición: `if valor is None:`.

```python
            if valor is None:
                continue

```

### COND-0113: MLContextBuilder._obtener_id

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:111. Condición: `if valor:`.

```python
            if valor:
                return valor

```

### COND-0114: MLContextBuilder._obtener_ids_productos

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:141. Condición: `if id_producto:`.

```python
            if id_producto:

                ids_productos.append(
                    id_producto
                )

```

### COND-0115: MLContextBuilder._normalizar_texto

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:163. Condición: `if valor is None:`.

```python
        if valor is None:
            return None

```

### COND-0116: MLContextBuilder._normalizar_texto

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:170. Condición: `if not valor:`.

```python
        if not valor:
            return None

```

### COND-0117: MLContextBuilder._normalizar_fecha_base

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:187. Condición: `if fecha_base is None:`.

```python
        if fecha_base is None:

            return (
                datetime.now(
                    timezone.utc
                )
                .date()
            )

```

### COND-0118: MLContextBuilder._normalizar_fecha_base

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:196. Condición: `if isinstance( fecha_base, datetime ):`.

```python
        if isinstance(
            fecha_base,
            datetime
        ):

            return fecha_base.date()

```

### COND-0119: MLContextBuilder._normalizar_fecha_base

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:203. Condición: `if isinstance( fecha_base, date ):`.

```python
        if isinstance(
            fecha_base,
            date
        ):

            return fecha_base

```

### COND-0120: MLContextBuilder._validar_horizon

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:240. Condición: `if horizon < 1 or horizon > 7:`.

```python
        if horizon < 1 or horizon > 7:

            raise ValueError(
                "horizon debe estar "
                "entre 1 y 7."
            )

```

### COND-0121: MLContextBuilder._crear_serie_diaria

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:342. Condición: `if fecha is None:`.

```python
            if fecha is None:
                continue

```

### COND-0122: MLContextBuilder._crear_serie_diaria

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:347. Condición: `if isinstance( fecha, datetime ):`.

```python
                if isinstance(
                    fecha,
                    datetime
                ):

                    fecha_registro = (
                        fecha.date()
                    )

```

### COND-0123: MLContextBuilder._crear_serie_diaria

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:356. Condición: `elif isinstance( fecha, date ):`.

```python
                elif isinstance(
                    fecha,
                    date
                ):

                    fecha_registro = fecha

```

### COND-0124: MLContextBuilder._crear_serie_diaria

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:380. Condición: `if fecha_registro not in serie:`.

```python
            if fecha_registro not in serie:
                continue

```

### COND-0125: MLContextBuilder._mean_anterior

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:477. Condición: `if not valores:`.

```python
        if not valores:
            return 0.0

```

### COND-0126: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:707. Condición: `if id_inventario is None:`.

```python
        if id_inventario is None:

            raise ValueError(
                "id_inventario es obligatorio."
            )

```

### COND-0127: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:717. Condición: `if not id_inventario:`.

```python
        if not id_inventario:

            raise ValueError(
                "id_inventario no puede estar vacío."
            )


        # ========================================================
        # FECHA BASE
        # ========================================================

```

### COND-0128: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:755. Condición: `if not inventario:`.

```python
        if not inventario:

            raise ValueError(
                "No existe el inventario "
                f"con id {id_inventario}."
            )


        # ========================================================
        # PRODUCTO
        # ========================================================

```

### COND-0129: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:774. Condición: `if not id_producto:`.

```python
        if not id_producto:

            raise ValueError(
                "El inventario no tiene "
                "id_producto asociado."
            )

```

### COND-0130: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:788. Condición: `if not producto:`.

```python
        if not producto:

            raise ValueError(
                "No se encontró el producto "
                f"{id_producto}."
            )


        # ========================================================
        # RACK
        # ========================================================

```

### COND-0131: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:807. Condición: `if not id_rack:`.

```python
        if not id_rack:

            id_rack = (
                self._obtener_id(
                    producto,
                    "id_rack"
                )
            )

```

### COND-0132: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:816. Condición: `if not id_rack:`.

```python
        if not id_rack:

            raise ValueError(
                "No se pudo determinar "
                "el rack del inventario."
            )

```

### COND-0133: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:830. Condición: `if not rack:`.

```python
        if not rack:

            raise ValueError(
                "No se encontró el rack "
                f"{id_rack}."
            )


        # ========================================================
        # ZONA
        # ========================================================

```

### COND-0134: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:849. Condición: `if not id_zona:`.

```python
        if not id_zona:

            raise ValueError(
                "El rack no tiene "
                "id_zona asociado."
            )

```

### COND-0135: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:863. Condición: `if not zona:`.

```python
        if not zona:

            raise ValueError(
                "No se encontró la zona "
                f"{id_zona}."
            )


        # ========================================================
        # ALMACEN
        # ========================================================

```

### COND-0136: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:882. Condición: `if not id_almacen:`.

```python
        if not id_almacen:

            raise ValueError(
                "La zona no tiene "
                "id_almacen asociado."
            )

```

### COND-0137: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:896. Condición: `if not almacen:`.

```python
        if not almacen:

            raise ValueError(
                "No se encontró el almacén "
                f"{id_almacen}."
            )

```

### COND-0138: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:948. Condición: `if categoria:`.

```python
        if categoria:

            productos_categoria_global = await (
                self.producto_repository
                .obtener_por_categoria(
                    categoria
                )
            )

```

### COND-0139: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:970. Condición: `if categoria:`.

```python
        if categoria:

            categoria_normalizada = (
                categoria.casefold()
            )

            for producto_almacen in (
                productos_almacen
            ):

                categoria_producto = (
                    self._normalizar_texto(
                        producto_almacen.get(
                            "categoria"
                        )
                    )
                )

                if not categoria_producto:
                    continue

                if (
                    categoria_producto.casefold()
                    == categoria_normalizada
                ):

                    productos_categoria_almacen.append(
                        producto_almacen
                    )

```

### COND-0140: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:988. Condición: `if not categoria_producto:`.

```python
                if not categoria_producto:
                    continue

```

### COND-0141: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:991. Condición: `if ( categoria_producto.casefold() == categoria_normalizada ):`.

```python
                if (
                    categoria_producto.casefold()
                    == categoria_normalizada
                ):

                    productos_categoria_almacen.append(
                        producto_almacen
                    )

```

### COND-0142: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:1044. Condición: `if ids_productos_categoria_almacen:`.

```python
        if ids_productos_categoria_almacen:

            consumo_categoria_almacen = await (
                self.movimiento_repository
                .obtener_consumo_diario_productos(

                    ids_productos=
                        ids_productos_categoria_almacen,

                    fecha_inicio=
                        fecha_inicio_query,

                    fecha_fin=
                        fecha_fin_query
                )
            )

```

### COND-0143: MLContextBuilder.build

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/ml_context_builder.py:1079. Condición: `if ids_productos_almacen:`.

```python
        if ids_productos_almacen:

            consumo_almacen = await (
                self.movimiento_repository
                .obtener_consumo_diario_productos(

                    ids_productos=
                        ids_productos_almacen,

                    fecha_inicio=
                        fecha_inicio_query,

                    fecha_fin=
                        fecha_fin_query
                )
            )

```

### COND-0144: ModelLoader.__init__

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:47. Condición: `if model_dir is None:`.

```python
        if model_dir is None:

            self.model_dir = (
                Path(__file__)
                .resolve()
                .parent
                / "models"
                / "psitwin_v3_6"
            )

```

### COND-0145: ModelLoader.validate_paths

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:115. Condición: `if not self.model_dir.exists():`.

```python
        if not self.model_dir.exists():

            raise FileNotFoundError(
                "No existe la carpeta principal "
                "del modelo:\n"
                f"{self.model_dir}"
            )

```

### COND-0146: ModelLoader.validate_paths

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:123. Condición: `if not self.config_path.exists():`.

```python
        if not self.config_path.exists():

            raise FileNotFoundError(
                "No se encontró "
                "config_v3_6.json:\n"
                f"{self.config_path}"
            )

```

### COND-0147: ModelLoader.validate_paths

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:131. Condición: `if not self.selection_path.exists():`.

```python
        if not self.selection_path.exists():

            raise FileNotFoundError(
                "No se encontró "
                "selection_by_horizon.csv:\n"
                f"{self.selection_path}"
            )

```

### COND-0148: ModelLoader.validate_paths

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:139. Condición: `if not self.models_dir.exists():`.

```python
        if not self.models_dir.exists():

            raise FileNotFoundError(
                "No se encontró la carpeta "
                "de modelos:\n"
                f"{self.models_dir}"
            )

    # ========================================================
    # CARGAR CONFIG
    # ========================================================

```

### COND-0149: ModelLoader.load_config

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:155. Condición: `if not self.config_path.exists():`.

```python
        if not self.config_path.exists():

            raise FileNotFoundError(
                f"No existe: "
                f"{self.config_path}"
            )

```

### COND-0150: ModelLoader.load_selection

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:181. Condición: `if not self.selection_path.exists():`.

```python
        if not self.selection_path.exists():

            raise FileNotFoundError(
                f"No existe: "
                f"{self.selection_path}"
            )

```

### COND-0151: ModelLoader._find_global_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:203. Condición: `if horizon < 1 or horizon > 7:`.

```python
        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

        # Primero intentamos el patrón
        # utilizado por el notebook.
```

### COND-0152: ModelLoader._find_global_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:223. Condición: `if not matches:`.

```python
        if not matches:

            pattern = (
                f"*global*D{horizon}.txt"
            )

            matches = sorted(
                self.models_dir.glob(
                    pattern
                )
            )

```

### COND-0153: ModelLoader._find_global_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:235. Condición: `if not matches:`.

```python
        if not matches:

            raise FileNotFoundError(
                "No se encontró un modelo "
                f"global para D+{horizon}.\n"
                f"Carpeta buscada:\n"
                f"{self.models_dir}"
            )

```

### COND-0154: ModelLoader._find_global_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:244. Condición: `if len(matches) > 1:`.

```python
        if len(matches) > 1:

            print(
                "[ADVERTENCIA] "
                f"Se encontraron {len(matches)} "
                f"modelos globales para D+{horizon}."
            )

            print(
                "[ADVERTENCIA] "
                f"Se utilizará: "
                f"{matches[0].name}"
            )

```

### COND-0155: ModelLoader.load_global_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:269. Condición: `if horizon in self.global_models:`.

```python
        if horizon in self.global_models:

            return self.global_models[
                horizon
            ]

```

### COND-0156: ModelLoader.load_local_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:332. Condición: `if not model_name:`.

```python
        if not model_name:

            raise ValueError(
                "model_name no puede "
                "estar vacío."
            )

```

### COND-0157: ModelLoader.load_local_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:339. Condición: `if model_name in self.local_models:`.

```python
        if model_name in self.local_models:

            return self.local_models[
                model_name
            ]

```

### COND-0158: ModelLoader.load_local_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:350. Condición: `if not model_path.exists():`.

```python
        if not model_path.exists():

            raise FileNotFoundError(
                "Modelo local no encontrado:\n"
                f"{model_path}"
            )

```

### COND-0159: ModelLoader.get_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:387. Condición: `if not self.config:`.

```python
        if not self.config:

            self.load_config()

```

### COND-0160: ModelLoader.get_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:395. Condición: `if features is None:`.

```python
        if features is None:

            raise KeyError(
                "config_v3_6.json no contiene "
                "la clave 'features'."
            )

```

### COND-0161: ModelLoader.get_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:402. Condición: `if not isinstance( features, list ):`.

```python
        if not isinstance(
            features,
            list
        ):

            raise TypeError(
                "'features' debe ser una lista."
            )

```

### COND-0162: ModelLoader.get_categorical_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:421. Condición: `if not self.config:`.

```python
        if not self.config:

            self.load_config()

```

### COND-0163: ModelLoader.get_categorical_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:430. Condición: `if categorical is None:`.

```python
        if categorical is None:

            return []

```

### COND-0164: ModelLoader.get_categorical_features

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:434. Condición: `if not isinstance( categorical, list ):`.

```python
        if not isinstance(
            categorical,
            list
        ):

            raise TypeError(
                "'categorical_features' "
                "debe ser una lista."
            )

```

### COND-0165: ModelLoader.get_selection_for_horizon

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:455. Condición: `if self.selection is None:`.

```python
        if self.selection is None:

            self.load_selection()

```

### COND-0166: ModelLoader.get_selection_for_horizon

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:459. Condición: `if self.selection is None:`.

```python
        if self.selection is None:
            return None

        # Intentamos encontrar automáticamente
        # la columna que representa el horizonte.

```

### COND-0167: ModelLoader.get_selection_for_horizon

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:476. Condición: `if column in self.selection.columns:`.

```python
            if column in self.selection.columns:

                horizon_column = column
                break

```

### COND-0168: ModelLoader.get_selection_for_horizon

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:481. Condición: `if horizon_column is None:`.

```python
        if horizon_column is None:

            return None

```

### COND-0169: ModelLoader.get_selection_for_horizon

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:491. Condición: `if rows.empty:`.

```python
        if rows.empty:

            return None

```

### COND-0170: ModelLoader.load_all

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:507. Condición: `if self._loaded:`.

```python
        if self._loaded:
            return

```

### COND-0171: ModelLoader.get_global_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:529. Condición: `if horizon < 1 or horizon > 7:`.

```python
        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

```

### COND-0172: ModelLoader.get_global_model

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:536. Condición: `if horizon not in self.global_models:`.

```python
        if horizon not in self.global_models:

            self.load_global_model(
                horizon
            )

```

### COND-0173: ModelLoader.info

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:554. Condición: `if not self.config:`.

```python
        if not self.config:

            self.load_config()

```

### COND-0174: ModelLoader.info

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/model_loader.py:558. Condición: `if self.selection is None:`.

```python
        if self.selection is None:

            self.load_selection()

```

### COND-0175: DemandPredictor.__init__

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:61. Condición: `if loader is None:`.

```python
        if loader is None:

            self.loader = (
                ModelLoader()
            )

```

### COND-0176: DemandPredictor.predict_horizon

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:94. Condición: `if horizon < 1 or horizon > 7:`.

```python
        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

        # ----------------------------------------------------
        # FEATURES
        # ----------------------------------------------------

```

### COND-0177: DemandPredictor.predict_horizon

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:143. Condición: `if prediction is None:`.

```python
        if prediction is None:

            raise RuntimeError(
                "LightGBM devolvió None."
            )

```

### COND-0178: DemandPredictor.predict_horizon

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:149. Condición: `if len(prediction) == 0:`.

```python
        if len(prediction) == 0:

            raise RuntimeError(
                "LightGBM no devolvió "
                "predicciones."
            )

```

### COND-0179: DemandPredictor.predict_7_days

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:185. Condición: `if start_date is None:`.

```python
        if start_date is None:

            base_date = (
                datetime.now()
                .date()
            )

```

### COND-0180: DemandPredictor.predict_7_days

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:192. Condición: `elif isinstance( start_date, datetime ):`.

```python
        elif isinstance(
            start_date,
            datetime
        ):

            base_date = (
                start_date.date()
            )

```

### COND-0181: DemandPredictor.predict_7_days

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:201. Condición: `elif isinstance( start_date, date ):`.

```python
        elif isinstance(
            start_date,
            date
        ):

            base_date = start_date

```

### COND-0182: DemandPredictor.predict_7_days

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:232. Condición: `if ( horizon not in features_by_horizon ):`.

```python
            if (
                horizon
                not in features_by_horizon
            ):

                raise ValueError(
                    "No se proporcionaron "
                    f"features para D+{horizon}."
                )

```

### COND-0183: DemandPredictor.predict_dataframe

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:305. Condición: `if horizon < 1 or horizon > 7:`.

```python
        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

        # Preparar features
```

### COND-0184: DemandPredictor.predict_batch

Estado IMPLEMENTADO; regla del pipeline ML. Evidencia app/ml/predictor.py:355. Condición: `if horizon < 1 or horizon > 7:`.

```python
        if horizon < 1 or horizon > 7:

            raise ValueError(
                "El horizonte debe estar "
                "entre 1 y 7."
            )

```

### COND-0185: AlertaRepository.actualizar

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/alerta_repository.py:333. Condición: `if resultado.matched_count == 0:`.

```python
        if resultado.matched_count == 0:

            return None

```

### COND-0186: AlmacenRepository.actualizar

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/almacen_repository.py:163. Condición: `if result.matched_count == 0:`.

```python
        if result.matched_count == 0:

            return None

```

### COND-0187: EmpresaRepository.actualizar

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/empresa_repository.py:183. Condición: `if result.matched_count == 0:`.

```python
        if result.matched_count == 0:

            return None

```

### COND-0188: InventarioRepository.actualizar

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/inventario_repository.py:235. Condición: `if result.matched_count == 0:`.

```python
        if result.matched_count == 0:

            return None

```

### COND-0189: MovimientoRepository.crear

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/movimiento_repository.py:57. Condición: `if not documento.get( "fecha_hora" ):`.

```python
        if not documento.get(
            "fecha_hora"
        ):

            documento[
                "fecha_hora"
            ] = datetime.now(
                timezone.utc
            )

```

### COND-0190: MovimientoRepository.obtener_consumo_diario_productos

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/movimiento_repository.py:842. Condición: `if not ids_productos:`.

```python
        if not ids_productos:

            return []

        # Eliminar:
        #
        # None
        # strings vacíos
        # duplicados
        #
        # Manteniendo IDs como string.

```

### COND-0191: MovimientoRepository.obtener_consumo_diario_productos

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/movimiento_repository.py:862. Condición: `if not ids_limpios:`.

```python
        if not ids_limpios:

            return []

        # --------------------------------------------------------
        # PIPELINE
        # --------------------------------------------------------

```

### COND-0192: OperarioRepository.nombres_por_ids

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/operario_repository.py:151. Condición: `if not ids:`.

```python
        if not ids:
            return {}

```

### COND-0193: OperarioRepository.actualizar

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/operario_repository.py:294. Condición: `if result.matched_count == 0:`.

```python
        if result.matched_count == 0:
            return None

```

### COND-0194: ProductoRepository.obtener_por_almacen

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/producto_repository.py:162. Condición: `if id_zona:`.

```python
            if id_zona:

                ids_zonas.append(
                    id_zona
                )


```

### COND-0195: ProductoRepository.obtener_por_almacen

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/producto_repository.py:169. Condición: `if not ids_zonas:`.

```python
        if not ids_zonas:

            return []


        # ========================================================
        # 2. RACKS DE LAS ZONAS
        # ========================================================

```

### COND-0196: ProductoRepository.obtener_por_almacen

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/producto_repository.py:207. Condición: `if id_rack:`.

```python
            if id_rack:

                ids_racks.append(
                    id_rack
                )


```

### COND-0197: ProductoRepository.obtener_por_almacen

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/producto_repository.py:214. Condición: `if not ids_racks:`.

```python
        if not ids_racks:

            return []


        # ========================================================
        # 3. PRODUCTOS QUE ESTAN EN ESOS RACKS
        # ========================================================

```

### COND-0198: ProductoRepository.actualizar

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/producto_repository.py:330. Condición: `if result.matched_count == 0:`.

```python
        if result.matched_count == 0:

            return None


```

### COND-0199: RackRepository.actualizar

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/rack_repository.py:237. Condición: `if result.matched_count == 0:`.

```python
        if result.matched_count == 0:

            return None

```

### COND-0200: RecomendacionRepository.actualizar

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/recomendacion_repository.py:334. Condición: `if resultado.matched_count == 0:`.

```python
        if resultado.matched_count == 0:

            return None

```

### COND-0201: ZonaRepository.actualizar

Estado IMPLEMENTADO; consulta/persistencia. Evidencia app/repositories/zona_repository.py:213. Condición: `if result.matched_count == 0:`.

```python
        if result.matched_count == 0:

            return None

```

### COND-0202: AccesoService.ids_almacenes

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:145. Condición: `if user.es_proveedor:`.

```python
        if user.es_proveedor:

            return set()

```

### COND-0203: AccesoService.ids_almacenes

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:149. Condición: `if user.es_operario:`.

```python
        if user.es_operario:

            return (
                {user.id_almacen}
                if user.id_almacen
                else set()
            )

```

### COND-0204: AccesoService.zonas_visibles

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:181. Condición: `if not ids_almacen:`.

```python
        if not ids_almacen:
            return []

```

### COND-0205: AccesoService.ids_racks

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:220. Condición: `if not ids_zona:`.

```python
        if not ids_zona:
            return set()

```

### COND-0206: AccesoService.ids_inventarios

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:247. Condición: `if not ids_rack:`.

```python
        if not ids_rack:
            return set()

```

### COND-0207: AccesoService.verificar_empresa

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:305. Condición: `if id_empresa != user.id_empresa:`.

```python
        if id_empresa != user.id_empresa:

            raise _no_encontrado(
                "Empresa no encontrada"
            )


    # ============================================================
    # ALMACEN
    # ============================================================

```

### COND-0208: AccesoService.verificar_almacen

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:322. Condición: `if user.es_proveedor:`.

```python
        if user.es_proveedor:

            raise _prohibido()

```

### COND-0209: AccesoService.verificar_almacen

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:332. Condición: `if ( not almacen or almacen.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not almacen
            or
            almacen.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Almacén no encontrado"
            )

```

### COND-0210: AccesoService.verificar_almacen

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:343. Condición: `if ( user.es_operario and id_de_almacen(almacen) != user.id_almacen ):`.

```python
        if (
            user.es_operario
            and
            id_de_almacen(almacen)
            != user.id_almacen
        ):

            raise _prohibido(
                "No tiene acceso a este almacén"
            )

```

### COND-0211: AccesoService.verificar_zona

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:367. Condición: `if user.es_proveedor:`.

```python
        if user.es_proveedor:

            raise _prohibido()

```

### COND-0212: AccesoService.verificar_zona

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:377. Condición: `if not zona:`.

```python
        if not zona:

            raise _no_encontrado(
                "Zona no encontrada"
            )

```

### COND-0213: AccesoService.verificar_zona

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:389. Condición: `if ( not almacen or almacen.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not almacen
            or
            almacen.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Zona no encontrada"
            )

```

### COND-0214: AccesoService.verificar_zona

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:400. Condición: `if ( user.es_operario and zona.get("id_almacen") != user.id_almacen ):`.

```python
        if (
            user.es_operario
            and
            zona.get("id_almacen")
            != user.id_almacen
        ):

            raise _prohibido(
                "No tiene acceso a esta zona"
            )

```

### COND-0215: AccesoService.verificar_rack

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:430. Condición: `if not rack:`.

```python
        if not rack:

            raise _no_encontrado(
                "Rack no encontrado"
            )

```

### COND-0216: AccesoService.verificar_rack

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:445. Condición: `if exc.status_code == 404:`.

```python
            if exc.status_code == 404:

                raise _no_encontrado(
                    "Rack no encontrado"
                )

```

### COND-0217: AccesoService.verificar_inventario

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:475. Condición: `if not inventario:`.

```python
        if not inventario:

            raise _no_encontrado(
                "Inventario no encontrado"
            )

```

### COND-0218: AccesoService.verificar_inventario

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:490. Condición: `if exc.status_code == 404:`.

```python
            if exc.status_code == 404:

                raise _no_encontrado(
                    "Inventario no encontrado"
                )

```

### COND-0219: AccesoService.verificar_producto

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:522. Condición: `if ( not producto or producto.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not producto
            or
            producto.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Producto no encontrado"
            )

```

### COND-0220: AccesoService.verificar_producto

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:533. Condición: `if ( user.es_proveedor and producto.get("id_proveedor") != user.id_proveedor ):`.

```python
        if (
            user.es_proveedor
            and
            producto.get("id_proveedor")
            != user.id_proveedor
        ):

            raise _prohibido(
                "El producto no es de este proveedor"
            )

```

### COND-0221: AccesoService.verificar_proveedor

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:564. Condición: `if ( not proveedor or proveedor.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not proveedor
            or
            proveedor.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Proveedor no encontrado"
            )

```

### COND-0222: AccesoService.verificar_operario

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:594. Condición: `if ( not operario or operario.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not operario
            or
            operario.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Operario no encontrado"
            )

```

### COND-0223: AccesoService.verificar_orden

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:629. Condición: `if ( not orden or orden.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not orden
            or
            orden.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Orden de reposición no encontrada"
            )

```

### COND-0224: AccesoService.verificar_orden

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:640. Condición: `if ( user.es_operario and orden.get("id_almacen") != user.id_almacen ):`.

```python
        if (
            user.es_operario
            and
            orden.get("id_almacen")
            != user.id_almacen
        ):

            raise _prohibido(
                "La orden no es de su almacén"
            )

```

### COND-0225: AccesoService.verificar_orden

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:651. Condición: `if ( user.es_proveedor and ( orden.get("id_proveedor") != user.id_proveedor or orden.get("estado") not in ( "ENVIADA", "PARCIAL", "RECIBIDA" ) ) ):`.

```python
        if (
            user.es_proveedor
            and
            (
                orden.get("id_proveedor")
                != user.id_proveedor
                or
                orden.get("estado") not in (
                    "ENVIADA",
                    "PARCIAL",
                    "RECIBIDA"
                )
            )
        ):

            raise _prohibido(
                "La orden no está enviada "
                "a este proveedor"
            )

```

### COND-0226: AccesoService.verificar_recepcion

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:694. Condición: `if not recepcion:`.

```python
        if not recepcion:

            raise _no_encontrado(
                "Recepción no encontrada"
            )

```

### COND-0227: AccesoService.verificar_recepcion

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:709. Condición: `if ( not orden or orden.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not orden
            or
            orden.get("id_empresa")
            != user.id_empresa
        ):

            raise _no_encontrado(
                "Recepción no encontrada"
            )

```

### COND-0228: AccesoService.verificar_recepcion

Estado IMPLEMENTADO; autorización. Evidencia app/services/acceso_service.py:720. Condición: `if ( user.es_proveedor or ( user.es_operario and orden.get("id_almacen") != user.id_almacen ) ):`.

```python
        if (
            user.es_proveedor
            or
            (
                user.es_operario
                and
                orden.get("id_almacen")
                != user.id_almacen
            )
        ):

            raise _prohibido(
                "No tiene acceso a esta recepción"
            )

```

### COND-0229: AlertaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/alerta_service.py:42. Condición: `if alerta_existente:`.

```python
        if alerta_existente:

            datos_actualizados = {
                "nivel_riesgo":
                    data.nivel_riesgo.value,

                "titulo":
                    data.titulo,

                "mensaje":
                    data.mensaje,

                "stock_actual":
                    data.stock_actual,

                "dias_cobertura":
                    data.dias_cobertura,

                "stock_seguridad":
                    data.stock_seguridad,

                "punto_reposicion":
                    data.punto_reposicion,

                "forecast_7d":
                    data.forecast_7d,

                "fecha_actualizacion":
                    ahora
            }

            return (
                await self.repository.actualizar(
                    alerta_existente[
                        "id_alerta"
                    ],
                    datos_actualizados
                )
            )

```

### COND-0230: AlertaService.obtener

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/alerta_service.py:153. Condición: `if alerta is None:`.

```python
        if alerta is None:
            raise HTTPException(
                status_code=404,
                detail="Alerta no encontrada"
            )

```

### COND-0231: AlertaService.cambiar_estado

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/alerta_service.py:244. Condición: `if ( data.estado == EstadoAlerta.RESUELTA ):`.

```python
        if (
            data.estado
            == EstadoAlerta.RESUELTA
        ):
            datos[
                "fecha_resolucion"
            ] = ahora

```

### COND-0232: AlertaService.cambiar_estado

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/alerta_service.py:252. Condición: `elif ( alerta.get( "fecha_resolucion" ) is not None ):`.

```python
        elif (
            alerta.get(
                "fecha_resolucion"
            )
            is not None
        ):
            datos[
                "fecha_resolucion"
            ] = None

```

### COND-0233: AlertaService.resolver_activa_por_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/alerta_service.py:281. Condición: `if not alerta:`.

```python
        if not alerta:
            return None

```

### COND-0234: AlmacenService.convertir_decimal

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/almacen_service.py:55. Condición: `if ( campo in data and isinstance( data[campo], Decimal ) ):`.

```python
            if (
                campo in data
                and
                isinstance(
                    data[campo],
                    Decimal
                )
            ):

                data[campo] = float(
                    data[campo]
                )

```

### COND-0235: AlmacenService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/almacen_service.py:90. Condición: `if not empresa:`.

```python
        if not empresa:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "La empresa especificada "
                    "no existe"
                )
            )

```

### COND-0236: AlmacenService.obtener_por_id

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/almacen_service.py:165. Condición: `if not almacen:`.

```python
        if not almacen:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Almacén no encontrado"
                )
            )

```

### COND-0237: AlmacenService.obtener_por_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/almacen_service.py:194. Condición: `if not empresa:`.

```python
        if not empresa:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Empresa no encontrada"
                )
            )

```

### COND-0238: AlmacenService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/almacen_service.py:228. Condición: `if not almacen_actual:`.

```python
        if not almacen_actual:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Almacén no encontrado"
                )
            )

```

### COND-0239: AlmacenService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/almacen_service.py:245. Condición: `if not update_data:`.

```python
        if not update_data:

            return almacen_actual

```

### COND-0240: AlmacenService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/almacen_service.py:262. Condición: `if not updated:`.

```python
        if not updated:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Almacén no encontrado"
                )
            )

```

### COND-0241: AlmacenService.eliminar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/almacen_service.py:291. Condición: `if not almacen:`.

```python
        if not almacen:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Almacén no encontrado"
                )
            )

```

### COND-0242: AlmacenService.eliminar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/almacen_service.py:308. Condición: `if not deleted:`.

```python
        if not deleted:

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "No se pudo eliminar "
                    "el almacén"
                )
            )

```

### COND-0243: módulo._empresa_de

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:89. Condición: `if not empresa:`.

```python
    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "La empresa de la cuenta no existe"
            )
        )

```

### COND-0244: módulo.login

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:132. Condición: `if empresa:`.

```python
    if empresa:

        if not _password_ok(
            data.password,
            empresa,
            "password"
        ):

            raise _credenciales_invalidas()

        return {

            "access_token":
                create_access_token(
                    sub=empresa["id_empresa"],
                    rol=ROL_EMPRESA,
                    id_empresa=empresa["id_empresa"]
                ),

            "token_type":
                "bearer",

            "rol":
                ROL_EMPRESA,

            "empresa":
                sanitize_empresa(
                    empresa
                ),

            "operario":
                None,

            "proveedor":
                None,

            "debe_cambiar_password":
                False
        }

    # --------------------------------------------------------
    # OPERARIO
    # --------------------------------------------------------

```

### COND-0245: módulo.login

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:134. Condición: `if not _password_ok( data.password, empresa, "password" ):`.

```python
        if not _password_ok(
            data.password,
            empresa,
            "password"
        ):

            raise _credenciales_invalidas()

```

### COND-0246: módulo.login

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:182. Condición: `if operario:`.

```python
    if operario:

        if not _password_ok(
            data.password,
            operario,
            "password_hash"
        ):

            raise _credenciales_invalidas()

        if (
            str(operario.get("estado", "")).upper()
            != "ACTIVO"
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail="Operario inactivo"
            )

        operario = sanitizar_cuenta(
            operario
        )

        return {

            "access_token":
                create_access_token(
                    sub=operario["id_operario"],
                    rol=ROL_OPERARIO,
                    id_empresa=operario["id_empresa"],
                    id_almacen=operario.get(
                        "id_almacen"
                    )
                ),

            "token_type":
                "bearer",

            "rol":
                ROL_OPERARIO,

            "empresa":
                await _empresa_de(
                    operario["id_empresa"]
                ),

            "operario":
                operario,

            "proveedor":
                None,

            "debe_cambiar_password":
                operario[
                    "debe_cambiar_password"
                ]
        }

    # --------------------------------------------------------
    # PROVEEDOR
    # --------------------------------------------------------

```

### COND-0247: módulo.login

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:184. Condición: `if not _password_ok( data.password, operario, "password_hash" ):`.

```python
        if not _password_ok(
            data.password,
            operario,
            "password_hash"
        ):

            raise _credenciales_invalidas()

```

### COND-0248: módulo.login

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:192. Condición: `if ( str(operario.get("estado", "")).upper() != "ACTIVO" ):`.

```python
        if (
            str(operario.get("estado", "")).upper()
            != "ACTIVO"
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail="Operario inactivo"
            )

```

### COND-0249: módulo.login

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:254. Condición: `if not _password_ok( data.password, proveedor, "password_hash" ):`.

```python
    if not _password_ok(
        data.password,
        proveedor,
        "password_hash"
    ):

        raise _credenciales_invalidas()

```

### COND-0250: módulo.login

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:262. Condición: `if ( str(proveedor.get("estado", "")).upper() != "ACTIVO" ):`.

```python
    if (
        str(proveedor.get("estado", "")).upper()
        != "ACTIVO"
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Proveedor inactivo"
        )

```

### COND-0251: módulo.me

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:327. Condición: `if user.es_operario:`.

```python
    if user.es_operario:

        operario = sanitizar_cuenta(
            await OperarioRepository.obtener_por_id(
                user.id_operario
            )
        )

```

### COND-0252: módulo.me

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:335. Condición: `if user.es_proveedor:`.

```python
    if user.es_proveedor:

        proveedor = sanitizar_cuenta(
            await ProveedorRepository().obtener_por_id(
                user.id_proveedor
            )
        )

```

### COND-0253: módulo.cambiar_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:375. Condición: `if user.es_operario:`.

```python
    if user.es_operario:

        cuenta = await OperarioRepository.obtener_por_id(
            user.id_operario
        )

```

### COND-0254: módulo.cambiar_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:381. Condición: `elif user.es_proveedor:`.

```python
    elif user.es_proveedor:

        cuenta = await ProveedorRepository().obtener_por_id(
            user.id_proveedor
        )

```

### COND-0255: módulo.cambiar_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:399. Condición: `if not _password_ok( data.password_actual, cuenta, "password_hash" ):`.

```python
    if not _password_ok(
        data.password_actual,
        cuenta,
        "password_hash"
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "La contraseña actual "
                "es incorrecta"
            )
        )

```

### COND-0256: módulo.cambiar_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:415. Condición: `if ( data.password_actual == data.password_nueva ):`.

```python
    if (
        data.password_actual
        ==
        data.password_nueva
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "La nueva contraseña debe "
                "ser diferente a la actual"
            )
        )

```

### COND-0257: módulo.cambiar_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/auth_service.py:442. Condición: `if user.es_operario:`.

```python
    if user.es_operario:

        await OperarioRepository.actualizar(
            user.id_operario,
            cambios
        )

```

### COND-0258: módulo.sanitizar_cuenta

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/cuenta_service.py:47. Condición: `if not documento:`.

```python
    if not documento:
        return documento

```

### COND-0259: módulo.validar_correo_disponible

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/cuenta_service.py:144. Condición: `if ocupado:`.

```python
    if ocupado:

        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,
            detail=
                "El correo ya está registrado"
        )

```

### COND-0260: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:122. Condición: `if not recepcion:`.

```python
        if not recepcion:

            raise HTTPException(
                status_code=404,
                detail="Recepción no encontrada"
            )

        # ====================================================
        # 2. VALIDAR DETALLE DE REPOSICION
        # ====================================================

```

### COND-0261: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:140. Condición: `if not detalle_orden:`.

```python
        if not detalle_orden:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Detalle de reposición "
                    "no encontrado"
                )
            )

        # ====================================================
        # 3. VALIDAR QUE PERTENEZCA A LA MISMA ORDEN
        # ====================================================

```

### COND-0262: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:154. Condición: `if ( detalle_orden[ "id_orden_reposicion" ] != recepcion[ "id_orden_reposicion" ] ):`.

```python
        if (
            detalle_orden[
                "id_orden_reposicion"
            ]
            != recepcion[
                "id_orden_reposicion"
            ]
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "El detalle de reposición "
                    "no pertenece a la orden "
                    "de esta recepción"
                )
            )

        # ====================================================
        # 4. VALIDAR INVENTARIO
        # ====================================================

```

### COND-0263: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:183. Condición: `if not inventario:`.

```python
        if not inventario:

            raise HTTPException(
                status_code=404,
                detail="Inventario no encontrado"
            )

```

### COND-0264: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:194. Condición: `if not rack:`.

```python
        if not rack:
            raise HTTPException(
                status_code=404,
                detail="Rack del inventario no encontrado"
            )

```

### COND-0265: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:204. Condición: `if not zona:`.

```python
        if not zona:
            raise HTTPException(
                status_code=404,
                detail="Zona del rack no encontrada"
            )

```

### COND-0266: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:215. Condición: `if not orden or id_almacen_zona != orden.get( "id_almacen" ):`.

```python
        if not orden or id_almacen_zona != orden.get(
            "id_almacen"
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "El rack del inventario no pertenece "
                    "al almacén de la orden"
                )
            )

        # ====================================================
        # 4.1 OPERARIO: SOLO ORDENES DE SU ALMACEN
        # ====================================================

```

### COND-0267: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:230. Condición: `if ( user is not None and orden.get("id_almacen") != user.id_almacen ):`.

```python
        if (
            user is not None
            and orden.get("id_almacen") != user.id_almacen
        ):
            raise HTTPException(
                status_code=403,
                detail="La orden no es de su almacén"
            )

        # ====================================================
        # 5. VALIDAR PRODUCTO
        #
        # El inventario seleccionado debe corresponder
        # exactamente al producto pedido.
        # ====================================================

```

### COND-0268: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:246. Condición: `if ( inventario["id_producto"] != detalle_orden["id_producto"] ):`.

```python
        if (
            inventario["id_producto"]
            != detalle_orden["id_producto"]
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "El inventario seleccionado "
                    "no corresponde al producto "
                    "de la orden"
                )
            )

        # ====================================================
        # 6. OBTENER RECEPCIONES ANTERIORES
        #
        # Esto permite recepciones parciales.
        # ====================================================

```

### COND-0269: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:285. Condición: `if data.estado_recepcion.value == "EN_EVALUACION":`.

```python
        if data.estado_recepcion.value == "EN_EVALUACION":
            cantidad_aceptada = 0
```

### COND-0270: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:302. Condición: `if ( cantidad_total_aceptada > detalle_orden[ "cantidad_solicitada" ] ):`.

```python
        if (
            cantidad_total_aceptada
            > detalle_orden[
                "cantidad_solicitada"
            ]
        ):

            cantidad_pendiente = (
                detalle_orden[
                    "cantidad_solicitada"
                ]
                - cantidad_aceptada_anterior
            )

            raise HTTPException(
                status_code=409,
                detail=(
                    "La cantidad aceptada supera "
                    "la cantidad pendiente de la orden. "
                    f"Pendiente: {cantidad_pendiente}"
                )
            )

        # ====================================================
        # 8.1 RACK DISPONIBLE, KG LIBRES Y TEMPERATURA (409)
        # ====================================================

```

### COND-0271: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:329. Condición: `if cantidad_aceptada > 0:`.

```python
        if cantidad_aceptada > 0:

            await RackService.validar_asignacion(
                rack,
                await ProductoRepository.obtener_por_id(
                    inventario["id_producto"]
                ) or {},
                cantidad_aceptada
            )

        # ====================================================
        # 9. CREAR DETALLE DE RECEPCION
        # ====================================================

```

### COND-0272: DetalleRecepcionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:387. Condición: `if cantidad_aceptada > 0:`.

```python
        if cantidad_aceptada > 0:

            movimiento_data = MovimientoCreate(

                id_inventario=
                    data.id_inventario,

                id_operario=
                    recepcion[
                        "id_operario"
                    ],

                id_detalle_recepcion=
                    detalle_recepcion[
                        "id_detalle_recepcion"
                    ],

                tipo_movimiento=
                    TipoMovimiento.ENTRADA,

                motivo_movimiento=
                    MotivoMovimiento.RECEPCION,

                cantidad=
                    cantidad_aceptada,

                observacion=(
                    "Entrada automática por "
                    "recepción de mercadería "
                    f"{id_recepcion}"
                )
            )

            movimiento = (
                await self.movimiento_service
                .crear_movimiento(
                    movimiento_data
                )
            )

            # ================================================
            # GUARDAR FK DEL MOVIMIENTO GENERADO
            # ================================================

            detalle_recepcion = (
                await self.repository
                .actualizar_movimiento(
                    detalle_recepcion[
                        "id_detalle_recepcion"
                    ],
                    movimiento[
                        "id_movimiento"
                    ]
                )
            )

        # ====================================================
        # 11. ACTUALIZAR ESTADO DE ORDEN
        # ====================================================

```

### COND-0273: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:463. Condición: `if user is not None and user.es_operario:`.

```python
        if user is not None and user.es_operario:
            data.id_operario = user.id_operario

```

### COND-0274: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:466. Condición: `if not data.id_operario:`.

```python
        if not data.id_operario:
            raise HTTPException(
                status_code=422,
                detail="Debe indicar id_operario"
            )

```

### COND-0275: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:476. Condición: `if not detalle:`.

```python
        if not detalle:
            raise HTTPException(
                status_code=404,
                detail="Detalle de recepción no encontrado"
            )

```

### COND-0276: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:482. Condición: `if detalle.get("id_movimiento"):`.

```python
        if detalle.get("id_movimiento"):
            return detalle

```

### COND-0277: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:492. Condición: `if movimiento_existente:`.

```python
        if movimiento_existente:
            return await self.repository.actualizar_movimiento(
                id_detalle_recepcion,
                movimiento_existente["id_movimiento"]
            )

```

### COND-0278: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:498. Condición: `if detalle.get("estado_recepcion") != "EN_EVALUACION":`.

```python
        if detalle.get("estado_recepcion") != "EN_EVALUACION":
            raise HTTPException(
                status_code=409,
                detail="El detalle ya fue resuelto"
            )

```

### COND-0279: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:508. Condición: `if not recepcion:`.

```python
        if not recepcion:
            raise HTTPException(
                status_code=404,
                detail="Recepción no encontrada"
            )

```

### COND-0280: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:522. Condición: `if not inventario:`.

```python
        if not inventario:
            raise HTTPException(
                status_code=404,
                detail="Inventario no encontrado"
            )

```

### COND-0281: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:538. Condición: `if not rack or not zona or not orden or zona.get( "id_almacen" ) != orden.get("id_almacen"):`.

```python
        if not rack or not zona or not orden or zona.get(
            "id_almacen"
        ) != orden.get("id_almacen"):
            raise HTTPException(
                status_code=400,
                detail="El rack no pertenece al almacén de la orden"
            )

```

### COND-0282: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:558. Condición: `if aceptada < 0 or rechazada < 0 or aceptada + rechazada != recibida:`.

```python
        if aceptada < 0 or rechazada < 0 or aceptada + rechazada != recibida:
            raise HTTPException(
                status_code=400,
                detail="Las cantidades aceptada y rechazada no coinciden con la recibida"
            )

```

### COND-0283: DetalleRecepcionService.resolver_evaluacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:568. Condición: `if aceptada <= 0:`.

```python
        if aceptada <= 0:
            actualizado = await self.repository.actualizar(
                id_detalle_recepcion,
                {
                    "id_inventario": id_inventario,
                    "id_rack": inventario["id_rack"],
                    "cantidad_aceptada": 0,
                    "cantidad_rechazada": rechazada,
                    "estado_recepcion": data.estado_recepcion.value,
                    "comentario_resolucion": data.comentario_resolucion,
                    "id_operario_resolucion": data.id_operario,
                    "fecha_resolucion": datetime.now(timezone.utc),
                    "ubicado": False
                }
            )
            await self._recalcular_estado_orden(
                recepcion["id_orden_reposicion"]
            )
            riesgo_despues = await self._obtener_riesgo(
                id_inventario
            )
            return await self._notificar_cierre(
                recepcion,
                actualizado,
                riesgo_antes,
                riesgo_despues
            )

        # Rack DISPONIBLE, kg libres y temperatura (409)
```

### COND-0284: DetalleRecepcionService._recalcular_estado_orden

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:708. Condición: `if not detalles_orden:`.

```python
        if not detalles_orden:
            return

        # ====================================================
        # TOTAL SOLICITADO
        # ====================================================

```

### COND-0285: DetalleRecepcionService._recalcular_estado_orden

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:751. Condición: `if ( total_aceptado >= total_solicitado ):`.

```python
        if (
            total_aceptado
            >= total_solicitado
        ):

            nuevo_estado = "RECIBIDA"

```

### COND-0286: DetalleRecepcionService._recalcular_estado_orden

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:758. Condición: `elif total_aceptado > 0:`.

```python
        elif total_aceptado > 0:

            nuevo_estado = "PARCIAL"

```

### COND-0287: DetalleRecepcionService.obtener_por_id

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:791. Condición: `if not detalle:`.

```python
        if not detalle:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Detalle de recepción "
                    "no encontrado"
                )
            )

```

### COND-0288: DetalleRecepcionService.obtener_por_recepcion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_recepcion_service.py:819. Condición: `if not recepcion:`.

```python
        if not recepcion:

            raise HTTPException(
                status_code=404,
                detail="Recepción no encontrada"
            )

```

### COND-0289: DetalleReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_reposicion_service.py:35. Condición: `if not orden:`.

```python
        if not orden:
            raise HTTPException(
                status_code=404,
                detail="Orden no encontrada"
            )

```

### COND-0290: DetalleReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_reposicion_service.py:41. Condición: `if orden["estado"] not in ("PENDIENTE", "OBSERVADA"):`.

```python
        if orden["estado"] not in ("PENDIENTE", "OBSERVADA"):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo pueden agregarse productos "
                    "a una orden pendiente"
                )
            )

```

### COND-0291: DetalleReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_reposicion_service.py:61. Condición: `if not producto:`.

```python
        if not producto:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

```

### COND-0292: DetalleReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_reposicion_service.py:67. Condición: `if ( producto.get("id_empresa") and producto.get("id_empresa") != orden["id_empresa"] ):`.

```python
        if (
            producto.get("id_empresa")
            and producto.get("id_empresa")
            != orden["id_empresa"]
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "El producto no pertenece "
                    "a la empresa de la orden"
                )
            )

```

### COND-0293: DetalleReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_reposicion_service.py:87. Condición: `if existente:`.

```python
        if existente:
            raise HTTPException(
                status_code=409,
                detail=(
                    "El producto ya existe "
                    "en esta orden"
                )
            )

```

### COND-0294: DetalleReposicionService.obtener_por_id

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_reposicion_service.py:114. Condición: `if not detalle:`.

```python
        if not detalle:
            raise HTTPException(
                status_code=404,
                detail="Detalle no encontrado"
            )

```

### COND-0295: DetalleReposicionService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_reposicion_service.py:134. Condición: `if orden["estado"] not in ("PENDIENTE", "OBSERVADA"):`.

```python
        if orden["estado"] not in ("PENDIENTE", "OBSERVADA"):
            raise HTTPException(
                status_code=409,
                detail=(
                    "El detalle ya no puede modificarse"
                )
            )

```

### COND-0296: DetalleReposicionService.eliminar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/detalle_reposicion_service.py:159. Condición: `if orden["estado"] not in ("PENDIENTE", "OBSERVADA"):`.

```python
        if orden["estado"] not in ("PENDIENTE", "OBSERVADA"):
            raise HTTPException(
                status_code=409,
                detail="El detalle ya no puede eliminarse"
            )

```

### COND-0297: EmailVerificationService._as_utc

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:48. Condición: `if not isinstance(value, datetime):`.

```python
        if not isinstance(value, datetime):
            return None
```

### COND-0298: EmailVerificationService._as_utc

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:50. Condición: `if value.tzinfo is None:`.

```python
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
```

### COND-0299: EmailVerificationService._get_entity_record

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:56. Condición: `if not collection_name:`.

```python
        if not collection_name:
            return None
```

### COND-0300: EmailVerificationService._upsert_entity_email_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:80. Condición: `if entity is None:`.

```python
        if entity is None:
            return None

```

### COND-0301: EmailVerificationService._upsert_entity_email_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:84. Condición: `if not collection_name:`.

```python
        if not collection_name:
            return None

```

### COND-0302: EmailVerificationService._upsert_entity_email_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:92. Condición: `if verified:`.

```python
        if verified:
            payload["fecha_verificacion_correo"] = datetime.now(timezone.utc)
```

### COND-0303: EmailVerificationService.request_entity_verification

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:127. Condición: `if not entity:`.

```python
        if not entity:
            return {"status": "ERROR", "reason": "Entidad no encontrada"}

```

### COND-0304: EmailVerificationService.verify_entity_code

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:150. Condición: `if not entity:`.

```python
        if not entity:
            return {
                "verified": False,
                "status": "NOT_FOUND",
            }

```

### COND-0305: EmailVerificationService.request_verification

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:182. Condición: `if not normalized_email:`.

```python
        if not normalized_email:
            return {"status": "ERROR", "reason": "Correo requerido"}

```

### COND-0306: EmailVerificationService.request_verification

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:190. Condición: `if not entity:`.

```python
        if not entity:
            return {"status": "ERROR", "reason": "Entidad no encontrada"}

```

### COND-0307: EmailVerificationService.request_verification

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:203. Condición: `if existing:`.

```python
        if existing:
            now = datetime.now(timezone.utc)
            expires_at = self._as_utc(existing.get("expires_at"))
            if expires_at is not None and expires_at > now:
                cooldown_until = self._as_utc(existing.get("cooldown_until"))
                if cooldown_until is not None and cooldown_until > now:
                    return {
                        "status": "COOLDOWN",
                        "remaining_seconds": max(
                            0,
                            int((cooldown_until - now).total_seconds()),
                        ),
                        "email": normalized_email,
                    }

```

### COND-0308: EmailVerificationService.request_verification

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:206. Condición: `if expires_at is not None and expires_at > now:`.

```python
            if expires_at is not None and expires_at > now:
                cooldown_until = self._as_utc(existing.get("cooldown_until"))
                if cooldown_until is not None and cooldown_until > now:
                    return {
                        "status": "COOLDOWN",
                        "remaining_seconds": max(
                            0,
                            int((cooldown_until - now).total_seconds()),
                        ),
                        "email": normalized_email,
                    }

```

### COND-0309: EmailVerificationService.request_verification

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:208. Condición: `if cooldown_until is not None and cooldown_until > now:`.

```python
                if cooldown_until is not None and cooldown_until > now:
                    return {
                        "status": "COOLDOWN",
                        "remaining_seconds": max(
                            0,
                            int((cooldown_until - now).total_seconds()),
                        ),
                        "email": normalized_email,
                    }

```

### COND-0310: EmailVerificationService.verify_code

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:295. Condición: `if not record:`.

```python
        if not record:
            return {"verified": False, "status": "NOT_FOUND"}

```

### COND-0311: EmailVerificationService.verify_code

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:298. Condición: `if record.get("used"):`.

```python
        if record.get("used"):
            return {"verified": False, "status": "REUSED"}

```

### COND-0312: EmailVerificationService.verify_code

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:303. Condición: `if expires_at is not None and expires_at < now:`.

```python
        if expires_at is not None and expires_at < now:
            await collection.update_one(
                {
                    "entity_type": entity_type.lower(),
                    "entity_id": entity_id,
                    "email": normalized_email,
                },
                {"$set": {"used": True, "status": "EXPIRED", "updated_at": now}},
            )
            return {"verified": False, "status": "EXPIRED"}

```

### COND-0313: EmailVerificationService.verify_code

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:316. Condición: `if attempts >= max_attempts:`.

```python
        if attempts >= max_attempts:
            await collection.update_one(
                {
                    "entity_type": entity_type.lower(),
                    "entity_id": entity_id,
                    "email": normalized_email,
                },
                {"$set": {"used": True, "status": "LOCKED", "updated_at": now}},
            )
            return {
                "verified": False,
                "status": "MAX_ATTEMPTS",
                "attempts": attempts,
            }

```

### COND-0314: EmailVerificationService.verify_code

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:331. Condición: `if record.get("code_hash") != self.hash_code(str(code)):`.

```python
        if record.get("code_hash") != self.hash_code(str(code)):
            attempts += 1
            await collection.update_one(
                {
                    "entity_type": entity_type.lower(),
                    "entity_id": entity_id,
                    "email": normalized_email,
                },
                {
                    "$set": {
                        "attempts": attempts,
                        "status": "INVALID_CODE",
                        "updated_at": now,
                    }
                },
            )
            return {
                "verified": False,
                "status": "INVALID_CODE",
                "attempts": attempts,
                "remaining_attempts": max_attempts - attempts,
            }

```

### COND-0315: EmailVerificationService.invalidate_on_email_change

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:385. Condición: `if not old_email_norm or old_email_norm == new_email_norm:`.

```python
        if not old_email_norm or old_email_norm == new_email_norm:
            return {"correo_verificado": False, "correo": new_email_norm}

```

### COND-0316: EmailVerificationService.invalidate_on_email_change

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:389. Condición: `if not collection_name:`.

```python
        if not collection_name:
            return {"correo_verificado": False, "correo": new_email_norm}

```

### COND-0317: EmailVerificationService.invalidate_on_email_change

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:404. Condición: `if record is None:`.

```python
        if record is None:
            return {"correo_verificado": False, "correo": new_email_norm}

```

### COND-0318: EmailVerificationService.invalidate_on_email_change

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:442. Condición: `if matched == 0:`.

```python
        if matched == 0:
            return {"correo_verificado": False, "correo": new_email_norm}

```

### COND-0319: EmailVerificationService._send_email

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:458. Condición: `if settings.email_enabled and all( ( settings.smtp_host, settings.smtp_user, settings.smtp_password, settings.smtp_from or settings.smtp_user, ) ):`.

```python
        if settings.email_enabled and all(
            (
                settings.smtp_host,
                settings.smtp_user,
                settings.smtp_password,
                settings.smtp_from or settings.smtp_user,
            )
        ):
            from email.message import EmailMessage
            import smtplib

            message = EmailMessage()
            message["From"] = settings.smtp_from or settings.smtp_user
            message["To"] = recipient
            message["Subject"] = subject
            message.set_content(body)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(message)
```

### COND-0320: EmailVerificationService._send_email

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/email_verification_service.py:475. Condición: `if settings.smtp_use_tls:`.

```python
                if settings.smtp_use_tls:
                    server.starttls()
```

### COND-0321: módulo.decode_access_token

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:158. Condición: `if ( not id_empresa or token_type != "empresa" ):`.

```python
        if (
            not id_empresa
            or
            token_type != "empresa"
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_401_UNAUTHORIZED
                ),
                detail="Token inválido",
                headers={
                    "WWW-Authenticate":
                        "Bearer"
                }
            )

```

### COND-0322: módulo.register_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:230. Condición: `if existing_email:`.

```python
    if existing_email:

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Ya existe una empresa "
                "registrada con ese correo"
            )
        )

    # Único entre empresas, operarios y proveedores
```

### COND-0323: módulo.register_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:254. Condición: `if existing_ruc:`.

```python
    if existing_ruc:

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Ya existe una empresa "
                "registrada con ese RUC"
            )
        )

```

### COND-0324: módulo.login_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:343. Condición: `if not empresa:`.

```python
    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Correo o contraseña incorrectos"
            )
        )

```

### COND-0325: módulo.login_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:360. Condición: `if ( not stored_password or not verify_password( data.password, stored_password ) ):`.

```python
    if (
        not stored_password
        or
        not verify_password(
            data.password,
            stored_password
        )
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Correo o contraseña incorrectos"
            )
        )

```

### COND-0326: módulo.get_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:414. Condición: `if not empresa:`.

```python
    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

```

### COND-0327: módulo.update_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:446. Condición: `if not current:`.

```python
    if not current:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

```

### COND-0328: módulo.update_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:463. Condición: `if not update_data:`.

```python
    if not update_data:

        return sanitize_empresa(
            current
        )

    # ========================================================
    # CORREO
    # ========================================================

```

### COND-0329: módulo.update_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:473. Condición: `if "correo" in update_data:`.

```python
    if "correo" in update_data:

        correo = (
            str(
                update_data[
                    "correo"
                ]
            )
            .lower()
            .strip()
        )

        existing = (
            await empresa_repository
            .find_by_email(
                correo
            )
        )

        if (
            existing
            and
            existing[
                "id_empresa"
            ]
            !=
            id_empresa
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "El correo ya está registrado"
                )
            )

        await validar_correo_disponible(
            correo,
            id_empresa
        )

        if current.get("correo") and current.get("correo").lower() != correo:
            update_data["correo_verificado"] = False
            update_data["fecha_verificacion_correo"] = None

        update_data[
            "correo"
        ] = correo


    # ========================================================
    # RUC
    # ========================================================

```

### COND-0330: módulo.update_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:492. Condición: `if ( existing and existing[ "id_empresa" ] != id_empresa ):`.

```python
        if (
            existing
            and
            existing[
                "id_empresa"
            ]
            !=
            id_empresa
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "El correo ya está registrado"
                )
            )

```

### COND-0331: módulo.update_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:516. Condición: `if current.get("correo") and current.get("correo").lower() != correo:`.

```python
        if current.get("correo") and current.get("correo").lower() != correo:
            update_data["correo_verificado"] = False
            update_data["fecha_verificacion_correo"] = None

```

### COND-0332: módulo.update_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:529. Condición: `if "ruc" in update_data:`.

```python
    if "ruc" in update_data:

        ruc = (
            update_data[
                "ruc"
            ]
            .strip()
        )

        existing = (
            await empresa_repository
            .find_by_ruc(
                ruc
            )
        )

        if (
            existing
            and
            existing[
                "id_empresa"
            ]
            !=
            id_empresa
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "El RUC ya está registrado"
                )
            )

        update_data[
            "ruc"
        ] = ruc


    # ========================================================
    # NORMALIZAR TEXTOS
    # ========================================================

```

### COND-0333: módulo.update_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:545. Condición: `if ( existing and existing[ "id_empresa" ] != id_empresa ):`.

```python
        if (
            existing
            and
            existing[
                "id_empresa"
            ]
            !=
            id_empresa
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "El RUC ya está registrado"
                )
            )

```

### COND-0334: módulo.update_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:579. Condición: `if ( field in update_data and update_data[field] ):`.

```python
        if (
            field in update_data
            and
            update_data[field]
        ):

            update_data[
                field
            ] = (
                update_data[
                    field
                ]
                .strip()
            )


```

### COND-0335: módulo.update_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:603. Condición: `if not updated:`.

```python
    if not updated:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

```

### COND-0336: módulo.change_empresa_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:635. Condición: `if not empresa:`.

```python
    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

```

### COND-0337: módulo.change_empresa_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:652. Condición: `if ( not current_hash or not verify_password( data.password_actual, current_hash ) ):`.

```python
    if (
        not current_hash
        or
        not verify_password(
            data.password_actual,
            current_hash
        )
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "La contraseña actual "
                "es incorrecta"
            )
        )

```

### COND-0338: módulo.change_empresa_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:671. Condición: `if ( data.password_actual == data.password_nueva ):`.

```python
    if (
        data.password_actual
        ==
        data.password_nueva
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "La nueva contraseña debe "
                "ser diferente a la actual"
            )
        )

```

### COND-0339: módulo.change_empresa_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:699. Condición: `if not success:`.

```python
    if not success:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "No se pudo actualizar "
                "la contraseña"
            )
        )

```

### COND-0340: módulo.delete_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:733. Condición: `if not empresa:`.

```python
    if not empresa:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Empresa no encontrada"
            )
        )

```

### COND-0341: módulo.delete_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:750. Condición: `if ( not stored_password or not verify_password( data.password, stored_password ) ):`.

```python
    if (
        not stored_password
        or
        not verify_password(
            data.password,
            stored_password
        )
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Contraseña incorrecta"
            )
        )

```

### COND-0342: módulo.delete_empresa_profile

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/empresa_service.py:775. Condición: `if not deleted:`.

```python
    if not deleted:

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "No se pudo eliminar "
                "la empresa"
            )
        )

```

### COND-0343: InventarioService.crear_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:61. Condición: `if not producto:`.

```python
        if not producto:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )


        # --------------------------------------------------------
        # VALIDAR RACK
        # --------------------------------------------------------

```

### COND-0344: InventarioService.crear_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:81. Condición: `if not rack:`.

```python
        if not rack:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Rack no encontrado"
            )


        # --------------------------------------------------------
        # VALIDAR STOCK MIN / MAX
        # --------------------------------------------------------

```

### COND-0345: InventarioService.crear_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:95. Condición: `if ( data.stock_minimo > data.stock_maximo ):`.

```python
        if (
            data.stock_minimo
            >
            data.stock_maximo
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "El stock mínimo no puede ser "
                    "mayor que el stock máximo"
                )
            )


        # --------------------------------------------------------
        # EVITAR DUPLICADOS
        # producto + rack
        # --------------------------------------------------------

```

### COND-0346: InventarioService.crear_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:125. Condición: `if ( inventario.get( "id_rack" ) == data.id_rack ):`.

```python
            if (
                inventario.get(
                    "id_rack"
                )
                ==
                data.id_rack
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Ya existe inventario para "
                        "este producto en este rack"
                    )
                )


        # --------------------------------------------------------
        # STOCK INICIAL <= STOCK MAXIMO (409)
        # --------------------------------------------------------

```

### COND-0347: InventarioService.crear_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:148. Condición: `if data.stock_actual > data.stock_maximo:`.

```python
        if data.stock_actual > data.stock_maximo:

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "El stock inicial no puede superar "
                    "el stock máximo"
                )
            )


        # --------------------------------------------------------
        # EL PRODUCTO DEBE CABER EN EL RACK (409)
        #
        # rack DISPONIBLE, kg libres y temperatura.
        # --------------------------------------------------------

```

### COND-0348: InventarioService.obtener_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:236. Condición: `if not inventario:`.

```python
        if not inventario:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Inventario no encontrado"
            )

```

### COND-0349: InventarioService.obtener_por_producto

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:263. Condición: `if not producto:`.

```python
        if not producto:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )

```

### COND-0350: InventarioService.obtener_por_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:294. Condición: `if not rack:`.

```python
        if not rack:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Rack no encontrado"
            )

```

### COND-0351: InventarioService.actualizar_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:414. Condición: `if not inventario_actual:`.

```python
        if not inventario_actual:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Inventario no encontrado"
            )


```

### COND-0352: InventarioService.actualizar_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:433. Condición: `if not update_data:`.

```python
        if not update_data:

            return inventario_actual


```

### COND-0353: InventarioService.actualizar_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:452. Condición: `if ( despues["stock_minimo"] > despues["stock_maximo"] ):`.

```python
        if (
            despues["stock_minimo"]
            >
            despues["stock_maximo"]
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "El stock mínimo no puede ser "
                    "mayor que el stock máximo"
                )
            )


```

### COND-0354: InventarioService.actualizar_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:476. Condición: `if despues != antes:`.

```python
        if despues != antes:

            await self.repository.registrar_historial(
                id_inventario,
                id_operario,
                "EDITAR_LIMITES",
                antes,
                despues
            )

```

### COND-0355: InventarioService.eliminar_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:540. Condición: `if not inventario:`.

```python
        if not inventario:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Inventario no encontrado"
            )


```

### COND-0356: InventarioService.eliminar_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:550. Condición: `if ( inventario.get( "stock_actual", 0 ) > 0 ):`.

```python
        if (
            inventario.get(
                "stock_actual",
                0
            )
            >
            0
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "No se puede eliminar un inventario "
                    "que todavía tiene stock"
                )
            )


```

### COND-0357: InventarioService.eliminar_inventario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventario_service.py:576. Condición: `if not eliminado:`.

```python
        if not eliminado:

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "No se pudo eliminar el inventario"
                )
            )


```

### COND-0358: InventoryRiskService._safe_float

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:143. Condición: `if math.isnan(valor):`.

```python
            if math.isnan(valor):
                return default

```

### COND-0359: InventoryRiskService._safe_float

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:146. Condición: `if math.isinf(valor):`.

```python
            if math.isinf(valor):
                return default

```

### COND-0360: InventoryRiskService._promedio

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:168. Condición: `if dias <= 0:`.

```python
        if dias <= 0:
            return 0.0

```

### COND-0361: InventoryRiskService._calcular_tendencia

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:183. Condición: `if promedio_28d <= 0:`.

```python
        if promedio_28d <= 0:

            if promedio_7d > 0:
                return 100.0

            return 0.0

```

### COND-0362: InventoryRiskService._calcular_tendencia

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:185. Condición: `if promedio_7d > 0:`.

```python
            if promedio_7d > 0:
                return 100.0

```

### COND-0363: InventoryRiskService._consumo_diario_28d

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:226. Condición: `if not isinstance( fecha, datetime ):`.

```python
            if not isinstance(
                fecha,
                datetime
            ):
                continue

```

### COND-0364: InventoryRiskService._consumo_diario_28d

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:241. Condición: `if ( 0 <= indice < 28 ):`.

```python
            if (
                0
                <= indice
                < 28
            ):

                cantidad = float(
                    movimiento.get(
                        "cantidad",
                        0
                    )
                )

                consumos[
                    indice
                ] += cantidad

```

### COND-0365: InventoryRiskService._normalizar_datetime

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:273. Condición: `if isinstance( fecha, pd.Timestamp ):`.

```python
        if isinstance(
            fecha,
            pd.Timestamp
        ):

            fecha = (
                fecha.to_pydatetime()
            )

```

### COND-0366: InventoryRiskService._normalizar_datetime

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:282. Condición: `if fecha.tzinfo is None:`.

```python
        if fecha.tzinfo is None:

            fecha = fecha.replace(
                tzinfo=timezone.utc
            )

```

### COND-0367: InventoryRiskService._generar_forecast

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:317. Condición: `if not historial:`.

```python
        if not historial:

            raise ValueError(
                "No existe historial de demanda "
                "para generar el forecast."
            )

```

### COND-0368: InventoryRiskService._generar_forecast

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:328. Condición: `if history_df.empty:`.

```python
        if history_df.empty:

            raise ValueError(
                "El historial de demanda está vacío."
            )

```

### COND-0369: InventoryRiskService._generar_forecast

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:346. Condición: `if missing_columns:`.

```python
        if missing_columns:

            raise ValueError(
                "DemandHistory no devolvió las "
                "columnas necesarias: "
                + ", ".join(
                    sorted(
                        missing_columns
                    )
                )
            )

        # ----------------------------------------------------
        # 2. FECHA BASE
        # ----------------------------------------------------

```

### COND-0370: InventoryRiskService._calcular_fecha_quiebre

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:538. Condición: `if stock_actual <= 0:`.

```python
        if stock_actual <= 0:

            return fecha_base

```

### COND-0371: InventoryRiskService._calcular_fecha_quiebre

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:552. Condición: `if acumulado >= stock_actual:`.

```python
            if acumulado >= stock_actual:

                return (
                    prediccion.fecha
                )

        # El forecast solamente cubre 7 días.
        #
        # Si no se agota dentro de esos 7 días,
        # no inventamos una fecha posterior.
```

### COND-0372: InventoryRiskService._calcular_nivel_riesgo

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:576. Condición: `if stock_actual <= 0:`.

```python
        if stock_actual <= 0:

            return (
                NivelRiesgo.CRITICO
            )

```

### COND-0373: InventoryRiskService._calcular_nivel_riesgo

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:582. Condición: `if dias_cobertura is None:`.

```python
        if dias_cobertura is None:

            return (
                NivelRiesgo.BAJO
            )

```

### COND-0374: InventoryRiskService._calcular_nivel_riesgo

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:588. Condición: `if ( lead_time_dias > 0 and dias_cobertura <= lead_time_dias ):`.

```python
        if (
            lead_time_dias > 0
            and
            dias_cobertura
            <= lead_time_dias
        ):

            return (
                NivelRiesgo.CRITICO
            )

```

### COND-0375: InventoryRiskService._calcular_nivel_riesgo

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:599. Condición: `if ( punto_reposicion > 0 and stock_actual <= punto_reposicion ):`.

```python
        if (
            punto_reposicion > 0
            and
            stock_actual
            <= punto_reposicion
        ):

            return (
                NivelRiesgo.ALTO
            )

```

### COND-0376: InventoryRiskService._calcular_nivel_riesgo

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:610. Condición: `if ( lead_time_dias > 0 and dias_cobertura <= lead_time_dias * 1.5 ):`.

```python
        if (
            lead_time_dias > 0
            and
            dias_cobertura
            <= lead_time_dias * 1.5
        ):

            return (
                NivelRiesgo.MEDIO
            )

```

### COND-0377: InventoryRiskService._calcular_score

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:635. Condición: `if stock_actual <= 0:`.

```python
        if stock_actual <= 0:
            return 100.0

```

### COND-0378: InventoryRiskService._calcular_score

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:640. Condición: `if ( dias_cobertura is not None and lead_time_dias > 0 ):`.

```python
        if (
            dias_cobertura is not None
            and
            lead_time_dias > 0
        ):

            ratio_cobertura = (
                dias_cobertura
                / lead_time_dias
            )

            if ratio_cobertura <= 1:
                score += 60

            elif ratio_cobertura <= 1.5:
                score += 40

            elif ratio_cobertura <= 2:
                score += 20

```

### COND-0379: InventoryRiskService._calcular_score

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:651. Condición: `if ratio_cobertura <= 1:`.

```python
            if ratio_cobertura <= 1:
                score += 60

```

### COND-0380: InventoryRiskService._calcular_score

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:654. Condición: `elif ratio_cobertura <= 1.5:`.

```python
            elif ratio_cobertura <= 1.5:
                score += 40

```

### COND-0381: InventoryRiskService._calcular_score

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:657. Condición: `elif ratio_cobertura <= 2:`.

```python
            elif ratio_cobertura <= 2:
                score += 20

```

### COND-0382: InventoryRiskService._calcular_score

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:660. Condición: `if punto_reposicion > 0:`.

```python
        if punto_reposicion > 0:

            ratio_stock = (
                stock_actual
                / punto_reposicion
            )

            if ratio_stock <= 0.5:
                score += 40

            elif ratio_stock <= 1:
                score += 30

            elif ratio_stock <= 1.25:
                score += 15

```

### COND-0383: InventoryRiskService._calcular_score

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:667. Condición: `if ratio_stock <= 0.5:`.

```python
            if ratio_stock <= 0.5:
                score += 40

```

### COND-0384: InventoryRiskService._calcular_score

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:670. Condición: `elif ratio_stock <= 1:`.

```python
            elif ratio_stock <= 1:
                score += 30

```

### COND-0385: InventoryRiskService._calcular_score

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:673. Condición: `elif ratio_stock <= 1.25:`.

```python
            elif ratio_stock <= 1.25:
                score += 15

```

### COND-0386: InventoryRiskService._calcular_reposicion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:696. Condición: `if promedio_diario <= 0:`.

```python
        if promedio_diario <= 0:
            return None

```

### COND-0387: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:769. Condición: `if inventario is None:`.

```python
        if inventario is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Inventario no encontrado"
                )
            )

```

### COND-0388: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:786. Condición: `if not id_producto:`.

```python
        if not id_producto:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El inventario no tiene "
                    "id_producto"
                )
            )

        # ----------------------------------------------------
        # PRODUCTO
        # ----------------------------------------------------

```

### COND-0389: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:807. Condición: `if producto is None:`.

```python
        if producto is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Producto asociado "
                    "no encontrado"
                )
            )

        # ----------------------------------------------------
        # RACK
        # ----------------------------------------------------

```

### COND-0390: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:821. Condición: `if not id_rack:`.

```python
        if not id_rack:

            id_rack = producto.get(
                "id_rack"
            )

```

### COND-0391: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:827. Condición: `if not id_rack:`.

```python
        if not id_rack:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo determinar "
                    "el rack"
                )
            )

```

### COND-0392: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:844. Condición: `if rack is None:`.

```python
        if rack is None:

            raise HTTPException(
                status_code=404,
                detail="Rack no encontrado"
            )

        # ----------------------------------------------------
        # ZONA
        # ----------------------------------------------------

```

### COND-0393: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:859. Condición: `if not id_zona:`.

```python
        if not id_zona:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El rack no tiene "
                    "id_zona"
                )
            )

```

### COND-0394: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:876. Condición: `if zona is None:`.

```python
        if zona is None:

            raise HTTPException(
                status_code=404,
                detail="Zona no encontrada"
            )

        # ----------------------------------------------------
        # ALMACEN
        # ----------------------------------------------------

```

### COND-0395: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:891. Condición: `if not id_almacen:`.

```python
        if not id_almacen:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La zona no tiene "
                    "id_almacen"
                )
            )

```

### COND-0396: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:908. Condición: `if almacen is None:`.

```python
        if almacen is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Almacén no encontrado"
                )
            )

        # ----------------------------------------------------
        # EMPRESA
        #
        # Jerarquía:
        #
        # Producto
        #   ↓
        # Rack
        #   ↓
        # Zona
        #   ↓
        # Almacén
        #   ↓
        # Empresa
        # ----------------------------------------------------

```

### COND-0397: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:942. Condición: `if not id_empresa:`.

```python
        if not id_empresa:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo determinar "
                    "la empresa del inventario"
                )
            )

        # ----------------------------------------------------
        # DATOS BASE
        # ----------------------------------------------------

```

### COND-0398: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1079. Condición: `if not isinstance( fecha, datetime ):`.

```python
            if not isinstance(
                fecha,
                datetime
            ):
                continue

            # Normalizar timezone para evitar comparar
            # datetime naive contra datetime aware.
```

### COND-0399: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1087. Condición: `if fecha.tzinfo is None:`.

```python
            if fecha.tzinfo is None:

                fecha = fecha.replace(
                    tzinfo=timezone.utc
                )

```

### COND-0400: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1104. Condición: `if fecha >= fecha_14d:`.

```python
            if fecha >= fecha_14d:
                total_14d += cantidad

```

### COND-0401: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1107. Condición: `if fecha >= fecha_7d:`.

```python
            if fecha >= fecha_7d:
                total_7d += cantidad

        # ----------------------------------------------------
        # PROMEDIOS HISTORICOS
        # ----------------------------------------------------

```

### COND-0402: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1143. Condición: `if consumo_historico_diario <= 0:`.

```python
        if consumo_historico_diario <= 0:

            consumo_historico_diario = (
                promedio_14d
            )

```

### COND-0403: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1149. Condición: `if consumo_historico_diario <= 0:`.

```python
        if consumo_historico_diario <= 0:

            consumo_historico_diario = (
                promedio_28d
            )

        # ----------------------------------------------------
        # DEMANDA FORECAST PROMEDIO
        # ----------------------------------------------------

```

### COND-0404: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1161. Condición: `if ( forecast.demanda_7d is not None ):`.

```python
        if (
            forecast.demanda_7d
            is not None
        ):

            forecast_promedio_diario = (
                forecast.demanda_7d
                / self.forecast_horizon
            )

        # ----------------------------------------------------
        # DEMANDA OPERATIVA
        #
        # Usamos el mayor entre:
        #
        # 1. consumo histórico reciente
        # 2. demanda pronosticada por LightGBM
        #
        # Esto permite que LightGBM aumente preventivamente
        # el riesgo cuando detecta crecimiento futuro,
        # pero evita que una predicción muy baja reduzca
        # artificialmente la protección del inventario.
        # ----------------------------------------------------

```

### COND-0405: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1210. Condición: `if consumo_diario > 0:`.

```python
        if consumo_diario > 0:

            dias_cobertura = (
                stock_actual
                / consumo_diario
            )

            dias_cobertura = round(
                dias_cobertura,
                2
            )

        # ----------------------------------------------------
        # VARIABILIDAD
        # ----------------------------------------------------

```

### COND-0406: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1235. Condición: `if len( consumos_diarios ) > 1:`.

```python
        if len(
            consumos_diarios
        ) > 1:

            desviacion = pstdev(
                consumos_diarios
            )

        # ----------------------------------------------------
        # STOCK DE SEGURIDAD
        #
        # SS = Z * sigma * sqrt(L)
        # ----------------------------------------------------

```

### COND-0407: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1249. Condición: `if ( lead_time_dias > 0 and desviacion > 0 ):`.

```python
        if (
            lead_time_dias > 0
            and
            desviacion > 0
        ):

            stock_seguridad = (
                self.z_service_level
                * desviacion
                * math.sqrt(
                    lead_time_dias
                )
            )

```

### COND-0408: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1358. Condición: `if consumo_diario <= 0:`.

```python
        if consumo_diario <= 0:

            explicacion = (
                "No existe consumo reciente ni una "
                "demanda pronosticada suficiente para "
                "calcular una cobertura representativa."
            )

```

### COND-0409: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1366. Condición: `elif ( nivel_riesgo == NivelRiesgo.CRITICO ):`.

```python
        elif (
            nivel_riesgo
            == NivelRiesgo.CRITICO
        ):

            explicacion = (
                f"El inventario tiene una cobertura "
                f"aproximada de {dias_cobertura} días, "
                f"mientras que el tiempo de reposición "
                f"es de {lead_time_dias} días. "
                f"LightGBM pronostica una demanda de "
                f"{forecast.demanda_7d} unidades para "
                f"los próximos 7 días. "
                f"Existe riesgo crítico de quiebre "
                f"de stock."
            )

```

### COND-0410: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1383. Condición: `elif ( nivel_riesgo == NivelRiesgo.ALTO ):`.

```python
        elif (
            nivel_riesgo
            == NivelRiesgo.ALTO
        ):

            explicacion = (
                f"El stock actual ({stock_actual}) "
                f"se encuentra por debajo o cerca "
                f"del punto de reposición "
                f"({punto_reposicion}). "
                f"LightGBM pronostica "
                f"{forecast.demanda_7d} unidades "
                f"de demanda para los próximos "
                f"7 días."
            )

```

### COND-0411: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1399. Condición: `elif ( nivel_riesgo == NivelRiesgo.MEDIO ):`.

```python
        elif (
            nivel_riesgo
            == NivelRiesgo.MEDIO
        ):

            explicacion = (
                f"La cobertura actual es de "
                f"{dias_cobertura} días y se está "
                f"acercando al tiempo necesario "
                f"para reponer el producto. "
                f"El forecast de 7 días es de "
                f"{forecast.demanda_7d} unidades."
            )

```

### COND-0412: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1415. Condición: `if dias_cobertura is None:`.

```python
            if dias_cobertura is None:

                explicacion = (
                    f"El producto no presenta una "
                    f"demanda suficiente para estimar "
                    f"riesgo de quiebre. "
                    f"El forecast de LightGBM para "
                    f"los próximos 7 días es de "
                    f"{forecast.demanda_7d} unidades."
                )

```

### COND-0413: InventoryRiskService.evaluar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1526. Condición: `if generar_alertas:`.

```python
        if generar_alertas:

            await self._procesar_alerta(
                resultado
            )

```

### COND-0414: InventoryRiskService._procesar_alerta

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1547. Condición: `if nivel not in ( NivelRiesgo.ALTO, NivelRiesgo.CRITICO ):`.

```python
        if nivel not in (
            NivelRiesgo.ALTO,
            NivelRiesgo.CRITICO
        ):
            await self.alerta_service.resolver_activa_por_inventario(
                resultado.id_inventario,
                TipoAlerta.RIESGO_STOCKOUT
            )
            return

```

### COND-0415: InventoryRiskService._procesar_alerta

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1557. Condición: `if ( nivel == NivelRiesgo.CRITICO ):`.

```python
        if (
            nivel
            == NivelRiesgo.CRITICO
        ):

            titulo = (
                "Riesgo crítico de "
                "quiebre de stock"
            )

```

### COND-0416: InventoryRiskService._procesar_alerta

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1630. Condición: `if resultado.reposicion is None:`.

```python
        if resultado.reposicion is None:
            return

```

### COND-0417: InventoryRiskService.evaluar_todos

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1719. Condición: `if not id_inventario:`.

```python
            if not id_inventario:
                continue

            # Alcance de la empresa (None = todos)
```

### COND-0418: InventoryRiskService.evaluar_todos

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/inventory_risk_service.py:1723. Condición: `if ( ids_inventario is not None and id_inventario not in ids_inventario ):`.

```python
            if (
                ids_inventario is not None
                and id_inventario not in ids_inventario
            ):
                continue

```

### COND-0419: MovimientoService.validar_tipo_motivo

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:83. Condición: `if ( tipo == TipoMovimiento.ENTRADA and motivo not in motivos_entrada ):`.

```python
        if (
            tipo == TipoMovimiento.ENTRADA
            and motivo not in motivos_entrada
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El motivo {motivo.value} "
                    "no es válido para una ENTRADA"
                )
            )

```

### COND-0420: MovimientoService.validar_tipo_motivo

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:95. Condición: `if ( tipo == TipoMovimiento.SALIDA and motivo not in motivos_salida ):`.

```python
        if (
            tipo == TipoMovimiento.SALIDA
            and motivo not in motivos_salida
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El motivo {motivo.value} "
                    "no es válido para una SALIDA"
                )
            )

```

### COND-0421: MovimientoService.validar_tipo_motivo

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:107. Condición: `if ( tipo == TipoMovimiento.AJUSTE and motivo not in motivos_ajuste ):`.

```python
        if (
            tipo == TipoMovimiento.AJUSTE
            and motivo not in motivos_ajuste
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El motivo {motivo.value} "
                    "no es válido para un AJUSTE"
                )
            )

    # ========================================================
    # CREAR MOVIMIENTO
    # ========================================================

```

### COND-0422: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:129. Condición: `if data.id_detalle_recepcion:`.

```python
        if data.id_detalle_recepcion:
            existente = await (
                self.repository
                .obtener_por_detalle_recepcion(
                    data.id_detalle_recepcion
                )
            )
            if existente:
                return existente

        # ----------------------------------------------------
        # 0. Operario responsable
        #
        # OPERARIO: siempre el del token.
        # ----------------------------------------------------

```

### COND-0423: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:136. Condición: `if existente:`.

```python
            if existente:
                return existente

        # ----------------------------------------------------
        # 0. Operario responsable
        #
        # OPERARIO: siempre el del token.
        # ----------------------------------------------------

```

### COND-0424: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:145. Condición: `if user is not None and user.es_operario:`.

```python
        if user is not None and user.es_operario:

            data.id_operario = user.id_operario

```

### COND-0425: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:149. Condición: `if not data.id_operario:`.

```python
        if not data.id_operario:

            raise HTTPException(
                status_code=422,
                detail=(
                    "Debe indicar id_operario"
                )
            )

        # ----------------------------------------------------
        # 1. Validar inventario
        # ----------------------------------------------------

```

### COND-0426: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:168. Condición: `if not inventario:`.

```python
        if not inventario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventario no encontrado"
            )

        # ----------------------------------------------------
        # 2. Validar operario
        # ----------------------------------------------------

```

### COND-0427: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:184. Condición: `if ( not operario or ( user is not None and operario.get("id_empresa") != user.id_empresa ) ):`.

```python
        if (
            not operario
            or
            (
                user is not None
                and
                operario.get("id_empresa")
                != user.id_empresa
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Operario no encontrado"
            )

        # ----------------------------------------------------
        # 3. Validar operario activo
        # ----------------------------------------------------

```

### COND-0428: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:210. Condición: `if estado_operario != "ACTIVO":`.

```python
        if estado_operario != "ACTIVO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "El operario debe estar ACTIVO "
                    "para registrar movimientos"
                )
            )

        # ----------------------------------------------------
        # 4. Validar tipo + motivo
        # ----------------------------------------------------

```

### COND-0429: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:242. Condición: `if ( data.tipo_movimiento == TipoMovimiento.ENTRADA ):`.

```python
        if (
            data.tipo_movimiento
            == TipoMovimiento.ENTRADA
        ):

            stock_nuevo = (
                stock_anterior
                + data.cantidad
            )

        # ----------------------------------------------------
        # 7. SALIDA
        # ----------------------------------------------------

```

### COND-0430: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:256. Condición: `elif ( data.tipo_movimiento == TipoMovimiento.SALIDA ):`.

```python
        elif (
            data.tipo_movimiento
            == TipoMovimiento.SALIDA
        ):

            if data.cantidad > stock_anterior:

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Stock insuficiente. "
                        f"Stock disponible: "
                        f"{stock_anterior}. "
                        f"Cantidad solicitada: "
                        f"{data.cantidad}"
                    )
                )

            stock_nuevo = (
                stock_anterior
                - data.cantidad
            )

        # ----------------------------------------------------
        # 8. AJUSTE
        # ----------------------------------------------------
        #
        # Para AJUSTE, cantidad representa el NUEVO STOCK
        # físico contado.
        #
        # Ejemplo:
        # stock sistema = 100
        # cantidad = 96
        # nuevo stock = 96
        #
        # ----------------------------------------------------

```

### COND-0431: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:261. Condición: `if data.cantidad > stock_anterior:`.

```python
            if data.cantidad > stock_anterior:

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "Stock insuficiente. "
                        f"Stock disponible: "
                        f"{stock_anterior}. "
                        f"Cantidad solicitada: "
                        f"{data.cantidad}"
                    )
                )

```

### COND-0432: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:293. Condición: `elif ( data.tipo_movimiento == TipoMovimiento.AJUSTE ):`.

```python
        elif (
            data.tipo_movimiento
            == TipoMovimiento.AJUSTE
        ):

            stock_nuevo = data.cantidad

        # ----------------------------------------------------
        # 9. Validar stock
        # ----------------------------------------------------

```

### COND-0433: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:304. Condición: `if stock_nuevo < 0:`.

```python
        if stock_nuevo < 0:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El movimiento produciría "
                    "stock negativo"
                )
            )

        # ----------------------------------------------------
        # 9.1 Validar capacidad del rack
        #
        # ENTRADA y AJUSTE: la carga resultante (kg) no
        # puede superar la capacidad del rack.
        # ----------------------------------------------------

```

### COND-0434: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:326. Condición: `if ( data.tipo_movimiento in ( TipoMovimiento.ENTRADA, TipoMovimiento.AJUSTE ) and incremento > 0 ):`.

```python
        if (
            data.tipo_movimiento
            in (
                TipoMovimiento.ENTRADA,
                TipoMovimiento.AJUSTE
            )
            and
            incremento > 0
        ):

            rack = await (
                RackRepository.obtener_por_id(
                    inventario["id_rack"]
                )
            )

            if not rack:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Rack no encontrado"
                )

            producto = await (
                ProductoRepository.obtener_por_id(
                    inventario["id_producto"]
                )
            )

            await RackService.validar_asignacion(
                rack,
                producto or {},
                incremento,
                exigir_disponible=False
            )

        # ----------------------------------------------------
        # 10. Actualizar inventario
        # ----------------------------------------------------

```

### COND-0435: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:342. Condición: `if not rack:`.

```python
            if not rack:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Rack no encontrado"
                )

```

### COND-0436: MovimientoService.crear_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:374. Condición: `if not actualizado:`.

```python
        if not actualizado:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "El inventario cambió durante el movimiento; "
                    "intente nuevamente"
                )
            )

        # ----------------------------------------------------
        # 11. Crear historial
        # ----------------------------------------------------

```

### COND-0437: MovimientoService.obtener_movimiento

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/movimiento_service.py:512. Condición: `if not movimiento:`.

```python
        if not movimiento:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movimiento no encontrado"
            )

```

### COND-0438: NotificationService.notify_owner

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:41. Condición: `if existing and existing.get("status") in {"ENVIADO", "OMITIDO"}:`.

```python
        if existing and existing.get("status") in {"ENVIADO", "OMITIDO"}:
            return existing

```

### COND-0439: NotificationService.notify_owner

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:56. Condición: `if not recipient:`.

```python
        if not recipient:
            return await self._record(
                collection,
                event_id,
                id_empresa,
                None,
                subject,
                "ERROR",
                "La empresa no tiene correo configurado",
                now,
            )

```

### COND-0440: NotificationService.notify_owner

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:68. Condición: `if not settings.email_enabled:`.

```python
        if not settings.email_enabled:
            return await self._record(
                collection,
                event_id,
                id_empresa,
                recipient,
                subject,
                "OMITIDO",
                "EMAIL_ENABLED=false",
                now,
            )

```

### COND-0441: NotificationService.notify_owner

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:80. Condición: `if not all( ( settings.smtp_host, settings.smtp_user, settings.smtp_password, settings.smtp_from or settings.smtp_user, ) ):`.

```python
        if not all(
            (
                settings.smtp_host,
                settings.smtp_user,
                settings.smtp_password,
                settings.smtp_from or settings.smtp_user,
            )
        ):
            return await self._record(
                collection,
                event_id,
                id_empresa,
                recipient,
                subject,
                "ERROR",
                "Configuracion SMTP incompleta",
                now,
            )

```

### COND-0442: NotificationService.notify_owner

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:110. Condición: `if asyncio.iscoroutine(result):`.

```python
            if asyncio.iscoroutine(result):
                await result
```

### COND-0443: NotificationService._entity_email_verified

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:151. Condición: `if document is None:`.

```python
        if document is None:
            return False
```

### COND-0444: NotificationService.enviar_solicitud_aprobacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:166. Condición: `if not recomendacion:`.

```python
        if not recomendacion:
            return {"status": "ERROR", "reason": "Recomendacion no encontrada"}

```

### COND-0445: NotificationService.enviar_solicitud_aprobacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:205. Condición: `if not recipient:`.

```python
        if not recipient:
            return await self._record(
                collection,
                event_id,
                recomendacion["id_empresa"],
                None,
                subject,
                "ERROR",
                "La empresa no tiene correo configurado",
                now,
            )

```

### COND-0446: NotificationService.enviar_solicitud_aprobacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:217. Condición: `if not await self._entity_email_verified( database, "empresas", "id_empresa", recomendacion["id_empresa"], ):`.

```python
        if not await self._entity_email_verified(
            database,
            "empresas",
            "id_empresa",
            recomendacion["id_empresa"],
        ):
            return await self._record(
                collection,
                event_id,
                recomendacion["id_empresa"],
                recipient,
                subject,
                "BLOQUEADA_EMAIL_NO_VERIFICADO",
                "El correo de la empresa no está verificado",
                now,
            )

```

### COND-0447: NotificationService.enviar_orden_proveedor

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:272. Condición: `if not orden:`.

```python
        if not orden:
            return {"status": "ERROR", "reason": "Orden no encontrada"}

```

### COND-0448: NotificationService.enviar_orden_proveedor

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:297. Condición: `if not recipient:`.

```python
        if not recipient:
            return await self._record(
                collection,
                event_id,
                orden["id_empresa"],
                None,
                subject,
                "ERROR",
                "El proveedor no tiene correo configurado",
                now,
            )

```

### COND-0449: NotificationService.enviar_orden_proveedor

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:309. Condición: `if not await self._entity_email_verified( database, "proveedores", "id_proveedor", orden["id_proveedor"], ):`.

```python
        if not await self._entity_email_verified(
            database,
            "proveedores",
            "id_proveedor",
            orden["id_proveedor"],
        ):
            return await self._record(
                collection,
                event_id,
                orden["id_empresa"],
                recipient,
                subject,
                "BLOQUEADA_EMAIL_NO_VERIFICADO",
                "El correo del proveedor no está verificado",
                now,
            )

```

### COND-0450: NotificationService.enviar_orden_proveedor

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:353. Condición: `if not settings.email_enabled:`.

```python
        if not settings.email_enabled:
            return await self._record(
                collection,
                event_id,
                orden["id_empresa"],
                recipient,
                subject,
                "OMITIDO",
                "EMAIL_ENABLED=false",
                now,
            )

```

### COND-0451: NotificationService.enviar_orden_proveedor

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:365. Condición: `if not all( ( settings.smtp_host, settings.smtp_user, settings.smtp_password, settings.smtp_from or settings.smtp_user, ) ):`.

```python
        if not all(
            (
                settings.smtp_host,
                settings.smtp_user,
                settings.smtp_password,
                settings.smtp_from or settings.smtp_user,
            )
        ):
            return await self._record(
                collection,
                event_id,
                orden["id_empresa"],
                recipient,
                subject,
                "ERROR",
                "Configuracion SMTP incompleta",
                now,
            )

```

### COND-0452: NotificationService.enviar_orden_proveedor

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:395. Condición: `if asyncio.iscoroutine(result):`.

```python
            if asyncio.iscoroutine(result):
                await result
```

### COND-0453: NotificationService.enviar_resumen_reposicion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:431. Condición: `if not detalle:`.

```python
        if not detalle:
            return {"status": "ERROR", "reason": "Detalle no encontrado"}

```

### COND-0454: NotificationService.enviar_resumen_reposicion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:472. Condición: `if not recipient:`.

```python
        if not recipient:
            return await self._record(
                collection,
                event_id,
                (orden or {}).get("id_empresa", ""),
                None,
                subject,
                "ERROR",
                "La empresa no tiene correo configurado",
                now,
            )

```

### COND-0455: NotificationService.enviar_resumen_reposicion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:484. Condición: `if not await self._entity_email_verified( database, "empresas", "id_empresa", (orden or {}).get("id_empresa", ""), ):`.

```python
        if not await self._entity_email_verified(
            database,
            "empresas",
            "id_empresa",
            (orden or {}).get("id_empresa", ""),
        ):
            return await self._record(
                collection,
                event_id,
                (orden or {}).get("id_empresa", ""),
                recipient,
                subject,
                "BLOQUEADA_EMAIL_NO_VERIFICADO",
                "El correo de la empresa no está verificado",
                now,
            )

```

### COND-0456: NotificationService._find

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:530. Condición: `if not identifier:`.

```python
        if not identifier:
            return None
```

### COND-0457: NotificationService._risk_message

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:544. Condición: `if level == "BAJO":`.

```python
        if level == "BAJO":
            return "El inventario se encuentra en un nivel de riesgo bajo/protegido."
```

### COND-0458: NotificationService._send_smtp

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/notification_service.py:598. Condición: `if settings.smtp_use_tls:`.

```python
            if settings.smtp_use_tls:
                server.starttls()
```

### COND-0459: OperarioService.validar_almacen

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:105. Condición: `if ( not almacen or almacen.get("id_empresa") != id_empresa ):`.

```python
        if (
            not almacen
            or
            almacen.get("id_empresa")
            != id_empresa
        ):

            raise HTTPException(
                status_code=
                    status.HTTP_400_BAD_REQUEST,
                detail=(
                    "El almacén del operario no pertenece "
                    "a la empresa"
                )
            )


    # ============================================================
    # CREAR
    #
    # id_empresa se toma del token.
    # Queda con debe_cambiar_password = true.
    # ============================================================

```

### COND-0460: OperarioService.crear_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:142. Condición: `if not empresa:`.

```python
        if not empresa:

            raise HTTPException(
                status_code=
                    status.HTTP_404_NOT_FOUND,
                detail=
                    "Empresa no encontrada"
            )

```

### COND-0461: OperarioService.obtener_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:251. Condición: `if ( not operario or operario.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not operario
            or
            operario.get("id_empresa")
            != user.id_empresa
        ):

            raise HTTPException(
                status_code=
                    status.HTTP_404_NOT_FOUND,
                detail=
                    "Operario no encontrado"
            )

```

### COND-0462: OperarioService.obtener_por_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:280. Condición: `if id_empresa != user.id_empresa:`.

```python
        if id_empresa != user.id_empresa:

            raise HTTPException(
                status_code=
                    status.HTTP_404_NOT_FOUND,
                detail=
                    "Empresa no encontrada"
            )

```

### COND-0463: OperarioService.actualizar_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:388. Condición: `if not update_data:`.

```python
        if not update_data:
            return operario


```

### COND-0464: OperarioService.actualizar_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:392. Condición: `if "id_almacen" in update_data:`.

```python
        if "id_almacen" in update_data:

            await self.validar_almacen(
                user.id_empresa,
                update_data["id_almacen"]
            )


```

### COND-0465: OperarioService.actualizar_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:400. Condición: `if "correo" in update_data:`.

```python
        if "correo" in update_data:

            update_data[
                "correo"
            ] = await (
                self.validar_correo_disponible(
                    str(update_data["correo"]),
                    id_operario
                )
            )

            # Correo distinto -> hay que verificarlo de nuevo
            if (
                (operario.get("correo") or "").lower()
                != update_data["correo"]
            ):
                update_data["correo_verificado"] = False
                update_data["fecha_verificacion_correo"] = None


```

### COND-0466: OperarioService.actualizar_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:412. Condición: `if ( (operario.get("correo") or "").lower() != update_data["correo"] ):`.

```python
            if (
                (operario.get("correo") or "").lower()
                != update_data["correo"]
            ):
                update_data["correo_verificado"] = False
                update_data["fecha_verificacion_correo"] = None


```

### COND-0467: OperarioService.actualizar_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:426. Condición: `if campo in update_data:`.

```python
            if campo in update_data:

                update_data[
                    campo
                ] = (
                    update_data[
                        campo
                    ].strip()
                )


```

### COND-0468: OperarioService.actualizar_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:442. Condición: `if campo in update_data:`.

```python
            if campo in update_data:

                update_data[
                    campo
                ] = (
                    update_data[
                        campo
                    ]
                    .strip()
                    .upper()
                )


```

### COND-0469: OperarioService.actualizar_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:463. Condición: `if not actualizado:`.

```python
        if not actualizado:

            raise HTTPException(
                status_code=
                    status.HTTP_404_NOT_FOUND,
                detail=
                    "Operario no encontrado"
            )

```

### COND-0470: OperarioService.reset_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:497. Condición: `if data.correo is not None:`.

```python
        if data.correo is not None:

            correo = await (
                self.validar_correo_disponible(
                    str(data.correo),
                    id_operario
                )
            )

            await (
                OperarioRepository
                .actualizar(
                    id_operario,
                    {
                        "correo": correo
                    }
                )
            )

```

### COND-0471: OperarioService.reset_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:516. Condición: `elif not operario.get("correo"):`.

```python
        elif not operario.get("correo"):

            raise HTTPException(
                status_code=
                    status.HTTP_409_CONFLICT,
                detail=(
                    "El operario no tiene correo. "
                    "Envíe 'correo' en el body "
                    "(o asígnelo con PUT /operarios/{id})"
                )
            )

```

### COND-0472: OperarioService.eliminar_operario

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/operario_service.py:566. Condición: `if not eliminado:`.

```python
        if not eliminado:

            raise HTTPException(
                status_code=
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=
                    "No se pudo eliminar el operario"
            )

```

### COND-0473: OrdenReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:64. Condición: `if not empresa:`.

```python
        if not empresa:
            raise HTTPException(
                status_code=404,
                detail="Empresa no encontrada"
            )

```

### COND-0474: OrdenReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:79. Condición: `if not almacen:`.

```python
        if not almacen:
            raise HTTPException(
                status_code=404,
                detail="Almacén no encontrado"
            )

```

### COND-0475: OrdenReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:85. Condición: `if almacen.get("id_empresa") != data.id_empresa:`.

```python
        if almacen.get("id_empresa") != data.id_empresa:
            raise HTTPException(
                status_code=400,
                detail="El almacén no pertenece a la empresa"
            )

```

### COND-0476: OrdenReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:97. Condición: `if not proveedor:`.

```python
        if not proveedor:
            raise HTTPException(
                status_code=404,
                detail="Proveedor no encontrado"
            )

```

### COND-0477: OrdenReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:103. Condición: `if proveedor["id_empresa"] != data.id_empresa:`.

```python
        if proveedor["id_empresa"] != data.id_empresa:
            raise HTTPException(
                status_code=400,
                detail="El proveedor no pertenece a la empresa"
            )

```

### COND-0478: OrdenReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:109. Condición: `if proveedor["estado"] != "ACTIVO":`.

```python
        if proveedor["estado"] != "ACTIVO":
            raise HTTPException(
                status_code=400,
                detail="El proveedor está inactivo"
            )

```

### COND-0479: OrdenReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:139. Condición: `if len(set(ids_producto)) != len(ids_producto):`.

```python
        if len(set(ids_producto)) != len(ids_producto):
            raise HTTPException(
                status_code=409,
                detail="Hay productos repetidos en las líneas"
            )

```

### COND-0480: OrdenReposicionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:151. Condición: `if ( not producto or producto.get("id_empresa") != data.id_empresa ):`.

```python
            if (
                not producto
                or producto.get("id_empresa")
                != data.id_empresa
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Producto no encontrado"
                )

```

### COND-0481: OrdenReposicionService.obtener_por_id

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:184. Condición: `if not orden:`.

```python
        if not orden:
            raise HTTPException(
                status_code=404,
                detail="Orden de reposición no encontrada"
            )

```

### COND-0482: OrdenReposicionService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:224. Condición: `if orden["estado"] not in [ "PENDIENTE", "OBSERVADA" ]:`.

```python
        if orden["estado"] not in [
            "PENDIENTE",
            "OBSERVADA"
        ]:
            raise HTTPException(
                status_code=409,
                detail="La orden ya no puede modificarse"
            )

```

### COND-0483: OrdenReposicionService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:237. Condición: `if cambios.get("id_proveedor"):`.

```python
        if cambios.get("id_proveedor"):

            proveedor = (
                await self.proveedor_repository.obtener_por_id(
                    cambios["id_proveedor"]
                )
            )

            if (
                not proveedor
                or proveedor["id_empresa"] != orden["id_empresa"]
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Proveedor no encontrado"
                )

            if proveedor["estado"] != "ACTIVO":
                raise HTTPException(
                    status_code=400,
                    detail="El proveedor está inactivo"
                )

```

### COND-0484: OrdenReposicionService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:245. Condición: `if ( not proveedor or proveedor["id_empresa"] != orden["id_empresa"] ):`.

```python
            if (
                not proveedor
                or proveedor["id_empresa"] != orden["id_empresa"]
            ):
                raise HTTPException(
                    status_code=404,
                    detail="Proveedor no encontrado"
                )

```

### COND-0485: OrdenReposicionService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:254. Condición: `if proveedor["estado"] != "ACTIVO":`.

```python
            if proveedor["estado"] != "ACTIVO":
                raise HTTPException(
                    status_code=400,
                    detail="El proveedor está inactivo"
                )

```

### COND-0486: OrdenReposicionService.validar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:281. Condición: `if orden["estado"] not in [ "PENDIENTE", "APROBADA" ]:`.

```python
        if orden["estado"] not in [
            "PENDIENTE",
            "APROBADA"
        ]:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo una solicitud PENDIENTE "
                    "puede validarse"
                )
            )

```

### COND-0487: OrdenReposicionService.validar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:297. Condición: `if not detalles:`.

```python
        if not detalles:
            raise HTTPException(
                status_code=409,
                detail=(
                    "No se puede validar una solicitud "
                    "sin productos"
                )
            )

```

### COND-0488: OrdenReposicionService.devolver

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:344. Condición: `if orden["estado"] != "PENDIENTE":`.

```python
        if orden["estado"] != "PENDIENTE":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo una solicitud PENDIENTE "
                    "puede devolverse"
                )
            )

```

### COND-0489: OrdenReposicionService.reenviar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:369. Condición: `if orden["estado"] != "OBSERVADA":`.

```python
        if orden["estado"] != "OBSERVADA":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo una solicitud OBSERVADA "
                    "puede reenviarse"
                )
            )

```

### COND-0490: OrdenReposicionService.cancelar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:391. Condición: `if orden["estado"] not in [ "PENDIENTE", "OBSERVADA", "APROBADA" ]:`.

```python
        if orden["estado"] not in [
            "PENDIENTE",
            "OBSERVADA",
            "APROBADA"
        ]:
            raise HTTPException(
                status_code=409,
                detail="La orden ya no puede cancelarse"
            )

```

### COND-0491: OrdenReposicionService.registrar_despacho

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:434. Condición: `if orden["estado"] not in [ "ENVIADA", "PARCIAL" ]:`.

```python
        if orden["estado"] not in [
            "ENVIADA",
            "PARCIAL"
        ]:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo se registra despacho de una "
                    "orden ENVIADA o PARCIAL"
                )
            )

```

### COND-0492: OrdenReposicionService.registrar_despacho

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:463. Condición: `if not detalle:`.

```python
            if not detalle:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "La línea "
                        f"{linea.id_detalle_reposicion} "
                        "no pertenece a la orden"
                    )
                )

```

### COND-0493: OrdenReposicionService.eliminar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/orden_reposicion_service.py:501. Condición: `if orden["estado"] != "PENDIENTE":`.

```python
        if orden["estado"] != "PENDIENTE":
            raise HTTPException(
                status_code=409,
                detail="Solo una orden pendiente puede eliminarse"
            )

```

### COND-0494: ProductoService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:56. Condición: `if not empresa:`.

```python
        if not empresa:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Empresa no encontrada"
            )


        # --------------------------------------------------------
        # VALIDAR RACK
        # --------------------------------------------------------

        # El rack de referencia es opcional al crear.
```

### COND-0495: ProductoService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:79. Condición: `if data.id_rack and not rack:`.

```python
        if data.id_rack and not rack:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Rack no encontrado"
            )


        # --------------------------------------------------------
        # VALIDAR REFRIGERACION
        # --------------------------------------------------------

```

### COND-0496: ProductoService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:93. Condición: `if data.requiere_refrigeracion:`.

```python
        if data.requiere_refrigeracion:

            if (
                data.temperatura_min_almacenamiento
                is None
                or
                data.temperatura_max_almacenamiento
                is None
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Si el producto requiere refrigeración, "
                        "debe indicar temperatura mínima y máxima"
                    )
                )

            if (
                data.temperatura_min_almacenamiento
                >
                data.temperatura_max_almacenamiento
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "La temperatura mínima no puede ser "
                        "mayor que la temperatura máxima"
                    )
                )


        # --------------------------------------------------------
        # CONSTRUIR PRODUCTO
        # --------------------------------------------------------

```

### COND-0497: ProductoService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:95. Condición: `if ( data.temperatura_min_almacenamiento is None or data.temperatura_max_almacenamiento is None ):`.

```python
            if (
                data.temperatura_min_almacenamiento
                is None
                or
                data.temperatura_max_almacenamiento
                is None
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Si el producto requiere refrigeración, "
                        "debe indicar temperatura mínima y máxima"
                    )
                )

```

### COND-0498: ProductoService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:113. Condición: `if ( data.temperatura_min_almacenamiento > data.temperatura_max_almacenamiento ):`.

```python
            if (
                data.temperatura_min_almacenamiento
                >
                data.temperatura_max_almacenamiento
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "La temperatura mínima no puede ser "
                        "mayor que la temperatura máxima"
                    )
                )


        # --------------------------------------------------------
        # CONSTRUIR PRODUCTO
        # --------------------------------------------------------

```

### COND-0499: ProductoService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:163. Condición: `if producto.get("marca"):`.

```python
        if producto.get("marca"):

            producto["marca"] = (
                producto[
                    "marca"
                ].strip()
            )


        # --------------------------------------------------------
        # ID Y FECHAS
        # --------------------------------------------------------

```

### COND-0500: ProductoService.obtener_por_id

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:237. Condición: `if not producto:`.

```python
        if not producto:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )

```

### COND-0501: ProductoService.obtener_por_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:264. Condición: `if not rack:`.

```python
        if not rack:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Rack no encontrado"
            )


```

### COND-0502: ProductoService.obtener_por_almacen

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:297. Condición: `if not almacen:`.

```python
        if not almacen:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Almacén no encontrado"
            )


```

### COND-0503: ProductoService.obtener_por_categoria

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:328. Condición: `if not categoria:`.

```python
        if not categoria:

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "La categoría no puede estar vacía"
                )
            )


```

### COND-0504: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:378. Condición: `if not producto_actual:`.

```python
        if not producto_actual:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )


```

### COND-0505: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:401. Condición: `if ( "id_rack" in update_data and update_data[ "id_rack" ] is not None ):`.

```python
        if (
            "id_rack" in update_data
            and
            update_data[
                "id_rack"
            ] is not None
        ):

            rack = await (
                RackRepository.obtener_por_id(
                    update_data[
                        "id_rack"
                    ]
                )
            )

            if not rack:

                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail="Rack no encontrado"
                )


        # --------------------------------------------------------
        # REFRIGERACION RESULTANTE
        # --------------------------------------------------------

```

### COND-0506: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:417. Condición: `if not rack:`.

```python
            if not rack:

                raise HTTPException(
                    status_code=(
                        status.HTTP_404_NOT_FOUND
                    ),
                    detail="Rack no encontrado"
                )


        # --------------------------------------------------------
        # REFRIGERACION RESULTANTE
        # --------------------------------------------------------

```

### COND-0507: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:462. Condición: `if requiere:`.

```python
        if requiere:

            if (
                temperatura_min is None
                or
                temperatura_max is None
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Un producto refrigerado debe tener "
                        "temperatura mínima y máxima"
                    )
                )


            if (
                temperatura_min
                >
                temperatura_max
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "La temperatura mínima no puede ser "
                        "mayor que la temperatura máxima"
                    )
                )


        # --------------------------------------------------------
        # SI YA NO REQUIERE REFRIGERACION
        # --------------------------------------------------------

```

### COND-0508: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:464. Condición: `if ( temperatura_min is None or temperatura_max is None ):`.

```python
            if (
                temperatura_min is None
                or
                temperatura_max is None
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "Un producto refrigerado debe tener "
                        "temperatura mínima y máxima"
                    )
                )


```

### COND-0509: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:481. Condición: `if ( temperatura_min > temperatura_max ):`.

```python
            if (
                temperatura_min
                >
                temperatura_max
            ):

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail=(
                        "La temperatura mínima no puede ser "
                        "mayor que la temperatura máxima"
                    )
                )


        # --------------------------------------------------------
        # SI YA NO REQUIERE REFRIGERACION
        # --------------------------------------------------------

```

### COND-0510: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:502. Condición: `if ( update_data.get( "requiere_refrigeracion" ) is False ):`.

```python
        if (
            update_data.get(
                "requiere_refrigeracion"
            )
            is False
        ):

            update_data[
                "temperatura_min_almacenamiento"
            ] = None

            update_data[
                "temperatura_max_almacenamiento"
            ] = None


        # --------------------------------------------------------
        # LIMPIAR TEXTOS
        # --------------------------------------------------------

```

### COND-0511: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:529. Condición: `if ( campo in update_data and isinstance( update_data[ campo ], str ) ):`.

```python
            if (
                campo in update_data
                and
                isinstance(
                    update_data[
                        campo
                    ],
                    str
                )
            ):

                update_data[
                    campo
                ] = (
                    update_data[
                        campo
                    ].strip()
                )


```

### COND-0512: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:549. Condición: `if not update_data:`.

```python
        if not update_data:

            return producto_actual


```

### COND-0513: ProductoService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:562. Condición: `if not producto_actualizado:`.

```python
        if not producto_actualizado:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )


```

### COND-0514: ProductoService.eliminar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:591. Condición: `if not producto:`.

```python
        if not producto:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Producto no encontrado"
            )


```

### COND-0515: ProductoService.eliminar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/producto_service.py:608. Condición: `if not eliminado:`.

```python
        if not eliminado:

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "No se pudo eliminar el producto"
                )
            )


```

### COND-0516: ProveedorService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:37. Condición: `if not empresa:`.

```python
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )

```

### COND-0517: ProveedorService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:47. Condición: `if existente:`.

```python
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un proveedor con ese RUC"
            )

```

### COND-0518: ProveedorService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:64. Condición: `if password_temporal:`.

```python
        if password_temporal:

            if not data.correo:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "El correo es obligatorio para "
                        "crear la cuenta del proveedor"
                    )
                )

            await validar_correo_disponible(
                str(data.correo)
            )

            documento["password_hash"] = hash_password(
                password_temporal
            )
            documento["debe_cambiar_password"] = True

```

### COND-0519: ProveedorService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:66. Condición: `if not data.correo:`.

```python
            if not data.correo:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "El correo es obligatorio para "
                        "crear la cuenta del proveedor"
                    )
                )

```

### COND-0520: ProveedorService.obtener_por_id

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:100. Condición: `if not proveedor:`.

```python
        if not proveedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado"
            )

```

### COND-0521: ProveedorService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:132. Condición: `if "correo" in cambios and cambios["correo"] is not None:`.

```python
        if "correo" in cambios and cambios["correo"] is not None:
            cambios["correo"] = str(cambios["correo"]).strip().lower()
            if proveedor.get("password_hash"):
                await validar_correo_disponible(
                    cambios["correo"],
                    id_proveedor
                )
            if proveedor.get("correo") and proveedor.get("correo").lower() != cambios["correo"]:
                cambios["correo_verificado"] = False
                cambios["fecha_verificacion_correo"] = None

```

### COND-0522: ProveedorService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:134. Condición: `if proveedor.get("password_hash"):`.

```python
            if proveedor.get("password_hash"):
                await validar_correo_disponible(
                    cambios["correo"],
                    id_proveedor
                )
```

### COND-0523: ProveedorService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:139. Condición: `if proveedor.get("correo") and proveedor.get("correo").lower() != cambios["correo"]:`.

```python
            if proveedor.get("correo") and proveedor.get("correo").lower() != cambios["correo"]:
                cambios["correo_verificado"] = False
                cambios["fecha_verificacion_correo"] = None

```

### COND-0524: ProveedorService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:143. Condición: `if "estado" in cambios:`.

```python
        if "estado" in cambios:
            cambios["estado"] = cambios["estado"].value

```

### COND-0525: ProveedorService.reset_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:168. Condición: `if not correo:`.

```python
        if not correo:
            raise HTTPException(
                status_code=409,
                detail=(
                    "El proveedor no tiene correo. "
                    "Envíe 'correo' en el body"
                )
            )

```

### COND-0526: ProveedorService.reset_password

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:188. Condición: `if cambios["correo"] != (proveedor.get("correo") or "").lower():`.

```python
        if cambios["correo"] != (proveedor.get("correo") or "").lower():
            cambios["correo_verificado"] = False
            cambios["fecha_verificacion_correo"] = None

```

### COND-0527: ProveedorService.eliminar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/proveedor_service.py:205. Condición: `if not eliminado:`.

```python
        if not eliminado:
            raise HTTPException(
                status_code=500,
                detail="No se pudo eliminar el proveedor"
            )

```

### COND-0528: RackService.enriquecer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:79. Condición: `if not racks:`.

```python
        if not racks:
            return []

```

### COND-0529: RackService.enriquecer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:149. Condición: `if "id_rack" not in item:`.

```python
            if "id_rack" not in item:
                item["id_rack"] = _id_rack(rack)

```

### COND-0530: RackService.motivo_no_cabe

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:215. Condición: `if ( exigir_disponible and rack.get("estado") != "DISPONIBLE" ):`.

```python
        if (
            exigir_disponible
            and
            rack.get("estado") != "DISPONIBLE"
        ):

            return (
                f"El rack {codigo} no está "
                "DISPONIBLE (estado: "
                f"{rack.get('estado')})"
            )

```

### COND-0531: RackService.motivo_no_cabe

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:232. Condición: `if carga > 0 and carga > rack["libre_kg"] + 1e-9:`.

```python
        if carga > 0 and carga > rack["libre_kg"] + 1e-9:

            return (
                f"Capacidad insuficiente en el rack "
                f"{codigo}. Libre: "
                f"{_kg(max(rack['libre_kg'], 0))} kg. "
                f"Carga a ingresar: {_kg(carga)} kg"
            )

```

### COND-0532: RackService.motivo_no_cabe

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:241. Condición: `if producto.get("requiere_refrigeracion"):`.

```python
        if producto.get("requiere_refrigeracion"):

            r_min = rack.get("temperatura_min")
            r_max = rack.get("temperatura_max")
            p_min = producto.get(
                "temperatura_min_almacenamiento"
            )
            p_max = producto.get(
                "temperatura_max_almacenamiento"
            )

            if r_min is None or r_max is None:

                return (
                    f"El producto requiere refrigeración "
                    f"y el rack {codigo} no tiene "
                    "temperatura definida"
                )

            if (
                (p_min is not None and r_min < p_min)
                or
                (p_max is not None and r_max > p_max)
            ):

                return (
                    f"La temperatura del rack {codigo} "
                    f"({_kg(r_min)} a {_kg(r_max)} °C) no cabe "
                    "en el rango del producto "
                    f"({_kg(p_min)} a {_kg(p_max)} °C)"
                )

```

### COND-0533: RackService.motivo_no_cabe

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:252. Condición: `if r_min is None or r_max is None:`.

```python
            if r_min is None or r_max is None:

                return (
                    f"El producto requiere refrigeración "
                    f"y el rack {codigo} no tiene "
                    "temperatura definida"
                )

```

### COND-0534: RackService.motivo_no_cabe

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:260. Condición: `if ( (p_min is not None and r_min < p_min) or (p_max is not None and r_max > p_max) ):`.

```python
            if (
                (p_min is not None and r_min < p_min)
                or
                (p_max is not None and r_max > p_max)
            ):

                return (
                    f"La temperatura del rack {codigo} "
                    f"({_kg(r_min)} a {_kg(r_max)} °C) no cabe "
                    "en el rango del producto "
                    f"({_kg(p_min)} a {_kg(p_max)} °C)"
                )

```

### COND-0535: RackService.validar_asignacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:304. Condición: `if motivo:`.

```python
        if motivo:

            raise HTTPException(
                status_code=409,
                detail=motivo
            )

```

### COND-0536: RackService.crear_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:328. Condición: `if not zona:`.

```python
        if not zona:
            raise HTTPException(
                status_code=404,
                detail="Zona no encontrada"
            )

        # --------------------------------------------------------
        # NIVEL DENTRO DE LOS NIVELES DE LA ZONA
        # --------------------------------------------------------

```

### COND-0537: RackService.crear_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:342. Condición: `if data.nivel > niveles:`.

```python
        if data.nivel > niveles:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"La zona solo tiene {niveles} "
                    f"nivel(es); no existe el nivel {data.nivel}"
                )
            )

        # --------------------------------------------------------
        # UN RACK POR NIVEL
        # --------------------------------------------------------

```

### COND-0538: RackService.crear_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:361. Condición: `if any( rack.get("nivel") == data.nivel for rack in racks_zona ):`.

```python
        if any(
            rack.get("nivel") == data.nivel
            for rack in racks_zona
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Ya existe un rack en el nivel "
                    f"{data.nivel} de esta zona"
                )
            )

```

### COND-0539: RackService.crear_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:375. Condición: `if any( rack.get("codigo") == codigo for rack in racks_zona ):`.

```python
        if any(
            rack.get("codigo") == codigo
            for rack in racks_zona
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Ya existe un rack con ese "
                    "código en la zona"
                )
            )

        # --------------------------------------------------------
        # TEMPERATURA: SOLO ZONAS REFRIGERADAS
        # --------------------------------------------------------

```

### COND-0540: RackService.crear_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:396. Condición: `if zona.get("refrigerada"):`.

```python
        if zona.get("refrigerada"):

            if (
                data.temperatura_min is None
                or data.temperatura_max is None
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "La zona es refrigerada: indique "
                        "temperatura_min y temperatura_max "
                        "del rack"
                    )
                )

```

### COND-0541: RackService.crear_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:398. Condición: `if ( data.temperatura_min is None or data.temperatura_max is None ):`.

```python
            if (
                data.temperatura_min is None
                or data.temperatura_max is None
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "La zona es refrigerada: indique "
                        "temperatura_min y temperatura_max "
                        "del rack"
                    )
                )

```

### COND-0542: RackService.crear_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:411. Condición: `elif tiene_temperatura:`.

```python
        elif tiene_temperatura:

            raise HTTPException(
                status_code=409,
                detail=(
                    "Solo los racks de zonas refrigeradas "
                    "tienen temperatura"
                )
            )

```

### COND-0543: RackService.obtener_racks

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:475. Condición: `if ids_zona is None:`.

```python
        if ids_zona is None:

            racks = await (
                self.repository.obtener_todos()
            )

```

### COND-0544: RackService.obtener_racks

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:481. Condición: `elif not ids_zona:`.

```python
        elif not ids_zona:

            return []

```

### COND-0545: RackService.obtener_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:508. Condición: `if not rack:`.

```python
        if not rack:
            raise HTTPException(
                status_code=404,
                detail="Rack no encontrado"
            )

```

### COND-0546: RackService.obtener_racks_zona

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:529. Condición: `if not zona:`.

```python
        if not zona:
            raise HTTPException(
                status_code=404,
                detail="Zona no encontrada"
            )

```

### COND-0547: RackService.obtener_disponibles

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:570. Condición: `if not nombres_zona:`.

```python
        if not nombres_zona:
            return []

```

### COND-0548: RackService.obtener_disponibles

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:583. Condición: `if self.motivo_no_cabe( rack, producto or {}, cantidad ):`.

```python
            if self.motivo_no_cabe(
                rack,
                producto or {},
                cantidad
            ):
                continue

```

### COND-0549: RackService.actualizar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:623. Condición: `if not rack_actual:`.

```python
        if not rack_actual:
            raise HTTPException(
                status_code=404,
                detail="Rack no encontrado"
            )

```

### COND-0550: RackService.actualizar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:633. Condición: `if "estado" in datos:`.

```python
        if "estado" in datos:

            if datos["estado"] is None:
                datos.pop("estado")
            else:
                datos["estado"] = datos["estado"].value

```

### COND-0551: RackService.actualizar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:635. Condición: `if datos["estado"] is None:`.

```python
            if datos["estado"] is None:
                datos.pop("estado")
```

### COND-0552: RackService.actualizar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:640. Condición: `if ( "temperatura_min" in datos or "temperatura_max" in datos ):`.

```python
        if (
            "temperatura_min" in datos
            or "temperatura_max" in datos
        ):

            zona = (
                await self.zona_repository.obtener_por_id(
                    rack_actual["id_zona"]
                )
            )

            if not (zona or {}).get("refrigerada"):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Solo los racks de zonas refrigeradas "
                        "tienen temperatura"
                    )
                )

            t_min = datos.get(
                "temperatura_min",
                rack_actual.get("temperatura_min")
            )

            t_max = datos.get(
                "temperatura_max",
                rack_actual.get("temperatura_max")
            )

            if t_min is None or t_max is None:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Indique temperatura_min "
                        "y temperatura_max"
                    )
                )

            if t_min > t_max:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "La temperatura mínima no puede "
                        "ser mayor que la máxima"
                    )
                )

```

### COND-0553: RackService.actualizar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:651. Condición: `if not (zona or {}).get("refrigerada"):`.

```python
            if not (zona or {}).get("refrigerada"):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Solo los racks de zonas refrigeradas "
                        "tienen temperatura"
                    )
                )

```

### COND-0554: RackService.actualizar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:670. Condición: `if t_min is None or t_max is None:`.

```python
            if t_min is None or t_max is None:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Indique temperatura_min "
                        "y temperatura_max"
                    )
                )

```

### COND-0555: RackService.actualizar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:679. Condición: `if t_min > t_max:`.

```python
            if t_min > t_max:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "La temperatura mínima no puede "
                        "ser mayor que la máxima"
                    )
                )

```

### COND-0556: RackService.actualizar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:688. Condición: `if not datos:`.

```python
        if not datos:
            return await self.enriquecer_uno(
                rack_actual
            )

```

### COND-0557: RackService.eliminar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:711. Condición: `if not rack:`.

```python
        if not rack:
            raise HTTPException(
                status_code=404,
                detail="Rack no encontrado"
            )

        # --------------------------------------------------------
        # NO BORRAR RACKS CON INVENTARIO
        # --------------------------------------------------------

```

### COND-0558: RackService.eliminar_rack

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/rack_service.py:728. Condición: `if inventarios:`.

```python
        if inventarios:
            raise HTTPException(
                status_code=409,
                detail=(
                    "El rack tiene inventarios; "
                    "no puede eliminarse"
                )
            )

```

### COND-0559: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:69. Condición: `if ( not orden or orden.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not orden
            or orden.get("id_empresa") != user.id_empresa
        ):
            raise HTTPException(
                status_code=404,
                detail="Orden no encontrada"
            )

        # ----------------------------------------------------
        # Solo OPERARIO, sobre órdenes de su almacén.
        # id_operario se fuerza al del token.
        # ----------------------------------------------------

```

### COND-0560: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:83. Condición: `if orden.get("id_almacen") != user.id_almacen:`.

```python
        if orden.get("id_almacen") != user.id_almacen:

            raise HTTPException(
                status_code=403,
                detail="La orden no es de su almacén"
            )

```

### COND-0561: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:92. Condición: `if orden["estado"] not in [ "ENVIADA", "PARCIAL" ]:`.

```python
        if orden["estado"] not in [
            "ENVIADA",
            "PARCIAL"
        ]:
            raise HTTPException(
                status_code=409,
                detail=(
                    "La orden debe estar ENVIADA "
                    "o PARCIAL para recibir mercancía"
                )
            )

```

### COND-0562: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:110. Condición: `if not detalles:`.

```python
        if not detalles:
            raise HTTPException(
                status_code=409,
                detail=(
                    "La orden no contiene productos"
                )
            )

        # Cada detalle debe pertenecer a la orden
```

### COND-0563: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:126. Condición: `if ( detalle.id_detalle_reposicion not in ids_detalle_orden ):`.

```python
            if (
                detalle.id_detalle_reposicion
                not in ids_detalle_orden
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "El detalle de reposición "
                        f"{detalle.id_detalle_reposicion} "
                        "no pertenece a la orden"
                    )
                )

```

### COND-0564: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:146. Condición: `if ( not operario or operario.get("id_empresa") != user.id_empresa ):`.

```python
        if (
            not operario
            or operario.get("id_empresa") != user.id_empresa
        ):
            raise HTTPException(
                status_code=404,
                detail="Operario no encontrado"
            )

```

### COND-0565: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:155. Condición: `if operario.get("estado") != "ACTIVO":`.

```python
        if operario.get("estado") != "ACTIVO":
            raise HTTPException(
                status_code=409,
                detail="El operario está inactivo"
            )

```

### COND-0566: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:161. Condición: `if ( operario.get("id_almacen") != orden["id_almacen"] ):`.

```python
        if (
            operario.get("id_almacen")
            != orden["id_almacen"]
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "El operario no pertenece "
                    "al almacén de la orden"
                )
            )

        # ----------------------------------------------------
        # PRE-VALIDACION (antes de crear nada)
        #
        # - inventario del producto de la línea, dentro
        #   del almacén del operario
        # - temperatura obligatoria si el producto es
        #   refrigerado (422)
        # - rack DISPONIBLE, con kg libres para todo lo
        #   aceptado en esta recepción y temperatura
        #   compatible (409)
        # ----------------------------------------------------

```

### COND-0567: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:211. Condición: `if ( inventario["id_producto"] != producto.get("id_producto") ):`.

```python
            if (
                inventario["id_producto"]
                != producto.get("id_producto")
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "El inventario seleccionado "
                        "no corresponde al producto "
                        "de la orden"
                    )
                )

```

### COND-0568: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:224. Condición: `if ( producto.get("requiere_refrigeracion") and detalle.temperatura_recepcion is None ):`.

```python
            if (
                producto.get("requiere_refrigeracion")
                and detalle.temperatura_recepcion is None
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Indique la temperatura de recepción: "
                        f"{producto.get('nombre')} es refrigerado"
                    )
                )

```

### COND-0569: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:236. Condición: `if detalle.estado_recepcion.value == "EN_EVALUACION":`.

```python
            if detalle.estado_recepcion.value == "EN_EVALUACION":
                continue

```

### COND-0570: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:244. Condición: `if aceptada <= 0:`.

```python
            if aceptada <= 0:
                continue

```

### COND-0571: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:249. Condición: `if id_rack not in racks:`.

```python
            if id_rack not in racks:

                racks[id_rack] = await (
                    RackService.enriquecer_uno(
                        await RackRepository.obtener_por_id(
                            id_rack
                        )
                    )
                )

```

### COND-0572: RecepcionMercaderiaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:265. Condición: `if motivo:`.

```python
            if motivo:
                raise HTTPException(
                    status_code=409,
                    detail=motivo
                )

            # Descontar para las siguientes líneas del mismo rack
```

### COND-0573: RecepcionMercaderiaService.obtener_por_id

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recepcion_mercaderia_service.py:307. Condición: `if not recepcion:`.

```python
        if not recepcion:
            raise HTTPException(
                status_code=404,
                detail="Recepción no encontrada"
            )

```

### COND-0574: RecomendacionService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:83. Condición: `if recomendacion_existente:`.

```python
        if recomendacion_existente:

            datos_actualizados = {
                "nivel_riesgo":
                    data.nivel_riesgo.value,

                "id_alerta":
                    data.id_alerta,

                "cantidad_minima":
                    data.cantidad_minima,

                "cantidad_recomendada":
                    data.cantidad_recomendada,

                "cantidad_segura":
                    data.cantidad_segura,

                "forecast_7d":
                    data.forecast_7d,

                "explicacion":
                    data.explicacion,

                "origen":
                    data.origen,

                "fecha_actualizacion":
                    ahora
            }

            return (
                await self.repository.actualizar(
                    recomendacion_existente[
                        "id_recomendacion"
                    ],
                    datos_actualizados
                )
            )

```

### COND-0575: RecomendacionService.obtener

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:201. Condición: `if recomendacion is None:`.

```python
        if recomendacion is None:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Recomendación "
                    "no encontrada"
                )
            )

```

### COND-0576: RecomendacionService.solicitar_cambios

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:277. Condición: `if recomendacion.get("id_empresa") != data.id_empresa:`.

```python
        if recomendacion.get("id_empresa") != data.id_empresa:
            raise HTTPException(status_code=403, detail="Empresa no autorizada")
```

### COND-0577: RecomendacionService.solicitar_cambios

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:279. Condición: `if recomendacion["estado"] not in { EstadoRecomendacion.VALIDADA_OPERARIO.value, EstadoRecomendacion.CAMBIOS_SOLICITADOS.value, }:`.

```python
        if recomendacion["estado"] not in {
            EstadoRecomendacion.VALIDADA_OPERARIO.value,
            EstadoRecomendacion.CAMBIOS_SOLICITADOS.value,
        }:
            raise HTTPException(status_code=409, detail="La recomendación no está pendiente de decisión")

```

### COND-0578: RecomendacionService.rechazar_por_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:307. Condición: `if recomendacion.get("id_empresa") != data.id_empresa:`.

```python
        if recomendacion.get("id_empresa") != data.id_empresa:
            raise HTTPException(status_code=403, detail="Empresa no autorizada")
```

### COND-0579: RecomendacionService.rechazar_por_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:309. Condición: `if recomendacion["estado"] not in { EstadoRecomendacion.VALIDADA_OPERARIO.value, EstadoRecomendacion.CAMBIOS_SOLICITADOS.value, }:`.

```python
        if recomendacion["estado"] not in {
            EstadoRecomendacion.VALIDADA_OPERARIO.value,
            EstadoRecomendacion.CAMBIOS_SOLICITADOS.value,
        }:
            raise HTTPException(status_code=409, detail="La recomendación no está pendiente de decisión")

```

### COND-0580: RecomendacionService.actualizar_propuesta

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:338. Condición: `if recomendacion["estado"] != EstadoRecomendacion.CAMBIOS_SOLICITADOS.value:`.

```python
        if recomendacion["estado"] != EstadoRecomendacion.CAMBIOS_SOLICITADOS.value:
            raise HTTPException(status_code=409, detail="No hay cambios solicitados para esta recomendación")

```

### COND-0581: RecomendacionService.actualizar_propuesta

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:342. Condición: `if not cambios:`.

```python
        if not cambios:
            raise HTTPException(status_code=400, detail="Debe indicar al menos un cambio permitido")
```

### COND-0582: RecomendacionService.aprobar_por_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:360. Condición: `if recomendacion.get("id_empresa") != data.id_empresa:`.

```python
        if recomendacion.get("id_empresa") != data.id_empresa:
            raise HTTPException(status_code=403, detail="Empresa no autorizada")
```

### COND-0583: RecomendacionService.aprobar_por_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:362. Condición: `if recomendacion["estado"] != EstadoRecomendacion.VALIDADA_OPERARIO.value:`.

```python
        if recomendacion["estado"] != EstadoRecomendacion.VALIDADA_OPERARIO.value:
            raise HTTPException(status_code=409, detail="La recomendación debe estar validada por Operario")

```

### COND-0584: RecomendacionService.aprobar_por_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:368. Condición: `if existing_order:`.

```python
        if existing_order:
            if existing_order.get("estado") == "PENDIENTE":
                existing_order = await self.orden_reposicion_service.aprobar(
                    existing_order["id_orden_reposicion"]
                )
            return {
                "recomendacion": recomendacion,
                "orden": existing_order,
            }

```

### COND-0585: RecomendacionService.aprobar_por_empresa

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:369. Condición: `if existing_order.get("estado") == "PENDIENTE":`.

```python
            if existing_order.get("estado") == "PENDIENTE":
                existing_order = await self.orden_reposicion_service.aprobar(
                    existing_order["id_orden_reposicion"]
                )
```

### COND-0586: RecomendacionService.cambiar_estado

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:443. Condición: `if data.estado.value not in transiciones_validas.get( estado_actual, set() ):`.

```python
        if data.estado.value not in transiciones_validas.get(
            estado_actual,
            set()
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"No se puede cambiar una recomendación "
                    f"{estado_actual} a {data.estado.value}"
                )
            )

```

### COND-0587: RecomendacionService.cambiar_estado

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:467. Condición: `if ( data.estado == EstadoRecomendacion.APLICADA ):`.

```python
        if (
            data.estado
            == EstadoRecomendacion.APLICADA
        ):

            datos[
                "fecha_aplicacion"
            ] = ahora

```

### COND-0588: RecomendacionService.cambiar_estado

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:481. Condición: `if data.estado == EstadoRecomendacion.VALIDADA_OPERARIO:`.

```python
        if data.estado == EstadoRecomendacion.VALIDADA_OPERARIO:
            try:
                notificacion = await (
                    self.notification_service
                    .enviar_solicitud_aprobacion(
                        id_recomendacion,
                        id_operario
                    )
                )
            except Exception as exc:
                notificacion = {
                    "status": "PENDIENTE",
                    "reason": str(exc)
                }

            resultado = await self.repository.actualizar(
                id_recomendacion,
                {
                    "notificacion_aprobacion": notificacion
                }
            )

```

### COND-0589: RecomendacionService.crear_orden_desde_recomendacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:532. Condición: `if ( recomendacion.get("estado") != EstadoRecomendacion.APROBADA_EMPRESA.value ):`.

```python
        if (
            recomendacion.get("estado")
            != EstadoRecomendacion.APROBADA_EMPRESA.value
        ):

            raise HTTPException(
                status_code=409,
                detail=(
                    "La recomendación debe estar aprobada "
                    "por la empresa antes de generar la orden"
                )
            )

        # ----------------------------------------------------
        # 3. VALIDAR TIPO
        # ----------------------------------------------------

```

### COND-0590: RecomendacionService.crear_orden_desde_recomendacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:549. Condición: `if ( recomendacion.get( "tipo_recomendacion" ) != "REABASTECER" ):`.

```python
        if (
            recomendacion.get(
                "tipo_recomendacion"
            )
            != "REABASTECER"
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Solo una recomendación de "
                    "REABASTECER puede generar "
                    "una orden de reposición"
                )
            )

        # ----------------------------------------------------
        # 4. DATOS NECESARIOS
        # ----------------------------------------------------

```

### COND-0591: RecomendacionService.crear_orden_desde_recomendacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:593. Condición: `if not id_empresa:`.

```python
        if not id_empresa:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La recomendación no tiene "
                    "id_empresa"
                )
            )

```

### COND-0592: RecomendacionService.crear_orden_desde_recomendacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:603. Condición: `if not id_almacen:`.

```python
        if not id_almacen:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La recomendación no tiene "
                    "id_almacen"
                )
            )

```

### COND-0593: RecomendacionService.crear_orden_desde_recomendacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:613. Condición: `if not id_producto:`.

```python
        if not id_producto:

            raise HTTPException(
                status_code=400,
                detail=(
                    "La recomendación no tiene "
                    "id_producto"
                )
            )

```

### COND-0594: RecomendacionService.crear_orden_desde_recomendacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:623. Condición: `if ( cantidad_recomendada is None or cantidad_recomendada <= 0 ):`.

```python
        if (
            cantidad_recomendada is None
            or cantidad_recomendada <= 0
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "La recomendación no contiene "
                    "una cantidad de reposición válida"
                )
            )

        # ----------------------------------------------------
        # 5. CREAR ORDEN PENDIENTE
        # ----------------------------------------------------

```

### COND-0595: RecomendacionService.crear_orden_desde_recomendacion

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/recomendacion_service.py:680. Condición: `if not id_orden:`.

```python
        if not id_orden:

            raise HTTPException(
                status_code=500,
                detail=(
                    "La orden fue creada pero no "
                    "se obtuvo id_orden_reposicion"
                )
            )

        # ----------------------------------------------------
        # 6. CREAR DETALLE
        #
        # Si falla el detalle, eliminamos la orden
        # PENDIENTE para no dejar una orden vacía.
        # ----------------------------------------------------

```

### COND-0596: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:28. Condición: `if re.fullmatch(r'\s*(hola|buenos dias|buenas tardes|buenas noches|hey)(\s+saiki)?[!,.?\s]*', text):`.

```python
        if re.fullmatch(r'\s*(hola|buenos dias|buenas tardes|buenas noches|hey)(\s+saiki)?[!,.?\s]*', text):
            return SaikiIntent('greeting', frozenset())
```

### COND-0597: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:33. Condición: `if analysis and replenishment:`.

```python
        if analysis and replenishment:
            return SaikiIntent('analysis', cls.MIXED_TOOLS, horizon)
```

### COND-0598: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:40. Condición: `if listing and inventory and not other_operation:`.

```python
        if listing and inventory and not other_operation:
            if location:
                return SaikiIntent('inventory_detail', frozenset({'get_warehouse_status'}))
            if quantities or re.search(r'mencion|enumera|listado|lista\b|todos.*productos', text):
                return SaikiIntent('product_quantities', frozenset({'get_warehouse_status', 'get_product'}))
```

### COND-0599: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:41. Condición: `if location:`.

```python
            if location:
                return SaikiIntent('inventory_detail', frozenset({'get_warehouse_status'}))
```

### COND-0600: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:43. Condición: `if quantities or re.search(r'mencion|enumera|listado|lista\b|todos.*productos', text):`.

```python
            if quantities or re.search(r'mencion|enumera|listado|lista\b|todos.*productos', text):
                return SaikiIntent('product_quantities', frozenset({'get_warehouse_status', 'get_product'}))
```

### COND-0601: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:46. Condición: `if predictive or (horizon is not None and cls._history_has_predictive_request(history)):`.

```python
        if predictive or (horizon is not None and cls._history_has_predictive_request(history)):
            return SaikiIntent('predictive', cls.PREDICTIVE_TOOLS, horizon if horizon is not None else 7)
```

### COND-0602: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:49. Condición: `if not qualified and re.search(r'\bcuantos? productos\b', text) and re.search(r'\btengo\b', text):`.

```python
        if not qualified and re.search(r'\bcuantos? productos\b', text) and re.search(r'\btengo\b', text):
            return SaikiIntent('product_count', frozenset({'get_product'}))
```

### COND-0603: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:51. Condición: `if not qualified and re.search(r'\b(?:tengo|hay|existen) almacenes\b', text):`.

```python
        if not qualified and re.search(r'\b(?:tengo|hay|existen) almacenes\b', text):
            return SaikiIntent('warehouses', frozenset({'get_warehouse_status'}))
```

### COND-0604: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:53. Condición: `if not qualified and re.search(r'\bcuanto (?:stock|inventario)\b', text) and re.search(r'\btengo\b', text):`.

```python
        if not qualified and re.search(r'\bcuanto (?:stock|inventario)\b', text) and re.search(r'\btengo\b', text):
            return SaikiIntent('stock_total', frozenset({'get_warehouse_status'}))
```

### COND-0605: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:65. Condición: `if matches:`.

```python
        if matches:
            tools = frozenset().union(*(tools for _, tools in matches))
            return SaikiIntent(matches[0][0] if len(matches) == 1 else 'mixed', tools)
```

### COND-0606: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:68. Condición: `if re.search(r'\bmuestrame\s+(?:el|la)\b', text):`.

```python
        if re.search(r'\bmuestrame\s+(?:el|la)\b', text):
            return SaikiIntent('products', frozenset({'get_product', 'get_warehouse_status'}))
```

### COND-0607: SaikiIntentRouter.classify

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:70. Condición: `if re.search(r'inventario|almacen', text) and re.search(r'como|estado|resumen|situacion|panorama', text):`.

```python
        if re.search(r'inventario|almacen', text) and re.search(r'como|estado|resumen|situacion|panorama', text):
            return SaikiIntent('general', frozenset({'get_warehouse_status'}))
```

### COND-0608: SaikiIntentRouter._horizon_days

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:83. Condición: `if match:`.

```python
        if match:
            return int(match[1]) * (7 if 'semana' in match[2] else 30 if 'mes' in match[2] else 1)
```

### COND-0609: SaikiIntentRouter._horizon_days

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:85. Condición: `if re.search(r'\b(?:una|la proxima|esta) semana\b', text):`.

```python
        if re.search(r'\b(?:una|la proxima|esta) semana\b', text):
            return 7
```

### COND-0610: SaikiIntentRouter._horizon_days

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_intent_router.py:87. Condición: `if re.search(r'\b(?:un|el proximo|este) mes\b', text):`.

```python
        if re.search(r'\b(?:un|el proximo|este) mes\b', text):
            return 30
```

### COND-0611: módulo.inventory_summary

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_inventory_summary.py:22. Condición: `if user is None:`.

```python
    if user is None:
        raise HTTPException(401, "Se requiere autenticación para consultar el inventario.")
```

### COND-0612: módulo.inventory_summary

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_inventory_summary.py:24. Condición: `if user.es_proveedor:`.

```python
    if user.es_proveedor:
        raise HTTPException(403, "No tiene acceso al inventario.")
```

### COND-0613: módulo.inventory_summary

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_inventory_summary.py:27. Condición: `if user.es_operario:`.

```python
    if user.es_operario:
        warehouses = [row for row in warehouses if identifier(row, "id_almacen") == user.id_almacen]
```

### COND-0614: módulo.inventory_summary

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_inventory_summary.py:42. Condición: `if not numeric(stock) or stock < 0:`.

```python
        if not numeric(stock) or stock < 0:
            raise HTTPException(503, "No se pudo verificar el stock: existen cantidades inválidas.")
```

### COND-0615: módulo.inventory_summary

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_inventory_summary.py:57. Condición: `if stock > 0 and numeric(minimum) and minimum >= 0:`.

```python
        if stock > 0 and numeric(minimum) and minimum >= 0:
            status = "Bajo stock" if stock <= minimum else "Disponible"
```

### COND-0616: módulo.number

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:6. Condición: `if value is None or not isinstance(value, (int, float)) or not math.isfinite(value):`.

```python
    if value is None or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
```

### COND-0617: módulo.operational_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:13. Condición: `if kind == "alerts":`.

```python
    if kind == "alerts":
        level = str(rows[0].get("nivel_riesgo", "")).lower() if count == 1 else ""
        detail = f" de riesgo {level}" if level in {"bajo", "medio", "alto", "critico"} else ""
        return "No tienes alertas activas." if not count else f"Tienes {count} alerta{'s' if count != 1 else ''} activa{'s' if count != 1 else ''}{detail}. Puedes consultar los detalles en los datos adjuntos."
```

### COND-0618: módulo.operational_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:17. Condición: `if kind == "movements":`.

```python
    if kind == "movements":
        if not count:
            return "No encontré movimientos recientes."
        quantity = number(rows[0].get("cantidad"))
        movement = rows[0].get("tipo_movimiento")
        if count == 1 and quantity is not None and movement in {"SALIDA", "ENTRADA"}:
            return f"Encontré un movimiento reciente: una {movement.lower()} de {quantity} {'unidad' if quantity == '1' else 'unidades'}."
        return f"Encontré {count} movimiento{'s' if count != 1 else ''} reciente{'s' if count != 1 else ''}. Los detalles están disponibles en la respuesta."
```

### COND-0619: módulo.operational_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:18. Condición: `if not count:`.

```python
        if not count:
            return "No encontré movimientos recientes."
```

### COND-0620: módulo.operational_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:22. Condición: `if count == 1 and quantity is not None and movement in {"SALIDA", "ENTRADA"}:`.

```python
        if count == 1 and quantity is not None and movement in {"SALIDA", "ENTRADA"}:
            return f"Encontré un movimiento reciente: una {movement.lower()} de {quantity} {'unidad' if quantity == '1' else 'unidades'}."
```

### COND-0621: módulo.operational_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:25. Condición: `if kind == "recommendations":`.

```python
    if kind == "recommendations":
        pending = [row for row in rows if row.get("estado") in {"PENDIENTE", "VALIDADA_OPERARIO", "CAMBIOS_SOLICITADOS", "APROBADA_EMPRESA", "ACEPTADA"}]
        if not pending:
            return "No hay recomendaciones pendientes de reposición registradas."
        if len(pending) == 1 and number(pending[0].get("cantidad_recomendada")) is not None:
            return f"La recomendación registrada propone reponer {number(pending[0]['cantidad_recomendada'])} unidades. Revisa el producto y los detalles antes de iniciar una compra."
        return f"Tienes {len(pending)} {'recomendación pendiente' if len(pending) == 1 else 'recomendaciones pendientes'}. Revisa las cantidades propuestas antes de iniciar una compra."
```

### COND-0622: módulo.operational_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:27. Condición: `if not pending:`.

```python
        if not pending:
            return "No hay recomendaciones pendientes de reposición registradas."
```

### COND-0623: módulo.operational_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:29. Condición: `if len(pending) == 1 and number(pending[0].get("cantidad_recomendada")) is not None:`.

```python
        if len(pending) == 1 and number(pending[0].get("cantidad_recomendada")) is not None:
            return f"La recomendación registrada propone reponer {number(pending[0]['cantidad_recomendada'])} unidades. Revisa el producto y los detalles antes de iniciar una compra."
```

### COND-0624: módulo.forecast_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:37. Condición: `if total is None:`.

```python
    if total is None:
        return "No pude obtener una estimación de demanda para los próximos 7 días."
```

### COND-0625: módulo.risk_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:47. Condición: `if not valid:`.

```python
    if not valid:
        return "No pude obtener un nivel de riesgo verificado con los datos disponibles."
```

### COND-0626: módulo.risk_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:55. Condición: `if stock == "0":`.

```python
    if stock == "0":
        reason = " porque no quedan existencias"
```

### COND-0627: módulo.risk_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_responses.py:57. Condición: `elif coverage is not None and lead is not None:`.

```python
    elif coverage is not None and lead is not None:
        reason = f": la cobertura es de {coverage} {'día' if coverage == '1' else 'días'} y la reposición tarda {lead} {'día' if lead == '1' else 'días'}"
```

### COND-0628: SaikiService.health

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:65. Condición: `if self.settings.ollama_model not in models:`.

```python
        if self.settings.ollama_model not in models:
            return {
                "status": "unavailable",
                "ready": False,
                **base,
                "detail": f"El modelo {self.settings.ollama_model} no está descargado en Ollama.",
            }
```

### COND-0629: SaikiService.ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:102. Condición: `if isinstance(exc, SaikiDatabaseError) or "MongoDB" in str(exc) or "motor" in str(exc):`.

```python
            if isinstance(exc, SaikiDatabaseError) or "MongoDB" in str(exc) or "motor" in str(exc):
                raise HTTPException(status_code=503, detail="No se pudo verificar el inventario en MongoDB.") from exc
```

### COND-0630: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:119. Condición: `if intent.kind == "greeting":`.

```python
        if intent.kind == "greeting":
            return self._simple_response(
                "¡Hola, soy Saiki!",
                source="router",
            )
```

### COND-0631: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:124. Condición: `if intent.horizon_days is not None and intent.horizon_days not in self.intent_router.SUPPORTED_HORIZONS:`.

```python
        if intent.horizon_days is not None and intent.horizon_days not in self.intent_router.SUPPORTED_HORIZONS:
            return self._clarification_response(
                "Actualmente puedo predecir la demanda de los próximos 7 días. El horizonte solicitado todavía no está disponible."
            )
```

### COND-0632: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:128. Condición: `if intent.horizon_days is not None:`.

```python
        if intent.horizon_days is not None:
            context["horizonte_dias_solicitado"] = intent.horizon_days
            context["tipo_prediccion"] = "demanda"
```

### COND-0633: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:131. Condición: `if data.id_inventario and user is not None:`.

```python
        if data.id_inventario and user is not None:
            context["inventario"] = await self._authorized_tool("get_inventory", {"id_inventario": data.id_inventario}, user)
```

### COND-0634: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:133. Condición: `if data.id_producto and user is not None:`.

```python
        if data.id_producto and user is not None:
            context["producto"] = await self._authorized_tool("get_product", {"id_producto": data.id_producto}, user)
```

### COND-0635: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:135. Condición: `if intent.kind in {"product_quantities", "inventory_detail"} and not data.id_producto and not data.id_inventario:`.

```python
        if intent.kind in {"product_quantities", "inventory_detail"} and not data.id_producto and not data.id_inventario:
            return await self._fast_detail_response(data, context, user, intent.kind)
```

### COND-0636: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:137. Condición: `if intent.kind in {"alerts", "movements", "recommendations"} and not data.id_producto:`.

```python
        if intent.kind in {"alerts", "movements", "recommendations"} and not data.id_producto:
            return await self._fast_operational_response(intent.kind, data, context, user)
```

### COND-0637: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:139. Condición: `if intent.kind in {"predictive", "risk"} and not re.search(r"\b(?:alerta|movimiento|recomend|comprar)", self.intent_router._normalize(data.message or "")):`.

```python
        if intent.kind in {"predictive", "risk"} and not re.search(r"\b(?:alerta|movimiento|recomend|comprar)", self.intent_router._normalize(data.message or "")):
            return await self._fast_analysis_response(intent.kind, data, context, user)
```

### COND-0638: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:141. Condición: `if intent.kind == "products" and not data.id_inventario and not data.id_producto:`.

```python
        if intent.kind == "products" and not data.id_inventario and not data.id_producto:
            return await self._fast_products_response(data, context, user)
```

### COND-0639: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:144. Condición: `if location_name and not data.id_inventario and not data.id_producto:`.

```python
        if location_name and not data.id_inventario and not data.id_producto:
            return await self._fast_location_response(location_name, context, user)
```

### COND-0640: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:146. Condición: `if ( intent.kind in {"general", "product_count", "warehouses", "stock_total"} and not data.id_inventario and not data.id_producto ):`.

```python
        if (
            intent.kind in {"general", "product_count", "warehouses", "stock_total"}
            and not data.id_inventario
            and not data.id_producto
        ):
            try:
                return await self._fast_current_response(context, user, intent.kind, data)
            except SaikiDatabaseError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="No se pudo verificar el inventario en MongoDB.",
                ) from exc
            except RuntimeError as exc:
                logger.exception("saiki_request_error type=unexpected_runtime")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Saiki no está disponible en este momento.",
                ) from exc
```

### COND-0641: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:165. Condición: `if intent.kind == "analysis":`.

```python
        if intent.kind == "analysis":
            summary, summary_source = await self._execute_tool("get_warehouse_status", {"include_visual": True}, user)
            recommendations, recommendation_source = await self._execute_tool("get_recommendations", {}, user)
            analysis_data = {"get_warehouse_status": summary, "get_recommendations": recommendations}
            analysis_sources = {summary_source, recommendation_source}
            context["datos_verificados_analisis"] = analysis_data
```

### COND-0642: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:214. Condición: `if analysis_data:`.

```python
        if analysis_data:
            tool_data = {**analysis_data, **tool_data}
            sources.update(analysis_sources)
```

### COND-0643: SaikiService._ask

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:217. Condición: `if "LIGHTGBM" in sources and intent.horizon_days == 7:`.

```python
        if "LIGHTGBM" in sources and intent.horizon_days == 7:
            answer = "La proyección corresponde a la demanda de los próximos 7 días. " + answer
```

### COND-0644: SaikiService._fast_detail_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:243. Condición: `if kind == "product_quantities":`.

```python
        if kind == "product_quantities":
            products, product_source = await self._execute_tool("get_product", {}, user)
            sources.add(product_source)
            stock = {row["id_producto"]: row["stock_actual"] for row in summary["stock_por_producto"]}
            rows = [{"id_producto": item["id_producto"], "product_name": item.get("nombre"),
                     "stock": stock.get(item["id_producto"]), "has_inventory": item["id_producto"] in stock} for item in products]
            data["product_quantities"] = rows
            answer = "; ".join(f"{row['product_name'] or 'Producto sin nombre'}: {row['stock']} unidades" if row['has_inventory'] else f"{row['product_name'] or 'Producto sin nombre'}: sin inventario registrado" for row in rows)
            answer = answer + "." if answer else "No tienes productos registrados en tu catálogo."
```

### COND-0645: SaikiService._fast_detail_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:259. Condición: `if structured["pagination"]["total_pages"] > 1:`.

```python
            if structured["pagination"]["total_pages"] > 1:
                answer += f" Página {request_data.page} de {structured['pagination']['total_pages']}; puedes consultar las demás páginas."
```

### COND-0646: SaikiService._fast_detail_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:263. Condición: `if kind == "product_quantities":`.

```python
        if kind == "product_quantities":
            response["visualization"] = {"type": "table", "rows_path": "data.product_quantities", "columns": [{"key": "product_name", "label": "Producto"}, {"key": "stock", "label": "Stock"}, {"key": "has_inventory", "label": "Inventario registrado"}]}
```

### COND-0647: SaikiService._fast_operational_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:272. Condición: `if kind == "movements" and re.search(r"\bsalidas?\b|\bentradas?\b", text):`.

```python
        if kind == "movements" and re.search(r"\bsalidas?\b|\bentradas?\b", text):
            movement_type = "SALIDA" if re.search(r"\bsalidas?\b", text) else "ENTRADA"
            rows = [row for row in rows if row.get("tipo_movimiento") == movement_type]
            answer = f"Encontré {len(rows)} {movement_type.lower()}{'s' if len(rows) != 1 else ''} entre los movimientos recientes consultados."
```

### COND-0648: SaikiService._fast_products_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:282. Condición: `if re.search(r"quedan|disponibles|existencias", text):`.

```python
        if re.search(r"quedan|disponibles|existencias", text):
            summary, source = await self._execute_tool("get_warehouse_status", {}, user)
            products = [row for row in summary.get("stock_por_producto", []) if row.get("stock_actual", 0) > 0]
            details = "; ".join(f"{row.get('nombre') or 'Producto sin nombre'}: {row['stock_actual']} unidades" for row in products[:5])
            answer = f"Tienes estas existencias: {details}." if products else "No encontré productos con existencias positivas en tus inventarios visibles."
            if len(products) == 1:
                answer = f"Quedan {products[0]['stock_actual']} unidades de {products[0].get('nombre') or 'un producto sin nombre registrado'}."
            if len(products) > 5:
                answer += " Puedes consultar el resto en los datos adjuntos."
            return self._verified_response(answer, context, {"get_warehouse_status": summary}, {source})
```

### COND-0649: SaikiService._fast_products_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:287. Condición: `if len(products) == 1:`.

```python
            if len(products) == 1:
                answer = f"Quedan {products[0]['stock_actual']} unidades de {products[0].get('nombre') or 'un producto sin nombre registrado'}."
```

### COND-0650: SaikiService._fast_products_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:289. Condición: `if len(products) > 5:`.

```python
            if len(products) > 5:
                answer += " Puedes consultar el resto en los datos adjuntos."
```

### COND-0651: SaikiService._fast_products_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:294. Condición: `if selected:`.

```python
        if selected:
            context["producto_consultado"] = {"id_producto": selected["id_producto"], "nombre": selected.get("nombre")}
            answer = f"{selected.get('nombre') or 'El producto'} está registrado en tu catálogo."
```

### COND-0652: SaikiService._fast_products_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:297. Condición: `elif "muestrame" in text:`.

```python
        elif "muestrame" in text:
            answer = "No pude identificar un único producto de tu catálogo. Indica su nombre completo para consultarlo."
```

### COND-0653: SaikiService._product_from_history

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:305. Condición: `if item.get("role") != "user":`.

```python
            if item.get("role") != "user":
                continue
```

### COND-0654: SaikiService._product_from_history

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:309. Condición: `if len(matches) == 1:`.

```python
            if len(matches) == 1:
                return matches[0]
```

### COND-0655: SaikiService._product_from_history

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:311. Condición: `if len(matches) > 1:`.

```python
            if len(matches) > 1:
                return None
```

### COND-0656: SaikiService._fast_analysis_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:320. Condición: `if request_data.id_producto:`.

```python
        if request_data.id_producto:
            product, product_source = await self._execute_tool("get_product", {"id_producto": request_data.id_producto}, user)
            sources.add(product_source)
            data["get_product"] = product
            inventories = [row for row in inventories if row.get("id_producto") == request_data.id_producto]
```

### COND-0657: SaikiService._fast_analysis_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:325. Condición: `elif request_data.history:`.

```python
        elif request_data.history:
            products, product_source = await self._execute_tool("get_product", {}, user)
            sources.add(product_source)
            data["get_product"] = products
            product = self._product_from_history(products, request_data.history)
            if product:
                inventories = [row for row in inventories if row.get("id_producto") == product["id_producto"]]
                context["producto_consultado"] = {"id_producto": product["id_producto"], "nombre": product.get("nombre")}
            elif any(item.get("role") == "user" and re.search(r"muestrame|donde", self.intent_router._normalize(str(item.get("content", "")))) for item in request_data.history[-4:]):
                return self._verified_response("No pude identificar un único producto de tu catálogo en el historial. ¿Qué producto deseas consultar?", context, data, sources)
```

### COND-0658: SaikiService._fast_analysis_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:330. Condición: `if product:`.

```python
            if product:
                inventories = [row for row in inventories if row.get("id_producto") == product["id_producto"]]
                context["producto_consultado"] = {"id_producto": product["id_producto"], "nombre": product.get("nombre")}
```

### COND-0659: SaikiService._fast_analysis_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:333. Condición: `elif any(item.get("role") == "user" and re.search(r"muestrame|donde", self.intent_router._normalize(str(item.get("content", "")))) for item in request_data.history[-4:]):`.

```python
            elif any(item.get("role") == "user" and re.search(r"muestrame|donde", self.intent_router._normalize(str(item.get("content", "")))) for item in request_data.history[-4:]):
                return self._verified_response("No pude identificar un único producto de tu catálogo en el historial. ¿Qué producto deseas consultar?", context, data, sources)
```

### COND-0660: SaikiService._fast_analysis_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:335. Condición: `if not inventories:`.

```python
        if not inventories:
            return self._verified_response("No hay inventarios visibles para calcular esta consulta. Registra existencias o indica un producto con inventario.", context, data, sources)
```

### COND-0661: SaikiService._fast_analysis_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:339. Condición: `if not is_risk and len(inventories) != 1:`.

```python
        if not is_risk and len(inventories) != 1:
            return self._verified_response("¿Para qué producto y ubicación deseas consultar la demanda de los próximos 7 días?", context, data, sources)
```

### COND-0662: SaikiService._fast_analysis_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:341. Condición: `if not is_risk:`.

```python
        if not is_risk:
            forecast, forecast_source = await self._execute_tool("get_forecast", {"id_inventario": inventories[0]["id_inventario"], "horizonte_dias": 7}, user)
            data["get_forecast"] = forecast
            sources.add(forecast_source)
            return self._verified_response(forecast_answer(forecast), context, data, sources)
```

### COND-0663: SaikiService._fast_analysis_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:351. Condición: `if product_names.get(inventory.get("id_producto")):`.

```python
            if product_names.get(inventory.get("id_producto")):
                result["nombre_producto"] = product_names[inventory["id_producto"]]
```

### COND-0664: SaikiService._fast_analysis_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:357. Condición: `if summary.get("total_registros_inventario", len(inventories)) > len(summary.get("inventarios", [])):`.

```python
        if summary.get("total_registros_inventario", len(inventories)) > len(summary.get("inventarios", [])):
            response["warnings"].append("El riesgo se evaluó solo para los inventarios incluidos en el resumen; no representa todos los inventarios.")
```

### COND-0665: SaikiService._location_name

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:364. Condición: `if not match:`.

```python
        if not match:
            return None
```

### COND-0666: SaikiService._location_name

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:367. Condición: `if re.search(r"\b(?:y|o|en|cu[aá]nt|explica|busco)\b", name, re.IGNORECASE):`.

```python
        if re.search(r"\b(?:y|o|en|cu[aá]nt|explica|busco)\b", name, re.IGNORECASE):
            return None
```

### COND-0667: SaikiService._fast_location_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:375. Condición: `if not matches:`.

```python
        if not matches:
            matches = [product for product in products if re.search(r"\b" + re.escape(normalized) + r"\b", self.intent_router._normalize(product.get("nombre", "")))]
```

### COND-0668: SaikiService._fast_location_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:379. Condición: `if not matches:`.

```python
        if not matches:
            answer = f"No encontré {name} en el catálogo de tu empresa."
```

### COND-0669: SaikiService._fast_location_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:381. Condición: `elif len(matches) > 1:`.

```python
        elif len(matches) > 1:
            answer = f"Encontré varios productos que coinciden con {name}. ¿Cuál deseas localizar?"
```

### COND-0670: SaikiService._fast_location_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:389. Condición: `if not locations:`.

```python
            if not locations:
                answer = f"{product['nombre']} está registrado, pero no encontré una ubicación de inventario en tus almacenes visibles."
```

### COND-0671: SaikiService._fast_location_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:391. Condición: `elif len(locations) == 1:`.

```python
            elif len(locations) == 1:
                rack = locations[0].get("rack") or {}
                label = rack.get("codigo") or rack.get("nombre")
                answer = f"{product['nombre']} está en el rack {label}." if label else f"{product['nombre']} tiene una ubicación registrada; puedes consultarla en el detalle de inventario."
```

### COND-0672: SaikiService._fast_current_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:423. Condición: `if "MongoDB" in str(exc) or "motor" in str(exc):`.

```python
            if "MongoDB" in str(exc) or "motor" in str(exc):
                raise SaikiDatabaseError(str(exc)) from exc
```

### COND-0673: SaikiService._fast_current_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:432. Condición: `if kind == "product_count":`.

```python
        if kind == "product_count":
            answer = f"Tienes {len(result)} {'producto registrado' if len(result) == 1 else 'productos registrados'} en tu catálogo."
```

### COND-0674: SaikiService._fast_current_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:434. Condición: `elif kind == "warehouses":`.

```python
        elif kind == "warehouses":
            count = result["total_almacenes"]
            answer = f"Tienes {count} {'almacén registrado' if count == 1 else 'almacenes registrados'} en PsiTwin." if count else "Actualmente no tienes almacenes registrados en PsiTwin. Te recomiendo crear tu primer almacén."
```

### COND-0675: SaikiService._fast_current_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:437. Condición: `elif kind == "stock_total":`.

```python
        elif kind == "stock_total":
            answer = f"Actualmente tienes {result['stock_total_unidades']} unidades en tu inventario."
```

### COND-0676: SaikiService._fast_current_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:441. Condición: `if result.get("estado_inventario") == "stock_positivo" and "inventory_summary" in result:`.

```python
            if result.get("estado_inventario") == "stock_positivo" and "inventory_summary" in result:
                summary = result["inventory_summary"]
                products_label = "producto diferente" if summary['distinct_products'] == 1 else "productos diferentes"
                warehouses_label = "almacén" if summary['warehouse_count'] == 1 else "almacenes"
                answer = f"Actualmente tienes {summary['distinct_products']} {products_label} y {summary['total_units']} unidades distribuidas en {summary['warehouse_count']} {warehouses_label}."
```

### COND-0677: SaikiService._fast_current_response

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:448. Condición: `if "inventory_summary" in result and kind == "general":`.

```python
        if "inventory_summary" in result and kind == "general":
            payload_data["inventory_summary"] = result["inventory_summary"]
            visualization = result["visualization"]
```

### COND-0678: SaikiService._natural_inventory_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:467. Condición: `if state == "sin_almacenes":`.

```python
        if state == "sin_almacenes":
            return (
                "Actualmente no tienes almacenes registrados en PsiTwin. Te "
                "recomiendo crear tu primer almacén para comenzar a gestionar "
                "el inventario."
            )
```

### COND-0679: SaikiService._natural_inventory_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:473. Condición: `if state == "almacen_sin_productos":`.

```python
        if state == "almacen_sin_productos":
            return (
                "Tu almacén está registrado, pero todavía no tienes productos "
                "registrados."
            )
```

### COND-0680: SaikiService._natural_inventory_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:478. Condición: `if state == "productos_sin_inventario":`.

```python
        if state == "productos_sin_inventario":
            return (
                "Tienes productos registrados, pero todavía no hay existencias "
                "de inventario asociadas."
            )
```

### COND-0681: SaikiService._natural_inventory_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:483. Condición: `if state == "stock_cero":`.

```python
        if state == "stock_cero":
            return (
                "Tienes productos registrados, pero actualmente sus existencias "
                "son cero."
            )
```

### COND-0682: SaikiService._natural_inventory_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:488. Condición: `if state == "stock_positivo":`.

```python
        if state == "stock_positivo":
            products = result.get("productos_distintos", 0)
            units = result.get("stock_total_unidades", 0)
            return (
                f"Actualmente tienes {products} {'producto distinto' if products == 1 else 'productos distintos'} y "
                f"{units} {'unidad registrada' if units == 1 else 'unidades registradas'} en tu inventario."
            )
```

### COND-0683: SaikiService._execute_tool

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:502. Condición: `if user is None:`.

```python
        if user is None:
            return await self.tools.execute(name, arguments)
```

### COND-0684: SaikiService._agent_loop

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:527. Condición: `if not isinstance(message, dict):`.

```python
            if not isinstance(message, dict):
                raise RuntimeError("Ollama devolvió un mensaje inválido.")
```

### COND-0685: SaikiService._agent_loop

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:530. Condición: `if not tool_calls:`.

```python
            if not tool_calls:
                answer = message.get("content")
                if not isinstance(answer, str) or not answer.strip():
                    raise RuntimeError("Ollama no devolvió una respuesta útil.")
                logger.info(
                    "saiki_agent_summary ollama_calls=%d tool_calls=%d",
                    ollama_calls,
                    tool_calls_count,
                )
                answer = self._clean_answer(answer)
                if not answer:
                    raise RuntimeError("Ollama solo devolvió razonamiento interno.")
                return answer, tool_data, sources

```

### COND-0686: SaikiService._agent_loop

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:532. Condición: `if not isinstance(answer, str) or not answer.strip():`.

```python
                if not isinstance(answer, str) or not answer.strip():
                    raise RuntimeError("Ollama no devolvió una respuesta útil.")
```

### COND-0687: SaikiService._agent_loop

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:540. Condición: `if not answer:`.

```python
                if not answer:
                    raise RuntimeError("Ollama solo devolvió razonamiento interno.")
```

### COND-0688: SaikiService._agent_loop

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:547. Condición: `if tool_names is not None and name not in tool_names:`.

```python
                if tool_names is not None and name not in tool_names:
                    raise ValueError(f"Tool no autorizada para esta consulta: {name}")
```

### COND-0689: SaikiService._agent_loop

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:552. Condición: `if call_key in seen_calls:`.

```python
                if call_key in seen_calls:
                    result, source = seen_calls[call_key]
                    logger.info("saiki_tool_duplicate name=%s", name)
```

### COND-0690: SaikiService._agent_loop

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:560. Condición: `if "MongoDB" in str(exc) or "motor" in str(exc):`.

```python
                        if "MongoDB" in str(exc) or "motor" in str(exc):
                            raise SaikiDatabaseError(str(exc)) from exc
```

### COND-0691: SaikiService._call_ollama_chat

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:623. Condición: `if connection.sock is not None:`.

```python
            if connection.sock is not None:
                connection.sock.settimeout(self.settings.ollama_read_timeout_seconds)
```

### COND-0692: SaikiService._call_ollama_chat

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:627. Condición: `if response.status >= 400:`.

```python
            if response.status >= 400:
                raise OllamaUnavailableError(
                    f"Ollama respondió HTTP {response.status}."
                )
```

### COND-0693: SaikiService._call_ollama_chat

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:638. Condición: `if connection is not None:`.

```python
            if connection is not None:
                connection.close()
```

### COND-0694: SaikiService._call_ollama_chat

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:644. Condición: `if not isinstance(result, dict):`.

```python
        if not isinstance(result, dict):
            raise RuntimeError("Ollama devolvió una respuesta inválida.")
```

### COND-0695: SaikiService._clean_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:651. Condición: `if "</think>" in answer:`.

```python
        if "</think>" in answer:
            answer = answer.rsplit("</think>", 1)[1]
```

### COND-0696: SaikiService._clean_answer

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:653. Condición: `if "<think>" in answer:`.

```python
        if "<think>" in answer:
            answer = answer.split("<think>", 1)[0]
```

### COND-0697: SaikiService._parse_tool_call

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:658. Condición: `if not isinstance(tool_call, dict):`.

```python
        if not isinstance(tool_call, dict):
            raise ValueError("Tool call inválida.")
```

### COND-0698: SaikiService._parse_tool_call

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:661. Condición: `if not isinstance(function, dict) or not isinstance(function.get("name"), str):`.

```python
        if not isinstance(function, dict) or not isinstance(function.get("name"), str):
            raise ValueError("Tool call inválida.")
```

### COND-0699: SaikiService._parse_tool_call

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:664. Condición: `if isinstance(arguments, str):`.

```python
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                raise ValueError("Los argumentos de la tool no son JSON válido.") from exc
```

### COND-0700: SaikiService._parse_tool_call

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:669. Condición: `if not isinstance(arguments, dict):`.

```python
        if not isinstance(arguments, dict):
            raise ValueError("Los argumentos de la tool deben ser un objeto.")
```

### COND-0701: SaikiService._warnings

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:689. Condición: `if "INVENTORY_RISK" in sources:`.

```python
        if "INVENTORY_RISK" in sources:
            warnings.append("El riesgo proviene de InventoryRiskService.")
```

### COND-0702: SaikiService._warnings

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:691. Condición: `if "LIGHTGBM" in sources:`.

```python
        if "LIGHTGBM" in sources:
            warnings.append("La predicción proviene del pipeline LightGBM.")
            warnings.append("La predicción depende del historial disponible y representa demanda, no stock futuro.")
            forecast = (data or {}).get("get_forecast")
            if isinstance(forecast, dict) and any(item.get("sin_datos", 0) > 0 for item in forecast.get("features_por_horizonte", {}).values() if isinstance(item, dict)):
                warnings.append("Hay variables sin datos en el modelo; interpreta la predicción con esa limitación.")
```

### COND-0703: SaikiService._warnings

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_service.py:695. Condición: `if isinstance(forecast, dict) and any(item.get("sin_datos", 0) > 0 for item in forecast.get("features_por_horizonte", {}).values() if isinstance(item, dict)):`.

```python
            if isinstance(forecast, dict) and any(item.get("sin_datos", 0) > 0 for item in forecast.get("features_por_horizonte", {}).values() if isinstance(item, dict)):
                warnings.append("Hay variables sin datos en el modelo; interpreta la predicción con esa limitación.")
```

### COND-0704: SaikiToolRegistry.execute

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:137. Condición: `if name not in self._handlers:`.

```python
        if name not in self._handlers:
            raise ValueError(f"Tool no autorizada: {name}")
```

### COND-0705: SaikiToolRegistry.execute

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:146. Condición: `if user is not None:`.

```python
        if user is not None:
            visible = await self._authorize(name, validated, user)
```

### COND-0706: SaikiToolRegistry.execute

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:151. Condición: `if name == "get_warehouse_status":`.

```python
            if name == "get_warehouse_status":
                return await handler(validated, user, visible), source
```

### COND-0707: SaikiToolRegistry.execute

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:153. Condición: `if name == "get_product":`.

```python
            if name == "get_product":
                return await handler(validated, user), source
```

### COND-0708: SaikiToolRegistry.execute

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:155. Condición: `if name in {"get_active_alerts", "get_recommendations", "get_recent_movements"}:`.

```python
            if name in {"get_active_alerts", "get_recommendations", "get_recent_movements"}:
                return await handler(validated, visible), source
```

### COND-0709: SaikiToolRegistry._authorize

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:162. Condición: `if name == "get_warehouse_status" and getattr(args, "include_visual", False) and not args.id_inventario:`.

```python
        if name == "get_warehouse_status" and getattr(args, "include_visual", False) and not args.id_inventario:
            # The visual summary traverses the authorized hierarchy once itself.
            return None
```

### COND-0710: SaikiToolRegistry._authorize

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:166. Condición: `if hasattr(args, "id_inventario") and args.id_inventario:`.

```python
        if hasattr(args, "id_inventario") and args.id_inventario:
            await AccesoService.verificar_inventario(user, args.id_inventario)
```

### COND-0711: SaikiToolRegistry._authorize

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:168. Condición: `if name == "get_product" and args.id_producto:`.

```python
        if name == "get_product" and args.id_producto:
            await AccesoService.verificar_producto(user, args.id_producto)
```

### COND-0712: SaikiToolRegistry.get_product

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:176. Condición: `if args.id_producto:`.

```python
        if args.id_producto:
            return await ProductoRepository.obtener_por_id(args.id_producto)
```

### COND-0713: SaikiToolRegistry.get_active_alerts

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:192. Condición: `if args.id_inventario:`.

```python
        if args.id_inventario:
            alerts = await self.alerta_service.listar_por_inventario(args.id_inventario)
            return [item for item in alerts if item.get("estado") == "ACTIVA"]
```

### COND-0714: SaikiToolRegistry.get_recommendations

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:199. Condición: `if args.id_inventario:`.

```python
        if args.id_inventario:
            return await self.recomendacion_service.listar_por_inventario(
                args.id_inventario
            )
```

### COND-0715: SaikiToolRegistry.get_recent_movements

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:211. Condición: `if args.id_inventario:`.

```python
        if args.id_inventario:
            movements = await self.movimiento_service.obtener_por_inventario(args.id_inventario)
```

### COND-0716: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:228. Condición: `if getattr(args, "include_visual", False):`.

```python
        if getattr(args, "include_visual", False):
            from app.services.saiki_inventory_summary import inventory_summary
            return await inventory_summary(user, args.page, args.page_size)
```

### COND-0717: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:232. Condición: `if user is not None:`.

```python
        if user is not None:
            visible_warehouse_ids = await AccesoService.ids_almacenes(user)
```

### COND-0718: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:235. Condición: `if visible_warehouse_ids is not None:`.

```python
        if visible_warehouse_ids is not None:
            warehouses = [
                warehouse
                for warehouse in warehouses
                if (warehouse.get("id_almacen") or warehouse.get("id"))
                in visible_warehouse_ids
            ]
```

### COND-0719: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:242. Condición: `if not warehouses:`.

```python
        if not warehouses:
            return {
                "estado_inventario": "sin_almacenes",
                "total_almacenes": 0,
                "mensaje": (
                    "Actualmente no tienes almacenes registrados en PsiTwin. "
                    "Primero debes crear uno para comenzar a gestionar tu inventario."
                ),
                "total_registros_inventario": 0,
                "productos_distintos": 0,
                "stock_total_unidades": 0,
                "almacenes": [],
                "stock_por_producto": [],
                "ubicaciones": [],
                "inventarios": [],
            }

```

### COND-0720: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:259. Condición: `if visible_warehouse_ids is not None:`.

```python
        if visible_warehouse_ids is not None:
            visible_zone_ids = {
                zone.get("id_zona", zone.get("id"))
                for zone in await ZonaRepository.obtener_todas()
                if zone.get("id_almacen") in visible_warehouse_ids
            }
            visible_rack_ids = {
                rack.get("id_rack") or rack.get("id")
                for rack in await RackRepository.obtener_todos()
                if rack.get("id_zona") in visible_zone_ids
            }
```

### COND-0721: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:274. Condición: `if visible is not None:`.

```python
        if visible is not None:
            inventories = [
                item for item in inventories
                if item.get("id_inventario") in visible
            ]
```

### COND-0722: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:279. Condición: `if args.id_inventario:`.

```python
        if args.id_inventario:
            inventories = [
                item for item in inventories
                if item.get("id_inventario") == args.id_inventario
            ]

```

### COND-0723: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:285. Condición: `if visible_rack_ids is not None:`.

```python
        if visible_rack_ids is not None:
            inventories = [
                item for item in inventories
                if item.get("id_rack") in visible_rack_ids
            ]

```

### COND-0724: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:306. Condición: `if not inventories and not products:`.

```python
        if not inventories and not products:
            return {
                "estado_inventario": "almacen_sin_productos",
                "total_almacenes": len(warehouses),
                "mensaje": (
                    "Tu almacén está registrado, pero todavía no tienes "
                    "productos registrados."
                ),
                "total_registros_inventario": 0,
                "productos_distintos": 0,
                "stock_total_unidades": 0,
                "almacenes": warehouses,
                "stock_por_producto": [],
                "ubicaciones": [],
                "inventarios": [],
            }
```

### COND-0725: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:322. Condición: `if not inventories:`.

```python
        if not inventories:
            return {
                "estado_inventario": "productos_sin_inventario",
                "total_almacenes": len(warehouses),
                "mensaje": (
                    "Tienes productos registrados, pero todavía no hay "
                    "existencias de inventario asociadas."
                ),
                "total_registros_inventario": 0,
                "productos_distintos": len(products),
                "stock_total_unidades": 0,
                "almacenes": warehouses,
                "stock_por_producto": [],
                "ubicaciones": [],
                "inventarios": [],
            }
```

### COND-0726: SaikiToolRegistry.get_warehouse_status

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/saiki_tools.py:405. Condición: `if all(stock <= 0 for stock in stock_by_product.values()):`.

```python
        if all(stock <= 0 for stock in stock_by_product.values()):
            result["estado_inventario"] = "stock_cero"
            result["mensaje"] = (
                "Tienes productos registrados, pero actualmente sus existencias son cero."
            )
```

### COND-0727: ZonaService.normalizar_zona

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:50. Condición: `if not zona:`.

```python
        if not zona:

            return zona

```

### COND-0728: ZonaService.normalizar_zona

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:62. Condición: `if ( "id" not in result and "id_zona" in result ):`.

```python
        if (
            "id" not in result
            and
            "id_zona" in result
        ):

            result["id"] = (
                result["id_zona"]
            )

        # --------------------------------------------------------
        # COMPLETAR ID_EMPRESA DESDE ALMACEN
        # --------------------------------------------------------

```

### COND-0729: ZonaService.normalizar_zona

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:76. Condición: `if ( not result.get("id_empresa") and result.get("id_almacen") ):`.

```python
        if (
            not result.get("id_empresa")
            and
            result.get("id_almacen")
        ):

            almacen = await (
                AlmacenRepository.obtener_por_id(
                    result["id_almacen"]
                )
            )

            if almacen:

                result["id_empresa"] = (
                    almacen.get(
                        "id_empresa"
                    )
                )

```

### COND-0730: ZonaService.normalizar_zona

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:88. Condición: `if almacen:`.

```python
            if almacen:

                result["id_empresa"] = (
                    almacen.get(
                        "id_empresa"
                    )
                )

```

### COND-0731: ZonaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:114. Condición: `if not almacen:`.

```python
        if not almacen:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "El almacén especificado "
                    "no existe"
                )
            )

```

### COND-0732: ZonaService.crear

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:126. Condición: `if ( data.temperatura_min is not None and data.temperatura_max is not None and data.temperatura_min > data.temperatura_max ):`.

```python
        if (
            data.temperatura_min is not None
            and
            data.temperatura_max is not None
            and
            data.temperatura_min
            >
            data.temperatura_max
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "La temperatura mínima "
                    "no puede ser mayor "
                    "que la máxima"
                )
            )

```

### COND-0733: ZonaService.obtener_por_id

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:246. Condición: `if not zona:`.

```python
        if not zona:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Zona no encontrada"
                )
            )

```

### COND-0734: ZonaService.obtener_por_almacen

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:279. Condición: `if not almacen:`.

```python
        if not almacen:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Almacén no encontrado"
                )
            )

```

### COND-0735: ZonaService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:329. Condición: `if not zona_actual:`.

```python
        if not zona_actual:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Zona no encontrada"
                )
            )

```

### COND-0736: ZonaService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:346. Condición: `if not update_data:`.

```python
        if not update_data:

            return await (
                ZonaService.normalizar_zona(
                    zona_actual
                )
            )

```

### COND-0737: ZonaService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:372. Condición: `if ( temperatura_min is not None and temperatura_max is not None and temperatura_min > temperatura_max ):`.

```python
        if (
            temperatura_min is not None
            and
            temperatura_max is not None
            and
            temperatura_min
            >
            temperatura_max
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "La temperatura mínima "
                    "no puede ser mayor "
                    "que la máxima"
                )
            )

```

### COND-0738: ZonaService.actualizar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:400. Condición: `if not updated:`.

```python
        if not updated:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Zona no encontrada"
                )
            )

```

### COND-0739: ZonaService.eliminar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:433. Condición: `if not zona:`.

```python
        if not zona:

            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Zona no encontrada"
                )
            )

```

### COND-0740: ZonaService.eliminar

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/services/zona_service.py:450. Condición: `if not deleted:`.

```python
        if not deleted:

            raise HTTPException(
                status_code=(
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    "No se pudo eliminar "
                    "la zona"
                )
            )

```

### COND-0741: módulo.create_access_token

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/utils/security.py:131. Condición: `if rol == ROL_OPERARIO:`.

```python
    if rol == ROL_OPERARIO:

        payload[
            "id_almacen"
        ] = id_almacen

```

### COND-0742: módulo.create_access_token

Estado IMPLEMENTADO; regla o ramificación operativa. Evidencia app/utils/security.py:137. Condición: `if rol == ROL_PROVEEDOR:`.

```python
    if rol == ROL_PROVEEDOR:

        payload[
            "id_proveedor"
        ] = id_proveedor

```


Aclaración RN-22: la deduplicación de transporte por evento está en notify_owner. enviar_orden_proveedor utiliza upsert del registro pero no aplica lectura de evento previo antes de SMTP; INC-32 documenta esa diferencia.


Defaults ejecutados de auxiliares: email_verifications.attempts=0, used=False, status=PENDING, max_attempts=settings(default5), expires_at=nowUTC+TTL(default10min), cooldown_until=nowUTC+cooldown(default60s), created_at/updated_at=nowUTC, code_hash=SHA256(código aleatorio6dígitos). inventario_historial.fecha=nowUTC, accion=CREAR/EDITAR_LIMITES por llamada, antes=None en crear y límites previos al editar, despues snapshot de campos. notificaciones_email.fecha_creacion=nowUTC solo $setOnInsert y fecha_actualizacion=nowUTC por upsert. Son defaults del servicio, no límites/constraints MongoDB.
