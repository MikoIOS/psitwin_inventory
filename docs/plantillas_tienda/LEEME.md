# Plantillas de levantamiento de la tienda

Usa el Excel de seis hojas o los seis CSV UTF-8 equivalentes. La fila de ejemplo
de cada hoja está marcada **SIMULADO** y no representa ventas, productos ni
proveedores reales. Bórrala de la copia de trabajo antes de cargar datos reales.
Las filas azules del Excel están reservadas para captura. No hay fórmulas ni
pronósticos precalculados. Los CSV contienen encabezado y un ejemplo.

Estas son plantillas de **levantamiento**, no un importador universal de PsiTwin.
Conserva el archivo del POS original y adapta una copia al contrato del importador
de demanda antes de cargar. Mantén un mapeo de SKU comercial a `id_producto`.
No inventes valores para completar campos vacíos ni mezcles unidades.

Campos comunes: `origen_datos` = REAL o SIMULADO; `sku_tienda` = código estable de
producto y presentación; `proveedor_codigo` = alias que enlaza las hojas; los
códigos y fechas se conservan como texto para evitar perder ceros o cambiar de
zona horaria. Fechas: AAAA-MM-DD; horas: AAAA-MM-DD HH:MM en Lima. Sufijo `_pen`
significa soles; `_base` significa la unidad vendible declarada en Catálogo.
Un vacío significa pendiente/no disponible, no cero. Cero solo si se comprobó.

## Catálogo

| Columna | Significado |
|---|---|
| nombre | Nombre y tamaño reconocibles; no cambiarlo para crear una duplicación |
| marca | Marca del empaque, si corresponde |
| categoria / familia | Clasificación comercial y familia usada por el catálogo |
| presentacion | Tamaño/envase de esta referencia, p. ej. bolsa 1 kg |
| unidad_base | Unidad vendible de conteo, p. ej. bolsa, botella o paquete |
| unidades_por_caja | Factor para convertir cajas a unidades base; mayor que cero |
| peso_kg_unidad | Kilogramos por unidad base; el backend lo exige para carga del rack |
| precio_compra_pen | Costo unitario; puede usarse en línea de reposición, no hay precio dedicado en catálogo |
| precio_venta_pen | Precio unitario comercial externo; el DTO actual no lo persiste como precio del producto |
| lead_time_dias | Días entre pedido y recepción; no frecuencia de compra |
| vida_util_dias | Vida útil según fabricante; no fecha real de vencimiento de cada lote |
| requiere_refrigeracion | SI/NO según producto; si SI, levantar también límites y fuente en la guía |

SKU, presentación, unidad y conversión de caja sirven como mapeo externo: no
asumas que existen esos campos dedicados en el DTO actual. Stock usa cantidades
enteras; los productos fraccionables requieren acordar la unidad sin redondear ocultamente.

## Stock

| Columna | Significado |
|---|---|
| fecha_corte_lima | Instante del conteo y del saldo del sistema que se comparan |
| almacen / zona / rack | Ubicación física exacta; cada fila corresponde a una ubicación y, si aplica, lote |
| stock_fisico | Unidades realmente contadas |
| stock_sistema | Unidades que muestra el registro actual de la tienda |
| reservado | Unidades comprometidas que no se deben considerar libres; registro externo |
| no_vendible | Unidades dañadas, vencidas o bloqueadas; registro externo separado |
| stock_minimo / stock_maximo | Límites operativos del detalle de inventario; máximo no menor que mínimo ni saldo inicial |
| lote | Identificador del lote; no unir dos lotes con vencimientos distintos |
| fecha_vencimiento | Fecha impresa del lote; disponible en Recepciones, no un campo único de stock por producto |
| responsable_rol | Rol que confirma el conteo; evita nombres personales innecesarios |

No cargues dos veces el mismo saldo al registrar producto e inventario. Para
conciliar calcula por separado físico utilizable, reservado y disponible acordado.

## Ventas

| Columna | Significado |
|---|---|
| fecha_lima | Día comercial de la venta; conservar cómo se convierte a UTC si se importa |
| local_codigo | Sucursal que realizó la venta; no sumar locales sin definir el alcance |
| unidades_vendidas | Ventas observadas del día y SKU; no mermas ni demanda no atendida |
| unidades_devueltas | Devoluciones de clientes, separadas de ventas brutas |
| estado_dia | ABIERTO_CON_STOCK, AGOTADO, CERRADO o SIN_DATO; explica el cero o el vacío |
| promocion | Descripción/código de promoción; NO si se confirmó que no existió |
| fuente_documento | Archivo/reporte del que se obtuvo el dato; sin datos de clientes |

Una fila por SKU/local/fecha. No pegues el total mensual debajo como si fuera otra
venta diaria. Si no sabes si el dato son ventas brutas o netas, pregunta y anótalo.

## Proveedores

| Columna | Significado |
|---|---|
| nombre_alias | Nombre comercial o alias no personal autorizado |
| dias_entrega_estimados | Estimación normal de pedido a recepción |
| dias_entrega_min / dias_entrega_max | Rango observado, con fuente; vacío si se desconoce |
| dias_visita | Días de visita o entrega; describir cuál de ambos representa |
| pedido_minimo_unidades | Compra mínima convertida a unidad base; si depende del producto, anotarlo en Reposición |
| costo_envio_pen | Costo por entrega; no repartir por producto sin regla acordada |

No incluye contraseñas. Para cuentas reales de proveedor el dueño autoriza los
datos de contacto y crea credenciales propias; esta hoja no concede acceso.

## Reposición

| Columna | Significado |
|---|---|
| pedido_codigo | Código de orden estable para enlazar documentos |
| fecha_necesidad | Día en que se detectó la falta, antes del pedido |
| fecha_pedido | Día en que se envió el pedido al proveedor |
| fecha_prometida | Compromiso de entrega, si existe |
| fecha_recepcion | Día real de ingreso; vacío mientras siga pendiente |
| cantidad_pedida_base / cantidad_recibida_base | Unidades base, no cajas sin convertir; admite recepción parcial como hecho documentado |
| frecuencia_compra_dias | Días entre compras habituales; distinto del plazo de entrega |
| estado | Pendiente, parcial, recibido o cancelado según el documento fuente |

Una fila por pedido y producto; si hay varias recepciones usa filas documentadas
sin duplicar la cantidad pedida al agregar totales.

## Movimientos

| Columna | Significado |
|---|---|
| evento_codigo | Identificador único de origen para detectar reenvíos/duplicados |
| fecha_hora_lima | Momento efectivo del evento |
| almacen_origen / rack_origen | De dónde salen las unidades o dónde ocurre el conteo |
| almacen_destino / rack_destino | Ubicación de entrada/transferencia, si aplica; vacío si no aplica |
| tipo | ENTRADA, SALIDA, AJUSTE o TRANSFERENCIA como descripción del hecho fuente |
| motivo | VENTA, RECEPCION, VENCIMIENTO, MERMA, DEVOLUCION, CONTEO_FISICO u otro documentado |
| cantidad_base | Unidades del evento; para un conteo final aclarar que es saldo, no una venta |
| documento | Ticket/guía/acta anonimizada que respalda el evento |
| responsable_rol | Rol responsable, sin contraseñas ni datos personales innecesarios |

La plantilla puede captar hechos que el backend actual aún no admite. No los
transformes en VENTA para forzar su carga. El endpoint público actual solo admite
SALIDA/VENTA y SALIDA/VENCIMIENTO; las entradas se generan desde Recepciones.
Las transferencias y ajustes completos requieren otra implementación validada.
