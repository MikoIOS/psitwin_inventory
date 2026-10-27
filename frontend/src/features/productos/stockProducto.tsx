/** Utilidades del módulo productos: stock real agregado por producto y badge de refrigeración. */
import { useInventarios } from '@/api/inventarios'
import type { EstadoStock, Producto } from '@/api/types'
import { useUbicaciones } from '@/api/ubicaciones'
import { Badge, Icon } from '@/components/ui'
import { formatNumero } from '@/lib/format'
import { estadoStock } from '@/lib/stock'

const GRAVEDAD: Record<EstadoStock, number> = { SIN_STOCK: 3, STOCK_BAJO: 2, SOBRE_STOCK: 1, STOCK_OK: 0 }

export interface StockProducto {
  total: number
  ubicaciones: number
  /** Estado más grave entre sus ubicaciones. */
  peor: EstadoStock
}

/** Stock real agregado por producto (Σ Inventario.stock_actual en racks de la empresa). */
export function useStockPorProducto() {
  const inventarios = useInventarios()
  const ub = useUbicaciones()
  const mapa = new Map<string, StockProducto>()
  if (inventarios.data && !ub.isLoading) {
    for (const inv of inventarios.data) {
      if (!ub.perteneceAEmpresa(inv.id_rack)) continue
      const e = estadoStock(inv)
      const prev = mapa.get(inv.id_producto)
      mapa.set(inv.id_producto, {
        total: (prev?.total ?? 0) + inv.stock_actual,
        ubicaciones: (prev?.ubicaciones ?? 0) + 1,
        peor: prev && GRAVEDAD[prev.peor] >= GRAVEDAD[e] ? prev.peor : e,
      })
    }
  }
  return { mapa, isLoading: inventarios.isLoading || ub.isLoading }
}

export function RefrigeracionBadge({ producto }: { producto: Producto }) {
  if (!producto.requiere_refrigeracion) return null
  const rango =
    producto.temperatura_min_almacenamiento !== null && producto.temperatura_max_almacenamiento !== null
      ? ` ${formatNumero(producto.temperatura_min_almacenamiento)}–${formatNumero(producto.temperatura_max_almacenamiento)} °C`
      : ''
  return (
    <Badge tone="info" dot={false} title="Requiere refrigeración">
      <Icon name="snowflake" className="size-3" />
      Frío{rango}
    </Badge>
  )
}
