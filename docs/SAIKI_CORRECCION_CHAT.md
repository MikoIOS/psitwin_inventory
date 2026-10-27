# Corrección de conversación e inventario general de Saiki

## ARCHIVOS MODIFICADOS

- `app/dto/saiki_dto.py`: `message` es el campo principal, con ejemplos OpenAPI; `question` continúa como alias legacy opcional.
- `app/services/saiki_tools.py`: `get_warehouse_status` ahora admite consulta general segura y agrega inventario por producto.
- `app/prompts/saiki_system_prompt.py`: instrucciones explícitas para consultas generales y diferencia entre registros, productos y unidades.
- `tests/test_saiki_service.py`: pruebas de esquema simple y agregación sin duplicar productos.

No se modificaron LightGBM, FeatureBuilder, InventoryRisk matemático, autenticación, MongoDB ni flujos de escritura.

## DTO FINAL

Request mínimo válido:

```json
{
  "message": "Hola Saiki, ¿cómo está mi inventario?"
}
```

Campo obligatorio en OpenAPI:

- `message`: mensaje principal del usuario.

Campos opcionales:

- `question`: alias legacy de `message`; se mantiene para compatibilidad.
- `id_inventario`: solo para un registro específico.
- `id_producto`: solo para un producto específico.
- `context`: contexto técnico opcional.
- `history`: historial opcional; por defecto `[]`.

El esquema OpenAPI de `SaikiAskRequest` declara `message` como requerido y contiene ejemplos de conversación e inventario general. El request mínimo fue validado con Pydantic.

## INVENTARIO

MongoDB mantiene la estructura existente: la colección `inventarios` contiene registros técnicos, normalmente uno por producto y rack, con `id_inventario`, `id_producto`, `id_rack` y `stock_actual`.

No se hizo migración ni se creó un segundo inventario físico.

La consulta general usa `get_warehouse_status`:

1. Obtiene únicamente los `id_inventario` visibles mediante `AccesoService`.
2. Lee los registros actuales desde `InventarioService`.
3. Agrupa unidades por `id_producto`.
4. Cuenta `productos_distintos` por identificador, no por cantidad de racks.
5. Conserva `ubicaciones` separadas por registro, rack y zona.
6. Calcula `stock_total_unidades` como la suma de los stocks de los registros visibles.
7. Incluye los almacenes relacionados cuando existen datos de rack y zona.

Así, un producto ubicado en dos racks se cuenta una sola vez como producto distinto, pero sus unidades se suman y sus ubicaciones permanecen separadas.

La Empresa se identifica exclusivamente mediante el token autenticado. Saiki no pide ni acepta `id_empresa` generado por Qwen.

## TOOLS

Se conserva el agent loop real y la whitelist read-only:

- `get_inventory`
- `get_product`
- `get_forecast`
- `get_inventory_risk`
- `get_active_alerts`
- `get_recommendations`
- `get_recent_movements`
- `get_warehouse_status`

`get_warehouse_status` es la tool utilizada para preguntas generales como:

- “¿Cómo está mi inventario?”
- “¿Cuántos productos tengo?”
- “¿Cuáles son mis almacenes?”
- “¿Qué productos están en poco stock?”

Los argumentos continúan validándose mediante Pydantic. Las tools específicas siguen verificando inventarios y productos con `AccesoService`. Las consultas generales filtran por los recursos visibles para la Empresa autenticada.

No se agregaron tools de escritura.

## FORECAST

No se modificó el pipeline predictivo.

La ruta continúa siendo:

```text
get_forecast
→ predict_7_days
→ DemandHistory
→ MLContextBuilder
→ FeatureBuilder
→ DemandPredictor
→ LightGBM
```

Las consultas generales pueden hacer que Qwen consulte inventarios visibles y luego forecast individuales. Saiki no genera predicciones propias ni presenta una suma parcial como total global válido si faltan predicciones.

## SWAGGER

Endpoint principal:

```text
POST /api/v1/saiki/chat
```

Autenticación:

- Bearer JWT.
- Rol EMPRESA.
- Aislamiento por Empresa mediante `AccesoService`.

JSON mínimo listo para copiar:

```json
{
  "message": "Hola Saiki, ¿cómo está mi inventario?"
}
```

Otros ejemplos válidos sin IDs:

```json
{
  "message": "Muéstrame un resumen de todo mi inventario."
}
```

```json
{
  "message": "¿Qué productos tienen riesgo de quedarse sin stock?"
}
```

```json
{
  "message": "¿Qué demanda se espera durante los próximos 7 días?"
}
```

Aliases conservados:

- `POST /api/v1/saiki/ask`
- `POST /api/v1/saiki/chat`

Health:

- `GET /api/v1/saiki/health`

El system prompt no se expone como endpoint HTTP.

## TESTS

- Tests específicos de Saiki: **16 passed**.
- Suite completa: **36 passed**.
- `compileall app tests`: **PASS**.
- Importación de FastAPI: **PASS**.
- Rutas registradas:
  - `/api/v1/saiki/health`
  - `/api/v1/saiki/ask`
  - `/api/v1/saiki/chat`
- Esquema OpenAPI: `message` requerido; campos técnicos opcionales.
- Request mínimo `{"message": "¿Cómo está mi inventario?"}`: **PASS**.
- Agregación de producto distribuido en varios racks: **PASS** mediante test con mocks.
- Conflictos Git: no existen marcadores en `app` ni `tests`.

## PENDIENTES

- Probar manualmente desde Swagger con una cuenta EMPRESA y datos reales.
- Verificar con datos reales los nombres de almacenes, zonas y racks que estén presentes en MongoDB.
- Probar una consulta general de forecast con suficientes registros históricos para todos los productos.
- Probar el aislamiento usando dos Empresas reales en un entorno autorizado.
- No se implementaron frontend, Orb, voz ni memoria persistente.
- No se hizo commit ni push para esta corrección.

## DIAGNÓSTICO HTTP 503 Y RENDIMIENTO

La reproducción controlada encontró que `get_warehouse_status` fallaba con
`RuntimeError: MongoDB no está conectado.`. Ese error llegaba al `except
RuntimeError` de `SaikiService.ask` y se convertía incorrectamente en un 503
genérico. Ahora se conserva la causa internamente, se registra como
`mongodb_unavailable` y la respuesta no afirma que el inventario esté vacío.

También se verificó Ollama directamente con `stream=false` y `think=false`.
La instancia comprobada respondió `/api/version` como **0.40.0**, no 0.35.1.
Con `qwen3:4b`, `think=false` no evitó razonamiento textual: la respuesta
incluyó `</think>` y aproximadamente 128 tokens en una prueba de 41.6
segundos. El campo `message.thinking` no apareció. Saiki no expone ese texto:
extrae únicamente la respuesta posterior a `</think>` y registra la
incompatibilidad para poder observarla.

Se configuraron timeouts separados y finitos:

- Conexión: `OLLAMA_CONNECT_TIMEOUT_SECONDS=5`.
- Lectura/generación: `OLLAMA_READ_TIMEOUT_SECONDS=180`.

La lectura se elevó de 120 a 180 segundos únicamente después de medir una
inferencia real con el payload completo de Saiki: tardó 118.983 segundos y
generó un tool call válido. Probar `num_predict=256` redujo la duración, pero
truncó la salida y no produjo un tool call válido, por lo que no se adoptó.

El payload real conserva `stream=false` y `think=false`. El agent loop mantiene
un máximo de cuatro iteraciones, registra duración de cada inferencia y tool,
cuenta llamadas y evita ejecutar dos veces la misma tool con los mismos
argumentos.

`get_warehouse_status` distingue, con datos autorizados de la Empresa:

- `sin_almacenes`
- `almacen_sin_productos`
- `productos_sin_inventario`
- `stock_cero`
- `stock_positivo`

Los errores de consulta de MongoDB se mantienen como errores, nunca como un
estado vacío.

## ENRUTAMIENTO DE INTENCIONES

`SaikiIntentRouter` clasifica sin otra llamada a Ollama las consultas actuales,
predictivas, mixtas y las continuaciones con horizonte en el historial. Las
consultas predictivas sin horizonte solicitan elegir 7 o 30 días antes de
invocar el modelo. Las consultas actuales no envían las ocho definiciones de
tools: el payload se limita al subconjunto operativo seleccionado.

El horizonte detectado se incluye en el contexto de la petición, sin modificar
LightGBM ni sus features. Las tools que requieren identificadores continúan
respetando sus contratos y autorizaciones existentes; no se inventan
identificadores para resolver nombres ambiguos.
