# PsiTwin Inventory — Especificación del frontend

Fuente de verdad del contrato: el `/openapi.json` del backend real (http://localhost:8000/openapi.json).
El PDF `Guia_Backend_PsiTwin_para_Frontend.pdf` queda como referencia histórica: donde difiera, manda el OpenAPI.
Todo acceso HTTP y todos los tipos viven en `src/api/`.

## Stack
- React 19 + Vite + TypeScript (strict)
- React Router, TanStack Query (estado servidor), react-hook-form + zod (formularios)
- Tailwind CSS v4 + componentes propios en `src/components/ui/` (sin librería pesada)
- La app llama a `/api/v1`; en desarrollo Vite lo reenvía a `VITE_PROXY_TARGET` (default `http://localhost:8000`)
- Interfaz 100% en español, responsive (la recepción de mercadería debe ser usable en tablet/celular)

## Roles (contrato: `docs/ROLES.md`, incluida su sección «Desviaciones», y el OpenAPI real)
Un solo login (`POST /auth/login`) para tres tipos de usuario. La sesión guarda token + rol + empresa / operario /
proveedor + `debe_cambiar_password`, y se refresca con `GET /auth/me`. Las pantallas y rutas son las MISMAS para todos:
cada rol ve su menú, entra solo a sus rutas (una ruta ajena vuelve a `/`) y ve solo las acciones que puede hacer.

| Pantalla | EMPRESA | OPERARIO (solo su almacén) | PROVEEDOR |
|---|---|---|---|
| Inicio `/` | sus almacenes + alertas de stock | zonas → racks (carga kg, temperatura) + solicitudes por atender | órdenes ENVIADA / PARCIAL por despachar |
| Almacén / zona / racks | CRUD almacén y zona; crear / borrar rack | leer; editar estado y temperatura del rack | — |
| Productos | leer | leer; asignar rack de referencia | crear / editar / borrar los suyos |
| Inventario | leer + historial (autor, antes → después) | crear, editar límites, borrar sin stock, historial | — |
| Movimientos | leer (autor y ubicación) | leer; registrar SALIDA (VENTA / VENCIMIENTO) | — |
| Solicitudes / órdenes | leer; Validar, Devolver con comentario, Cancelar | crear, editar (PENDIENTE / OBSERVADA), Reenviar, eliminar PENDIENTE | detalle de las suyas; registrar despacho |
| Recepciones | leer | registrar (un paso) y resolver evaluación | — |
| Operarios / Proveedores | cuentas: crear con contraseña temporal, restablecer, «dar acceso», editar, activar, eliminar | — | — |
| Cuenta | Perfil de la empresa | Mi cuenta (cambio de contraseña) | Mi cuenta (cambio de contraseña) |

- **Cuentas**: la empresa se registra sola y es la única que crea operarios y proveedores (correo + contraseña temporal con
  generar / copiar). Operario / proveedor con contraseña temporal → `/cambiar-password` obligatorio (no puede navegar fuera).
  «Restablecer contraseña» genera otra temporal; para una cuenta sin credenciales el mismo botón es «Dar acceso».
- **Onboarding**: solo EMPRESA (debe crear su primer almacén). Un operario sin almacén asignado no puede trabajar.

## Flujo de reposición
`PENDIENTE → (OBSERVADA ↔ PENDIENTE) → ENVIADA → PARCIAL → RECIBIDA`; `CANCELADA`. (`APROBADA` solo en datos antiguos.)
1. **Operario** crea la solicitud (proveedor, fecha estimada, observación) y agrega líneas (productos de ese proveedor).
2. **Empresa**: *Validar* → ENVIADA (visible para el proveedor; el correo es un aviso que no bloquea), *Devolver* con
   comentario → OBSERVADA, o *Cancelar*.
3. **Operario** ve el comentario, corrige y *Reenvía* → PENDIENTE.
4. **Proveedor** registra su despacho por línea (cantidad, vencimiento, temperatura) + observación. Un despacho nuevo
   reemplaza al anterior.
5. **Operario** registra la recepción en UN paso (`POST /recepciones` crea la recepción e ingresa cada línea: detalle +
   movimiento ENTRADA/RECEPCION + estado de la orden):
   - Se precargan cantidad, vencimiento y temperatura del despacho (si existe; no es obligatorio que exista).
   - Por línea: recibida, rechazadas, estado CONFORME / RECHAZADO (rechazada = recibida) / EN_EVALUACION (aceptada 0, sin
     movimiento hasta resolverla en el detalle de la recepción), vencimiento, temperatura (obligatoria en refrigerados y
     dentro de su rango para aceptar) y comentario (obligatorio si hay rechazo o no es conforme). Sin lote.
   - Rack de destino: `GET /racks/disponibles?id_almacen=&id_producto=&cantidad=` (cabe por kg y temperatura), primero los
     que ya tienen el producto. Si el producto no tiene inventario en ese rack se crea al enviar (stock 0, mín/máx editables).
   - La sobre-recepción (aceptado > pendiente) se bloquea en el formulario. Un 409 del backend se muestra en el modal.
   - **Nunca** llamar a `POST /recepciones/{id}/detalles` tras crear la recepción (duplica el ingreso).
- Cantidad pendiente por línea = `cantidad_solicitada − Σ cantidad_aceptada` de todas las recepciones (cálculo cliente).

## Almacén, zona, rack, producto, inventario
- **Catálogo de alimentos** (`src/lib/catalogo.ts`): 4 tipos de zona → familias → categorías (texto libre en el backend).
- **Almacén**: tipo con opción "Alimentos"; ubicación con buscador de direcciones (Nominatim) y mapa OSM embebido.
- **Zona**: tipo del catálogo; `refrigerada` es un campo real que decide la empresa (el tipo solo sugiere el valor
  inicial); `capacidad` = número de **niveles**. La temperatura de la zona no se pide (null).
- **Rack**: lo crea / borra la EMPRESA (código, nivel libre, carga máxima en **kg**, y temperatura mín/máx si la zona es
  refrigerada). Un rack por nivel. El OPERARIO edita solo estado (Libre / Lleno / No disponible) y temperatura.
  La carga (`carga_kg`, `libre_kg`) la calcula el backend.
- **Producto**: lo registra el PROVEEDOR (tipo → familia → categoría del catálogo, peso obligatorio en kg, "Cantidad" =
  campo `volumen`, refrigeración con rango). El rack de referencia lo asigna el OPERARIO.
- **Inventario**: stock real = `Inventario.stock_actual` (no `Producto.stock`). Lo crea el OPERARIO (stock inicial ≤
  máximo; rack Libre, con kg libres y temperatura compatible → si no, 409). Después solo se editan los límites: el stock
  cambia por recepciones y movimientos. Historial por inventario: creación / cambios de límites y movimientos, con autor.
- **Movimientos**: solo listar y crear; nunca editar ni borrar. El formulario registra SALIDA con motivo VENTA o
  VENCIMIENTO; el autor sale del token.

## Errores
- 401 → limpiar sesión y redirigir a `/login`. 403 `PASSWORD_CHANGE_REQUIRED` → `/cambiar-password` (sin cerrar sesión).
  403 "Operario inactivo" / "Proveedor inactivo" → cerrar sesión con aviso. Otro 403 → «acceso denegado» sin cerrar sesión.
- 404, 409 (mostrar `detail` del backend), 422 (mapear `detail[].loc` a campos del form), 500 (mensaje genérico + console.error).

## Compatibilidad / normalización (`src/api/normalize.ts`)
- Almacén y zona responden `id`: se copia a `id_almacen` / `id_zona`. `latitud`/`longitud` llegan como string → number.
- Recepción: `observaciones_generales` (se tolera `observacion` antiguo); `detalles` siempre es array.
- Estado rack: DISPONIBLE (Libre) / LLENO / MANTENIMIENTO (No disponible); se toleran ACTIVO / INACTIVO antiguos al mostrar.
- Turno y estado de operario son texto libre: se muestran tal cual si no son MAÑANA/TARDE/NOCHE, ACTIVO/INACTIVO.
- Listados: se usan `/x/empresa/{id}` (el backend los acota por rol: el operario recibe solo lo de su almacén). El
  PROVEEDOR no puede leerlos: usa `/productos`, `/ordenes-reposicion/proveedor/me` y los datos de su sesión.

## Monitoreo con sensores (contrato: `docs/SENSORES.md`)
Un ESP32 por equipo de frío publica por MQTT cada 0,5 s `t_int`, `puerta`, `t_amb`, `hum` y `corriente`; el backend
evalúa límites, abre/resuelve alertas y las reenvía por WebSocket. Pantalla **Monitoreo** (`/monitoreo`, EMPRESA y
OPERARIO; el operario solo ve su almacén):
- Tarjetas por dispositivo agrupadas por zona con los valores en vivo (puerta: «abierta hace X s») y color por estado:
  **alerta** (alerta abierta) > **fuera de rango** (aún dentro de la tolerancia) > **sin datos** (sin lecturas 5 s) >
  **normal**. Indicador de conexión del WebSocket. Límite de `t_int` sin min/max → rango de temperatura del rack.
- Detalle (`/monitoreo/:id`): valores en vivo, gráfico SVG por parámetro (1 h / 6 h / 24 h / 7 días, con los límites en
  rojo) y alertas del dispositivo con **Atender** (`PATCH /alertas/{id}/estado` → VISTA; la alerta se resuelve sola cuando
  el valor vuelve al rango). El historial de alertas viene de `/alertas` (EMPRESA); el operario ve las abiertas.
- **EMPRESA**: crear dispositivo (almacén → zona → rack opcional), editar nombre / rack / activo / límites (min, max,
  tolerancia en s por parámetro; puerta: máx. segundos abierta y máx. aperturas por hora), regenerar token y eliminar.
  Campos de límite vacíos no se envían (defaults del backend). El token se muestra **una sola vez** (al crear o
  regenerar) con copiar, junto al tema MQTT `psitwin/dispositivos/{id}/lecturas` y el formato del mensaje.
- **Avisos globales**: una conexión WebSocket por sesión (`MonitoreoProvider` en el layout). Cada alerta ABIERTA → toast
  en cualquier pantalla y contador en el menú «Monitoreo» mientras haya alertas abiertas. Reconexión con backoff (1–30 s).
- En desarrollo el WebSocket `/api/v1/ws/monitoreo?token=<JWT>` pasa por el proxy de Vite (`ws: true`).

## Sin pantallas (por decidir)
Recomendaciones, alertas, forecast e inventory-risk.
