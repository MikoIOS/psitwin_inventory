# Pruebas de endpoints — 27 de octubre de 2026

Se ejecutaron **174 solicitudes HTTP** sobre **55 combinaciones de método y ruta**,
además del WebSocket de monitoreo. Todas las rutas del alcance tuvieron una
respuesta satisfactoria con datos y permisos válidos; también se comprobaron
rechazos esperados. La prueba verifica su cobertura contra OpenAPI y falla si
queda alguna ruta del alcance sin una solicitud exitosa.

## Alcance

| Grupo bajo `/api/v1` | Rutas HTTP | Operaciones comprobadas |
|---|---:|---|
| `/productos` | 9 | Crear, listar, refrigerados, almacén, rack, categoría, detalle, editar y eliminar |
| `/movimientos` | 9 | Crear salida, listar, inventario, producto, rack, operario, tipo, motivo y detalle |
| `/inventarios` | 8 | Crear/garantizar cabecera, listar, almacén, detalles, productos, distribución, historial y detalle |
| `/detalles-inventario` | 11 | Crear, listar, stock bajo/cero/excesivo, producto, rack, detalle, editar límites, historial y eliminar |
| `/dispositivos` | 7 | Crear, listar/filtrar, detalle, editar, eliminar, regenerar token e historial de lecturas |
| `/alertas` | 10 | Crear, listar, activas, empresa, almacén, producto, inventario, nivel, detalle y cambiar estado |
| `/analisis/historico` | 1 | Consulta histórica y validación de empresa/fechas |
| `/ws/monitoreo` | WebSocket | Autenticación, snapshot, eventos, aislamiento y desconexión |

Este alcance corresponde a historial, productos, movimientos y monitoreo con
inventarios y alertas relacionados. No representa todas las rutas de otros
módulos del sistema, como pedidos, recepciones o pronósticos.

## Escenarios comprobados

- JWT reales de empresa, operario y proveedor. Ninguna dependencia de permisos
  se sustituyó. Todas las rutas HTTP rechazaron solicitudes sin autenticación.
- Dos empresas con productos, inventarios, detalles, movimientos, dispositivos y
  alertas reales dentro de MongoDB temporal: sin filtraciones en listas ni acceso
  cruzado mediante identificadores. Restricciones por rol y por almacén.
- El proveedor no puede falsificar empresa o proveedor al crear un producto;
  el operario solo puede modificar el rack de referencia.
- Una salida de 3 unidades pasa de stock 10 a 7. Se conserva el autor y los
  valores anteriores y posteriores en ambos historiales.
- Salidas superiores al stock, entradas manuales no permitidas y operaciones con
  rol incorrecto son rechazadas sin alterar el stock.
- No se eliminan detalles con stock o con movimientos históricos. Sí se puede
  eliminar un detalle vacío sin movimientos y después su producto sin inventario.
- Historial de sensores con paginación, parámetro seleccionado, resumen completo,
  rangos de 7 y 30 días y rechazo de páginas, límites, tipos y fechas inválidos.
- Selección de dispositivos por almacén, zona, rack, tipo y combinación de filtros.
- La regeneración de token invalida el anterior; las consultas no devuelven
  tokens ni hashes privados.
- WebSocket: token ausente/inválido → 4401; proveedor → 4403. Empresa y operario
  reciben snapshot autorizado. Los eventos respetan empresa, almacén y zona.
- Detector real de rangos con umbrales configurados para el dispositivo temporal:
  lectura de 8 frente a máximo 6 → una alerta en MongoDB, referencia a lectura y
  evento de apertura. Lecturas repetidas no duplican el incidente. Volver a 4
  resuelve el mismo incidente y emite el evento de resolución.
- Se comprueba la limpieza de las suscripciones al desconectar el WebSocket.

## Fallo encontrado y corregido

`PUT /productos/{id_producto}` aceptaba peso cero/negativo, nombres vacíos y valores
nulos en campos obligatorios. Podía guardar datos inválidos y causar después
errores de serialización. Se alinearon las validaciones de edición con creación:
peso y volumen positivos y finitos, texto recortado con longitudes válidas y
rechazo de nulos explícitos en campos obligatorios. Omitir un campo sigue dejando
su valor intacto; los campos opcionales que admiten borrado mantienen esa opción.

Los casos regresivos HTTP ahora reciben **422** antes de modificar MongoDB.

## Resultado y evidencia

- Prueba nueva de rutas: aprobada, 55 rutas HTTP y 174 solicitudes.
- Suite completa: **350 aprobadas, 3 omitidas y 26 subpruebas aprobadas**.
- Sintaxis Python y comprobación de espacios Git: aprobadas.
- Prueba reproducible: `backend/tests/test_endpoint_review.py`.
- Lista exacta de rutas: `artifacts/endpoint-review.local/coverage.json`.
- Registro de método, ruta, rol y estado esperado/obtenido:
  `artifacts/endpoint-review.local/requests.json`.
- Resultado completo: `artifacts/endpoints-regression.xml`.

```powershell
cd backend
..\.runtime.local\python\python.exe -m pytest -q tests/test_endpoint_review.py
..\.runtime.local\python\python.exe -m pytest -q
```

Las pruebas usan FastAPI/ASGI, servicios y repositorios reales con MongoDB temporal
eliminado al terminar. No se modificó inventario de producción ni se arrancó el
lifespan productivo. La entrada de sensores se entregó al procesador de mensajes
del monitoreo, sin broker MQTT ni dispositivos físicos. No se comprobó transporte
por red, proxy, navegador o hardware en esta ronda. Las omisiones de la suite
corresponden a integraciones optativas de AutoGluon, MongoDB adicional y Ollama.
