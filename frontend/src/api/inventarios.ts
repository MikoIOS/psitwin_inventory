/**
 * Inventarios (stock real por producto y rack).
 *   Listados de existencias: GET /detalles-inventario y sus filtros
 *   /stock-bajo, /sin-stock, /sobre-stock, /producto/{id_producto}.
 *   GET /inventarios devuelve cabeceras de almacén, no filas de stock.
 *   GET /detalles-inventario/rack/{id_rack} (stock por ubicación, esquema v2)
 *   GET /inventarios/{id} · PUT /inventarios/{id} · DELETE /inventarios/{id}
 *
 *   GET /inventarios/{id}/historial → quién lo creó / cambió sus límites
 *
 * EMPRESA: solo lectura. OPERARIO (su almacén): crear, editar límites (mín/máx) y borrar sin stock.
 * El stock solo cambia por recepciones y movimientos. PROVEEDOR: sin acceso (los hooks quedan deshabilitados).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { api, seg } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type { Inventario, InventarioCreate, InventarioHistorial, InventarioUpdate } from './types'

export const inventariosApi = {
  create: async (body: InventarioCreate): Promise<Inventario> => norm.inventario.one(await api.post('/inventarios', body)),
  list: async (): Promise<Inventario[]> => norm.inventario.list(await api.get('/detalles-inventario')),
  listStockBajo: async (): Promise<Inventario[]> => norm.inventario.list(await api.get('/detalles-inventario/stock-bajo')),
  listSinStock: async (): Promise<Inventario[]> => norm.inventario.list(await api.get('/detalles-inventario/sin-stock')),
  listSobreStock: async (): Promise<Inventario[]> => norm.inventario.list(await api.get('/detalles-inventario/sobre-stock')),
  listByProducto: async (idProducto: string): Promise<Inventario[]> =>
    norm.inventario.list(await api.get(`/detalles-inventario/producto/${seg(idProducto)}`)),
  listByRack: async (idRack: string): Promise<Inventario[]> =>
    norm.inventario.list(await api.get(`/detalles-inventario/rack/${seg(idRack)}`)),
  get: async (id: string): Promise<Inventario> => norm.inventario.one(await api.get(`/inventarios/${seg(id)}`)),
  update: async (id: string, body: InventarioUpdate): Promise<Inventario> =>
    norm.inventario.one(await api.put(`/inventarios/${seg(id)}`, body)),
  remove: (id: string) => api.delete<unknown>(`/inventarios/${seg(id)}`),
  historial: (id: string) => api.get<InventarioHistorial[]>(`/inventarios/${seg(id)}/historial`),
}

const usePuedeVer = () => useSession().rol !== 'PROVEEDOR'

export function useInventarios() {
  return useQuery({ queryKey: queryKeys.inventarios.list(), queryFn: inventariosApi.list, enabled: usePuedeVer() })
}

export function useInventarioHistorial(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.inventarios.historial(id ?? ''),
    queryFn: () => inventariosApi.historial(id!),
    enabled: !!id,
  })
}

export function useInventariosStockBajo() {
  return useQuery({ queryKey: queryKeys.inventarios.stockBajo(), queryFn: inventariosApi.listStockBajo, enabled: usePuedeVer() })
}

export function useInventariosSinStock() {
  return useQuery({ queryKey: queryKeys.inventarios.sinStock(), queryFn: inventariosApi.listSinStock, enabled: usePuedeVer() })
}

export function useInventariosSobreStock() {
  return useQuery({ queryKey: queryKeys.inventarios.sobreStock(), queryFn: inventariosApi.listSobreStock, enabled: usePuedeVer() })
}

export function useInventariosPorProducto(idProducto: string | undefined) {
  return useQuery({
    queryKey: queryKeys.inventarios.byProducto(idProducto ?? ''),
    queryFn: () => inventariosApi.listByProducto(idProducto!),
    enabled: !!idProducto,
  })
}

export function useInventariosPorRack(idRack: string | undefined) {
  return useQuery({
    queryKey: queryKeys.inventarios.byRack(idRack ?? ''),
    queryFn: () => inventariosApi.listByRack(idRack!),
    enabled: !!idRack,
  })
}

export function useInventario(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.inventarios.detail(id ?? ''),
    queryFn: () => inventariosApi.get(id!),
    enabled: !!id,
  })
}

export function useCreateInventario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: inventariosApi.create,
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: queryKeys.inventarios.all }),
        qc.invalidateQueries({ queryKey: queryKeys.racks.all }),
      ]),
  })
}

export function useUpdateInventario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: InventarioUpdate }) => inventariosApi.update(id, body),
    onSuccess: (inv) => {
      qc.setQueryData(queryKeys.inventarios.detail(inv.id_inventario), inv)
      return Promise.all([
        qc.invalidateQueries({ queryKey: queryKeys.inventarios.all }),
      ])
    },
  })
}

export function useDeleteInventario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => inventariosApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.inventarios.all }),
  })
}
