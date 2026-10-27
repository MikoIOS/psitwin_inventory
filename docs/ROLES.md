# Roles y flujo de reposición — contrato backend ↔ frontend (2026-10-03)

Backend: `backend/` (este repo) (base: commit `b892108`). El usuario autorizó modificarlo. **Sin commits.**
Si al implementar hay que desviarse, actualizar este archivo (sección "Desviaciones").

## 1. Tres tipos de usuario, un solo login

`POST /auth/login {correo, password}` → `{access_token, token_type, rol: EMPRESA|OPERARIO|PROVEEDOR, empresa,
operario|null, proveedor|null, debe_cambiar_password}`. Correo único entre empresas, operarios y proveedores.
- **Empresa**: se registra sola (`/auth/register`). Es la única que crea cuentas de operario y de proveedor
  (correo + contraseña temporal; deben cambiarla en el primer ingreso → 403 `code: PASSWORD_CHANGE_REQUIRED` hasta hacerlo).
- JWT: `sub`, `rol`, `id_empresa`, y `id_almacen` (operario) / `id_proveedor` (proveedor).
- Toda la API exige token (salvo login/registro). Aislamiento por empresa. 403 si el rol no puede.
- `GET /auth/me`, `PATCH /auth/me/password {password_actual, password_nueva}` para operario y proveedor.
- `POST /operarios/{id}/reset-password`, `POST /proveedores/{id}/reset-password` `{password_temporal}` (EMPRESA).

## 2. Qué puede hacer cada rol

| Recurso | EMPRESA | OPERARIO (solo su almacén) | PROVEEDOR |
|---|---|---|---|
| Almacenes, zonas | CRUD | leer | — |
| Racks | crear / borrar | leer, **editar** (estado, temperatura, rack de referencia) | — |
| Operarios, proveedores (cuentas) | CRUD | — | leer el suyo |
| Productos | leer | leer, editar rack de referencia | **crear / editar los suyos** |
| Inventario | **solo lectura** | crear, editar límites | — |
| Movimientos | leer (historial con autor) | crear SALIDA (VENTA, VENCIMIENTO), leer | — |
| Solicitud / orden | validar, devolver con comentario, cancelar, leer | **crear y editar** (PENDIENTE u OBSERVADA), leer las de su almacén | leer las ENVIADAS a él, registrar despacho |
| Recepción | leer | **registrar** (solo operario), resolver evaluación | — |

## 3. Zona y rack
- Zona: nuevo `refrigerada: bool` (lo decide la empresa al crear). `capacidad` = niveles. Sin temperatura obligatoria.
- Rack: `capacidad` = carga máxima en **kg**; nuevos `temperatura_min`, `temperatura_max` (solo si la zona es refrigerada;
  min ≤ max). No se pide `estado` al crear (DISPONIBLE). **Un rack por nivel** y `nivel ≤ zona.capacidad` (409).
- `RackResponse` añade `carga_kg` (Σ stock × peso del producto) y `libre_kg`.
- Asignar producto a rack (crear inventario, ingresar recepción): 409 si la carga supera `libre_kg`, si el rack no está
  DISPONIBLE, o si el producto requiere refrigeración y el rango del rack no cabe en el del producto
  (rack.temperatura_min ≥ producto.temperatura_min y rack.temperatura_max ≤ producto.temperatura_max).
- Inventario: 409 si `stock_actual > stock_maximo` al crear.

## 4. Producto
- Lo crea el **proveedor** (`id_proveedor` del token; `id_empresa` = la empresa a la que pertenece). `id_rack` opcional al crear:
  el rack de referencia lo asigna después el operario. `peso` obligatorio. Categoría/familia: texto (catálogo en el frontend).

## 5. Solicitud de reposición (reutiliza OrdenReposicion)
Estados: `PENDIENTE → (OBSERVADA ↔ PENDIENTE) → ENVIADA → PARCIAL → RECIBIDA`; `CANCELADA`.
1. **Operario** crea la solicitud (almacén = el suyo, proveedor, líneas) → `PENDIENTE`. Campos nuevos:
   `id_operario_solicitante`, `comentario_empresa`.
2. **Empresa**: `PATCH /{id}/validar` → `ENVIADA` (queda visible para el proveedor; el correo es un aviso opcional que
   **no bloquea**), o `PATCH /{id}/devolver {comentario}` → `OBSERVADA`.
3. **Operario** corrige una OBSERVADA y `PATCH /{id}/reenviar` → `PENDIENTE`.
4. **Proveedor**: `GET /ordenes-reposicion/proveedor/me` (ENVIADA/PARCIAL) y `POST /{id}/despacho`
   `{lineas: [{id_detalle_reposicion, cantidad, fecha_vencimiento?, temperatura?}], observacion?}` → queda en la orden
   (`despacho`, `fecha_despacho`). Se mantienen `aprobar`/`enviar` antiguos como alias de `validar` para no romper.
5. **Operario** registra la recepción (`POST /recepciones`, id_operario del token): parte de los datos del despacho,
   elige rack por línea. Sin lote. Temperatura obligatoria si el producto es refrigerado.

## 6. Historial para la empresa
- `MovimientoResponse` añade `operario_nombre` y `id_zona`. Los cambios de inventario (crear, editar límites) quedan
  registrados con `id_operario` y fecha: `GET /inventarios/{id}/historial` → `[{fecha, id_operario, operario_nombre, accion, antes, despues}]`.

## 7. Correo
- El envío de correos (SMTP) es opcional: si no está configurado, ninguna acción se bloquea.

## Desviaciones
(el agente del backend anota aquí lo que cambie)

Implementado sobre `b892108` y probado end-to-end el 2026-10-03. Todo lo que precisa o cambia el contrato:

### Auth y cuentas
- `GET /auth/me` (cualquier rol, también EMPRESA) → `{rol, empresa, operario|null, proveedor|null, debe_cambiar_password}` (igual que el login, sin token).
  `PATCH /auth/me/password` → `{"mensaje": "Contraseña actualizada correctamente"}`; solo OPERARIO/PROVEEDOR (EMPRESA → 403, usa `/empresas/me/password`);
  contraseña actual incorrecta o nueva igual a la actual → 400. **No existen** `/operarios/me` ni `/operarios/me/password`.
- Errores: sin token/expirado/inválido → 401; rol no permitido → 403 `"Su rol no puede realizar esta acción"`; recurso de otra empresa → 404;
  OPERARIO fuera de su almacén o PROVEEDOR sobre algo que no es suyo → 403; cuenta inactiva → 403 `"Operario inactivo"` / `"Proveedor inactivo"`.
  El backend relee la cuenta en cada request: tras cambiar la contraseña el mismo token sigue sirviendo.
- `POST /operarios` → body `{id_almacen, nombre, apellido, cargo, turno, estado?, correo, password_temporal}`.
  `POST /proveedores` → body anterior + `password_temporal` **opcional** (si viene exige `correo` y crea la cuenta; sin ella el proveedor queda sin cuenta).
  `reset-password` de ambos acepta además `correo` opcional (para cuentas antiguas sin correo; 409 si no hay ninguno) y responde el Operario/ProveedorResponse.
- `OperarioResponse` y `ProveedorResponse` incluyen `tiene_cuenta`, `debe_cambiar_password`, `correo_verificado`. Nunca el hash.
- `id_empresa` en cualquier body se ignora (se toma del token).
- Verificación de correo (Dylan): `POST /empresas/{id}/correo/enviar-verificacion|verificar`, ídem `/operarios/{id}/…` y `/proveedores/{id}/…` → **solo EMPRESA** dueña.

### Permisos que se apartan de la tabla §2
- **OPERARIO puede leer proveedores** (`GET /proveedores`, `/proveedores/{id}`): lo necesita para elegir proveedor al crear la solicitud. PROVEEDOR solo `GET /proveedores/{su id}`.
- **PROVEEDOR**: `GET /productos` devuelve solo los suyos; también puede **borrar** los suyos (`DELETE /productos/{id}`; 409 si el producto tiene inventarios).
  Puede leer `GET /ordenes-reposicion/{id}` y `/{id}/detalles` de órdenes suyas en ENVIADA, PARCIAL **o RECIBIDA** (`/proveedor/me` lista solo ENVIADA/PARCIAL).
- **Racks**: `PUT /racks/{id}` es solo OPERARIO y solo acepta `{estado?, temperatura_min?, temperatura_max?}`. Código, nivel y capacidad no se editan
  (la empresa borra y recrea). El "rack de referencia" es del producto: `PUT /productos/{id} {id_rack}` (OPERARIO; cualquier otro campo → 403).
  `DELETE /racks/{id}` → 409 si el rack tiene inventarios.
- **Inventario**: `PUT /inventarios/{id}` (OPERARIO) solo `{stock_minimo?, stock_maximo?}`; ya no acepta `stock_actual` ni `id_rack`.
  `DELETE /inventarios/{id}` lo hace el OPERARIO (solo sin stock).
- **Movimientos**: `POST /movimientos` solo OPERARIO y solo `tipo_movimiento=SALIDA` con `motivo_movimiento` VENTA o VENCIMIENTO (otro → 422). `id_operario` se toma del token.
- **Órdenes**: `POST /ordenes-reposicion` solo OPERARIO (`id_almacen` se fuerza al suyo; acepta `lineas: [{id_producto, cantidad_solicitada, costo_unitario?}]` opcional).
  Las líneas (`POST /ordenes-reposicion/{id}/detalles`, `PUT/DELETE /detalles-reposicion/{id}`) y `PUT /ordenes-reposicion/{id}` (`{id_proveedor?, fecha_estimada_recepcion?, observacion?}`)
  solo OPERARIO y solo en PENDIENTE/OBSERVADA (409 si no). `DELETE /ordenes-reposicion/{id}`: OPERARIO, solo PENDIENTE.
  `cancelar` (EMPRESA): PENDIENTE, OBSERVADA o APROBADA.
  **Eliminado** del contrato anterior: `id_operario_asignado`, `PATCH /{id}/asignar`, `GET /asignadas/me` (el operario ve todas las de su almacén con `GET /ordenes-reposicion`).
- **Recepción**: `POST /recepciones`, `POST /recepciones/{id}/detalles` y `POST /detalles-recepcion/{id}/resolver` solo OPERARIO (orden de su almacén).
  El operario ve las recepciones de todas las órdenes de su almacén.
- **Recomendaciones**: OPERARIO lee las de su almacén (`GET /recomendaciones`, `/almacen/{id}`, `/inventario/{id}`, `/{id}`),
  `PATCH /{id}/validar-operario` y `PATCH /{id}/actualizar-propuesta {cantidad_recomendada?, explicacion?}` (solo OPERARIO; `id_operario` del token).
  EMPRESA: resto (`aprobar-empresa {id_proveedor, costo_unitario, fecha_estimada_recepcion?, observacion?}`, `solicitar-cambios {comentario}`, `rechazar-empresa {comentario}`, `estado`, `crear-orden`).
  `aprobar-empresa` crea la orden y la deja directamente **ENVIADA** (`origen: RECOMENDACION_IA`, sin solicitante). Alertas, inventory-risk y forecast: solo EMPRESA.

### Zona / rack / producto / inventario
- Zona: `refrigerada` (default false; zonas antiguas → false). No se valida al bajar `capacidad` por debajo de los niveles ya usados.
- Rack (`POST /racks {id_zona, codigo, nivel ≥ 1, capacidad (kg), temperatura_min?, temperatura_max?}`):
  zona refrigerada sin ambas temperaturas → **422**; temperaturas en zona no refrigerada → 409; nivel ocupado → 409 `"Ya existe un rack en el nivel N de esta zona"`;
  nivel > zona.capacidad → 409; código repetido en la zona → 409. `RackResponse`: `{id_rack, id_zona, codigo, nivel, capacidad, estado, temperatura_min, temperatura_max, carga_kg, libre_kg, fechas}`
  (**desaparecen** `ocupacion` y `espacio_libre`). Productos sin `peso` (antiguos) cuentan 0 kg. Racks antiguos pueden compartir nivel y aparecer con `libre_kg` negativo.
- Extra: `GET /racks/disponibles?id_almacen=&id_producto=&cantidad=` (EMPRESA/OPERARIO; operario → su almacén) → racks DISPONIBLES donde caben `cantidad` unidades
  del producto por kg y temperatura; `RackResponse + id_almacen + nombre_zona`.
- Mensajes 409 de asignación: `"El rack X no está DISPONIBLE (estado: …)"`, `"Capacidad insuficiente en el rack X. Libre: N kg. Carga a ingresar: M kg"`,
  `"La temperatura del rack X (a a b °C) no cabe en el rango del producto (c a d °C)"`, `"El producto requiere refrigeración y el rack X no tiene temperatura definida"`.
- Producto (`POST /productos`, PROVEEDOR): `peso` obligatorio (> 0); `id_rack` enviado por el proveedor se ignora. `ProductoResponse` añade `id_proveedor` (antiguos → null).
- Inventario: `stock_actual > stock_maximo` al crear → 409 `"El stock inicial no puede superar el stock máximo"`.
  Historial `accion`: `CREAR` | `EDITAR_LIMITES`; `antes`/`despues` son objetos con los campos afectados (en CREAR `antes = null`).

### Solicitud / despacho / recepción
- `OrdenReposicionResponse` añade `id_operario_solicitante`, `comentario_empresa`, `despacho`, `fecha_despacho`, `id_recomendacion`.
  `despacho = {lineas: [{id_detalle_reposicion, id_producto, cantidad, fecha_vencimiento, temperatura}], observacion, fecha}`. Un nuevo despacho reemplaza al anterior.
- `validar` (y alias `aprobar`/`enviar`): desde PENDIENTE o APROBADA (órdenes antiguas) → ENVIADA; sin líneas → 409; una OBSERVADA no se valida (primero `reenviar`).
  `devolver`: solo desde PENDIENTE. `reenviar`: solo desde OBSERVADA; `comentario_empresa` se conserva como referencia.
  El estado `APROBADA` sigue en el enum solo para datos antiguos.
- `POST /recepciones` (un solo paso, lógica de Dylan): `{id_orden_reposicion, fecha_recepcion?, observaciones_generales?, detalles: [{id_detalle_reposicion, id_inventario,
  cantidad_recibida, cantidad_rechazada?, motivo_rechazo?, temperatura_recepcion?, fecha_vencimiento?, estado_recepcion?, comentario_recepcion?}]}`.
  `id_inventario` por línea es obligatorio (el operario crea el inventario en el rack elegido si no existe). `lote` es opcional (queda `"SIN_LOTE"`).
  Producto refrigerado sin `temperatura_recepcion` → 422. No se exige que exista despacho. Kg/estado/temperatura del rack → 409 antes de crear nada.

### Correo
- Sin SMTP o con correo sin verificar, `validar` deja la orden ENVIADA igual; el resultado del aviso no se devuelve.
