/**
 * Zonas.
 *   POST /zonas · GET /zonas · GET /zonas/{id} · GET /zonas/almacen/{id_almacen}
 *   PUT /zonas/{id} · DELETE /zonas/{id}
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { api, seg } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type { Zona, ZonaCreate, ZonaUpdate } from './types'

export const zonasApi = {
  create: async (body: ZonaCreate): Promise<Zona> => norm.zona.one(await api.post('/zonas', body)),
  list: async (): Promise<Zona[]> => norm.zona.list(await api.get('/zonas')),
  get: async (id: string): Promise<Zona> => norm.zona.one(await api.get(`/zonas/${seg(id)}`)),
  listByAlmacen: async (idAlmacen: string): Promise<Zona[]> =>
    norm.zona.list(await api.get(`/zonas/almacen/${seg(idAlmacen)}`)),
  update: async (id: string, body: ZonaUpdate): Promise<Zona> => norm.zona.one(await api.put(`/zonas/${seg(id)}`, body)),
  remove: (id: string) => api.delete<unknown>(`/zonas/${seg(id)}`),
}

/** Todas las zonas (sin filtrar por empresa). Preferir `useZonasPorAlmacen`. */
export function useZonas() {
  const { rol } = useSession()
  return useQuery({ queryKey: queryKeys.zonas.list(), queryFn: zonasApi.list, enabled: rol !== 'PROVEEDOR' })
}

export function useZonasPorAlmacen(idAlmacen: string | undefined) {
  return useQuery({
    queryKey: queryKeys.zonas.byAlmacen(idAlmacen ?? ''),
    queryFn: () => zonasApi.listByAlmacen(idAlmacen!),
    enabled: !!idAlmacen,
  })
}

export function useZona(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.zonas.detail(id ?? ''),
    queryFn: () => zonasApi.get(id!),
    enabled: !!id,
  })
}

export function useCreateZona() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: zonasApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.zonas.all }),
  })
}

export function useUpdateZona() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ZonaUpdate }) => zonasApi.update(id, body),
    onSuccess: (zona) => {
      qc.setQueryData(queryKeys.zonas.detail(zona.id_zona), zona)
      return qc.invalidateQueries({ queryKey: queryKeys.zonas.all })
    },
  })
}

export function useDeleteZona() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => zonasApi.remove(id),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: queryKeys.zonas.all }),
        qc.invalidateQueries({ queryKey: queryKeys.racks.all }),
        qc.invalidateQueries({ queryKey: queryKeys.inventarios.all }),
        qc.invalidateQueries({ queryKey: queryKeys.productos.all }),
      ]),
  })
}
