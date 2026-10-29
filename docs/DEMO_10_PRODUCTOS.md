# Demo de 10 productos

La demo actual usa `psitwin_demo10_test`. Conserva `psitwin_forecasting_test` y
la base habitual sin borrar ni sustituir sus registros.

## Iniciar desde la terminal de VS Code

Git Bash:

```bash
./iniciar.cmd -Demo
```

PowerShell:

```powershell
.\iniciar.cmd -Demo
```

Abre **http://127.0.0.1:5174**. El backend está en `http://127.0.0.1:8001`.
La cuenta es la misma empresa de prueba anterior: `forecasting.pruebas@example.com`,
con su contraseña existente. El script no importa datos al iniciar. Para detener:
`./iniciar.cmd -Demo -Detener`. El comando `./iniciar.cmd` sin `-Demo` conserva el
arranque habitual y su base configurada en `.env`.

## Datos disponibles

- 10 productos de catálogo, 1 almacén, 1 zona y 1 rack.
- 10 ubicaciones de inventario con stock inicial de demostración, de 25 a 70 unidades.
- 1 proveedor de demostración sin cuenta ni envíos reales.
- 3 solicitudes pendientes, con líneas de esos productos; ninguna se envía o aprueba.
- 10 series completas del CSV: 10 960 registros, del 2023-10-15 al 2026-10-14.

**La demanda histórica es del CSV; el stock no lo es.** El peso (1 kg/unidad), las
coordenadas, capacidades, plazos, stock y solicitudes son configuración ficticia de
la demo. Se identifican en los nombres y en `demo_config`. No se generan ventas ni
movimientos ficticios para completar el historial. Crear una solicitud no incrementa
el stock disponible.

La demanda conserva `id_almacen_origen` e `id_producto_origen`; los IDs utilizados en
la web corresponden a las entidades operativas creadas mediante los servicios y DTO
existentes. `demo_config` guarda los mapas de correspondencia. Así, seleccionar un
almacén o producto filtra el mismo recurso en historial, inventario y pronósticos.
Análisis consulta el stock únicamente si producto y almacén pertenecen a la empresa.

## Preparar o verificar de nuevo

Desde la configuración habitual del proyecto (sin establecer `MONGODB_DATABASE` a
la base demo), usa el Python existente:

```powershell
.\.venv\Scripts\python.exe scripts\preparar_demo10.py --dry-run
.\.venv\Scripts\python.exe scripts\preparar_demo10.py --confirmar
```

El script solo escribe en `psitwin_demo10_test`, y copia la cuenta de empresa
seleccionada únicamente desde la base previa `psitwin_forecasting_test`. Admite
`--empresa-id` y `--csv`. El resumen queda en
`artifacts/forecasting-access.local/demo10-resumen.json`. Repetir el comando reutiliza
los registros existentes sin restablecer el stock, sobrescribir observaciones ni
cambiar el estado de solicitudes. No debe usarse para reconstruir entidades de la
demo que se hayan eliminado o renombrado manualmente.

El importador general ahora selecciona **10 productos distintos por defecto**, con
todas las series completas de cada uno (incluidos todos sus almacenes):

```powershell
.\.venv\Scripts\python.exe scripts\importar_demanda_forecasting.py --empresa-id ID_EMPRESA --productos 10 --dry-run
```

`--porcentaje` sigue disponible como opción explícita y no se combina con
`--productos`. Este importador general solo inserta historia; el script de preparación
de demo crea el catálogo y los datos operativos adicionales.

## Análisis y Saiki

La vista **Historial** contiene fechas, un único control «Ver historial por»
(día/semana/mes), curva, indicadores y tabla desplegable con nombres legibles.
La vista **Pronósticos** contiene un único selector «Días a pronosticar», el total
disponible y una tabla de demanda/stock. Selecciona un producto de la tabla para ver
su curva. No se repiten las cuatro tarjetas de horizontes ni tablas equivalentes.
La vista inicial de historial no pone automáticamente diez inferencias en cola.
La leyenda de predicción solo aparece si existen valores de predicción.

Preguntas para Saiki: «¿Cuántos productos tengo?», «¿Cuánto stock tengo?» y
«¿Qué productos tienen mayor demanda histórica?». El catálogo responde 10 productos;
el historial no se presenta como stock. Los pronósticos siguen procediendo únicamente
de AutoGluon, con fechas posteriores al corte del dataset.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_importar_demanda.py tests/test_historico_demanda.py tests/test_analisis_demanda.py tests/test_saiki_demand_analysis.py tests/test_saiki_http.py tests/test_saiki_request_semantics.py -q
npm.cmd run test:ui -- src/features/analisis
npm.cmd run typecheck
```
