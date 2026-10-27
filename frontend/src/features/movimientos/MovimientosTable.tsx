/**
 * Historial de movimientos (SOLO LECTURA: sin acciones de editar ni eliminar).
 * Resuelve producto, ubicación y operario de cada movimiento con `useContextoMovimientos()`.
 * El backend devuelve `id_producto` e `id_rack` en cada movimiento: se usan directamente.
 */
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { useInventarios } from '@/api/inventarios'
import { useOperarios } from '@/api/operarios'
import { useProductos } from '@/api/productos'
import type { Inventario, Movimiento, Operario, Producto } from '@/api/types'
import { useUbicaciones, type RackUbicado } from '@/api/ubicaciones'
import { DataTable, StatusBadge, type Column } from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatFechaHora, formatNumero } from '@/lib/format'
import { paths } from '@/paths'

export interface ContextoMovimiento {
  inventario: Inventario | undefined
  producto: Producto | undefined
  ubicacion: RackUbicado | undefined
  operario: Operario | undefined
}

/** Mapas para describir movimientos y acotarlos a la empresa autenticada. */
export function useContextoMovimientos() {
  const inventarios = useInventarios()
  const productos = useProductos()
  const operarios = useOperarios()
  const ub = useUbicaciones()

  const inventarioPorId = new Map((inventarios.data ?? []).map((i) => [i.id_inventario, i]))
  const productoPorId = new Map((productos.data ?? []).map((p) => [p.id_producto, p]))
  const operarioPorId = new Map((operarios.data ?? []).map((o) => [o.id_operario, o]))

  const contexto = (m: Movimiento): ContextoMovimiento => {
    const inventario = inventarioPorId.get(m.id_inventario)
    const idProducto = m.id_producto ?? inventario?.id_producto
    const idRack = m.id_rack ?? inventario?.id_rack
    return {
      inventario,
      producto: idProducto ? productoPorId.get(idProducto) : undefined,
      ubicacion: idRack ? ub.porRack.get(idRack) : undefined,
      operario: m.id_operario ? operarioPorId.get(m.id_operario) : undefined,
    }
  }

  /** El backend no filtra por empresa: se acota por el rack del movimiento (o, en su defecto, por el operario). */
  const perteneceAEmpresa = (m: Movimiento): boolean => {
    const idRack = m.id_rack ?? inventarioPorId.get(m.id_inventario)?.id_rack
    if (idRack && ub.perteneceAEmpresa(idRack)) return true
    return !!m.id_operario && operarioPorId.has(m.id_operario)
  }

  return {
    contexto,
    perteneceAEmpresa,
    isLoading: inventarios.isLoading || productos.isLoading || operarios.isLoading || ub.isLoading,
    error: inventarios.error ?? productos.error ?? operarios.error ?? ub.error,
  }
}

export function nombreOperario(o: Pick<Operario, 'nombre' | 'apellido'> | undefined): string {
  return o ? `${o.nombre} ${o.apellido}`.trim() : '—'
}

function Cantidad({ m }: { m: Movimiento }) {
  const signo = m.tipo_movimiento === 'ENTRADA' ? '+' : m.tipo_movimiento === 'SALIDA' ? '−' : '='
  const color = m.tipo_movimiento === 'ENTRADA' ? 'text-success' : m.tipo_movimiento === 'SALIDA' ? 'text-danger' : 'text-info'
  return (
    <span className={cn('font-mono font-semibold', color)} title={m.tipo_movimiento === 'AJUSTE' ? 'Nuevo stock contado' : undefined}>
      {signo}
      {formatNumero(m.cantidad)}
    </span>
  )
}

export interface MovimientosTableProps {
  data: Movimiento[] | undefined
  caption?: string
  loading?: boolean
  error?: unknown
  onRetry?: () => void
  empty?: ReactNode
  /** Oculta el nombre del producto (p. ej. en el detalle de producto). */
  ocultarProducto?: boolean
}

export function MovimientosTable({ data, caption = 'Historial de movimientos', loading, error, onRetry, empty, ocultarProducto = false }: MovimientosTableProps) {
  const ctx = useContextoMovimientos()

  const columnas: Column<Movimiento>[] = [
    {
      id: 'fecha',
      header: 'Fecha / autor',
      cell: (m) => {
        // El backend envía `operario_nombre`; la lista de operarios (solo EMPRESA) es el respaldo.
        const o = ctx.contexto(m).operario
        const autor = m.operario_nombre?.trim() || (o ? nombreOperario(o) : m.id_operario ? '—' : 'Sistema')
        return (
          <div className="min-w-0">
            <p className="font-mono text-xs whitespace-nowrap text-fg-muted">{formatFechaHora(m.fecha_hora)}</p>
            <p className="font-medium whitespace-nowrap text-fg">{autor}</p>
            {m.observacion?.trim() && (
              <p className="max-w-44 truncate text-xs text-fg-muted" title={m.observacion}>
                {m.observacion}
              </p>
            )}
          </div>
        )
      },
    },
    {
      id: 'tipo',
      header: 'Tipo / motivo',
      mobile: 'badge',
      cell: (m) => (
        <span className="flex flex-col items-start gap-1">
          <StatusBadge estado={m.tipo_movimiento} />
          <StatusBadge estado={m.motivo_movimiento} />
        </span>
      ),
    },
    {
      id: 'producto',
      header: ocultarProducto ? 'Ubicación' : 'Producto / ubicación',
      mobile: 'title',
      cell: (m) => {
        const c = ctx.contexto(m)
        return (
          <div className="min-w-0">
            {!ocultarProducto &&
              (c.producto ? (
                <Link to={paths.producto(c.producto.id_producto)} className="font-semibold text-fg hover:underline">
                  {c.producto.nombre}
                </Link>
              ) : (
                <span className="font-semibold text-fg-subtle">{ctx.isLoading ? '…' : 'Producto no disponible'}</span>
              ))}
            <p className={cn('truncate', ocultarProducto ? 'font-medium text-fg' : 'text-xs text-fg-muted')}>
              {c.ubicacion?.etiqueta ?? (ctx.isLoading ? '…' : 'Ubicación no disponible')}
            </p>
          </div>
        )
      },
    },
    { id: 'cantidad', header: 'Cantidad', align: 'right', cell: (m) => <Cantidad m={m} /> },
    {
      id: 'stock',
      header: 'Stock ant. → nuevo',
      align: 'right',
      cell: (m) => (
        <span className="font-mono whitespace-nowrap">
          <span className="text-fg-muted">{formatNumero(m.stock_anterior)}</span>
          <span className="px-1 text-fg-subtle" aria-label="a">
            →
          </span>
          <span className="font-semibold text-fg">{formatNumero(m.stock_nuevo)}</span>
        </span>
      ),
    },
  ]

  return (
    <DataTable
      caption={caption}
      data={data}
      loading={loading ?? false}
      error={error}
      {...(onRetry ? { onRetry } : {})}
      empty={empty}
      rowKey={(m) => m.id_movimiento}
      columns={columnas}
    />
  )
}
