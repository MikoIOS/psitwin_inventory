# Requisitos predictivos: actual y propuesta

## Implementación actual

`app/ml/demand_history.py` consulta `MovimientoRepository`, suma cantidad de todas las SALIDA por día UTC/id_inventario y rellena fechas sin salidas con 0. Devuelve DataFrame con **fecha** (datetime parseable) y **demanda** (float). No consume ventas_diarias.csv. Inventario→producto/rack→zona→almacén identifica la serie; la demanda del backend significa consumo por salidas, no demanda latente.

`FeatureBuilder` requiere fecha/demanda, ordena historial y construye calendario, lags, rolling, EWMA y cambios. `_prepare_history` conserva última fila duplicada y convierte demanda inválida a cero: el generador debe rechazar ambos errores antes de llegar ahí. std ddof=0; EWMA adjust=False. Historia recomendada>=367 días para lags anuales y>=180 para rolling/precios; calentamiento sin ceros inventados.

Detalle de alineación: `_lag(series,k)=series.iloc[-k]`; **lag_1=última observación t, igual a current_y**, no t-1. future_lag_k usa _lag(k-h) si positivo, y última observación si cero. No asumir fórmula convencional del entrenamiento anterior. Adaptador legacy futuro replica esta semántica; evaluación nueva usa y(t-k) y future_lag_k=y(t+h-k) con fecha<=t, documentando diferencia. No mezclar perfiles.

`MLContextBuilder` usa MAX_LAG=28 (29 fechas) y arma agregados store/dept/item, además de future_store/dept_lag_7. Selección de productos por rack de referencia y posterior suma por IDs sin almacén produce incompatibilidad para SKU compartidos: ver RELATIONSHIPS. No afirmar que contexto resuelve todos los datos pendientes.

`DemandPredictor` usa LightGBM global Direct Horizon D+1..D+7; recorta negativos a cero. Devuelve demanda_7d, predicciones_diarias (horizonte, fecha, demanda_predicha), no archivos ni entrenamiento. `ModelLoader` carga config_v3_6.json, selection_by_horizon.csv (pandas) y boosters nativos models/L1_FAST__global_D1.txt..D7.txt. Tiene carga de locales, pero predictor actual usa globals y no aplica automáticamente ensemble/scale de selection.

Config identifica dataset Kaggle `psitwin_m5_base_v2.pkl`: es metadata del entrenamiento anterior, **no lector pickle del backend**. No está el dataset/pipeline de entrenamiento. No existe importación histórica CSV/Parquet/XLSX en módulos auditados. Features exactas/categóricas de config se incluyen más abajo; cabecera booster global coincide con 136 features, objetivo regression_l1. Métricas M5 de config no son metas del generador.

Identificación item_id/dept_id/cat_id/store_id/state_id, precios, eventos/SNAP requieren context externo; si falta quedan NaN. Categorías se convierten con pandas category; el código no traduce UUID PsiTwin a vocabularios aprendidos M5. Los nuevos códigos de series_mapping no garantizan inferencia válida con esos boosters.

## API y recomendaciones

Base `/api/v1/forecast`: debug-history/{id_inventario}, debug-context/{id_inventario}, debug-features/{id_inventario}, debug-predict/{id_inventario}, predict-7-days/{id_inventario}, debug-feature-info. Autenticación/ámbito según controladores/acceso_service. dias default 30 (hasta 500), horizonte individual 1..7. Saiki get_forecast llama a predict_7_days; horizonte_dias solo 7.

`InventoryRiskService` consulta **30 días**, genera 7 horizontes y calcula consumo=max(media histórica con fallback 7/14/28, forecast_7d/7), cobertura, seguridad=1.645*std28*sqrt(lead), punto=consumo*lead+seguridad, cantidades para lead+7 días. Puede crear alertas/recomendaciones. 30 días no alimentan lag_366/rolling_180; missing_features solo valida presencia de claves, no calidad/suficiencia. No ejecutar estos endpoints para validar/generar datos.

Backend usa fecha actual. Cortes históricos no se inyectan desde manifest ni CSV. Una historia 2020–2025 no garantiza demanda reciente al ejecutar en octubre 2026. No generar forecast precalculado como solución.

## Extensión propuesta para trabajo ML independiente

ventas_diarias, precios, calendario y series_mapping son **fuentes nuevas sin DTO/consumidor backend**. Objetivo nuevo: ventas_observadas(t+h) por producto+almacén (una ubicación por serie demo). Demanda latente/perdidas/stockout explican censura, nunca se pasan como features observadas. Experimento latente solo separado y etiquetado.

Calendario y precios futuros utilizables únicamente si conocido_en<=origen. SNAP=0 porque no se simula ese programa; códigos de campañas sintéticas, sin afirmar feriados verificados. Agregados nuevos se filtran correctamente por almacén/familia y usan observaciones<=t; no copiar error de alcance backend a evaluación honesta.

TRAIN por fecha objetivo 2020-01-01..2023-12-31; VALID 2024-01-01..2024-12-31; TEST 2025-01-01..2025-12-31. 2020 calentamiento cuando se exigen lags anuales. Origen t, etiqueta y(t+h), h=1..7. Fila multiobjetivo que cruza corte se excluye; formato largo asigna split por target_date. Encoders/imputadores/escaladores ajustados solo TRAIN, UNKNOWN explícito. VALID/TEST pueden usar pasado observado en rolling origin, sin usar futuro al origen. TEST no selecciona modelos/semillas.

No entrenar durante generación inicial. Proyecto B entrega fuentes y opcionalmente código de preparación/evaluación, sin ejecutarlo para optimizar métricas. No exigir matriz de features materializada: las fuentes completas permiten crearla en trabajo posterior. Separar features de consumo legacy y ventas nuevas.

## Features exactas del modelo anterior

Fuente: app/ml/models/psitwin_v3_6/config_v3_6.json. 136 columnas en este orden; matriz ML, no campos Producto. Numericas salvo las categorias listadas; flags 0/1, lags/estadisticas/precios float, calendario enteros. NaN de perfil legacy no certifica suficiencia.

```text
item_id
dept_id
cat_id
store_id
state_id
month
year
dayofweek
day
weekofyear
is_weekend
has_event
quarter
dayofyear
is_month_start
is_month_end
snap
event_name_1
event_type_1
event_name_2
event_type_2
age_days
current_y
lag_1
lag_2
lag_3
lag_4
lag_5
lag_6
lag_7
lag_14
lag_21
lag_28
lag_35
lag_42
lag_56
lag_364
lag_365
lag_366
rolling_mean_3
rolling_mean_7
rolling_mean_14
rolling_mean_28
rolling_mean_56
rolling_mean_180
rolling_std_3
rolling_std_7
rolling_std_28
rolling_std_56
rolling_max_3
rolling_max_7
rolling_max_28
ewma_3
ewma_7
ewma_14
ewma_28
zero_ratio_7
zero_ratio_28
change_1_2
change_1_3
change_1_7
ratio_mean3_mean14
ratio_mean7_mean28
acceleration_3_7
acceleration_7_28
max7_vs_mean28
max3_vs_mean28
previous_7_mean
recent7_vs_previous7
dow_mean_4w
growth_streak_3
peak_count_7
rolling_inc_mean_3
rolling_inc_mean_7
rolling_inc_mean_14
rolling_inc_mean_28
rolling_inc_std_7
rolling_inc_std_28
days_since_sale
sale_rate_28
current_vs_mean7
current_vs_mean28
sell_price
price_available
price_lag_1
price_lag_7
price_change_1
price_change_7
price_mean_28
price_relative_28
price_mean_180
price_std_180
price_min_180
price_max_180
price_relative_180
price_to_max_180
price_range_position_180
store_sales_lag_1
store_sales_lag_7
store_sales_lag_28
store_sales_mean_7
store_sales_mean_28
dept_sales_lag_1
dept_sales_lag_7
dept_sales_lag_28
dept_sales_mean_7
dept_sales_mean_28
item_total_lag_1
item_total_lag_7
item_total_lag_28
target_month
target_dayofweek
target_day
target_weekofyear
target_is_weekend
target_quarter
target_dayofyear
future_sell_price
future_price_available
future_snap
future_has_event
future_event_name_1_code
future_event_type_1_code
future_lag_7
future_lag_14
future_lag_21
future_lag_28
future_lag_35
future_lag_42
future_lag_364
future_lag_365
future_lag_366
future_dow_mean_6w
future_dow_std_6w
future_store_lag_7
future_dept_lag_7
```

Categoricas: item_id, dept_id, cat_id, store_id, state_id, event_name_1, event_type_1, event_name_2, event_type_2.
