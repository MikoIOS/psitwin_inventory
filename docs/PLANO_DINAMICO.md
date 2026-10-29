# Plano dinámico de almacenes

Implementación del 29 de octubre de 2026.

## Fuente y vistas

`consultar_inventario` conserva el alcance de empresa/almacén del usuario y prepara la misma estructura para el endpoint del plano, Saiki y exportaciones. `warehouse_map_service` proyecta nombres únicos con existencias positivas y ubicación válida, excluye rechazados y calcula monitoreo por nivel. No modifica inventario ni crea niveles durante las lecturas.

`WarehouseMap` se reutiliza en el inicio de Empresa, Monitoreo de Empresa/Operario y la página del plano. El selector del operario queda limitado a su almacén. Al seleccionar un nivel se accede al detalle con cantidades, unidades, sensores, alertas y movimientos. El dibujo solo muestra ubicación y nombres, con expansión de listas largas.

## Sincronización

- Estructura y existencias: consulta autorizada cada cinco segundos mientras la vista está visible; cambios de otra sesión se recuperan de MongoDB.
- Selector de almacenes: consulta cada diez segundos.
- Sensores: se reutiliza el WebSocket global; cada celda escucha los estados. Las lecturas no invalidan el plano completo.
- Alertas: invalidan el plano además de actualizar los estados del WebSocket.
- Mutaciones React Query y administración manual de niveles: invalidan las consultas del plano.
- No se abren conexiones WebSocket adicionales por plano. Las consultas se comparten en la caché de React Query.

## Tipo y niveles

`tipo_rack` es opcional para compatibilidad con datos antiguos. El formulario ofrece tipos sugeridos y existentes sin duplicados, admite un tipo personalizado y lo valida en backend. Los datos antiguos muestran «Tipo no definido». Se muestra el número real de niveles registrados, además de conservar el máximo configurable y la habilitación explícita de niveles.

Los sensores admiten `id_nivel`, validado contra el rack y editable en su formulario. Un sensor asignado únicamente a un rack no se atribuye automáticamente a todos sus niveles: estos permanecen sin información suficiente hasta configurar su ubicación.

## Integridad

Eliminar físicamente un nivel queda bloqueado si tiene referencias en inventario, recepciones, movimientos, dispositivos, alertas o lecturas. El rack no se elimina si contiene niveles, inventario o referencias históricas/de dispositivos. La zona no se elimina con racks o referencias de dispositivos, movimientos o alertas. Nunca se elimina inventario en cascada.

Desactivación y archivado conservan documentos e historial. El plano permite consultar ubicaciones activas o todas. Racks y zonas admiten `ARCHIVADO`; los niveles admiten `ACTIVO`, `INACTIVO` y `ARCHIVADO` mediante PATCH autorizado y controles de administración. El borrado sigue siendo una operación independiente.

## Reportes y Saiki

Excel incluye la hoja `Plano`; PDF incluye distribución por zona, rack, tipo, número de niveles y productos por nivel. Se incluyen niveles vacíos y se respeta el alcance seleccionado. La exportación mantiene sus controles contra fórmulas de Excel e inyección de marcado PDF.

Saiki consulta MongoDB para las ocho preguntas sobre productos por nivel, tipos, número de niveles, vacíos, localización de productos, niveles con alertas, racks creados en los últimos siete días y zonas actuales. Solicita una ubicación inequívoca cuando hay coincidencias múltiples.

## Verificación

- `backend/tests/test_warehouse_map.py`: MongoDB real en base temporal aislada, nombres y lotes, traslado simulado mediante cambio persistido de ubicación, nuevas zonas/racks/niveles, consistencia entre roles, protección de inventario, sensor real registrado, renovación de token, alerta crítica y resolución, PDF/Excel leídos y las ocho preguntas de Saiki.
- `backend/tests/test_plano_reportes.py`: API HTTP, autorización, reportes y flujo existente de envío.
- Regresión de backend: 46 pruebas aprobadas entre plano, reportes, asignación de rack, abastecimiento y sensores de Saiki.
- `WarehouseMap.test.tsx`: nombres, tipos antiguos, vacíos, expansión y color de la celda afectada.
- `e2e/plano-reportes.spec.ts`: navegador Edge real con respuestas HTTP controladas para cambios remotos sin recarga y flujo de reportes. No representa un ensayo con hardware MQTT físico.
- Compilación de producción y comprobación TypeScript aprobadas.
- Suite completa de frontend: 22 archivos y 101 pruebas aprobadas con `vitest run --pool=forks`. El ejecutor con threads agotó el tiempo de arranque de un worker; la ejecución completa con forks terminó correctamente.

No se aplican migraciones destructivas a datos existentes ni se publica automáticamente esta versión.
