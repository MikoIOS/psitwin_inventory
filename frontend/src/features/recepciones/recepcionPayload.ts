import type { DetalleRecepcionCreate, EstadoRecepcion } from '@/api/types'

interface LineaRecepcion {
  id_detalle_reposicion: string
  id_rack: string
  id_nivel: string
  cantidad_recibida: string
  cantidad_rechazada: string
  fecha_vencimiento: string
  temperatura_recepcion: string
  estado_recepcion: EstadoRecepcion
  comentario_recepcion: string
}

const numero = (value: string) => Number(value.trim().replace(',', '.'))

export function aDetalleCreate(linea: LineaRecepcion, idInventario: string): DetalleRecepcionCreate {
  const recibida = numero(linea.cantidad_recibida)
  const rechazada = linea.estado_recepcion === 'RECHAZADO' ? recibida
    : linea.estado_recepcion === 'CONFORME' ? numero(linea.cantidad_rechazada) : 0
  const comentario = linea.comentario_recepcion.trim() || null
  const fecha = linea.fecha_vencimiento ? new Date(`${linea.fecha_vencimiento}T00:00:00`) : null
  return {
    id_detalle_reposicion: linea.id_detalle_reposicion,
    id_inventario: idInventario,
    id_rack: linea.id_rack,
    id_nivel: linea.id_nivel || null,
    // El operario recibe mercadería; los umbrales los define la empresa.
    stock_minimo: 0,
    stock_maximo: 0,
    cantidad_recibida: recibida,
    cantidad_rechazada: rechazada,
    motivo_rechazo: rechazada > 0 ? comentario : null,
    fecha_vencimiento: fecha && !Number.isNaN(fecha.getTime()) ? fecha.toISOString() : null,
    temperatura_recepcion: linea.temperatura_recepcion.trim() ? numero(linea.temperatura_recepcion) : null,
    estado_recepcion: linea.estado_recepcion,
    comentario_recepcion: comentario,
  }
}
