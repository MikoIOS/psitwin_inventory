import type { ReactNode } from 'react'
import { ApiError } from '@/api/client'
import { cn } from '@/lib/cn'
import { Button } from './Button'
import { Icon, type IconName } from './Icon'

export interface EmptyStateProps {
  icon?: IconName
  title: ReactNode
  description?: ReactNode
  /** Botón u otra acción (ej. "Crear primer producto"). */
  action?: ReactNode
  className?: string
  compact?: boolean
}

export function EmptyState({ icon = 'box', title, description, action, className, compact }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-[var(--radius-ui)] border border-dashed border-border-strong text-center',
        compact ? 'gap-2 px-4 py-6' : 'gap-3 px-6 py-12',
        className,
      )}
    >
      <span className="flex size-11 items-center justify-center rounded-lg bg-surface-2 text-fg-subtle">
        <Icon name={icon} className="size-6" />
      </span>
      <div className="max-w-sm">
        <p className="font-semibold text-fg">{title}</p>
        {description && <p className="mt-1 text-sm text-fg-muted">{description}</p>}
      </div>
      {action}
    </div>
  )
}

export interface ErrorStateProps {
  error: unknown
  onRetry?: () => void
  title?: string
  className?: string
}

/** Estado de error para queries fallidas. */
export function ErrorState({ error, onRetry, title = 'No se pudo cargar la información', className }: ErrorStateProps) {
  const msg = error instanceof ApiError ? error.detail : error instanceof Error ? error.message : 'Error desconocido'
  return (
    <div role="alert" className={cn('flex flex-col items-center gap-3 rounded-[var(--radius-ui)] border border-danger/30 bg-danger-soft/50 px-6 py-10 text-center', className)}>
      <Icon name="alert" className="size-7 text-danger" />
      <div>
        <p className="font-semibold text-fg">{title}</p>
        <p className="mt-1 text-sm text-fg-muted">{msg}</p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" icon="refresh" onClick={onRetry}>
          Reintentar
        </Button>
      )}
    </div>
  )
}
