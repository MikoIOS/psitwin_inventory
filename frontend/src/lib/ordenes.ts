import type { DetalleRecepcion, DetalleReposicion } from '@/api/types'

export interface LineaPendiente {
  detalle: DetalleReposicion
  solicitada: number
  aceptada: number
  rechazada: number
  /** max(0, solicitada − Σ aceptada) */
  pendiente: number
  completa: boolean
}

/**
 * Cantidad pendiente por línea de orden = cantidad_solicitada − Σ cantidad_aceptada
 * de los detalles de TODAS las recepciones de la orden (decisión confirmada, se calcula en frontend).
 * Datos: `useDetallesReposicion(idOrden)` + `useDetallesRecepcionPorOrden(idOrden)`.
 */
export function calcularPendientes(detalles: DetalleReposicion[], recibidos: DetalleRecepcion[]): LineaPendiente[] {
  const aceptadas = new Map<string, number>()
  const rechazadas = new Map<string, number>()
  for (const r of recibidos) {
    aceptadas.set(r.id_detalle_reposicion, (aceptadas.get(r.id_detalle_reposicion) ?? 0) + (r.cantidad_aceptada ?? 0))
    rechazadas.set(r.id_detalle_reposicion, (rechazadas.get(r.id_detalle_reposicion) ?? 0) + (r.cantidad_rechazada ?? 0))
  }
  return detalles.map((detalle) => {
    const aceptada = aceptadas.get(detalle.id_detalle_reposicion) ?? 0
    const pendiente = Math.max(0, detalle.cantidad_solicitada - aceptada)
    return {
      detalle,
      solicitada: detalle.cantidad_solicitada,
      aceptada,
      rechazada: rechazadas.get(detalle.id_detalle_reposicion) ?? 0,
      pendiente,
      completa: pendiente === 0,
    }
  })
}
