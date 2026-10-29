# Corrección del contrato de inventario

El backend distingue `id_inventario` (cabecera del almacén) de
`id_detalle_inventario` (producto y rack con su stock y límites).
La pantalla debe listar `/detalles-inventario`, conservar ambos identificadores
y usar el detalle para editar, eliminar y consultar su historial.

Crear una existencia primero garantiza la cabecera con `POST /inventarios`
usando el almacén elegido y después crea el detalle en `/detalles-inventario`.
Una salida y una recepción deben enviar la cabecera y el detalle seleccionado.
Las consultas de Saiki que requieren cabecera conservan `id_inventario`.
No requiere migración ni cambios de datos en MongoDB.

## Validación completada

- Compilación TypeScript/Vite aprobada.
- 52 pruebas frontend aprobadas, incluidas cuatro pruebas del contrato de inventario.
- Playwright con FastAPI y MongoDB aislado: 3 pruebas aprobadas y una repetición
  móvil de escritura omitida expresamente. Lectura, diez existencias, filtros,
  historial y recarga comprobados en escritorio y móvil.
- Operario en escritorio: creación de una segunda ubicación del mismo producto
  bajo la misma cabecera, edición de límites, venta de una unidad con ambos IDs y
  descuento correcto, y eliminación de la ubicación vacía comprobados.
- Las recepciones envían ambos identificadores; el selector de Saiki conserva el
  ID de cabecera. No se modificaron los algoritmos de pronóstico ni de Saiki.

Evidencias: `artifacts/inventario-corregido.local/resultados.json`, `desktop.png`
y `mobile.png`. Solo se usaron datos SIMULADOS; la base temporal se limpia al cerrar.

## Cómo comprobarlo

Abre `http://localhost:5173`, recarga con Ctrl+F5 e inicia sesión. En Inventario
deben aparecer las existencias de la empresa por producto y rack. Prueba Todos,
Stock bajo, Sin stock y el historial. Crear, editar límites y registrar salidas
requieren la cuenta de operario del almacén. No registres movimientos de prueba
en una empresa real.

Para repetir la prueba aislada con el snapshot del piloto:

```bash
./.runtime.local/python/python.exe backend/scripts/restaurar_snapshot_piloto.py
cd frontend
npm.cmd exec -- playwright test --config playwright.inventario.config.ts
cd ..
./.runtime.local/python/python.exe backend/scripts/evaluar_piloto.py --cleanup
```

Esta corrección resuelve el inventario vacío. Los demás hallazgos del informe
integral, como idempotencia de ventas y consultas de riesgo, siguen siendo independientes.
