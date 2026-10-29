# Plano, consultas verificables y reportes de inventario

Implementación y validación: 29/10/2026. Se conservan React, FastAPI, MongoDB, Ollama y los flujos existentes. Los datos de ejemplo y las escrituras de las pruebas pertenecen exclusivamente a bases temporales `psitwin_test_google_<uuid>`, eliminadas al terminar. No se insertaron productos, ubicaciones ni existencias ficticias en producción. No se enviaron correos reales.

## Diagnóstico

Saiki disponía de respuestas de catálogo que devolvían el número de productos; esa consulta no constituía una lista de existencias físicas. La consulta rápida de cantidades ya existente se conserva. Las preguntas explícitas de inventario, ubicación, movimientos, alertas y reportes ahora consultan datos estructurados y construyen respuestas verificables sin esperar a Ollama. No se utiliza el historial del chat como evidencia de cantidades o autorización de envíos.

Los niveles existían como entidad, pero su creación era manual. Crear un rack ahora habilita exactamente sus niveles 1…N mediante operaciones idempotentes. El código respeta los IDs históricos y no reasigna inventario legado. La zona limita racks; cada rack mantiene su propio máximo de niveles. No se reduce por debajo de niveles existentes ni se eliminan niveles referenciados por inventario, recepciones o movimientos.

## Plano y contexto

Desde el detalle del almacén se abre `/almacenes/:idAlmacen/plano`. El contorno contiene zonas y bloques de racks; seleccionar uno muestra sus niveles en vertical, ordenados de arriba abajo. Seleccionar un nivel filtra productos, cantidad, unidad y estado. Las alertas se limitan a la ubicación seleccionada. Hay actualización cada cinco segundos y un botón de actualización inmediata. Un error de consulta se muestra como error, separado de un almacén vacío.

La distribución es un esquema sin escala: no se recibieron dimensiones físicas que permitan afirmar posiciones reales. Los ejemplos de zonas A/B/C no se cargan en producción. Un rack antiguo con niveles faltantes ofrece a la empresa una acción explícita para habilitar los niveles configurados; consultar el plano nunca crea registros. No se inventa una capacidad física por nivel.

La selección del plano y los filtros de Inventario se transmiten a la sesión persistente de Saiki mediante `context.ubicacion`. Los IDs de almacén, zona, rack, nivel, producto e inventario se validan en el servidor, incluyendo consistencia entre padres y aislamiento de empresa. El operario queda limitado a su almacén. El proveedor no adquiere acceso a inventario ni a reportes.

## Consulta y veracidad

`inventario_consulta_service.py` comparte la fuente entre mapa, chat y reportes. Consolida por producto las filas físicas autorizadas y conserva el detalle por ubicación. Las ofertas comerciales no se suman al stock. Los totales permanecen separados por unidad. No existe una reserva física global configurada: no se atribuyen a inventario las reservas de ofertas de proveedor.

Los mínimos y máximos se evalúan por ubicación. Cero o ausencia significa umbral no configurado; estar en cero existencias sí significa agotado. Se distingue debajo del mínimo, en el mínimo, sobre máximo, dentro de umbrales y sin umbrales. Un mínimo agregado no se inventa cuando las ubicaciones tienen configuraciones distintas. Las referencias inválidas se señalan. Los fallos MongoDB producen 503 y no se presentan como ausencia de registros.

Saiki enumera páginas de productos con nombres, cantidades, unidades, ubicación y estados; el chat permite solicitar la siguiente página. La supervisión combina estados de stock, alertas registradas y pendientes reales de abastecimiento, incluidos rechazos y motivos. No afirma una avería a partir de una incidencia ni supone lecturas nuevas de sensores. Las consultas de últimos movimientos leen su historial registrado, con un máximo de 25 movimientos por consulta.

Ejemplos de la base temporal de prueba, no de producción:

- «¿Qué productos tengo?» devuelve Mango Kent, **25 kg**, repartidos en niveles 2 y 3; Fresas de prueba, **0 unidades**. No responde solamente «dos productos».
- «¿Qué productos hay aquí?» con el nivel 2 seleccionado devuelve Mango Kent, **10 kg**, y su estado por debajo del mínimo 15.
- La supervisión distingue esos 10 kg bajo mínimo de los 15 kg del nivel 3 sobre su máximo 10. No suma ambos umbrales como una configuración global.
- «Mándame el resumen de inventario a mi correo» → elección de formato → «PDF» → destinatario y alcance → «Sí» → un único intento SMTP autorizado.

## Exportación y correo

Inventario ofrece **Exportar inventario**, respetando almacén, búsqueda y estado. Excel contiene Resumen, Por producto, Por ubicación y Alertas. Las cantidades son celdas numéricas; los nombres y observaciones son texto literal para evitar fórmulas inyectadas. El PDF incluye resumen, clasificación, cantidades, límites, estado, jerarquía, actualización y alertas, con cabeceras repetidas y numeración. Ambos incluyen empresa, solicitante, alcance y fecha en Lima. Los datos ausentes se muestran explícitamente; no se inventan precios ni valoraciones.

El servidor comparte el mismo generador para descarga y adjunto. Los archivos se generan en memoria; la descarga requiere autenticación, usa `no-store` y no publica enlaces anónimos. Se limita el reporte a 10 000 ubicaciones y el adjunto a 10 MiB.

Solo EMPRESA puede preparar y confirmar correo. El destinatario se obtiene del correo registrado **verificado**, sin campo libre. El remitente está fijado a `psitwin2026@gmail.com`; el envío exige host Gmail y TLS. La solicitud almacena actor, empresa, destinatario, formato, filtros, resumen, caducidad de diez minutos y estado. Una clave idempotente evita duplicar la solicitud y una actualización condicional reclama una sola ejecución. Hay un máximo de cinco solicitudes por actor cada diez minutos.

Estados: ELEGIR_FORMATO → CONFIRMAR → GENERANDO → ENVIANDO → ACEPTADO_SMTP; también CANCELADO, ERROR y REVISAR_ENVIO. Una aceptación SMTP no confirma entrega en bandeja. Un resultado incierto no se reintenta automáticamente. Después de una caída en GENERANDO/ENVIANDO debe revisarse el registro y el transporte; no se cambia su estado a mano para reenviarlo a ciegas. El registro durable constituye la auditoría del intento; no almacena secretos ni el archivo binario.

Saiki usa el ID de acción emitido por el servidor. Un «Sí» o un historial fabricado sin esa acción no autoriza correo. Los botones del chat utilizan el mismo flujo. Cambiar el correo registrado invalida la confirmación anterior. Comparar con un reporte anterior exige una instantánea realmente almacenada tras aceptación SMTP, del mismo alcance; si no existe, Saiki lo explica. Que un producto desaparezca de una instantánea no se interpreta como cantidad cero.

## API

Todas las rutas bajo `/api/v1`; filtros `id_almacen`, `id_zona`, `id_rack`, `id_nivel`, `id_producto`, `id_inventario`, `busqueda`, `estado`.

| Método y ruta | Acceso / función |
|---|---|
| GET `/inventario-consultas/resumen?pagina=1&limite=25` | Empresa/operario; productos paginados, detalle y alertas autorizadas. |
| GET `/almacenes/{id}/plano` | Empresa/operario; jerarquía e inventario del almacén. |
| GET `/niveles/{id}/inventario` | Empresa/operario; inventario del nivel. |
| POST `/racks/{id}/habilitar-niveles` | Empresa; completar configuración histórica explícitamente. |
| GET `/inventario-reportes/exportar?formato=pdf` | Empresa/operario; PDF o xlsx. |
| GET `/inventario-reportes/destinatario` | Empresa; correo verificado. |
| POST `/inventario-reportes/solicitudes` | Empresa; formato, filtros y clave idempotente; nunca envía. |
| GET `/inventario-reportes/envios/{id}` | Empresa/actor propietario; estado. |
| POST `/inventario-reportes/envios/{id}/confirmar` | Empresa; cuerpo `{"confirmar":true}`. |
| POST `/inventario-reportes/envios/{id}/cancelar` | Empresa; cancelar una preparación pendiente. |

Se conservan las rutas existentes de racks, niveles, inventario y movimientos. `SaikiAskRequest` admite IDs de ubicación y página; el backend revalida todos los filtros recibidos.

## Archivos y modelo

| Archivos | Cambio |
|---|---|
| `backend/app/services/jerarquia_service.py`, `rack_service.py` | Creación idempotente de niveles, límites y protección de referencias. |
| `backend/app/services/inventario_consulta_service.py`, DTO `inventario_consulta_dto.py` | Fuente común, estados, filtros y cantidades. |
| `backend/app/services/inventario_reportes_archivos.py` | Renderizadores openpyxl y ReportLab compartidos. |
| `backend/app/services/inventario_reportes_service.py` | Preparación, confirmación, auditoría y SMTP existente. |
| `backend/app/controllers/inventario_consulta_controller.py`, `main.py` | Rutas autenticadas y descargas. |
| `backend/app/services/saiki_inventario_detallado.py`, `saiki_reportes.py`, `saiki_service.py`, DTO Saiki | Respuestas deterministas y flujo conversacional confirmado. |
| `backend/app/services/movimiento_service.py`, DTO de movimiento | Preservar `id_nivel` al registrar un movimiento. |
| `backend/app/database/mongodb.py` | Índices de ID y actor/fecha para nueva colección `reportes_inventario`. |
| `frontend/src/api/inventarioConsultas.ts` | Contratos, descarga autenticada y consulta periódica del plano. |
| `frontend/src/features/almacenes/PlanoAlmacenPage.tsx`, detalle, rutas y paths | Plano, selección y acceso desde almacén. |
| `frontend/src/features/inventario/ExportarInventario.tsx`, `InventarioPage.tsx` | Exportación y correo con revisión. |
| `frontend/src/features/saiki/ReporteSaiki.tsx`, `SaikiSession.tsx`, `SaikiPage.tsx`, API Saiki | Contexto persistente, paginación y acciones de reporte. |
| `frontend/src/features/recepciones/RecepcionCrearModal.tsx` | Filtrar racks por zona y seleccionar nivel de destino. |
| `backend/tests/test_plano_reportes.py`, `frontend/e2e/plano-reportes.spec.ts` | Pruebas nuevas de reglas, archivos, HTTP y UI. |
| `backend/scripts/ejemplos_reportes.py` | Ejemplos reproducibles en MongoDB temporal y vistas de revisión. |

No se modifica el significado histórico de `rack.nivel`; `max_niveles` y la colección `niveles` representan la jerarquía actual. Se mantiene `id_nivel` opcional en registros antiguos: no se adivina dónde estaban. La migración previa de abastecimiento y su índice de ubicación de cuatro campos siguen requiriendo respaldo y ventana de mantenimiento; no se han aplicado a producción en esta tarea.

## Gmail e instalación

Configurar exclusivamente en el entorno del backend, sin versionar secretos:

```dotenv
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=psitwin2026@gmail.com
SMTP_APP_PASSWORD=<secreto del propietario de la cuenta>
```

También se conserva SMTP SSL en puerto 465. Gmail requiere credenciales autorizadas; las contraseñas de aplicación dependen de la verificación en dos pasos y de las políticas de la cuenta. No se ha creado ni solicitado el secreto por chat. Referencias oficiales: [SMTP de Gmail](https://developers.google.com/workspace/gmail/imap/imap-smtp?hl=es-419), [contraseñas de aplicación](https://support.google.com/mail/answer/185833?hl=en-IN). El correo seguirá mostrando un error de configuración si falta el secreto o la verificación del destinatario; no se presenta como enviado.

Desde la raíz:

```powershell
.\.runtime.local\python\python.exe -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
cd frontend
npm.cmd ci
npm.cmd run typecheck
npm.cmd run build
# Desarrollo: npm.cmd run dev
# Otra terminal, desde backend:
..\.runtime.local\python\python.exe -m app.run --host 127.0.0.1 --port 8000
```

El frontend local de 5173 sirve `dist` mediante preview: hace falta compilar para actualizarlo. En Windows se conserva `app.run`, que configura el bucle compatible con el MQTT existente. El backend requiere reinicio al cambiar estos servicios. En este equipo ya se compiló `dist` y se reinició la API; su OpenAPI confirma las rutas nuevas, una descarga sin autenticación devuelve 401 y localhost:5173 responde 200. Esto comprueba el despliegue local y la protección de acceso, no un envío real de Gmail.

## Verificación y límites

Resultados comprobados:

- Backend completo sin la prueba optativa de artefacto: **423 correctas, 26 subcasos correctos y 2 optativas omitidas**.

- React/Vitest: 98 pruebas correctas en 21 archivos.
- TypeScript y compilación Vite correctos; permanece el aviso previo del paquete grande del visualizador de audio.
- Edge/Playwright: 16 pruebas correctas, con HTTP y audio simulados salvo la inspección del catálogo nativo de voces.
- Módulo nuevo de plano/reportes: 12 pruebas correctas contra MongoDB temporal, incluyendo dos formatos y tres clases de error SMTP.
- PDF de ejemplo: cuatro páginas renderizadas y revisadas. Excel: cuatro hojas revisadas mediante vistas de sus valores y estilos guardados. Se ajustaron anchos PDF, cabeceras y alturas persistidas de filas Excel.
- No se ejecutó la prueba optativa de artefacto AutoGluon en esta tarea; se conserva su validación previa en el informe de abastecimiento.

Pruebas reproducibles:

```powershell
# Desde backend
..\.runtime.local\python\python.exe -m pytest tests --ignore=tests/test_autogluon_real.py -q
..\.runtime.local\python\python.exe scripts/ejemplos_reportes.py
# Desde frontend
node node_modules/vitest/vitest.mjs run --maxWorkers=2
npm.cmd run typecheck
npm.cmd run build
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 15473 --strictPort
# Otra terminal frontend
$env:SAIKI_TEST_EXTERNAL_SERVER='1'
node node_modules/@playwright/test/cli.js test --config playwright.saiki.config.ts
```

Las pruebas del correo usan el transporte simulado y archivos reales generados; comprueban destinatario, adjunto, expiración, cancelación, errores, permisos y un solo intento. La prueba conversacional recorre solicitud → PDF → Sí → reintento sin duplicado. Las pruebas de UI simulan HTTP y los dispositivos de audio, mientras que las reglas del servidor usan FastAPI y MongoDB temporal reales. No se afirma una conversación humana con micrófono físico, acceso a una bandeja Gmail real ni validación nativa en Microsoft Excel. Se revisaron las páginas PDF renderizadas y las vistas de celdas guardadas de las cuatro hojas; no se sustituyen estas verificaciones por la compilación.

Pendientes operativos: secreto Gmail autorizado y prueba de entrega consentida; migración histórica con respaldo y escritores detenidos; validación física de micrófono/altavoces. Los informes son una lectura de varias colecciones, no una transacción de instantánea global bajo escrituras simultáneas. Para un cierre contable exacto debe realizarse una exportación con escritores detenidos o implementar una instantánea transaccional en un replica set. Las consultas grandes necesitan filtros; no hay trabajos de exportación en segundo plano ni archivado binario de todos los reportes descargados.
