# Motor temporal, forecasting, logística y LLM de PsiTwin

Fecha de auditoría: 2026-10-13 (America/Lima). Inspección estática del workspace real. No se ejecutó el backend, no se importó app.main, no se abrió una conexión a MongoDB, no se entrenaron modelos, no se generaron registros ni datasets. Los JSON son ejemplos documentales ilustrativos. IMPLEMENTADO significa presencia y trazabilidad en código; no acredita ejecución exitosa ni datos desplegados. NO DEFINIDA significa ausencia de restricción declarada en ese contrato; NO VERIFICABLE significa falta de evidencia de ejecución o del despliegue. INFERIDO se reserva para cardinalidades y efectos deducidos. PARCIALMENTE IMPLEMENTADO distingue código existente con componentes faltantes. NO IMPLEMENTADO se limita al alcance inspeccionado.

## ESTADO ACTUAL DEL PROYECTO

El motor numérico existe: LightGBM de horizonte directo D+1..D+7. Hay 70 archivos de boosters: 7 globales y 63 locales. DemandPredictor utiliza únicamente los globales. El pipeline de entrenamiento y Vertex AI están NO IMPLEMENTADOS en el alcance. La ejecución del modelo y calidad en producción son NO VERIFICABLES en esta auditoría. Los metadatos de métricas de config no son una evaluación nueva.

### Series y tiempo

La identidad operativa es id_inventario; series_id está NO IMPLEMENTADO. Inventario referencia id_producto/id_rack, Rack id_zona, Zona id_almacen, Almacen id_empresa. No hay colección independiente de ventas, demanda ni predicciones. DemandHistory consulta movimientos SALIDA, suma cantidad por día UTC (incluye VENTA, MERMA, VENCIMIENTO, CONTEO_FISICO y OTRO permitidos). Objetivo A: demanda float en DataFrame fecha/demanda; unidades consumidas, no demanda latente ni venta exclusivamente. Evidencia: app/repositories/movimiento_repository.py:567 y app/ml/demand_history.py:94.

La agregación usa $match de rango inclusive, $group con $dateToString YYYY-MM-DD timezone UTC, $sum cantidad, $sort ascendente y $project. Movimientos se almacenan con fecha_hora BSON date. DemandHistory calendario freq=D: días ausentes -> 0.0. No hay bandera de observación ni distinción ausencia/cero. historial_completo sin SALIDA devuelve DataFrame vacío; historial fijo sin SALIDA devuelve calendario con ceros. Obtener_resumen marca historial_suficiente_ml con len>=367, aunque sean ceros rellenados.

FeatureBuilder normaliza fecha/demanda, demanda inválida -> 0, descarta fechas inválidas, ordena y conserva último duplicado por fecha; reindexa calendario continuo. UTC es la zona de agregación, no America/Lima. date() sobre datetime recibido no siempre convierte antes a UTC. Motor no solicita tz_aware explícito; consumo normaliza algunos datetimes naive a UTC. No índice temporal está declarado; índices reales NO VERIFICABLES.

### Ventanas y horizontes

DemandHistory default 400 días. Endpoints debug default dias=30, límites 1..500; predict-7-days default 30, límites 7..500. InventoryRiskService usa 30 días y horizonte7. Predicción individual horizon default1, 1..7. Saiki solo horizonte_dias=7; dias es ventana histórica 7..500, default30, no horizonte. No existen horizontes 30/90, intervalos de incertidumbre ni predicción recursiva. Predicciones son por inventario; agregados de producto/categoría/almacén alimentan features, no un endpoint de forecast agregado independiente.

Lags 1,2,3,4,5,6,7,14,21,28,35,42,56,364,365,366. Rolling mean3/7/14/28/56/180, std3/7/28/56 (ddof=0), max3/7/28. EWMA3/7/14/28 adjust=False. Future lags7/14/21/28/35/42/364/365/366 se desplazan lag-horizon: si0 current_y, si negativo NaN. current_y es última demanda del día base; age_days=len(historia)-1. Los helpers de ventanas, diferencias, tendencia, ceros y días desde venta están reproducidos en el anexo con fórmulas exactas. Ventana30 deja anuales y otras ventanas extensas sin datos.

### Variables y categorías A–F

A: demanda (objetivo), origen movimientos.cantidad SALIDA, diario; no se persiste como tabla de ventas. B: IDs M5 esperados sin mapeo disponible. C: calendario target_* realmente calculado; eventos/SNAP/precio futuro solo esperado y NaN. D: precios históricos/variables externas sin fuente actual. E: calendario base, lags, rolling, EWMA, cambios, tendencias y agregados operativos. F: no se encontró covariable logística simulada que el flujo actual entregue al booster; stock/lead son inputs del riesgo, no features del booster. No incluir promociones ni descuentos. Tampoco suponer feriados, sensores o eventos efectivos por existir un nombre en config.

| Variable exacta | Tipo | Categoría | Uso actual | Disponible futuro | Estado | Evidencia |
|---|---|---|---|---|---|---|
| item_id | pandas category (np.nan si ausente) | B. atributo estático esperado por artefacto | Sin mapeo/fuente en flujo actual; np.nan | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| dept_id | pandas category (np.nan si ausente) | B. atributo estático esperado por artefacto | Sin mapeo/fuente en flujo actual; np.nan | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| cat_id | pandas category (np.nan si ausente) | B. atributo estático esperado por artefacto | Sin mapeo/fuente en flujo actual; np.nan | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| store_id | pandas category (np.nan si ausente) | B. atributo estático esperado por artefacto | Sin mapeo/fuente en flujo actual; np.nan | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| state_id | pandas category (np.nan si ausente) | B. atributo estático esperado por artefacto | Sin mapeo/fuente en flujo actual; np.nan | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| month | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| year | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| dayofweek | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| day | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| weekofyear | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| is_weekend | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| has_event | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| quarter | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| dayofyear | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| is_month_start | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| is_month_end | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| snap | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| event_name_1 | pandas category (np.nan si ausente) | C. calendario de origen externo esperado | Sin mapeo/fuente en flujo actual; np.nan | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| event_type_1 | pandas category (np.nan si ausente) | C. calendario de origen externo esperado | Sin mapeo/fuente en flujo actual; np.nan | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| event_name_2 | pandas category (np.nan si ausente) | C. calendario de origen externo esperado | Sin mapeo/fuente en flujo actual; np.nan | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| event_type_2 | pandas category (np.nan si ausente) | C. calendario de origen externo esperado | Sin mapeo/fuente en flujo actual; np.nan | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| age_days | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| current_y | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_1 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_2 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_3 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_4 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_5 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_6 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_14 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_21 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_35 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_42 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_56 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_364 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_365 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| lag_366 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_mean_3 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_mean_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_mean_14 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_mean_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_mean_56 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_mean_180 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_std_3 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_std_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_std_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_std_56 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_max_3 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_max_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_max_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| ewma_3 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| ewma_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| ewma_14 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| ewma_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| zero_ratio_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| zero_ratio_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| change_1_2 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| change_1_3 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| change_1_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| ratio_mean3_mean14 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| ratio_mean7_mean28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| acceleration_3_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| acceleration_7_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| max7_vs_mean28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| max3_vs_mean28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| previous_7_mean | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| recent7_vs_previous7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| dow_mean_4w | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| growth_streak_3 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| peak_count_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_inc_mean_3 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_inc_mean_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_inc_mean_14 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_inc_mean_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_inc_std_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| rolling_inc_std_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| days_since_sale | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| sale_rate_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| current_vs_mean7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| current_vs_mean28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| sell_price | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_available | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_lag_1 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_lag_7 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_change_1 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_change_7 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_mean_28 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_relative_28 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_mean_180 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_std_180 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_min_180 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_max_180 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_relative_180 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_to_max_180 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| price_range_position_180 | float/int -> pandas numérico, admite NaN | D. dato externo histórico esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| store_sales_lag_1 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| store_sales_lag_7 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| store_sales_lag_28 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| store_sales_mean_7 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| store_sales_mean_28 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| dept_sales_lag_1 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| dept_sales_lag_7 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| dept_sales_lag_28 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| dept_sales_mean_7 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| dept_sales_mean_28 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| item_total_lag_1 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| item_total_lag_7 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| item_total_lag_28 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| target_month | float/int -> pandas numérico, admite NaN | C. calendario conocido a futuro | Derivado fecha_base + horizon por _target_calendar_features | sí, calendario determinista | IMPLEMENTADO | app/ml/feature_builder.py:773 |
| target_dayofweek | float/int -> pandas numérico, admite NaN | C. calendario conocido a futuro | Derivado fecha_base + horizon por _target_calendar_features | sí, calendario determinista | IMPLEMENTADO | app/ml/feature_builder.py:773 |
| target_day | float/int -> pandas numérico, admite NaN | C. calendario conocido a futuro | Derivado fecha_base + horizon por _target_calendar_features | sí, calendario determinista | IMPLEMENTADO | app/ml/feature_builder.py:773 |
| target_weekofyear | float/int -> pandas numérico, admite NaN | C. calendario conocido a futuro | Derivado fecha_base + horizon por _target_calendar_features | sí, calendario determinista | IMPLEMENTADO | app/ml/feature_builder.py:773 |
| target_is_weekend | float/int -> pandas numérico, admite NaN | C. calendario conocido a futuro | Derivado fecha_base + horizon por _target_calendar_features | sí, calendario determinista | IMPLEMENTADO | app/ml/feature_builder.py:773 |
| target_quarter | float/int -> pandas numérico, admite NaN | C. calendario conocido a futuro | Derivado fecha_base + horizon por _target_calendar_features | sí, calendario determinista | IMPLEMENTADO | app/ml/feature_builder.py:773 |
| target_dayofyear | float/int -> pandas numérico, admite NaN | C. calendario conocido a futuro | Derivado fecha_base + horizon por _target_calendar_features | sí, calendario determinista | IMPLEMENTADO | app/ml/feature_builder.py:773 |
| future_sell_price | float/int -> pandas numérico, admite NaN | C. dato futuro esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| future_price_available | float/int -> pandas numérico, admite NaN | C. dato futuro esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| future_snap | float/int -> pandas numérico, admite NaN | C. dato futuro esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| future_has_event | float/int -> pandas numérico, admite NaN | C. dato futuro esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| future_event_name_1_code | float/int -> pandas numérico, admite NaN | C. dato futuro esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| future_event_type_1_code | float/int -> pandas numérico, admite NaN | C. dato futuro esperado (no abastecido) | pending_features -> np.nan salvo context explícito; endpoints no aportan esta fuente | NO VERIFICABLE | PARCIALMENTE IMPLEMENTADO | app/ml/feature_builder.py:1401 |
| future_lag_7 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_lag_14 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_lag_21 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_lag_28 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_lag_35 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_lag_42 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_lag_364 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_lag_365 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_lag_366 | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_dow_mean_6w | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_dow_std_6w | float/int -> pandas numérico, admite NaN | E. histórico derivado | FeatureBuilder.build_demand_features; fórmula en anexo | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_store_lag_7 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |
| future_dept_lag_7 | float/int -> pandas numérico, admite NaN | E. agregado histórico derivado | MLContextBuilder: suma SALIDA por IDs de producto; contexto operacional | histórica al corte | IMPLEMENTADO | app/ml/feature_builder.py:813 |

### Motor y compatibilidad de artefactos

ModelLoader lee config_v3_6.json, selection_by_horizon.csv y lgb.Booster(model_file). validate_paths y métodos horizon exigen 1..7; carga todos globales y cachea por horizonte. Local loader existe, pero predict_horizon no lo invoca. El header contiene version=v4, max_feature_idx=135, objective=regression_l1 y 136 feature_names; version del formato no es versión del paquete.

Features se ordenan según config.features, categorías astype(category), resto pd.to_numeric(errors=coerce), +/-Inf a NaN. validate_features/missing_features solo exigen claves, no valores observados. Sin context, pending_features=np.nan. MLContextBuilder entrega13 agregados históricos +2 desplazados por horizonte: store_sales_lag_1/7/28 y mean7/28; dept_sales_lag_1/7/28 y mean7/28; item_total_lag_1/7/28; future_store_lag_7/future_dept_lag_7 con effective_lag=7-horizon. ContextBuilder MAX_LAG28 genera29 fechas; medias anteriores excluyen día base.

El grupo store se forma mediante ProductoRepository.obtener_por_almacen (producto.id_rack de referencia). Las salidas por lista id_producto no filtran ubicación física: para producto multialmacén puede haber contaminación entre almacenes. Categoria global se calcula para identificación pero usado_para_dept_sales=False; dept usa categoría dentro del listado del almacén. No existe traducción UUID->item_id/dept_id/cat_id/store_id/state_id.

La config describe ensemble scale1.15/alpha/beta y métricas, pero predictor ejecuta modelo global raw y recorta negativo a0. No aplica esas correcciones ni selección local/global. Las categorías entrenadas M5 y los nuevos UUID no son automáticamente equivalentes.

### Integración logística real

- **consumo_diario**: max(primer promedio positivo entre 7d/14d/28d, forecast.demanda_7d/7)
- **cobertura**: stock_actual/consumo_diario, round(2); None si consumo<=0
- **stock_seguridad**: round(1.645*pstdev(consumos_diarios_28d)*sqrt(lead_time_dias),2) si lead y desviación positivos; si no 0
- **punto_reposicion**: round(consumo_diario*lead_time_dias+stock_seguridad,2)
- **reposicion**: ceil(max(0,consumo_diario*max(lead_time_dias+7,7)+stock_seguridad-stock_actual)); mínima ceil(recomendada*.85), segura ceil(recomendada*1.15)
- **fecha_quiebre**: primera fecha cuyo acumulado de demanda predicha >= stock_actual; stock<=0 -> fecha_base; None si no quiebra en 7 días
- **risk**: CRITICO stock<=0 o cobertura<=lead positivo; ALTO stock<=punto positivo; MEDIO cobertura<=1.5*lead; BAJO resto/consumo ausente con stock positivo
- **score**: stock<=0:100. Cobertura/lead <=1:+60, <=1.5:+40, <=2:+20. Stock/punto <=.5:+40, <=1:+30, <=1.25:+15. min(total,100), round(2)
- **effects**: generar_alertas=True crea/actualiza alerta RIESGO_STOCKOUT y recomendación REABASTECER en ALTO/CRITICO; otro riesgo resuelve alerta activa. No descuenta stock ni compra automáticamente.
- **decision_flow**: PENDIENTE -> VALIDADA_OPERARIO -> APROBADA_EMPRESA -> APLICADA; se crea OrdenReposicion y detalle, requiere proveedor y costo. Orden -> validar ENVIADA -> recepción -> ENTRADA actualiza stock.
- **bounds**: Cantidad sugerida no limita stock_maximo ni capacidad kg dentro de _calcular_reposicion; esos límites se controlan parcialmente al ingresar/ubicar stock.

Evaluar_todos generar_alertas=False; evaluar individual defaultTrue. GET /inventory-risk/{id_inventario} puede escribir alertas/recomendaciones; no se invocó. Saiki get_inventory_risk pasa False. ALTO/CRITICO producen RIESGO_STOCKOUT y REABASTECER; otros riesgos resuelven alerta activa. No todas las enumeraciones TipoAlerta/TipoRecomendacion tienen un detector automático. Enumerar PROXIMO_VENCIMIENTO no demuestra escaneo automático de vencimientos. No hay reposición ni movimiento decidido automáticamente por LLM.

### Integración LLM Saiki

IMPLEMENTADO Ollama local configurable, default http://localhost:11434 y qwen3:4b. Health GET /api/tags valida disponibilidad/modelo; POST /api/chat manda model/messages/tools/stream=false/think=false. Mensajes system (prompt del repo), history frontend user/assistant, user con message/context y luego resultados tool serializados default=str. Cliente context no da autorización. Ocho tools: get_inventory, get_product, get_forecast, get_inventory_risk, get_active_alerts, get_recommendations, get_recent_movements, get_warehouse_status. Pydantic valida argumentos; tool inválida/restringida ->400; autoriza IDs y filtra visibilidad. ForecastArgs extra=forbid, horizonte_dias=7 estricto.

Loop máximo4 iteraciones, deduplica nombre+argumentos por llamada. HTTP generativo en asyncio.to_thread. Timeout conexión5s/lectura180s. Errors MongoDB/Ollama indisponible503, timeout504, inesperado500. Limpia etiquetas think. Respuesta answer/model/base_url/source/context/warnings/data/visualization/sources. Datos estructurados provienen del backend; texto generativo no es validado como cálculo numérico, solo su forma. Prompt limita inventar cifras, compras y acceso directo a MongoDB; restricciones de tools sí están en código. Fast paths contestan sin LLM; por ello source puede ser backend/router/ollama según ruta. No persistencia de chat independiente.

### Contratos entre componentes

| Origen | Destino | Contrato exacto | Resultado | Estado |
|---|---|---|---|---|
| Mongo movimientos | DemandHistory | id_inventario, fecha_inicio, fecha_fin; SALIDA | fecha, cantidad, numero_movimientos -> fecha/demanda | IMPLEMENTADO |
| DemandHistory | FeatureBuilder | DataFrame fecha/demanda, horizon, context | dict136 columnas | IMPLEMENTADO con NaN |
| MLContextBuilder | FeatureBuilder | id_inventario, fecha_base, horizon |13 agregados +2 future | IMPLEMENTADO con limitación espacial |
| FeatureBuilder | DemandPredictor | features, horizon | float max(0,predict[0]) | IMPLEMENTADO |
| Forecast | Cliente | id_inventario,dias query | fechas YYYY-MM-DD, demanda_total_7d, demanda_promedio_diaria,predicciones_diarias | IMPLEMENTADO |
| Predictor | InventoryRisk | demanda_7d y predicciones_diarias fecha/demanda_predicha | consumo/cobertura/seguridad/riesgo/reposicion | IMPLEMENTADO |
| InventoryRisk | Alerta/Recomendacion | IDs, nivel, stock, forecast_7d, cantidades | documentos activos/pendientes | IMPLEMENTADO si generar_alertas |
| Recomendacion | OrdenReposicion | proveedor,costo,fecha, cantidad_recomendada | orden+detalle, estadoAPLICADA | IMPLEMENTADO multietapa |
| Saiki | Ollama | POST /api/chat model,messages,tools,stream,think | message.content o message.tool_calls | IMPLEMENTADO |
| Ollama | Registry | function.name, arguments dict o JSON string | tool result + source | IMPLEMENTADO |
| Dataset M5/precios/calendario | Backend | no consumidor/importador | ninguno | NO IMPLEMENTADO |

Ejemplo de solicitud sin body: GET /api/v1/forecast/predict-7-days/66666666-6666-4666-8666-666666666666?dias=400, Bearer EMPRESA propietaria. Respuesta exacta con todos los campos y firmas está en anexo ForecastController; los valores de inferencia no se inventan aquí. Ejemplo Saiki:

```json
{"message":"Predice la demanda de los próximos siete días","id_inventario":"66666666-6666-4666-8666-666666666666"}
```

### Fuentes externas

config.dataset apunta a /kaggle/input/datasets/omniscientreader2025/data-procesada-gemini/psitwin_m5_base_v2.pkl. Es metadata de origen del artefacto; el archivo PKL/notebook/CSV de M5 no está en el workspace. No hay reader/importador externo hacia colecciones. Los 70 boosters y selection CSV sí son artefactos locales. dataset_contract es propuesta/documentación previa; los CSV planificados de ventas, snapshots, series_mapping, precio/calendario no existen como entidades operativas/API. Promociones mencionadas en esa documentación están EXCLUIDAS del forecasting de PsiTwin; no se detectó predictor promotion/discount en artefactos.

## REQUISITOS O RECOMENDACIONES FUTURAS

1. Definir continuidad y corte de observación explícitos; no confundir ceros rellenados con historia observada.
2. Si se usa exclusivamente venta, distinguir SALIDA/VENTA del consumo operativo actual.
3. Definir un mapeo de categorías válido para los boosters existentes o un proceso posterior separado de adaptación; no crearlo ahora.
4. No incluir promociones ni descuentos; no suponer feriados, SNAP, precios futuros ni sensores disponibles.

Para compatibilidad actual, construir historia desde movimientos referenciados a inventario y documentos maestros válidos. Conservar fechas BSON, UTC y corte, nombres exactos, continuidad comprobable, saldos y stock no negativo. El backend actual no ingiere ventas_diarias ni covariables por contrato público. Si otra IA prepara datos para uso posterior debe separar esos artefactos externos de los documentos insertables actuales. No se implementó nada de esta sección.

## Evidencia autosuficiente del pipeline y LLM

Los números antes de dos puntos son líneas del archivo original; extractos no se ejecutan.

### app/controllers/forecast_controller.py

```python
3: from fastapi import (
4:     APIRouter,
5:     HTTPException,
6:     Query
7: )
9: import pandas as pd
11: from app.ml.demand_history import (
12:     DemandHistory
13: )
15: from app.ml.model_loader import (
16:     ModelLoader
17: )
19: from app.ml.feature_builder import (
20:     FeatureBuilder
21: )
23: from app.ml.predictor import (
24:     DemandPredictor
25: )
27: from app.ml.ml_context_builder import (
28:     MLContextBuilder
29: )
32: router = APIRouter(
33:     prefix="/forecast",
34:     tags=["Forecast"]
35: )
42: model_loader = ModelLoader()
44: feature_builder = FeatureBuilder(
45:     loader=model_loader
46: )
53: def _json_safe_value(
54:     value
55: ):
57:     try:
59:         if pd.isna(value):
60:             return None
62:     except (
63:         TypeError,
64:         ValueError
65:     ):
67:         pass
69:     if hasattr(
70:         value,
71:         "item"
72:     ):
74:         try:
75:             return value.item()
77:         except Exception:
78:             pass
80:     return value
83: def _features_to_json(
84:     features: dict
85: ) -> dict:
87:     return {
89:         key:
90:             _json_safe_value(
91:                 value
92:             )
94:         for key, value
95:         in features.items()
96:     }
103: def _contar_features(
104:     features: dict
105: ) -> dict:
107:     features_json = (
108:         _features_to_json(
109:             features
110:         )
111:     )
113:     disponibles = sum(
115:         1
117:         for value
118:         in features_json.values()
120:         if value is not None
121:     )
123:     sin_datos = sum(
125:         1
127:         for value
128:         in features_json.values()
130:         if value is None
131:     )
133:     return {
135:         "disponibles":
136:             disponibles,
138:         "sin_datos":
139:             sin_datos
140:     }
147: def _crear_history_dataframe(
148:     historial: list
149: ) -> pd.DataFrame:
151:     if not historial:
153:         raise ValueError(
154:             "No existe historial de demanda "
155:             "para el inventario indicado."
156:         )
158:     history_df = pd.DataFrame(
159:         historial
160:     )
162:     if history_df.empty:
164:         raise ValueError(
165:             "El historial de demanda está vacío."
166:         )
168:     required_columns = {
169:         "fecha",
170:         "demanda"
171:     }
173:     missing_columns = (
175:         required_columns
177:         - set(
178:             history_df.columns
179:         )
180:     )
182:     if missing_columns:
184:         raise ValueError(
185:             "DemandHistory no devolvió "
186:             "las columnas necesarias: "
187:             + ", ".join(
188:                 sorted(
189:                     missing_columns
190:                 )
191:             )
192:         )
194:     history_df[
195:         "fecha"
196:     ] = pd.to_datetime(
197:         history_df[
198:             "fecha"
199:         ]
200:     )
202:     return history_df
209: def _obtener_fecha_base(
210:     history_df: pd.DataFrame
211: ) -> pd.Timestamp:
213:     fecha_base = (
214:         pd.to_datetime(
215:             history_df[
216:                 "fecha"
217:             ]
218:         )
219:         .max()
220:     )
222:     if pd.isna(
223:         fecha_base
224:     ):
226:         raise ValueError(
227:             "No se pudo determinar "
228:             "la fecha base."
229:         )
231:     return fecha_base
238: @router.get(
239:     "/debug-history/{id_inventario}",
240:     summary="Probar historial diario de demanda"
241: )
242: async def debug_history(
244:     id_inventario: str,
246:     dias: int = Query(
247:         default=30,
248:         ge=1,
249:         le=500
250:     )
252: ):
254:     try:
256:         demand_history = (
257:             DemandHistory()
258:         )
260:         historial = await (
261:             demand_history
262:             .obtener_ultimos_dias(
264:                 id_inventario=
265:                     id_inventario,
267:                 dias=
268:                     dias
269:             )
270:         )
272:         resumen = await (
273:             demand_history
274:             .obtener_resumen(
276:                 id_inventario=
277:                     id_inventario,
279:                 dias=
280:                     dias
281:             )
282:         )
284:         return {
286:             "mensaje":
287:                 "Historial de demanda generado correctamente",
289:             "resumen":
290:                 resumen,
292:             "historial":
293:                 historial
294:         }
296:     except ValueError as exc:
298:         raise HTTPException(
299:             status_code=404,
300:             detail=str(exc)
301:         )
303:     except Exception as exc:
305:         raise HTTPException(
306:             status_code=500,
307:             detail=(
308:                 "Error generando historial "
309:                 f"de demanda: {str(exc)}"
310:             )
311:         )
318: @router.get(
319:     "/debug-context/{id_inventario}",
320:     summary="Probar contexto operacional para ML"
321: )
322: async def debug_context(
324:     id_inventario: str
326: ):
328:     try:
330:         demand_history = (
331:             DemandHistory()
332:         )
334:         historial = await (
335:             demand_history
336:             .obtener_ultimos_dias(
338:                 id_inventario=
339:                     id_inventario,
341:                 dias=
342:                     30
343:             )
344:         )
346:         history_df = (
347:             _crear_history_dataframe(
348:                 historial
349:             )
350:         )
352:         fecha_base = (
353:             _obtener_fecha_base(
354:                 history_df
355:             )
356:         )
358:         context_builder = (
359:             MLContextBuilder()
360:         )
362:         resultado = await (
363:             context_builder.build(
365:                 id_inventario=
366:                     id_inventario,
368:                 fecha_base=
369:                     fecha_base.to_pydatetime()
370:             )
371:         )
373:         return {
375:             "mensaje":
376:                 "Contexto ML generado correctamente",
378:             "id_inventario":
379:                 id_inventario,
381:             "fecha_base_forecast":
382:                 fecha_base.strftime(
383:                     "%Y-%m-%d"
384:                 ),
386:             **resultado
387:         }
389:     except ValueError as exc:
391:         raise HTTPException(
392:             status_code=404,
393:             detail=str(exc)
394:         )
396:     except Exception as exc:
398:         raise HTTPException(
399:             status_code=500,
400:             detail=(
401:                 "Error construyendo contexto "
402:                 f"ML: {str(exc)}"
403:             )
404:         )
411: @router.get(
412:     "/debug-features/{id_inventario}",
413:     summary="Probar construcción de features ML"
414: )
415: async def debug_features(
417:     id_inventario: str,
419:     dias: int = Query(
420:         default=30,
421:         ge=1,
422:         le=500
423:     ),
425:     horizon: int = Query(
426:         default=1,
427:         ge=1,
428:         le=7
429:     )
431: ):
433:     try:
439:         demand_history = (
440:             DemandHistory()
441:         )
443:         historial = await (
444:             demand_history
445:             .obtener_ultimos_dias(
447:                 id_inventario=
448:                     id_inventario,
450:                 dias=
451:                     dias
452:             )
453:         )
455:         history_df = (
456:             _crear_history_dataframe(
457:                 historial
458:             )
459:         )
461:         fecha_base = (
462:             _obtener_fecha_base(
463:                 history_df
464:             )
465:         )
467:         fecha_objetivo = (
469:             fecha_base
471:             + pd.Timedelta(
472:                 days=horizon
473:             )
474:         )
481:         context_builder = (
482:             MLContextBuilder()
483:         )
485:         context = await (
486:             context_builder
487:             .build_feature_context(
489:                 id_inventario=
490:                     id_inventario,
492:                 fecha_base=
493:                     fecha_base.to_pydatetime(),
495:                 horizon=
496:                     horizon
497:             )
498:         )
505:         features = (
506:             feature_builder
507:             .build_demand_features(
509:                 history=
510:                     history_df,
512:                 horizon=
513:                     horizon,
515:                 context=
516:                     context
517:             )
518:         )
520:         missing_features = (
521:             feature_builder
522:             .missing_features(
523:                 features
524:             )
525:         )
527:         features_modelo = {
529:             feature:
530:                 features.get(
531:                     feature
532:                 )
534:             for feature
535:             in feature_builder.features
536:         }
538:         conteo = (
539:             _contar_features(
540:                 features_modelo
541:             )
542:         )
544:         return {
546:             "mensaje":
547:                 "Features generadas correctamente",
549:             "id_inventario":
550:                 id_inventario,
552:             "configuracion": {
554:                 "dias_historial":
555:                     dias,
557:                 "horizon":
558:                     horizon,
560:                 "fecha_base":
561:                     fecha_base.strftime(
562:                         "%Y-%m-%d"
563:                     ),
565:                 "fecha_objetivo":
566:                     fecha_objetivo.strftime(
567:                         "%Y-%m-%d"
568:                     ),
570:                 "future_effective_lag":
571:                     7 - horizon
572:             },
574:             "contexto_ml": {
576:                 "cantidad":
577:                     len(
578:                         context
579:                     ),
581:                 "features":
582:                     _features_to_json(
583:                         context
584:                     )
585:             },
587:             "resumen": {
589:                 "features_modelo":
590:                     len(
591:                         feature_builder.features
592:                     ),
594:                 "features_disponibles":
595:                     conteo[
596:                         "disponibles"
597:                     ],
599:                 "features_sin_datos":
600:                     conteo[
601:                         "sin_datos"
602:                     ],
604:                 "features_faltantes":
605:                     len(
606:                         missing_features
607:                     )
608:             },
610:             "missing_features":
611:                 missing_features,
613:             "features":
614:                 _features_to_json(
615:                     features_modelo
616:                 )
617:         }
619:     except ValueError as exc:
621:         raise HTTPException(
622:             status_code=400,
623:             detail=str(exc)
624:         )
626:     except Exception as exc:
628:         raise HTTPException(
629:             status_code=500,
630:             detail=(
631:                 "Error construyendo features "
632:                 f"ML: {str(exc)}"
633:             )
634:         )
641: @router.get(
642:     "/debug-predict/{id_inventario}",
643:     summary="Probar predicción LightGBM D+N"
644: )
645: async def debug_predict(
647:     id_inventario: str,
649:     dias: int = Query(
650:         default=30,
651:         ge=1,
652:         le=500
653:     ),
655:     horizon: int = Query(
656:         default=1,
657:         ge=1,
658:         le=7
659:     )
661: ):
663:     try:
665:         demand_history = (
666:             DemandHistory()
667:         )
669:         historial = await (
670:             demand_history
671:             .obtener_ultimos_dias(
673:                 id_inventario=
674:                     id_inventario,
676:                 dias=
677:                     dias
678:             )
679:         )
681:         history_df = (
682:             _crear_history_dataframe(
683:                 historial
684:             )
685:         )
687:         fecha_base = (
688:             _obtener_fecha_base(
689:                 history_df
690:             )
691:         )
693:         fecha_objetivo = (
695:             fecha_base
697:             + pd.Timedelta(
698:                 days=horizon
699:             )
700:         )
707:         context_builder = (
708:             MLContextBuilder()
709:         )
711:         context = await (
712:             context_builder
713:             .build_feature_context(
715:                 id_inventario=
716:                     id_inventario,
718:                 fecha_base=
719:                     fecha_base.to_pydatetime(),
721:                 horizon=
722:                     horizon
723:             )
724:         )
731:         features = (
732:             feature_builder
733:             .build_demand_features(
735:                 history=
736:                     history_df,
738:                 horizon=
739:                     horizon,
741:                 context=
742:                     context
743:             )
744:         )
746:         missing_features = (
747:             feature_builder
748:             .missing_features(
749:                 features
750:             )
751:         )
753:         if missing_features:
755:             raise ValueError(
756:                 "Faltan features requeridas "
757:                 "por LightGBM: "
758:                 + ", ".join(
759:                     missing_features
760:                 )
761:             )
763:         features_modelo = {
765:             feature:
766:                 features.get(
767:                     feature
768:                 )
770:             for feature
771:             in feature_builder.features
772:         }
774:         conteo = (
775:             _contar_features(
776:                 features_modelo
777:             )
778:         )
785:         predictor = (
786:             DemandPredictor(
787:                 loader=model_loader
788:             )
789:         )
791:         demanda_predicha = (
792:             predictor.predict_horizon(
794:                 features=
795:                     features,
797:                 horizon=
798:                     horizon
799:             )
800:         )
802:         return {
804:             "mensaje":
805:                 "Predicción generada correctamente",
807:             "id_inventario":
808:                 id_inventario,
810:             "modelo":
811:                 "LightGBM Global",
813:             "horizon":
814:                 horizon,
816:             "future_effective_lag":
817:                 7 - horizon,
819:             "fecha_base":
820:                 fecha_base.strftime(
821:                     "%Y-%m-%d"
822:                 ),
824:             "fecha_objetivo":
825:                 fecha_objetivo.strftime(
826:                     "%Y-%m-%d"
827:                 ),
829:             "dias_historial":
830:                 dias,
832:             "contexto_ml": {
834:                 "cantidad":
835:                     len(
836:                         context
837:                     ),
839:                 "features":
840:                     _features_to_json(
841:                         context
842:                     )
843:             },
845:             "features": {
847:                 "total":
848:                     len(
849:                         feature_builder.features
850:                     ),
852:                 "disponibles":
853:                     conteo[
854:                         "disponibles"
855:                     ],
857:                 "sin_datos":
858:                     conteo[
859:                         "sin_datos"
860:                     ],
862:                 "faltantes":
863:                     len(
864:                         missing_features
865:                     )
866:             },
868:             "demanda_predicha":
869:                 round(
870:                     float(
871:                         demanda_predicha
872:                     ),
873:                     4
874:                 )
875:         }
877:     except ValueError as exc:
879:         raise HTTPException(
880:             status_code=400,
881:             detail=str(exc)
882:         )
884:     except Exception as exc:
886:         raise HTTPException(
887:             status_code=500,
888:             detail=(
889:                 "Error realizando predicción "
890:                 f"ML: {str(exc)}"
891:             )
892:         )
899: @router.get(
900:     "/predict-7-days/{id_inventario}",
901:     summary="Generar forecast de demanda de 7 días"
902: )
903: async def predict_7_days(
905:     id_inventario: str,
907:     dias: int = Query(
908:         default=30,
909:         ge=7,
910:         le=500
911:     )
913: ):
915:     try:
921:         demand_history = (
922:             DemandHistory()
923:         )
925:         historial = await (
926:             demand_history
927:             .obtener_ultimos_dias(
929:                 id_inventario=
930:                     id_inventario,
932:                 dias=
933:                     dias
934:             )
935:         )
937:         history_df = (
938:             _crear_history_dataframe(
939:                 historial
940:             )
941:         )
943:         fecha_base = (
944:             _obtener_fecha_base(
945:                 history_df
946:             )
947:         )
964:         context_builder = (
965:             MLContextBuilder()
966:         )
968:         contexts_by_horizon = await (
969:             context_builder
970:             .build_feature_contexts_7_days(
972:                 id_inventario=
973:                     id_inventario,
975:                 fecha_base=
976:                     fecha_base.to_pydatetime()
977:             )
978:         )
985:         features_by_horizon = {}
987:         features_por_horizonte = {}
989:         contexto_por_horizonte = {}
991:         for horizon in range(
992:             1,
993:             8
994:         ):
996:             context = (
997:                 contexts_by_horizon[
998:                     horizon
999:                 ]
1000:             )
1002:             features = (
1003:                 feature_builder
1004:                 .build_demand_features(
1006:                     history=
1007:                         history_df,
1009:                     horizon=
1010:                         horizon,
1012:                     context=
1013:                         context
1014:                 )
1015:             )
1017:             missing_features = (
1018:                 feature_builder
1019:                 .missing_features(
1020:                     features
1021:                 )
1022:             )
1024:             if missing_features:
1026:                 raise ValueError(
1027:                     f"D+{horizon}: faltan "
1028:                     "features requeridas por "
1029:                     "LightGBM: "
1030:                     + ", ".join(
1031:                         missing_features
1032:                     )
1033:                 )
1035:             features_by_horizon[
1036:                 horizon
1037:             ] = features
1039:             features_modelo = {
1041:                 feature:
1042:                     features.get(
1043:                         feature
1044:                     )
1046:                 for feature
1047:                 in feature_builder.features
1048:             }
1050:             conteo = (
1051:                 _contar_features(
1052:                     features_modelo
1053:                 )
1054:             )
1056:             features_por_horizonte[
1057:                 f"D+{horizon}"
1058:             ] = {
1060:                 "disponibles":
1061:                     conteo[
1062:                         "disponibles"
1063:                     ],
1065:                 "sin_datos":
1066:                     conteo[
1067:                         "sin_datos"
1068:                     ]
1069:             }
1071:             contexto_por_horizonte[
1072:                 f"D+{horizon}"
1073:             ] = {
1075:                 "effective_lag":
1076:                     7 - horizon,
1078:                 "future_store_lag_7":
1079:                     context.get(
1080:                         "future_store_lag_7"
1081:                     ),
1083:                 "future_dept_lag_7":
1084:                     context.get(
1085:                         "future_dept_lag_7"
1086:                     )
1087:             }
1094:         predictor = (
1095:             DemandPredictor(
1096:                 loader=model_loader
1097:             )
1098:         )
1100:         forecast = (
1101:             predictor.predict_7_days(
1103:                 features_by_horizon=
1104:                     features_by_horizon,
1106:                 start_date=
1107:                     fecha_base.date()
1108:             )
1109:         )
1116:         demanda_total_7d = float(
1117:             forecast[
1118:                 "demanda_7d"
1119:             ]
1120:         )
1122:         demanda_promedio_diaria = (
1124:             demanda_total_7d
1126:             / 7.0
1127:         )
1129:         fecha_desde = (
1131:             fecha_base
1133:             + pd.Timedelta(
1134:                 days=1
1135:             )
1136:         )
1138:         fecha_hasta = (
1140:             fecha_base
1142:             + pd.Timedelta(
1143:                 days=7
1144:             )
1145:         )
1152:         return {
1154:             "mensaje":
1155:                 "Forecast de 7 días generado correctamente",
1157:             "id_inventario":
1158:                 id_inventario,
1160:             "modelo":
1161:                 "LightGBM Direct Horizon",
1163:             "modo_modelo":
1164:                 "global",
1166:             "dias_historial":
1167:                 dias,
1169:             "fecha_base":
1170:                 fecha_base.strftime(
1171:                     "%Y-%m-%d"
1172:                 ),
1174:             "periodo_forecast": {
1176:                 "desde":
1177:                     fecha_desde.strftime(
1178:                         "%Y-%m-%d"
1179:                     ),
1181:                 "hasta":
1182:                     fecha_hasta.strftime(
1183:                         "%Y-%m-%d"
1184:                     )
1185:             },
1187:             "contexto_ml": {
1189:                 "cantidad_features_por_horizonte":
1190:                     15,
1192:                 "future_features":
1193:                     contexto_por_horizonte
1194:             },
1196:             "features_por_horizonte":
1197:                 features_por_horizonte,
1199:             "demanda_total_7d":
1200:                 round(
1201:                     demanda_total_7d,
1202:                     4
1203:                 ),
1205:             "demanda_promedio_diaria":
1206:                 round(
1207:                     demanda_promedio_diaria,
1208:                     4
1209:                 ),
1211:             "predicciones_diarias":
1212:                 forecast[
1213:                     "predicciones_diarias"
1214:                 ]
1215:         }
1217:     except ValueError as exc:
1219:         raise HTTPException(
1220:             status_code=400,
1221:             detail=str(exc)
1222:         )
1224:     except Exception as exc:
1226:         raise HTTPException(
1227:             status_code=500,
1228:             detail=(
1229:                 "Error generando forecast "
1230:                 f"de 7 días: {str(exc)}"
1231:             )
1232:         )
1239: @router.get(
1240:     "/debug-feature-info",
1241:     summary="Ver configuración de features ML"
1242: )
1243: async def debug_feature_info():
1245:     try:
1247:         return (
1248:             feature_builder.info()
1249:         )
1251:     except Exception as exc:
1253:         raise HTTPException(
1254:             status_code=500,
1255:             detail=(
1256:                 "Error obteniendo información "
1257:                 f"del FeatureBuilder: {str(exc)}"
1258:             )
1259:         )
```

### app/controllers/inventory_risk_controller.py

```python
1: from typing import List
3: from fastapi import (
4:     APIRouter,
5:     Depends,
6:     Query
7: )
9: from app.dependencies.dependencies import (
10:     require_empresa
11: )
13: from app.dto.auth_dto import (
14:     UsuarioActual
15: )
17: from app.dto.inventory_risk_dto import (
18:     InventoryRiskResponse
19: )
21: from app.services.acceso_service import (
22:     AccesoService
23: )
25: from app.services.inventory_risk_service import (
26:     InventoryRiskService
27: )
34: router = APIRouter(
35:     prefix="/inventory-risk",
36:     tags=["Inventory Intelligence"]
37: )
39: service = InventoryRiskService()
42: @router.get(
43:     "",
44:     response_model=List[
45:         InventoryRiskResponse
46:     ],
47:     summary=(
48:         "Evaluar riesgo de todos "
49:         "los inventarios"
50:     )
51: )
52: async def evaluar_todos(
53:     generar_alertas: bool = Query(
54:         default=False,
55:         description=(
56:             "Si es true, crea o actualiza "
57:             "alertas y recomendaciones "
58:             "para inventarios con riesgo "
59:             "alto o crítico."
60:         )
61:     ),
62:     user: UsuarioActual = Depends(
63:         require_empresa
64:     )
65: ):
67:     return await service.evaluar_todos(
68:         generar_alertas=
69:             generar_alertas,
70:         ids_inventario=
71:             await AccesoService.ids_inventarios(
72:                 user
73:             )
74:     )
77: @router.get(
78:     "/{id_inventario}",
79:     response_model=InventoryRiskResponse,
80:     summary=(
81:         "Evaluar riesgo de un inventario"
82:     )
83: )
84: async def evaluar_inventario(
85:     id_inventario: str,
86:     generar_alertas: bool = Query(
87:         default=True,
88:         description=(
89:             "Si es true, crea o actualiza "
90:             "automáticamente la alerta y "
91:             "la recomendación cuando existe "
92:             "riesgo alto o crítico."
93:         )
94:     ),
95:     user: UsuarioActual = Depends(
96:         require_empresa
97:     )
98: ):
100:     await AccesoService.verificar_inventario(
101:         user,
102:         id_inventario
103:     )
105:     return await service.evaluar(
106:         id_inventario=
107:             id_inventario,
108:         generar_alertas=
109:             generar_alertas
110:     )
```

### app/controllers/saiki_controller.py

```python
1: import logging
2: import time
3: from uuid import uuid4
5: from fastapi import APIRouter, Depends, Request
6: from fastapi.routing import APIRoute
8: from app.dependencies.dependencies import require_empresa
9: from app.dto.auth_dto import UsuarioActual
10: from app.dto.saiki_dto import SaikiAskRequest, SaikiAskResponse
11: from app.services.saiki_service import SaikiService
14: logger = logging.getLogger(__name__)
17: class MeasuredSaikiRoute(APIRoute):
18:     def get_route_handler(self):
19:         handler = super().get_route_handler()
21:         async def measured(request: Request):
22:             started = time.perf_counter()
23:             request_id = uuid4().hex
24:             request.state.saiki_request_id = request_id
25:             logger.info("saiki_endpoint_start request_id=%s path=%s revision=%s", request_id, request.url.path, service._code_revision())
26:             try:
27:                 response = await handler(request)
28:                 response.headers["X-Saiki-Request-ID"] = request_id
29:                 response.headers["X-Saiki-Revision"] = service._code_revision()
30:                 return response
31:             finally:
32:                 logger.info("saiki_endpoint_complete request_id=%s path=%s duration_ms=%.3f", request_id, request.url.path, (time.perf_counter() - started) * 1000)
34:         return measured
37: router = APIRouter(
38:     prefix="/saiki",
39:     tags=["Saiki"],
40:     dependencies=[Depends(require_empresa)],
41:     route_class=MeasuredSaikiRoute,
42: )
43: service = SaikiService()
46: @router.get("/health", summary="Comprobar disponibilidad de Ollama y Saiki")
47: async def health():
48:     return await service.health()
51: @router.post(
52:     "/ask",
53:     response_model=SaikiAskResponse,
54:     summary="Resolver una consulta operacional con datos de PsiTwin",
55: )
56: async def ask(
57:     data: SaikiAskRequest,
58:     request: Request,
59:     user: UsuarioActual = Depends(require_empresa),
60: ):
61:     return await service.ask(data, user, request_id=request.state.saiki_request_id)
64: @router.post(
65:     "/chat",
66:     response_model=SaikiAskResponse,
67:     summary="Alias de consulta operacional de Saiki",
68: )
69: async def chat(
70:     data: SaikiAskRequest,
71:     request: Request,
72:     user: UsuarioActual = Depends(require_empresa),
73: ):
74:     return await service.ask(data, user, request_id=request.state.saiki_request_id)
```

### app/dto/inventory_risk_dto.py

```python
1: from datetime import datetime
2: from typing import Optional
4: from pydantic import BaseModel, Field
6: from app.dto.alerta_dto import (
7:     NivelRiesgo
8: )
11: class ConsumoInfo(BaseModel):
12:     promedio_7d: float = Field(
13:         ge=0
14:     )
16:     promedio_14d: float = Field(
17:         ge=0
18:     )
20:     promedio_28d: float = Field(
21:         ge=0
22:     )
24:     tendencia_porcentaje: float
27: class CoberturaInfo(BaseModel):
28:     dias: Optional[float] = Field(
29:         default=None,
30:         ge=0
31:     )
34: class ForecastDiario(BaseModel):
35:     fecha: datetime
37:     demanda_predicha: float = Field(
38:         ge=0
39:     )
42: class ForecastInfo(BaseModel):
43:     demanda_7d: Optional[float] = Field(
44:         default=None,
45:         ge=0
46:     )
48:     fecha_quiebre_estimada: Optional[
49:         datetime
50:     ] = None
52:     predicciones_diarias: list[
53:         ForecastDiario
54:     ] = Field(
55:         default_factory=list
56:     )
59: class SeguridadInfo(BaseModel):
60:     stock_seguridad: float = Field(
61:         ge=0
62:     )
64:     punto_reposicion: float = Field(
65:         ge=0
66:     )
69: class RiesgoInfo(BaseModel):
70:     nivel: NivelRiesgo
72:     score: float = Field(
73:         ge=0,
74:         le=100
75:     )
78: class ReposicionInfo(BaseModel):
79:     cantidad_minima: int = Field(
80:         ge=0
81:     )
83:     cantidad_recomendada: int = Field(
84:         ge=0
85:     )
87:     cantidad_segura: int = Field(
88:         ge=0
89:     )
92: class InventoryRiskResponse(BaseModel):
93:     id_empresa: str
94:     id_almacen: str
95:     id_inventario: str
96:     id_producto: str
98:     stock_actual: float = Field(
99:         ge=0
100:     )
102:     consumo: ConsumoInfo
104:     cobertura: CoberturaInfo
106:     lead_time_dias: int = Field(
107:         ge=0
108:     )
110:     forecast: ForecastInfo
112:     seguridad: SeguridadInfo
114:     riesgo: RiesgoInfo
116:     reposicion: Optional[
117:         ReposicionInfo
118:     ] = None
120:     explicacion: Optional[str] = None
```

### app/dto/saiki_dto.py

```python
1: from typing import Any
3: from pydantic import BaseModel, ConfigDict, Field, model_validator
6: class SaikiAskRequest(BaseModel):
7:     model_config = ConfigDict(
8:         json_schema_extra={
9:             "required": ["message"],
10:             "examples": [
11:                 {
12:                     "message": "Hola Saiki, ¿cómo está mi inventario?"
13:                 },
14:                 {
15:                     "message": "¿Qué productos tienen riesgo de quedarse sin stock?"
16:                 },
17:             ],
18:         }
19:     )
21:     message: str | None = Field(default=None, min_length=1)
22:     question: str | None = Field(
23:         default=None,
24:         min_length=1,
25:         description="Alias legacy de message. No es necesario para nuevas consultas.",
26:     )
27:     id_inventario: str | None = None
28:     id_producto: str | None = None
29:     page: int = Field(default=1, ge=1, description="Página del detalle de inventario.")
30:     page_size: int = Field(default=25, ge=1, le=100)
31:     context: dict[str, Any] = Field(
32:         default_factory=dict,
33:         description="Contexto técnico opcional; normalmente debe omitirse.",
34:     )
35:     history: list[dict[str, Any]] = Field(
36:         default_factory=list,
37:         description="Historial opcional de mensajes previos.",
38:     )
40:     @model_validator(mode="after")
41:     def require_message(self):
42:         if not self.message and not self.question:
43:             raise ValueError("Debe indicar message o question.")
44:         if self.message and self.question and self.message != self.question:
45:             raise ValueError("message y question no pueden ser diferentes.")
46:         if not self.message:
47:             self.message = self.question
48:         if not self.message.strip():
49:             raise ValueError("message no puede contener solo espacios.")
50:         if len(self.history) > 40:
51:             raise ValueError("El historial admite hasta 40 mensajes.")
52:         for item in self.history:
53:             if item.get("role") not in {"user", "assistant"} or not isinstance(item.get("content"), str):
54:                 raise ValueError("El historial solo admite mensajes de usuario y asistente con contenido textual.")
55:             if len(item["content"]) > 8000:
56:                 raise ValueError("Un mensaje del historial supera el límite de tamaño.")
57:             if set(item) - {"role", "content"}:
58:                 raise ValueError("El historial no admite instrucciones de herramientas.")
59:         return self
62: class SaikiAskResponse(BaseModel):
63:     answer: str
64:     model: str
65:     base_url: str
66:     source: str = "ollama"
67:     context: dict[str, Any] = Field(default_factory=dict)
68:     warnings: list[str] = Field(default_factory=list)
69:     data: dict[str, Any] = Field(default_factory=dict)
70:     visualization: dict[str, Any] = Field(
71:         default_factory=lambda: {"type": "none"}
72:     )
73:     sources: list[str] = Field(default_factory=list)
```

### app/ml/demand_history.py

```python
1: from __future__ import annotations
3: from datetime import (
4:     date,
5:     datetime,
6:     time,
7:     timedelta,
8:     timezone
9: )
11: from typing import (
12:     Optional,
13:     Dict,
14:     Any,
15:     List
16: )
18: import pandas as pd
20: from app.repositories.movimiento_repository import (
21:     MovimientoRepository
22: )
24: from app.repositories.inventario_repository import (
25:     InventarioRepository
26: )
29: class DemandHistory:
30:     """
31:     Construye el historial diario de demanda utilizado
32:     posteriormente por FeatureBuilder y LightGBM.
34:     Fuente:
36:         Movimiento
37:             ↓
38:         tipo = SALIDA
39:             ↓
40:         suma de cantidad por día
41:             ↓
42:         serie diaria
44:     Los días sin SALIDA se rellenan con demanda 0.
45:     """
51:     def __init__(
52:         self,
53:         movimiento_repository: Optional[
54:             MovimientoRepository
55:         ] = None,
56:         inventario_repository: Optional[
57:             InventarioRepository
58:         ] = None
59:     ) -> None:
61:         self.movimiento_repository = (
62:             movimiento_repository
63:             or MovimientoRepository()
64:         )
66:         self.inventario_repository = (
67:             inventario_repository
68:             or InventarioRepository()
69:         )
75:     @staticmethod
76:     def _inicio_dia(
77:         fecha: date | datetime
78:     ) -> datetime:
80:         if isinstance(
81:             fecha,
82:             datetime
83:         ):
85:             fecha = fecha.date()
87:         return datetime.combine(
88:             fecha,
89:             time.min,
90:             tzinfo=timezone.utc
91:         )
93:     @staticmethod
94:     def _fin_dia(
95:         fecha: date | datetime
96:     ) -> datetime:
98:         if isinstance(
99:             fecha,
100:             datetime
101:         ):
103:             fecha = fecha.date()
105:         return datetime.combine(
106:             fecha,
107:             time.max,
108:             tzinfo=timezone.utc
109:         )
115:     async def obtener_historial(
116:         self,
117:         id_inventario: str,
118:         dias: int = 400,
119:         fecha_fin: Optional[
120:             date | datetime
121:         ] = None
122:     ) -> pd.DataFrame:
124:         if dias <= 0:
126:             raise ValueError(
127:                 "dias debe ser mayor que 0."
128:             )
134:         inventario = (
135:             await self.inventario_repository
136:             .obtener_por_id(
137:                 id_inventario
138:             )
139:         )
141:         if inventario is None:
143:             raise ValueError(
144:                 "No existe el inventario "
145:                 f"{id_inventario}."
146:             )
152:         if fecha_fin is None:
154:             fecha_final_date = (
155:                 datetime.now(
156:                     timezone.utc
157:                 )
158:                 .date()
159:             )
161:         elif isinstance(
162:             fecha_fin,
163:             datetime
164:         ):
166:             fecha_final_date = (
167:                 fecha_fin.date()
168:             )
170:         else:
172:             fecha_final_date = (
173:                 fecha_fin
174:             )
180:         fecha_inicial_date = (
181:             fecha_final_date
182:             - timedelta(
183:                 days=dias - 1
184:             )
185:         )
187:         fecha_inicio_query = (
188:             self._inicio_dia(
189:                 fecha_inicial_date
190:             )
191:         )
193:         fecha_fin_query = (
194:             self._fin_dia(
195:                 fecha_final_date
196:             )
197:         )
203:         consumo = (
204:             await self.movimiento_repository
205:             .obtener_consumo_diario_inventario(
206:                 id_inventario=
207:                     id_inventario,
209:                 fecha_inicio=
210:                     fecha_inicio_query,
212:                 fecha_fin=
213:                     fecha_fin_query
214:             )
215:         )
221:         fechas = pd.date_range(
222:             start=fecha_inicial_date,
223:             end=fecha_final_date,
224:             freq="D"
225:         )
227:         historial = pd.DataFrame(
228:             {
229:                 "fecha":
230:                     fechas
231:             }
232:         )
235:         historial[
236:             "demanda"
237:         ] = 0.0
243:         if consumo:
245:             consumo_df = pd.DataFrame(
246:                 consumo
247:             )
249:             consumo_df[
250:                 "fecha"
251:             ] = pd.to_datetime(
252:                 consumo_df[
253:                     "fecha"
254:                 ]
255:             )
257:             consumo_df[
258:                 "cantidad"
259:             ] = pd.to_numeric(
260:                 consumo_df[
261:                     "cantidad"
262:                 ],
263:                 errors="coerce"
264:             ).fillna(
265:                 0
266:             )
268:             consumo_df = (
269:                 consumo_df[
270:                     [
271:                         "fecha",
272:                         "cantidad"
273:                     ]
274:                 ]
275:                 .rename(
276:                     columns={
277:                         "cantidad":
278:                             "demanda"
279:                     }
280:                 )
281:             )
287:             historial = (
288:                 historial[
289:                     [
290:                         "fecha"
291:                     ]
292:                 ]
293:                 .merge(
294:                     consumo_df,
295:                     how="left",
296:                     on="fecha"
297:                 )
298:             )
300:             historial[
301:                 "demanda"
302:             ] = (
303:                 historial[
304:                     "demanda"
305:                 ]
306:                 .fillna(
307:                     0
308:                 )
309:                 .astype(
310:                     float
311:                 )
312:             )
318:         historial = (
319:             historial
320:             .sort_values(
321:                 "fecha"
322:             )
323:             .reset_index(
324:                 drop=True
325:             )
326:         )
328:         return historial
334:     async def obtener_historial_completo(
335:         self,
336:         id_inventario: str
337:     ) -> pd.DataFrame:
339:         inventario = (
340:             await self.inventario_repository
341:             .obtener_por_id(
342:                 id_inventario
343:             )
344:         )
346:         if inventario is None:
348:             raise ValueError(
349:                 "Inventario no encontrado."
350:             )
352:         movimientos = (
353:             await self.movimiento_repository
354:             .obtener_por_inventario(
355:                 id_inventario
356:             )
357:         )
359:         salidas = [
361:             movimiento
363:             for movimiento in movimientos
365:             if (
366:                 movimiento.get(
367:                     "tipo_movimiento"
368:                 )
369:                 == "SALIDA"
370:             )
372:             and movimiento.get(
373:                 "fecha_hora"
374:             )
375:         ]
377:         if not salidas:
379:             return pd.DataFrame(
380:                 columns=[
381:                     "fecha",
382:                     "demanda"
383:                 ]
384:             )
386:         fecha_minima = min(
387:             movimiento[
388:                 "fecha_hora"
389:             ]
390:             for movimiento in salidas
391:         )
393:         fecha_maxima = datetime.now(
394:             timezone.utc
395:         )
397:         dias = (
398:             fecha_maxima.date()
399:             - fecha_minima.date()
400:         ).days + 1
402:         return await self.obtener_historial(
403:             id_inventario=
404:                 id_inventario,
406:             dias=
407:                 dias,
409:             fecha_fin=
410:                 fecha_maxima
411:         )
417:     async def obtener_resumen(
418:         self,
419:         id_inventario: str,
420:         dias: int = 400
421:     ) -> Dict[str, Any]:
423:         historial = (
424:             await self.obtener_historial(
425:                 id_inventario=
426:                     id_inventario,
428:                 dias=
429:                     dias
430:             )
431:         )
433:         if historial.empty:
435:             return {
436:                 "id_inventario":
437:                     id_inventario,
439:                 "dias":
440:                     0,
442:                 "demanda_total":
443:                     0,
445:                 "demanda_promedio":
446:                     0,
448:                 "dias_con_demanda":
449:                     0,
451:                 "dias_sin_demanda":
452:                     0,
454:                 "historial_suficiente_ml":
455:                     False
456:             }
458:         demanda = historial[
459:             "demanda"
460:         ]
462:         dias_con_demanda = int(
463:             (
464:                 demanda > 0
465:             ).sum()
466:         )
468:         dias_sin_demanda = int(
469:             (
470:                 demanda == 0
471:             ).sum()
472:         )
474:         return {
476:             "id_inventario":
477:                 id_inventario,
479:             "dias":
480:                 len(
481:                     historial
482:                 ),
484:             "fecha_inicio":
485:                 historial[
486:                     "fecha"
487:                 ]
488:                 .min()
489:                 .date()
490:                 .isoformat(),
492:             "fecha_fin":
493:                 historial[
494:                     "fecha"
495:                 ]
496:                 .max()
497:                 .date()
498:                 .isoformat(),
500:             "demanda_total":
501:                 float(
502:                     demanda.sum()
503:                 ),
505:             "demanda_promedio":
506:                 float(
507:                     demanda.mean()
508:                 ),
510:             "demanda_maxima":
511:                 float(
512:                     demanda.max()
513:                 ),
515:             "dias_con_demanda":
516:                 dias_con_demanda,
518:             "dias_sin_demanda":
519:                 dias_sin_demanda,
522:             "historial_suficiente_ml":
523:                 len(
524:                     historial
525:                 ) >= 367
526:         }
532:     async def obtener_ultimos_dias(
533:         self,
534:         id_inventario: str,
535:         dias: int
536:     ) -> List[Dict[str, Any]]:
538:         historial = (
539:             await self.obtener_historial(
540:                 id_inventario=
541:                     id_inventario,
543:                 dias=
544:                     dias
545:             )
546:         )
548:         resultado = []
550:         for _, row in (
551:             historial.iterrows()
552:         ):
554:             resultado.append(
555:                 {
556:                     "fecha":
557:                         row[
558:                             "fecha"
559:                         ]
560:                         .date()
561:                         .isoformat(),
563:                     "demanda":
564:                         float(
565:                             row[
566:                                 "demanda"
567:                             ]
568:                         )
569:                 }
570:             )
572:         return resultado
```

### app/ml/feature_builder.py

```python
3: from __future__ import annotations
5: from datetime import (
6:     date,
7:     datetime,
8:     timedelta
9: )
11: from typing import (
12:     Any,
13:     Dict,
14:     Iterable,
15:     Optional
16: )
18: import numpy as np
19: import pandas as pd
21: from app.ml.model_loader import (
22:     ModelLoader
23: )
26: class FeatureBuilder:
27:     """
28:     Construye y prepara las variables utilizadas por los
29:     modelos LightGBM de PsiTwin.
31:     Responsabilidades:
33:     1. Obtener la lista exacta de features del modelo.
34:     2. Construir features temporales.
35:     3. Construir lags.
36:     4. Construir rolling statistics.
37:     5. Construir EWMA.
38:     6. Construir variables de comportamiento/tendencia.
39:     7. Preparar features del horizonte D+1 ... D+7.
40:     8. Validar y ordenar las columnas exactamente como
41:        fueron utilizadas durante el entrenamiento.
43:     IMPORTANTE:
45:     Esta versión construye las variables que pueden obtenerse
46:     directamente del historial diario de demanda.
48:     Las variables de:
50:     - precio
51:     - eventos
52:     - SNAP
53:     - agregaciones de tienda
54:     - agregaciones de departamento
55:     - agregaciones globales del producto
57:     serán incorporadas posteriormente con sus fuentes reales.
58:     """
60:     EPSILON = 1e-8
66:     def __init__(
67:         self,
68:         loader: ModelLoader
69:     ) -> None:
71:         self.loader = loader
73:         self.features = (
74:             self.loader.get_features()
75:         )
77:         self.categorical_features = (
78:             self.loader
79:             .get_categorical_features()
80:         )
86:     @staticmethod
87:     def _safe_float(
88:         value: Any,
89:         default: float = 0.0
90:     ) -> float:
92:         try:
94:             result = float(
95:                 value
96:             )
98:             if np.isnan(result):
100:                 return default
102:             if np.isinf(result):
104:                 return default
106:             return result
108:         except (
109:             TypeError,
110:             ValueError
111:         ):
113:             return default
119:     @classmethod
120:     def _safe_divide(
121:         cls,
122:         numerator: float,
123:         denominator: float,
124:         default: float = 0.0
125:     ) -> float:
127:         numerator = cls._safe_float(
128:             numerator
129:         )
131:         denominator = cls._safe_float(
132:             denominator
133:         )
135:         if abs(
136:             denominator
137:         ) < cls.EPSILON:
139:             return default
141:         return (
142:             numerator
143:             / denominator
144:         )
150:     @staticmethod
151:     def _prepare_history(
152:         history: pd.DataFrame
153:     ) -> pd.DataFrame:
155:         if not isinstance(
156:             history,
157:             pd.DataFrame
158:         ):
160:             raise TypeError(
161:                 "history debe ser un pandas.DataFrame."
162:             )
164:         if history.empty:
166:             raise ValueError(
167:                 "El historial de demanda está vacío."
168:             )
170:         required = {
171:             "fecha",
172:             "demanda"
173:         }
175:         missing = (
176:             required
177:             - set(history.columns)
178:         )
180:         if missing:
182:             raise ValueError(
183:                 "El historial debe contener las columnas: "
184:                 "fecha y demanda."
185:             )
187:         df = history[
188:             [
189:                 "fecha",
190:                 "demanda"
191:             ]
192:         ].copy()
194:         df[
195:             "fecha"
196:         ] = pd.to_datetime(
197:             df["fecha"],
198:             errors="coerce"
199:         )
201:         df[
202:             "demanda"
203:         ] = pd.to_numeric(
204:             df["demanda"],
205:             errors="coerce"
206:         ).fillna(
207:             0.0
208:         )
210:         df = (
211:             df
212:             .dropna(
213:                 subset=[
214:                     "fecha"
215:                 ]
216:             )
217:             .sort_values(
218:                 "fecha"
219:             )
220:             .drop_duplicates(
221:                 subset=[
222:                     "fecha"
223:                 ],
224:                 keep="last"
225:             )
226:             .reset_index(
227:                 drop=True
228:             )
229:         )
231:         if df.empty:
233:             raise ValueError(
234:                 "No existen fechas válidas "
235:                 "en el historial."
236:             )
238:         return df
244:     @classmethod
245:     def _series(
246:         cls,
247:         history: pd.DataFrame
248:     ) -> pd.Series:
250:         df = cls._prepare_history(
251:             history
252:         )
254:         return (
255:             df[
256:                 "demanda"
257:             ]
258:             .astype(float)
259:             .reset_index(
260:                 drop=True
261:             )
262:         )
268:     @classmethod
269:     def _base_date(
270:         cls,
271:         history: pd.DataFrame
272:     ) -> pd.Timestamp:
274:         df = cls._prepare_history(
275:             history
276:         )
278:         return pd.Timestamp(
279:             df[
280:                 "fecha"
281:             ].iloc[-1]
282:         )
291:     @staticmethod
292:     def _lag(
293:         series: pd.Series,
294:         lag: int
295:     ) -> float:
297:         if lag <= 0:
299:             raise ValueError(
300:                 "lag debe ser mayor que 0."
301:             )
303:         if len(series) < lag:
305:             return np.nan
307:         return float(
308:             series.iloc[
309:                 -lag
310:             ]
311:         )
317:     @staticmethod
318:     def _last_values(
319:         series: pd.Series,
320:         window: int
321:     ) -> pd.Series:
323:         if window <= 0:
325:             raise ValueError(
326:                 "window debe ser mayor que 0."
327:             )
329:         if series.empty:
331:             return pd.Series(
332:                 dtype=float
333:             )
335:         return (
336:             series
337:             .iloc[
338:                 -window:
339:             ]
340:             .astype(float)
341:         )
347:     @classmethod
348:     def _rolling_mean(
349:         cls,
350:         series: pd.Series,
351:         window: int
352:     ) -> float:
354:         values = cls._last_values(
355:             series,
356:             window
357:         )
359:         if len(values) < window:
361:             return np.nan
363:         return float(
364:             values.mean()
365:         )
371:     @classmethod
372:     def _rolling_std(
373:         cls,
374:         series: pd.Series,
375:         window: int
376:     ) -> float:
378:         values = cls._last_values(
379:             series,
380:             window
381:         )
383:         if len(values) < window:
385:             return np.nan
387:         return float(
388:             values.std(
389:                 ddof=0
390:             )
391:         )
397:     @classmethod
398:     def _rolling_max(
399:         cls,
400:         series: pd.Series,
401:         window: int
402:     ) -> float:
404:         values = cls._last_values(
405:             series,
406:             window
407:         )
409:         if len(values) < window:
411:             return np.nan
413:         return float(
414:             values.max()
415:         )
421:     @classmethod
422:     def _ewma(
423:         cls,
424:         series: pd.Series,
425:         span: int
426:     ) -> float:
428:         if series.empty:
430:             return np.nan
432:         value = (
433:             series
434:             .astype(float)
435:             .ewm(
436:                 span=span,
437:                 adjust=False
438:             )
439:             .mean()
440:             .iloc[-1]
441:         )
443:         return float(
444:             value
445:         )
451:     @classmethod
452:     def _zero_ratio(
453:         cls,
454:         series: pd.Series,
455:         window: int
456:     ) -> float:
458:         values = cls._last_values(
459:             series,
460:             window
461:         )
463:         if len(values) < window:
465:             return np.nan
467:         return float(
468:             (
469:                 values == 0
470:             ).mean()
471:         )
477:     @staticmethod
478:     def _days_since_sale(
479:         series: pd.Series
480:     ) -> float:
482:         if series.empty:
484:             return np.nan
486:         values = (
487:             series
488:             .astype(float)
489:             .to_numpy()
490:         )
492:         positive_indices = np.where(
493:             values > 0
494:         )[0]
496:         if len(
497:             positive_indices
498:         ) == 0:
500:             return float(
501:                 len(values)
502:             )
504:         last_index = int(
505:             positive_indices[-1]
506:         )
508:         return float(
509:             len(values)
510:             - 1
511:             - last_index
512:         )
518:     @classmethod
519:     def _sale_rate(
520:         cls,
521:         series: pd.Series,
522:         window: int
523:     ) -> float:
525:         values = cls._last_values(
526:             series,
527:             window
528:         )
530:         if len(values) < window:
532:             return np.nan
534:         return float(
535:             (
536:                 values > 0
537:             ).mean()
538:         )
544:     @classmethod
545:     def _growth_streak_3(
546:         cls,
547:         series: pd.Series
548:     ) -> float:
550:         values = cls._last_values(
551:             series,
552:             4
553:         )
555:         if len(values) < 4:
557:             return np.nan
559:         diffs = (
560:             values
561:             .diff()
562:             .dropna()
563:         )
565:         return float(
566:             (
567:                 diffs > 0
568:             ).all()
569:         )
575:     @classmethod
576:     def _peak_count_7(
577:         cls,
578:         series: pd.Series
579:     ) -> float:
581:         values = cls._last_values(
582:             series,
583:             7
584:         )
586:         if len(values) < 7:
588:             return np.nan
590:         mean_28 = cls._rolling_mean(
591:             series,
592:             28
593:         )
595:         if np.isnan(
596:             mean_28
597:         ):
599:             return np.nan
601:         return float(
602:             (
603:                 values > mean_28
604:             ).sum()
605:         )
611:     @staticmethod
612:     def _increments(
613:         series: pd.Series
614:     ) -> pd.Series:
616:         return (
617:             series
618:             .astype(float)
619:             .diff()
620:             .dropna()
621:             .reset_index(
622:                 drop=True
623:             )
624:         )
632:     @classmethod
633:     def _dow_mean(
634:         cls,
635:         history: pd.DataFrame,
636:         target_date: pd.Timestamp,
637:         weeks: int
638:     ) -> float:
640:         df = cls._prepare_history(
641:             history
642:         )
644:         target_dow = (
645:             target_date.dayofweek
646:         )
648:         filtered = df[
649:             df[
650:                 "fecha"
651:             ].dt.dayofweek
652:             == target_dow
653:         ]
655:         filtered = (
656:             filtered.tail(
657:                 weeks
658:             )
659:         )
661:         if len(
662:             filtered
663:         ) < 1:
665:             return np.nan
667:         return float(
668:             filtered[
669:                 "demanda"
670:             ].mean()
671:         )
677:     @classmethod
678:     def _dow_std(
679:         cls,
680:         history: pd.DataFrame,
681:         target_date: pd.Timestamp,
682:         weeks: int
683:     ) -> float:
685:         df = cls._prepare_history(
686:             history
687:         )
689:         target_dow = (
690:             target_date.dayofweek
691:         )
693:         filtered = df[
694:             df[
695:                 "fecha"
696:             ].dt.dayofweek
697:             == target_dow
698:         ].tail(
699:             weeks
700:         )
702:         if len(filtered) < 2:
704:             return np.nan
706:         return float(
707:             filtered[
708:                 "demanda"
709:             ].std(
710:                 ddof=0
711:             )
712:         )
718:     @staticmethod
719:     def _calendar_features(
720:         fecha: pd.Timestamp
721:     ) -> Dict[str, Any]:
723:         iso_calendar = (
724:             fecha.isocalendar()
725:         )
727:         return {
729:             "month":
730:                 int(fecha.month),
732:             "year":
733:                 int(fecha.year),
735:             "dayofweek":
736:                 int(fecha.dayofweek),
738:             "day":
739:                 int(fecha.day),
741:             "weekofyear":
742:                 int(
743:                     iso_calendar.week
744:                 ),
746:             "is_weekend":
747:                 int(
748:                     fecha.dayofweek >= 5
749:                 ),
751:             "quarter":
752:                 int(fecha.quarter),
754:             "dayofyear":
755:                 int(fecha.dayofyear),
757:             "is_month_start":
758:                 int(
759:                     fecha.is_month_start
760:                 ),
762:             "is_month_end":
763:                 int(
764:                     fecha.is_month_end
765:                 )
766:         }
772:     @staticmethod
773:     def _target_calendar_features(
774:         fecha: pd.Timestamp
775:     ) -> Dict[str, Any]:
777:         iso_calendar = (
778:             fecha.isocalendar()
779:         )
781:         return {
783:             "target_month":
784:                 int(fecha.month),
786:             "target_dayofweek":
787:                 int(fecha.dayofweek),
789:             "target_day":
790:                 int(fecha.day),
792:             "target_weekofyear":
793:                 int(
794:                     iso_calendar.week
795:                 ),
797:             "target_is_weekend":
798:                 int(
799:                     fecha.dayofweek >= 5
800:                 ),
802:             "target_quarter":
803:                 int(fecha.quarter),
805:             "target_dayofyear":
806:                 int(fecha.dayofyear)
807:         }
813:     def build_demand_features(
814:         self,
815:         history: pd.DataFrame,
816:         horizon: int,
817:         context: Optional[
818:             Dict[str, Any]
819:         ] = None
820:     ) -> Dict[str, Any]:
822:         if horizon < 1 or horizon > 7:
824:             raise ValueError(
825:                 "horizon debe estar entre 1 y 7."
826:             )
828:         df = self._prepare_history(
829:             history
830:         )
832:         series = (
833:             df[
834:                 "demanda"
835:             ]
836:             .astype(float)
837:             .reset_index(
838:                 drop=True
839:             )
840:         )
842:         base_date = pd.Timestamp(
843:             df[
844:                 "fecha"
845:             ].iloc[-1]
846:         )
848:         target_date = (
849:             base_date
850:             + pd.Timedelta(
851:                 days=horizon
852:             )
853:         )
855:         context = (
856:             dict(context)
857:             if context
858:             else {}
859:         )
861:         result: Dict[
862:             str,
863:             Any
864:         ] = {}
870:         result.update(
871:             context
872:         )
878:         result.update(
879:             self._calendar_features(
880:                 base_date
881:             )
882:         )
888:         result.update(
889:             self._target_calendar_features(
890:                 target_date
891:             )
892:         )
898:         result[
899:             "current_y"
900:         ] = float(
901:             series.iloc[-1]
902:         )
908:         result[
909:             "age_days"
910:         ] = float(
911:             len(series)
912:             - 1
913:         )
919:         lags = [
920:             1,
921:             2,
922:             3,
923:             4,
924:             5,
925:             6,
926:             7,
927:             14,
928:             21,
929:             28,
930:             35,
931:             42,
932:             56,
933:             364,
934:             365,
935:             366
936:         ]
938:         for lag in lags:
940:             result[
941:                 f"lag_{lag}"
942:             ] = self._lag(
943:                 series,
944:                 lag
945:             )
951:         for window in [
952:             3,
953:             7,
954:             14,
955:             28,
956:             56,
957:             180
958:         ]:
960:             result[
961:                 f"rolling_mean_{window}"
962:             ] = self._rolling_mean(
963:                 series,
964:                 window
965:             )
971:         for window in [
972:             3,
973:             7,
974:             28,
975:             56
976:         ]:
978:             result[
979:                 f"rolling_std_{window}"
980:             ] = self._rolling_std(
981:                 series,
982:                 window
983:             )
989:         for window in [
990:             3,
991:             7,
992:             28
993:         ]:
995:             result[
996:                 f"rolling_max_{window}"
997:             ] = self._rolling_max(
998:                 series,
999:                 window
1000:             )
1006:         for span in [
1007:             3,
1008:             7,
1009:             14,
1010:             28
1011:         ]:
1013:             result[
1014:                 f"ewma_{span}"
1015:             ] = self._ewma(
1016:                 series,
1017:                 span
1018:             )
1024:         result[
1025:             "zero_ratio_7"
1026:         ] = self._zero_ratio(
1027:             series,
1028:             7
1029:         )
1031:         result[
1032:             "zero_ratio_28"
1033:         ] = self._zero_ratio(
1034:             series,
1035:             28
1036:         )
1042:         lag_1 = result.get(
1043:             "lag_1"
1044:         )
1046:         lag_2 = result.get(
1047:             "lag_2"
1048:         )
1050:         lag_3 = result.get(
1051:             "lag_3"
1052:         )
1054:         lag_7 = result.get(
1055:             "lag_7"
1056:         )
1058:         result[
1059:             "change_1_2"
1060:         ] = (
1061:             lag_1 - lag_2
1062:             if not (
1063:                 pd.isna(lag_1)
1064:                 or pd.isna(lag_2)
1065:             )
1066:             else np.nan
1067:         )
1069:         result[
1070:             "change_1_3"
1071:         ] = (
1072:             lag_1 - lag_3
1073:             if not (
1074:                 pd.isna(lag_1)
1075:                 or pd.isna(lag_3)
1076:             )
1077:             else np.nan
1078:         )
1080:         result[
1081:             "change_1_7"
1082:         ] = (
1083:             lag_1 - lag_7
1084:             if not (
1085:                 pd.isna(lag_1)
1086:                 or pd.isna(lag_7)
1087:             )
1088:             else np.nan
1089:         )
1095:         mean_3 = result.get(
1096:             "rolling_mean_3"
1097:         )
1099:         mean_7 = result.get(
1100:             "rolling_mean_7"
1101:         )
1103:         mean_14 = result.get(
1104:             "rolling_mean_14"
1105:         )
1107:         mean_28 = result.get(
1108:             "rolling_mean_28"
1109:         )
1111:         max_3 = result.get(
1112:             "rolling_max_3"
1113:         )
1115:         max_7 = result.get(
1116:             "rolling_max_7"
1117:         )
1119:         result[
1120:             "ratio_mean3_mean14"
1121:         ] = self._safe_divide(
1122:             mean_3,
1123:             mean_14
1124:         )
1126:         result[
1127:             "ratio_mean7_mean28"
1128:         ] = self._safe_divide(
1129:             mean_7,
1130:             mean_28
1131:         )
1133:         result[
1134:             "acceleration_3_7"
1135:         ] = (
1136:             mean_3 - mean_7
1137:             if not (
1138:                 pd.isna(mean_3)
1139:                 or pd.isna(mean_7)
1140:             )
1141:             else np.nan
1142:         )
1144:         result[
1145:             "acceleration_7_28"
1146:         ] = (
1147:             mean_7 - mean_28
1148:             if not (
1149:                 pd.isna(mean_7)
1150:                 or pd.isna(mean_28)
1151:             )
1152:             else np.nan
1153:         )
1155:         result[
1156:             "max7_vs_mean28"
1157:         ] = self._safe_divide(
1158:             max_7,
1159:             mean_28
1160:         )
1162:         result[
1163:             "max3_vs_mean28"
1164:         ] = self._safe_divide(
1165:             max_3,
1166:             mean_28
1167:         )
1173:         if len(series) >= 14:
1175:             recent_7 = (
1176:                 series.iloc[
1177:                     -7:
1178:                 ].mean()
1179:             )
1181:             previous_7 = (
1182:                 series.iloc[
1183:                     -14:-7
1184:                 ].mean()
1185:             )
1187:             result[
1188:                 "previous_7_mean"
1189:             ] = float(
1190:                 previous_7
1191:             )
1193:             result[
1194:                 "recent7_vs_previous7"
1195:             ] = self._safe_divide(
1196:                 recent_7,
1197:                 previous_7
1198:             )
1200:         else:
1202:             result[
1203:                 "previous_7_mean"
1204:             ] = np.nan
1206:             result[
1207:                 "recent7_vs_previous7"
1208:             ] = np.nan
1214:         result[
1215:             "dow_mean_4w"
1216:         ] = self._dow_mean(
1217:             df,
1218:             base_date,
1219:             4
1220:         )
1226:         result[
1227:             "growth_streak_3"
1228:         ] = self._growth_streak_3(
1229:             series
1230:         )
1236:         result[
1237:             "peak_count_7"
1238:         ] = self._peak_count_7(
1239:             series
1240:         )
1246:         increments = (
1247:             self._increments(
1248:                 series
1249:             )
1250:         )
1252:         for window in [
1253:             3,
1254:             7,
1255:             14,
1256:             28
1257:         ]:
1259:             result[
1260:                 f"rolling_inc_mean_{window}"
1261:             ] = self._rolling_mean(
1262:                 increments,
1263:                 window
1264:             )
1266:         for window in [
1267:             7,
1268:             28
1269:         ]:
1271:             result[
1272:                 f"rolling_inc_std_{window}"
1273:             ] = self._rolling_std(
1274:                 increments,
1275:                 window
1276:             )
1282:         result[
1283:             "days_since_sale"
1284:         ] = self._days_since_sale(
1285:             series
1286:         )
1288:         result[
1289:             "sale_rate_28"
1290:         ] = self._sale_rate(
1291:             series,
1292:             28
1293:         )
1299:         current_y = result[
1300:             "current_y"
1301:         ]
1303:         result[
1304:             "current_vs_mean7"
1305:         ] = self._safe_divide(
1306:             current_y,
1307:             mean_7
1308:         )
1310:         result[
1311:             "current_vs_mean28"
1312:         ] = self._safe_divide(
1313:             current_y,
1314:             mean_28
1315:         )
1330:         future_lags = [
1331:             7,
1332:             14,
1333:             21,
1334:             28,
1335:             35,
1336:             42,
1337:             364,
1338:             365,
1339:             366
1340:         ]
1342:         for lag in future_lags:
1344:             effective_lag = (
1345:                 lag
1346:                 - horizon
1347:             )
1349:             if effective_lag >= 1:
1351:                 value = self._lag(
1352:                     series,
1353:                     effective_lag
1354:                 )
1356:             elif effective_lag == 0:
1358:                 value = float(
1359:                     series.iloc[-1]
1360:                 )
1362:             else:
1366:                 value = np.nan
1368:             result[
1369:                 f"future_lag_{lag}"
1370:             ] = value
1376:         result[
1377:             "future_dow_mean_6w"
1378:         ] = self._dow_mean(
1379:             df,
1380:             target_date,
1381:             6
1382:         )
1384:         result[
1385:             "future_dow_std_6w"
1386:         ] = self._dow_std(
1387:             df,
1388:             target_date,
1389:             6
1390:         )
1401:         pending_features = [
1407:             "item_id",
1408:             "dept_id",
1409:             "cat_id",
1410:             "store_id",
1411:             "state_id",
1417:             "snap",
1418:             "has_event",
1419:             "event_name_1",
1420:             "event_type_1",
1421:             "event_name_2",
1422:             "event_type_2",
1428:             "sell_price",
1429:             "price_available",
1430:             "price_lag_1",
1431:             "price_lag_7",
1432:             "price_change_1",
1433:             "price_change_7",
1434:             "price_mean_28",
1435:             "price_relative_28",
1436:             "price_mean_180",
1437:             "price_std_180",
1438:             "price_min_180",
1439:             "price_max_180",
1440:             "price_relative_180",
1441:             "price_to_max_180",
1442:             "price_range_position_180",
1448:             "store_sales_lag_1",
1449:             "store_sales_lag_7",
1450:             "store_sales_lag_28",
1451:             "store_sales_mean_7",
1452:             "store_sales_mean_28",
1458:             "dept_sales_lag_1",
1459:             "dept_sales_lag_7",
1460:             "dept_sales_lag_28",
1461:             "dept_sales_mean_7",
1462:             "dept_sales_mean_28",
1468:             "item_total_lag_1",
1469:             "item_total_lag_7",
1470:             "item_total_lag_28",
1476:             "future_sell_price",
1477:             "future_price_available",
1478:             "future_snap",
1479:             "future_has_event",
1480:             "future_event_name_1_code",
1481:             "future_event_type_1_code",
1483:             "future_store_lag_7",
1484:             "future_dept_lag_7"
1485:         ]
1487:         for feature in pending_features:
1489:             if feature not in result:
1491:                 result[
1492:                     feature
1493:                 ] = np.nan
1495:         return result
1501:     def build_horizons(
1502:         self,
1503:         history: pd.DataFrame,
1504:         context: Optional[
1505:             Dict[str, Any]
1506:         ] = None
1507:     ) -> Dict[
1508:         int,
1509:         Dict[str, Any]
1510:     ]:
1512:         result = {}
1514:         for horizon in range(
1515:             1,
1516:             8
1517:         ):
1519:             result[
1520:                 horizon
1521:             ] = self.build_demand_features(
1522:                 history=
1523:                     history,
1525:                 horizon=
1526:                     horizon,
1528:                 context=
1529:                     context
1530:             )
1532:         return result
1538:     def validate_features(
1539:         self,
1540:         data: Dict[
1541:             str,
1542:             Any
1543:         ]
1544:     ) -> None:
1546:         if not isinstance(
1547:             data,
1548:             dict
1549:         ):
1551:             raise TypeError(
1552:                 "data debe ser un diccionario."
1553:             )
1555:         missing = [
1557:             feature
1559:             for feature
1560:             in self.features
1562:             if feature
1563:             not in data
1564:         ]
1566:         if missing:
1568:             raise ValueError(
1569:                 "Faltan features requeridas "
1570:                 "por LightGBM:\n\n"
1571:                 + "\n".join(
1572:                     missing
1573:                 )
1574:             )
1580:     def missing_features(
1581:         self,
1582:         data: Dict[
1583:             str,
1584:             Any
1585:         ]
1586:     ) -> list[str]:
1588:         return [
1590:             feature
1592:             for feature
1593:             in self.features
1595:             if feature
1596:             not in data
1597:         ]
1603:     def extra_features(
1604:         self,
1605:         data: Dict[
1606:             str,
1607:             Any
1608:         ]
1609:     ) -> list[str]:
1611:         expected = set(
1612:             self.features
1613:         )
1615:         return [
1617:             column
1619:             for column
1620:             in data.keys()
1622:             if column
1623:             not in expected
1624:         ]
1630:     def build_row(
1631:         self,
1632:         data: Dict[
1633:             str,
1634:             Any
1635:         ]
1636:     ) -> pd.DataFrame:
1638:         self.validate_features(
1639:             data
1640:         )
1642:         row = {
1644:             feature:
1645:                 data[
1646:                     feature
1647:                 ]
1649:             for feature
1650:             in self.features
1651:         }
1653:         df = pd.DataFrame(
1654:             [
1655:                 row
1656:             ]
1657:         )
1659:         return self.prepare_dataframe(
1660:             df
1661:         )
1667:     def build_dataframe(
1668:         self,
1669:         rows: Iterable[
1670:             Dict[
1671:                 str,
1672:                 Any
1673:             ]
1674:         ]
1675:     ) -> pd.DataFrame:
1677:         rows = list(
1678:             rows
1679:         )
1681:         if not rows:
1683:             raise ValueError(
1684:                 "No se recibieron filas "
1685:                 "para construir features."
1686:             )
1688:         df = pd.DataFrame(
1689:             rows
1690:         )
1692:         return self.prepare_dataframe(
1693:             df
1694:         )
1700:     def prepare_dataframe(
1701:         self,
1702:         df: pd.DataFrame
1703:     ) -> pd.DataFrame:
1705:         if not isinstance(
1706:             df,
1707:             pd.DataFrame
1708:         ):
1710:             raise TypeError(
1711:                 "df debe ser un pandas.DataFrame."
1712:             )
1714:         if df.empty:
1716:             raise ValueError(
1717:                 "El DataFrame está vacío."
1718:             )
1720:         df = df.copy()
1726:         missing = [
1728:             feature
1730:             for feature
1731:             in self.features
1733:             if feature
1734:             not in df.columns
1735:         ]
1737:         if missing:
1739:             raise ValueError(
1740:                 "El DataFrame no contiene "
1741:                 "todas las features requeridas:\n\n"
1742:                 + "\n".join(
1743:                     missing
1744:                 )
1745:             )
1751:         df = df[
1752:             self.features
1753:         ].copy()
1755:         categorical_set = set(
1756:             self.categorical_features
1757:         )
1763:         for column in (
1764:             self.categorical_features
1765:         ):
1767:             if column not in df.columns:
1769:                 continue
1771:             df[
1772:                 column
1773:             ] = (
1774:                 df[
1775:                     column
1776:                 ]
1777:                 .astype(
1778:                     "category"
1779:                 )
1780:             )
1786:         numerical_columns = [
1788:             column
1790:             for column
1791:             in self.features
1793:             if column
1794:             not in categorical_set
1795:         ]
1797:         for column in numerical_columns:
1799:             df[
1800:                 column
1801:             ] = pd.to_numeric(
1802:                 df[
1803:                     column
1804:                 ],
1805:                 errors="coerce"
1806:             )
1812:         df.replace(
1813:             [
1814:                 np.inf,
1815:                 -np.inf
1816:             ],
1817:             np.nan,
1818:             inplace=True
1819:         )
1821:         return df
1827:     def info(
1828:         self
1829:     ) -> dict:
1831:         return {
1833:             "feature_count":
1834:                 len(
1835:                     self.features
1836:                 ),
1838:             "categorical_feature_count":
1839:                 len(
1840:                     self.categorical_features
1841:                 ),
1843:             "features":
1844:                 self.features,
1846:             "categorical_features":
1847:                 self.categorical_features
1848:         }
```

### app/ml/ml_context_builder.py

```python
3: from __future__ import annotations
5: from datetime import (
6:     date,
7:     datetime,
8:     time,
9:     timedelta,
10:     timezone
11: )
13: from typing import (
14:     Any,
15:     Dict,
16:     List,
17:     Optional
18: )
20: from app.repositories.inventario_repository import (
21:     InventarioRepository
22: )
24: from app.repositories.producto_repository import (
25:     ProductoRepository
26: )
28: from app.repositories.rack_repository import (
29:     RackRepository
30: )
32: from app.repositories.zona_repository import (
33:     ZonaRepository
34: )
36: from app.repositories.almacen_repository import (
37:     AlmacenRepository
38: )
40: from app.repositories.movimiento_repository import (
41:     MovimientoRepository
42: )
45: class MLContextBuilder:
47:     MAX_LAG = 28
54:     def __init__(
55:         self
56:     ) -> None:
58:         self.inventario_repository = (
59:             InventarioRepository()
60:         )
62:         self.producto_repository = (
63:             ProductoRepository
64:         )
66:         self.rack_repository = (
67:             RackRepository
68:         )
70:         self.zona_repository = (
71:             ZonaRepository
72:         )
74:         self.almacen_repository = (
75:             AlmacenRepository
76:         )
78:         self.movimiento_repository = (
79:             MovimientoRepository()
80:         )
87:     @staticmethod
88:     def _obtener_id(
89:         documento: Optional[
90:             Dict[str, Any]
91:         ],
92:         *campos: str
93:     ) -> Optional[str]:
95:         if not documento:
96:             return None
98:         for campo in campos:
100:             valor = documento.get(
101:                 campo
102:             )
104:             if valor is None:
105:                 continue
107:             valor = str(
108:                 valor
109:             ).strip()
111:             if valor:
112:                 return valor
114:         return None
121:     @classmethod
122:     def _obtener_ids_productos(
123:         cls,
124:         productos: List[
125:             Dict[str, Any]
126:         ]
127:     ) -> List[str]:
129:         ids_productos = []
131:         for producto in productos:
133:             id_producto = (
134:                 cls._obtener_id(
135:                     producto,
136:                     "id_producto",
137:                     "id"
138:                 )
139:             )
141:             if id_producto:
143:                 ids_productos.append(
144:                     id_producto
145:                 )
147:         return list(
148:             dict.fromkeys(
149:                 ids_productos
150:             )
151:         )
158:     @staticmethod
159:     def _normalizar_texto(
160:         valor: Any
161:     ) -> Optional[str]:
163:         if valor is None:
164:             return None
166:         valor = str(
167:             valor
168:         ).strip()
170:         if not valor:
171:             return None
173:         return valor
180:     @staticmethod
181:     def _normalizar_fecha_base(
182:         fecha_base: Optional[
183:             date | datetime
184:         ] = None
185:     ) -> date:
187:         if fecha_base is None:
189:             return (
190:                 datetime.now(
191:                     timezone.utc
192:                 )
193:                 .date()
194:             )
196:         if isinstance(
197:             fecha_base,
198:             datetime
199:         ):
201:             return fecha_base.date()
203:         if isinstance(
204:             fecha_base,
205:             date
206:         ):
208:             return fecha_base
210:         raise TypeError(
211:             "fecha_base debe ser "
212:             "date, datetime o None."
213:         )
220:     @staticmethod
221:     def _validar_horizon(
222:         horizon: int
223:     ) -> int:
225:         try:
227:             horizon = int(
228:                 horizon
229:             )
231:         except (
232:             TypeError,
233:             ValueError
234:         ):
236:             raise ValueError(
237:                 "horizon debe ser un entero."
238:             )
240:         if horizon < 1 or horizon > 7:
242:             raise ValueError(
243:                 "horizon debe estar "
244:                 "entre 1 y 7."
245:             )
247:         return horizon
254:     @classmethod
255:     def _obtener_rango_fechas(
256:         cls,
257:         fecha_base: date
258:     ) -> tuple[
259:         datetime,
260:         datetime
261:     ]:
263:         fecha_inicio_date = (
265:             fecha_base
267:             - timedelta(
268:                 days=cls.MAX_LAG
269:             )
270:         )
272:         fecha_inicio = datetime.combine(
273:             fecha_inicio_date,
274:             time.min,
275:             tzinfo=timezone.utc
276:         )
278:         fecha_fin = datetime.combine(
279:             fecha_base,
280:             time.max,
281:             tzinfo=timezone.utc
282:         )
284:         return (
285:             fecha_inicio,
286:             fecha_fin
287:         )
296:     @classmethod
297:     def _crear_serie_diaria(
298:         cls,
299:         consumos: List[
300:             Dict[str, Any]
301:         ],
302:         fecha_base: date
303:     ) -> Dict[
304:         date,
305:         float
306:     ]:
308:         fecha_inicio = (
310:             fecha_base
312:             - timedelta(
313:                 days=cls.MAX_LAG
314:             )
315:         )
317:         serie = {}
319:         fecha_actual = fecha_inicio
321:         while fecha_actual <= fecha_base:
323:             serie[
324:                 fecha_actual
325:             ] = 0.0
327:             fecha_actual += timedelta(
328:                 days=1
329:             )
331:         for registro in consumos:
333:             fecha = registro.get(
334:                 "fecha"
335:             )
337:             cantidad = registro.get(
338:                 "cantidad",
339:                 0
340:             )
342:             if fecha is None:
343:                 continue
345:             try:
347:                 if isinstance(
348:                     fecha,
349:                     datetime
350:                 ):
352:                     fecha_registro = (
353:                         fecha.date()
354:                     )
356:                 elif isinstance(
357:                     fecha,
358:                     date
359:                 ):
361:                     fecha_registro = fecha
363:                 else:
365:                     fecha_registro = (
366:                         datetime.strptime(
367:                             str(fecha),
368:                             "%Y-%m-%d"
369:                         )
370:                         .date()
371:                     )
373:             except (
374:                 TypeError,
375:                 ValueError
376:             ):
378:                 continue
380:             if fecha_registro not in serie:
381:                 continue
383:             try:
385:                 cantidad_float = float(
386:                     cantidad
387:                 )
389:             except (
390:                 TypeError,
391:                 ValueError
392:             ):
394:                 cantidad_float = 0.0
396:             serie[
397:                 fecha_registro
398:             ] += cantidad_float
400:         return serie
407:     @staticmethod
408:     def _lag(
409:         serie: Dict[
410:             date,
411:             float
412:         ],
413:         fecha_base: date,
414:         lag: int
415:     ) -> float:
417:         fecha_objetivo = (
419:             fecha_base
421:             - timedelta(
422:                 days=lag
423:             )
424:         )
426:         return float(
427:             serie.get(
428:                 fecha_objetivo,
429:                 0.0
430:             )
431:         )
442:     @staticmethod
443:     def _mean_anterior(
444:         serie: Dict[
445:             date,
446:             float
447:         ],
448:         fecha_base: date,
449:         window: int
450:     ) -> float:
452:         valores = []
454:         for lag in range(
455:             1,
456:             window + 1
457:         ):
459:             fecha_objetivo = (
461:                 fecha_base
463:                 - timedelta(
464:                     days=lag
465:                 )
466:             )
468:             valores.append(
469:                 float(
470:                     serie.get(
471:                         fecha_objetivo,
472:                         0.0
473:                     )
474:                 )
475:             )
477:         if not valores:
478:             return 0.0
480:         return float(
481:             sum(valores)
482:             / len(valores)
483:         )
490:     @classmethod
491:     def _crear_item_features(
492:         cls,
493:         serie: Dict[
494:             date,
495:             float
496:         ],
497:         fecha_base: date
498:     ) -> Dict[str, float]:
500:         return {
502:             "item_total_lag_1":
503:                 cls._lag(
504:                     serie,
505:                     fecha_base,
506:                     1
507:                 ),
509:             "item_total_lag_7":
510:                 cls._lag(
511:                     serie,
512:                     fecha_base,
513:                     7
514:                 ),
516:             "item_total_lag_28":
517:                 cls._lag(
518:                     serie,
519:                     fecha_base,
520:                     28
521:                 )
522:         }
529:     @classmethod
530:     def _crear_dept_features(
531:         cls,
532:         serie: Dict[
533:             date,
534:             float
535:         ],
536:         fecha_base: date
537:     ) -> Dict[str, float]:
539:         return {
541:             "dept_sales_lag_1":
542:                 cls._lag(
543:                     serie,
544:                     fecha_base,
545:                     1
546:                 ),
548:             "dept_sales_lag_7":
549:                 cls._lag(
550:                     serie,
551:                     fecha_base,
552:                     7
553:                 ),
555:             "dept_sales_lag_28":
556:                 cls._lag(
557:                     serie,
558:                     fecha_base,
559:                     28
560:                 ),
562:             "dept_sales_mean_7":
563:                 cls._mean_anterior(
564:                     serie,
565:                     fecha_base,
566:                     7
567:                 ),
569:             "dept_sales_mean_28":
570:                 cls._mean_anterior(
571:                     serie,
572:                     fecha_base,
573:                     28
574:                 )
575:         }
582:     @classmethod
583:     def _crear_store_features(
584:         cls,
585:         serie: Dict[
586:             date,
587:             float
588:         ],
589:         fecha_base: date
590:     ) -> Dict[str, float]:
592:         return {
594:             "store_sales_lag_1":
595:                 cls._lag(
596:                     serie,
597:                     fecha_base,
598:                     1
599:                 ),
601:             "store_sales_lag_7":
602:                 cls._lag(
603:                     serie,
604:                     fecha_base,
605:                     7
606:                 ),
608:             "store_sales_lag_28":
609:                 cls._lag(
610:                     serie,
611:                     fecha_base,
612:                     28
613:                 ),
615:             "store_sales_mean_7":
616:                 cls._mean_anterior(
617:                     serie,
618:                     fecha_base,
619:                     7
620:                 ),
622:             "store_sales_mean_28":
623:                 cls._mean_anterior(
624:                     serie,
625:                     fecha_base,
626:                     28
627:                 )
628:         }
648:     @classmethod
649:     def _crear_future_features(
650:         cls,
651:         serie_almacen: Dict[
652:             date,
653:             float
654:         ],
655:         serie_departamento: Dict[
656:             date,
657:             float
658:         ],
659:         fecha_base: date,
660:         horizon: int
661:     ) -> Dict[str, float]:
663:         horizon = (
664:             cls._validar_horizon(
665:                 horizon
666:             )
667:         )
669:         effective_lag = (
670:             7 - horizon
671:         )
673:         return {
675:             "future_store_lag_7":
676:                 cls._lag(
677:                     serie_almacen,
678:                     fecha_base,
679:                     effective_lag
680:                 ),
682:             "future_dept_lag_7":
683:                 cls._lag(
684:                     serie_departamento,
685:                     fecha_base,
686:                     effective_lag
687:                 )
688:         }
695:     async def build(
696:         self,
697:         id_inventario: str,
698:         fecha_base: Optional[
699:             date | datetime
700:         ] = None
701:     ) -> Dict[str, Any]:
707:         if id_inventario is None:
709:             raise ValueError(
710:                 "id_inventario es obligatorio."
711:             )
713:         id_inventario = str(
714:             id_inventario
715:         ).strip()
717:         if not id_inventario:
719:             raise ValueError(
720:                 "id_inventario no puede estar vacío."
721:             )
728:         fecha_base_normalizada = (
729:             self._normalizar_fecha_base(
730:                 fecha_base
731:             )
732:         )
734:         (
735:             fecha_inicio_query,
736:             fecha_fin_query
737:         ) = (
738:             self._obtener_rango_fechas(
739:                 fecha_base_normalizada
740:             )
741:         )
748:         inventario = await (
749:             self.inventario_repository
750:             .obtener_por_id(
751:                 id_inventario
752:             )
753:         )
755:         if not inventario:
757:             raise ValueError(
758:                 "No existe el inventario "
759:                 f"con id {id_inventario}."
760:             )
767:         id_producto = (
768:             self._obtener_id(
769:                 inventario,
770:                 "id_producto"
771:             )
772:         )
774:         if not id_producto:
776:             raise ValueError(
777:                 "El inventario no tiene "
778:                 "id_producto asociado."
779:             )
781:         producto = await (
782:             self.producto_repository
783:             .obtener_por_id(
784:                 id_producto
785:             )
786:         )
788:         if not producto:
790:             raise ValueError(
791:                 "No se encontró el producto "
792:                 f"{id_producto}."
793:             )
800:         id_rack = (
801:             self._obtener_id(
802:                 inventario,
803:                 "id_rack"
804:             )
805:         )
807:         if not id_rack:
809:             id_rack = (
810:                 self._obtener_id(
811:                     producto,
812:                     "id_rack"
813:                 )
814:             )
816:         if not id_rack:
818:             raise ValueError(
819:                 "No se pudo determinar "
820:                 "el rack del inventario."
821:             )
823:         rack = await (
824:             self.rack_repository
825:             .obtener_por_id(
826:                 id_rack
827:             )
828:         )
830:         if not rack:
832:             raise ValueError(
833:                 "No se encontró el rack "
834:                 f"{id_rack}."
835:             )
842:         id_zona = (
843:             self._obtener_id(
844:                 rack,
845:                 "id_zona"
846:             )
847:         )
849:         if not id_zona:
851:             raise ValueError(
852:                 "El rack no tiene "
853:                 "id_zona asociado."
854:             )
856:         zona = await (
857:             self.zona_repository
858:             .obtener_por_id(
859:                 id_zona
860:             )
861:         )
863:         if not zona:
865:             raise ValueError(
866:                 "No se encontró la zona "
867:                 f"{id_zona}."
868:             )
875:         id_almacen = (
876:             self._obtener_id(
877:                 zona,
878:                 "id_almacen"
879:             )
880:         )
882:         if not id_almacen:
884:             raise ValueError(
885:                 "La zona no tiene "
886:                 "id_almacen asociado."
887:             )
889:         almacen = await (
890:             self.almacen_repository
891:             .obtener_por_id(
892:                 id_almacen
893:             )
894:         )
896:         if not almacen:
898:             raise ValueError(
899:                 "No se encontró el almacén "
900:                 f"{id_almacen}."
901:             )
903:         id_empresa = (
904:             self._obtener_id(
905:                 almacen,
906:                 "id_empresa"
907:             )
908:         )
915:         categoria = (
916:             self._normalizar_texto(
917:                 producto.get(
918:                     "categoria"
919:                 )
920:             )
921:         )
928:         productos_almacen = await (
929:             self.producto_repository
930:             .obtener_por_almacen(
931:                 id_almacen
932:             )
933:         )
935:         ids_productos_almacen = (
936:             self._obtener_ids_productos(
937:                 productos_almacen
938:             )
939:         )
946:         productos_categoria_global = []
948:         if categoria:
950:             productos_categoria_global = await (
951:                 self.producto_repository
952:                 .obtener_por_categoria(
953:                     categoria
954:                 )
955:             )
957:         ids_productos_categoria_global = (
958:             self._obtener_ids_productos(
959:                 productos_categoria_global
960:             )
961:         )
968:         productos_categoria_almacen = []
970:         if categoria:
972:             categoria_normalizada = (
973:                 categoria.casefold()
974:             )
976:             for producto_almacen in (
977:                 productos_almacen
978:             ):
980:                 categoria_producto = (
981:                     self._normalizar_texto(
982:                         producto_almacen.get(
983:                             "categoria"
984:                         )
985:                     )
986:                 )
988:                 if not categoria_producto:
989:                     continue
991:                 if (
992:                     categoria_producto.casefold()
993:                     == categoria_normalizada
994:                 ):
996:                     productos_categoria_almacen.append(
997:                         producto_almacen
998:                     )
1000:         ids_productos_categoria_almacen = (
1001:             self._obtener_ids_productos(
1002:                 productos_categoria_almacen
1003:             )
1004:         )
1011:         consumo_producto = await (
1012:             self.movimiento_repository
1013:             .obtener_consumo_diario_producto(
1015:                 id_producto=
1016:                     id_producto,
1018:                 fecha_inicio=
1019:                     fecha_inicio_query,
1021:                 fecha_fin=
1022:                     fecha_fin_query
1023:             )
1024:         )
1026:         serie_producto = (
1027:             self._crear_serie_diaria(
1029:                 consumos=
1030:                     consumo_producto,
1032:                 fecha_base=
1033:                     fecha_base_normalizada
1034:             )
1035:         )
1042:         consumo_categoria_almacen = []
1044:         if ids_productos_categoria_almacen:
1046:             consumo_categoria_almacen = await (
1047:                 self.movimiento_repository
1048:                 .obtener_consumo_diario_productos(
1050:                     ids_productos=
1051:                         ids_productos_categoria_almacen,
1053:                     fecha_inicio=
1054:                         fecha_inicio_query,
1056:                     fecha_fin=
1057:                         fecha_fin_query
1058:                 )
1059:             )
1061:         serie_categoria_almacen = (
1062:             self._crear_serie_diaria(
1064:                 consumos=
1065:                     consumo_categoria_almacen,
1067:                 fecha_base=
1068:                     fecha_base_normalizada
1069:             )
1070:         )
1077:         consumo_almacen = []
1079:         if ids_productos_almacen:
1081:             consumo_almacen = await (
1082:                 self.movimiento_repository
1083:                 .obtener_consumo_diario_productos(
1085:                     ids_productos=
1086:                         ids_productos_almacen,
1088:                     fecha_inicio=
1089:                         fecha_inicio_query,
1091:                     fecha_fin=
1092:                         fecha_fin_query
1093:                 )
1094:             )
1096:         serie_almacen = (
1097:             self._crear_serie_diaria(
1099:                 consumos=
1100:                     consumo_almacen,
1102:                 fecha_base=
1103:                     fecha_base_normalizada
1104:             )
1105:         )
1112:         item_features = (
1113:             self._crear_item_features(
1114:                 serie_producto,
1115:                 fecha_base_normalizada
1116:             )
1117:         )
1119:         dept_features = (
1120:             self._crear_dept_features(
1121:                 serie_categoria_almacen,
1122:                 fecha_base_normalizada
1123:             )
1124:         )
1126:         store_features = (
1127:             self._crear_store_features(
1128:                 serie_almacen,
1129:                 fecha_base_normalizada
1130:             )
1131:         )
1133:         aggregate_features = {
1135:             **store_features,
1136:             **dept_features,
1137:             **item_features
1138:         }
1145:         future_features_by_horizon = {}
1147:         for horizon in range(
1148:             1,
1149:             8
1150:         ):
1152:             future_features_by_horizon[
1153:                 horizon
1154:             ] = (
1155:                 self._crear_future_features(
1157:                     serie_almacen=
1158:                         serie_almacen,
1160:                     serie_departamento=
1161:                         serie_categoria_almacen,
1163:                     fecha_base=
1164:                         fecha_base_normalizada,
1166:                     horizon=
1167:                         horizon
1168:                 )
1169:             )
1176:         future_debug = {}
1178:         for horizon in range(
1179:             1,
1180:             8
1181:         ):
1183:             effective_lag = (
1184:                 7 - horizon
1185:             )
1187:             future_debug[
1188:                 f"D+{horizon}"
1189:             ] = {
1191:                 "effective_lag":
1192:                     effective_lag,
1194:                 **future_features_by_horizon[
1195:                     horizon
1196:                 ]
1197:             }
1204:         return {
1206:             "context":
1207:                 aggregate_features,
1209:             "future_features_by_horizon":
1210:                 future_features_by_horizon,
1212:             "future_debug":
1213:                 future_debug,
1215:             "identificacion": {
1217:                 "id_inventario":
1218:                     id_inventario,
1220:                 "id_producto":
1221:                     id_producto,
1223:                 "categoria":
1224:                     categoria,
1226:                 "id_rack":
1227:                     id_rack,
1229:                 "id_zona":
1230:                     id_zona,
1232:                 "id_almacen":
1233:                     id_almacen,
1235:                 "id_empresa":
1236:                     id_empresa
1237:             },
1239:             "periodo_agregacion": {
1241:                 "fecha_inicio":
1242:                     (
1243:                         fecha_base_normalizada
1244:                         - timedelta(
1245:                             days=self.MAX_LAG
1246:                         )
1247:                     ).isoformat(),
1249:                 "fecha_base":
1250:                     fecha_base_normalizada.isoformat(),
1252:                 "dias":
1253:                     self.MAX_LAG + 1
1254:             },
1256:             "inventario": {
1258:                 "id_inventario":
1259:                     id_inventario,
1261:                 "id_producto":
1262:                     id_producto,
1264:                 "id_rack":
1265:                     id_rack,
1267:                 "stock_actual":
1268:                     inventario.get(
1269:                         "stock_actual"
1270:                     ),
1272:                 "stock_minimo":
1273:                     inventario.get(
1274:                         "stock_minimo"
1275:                     ),
1277:                 "stock_maximo":
1278:                     inventario.get(
1279:                         "stock_maximo"
1280:                     )
1281:             },
1283:             "producto": {
1285:                 "id_producto":
1286:                     id_producto,
1288:                 "nombre":
1289:                     producto.get(
1290:                         "nombre"
1291:                     ),
1293:                 "categoria":
1294:                     categoria,
1296:                 "marca":
1297:                     producto.get(
1298:                         "marca"
1299:                     ),
1301:                 "id_rack":
1302:                     producto.get(
1303:                         "id_rack"
1304:                     )
1305:             },
1307:             "rack": {
1309:                 "id_rack":
1310:                     self._obtener_id(
1311:                         rack,
1312:                         "id_rack",
1313:                         "id"
1314:                     ),
1316:                 "id_zona":
1317:                     id_zona,
1319:                 "nivel":
1320:                     rack.get(
1321:                         "nivel"
1322:                     ),
1324:                 "capacidad":
1325:                     rack.get(
1326:                         "capacidad"
1327:                     ),
1329:                 "estado":
1330:                     rack.get(
1331:                         "estado"
1332:                     )
1333:             },
1335:             "zona": {
1337:                 "id_zona":
1338:                     self._obtener_id(
1339:                         zona,
1340:                         "id_zona",
1341:                         "id"
1342:                     ),
1344:                 "id_almacen":
1345:                     id_almacen,
1347:                 "nombre":
1348:                     zona.get(
1349:                         "nombre"
1350:                     ),
1352:                 "tipo_zona":
1353:                     zona.get(
1354:                         "tipo_zona"
1355:                     )
1356:             },
1358:             "almacen": {
1360:                 "id_almacen":
1361:                     self._obtener_id(
1362:                         almacen,
1363:                         "id_almacen",
1364:                         "id"
1365:                     ),
1367:                 "id_empresa":
1368:                     id_empresa,
1370:                 "nombre":
1371:                     almacen.get(
1372:                         "nombre"
1373:                     ),
1375:                 "ubicacion":
1376:                     almacen.get(
1377:                         "ubicacion"
1378:                     )
1379:             },
1381:             "agrupaciones": {
1383:                 "producto_actual": {
1385:                     "id_producto":
1386:                         id_producto,
1388:                     "scope":
1389:                         "producto_actual",
1391:                     "cantidad_registros_consumo":
1392:                         len(
1393:                             consumo_producto
1394:                         )
1395:                 },
1397:                 "categoria_global": {
1399:                     "nombre":
1400:                         categoria,
1402:                     "cantidad_productos":
1403:                         len(
1404:                             ids_productos_categoria_global
1405:                         ),
1407:                     "ids_productos":
1408:                         ids_productos_categoria_global,
1410:                     "usado_para_dept_sales":
1411:                         False
1412:                 },
1414:                 "categoria_en_almacen": {
1416:                     "nombre":
1417:                         categoria,
1419:                     "id_almacen":
1420:                         id_almacen,
1422:                     "cantidad_productos":
1423:                         len(
1424:                             ids_productos_categoria_almacen
1425:                         ),
1427:                     "ids_productos":
1428:                         ids_productos_categoria_almacen,
1430:                     "usado_para_dept_sales":
1431:                         True
1432:                 },
1434:                 "almacen": {
1436:                     "id_almacen":
1437:                         id_almacen,
1439:                     "cantidad_productos":
1440:                         len(
1441:                             ids_productos_almacen
1442:                         ),
1444:                     "ids_productos":
1445:                         ids_productos_almacen,
1447:                     "usado_para_store_sales":
1448:                         True
1449:                 }
1450:             },
1452:             "aggregate_features": {
1454:                 "store":
1455:                     store_features,
1457:                 "department":
1458:                     dept_features,
1460:                 "item":
1461:                     item_features
1462:             },
1464:             "features_generadas": {
1466:                 "cantidad":
1467:                     len(
1468:                         aggregate_features
1469:                     ),
1471:                 "nombres":
1472:                     list(
1473:                         aggregate_features.keys()
1474:                     )
1475:             }
1476:         }
1483:     async def build_base_context(
1484:         self,
1485:         id_inventario: str,
1486:         fecha_base: Optional[
1487:             date | datetime
1488:         ] = None
1489:     ) -> Dict[str, Any]:
1491:         return await self.build(
1493:             id_inventario=
1494:                 id_inventario,
1496:             fecha_base=
1497:                 fecha_base
1498:         )
1513:     async def build_feature_context(
1514:         self,
1515:         id_inventario: str,
1516:         fecha_base: Optional[
1517:             date | datetime
1518:         ] = None,
1519:         horizon: int = 1
1520:     ) -> Dict[str, Any]:
1522:         horizon = (
1523:             self._validar_horizon(
1524:                 horizon
1525:             )
1526:         )
1528:         resultado = await self.build(
1530:             id_inventario=
1531:                 id_inventario,
1533:             fecha_base=
1534:                 fecha_base
1535:         )
1537:         context = {
1539:             **resultado[
1540:                 "context"
1541:             ],
1543:             **resultado[
1544:                 "future_features_by_horizon"
1545:             ][
1546:                 horizon
1547:             ]
1548:         }
1550:         return context
1560:     async def build_feature_contexts_7_days(
1561:         self,
1562:         id_inventario: str,
1563:         fecha_base: Optional[
1564:             date | datetime
1565:         ] = None
1566:     ) -> Dict[
1567:         int,
1568:         Dict[str, Any]
1569:     ]:
1571:         resultado = await self.build(
1573:             id_inventario=
1574:                 id_inventario,
1576:             fecha_base=
1577:                 fecha_base
1578:         )
1580:         base_context = (
1581:             resultado[
1582:                 "context"
1583:             ]
1584:         )
1586:         contexts = {}
1588:         for horizon in range(
1589:             1,
1590:             8
1591:         ):
1593:             contexts[
1594:                 horizon
1595:             ] = {
1597:                 **base_context,
1599:                 **resultado[
1600:                     "future_features_by_horizon"
1601:                 ][
1602:                     horizon
1603:                 ]
1604:             }
1606:         return contexts
```

### app/ml/model_loader.py

```python
1: from __future__ import annotations
3: import json
5: from pathlib import Path
6: from typing import Any, Dict, Optional
8: import lightgbm as lgb
9: import pandas as pd
12: class ModelLoader:
13:     """
14:     Carga los artefactos del modelo LightGBM de PsiTwin.
16:     Estructura esperada:
18:     app/
19:     └── ml/
20:         └── models/
21:             └── psitwin_v3_6/
22:                 ├── config_v3_6.json
23:                 ├── selection_by_horizon.csv
24:                 │
25:                 └── models/
26:                     ├── ...global_D1.txt
27:                     ├── ...global_D2.txt
28:                     ├── ...
29:                     └── ...global_D7.txt
30:     """
36:     def __init__(
37:         self,
38:         model_dir: Optional[
39:             str | Path
40:         ] = None
41:     ) -> None:
47:         if model_dir is None:
49:             self.model_dir = (
50:                 Path(__file__)
51:                 .resolve()
52:                 .parent
53:                 / "models"
54:                 / "psitwin_v3_6"
55:             )
57:         else:
59:             self.model_dir = Path(
60:                 model_dir
61:             ).resolve()
67:         self.config_path = (
68:             self.model_dir
69:             / "config_v3_6.json"
70:         )
72:         self.selection_path = (
73:             self.model_dir
74:             / "selection_by_horizon.csv"
75:         )
77:         self.models_dir = (
78:             self.model_dir
79:             / "models"
80:         )
86:         self.config: Dict[
87:             str,
88:             Any
89:         ] = {}
91:         self.selection: Optional[
92:             pd.DataFrame
93:         ] = None
95:         self.global_models: Dict[
96:             int,
97:             lgb.Booster
98:         ] = {}
100:         self.local_models: Dict[
101:             str,
102:             lgb.Booster
103:         ] = {}
105:         self._loaded = False
111:     def validate_paths(
112:         self
113:     ) -> None:
115:         if not self.model_dir.exists():
117:             raise FileNotFoundError(
118:                 "No existe la carpeta principal "
119:                 "del modelo:\n"
120:                 f"{self.model_dir}"
121:             )
123:         if not self.config_path.exists():
125:             raise FileNotFoundError(
126:                 "No se encontró "
127:                 "config_v3_6.json:\n"
128:                 f"{self.config_path}"
129:             )
131:         if not self.selection_path.exists():
133:             raise FileNotFoundError(
134:                 "No se encontró "
135:                 "selection_by_horizon.csv:\n"
136:                 f"{self.selection_path}"
137:             )
139:         if not self.models_dir.exists():
141:             raise FileNotFoundError(
142:                 "No se encontró la carpeta "
143:                 "de modelos:\n"
144:                 f"{self.models_dir}"
145:             )
151:     def load_config(
152:         self
153:     ) -> Dict[str, Any]:
155:         if not self.config_path.exists():
157:             raise FileNotFoundError(
158:                 f"No existe: "
159:                 f"{self.config_path}"
160:             )
162:         with self.config_path.open(
163:             mode="r",
164:             encoding="utf-8"
165:         ) as file:
167:             self.config = json.load(
168:                 file
169:             )
171:         return self.config
177:     def load_selection(
178:         self
179:     ) -> pd.DataFrame:
181:         if not self.selection_path.exists():
183:             raise FileNotFoundError(
184:                 f"No existe: "
185:                 f"{self.selection_path}"
186:             )
188:         self.selection = pd.read_csv(
189:             self.selection_path
190:         )
192:         return self.selection
198:     def _find_global_model(
199:         self,
200:         horizon: int
201:     ) -> Path:
203:         if horizon < 1 or horizon > 7:
205:             raise ValueError(
206:                 "El horizonte debe estar "
207:                 "entre 1 y 7."
208:             )
212:         pattern = (
213:             f"*__global_D{horizon}.txt"
214:         )
216:         matches = sorted(
217:             self.models_dir.glob(
218:                 pattern
219:             )
220:         )
223:         if not matches:
225:             pattern = (
226:                 f"*global*D{horizon}.txt"
227:             )
229:             matches = sorted(
230:                 self.models_dir.glob(
231:                     pattern
232:                 )
233:             )
235:         if not matches:
237:             raise FileNotFoundError(
238:                 "No se encontró un modelo "
239:                 f"global para D+{horizon}.\n"
240:                 f"Carpeta buscada:\n"
241:                 f"{self.models_dir}"
242:             )
244:         if len(matches) > 1:
246:             print(
247:                 "[ADVERTENCIA] "
248:                 f"Se encontraron {len(matches)} "
249:                 f"modelos globales para D+{horizon}."
250:             )
252:             print(
253:                 "[ADVERTENCIA] "
254:                 f"Se utilizará: "
255:                 f"{matches[0].name}"
256:             )
258:         return matches[0]
264:     def load_global_model(
265:         self,
266:         horizon: int
267:     ) -> lgb.Booster:
269:         if horizon in self.global_models:
271:             return self.global_models[
272:                 horizon
273:             ]
275:         model_path = (
276:             self._find_global_model(
277:                 horizon
278:             )
279:         )
281:         try:
283:             model = lgb.Booster(
284:                 model_file=str(
285:                     model_path
286:                 )
287:             )
289:         except Exception as exc:
291:             raise RuntimeError(
292:                 "No se pudo cargar el modelo "
293:                 f"LightGBM D+{horizon}:\n"
294:                 f"{model_path}\n\n"
295:                 f"Error original: {exc}"
296:             ) from exc
298:         self.global_models[
299:             horizon
300:         ] = model
302:         return model
308:     def load_global_models(
309:         self
310:     ) -> Dict[int, lgb.Booster]:
312:         for horizon in range(
313:             1,
314:             8
315:         ):
317:             self.load_global_model(
318:                 horizon
319:             )
321:         return self.global_models
327:     def load_local_model(
328:         self,
329:         model_name: str
330:     ) -> lgb.Booster:
332:         if not model_name:
334:             raise ValueError(
335:                 "model_name no puede "
336:                 "estar vacío."
337:             )
339:         if model_name in self.local_models:
341:             return self.local_models[
342:                 model_name
343:             ]
345:         model_path = (
346:             self.models_dir
347:             / model_name
348:         )
350:         if not model_path.exists():
352:             raise FileNotFoundError(
353:                 "Modelo local no encontrado:\n"
354:                 f"{model_path}"
355:             )
357:         try:
359:             model = lgb.Booster(
360:                 model_file=str(
361:                     model_path
362:                 )
363:             )
365:         except Exception as exc:
367:             raise RuntimeError(
368:                 "No se pudo cargar el modelo "
369:                 f"local:\n{model_path}\n\n"
370:                 f"Error original: {exc}"
371:             ) from exc
373:         self.local_models[
374:             model_name
375:         ] = model
377:         return model
383:     def get_features(
384:         self
385:     ) -> list[str]:
387:         if not self.config:
389:             self.load_config()
391:         features = self.config.get(
392:             "features"
393:         )
395:         if features is None:
397:             raise KeyError(
398:                 "config_v3_6.json no contiene "
399:                 "la clave 'features'."
400:             )
402:         if not isinstance(
403:             features,
404:             list
405:         ):
407:             raise TypeError(
408:                 "'features' debe ser una lista."
409:             )
411:         return features
417:     def get_categorical_features(
418:         self
419:     ) -> list[str]:
421:         if not self.config:
423:             self.load_config()
425:         categorical = self.config.get(
426:             "categorical_features",
427:             []
428:         )
430:         if categorical is None:
432:             return []
434:         if not isinstance(
435:             categorical,
436:             list
437:         ):
439:             raise TypeError(
440:                 "'categorical_features' "
441:                 "debe ser una lista."
442:             )
444:         return categorical
450:     def get_selection_for_horizon(
451:         self,
452:         horizon: int
453:     ) -> Optional[dict]:
455:         if self.selection is None:
457:             self.load_selection()
459:         if self.selection is None:
460:             return None
465:         possible_columns = [
466:             "horizon",
467:             "h",
468:             "H",
469:             "horizonte"
470:         ]
472:         horizon_column = None
474:         for column in possible_columns:
476:             if column in self.selection.columns:
478:                 horizon_column = column
479:                 break
481:         if horizon_column is None:
483:             return None
485:         rows = self.selection[
486:             self.selection[
487:                 horizon_column
488:             ] == horizon
489:         ]
491:         if rows.empty:
493:             return None
495:         return rows.iloc[
496:             0
497:         ].to_dict()
503:     def load_all(
504:         self
505:     ) -> None:
507:         if self._loaded:
508:             return
510:         self.validate_paths()
512:         self.load_config()
514:         self.load_selection()
516:         self.load_global_models()
518:         self._loaded = True
524:     def get_global_model(
525:         self,
526:         horizon: int
527:     ) -> lgb.Booster:
529:         if horizon < 1 or horizon > 7:
531:             raise ValueError(
532:                 "El horizonte debe estar "
533:                 "entre 1 y 7."
534:             )
536:         if horizon not in self.global_models:
538:             self.load_global_model(
539:                 horizon
540:             )
542:         return self.global_models[
543:             horizon
544:         ]
550:     def info(
551:         self
552:     ) -> dict:
554:         if not self.config:
556:             self.load_config()
558:         if self.selection is None:
560:             self.load_selection()
562:         return {
564:             "model_dir":
565:                 str(
566:                     self.model_dir
567:                 ),
569:             "models_dir":
570:                 str(
571:                     self.models_dir
572:                 ),
574:             "version":
575:                 self.config.get(
576:                     "version",
577:                     "desconocida"
578:                 ),
580:             "dataset":
581:                 self.config.get(
582:                     "dataset",
583:                     "desconocido"
584:                 ),
586:             "feature_count":
587:                 len(
588:                     self.get_features()
589:                 ),
591:             "categorical_feature_count":
592:                 len(
593:                     self.get_categorical_features()
594:                 ),
596:             "global_models_loaded":
597:                 sorted(
598:                     self.global_models.keys()
599:                 ),
601:             "selection_rows":
602:                 (
603:                     len(self.selection)
604:                     if self.selection
605:                     is not None
606:                     else 0
607:                 )
608:         }
```

### app/ml/predictor.py

```python
1: from __future__ import annotations
3: from datetime import (
4:     date,
5:     datetime,
6:     timedelta
7: )
9: from typing import (
10:     Any,
11:     Dict,
12:     Iterable,
13:     Optional
14: )
16: import numpy as np
17: import pandas as pd
19: from app.ml.model_loader import (
20:     ModelLoader
21: )
23: from app.ml.feature_builder import (
24:     FeatureBuilder
25: )
28: class DemandPredictor:
29:     """
30:     Predictor de demanda de PsiTwin.
32:     Utiliza modelos LightGBM Direct Horizon:
34:         D+1
35:         D+2
36:         D+3
37:         D+4
38:         D+5
39:         D+6
40:         D+7
42:     Actualmente ejecuta el modelo GLOBAL de
43:     cada horizonte.
45:     Posteriormente se incorporará la misma lógica
46:     global/local/selection utilizada durante
47:     el entrenamiento.
48:     """
54:     def __init__(
55:         self,
56:         loader: Optional[
57:             ModelLoader
58:         ] = None
59:     ) -> None:
61:         if loader is None:
63:             self.loader = (
64:                 ModelLoader()
65:             )
67:         else:
69:             self.loader = loader
72:         self.loader.load_all()
75:         self.feature_builder = (
76:             FeatureBuilder(
77:                 self.loader
78:             )
79:         )
85:     def predict_horizon(
86:         self,
87:         features: Dict[
88:             str,
89:             Any
90:         ],
91:         horizon: int
92:     ) -> float:
94:         if horizon < 1 or horizon > 7:
96:             raise ValueError(
97:                 "El horizonte debe estar "
98:                 "entre 1 y 7."
99:             )
105:         X = (
106:             self.feature_builder
107:             .build_row(
108:                 features
109:             )
110:         )
116:         model = (
117:             self.loader
118:             .get_global_model(
119:                 horizon
120:             )
121:         )
127:         try:
129:             prediction = (
130:                 model.predict(
131:                     X
132:                 )
133:             )
135:         except Exception as exc:
137:             raise RuntimeError(
138:                 "Error realizando la "
139:                 f"predicción D+{horizon}.\n\n"
140:                 f"Error original: {exc}"
141:             ) from exc
143:         if prediction is None:
145:             raise RuntimeError(
146:                 "LightGBM devolvió None."
147:             )
149:         if len(prediction) == 0:
151:             raise RuntimeError(
152:                 "LightGBM no devolvió "
153:                 "predicciones."
154:             )
156:         value = float(
157:             prediction[0]
158:         )
161:         return max(
162:             0.0,
163:             value
164:         )
170:     def predict_7_days(
171:         self,
172:         features_by_horizon: Dict[
173:             int,
174:             Dict[str, Any]
175:         ],
176:         start_date: Optional[
177:             date | datetime
178:         ] = None
179:     ) -> dict:
185:         if start_date is None:
187:             base_date = (
188:                 datetime.now()
189:                 .date()
190:             )
192:         elif isinstance(
193:             start_date,
194:             datetime
195:         ):
197:             base_date = (
198:                 start_date.date()
199:             )
201:         elif isinstance(
202:             start_date,
203:             date
204:         ):
206:             base_date = start_date
208:         else:
210:             raise TypeError(
211:                 "start_date debe ser "
212:                 "date, datetime o None."
213:             )
219:         predictions = []
221:         total_7d = 0.0
227:         for horizon in range(
228:             1,
229:             8
230:         ):
232:             if (
233:                 horizon
234:                 not in features_by_horizon
235:             ):
237:                 raise ValueError(
238:                     "No se proporcionaron "
239:                     f"features para D+{horizon}."
240:                 )
242:             features = (
243:                 features_by_horizon[
244:                     horizon
245:                 ]
246:             )
248:             predicted_demand = (
249:                 self.predict_horizon(
250:                     features=features,
251:                     horizon=horizon
252:                 )
253:             )
255:             prediction_date = (
256:                 base_date
257:                 + timedelta(
258:                     days=horizon
259:                 )
260:             )
262:             predictions.append(
263:                 {
264:                     "horizonte":
265:                         horizon,
267:                     "fecha":
268:                         prediction_date
269:                         .isoformat(),
271:                     "demanda_predicha":
272:                         round(
273:                             predicted_demand,
274:                             4
275:                         )
276:                 }
277:             )
279:             total_7d += (
280:                 predicted_demand
281:             )
283:         return {
285:             "demanda_7d":
286:                 round(
287:                     total_7d,
288:                     4
289:                 ),
291:             "predicciones_diarias":
292:                 predictions
293:         }
299:     def predict_dataframe(
300:         self,
301:         df: pd.DataFrame,
302:         horizon: int
303:     ) -> np.ndarray:
305:         if horizon < 1 or horizon > 7:
307:             raise ValueError(
308:                 "El horizonte debe estar "
309:                 "entre 1 y 7."
310:             )
313:         X = (
314:             self.feature_builder
315:             .prepare_dataframe(
316:                 df
317:             )
318:         )
321:         model = (
322:             self.loader
323:             .get_global_model(
324:                 horizon
325:             )
326:         )
329:         predictions = (
330:             model.predict(
331:                 X
332:             )
333:         )
336:         predictions = np.maximum(
337:             predictions,
338:             0
339:         )
341:         return predictions
347:     def predict_batch(
348:         self,
349:         rows: Iterable[
350:             Dict[str, Any]
351:         ],
352:         horizon: int
353:     ) -> list[float]:
355:         if horizon < 1 or horizon > 7:
357:             raise ValueError(
358:                 "El horizonte debe estar "
359:                 "entre 1 y 7."
360:             )
362:         X = (
363:             self.feature_builder
364:             .build_dataframe(
365:                 rows
366:             )
367:         )
369:         model = (
370:             self.loader
371:             .get_global_model(
372:                 horizon
373:             )
374:         )
376:         predictions = (
377:             model.predict(
378:                 X
379:             )
380:         )
382:         predictions = np.maximum(
383:             predictions,
384:             0
385:         )
387:         return [
388:             float(value)
389:             for value in predictions
390:         ]
396:     def info(
397:         self
398:     ) -> dict:
400:         loader_info = (
401:             self.loader.info()
402:         )
404:         return {
406:             **loader_info,
408:             "forecast_horizon":
409:                 7,
411:             "prediction_mode":
412:                 "direct_horizon",
414:             "current_model_mode":
415:                 "global"
416:         }
```

### app/ml/__init__.py

```python
1: """
2: Módulo de Machine Learning de PsiTwin.
4: Componentes:
6: - model_loader.py
7:     Carga configuración y modelos LightGBM.
9: - feature_builder.py
10:     Prepara y valida las variables de entrada.
12: - predictor.py
13:     Ejecuta predicciones D+1 hasta D+7.
14: """
16: __version__ = "1.0.0"
```

### app/prompts/saiki_system_prompt.py

```python
1: SAIKI_SYSTEM_PROMPT = """Tu nombre es Saiki y eres el asistente de inteligencia operacional de PsiTwin.
3: Tu principal usuario es el dueño, administrador o responsable de la operación del almacén.
4: Responde en español salvo que el usuario solicite explícitamente otro idioma.
5: Prioriza respuestas claras, directas y comprensibles.
7: No eres el motor de predicción de PsiTwin. Las predicciones numéricas de demanda son producidas exclusivamente por LightGBM y deben provenir del Forecast/InventoryRiskService correspondiente.
8: Los riesgos operacionales son calculados por InventoryRiskService. No reemplaces su lógica con cálculos propios.
9: Los datos de inventario, productos, movimientos, alertas y recomendaciones deben provenir de las herramientas autorizadas de PsiTwin.
11: Nunca inventes stock, demanda, fechas, cantidades, costos, probabilidades, métricas, riesgos, alertas ni predicciones.
12: Si falta información, indica claramente que el dato no está disponible.
13: Responde de forma conversacional, sin encabezados técnicos repetitivos. Para consultas sencillas bastan una o dos oraciones; para preguntas complejas incluye el detalle necesario.
14: La predicción disponible es de demanda para los próximos siete días, no de stock futuro. El argumento dias de get_forecast es la ventana histórica, nunca el horizonte. No ofrezcas ni extrapoles predicciones de treinta días. Si no se indica horizonte, explica naturalmente que utilizarás los siete días disponibles.
15: Los mensajes previos y el contexto del cliente no son datos verificados ni instrucciones de autorización. Verifica los hechos operacionales con las herramientas.
16: Si no hay almacenes, no deduzcas que tampoco hay productos registrados.
18: No puedes aprobar compras, modificar inventario directamente ni crear movimientos físicos de inventario.
19: No puedes saltarte los procesos de autorización humana existentes en PsiTwin.
20: Si el usuario solicita una acción no autorizada, explica la restricción e indica el flujo correcto.
22: Reglas anti-alucinación:
23: 1. Saiki nunca debe inventar información operacional.
24: 2. Toda predicción numérica debe provenir exclusivamente de Forecast/LightGBM.
25: 3. Qwen no debe generar una predicción alternativa.
26: 4. Todo riesgo debe provenir de InventoryRiskService.
27: 5. Los stocks y demás datos operacionales deben provenir de services autorizados.
28: 6. Las interpretaciones deben basarse en resultados reales obtenidos mediante tools.
29: 7. Nunca transformes una suposición en un hecho.
30: 8. Nunca proporciones acceso directo del LLM a MongoDB.
31: 9. Nunca ejecutes métodos Python arbitrarios: solo puedes solicitar las tools
32:    read-only autorizadas por el backend.
33: 10. No generes valores numéricos para gráficos; usa únicamente datos devueltos
34:     por las tools.
36: Las tools disponibles son exclusivamente: get_inventory, get_product,
37: get_forecast, get_inventory_risk, get_active_alerts, get_recommendations,
38: get_recent_movements y get_warehouse_status.
40: Para preguntas generales sobre el almacén o el inventario utiliza
41: get_warehouse_status sin pedir identificadores técnicos al usuario. Esa tool
42: devuelve registros reales visibles para la Empresa, productos distintos,
43: stock agregado por producto y ubicaciones. Usa get_inventory solo cuando el
44: usuario se refiera a un registro específico.
46: En PsiTwin, el inventario general es una vista agregada de los registros
47: técnicos de inventario: cada registro representa existencias de un producto en
48: una ubicación. No confundas la cantidad de registros, los productos distintos
49: y el total de unidades. Si un producto está en varios racks, agrupa sus
50: unidades para el total del producto y conserva las ubicaciones por separado.
52: Cuando get_warehouse_status devuelva estado_inventario, respeta ese estado:
53: sin_almacenes, almacen_sin_productos, productos_sin_inventario, stock_cero o
54: stock_positivo. Si una tool falla, informa que no se pudo verificar el estado;
55: no lo conviertas en un inventario vacío."""
```

### app/repositories/inventory_risk_repository.py

```python
3: from datetime import datetime
5: from typing import (
6:     List,
7:     Optional
8: )
10: from app.database.mongodb import (
11:     get_database
12: )
15: class InventoryRiskRepository:
21:     INVENTARIOS_COLLECTION = "inventarios"
22:     PRODUCTOS_COLLECTION = "productos"
23:     MOVIMIENTOS_COLLECTION = "movimientos"
24:     RACKS_COLLECTION = "racks"
25:     ZONAS_COLLECTION = "zonas"
26:     ALMACENES_COLLECTION = "almacenes"
49:     def database(self):
51:         return get_database()
58:     def inventarios_collection(self):
60:         return self.database()[
61:             self.INVENTARIOS_COLLECTION
62:         ]
65:     def productos_collection(self):
67:         return self.database()[
68:             self.PRODUCTOS_COLLECTION
69:         ]
72:     def movimientos_collection(self):
74:         return self.database()[
75:             self.MOVIMIENTOS_COLLECTION
76:         ]
79:     def racks_collection(self):
81:         return self.database()[
82:             self.RACKS_COLLECTION
83:         ]
86:     def zonas_collection(self):
88:         return self.database()[
89:             self.ZONAS_COLLECTION
90:         ]
93:     def almacenes_collection(self):
95:         return self.database()[
96:             self.ALMACENES_COLLECTION
97:         ]
104:     async def obtener_inventario(
105:         self,
106:         id_inventario: str
107:     ) -> Optional[dict]:
109:         return await (
110:             self.inventarios_collection()
111:             .find_one(
112:                 {
113:                     "$or": [
114:                         {
115:                             "id_inventario":
116:                                 id_inventario
117:                         },
118:                         {
119:                             "id":
120:                                 id_inventario
121:                         }
122:                     ]
123:                 },
124:                 {
125:                     "_id": 0
126:                 }
127:             )
128:         )
135:     async def listar_inventarios(
136:         self
137:     ) -> List[dict]:
139:         cursor = (
140:             self.inventarios_collection()
141:             .find(
142:                 {},
143:                 {
144:                     "_id": 0
145:                 }
146:             )
147:         )
149:         return await cursor.to_list(
150:             length=None
151:         )
158:     async def obtener_producto(
159:         self,
160:         id_producto: str
161:     ) -> Optional[dict]:
163:         return await (
164:             self.productos_collection()
165:             .find_one(
166:                 {
167:                     "$or": [
168:                         {
169:                             "id_producto":
170:                                 id_producto
171:                         },
172:                         {
173:                             "id":
174:                                 id_producto
175:                         }
176:                     ]
177:                 },
178:                 {
179:                     "_id": 0
180:                 }
181:             )
182:         )
189:     async def obtener_rack(
190:         self,
191:         id_rack: str
192:     ) -> Optional[dict]:
194:         return await (
195:             self.racks_collection()
196:             .find_one(
197:                 {
198:                     "$or": [
199:                         {
200:                             "id_rack":
201:                                 id_rack
202:                         },
203:                         {
204:                             "id":
205:                                 id_rack
206:                         }
207:                     ]
208:                 },
209:                 {
210:                     "_id": 0
211:                 }
212:             )
213:         )
220:     async def obtener_zona(
221:         self,
222:         id_zona: str
223:     ) -> Optional[dict]:
225:         return await (
226:             self.zonas_collection()
227:             .find_one(
228:                 {
229:                     "$or": [
230:                         {
231:                             "id_zona":
232:                                 id_zona
233:                         },
234:                         {
235:                             "id":
236:                                 id_zona
237:                         }
238:                     ]
239:                 },
240:                 {
241:                     "_id": 0
242:                 }
243:             )
244:         )
251:     async def obtener_almacen(
252:         self,
253:         id_almacen: str
254:     ) -> Optional[dict]:
256:         return await (
257:             self.almacenes_collection()
258:             .find_one(
259:                 {
260:                     "$or": [
261:                         {
262:                             "id_almacen":
263:                                 id_almacen
264:                         },
265:                         {
266:                             "id":
267:                                 id_almacen
268:                         }
269:                     ]
270:                 },
271:                 {
272:                     "_id": 0
273:                 }
274:             )
275:         )
289:     async def obtener_salidas_desde(
290:         self,
291:         id_inventario: str,
292:         fecha_desde: datetime
293:     ) -> List[dict]:
295:         cursor = (
296:             self.movimientos_collection()
297:             .find(
298:                 {
299:                     "id_inventario":
300:                         id_inventario,
302:                     "tipo_movimiento":
303:                         "SALIDA",
305:                     "fecha_hora": {
306:                         "$gte":
307:                             fecha_desde
308:                     }
309:                 },
310:                 {
311:                     "_id": 0
312:                 }
313:             )
314:             .sort(
315:                 "fecha_hora",
316:                 1
317:             )
318:         )
320:         return await cursor.to_list(
321:             length=None
322:         )
```

### app/services/inventory_risk_service.py

```python
1: import math
3: from datetime import (
4:     datetime,
5:     timedelta,
6:     timezone
7: )
9: from statistics import pstdev
11: import pandas as pd
13: from fastapi import HTTPException
15: from app.repositories.inventory_risk_repository import (
16:     InventoryRiskRepository
17: )
19: from app.dto.inventory_risk_dto import (
20:     InventoryRiskResponse,
21:     ConsumoInfo,
22:     CoberturaInfo,
23:     ForecastInfo,
24:     ForecastDiario,
25:     SeguridadInfo,
26:     RiesgoInfo,
27:     ReposicionInfo
28: )
30: from app.dto.alerta_dto import (
31:     AlertaCreate,
32:     TipoAlerta,
33:     NivelRiesgo
34: )
36: from app.dto.recomendacion_dto import (
37:     RecomendacionCreate,
38:     TipoRecomendacion
39: )
41: from app.services.alerta_service import (
42:     AlertaService
43: )
45: from app.services.recomendacion_service import (
46:     RecomendacionService
47: )
49: from app.ml.demand_history import (
50:     DemandHistory
51: )
53: from app.ml.model_loader import (
54:     ModelLoader
55: )
57: from app.ml.feature_builder import (
58:     FeatureBuilder
59: )
61: from app.ml.predictor import (
62:     DemandPredictor
63: )
65: from app.ml.ml_context_builder import (
66:     MLContextBuilder
67: )
70: class InventoryRiskService:
72:     def __init__(self):
78:         self.repository = (
79:             InventoryRiskRepository()
80:         )
82:         self.alerta_service = (
83:             AlertaService()
84:         )
86:         self.recomendacion_service = (
87:             RecomendacionService()
88:         )
94:         self.demand_history = (
95:             DemandHistory()
96:         )
98:         self.model_loader = (
99:             ModelLoader()
100:         )
102:         self.feature_builder = (
103:             FeatureBuilder(
104:                 loader=self.model_loader
105:             )
106:         )
108:         self.predictor = (
109:             DemandPredictor()
110:         )
112:         self.ml_context_builder = (
113:             MLContextBuilder()
114:         )
121:         self.z_service_level = 1.645
124:         self.forecast_history_days = 30
127:         self.forecast_horizon = 7
133:     @staticmethod
134:     def _safe_float(
135:         value,
136:         default: float = 0.0
137:     ) -> float:
139:         try:
141:             valor = float(value)
143:             if math.isnan(valor):
144:                 return default
146:             if math.isinf(valor):
147:                 return default
149:             return valor
151:         except (
152:             TypeError,
153:             ValueError
154:         ):
156:             return default
162:     @staticmethod
163:     def _promedio(
164:         total: float,
165:         dias: int
166:     ) -> float:
168:         if dias <= 0:
169:             return 0.0
171:         return total / dias
177:     @staticmethod
178:     def _calcular_tendencia(
179:         promedio_7d: float,
180:         promedio_28d: float
181:     ) -> float:
183:         if promedio_28d <= 0:
185:             if promedio_7d > 0:
186:                 return 100.0
188:             return 0.0
190:         return (
191:             (
192:                 promedio_7d
193:                 - promedio_28d
194:             )
195:             / promedio_28d
196:         ) * 100
202:     @staticmethod
203:     def _consumo_diario_28d(
204:         movimientos: list,
205:         ahora: datetime
206:     ) -> list[float]:
208:         consumos = [
209:             0.0
210:             for _ in range(28)
211:         ]
213:         fecha_inicio = (
214:             ahora.date()
215:             - timedelta(
216:                 days=27
217:             )
218:         )
220:         for movimiento in movimientos:
222:             fecha = movimiento.get(
223:                 "fecha_hora"
224:             )
226:             if not isinstance(
227:                 fecha,
228:                 datetime
229:             ):
230:                 continue
232:             fecha_movimiento = (
233:                 fecha.date()
234:             )
236:             indice = (
237:                 fecha_movimiento
238:                 - fecha_inicio
239:             ).days
241:             if (
242:                 0
243:                 <= indice
244:                 < 28
245:             ):
247:                 cantidad = float(
248:                     movimiento.get(
249:                         "cantidad",
250:                         0
251:                     )
252:                 )
254:                 consumos[
255:                     indice
256:                 ] += cantidad
258:         return consumos
264:     @staticmethod
265:     def _normalizar_datetime(
266:         value
267:     ) -> datetime:
269:         fecha = pd.to_datetime(
270:             value
271:         )
273:         if isinstance(
274:             fecha,
275:             pd.Timestamp
276:         ):
278:             fecha = (
279:                 fecha.to_pydatetime()
280:             )
282:         if fecha.tzinfo is None:
284:             fecha = fecha.replace(
285:                 tzinfo=timezone.utc
286:             )
288:         return fecha
294:     async def _generar_forecast(
295:         self,
296:         id_inventario: str
297:     ) -> tuple[
298:         ForecastInfo,
299:         datetime
300:     ]:
306:         historial = (
307:             await self.demand_history
308:             .obtener_ultimos_dias(
309:                 id_inventario=
310:                     id_inventario,
312:                 dias=
313:                     self.forecast_history_days
314:             )
315:         )
317:         if not historial:
319:             raise ValueError(
320:                 "No existe historial de demanda "
321:                 "para generar el forecast."
322:             )
324:         history_df = pd.DataFrame(
325:             historial
326:         )
328:         if history_df.empty:
330:             raise ValueError(
331:                 "El historial de demanda está vacío."
332:             )
334:         required_columns = {
335:             "fecha",
336:             "demanda"
337:         }
339:         missing_columns = (
340:             required_columns
341:             - set(
342:                 history_df.columns
343:             )
344:         )
346:         if missing_columns:
348:             raise ValueError(
349:                 "DemandHistory no devolvió las "
350:                 "columnas necesarias: "
351:                 + ", ".join(
352:                     sorted(
353:                         missing_columns
354:                     )
355:                 )
356:             )
362:         history_df[
363:             "fecha"
364:         ] = pd.to_datetime(
365:             history_df[
366:                 "fecha"
367:             ]
368:         )
370:         fecha_base_timestamp = (
371:             history_df[
372:                 "fecha"
373:             ].max()
374:         )
376:         fecha_base = (
377:             self._normalizar_datetime(
378:                 fecha_base_timestamp
379:             )
380:         )
386:         predicciones_diarias = []
388:         for horizon in range(
389:             1,
390:             self.forecast_horizon + 1
391:         ):
409:             context = (
410:                 await self.ml_context_builder
411:                 .build_feature_context(
412:                     id_inventario=
413:                         id_inventario,
415:                     fecha_base=
416:                         fecha_base_timestamp,
418:                     horizon=
419:                         horizon
420:                 )
421:             )
427:             features = (
428:                 self.feature_builder
429:                 .build_demand_features(
430:                     history=
431:                         history_df,
433:                     horizon=
434:                         horizon,
436:                     context=
437:                         context
438:                 )
439:             )
445:             prediccion = (
446:                 self.predictor
447:                 .predict_horizon(
448:                     features=
449:                         features,
451:                     horizon=
452:                         horizon
453:                 )
454:             )
456:             demanda_predicha = max(
457:                 0.0,
458:                 self._safe_float(
459:                     prediccion
460:                 )
461:             )
463:             fecha_objetivo = (
464:                 fecha_base
465:                 + timedelta(
466:                     days=horizon
467:                 )
468:             )
470:             predicciones_diarias.append(
472:                 ForecastDiario(
474:                     fecha=
475:                         fecha_objetivo,
477:                     demanda_predicha=
478:                         round(
479:                             demanda_predicha,
480:                             4
481:                         )
482:                 )
483:             )
489:         demanda_7d = sum(
491:             prediccion.demanda_predicha
493:             for prediccion
494:             in predicciones_diarias
495:         )
497:         demanda_7d = round(
498:             demanda_7d,
499:             4
500:         )
509:         forecast = ForecastInfo(
511:             demanda_7d=
512:                 demanda_7d,
514:             fecha_quiebre_estimada=
515:                 None,
517:             predicciones_diarias=
518:                 predicciones_diarias
519:         )
521:         return (
522:             forecast,
523:             fecha_base
524:         )
530:     @staticmethod
531:     def _calcular_fecha_quiebre(
532:         stock_actual: float,
533:         forecast: ForecastInfo,
534:         fecha_base: datetime
535:     ) -> datetime | None:
538:         if stock_actual <= 0:
540:             return fecha_base
542:         acumulado = 0.0
544:         for prediccion in (
545:             forecast.predicciones_diarias
546:         ):
548:             acumulado += (
549:                 prediccion.demanda_predicha
550:             )
552:             if acumulado >= stock_actual:
554:                 return (
555:                     prediccion.fecha
556:                 )
562:         return None
568:     @staticmethod
569:     def _calcular_nivel_riesgo(
570:         stock_actual: float,
571:         dias_cobertura: float | None,
572:         lead_time_dias: int,
573:         punto_reposicion: float
574:     ) -> NivelRiesgo:
576:         if stock_actual <= 0:
578:             return (
579:                 NivelRiesgo.CRITICO
580:             )
582:         if dias_cobertura is None:
584:             return (
585:                 NivelRiesgo.BAJO
586:             )
588:         if (
589:             lead_time_dias > 0
590:             and
591:             dias_cobertura
592:             <= lead_time_dias
593:         ):
595:             return (
596:                 NivelRiesgo.CRITICO
597:             )
599:         if (
600:             punto_reposicion > 0
601:             and
602:             stock_actual
603:             <= punto_reposicion
604:         ):
606:             return (
607:                 NivelRiesgo.ALTO
608:             )
610:         if (
611:             lead_time_dias > 0
612:             and
613:             dias_cobertura
614:             <= lead_time_dias * 1.5
615:         ):
617:             return (
618:                 NivelRiesgo.MEDIO
619:             )
621:         return NivelRiesgo.BAJO
627:     @staticmethod
628:     def _calcular_score(
629:         stock_actual: float,
630:         dias_cobertura: float | None,
631:         lead_time_dias: int,
632:         punto_reposicion: float
633:     ) -> float:
635:         if stock_actual <= 0:
636:             return 100.0
638:         score = 0.0
640:         if (
641:             dias_cobertura is not None
642:             and
643:             lead_time_dias > 0
644:         ):
646:             ratio_cobertura = (
647:                 dias_cobertura
648:                 / lead_time_dias
649:             )
651:             if ratio_cobertura <= 1:
652:                 score += 60
654:             elif ratio_cobertura <= 1.5:
655:                 score += 40
657:             elif ratio_cobertura <= 2:
658:                 score += 20
660:         if punto_reposicion > 0:
662:             ratio_stock = (
663:                 stock_actual
664:                 / punto_reposicion
665:             )
667:             if ratio_stock <= 0.5:
668:                 score += 40
670:             elif ratio_stock <= 1:
671:                 score += 30
673:             elif ratio_stock <= 1.25:
674:                 score += 15
676:         return round(
677:             min(
678:                 score,
679:                 100
680:             ),
681:             2
682:         )
688:     @staticmethod
689:     def _calcular_reposicion(
690:         stock_actual: float,
691:         promedio_diario: float,
692:         stock_seguridad: float,
693:         lead_time_dias: int
694:     ) -> ReposicionInfo | None:
696:         if promedio_diario <= 0:
697:             return None
699:         horizonte_dias = max(
700:             lead_time_dias + 7,
701:             7
702:         )
704:         demanda_horizonte = (
705:             promedio_diario
706:             * horizonte_dias
707:         )
709:         cantidad_base = max(
710:             0,
711:             demanda_horizonte
712:             + stock_seguridad
713:             - stock_actual
714:         )
716:         cantidad_recomendada = (
717:             math.ceil(
718:                 cantidad_base
719:             )
720:         )
722:         cantidad_minima = (
723:             math.ceil(
724:                 cantidad_recomendada
725:                 * 0.85
726:             )
727:         )
729:         cantidad_segura = (
730:             math.ceil(
731:                 cantidad_recomendada
732:                 * 1.15
733:             )
734:         )
736:         return ReposicionInfo(
738:             cantidad_minima=
739:                 cantidad_minima,
741:             cantidad_recomendada=
742:                 cantidad_recomendada,
744:             cantidad_segura=
745:                 cantidad_segura
746:         )
752:     async def evaluar(
753:         self,
754:         id_inventario: str,
755:         generar_alertas: bool = True
756:     ) -> InventoryRiskResponse:
762:         inventario = (
763:             await self.repository
764:             .obtener_inventario(
765:                 id_inventario
766:             )
767:         )
769:         if inventario is None:
771:             raise HTTPException(
772:                 status_code=404,
773:                 detail=(
774:                     "Inventario no encontrado"
775:                 )
776:             )
778:         id_producto = inventario.get(
779:             "id_producto"
780:         )
782:         id_rack = inventario.get(
783:             "id_rack"
784:         )
786:         if not id_producto:
788:             raise HTTPException(
789:                 status_code=400,
790:                 detail=(
791:                     "El inventario no tiene "
792:                     "id_producto"
793:                 )
794:             )
800:         producto = (
801:             await self.repository
802:             .obtener_producto(
803:                 id_producto
804:             )
805:         )
807:         if producto is None:
809:             raise HTTPException(
810:                 status_code=404,
811:                 detail=(
812:                     "Producto asociado "
813:                     "no encontrado"
814:                 )
815:             )
821:         if not id_rack:
823:             id_rack = producto.get(
824:                 "id_rack"
825:             )
827:         if not id_rack:
829:             raise HTTPException(
830:                 status_code=400,
831:                 detail=(
832:                     "No se pudo determinar "
833:                     "el rack"
834:                 )
835:             )
837:         rack = (
838:             await self.repository
839:             .obtener_rack(
840:                 id_rack
841:             )
842:         )
844:         if rack is None:
846:             raise HTTPException(
847:                 status_code=404,
848:                 detail="Rack no encontrado"
849:             )
855:         id_zona = rack.get(
856:             "id_zona"
857:         )
859:         if not id_zona:
861:             raise HTTPException(
862:                 status_code=400,
863:                 detail=(
864:                     "El rack no tiene "
865:                     "id_zona"
866:                 )
867:             )
869:         zona = (
870:             await self.repository
871:             .obtener_zona(
872:                 id_zona
873:             )
874:         )
876:         if zona is None:
878:             raise HTTPException(
879:                 status_code=404,
880:                 detail="Zona no encontrada"
881:             )
887:         id_almacen = zona.get(
888:             "id_almacen"
889:         )
891:         if not id_almacen:
893:             raise HTTPException(
894:                 status_code=400,
895:                 detail=(
896:                     "La zona no tiene "
897:                     "id_almacen"
898:                 )
899:             )
901:         almacen = (
902:             await self.repository
903:             .obtener_almacen(
904:                 id_almacen
905:             )
906:         )
908:         if almacen is None:
910:             raise HTTPException(
911:                 status_code=404,
912:                 detail=(
913:                     "Almacén no encontrado"
914:                 )
915:             )
933:         id_empresa = (
934:             almacen.get(
935:                 "id_empresa"
936:             )
937:             or producto.get(
938:                 "id_empresa"
939:             )
940:         )
942:         if not id_empresa:
944:             raise HTTPException(
945:                 status_code=400,
946:                 detail=(
947:                     "No se pudo determinar "
948:                     "la empresa del inventario"
949:                 )
950:             )
956:         stock_actual = (
957:             self._safe_float(
958:                 inventario.get(
959:                     "stock_actual",
960:                     0
961:                 )
962:             )
963:         )
965:         lead_time_dias = int(
966:             producto.get(
967:                 "lead_time_dias",
968:                 0
969:             )
970:             or 0
971:         )
977:         try:
979:             (
980:                 forecast,
981:                 fecha_base_forecast
982:             ) = await self._generar_forecast(
983:                 id_inventario=
984:                     id_inventario
985:             )
987:         except Exception as exc:
989:             raise HTTPException(
990:                 status_code=500,
991:                 detail=(
992:                     "No se pudo generar el forecast "
993:                     "LightGBM para evaluar el riesgo: "
994:                     f"{str(exc)}"
995:                 )
996:             )
1002:         forecast.fecha_quiebre_estimada = (
1003:             self._calcular_fecha_quiebre(
1004:                 stock_actual=
1005:                     stock_actual,
1007:                 forecast=
1008:                     forecast,
1010:                 fecha_base=
1011:                     fecha_base_forecast
1012:             )
1013:         )
1028:         ahora = (
1029:             fecha_base_forecast
1030:         )
1032:         fecha_28d = (
1033:             ahora
1034:             - timedelta(
1035:                 days=28
1036:             )
1037:         )
1043:         movimientos = (
1044:             await self.repository
1045:             .obtener_salidas_desde(
1047:                 id_inventario=
1048:                     id_inventario,
1050:                 fecha_desde=
1051:                     fecha_28d
1052:             )
1053:         )
1055:         fecha_7d = (
1056:             ahora
1057:             - timedelta(
1058:                 days=7
1059:             )
1060:         )
1062:         fecha_14d = (
1063:             ahora
1064:             - timedelta(
1065:                 days=14
1066:             )
1067:         )
1069:         total_7d = 0.0
1070:         total_14d = 0.0
1071:         total_28d = 0.0
1073:         for movimiento in movimientos:
1075:             fecha = movimiento.get(
1076:                 "fecha_hora"
1077:             )
1079:             if not isinstance(
1080:                 fecha,
1081:                 datetime
1082:             ):
1083:                 continue
1087:             if fecha.tzinfo is None:
1089:                 fecha = fecha.replace(
1090:                     tzinfo=timezone.utc
1091:                 )
1093:             cantidad = (
1094:                 self._safe_float(
1095:                     movimiento.get(
1096:                         "cantidad",
1097:                         0
1098:                     )
1099:                 )
1100:             )
1102:             total_28d += cantidad
1104:             if fecha >= fecha_14d:
1105:                 total_14d += cantidad
1107:             if fecha >= fecha_7d:
1108:                 total_7d += cantidad
1114:         promedio_7d = (
1115:             self._promedio(
1116:                 total_7d,
1117:                 7
1118:             )
1119:         )
1121:         promedio_14d = (
1122:             self._promedio(
1123:                 total_14d,
1124:                 14
1125:             )
1126:         )
1128:         promedio_28d = (
1129:             self._promedio(
1130:                 total_28d,
1131:                 28
1132:             )
1133:         )
1139:         consumo_historico_diario = (
1140:             promedio_7d
1141:         )
1143:         if consumo_historico_diario <= 0:
1145:             consumo_historico_diario = (
1146:                 promedio_14d
1147:             )
1149:         if consumo_historico_diario <= 0:
1151:             consumo_historico_diario = (
1152:                 promedio_28d
1153:             )
1159:         forecast_promedio_diario = 0.0
1161:         if (
1162:             forecast.demanda_7d
1163:             is not None
1164:         ):
1166:             forecast_promedio_diario = (
1167:                 forecast.demanda_7d
1168:                 / self.forecast_horizon
1169:             )
1185:         consumo_diario = max(
1186:             consumo_historico_diario,
1187:             forecast_promedio_diario
1188:         )
1194:         tendencia = (
1195:             self._calcular_tendencia(
1196:                 promedio_7d=
1197:                     promedio_7d,
1199:                 promedio_28d=
1200:                     promedio_28d
1201:             )
1202:         )
1208:         dias_cobertura = None
1210:         if consumo_diario > 0:
1212:             dias_cobertura = (
1213:                 stock_actual
1214:                 / consumo_diario
1215:             )
1217:             dias_cobertura = round(
1218:                 dias_cobertura,
1219:                 2
1220:             )
1226:         consumos_diarios = (
1227:             self._consumo_diario_28d(
1228:                 movimientos,
1229:                 ahora
1230:             )
1231:         )
1233:         desviacion = 0.0
1235:         if len(
1236:             consumos_diarios
1237:         ) > 1:
1239:             desviacion = pstdev(
1240:                 consumos_diarios
1241:             )
1249:         if (
1250:             lead_time_dias > 0
1251:             and
1252:             desviacion > 0
1253:         ):
1255:             stock_seguridad = (
1256:                 self.z_service_level
1257:                 * desviacion
1258:                 * math.sqrt(
1259:                     lead_time_dias
1260:                 )
1261:             )
1263:         else:
1265:             stock_seguridad = 0.0
1267:         stock_seguridad = round(
1268:             stock_seguridad,
1269:             2
1270:         )
1278:         demanda_lead_time = (
1279:             consumo_diario
1280:             * lead_time_dias
1281:         )
1283:         punto_reposicion = (
1284:             demanda_lead_time
1285:             + stock_seguridad
1286:         )
1288:         punto_reposicion = round(
1289:             punto_reposicion,
1290:             2
1291:         )
1297:         nivel_riesgo = (
1298:             self._calcular_nivel_riesgo(
1300:                 stock_actual=
1301:                     stock_actual,
1303:                 dias_cobertura=
1304:                     dias_cobertura,
1306:                 lead_time_dias=
1307:                     lead_time_dias,
1309:                 punto_reposicion=
1310:                     punto_reposicion
1311:             )
1312:         )
1314:         score = (
1315:             self._calcular_score(
1317:                 stock_actual=
1318:                     stock_actual,
1320:                 dias_cobertura=
1321:                     dias_cobertura,
1323:                 lead_time_dias=
1324:                     lead_time_dias,
1326:                 punto_reposicion=
1327:                     punto_reposicion
1328:             )
1329:         )
1337:         reposicion = (
1338:             self._calcular_reposicion(
1340:                 stock_actual=
1341:                     stock_actual,
1343:                 promedio_diario=
1344:                     consumo_diario,
1346:                 stock_seguridad=
1347:                     stock_seguridad,
1349:                 lead_time_dias=
1350:                     lead_time_dias
1351:             )
1352:         )
1358:         if consumo_diario <= 0:
1360:             explicacion = (
1361:                 "No existe consumo reciente ni una "
1362:                 "demanda pronosticada suficiente para "
1363:                 "calcular una cobertura representativa."
1364:             )
1366:         elif (
1367:             nivel_riesgo
1368:             == NivelRiesgo.CRITICO
1369:         ):
1371:             explicacion = (
1372:                 f"El inventario tiene una cobertura "
1373:                 f"aproximada de {dias_cobertura} días, "
1374:                 f"mientras que el tiempo de reposición "
1375:                 f"es de {lead_time_dias} días. "
1376:                 f"LightGBM pronostica una demanda de "
1377:                 f"{forecast.demanda_7d} unidades para "
1378:                 f"los próximos 7 días. "
1379:                 f"Existe riesgo crítico de quiebre "
1380:                 f"de stock."
1381:             )
1383:         elif (
1384:             nivel_riesgo
1385:             == NivelRiesgo.ALTO
1386:         ):
1388:             explicacion = (
1389:                 f"El stock actual ({stock_actual}) "
1390:                 f"se encuentra por debajo o cerca "
1391:                 f"del punto de reposición "
1392:                 f"({punto_reposicion}). "
1393:                 f"LightGBM pronostica "
1394:                 f"{forecast.demanda_7d} unidades "
1395:                 f"de demanda para los próximos "
1396:                 f"7 días."
1397:             )
1399:         elif (
1400:             nivel_riesgo
1401:             == NivelRiesgo.MEDIO
1402:         ):
1404:             explicacion = (
1405:                 f"La cobertura actual es de "
1406:                 f"{dias_cobertura} días y se está "
1407:                 f"acercando al tiempo necesario "
1408:                 f"para reponer el producto. "
1409:                 f"El forecast de 7 días es de "
1410:                 f"{forecast.demanda_7d} unidades."
1411:             )
1413:         else:
1415:             if dias_cobertura is None:
1417:                 explicacion = (
1418:                     f"El producto no presenta una "
1419:                     f"demanda suficiente para estimar "
1420:                     f"riesgo de quiebre. "
1421:                     f"El forecast de LightGBM para "
1422:                     f"los próximos 7 días es de "
1423:                     f"{forecast.demanda_7d} unidades."
1424:                 )
1426:             else:
1428:                 explicacion = (
1429:                     f"El inventario presenta una "
1430:                     f"cobertura aproximada de "
1431:                     f"{dias_cobertura} días. "
1432:                     f"LightGBM pronostica "
1433:                     f"{forecast.demanda_7d} unidades "
1434:                     f"para los próximos 7 días y "
1435:                     f"actualmente no se detecta un "
1436:                     f"riesgo significativo."
1437:                 )
1443:         resultado = InventoryRiskResponse(
1445:             id_empresa=
1446:                 id_empresa,
1448:             id_almacen=
1449:                 id_almacen,
1451:             id_inventario=
1452:                 id_inventario,
1454:             id_producto=
1455:                 id_producto,
1457:             stock_actual=
1458:                 round(
1459:                     stock_actual,
1460:                     2
1461:                 ),
1463:             consumo=ConsumoInfo(
1465:                 promedio_7d=round(
1466:                     promedio_7d,
1467:                     2
1468:                 ),
1470:                 promedio_14d=round(
1471:                     promedio_14d,
1472:                     2
1473:                 ),
1475:                 promedio_28d=round(
1476:                     promedio_28d,
1477:                     2
1478:                 ),
1480:                 tendencia_porcentaje=round(
1481:                     tendencia,
1482:                     2
1483:                 )
1484:             ),
1486:             cobertura=CoberturaInfo(
1487:                 dias=
1488:                     dias_cobertura
1489:             ),
1491:             lead_time_dias=
1492:                 lead_time_dias,
1494:             forecast=
1495:                 forecast,
1497:             seguridad=SeguridadInfo(
1499:                 stock_seguridad=
1500:                     stock_seguridad,
1502:                 punto_reposicion=
1503:                     punto_reposicion
1504:             ),
1506:             riesgo=RiesgoInfo(
1508:                 nivel=
1509:                     nivel_riesgo,
1511:                 score=
1512:                     score
1513:             ),
1515:             reposicion=
1516:                 reposicion,
1518:             explicacion=
1519:                 explicacion
1520:         )
1526:         if generar_alertas:
1528:             await self._procesar_alerta(
1529:                 resultado
1530:             )
1532:         return resultado
1538:     async def _procesar_alerta(
1539:         self,
1540:         resultado: InventoryRiskResponse
1541:     ):
1543:         nivel = (
1544:             resultado.riesgo.nivel
1545:         )
1547:         if nivel not in (
1548:             NivelRiesgo.ALTO,
1549:             NivelRiesgo.CRITICO
1550:         ):
1551:             await self.alerta_service.resolver_activa_por_inventario(
1552:                 resultado.id_inventario,
1553:                 TipoAlerta.RIESGO_STOCKOUT
1554:             )
1555:             return
1557:         if (
1558:             nivel
1559:             == NivelRiesgo.CRITICO
1560:         ):
1562:             titulo = (
1563:                 "Riesgo crítico de "
1564:                 "quiebre de stock"
1565:             )
1567:         else:
1569:             titulo = (
1570:                 "Inventario cerca del "
1571:                 "punto de reposición"
1572:             )
1574:         alerta = (
1575:             await self.alerta_service.crear(
1577:                 AlertaCreate(
1579:                     id_empresa=
1580:                         resultado.id_empresa,
1582:                     id_almacen=
1583:                         resultado.id_almacen,
1585:                     id_inventario=
1586:                         resultado.id_inventario,
1588:                     id_producto=
1589:                         resultado.id_producto,
1591:                     tipo_alerta=
1592:                         TipoAlerta
1593:                         .RIESGO_STOCKOUT,
1595:                     nivel_riesgo=
1596:                         nivel,
1598:                     titulo=
1599:                         titulo,
1601:                     mensaje=
1602:                         resultado.explicacion,
1604:                     stock_actual=
1605:                         resultado.stock_actual,
1607:                     dias_cobertura=
1608:                         resultado
1609:                         .cobertura
1610:                         .dias,
1612:                     stock_seguridad=
1613:                         resultado
1614:                         .seguridad
1615:                         .stock_seguridad,
1617:                     punto_reposicion=
1618:                         resultado
1619:                         .seguridad
1620:                         .punto_reposicion,
1622:                     forecast_7d=
1623:                         resultado
1624:                         .forecast
1625:                         .demanda_7d
1626:                 )
1627:             )
1628:         )
1630:         if resultado.reposicion is None:
1631:             return
1633:         await self.recomendacion_service.crear(
1635:             RecomendacionCreate(
1637:                 id_empresa=
1638:                     resultado.id_empresa,
1640:                 id_almacen=
1641:                     resultado.id_almacen,
1643:                 id_inventario=
1644:                     resultado.id_inventario,
1646:                 id_producto=
1647:                     resultado.id_producto,
1649:                 id_alerta=
1650:                     alerta[
1651:                         "id_alerta"
1652:                     ],
1654:                 tipo_recomendacion=
1655:                     TipoRecomendacion
1656:                     .REABASTECER,
1658:                 nivel_riesgo=
1659:                     nivel,
1661:                 cantidad_minima=
1662:                     resultado
1663:                     .reposicion
1664:                     .cantidad_minima,
1666:                 cantidad_recomendada=
1667:                     resultado
1668:                     .reposicion
1669:                     .cantidad_recomendada,
1671:                 cantidad_segura=
1672:                     resultado
1673:                     .reposicion
1674:                     .cantidad_segura,
1676:                 forecast_7d=
1677:                     resultado
1678:                     .forecast
1679:                     .demanda_7d,
1681:                 explicacion=
1682:                     resultado.explicacion,
1684:                 origen=
1685:                     "MOTOR_SEGURIDAD_LIGHTGBM"
1686:             )
1687:         )
1693:     async def evaluar_todos(
1694:         self,
1695:         generar_alertas: bool = False,
1696:         ids_inventario: set | None = None
1697:     ) -> list[
1698:         InventoryRiskResponse
1699:     ]:
1701:         inventarios = (
1702:             await self.repository
1703:             .listar_inventarios()
1704:         )
1706:         resultados = []
1708:         for inventario in inventarios:
1710:             id_inventario = (
1711:                 inventario.get(
1712:                     "id_inventario"
1713:                 )
1714:                 or inventario.get(
1715:                     "id"
1716:                 )
1717:             )
1719:             if not id_inventario:
1720:                 continue
1723:             if (
1724:                 ids_inventario is not None
1725:                 and id_inventario not in ids_inventario
1726:             ):
1727:                 continue
1729:             resultado = (
1730:                 await self.evaluar(
1732:                     id_inventario=
1733:                         id_inventario,
1735:                     generar_alertas=
1736:                         generar_alertas
1737:                 )
1738:             )
1740:             resultados.append(
1741:                 resultado
1742:             )
1744:         return resultados
```

### app/services/saiki_intent_router.py

```python
1: ﻿from dataclasses import dataclass
2: import re
3: import unicodedata
6: @dataclass(frozen=True)
7: class SaikiIntent:
8:     kind: str
9:     tool_names: frozenset[str]
10:     horizon_days: int | None = None
11:     needs_horizon: bool = False
14: class SaikiIntentRouter:
15:     """Route clear requests; leave uncertain requests to the model."""
16:     SUPPORTED_HORIZONS = frozenset({7})
17:     CURRENT_TOOLS = frozenset({'get_warehouse_status', 'get_inventory', 'get_product', 'get_active_alerts', 'get_recommendations', 'get_recent_movements'})
18:     PREDICTIVE_TOOLS = frozenset({'get_warehouse_status', 'get_inventory', 'get_product', 'get_forecast', 'get_inventory_risk'})
19:     MIXED_TOOLS = CURRENT_TOOLS | PREDICTIVE_TOOLS
21:     @staticmethod
22:     def _normalize(text):
23:         return ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if not unicodedata.combining(c))
25:     @classmethod
26:     def classify(cls, message: str, history: list[dict] | None = None) -> SaikiIntent:
27:         text = cls._normalize(message)
28:         if re.fullmatch(r'\s*(hola|buenos dias|buenas tardes|buenas noches|hey)(\s+saiki)?[!,.?\s]*', text):
29:             return SaikiIntent('greeting', frozenset())
30:         horizon = cls._horizon_days(text)
31:         analysis = bool(re.search(r'analiz|evalua|prioriz|justific|por que|motivo|explica', text))
32:         replenishment = bool(re.search(r'repon|reposicion|comprar|recomend', text))
33:         if analysis and replenishment:
34:             return SaikiIntent('analysis', cls.MIXED_TOOLS, horizon)
35:         listing = bool(re.search(r'mencion|enumera|lista|listado|detalle|desglos|muestra|dime|dame|ensena|quiero ver|que productos', text))
36:         inventory = bool(re.search(r'producto|inventario|existencia|stock', text))
37:         location = bool(re.search(r'ubicacion|rack|zona|donde', text))
38:         quantities = bool(re.search(r'cantidad|stock|unidades|existencia', text))
39:         other_operation = bool(re.search(r'alert|movimiento|entrada|salida|riesgo|agot|demanda|predic|repon|recomend', text))
40:         if listing and inventory and not other_operation:
41:             if location:
42:                 return SaikiIntent('inventory_detail', frozenset({'get_warehouse_status'}))
43:             if quantities or re.search(r'mencion|enumera|listado|lista\b|todos.*productos', text):
44:                 return SaikiIntent('product_quantities', frozenset({'get_warehouse_status', 'get_product'}))
45:         predictive = bool(re.search(r'proyect|proyecc|pronostic|predec|predic|demanda futura|agot|quedarse sin|alcanzara|necesitare', text)) or (bool(re.search(r'demanda|vendera|venderan', text)) and horizon is not None)
46:         if predictive or (horizon is not None and cls._history_has_predictive_request(history)):
47:             return SaikiIntent('predictive', cls.PREDICTIVE_TOOLS, horizon if horizon is not None else 7)
48:         qualified = bool(re.search(r'\brack|\bzona|\bcon\b|\bsin\b|\b(?:de|en|para|del)\b', text))
49:         if not qualified and re.search(r'\bcuantos? productos\b', text) and re.search(r'\btengo\b', text):
50:             return SaikiIntent('product_count', frozenset({'get_product'}))
51:         if not qualified and re.search(r'\b(?:tengo|hay|existen) almacenes\b', text):
52:             return SaikiIntent('warehouses', frozenset({'get_warehouse_status'}))
53:         if not qualified and re.search(r'\bcuanto (?:stock|inventario)\b', text) and re.search(r'\btengo\b', text):
54:             return SaikiIntent('stock_total', frozenset({'get_warehouse_status'}))
55:         categories = [
56:             ('movements', r'movimiento|entrada|salida|venta|historial', {'get_recent_movements'}),
57:             ('alerts', r'alerta|aviso', {'get_active_alerts'}),
58:             ('recommendations', r'recomend|reponer|reposicion|comprar', {'get_recommendations'}),
59:             ('risk', r'riesgo|desabastec', {'get_inventory_risk', 'get_forecast', 'get_warehouse_status'}),
60:             ('location', r'donde|ubicacion|localiza|en que rack|en que zona', {'get_warehouse_status', 'get_product'}),
61:             ('stock', r'stock|existencia|cuantas unidades|cantidad disponible', {'get_warehouse_status', 'get_inventory', 'get_product'}),
62:             ('products', r'producto|catalogo', {'get_product', 'get_warehouse_status'}),
63:         ]
64:         matches = [(kind, tools) for kind, pattern, tools in categories if re.search(r'\b(?:' + pattern + ')', text)]
65:         if matches:
66:             tools = frozenset().union(*(tools for _, tools in matches))
67:             return SaikiIntent(matches[0][0] if len(matches) == 1 else 'mixed', tools)
68:         if re.search(r'\bmuestrame\s+(?:el|la)\b', text):
69:             return SaikiIntent('products', frozenset({'get_product', 'get_warehouse_status'}))
70:         if re.search(r'inventario|almacen', text) and re.search(r'como|estado|resumen|situacion|panorama', text):
71:             return SaikiIntent('general', frozenset({'get_warehouse_status'}))
72:         return SaikiIntent('ambiguous', frozenset())
74:     @classmethod
75:     def _history_has_predictive_request(cls, history):
76:         return any(re.search(r'proyect|proyecc|pronostic|predic|agot|demanda futura', cls._normalize(str(item.get('content', '')))) for item in (history or [])[-4:] if item.get('role') == 'user')
78:     @staticmethod
79:     def _horizon_days(text):
80:         text = re.sub(r'\btreinta\b', '30', text)
81:         text = re.sub(r'\bsiete\b', '7', text)
82:         match = re.search(r'\b(\d+)\s*(dias?|semanas?|mes(?:es)?)\b', text)
83:         if match:
84:             return int(match[1]) * (7 if 'semana' in match[2] else 30 if 'mes' in match[2] else 1)
85:         if re.search(r'\b(?:una|la proxima|esta) semana\b', text):
86:             return 7
87:         if re.search(r'\b(?:un|el proximo|este) mes\b', text):
88:             return 30
89:         return None
```

### app/services/saiki_inventory_summary.py

```python
1: """Read-only visual summary; all scope comes from the authenticated user."""
2: import math
4: from fastapi import HTTPException
6: from app.repositories.almacen_repository import AlmacenRepository
7: from app.repositories.zona_repository import ZonaRepository
8: from app.repositories.rack_repository import RackRepository
9: from app.repositories.producto_repository import ProductoRepository
10: from app.repositories.inventario_repository import InventarioRepository
13: def identifier(row, key):
14:     return row.get(key) or row.get("id")
17: def numeric(value):
18:     return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
21: async def inventory_summary(user, page=1, page_size=25):
22:     if user is None:
23:         raise HTTPException(401, "Se requiere autenticación para consultar el inventario.")
24:     if user.es_proveedor:
25:         raise HTTPException(403, "No tiene acceso al inventario.")
26:     warehouses = await AlmacenRepository.obtener_por_empresa(user.id_empresa)
27:     if user.es_operario:
28:         warehouses = [row for row in warehouses if identifier(row, "id_almacen") == user.id_almacen]
29:     warehouse_map = {identifier(row, "id_almacen"): row for row in warehouses}
30:     zones = await ZonaRepository.obtener_por_almacenes(list(warehouse_map)) if warehouse_map else []
31:     zone_map = {identifier(row, "id_zona"): row for row in zones}
32:     racks = await RackRepository.obtener_por_zonas(list(zone_map)) if zone_map else []
33:     rack_map = {identifier(row, "id_rack"): row for row in racks}
34:     inventories = await InventarioRepository().obtener_por_racks(list(rack_map)) if rack_map else []
35:     products = await ProductoRepository.collection().find({"id_empresa": user.id_empresa}, {"_id": 0}).to_list(length=None)
36:     product_map = {row["id_producto"]: row for row in products}
38:     inventories = [row for row in inventories if row.get("id_producto") in product_map]
39:     grouped = {}
40:     for item in inventories:
41:         stock = item.get("stock_actual")
42:         if not numeric(stock) or stock < 0:
43:             raise HTTPException(503, "No se pudo verificar el stock: existen cantidades inválidas.")
44:         key = (item["id_producto"], item["id_rack"])
45:         group = grouped.setdefault(key, {"stock": 0, "ids": [], "minimums": []})
46:         group["stock"] += stock
47:         group["ids"].append(item["id_inventario"])
48:         group["minimums"].append(item.get("stock_minimo"))
49:     rows = []
50:     for (product_id, rack_id), group in grouped.items():
51:         rack = rack_map[rack_id]
52:         zone = zone_map[rack["id_zona"]]
53:         warehouse = warehouse_map[zone["id_almacen"]]
54:         stock = group["stock"]
55:         minimum = group["minimums"][0] if len(group["minimums"]) == 1 else None
56:         status = "Sin stock" if stock == 0 else "Sin determinar"
57:         if stock > 0 and numeric(minimum) and minimum >= 0:
58:             status = "Bajo stock" if stock <= minimum else "Disponible"
59:         rows.append({"id_producto": product_id, "product_name": product_map[product_id].get("nombre"),
60:                      "id_almacen": identifier(warehouse, "id_almacen"), "warehouse_name": warehouse.get("nombre"),
61:                      "id_zona": identifier(zone, "id_zona"), "zone_name": zone.get("nombre"),
62:                      "id_rack": rack_id, "rack_name": rack.get("codigo") or rack.get("nombre"),
63:                      "inventory_ids": sorted(group["ids"]), "stock": stock, "status_label": status})
64:     rows.sort(key=lambda row: (row["id_producto"], row["id_almacen"], row["id_zona"], row["id_rack"]))
65:     total_units = sum(row["stock"] for row in rows)
66:     positive_products = {row["id_producto"] for row in rows if row["stock"] > 0}
67:     state = ("sin_almacenes" if not warehouses else "almacen_sin_productos" if not products and not inventories
68:              else "productos_sin_inventario" if not inventories else "stock_cero" if total_units == 0 else "stock_positivo")
69:     summary = {"distinct_products": len(positive_products), "total_units": total_units,
70:                "warehouse_count": len(warehouses), "catalog_products": len(products), "inventory_state": state,
71:                "rows": rows[(page - 1) * page_size:page * page_size],
72:                "pagination": {"page": page, "page_size": page_size, "total_rows": len(rows),
73:                               "total_pages": math.ceil(len(rows) / page_size)}}
74:     visualization = {"type": "inventory_summary", "version": 1, "title": "Resumen de inventario",
75:                      "cards": [{"label": label, "value_path": "data.inventory_summary." + key}
76:                                for label, key in (("Productos", "distinct_products"), ("Unidades", "total_units"), ("Almacenes", "warehouse_count"))],
77:                      "table": {"rows_path": "data.inventory_summary.rows",
78:                                "columns": [{"key": key, "label": label} for key, label in
79:                                            (("product_name", "Producto"), ("stock", "Stock"), ("warehouse_name", "Almacén"),
80:                                             ("zone_name", "Zona"), ("rack_name", "Rack"), ("status_label", "Estado"))],
81:                                "pagination_path": "data.inventory_summary.pagination"}}
82:     stock_by_product = {}
83:     for row in rows:
84:         stock_by_product[row["id_producto"]] = stock_by_product.get(row["id_producto"], 0) + row["stock"]
85:     return {"inventory_summary": summary, "visualization": visualization,
86:             "estado_inventario": state, "total_almacenes": len(warehouses),
87:             "total_registros_inventario": len(inventories), "productos_distintos": len(stock_by_product),
88:             "stock_total_unidades": total_units, "almacenes": warehouses, "inventarios": inventories[:50],
89:             "stock_por_producto": [{"id_producto": key, "nombre": product_map[key].get("nombre"), "stock_actual": value}
90:                                    for key, value in stock_by_product.items()],
91:             "ubicaciones": [{"id_producto": row["id_producto"], "id_rack": row["id_rack"], "stock_actual": row["stock"],
92:                              "rack": rack_map[row["id_rack"]], "zona": zone_map[row["id_zona"]]} for row in rows]}
```

### app/services/saiki_responses.py

```python
1: """Conversational rendering of verified tool results; no business calculations."""
2: import math
5: def number(value):
6:     if value is None or not isinstance(value, (int, float)) or not math.isfinite(value):
7:         return None
8:     return f"{value:g}"
11: def operational_answer(kind, rows):
12:     count = len(rows)
13:     if kind == "alerts":
14:         level = str(rows[0].get("nivel_riesgo", "")).lower() if count == 1 else ""
15:         detail = f" de riesgo {level}" if level in {"bajo", "medio", "alto", "critico"} else ""
16:         return "No tienes alertas activas." if not count else f"Tienes {count} alerta{'s' if count != 1 else ''} activa{'s' if count != 1 else ''}{detail}. Puedes consultar los detalles en los datos adjuntos."
17:     if kind == "movements":
18:         if not count:
19:             return "No encontré movimientos recientes."
20:         quantity = number(rows[0].get("cantidad"))
21:         movement = rows[0].get("tipo_movimiento")
22:         if count == 1 and quantity is not None and movement in {"SALIDA", "ENTRADA"}:
23:             return f"Encontré un movimiento reciente: una {movement.lower()} de {quantity} {'unidad' if quantity == '1' else 'unidades'}."
24:         return f"Encontré {count} movimiento{'s' if count != 1 else ''} reciente{'s' if count != 1 else ''}. Los detalles están disponibles en la respuesta."
25:     if kind == "recommendations":
26:         pending = [row for row in rows if row.get("estado") in {"PENDIENTE", "VALIDADA_OPERARIO", "CAMBIOS_SOLICITADOS", "APROBADA_EMPRESA", "ACEPTADA"}]
27:         if not pending:
28:             return "No hay recomendaciones pendientes de reposición registradas."
29:         if len(pending) == 1 and number(pending[0].get("cantidad_recomendada")) is not None:
30:             return f"La recomendación registrada propone reponer {number(pending[0]['cantidad_recomendada'])} unidades. Revisa el producto y los detalles antes de iniciar una compra."
31:         return f"Tienes {len(pending)} {'recomendación pendiente' if len(pending) == 1 else 'recomendaciones pendientes'}. Revisa las cantidades propuestas antes de iniciar una compra."
32:     raise ValueError("Unsupported operational answer")
35: def forecast_answer(result):
36:     total = number(result.get("demanda_total_7d"))
37:     if total is None:
38:         return "No pude obtener una estimación de demanda para los próximos 7 días."
39:     incomplete = any(item.get("sin_datos", 0) > 0 for item in result.get("features_por_horizonte", {}).values() if isinstance(item, dict))
40:     uncertainty = "Faltan datos de algunas variables, por lo que es una estimación con limitaciones" if incomplete else "Es una estimación sujeta al historial disponible"
41:     return f"La demanda estimada para los próximos 7 días es de {total} unidades. {uncertainty}, no una proyección de stock futuro."
44: def risk_answer(results):
45:     levels = {"BAJO": 0, "MEDIO": 1, "ALTO": 2, "CRITICO": 3}
46:     valid = [row for row in results if row.get("riesgo", {}).get("nivel") in levels]
47:     if not valid:
48:         return "No pude obtener un nivel de riesgo verificado con los datos disponibles."
49:     highest = max(valid, key=lambda row: levels[row["riesgo"]["nivel"]])
50:     level = highest["riesgo"]["nivel"].lower().replace("critico", "crítico")
51:     stock = number(highest.get("stock_actual"))
52:     coverage = number(highest.get("cobertura", {}).get("dias"))
53:     lead = number(highest.get("lead_time_dias"))
54:     reason = ""
55:     if stock == "0":
56:         reason = " porque no quedan existencias"
57:     elif coverage is not None and lead is not None:
58:         reason = f": la cobertura es de {coverage} {'día' if coverage == '1' else 'días'} y la reposición tarda {lead} {'día' if lead == '1' else 'días'}"
59:     count = sum(row["riesgo"]["nivel"] in {"ALTO", "CRITICO"} for row in valid)
60:     prefix = f"Hay {count} inventario{'s' if count != 1 else ''} con riesgo alto o crítico. " if len(valid) > 1 else ""
61:     subject = f" de {highest['nombre_producto']}" if highest.get("nombre_producto") else " calculado"
62:     return prefix + f"El riesgo{subject} es {level}{reason}."
```

### app/services/saiki_service.py

```python
1: import asyncio
2: import http.client
3: import json
4: import logging
5: import socket
6: import time
7: import hashlib
8: import re
9: from uuid import uuid4
10: from typing import Any
11: from urllib.parse import urlsplit
12: from urllib import error, request
14: from fastapi import HTTPException, status
15: from pymongo.errors import PyMongoError
17: from app.config.settings import get_settings
18: from app.dto.saiki_dto import SaikiAskRequest
19: from app.dto.auth_dto import UsuarioActual
20: from app.prompts.saiki_system_prompt import SAIKI_SYSTEM_PROMPT
21: from app.services.saiki_intent_router import SaikiIntentRouter
22: from app.services.saiki_tools import SaikiToolRegistry
23: from app.services.saiki_responses import operational_answer, forecast_answer, risk_answer
25: logger = logging.getLogger(__name__)
28: class OllamaTimeoutError(RuntimeError):
29:     pass
32: class OllamaUnavailableError(RuntimeError):
33:     pass
36: class SaikiDatabaseError(RuntimeError):
37:     pass
40: class SaikiService:
41:     max_tool_iterations = 4
43:     def __init__(self):
44:         from pathlib import Path
45:         root = Path(__file__).resolve().parents[1]
46:         files = ("services/saiki_service.py", "services/saiki_tools.py", "services/saiki_inventory_summary.py", "services/saiki_intent_router.py", "services/saiki_responses.py", "dto/saiki_dto.py", "prompts/saiki_system_prompt.py", "controllers/saiki_controller.py")
47:         self.code_revision = hashlib.sha256(b"".join((root / name).read_bytes() for name in files)).hexdigest()[:12]
48:         self.settings = get_settings()
49:         self.tools = SaikiToolRegistry()
50:         self.intent_router = SaikiIntentRouter()
52:     @staticmethod
53:     def get_system_prompt() -> str:
54:         return SAIKI_SYSTEM_PROMPT
56:     async def health(self) -> dict:
57:         base = {
58:             "ollama_base_url": self.settings.ollama_base_url,
59:             "model": self.settings.ollama_model,
60:         }
61:         try:
62:             models = await asyncio.to_thread(self._installed_models)
63:         except RuntimeError as exc:
64:             return {"status": "unavailable", "ready": False, **base, "detail": str(exc)}
65:         if self.settings.ollama_model not in models:
66:             return {
67:                 "status": "unavailable",
68:                 "ready": False,
69:                 **base,
70:                 "detail": f"El modelo {self.settings.ollama_model} no está descargado en Ollama.",
71:             }
72:         return {"status": "ok", "ready": True, **base}
74:     def _installed_models(self) -> list[str]:
75:         url = f"{self.settings.ollama_base_url.rstrip('/')}/api/tags"
76:         try:
77:             with request.urlopen(url, timeout=5) as response:
78:                 data = json.loads(response.read().decode("utf-8"))
79:         except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
80:             raise RuntimeError(f"No se pudo conectar con Ollama en {url}: {exc}") from exc
81:         return [model.get("name", "") for model in data.get("models", [])]
83:     async def ask(
84:         self, data: SaikiAskRequest, user: UsuarioActual | None = None, *, request_id: str | None = None,
85:     ) -> dict:
86:         started = time.perf_counter()
87:         request_id = request_id or uuid4().hex
88:         classified = time.perf_counter()
89:         intent = self.intent_router.classify(data.message or "", data.history)
90:         logger.info("saiki_classification request_id=%s duration_ms=%.3f", request_id, (time.perf_counter() - classified) * 1000)
91:         logger.info(
92:             "saiki_request_start request_id=%s revision=%s intent=%s has_inventory_id=%s has_product_id=%s history_count=%d",
93:             request_id, self._code_revision(), intent.kind,
94:             bool(data.id_inventario), bool(data.id_producto), len(data.history),
95:         )
96:         try:
97:             return await self._ask(data, user, intent)
98:         except PyMongoError as exc:
99:             logger.warning("saiki_request_error request_id=%s type=mongodb_unavailable", request_id)
100:             raise HTTPException(status_code=503, detail="No se pudo verificar el inventario en MongoDB.") from exc
101:         except RuntimeError as exc:
102:             if isinstance(exc, SaikiDatabaseError) or "MongoDB" in str(exc) or "motor" in str(exc):
103:                 raise HTTPException(status_code=503, detail="No se pudo verificar el inventario en MongoDB.") from exc
104:             raise
105:         finally:
106:             logger.info("saiki_request_complete request_id=%s duration_ms=%.3f", request_id, (time.perf_counter() - started) * 1000)
108:     def _code_revision(self):
109:         return self.code_revision
111:     async def _ask(
112:         self,
113:         data: SaikiAskRequest,
114:         user: UsuarioActual | None = None,
115:         intent=None,
116:     ) -> dict:
117:         context = dict(data.context)
118:         intent = intent or self.intent_router.classify(data.message or "", data.history)
119:         if intent.kind == "greeting":
120:             return self._simple_response(
121:                 "¡Hola, soy Saiki!",
122:                 source="router",
123:             )
124:         if intent.horizon_days is not None and intent.horizon_days not in self.intent_router.SUPPORTED_HORIZONS:
125:             return self._clarification_response(
126:                 "Actualmente puedo predecir la demanda de los próximos 7 días. El horizonte solicitado todavía no está disponible."
127:             )
128:         if intent.horizon_days is not None:
129:             context["horizonte_dias_solicitado"] = intent.horizon_days
130:             context["tipo_prediccion"] = "demanda"
131:         if data.id_inventario and user is not None:
132:             context["inventario"] = await self._authorized_tool("get_inventory", {"id_inventario": data.id_inventario}, user)
133:         if data.id_producto and user is not None:
134:             context["producto"] = await self._authorized_tool("get_product", {"id_producto": data.id_producto}, user)
135:         if intent.kind in {"product_quantities", "inventory_detail"} and not data.id_producto and not data.id_inventario:
136:             return await self._fast_detail_response(data, context, user, intent.kind)
137:         if intent.kind in {"alerts", "movements", "recommendations"} and not data.id_producto:
138:             return await self._fast_operational_response(intent.kind, data, context, user)
139:         if intent.kind in {"predictive", "risk"} and not re.search(r"\b(?:alerta|movimiento|recomend|comprar)", self.intent_router._normalize(data.message or "")):
140:             return await self._fast_analysis_response(intent.kind, data, context, user)
141:         if intent.kind == "products" and not data.id_inventario and not data.id_producto:
142:             return await self._fast_products_response(data, context, user)
143:         location_name = self._location_name(data.message or "") if intent.kind == "location" else None
144:         if location_name and not data.id_inventario and not data.id_producto:
145:             return await self._fast_location_response(location_name, context, user)
146:         if (
147:             intent.kind in {"general", "product_count", "warehouses", "stock_total"}
148:             and not data.id_inventario
149:             and not data.id_producto
150:         ):
151:             try:
152:                 return await self._fast_current_response(context, user, intent.kind, data)
153:             except SaikiDatabaseError as exc:
154:                 raise HTTPException(
155:                     status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
156:                     detail="No se pudo verificar el inventario en MongoDB.",
157:                 ) from exc
158:             except RuntimeError as exc:
159:                 logger.exception("saiki_request_error type=unexpected_runtime")
160:                 raise HTTPException(
161:                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
162:                     detail="Saiki no está disponible en este momento.",
163:                 ) from exc
164:         analysis_data, analysis_sources = {}, set()
165:         if intent.kind == "analysis":
166:             summary, summary_source = await self._execute_tool("get_warehouse_status", {"include_visual": True}, user)
167:             recommendations, recommendation_source = await self._execute_tool("get_recommendations", {}, user)
168:             analysis_data = {"get_warehouse_status": summary, "get_recommendations": recommendations}
169:             analysis_sources = {summary_source, recommendation_source}
170:             context["datos_verificados_analisis"] = analysis_data
171:         messages = [
172:             {"role": "system", "content": self.get_system_prompt()},
173:             *data.history,
174:             {
175:                 "role": "user",
176:                 "content": self._build_prompt(data.message or "", context),
177:             },
178:         ]
179:         started = time.perf_counter()
180:         try:
181:             answer, tool_data, sources = await self._agent_loop(messages, user, intent.tool_names or None)
182:         except ValueError as exc:
183:             raise HTTPException(status_code=400, detail=str(exc)) from exc
184:         except OllamaTimeoutError as exc:
185:             logger.warning("saiki_request_error type=ollama_timeout")
186:             raise HTTPException(
187:                 status_code=status.HTTP_504_GATEWAY_TIMEOUT,
188:                 detail="Ollama tardó demasiado en responder.",
189:             ) from exc
190:         except OllamaUnavailableError as exc:
191:             logger.warning("saiki_request_error type=ollama_unavailable")
192:             raise HTTPException(
193:                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
194:                 detail="Ollama no está disponible en este momento.",
195:             ) from exc
196:         except SaikiDatabaseError as exc:
197:             logger.warning("saiki_request_error type=mongodb_unavailable")
198:             raise HTTPException(
199:                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
200:                 detail="No se pudo verificar el inventario en MongoDB.",
201:             ) from exc
202:         except RuntimeError as exc:
203:             logger.exception("saiki_request_error type=unexpected_runtime")
204:             raise HTTPException(
205:                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
206:                 detail="Saiki no está disponible en este momento.",
207:             ) from exc
208:         finally:
209:             logger.info(
210:                 "saiki_request duration_ms=%d",
211:                 round((time.perf_counter() - started) * 1000),
212:             )
214:         if analysis_data:
215:             tool_data = {**analysis_data, **tool_data}
216:             sources.update(analysis_sources)
217:         if "LIGHTGBM" in sources and intent.horizon_days == 7:
218:             answer = "La proyección corresponde a la demanda de los próximos 7 días. " + answer
219:         return {
220:             "answer": answer,
221:             "model": self.settings.ollama_model,
222:             "base_url": self.settings.ollama_base_url,
223:             "source": "ollama",
224:             "context": context,
225:             "data": tool_data,
226:             "visualization": self._visualization(tool_data),
227:             "sources": sorted(sources),
228:             "warnings": self._warnings(sources, tool_data),
229:         }
231:     def _clarification_response(self, answer: str) -> dict:
232:         return self._simple_response(answer, source="router")
234:     def _verified_response(self, answer, context, data, sources):
235:         response = self._simple_response(answer, "backend", data)
236:         response.update(context=context, sources=sorted(sources), warnings=self._warnings(sources, data))
237:         return response
239:     async def _fast_detail_response(self, request_data, context, user, kind):
240:         summary, source = await self._execute_tool("get_warehouse_status", {"include_visual": True, "page": request_data.page, "page_size": request_data.page_size}, user)
241:         structured = summary["inventory_summary"]
242:         data, sources = {"get_warehouse_status": summary, "inventory_summary": structured}, {source}
243:         if kind == "product_quantities":
244:             products, product_source = await self._execute_tool("get_product", {}, user)
245:             sources.add(product_source)
246:             stock = {row["id_producto"]: row["stock_actual"] for row in summary["stock_por_producto"]}
247:             rows = [{"id_producto": item["id_producto"], "product_name": item.get("nombre"),
248:                      "stock": stock.get(item["id_producto"]), "has_inventory": item["id_producto"] in stock} for item in products]
249:             data["product_quantities"] = rows
250:             answer = "; ".join(f"{row['product_name'] or 'Producto sin nombre'}: {row['stock']} unidades" if row['has_inventory'] else f"{row['product_name'] or 'Producto sin nombre'}: sin inventario registrado" for row in rows)
251:             answer = answer + "." if answer else "No tienes productos registrados en tu catálogo."
252:         else:
253:             rows = structured["rows"]
254:             parts = []
255:             for row in rows:
256:                 location = ", ".join(("almacén " + (row["warehouse_name"] or "sin información"), "zona " + (row["zone_name"] or "sin información"), "rack " + (row["rack_name"] or "sin información")))
257:                 parts.append(f"{row['product_name'] or 'Producto sin nombre'}: {row['stock']} unidades en {location}")
258:             answer = "; ".join(parts) + "." if parts else "No hay ubicaciones de inventario en esta página."
259:             if structured["pagination"]["total_pages"] > 1:
260:                 answer += f" Página {request_data.page} de {structured['pagination']['total_pages']}; puedes consultar las demás páginas."
261:         response = self._verified_response(answer, context, data, sources)
262:         response["visualization"] = summary["visualization"]
263:         if kind == "product_quantities":
264:             response["visualization"] = {"type": "table", "rows_path": "data.product_quantities", "columns": [{"key": "product_name", "label": "Producto"}, {"key": "stock", "label": "Stock"}, {"key": "has_inventory", "label": "Inventario registrado"}]}
265:         return response
267:     async def _fast_operational_response(self, kind, request_data, context, user):
268:         tool = {"alerts": "get_active_alerts", "movements": "get_recent_movements", "recommendations": "get_recommendations"}[kind]
269:         arguments = {"id_inventario": request_data.id_inventario} if request_data.id_inventario else {}
270:         rows, source = await self._execute_tool(tool, arguments, user)
271:         text = self.intent_router._normalize(request_data.message or "")
272:         if kind == "movements" and re.search(r"\bsalidas?\b|\bentradas?\b", text):
273:             movement_type = "SALIDA" if re.search(r"\bsalidas?\b", text) else "ENTRADA"
274:             rows = [row for row in rows if row.get("tipo_movimiento") == movement_type]
275:             answer = f"Encontré {len(rows)} {movement_type.lower()}{'s' if len(rows) != 1 else ''} entre los movimientos recientes consultados."
276:         else:
277:             answer = operational_answer(kind, rows)
278:         return self._verified_response(answer, context, {tool: rows}, {source})
280:     async def _fast_products_response(self, request_data, context, user):
281:         text = self.intent_router._normalize(request_data.message or "")
282:         if re.search(r"quedan|disponibles|existencias", text):
283:             summary, source = await self._execute_tool("get_warehouse_status", {}, user)
284:             products = [row for row in summary.get("stock_por_producto", []) if row.get("stock_actual", 0) > 0]
285:             details = "; ".join(f"{row.get('nombre') or 'Producto sin nombre'}: {row['stock_actual']} unidades" for row in products[:5])
286:             answer = f"Tienes estas existencias: {details}." if products else "No encontré productos con existencias positivas en tus inventarios visibles."
287:             if len(products) == 1:
288:                 answer = f"Quedan {products[0]['stock_actual']} unidades de {products[0].get('nombre') or 'un producto sin nombre registrado'}."
289:             if len(products) > 5:
290:                 answer += " Puedes consultar el resto en los datos adjuntos."
291:             return self._verified_response(answer, context, {"get_warehouse_status": summary}, {source})
292:         products, source = await self._execute_tool("get_product", {}, user)
293:         selected = self._product_from_history(products, [{"role": "user", "content": request_data.message or ""}])
294:         if selected:
295:             context["producto_consultado"] = {"id_producto": selected["id_producto"], "nombre": selected.get("nombre")}
296:             answer = f"{selected.get('nombre') or 'El producto'} está registrado en tu catálogo."
297:         elif "muestrame" in text:
298:             answer = "No pude identificar un único producto de tu catálogo. Indica su nombre completo para consultarlo."
299:         else:
300:             answer = f"Tienes {len(products)} {'producto registrado' if len(products) == 1 else 'productos registrados'} en tu catálogo."
301:         return self._verified_response(answer, context, {"get_product": products}, {source})
303:     def _product_from_history(self, products, history):
304:         for item in reversed((history or [])[-4:]):
305:             if item.get("role") != "user":
306:                 continue
307:             text = self.intent_router._normalize(str(item.get("content", "")))
308:             matches = [product for product in products if product.get("nombre") and re.search(r"\b" + re.escape(self.intent_router._normalize(product["nombre"])) + r"\b", text)]
309:             if len(matches) == 1:
310:                 return matches[0]
311:             if len(matches) > 1:
312:                 return None
313:         return None
315:     async def _fast_analysis_response(self, kind, request_data, context, user):
316:         arguments = {"id_inventario": request_data.id_inventario} if request_data.id_inventario else {}
317:         summary, source = await self._execute_tool("get_warehouse_status", arguments, user)
318:         data, sources = {"get_warehouse_status": summary}, {source}
319:         inventories = summary.get("inventarios", [])
320:         if request_data.id_producto:
321:             product, product_source = await self._execute_tool("get_product", {"id_producto": request_data.id_producto}, user)
322:             sources.add(product_source)
323:             data["get_product"] = product
324:             inventories = [row for row in inventories if row.get("id_producto") == request_data.id_producto]
325:         elif request_data.history:
326:             products, product_source = await self._execute_tool("get_product", {}, user)
327:             sources.add(product_source)
328:             data["get_product"] = products
329:             product = self._product_from_history(products, request_data.history)
330:             if product:
331:                 inventories = [row for row in inventories if row.get("id_producto") == product["id_producto"]]
332:                 context["producto_consultado"] = {"id_producto": product["id_producto"], "nombre": product.get("nombre")}
333:             elif any(item.get("role") == "user" and re.search(r"muestrame|donde", self.intent_router._normalize(str(item.get("content", "")))) for item in request_data.history[-4:]):
334:                 return self._verified_response("No pude identificar un único producto de tu catálogo en el historial. ¿Qué producto deseas consultar?", context, data, sources)
335:         if not inventories:
336:             return self._verified_response("No hay inventarios visibles para calcular esta consulta. Registra existencias o indica un producto con inventario.", context, data, sources)
337:         text = self.intent_router._normalize(request_data.message or "")
338:         is_risk = kind == "risk" or bool(re.search(r"agot|riesgo|desabastec", text))
339:         if not is_risk and len(inventories) != 1:
340:             return self._verified_response("¿Para qué producto y ubicación deseas consultar la demanda de los próximos 7 días?", context, data, sources)
341:         if not is_risk:
342:             forecast, forecast_source = await self._execute_tool("get_forecast", {"id_inventario": inventories[0]["id_inventario"], "horizonte_dias": 7}, user)
343:             data["get_forecast"] = forecast
344:             sources.add(forecast_source)
345:             return self._verified_response(forecast_answer(forecast), context, data, sources)
346:         results = []
347:         product_names = {row.get("id_producto"): row.get("nombre") for row in summary.get("stock_por_producto", [])}
348:         for inventory in inventories:
349:             result, risk_source = await self._execute_tool("get_inventory_risk", {"id_inventario": inventory["id_inventario"]}, user)
350:             result = dict(result)
351:             if product_names.get(inventory.get("id_producto")):
352:                 result["nombre_producto"] = product_names[inventory["id_producto"]]
353:             results.append(result)
354:             sources.add(risk_source)
355:         data["get_inventory_risk"] = results[0] if len(results) == 1 else results
356:         response = self._verified_response(risk_answer(results), context, data, sources)
357:         if summary.get("total_registros_inventario", len(inventories)) > len(summary.get("inventarios", [])):
358:             response["warnings"].append("El riesgo se evaluó solo para los inventarios incluidos en el resumen; no representa todos los inventarios.")
359:         return response
361:     @staticmethod
362:     def _location_name(message: str) -> str | None:
363:         match = re.search(r"(?:d[oó]nde\s+(?:est[aá]n?|se\s+encuentran?)|ubicaci[oó]n\s+de)\s+(?:(?:el|la|los|las|producto)\s+)?(.+?)[?!.]*$", message, re.IGNORECASE)
364:         if not match:
365:             return None
366:         name = match[1].strip()
367:         if re.search(r"\b(?:y|o|en|cu[aá]nt|explica|busco)\b", name, re.IGNORECASE):
368:             return None
369:         return name or None
371:     async def _fast_location_response(self, name: str, context: dict, user) -> dict:
372:         products, source = await self._execute_tool("get_product", {}, user)
373:         normalized = self.intent_router._normalize(name)
374:         matches = [product for product in products if self.intent_router._normalize(product.get("nombre", "")) == normalized]
375:         if not matches:
376:             matches = [product for product in products if re.search(r"\b" + re.escape(normalized) + r"\b", self.intent_router._normalize(product.get("nombre", "")))]
377:         data = {"get_product": products}
378:         sources = {source}
379:         if not matches:
380:             answer = f"No encontré {name} en el catálogo de tu empresa."
381:         elif len(matches) > 1:
382:             answer = f"Encontré varios productos que coinciden con {name}. ¿Cuál deseas localizar?"
383:         else:
384:             summary, inventory_source = await self._execute_tool("get_warehouse_status", {}, user)
385:             data["get_warehouse_status"] = summary
386:             sources.add(inventory_source)
387:             product = matches[0]
388:             locations = [item for item in summary.get("ubicaciones", []) if item.get("id_producto") == product["id_producto"]]
389:             if not locations:
390:                 answer = f"{product['nombre']} está registrado, pero no encontré una ubicación de inventario en tus almacenes visibles."
391:             elif len(locations) == 1:
392:                 rack = locations[0].get("rack") or {}
393:                 label = rack.get("codigo") or rack.get("nombre")
394:                 answer = f"{product['nombre']} está en el rack {label}." if label else f"{product['nombre']} tiene una ubicación registrada; puedes consultarla en el detalle de inventario."
395:             else:
396:                 answer = f"{product['nombre']} está distribuido en {len(locations)} ubicaciones. Puedes consultar los racks en el detalle de inventario."
397:         response = self._simple_response(answer, "backend", data)
398:         response.update(context=context, sources=sorted(sources))
399:         logger.info("saiki_agent_summary ollama_calls=0 tool_calls=%d source=backend", len(data))
400:         return response
402:     def _simple_response(self, answer: str, source: str, data: dict | None = None):
403:         return {
404:             "answer": answer,
405:             "model": self.settings.ollama_model,
406:             "base_url": self.settings.ollama_base_url,
407:             "source": source,
408:             "context": {},
409:             "data": data or {},
410:             "visualization": {"type": "none"},
411:             "sources": [],
412:             "warnings": [],
413:         }
415:     async def _fast_current_response(self, context: dict, user, kind="general", request_data=None) -> dict:
416:         started = time.perf_counter()
417:         tool = "get_product" if kind == "product_count" else "get_warehouse_status"
418:         try:
419:             result, source = await self._execute_tool(
420:                 tool, ({"include_visual": True, "page": getattr(request_data, "page", 1), "page_size": getattr(request_data, "page_size", 25)} if kind == "general" and request_data is not None else {}), user
421:             )
422:         except RuntimeError as exc:
423:             if "MongoDB" in str(exc) or "motor" in str(exc):
424:                 raise SaikiDatabaseError(str(exc)) from exc
425:             raise
426:         finally:
427:             logger.info(
428:                 "saiki_fast_path tool=%s duration_ms=%d",
429:                 tool,
430:                 round((time.perf_counter() - started) * 1000),
431:             )
432:         if kind == "product_count":
433:             answer = f"Tienes {len(result)} {'producto registrado' if len(result) == 1 else 'productos registrados'} en tu catálogo."
434:         elif kind == "warehouses":
435:             count = result["total_almacenes"]
436:             answer = f"Tienes {count} {'almacén registrado' if count == 1 else 'almacenes registrados'} en PsiTwin." if count else "Actualmente no tienes almacenes registrados en PsiTwin. Te recomiendo crear tu primer almacén."
437:         elif kind == "stock_total":
438:             answer = f"Actualmente tienes {result['stock_total_unidades']} unidades en tu inventario."
439:         else:
440:             answer = self._natural_inventory_answer(result)
441:             if result.get("estado_inventario") == "stock_positivo" and "inventory_summary" in result:
442:                 summary = result["inventory_summary"]
443:                 products_label = "producto diferente" if summary['distinct_products'] == 1 else "productos diferentes"
444:                 warehouses_label = "almacén" if summary['warehouse_count'] == 1 else "almacenes"
445:                 answer = f"Actualmente tienes {summary['distinct_products']} {products_label} y {summary['total_units']} unidades distribuidas en {summary['warehouse_count']} {warehouses_label}."
446:         payload_data = {tool: result}
447:         visualization = {"type": "none"}
448:         if "inventory_summary" in result and kind == "general":
449:             payload_data["inventory_summary"] = result["inventory_summary"]
450:             visualization = result["visualization"]
451:         logger.info("saiki_agent_summary ollama_calls=0 tool_calls=1 source=backend")
452:         return {
453:             "answer": answer,
454:             "model": self.settings.ollama_model,
455:             "base_url": self.settings.ollama_base_url,
456:             "source": "backend",
457:             "context": context,
458:             "data": payload_data,
459:             "visualization": visualization,
460:             "sources": [source],
461:             "warnings": [],
462:         }
464:     @staticmethod
465:     def _natural_inventory_answer(result: dict) -> str:
466:         state = result.get("estado_inventario")
467:         if state == "sin_almacenes":
468:             return (
469:                 "Actualmente no tienes almacenes registrados en PsiTwin. Te "
470:                 "recomiendo crear tu primer almacén para comenzar a gestionar "
471:                 "el inventario."
472:             )
473:         if state == "almacen_sin_productos":
474:             return (
475:                 "Tu almacén está registrado, pero todavía no tienes productos "
476:                 "registrados."
477:             )
478:         if state == "productos_sin_inventario":
479:             return (
480:                 "Tienes productos registrados, pero todavía no hay existencias "
481:                 "de inventario asociadas."
482:             )
483:         if state == "stock_cero":
484:             return (
485:                 "Tienes productos registrados, pero actualmente sus existencias "
486:                 "son cero."
487:             )
488:         if state == "stock_positivo":
489:             products = result.get("productos_distintos", 0)
490:             units = result.get("stock_total_unidades", 0)
491:             return (
492:                 f"Actualmente tienes {products} {'producto distinto' if products == 1 else 'productos distintos'} y "
493:                 f"{units} {'unidad registrada' if units == 1 else 'unidades registradas'} en tu inventario."
494:             )
495:         raise RuntimeError("La consulta de inventario no devolvió un estado válido.")
497:     async def _authorized_tool(self, name, arguments, user):
498:         result, _ = await self.tools.execute(name, arguments, user)
499:         return result
501:     async def _execute_tool(self, name, arguments, user=None):
502:         if user is None:
503:             return await self.tools.execute(name, arguments)
504:         return await self.tools.execute(name, arguments, user)
506:     async def _agent_loop(
507:         self,
508:         messages: list[dict],
509:         user: UsuarioActual | None = None,
510:         tool_names: frozenset[str] | None = None,
511:     ) -> tuple[str, dict, set[str]]:
512:         tool_data: dict[str, object] = {}
513:         sources: set[str] = set()
514:         seen_calls: dict[str, Any] = {}
515:         ollama_calls = 0
516:         tool_calls_count = 0
517:         for iteration in range(1, self.max_tool_iterations + 1):
518:             call_started = time.perf_counter()
519:             response = await asyncio.to_thread(self._call_ollama_chat, messages, tool_names)
520:             ollama_calls += 1
521:             logger.info(
522:                 "saiki_agent_iteration iteration=%d ollama_duration_ms=%d",
523:                 iteration,
524:                 round((time.perf_counter() - call_started) * 1000),
525:             )
526:             message = response.get("message")
527:             if not isinstance(message, dict):
528:                 raise RuntimeError("Ollama devolvió un mensaje inválido.")
529:             tool_calls = message.get("tool_calls") or []
530:             if not tool_calls:
531:                 answer = message.get("content")
532:                 if not isinstance(answer, str) or not answer.strip():
533:                     raise RuntimeError("Ollama no devolvió una respuesta útil.")
534:                 logger.info(
535:                     "saiki_agent_summary ollama_calls=%d tool_calls=%d",
536:                     ollama_calls,
537:                     tool_calls_count,
538:                 )
539:                 answer = self._clean_answer(answer)
540:                 if not answer:
541:                     raise RuntimeError("Ollama solo devolvió razonamiento interno.")
542:                 return answer, tool_data, sources
544:             messages.append(message)
545:             for tool_call in tool_calls:
546:                 name, arguments = self._parse_tool_call(tool_call)
547:                 if tool_names is not None and name not in tool_names:
548:                     raise ValueError(f"Tool no autorizada para esta consulta: {name}")
549:                 call_key = json.dumps(
550:                     [name, arguments], sort_keys=True, ensure_ascii=False
551:                 )
552:                 if call_key in seen_calls:
553:                     result, source = seen_calls[call_key]
554:                     logger.info("saiki_tool_duplicate name=%s", name)
555:                 else:
556:                     tool_started = time.perf_counter()
557:                     try:
558:                         result, source = await self._execute_tool(name, arguments, user)
559:                     except RuntimeError as exc:
560:                         if "MongoDB" in str(exc) or "motor" in str(exc):
561:                             raise SaikiDatabaseError(str(exc)) from exc
562:                         raise
563:                     finally:
564:                         logger.info(
565:                             "saiki_tool name=%s duration_ms=%d",
566:                             name,
567:                             round((time.perf_counter() - tool_started) * 1000),
568:                         )
569:                     seen_calls[call_key] = (result, source)
570:                 tool_calls_count += 1
571:                 sources.add(source)
572:                 tool_data[name] = result
573:                 messages.append(
574:                     {
575:                         "role": "tool",
576:                         "tool_name": name,
577:                         "content": json.dumps(result, ensure_ascii=False, default=str),
578:                     }
579:                 )
580:         logger.warning(
581:             "saiki_agent_limit iterations=%d ollama_calls=%d tool_calls=%d",
582:             self.max_tool_iterations,
583:             ollama_calls,
584:             tool_calls_count,
585:         )
586:         raise RuntimeError("Se alcanzó el límite de consultas de Saiki.")
588:     def _call_ollama_chat(self, messages: list[dict], tool_names=None) -> dict:
589:         url = f"{self.settings.ollama_base_url.rstrip('/')}/api/chat"
590:         payload = {
591:             "model": self.settings.ollama_model,
592:             "messages": messages,
593:             "tools": self.tools.definitions(tool_names),
594:             "stream": False,
595:             "think": False,
596:         }
597:         req = request.Request(
598:             url,
599:             data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
600:             headers={"Content-Type": "application/json"},
601:             method="POST",
602:         )
603:         parsed = urlsplit(url)
604:         connection_class = (
605:             http.client.HTTPSConnection
606:             if parsed.scheme == "https"
607:             else http.client.HTTPConnection
608:         )
609:         started = time.perf_counter()
610:         connection = None
611:         try:
612:             connection = connection_class(
613:                 parsed.hostname,
614:                 parsed.port,
615:                 timeout=self.settings.ollama_connect_timeout_seconds,
616:             )
617:             connection.request(
618:                 "POST",
619:                 parsed.path or "/",
620:                 body=req.data,
621:                 headers=dict(req.headers),
622:             )
623:             if connection.sock is not None:
624:                 connection.sock.settimeout(self.settings.ollama_read_timeout_seconds)
625:             response = connection.getresponse()
626:             result = json.loads(response.read().decode("utf-8"))
627:             if response.status >= 400:
628:                 raise OllamaUnavailableError(
629:                     f"Ollama respondió HTTP {response.status}."
630:                 )
631:         except (TimeoutError, socket.timeout) as exc:
632:             raise OllamaTimeoutError("Tiempo de espera agotado con Ollama.") from exc
633:         except (OSError, http.client.HTTPException, error.URLError) as exc:
634:             raise OllamaUnavailableError("No se pudo conectar con Ollama.") from exc
635:         except json.JSONDecodeError as exc:
636:             raise OllamaUnavailableError("Ollama devolvió JSON inválido.") from exc
637:         finally:
638:             if connection is not None:
639:                 connection.close()
640:             logger.info(
641:                 "saiki_ollama duration_ms=%d",
642:                 round((time.perf_counter() - started) * 1000),
643:             )
644:         if not isinstance(result, dict):
645:             raise RuntimeError("Ollama devolvió una respuesta inválida.")
646:         logger.info("saiki_ollama_metrics total_ns=%s load_ns=%s prompt_tokens=%s output_tokens=%s", result.get("total_duration"), result.get("load_duration"), result.get("prompt_eval_count"), result.get("eval_count"))
647:         return result
649:     @staticmethod
650:     def _clean_answer(answer: str) -> str:
651:         if "</think>" in answer:
652:             answer = answer.rsplit("</think>", 1)[1]
653:         if "<think>" in answer:
654:             answer = answer.split("<think>", 1)[0]
655:         return answer.strip()
657:     def _parse_tool_call(self, tool_call: object) -> tuple[str, dict]:
658:         if not isinstance(tool_call, dict):
659:             raise ValueError("Tool call inválida.")
660:         function = tool_call.get("function")
661:         if not isinstance(function, dict) or not isinstance(function.get("name"), str):
662:             raise ValueError("Tool call inválida.")
663:         arguments = function.get("arguments", {})
664:         if isinstance(arguments, str):
665:             try:
666:                 arguments = json.loads(arguments)
667:             except json.JSONDecodeError as exc:
668:                 raise ValueError("Los argumentos de la tool no son JSON válido.") from exc
669:         if not isinstance(arguments, dict):
670:             raise ValueError("Los argumentos de la tool deben ser un objeto.")
671:         return function["name"], arguments
673:     @staticmethod
674:     def _build_prompt(question: str, context: dict) -> str:
675:         return (
676:             "Usa únicamente el contexto y las tools autorizadas. No inventes datos. "
677:             "Si falta información, dilo claramente.\n\n"
678:             f"CONTEXTO PSI TWIN:\n{json.dumps(context, ensure_ascii=False, default=str, indent=2)}"
679:             f"\n\nPREGUNTA:\n{question}"
680:         )
682:     @staticmethod
683:     def _visualization(data: dict) -> dict:
684:         return {"type": "none"} if not data else {"type": "table", "data": data}
686:     @staticmethod
687:     def _warnings(sources: set[str], data: dict | None = None) -> list[str]:
688:         warnings = []
689:         if "INVENTORY_RISK" in sources:
690:             warnings.append("El riesgo proviene de InventoryRiskService.")
691:         if "LIGHTGBM" in sources:
692:             warnings.append("La predicción proviene del pipeline LightGBM.")
693:             warnings.append("La predicción depende del historial disponible y representa demanda, no stock futuro.")
694:             forecast = (data or {}).get("get_forecast")
695:             if isinstance(forecast, dict) and any(item.get("sin_datos", 0) > 0 for item in forecast.get("features_por_horizonte", {}).values() if isinstance(item, dict)):
696:                 warnings.append("Hay variables sin datos en el modelo; interpreta la predicción con esa limitación.")
697:         return warnings
```

### app/services/saiki_tools.py

```python
1: from typing import Any, Awaitable, Callable
2: import logging
3: import time
5: from pydantic import BaseModel, ConfigDict, Field
7: from app.controllers.forecast_controller import predict_7_days
8: from app.repositories.producto_repository import ProductoRepository
9: from app.repositories.almacen_repository import AlmacenRepository
10: from app.repositories.rack_repository import RackRepository
11: from app.repositories.zona_repository import ZonaRepository
12: from app.services.alerta_service import AlertaService
13: from app.services.inventario_service import InventarioService
14: from app.services.inventory_risk_service import InventoryRiskService
15: from app.services.movimiento_service import MovimientoService
16: from app.services.recomendacion_service import RecomendacionService
17: from app.services.acceso_service import AccesoService
18: from app.dto.auth_dto import UsuarioActual
20: logger = logging.getLogger(__name__)
23: class InventoryArgs(BaseModel):
24:     id_inventario: str = Field(min_length=1)
27: class ProductArgs(BaseModel):
28:     id_producto: str | None = Field(default=None, min_length=1, description="Producto específico; omitir para consultar el catálogo de la empresa autenticada.")
31: class ForecastArgs(BaseModel):
32:     model_config = ConfigDict(extra="forbid")
33:     id_inventario: str = Field(min_length=1)
34:     dias: int = Field(default=30, ge=7, le=500, description="Ventana histórica; no es el horizonte de predicción.")
35:     horizonte_dias: int = Field(default=7, ge=7, le=7, description="Horizonte disponible: siete días de demanda, no stock futuro.")
38: class OptionalInventoryArgs(BaseModel):
39:     id_inventario: str | None = None
42: class WarehouseStatusArgs(OptionalInventoryArgs):
43:     include_visual: bool = False
44:     page: int = Field(default=1, ge=1)
45:     page_size: int = Field(default=25, ge=1, le=100)
48: ToolHandler = Callable[..., Awaitable[Any]]
51: class SaikiToolRegistry:
52:     """Whitelist of read-only operations available to Saiki."""
54:     def __init__(self):
55:         self.inventario_service = InventarioService()
56:         self.risk_service = InventoryRiskService()
57:         self.alerta_service = AlertaService()
58:         self.recomendacion_service = RecomendacionService()
59:         self.movimiento_service = MovimientoService()
60:         self._handlers: dict[str, tuple[type[BaseModel], ToolHandler, str]] = {
61:             "get_inventory": (
62:                 InventoryArgs,
63:                 self.get_inventory,
64:                 "INVENTARIO",
65:             ),
66:             "get_product": (
67:                 ProductArgs,
68:                 self.get_product,
69:                 "PRODUCTO",
70:             ),
71:             "get_forecast": (
72:                 ForecastArgs,
73:                 self.get_forecast,
74:                 "LIGHTGBM",
75:             ),
76:             "get_inventory_risk": (
77:                 InventoryArgs,
78:                 self.get_inventory_risk,
79:                 "INVENTORY_RISK",
80:             ),
81:             "get_active_alerts": (
82:                 OptionalInventoryArgs,
83:                 self.get_active_alerts,
84:                 "ALERTAS",
85:             ),
86:             "get_recommendations": (
87:                 OptionalInventoryArgs,
88:                 self.get_recommendations,
89:                 "RECOMENDACIONES",
90:             ),
91:             "get_recent_movements": (
92:                 OptionalInventoryArgs,
93:                 self.get_recent_movements,
94:                 "MOVIMIENTOS",
95:             ),
96:             "get_warehouse_status": (
97:                 WarehouseStatusArgs,
98:                 self.get_warehouse_status,
99:                 "INVENTARIO",
100:             ),
101:         }
103:     @property
104:     def names(self) -> set[str]:
105:         return set(self._handlers)
107:     def definitions(
108:         self,
109:         names: set[str] | frozenset[str] | None = None,
110:     ) -> list[dict[str, Any]]:
111:         return [
112:             {
113:                 "type": "function",
114:                 "function": {
115:                     "name": name,
116:                     "description": (
117:                         "Consulta de solo lectura. "
118:                         + (
119:                             "Para un resumen general del almacén no requiere argumentos."
120:                             if name == "get_warehouse_status"
121:                             else f"Tool autorizada: {name}."
122:                         )
123:                     ),
124:                     "parameters": model.model_json_schema(),
125:                 },
126:             }
127:             for name, (model, _, _) in self._handlers.items()
128:             if names is None or name in names
129:         ]
131:     async def execute(
132:         self,
133:         name: str,
134:         arguments: dict[str, Any],
135:         user=None,
136:     ) -> tuple[Any, str]:
137:         if name not in self._handlers:
138:             raise ValueError(f"Tool no autorizada: {name}")
139:         model, handler, source = self._handlers[name]
140:         try:
141:             validated = model.model_validate(arguments)
142:         except Exception as exc:
143:             raise ValueError(f"Argumentos inválidos para {name}: {exc}") from exc
144:         visible = None
145:         started = time.perf_counter()
146:         if user is not None:
147:             visible = await self._authorize(name, validated, user)
148:         logger.info("saiki_authorization tool=%s duration_ms=%.3f", name, (time.perf_counter() - started) * 1000)
149:         started = time.perf_counter()
150:         try:
151:             if name == "get_warehouse_status":
152:                 return await handler(validated, user, visible), source
153:             if name == "get_product":
154:                 return await handler(validated, user), source
155:             if name in {"get_active_alerts", "get_recommendations", "get_recent_movements"}:
156:                 return await handler(validated, visible), source
157:             return await handler(validated), source
158:         finally:
159:             logger.info("saiki_data_query tool=%s duration_ms=%.3f", name, (time.perf_counter() - started) * 1000)
161:     async def _authorize(self, name: str, args: BaseModel, user):
162:         if name == "get_warehouse_status" and getattr(args, "include_visual", False) and not args.id_inventario:
164:             return None
165:         visible = frozenset(await AccesoService.ids_inventarios(user))
166:         if hasattr(args, "id_inventario") and args.id_inventario:
167:             await AccesoService.verificar_inventario(user, args.id_inventario)
168:         if name == "get_product" and args.id_producto:
169:             await AccesoService.verificar_producto(user, args.id_producto)
170:         return visible
172:     async def get_inventory(self, args: InventoryArgs):
173:         return await self.inventario_service.obtener_inventario(args.id_inventario)
175:     async def get_product(self, args: ProductArgs, user=None):
176:         if args.id_producto:
177:             return await ProductoRepository.obtener_por_id(args.id_producto)
178:         products = await ProductoRepository.obtener_todos()
179:         return [item for item in products if user is None or item.get("id_empresa") == user.id_empresa]
181:     async def get_forecast(self, args: ForecastArgs):
182:         return await predict_7_days(args.id_inventario, args.dias)
184:     async def get_inventory_risk(self, args: InventoryArgs):
185:         result = await self.risk_service.evaluar(
186:             id_inventario=args.id_inventario,
187:             generar_alertas=False,
188:         )
189:         return result.model_dump(mode="python")
191:     async def get_active_alerts(self, args: OptionalInventoryArgs, visible=None):
192:         if args.id_inventario:
193:             alerts = await self.alerta_service.listar_por_inventario(args.id_inventario)
194:             return [item for item in alerts if item.get("estado") == "ACTIVA"]
195:         alerts = await self.alerta_service.listar_activas()
196:         return [item for item in alerts if visible is None or item.get("id_inventario") in visible]
198:     async def get_recommendations(self, args: OptionalInventoryArgs, visible=None):
199:         if args.id_inventario:
200:             return await self.recomendacion_service.listar_por_inventario(
201:                 args.id_inventario
202:             )
203:         recommendations = await self.recomendacion_service.listar()
204:         return [
205:             item
206:             for item in recommendations
207:             if visible is None or item.get("id_inventario") in visible
208:         ]
210:     async def get_recent_movements(self, args: OptionalInventoryArgs, visible=None):
211:         if args.id_inventario:
212:             movements = await self.movimiento_service.obtener_por_inventario(args.id_inventario)
213:         else:
214:             movements = await self.movimiento_service.obtener_movimientos()
215:             movements = [item for item in movements if visible is None or item.get("id_inventario") in visible]
216:         return sorted(
217:             movements,
218:             key=lambda item: str(item.get("fecha_hora", "")),
219:             reverse=True,
220:         )[:20]
222:     async def get_warehouse_status(
223:         self,
224:         args: OptionalInventoryArgs,
225:         user: UsuarioActual | None = None,
226:         visible=None,
227:     ):
228:         if getattr(args, "include_visual", False):
229:             from app.services.saiki_inventory_summary import inventory_summary
230:             return await inventory_summary(user, args.page, args.page_size)
231:         visible_warehouse_ids = None
232:         if user is not None:
233:             visible_warehouse_ids = await AccesoService.ids_almacenes(user)
234:         warehouses = await AlmacenRepository.obtener_todos()
235:         if visible_warehouse_ids is not None:
236:             warehouses = [
237:                 warehouse
238:                 for warehouse in warehouses
239:                 if (warehouse.get("id_almacen") or warehouse.get("id"))
240:                 in visible_warehouse_ids
241:             ]
242:         if not warehouses:
243:             return {
244:                 "estado_inventario": "sin_almacenes",
245:                 "total_almacenes": 0,
246:                 "mensaje": (
247:                     "Actualmente no tienes almacenes registrados en PsiTwin. "
248:                     "Primero debes crear uno para comenzar a gestionar tu inventario."
249:                 ),
250:                 "total_registros_inventario": 0,
251:                 "productos_distintos": 0,
252:                 "stock_total_unidades": 0,
253:                 "almacenes": [],
254:                 "stock_por_producto": [],
255:                 "ubicaciones": [],
256:                 "inventarios": [],
257:             }
259:         if visible_warehouse_ids is not None:
260:             visible_zone_ids = {
261:                 zone.get("id_zona", zone.get("id"))
262:                 for zone in await ZonaRepository.obtener_todas()
263:                 if zone.get("id_almacen") in visible_warehouse_ids
264:             }
265:             visible_rack_ids = {
266:                 rack.get("id_rack") or rack.get("id")
267:                 for rack in await RackRepository.obtener_todos()
268:                 if rack.get("id_zona") in visible_zone_ids
269:             }
270:         else:
271:             visible_rack_ids = None
273:         inventories = await self.inventario_service.obtener_inventarios()
274:         if visible is not None:
275:             inventories = [
276:                 item for item in inventories
277:                 if item.get("id_inventario") in visible
278:             ]
279:         if args.id_inventario:
280:             inventories = [
281:                 item for item in inventories
282:                 if item.get("id_inventario") == args.id_inventario
283:             ]
285:         if visible_rack_ids is not None:
286:             inventories = [
287:                 item for item in inventories
288:                 if item.get("id_rack") in visible_rack_ids
289:             ]
291:         product_ids = {
292:             item.get("id_producto")
293:             for item in inventories
294:             if item.get("id_producto")
295:         }
296:         all_products = await ProductoRepository.obtener_todos()
297:         products = {
298:             product["id_producto"]: product
299:             for product in all_products
300:             if (
301:                 product.get("id_producto") in product_ids
302:                 or visible_rack_ids is None
303:                 or (user is not None and product.get("id_empresa") == user.id_empresa)
304:             )
305:         }
306:         if not inventories and not products:
307:             return {
308:                 "estado_inventario": "almacen_sin_productos",
309:                 "total_almacenes": len(warehouses),
310:                 "mensaje": (
311:                     "Tu almacén está registrado, pero todavía no tienes "
312:                     "productos registrados."
313:                 ),
314:                 "total_registros_inventario": 0,
315:                 "productos_distintos": 0,
316:                 "stock_total_unidades": 0,
317:                 "almacenes": warehouses,
318:                 "stock_por_producto": [],
319:                 "ubicaciones": [],
320:                 "inventarios": [],
321:             }
322:         if not inventories:
323:             return {
324:                 "estado_inventario": "productos_sin_inventario",
325:                 "total_almacenes": len(warehouses),
326:                 "mensaje": (
327:                     "Tienes productos registrados, pero todavía no hay "
328:                     "existencias de inventario asociadas."
329:                 ),
330:                 "total_registros_inventario": 0,
331:                 "productos_distintos": len(products),
332:                 "stock_total_unidades": 0,
333:                 "almacenes": warehouses,
334:                 "stock_por_producto": [],
335:                 "ubicaciones": [],
336:                 "inventarios": [],
337:             }
338:         rack_ids = {
339:             item.get("id_rack")
340:             for item in inventories
341:             if item.get("id_rack")
342:         }
343:         racks = {
344:             (rack.get("id_rack") or rack.get("id")): rack
345:             for rack in await RackRepository.obtener_todos()
346:             if (rack.get("id_rack") or rack.get("id")) in rack_ids
347:         }
348:         zone_ids = {
349:             rack.get("id_zona")
350:             for rack in racks.values()
351:             if rack.get("id_zona")
352:         }
353:         zones = {
354:             zone.get("id_zona", zone.get("id")): zone
355:             for zone in await ZonaRepository.obtener_todas()
356:             if zone.get("id_zona", zone.get("id")) in zone_ids
357:         }
358:         warehouse_ids = {
359:             zone.get("id_almacen")
360:             for zone in zones.values()
361:             if zone.get("id_almacen")
362:         }
363:         warehouses_by_id = {
364:             almacen.get("id_almacen", almacen.get("id")): almacen
365:             for almacen in warehouses
366:             if almacen.get("id_almacen", almacen.get("id")) in warehouse_ids
367:         }
368:         stock_by_product: dict[str, int | float] = {}
369:         for item in inventories:
370:             product_id = item.get("id_producto")
371:             stock_by_product[product_id] = (
372:                 stock_by_product.get(product_id, 0)
373:                 + (item.get("stock_actual", 0) or 0)
374:             )
376:         result = {
377:             "total_almacenes": len(warehouses),
378:             "total_registros_inventario": len(inventories),
379:             "productos_distintos": len(product_ids),
380:             "stock_total_unidades": sum(stock_by_product.values()),
381:             "stock_por_producto": [
382:                 {
383:                     "id_producto": product_id,
384:                     "nombre": products.get(product_id, {}).get("nombre"),
385:                     "stock_actual": stock,
386:                 }
387:                 for product_id, stock in stock_by_product.items()
388:             ],
389:             "almacenes": list(warehouses_by_id.values()),
390:             "ubicaciones": [
391:                 {
392:                     "id_inventario": item.get("id_inventario"),
393:                     "id_producto": item.get("id_producto"),
394:                     "id_rack": item.get("id_rack"),
395:                     "rack": racks.get(item.get("id_rack")),
396:                     "zona": zones.get(
397:                         racks.get(item.get("id_rack"), {}).get("id_zona")
398:                     ),
399:                     "stock_actual": item.get("stock_actual", 0),
400:                 }
401:                 for item in inventories
402:             ],
403:             "inventarios": inventories[:50],
404:         }
405:         if all(stock <= 0 for stock in stock_by_product.values()):
406:             result["estado_inventario"] = "stock_cero"
407:             result["mensaje"] = (
408:                 "Tienes productos registrados, pero actualmente sus existencias son cero."
409:             )
410:         else:
411:             result["estado_inventario"] = "stock_positivo"
412:         return result
```

## Configuración real del artefacto (sin credenciales)

```json
{
  "version": "PSITWIN V3.6 WAPE-FOCUSED DIRECT HORIZON ENSEMBLE (FIXED)",
  "dataset": "/kaggle/input/datasets/omniscientreader2025/data-procesada-gemini/psitwin_m5_base_v2.pkl",
  "features": [
    "item_id",
    "dept_id",
    "cat_id",
    "store_id",
    "state_id",
    "month",
    "year",
    "dayofweek",
    "day",
    "weekofyear",
    "is_weekend",
    "has_event",
    "quarter",
    "dayofyear",
    "is_month_start",
    "is_month_end",
    "snap",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2",
    "age_days",
    "current_y",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_4",
    "lag_5",
    "lag_6",
    "lag_7",
    "lag_14",
    "lag_21",
    "lag_28",
    "lag_35",
    "lag_42",
    "lag_56",
    "lag_364",
    "lag_365",
    "lag_366",
    "rolling_mean_3",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_28",
    "rolling_mean_56",
    "rolling_mean_180",
    "rolling_std_3",
    "rolling_std_7",
    "rolling_std_28",
    "rolling_std_56",
    "rolling_max_3",
    "rolling_max_7",
    "rolling_max_28",
    "ewma_3",
    "ewma_7",
    "ewma_14",
    "ewma_28",
    "zero_ratio_7",
    "zero_ratio_28",
    "change_1_2",
    "change_1_3",
    "change_1_7",
    "ratio_mean3_mean14",
    "ratio_mean7_mean28",
    "acceleration_3_7",
    "acceleration_7_28",
    "max7_vs_mean28",
    "max3_vs_mean28",
    "previous_7_mean",
    "recent7_vs_previous7",
    "dow_mean_4w",
    "growth_streak_3",
    "peak_count_7",
    "rolling_inc_mean_3",
    "rolling_inc_mean_7",
    "rolling_inc_mean_14",
    "rolling_inc_mean_28",
    "rolling_inc_std_7",
    "rolling_inc_std_28",
    "days_since_sale",
    "sale_rate_28",
    "current_vs_mean7",
    "current_vs_mean28",
    "sell_price",
    "price_available",
    "price_lag_1",
    "price_lag_7",
    "price_change_1",
    "price_change_7",
    "price_mean_28",
    "price_relative_28",
    "price_mean_180",
    "price_std_180",
    "price_min_180",
    "price_max_180",
    "price_relative_180",
    "price_to_max_180",
    "price_range_position_180",
    "store_sales_lag_1",
    "store_sales_lag_7",
    "store_sales_lag_28",
    "store_sales_mean_7",
    "store_sales_mean_28",
    "dept_sales_lag_1",
    "dept_sales_lag_7",
    "dept_sales_lag_28",
    "dept_sales_mean_7",
    "dept_sales_mean_28",
    "item_total_lag_1",
    "item_total_lag_7",
    "item_total_lag_28",
    "target_month",
    "target_dayofweek",
    "target_day",
    "target_weekofyear",
    "target_is_weekend",
    "target_quarter",
    "target_dayofyear",
    "future_sell_price",
    "future_price_available",
    "future_snap",
    "future_has_event",
    "future_event_name_1_code",
    "future_event_type_1_code",
    "future_lag_7",
    "future_lag_14",
    "future_lag_21",
    "future_lag_28",
    "future_lag_35",
    "future_lag_42",
    "future_lag_364",
    "future_lag_365",
    "future_lag_366",
    "future_dow_mean_6w",
    "future_dow_std_6w",
    "future_store_lag_7",
    "future_dept_lag_7"
  ],
  "categorical_features": [
    "item_id",
    "dept_id",
    "cat_id",
    "store_id",
    "state_id",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2"
  ],
  "selection_by_horizon": {
    "1": {
      "candidate1": "L1_FAST",
      "candidate2": "L1_FAST",
      "beta2": 0,
      "scale": 1.15,
      "rounds1": 899,
      "rounds2": 899,
      "alpha1": 1,
      "alpha2": 1
    },
    "2": {
      "candidate1": "L1_FAST",
      "candidate2": "L1_FAST",
      "beta2": 0,
      "scale": 1.15,
      "rounds1": 900,
      "rounds2": 900,
      "alpha1": 1,
      "alpha2": 1
    },
    "3": {
      "candidate1": "L1_FAST",
      "candidate2": "L1_FAST",
      "beta2": 0,
      "scale": 1.15,
      "rounds1": 900,
      "rounds2": 900,
      "alpha1": 1,
      "alpha2": 1
    },
    "4": {
      "candidate1": "L1_FAST",
      "candidate2": "L1_FAST",
      "beta2": 0,
      "scale": 1.15,
      "rounds1": 890,
      "rounds2": 890,
      "alpha1": 0.75,
      "alpha2": 0.75
    },
    "5": {
      "candidate1": "L1_FAST",
      "candidate2": "L1_FAST",
      "beta2": 0,
      "scale": 1.15,
      "rounds1": 900,
      "rounds2": 900,
      "alpha1": 0.5,
      "alpha2": 0.5
    },
    "6": {
      "candidate1": "L1_FAST",
      "candidate2": "L1_FAST",
      "beta2": 0,
      "scale": 1.15,
      "rounds1": 499,
      "rounds2": 499,
      "alpha1": 1,
      "alpha2": 1
    },
    "7": {
      "candidate1": "L1_FAST",
      "candidate2": "L1_FAST",
      "beta2": 0,
      "scale": 1.15,
      "rounds1": 900,
      "rounds2": 900,
      "alpha1": 0.75,
      "alpha2": 0.75
    }
  },
  "valid_wape": 57.34627067879436,
  "valid_bias": -5.250047281943216,
  "test_wape": 57.632836510216364,
  "test_bias": -7.643220664247457
}
```


Verificación de artefactos: se leyeron headers de70/70 archivos; todos declararon136 features en el mismo orden de config y objective regression_l1. No se ejecutó predict ni training.
