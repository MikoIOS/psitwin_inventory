/**
 * Almacenes.
 *   POST /almacenes · GET /almacenes · GET /almacenes/{id} · GET /almacenes/empresa/{id_empresa}
 *   PUT /almacenes/{id} · DELETE /almacenes/{id}
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { requireIdEmpresa, useIdEmpresa } from '@/auth/useEmpresa'
import { api, seg } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type { Almacen, AlmacenCreate, AlmacenUpdate } from './types'

export const almacenesApi = {
  create: async (body: AlmacenCreate): Promise<Almacen> => norm.almacen.one(await api.post('/almacenes', body)),
  list: async (): Promise<Almacen[]> => norm.almacen.list(await api.get('/almacenes')),
  get: async (id: string): Promise<Almacen> => norm.almacen.one(await api.get(`/almacenes/${seg(id)}`)),
  listByEmpresa: async (idEmpresa: string): Promise<Almacen[]> =>
    norm.almacen.list(await api.get(`/almacenes/empresa/${seg(idEmpresa)}`)),
  update: async (id: string, body: AlmacenUpdate): Promise<Almacen> =>
    norm.almacen.one(await api.put(`/almacenes/${seg(id)}`, body)),
  remove: (id: string) => api.delete<unknown>(`/almacenes/${seg(id)}`),
}

/* ---------------------------- Queries ---------------------------- */

/** Almacenes de la empresa autenticada (usa `/almacenes/empresa/{id}`). */
export function useAlmacenes() {
  const idEmpresa = useIdEmpresa()
  return useQuery({
    queryKey: queryKeys.almacenes.byEmpresa(idEmpresa ?? ''),
    queryFn: () => almacenesApi.listByEmpresa(requireIdEmpresa(idEmpresa)),
    enabled: !!idEmpresa,
  })
}

export function useAlmacen(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.almacenes.detail(id ?? ''),
    queryFn: () => almacenesApi.get(id!),
    enabled: !!id,
  })
}

/* --------------------------- Mutations --------------------------- */

/** Crea un almacén de la empresa autenticada (inyecta `id_empresa`). */
export function useCreateAlmacen() {
  const qc = useQueryClient()
  const idEmpresa = useIdEmpresa()
  return useMutation({
    mutationFn: (body: AlmacenUpdate) => almacenesApi.create({ ...body, id_empresa: requireIdEmpresa(idEmpresa) }),
    onSuccess: (nuevo) => {
      // Escribe en caché antes de invalidar: el guard de onboarding lee esta lista
      // y no debe ver el valor obsoleto (0 almacenes) mientras se refresca.
      qc.setQueryData<Almacen[]>(queryKeys.almacenes.byEmpresa(nuevo.id_empresa ?? idEmpresa ?? ''), (old) => [
        ...(old ?? []).filter((a) => a.id_almacen !== nuevo.id_almacen),
        nuevo,
      ])
      return qc.invalidateQueries({ queryKey: queryKeys.almacenes.all })
    },
  })
}

export function useUpdateAlmacen() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: AlmacenUpdate }) => almacenesApi.update(id, body),
    onSuccess: (almacen) => {
      qc.setQueryData(queryKeys.almacenes.detail(almacen.id_almacen), almacen)
      return qc.invalidateQueries({ queryKey: queryKeys.almacenes.all })
    },
  })
}

export function useDeleteAlmacen() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => almacenesApi.remove(id),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: queryKeys.almacenes.all }),
        qc.invalidateQueries({ queryKey: queryKeys.zonas.all }),
        qc.invalidateQueries({ queryKey: queryKeys.racks.all }),
        qc.invalidateQueries({ queryKey: queryKeys.operarios.all }),
        qc.invalidateQueries({ queryKey: queryKeys.inventarios.all }),
        qc.invalidateQueries({ queryKey: queryKeys.productos.all }),
        qc.invalidateQueries({ queryKey: queryKeys.ordenes.all }),
      ]),
  })
}
