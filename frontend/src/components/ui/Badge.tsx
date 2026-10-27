/**
 * Badges de estado.
 *   <Badge tone="info">Texto</Badge>
 *   <StatusBadge estado="PENDIENTE" />         // órdenes, operarios, proveedores, racks, movimientos
 *   <StockBadge inventario={inv} />  o  <StockBadge estado="STOCK_BAJO" />
 */
import type { ReactNode } from 'react'
import {
  ESTADO_ORDEN_LABEL,
  ESTADO_RACK_LABEL,
  ESTADO_RECEPCION_LABEL,
  ESTADO_STOCK_LABEL,
  MOTIVO_MOVIMIENTO_LABEL,
  TIPO_MOVIMIENTO_LABEL,
} from '@/api/enums'
import type { EstadoStock, Inventario } from '@/api/types'
import { cn } from '@/lib/cn'
import { estadoStock } from '@/lib/stock'

export type BadgeTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'accent'

const TONES: Record<BadgeTone, { box: string; dot: string }> = {
  neutral: { box: 'bg-neutral-soft text-neutral-ink border-border', dot: 'bg-fg-subtle' },
  info: { box: 'bg-info-soft text-info border-info/25', dot: 'bg-info' },
  success: { box: 'bg-success-soft text-success border-success/25', dot: 'bg-success' },
  warning: { box: 'bg-warning-soft text-warning border-warning/30', dot: 'bg-warning' },
  danger: { box: 'bg-danger-soft text-danger border-danger/25', dot: 'bg-danger' },
  accent: { box: 'bg-accent-soft text-accent-ink border-accent/40', dot: 'bg-accent' },
}

export interface BadgeProps {
  tone?: BadgeTone
  /** Punto de color a la izquierda (por defecto sí). */
  dot?: boolean
  className?: string
  title?: string
  children: ReactNode
}

export function Badge({ tone = 'neutral', dot = true, className, title, children }: BadgeProps) {
  const t = TONES[tone]
  return (
    <span
      title={title}
      className={cn(
        'inline-flex h-6 items-center gap-1.5 rounded-full border px-2.5 font-mono text-[0.6875rem] font-semibold tracking-wide whitespace-nowrap uppercase',
        t.box,
        className,
      )}
    >
      {dot && <span className={cn('size-1.5 rounded-full', t.dot)} aria-hidden="true" />}
      {children}
    </span>
  )
}

/* ------------------------------------------------------------------ */

type EstadoConocido =
  | 'PENDIENTE' | 'OBSERVADA' | 'APROBADA' | 'ENVIADA' | 'PARCIAL' | 'RECIBIDA' | 'CANCELADA'
  | 'ACTIVO' | 'INACTIVO'
  | 'DISPONIBLE' | 'LLENO' | 'MANTENIMIENTO'
  | 'ENTRADA' | 'SALIDA' | 'AJUSTE'
  | 'RECEPCION' | 'VENTA' | 'MERMA' | 'CONTEO_FISICO' | 'REPOSICION' | 'VENCIMIENTO' | 'DEVOLUCION' | 'OTRO'
  | 'CONFORME' | 'RECHAZADO' | 'EN_EVALUACION'
  | 'ACTIVA' | 'ABIERTA' | 'VISTA' | 'RESUELTA' | 'IGNORADA'
  | EstadoStock

const ESTADOS: Record<EstadoConocido, { tone: BadgeTone; label: string }> = {
  // Orden de reposición
  PENDIENTE: { tone: 'neutral', label: ESTADO_ORDEN_LABEL.PENDIENTE },
  OBSERVADA: { tone: 'warning', label: ESTADO_ORDEN_LABEL.OBSERVADA },
  APROBADA: { tone: 'info', label: ESTADO_ORDEN_LABEL.APROBADA },
  ENVIADA: { tone: 'accent', label: ESTADO_ORDEN_LABEL.ENVIADA },
  PARCIAL: { tone: 'warning', label: ESTADO_ORDEN_LABEL.PARCIAL },
  RECIBIDA: { tone: 'success', label: ESTADO_ORDEN_LABEL.RECIBIDA },
  CANCELADA: { tone: 'danger', label: ESTADO_ORDEN_LABEL.CANCELADA },
  // Operario / proveedor / rack (versión antigua)
  ACTIVO: { tone: 'success', label: ESTADO_RACK_LABEL.ACTIVO },
  INACTIVO: { tone: 'neutral', label: ESTADO_RACK_LABEL.INACTIVO },
  // Rack
  DISPONIBLE: { tone: 'success', label: ESTADO_RACK_LABEL.DISPONIBLE },
  LLENO: { tone: 'accent', label: ESTADO_RACK_LABEL.LLENO },
  MANTENIMIENTO: { tone: 'warning', label: ESTADO_RACK_LABEL.MANTENIMIENTO },
  // Movimiento: tipo
  ENTRADA: { tone: 'success', label: TIPO_MOVIMIENTO_LABEL.ENTRADA },
  SALIDA: { tone: 'danger', label: TIPO_MOVIMIENTO_LABEL.SALIDA },
  AJUSTE: { tone: 'info', label: TIPO_MOVIMIENTO_LABEL.AJUSTE },
  // Movimiento: motivo
  RECEPCION: { tone: 'accent', label: MOTIVO_MOVIMIENTO_LABEL.RECEPCION },
  VENTA: { tone: 'neutral', label: MOTIVO_MOVIMIENTO_LABEL.VENTA },
  MERMA: { tone: 'warning', label: MOTIVO_MOVIMIENTO_LABEL.MERMA },
  CONTEO_FISICO: { tone: 'info', label: MOTIVO_MOVIMIENTO_LABEL.CONTEO_FISICO },
  REPOSICION: { tone: 'success', label: MOTIVO_MOVIMIENTO_LABEL.REPOSICION },
  VENCIMIENTO: { tone: 'danger', label: MOTIVO_MOVIMIENTO_LABEL.VENCIMIENTO },
  DEVOLUCION: { tone: 'info', label: MOTIVO_MOVIMIENTO_LABEL.DEVOLUCION },
  OTRO: { tone: 'neutral', label: MOTIVO_MOVIMIENTO_LABEL.OTRO },
  // Línea de recepción
  CONFORME: { tone: 'success', label: ESTADO_RECEPCION_LABEL.CONFORME },
  RECHAZADO: { tone: 'danger', label: ESTADO_RECEPCION_LABEL.RECHAZADO },
  EN_EVALUACION: { tone: 'warning', label: ESTADO_RECEPCION_LABEL.EN_EVALUACION },
  // Alerta
  ACTIVA: { tone: 'danger', label: 'Abierta' },
  ABIERTA: { tone: 'danger', label: 'Abierta' },
  VISTA: { tone: 'warning', label: 'Atendida' },
  RESUELTA: { tone: 'success', label: 'Resuelta' },
  IGNORADA: { tone: 'neutral', label: 'Ignorada' },
  // Stock
  SIN_STOCK: { tone: 'danger', label: ESTADO_STOCK_LABEL.SIN_STOCK },
  STOCK_BAJO: { tone: 'warning', label: ESTADO_STOCK_LABEL.STOCK_BAJO },
  STOCK_OK: { tone: 'success', label: ESTADO_STOCK_LABEL.STOCK_OK },
  SOBRE_STOCK: { tone: 'info', label: ESTADO_STOCK_LABEL.SOBRE_STOCK },
}

export interface StatusBadgeProps {
  /** Cualquier estado/enum conocido. Valores desconocidos se muestran tal cual en tono neutro. */
  estado: EstadoConocido | (string & {}) | null | undefined
  className?: string
}

export function StatusBadge({ estado, className }: StatusBadgeProps) {
  if (!estado) return null
  const cfg = ESTADOS[estado as EstadoConocido] ?? ESTADOS[estado.toUpperCase() as EstadoConocido] ?? { tone: 'neutral' as const, label: estado }
  return (
    <Badge tone={cfg.tone} {...(className ? { className } : {})}>
      {cfg.label}
    </Badge>
  )
}

export type StockBadgeProps =
  | { estado: EstadoStock; inventario?: never; className?: string }
  | { inventario: Pick<Inventario, 'stock_actual' | 'stock_minimo' | 'stock_maximo'>; estado?: never; className?: string }

/** Estado de stock de un inventario (calculado) o explícito. */
export function StockBadge(props: StockBadgeProps) {
  const estado = props.estado ?? estadoStock(props.inventario!)
  return <StatusBadge estado={estado} {...(props.className ? { className: props.className } : {})} />
}
