# Validacion conversacional de Saiki - 8 de octubre de 2026

Resultado: 129 pruebas y 26 subpruebas aprobadas; cero fallos y una prueba omitida. Duracion: 19,22 s.

Entorno separado: venv/saiki-tests-py312; Python 3.12.2, FastAPI 0.142.2, Pydantic 2.13.5, pytest 9.1.1. Solo se instalaron HTTPX 0.28.1, HTTPcore 1.0.9 y certifi 2026.7.22; las otras dependencias necesarias se copiaron sin modificar .venv.

Las 20 respuestas siguientes son pruebas con FastAPI ASGI, JWT, servicios y repositorios reales, usando una base simulada y datos sinteticos. Historial, contexto ML y evaluador de riesgo estan simulados. FeatureBuilder y los modelos LightGBM de las predicciones son reales. No son datos de la empresa del usuario.

| Pregunta | Respuesta obtenida | Herramienta utilizada | Tiempo | Ollama | Resultado |
|---|---|---|---:|---:|---|
| Hola Saiki. | ¡Hola, soy Saiki! | Router | 14.42 ms | 0 | Aprobada, datos sinteticos |
| ¿Cómo está mi inventario? | Actualmente tienes 1 producto distinto y 3 unidades registradas en tu inventario. | get_warehouse_status | 9.97 ms | 0 | Aprobada, datos sinteticos |
| ¿Cuántos productos tengo? | Tienes 1 producto registrado en tu catálogo. | get_product | 6.85 ms | 0 | Aprobada, datos sinteticos |
| ¿Tengo almacenes registrados? | Tienes 1 almacén registrado en PsiTwin. | get_warehouse_status | 8.07 ms | 0 | Aprobada, datos sinteticos |
| ¿Cuánto stock tengo? | Actualmente tienes 3 unidades en tu inventario. | get_warehouse_status | 9.18 ms | 0 | Aprobada, datos sinteticos |
| ¿Tengo alertas activas? | Tienes 1 alerta activa de riesgo alto. Puedes consultar los detalles en los datos adjuntos. | get_active_alerts | 6.30 ms | 0 | Aprobada, datos sinteticos |
| ¿Qué movimientos recientes tengo? | Encontré un movimiento reciente: una salida de 2 unidades. | get_recent_movements | 9.27 ms | 0 | Aprobada, datos sinteticos |
| ¿Dónde está el arroz? | Arroz está en el rack A01. | get_product, get_warehouse_status | 9.59 ms | 0 | Aprobada, datos sinteticos |
| ¿Qué productos podrían agotarse? | El riesgo de Arroz es crítico: la cobertura es de 1 día y la reposición tarda 2 días. | get_warehouse_status, get_inventory_risk | 7.43 ms | 0 | Aprobada, datos sinteticos |
| ¿Qué me recomiendas reponer? | La recomendación registrada propone reponer 5 unidades. Revisa el producto y los detalles antes de iniciar una compra. | get_recommendations | 10.27 ms | 0 | Aprobada, datos sinteticos |
| ¿Cuál será la demanda de la próxima semana? | La demanda estimada para los próximos 7 días es de 1.042 unidades. Faltan datos de algunas variables, por lo que es una estimación con limitaciones, no una proyección de stock futuro. | get_warehouse_status, get_forecast | 850.23 ms | 0 | Aprobada, datos sinteticos |
| Explícame el riesgo de desabastecimiento. | El riesgo de Arroz es crítico: la cobertura es de 1 día y la reposición tarda 2 días. | get_warehouse_status, get_inventory_risk | 12.28 ms | 0 | Aprobada, datos sinteticos |
| ¿Cómo vamos de inventario? | Actualmente tienes 1 producto distinto y 3 unidades registradas en tu inventario. | get_warehouse_status | 12.66 ms | 0 | Aprobada, datos sinteticos |
| Dime cómo está el almacén. | Actualmente tienes 1 producto distinto y 3 unidades registradas en tu inventario. | get_warehouse_status | 11.29 ms | 0 | Aprobada, datos sinteticos |
| ¿Qué productos me quedan? | Quedan 3 unidades de Arroz. | get_warehouse_status | 9.23 ms | 0 | Aprobada, datos sinteticos |
| ¿Hay alguna alerta? | Tienes 1 alerta activa de riesgo alto. Puedes consultar los detalles en los datos adjuntos. | get_active_alerts | 10.04 ms | 0 | Aprobada, datos sinteticos |
| Muéstrame las últimas salidas. | Encontré 1 salida entre los movimientos recientes consultados. | get_recent_movements | 9.06 ms | 0 | Aprobada, datos sinteticos |
| ¿Qué debería comprar? | La recomendación registrada propone reponer 5 unidades. Revisa el producto y los detalles antes de iniciar una compra. | get_recommendations | 6.95 ms | 0 | Aprobada, datos sinteticos |
| ¿Qué se va a agotar? | El riesgo de Arroz es crítico: la cobertura es de 1 día y la reposición tarda 2 días. | get_warehouse_status, get_inventory_risk | 6.45 ms | 0 | Aprobada, datos sinteticos |
| ¿Qué demanda tendremos en 7 días? | La demanda estimada para los próximos 7 días es de 1.042 unidades. Faltan datos de algunas variables, por lo que es una estimación con limitaciones, no una proyección de stock futuro. | get_warehouse_status, get_forecast | 449.93 ms | 0 | Aprobada, datos sinteticos |

## Seguridad, contexto y compatibilidad

Se verificaron solicitudes concurrentes de dos empresas; aislamiento de inventarios, alertas y recomendaciones; IDs ajenos; JWT invalidos/expirados; filtros de Empresa y errores de MongoDB/Ollama. Las pruebas usan datos sinteticos.

Los seguimientos de demanda futura y de Arroz utilizan solo history enviado por el frontend. Una solicitud independiente no conserva memoria. Un producto desconocido pide aclaracion y no pronostica otro producto. Se conservan answer, data, visualization, sources, warnings y context.

## Correcciones

Se incorporaron respuestas directas autorizadas para consultas claras de productos, alertas, movimientos, recomendaciones, riesgo y demanda. Las preguntas mixtas o ambiguas conservan el agent loop. Se corrigieron variaciones comprar/ventas futuras y el reconocimiento de demanda futura en history; se mejoraron saludo, concordancia, cantidades, motivos de riesgo e incertidumbre. No se modificaron formulas ni modelos.

Una prueba antigua esperaba el agent loop para preguntas ahora directas: se adapto a preguntas mixtas para mantener la comprobacion de seleccion local concurrente. Otra detecto el seguimiento de demanda futura ausente en el router: se corrigio. La regresion final pasa.

## Mediciones reales y pendientes

El JSON registra tiempo HTTP y tiempo de cada herramienta. mongodb_real_ms=null identifica que las 20 consultas no midieron MongoDB real. Con cero llamadas Ollama no hay tiempo de inferencia para estas consultas.

MongoDB local respondio a ping en 57,77 ms; no se consultaron ni modificaron datos de negocio. tests/test_saiki_mongodb_integration.py esta preparado pero omitido: requiere autorizacion para crear y eliminar exclusivamente una base temporal saiki_test_<UUID> con datos sinteticos.

Ollama /api/tags respondio HTTP 200 en 153,60 ms y confirmo qwen3:4b. La generacion real para preguntas complejas sigue pendiente: la prueba real previa de ubicacion agoto el timeout en 180029 ms con una inferencia y cero herramientas. Con el camino directo y el mismo catalogo sintetico, la medicion posterior fue 7,13 ms. Esto no demuestra latencia con MongoDB real ni del servidor desplegado.

LightGBM predice D+1 a D+7. dias=30 es la ventana historica. Se rechazan horizontes no soportados, incluyendo 30 dias; se advierten variables faltantes y se distingue demanda de stock futuro. No se suman pronosticos de inventarios arbitrariamente.

Pendientes: consultas reales de inventario en MongoDB con base temporal autorizada; servidor desplegado por TCP y frontend; generacion real de Ollama para preguntas complejas; validar con historial real autorizado la calidad predictiva.

No se modificaron .venv, .env, claves JWT, datos reales, formulas ni modelos. No hubo commit, push ni reversion de cambios anteriores.
