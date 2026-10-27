# Resumen visual de inventario

Implementado en el backend; frontend pendiente. El acceso al workspace funciona mediante cmd.exe. PowerShell no devolvió salida en las comprobaciones de esta sesión; no se modificó su configuración.

## Consulta

POST /api/v1/saiki/ask (también /api/v1/saiki/chat), con Authorization: Bearer <JWT existente>:

```json
{"message":"Saiki, ¿cómo está mi inventario?","page":1,"page_size":25}
```

En /docs, autorizar con el JWT y ejecutar el endpoint Saiki. page debe ser >= 1; page_size entre 1 y 100. Parámetros inválidos devuelven 422. La empresa se obtiene exclusivamente del usuario autenticado; context.id_empresa no altera la consulta.

## Contrato

Se conservan answer, model, base_url, source, context, data, visualization, sources y warnings. Se mantiene data.get_warehouse_status para consumidores anteriores. Se añade data.inventory_summary:

- distinct_products: productos diferentes con stock positivo, no cantidad del catálogo.
- total_units: suma de stock de todas las ubicaciones autorizadas.
- warehouse_count: almacenes autorizados, incluidos los vacíos.
- catalog_products: cantidad de productos registrados en el catálogo de la empresa.
- inventory_state: sin_almacenes, almacen_sin_productos, productos_sin_inventario, stock_cero o stock_positivo.
- rows: una fila por producto/rack; varios registros en una ubicación se suman una sola vez y se conservan inventory_ids.
- pagination: page, page_size, total_rows y total_pages, calculados antes de recortar la página. Una página posterior al final devuelve rows vacío sin alterar indicadores.

Las filas contienen product_name, stock, warehouse_name, zone_name, rack_name, status_label e identificadores. Los nombres ausentes son null, no nombres inventados. Sin stock se deriva de stock=0; Bajo stock usa stock_actual <= stock_minimo registrado, como InventarioService.obtener_stock_bajo. Sin mínimo verificable, o con varios registros de una misma ubicación cuyos mínimos no tienen una regla agregada definida, se devuelve Sin determinar. No se ejecuta InventoryRisk ni se modifica su fórmula.

visualization.type=inventory_summary, version=1, title=Resumen de inventario. cards y table contienen los value_path/rows_path/pagination_path del contrato. El ejemplo JSON adjunto es exclusivamente sintético, no información obtenida de MongoDB real.

## Seguridad y consultas

saiki_inventory_summary.inventory_summary recorre Almacén -> Zona -> Rack -> Inventario con repositorios existentes y filtros por empresa/IDs autorizados. Filtra el catálogo en MongoDB por id_empresa y excluye referencias de inventario a productos de otra empresa. No hay estado mutable de solicitud ni llamadas Ollama.

El caso completo usa cinco consultas: almacenes de empresa, zonas de esos almacenes, racks de esas zonas, inventarios de esos racks y catálogo de empresa. No hay consulta por fila. Se conserva el filtro de almacén para operarios y se rechazan proveedores.

La paginación es del resultado en memoria: carga el inventario autorizado completo para calcular totales coherentes. Para empresas muy grandes queda pendiente medir y considerar agregación MongoDB con facet y paginación en base; no se afirma que esta implementación limite la memoria al tamaño de una página.

Un error MongoDB produce HTTP 503, no un resumen de ceros. Cantidades ausentes, negativas o inválidas también producen 503. Los estados vacíos solo se calculan tras completar las consultas pertinentes.

## Frontend pendiente

Implementar InventorySummary al recibir visualization.type=inventory_summary: encabezado, answer breve, tres tarjetas leyendo los value_path y tabla real de rows. Resolver null como Sin información. Cambiar de página enviando page/page_size al mismo endpoint; no recalcular tarjetas con las filas visibles. Mostrar los estados vacíos según inventory_state y diferenciar error HTTP de inventario vacío. Usar indicadores de carga, encabezados accesibles y diseño adaptable. No renderizar todo data.get_warehouse_status como una tabla Markdown.

No se modificaron frontend, .env, .venv, claves JWT, modelos ni datos reales. No hubo commit ni push. Las pruebas de esta entrega usan FastAPI/JWT/repositorios reales con una base simulada, sin crear bases temporales.
