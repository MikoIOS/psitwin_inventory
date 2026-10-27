# Relaciones, restricciones e incompatibilidades

MongoDB no impone FKs SQL. Son referencias lógicas verificables por el generador; no todas las rutas actuales las comprueban. UUIDv5 determinístico es una decisión del generador, no una validación de los DTO.

| Entidad / colección | PK | Referencias | Relaciones |
|---|---|---|---|
| Empresa / empresas | id_empresa | — | 1:N almacenes, productos, operarios, proveedores |
| Almacén / almacenes | id | id_empresa | 1:N zonas, operarios |
| Zona / zonas | id | id_almacen, id_empresa | 1:N racks |
| Rack / racks | id_rack | id_zona | 1:N inventarios |
| Producto / productos | id_producto | id_empresa; id_proveedor, id_rack nullable | N:M almacenes mediante inventario; rack de referencia único |
| Inventario / inventarios | id_inventario | id_producto, id_rack | Único producto+rack |
| Operario / operarios | id_operario | id_empresa; id_almacen nullable legacy | Un almacén por operario demo |
| Proveedor / proveedores | id_proveedor | id_empresa | 1:N productos, órdenes |
| OrdenReposicion / ordenes_reposicion | id_orden_reposicion | id_empresa, id_almacen, id_proveedor; id_recomendacion/id_operario_solicitante nullable | 1:N detalles y recepciones |
| DetalleReposicion / detalles_reposicion | id_detalle_reposicion | id_orden_reposicion, id_producto | Único producto por orden |
| RecepcionMercaderia / recepciones_mercaderia | id_recepcion | id_orden_reposicion, id_operario | 1:N detalles |
| DetalleRecepcion / detalles_recepcion | id_detalle_recepcion | id_recepcion, id_detalle_reposicion, id_inventario; id_movimiento nullable | Varias recepciones por línea |
| Movimiento / movimientos | id_movimiento | id_inventario, id_producto, id_rack, id_operario; id_detalle_recepcion nullable | Una entrada por detalle aceptado |
| Alerta / alertas | id_alerta | id_empresa, id_almacen, id_inventario, id_producto | N:1 inventario |
| Recomendacion / recomendaciones | id_recomendacion | mismos; id_alerta nullable | N:1 inventario; puede originar orden |

El almacén de inventario se obtiene por inventario→rack→zona→almacén, **no por Producto.id_rack**. Todas las referencias preservan empresa y almacén; proveedores/productos de una orden pertenecen al tenant. Categoría y familia son strings, no entidades.

## Restricciones verificadas en servicios

- `app/services/rack_service.py`: nivel>=1 y <=Zona.capacidad; un rack por nivel/zona. Rack.capacidad es **kg**; carga=sum(stock_actual*peso). Zona.capacidad es número de niveles. area_m2/aforo de almacén no definen capacidad de productos. El código no permite convertir aforo o área en kg.
- Temperaturas de rack solamente si zona.refrigerada; ambas obligatorias en zona refrigerada. Para producto refrigerado, rango rack contenido en rango permitido del producto. Asignación inicial exige DISPONIBLE y carga libre. Temperaturas mínimas<=máximas. `ZonaCreate` no tiene validador de rango: no atribuir al DTO esa regla.
- `inventario_service.py`: producto y rack existentes, producto+rack único, stock_minimo<=stock_maximo, stock_actual inicial<=stock_maximo y asignación física válida. Update solo modifica límites. La política demo mantendrá stock<=máximo también durante la historia; los movimientos del backend no siempre controlan ese máximo.
- `movimiento_service.py`: cantidad>0. ENTRADA motivos RECEPCION/REPOSICION/DEVOLUCION/CONTEO_FISICO/OTRO; SALIDA motivos VENTA/MERMA/VENCIMIENTO/CONTEO_FISICO/OTRO; AJUSTE motivos CONTEO_FISICO/OTRO. ENTRADA suma; SALIDA resta con stock suficiente; **AJUSTE fija stock_nuevo=cantidad**, no delta. No permite AJUSTE a cero. Incrementos validan kg con exigir_disponible=False. Operario activo obligatorio.
- `database/mongodb.py`: índice único parcial de movimientos.id_detalle_recepcion cuando es string; null no debe convertirse en string vacío. Servicio devuelve movimiento existente para idempotencia y usa actualización condicional de stock.
- `detalle_recepcion_service.py`: aceptada=recibida-rechazada en caso resuelto; EN_EVALUACION aceptada=0 y no disponible. Rechazo/evaluación requiere motivo/comentario. Suma aceptada por línea no excede solicitada. Producto del inventario coincide con línea y almacén de orden. Perfil base CONFORME sin rechazos evita ambigüedad.
- Órdenes: PENDIENTE→ENVIADA→PARCIAL→RECIBIDA, también recepción completa directa. OBSERVADA requiere comentario y reenvío; APROBADA es legacy. Proveedor ACTIVO; líneas sin productos repetidos. La aprobación actual lleva a ENVIADA.
- Recomendaciones: PENDIENTE→VALIDADA_OPERARIO→APROBADA_EMPRESA→APLICADA; CAMBIOS_SOLICITADOS vuelve a VALIDADA_OPERARIO; rechazo permitido según estado. Crear orden exige REABASTECER y cantidad>0. No basta que un enum permita un valor para que cualquier transición sea válida.
- Alertas activas se buscan por inventario+tipo y ACTIVA/VISTA. Recomendaciones pendientes se buscan por inventario+tipo y PENDIENTE/ACEPTADA; este filtro no cubre todos los estados del circuito nuevo. No precargar múltiples propuestas abiertas para ocultar esa diferencia.

## Incompatibilidades verificadas

1. `empresa_model.py`: TypedDict usa id/password_hash, omite ruc, declara fechas datetime. Servicio/repositorio real usan id_empresa/ruc/password y fechas ISO string. No usar modelo antiguo para importar.
2. Almacén: DTO Decimal con 6 decimales vs modelo/servicio float. Response devuelve id; acepta alias id_almacen. CSV canónico id; referencias siguen llamándose id_almacen.
3. `zona_model.py` omite refrigerada, que sí persiste el servicio. Response id acepta alias id_zona; repositorio admite ambos. CSV canónico id.
4. RackRepository acepta id/id_rack en algunas lecturas; otros enriquecimientos consultan exclusivamente id_rack. Generar id_rack. carga_kg/libre_kg son derivados de inventarios, no fuente de stock.
5. ProductoCreate/Update aceptan stock; ProductoService lo elimina. Response stock=0 es compatibilidad legacy. **Stock verdadero=Inventario.stock_actual**. CSV producto omite stock.
6. Producto.id_rack es una sola referencia. `ProductoRepository.obtener_por_almacen` selecciona productos por rack de referencia, no por inventarios. `MLContextBuilder` después suma movimientos por IDs de producto sin filtro de almacén: un SKU presente en tres almacenes puede omitirse de selección o mezclar almacenes en agregados store/dept. Mantener 30 SKU/90 inventarios y advertir; no duplicar SKU para esconderlo.
7. DemandHistory y riesgo agregan todas las SALIDA, no solo VENTA. Ventas históricas son extensión, sin consumidor CSV actual. Mermas/vencimientos cambiarían el objetivo implícito del modelo.
8. Identificación M5, precios, eventos/SNAP quedan NaN sin context. No existe mapeo UUID→vocabulario M5 ni consumidor precios/calendario. Nuevos datos no garantizan calidad de boosters existentes.
9. Riesgo/default API usan 30 días aunque hay lag_366/rolling_180. `missing_features` comprueba nombres, no suficiencia de datos: NaN pasa presencia.
10. Backend usa reloj actual; 2020–2025 cargado en octubre 2026 produce ceros recientes. El corte fijo del manifiesto no cambia el reloj. Se requiere replay offline o perfil desplazado separado posterior; no está implementado soporte de fecha de corte en las rutas públicas actuales.
11. APIs crean UUID/fechas actuales. MovimientoCreate no acepta fecha_hora ni stock_anterior/nuevo; POST histórico no preserva historia. Recepciones pueden disparar movimientos, riesgo/notificaciones. Exportación no equivale a replay por API.
12. OperarioCreate/Update repiten correo; Python conserva última declaración. ProductoUpdate valida menos que Create: generación siempre satisface Create y reglas de servicio.
13. Sin credenciales, EmpresaRegisterRequest y OperarioCreate no pueden recibir directamente sus CSV. Provisionar autenticación fuera de los datos; no guardar hashes/contraseñas como solución.

14. `movimiento_controller.py` restringe el POST público a **SALIDA por VENTA o VENCIMIENTO** y elimina id_detalle_recepcion del cliente. DTO/servicio permiten más motivos/tipos para operaciones internas. ENTRADA y AJUSTE del ledger no se pueden cargar mediante ese POST.

Estas diferencias se documentan, **no se corrigen ni modifican contratos en este trabajo**.
