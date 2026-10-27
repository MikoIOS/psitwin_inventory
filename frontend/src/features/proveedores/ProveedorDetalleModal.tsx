/**
 * Detalle de un proveedor: datos de contacto + órdenes de reposición (useOrdenes filtrado).
 */
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { useAlmacenes } from '@/api/almacenes'
import { useOrdenes } from '@/api/ordenesReposicion'
import type { EstadoOrden, Proveedor } from '@/api/types'
import { Button, DataTable, EmptyState, Icon, LinkButton, Modal, StatusBadge } from '@/components/ui'
import { formatFecha, formatNumero, shortId } from '@/lib/format'
import { paths } from '@/paths'

/** Estados en los que la orden sigue en curso. */
const ABIERTAS: readonly EstadoOrden[] = ['PENDIENTE', 'OBSERVADA', 'APROBADA', 'ENVIADA', 'PARCIAL']

export interface ProveedorDetalleModalProps {
  proveedor: Proveedor | null
  onClose: () => void
  onEditar: (p: Proveedor) => void
  onToggleEstado: (p: Proveedor) => void
  toggling: boolean
}

export function ProveedorDetalleModal({ proveedor, onClose, onEditar, onToggleEstado, toggling }: ProveedorDetalleModalProps) {
  const q = useOrdenes()
  const almacenesQ = useAlmacenes()
  const nombreAlmacen = (id: string) => almacenesQ.data?.find((a) => a.id_almacen === id)?.nombre ?? '—'

  const ordenes = q.data?.filter((o) => o.id_proveedor === proveedor?.id_proveedor).sort((a, b) => (b.fecha_creacion ?? '').localeCompare(a.fecha_creacion ?? ''))
  const abiertas = ordenes?.filter((o) => ABIERTAS.includes(o.estado)).length ?? 0
  const activo = proveedor?.estado === 'ACTIVO'

  return (
    <Modal
      open={!!proveedor}
      onClose={onClose}
      size="xl"
      title={proveedor?.nombre ?? 'Proveedor'}
      description={proveedor ? `RUC ${proveedor.ruc}` : undefined}
      footer={
        proveedor && (
          <>
            <Button variant="secondary" onClick={onClose}>
              Cerrar
            </Button>
            <Button variant="secondary" icon={activo ? 'x' : 'check'} loading={toggling} onClick={() => onToggleEstado(proveedor)}>
              {activo ? 'Desactivar' : 'Activar'}
            </Button>
            <Button variant="secondary" icon="edit" onClick={() => onEditar(proveedor)}>
              Editar
            </Button>
          </>
        )
      }
    >
      {proveedor && (
        <div className="flex flex-col gap-5">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-3 rounded-[var(--radius-ui)] border border-border bg-surface-2/60 p-4 text-sm sm:grid-cols-3">
            <Dato label="Estado">
              <StatusBadge estado={proveedor.estado} />
            </Dato>
            <Dato label="RUC">
              <span className="font-mono">{proveedor.ruc}</span>
            </Dato>
            <Dato label="Entrega estimada">
              <span className="tabular">{formatNumero(proveedor.tiempo_entrega_estimado_dias)}</span>{' '}
              {proveedor.tiempo_entrega_estimado_dias === 1 ? 'día' : 'días'}
            </Dato>
            <Dato label="Correo">
              {proveedor.correo ? (
                <a href={`mailto:${proveedor.correo}`} className="text-accent-ink underline-offset-2 hover:underline">
                  {proveedor.correo}
                </a>
              ) : (
                '—'
              )}
            </Dato>
            <Dato label="Teléfono">
              {proveedor.telefono ? (
                <a href={`tel:${proveedor.telefono.replace(/[^\d+]/g, '')}`} className="tabular text-accent-ink underline-offset-2 hover:underline">
                  {proveedor.telefono}
                </a>
              ) : (
                '—'
              )}
            </Dato>
            <Dato label="Dirección">{proveedor.direccion ?? '—'}</Dato>
          </dl>

          {!activo && (
            <p className="flex items-start gap-2 rounded-[var(--radius-ui)] border border-warning/30 bg-warning-soft/50 px-3 py-2 text-sm text-fg">
              <Icon name="info" className="mt-0.5 size-4 shrink-0 text-warning" />
              Proveedor inactivo: no aparece al crear órdenes de reposición. Actívalo para volver a pedirle mercadería.
            </p>
          )}

          <section aria-labelledby="ordenes-proveedor">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
              <h3 id="ordenes-proveedor" className="text-base font-semibold text-fg">
                Órdenes de reposición
              </h3>
              {ordenes && ordenes.length > 0 && (
                <p className="text-sm text-fg-muted">
                  <span className="tabular font-semibold text-fg">{ordenes.length}</span> en total ·{' '}
                  <span className="tabular font-semibold text-fg">{abiertas}</span> en curso
                </p>
              )}
            </div>
            <DataTable
              caption={`Órdenes de reposición de ${proveedor.nombre}`}
              data={ordenes}
              loading={q.isLoading}
              error={q.error}
              onRetry={() => void q.refetch()}
              rowKey={(o) => o.id_orden_reposicion}
              empty={
                <EmptyState
                  compact
                  icon="clipboard"
                  title="Sin órdenes"
                  description="Todavía no se ha pedido mercadería a este proveedor."
                />
              }
              columns={[
                {
                  id: 'codigo',
                  header: 'Orden',
                  mobile: 'title',
                  cell: (o) => (
                    <Link to={paths.orden(o.id_orden_reposicion)} className="font-mono text-accent-ink underline-offset-2 hover:underline">
                      #{shortId(o.id_orden_reposicion)}
                    </Link>
                  ),
                },
                { id: 'estado', header: 'Estado', cell: (o) => <StatusBadge estado={o.estado} />, mobile: 'badge' },
                { id: 'almacen', header: 'Almacén', cell: (o) => nombreAlmacen(o.id_almacen) },
                { id: 'creada', header: 'Creada', cell: (o) => formatFecha(o.fecha_creacion) },
                { id: 'estimada', header: 'Recepción estimada', cell: (o) => formatFecha(o.fecha_estimada_recepcion) },
              ]}
              actions={(o) => (
                <LinkButton size="sm" variant="ghost" iconRight="chevron-right" to={paths.orden(o.id_orden_reposicion)}>
                  Ver orden
                </LinkButton>
              )}
            />
          </section>
        </div>
      )}
    </Modal>
  )
}

function Dato({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="label-stencil">{label}</dt>
      <dd className="mt-1 break-words text-fg">{children}</dd>
    </div>
  )
}
