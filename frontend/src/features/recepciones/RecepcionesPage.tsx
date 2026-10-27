/**
 * Recepciones de mercadería: órdenes por recibir (ENVIADA/PARCIAL) como accesos rápidos y listado de
 * recepciones (fecha, orden, operario, nº de líneas). `?orden=<id>` abre el alta con esa orden elegida.
 * El backend no filtra recepciones por empresa: se acotan a las órdenes de la empresa autenticada.
 */
import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { ACCIONES_ORDEN } from '@/api/enums'
import { useOrdenes } from '@/api/ordenesReposicion'
import { useRecepciones } from '@/api/recepciones'
import type { OrdenReposicion } from '@/api/types'
import { Button, Card, DataTable, EmptyState, PageHeader, StatusBadge } from '@/components/ui'
import { formatFechaHora } from '@/lib/format'
import { paths } from '@/paths'
import { codigoOrden, codigoRecepcion, useNombres } from '@/features/ordenes/useNombres'
import { useRol } from '@/auth/useRol'
import { RecepcionCrearModal } from './RecepcionCrearModal'

export default function RecepcionesPage() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const ordenParam = params.get('orden') ?? undefined
  const nombres = useNombres()

  const { esOperario } = useRol()
  const recepcionesQ = useRecepciones()
  const ordenesQ = useOrdenes()

  const [modal, setModal] = useState<{ idOrden?: string } | null>(ordenParam ? { idOrden: ordenParam } : null)

  const ordenPorId = new Map((ordenesQ.data ?? []).map((o) => [o.id_orden_reposicion, o]))
  const recepciones = recepcionesQ.data && ordenesQ.data ? recepcionesQ.data.filter((r) => ordenPorId.has(r.id_orden_reposicion)) : undefined

  const porRecibir = (ordenesQ.data ?? [])
    .filter((o) => ACCIONES_ORDEN.puedeRecibir(o.estado))
    .sort((a, b) => (a.fecha_estimada_recepcion ?? '').localeCompare(b.fecha_estimada_recepcion ?? ''))

  const cerrarModal = () => {
    setModal(null)
    if (ordenParam) {
      const next = new URLSearchParams(params)
      next.delete('orden')
      setParams(next, { replace: true })
    }
  }

  return (
    <>
      <PageHeader
        title="Recepciones"
        eyebrow="Reposición"
        description="Registro de la mercadería que llega de los proveedores. Cada producto aceptado ingresa al inventario automáticamente."
        {...(esOperario
          ? {
              actions: (
                <Button icon="plus" size="lg" className="sm:h-10 sm:text-sm" onClick={() => setModal({})}>
                  Nueva recepción
                </Button>
              ),
            }
          : {})}
      />

      {porRecibir.length > 0 && (
        <Card padding="md" title="Órdenes por recibir" description="Enviadas al proveedor o con recepción parcial." className="mb-5" accent="accent">
          <ul className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {porRecibir.map((o) => (
              <OrdenPorRecibir
                key={o.id_orden_reposicion}
                orden={o}
                proveedor={nombres.proveedor(o.id_proveedor)}
                almacen={nombres.almacen(o.id_almacen)}
                {...(esOperario ? { onRecibir: () => setModal({ idOrden: o.id_orden_reposicion }) } : {})}
              />
            ))}
          </ul>
        </Card>
      )}

      <h2 className="mb-3 text-lg font-semibold text-fg">Historial de recepciones</h2>
      <DataTable
        caption="Recepciones registradas"
        data={recepciones}
        loading={recepcionesQ.isLoading || ordenesQ.isLoading}
        error={recepcionesQ.error ?? ordenesQ.error}
        onRetry={() => {
          void recepcionesQ.refetch()
          void ordenesQ.refetch()
        }}
        rowKey={(r) => r.id_recepcion}
        onRowClick={(r) => navigate(paths.recepcion(r.id_recepcion))}
        empty={
          <EmptyState
            icon="inbox"
            title="Aún no hay recepciones"
            description="Cuando una orden esté enviada, registra aquí la llegada de la mercadería."
          />
        }
        columns={[
          {
            id: 'codigo',
            header: 'Recepción',
            mobile: 'title',
            cell: (r) => <span className="font-mono font-semibold">{codigoRecepcion(r.id_recepcion)}</span>,
          },
          {
            id: 'estado',
            header: 'Estado orden',
            mobile: 'badge',
            cell: (r) => <StatusBadge estado={ordenPorId.get(r.id_orden_reposicion)?.estado} />,
          },
          { id: 'fecha', header: 'Fecha', cell: (r) => formatFechaHora(r.fecha_recepcion) },
          {
            id: 'orden',
            header: 'Orden',
            cell: (r) => {
              const o = ordenPorId.get(r.id_orden_reposicion)
              return (
                <span className="flex min-w-0 flex-col">
                  <span className="font-mono text-sm">{codigoOrden(r.id_orden_reposicion)}</span>
                  {o && <span className="truncate text-xs text-fg-muted">{nombres.proveedor(o.id_proveedor)}</span>}
                </span>
              )
            },
          },
          { id: 'operario', header: 'Operario', cell: (r) => nombres.operario(r.id_operario) },
          {
            id: 'lineas',
            header: 'Líneas',
            align: 'right',
            cell: (r) => r.detalles.length,
          },
        ]}
      />

      <RecepcionCrearModal
        open={!!modal}
        onClose={cerrarModal}
        idOrdenInicial={modal?.idOrden}
        onCreated={(r) => {
          setModal(null)
          navigate(paths.recepcion(r.id_recepcion))
        }}
      />
    </>
  )
}

function OrdenPorRecibir({
  orden,
  proveedor,
  almacen,
  onRecibir,
}: {
  orden: OrdenReposicion
  proveedor: string
  almacen: string
  /** Solo el OPERARIO recibe. */
  onRecibir?: () => void
}) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-[var(--radius-ui)] border border-border bg-surface-2/60 p-3">
      <div className="min-w-0">
        <p className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-sm font-semibold">{codigoOrden(orden)}</span>
          <StatusBadge estado={orden.estado} />
        </p>
        <p className="mt-0.5 truncate text-sm text-fg">{proveedor}</p>
        <p className="truncate text-xs text-fg-muted">
          {almacen} · est. {formatFechaHora(orden.fecha_estimada_recepcion)}
        </p>
      </div>
      {onRecibir && (
        <Button size="lg" className="sm:h-10 sm:text-sm" icon="inbox" onClick={onRecibir} aria-label={`Recibir orden ${codigoOrden(orden)}`}>
          Recibir
        </Button>
      )}
    </li>
  )
}
