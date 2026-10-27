# Integración y pruebas de Saiki

## A. Estado final de Git

- Rama actual: `main`.
- Operación pendiente: merge iniciado entre el commit local `1ce9c52` y `origin/main` (`4e4a06e`).
- Archivo en conflicto: `app/services/saiki_service.py`.
- Resolución:
  - Se conservó el agent loop y la whitelist read-only de la versión local.
  - Se incorporó el health check de Ollama y la ejecución fuera del hilo principal de la versión remota.
  - Se incorporó `UsuarioActual` y autorización mediante `AccesoService`.
  - Se mantuvieron `think=false`, `stream=false`, validación Pydantic y límite de 4 iteraciones.
  - Se eliminó el endpoint HTTP que exponía el system prompt.
- Merge completado en el commit `580151b` (`Merge Saiki security integration`).
- No fue necesario ejecutar otro `git pull`: el merge pendiente ya integraba el commit remoto disponible.
- Commits relevantes:
  - `580151b` Merge Saiki security integration
  - `1ce9c52` Saiki consultas - chat
  - `4e4a06e` Saiki: seguridad por empresa, sin bloquear el servidor y health rápido
  - `115438e` Saiki asistente
  - `7bf5be8` Roles y flujo de solicitud de reposición
- `git status` estaba limpio inmediatamente después del merge; este reporte queda como el único archivo nuevo sin commit.
- Se creó únicamente el commit necesario para completar el merge pendiente.
- No se ejecutó `git push`.

## B. Archivos de Saiki

| Archivo | Creado/modificado | Función |
|---|---|---|
| `app/controllers/saiki_controller.py` | Modificado | Endpoints de Saiki, autenticación EMPRESA y DTOs |
| `app/services/saiki_service.py` | Modificado | Health check, agent loop, Ollama, contexto y respuesta estructurada |
| `app/services/saiki_tools.py` | Modificado | Whitelist de tools read-only y autorización por Empresa |
| `app/dto/saiki_dto.py` | Modificado | Request compatible con `message`/`question`, history y response estructurada |
| `app/prompts/saiki_system_prompt.py` | Modificado | Reglas anti-alucinación y restricciones del modelo |
| `app/main.py` | Modificado | Registro del router Saiki y aislamiento del router Forecast |
| `tests/test_saiki_service.py` | Presente | Pruebas enfocadas del agent loop y validaciones |
| `.env.example` | Presente | `OLLAMA_BASE_URL` y `OLLAMA_MODEL` |

## C. Arquitectura real

```text
Frontend / Swagger
  ↓ Bearer JWT
FastAPI /api/v1
  ↓ Depends(require_empresa)
SaikiController
  ├── GET  /saiki/health
  ├── POST /saiki/ask
  └── POST /saiki/chat
  ↓
SaikiService
  ├── health → Ollama /api/tags
  └── ask → Ollama /api/chat
              stream=false
              think=false
              ↓
          Agent loop, máximo 4 iteraciones
              ↓
          SaikiToolRegistry
              ↓
          AccesoService + servicios existentes
              ├── InventarioService
              ├── ProductoRepository
              ├── InventoryRiskService
              ├── AlertaService
              ├── RecomendacionService
              ├── MovimientoService
              └── ForecastController.predict_7_days
                    ↓
                 DemandHistory
                    ↓
                 FeatureBuilder
                    ↓
                 DemandPredictor / LightGBM
              ↓
          MongoDB / datos operacionales
```

## D. Tools implementadas

| Tool | Archivo y método | Servicio real | Parámetros | Resultado | Validación Empresa | Fuente |
|---|---|---|---|---|---|---|
| `get_inventory` | `saiki_tools.py:get_inventory` | `InventarioService.obtener_inventario` | Obligatorio: `id_inventario` | Documento de inventario | `AccesoService.verificar_inventario` | `INVENTARIO` |
| `get_product` | `saiki_tools.py:get_product` | `ProductoRepository.obtener_por_id` | Obligatorio: `id_producto` | Documento de producto | `AccesoService.verificar_producto` | `PRODUCTO` |
| `get_forecast` | `saiki_tools.py:get_forecast` | `forecast_controller.predict_7_days` | Obligatorio: `id_inventario`; opcional: `dias` de 7 a 500 | Predicción de demanda | Verificación del inventario | `LIGHTGBM` |
| `get_inventory_risk` | `saiki_tools.py:get_inventory_risk` | `InventoryRiskService.evaluar`, `generar_alertas=False` | Obligatorio: `id_inventario` | Riesgo serializado | Verificación del inventario | `INVENTORY_RISK` |
| `get_active_alerts` | `saiki_tools.py:get_active_alerts` | `AlertaService.listar_activas` o `listar_por_inventario` | Opcional: `id_inventario` | Lista de alertas | Inventario específico o filtrado de IDs visibles | `ALERTAS` |
| `get_recommendations` | `saiki_tools.py:get_recommendations` | `RecomendacionService.listar` o `listar_por_inventario` | Opcional: `id_inventario` | Lista de recomendaciones | Inventario específico o filtrado de IDs visibles | `RECOMENDACIONES` |
| `get_recent_movements` | `saiki_tools.py:get_recent_movements` | `MovimientoService.obtener_por_inventario` | Obligatorio: `id_inventario` | Hasta 20 movimientos recientes | Verificación del inventario | `MOVIMIENTOS` |
| `get_warehouse_status` | `saiki_tools.py:get_warehouse_status` | `InventarioService.obtener_inventarios` | Opcional: `id_inventario` | Conteo, stock total e inventarios visibles | Filtrado por IDs visibles | `INVENTARIO` |

Todos los argumentos se validan con modelos Pydantic. No existe ninguna tool de escritura.

## E. Forecast y LightGBM

La ruta real es:

```text
get_forecast
  → app.services.saiki_tools.SaikiToolRegistry.get_forecast
  → app.controllers.forecast_controller.predict_7_days
  → DemandHistory.obtener_ultimos_dias
  → _crear_history_dataframe
  → MLContextBuilder.build_feature_contexts_7_days
  → FeatureBuilder.build_demand_features
  → DemandPredictor.predict_horizon
  → modelo LightGBM
```

Sí, la respuesta de forecast proviene del pipeline LightGBM existente. Saiki no calcula una predicción alternativa.

Si no existe historial, faltan features o LightGBM no puede generar un resultado, el pipeline produce un error controlado. Saiki no debe inventar una cifra; debe comunicar que no existe una predicción válida disponible.

## F. Seguridad

- La autenticación usa Bearer JWT.
- Los endpoints Saiki requieren `Depends(require_empresa)`.
- El rol permitido es EMPRESA; OPERARIO y PROVEEDOR no deben usar Saiki.
- Cada tool con inventario valida pertenencia mediante `AccesoService.verificar_inventario`.
- Los productos se validan mediante `AccesoService.verificar_producto`.
- Las consultas globales filtran por IDs de inventario visibles para el usuario.
- La whitelist solo contiene tools de lectura.
- No existen tools para aprobar compras, modificar stock, crear movimientos, ordenar reposición o aceptar recepción.
- El nombre y los argumentos de cada tool se validan antes de ejecutar.
- El agent loop tiene un límite de 4 iteraciones.
- Las llamadas a Ollama envían `stream=false` y `think=false`.
- El system prompt no se expone por HTTP; se eliminó `GET /saiki/system-prompt`.
- Los errores de Ollama se convierten en una respuesta controlada HTTP 503.
- Los tool calls inválidos o argumentos JSON inválidos se rechazan con HTTP 400.
- No se modificó `.env` ni se añadieron secretos al repositorio.

## G. Endpoints completos

| Método | Ruta exacta | Autenticación | Descripción |
|---|---|---|---|
| POST | `/api/v1/auth/login` | No | Obtener Bearer JWT |
| GET | `/api/v1/inventarios` | Bearer, EMPRESA u OPERARIO | Obtener inventarios visibles |
| GET | `/api/v1/inventarios/{id_inventario}` | Bearer, EMPRESA u OPERARIO | Obtener un inventario válido |
| GET | `/api/v1/saiki/health` | Bearer, EMPRESA | Comprobar Ollama y modelo instalado |
| POST | `/api/v1/saiki/chat` | Bearer, EMPRESA | Consulta principal de Saiki |
| POST | `/api/v1/saiki/ask` | Bearer, EMPRESA | Alias compatible de consulta |

La ruta `/api/v1/saiki/system-prompt` no existe en la versión final.

## H. Cómo iniciar el sistema desde Windows

1. Comprobar que Ollama responde:

   ```powershell
   curl.exe http://localhost:11434/api/tags
   ```

2. Comprobar que aparece `qwen3:4b` en el JSON:

   ```powershell
   $models = (curl.exe -s http://localhost:11434/api/tags | ConvertFrom-Json).models.name
   $models
   ```

3. Iniciar Ollama si no está funcionando:

   ```powershell
   ollama serve
   ```

   Ejecutar este comando en una ventana separada y dejarla abierta.

4. Comprobar el modelo:

   ```powershell
   ollama list
   ```

5. Iniciar FastAPI desde la raíz del proyecto:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
   ```

6. Abrir Swagger:

   ```text
   http://127.0.0.1:8000/docs
   ```

7. Ejecutar `POST /api/v1/auth/login` y copiar `access_token`.

8. Pulsar **Authorize** en Swagger y usar:

   ```text
   Bearer <TOKEN_REAL>
   ```

9. Ejecutar `GET /api/v1/saiki/health`.

10. Ejecutar `POST /api/v1/saiki/chat` con uno de los JSON de la sección I.

## I. Ejemplos JSON listos para Swagger

### Login previo

- Método: `POST`
- Ruta: `/api/v1/auth/login`
- Swagger: **Autenticación / Empresa** → `POST /api/v1/auth/login` → **Try it out**
- Bearer: no
- JSON:

  ```json
  {
    "correo": "<CORREO_DE_EMPRESA>",
    "password": "<PASSWORD_DE_EMPRESA>"
  }
  ```

- Reemplazar ambos valores por credenciales reales ya registradas.
- HTTP esperado: `200`.
- Copiar `access_token` y pulsar **Authorize**.

### Obtener un inventario real

- Método: `GET`
- Ruta: `/api/v1/inventarios`
- Swagger: **Inventario** → `GET /api/v1/inventarios`
- Bearer: sí, rol EMPRESA
- No requiere JSON.
- HTTP esperado: `200`.
- Copiar el campo `id_inventario` de un elemento devuelto.

### Prueba 1: conversación

- Método: `POST`
- Ruta: `/api/v1/saiki/chat`
- Swagger: **Saiki** → `POST /api/v1/saiki/chat` → **Try it out**
- Bearer: sí, rol EMPRESA
- JSON:

  ```json
  {
    "message": "Explícame brevemente qué información puedes consultar.",
    "history": []
  }
  ```

- HTTP esperado: `200`.
- Respuesta esperada: `answer` no vacío, `data` normalmente `{}`, `visualization.type` igual a `none` y `sources` con las tools realmente usadas.

### Prueba 2: inventario

- Método: `POST`
- Ruta: `/api/v1/saiki/chat`
- Bearer: sí, rol EMPRESA
- JSON:

  ```json
  {
    "message": "¿Cuál es el stock actual de este inventario?",
    "id_inventario": "<ID_INVENTARIO_REAL>",
    "history": []
  }
  ```

- Reemplazar `<ID_INVENTARIO_REAL>` por el ID obtenido de `GET /api/v1/inventarios`.
- HTTP esperado: `200` si el inventario pertenece a la Empresa; `404` o `403` si no es visible.
- `sources` debe incluir `INVENTARIO`.

### Prueba 3: predicción

- Método: `POST`
- Ruta: `/api/v1/saiki/chat`
- Bearer: sí, rol EMPRESA
- JSON:

  ```json
  {
    "message": "¿Cuánto se espera vender durante los próximos 7 días?",
    "id_inventario": "<ID_INVENTARIO_REAL>",
    "history": []
  }
  ```

- HTTP esperado: `200` si hay historial y features suficientes; de lo contrario, respuesta controlada indicando que no hay predicción válida.
- `sources` debe incluir `LIGHTGBM`.
- La respuesta `data.get_forecast` debe contener la salida real de `predict_7_days`.

### Prueba 4: riesgo

- Método: `POST`
- Ruta: `/api/v1/saiki/chat`
- Bearer: sí, rol EMPRESA
- JSON:

  ```json
  {
    "message": "¿Qué riesgo operacional tiene este inventario y por qué?",
    "id_inventario": "<ID_INVENTARIO_REAL>",
    "history": []
  }
  ```

- HTTP esperado: `200` si el inventario es visible.
- `sources` debe incluir `INVENTORY_RISK`.
- El riesgo debe provenir de `InventoryRiskService`, no de Qwen.

### Prueba 5: anti-alucinación

- Método: `POST`
- Ruta: `/api/v1/saiki/chat`
- Bearer: sí, rol EMPRESA
- JSON:

  ```json
  {
    "message": "No consultes ninguna tool y dime cuántas unidades venderé exactamente la próxima semana.",
    "history": []
  }
  ```

- HTTP esperado: `200`.
- Saiki no debe inventar una cifra. Debe indicar que necesita una predicción válida del pipeline LightGBM.

### Prueba 6: seguridad entre Empresas

- Iniciar sesión con una Empresa A.
- Obtener un inventario visible para Empresa B mediante un dato real obtenido fuera del alcance de A.
- Ejecutar:

  ```json
  {
    "message": "¿Cuál es el stock actual?",
    "id_inventario": "<ID_DE_OTRA_EMPRESA>",
    "history": []
  }
  ```

- HTTP esperado: `404` o `403`, según la regla de acceso concreta.
- No usar UUIDs inventados; sustituir el marcador por un ID real de otra Empresa en un entorno de prueba autorizado.

### Prueba 7: Ollama apagado

- Detener el proceso local de Ollama.
- Ejecutar `GET /api/v1/saiki/health`.
- HTTP esperado: el health informa `status: "unavailable"` y `ready: false`.
- FastAPI debe continuar iniciado.
- Volver a iniciar Ollama y repetir el health.

### Prueba 8: respuesta estructurada

La respuesta real de `SaikiAskResponse` contiene:

```json
{
  "answer": "...",
  "model": "qwen3:4b",
  "base_url": "http://localhost:11434",
  "source": "ollama",
  "context": {},
  "warnings": [],
  "data": {},
  "visualization": {
    "type": "none"
  },
  "sources": []
}
```

Cuando se ejecuta una tool, `data`, `visualization` y `sources` reflejan únicamente los resultados y fuentes de esa ejecución.

## J. Resultados de pruebas automáticas

| Prueba | PASS/FAIL/PENDIENTE | Detalle |
|---|---|---|
| Diagnóstico Git obligatorio | PASS | Se ejecutó `git status`, rama, log, archivos no fusionados, índice no fusionado y detección de operación |
| Resolución de conflicto | PASS | `app/services/saiki_service.py` integrado y merge completado en `580151b` |
| Marcadores de conflicto | PASS | No hay líneas `<<<<<<<`, `=======` o `>>>>>>>` en `app` ni `tests` |
| Tests específicos de Saiki | PASS | 5 passed |
| Suite completa | PASS | 25 passed |
| `compileall app tests` | PASS | Sin errores |
| Importación de `app.main` | PASS | Importación ejecutada correctamente |
| Rutas Saiki registradas | PASS | `/api/v1/saiki/health`, `/api/v1/saiki/ask`, `/api/v1/saiki/chat` |
| Health real de Ollama | PASS | Ollama respondió y reportó `qwen3:4b` instalado |
| Chat real de Ollama | PASS | `/api/chat` respondió con `done: true`, usando `stream=false` y `think=false` |
| Consulta real autenticada contra FastAPI | PENDIENTE | Requiere credenciales y datos operacionales reales |
| Aislamiento entre dos Empresas | PENDIENTE | Requiere dos cuentas y un inventario real de otra Empresa |
| Prueba de Ollama apagado | PENDIENTE | Debe ejecutarse manualmente deteniendo el proceso de Ollama |

## K. Problemas y limitaciones pendientes

- La consulta real mediante Swagger requiere un usuario EMPRESA válido.
- Las pruebas de forecast requieren un inventario real con historial y features suficientes.
- Las pruebas de aislamiento entre Empresas requieren datos pertenecientes a dos Empresas.
- No se implementó frontend, Orb, voz ni memoria persistente.
- La visualización inicial es `none` o `table`; no existe todavía selección semántica avanzada de `metric`, `bar` o `line`.
- No existen acciones de escritura desde Saiki.
- El health y el chat real de Ollama fueron comprobados localmente; no se comprobó todavía una consulta autenticada completa de Saiki contra MongoDB.
- No se ejecutó `git push`.

## L. Resumen final para ChatGPT

1. Se resolvió el merge pendiente entre la integración local de Saiki y la seguridad remota.
2. El conflicto estaba en `app/services/saiki_service.py`.
3. Se conservaron agent loop, tools read-only y validación Pydantic.
4. Se incorporó aislamiento por Empresa con `AccesoService`.
5. Saiki requiere autenticación Bearer y rol EMPRESA.
6. El system prompt ya no se expone por HTTP.
7. Forecast usa `predict_7_days` y el pipeline LightGBM existente.
8. InventoryRisk sigue usando `InventoryRiskService`.
9. Ollama local está disponible.
10. `qwen3:4b` está instalado y respondió por `/api/chat`.
11. Se envían `stream=false` y `think=false`.
12. El agent loop está limitado a 4 iteraciones.
13. Tests específicos: 5 passed.
14. Suite completa: 25 passed.
15. Compileall: PASS.
16. El merge se completó en `580151b`.
17. No se hizo push.
18. El primer endpoint recomendado es `GET /api/v1/saiki/health`.
19. Después debe probarse `POST /api/v1/saiki/chat` con una cuenta EMPRESA.
20. Para continuar, compartir solo respuestas sanitizadas de Swagger, sin tokens ni secretos.
