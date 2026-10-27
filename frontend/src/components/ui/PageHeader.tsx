import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { Icon } from './Icon'

export interface PageHeaderProps {
  title: ReactNode
  description?: ReactNode
  /** Rótulo sobre el título (ej. "Reposición"). */
  eyebrow?: ReactNode
  /** Botones a la derecha (se apilan debajo en móvil). */
  actions?: ReactNode
  /** Enlace de retorno (ej. { to: '/ordenes', label: 'Órdenes' }). */
  back?: { to: string; label: string }
  /** Contenido extra bajo el título (badges de estado, metadatos). */
  meta?: ReactNode
}

export function PageHeader({ title, description, eyebrow, actions, back, meta }: PageHeaderProps) {
  return (
    <header className="mb-6 flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {back && (
          <Link
            to={back.to}
            className="mb-2 inline-flex min-h-6 items-center gap-1 text-sm text-fg-muted hover:text-fg"
          >
            <Icon name="arrow-left" className="size-4" />
            {back.label}
          </Link>
        )}
        {eyebrow && <p className="label-stencil mb-1">{eyebrow}</p>}
        <h1 className="text-2xl font-semibold tracking-tight text-fg sm:text-[1.75rem]">{title}</h1>
        {description && <p className="mt-1 max-w-2xl text-sm text-fg-muted">{description}</p>}
        {meta && <div className="mt-3 flex flex-wrap items-center gap-2">{meta}</div>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2 sm:justify-end">{actions}</div>}
    </header>
  )
}
