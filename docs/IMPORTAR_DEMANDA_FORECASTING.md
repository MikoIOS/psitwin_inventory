# Demanda de forecasting en una base de pruebas

> La demo actual utiliza **10 productos**, inventario y solicitudes en una base nueva.
> Consulta [DEMO_10_PRODUCTOS.md](DEMO_10_PRODUCTOS.md) para iniciar con
> `./iniciar.cmd -Demo`. El porcentaje y la carga descritos abajo corresponden al
> procedimiento anterior; `--porcentaje 10` debe indicarse explícitamente. El
> importador ahora selecciona 10 productos distintos por defecto.

El CSV inspeccionado contiene **200 series de 1096 días** (219 200 filas), desde
2023-10-15 hasta 2026-10-14. El 10 % selecciona **20 series completas: 21 920 documentos**.
La selección es determinista por `(id_almacen, id_producto)`; porcentajes mayores incluyen
las series de porcentajes menores. Nunca se muestrean días de una misma serie.

Se leen `fecha`, `id_almacen`, `id_producto`, `cantidad`, `es_imputado`,
`producto_original`, `categoria`. Los lags, targets y demás variables de entrenamiento
no son demanda observada ni pronósticos servidos por AutoGluon; no se importan.
Las fechas originales no se trasladan ni se reescriben.

## Ejecutar en Windows (PowerShell)

Se requiere Python 3.12, Node para la web y MongoDB accesible por `MONGODB_URL`.
Los entornos virtuales incluidos en una copia del proyecto pueden apuntar a un Python
que ya no existe: crea uno nuevo si aparece `No Python at ...`.

```powershell
cd C:\Users\dylan\OneDrive\Escritorio\PsiTwin_inventory
py -3.12 -m venv .venv-forecasting
.\.venv-forecasting\Scripts\python.exe -m pip install -r requirements-dev.txt
```

No cambies `.env` de producción. La variable de entorno de esta terminal prevalece
sobre `.env`. Mantén el nombre de producción declarado incluso si usa otro nombre:

```powershell
$env:PSITWIN_PRODUCTION_DATABASE = 'inventory_db_v2_fresh'
$env:MONGODB_DATABASE = 'psitwin_forecasting_test'
```

Si tienes una empresa existente en esta base, usa su `id_empresa` y sus credenciales.
No se copian empresas, contraseñas ni usuarios desde producción. Para una cuenta nueva:

```powershell
.\.venv-forecasting\Scripts\python.exe scripts\preparar_empresa_forecasting.py --confirmar
```

Cuenta propuesta: **PsiTwin Forecasting Pruebas**, usuario/correo
**forecasting.pruebas@example.com**, rol **EMPRESA**. Define la contraseña cuando
el script la solicite; no hay una contraseña predeterminada. El script reutiliza el
registro y hash existentes, imprime el ID creado y no cambia cuentas existentes.
También admite `--nombre`, `--correo`, `--ruc`, `--telefono`, `--database`.
Esta cuenta solo existe después de ejecutar el comando correctamente.

```powershell
$empresaId = 'PEGA_EL_ID_IMPRESO'
.\.venv-forecasting\Scripts\python.exe scripts\importar_demanda_forecasting.py --empresa-id $empresaId --porcentaje 10 --dry-run
.\.venv-forecasting\Scripts\python.exe scripts\importar_demanda_forecasting.py --empresa-id $empresaId --porcentaje 10 --confirmar
```

`--csv RUTA` permite cambiar la ubicación del archivo; la ubicación predeterminada es
la proporcionada en este proyecto. Porcentajes: 5, 10 (predeterminado), 25, 50, 100.
`--lote 1000` controla el tamaño del lote y `--log RUTA` el registro de ejecución.
`--dry-run` prevalece sobre `--confirmar`: no crea índices ni documentos. Requiere
la empresa existente y conexión de lectura para informar duplicados reales.
La salida informa series, fechas, documentos insertados, omitidos, fallidos,
pendientes de insertar y conflictos. Un conflicto conserva siempre el documento previo.
Un fallo de validación detiene la carga antes de escribir. Los errores de lote se
registran en el resumen y producen código de salida 1. Una interrupción de conexión
puede dejar lotes ya importados: reejecutar es seguro.

## Ver la página

Para iniciar la web y API de prueba con puertos separados, sin cambiar `.env`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\iniciar_forecasting_pruebas.ps1
```

Abre **http://127.0.0.1:5174/analisis** e ingresa con la cuenta de pruebas.
Para detener únicamente esos procesos:
`powershell -ExecutionPolicy Bypass -File scripts\iniciar_forecasting_pruebas.ps1 -Detener`.
El script elige `.venv-forecasting` si existe y, en caso contrario, `.venv`.
Los logs quedan en `artifacts/forecasting-run.local`.

Alternativamente, para ejecutarlo manualmente en los puertos habituales:

Inicia FastAPI desde **esta misma terminal**, con la base de prueba seleccionada:

```powershell
.\.venv-forecasting\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

En otra terminal, desde el proyecto: `npm.cmd run dev`. Abre la dirección que muestre
Vite (normalmente http://localhost:5173), cierra cualquier sesión previa e ingresa con
el correo y contraseña de la empresa de pruebas. Abre **Análisis → Demanda histórica
importada**. El selector Empresa se limita a la sesión autenticada; no permite consultar
otras empresas. Filtra almacén, producto, fechas y agrupación. La tabla muestra 100
observaciones por página y señala los datos imputados por el dataset original.

La colección `demanda_historica` conserva los IDs **de origen**, vinculados a la
empresa mediante `id_empresa`. Son dimensiones históricas, no entidades operativas
creadas a medias. El CSV no tiene ubicación, área ni aforo de almacenes, ni peso,
familia, vida útil o plazos de producto: **no se crean almacenes ni productos** con
valores inventados. Las etiquetas `Almacén CSV <id>` y `Producto CSV <producto_original>`
identifican la fuente; no aseguran que haya inventario operativo. Si existen entidades
de la misma empresa con esos IDs, sus nombres aparecen en los filtros.

No se escriben `inventarios`, `detalles_inventario`, `movimientos` ni stock de productos.
Los IDs deterministas y el índice único por empresa/almacén/producto/fecha impiden
duplicados. Solo se usa `$setOnInsert`; no hay borrados ni actualizaciones de valores.

## FastAPI, Saiki y AutoGluon

`GET /api/v1/analisis/historico` requiere token de EMPRESA. Admite `id_empresa`
(solo la propia), `id_almacen`, `id_producto`, `fecha_inicio`, `fecha_fin`,
`frecuencia=diaria|semanal|mensual`, `offset`, `limite` (1–1000).
Devuelve curva agregada, tabla paginada, total, promedio por fechas presentes y ranking.
No rellena huecos. Semanas comienzan el lunes; meses el día 1. El promedio usa días
observados incluso al agrupar en semanas/meses. El ranking corresponde a series
producto/almacén y se limita a 20; la tendencia compara promedios de las dos mitades
de las fechas disponibles, sin extrapolar.

Preguntas para Saiki:

- «¿Cuál es la demanda histórica?»
- «¿Qué productos tienen mayor demanda histórica entre 2026-01-01 y 2026-03-31?»
- «¿Qué tendencia observada tiene la demanda?»
- «Analiza la demanda proyectada a 30 días».

Las respuestas históricas son deterministas a partir de MongoDB. Para rangos relativos
Saiki solicita fechas explícitas. Las respuestas futuras mantienen el flujo AutoGluon
existente. El historial importado tiene prioridad por serie; no se suma a SALIDAS
operativas ni se extiende con ceros hasta hoy. El corte es el último dato importado
anterior a hoy UTC. Las predicciones deben tener exactamente 90 fechas posteriores a
ese corte y cantidades finitas no negativas. No se presentan los targets CSV como
predicciones. Sin modelo válido se conserva el historial y no se inventa futuro.
La gráfica conjunta se limita al mismo producto y almacén. No hay backtest ni
comparación de precisión para fechas coincidentes si no existen predicciones válidas
de esas fechas. El stock para series importadas se muestra como no registrado en
esta vista, sin inferirlo de `cantidad`.

## Verificación

```powershell
.\.venv-forecasting\Scripts\python.exe -m pytest tests/test_importar_demanda.py tests/test_historico_demanda.py tests/test_analisis_demanda.py
npm.cmd run test:ui -- src/features/analisis
npm.cmd run typecheck
```

Ejecuta la importación confirmada dos veces: la segunda debe informar 0 insertados y
21 920 omitidos con el CSV actual al 10 %. Comprueba que la consulta histórica devuelve
21 920 documentos, que la suma semanal y mensual coincide con la diaria y que una
sesión de otra empresa no obtiene estos registros. Ni preparar la empresa ni importar
demanda se ejecuta al iniciar FastAPI.
