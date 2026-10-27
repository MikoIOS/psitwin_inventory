/**
 * Barra visual del nivel de stock de un inventario: relleno = stock_actual sobre la escala
 * (stock_maximo, o el stock actual si lo supera), marca vertical en el mínimo y, en sobre stock,
 * marca del máximo. Color según el estado calculado (estadoStock).
 */
import type { EstadoStock, Inventario } from '@/api/types'
import { cn } from '@/lib/cn'
import { formatNumero } from '@/lib/format'
import { estadoStock } from '@/lib/stock'

const FILL: Record<EstadoStock, string> = {
  SIN_STOCK: 'bg-danger',
  STOCK_BAJO: 'bg-warning',
  STOCK_OK: 'bg-success',
  SOBRE_STOCK: 'bg-info',
}

export interface StockLevelBarProps {
  inventario: Pick<Inventario, 'stock_actual' | 'stock_minimo' | 'stock_maximo'>
  className?: string
}

export function StockLevelBar({ inventario, className }: StockLevelBarProps) {
  const { stock_actual: actual, stock_minimo: min, stock_maximo: max } = inventario
  const estado = estadoStock(inventario)
  const escala = Math.max(max, actual, min, 1)
  const pct = (v: number) => Math.min(100, Math.max(0, (v / escala) * 100))
  const etiqueta = `Stock ${formatNumero(actual)} de un máximo de ${formatNumero(max)} (mínimo ${formatNumero(min)})`

  return (
    <div
      role="meter"
      aria-label={etiqueta}
      aria-valuemin={0}
      aria-valuemax={escala}
      aria-valuenow={actual}
      title={etiqueta}
      className={cn('relative h-2 w-full min-w-20 rounded-full bg-surface-3', className)}
    >
      <div className={cn('h-full rounded-full', FILL[estado])} style={{ width: `${pct(actual)}%` }} />
      {min > 0 && (
        <span
          aria-hidden="true"
          className="absolute -top-0.5 h-3 w-0.5 rounded-full bg-fg-muted"
          style={{ left: `calc(${pct(min)}% - 1px)` }}
        />
      )}
      {max > 0 && escala > max && (
        <span
          aria-hidden="true"
          className="absolute -top-0.5 h-3 w-0.5 rounded-full bg-fg"
          style={{ left: `calc(${pct(max)}% - 1px)` }}
        />
      )}
    </div>
  )
}
