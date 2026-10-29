import { inventarioDetalleId } from '@/api/inventarios'
/**
 * Tabla de inventarios. Todos ven «Historial» (quién lo creó / cambió límites + movimientos con autor).
 * Solo el OPERARIO tiene además: registrar salida, editar mínimo/máximo y eliminar (409 si aún tiene stock).
 * Usada por la pantalla de Inventario y por el detalle de producto.
 */
import { useState, type ReactNode } from 'react'
import { Link } from 'react-router'
import { ApiError } from '@/api/client'
import { useDeleteInventario, useInventarioHistorial } from '@/api/inventarios'
import { useMovimientosPorInventario } from '@/api/movimientos'
import { useRol } from '@/auth/useRol'
import { useProductos } from '@/api/productos'
import type { Inventario } from '@/api/types'
import { useUbicaciones } from '@/api/ubicaciones'
import { Button, ConfirmDialog, DataTable, EmptyState, Modal, StockBadge, useToast, type Column } from '@/components/ui'
import { formatFechaHora, formatNumero } from '@/lib/format'
import { paths } from '@/paths'
import { MovimientoModal } from '@/features/movimientos/MovimientoForm'
import { MovimientosTable } from '@/features/movimientos/MovimientosTable'
import { FormAlert } from './formUtils'
import { InventarioLimitesForm } from './InventarioForm'
import { StockLevelBar } from './StockLevelBar'

export interface InventariosTableProps {
  data: Inventario[] | undefined
  caption: string
  loading?: boolean
  error?: unknown
  onRetry?: () => void
  empty?: ReactNode
  /** Muestra la columna de producto (false en el detalle de producto). Por defecto true. */
  mostrarProducto?: boolean
}

export function InventariosTable({ data, caption, loading, error, onRetry, empty, mostrarProducto = true }: InventariosTableProps) {
  const ub = useUbicaciones()
  const productos = useProductos()
  const toast = useToast()
  const eliminar = useDeleteInventario()
  const productoPorId = new Map((productos.data ?? []).map((p) => [p.id_producto, p]))

  const { esOperario, esEmpresa } = useRol()
  const [historial, setHistorial] = useState<Inventario | null>(null)
  const [movimiento, setMovimiento] = useState<Inventario | null>(null)
  const [editando, setEditando] = useState<Inventario | null>(null)
  const [aEliminar, setAEliminar] = useState<Inventario | null>(null)
  const [errorEliminar, setErrorEliminar] = useState<string | null>(null)

  const nombreProducto = (inv: Inventario) => productoPorId.get(inv.id_producto)?.nombre ?? inv.producto?.nombre ?? 'Producto'

  const columnas: Column<Inventario>[] = [
    ...(mostrarProducto
      ? [
          {
            id: 'producto',
            header: 'Producto',
            mobile: 'title' as const,
            cell: (inv: Inventario) => {
              const p = productoPorId.get(inv.id_producto)
              return (
                <div className="min-w-0">
                  <Link to={paths.producto(inv.id_producto)} className="font-semibold text-fg hover:underline">
                    {nombreProducto(inv)}
                  </Link>
                  {p && <p className="truncate text-xs text-fg-subtle">{[p.categoria, p.marca].filter(Boolean).join(' · ')}</p>}
                </div>
              )
            },
          },
        ]
      : []),
    {
      id: 'ubicacion',
      header: 'Ubicación',
      ...(mostrarProducto ? {} : { mobile: 'title' as const }),
      cell: (inv) => {
        const u = ub.porRack.get(inv.id_rack)
        if (!u) return <span className="text-fg-subtle">{ub.isLoading ? '…' : 'Rack desconocido'}</span>
        return (
          <div className="min-w-0">
            <p className="truncate font-medium text-fg">{u.almacen.nombre}</p>
            <p className="truncate text-xs text-fg-muted">{u.etiquetaCorta}</p>
          </div>
        )
      },
    },
    {
      id: 'actual',
      header: 'Stock actual',
      align: 'right',
      cell: (inv) => <span className="font-mono text-base font-semibold">{formatNumero(inv.stock_actual)}</span>,
    },
    { id: 'min', header: 'Mín.', align: 'right', cell: (inv) => <span className="font-mono text-fg-muted">{formatNumero(inv.stock_minimo)}</span> },
    { id: 'max', header: 'Máx.', align: 'right', cell: (inv) => <span className="font-mono text-fg-muted">{formatNumero(inv.stock_maximo)}</span> },
    { id: 'nivel', header: 'Nivel', cell: (inv) => <StockLevelBar inventario={inv} className="md:w-28" /> },
    { id: 'estado', header: 'Estado', mobile: 'badge', cell: (inv) => <StockBadge inventario={inv} /> },
  ]

  const confirmarEliminar = () => {
    if (!aEliminar) return
    setErrorEliminar(null)
    eliminar.mutate(inventarioDetalleId(aEliminar), {
      onSuccess: () => {
        setAEliminar(null)
        toast.success('Inventario eliminado')
      },
      onError: (e) => {
        if (e instanceof ApiError && e.isHandledGlobally) return
        setErrorEliminar(e instanceof ApiError ? e.detail : 'No se pudo eliminar el inventario.')
      },
    })
  }

  return (
    <>
      <DataTable
        caption={caption}
        data={data}
        loading={loading ?? false}
        error={error}
        {...(onRetry ? { onRetry } : {})}
        empty={empty}
        rowKey={inventarioDetalleId}
        columns={columnas}
        actions={(inv) => (
          <>
            <Button size="sm" variant="ghost" icon="clipboard" onClick={() => setHistorial(inv)} aria-label={`Historial de ${nombreProducto(inv)}`}>
              Historial
            </Button>
            {esEmpresa && <Button size="sm" variant="ghost" icon="edit" iconOnly aria-label={`Editar límites de ${nombreProducto(inv)}`} onClick={() => setEditando(inv)} />}
            {esOperario && (
              <>
                <Button size="sm" variant="secondary" icon="arrows" onClick={() => setMovimiento(inv)}>
                  Salida
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  icon="trash"
                  iconOnly
                  aria-label={`Eliminar inventario de ${nombreProducto(inv)}`}
                  onClick={() => {
                    setErrorEliminar(null)
                    setAEliminar(inv)
                  }}
                />
              </>
            )}
          </>
        )}
      />

      <Modal
        open={!!historial}
        onClose={() => setHistorial(null)}
        size="xl"
        title="Historial del inventario"
        description={historial ? `${nombreProducto(historial)} · ${ub.porRack.get(historial.id_rack)?.etiqueta ?? ''}` : undefined}
      >
        {historial && <HistorialInventario inventario={historial} />}
      </Modal>

      <MovimientoModal open={!!movimiento} onClose={() => setMovimiento(null)} inventario={movimiento ?? undefined} />

      <Modal
        open={!!editando}
        onClose={() => setEditando(null)}
        title="Editar límites de stock"
        description={editando ? `${nombreProducto(editando)} · ${ub.porRack.get(editando.id_rack)?.etiqueta ?? ''}` : undefined}
      >
        {editando && <InventarioLimitesForm inventario={editando} onCancel={() => setEditando(null)} onSuccess={() => setEditando(null)} />}
      </Modal>

      <ConfirmDialog
        open={!!aEliminar}
        title="Eliminar inventario"
        tone="danger"
        confirmLabel="Eliminar"
        loading={eliminar.isPending}
        onCancel={() => setAEliminar(null)}
        onConfirm={confirmarEliminar}
        description={
          aEliminar && (
            <div className="flex flex-col gap-3">
              <p>
                Se eliminará el registro de <strong className="text-fg">{nombreProducto(aEliminar)}</strong> en{' '}
                {ub.porRack.get(aEliminar.id_rack)?.etiqueta ?? 'este rack'}.
              </p>
              {aEliminar.stock_actual > 0 && (
                <p>
                  Todavía tiene <strong className="text-fg">{formatNumero(aEliminar.stock_actual)} und.</strong> en stock: el sistema
                  puede rechazar la eliminación. Registra antes una salida para dejarlo en cero.
                </p>
              )}
              {errorEliminar && <FormAlert title="No se pudo eliminar">{errorEliminar}</FormAlert>}
            </div>
          )
        }
      />
    </>
  )
}

/* ------------------------------------------------------------------ */

const ACCION_LABEL: Record<string, string> = { CREAR: 'Creó el inventario', EDITAR_LIMITES: 'Cambió los límites' }
const CAMPO_LABEL: Record<string, string> = { stock_actual: 'stock', stock_minimo: 'mínimo', stock_maximo: 'máximo', id_rack: 'rack' }

/** "mínimo 5 → 10 · máximo 100 → 80" a partir de los objetos `antes` / `despues` del historial. */
function resumenCambio(antes: Record<string, unknown> | null, despues: Record<string, unknown> | null): string {
  const campos = Object.keys(despues ?? antes ?? {}).filter((k) => k in CAMPO_LABEL && k !== 'id_rack')
  return campos
    .map((k) => {
      const a = antes?.[k]
      const d = despues?.[k]
      return a === undefined || a === null ? `${CAMPO_LABEL[k]} ${String(d)}` : `${CAMPO_LABEL[k]} ${String(a)} → ${String(d)}`
    })
    .join(' · ')
}

/** Quién creó / cambió los límites del inventario y sus movimientos de stock (autor, antes → después). */
function HistorialInventario({ inventario }: { inventario: Inventario }) {
  const histQ = useInventarioHistorial(inventarioDetalleId(inventario))
  const movQ = useMovimientosPorInventario(inventario.id_inventario)
  const cambios = [...(histQ.data ?? [])].sort((a, b) => b.fecha.localeCompare(a.fecha))
  return (
    <div className="flex flex-col gap-6">
      <section aria-labelledby="hist-cambios">
        <h3 id="hist-cambios" className="label-stencil mb-2">
          Creación y cambios de límites
        </h3>
        <DataTable
          caption="Cambios del inventario"
          data={histQ.data ? cambios : undefined}
          loading={histQ.isLoading}
          error={histQ.error}
          onRetry={() => void histQ.refetch()}
          rowKey={(h) => `${h.fecha}-${h.accion}`}
          empty={<EmptyState compact icon="clipboard" title="Sin cambios registrados" description="Este inventario es anterior al registro de historial." />}
          columns={[
            { id: 'fecha', header: 'Fecha', cell: (h) => <span className="font-mono text-xs whitespace-nowrap text-fg-muted">{formatFechaHora(h.fecha)}</span> },
            { id: 'accion', header: 'Acción', mobile: 'title', cell: (h) => ACCION_LABEL[h.accion] ?? h.accion },
            { id: 'autor', header: 'Autor', cell: (h) => h.operario_nombre ?? '—' },
            { id: 'cambio', header: 'Antes → después', cell: (h) => <span className="font-mono text-xs">{resumenCambio(h.antes, h.despues) || '—'}</span> },
          ]}
        />
      </section>
      <section aria-labelledby="hist-movs">
        <h3 id="hist-movs" className="label-stencil mb-2">
          Movimientos de stock
        </h3>
        <MovimientosTable
          caption="Movimientos del inventario"
          data={movQ.data?.filter(m => m.id_detalle_inventario ? m.id_detalle_inventario === inventarioDetalleId(inventario) : m.id_producto === inventario.id_producto && m.id_rack === inventario.id_rack)}
          ocultarProducto
          loading={movQ.isLoading}
          error={movQ.error}
          onRetry={() => void movQ.refetch()}
          empty={<EmptyState compact icon="arrows" title="Sin movimientos" description="Aún no hay entradas ni salidas en este inventario." />}
        />
      </section>
    </div>
  )
}
