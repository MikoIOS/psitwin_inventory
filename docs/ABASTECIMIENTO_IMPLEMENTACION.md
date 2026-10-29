# Abastecimiento integral de PsiTwin

Validación: 28 de octubre de 2026. React, FastAPI, MongoDB, Ollama y AutoGluon se conservan. No se agregaron servicios de pago ni modelos nuevos. Las escrituras de prueba se realizaron exclusivamente en bases temporales con prefijo de prueba; no se insertaron ofertas, pedidos, existencias ni sensores ficticios en la base de la aplicación.

## Diagnóstico y decisiones

El proyecto ya tenía solicitudes, aprobación, despachos, recepciones, movimientos y bloqueo de stock. Los problemas eran su desconexión comercial: productos ligados a un solo proveedor, cantidades enteras, precios editables desde la solicitud, ausencia de reservas de oferta y sustitución del despacho anterior. La clasificación no se validaba contra un catálogo compartido. La zona utilizaba `capacidad` como niveles, mientras faltaba una entidad de nivel dentro del rack. Los estados vacíos del frontend no siempre distinguían errores de carga.

Se reutilizan los servicios y rutas existentes para aprobar, despachar, recibir y registrar movimientos. Se añade una oferta comercial separada del producto canónico. Las cantidades admiten tres decimales para kg y cantidades enteras para unidades indivisibles. Las reservas usan enteros en milésimas y operaciones condicionales de MongoDB; los precios y subtotales usan céntimos PEN enteros, con redondeo comercial. Los precios enviados arbitrariamente por el cliente no sustituyen el precio real de la oferta.

La prueba real de AutoGluon encontró una referencia rota en `.autogluon.local/pyvenv.cfg`: apuntaba a un Python instalado que ya no existía. Se respaldó en `pyvenv.cfg.antes_reparacion` y se reparó el entorno local usando `.runtime.local/python`. El servicio ahora comprueba que el intérprete arranque, además del artefacto y su huella; un informe antiguo de validación no basta para declarar disponible un intérprete roto.

## Flujo implementado

1. Proveedor: registra/reutiliza un producto y configura su oferta, unidad, precio, cantidad total y estado activo.
2. Operario: elige proveedor y cantidades de sus ofertas disponibles; revisa el resumen y confirma. Se reservan cantidades y se conserva el precio acordado.
3. Empresa: aprueba, devuelve para corrección o rechaza. La cancelación conserva la solicitud y libera reservas.
4. Proveedor: revisa y acepta expresamente antes de registrar cada despacho. Se admiten despachos parciales acumulados; nunca se sustituye su historial.
5. Operario: recibe cantidades realmente despachadas, registra conformidad, rechazo parcial/total o evaluación, y ubicación. Solo lo aceptado genera entrada de inventario.
6. Empresa: consulta solicitado/despachado/recibido/aceptado/rechazado/faltante, motivo y teléfono registrado; mantiene o cierra el pendiente con motivo obligatorio. No se crea automáticamente otra compra.
7. Pedidos e intervenciones quedan en seguimiento e historial. Las recomendaciones aprobadas reutilizan la misma creación con oferta y reserva, sin convertir kilos a enteros ni crear cabeceras vacías.

Las recepciones y solicitudes tienen claves de idempotencia. Los reintentos de despacho emplean un diario persistente y operaciones de consumo identificadas. Un cierre no interrumpe un despacho parcialmente persistido. Una recepción parcialmente procesada tras un fallo técnico se bloquea para reconciliación, evitando repetir entradas.

## Modelo y compatibilidad

| Entidad | Cambios |
|---|---|
| Producto | Unidad kg/unidad, activo, código opcional y clasificación canónica. Reutilización de equivalentes por nombre/marca; validación de variantes. Los productos con referencias se conservan al desactivarlos. |
| Oferta de proveedor | Nueva colección `ofertas_proveedor`: producto/proveedor/empresa, precio en céntimos, cantidad total/reservada/despachada en milésimas, disponibilidad derivada, reservas y consumos idempotentes. |
| Solicitud y líneas | Oferta, unidad y precio histórico, subtotal/total en céntimos, clave de creación, historial de estados y despachos acumulados. |
| Recepción y detalles | Cantidades decimales, nivel, clave/firma/estado de procesamiento y comparación de cantidades. Rechazado implica aceptación cero. |
| Almacén y zona | Código, descripción, estado; almacén con ubicación. Zona con máximo de racks, compatible con `capacidad`. |
| Rack y nivel | Rack con máximo de niveles; nueva colección `niveles`, número/código único dentro de cada rack. Se retienen IDs y campo `nivel` antiguos. |
| Inventario | Nivel opcional para compatibilidad; unicidad inventario/producto/rack/nivel. Crear ubicación implica stock cero. |

El catálogo compartido está en `backend/app/knowledge/catalogo_alimentos.json` y se importa desde React. Conserva clasificaciones existentes y normaliza equivalentes; una categoría nueva incompatible con su familia devuelve 422. No se reclasifican registros históricos silenciosamente. Para ampliar familias/categorías, editar ese catálogo compartido y volver a compilar; no se añadió una consola administrativa de taxonomías.

## Roles

| Acción | Empresa | Operario | Proveedor |
|---|---|---|---|
| Consultar ofertas | Empresa propia | Empresa propia | Solo propias |
| Cambiar oferta | No | No | Solo propias |
| Crear/editar solicitud | Recomendación aprobada por flujo existente | Almacén asignado | No |
| Aprobar/rechazar/resolver pendiente | Sí | No | No |
| Despachar | No | No | Solicitudes aprobadas dirigidas a él |
| Recibir | No | Almacén asignado | No |
| Cambiar mínimo/máximo | Sí | No | No |
| Administrar niveles y máximos | Sí | Lectura; se conserva mantenimiento operativo de rack | No |
| Análisis / Saiki | Empresa propia | Almacén asignado | No se amplía su acceso a inventario |
| Teléfono en seguimiento | Sí | No | No |

Los controles se validan en el backend además de ocultarse en React. No se usan comentarios de proveedor como instrucciones para ejecutar acciones de IA.

## API

Se mantienen `/ordenes-reposicion`, `/detalles-reposicion`, `/recepciones`, `/inventarios`, `/detalles-inventario`, `/movimientos`, `/almacenes`, `/zonas` y `/racks`.

Nuevas rutas bajo `/api/v1/abastecimiento`:

- `GET /catalogo`, `GET /clasificacion`.
- `GET /ofertas?solo_disponibles=true&id_proveedor=...`, `PUT /ofertas`.
- `GET /seguimiento`.
- `PATCH /solicitudes/{id}/rechazar` y `/pendiente`, con motivo.
- `GET /historial-pedidos?id_producto=...&id_proveedor=...&desde=...&hasta=...&incluir_canceladas=false`.
- `GET/POST /racks/{id}/niveles`, `DELETE /niveles/{id}`.

`/analisis/pronostico` y `/analisis/resumen` aceptan `fuente=salidas|solicitudes`. Se mantiene la fuente histórica CSV para la consulta preexistente.

## Análisis y Saiki

Los productos solamente ofertados no aparecen como inventario analizable. Una entrada aceptada permite analizarlos aunque después se agote el stock. El CSV se conserva como fuente histórica independiente, incluyendo `es_imputado` y sus dimensiones; no se interpreta como prueba de stock operativo.

El historial de pedidos usa las fechas reales, zona horaria Lima y puntos individuales agrupados por producto/unidad. No inventa fechas ni rellena días con ceros. Se mantienen filtros de producto, proveedor, fechas y cancelados; los registros antiguos sin fecha verificable se excluyen y se contabilizan como tales. El gráfico CSV requiere seleccionar un producto para evitar una curva que mezcle productos.

El pronóstico conserva WeightedEnsemble de AutoGluon TimeSeries 1.6.1, sin entrenamiento por consulta. La fuente de abastecimiento tiene identidad/caché separada de las salidas. Exige historial diario suficiente, fechas continuas hasta el corte y modelo válido; si falta algo devuelve un estado explícito en lugar de fabricar una predicción. Las cantidades previstas no se suman entre productos o unidades para presentar un supuesto total global.

Saiki consulta ofertas reales y calcula costes con céntimos; explica estados, rechazo, cantidades pendientes, fechas, intervalos, mínimos/máximos y promedios por producto/unidad. Recibe filtros estructurados del gráfico y distingue historia de pronóstico. Respeta empresa y almacén del operario. El nuevo acceso al abastecimiento es de lectura: no aprueba ni recibe mercancía a partir de una frase.

## Archivos principales

| Grupo | Archivos y finalidad |
|---|---|
| Abastecimiento | `backend/app/services/oferta_service.py`, `abastecimiento_service.py`, `linea_abastecimiento_service.py`, `pedidos_history_service.py`: oferta/reservas, estado, líneas y trazabilidad. |
| Contrato API | `backend/app/controllers/abastecimiento_controller.py`, DTO `abastecimiento_dto.py`, `cantidad.py` y DTO existentes de pedidos, recepción, producto y ubicaciones. `app/main.py` registra rutas e índice de ubicación. |
| Integración | Servicios/controladores existentes de órdenes, recepción, detalle de inventario, movimiento y recomendaciones: autorización, decimales, entrada aceptada e idempotencia. |
| Catálogo / ubicaciones | `clasificacion_service.py`, catálogo JSON, `jerarquia_service.py`, servicios de almacén/zona/rack/producto, índices en `database/mongodb.py`. |
| Análisis | `analisis_repository.py`, `analisis_service.py`, `analisis_controller.py`, DTO y `autogluon_runtime.py`: fuentes, elegibilidad, permisos y comprobación del intérprete. |
| Saiki | `saiki_abastecimiento.py`, `saiki_service.py`, `saiki_intent_router.py`, `saiki_inventory_summary.py`, dependencias de controladores: evidencia real y cantidades por unidad. |
| React / API | `api/abastecimiento.ts`, `api/analisis.ts`, contratos `types.ts` e invalidaciones de solicitudes y recepciones. |
| React / flujo | `features/abastecimiento/*`, `OfertaSolicitudForm.tsx`, `DetalleLineaModal.tsx`, `OrdenDetallePage.tsx`, `DespachoModal.tsx`, `RecepcionCrearModal.tsx`. |
| React / ubicaciones | Formularios de almacén/zona/rack, `NivelesPanel.tsx`, selects dependientes y formularios/tablas de inventario. |
| React / acceso | `routes.tsx`, `paths.ts`, navegación, análisis, historial, sesión/evidencia de Saiki y catálogo compartido. |
| Migración / pruebas | `backend/scripts/migrar_abastecimiento.py`, `backend/tests/test_abastecimiento_integral.py`, pruebas de regresión actualizadas, `frontend/src/features/abastecimiento/abastecimiento.test.tsx`, `frontend/e2e/abastecimiento.spec.ts`. |

Los cambios de voz anteriores se documentan por separado en [SAIKI_VOZ_VALIDACION.md](SAIKI_VOZ_VALIDACION.md).

## Migración

La base real se examinó únicamente con el modo de solo lectura: **17 actualizaciones aditivas y 7 niveles heredados**, cero ofertas inventadas, cero pedidos o stocks alterados. La aplicación de la migración se probó sobre MongoDB temporal: respaldo, conservación del stock e idempotencia.

Desde `backend`:

```powershell
..\.runtime.local\python\python.exe scripts/migrar_abastecimiento.py
# Para aplicar al desplegar: detener antes API y demás escritores de inventario.
# El directorio de respaldo debe ser nuevo.
..\.runtime.local\python\python.exe scripts/migrar_abastecimiento.py --apply --backup ..\backups.local\abastecimiento-20261028
```

No se aplicó a la base real: hay una API activa escuchando en localhost:8000, por lo que no se ha acreditado que estén detenidos los escritores. Actualización posterior durante la corrección de voz: la API ya se reinició y su OpenAPI confirma las rutas actuales de voz y abastecimiento; la migración de datos sigue pendiente de una ventana sin escritores. Es un paso pendiente del despliegue para habilitar varias ubicaciones de nivel bajo el mismo producto/rack: el script crea el índice de cuatro campos y retira únicamente el índice único antiguo de tres campos. Antes de cambiar datos guarda originales BSON/JSON e índices. Las clasificaciones, precios, existencias, pedidos y registros de CSV no se inventan ni sobrescriben.

Los bloqueos MongoDB no caducan automáticamente: después de una caída se deben revisar operaciones en proceso y reconciliar cantidades con los escritores detenidos. No eliminar bloqueos activos ni repetir recepciones incompletas a ciegas.

## Instalación y ejecución

En este equipo se utiliza `.runtime.local/python/python.exe`; la antigua `.venv` apunta a una instalación inexistente. En otra instalación puede utilizarse un venv normal de Python compatible.

```powershell
# Desde la raíz, si faltan dependencias:
.\.runtime.local\python\python.exe -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
cd frontend
npm.cmd ci
npm.cmd run build
npm.cmd run dev
# En otra terminal, desde backend:
..\.runtime.local\python\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Se conservan las variables de MongoDB, JWT, Ollama y AutoGluon ya configuradas. No se incluyen sus valores ni credenciales en este documento. AutoGluon conserva su entorno aislado existente y no es requisito instalarlo dentro del Python de FastAPI.

## Verificaciones

- Backend completo sin la prueba de artefacto optativa: 404 pruebas correctas, 26 subcasos correctos y 2 pruebas optativas omitidas (Ollama y la prueba histórica adicional de MongoDB), que requieren activación explícita. Incluye una prueba específica del intérprete roto.
- Prueba real optativa de AutoGluon: **1 correcta**, 98.32 s, carga del ensemble y predicción de 90 días a partir del historial de referencia de 1096 días; sin entrenamiento ni cambios en MongoDB.
- React/Vitest: **92 pruebas correctas en 20 archivos**.
- Edge/Playwright: **12 casos correctos**: cinco de abastecimiento y siete de voz/sensores/navegación. Las pruebas de UI simulan HTTP y el reconocimiento/síntesis. La inspección del catálogo nativo de voces no utiliza un mock.
- TypeScript y compilación Vite correctos. Se conserva el aviso de tamaño del paquete del visualizador de audio existente.
- El flujo HTTP de abastecimiento se prueba contra FastAPI y MongoDB temporal reales, simulando la identidad de cada rol y los avisos externos: oferta → solicitud → aprobación → despacho → recepción parcial → historial; también denegación por rol y aislamiento de empresa. La prueba de rutas preexistente usa JWT reales.

Comandos de reproducción:

```powershell
# backend
..\.runtime.local\python\python.exe -m pytest tests --ignore=tests/test_autogluon_real.py -q
$env:PSITWIN_AUTOGLUON_INTEGRATION='1'
..\.runtime.local\python\python.exe -m pytest tests/test_autogluon_real.py -q
# frontend
npm.cmd run typecheck
node node_modules/vitest/vitest.mjs run --maxWorkers=2
npm.cmd run build
# Arrancar este Vite en otra terminal para evitar bloqueo del cierre de Playwright en Windows:
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 15473 --strictPort
$env:SAIKI_TEST_EXTERNAL_SERVER='1'
node node_modules/@playwright/test/cli.js test --config playwright.saiki.config.ts
```

## Límites comprobados y pendientes de despliegue

- Aplicar la migración con respaldo y escritores detenidos antes de utilizar múltiples niveles en los datos antiguos.
- Validar manualmente el flujo con usuarios reales, micrófono físico y altavoces. No se afirma haber probado una conversación humana real ni un circuito completo de UI contra el backend de producción.
- La prueba de AutoGluon demuestra funcionamiento técnico del modelo existente con su serie de referencia; no demuestra precisión para cada producto ni para solicitudes de abastecimiento nuevas. Las series insuficientes se muestran como tales.
- Actualización de voz: Jorge (México) no está instalado en el catálogo de Edge de este equipo. Para corregir el silencio, ahora se prioriza Jorge y se utiliza una voz española disponible con su nombre real; si la síntesis nativa falla, se recupera con Kokoro em_alex local. Desde la corrección del 29/10, el micrófono usa captura y transcripción local de forma predeterminada, con medidor de entrada y reconocimiento nativo como recuperación. No se usa scraping ni se atribuye a otra voz el nombre Jorge. Véase el informe de voz actualizado.
