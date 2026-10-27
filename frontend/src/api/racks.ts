/**
 * Racks. EMPRESA: crear / borrar. OPERARIO: editar estado y temperatura. PROVEEDOR: sin acceso.
 *   POST /racks · GET /racks · GET /racks/{id} · GET /racks/zona/{id_zona} · PUT /racks/{id} · DELETE /racks/{id}
 *   GET /racks/disponibles?id_almacen=&id_producto=&cantidad= → racks DISPONIBLES donde cabe el producto (kg y temperatura)
 *
 * `capacidad` = carga máxima en kg; el backend envía `carga_kg` y `libre_kg`.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { api, seg } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type { Rack, RackCreate, RackDisponible, RackUpdate } from './types'

export const racksApi = {
  create: async (body: RackCreate): Promise<Rack> => norm.rack.one(await api.post('/racks', body)),
  list: async (): Promise<Rack[]> => norm.rack.list(await api.get('/racks')),
  get: async (id: string): Promise<Rack> => norm.rack.one(await api.get(`/racks/${seg(id)}`)),
  listByZona: async (idZona: string): Promise<Rack[]> => norm.rack.list(await api.get(`/racks/zona/${seg(idZona)}`)),
  update: async (id: string, body: RackUpdate): Promise<Rack> => norm.rack.one(await api.put(`/racks/${seg(id)}`, body)),
  remove: (id: string) => api.delete<unknown>(`/racks/${seg(id)}`),
  disponibles: async (idAlmacen: string, idProducto: string, cantidad: number): Promise<RackDisponible[]> =>
    norm.rack.list(await api.get('/racks/disponibles', { query: { id_almacen: idAlmacen, id_producto: idProducto, cantidad } })) as RackDisponible[],
}

/** Todos los racks (sin filtrar por empresa). Preferir `useRacksPorZona` o `useUbicaciones`. */
export function useRacks() {
  const { rol } = useSession()
  return useQuery({ queryKey: queryKeys.racks.list(), queryFn: racksApi.list, enabled: rol !== 'PROVEEDOR' })
}

/** Racks DISPONIBLES del almacén donde caben `cantidad` unidades del producto (por kg y temperatura). */
export function useRacksDisponibles(idAlmacen: string | undefined, idProducto: string | undefined, cantidad: number) {
  const cant = Number.isFinite(cantidad) && cantidad > 0 ? Math.floor(cantidad) : 0
  return useQuery({
    queryKey: queryKeys.racks.disponibles(idAlmacen ?? '', idProducto ?? '', cant),
    queryFn: () => racksApi.disponibles(idAlmacen!, idProducto!, cant),
    enabled: !!idAlmacen && !!idProducto,
    placeholderData: (prev) => prev,
  })
}

export function useRacksPorZona(idZona: string | undefined) {
  return useQuery({
    queryKey: queryKeys.racks.byZona(idZona ?? ''),
    queryFn: () => racksApi.listByZona(idZona!),
    enabled: !!idZona,
  })
}

export function useRack(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.racks.detail(id ?? ''),
    queryFn: () => racksApi.get(id!),
    enabled: !!id,
  })
}

export function useCreateRack() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: racksApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.racks.all }),
  })
}

export function useUpdateRack() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: RackUpdate }) => racksApi.update(id, body),
    onSuccess: (rack) => {
      qc.setQueryData(queryKeys.racks.detail(rack.id_rack), rack)
      return qc.invalidateQueries({ queryKey: queryKeys.racks.all })
    },
  })
}

export function useDeleteRack() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => racksApi.remove(id),
    onSuccess: (_d, id) =>
      Promise.all([
        qc.invalidateQueries({ queryKey: queryKeys.racks.all }),
        // Sin el inventario del rack borrado: su panel aún montado lo volvería a pedir (404).
        qc.invalidateQueries({ queryKey: queryKeys.inventarios.all, predicate: (q) => q.queryKey[1] !== 'rack' || q.queryKey[2] !== id }),
        qc.invalidateQueries({ queryKey: queryKeys.productos.all }),
      ]),
  })
}
