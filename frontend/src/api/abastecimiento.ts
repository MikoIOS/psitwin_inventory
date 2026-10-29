import { useQuery } from '@tanstack/react-query'
import { api, seg } from './client'
import { requireList, norm } from './normalize'
import type { Producto } from './types'

export interface Oferta {
  id_oferta: string; id_producto: string; id_proveedor: string
  producto: string; proveedor: string; familia: string; categoria: string
  unidad: 'kg' | 'unidad'; precio_centimos: number; precio: number
  cantidad_total: number; cantidad_reservada: number; cantidad_despachada: number; cantidad_disponible: number
  activa: boolean; observaciones?: string | null
}
export interface Seguimiento {
  id_orden: string; id_producto: string; id_proveedor: string; estado: string; fecha: string
  unidad: string; proveedor: string; telefono: string | null; motivos: string[]
  solicitada: number; despachada: number; recibida: number; aceptada: number; rechazada: number
  faltante: number; diferencia_despacho: number
  resolucion?: { decision: string; motivo: string } | null
}
export interface PedidoHistorico extends Seguimiento { cantidad: number; dia: string; id_origen: string; es_imputado: boolean }
export interface Nivel { id_nivel: string; id_rack: string; codigo: string; numero: number }
export const abastecimientoApi = {
  catalogo: async (): Promise<Producto[]> => norm.producto.list(requireList(await api.get('/abastecimiento/catalogo'))),
  ofertas: async (disponibles = false, proveedor = '') => requireList<Oferta>(await api.get('/abastecimiento/ofertas', { query: { solo_disponibles: disponibles, id_proveedor: proveedor } })),
  guardarOferta: (body: { id_producto: string; unidad: string; precio: string; cantidad_total: number; activa: boolean; observaciones: string }) => api.put<Oferta>('/abastecimiento/ofertas', body),
  seguimiento: async () => requireList<Seguimiento>(await api.get('/abastecimiento/seguimiento')),
  decidir: (id: string, decision: 'MANTENER' | 'CERRAR', motivo: string) => api.patch(`/abastecimiento/solicitudes/${seg(id)}/pendiente`, { decision, motivo }),
  rechazar: (id: string, motivo: string) => api.patch(`/abastecimiento/solicitudes/${seg(id)}/rechazar`, { decision: 'CERRAR', motivo }),
  historial: (query: Record<string, string | boolean>) => api.get<{ registros: PedidoHistorico[]; totales_por_unidad: Record<string, number> }>('/abastecimiento/historial-pedidos', { query }),
  niveles: (rack: string) => api.get<Nivel[]>(`/abastecimiento/racks/${seg(rack)}/niveles`),
  crearNivel: (rack: string, body: { codigo: string; numero: number }) => api.post<Nivel>(`/abastecimiento/racks/${seg(rack)}/niveles`, body),
  eliminarNivel: (id: string) => api.delete(`/abastecimiento/niveles/${seg(id)}`),
}
export function useOfertas(disponibles = false, proveedor = '') {
  return useQuery({ queryKey: ['abastecimiento', 'ofertas', disponibles, proveedor], queryFn: () => abastecimientoApi.ofertas(disponibles, proveedor) })
}
