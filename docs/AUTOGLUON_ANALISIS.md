# AutoGluon y Análisis de demanda

Se conserva FastAPI, MongoDB y Saiki/Ollama. AutoGluon es el único motor de demanda. La integración nueva es de solo lectura sobre MongoDB y no entrena modelos ni realiza compras, movimientos o acciones sobre equipos.

## Contrato verificado

- Artefacto: `PsiTwin_AutoGluon_Completo.zip` (9 080 810 bytes; 53 archivos; aproximadamente 45 MB descomprimidos).
- AutoGluon TimeSeries **1.6.1**, frecuencia `D`, objetivo `cantidad`, horizonte fijo de **90** días y modelo explícito **WeightedEnsemble**.
- `series_id = str(id_almacen) + "_" + str(id_producto)`; internamente AutoGluon usa esa clave como `item_id`.
- Covariables: `month`, `day`, `dayofweek` (lunes=0), `is_weekend`, `dayofyear`, `weekofyear` (ISO), `quarter`, `is_campana_navidena`.
- El usuario confirmó que la campaña navideña es **diciembre completo** y solo diciembre. No se añaden eventos ni calendarios externos.
- El archivo proporcionado posteriormente, `autogluton.xpynb`, tiene 0 bytes: no contiene celdas revisables. Se usaron el artefacto, sus metadatos y las definiciones confirmadas por el usuario; no se ejecutó entrenamiento.
- `metadata.json` declara `modelo_final_entrenado=false`. El modelo de evaluación fue entrenado con corte 2026-07-16; el holdout va de 2026-07-17 a 2026-10-14. No se ejecuta `fit` ni `refit_full`.

Los WAPE acumulados del CSV entregado son 37,4312496 % (1 día), 18,2665268 % (7), 15,2469883 % (30), 14,9845349 % (90), sobre 200 series. No son probabilidades de acierto, errores diarios ni métricas de las predicciones futuras. El dashboard redondea a dos decimales.

## Instalación aislada y validación real

El backend utiliza pandas 3, pero el artefacto requiere pandas <2.4. Se separa el entorno de inferencia para no cambiar ni romper FastAPI:

DeepAR fue serializado con scikit-learn 1.6.1; se fija esa versión para evitar incompatibilidad de `_RemainderColsList`. El worker adapta en memoria las referencias de `pathlib._local` de Python 3.13 al Python 3.12 local; AutoGluon restablece las rutas. No se modifican los archivos originales del modelo.

```bash
.venv/Scripts/python.exe scripts/preparar_autogluon.py --zip "C:/Users/dylan/Downloads/PsiTwin_AutoGluon_Completo.zip"
.venv/Scripts/python.exe -m venv .autogluon.local
.autogluon.local/Scripts/python.exe -m pip install -r requirements-autogluon.txt
.autogluon.local/Scripts/python.exe scripts/verificar_autogluon.py --allow-downloads
```

La validación carga `TimeSeriesPredictor.load(require_version_match=True)` y solicita una predicción de 90 días con `model="WeightedEnsemble"`, usando **todo el historial de una serie real del dataset suministrado**. Comprueba fechas, finitud y cuantiles; guarda `runtime_validation.json` y `smoke_predictions.json` dentro del artefacto privado. Una prueba unitaria con doble de modelo no habilita el motor.

El ZIP incluye redes locales de DeepAR y TemporalFusionTransformer, pero no contiene checkpoints grandes de Chronos2/Toto2. El ensemble depende de **DynamicOptimizedTheta, AutoETS, Chronos2, Toto2 y DeepAR**. La comprobación real debe resolver también esas dependencias y sus pesos. El informe guarda el error exacto si no es posible. No se cambia a otro integrante ni a otro motor para afirmar que funcionó WeightedEnsemble.

El backend solo declara el nuevo motor disponible si el smoke test real pasa y su huella coincide con los pickle actuales. La inferencia operativa funciona con `HF_HUB_OFFLINE=1`; no descarga pesos por cada petición. Los artefactos, pesos, entornos y cachés están en directorios `*.local`, ignorados por Git.

Configuración opcional en `.env`:

```dotenv
AUTOGLUON_ARTIFACT_DIR=artifacts/autogluon.local/psitwin_forecasting
AUTOGLUON_PYTHON=.autogluon.local/Scripts/python.exe
AUTOGLUON_CACHE_DIR=artifacts/autogluon-cache.local
AUTOGLUON_TIMEOUT_SECONDS=300
```

En Linux, indicar `.autogluon.local/bin/python`. Los pesos se buscan en `artifacts/huggingface.local`.

## Datos operativos y caché

El historial sale de las SALIDAS del producto en el almacén autorizado, desde la primera disponible hasta ayer UTC. Se conservan todas las filas disponibles, sin la ventana anterior de 400/500 días. Los días sin SALIDA se completan con cero conforme al contrato operativo: eso **no acredita observación, disponibilidad ni demanda latente**. No se pronostica stock ni se usa el saldo como objetivo. La integración aplica un guard operativo de 91 días de cobertura; no se presenta como garantía de calidad ni como días observados completos.

El dataset de referencia del ZIP se utiliza únicamente para comprobar el modelo. No se importa a MongoDB ni se atribuyen sus 200 series a una empresa autenticada.

La primera consulta genera trabajo en segundo plano y devuelve `CALCULANDO`; las siguientes reutilizan ese trabajo. Un proceso aislado mantiene el predictor cargado y serializa inferencias. La caché guarda los 90 días una vez y los reutiliza para 1/7/30/90. Su clave incluye empresa, almacén/producto, historial completo, contrato de calendario y huella del modelo. Cambiar stock actual no vuelve a pronosticar: el saldo se vuelve a consultar para comparar existencias.

Las salidas negativas se truncan a cero y se advierte cuando ocurre. Los cuantiles diarios Q10/Q50/Q90 se conservan; Q10–Q90 es una banda central del 80 %. **No se suman cuantiles diarios como intervalos acumulados**, porque faltaría la dependencia entre días.

## API, dashboard y Saiki

Todos los endpoints requieren rol EMPRESA:

- `GET /api/v1/analisis/modelo`: contrato, evaluación histórica y diagnóstico de carga real.
- `GET /api/v1/analisis/filtros`: almacenes y productos de la empresa autenticada.
- `GET /api/v1/analisis/pronostico?id_almacen=...&id_producto=...`: histórico, 90 predicciones, cuantiles y acumulados.
- `GET /api/v1/analisis/resumen?horizonte_dias=30`: ranking, stock y brecha orientativa. Filtros opcionales por almacén/producto; hasta 50 series por defecto, máximo 200. Se explicita cobertura parcial.

Un `id_empresa` ajeno devuelve 403; referencias ajenas no permiten acceder a historial, caché ni predicciones. No hay endpoint para cargar pickle desde un cliente.

El menú **Análisis** abre `/analisis`. La empresa se restringe a la sesión. El gráfico permite historial completo o los últimos 180 días, muestra pronóstico medio y banda diaria. Los acumulados y la tabla diaria distinguen demanda del día y demanda acumulada. El ranking parcial no se presenta como ranking exhaustivo. Una brecha de stock no es una orden de compra: faltan entradas pendientes, capacidad y políticas.

Saiki utiliza `get_demand_analysis` para las preguntas de demanda proyectada, mayor demanda, confiabilidad y planificación. Interpreta resultados calculados por FastAPI y nunca genera su propio pronóstico. Las rutas Forecast y Análisis comparten el mismo runtime AutoGluon. Sin validación no se producen predicciones ni se utiliza otro motor. Saiki entrega al LLM únicamente evidencia operacional y acepta solo frases verificadas; ante contenido sin respaldo conserva la explicación del backend. Los diagnósticos técnicos permanecen en el runtime, el manifiesto y los registros internos. Se conserva voz, mini ventana, LiveKit y supervisión de sensores.

## Pruebas

`scripts/verificar_integracion_demanda.py` comprueba MongoDB, el runtime compartido y la interpretación con Saiki sin insertar movimientos ni generar alertas. Solo imprime disponibilidad y conteos. Si no hay series operativas elegibles, informa esa limitación; no usa la serie de referencia como si perteneciera a una empresa. El LLM recibe un resumen compacto de resultados verificados; el backend rechaza cifras nuevas, cambios de significado y afirmaciones causales adicionales. Su indisponibilidad conserva la explicación verificada del backend, sin cambiar de motor predictivo.

Validación local completada el 21 de octubre de 2026: `TimeSeriesPredictor.load()` y `predict(model='WeightedEnsemble')` produjeron 90 fechas (2026-10-15 a 2027-01-12), con Q10/Q50/Q90, sobre una serie completa de referencia de 1.096 días. Es una prueba de inferencia del artefacto, no una evaluación adicional ni datos importados a MongoDB. Los pesos locales de Chronos2 ocupan 477.930.472 bytes y los de Toto2, 87.669.368 bytes; no estaban incluidos en el ZIP. El reporte local `runtime_validation.json` controla la disponibilidad y registra el resultado real.

También se verificó el worker persistente desde el entorno del backend: 90 predicciones reales y reutilización de caché sin acceso a MongoDB. Resultado: 145 pruebas de backend/permisos/Saiki, una prueba del artefacto real y 17 pruebas de frontend aprobadas; TypeScript y compilación de producción correctos. Las gráficas tienen pruebas automatizadas de renderizado; no se realizó revisión visual manual en navegador.

```bash
.venv/Scripts/python.exe -m pytest tests/test_analisis_demanda.py -q
npm run test:ui
npm run build
```

Las pruebas unitarias comprueban el contrato de calendario, horizonte, finitud, caché, stock independiente de demanda, roles, filtros y visualización. La prueba real de carga/inferencia es el script `verificar_autogluon.py`; su reporte determina la disponibilidad, no los dobles usados en tests. Los índices y los datos originales de MongoDB no se modifican para realizar estas pruebas.

Referencias oficiales: https://auto.gluon.ai/stable/api/autogluon.timeseries.TimeSeriesPredictor.load.html y https://auto.gluon.ai/stable/api/autogluon.timeseries.TimeSeriesPredictor.predict.html.
