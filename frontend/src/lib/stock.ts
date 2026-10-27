import type { EstadoStock, Inventario } from '@/api/types'

/** Estado de stock calculado en cliente a partir de Inventario (fuente real de stock). */
export function estadoStock(inv: Pick<Inventario, 'stock_actual' | 'stock_minimo' | 'stock_maximo'>): EstadoStock {
  if (inv.stock_actual <= 0) return 'SIN_STOCK'
  if (inv.stock_actual < inv.stock_minimo) return 'STOCK_BAJO'
  if (inv.stock_maximo > 0 && inv.stock_actual > inv.stock_maximo) return 'SOBRE_STOCK'
  return 'STOCK_OK'
}

export interface ResumenStock {
  sinStock: number
  stockBajo: number
  sobreStock: number
  ok: number
  total: number
}

export function resumenStock(invs: Inventario[]): ResumenStock {
  const r: ResumenStock = { sinStock: 0, stockBajo: 0, sobreStock: 0, ok: 0, total: invs.length }
  for (const inv of invs) {
    const e = estadoStock(inv)
    if (e === 'SIN_STOCK') r.sinStock++
    else if (e === 'STOCK_BAJO') r.stockBajo++
    else if (e === 'SOBRE_STOCK') r.sobreStock++
    else r.ok++
  }
  return r
}
