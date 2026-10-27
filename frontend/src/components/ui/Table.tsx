/**
 * Tabla de datos responsive: tabla en ≥ md, tarjetas apiladas en móvil.
 *
 *   <DataTable
 *     caption="Productos"
 *     data={productos} rowKey={(p) => p.id_producto}
 *     loading={q.isLoading} error={q.error} onRetry={q.refetch}
 *     empty={<EmptyState title="Sin productos" />}
 *     onRowClick={(p) => navigate(`/productos/${p.id_producto}`)}
 *     columns={[
 *       { id: 'nombre', header: 'Nombre', cell: (p) => p.nombre, mobile: 'title' },
 *       { id: 'cat', header: 'Categoría', cell: (p) => p.categoria },
 *       { id: 'stock', header: 'Stock', cell: (p) => p.stock, align: 'right' },
 *     ]}
 *     actions={(p) => <Button size="sm" variant="ghost" icon="edit" iconOnly aria-label="Editar" />}
 *   />
 */
import type { KeyboardEvent, ReactNode } from 'react'
import { cn } from '@/lib/cn'
import { ErrorState } from './EmptyState'
import { LoadingBlock } from './Spinner'

export interface Column<T> {
  id: string
  header: ReactNode
  cell: (row: T) => ReactNode
  align?: 'left' | 'right' | 'center'
  className?: string
  /**
   * Presentación en móvil:
   *  - 'title'    → encabezado de la tarjeta
   *  - 'badge'    → a la derecha del título (estado)
   *  - 'field'    → par etiqueta/valor (por defecto)
   *  - 'hidden'   → no se muestra en móvil
   */
  mobile?: 'title' | 'badge' | 'field' | 'hidden'
}

export interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[] | undefined
  rowKey: (row: T) => string
  /** Título accesible de la tabla (se lee en lectores de pantalla). */
  caption: string
  loading?: boolean
  error?: unknown
  onRetry?: () => void
  empty?: ReactNode
  onRowClick?: (row: T) => void
  /** Acciones por fila (última columna en desktop, pie de tarjeta en móvil). */
  actions?: (row: T) => ReactNode
  rowClassName?: (row: T) => string | undefined
  className?: string
}

const ALIGN = { left: 'text-left', right: 'text-right', center: 'text-center' }

export function DataTable<T>({
  columns,
  data,
  rowKey,
  caption,
  loading,
  error,
  onRetry,
  empty,
  onRowClick,
  actions,
  rowClassName,
  className,
}: DataTableProps<T>) {
  if (loading && !data) return <LoadingBlock />
  if (error && !data) return <ErrorState error={error} {...(onRetry ? { onRetry } : {})} />
  if (!data || data.length === 0) return <>{empty ?? <p className="py-8 text-center text-sm text-fg-muted">Sin registros.</p>}</>

  const clickProps = (row: T) =>
    onRowClick
      ? {
          onClick: () => onRowClick(row),
          onKeyDown: (e: KeyboardEvent) => {
            if (e.target !== e.currentTarget) return
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              onRowClick(row)
            }
          },
          tabIndex: 0,
          role: 'link' as const,
        }
      : {}

  const titleCol = columns.find((c) => c.mobile === 'title') ?? columns[0]
  const badgeCols = columns.filter((c) => c.mobile === 'badge')
  const fieldCols = columns.filter((c) => c !== titleCol && c.mobile !== 'badge' && c.mobile !== 'hidden')

  return (
    <div className={className}>
      {/* Desktop / tablet */}
      <div className="hidden overflow-x-auto rounded-[calc(var(--radius-ui)+2px)] border border-border bg-surface shadow-card md:block">
        <table className="w-full border-collapse text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr className="border-b border-border-strong bg-surface-2">
              {columns.map((c) => (
                <th key={c.id} scope="col" className={cn('label-stencil px-4 py-2.5 whitespace-nowrap', ALIGN[c.align ?? 'left'], c.className)}>
                  {c.header}
                </th>
              ))}
              {actions && (
                <th scope="col" className="px-4 py-2.5">
                  <span className="sr-only">Acciones</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr
                key={rowKey(row)}
                {...clickProps(row)}
                className={cn(
                  'border-b border-border last:border-b-0',
                  onRowClick && 'cursor-pointer hover:bg-accent-soft/40 focus-visible:bg-accent-soft/40',
                  rowClassName?.(row),
                )}
              >
                {columns.map((c) => (
                  <td key={c.id} className={cn('px-4 py-3 align-middle', ALIGN[c.align ?? 'left'], c.align === 'right' && 'tabular', c.className)}>
                    {c.cell(row)}
                  </td>
                ))}
                {actions && (
                  <td className="px-4 py-2 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                    <div className="inline-flex items-center gap-1">{actions(row)}</div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Móvil: tarjetas */}
      <ul className="flex flex-col gap-2 md:hidden" aria-label={caption}>
        {data.map((row) => (
          <li
            key={rowKey(row)}
            {...clickProps(row)}
            className={cn(
              'rounded-[calc(var(--radius-ui)+2px)] border border-border bg-surface p-3.5 shadow-card',
              onRowClick && 'cursor-pointer active:bg-surface-2',
              rowClassName?.(row),
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0 font-semibold text-fg">{titleCol?.cell(row)}</div>
              {badgeCols.length > 0 && (
                <div className="flex shrink-0 flex-wrap justify-end gap-1">
                  {badgeCols.map((c) => (
                    <span key={c.id}>{c.cell(row)}</span>
                  ))}
                </div>
              )}
            </div>
            {fieldCols.length > 0 && (
              <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
                {fieldCols.map((c) => (
                  <div key={c.id} className="min-w-0">
                    <dt className="label-stencil">{c.header}</dt>
                    <dd className={cn('truncate text-fg', c.align === 'right' && 'tabular')}>{c.cell(row)}</dd>
                  </div>
                ))}
              </dl>
            )}
            {actions && (
              <div className="mt-3 flex flex-wrap justify-end gap-2 border-t border-border pt-2.5" onClick={(e) => e.stopPropagation()}>
                {actions(row)}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
