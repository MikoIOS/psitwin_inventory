/**
 * Proveedores (EMPRESA: CRUD y cuentas; OPERARIO: leer; PROVEEDOR: solo el suyo, que ya viene en la sesión).
 *   POST /proveedores/{id}/reset-password `{ password_temporal, correo? }`
 *   POST /proveedores · GET /proveedores · GET /proveedores/empresa/{id_empresa}
 *   GET /proveedores/estado/{estado} · GET /proveedores/{id} · PUT /proveedores/{id} · DELETE /proveedores/{id}
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { requireIdEmpresa, useIdEmpresa } from '@/auth/useEmpresa'
import { api, seg } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type { EstadoProveedor, Proveedor, ProveedorCreate, ProveedorUpdate, ResetPasswordBody } from './types'

export const proveedoresApi = {
  create: async (body: ProveedorCreate): Promise<Proveedor> => norm.proveedor.one(await api.post('/proveedores', body)),
  list: async (): Promise<Proveedor[]> => norm.proveedor.list(await api.get('/proveedores')),
  listByEmpresa: async (idEmpresa: string): Promise<Proveedor[]> =>
    norm.proveedor.list(await api.get(`/proveedores/empresa/${seg(idEmpresa)}`)),
  listByEstado: async (estado: EstadoProveedor): Promise<Proveedor[]> =>
    norm.proveedor.list(await api.get(`/proveedores/estado/${seg(estado)}`)),
  get: async (id: string): Promise<Proveedor> => norm.proveedor.one(await api.get(`/proveedores/${seg(id)}`)),
  update: async (id: string, body: ProveedorUpdate): Promise<Proveedor> =>
    norm.proveedor.one(await api.put(`/proveedores/${seg(id)}`, body)),
  remove: (id: string) => api.delete<unknown>(`/proveedores/${seg(id)}`),
  resetPassword: async (id: string, body: ResetPasswordBody): Promise<Proveedor> =>
    norm.proveedor.one(await api.post(`/proveedores/${seg(id)}/reset-password`, body)),
  enviarVerificacion: (id: string) =>
    api.post<{ status: string; email?: string | null; remaining_seconds?: number | null; reason?: string | null }>(
      `/proveedores/${seg(id)}/correo/enviar-verificacion`,
    ),
  verificarCorreo: (id: string, codigo: string) =>
    api.post<{ verified: boolean; status: string; remaining_attempts?: number | null }>(`/proveedores/${seg(id)}/correo/verificar`, { codigo }),
}

/** Proveedores de la empresa autenticada. `{ soloActivos: true }` filtra en cliente. */
export function useProveedores(filtro: { soloActivos?: boolean } = {}) {
  const idEmpresa = useIdEmpresa()
  const { soloActivos = false } = filtro
  return useQuery({
    queryKey: queryKeys.proveedores.byEmpresa(idEmpresa ?? ''),
    queryFn: () => proveedoresApi.listByEmpresa(requireIdEmpresa(idEmpresa)),
    enabled: !!idEmpresa,
    select: (list) => (soloActivos ? list.filter((p) => p.estado === 'ACTIVO') : list),
  })
}

export function useProveedor(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.proveedores.detail(id ?? ''),
    queryFn: () => proveedoresApi.get(id!),
    enabled: !!id,
  })
}

/** EMPRESA: restablece la contraseña (temporal) de un proveedor, o le da acceso si no tenía cuenta. */
export function useResetPasswordProveedor() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ResetPasswordBody }) => proveedoresApi.resetPassword(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.proveedores.all }),
  })
}

/** Crea un proveedor (la empresa sale del token). Con `password_temporal` crea también su cuenta. */
export function useCreateProveedor() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: proveedoresApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.proveedores.all }),
  })
}

export function useUpdateProveedor() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ProveedorUpdate }) => proveedoresApi.update(id, body),
    onSuccess: (prov) => {
      qc.setQueryData(queryKeys.proveedores.detail(prov.id_proveedor), prov)
      return qc.invalidateQueries({ queryKey: queryKeys.proveedores.all })
    },
  })
}

export function useDeleteProveedor() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => proveedoresApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.proveedores.all }),
  })
}
