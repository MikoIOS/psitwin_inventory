/**
 * Tipos del contrato con el backend PsiTwin.
 * Fuente de verdad: `/openapi.json` del backend real (no el PDF).
 *
 * - Las entidades (respuestas) usan siempre el id canónico `id_xxx`: si el backend responde
 *   `id` (almacén, zona), `normalize.ts` lo copia al nombre canónico.
 * - Los bodies `XxxUpdate` del backend son parciales (todos los campos opcionales); aquí se
 *   tipan con los campos que el frontend envía.
 * - Todos los ids son UUID en formato string.
 */

export type Id = string
/** Fecha/hora ISO 8601 (ej. "2026-09-25T15:00:00Z"). */
export type IsoDateTime = string

/* ------------------------------------------------------------------ */
/* Enums (union types)                                                  */
/* ------------------------------------------------------------------ */

/** Estados de rack que el frontend puede ASIGNAR (enum `EstadoRack` del backend). */
export type EstadoRackEditable = 'DISPONIBLE' | 'LLENO' | 'MANTENIMIENTO'
/** Estados de rack que el frontend puede RECIBIR (incluye la versión antigua ACTIVO/INACTIVO). */
export type EstadoRack = EstadoRackEditable | 'ACTIVO' | 'INACTIVO'

/**
 * Turno y estado de operario son strings LIBRES en el backend (2–50 caracteres).
 * El formulario ofrece los valores conocidos, pero al mostrar hay que tolerar cualquier otro.
 */
export type TurnoOperarioConocido = 'MAÑANA' | 'TARDE' | 'NOCHE'
export type EstadoOperarioConocido = 'ACTIVO' | 'INACTIVO'
export type TurnoOperario = TurnoOperarioConocido | (string & {})
export type EstadoOperario = EstadoOperarioConocido | (string & {})
export type EstadoProveedor = 'ACTIVO' | 'INACTIVO'

export type TipoMovimiento = 'ENTRADA' | 'SALIDA' | 'AJUSTE'
export type MotivoMovimiento =
  | 'RECEPCION'
  | 'REPOSICION'
  | 'VENTA'
  | 'MERMA'
  | 'VENCIMIENTO'
  | 'DEVOLUCION'
  | 'CONTEO_FISICO'
  | 'OTRO'

/** OBSERVADA = devuelta por la empresa con comentario. APROBADA solo existe en datos antiguos. */
export type EstadoOrden = 'PENDIENTE' | 'OBSERVADA' | 'APROBADA' | 'ENVIADA' | 'PARCIAL' | 'RECIBIDA' | 'CANCELADA'
export type OrigenOrden = 'MANUAL' | 'RECOMENDACION_IA'

/** Estado de cada línea de una recepción de mercadería (registro documental). */
export type EstadoRecepcion = 'CONFORME' | 'RECHAZADO' | 'EN_EVALUACION'

/** Estado calculado de stock de un inventario (no viene del backend). */
export type EstadoStock = 'SIN_STOCK' | 'STOCK_BAJO' | 'STOCK_OK' | 'SOBRE_STOCK'

/* ------------------------------------------------------------------ */
/* Auth / Empresa                                                       */
/* ------------------------------------------------------------------ */

export interface RegisterBody {
  nombre: string
  ruc: string
  sector: string
  correo: string
  telefono: string
  password: string
}

export interface LoginBody {
  correo: string
  password: string
}

export type Rol = 'EMPRESA' | 'OPERARIO' | 'PROVEEDOR'

/** `GET /auth/me` (y el login, que añade el token): quién es el usuario. */
export interface MeResponseRaw {
  rol?: Rol
  /** Siempre: para operario / proveedor, la empresa a la que pertenece. */
  empresa?: unknown
  operario?: unknown
  proveedor?: unknown
  /** true si operario / proveedor entra con contraseña temporal. */
  debe_cambiar_password?: boolean
}

/** Respuesta de `POST /auth/login` (un solo login para los tres roles). */
export interface LoginResponseRaw extends MeResponseRaw {
  access_token?: string
  token_type?: string
}

/** `POST /operarios|proveedores/{id}/reset-password` (EMPRESA). `correo` solo para cuentas antiguas sin correo. */
export interface ResetPasswordBody {
  password_temporal: string
  correo?: string
}

/** Campos de cuenta que comparten Operario y Proveedor. */
export interface DatosCuenta {
  correo?: string | null
  correo_verificado?: boolean
  /** false si aún no tiene credenciales (la empresa le «da acceso» con reset-password). */
  tiene_cuenta?: boolean
  /** true mientras use la contraseña temporal. */
  debe_cambiar_password?: boolean
}

/** Campos de auditoría que devuelven todas las entidades. */
export interface Auditoria {
  fecha_creacion?: IsoDateTime
  fecha_actualizacion?: IsoDateTime
}

export interface Empresa extends Auditoria {
  id_empresa: Id
  nombre: string
  ruc: string
  sector: string
  correo: string
  telefono: string
}

/** PUT /empresas/me (todos opcionales en el backend; el RUC también es editable). */
export interface EmpresaUpdate {
  nombre: string
  ruc?: string
  sector: string
  correo: string
  telefono: string
}

/** DELETE /empresas/me exige la contraseña actual en el body. */
export interface EmpresaDeleteBody {
  password: string
}

export interface CambiarPasswordBody {
  password_actual: string
  password_nueva: string
}

/* ------------------------------------------------------------------ */
/* Almacén / Zona / Rack                                                */
/* ------------------------------------------------------------------ */

/**
 * El backend responde `id` (normalizado a `id_almacen`) y latitud/longitud como string decimal
 * (normalizados a number).
 */
export interface Almacen extends Auditoria {
  id_almacen: Id
  id_empresa: Id
  nombre: string
  area_m2: number
  aforo: number
  tipo_almacen: string
  latitud: number
  longitud: number
}

/** latitud −90..90 y longitud −180..180 (máx. 6 decimales) OBLIGATORIAS; area_m2 > 0; aforo ≥ 0. */
export interface AlmacenCreate {
  id_empresa: Id
  nombre: string
  area_m2: number
  aforo: number
  tipo_almacen: string
  latitud: number
  longitud: number
}

export type AlmacenUpdate = Omit<AlmacenCreate, 'id_empresa'>

/** El backend responde `id` (normalizado a `id_zona`) e incluye `id_empresa`. */
export interface Zona extends Auditoria {
  id_zona: Id
  id_almacen: Id
  id_empresa?: Id
  nombre: string
  tipo_zona: string
  /** La decide la empresa. Sus racks llevan temperatura mín/máx obligatoria. */
  refrigerada: boolean
  temperatura_min: number | null
  temperatura_max: number | null
  /** Niveles de la zona (un rack por nivel). */
  capacidad: number
}

export interface ZonaCreate {
  id_almacen: Id
  nombre: string
  tipo_zona: string
  refrigerada: boolean
  temperatura_min: number | null
  temperatura_max: number | null
  capacidad: number
}

export type ZonaUpdate = Omit<ZonaCreate, 'id_almacen'>

export interface Rack extends Auditoria {
  id_rack: Id
  id_zona: Id
  /** Código visible del rack (único en la zona). */
  codigo: string
  /** Un rack por nivel; nivel ≤ zona.capacidad. */
  nivel: number
  /** Carga máxima en KG. */
  capacidad: number
  estado: EstadoRack
  /** Solo en zonas refrigeradas (min ≤ max). */
  temperatura_min: number | null
  temperatura_max: number | null
  /** Σ stock × peso del producto (lo calcula el backend). */
  carga_kg: number
  /** capacidad − carga_kg (puede ser negativo en racks antiguos). */
  libre_kg: number
}

/** `GET /racks/disponibles`: rack DISPONIBLE donde cabe el producto (kg y temperatura). */
export interface RackDisponible extends Rack {
  id_almacen: Id
  nombre_zona: string | null
}

/** POST /racks (EMPRESA). Nace DISPONIBLE. Temperaturas obligatorias si la zona es refrigerada (y solo entonces). */
export interface RackCreate {
  id_zona: Id
  codigo: string
  nivel: number
  capacidad: number
  temperatura_min?: number | null
  temperatura_max?: number | null
}

/** PUT /racks/{id} (solo OPERARIO): estado y temperatura. Código, nivel y capacidad no se editan. */
export interface RackUpdate {
  estado?: EstadoRackEditable
  temperatura_min?: number | null
  temperatura_max?: number | null
}

/* ------------------------------------------------------------------ */
/* Producto / Inventario                                                */
/* ------------------------------------------------------------------ */

export interface Producto extends Auditoria {
  id_producto: Id
  id_empresa: Id
  /** Proveedor que lo creó (productos antiguos → null). */
  id_proveedor?: Id | null
  /** Rack de referencia: lo asigna el OPERARIO (`PUT /productos/{id} { id_rack }`). */
  id_rack: Id | null
  nombre: string
  categoria: string
  familia: string
  marca: string | null
  peso: number | null
  volumen: number | null
  /** Solo por compatibilidad. El stock real es `Inventario.stock_actual`. */
  stock: number
  requiere_refrigeracion: boolean
  temperatura_min_almacenamiento: number | null
  temperatura_max_almacenamiento: number | null
  lead_time_dias: number
  vida_util_dias: number
}

/** peso/volumen > 0 si se envían (null permitido); lead_time_dias ≥ 0; vida_util_dias ≥ 1. */
export interface ProductoCreate {
  nombre: string
  categoria: string
  familia: string
  marca: string | null
  /** Obligatorio (> 0): kg por unidad. */
  peso: number
  volumen: number | null
  stock: number
  requiere_refrigeracion: boolean
  temperatura_min_almacenamiento: number | null
  temperatura_max_almacenamiento: number | null
  lead_time_dias: number
  vida_util_dias: number
}

/** Body de PUT /productos/{id} (parcial en el backend). */
export interface ProductoUpdate {
  nombre: string
  categoria: string
  familia: string
  marca: string | null
  peso: number
  volumen: number | null
  requiere_refrigeracion: boolean
  lead_time_dias: number
  vida_util_dias: number
  temperatura_min_almacenamiento?: number | null
  temperatura_max_almacenamiento?: number | null
}

export interface Inventario extends Auditoria {
  id_inventario: Id
  /** Identificador de la ubicación de stock en el esquema v2. */
  id_detalle_inventario?: Id
  id_producto: Id
  id_rack: Id
  stock_actual: number
  stock_minimo: number
  stock_maximo: number
  /** Algunos listados pueden incluir el producto/rack anidado. No depender de ello. */
  producto?: Producto
  rack?: Rack
}

export interface InventarioCreate {
  id_producto: Id
  id_rack: Id
  stock_actual: number
  stock_minimo: number
  stock_maximo: number
}

/** PUT /inventarios/{id} (solo OPERARIO): solo límites. El stock cambia por recepciones y movimientos. */
export interface InventarioUpdate {
  stock_minimo: number
  stock_maximo: number
}

/** `GET /inventarios/{id}/historial`: quién creó / cambió límites y cuándo. */
export interface InventarioHistorial {
  fecha: IsoDateTime
  id_operario: Id | null
  operario_nombre: string | null
  accion: 'CREAR' | 'EDITAR_LIMITES' | (string & {})
  antes: Record<string, unknown> | null
  despues: Record<string, unknown> | null
}

/* ------------------------------------------------------------------ */
/* Operario / Movimiento                                                */
/* ------------------------------------------------------------------ */

/** Operario: cuenta propia (rol OPERARIO) creada por la empresa; solo ve su almacén. */
export interface Operario extends Auditoria, DatosCuenta {
  id_operario: Id
  id_empresa: Id
  id_almacen?: Id | null
  nombre: string
  apellido: string
  cargo: string
  turno: TurnoOperario
  estado: EstadoOperario
}

/** POST /operarios (EMPRESA). Nace con `debe_cambiar_password = true`. */
export interface OperarioCreate {
  id_almacen: Id
  correo: string
  /** Mínimo 6 caracteres. */
  password_temporal: string
  nombre: string
  apellido: string
  cargo: string
  turno: TurnoOperario
  estado: EstadoOperario
}

/** PUT /operarios/{id} (parcial). */
export interface OperarioUpdate {
  id_almacen?: Id
  correo?: string
  nombre: string
  apellido: string
  cargo: string
  turno: TurnoOperario
  estado: EstadoOperario
}

/** El backend devuelve id_producto e id_rack del inventario al momento del movimiento. */
export interface Movimiento {
  id_movimiento: Id
  id_inventario: Id
  /** Detalle de recepción que generó la entrada (solo ENTRADA/RECEPCION). */
  id_detalle_recepcion?: Id | null
  id_producto: Id
  id_rack: Id
  id_operario: Id
  /** Autor del movimiento (lo resuelve el backend). */
  operario_nombre?: string | null
  id_zona?: Id | null
  tipo_movimiento: TipoMovimiento
  motivo_movimiento: MotivoMovimiento
  cantidad: number
  stock_anterior: number
  stock_nuevo: number
  observacion: string | null
  fecha_hora: IsoDateTime
}

/** POST /movimientos (solo OPERARIO; el autor sale del token): solo SALIDA por VENTA o VENCIMIENTO. */
export interface MovimientoCreate {
  id_inventario: Id
  tipo_movimiento: 'SALIDA'
  motivo_movimiento: 'VENTA' | 'VENCIMIENTO'
  cantidad: number
  observacion: string | null
}

/* ------------------------------------------------------------------ */
/* Proveedor                                                            */
/* ------------------------------------------------------------------ */

export interface Proveedor extends Auditoria, DatosCuenta {
  id_proveedor: Id
  id_empresa: Id
  nombre: string
  ruc: string
  telefono: string | null
  direccion: string | null
  tiempo_entrega_estimado_dias: number
  estado: EstadoProveedor
}

/** RUC exactamente 11 caracteres. Con `password_temporal` (exige `correo`) se crea además su cuenta de acceso. */
export interface ProveedorCreate {
  nombre: string
  ruc: string
  correo: string | null
  telefono: string | null
  direccion: string | null
  tiempo_entrega_estimado_dias: number
  estado: EstadoProveedor
  password_temporal?: string
}

/** PUT /proveedores/{id}: el RUC no es editable. */
export type ProveedorUpdate = Omit<ProveedorCreate, 'ruc' | 'password_temporal'>

/* ------------------------------------------------------------------ */
/* Orden de reposición / Detalle                                        */
/* ------------------------------------------------------------------ */

export interface OrdenReposicion extends Auditoria {
  id_orden_reposicion: Id
  id_empresa: Id
  id_almacen: Id
  id_proveedor: Id
  estado: EstadoOrden
  /** Fecha de emisión de la orden (la asigna el backend). */
  fecha_orden?: IsoDateTime
  fecha_estimada_recepcion: IsoDateTime | null
  origen: OrigenOrden
  observacion: string | null
  /** Operario que creó la solicitud (órdenes antiguas o de recomendación → null). */
  id_operario_solicitante?: Id | null
  /** Comentario de la empresa al devolverla (OBSERVADA); se conserva tras reenviar. */
  comentario_empresa?: string | null
  /** Lo que el proveedor dice que envió (el último despacho reemplaza al anterior). */
  despacho?: Despacho | null
  fecha_despacho?: IsoDateTime | null
}

export interface LineaDespacho {
  id_detalle_reposicion: Id
  id_producto?: Id
  cantidad: number
  fecha_vencimiento: IsoDateTime | null
  temperatura: number | null
}

export interface Despacho {
  lineas: LineaDespacho[]
  observacion: string | null
  fecha?: IsoDateTime
}

/** `POST /ordenes-reposicion/{id}/despacho` (PROVEEDOR, orden ENVIADA / PARCIAL). */
export interface DespachoBody {
  lineas: Pick<LineaDespacho, 'id_detalle_reposicion' | 'cantidad' | 'fecha_vencimiento' | 'temperatura'>[]
  observacion: string | null
}

/** POST /ordenes-reposicion (solo OPERARIO; el almacén es el suyo). Nace PENDIENTE. */
export interface OrdenReposicionCreate {
  id_proveedor: Id
  lineas?: DetalleReposicionCreate[]
  fecha_estimada_recepcion: IsoDateTime | null
  origen: OrigenOrden
  observacion: string | null
}

/** PUT (OPERARIO, solo PENDIENTE / OBSERVADA). */
export interface OrdenReposicionUpdate {
  id_proveedor?: Id
  fecha_estimada_recepcion: IsoDateTime | null
  observacion: string | null
}

export interface DetalleReposicion extends Auditoria {
  id_detalle_reposicion: Id
  id_orden_reposicion: Id
  id_producto: Id
  cantidad_solicitada: number
  costo_unitario: number | null
}

export interface DetalleReposicionCreate {
  id_producto: Id
  cantidad_solicitada: number
  costo_unitario: number | null
}

export interface DetalleReposicionUpdate {
  cantidad_solicitada: number
  costo_unitario: number | null
}

/* ------------------------------------------------------------------ */
/* Recepción de mercadería / Detalle                                    */
/* ------------------------------------------------------------------ */
/*
 * Recepción en UN SOLO PASO: `POST /recepciones` crea la recepción e ingresa
 * cada línea al inventario (detalle + movimiento ENTRADA/RECEPCION + recálculo de la orden).
 * Hay un único esquema de detalle (`DetalleRecepcion`). Una línea EN_EVALUACION queda con
 * cantidad_aceptada = 0 y sin movimiento hasta resolverse (`POST /detalles-recepcion/{id}/resolver`).
 */

/** Línea de una recepción (body de `POST /recepciones` → `detalles[]`). */
export interface DetalleRecepcionCreate {
  id_detalle_reposicion: Id
  /** OBLIGATORIO: inventario del producto de la línea en un rack del almacén de la orden. */
  id_inventario: Id
  /** > 0 */
  cantidad_recibida: number
  /** ≤ recibida. Si > 0 exige motivo_rechazo (o comentario_recepcion). */
  cantidad_rechazada: number
  motivo_rechazo: string | null
  /** Opcional en el backend (default "SIN_LOTE"). 1–100 caracteres. */
  lote?: string
  fecha_vencimiento: IsoDateTime | null
  temperatura_recepcion: number | null
  /** RECHAZADO / EN_EVALUACION exigen comentario_recepcion o motivo_rechazo. */
  estado_recepcion: EstadoRecepcion
  comentario_recepcion: string | null
}

/** Detalle de recepción tal como lo devuelve el backend (también en `RecepcionMercaderia.detalles[]`). */
export interface DetalleRecepcion {
  id_detalle_recepcion: Id
  id_recepcion: Id
  id_detalle_reposicion: Id
  id_inventario: Id
  cantidad_recibida: number
  cantidad_rechazada: number
  /** recibida − rechazada; 0 mientras la línea esté EN_EVALUACION. */
  cantidad_aceptada: number
  lote: string
  fecha_vencimiento: IsoDateTime | null
  temperatura_recepcion: number | null
  estado_recepcion: EstadoRecepcion
  comentario_recepcion: string | null
  motivo_rechazo: string | null
  /** Movimiento ENTRADA/RECEPCION generado (null si no ingresó nada). */
  id_movimiento: Id | null
  ubicado: boolean
  fecha_creacion?: IsoDateTime
}

export interface RecepcionMercaderia {
  id_recepcion: Id
  id_orden_reposicion: Id
  id_operario: Id
  observaciones_generales: string | null
  fecha_recepcion: IsoDateTime
  fecha_creacion?: IsoDateTime
  detalles: DetalleRecepcion[]
}

export interface RecepcionMercaderiaCreate {
  id_orden_reposicion: Id
  /** Opcional: si no se envía, el backend usa la fecha actual. */
  fecha_recepcion?: IsoDateTime | null
  observaciones_generales: string | null
  /** REQUERIDO, mínimo 1 línea. */
  detalles: DetalleRecepcionCreate[]
}

/** `POST /detalles-recepcion/{id}/resolver`: resuelve una línea EN_EVALUACION. aceptada + rechazada = recibida. */
export interface ResolverEvaluacionBody {
  estado_recepcion: 'CONFORME' | 'RECHAZADO'
  /** Obligatorio (1–1000). */
  comentario_resolucion: string
  cantidad_aceptada?: number
  cantidad_rechazada?: number
  id_inventario?: Id
}
