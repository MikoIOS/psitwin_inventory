import { describe, expect, it } from 'vitest'
import { aDetalleCreate } from './recepcionPayload'

const linea = {
  id_detalle_reposicion: 'pedido', id_rack: 'rack', id_nivel: 'nivel',
  cantidad_recibida: '12,5', cantidad_rechazada: '0,5', fecha_vencimiento: '',
  temperatura_recepcion: '3,5', estado_recepcion: 'CONFORME' as const,
  comentario_recepcion: ' Una caja dañada ',
}

describe('Recepción compatible con inventario general y permisos de operario', () => {
  it('conserva almacén, rack y nivel sin crear umbrales no autorizados', () => {
    expect(aDetalleCreate(linea, 'cabecera')).toMatchObject({
      id_inventario: 'cabecera', id_rack: 'rack', id_nivel: 'nivel',
      stock_minimo: 0, stock_maximo: 0, cantidad_recibida: 12.5,
      cantidad_rechazada: 0.5, temperatura_recepcion: 3.5,
      motivo_rechazo: 'Una caja dañada',
    })
  })
  it('rechaza toda la cantidad cuando la mercadería es rechazada', () => {
    expect(aDetalleCreate({ ...linea, estado_recepcion: 'RECHAZADO' }, 'cabecera').cantidad_rechazada).toBe(12.5)
  })
  it('deja la cantidad sin resolver para una evaluación', () => {
    expect(aDetalleCreate({ ...linea, estado_recepcion: 'EN_EVALUACION' }, 'cabecera').cantidad_rechazada).toBe(0)
  })
  it('admite ubicaciones sin nivel y datos opcionales vacíos', () => {
    expect(aDetalleCreate({ ...linea, id_nivel: '', temperatura_recepcion: '', cantidad_rechazada: '0', comentario_recepcion: '' }, 'cabecera'))
      .toMatchObject({ id_nivel: null, temperatura_recepcion: null, fecha_vencimiento: null, motivo_rechazo: null })
  })
})
