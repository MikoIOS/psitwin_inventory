/**
 * Valores de enums, etiquetas en español y opciones para <Select>.
 * Única fuente de verdad para textos de estados; usar siempre estos mapas.
 */
import type {
  EstadoOperarioConocido,
  EstadoOrden,
  EstadoProveedor,
  EstadoRack,
  EstadoRackEditable,
  EstadoRecepcion,
  EstadoStock,
  MotivoMovimiento,
  OrigenOrden,
  TipoMovimiento,
  TurnoOperarioConocido,
} from './types'

export interface Opcion<V extends string = string> {
  value: V
  label: string
}

function opciones<V extends string>(labels: Record<V, string>, valores?: readonly V[]): Opcion<V>[] {
  const keys = valores ?? (Object.keys(labels) as V[])
  return keys.map((value) => ({ value, label: labels[value] }))
}

export const ESTADO_RACK_LABEL: Record<EstadoRack, string> = {
  DISPONIBLE: 'Libre',
  LLENO: 'Lleno',
  MANTENIMIENTO: 'No disponible',
  ACTIVO: 'Activo',
  INACTIVO: 'Inactivo',
  ARCHIVADO: 'Archivado',
}
export const ESTADOS_RACK_EDITABLES = ['DISPONIBLE', 'LLENO', 'MANTENIMIENTO', 'INACTIVO', 'ARCHIVADO'] as const satisfies readonly EstadoRackEditable[]
export const ESTADO_RACK_OPCIONES = opciones(ESTADO_RACK_LABEL, ESTADOS_RACK_EDITABLES)

/** Etiqueta de un valor libre: usa el mapa si lo conoce; si no, muestra el valor tal cual. */
function etiquetaLibre(labels: Record<string, string>, v: string | null | undefined): string {
  if (!v) return '—'
  return labels[v] ?? labels[v.toUpperCase()] ?? v
}

export const TURNO_LABEL: Record<TurnoOperarioConocido, string> = {
  MAÑANA: 'Mañana',
  TARDE: 'Tarde',
  NOCHE: 'Noche',
}
export const TURNO_OPCIONES = opciones(TURNO_LABEL)
/** Turno es texto libre en el backend: tolera valores desconocidos. */
export const etiquetaTurno = (v: string | null | undefined) => etiquetaLibre(TURNO_LABEL, v)

export const ESTADO_OPERARIO_LABEL: Record<EstadoOperarioConocido, string> = {
  ACTIVO: 'Activo',
  INACTIVO: 'Inactivo',
}
export const ESTADO_OPERARIO_OPCIONES = opciones(ESTADO_OPERARIO_LABEL)
/** Estado de operario es texto libre en el backend: tolera valores desconocidos. */
export const etiquetaEstadoOperario = (v: string | null | undefined) => etiquetaLibre(ESTADO_OPERARIO_LABEL, v)
/** true solo si el estado es ACTIVO (sin distinguir mayúsculas, como el backend). */
export const operarioActivo = (estado: string | null | undefined) => (estado ?? '').toUpperCase() === 'ACTIVO'

export const ESTADO_PROVEEDOR_LABEL: Record<EstadoProveedor, string> = {
  ACTIVO: 'Activo',
  INACTIVO: 'Inactivo',
}
export const ESTADO_PROVEEDOR_OPCIONES = opciones(ESTADO_PROVEEDOR_LABEL)

export const TIPO_MOVIMIENTO_LABEL: Record<TipoMovimiento, string> = {
  ENTRADA: 'Entrada',
  SALIDA: 'Salida',
  AJUSTE: 'Ajuste',
}
export const TIPO_MOVIMIENTO_OPCIONES = opciones(TIPO_MOVIMIENTO_LABEL)

export const MOTIVO_MOVIMIENTO_LABEL: Record<MotivoMovimiento, string> = {
  RECEPCION: 'Recepción',
  REPOSICION: 'Reposición',
  VENTA: 'Venta',
  MERMA: 'Merma',
  VENCIMIENTO: 'Vencimiento',
  DEVOLUCION: 'Devolución',
  CONTEO_FISICO: 'Conteo físico',
  OTRO: 'Otro',
}
export const MOTIVO_MOVIMIENTO_OPCIONES = opciones(MOTIVO_MOVIMIENTO_LABEL)

/**
 * Motivos permitidos en el formulario MANUAL de movimientos, por tipo.
 * RECEPCION nunca se ofrece (solo lo genera el backend al registrar el ingreso de una recepción).
 * En AJUSTE la cantidad es el nuevo stock físico contado (el backend exige cantidad > 0).
 */
export const MOTIVOS_MANUALES_POR_TIPO = {
  ENTRADA: ['REPOSICION', 'DEVOLUCION', 'OTRO'],
  // El formulario manual solo registra salidas por venta o vencimiento (las entradas llegan por recepción).
  SALIDA: ['VENTA', 'VENCIMIENTO'],
  AJUSTE: ['CONTEO_FISICO', 'OTRO'],
} as const satisfies Record<TipoMovimiento, readonly Exclude<MotivoMovimiento, 'RECEPCION'>[]>

export function motivosManualesOpciones(tipo: TipoMovimiento): Opcion<Exclude<MotivoMovimiento, 'RECEPCION'>>[] {
  return MOTIVOS_MANUALES_POR_TIPO[tipo].map((value) => ({ value, label: MOTIVO_MOVIMIENTO_LABEL[value] }))
}

export const ESTADO_ORDEN_LABEL: Record<EstadoOrden, string> = {
  PENDIENTE: 'Pendiente',
  OBSERVADA: 'Observada',
  APROBADA: 'Aprobada',
  ENVIADA: 'Enviada',
  PARCIAL: 'Parcial',
  RECIBIDA: 'Recibida',
  CANCELADA: 'Cancelada',
}
export const ESTADO_ORDEN_OPCIONES = opciones(ESTADO_ORDEN_LABEL)

export const ORIGEN_ORDEN_LABEL: Record<OrigenOrden, string> = {
  MANUAL: 'Manual',
  RECOMENDACION_IA: 'Recomendación IA',
}

export const ESTADO_RECEPCION_LABEL: Record<EstadoRecepcion, string> = {
  CONFORME: 'Conforme',
  RECHAZADO: 'Rechazado',
  EN_EVALUACION: 'En evaluación',
}
export const ESTADO_RECEPCION_OPCIONES = opciones(ESTADO_RECEPCION_LABEL)

export const ESTADO_STOCK_LABEL: Record<EstadoStock, string> = {
  SIN_STOCK: 'Sin stock',
  STOCK_BAJO: 'Stock bajo',
  STOCK_OK: 'Stock normal',
  SOBRE_STOCK: 'Sobre stock',
}

/**
 * Acciones de solicitud / orden según su ESTADO (el rol se comprueba aparte con `useRol()`):
 * EMPRESA valida / devuelve / cancela; OPERARIO edita / reenvía / elimina / recibe; PROVEEDOR despacha.
 */
export const ACCIONES_ORDEN = {
  /** EMPRESA → ENVIADA (APROBADA solo en datos antiguos). */
  puedeValidar: (e: EstadoOrden) => e === 'PENDIENTE' || e === 'APROBADA',
  /** EMPRESA → OBSERVADA con comentario. */
  puedeDevolver: (e: EstadoOrden) => e === 'PENDIENTE',
  puedeCancelar: (e: EstadoOrden) => e === 'PENDIENTE' || e === 'OBSERVADA' || e === 'APROBADA',
  /** OPERARIO: cabecera y líneas. */
  puedeEditar: (e: EstadoOrden) => e === 'PENDIENTE' || e === 'OBSERVADA',
  puedeReenviar: (e: EstadoOrden) => e === 'OBSERVADA',
  puedeEliminar: (e: EstadoOrden) => e === 'PENDIENTE',
  /** OPERARIO recibe / PROVEEDOR despacha. */
  puedeRecibir: (e: EstadoOrden) => e === 'ENVIADA' || e === 'PARCIAL',
} as const
