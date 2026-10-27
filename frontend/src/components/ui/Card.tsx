import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/cn'

export interface CardProps extends Omit<HTMLAttributes<HTMLElement>, 'title'> {
  title?: ReactNode
  description?: ReactNode
  /** Botones a la derecha de la cabecera. */
  actions?: ReactNode
  /** Rótulo pequeño sobre el título (estilo etiqueta de estantería). */
  eyebrow?: ReactNode
  padding?: 'none' | 'sm' | 'md'
  /** Borde izquierdo de color para destacar (ej. alertas). */
  accent?: 'accent' | 'danger' | 'warning' | 'success' | 'info'
  as?: 'section' | 'article' | 'div'
  children?: ReactNode
}

const PAD = { none: '', sm: 'p-3', md: 'p-4 sm:p-5' }
const ACCENT = {
  accent: 'border-l-4 border-l-accent',
  danger: 'border-l-4 border-l-danger',
  warning: 'border-l-4 border-l-warning',
  success: 'border-l-4 border-l-success',
  info: 'border-l-4 border-l-info',
}

export function Card({ title, description, actions, eyebrow, padding = 'md', accent, as: Tag = 'section', className, children, ...rest }: CardProps) {
  const hasHeader = title || actions || eyebrow || description
  return (
    <Tag
      className={cn('rounded-[calc(var(--radius-ui)+2px)] border border-border bg-surface shadow-card', accent && ACCENT[accent], className)}
      {...rest}
    >
      {hasHeader && (
        <header className={cn('flex flex-wrap items-start justify-between gap-3', padding === 'none' ? 'p-4 sm:px-5' : PAD[padding], children && 'pb-0 sm:pb-0')}>
          <div className="min-w-0">
            {eyebrow && <p className="label-stencil mb-1">{eyebrow}</p>}
            {title && <h2 className="text-base font-semibold text-fg">{title}</h2>}
            {description && <p className="mt-0.5 text-sm text-fg-muted">{description}</p>}
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </header>
      )}
      {children && <div className={cn(PAD[padding], hasHeader && padding !== 'none' && 'pt-4 sm:pt-4')}>{children}</div>}
    </Tag>
  )
}
