import type { ReactNode } from 'react'
import { EmptyState, PageHeader, type IconName } from '@/components/ui'

/**
 * Página provisional para módulos aún no implementados.
 * REEMPLAZAR por la implementación real del módulo.
 */
export function ModulePlaceholder({
  title,
  eyebrow,
  description,
  icon = 'box',
  back,
  children,
}: {
  title: string
  eyebrow?: string
  description?: string
  icon?: IconName
  back?: { to: string; label: string }
  children?: ReactNode
}) {
  return (
    <>
      <PageHeader title={title} {...(eyebrow ? { eyebrow } : {})} {...(description ? { description } : {})} {...(back ? { back } : {})} />
      <EmptyState icon={icon} title="Módulo en construcción" description="Esta sección estará disponible próximamente." />
      {children}
    </>
  )
}
