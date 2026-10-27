# Contrato de datos PsiTwin — implementación v2

Actualización de código: 2026-10-13. Migración e índices preparados, sin ejecutarlos en MongoDB real. No se entrenaron modelos.
Este bloque reemplaza los contratos de inventario/forecast de la auditoría histórica que se conserva debajo.

## Inventario general y ubicaciones

| Colección | Contrato vigente |
|---|---|
| inventarios | id_inventario:str UUID4, id_almacen:str, fecha_creacion/fecha_actualizacion:datetime UTC. Único id_almacen; cabecera sin producto, rack ni stock. |
| detalles_inventario | id_detalle_inventario:str UUID4, id_inventario:str, id_producto:str, id_rack:str, stock_actual:int>=0, stock_minimo:int>=0 (default0), stock_maximo:int>=0 requerido, fechas datetime UTC. |
| movimientos | id_inventario ahora es cabecera; id_detalle_inventario requerido; id_almacen/id_producto/id_rack derivados. Saldos anterior/nuevo y cantidad conservados. |
| inventario_historial | Guarda cabecera, detalle, almacén, producto/rack, operario y snapshots. Consulta unifica CREAR/EDITAR_LIMITES con el ledger de movimientos sin duplicarlo. |
| detalles_recepcion | Cabecera requerida; id_detalle_inventario opcional al solicitar nueva ubicación. id_rack opcional; stock_minimo default0 y stock_maximo requerido si se crea detalle. No crea una cabecera nueva. |
| alertas/recomendaciones | id_detalle_inventario opcional distingue ubicación. RIESGO_STOCKOUT/REABASTECER se normalizan al producto agregado del almacén, con detalle=None y deduplicación por producto. |
| bloqueos_stock_rack | Auxiliar interna: _id de recurso, token UUID y fecha UTC. Excluye escritores simultáneos en rack, recepción de orden y decisiones agregadas. No es un saldo. |

API 2.0.0. El almacén crea su cabecera; creación de cabecera idempotente. Detalle único por (id_inventario,id_producto,id_rack).
Productos por almacén se consultan mediante detalles, sin depender del rack comercial de referencia.
Almacén con estructura/operaciones/auditoría y zona con racks no se eliminan; almacén vacío elimina su cabecera vacía.
Producto de la misma empresa; rack del almacén de la cabecera. Mínimo<=máximo; inicial<=máximo; límites continúan por ubicación.
Capacidad=sum(stock_actual*peso) por rack; rangos térmicos existentes conservados. Stock total por producto se suma al consultar; no se persiste.
Movimiento público conserva solo SALIDA por VENTA/VENCIMIENTO; otras combinaciones existentes son internas. Recepción valida DISPONIBLE también dentro del movimiento protegido.
CAS y compensación de stock conservados. Si falla el movimiento de recepción, el detalle queda EN_EVALUACION con aceptada0 para resolverlo tras reconciliar. Bloqueos distribuidos sin TTL: después de una caída requieren revisión manual con escritores detenidos.
No se elimina un detalle con movimientos, recepciones, alertas o recomendaciones referenciándolo.
Startup detecta inventarios legacy antes de instalar índices y exige migración; los repositorios también rechazan reinterpretación con HTTP409 MIGRACION_INVENTARIO_REQUERIDA. Índices críticos de stock/idempotencia fallidos impiden startup.

## Rutas vigentes (prefijo /api/v1)

| Ruta | Uso |
|---|---|
| POST /inventarios | Body id_almacen; garantizar cabecera; HTTP200 idempotente. |
| GET /inventarios/almacen/{id_almacen} | Cabecera del almacén autorizado. |
| GET /inventarios/{id_inventario}/detalles | Filtros id_producto, id_rack, id_zona. |
| GET /inventarios/{id_inventario}/productos | Totales por producto y distribución; no suma límites como si fueran límites generales. |
| GET /inventarios/{id_inventario}/productos/{id_producto} | Distribución de ese producto por racks. |
| GET /inventarios/{id_inventario}/historial | Auditoría de cabecera y detalles. |
| /detalles-inventario | Alta/consulta/límites/borrado por id_detalle_inventario; filtros de producto/rack y stock. |
| /movimientos y /recepciones-mercaderia | Contratos adaptados a cabecera+detalle; estados y aprobaciones conservados. |
| GET /forecast/almacenes/{id_almacen}/productos/{id_producto} | horizonte_dias=1/7/30/90; fecha_corte opcional (date UTC); dias=400, rango7..500. |
| GET /forecast/predict-7-days/{id_inventario} | Compatibilidad de ruta; requiere id_producto, cabecera nueva. Respuesta del contrato común. |
| GET /inventory-risk/{id_inventario} | Requiere id_producto; stock agregado. Listado evalúa una serie por producto/almacén. |

Los antiguos POST/límites/borrado de inventario físico se sustituyen por /detalles-inventario. Las rutas debug de forecasting anteriores no se mantienen.
El frontend debe enviar ambos IDs en movimientos, y seleccionar producto en forecasting/riesgo. No convertir un ID antiguo a cabecera por su cuenta.

## Forecasting vigente

Serie=(id_almacen,id_producto); demanda=suma diaria UTC de toda SALIDA, sin filtrar motivo. Racks sumados una vez, almacenes aislados.
No hay promociones/descuentos. Se conservan 136 features de artefactos; sin fuentes/mapeos nuevos de precios, eventos, SNAP o categorías M5.
Servicio común directo D+1..D+7, conserva calendario/lags/rolling. Cada horizonte usa el mismo corte e historia; no se alimentan lags con datos posteriores.
Para cortes históricos, metadata de categoría actualizada después del corte o sin fecha verificable no alimenta agregados dept; usa NaN y advertencia. Snapshots históricos de maestros NO IMPLEMENTADOS.
Corte por defecto hoy UTC; primera predicción mañana UTC. Día en curso se advierte como parcial; consultas históricas acotan el ledger al corte.
Historial: ventana>=367 y primera SALIDA al menos366 días antes del corte. Es cobertura histórica, no prueba de observación continua; relleno cero conserva comportamiento previo.
1/7 disponibles si historia/artefactos permiten inferencia. Artefactos existentes psitwin_v3_6 sin validación nueva de precisión para producto/almacén.
30/90: MODELO_NO_DISPONIBLE; no se extrapola, no se multiplica la semana, no hay valores ficticios. Necesitan artefactos y validación autorizados.

Respuesta: id_almacen, id_producto, fecha_generacion, fecha_corte, horizonte_dias, fecha_inicio/fin, estado,
demanda_total_estimada (suma de diarios), predicciones_diarias[{fecha,demanda_estimada}], modelo/version_modelo,
historial_suficiente, advertencias. Estados: DISPONIBLE, HISTORIAL_INSUFICIENTE, MODELO_NO_DISPONIBLE.
Solo DISPONIBLE contiene los días consecutivos completos. Otros estados tienen lista vacía y total=None, sin modelo/version inventados.
Logística devuelve pronosticos por los cuatro horizontes; mantiene fórmulas de cobertura/seguridad/reposición usando semana disponible.
Sin semana válida: riesgo, seguridad, reposición y agotamiento sin calcular; no crea alertas ni órdenes.
Saiki expone cabecera y ids_detalles_inventario separados, agrega todas las series antes de seleccionar producto/almacén y resume stock general y físico, reconoce los cuatro horizontes y estados sin predicción. Herramientas siguen siendo de lectura.

## Migración offline y recuperación

Script: scripts/migrar_inventario_v2.py. No contiene cliente ni conexión MongoDB.
Entrada: snapshot BSON Extended JSON {nombre_coleccion:[documentos]}; no URI. Exige inventarios, almacenes, zonas, racks, productos, operarios, proveedores, órdenes/detalles y todas las dependientes (movimientos, recepciones, historial, alertas, recomendaciones); incluir listas vacías explícitas. Rechaza exportaciones parciales.
Dry-run (por defecto no escribe):
    .venv/Scripts/python.exe scripts/migrar_inventario_v2.py --input snapshot.json --dry-run
Transformar únicamente una copia offline, si no hay errores:
    .venv/Scripts/python.exe scripts/migrar_inventario_v2.py --input snapshot.json --output snapshot-v2.json
Salida nueva obligatoria; nunca sobrescribe fuente; escritura temporal+rename y checksum SHA256 fuente.
Crea cabeceras para todos los almacenes, detalles con UUID5 deterministas distintos del ID antiguo, y migracion_inventario_mapeo.
Preserva inventarios_legacy, saldos/límites/fechas, movimientos, históricos y copias de recepción. Reejecución no duplica.
Verifica huérfanos, empresas, pares repetidos, kg/temperaturas, continuidad del ledger y saldo final; errores bloquean salida.
RIESGO_STOCKOUT/REABASTECER pendientes de racks distintos se consolidan: conserva registros, marca secundarios IGNORADA/RECHAZADA y registra estado anterior.
Recuperación: conservar snapshot fuente completo y checksum; restaurar todas las colecciones conjuntamente, no solo inventarios.
Importación online y ejecución en producción NO IMPLEMENTADAS ni autorizadas; primero validar una restauración en staging sin escritores.
Índices únicos preparados en startup; instalación efectiva NO VERIFICABLE aquí. No iniciar el nuevo backend contra producción antes de migración/restauración autorizada.
No hay transacción multientidad: una caída entre stock/ledger o entre pasos de recepción requiere reconciliación y revisión antes de liberar bloqueos.

## Archivos de esta implementación

| Directorio | Archivos creados o modificados |
|---|---|
| . | `CONTRATO_DATOS_PSITWIN.md`, `requirements-dev.txt` |
| app/controllers | `detalle_inventario_controller.py`, `detalle_recepcion_controller.py`, `forecast_controller.py`, `inventario_controller.py`, `inventory_risk_controller.py`, `movimiento_controller.py`, `producto_controller.py` |
| app/database | `mongodb.py` |
| app/dto | `alerta_dto.py`, `detalle_inventario_dto.py`, `detalle_recepcion_dto.py`, `forecast_dto.py`, `inventario_dto.py`, `inventory_risk_dto.py`, `movimiento_dto.py`, `recepcion_mercaderia_dto.py`, `recomendacion_dto.py`, `saiki_dto.py` |
| app | `main.py` |
| app/ml | `demand_history.py`, `ml_context_builder.py` |
| app/prompts | `saiki_system_prompt.py` |
| app/repositories | `alerta_repository.py`, `detalle_inventario_repository.py`, `historial_inventario.py`, `inventario_repository.py`, `inventory_risk_repository.py`, `producto_repository.py`, `recomendacion_repository.py`, `serie_demanda_repository.py` |
| app/services | `acceso_service.py`, `alerta_service.py`, `almacen_service.py`, `detalle_inventario_service.py`, `detalle_recepcion_service.py`, `forecast_service.py`, `inventario_integridad.py`, `inventario_service.py`, `inventory_risk_service.py`, `movimiento_service.py`, `notification_service.py`, `rack_service.py`, `recepcion_mercaderia_service.py`, `recomendacion_service.py`, `saiki_intent_router.py`, `saiki_inventory_summary.py`, `saiki_responses.py`, `saiki_service.py`, `saiki_tools.py`, `stock_lock.py`, `zona_service.py` |
| scripts | `migrar_inventario_v2.py` |
| tests | `test_forecasting_v2.py`, `test_inventario_v2.py`, `test_inventario_v2_http.py`, `test_migracion_inventario_v2.py`, `test_notification_service.py`, `test_saiki_conversation_quality.py`, `test_saiki_http.py`, `test_saiki_inventory_summary.py`, `test_saiki_isolation_stdlib.py`, `test_saiki_request_semantics.py`, `test_saiki_service.py` |

---

# Auditoría histórica previa a la refactorización

Los apartados siguientes describen exclusivamente el esquema anterior. Para los módulos modificados prevalece el contrato v2 de arriba.


Estado auditado: 2026-10-13. Síntesis de la auditoría existente; solo se aclararon restricciones puntuales. No se ejecutó backend/ML ni se consultó MongoDB.

## 1. Entidades y atributos

18 colecciones: 15 entidades de negocio y 3 auxiliares. Los DTO anidados y resultados de ML/LLM no son colecciones independientes.
C=creación; U=actualización general; M=persistido; R=respuesta; G=generado. `?`=admite None en esa vista, no necesariamente omisión.
«obligatorio» exige presencia en C; «omitible=X» aplica X al omitir. Las U con default None son parciales y nullable en DTO; el servicio puede descartar o procesar null (§3). Los DTO de cambio de estado exigen estado.
Los defaults R no son defaults Mongo. Campos internos/condicionales no tienen obligación de cliente. NO DEFINIDA significa sin restricción en ese contrato, no sin reglas transversales.
Enum remite a sus valores exactos en §3. `str` de identificador no implica validador UUID. Los tipos C/R pueden diferir; BSON se explica en §4.

### Empresa — `empresas`

C: EmpresaRegisterRequest; U: EmpresaUpdateRequest. Evidencia: app/services/empresa_service.py, app/dto/empresa_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `nombre` | str | obligatorio | omitible=None; longitud≥2; longitud≤100 | M/R | longitud≥2; longitud≤100 |
| `ruc` | str | obligatorio | omitible=None; longitud≥8; longitud≤20 | M/R | longitud≥8; longitud≤20 |
| `sector` | str | obligatorio | omitible=None; longitud≥2; longitud≤100 | M/R | longitud≥2; longitud≤100 |
| `correo` | EmailStr | obligatorio | omitible=None; email válido | M/R | email válido |
| `telefono` | str | obligatorio | omitible=None; longitud≥6; longitud≤20 | M/R | longitud≥6; longitud≤20 |
| `password` | str | obligatorio | — | M; R excluido | longitud≥6; longitud≤128 ; M: hash bcrypt; R: excluido |
| `id_empresa` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `correo_verificado` | bool | no es entrada C | — | M/R | NO DEFINIDA; R default=False |
| `fecha_verificacion_correo` | str? | no es entrada C | — | M/R | NO DEFINIDA; R str?; verificador guarda datetime (inconsistencia); R default=None |
| `fecha_creacion` | str | no es entrada C | — | M/R | G ISO8601 str UTC |
| `fecha_actualizacion` | str | no es entrada C | — | M/R | G ISO8601 str UTC |

### Almacen — `almacenes`

C: AlmacenCreate; U: AlmacenUpdate. Evidencia: app/services/almacen_service.py, app/dto/almacen_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_empresa` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: se sustituye por token |
| `nombre` | str | obligatorio | omitible=None; longitud≥2; longitud≤100 | M/R | longitud≥2; longitud≤100 |
| `longitud` | Decimal | obligatorio | omitible=None; ≥-180.000000; ≤180.000000; dígitos≤9; decimales≤6 | M/R | ≥-180.000000; ≤180.000000; dígitos≤9; decimales≤6 |
| `latitud` | Decimal | obligatorio | omitible=None; ≥-90.000000; ≤90.000000; dígitos≤8; decimales≤6 | M/R | ≥-90.000000; ≤90.000000; dígitos≤8; decimales≤6 |
| `area_m2` | float | obligatorio | omitible=None; >0 | M/R | >0 |
| `aforo` | int | obligatorio | omitible=None; ≥0 | M/R | ≥0 |
| `tipo_almacen` | str | obligatorio | omitible=None; longitud≥2; longitud≤100 | M/R | longitud≥2; longitud≤100 |
| `id` | str | no es entrada C | — | M/R | G UUID; R acepta alias legacy id_almacen |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |

### Zona — `zonas`

C: ZonaCreate; U: ZonaUpdate. Evidencia: app/services/zona_service.py, app/dto/zona_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_almacen` | str | obligatorio | — | M/R | NO DEFINIDA |
| `nombre` | str | obligatorio | omitible=None; longitud≥2; longitud≤100 | M/R | longitud≥2; longitud≤100 |
| `tipo_zona` | str | obligatorio | omitible=None; longitud≥2; longitud≤100 | M/R | longitud≥2; longitud≤100 |
| `refrigerada` | bool | omitible=False | omitible=None | M/R | NO DEFINIDA |
| `temperatura_min` | float? | omitible=None | omitible=None | M/R | NO DEFINIDA |
| `temperatura_max` | float? | omitible=None | omitible=None | M/R | NO DEFINIDA |
| `capacidad` | int | obligatorio | omitible=None; ≥0 | M/R | ≥0 ; niveles; no kg/m³ |
| `id` | str | no es entrada C | — | M/R | G UUID; R acepta alias legacy id_zona |
| `id_empresa` | str | no es entrada C | — | M/R | NO DEFINIDA |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |

### Rack — `racks`

C: RackCreate; U: RackUpdate. Evidencia: app/services/rack_service.py, app/dto/rack_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_zona` | str | obligatorio | — | M/R | NO DEFINIDA |
| `codigo` | str | obligatorio | — | M/R | longitud≥1; longitud≤50 |
| `nivel` | int | obligatorio | — | M/R | ≥1 |
| `capacidad` | float | obligatorio | — | M/R | >0 ; kg |
| `temperatura_min` | float? | omitible=None | omitible=None | M/R | NO DEFINIDA |
| `temperatura_max` | float? | omitible=None | omitible=None | M/R | NO DEFINIDA |
| `estado` | EstadoRack | omitible=EstadoRack.DISPONIBLE | omitible=None | M/R | NO DEFINIDA |
| `id_rack` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `carga_kg` | float | no es entrada C | — | —/R | NO DEFINIDA; R default=0 |
| `libre_kg` | float | no es entrada C | — | —/R | NO DEFINIDA; R default=0 |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |

### Producto — `productos`

C: ProductoCreate; U: ProductoUpdate. Evidencia: app/services/producto_service.py, app/dto/producto_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_empresa` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: se sustituye por token |
| `id_proveedor` | str? | omitible=None | — | M/R | NO DEFINIDA; C: se sustituye por token |
| `id_rack` | str? | omitible=None | omitible=None | M/R | NO DEFINIDA; C: forzado a None; U: solo OPERARIO asigna rack |
| `nombre` | str | obligatorio | omitible=None | M/R | longitud≥2; longitud≤150 |
| `categoria` | str | obligatorio | omitible=None | M/R | longitud≥2; longitud≤100 |
| `familia` | str | obligatorio | omitible=None | M/R | longitud≥2; longitud≤100 |
| `marca` | str? | omitible=None | omitible=None | M/R | NO DEFINIDA |
| `peso` | float C; float? R | obligatorio | omitible=None | M/R | >0 ; kg/unidad; C obligatorio >0, R nullable legacy |
| `volumen` | float? | omitible=None | omitible=None | M/R | >0 |
| `stock` | int | omitible=0 | omitible=None; ≥0 | —/R | ≥0 ; DTO acepta ≥0/default0; service descarta; R=0 si campo ausente |
| `requiere_refrigeracion` | bool | omitible=False | omitible=None | M/R | NO DEFINIDA |
| `temperatura_min_almacenamiento` | float? | omitible=None | omitible=None | M/R | NO DEFINIDA |
| `temperatura_max_almacenamiento` | float? | omitible=None | omitible=None | M/R | NO DEFINIDA |
| `lead_time_dias` | int | obligatorio | omitible=None; ≥0 | M/R | ≥0 |
| `vida_util_dias` | int | obligatorio | omitible=None; ≥1 | M/R | ≥1 |
| `id_producto` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |

### Inventario — `inventarios`

C: InventarioCreate; U: InventarioUpdate. Evidencia: app/services/inventario_service.py, app/dto/inventario_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_producto` | str | obligatorio | — | M/R | NO DEFINIDA |
| `id_rack` | str | obligatorio | — | M/R | NO DEFINIDA |
| `stock_actual` | int | obligatorio | — | M/R | ≥0 |
| `stock_minimo` | int | omitible=0 | omitible=None; ≥0 | M/R | ≥0 |
| `stock_maximo` | int | obligatorio | omitible=None; ≥0 | M/R | ≥0 |
| `id_inventario` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |

### Operario — `operarios`

C: OperarioCreate; U: OperarioUpdate. Evidencia: app/services/operario_service.py, app/dto/operario_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_empresa` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: se sustituye por token |
| `id_almacen` | str C; str? R | obligatorio | omitible=None | M/R | NO DEFINIDA |
| `nombre` | str | obligatorio | omitible=None; longitud≥2; longitud≤100 | M/R | longitud≥2; longitud≤100 |
| `apellido` | str | obligatorio | omitible=None; longitud≥2; longitud≤100 | M/R | longitud≥2; longitud≤100 |
| `cargo` | str | obligatorio | omitible=None; longitud≥2; longitud≤100 | M/R | longitud≥2; longitud≤100 |
| `turno` | str | obligatorio | omitible=None; longitud≥2; longitud≤50 | M/R | longitud≥2; longitud≤50 |
| `estado` | str | omitible=ACTIVO | omitible=None; longitud≥2; longitud≤50 | M/R | longitud≥2; longitud≤50 |
| `correo` | EmailStr C; str? R | obligatorio | omitible=None; email válido | M/R | email válido |
| `password_temporal` | str | obligatorio | — | — | longitud≥6; longitud≤128 ; C: obligatorio; transforma a password_hash; no persiste |
| `id_operario` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `correo_verificado` | bool | no es entrada C | — | M/R | NO DEFINIDA; R default=False |
| `fecha_verificacion_correo` | datetime? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `tiene_cuenta` | bool | no es entrada C | — | —/R | NO DEFINIDA; R default=False |
| `debe_cambiar_password` | bool | no es entrada C | — | M/R | NO DEFINIDA; R default=False |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `password_hash` | str? (hash bcrypt) | no es entrada C | — | M; R excluido | NO DEFINIDA; M: hash bcrypt; R: excluido |

### Movimiento — `movimientos`

C: MovimientoCreate; U: sin DTO de actualización general. Evidencia: app/services/movimiento_service.py, app/dto/movimiento_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_inventario` | str | obligatorio | — | M/R | NO DEFINIDA |
| `id_operario` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: token OPERARIO prevalece; servicio exige operario ACTIVO |
| `id_detalle_recepcion` | str? | omitible=None | — | M/R | NO DEFINIDA; C pública: forzado a None; solo recepción interna asigna |
| `tipo_movimiento` | TipoMovimiento | obligatorio | — | M/R | NO DEFINIDA |
| `motivo_movimiento` | MotivoMovimiento | obligatorio | — | M/R | NO DEFINIDA |
| `cantidad` | int | obligatorio | — | M/R | >0 |
| `observacion` | str? | omitible=None | — | M/R | longitud≤500 |
| `id_movimiento` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `id_producto` | str | no es entrada C | — | M/R | NO DEFINIDA |
| `id_rack` | str | no es entrada C | — | M/R | NO DEFINIDA |
| `operario_nombre` | str? | no es entrada C | — | —/R | NO DEFINIDA; R default=None |
| `id_zona` | str? | no es entrada C | — | —/R | NO DEFINIDA; R default=None |
| `stock_anterior` | int | no es entrada C | — | M/R | NO DEFINIDA |
| `stock_nuevo` | int | no es entrada C | — | M/R | NO DEFINIDA |
| `fecha_hora` | datetime | no es entrada C | — | M/R | G datetime UTC |

### Proveedor — `proveedores`

C: ProveedorCreate; U: ProveedorUpdate. Evidencia: app/services/proveedor_service.py, app/dto/proveedor_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_empresa` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: se sustituye por token |
| `nombre` | str | obligatorio | omitible=None; longitud≥2; longitud≤150 | M/R | longitud≥2; longitud≤150 |
| `ruc` | str | obligatorio | — | M/R | longitud≥11; longitud≤11 |
| `correo` | EmailStr? | omitible=None | omitible=None; email válido | M/R | email válido |
| `telefono` | str? | omitible=None | omitible=None; longitud≤20 | M/R | longitud≤20 |
| `direccion` | str? | omitible=None | omitible=None; longitud≤250 | M/R | longitud≤250 |
| `tiempo_entrega_estimado_dias` | int | omitible=1 | omitible=None; ≥0 | M/R | ≥0 |
| `estado` | EstadoProveedor | omitible=EstadoProveedor.ACTIVO | omitible=None | M/R | NO DEFINIDA |
| `password_temporal` | str? | omitible=None | — | — | longitud≥6; longitud≤128 ; C: opcional; si se da exige correo; transforma a hash |
| `id_proveedor` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `tiene_cuenta` | bool | no es entrada C | — | —/R | NO DEFINIDA; R default=False |
| `debe_cambiar_password` | bool | no es entrada C | — | M/R | NO DEFINIDA; R default=False |
| `correo_verificado` | bool | no es entrada C | — | M/R | NO DEFINIDA; R default=False |
| `fecha_verificacion_correo` | datetime? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `password_hash` | str? (hash bcrypt) | no es entrada C | — | M; R excluido | NO DEFINIDA; M: hash bcrypt si cuenta; R: excluido |

### OrdenReposicion — `ordenes_reposicion`

C: OrdenReposicionCreate; U: OrdenReposicionUpdate. Evidencia: app/services/orden_reposicion_service.py, app/dto/orden_reposicion_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_recomendacion` | str? | omitible=None | — | M/R | NO DEFINIDA |
| `id_empresa` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: se sustituye por token |
| `id_almacen` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: almacén del OPERARIO |
| `id_proveedor` | str | obligatorio | omitible=None | M/R | NO DEFINIDA |
| `lineas` | list[DetalleReposicionCreate] | omitible=[] | — | — | NO DEFINIDA; C: lista default[]; NO en cabecera; crea detalles separados |
| `fecha_estimada_recepcion` | datetime? | omitible=None | omitible=None | M/R | NO DEFINIDA |
| `origen` | OrigenOrden | omitible=OrigenOrden.MANUAL | — | M/R | NO DEFINIDA |
| `observacion` | str? | omitible=None | omitible=None; longitud≤500 | M/R | longitud≤500 |
| `id_orden_reposicion` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `estado` | EstadoOrdenReposicion | no es entrada C | — | M/R | NO DEFINIDA |
| `fecha_orden` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `id_operario_solicitante` | str? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `comentario_empresa` | str? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `despacho` | dict? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `fecha_despacho` | datetime? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |

### DetalleReposicion — `detalles_reposicion`

C: DetalleReposicionCreate; U: DetalleReposicionUpdate. Evidencia: app/services/detalle_reposicion_service.py, app/dto/detalle_reposicion_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_producto` | str | obligatorio | — | M/R | NO DEFINIDA |
| `cantidad_solicitada` | int | obligatorio | omitible=None; >0 | M/R | >0 |
| `costo_unitario` | float? | omitible=None | omitible=None; ≥0 | M/R | ≥0 |
| `id_detalle_reposicion` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `id_orden_reposicion` | str | no es entrada C | — | M/R | NO DEFINIDA |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |

### RecepcionMercaderia — `recepciones_mercaderia`

C: RecepcionMercaderiaCreate; U: sin DTO de actualización general. Evidencia: app/services/recepcion_mercaderia_service.py, app/dto/recepcion_mercaderia_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_orden_reposicion` | str | obligatorio | — | M/R | NO DEFINIDA |
| `id_operario` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: token OPERARIO prevalece |
| `fecha_recepcion` | datetime? C; datetime R | omitible=None | — | M/R | NO DEFINIDA |
| `observaciones_generales` | str? | omitible=None | — | M/R | longitud≤1000 |
| `detalles` | list[DetalleRecepcionCreate] C; list[DetalleRecepcionResponse] R | obligatorio | — | M/R | longitud≥1 ; M copia Create; R reconstruye Response desde detalles_recepcion |
| `id_recepcion` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |

### DetalleRecepcion — `detalles_recepcion`

C: DetalleRecepcionCreate; U: sin DTO de actualización general. Evidencia: app/services/detalle_recepcion_service.py, app/dto/detalle_recepcion_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_detalle_reposicion` | str | obligatorio | — | M/R | NO DEFINIDA |
| `id_inventario` | str | obligatorio | — | M/R | NO DEFINIDA |
| `cantidad_recibida` | int | obligatorio | — | M/R | >0 |
| `cantidad_rechazada` | int | omitible=0 | — | M/R | ≥0 |
| `lote` | str | omitible=SIN_LOTE | — | M/R | longitud≥1; longitud≤100 |
| `fecha_vencimiento` | datetime? | omitible=None | — | M/R | NO DEFINIDA |
| `temperatura_recepcion` | float? | omitible=None | — | M/R | NO DEFINIDA |
| `estado_recepcion` | EstadoRecepcion | omitible=EstadoRecepcion.CONFORME | — | M/R | NO DEFINIDA |
| `comentario_recepcion` | str? | omitible=None | — | M/R | longitud≤1000 |
| `motivo_rechazo` | str? | omitible=None | — | M/R | longitud≤500 |
| `id_detalle_recepcion` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `id_recepcion` | str | no es entrada C | — | M/R | NO DEFINIDA |
| `cantidad_aceptada` | int | no es entrada C | — | M/R | NO DEFINIDA |
| `id_movimiento` | str? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `ubicado` | bool | no es entrada C | — | M/R | NO DEFINIDA; R default=True |
| `riesgo_antes` | str? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `riesgo_despues` | str? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `notificacion_final` | dict? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `id_rack` | str | no es entrada C | — | M condicional/interno | NO DEFINIDA; M: derivado de inventario; no declarado en Response |
| `comentario_resolucion` | str | no es entrada C | — | M condicional/interno | NO DEFINIDA; M: solo al resolver; no declarado en Response |
| `id_operario_resolucion` | str | no es entrada C | — | M condicional/interno | NO DEFINIDA; M: solo al resolver; no declarado en Response |
| `fecha_resolucion` | datetime | no es entrada C | — | M condicional/interno | NO DEFINIDA; M: solo al resolver; no declarado en Response |

### Alerta — `alertas`

C: AlertaCreate; U: AlertaEstadoUpdate. Evidencia: app/services/alerta_service.py, app/dto/alerta_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_empresa` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: se sustituye por token |
| `id_almacen` | str | obligatorio | — | M/R | NO DEFINIDA |
| `id_inventario` | str | obligatorio | — | M/R | NO DEFINIDA |
| `id_producto` | str | obligatorio | — | M/R | NO DEFINIDA |
| `tipo_alerta` | TipoAlerta | obligatorio | — | M/R | NO DEFINIDA |
| `nivel_riesgo` | NivelRiesgo | obligatorio | — | M/R | NO DEFINIDA |
| `titulo` | str | obligatorio | — | M/R | longitud≥3; longitud≤150 |
| `mensaje` | str | obligatorio | — | M/R | longitud≥3; longitud≤1000 |
| `stock_actual` | float | obligatorio | — | M/R | ≥0 |
| `dias_cobertura` | float? | omitible=None | — | M/R | ≥0 |
| `stock_seguridad` | float? | omitible=None | — | M/R | ≥0 |
| `punto_reposicion` | float? | omitible=None | — | M/R | ≥0 |
| `forecast_7d` | float? | omitible=None | — | M/R | ≥0 |
| `estado` | EstadoAlerta | no es entrada C | obligatorio (Enum; no None) | M/R | NO DEFINIDA |
| `id_alerta` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_resolucion` | datetime? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |

### Recomendacion — `recomendaciones`

C: RecomendacionCreate; U: RecomendacionEstadoUpdate. Evidencia: app/services/recomendacion_service.py, app/dto/recomendacion_dto.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `id_empresa` | str? C; str R | omitible=None | — | M/R | NO DEFINIDA; C: se sustituye por token |
| `id_almacen` | str | obligatorio | — | M/R | NO DEFINIDA |
| `id_inventario` | str | obligatorio | — | M/R | NO DEFINIDA |
| `id_producto` | str | obligatorio | — | M/R | NO DEFINIDA |
| `id_alerta` | str? | omitible=None | — | M/R | NO DEFINIDA |
| `tipo_recomendacion` | TipoRecomendacion | obligatorio | — | M/R | NO DEFINIDA |
| `nivel_riesgo` | NivelRiesgo | obligatorio | — | M/R | NO DEFINIDA |
| `cantidad_minima` | int? | omitible=None | — | M/R | ≥0 |
| `cantidad_recomendada` | int? | omitible=None | — | M/R | ≥0 |
| `cantidad_segura` | int? | omitible=None | — | M/R | ≥0 |
| `forecast_7d` | float? | omitible=None | — | M/R | ≥0 |
| `explicacion` | str | obligatorio | — | M/R | longitud≥3; longitud≤3000 |
| `origen` | str | omitible=PSITWIN | — | M/R | longitud≥2; longitud≤100 |
| `estado` | EstadoRecomendacion | no es entrada C | obligatorio (Enum; no None) | M/R | NO DEFINIDA |
| `id_recomendacion` | str | no es entrada C | — | M/R | G UUID; str sin patrón UUID exigido |
| `fecha_creacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_actualizacion` | datetime | no es entrada C | — | M/R | G datetime UTC |
| `fecha_aplicacion` | datetime? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `notificacion_aprobacion` | dict? | no es entrada C | — | M/R | NO DEFINIDA; R default=None |
| `solicitud_cambios` | dict | no es entrada C | — | M condicional/interno | NO DEFINIDA; M: solo al solicitar cambios; no declarado en Response |
| `decision_empresa` | dict | no es entrada C | — | M condicional/interno | NO DEFINIDA; M: solo al decidir; no declarado en Response |

### inventario_historial — `inventario_historial`

C: servicio interno; U: sin DTO de actualización general. Evidencia: app/services/inventario_service.py, app/repositories/inventario_repository.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `fecha` | datetime | interno; nowUTC | — | M/R | NO DEFINIDA |
| `id_operario` | str? | interno; NO DEFINIDO en contrato formal | — | M/R | NO DEFINIDA; R default=None |
| `operario_nombre` | str? | no es entrada C | — | —/R | NO DEFINIDA; R default=None |
| `accion` | str | interno; CREAR o EDITAR_LIMITES según flujo | — | M/R | NO DEFINIDA |
| `antes` | dict? | interno; None al crear; límites anteriores al editar | — | M/R | NO DEFINIDA; R default=None |
| `despues` | dict? | interno; campos del inventario al crear; límites nuevos al editar | — | M/R | NO DEFINIDA; R default=None |
| `id_inventario` | str | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | NO DEFINIDA |

### email_verifications — `email_verifications`

C: servicio interno; U: sin DTO de actualización general. Evidencia: app/services/email_verification_service.py, app/services/email_verification_service.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `entity_type` | str | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | NO DEFINIDA |
| `entity_id` | str | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | NO DEFINIDA |
| `email` | str | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | NO DEFINIDA |
| `code_hash` | str | interno; SHA256(código aleatorio6 dígitos) | — | M condicional/interno | NO DEFINIDA |
| `expires_at` | datetime | interno; nowUTC + expires_minutes (default10min) | — | M condicional/interno | NO DEFINIDA |
| `attempts` | int | interno; 0 | — | M condicional/interno | NO DEFINIDA |
| `max_attempts` | int | interno; settings.email_verification_max_attempts (default5) | — | M condicional/interno | NO DEFINIDA |
| `cooldown_until` | datetime | interno; nowUTC + cooldown_seconds (default60s) | — | M condicional/interno | NO DEFINIDA |
| `used` | bool | interno; False | — | M condicional/interno | NO DEFINIDA |
| `status` | str | interno; PENDING | — | M condicional/interno | NO DEFINIDA |
| `created_at` | datetime | interno; nowUTC | — | M condicional/interno | NO DEFINIDA |
| `updated_at` | datetime | interno; nowUTC | — | M condicional/interno | NO DEFINIDA |

### notificaciones_email — `notificaciones_email`

C: servicio interno; U: sin DTO de actualización general. Evidencia: app/services/notification_service.py, app/services/notification_service.py.

| Variable exacta | Tipo | Creación/default | Actualización general | Mongo/respuesta | Restricciones y tratamiento |
|---|---|---|---|---|---|
| `event_id` | str | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | G UUID; str sin patrón UUID exigido |
| `id_empresa` | str | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | NO DEFINIDA |
| `recipient` | str? | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | NO DEFINIDA |
| `subject` | str | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | NO DEFINIDA |
| `status` | str | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | NO DEFINIDA |
| `error` | str? | interno; NO DEFINIDO en contrato formal | — | M condicional/interno | NO DEFINIDA |
| `fecha_actualizacion` | datetime | interno; nowUTC en cada upsert | — | M condicional/interno | G datetime UTC |
| `fecha_creacion` | datetime | interno; nowUTC vía $setOnInsert (solo inserción) | — | M condicional/interno | G datetime UTC |

### Contratos adicionales que afectan estructura o validez

No son entidades persistidas independientes. Obligatoriedad/default corresponden a su DTO; no duplicar documentos al enviar listas anidadas.

| Contrato | Campos y restricciones exactos |
|---|---|
| LineaDespacho | `id_detalle_reposicion`:str [obligatorio]; `cantidad`:int [obligatorio] {>0}; `fecha_vencimiento`:datetime? [default=None]; `temperatura`:float? [default=None] |
| DespachoRequest | `lineas`:list[LineaDespacho] [obligatorio] {longitud≥1}; `observacion`:str? [default=None] {longitud≤500} |
| DevolverOrdenRequest | `comentario`:str [obligatorio] {longitud≥1; longitud≤1000} |
| ResolverEvaluacion | `id_operario`:str? [default=None]; `estado_recepcion`:EstadoRecepcion [obligatorio]; `comentario_resolucion`:str [obligatorio] {longitud≥1; longitud≤1000}; `cantidad_aceptada`:int? [default=None] {≥0}; `cantidad_rechazada`:int? [default=None] {≥0}; `id_inventario`:str? [default=None] |
| EmpresaCambiosRequest | `id_empresa`:str? [default=None]; `comentario`:str [obligatorio] {longitud≥1; longitud≤1000} |
| EmpresaRechazoRequest | `id_empresa`:str? [default=None]; `comentario`:str [obligatorio] {longitud≥1; longitud≤1000} |
| EmpresaAprobacionRequest | `id_empresa`:str? [default=None]; `id_proveedor`:str [obligatorio]; `costo_unitario`:float [obligatorio] {≥0}; `fecha_estimada_recepcion`:datetime? [default=None]; `observacion`:str? [default=None] {longitud≤500} |
| CrearOrdenDesdeRecomendacionRequest | `id_proveedor`:str [obligatorio]; `costo_unitario`:float [obligatorio] {≥0}; `fecha_estimada_recepcion`:datetime? [default=None] |
| PropuestaRecomendacionUpdate | `cantidad_recomendada`:int? [default=None] {≥1}; `explicacion`:str? [default=None] {longitud≥3; longitud≤3000} |
| LoginRequest | `correo`:EmailStr [obligatorio] {email válido}; `password`:str [obligatorio] {longitud≥6; longitud≤128} |
| CambiarPasswordRequest | `password_actual`:str [obligatorio] {longitud≥6; longitud≤128}; `password_nueva`:str [obligatorio] {longitud≥6; longitud≤128} |
| ResetPasswordRequest | `password_temporal`:str [obligatorio] {longitud≥6; longitud≤128}; `correo`:EmailStr? [default=None] {email válido} |
| OperarioResetPassword | `password_temporal`:str [obligatorio] {longitud≥6; longitud≤128}; `correo`:EmailStr? [default=None] {email válido} |
| EmailVerificationCodeRequest | `codigo`:str [obligatorio] {longitud≥6; longitud≤6; regex=r"^\d{6}$"} |
| EmailVerificationSendResponse | `status`:str [obligatorio]; `email`:str? [default=None]; `remaining_seconds`:int? [default=None]; `reason`:str? [default=None] |
| EmailVerificationResponse | `verified`:bool [obligatorio]; `status`:str [obligatorio]; `email`:str? [default=None]; `attempts`:int? [default=None]; `remaining_attempts`:int? [default=None] |
| RackDisponibleResponse | Hereda RackResponse; añade `id_almacen`:str [obligatorio]; `nombre_zona`:str? [default=None] |
| SaikiAskRequest | `message`:str? [default=None] {longitud≥1}; `question`:str? [default=None] {longitud≥1}; `id_inventario`:str? [default=None]; `id_producto`:str? [default=None]; `page`:int [default=1] {≥1}; `page_size`:int [default=25] {≥1; ≤100}; `context`:dict[str, Any] [default=factory dict]; `history`:list[dict[str, Any]] [default=factory list] |
| SaikiAskResponse | `answer`:str [obligatorio]; `model`:str [obligatorio]; `base_url`:str [obligatorio]; `source`:str [default=ollama]; `context`:dict[str, Any] [default=factory dict]; `warnings`:list[str] [default=factory list]; `data`:dict[str, Any] [default=factory dict]; `visualization`:dict[str, Any] [default=factory lambda: {"type": "none"}]; `sources`:list[str] [default=factory list] |

Subdocumentos Mongo no tipados exhaustivamente por DTO: `OrdenReposicion.despacho` contiene `lineas:list` (campos LineaDespacho más `id_producto:str`), `observacion:str?`, `fecha:datetime`; cada línea conserva cantidad/fecha_vencimiento/temperatura.
Estados string internos, sin Enum/constraint Mongo cerrado: email_verifications.status observa PENDING, INVALID_CODE, EXPIRED, LOCKED, VERIFIED, INVALIDATED_BY_EMAIL_CHANGE; notificaciones_email.status observa ERROR, OMITIDO, ENVIADO, BLOQUEADA_EMAIL_NO_VERIFICADO. No confundirlos con status de respuestas de envío/verificación.
`Recomendacion.solicitud_cambios`: `id_empresa:str`, `comentario:str`, `estado_anterior:str`, `estado_nuevo:str`, `fecha:datetime`. `decision_empresa` al rechazar: `id_empresa:str`, `decision:str`, `comentario:str`, `estado_anterior:str`, `fecha:datetime`; al aprobar: `id_empresa:str`, `decision:str`, `fecha:datetime`, `id_proveedor:str`, `costo_unitario:float`. Son variantes, no un DTO único.
`notificacion_aprobacion`/`notificacion_final` son dicts de servicio: pueden contener el registro de notificaciones_email o `status`, `reason` y datos según rama; shape uniforme NO VERIFICABLE. `inventario_historial.antes/despues`: CREAR guarda id_producto/id_rack/stock_actual/stock_minimo/stock_maximo; EDITAR_LIMITES guarda stock_minimo/stock_maximo.
`RackDisponibleResponse` hereda todos los campos RackResponse. `EmpresaRechazoRequest` hereda EmpresaCambiosRequest; no añade campos. Operario.correo está anotado dos veces en Create/Update: existe un solo campo efectivo. `UbicarDetalleRecepcion.id_rack:str` existe como DTO; operación de ubicación dedicada NO IMPLEMENTADA en las rutas auditadas.

## 2. Relaciones e identificadores

Cardinalidades inversas 1:0..N son INFERIDAS de referencias escalares; no hay FK Mongo ni garantía DB de unicidad lógica. Almacen/Zona tienen PK `id`; el resto de negocio usa el `id_*` indicado en tablas. Todas las colecciones pueden tener `_id` técnico independiente.

| Relación | Referencia exacta | Cardinalidad e integridad real |
|---|---|---|
| Empresa → Almacen | Almacen.id_empresa → Empresa.id_empresa | 1:0..N; empresa validada al crear; token fija pertenencia |
| Almacen → Zona | Zona.id_almacen → Almacen.id | 1:0..N; almacén existente/autorizado; id_empresa se deriva |
| Zona → Rack | Rack.id_zona → Zona.id | 1:0..N; zona existente/autorizada; restricciones de nivel |
| Empresa → Operario/Proveedor/Producto | id_empresa → Empresa.id_empresa | 1:0..N; pertenencia de cuenta/token; reglas de almacén propias |
| Proveedor → Producto | Producto.id_proveedor → Proveedor.id_proveedor | 1:0..N; opcional legacy, token de proveedor lo fija al crear |
| Almacen → Operario | Operario.id_almacen → Almacen.id | 1:0..N; obligatorio C, almacén de misma empresa |
| Producto/Rack → Inventario | Inventario.id_producto/id_rack → respectivas claves | cada inventario:1 producto+1 rack; existencia/ámbito verificados; pareja única por servicio |
| Inventario → Movimiento | Movimiento.id_inventario; id_producto/id_rack derivados | 1:0..N; inventario validado; operario existe y ACTIVO |
| Empresa/Almacen/Proveedor → OrdenReposicion | id_empresa/id_almacen/id_proveedor | N:1 cada referencia; mismo tenant, proveedor ACTIVO; id_recomendacion opcional sin FK automática |
| OrdenReposicion/Producto → DetalleReposicion | id_orden_reposicion/id_producto | N:1; orden existe, producto existe, no repetido por orden; empresa comprobada si producto tiene id_empresa |
| OrdenReposicion/Operario → RecepcionMercaderia | id_orden_reposicion/id_operario | N:1; orden ENVIADA/PARCIAL y operario ACTIVO del almacén |
| Recepcion/DetalleReposicion/Inventario → DetalleRecepcion | id_recepcion/id_detalle_reposicion/id_inventario | N:1; crear coteja orden/producto/almacén; resolver no revalida todo |
| DetalleRecepcion → Movimiento | Movimiento.id_detalle_recepcion; DetalleRecepcion.id_movimiento | 0..1 entrada idempotente por detalle si índice parcial disponible; campo de movimiento no verifica FK por sí solo |
| Inventario/Producto/Almacen/Empresa → Alerta/Recomendacion | id_inventario/id_producto/id_almacen/id_empresa; id_alerta opcional | N:1 lógica; creación manual solo verifica almacén propio, no coherencia completa de todas las referencias |
| Auxiliares → negocio | historial.id_inventario/id_operario; email.entity_type/entity_id; notificación.id_empresa | referencias de servicios; sin FK Mongo; entity_type empresa/operario/proveedor; event_id identifica evento |

Un mismo `id_producto` puede tener varios inventarios en racks/almacenes de su empresa; Producto es el registro comercial existente, sin catálogo adicional ni SKU/EAN obligatorio. `Producto.id_rack` es referencia única opcional, no lista de ubicaciones. Nombres iguales no identifican el mismo artículo; conservar el ID.
Orden de creación: Empresa → Almacen/Proveedor → Zona → Rack → Operario → login y cambio de contraseña temporal → Producto por PROVEEDOR → Inventario por OPERARIO → movimientos/orden y detalles → validación EMPRESA (ENVIADA) → recepción y detalles. Alertas/recomendaciones pueden producirse después de demanda; su aprobación genera nueva orden.
Las auxiliares las crean servicios, no requieren siembra. Cada creación API genera IDs: capturarlos y reutilizarlos. Una orden con lineas ya crea DetalleReposicion; una recepción con detalles ya crea DetalleRecepcion: no repetir ambas vías.
Borrar Inventario exige stock_actual=0; borrar Rack/Producto bloquea cualquier inventario, incluso con stock0. Empresa/Almacen/Zona/Operario/Proveedor no tienen control integral de dependencias ni cascada: referencias huérfanas son posibles. No borrar maestros necesarios para historia/forecast.

## 3. Reglas de negocio que afectan validez

### Enumeraciones (strings exactos al persistir)

| Tipo | Valores permitidos |
|---|---|
| TipoAlerta | RIESGO_STOCKOUT, STOCK_BAJO, SOBRESTOCK, CONSUMO_ANOMALO, PROXIMO_VENCIMIENTO |
| NivelRiesgo | BAJO, MEDIO, ALTO, CRITICO |
| EstadoAlerta | ACTIVA, VISTA, RESUELTA, IGNORADA |
| EstadoRecepcion | CONFORME, RECHAZADO, EN_EVALUACION |
| TipoMovimiento | ENTRADA, SALIDA, AJUSTE |
| MotivoMovimiento | RECEPCION, REPOSICION, VENTA, MERMA, VENCIMIENTO, DEVOLUCION, CONTEO_FISICO, OTRO |
| EstadoOrdenReposicion | PENDIENTE, OBSERVADA, APROBADA, ENVIADA, PARCIAL, RECIBIDA, CANCELADA |
| OrigenOrden | MANUAL, RECOMENDACION_IA |
| EstadoProveedor | ACTIVO, INACTIVO |
| EstadoRack | DISPONIBLE, LLENO, MANTENIMIENTO |
| TipoRecomendacion | REABASTECER, NO_REABASTECER, REDUCIR_REPOSICION, TRASLADAR_STOCK, REVISAR_CONSUMO, REVISAR_INVENTARIO |
| EstadoRecomendacion | PENDIENTE, VALIDADA_OPERARIO, CAMBIOS_SOLICITADOS, APROBADA_EMPRESA, ACEPTADA, RECHAZADA, APLICADA, EXPIRADA |

### Invariantes y límites del flujo

| Regla | Condición/acción real relevante para datos |
|---|---|
| Autoría/tenant | EMPRESA crea estructura física/cuentas; PROVEEDOR crea/edita sus productos; OPERARIO crea inventario, solicita órdenes y recibe. id_empresa/id_proveedor/id_operario enviados no sustituyen identidad del token. Operario actúa en su almacén. Debe cambiar contraseña temporal antes de operaciones. |
| Texto/cuentas | Correo se normaliza lower/strip; correo de cuentas no puede duplicarse entre empresa/operario/proveedor con cuenta; Empresa RUC y Proveedor RUC se consultan globalmente. No asumir índice unique, RUC numérico ni verificación SUNAT. Longitud del DTO se evalúa antes de strip; no equivale a validación de texto final no vacío. |
| Zona/rack | Zona min<=max si ambos presentes. nivel rack<=zona.capacidad; nivel y código no repetidos por zona; código strip/uppercase. Zona refrigerada exige ambas temperaturas rack; zona no refrigerada las prohíbe. RackUpdate valida rango resultante. |
| Kg/refrigeración | Carga rack=sum(stock_actual*peso) sobre inventarios; libre=capacidad-carga. Ingreso no cabe si kg>libre+1e-9. Asignación inicial/recepción exige DISPONIBLE. Incrementos del servicio Movimiento omiten esa exigencia. Producto refrigerado requiere ambas temperaturas y min<=max; rango completo del rack debe quedar dentro del producto. |
| Inventario | Inicial>=0, min/max>=0, min<=max, inicial<=max, no repetir producto+rack y validar kg/temperatura. U solo límites, descarta None; puede reducir max por debajo del saldo. NO se actualiza rack/producto/stock mediante InventarioUpdate. |
| Movimiento público | Solo SALIDA con motivo VENTA o VENCIMIENTO; otro tipo/motivo produce422 aunque esté en Enum/DTO. id_detalle_recepcion del cliente se borra; id_operario proviene del token. fecha_hora no es campo del DTO: se genera al insertar. |
| Movimiento interno | ENTRADA suma; SALIDA resta y cantidad<=stock disponible; AJUSTE fija stock_nuevo=cantidad. Todos cantidad>0: AJUSTE a0 no permitido. Operario existe/ACTIVO. Nuevo stock>=0; incremento positivo valida kg. No controla stock_maximo de forma universal. |
| Compatibilidad tipo/motivo interno | ENTRADA: RECEPCION, REPOSICION, DEVOLUCION, CONTEO_FISICO, OTRO. SALIDA: VENTA, MERMA, VENCIMIENTO, CONTEO_FISICO, OTRO. AJUSTE: CONTEO_FISICO, OTRO. Estas combinaciones no amplían el contrato público. |
| Concurrencia/idempotencia | Stock CAS por id_inventario+stock_anterior; si cambió,409. Después inserta movimiento; error intenta compensar con otro CAS. No transacción stock+ledger; kg compartidos/duplicados por aplicación tienen carreras. Movimiento previo por id_detalle_recepcion devuelve existente. |
| Orden/detalle | Almacén/proveedor de empresa, proveedor ACTIVO; lineas productos existentes de empresa sin duplicar. Detalle independiente valida pertenencia si id_empresa de producto presente. Detalles editables/agregables/eliminables solo PENDIENTE/OBSERVADA. Despacho exige líneas de la orden y cantidad>0, pero no compara con solicitado en ese método. |
| Estados orden | Nuevo PENDIENTE; U PENDIENTE/OBSERVADA; validar PENDIENTE/APROBADA con al menos un detalle →ENVIADA; devolver PENDIENTE→OBSERVADA; reenviar OBSERVADA→PENDIENTE; cancelar PENDIENTE/OBSERVADA/APROBADA→CANCELADA; borrar solo PENDIENTE. aprobar/enviar internos son alias de validar. |
| Recepción | Cabecera exige orden ENVIADA/PARCIAL, operario ACTIVO del almacén, detalles de orden e inventarios de producto/almacén correcto; si producto refrigerado exige temperatura_recepcion. No confundir exigir temperatura con verificar que esté dentro del rango. Prevalida kg acumulados por rack. |
| Cantidad/estado recepción | recibida>0; 0<=rechazada<=recibida; rechazo>0 o estado RECHAZADO/EN_EVALUACION exige motivo/comentario. EN_EVALUACION aceptada=0; otros aceptada=recibida-rechazada, incluso RECHAZADO. Aceptada anterior+actual<=solicitada en crear. Aceptada>0 genera ENTRADA/RECEPCION. lote default SIN_LOTE, luego strip. |
| Resolución/orden recibida | Solo CONFORME/RECHAZADO; aceptada/rechazada>=0 y suman recibida; si omitidas se derivan de detalle. Movimiento previo vuelve idempotente. Resolver no vuelve a cotejar producto de inventario alternativo ni cupo acumulado. Total aceptado>=solicitado→RECIBIDA; >0→PARCIAL;0 no cambia orden. |
| Alertas/recomendaciones | Alerta ACTIVA por inventario+tipo se actualiza; nueva ACTIVA. Recomendación busca estado PENDIENTE o ACEPTADA por inventario+tipo; actualiza si existe, nueva PENDIENTE. No hay unique compuesto declarado. Manual permite referencias incoherentes salvo almacén validado. |
| Transiciones recomendación | PENDIENTE→VALIDADA_OPERARIO/RECHAZADA; VALIDADA_OPERARIO→APROBADA_EMPRESA/CAMBIOS_SOLICITADOS/RECHAZADA; CAMBIOS_SOLICITADOS→VALIDADA_OPERARIO/RECHAZADA; APROBADA_EMPRESA→APLICADA. ACEPTADA/EXPIRADA existen en Enum sin transición habilitada aquí. |
| Orden desde recomendación | Solo APROBADA_EMPRESA, tipo REABASTECER, cantidad_recomendada>0 y IDs empresa/almacén/producto completos; proveedor/costo requeridos. Genera orden+detalle y marca APLICADA; multietapa no transaccional. Recomendación de riesgo no descuenta stock ni compra automáticamente. |
| Null en U | Inventario/Operario descartan None; propuesta excluye None; Rack descarta estado=None pero exige temperaturas completas resultantes si se editan. Producto/Almacen/Zona/Empresa/Proveedor/DetalleReposicion pueden conservar o procesar null y romper Response/invariantes; proveedor.estado=None usa .value y empresa.ruc=None usa .strip. Omitir claves que no cambian; no usar null como borrado universal. |
| Cambio de producto | OPERARIO solo id_rack; PROVEEDOR excluye id_rack. ProductoUpdate relaja longitud/peso/volumen respecto C; stock siempre descartado. Modificar peso/temperatura puede desvirtuar capacidad almacenada: evitar datos físicamente inválidos aunque U no replique todos los límites C. |
| Verificación/email | Código6 dígitos, SHA256; defaults TTL10min/cooldown60s/max5 intentos; usado/expirado/bloqueado no verifica. Evento ENVIADO/OMITIDO se deduplica en notify_owner, no uniformemente en envío a proveedor. Flags de verificación pueden resetearse al cambiar correo; no asumir invalidación completa de códigos viejos en cada U. |

## 4. Formato de entrada y almacenamiento

| Aspecto | Contrato actual |
|---|---|
| JSON de entrada | Usar campos C/DTO de operación; no enviar campos G para imponer IDs/fechas. BaseModel normalmente ignora extras: un campo no declarado no amplía el esquema. ForecastArgs prohíbe extras. |
| Documento Mongo | Tipos str/enum→BSON string, int→entero BSON, float→double, bool→boolean, dict→documento, list→array, None→null. Ausencia de campo y null son diferentes; auxiliar/auditoría condicional puede faltar. |
| IDs | UUID4 str de negocio generados por servicios/repositorios; Almacen/Zona guardan id. Mongo genera _id:ObjectId independiente, excluido en respuestas. IDs recibidos suelen ser str sin regex UUID, pero referencias deben resolver al documento correcto. |
| Alias | AlmacenResponse.id acepta id o id_almacen; ZonaResponse.id acepta id o id_zona al validar. JSON de salida usa id. Algunas consultas admiten variantes legacy, pero AlmacenRepository update/delete usan id. No normalizar todas las claves a id_* por cuenta propia. |
| Decimal | C longitud/latitud Decimal, rangos/dígitos/decimales en tabla; service convierte a float/BSON double. Response Decimal puede serializarse como string. Decimal128 NO IMPLEMENTADO para coordenadas. |
| Fechas | Empresa.fecha_creacion/fecha_actualizacion: string ISO8601 UTC. Resto datetime UTC→BSON date; JSON respuesta ISO8601. Forecast retorna fechas YYYY-MM-DD; no guardar strings históricos donde consultas esperan BSON date. Motor no configura tz_aware explícito. |
| Seguridad | Empresa.password guarda bcrypt hash; Operario/Proveedor usan password_hash. password_temporal no se almacena. Hashes se excluyen de respuesta; tiene_cuenta se calcula. No distribuir claves/JWT/códigos/hashes reales en datos para otra IA. |
| Generados | PK UUID, fechas y estados iniciales; correo_verificado=False y fecha_verificacion_correo=None al crear Empresa/Operario/Proveedor; cuenta temporal→debe_cambiar_password=True; Movimiento deriva id_producto/id_rack/stock_anterior/stock_nuevo y fecha_hora; DetalleRecepcion deriva cantidad_aceptada/id_rack/ubicado/id_movimiento; Zona deriva id_empresa; campos token prevalecen. |
| Copias anidadas | Orden.lineas no está en cabecera: detalles separados. Recepción.detalles sí guarda copia Create y además crea detalles separados; respuesta consulta estos. Cambios/resolución no sincronizan copia embebida. |
| Campos de respuesta | Rack kg libres/carga, Movimiento operario_nombre/id_zona, cuenta tiene_cuenta e historial operario_nombre se enriquecen sin persistir. Campos internos ausentes del DTO Response pueden quedar excluidos aunque se guarden en Mongo. |
| Índices declarados | movimientos.id_detalle_recepcion unique parcial para strings; notificaciones_email.event_id unique. Creación de índices puede fallar sin detener servicio: instalación real NO VERIFICABLE. No índice compuesto producto+rack/correo/RUC/nivel/fecha ni validador Mongo $jsonSchema declarado en alcance. |
| Carga directa/API | Importador de lote NO IMPLEMENTADO. API crea efectos/IDs actuales; insert directo hipotético debe reproducir saldos, referencias, defaults y efectos coherentes. No mezclar ambos enfoques ni saltar servicios creyendo que Mongo validará reglas. |

## 5. Series temporales, forecasting y logística

### Identidad, objetivo y ventana

Serie operativa: `id_inventario`; contexto `id_producto`, `id_rack`, `id_zona`, `id_almacen`, `id_empresa`. `series_id`: NO IMPLEMENTADO. Un producto multirack tiene varias series de inventario.
Objetivo `demanda:float` = suma diaria UTC de `movimientos.cantidad` con tipo_movimiento=SALIDA, sin filtro por motivo: no es ventas exclusivamente ni demanda latente. Granularidad D; fuente fecha_hora BSON date, agregación YYYY-MM-DD.
DemandHistory crea calendario y rellena días sin SALIDA con0. No distingue observación ausente de cero. Fecha inválida se descarta; demanda no numérica se convierte a0; FeatureBuilder ordena y conserva último duplicado fecha, pero no completa por sí mismo días faltantes.
Ventana DemandHistory default400; API debug default30 y1..500; API predict-7-days default30 y7..500; riesgo usa30. API no expone fecha_fin/corte histórico; por defecto termina hoy UTC. Historial 2020–2025 no entra en ventana actual30 días de2026.
Resumen historial_suficiente_ml usa longitud>=367, incluso calendario rellenado; no acredita observación. Modelos D+1..D+7 directos, no recursivos; Saiki solo horizonte7. Otros horizontes e intervalos: NO IMPLEMENTADOS.

### Features: nombres exactos y disponibilidad real

136 nombres esperados por artefactos. Solo los derivados/calendario/agregados siguientes reciben datos del flujo actual; pueden ser NaN por historia insuficiente. Los campos de origen M5 pendientes no se convierten en predictores disponibles por estar en config.

| Grupo | Variables exactas | Uso actual |
|---|---|---|
| Identificación esperada | `item_id`, `dept_id`, `cat_id`, `store_id`, `state_id` | NO IMPLEMENTADO mapeo/fuente en flujo; NaN; atributos estáticos esperados |
| Calendario base | `month`, `year`, `dayofweek`, `day`, `weekofyear`, `is_weekend`, `quarter`, `dayofyear`, `is_month_start`, `is_month_end` | IMPLEMENTADO desde fecha_base; enteros/flags, dayofweek0..6 |
| Nivel/contexto histórico | `age_days`, `current_y` | IMPLEMENTADO: age_days=len(historia)-1; current_y=última demanda |
| Lags | `lag_1`, `lag_2`, `lag_3`, `lag_4`, `lag_5`, `lag_6`, `lag_7`, `lag_14`, `lag_21`, `lag_28`, `lag_35`, `lag_42`, `lag_56`, `lag_364`, `lag_365`, `lag_366` | IMPLEMENTADO por posición de fila; valores float o NaN |
| Rolling/EWMA | `rolling_mean_3`, `rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28`, `rolling_mean_56`, `rolling_mean_180`, `rolling_std_3`, `rolling_std_7`, `rolling_std_28`, `rolling_std_56`, `rolling_max_3`, `rolling_max_7`, `rolling_max_28`, `ewma_3`, `ewma_7`, `ewma_14`, `ewma_28` | IMPLEMENTADO ventanas indicadas por nombre; mean/std/max requieren ventana completa; std ddof0; EWMA adjust=False |
| Comportamiento | `zero_ratio_7`, `zero_ratio_28`, `change_1_2`, `change_1_3`, `change_1_7`, `ratio_mean3_mean14`, `ratio_mean7_mean28`, `acceleration_3_7`, `acceleration_7_28`, `max7_vs_mean28`, `max3_vs_mean28`, `previous_7_mean`, `recent7_vs_previous7`, `dow_mean_4w`, `growth_streak_3`, `peak_count_7`, `days_since_sale`, `sale_rate_28`, `current_vs_mean7`, `current_vs_mean28` | IMPLEMENTADO diferencias, ratios, frecuencias, medias y cambios históricos |
| Incrementos | `rolling_inc_mean_3`, `rolling_inc_mean_7`, `rolling_inc_mean_14`, `rolling_inc_mean_28`, `rolling_inc_std_7`, `rolling_inc_std_28` | IMPLEMENTADO estadísticas sobre diff(demanda), float/NaN |
| Agregados históricos | `store_sales_lag_1`, `store_sales_lag_7`, `store_sales_lag_28`, `store_sales_mean_7`, `store_sales_mean_28`, `dept_sales_lag_1`, `dept_sales_lag_7`, `dept_sales_lag_28`, `dept_sales_mean_7`, `dept_sales_mean_28`, `item_total_lag_1`, `item_total_lag_7`, `item_total_lag_28` | IMPLEMENTADO desde SALIDA por producto/listas; limitaciones espaciales descritas abajo |
| Calendario objetivo | `target_month`, `target_dayofweek`, `target_day`, `target_weekofyear`, `target_is_weekend`, `target_quarter`, `target_dayofyear` | IMPLEMENTADO desde fecha_base+horizon; conocido a futuro sin fuente externa |
| Lags objetivo | `future_lag_7`, `future_lag_14`, `future_lag_21`, `future_lag_28`, `future_lag_35`, `future_lag_42`, `future_lag_364`, `future_lag_365`, `future_lag_366`, `future_dow_mean_6w`, `future_dow_std_6w` | IMPLEMENTADO desde historia; desplazamiento lag-horizon, medias/std del weekday objetivo |
| Agregados desplazados | `future_store_lag_7`, `future_dept_lag_7` | IMPLEMENTADO consulta fecha_base-(7-horizon) en serie agregada |
| Datos externos esperados | `has_event`, `snap`, `event_name_1`, `event_type_1`, `event_name_2`, `event_type_2`, `sell_price`, `price_available`, `price_lag_1`, `price_lag_7`, `price_change_1`, `price_change_7`, `price_mean_28`, `price_relative_28`, `price_mean_180`, `price_std_180`, `price_min_180`, `price_max_180`, `price_relative_180`, `price_to_max_180`, `price_range_position_180`, `future_sell_price`, `future_price_available`, `future_snap`, `future_has_event`, `future_event_name_1_code`, `future_event_type_1_code` | NO IMPLEMENTADO abastecimiento en flujo actual; NaN salvo context externo explícito; sin contratos operativos para precio/eventos/SNAP |

Categorías del booster: item_id/dept_id/cat_id/store_id/state_id/event_name_1/event_type_1/event_name_2/event_type_2. FeatureBuilder convierte a pandas category; resto numérico, Inf→NaN. No existe mapeo UUID a vocabulario entrenado M5. Promociones/descuentos están EXCLUIDOS; tampoco asumir feriados, sensores o eventos observados.
Semántica exacta: FeatureBuilder lag_k toma k-ésimo valor desde final: lag_1=current_y. Rolling incluye última observación. Future lag con lag-horizon>=1 usa esa posición; si0 usa current_y; negativo NaN. MLContextBuilder lag_k usa fecha_base-k días: ambas convenciones difieren, no reinterpretarlas como iguales.
Agregados: item suma SALIDA por id_producto; dept categoría de productos seleccionados en almacén; store lista de productos obtenida por Producto.id_rack de referencia. Consultas por id_producto no filtran ubicación física: producto multialmacén puede contaminar agregados. Categoría global no alimenta dept_sales. Contexto usa29 fechas y medias anteriores excluyen día base.
La regla futura de compatibilidad es conservar fechas diarias continuas/observadas y corte sin datos posteriores, no fabricar ceros o covariables para afirmar suficiencia. Ventana30 deja lags anuales/rolling180 sin datos; nombres presentes no significan valores válidos.

### Entrada/salida del motor y resultados logísticos

Entrada FeatureBuilder: DataFrame con `fecha` parseable y `demanda` numérica; `horizon:int`1..7; `context:dict` opcional de features. Fila del modelo:136 columnas en orden config; contexto actual13 agregadas+2 desplazadas. Los datos maestros/stock alimentan contexto/riesgo, no todas las columnas de booster.
Inferencia: siete boosters globales LightGBM regression_l1; existen63 locales pero no usados por DemandPredictor. scale/alpha/beta/ensemble de metadata no se aplican. No ejecutar entrenamiento para generar datos compatibles.
Salida individual: float>=0. Predictor siete días: `demanda_7d:float`, `predicciones_diarias:list` con `horizonte:int`, `fecha:str YYYY-MM-DD`, `demanda_predicha:float>=0` (round4). API usa `demanda_total_7d`, `demanda_promedio_diaria`, `fecha_base`, `periodo_forecast.desde/hasta`, más IDs y metadatos; no devuelve stock futuro.
Resultado InventoryRisk y sus DTO anidados (calculados, no colecciones):

| Contrato | Campos exactos y restricciones |
|---|---|
| InventoryRiskResponse | `id_empresa`:str [obligatorio]; `id_almacen`:str [obligatorio]; `id_inventario`:str [obligatorio]; `id_producto`:str [obligatorio]; `stock_actual`:float [obligatorio] {≥0}; `consumo`:ConsumoInfo [obligatorio]; `cobertura`:CoberturaInfo [obligatorio]; `lead_time_dias`:int [obligatorio] {≥0}; `forecast`:ForecastInfo [obligatorio]; `seguridad`:SeguridadInfo [obligatorio]; `riesgo`:RiesgoInfo [obligatorio]; `reposicion`:ReposicionInfo? [default=None]; `explicacion`:str? [default=None] |
| ConsumoInfo | `promedio_7d`:float [obligatorio] {≥0}; `promedio_14d`:float [obligatorio] {≥0}; `promedio_28d`:float [obligatorio] {≥0}; `tendencia_porcentaje`:float [obligatorio] |
| CoberturaInfo | `dias`:float? [default=None] {≥0} |
| ForecastDiario | `fecha`:datetime [obligatorio]; `demanda_predicha`:float [obligatorio] {≥0} |
| ForecastInfo | `demanda_7d`:float? [default=None] {≥0}; `fecha_quiebre_estimada`:datetime? [default=None]; `predicciones_diarias`:list[ForecastDiario] [default=factory list] |
| SeguridadInfo | `stock_seguridad`:float [obligatorio] {≥0}; `punto_reposicion`:float [obligatorio] {≥0} |
| RiesgoInfo | `nivel`:NivelRiesgo [obligatorio]; `score`:float [obligatorio] {≥0; ≤100} |
| ReposicionInfo | `cantidad_minima`:int [obligatorio] {≥0}; `cantidad_recomendada`:int [obligatorio] {≥0}; `cantidad_segura`:int [obligatorio] {≥0} |

Fórmulas: consumo_diario=max(primer promedio histórico positivo7/14/28, demanda_7d/7); cobertura=stock_actual/consumo (None si consumo<=0); seguridad=round(1.645*pstdev(consumos28)*sqrt(lead_time_dias),2) si lead/desviación>0, si no0; punto=round(consumo*lead+seguridad,2).
Reposición recomendada=ceil(max(0,consumo*max(lead+7,7)+seguridad-stock_actual)); mínima=ceil(recomendada*0.85), segura=ceil(recomendada*1.15); sin consumo→None. No limita por capacidad/stock_maximo dentro de esa fórmula. Quiebre: primer día con demanda acumulada>=stock; stock<=0→fecha_base; no quiebre en7→None.
Riesgo: CRITICO si stock<=0 o cobertura<=lead>0; BAJO si cobertura None con stock>0; ALTO si stock<=punto>0; MEDIO si cobertura<=1.5*lead>0; BAJO resto. Score: stock<=0→100; cobertura/lead<=1,1.5,2 suma60,40,20; stock/punto<=0.5,1,1.25 suma40,30,15; tope100.
Si generar_alertas=True: ALTO/CRITICO crean/actualizan RIESGO_STOCKOUT y REABASTECER; otros riesgos resuelven alerta activa. Evaluación individual defaultTrue puede escribir incluso mediante GET; Saiki usaFalse. No todas las enumeraciones de alertas/recomendaciones tienen detectores automáticos.

### LLM

IMPLEMENTADO Saiki/Ollama, default qwen3:4b; interpreta datos/forecast del backend y no sustituye LightGBM. Entrada/salida Saiki están en §1. History≤40 mensajes, cada uno solo role=user/assistant y content:str≤8000, sin claves adicionales; message/question al menos uno, no whitespace, si ambos coinciden.
Herramientas: get_inventory, get_product, get_forecast, get_inventory_risk, get_active_alerts, get_recommendations, get_recent_movements, get_warehouse_status; autorizadas y filtradas para EMPRESA. ForecastArgs: id_inventario:str longitud≥1, dias:int default30/7..500, horizonte_dias:int default7/solo7, extra=forbid; horizonte no es ventana histórica.
Ollama intercambia model/messages/tools/stream=False/think=False; retorna message.content o function.name+arguments, resultados tool alimentan answer/data/sources. Máximo4 iteraciones. Hay respuestas backend sin LLM; no herramientas de escritura operativa ni persistencia independiente del chat.

## 6. Información faltante y decisiones para un generador

| Estado | Componente o decisión |
|---|---|
| NO IMPLEMENTADO | Entidades/colecciones independientes de ventas diarias, demanda latente, forecast persistido, snapshots diarios de inventario o series_id. inventario_historial registra CREAR/EDITAR_LIMITES, no cada movimiento ni stock diario. |
| NO IMPLEMENTADO | Importador de datasets, pipeline de entrenamiento, Vertex AI, intervalos de incertidumbre, forecast30/90 días, mapeo UUID→categorías M5 y fuentes operativas de precio/calendario/SNAP. Hay artefactos M5 locales, no integración completa de su dataset de origen. |
| NO IMPLEMENTADO | Sensores, control automático FEFO/consumo por lote, detección universal de vencimientos, FK/cascada DB, transacción multientidad y reservas atómicas de kg por rack. Lote/fecha_vencimiento de recepción no crean inventario por lote. |
| NO VERIFICABLE | Documentos/índices reales Mongo, validadores creados fuera del código, configuración efectiva del entorno, disponibilidad SMTP/Ollama, precisión del modelo, vocabularios categóricos válidos para nuevos IDs y ejecución runtime de contratos. Python base de entornos no estaba disponible en auditoría. |
| Inconsistencia actual | EmpresaDocument antiguo usa id/password_hash y no coincide con servicio id_empresa/password/ruc; factories TypedDict no gobiernan flujos activos. Verificación correo escribe datetime donde EmpresaResponse espera str. No basar generación en modelos obsoletos ni ocultar discrepancia. |
| Decisión pendiente | Elegir carga API operativa o futura importación offline autorizada. API no acepta fecha_hora histórica de movimiento y modifica saldos; Mongo directo no ejecuta validaciones/efectos. No existe mecanismo compatible de importación histórica ya implementado. |
| Decisión pendiente | Definir corte/continuidad observada y semántica de objetivo: backend actual usa toda SALIDA. No imponer ventas exclusivamente ni distinguir ausencia/cero como si ya existiera. No generar targets desde predicciones. |
| Decisión pendiente | Definir vocabulario/mapeo de categorías y fuentes conocidas al corte si se usan boosters actuales. No inventar promociones/descuentos ni asumir feriados/eventos/sensores. Tener136 columnas no garantiza compatibilidad semántica/calidad. |
| Requisito de compatibilidad futura | Validar DTO C/U, defaults, rol/tenant, referencias, unicidad por servicio, kg/rangos térmicos, saldos y estados antes de cargar. Reconciliar apertura+movimientos con stock final; no registrar cantidad0 ni duplicar detalles anidados. Es especificación previa, no validador implementado aquí. |

Trazabilidad principal: app/dto/*_dto.py (tablas), app/services/{inventario,rack,movimiento,orden_reposicion,detalle_recepcion,recomendacion}_service.py (invariantes), app/controllers/movimiento_controller.py:86 (restricción pública), app/repositories/recepcion_mercaderia_repository.py:18 (copia embebida), app/ml/feature_builder.py:292 (lags), app/ml/ml_context_builder.py:408 (lags de agregados), app/database/mongodb.py:53 y70 (índices).
