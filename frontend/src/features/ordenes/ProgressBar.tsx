import { cn } from '@/lib/cn'
import { formatNumero } from '@/lib/format'

export interface ProgressBarProps {
  value: number
  max: number
  /** Texto accesible (ej. "Avance de recepción de Arroz"). */
  label: string
  className?: string
  /** Muestra el porcentaje a la derecha. */
  showPercent?: boolean
}

/** Barra de avance (aceptado / solicitado). */
export function ProgressBar({ value, max, label, className, showPercent = true }: ProgressBarProps) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0
  const completo = max > 0 && value >= max
  return (
    <div className={cn('flex min-w-24 items-center gap-2', className)}>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={Math.min(value, max)}
        aria-valuetext={`${formatNumero(value)} de ${formatNumero(max)}`}
        className="h-2 flex-1 overflow-hidden rounded-full bg-surface-3"
      >
        <div
          className={cn('h-full rounded-full transition-[width]', completo ? 'bg-success' : pct > 0 ? 'bg-accent' : 'bg-transparent')}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showPercent && <span className="w-10 text-right font-mono text-xs text-fg-muted tabular">{Math.round(pct)}%</span>}
    </div>
  )
}
