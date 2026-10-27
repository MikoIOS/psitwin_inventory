# Reglas de generación del proyecto B

## Escala y reproducibilidad

1 empresa, 3 almacenes (Lima/Arequipa/Trujillo ficticios), 30 SKU compartidos, 3 proveedores de 10 SKU, 6 operarios (2/almacén), 6 zonas (seca/refrigerada por almacén), 30 racks (5 niveles/zona), 90 inventarios (un SKU por almacén y una ubicación por serie). 15 SKU secos y 15 refrigerados: 3 SKU compatibles por rack. No multiplicar el catálogo por almacén.

2020-01-01..2025-12-31 inclusivo: 2192 días, 197280 ventas y snapshots diarios. Calendario/planes de precio hasta 2026-01-07 (2199 fechas), sin ventas 2026. Seed=20261010. UUIDv5 namespace fijo `a1d188f7-265c-5ebc-894a-b65ea36c236f`; nombres de clave `entidad:clave_natural`, UTF-8, publicados en README; claves por entidad y subsemillas por módulo+serie derivadas SHA256, no hash() aleatorio de proceso. Orden estable, floats redondeados, configuración/dependencias versionadas; mismos parámetros producen bytes iguales. No incluir reloj real en artefactos deterministas.

Maestros creados antes de 2020, padres antes de hijos, inventario antes del saldo inicial. UTC tanto en ledger como agrupación. reference_date=2025-12-31; no atribuir al endpoint soporte automático de esa fecha.

## Demanda y ventas

Media propuesta mu=base_producto*factor_almacén*tendencia*semana*estacionalidad_anual*campaña*efecto_precio. Parámetros de generación nuevos, no defaults backend: base 5..40 unidades/día; factor almacén 0.8..1.2; tendencia anual -3%..8%; semana 0.8..1.2; amplitud anual 0.05..0.20; campañas sintéticas 1.10..1.35 según familia. Mu>=0, Poisson o binomial negativa con dispersión moderada registrada. Choques escasos (~1% días), factor 0.7..1.4. Heterogeneidad de escalas y algunos SKU intermitentes con ceros auténticos.

No generar targets desde predicciones, seleccionar seed por métricas ni recortar variaciones para garantizar WAPE. Campañas de Navidad/verano/invierno son simulaciones, no afirmaciones de feriados oficiales. Precios positivos mensuales, cambios graduales y promociones publicadas antes de vigencia; elasticidad en configuración interna, no DTO.

Demanda latente entera>=0 se calcula **antes** de consultar stock. Ventas=min(latente,disponible); perdidas=latente-ventas; stockout=perdidas>0. No vender unidades inexistentes ni registrar SALIDA cero. La latente es una verdad del simulador, no observación ni feature disponible al modelo.

## Ledger y reposición causal

Entradas aceptadas a 09:00 UTC, ventas agregadas 12:00, otras salidas opcionales 16:00. Evitar colisiones de timestamp por inventario; ordenar fecha_hora+ID. Saldo inicial separado; inventario.csv es cierre final, no apertura. Historial CREAR conserva apertura; snapshot.fecha_actualizacion=última modificación real al corte.

Peso kg por unidad alimenticia; volumen null porque unidad no está documentada. Capacidad inicial de diseño 5000 kg/rack; comprobar carga tras **cada evento**. Si diseño insuficiente, redimensionar antes de generación y justificar manifest, sin alterar capacidad para hacer pasar un evento inválido. Zona seca sin temperaturas; refrigerada y racks 2..6 °C, productos compatibles con ese rango. area_m2=1200/aforo=25 son atributos demo, no conversión a kg.

Reposición al cierre usando ventas pasadas (media móvil 28d y std poblacional; arranque con escala base publicada). Lead producto/proveedor coherente: 3 proveedores con 2/4/7 días. Seguridad=1.645*std*sqrt(lead), punto=media*lead+seguridad, posición=stock+pendientes. Si posición<=punto, solicitar max(0,ceil(media*(lead+7)+seguridad-posición)) sujeto a kg y máximo. No usar demanda latente, ventas futuras ni forecast previo para decidir.

Cada reposición efectiva genera orden MANUAL, línea, recepción CONFORME y ENTRADA/RECEPCION enlazada. Una línea y una recepción por orden en base; cantidades positivas. Órdenes pendientes al corte sin recepción futura; fechas estimadas pueden superar corte. Proveedor y operario ACTIVO del ámbito correspondiente. Despacho opcional: si null, fecha_despacho null; si existe, respetar LineaDespacho/DespachoRequest.

Límites fijos de diseño por serie: mínimo=ceil(base*factor*lead), máximo=ceil(base*factor*(lead+21)); registrar parámetros, sin recalibrar con TEST. Stock<=máximo como política demo. Movimientos AJUSTE opcionales usan valor absoluto; base no los necesita. Recomendaciones del backend no limitan siempre por kg/máximo: no garantizar que sugerencia futura quepa sin validación.

Base sin merma/vencimiento como SALIDA: consumo backend equivale a ventas. Si se habilitan otras salidas, separarlas en inventario_diario y advertir diferencia de objetivo en manifest. Mantener ledger interno de lotes perecederos para verificar que no se consumen después de vencer; vida útil/cantidades/reposición compatibles. El backend Inventario no tiene lotes: no afirmar FEFO implementado. Si no se puede evitar vencimiento real, registrar SALIDA/VENCIMIENTO y declarar cambio de perfil/objetivo, sin ocultarlo.

## Escenarios explicables

Seleccionar políticas antes de simular: al menos 5 series candidatas a reposición retrasada, 5 de cobertura alta y 2 intermitentes; resto normal/refrigerado. Clasificar **resultado real** al corte en NORMAL/BAJO_STOCK/SIN_STOCK/SOBRESTOCK/SIN_CONSUMO/REFRIGERADO. No exigir cuotas exactas de niveles IA ni alterar cierre para cumplir etiquetas. Retrasos posponen entregas con fecha estimada coherente; sobrantes siempre<=máximo y respetan vida útil. Explicación cita política y saldo/consumo observados, no una predicción ejecutada.

## Exportación y límites

Solo archivos DATA_FILES; no entrenamiento/inferencia masiva, API/Mongo writes ni correo. Snapshot+histórico se importan sin volver a aplicar movimientos, o se reconstruye apertura+replay y se verifica igualdad. Provisionar cuentas externamente; si se reutilizan IDs existentes, remapear todas referencias consistentemente.

Posterior demo viva podría usar perfil aparte desplazando todas las fechas (maestros, movimientos, vencimientos y conocido_en) por igual cantidad de días, conservando originales 2020–2025. No forma parte de base ni arregla M5/agregaciones. No simular ventas adicionales para rellenar reloj actual sin autorización y contrato actualizado.
