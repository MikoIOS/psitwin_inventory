/**
 * Detalle de un operario: datos + historial de movimientos y recepciones que registró.
 * Datos: useMovimientosPorOperario / useRecepcionesPorOperario (ya vienen ordenados, recientes primero).
 */
import { useId, useState, type ReactNode } from 'react'
import { Link } from 'react-router'
import { etiquetaTurno, operarioActivo } from '@/api/enums'
import { useMovimientosPorOperario } from '@/api/movimientos'
import { useProductos } from '@/api/productos'
import { useRecepcionesPorOperario } from '@/api/recepciones'
import type { Movimiento, Operario } from '@/api/types'
import { useUbicaciones } from '@/api/ubicaciones'
import { Button, DataTable, EmptyState, LinkButton, Modal, StatusBadge } from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatFechaHora, formatNumero, shortId, textoOVacio } from '@/lib/format'
import { paths } from '@/paths'

export interface OperarioDetalleModalProps {
  operario: Operario | null
  nombreAlmacen: string
  onClose: () => void
  onEditar: (o: Operario) => void
  onToggleEstado: (o: Operario) => void
  toggling: boolean
}

type Pestana = 'movimientos' | 'recepciones'

export function OperarioDetalleModal({ operario, nombreAlmacen, onClose, onEditar, onToggleEstado, toggling }: OperarioDetalleModalProps) {
  const [pestana, setPestana] = useState<Pestana>('movimientos')
  const id = operario?.id_operario
  const movQ = useMovimientosPorOperario(id)
  const recQ = useRecepcionesPorOperario(id)
  const tabsId = useId()

  return (
    <Modal
      open={!!operario}
      onClose={onClose}
      size="xl"
      title={operario ? `${operario.nombre} ${operario.apellido}` : 'Operario'}
      description={operario ? `${operario.cargo} · ${nombreAlmacen}` : undefined}
      footer={
        operario && (
          <>
            <Button variant="secondary" onClick={onClose}>
              Cerrar
            </Button>
            <Button
              variant="secondary"
              icon={operarioActivo(operario.estado) ? 'x' : 'check'}
              loading={toggling}
              onClick={() => onToggleEstado(operario)}
            >
              {operarioActivo(operario.estado) ? 'Desactivar' : 'Activar'}
            </Button>
            <Button icon="edit" onClick={() => onEditar(operario)}>
              Editar
            </Button>
          </>
        )
      }
    >
      {operario && (
        <div className="flex flex-col gap-5">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-[var(--radius-ui)] border border-border bg-surface-2/60 p-4 text-sm sm:grid-cols-4">
            <Dato label="Estado">
              <StatusBadge estado={operario.estado} />
            </Dato>
            <Dato label="Turno">{etiquetaTurno(operario.turno)}</Dato>
            <Dato label="Almacén">{nombreAlmacen}</Dato>
            <Dato label="Código">
              <span className="font-mono">{shortId(operario.id_operario)}</span>
            </Dato>
          </dl>

          <div>
            <div role="tablist" aria-label="Historial del operario" className="mb-3 flex gap-1 border-b border-border">
              <Tab id={`${tabsId}-mov`} controls={`${tabsId}-mov-panel`} activa={pestana === 'movimientos'} onClick={() => setPestana('movimientos')}>
                Movimientos{movQ.data ? ` (${movQ.data.length})` : ''}
              </Tab>
              <Tab id={`${tabsId}-rec`} controls={`${tabsId}-rec-panel`} activa={pestana === 'recepciones'} onClick={() => setPestana('recepciones')}>
                Recepciones{recQ.data ? ` (${recQ.data.length})` : ''}
              </Tab>
            </div>

            {pestana === 'movimientos' ? (
              <div role="tabpanel" id={`${tabsId}-mov-panel`} aria-labelledby={`${tabsId}-mov`}>
                <HistorialMovimientos q={movQ} />
              </div>
            ) : (
              <div role="tabpanel" id={`${tabsId}-rec-panel`} aria-labelledby={`${tabsId}-rec`}>
                <DataTable
                  caption="Recepciones registradas por el operario"
                  data={recQ.data}
                  loading={recQ.isLoading}
                  error={recQ.error}
                  onRetry={() => void recQ.refetch()}
                  rowKey={(r) => r.id_recepcion}
                  empty={<EmptyState compact icon="inbox" title="Sin recepciones" description="Este operario aún no ha recibido mercadería." />}
                  columns={[
                    { id: 'fecha', header: 'Fecha', cell: (r) => formatFechaHora(r.fecha_recepcion), mobile: 'title' },
                    {
                      id: 'orden',
                      header: 'Orden',
                      cell: (r) => (
                        <Link to={paths.orden(r.id_orden_reposicion)} className="font-mono text-accent-ink underline-offset-2 hover:underline">
                          #{shortId(r.id_orden_reposicion)}
                        </Link>
                      ),
                    },
                    { id: 'obs', header: 'Observaciones', cell: (r) => textoOVacio(r.observaciones_generales) },
                  ]}
                  actions={(r) => (
                    <LinkButton size="sm" variant="ghost" iconRight="chevron-right" to={paths.recepcion(r.id_recepcion)}>
                      Ver recepción
                    </LinkButton>
                  )}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </Modal>
  )
}

function HistorialMovimientos({ q }: { q: ReturnType<typeof useMovimientosPorOperario> }) {
  const prodQ = useProductos()
  const ub = useUbicaciones()
  const prodPorId = new Map((prodQ.data ?? []).map((p) => [p.id_producto, p]))

  // El movimiento trae id_producto e id_rack directamente.
  const producto = (m: Movimiento) => prodPorId.get(m.id_producto)?.nombre ?? `Producto ${shortId(m.id_producto)}`
  const ubicacion = (m: Movimiento) => ub.porRack.get(m.id_rack)?.etiqueta ?? '—'

  return (
    <DataTable
      caption="Movimientos registrados por el operario"
      data={q.data}
      loading={q.isLoading}
      error={q.error}
      onRetry={() => void q.refetch()}
      rowKey={(m) => m.id_movimiento}
      empty={<EmptyState compact icon="arrows" title="Sin movimientos" description="Este operario aún no ha registrado movimientos de inventario." />}
      columns={[
        { id: 'producto', header: 'Producto', cell: (m) => producto(m), mobile: 'title' },
        { id: 'tipo', header: 'Tipo', cell: (m) => <StatusBadge estado={m.tipo_movimiento} />, mobile: 'badge' },
        { id: 'motivo', header: 'Motivo', cell: (m) => <StatusBadge estado={m.motivo_movimiento} /> },
        { id: 'cantidad', header: 'Cantidad', cell: (m) => formatNumero(m.cantidad), align: 'right' },
        {
          id: 'stock',
          header: 'Stock',
          cell: (m) => `${formatNumero(m.stock_anterior)} → ${formatNumero(m.stock_nuevo)}`,
          align: 'right',
        },
        { id: 'ubicacion', header: 'Ubicación', cell: (m) => ubicacion(m) },
        { id: 'fecha', header: 'Fecha', cell: (m) => formatFechaHora(m.fecha_hora) },
      ]}
    />
  )
}

function Dato({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="label-stencil">{label}</dt>
      <dd className="mt-1 truncate text-fg">{children}</dd>
    </div>
  )
}

function Tab({ id, controls, activa, onClick, children }: { id: string; controls: string; activa: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      role="tab"
      id={id}
      aria-controls={controls}
      aria-selected={activa}
      onClick={onClick}
      className={cn(
        '-mb-px min-h-10 border-b-2 px-3 text-sm font-medium transition-colors',
        activa ? 'border-accent text-fg' : 'border-transparent text-fg-muted hover:text-fg',
      )}
    >
      {children}
    </button>
  )
}
