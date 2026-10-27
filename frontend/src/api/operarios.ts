/**
 * Operarios: cuentas (rol OPERARIO) que crea y gestiona la EMPRESA. Solo EMPRESA puede leer estos endpoints.
 *   POST /operarios/{id}/reset-password `{ password_temporal, correo? }` → nueva contraseña temporal / «dar acceso».
 *   POST /operarios · GET /operarios · GET /operarios/empresa/{id_empresa}
 *   GET /operarios/estado/{estado} · GET /operarios/turno/{turno}
 *   GET /operarios/{id} · PUT /operarios/{id} · DELETE /operarios/{id}
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { requireIdEmpresa, useIdEmpresa } from '@/auth/useEmpresa'
import { api, seg } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import { operarioActivo } from './enums'
import type { EstadoOperario, Operario, OperarioCreate, OperarioUpdate, ResetPasswordBody, TurnoOperario } from './types'

export const operariosApi = {
  create: async (body: OperarioCreate): Promise<Operario> => norm.operario.one(await api.post('/operarios', body)),
  list: async (): Promise<Operario[]> => norm.operario.list(await api.get('/operarios')),
  listByEmpresa: async (idEmpresa: string): Promise<Operario[]> =>
    norm.operario.list(await api.get(`/operarios/empresa/${seg(idEmpresa)}`)),
  listByEstado: async (estado: EstadoOperario): Promise<Operario[]> =>
    norm.operario.list(await api.get(`/operarios/estado/${seg(estado)}`)),
  listByTurno: async (turno: TurnoOperario): Promise<Operario[]> =>
    norm.operario.list(await api.get(`/operarios/turno/${seg(turno)}`)),
  get: async (id: string): Promise<Operario> => norm.operario.one(await api.get(`/operarios/${seg(id)}`)),
  update: async (id: string, body: OperarioUpdate): Promise<Operario> =>
    norm.operario.one(await api.put(`/operarios/${seg(id)}`, body)),
  remove: (id: string) => api.delete<unknown>(`/operarios/${seg(id)}`),
  resetPassword: async (id: string, body: ResetPasswordBody): Promise<Operario> =>
    norm.operario.one(await api.post(`/operarios/${seg(id)}/reset-password`, body)),
}

export interface FiltroOperarios {
  soloActivos?: boolean
  idAlmacen?: string | undefined
  /** Con `idAlmacen`: excluir también a los operarios antiguos SIN almacén (recepción: el backend lo exige). */
  estrictoAlmacen?: boolean
}

/** true si el operario puede trabajar en el almacén. Sin `id_almacen` se considera de todos, salvo con `estricto`. */
export function operarioDeAlmacen(o: Pick<Operario, 'id_almacen'>, idAlmacen: string | undefined, estricto = false): boolean {
  if (!idAlmacen) return true
  if (!o.id_almacen) return !estricto
  return o.id_almacen === idAlmacen
}

/**
 * Operarios de la empresa autenticada (`/operarios/empresa/{id}`), con filtros en cliente opcionales:
 * `{ soloActivos, idAlmacen, estrictoAlmacen }`.
 */
export function useOperarios(filtro: FiltroOperarios = {}) {
  const { rol } = useSession()
  const idEmpresa = useIdEmpresa()
  const { soloActivos = false, idAlmacen, estrictoAlmacen = false } = filtro
  return useQuery({
    queryKey: queryKeys.operarios.byEmpresa(idEmpresa ?? ''),
    queryFn: () => operariosApi.listByEmpresa(requireIdEmpresa(idEmpresa)),
    enabled: !!idEmpresa && rol === 'EMPRESA',
    select: (list) => list.filter((o) => (!soloActivos || operarioActivo(o.estado)) && operarioDeAlmacen(o, idAlmacen, estrictoAlmacen)),
  })
}

export function useOperario(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.operarios.detail(id ?? ''),
    queryFn: () => operariosApi.get(id!),
    enabled: !!id,
  })
}

/** EMPRESA: restablece la contraseña (temporal) de un operario, o le da acceso si no tenía cuenta. */
export function useResetPasswordOperario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ResetPasswordBody }) => operariosApi.resetPassword(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.operarios.all }),
  })
}

/** Crea la cuenta de un operario (la empresa sale del token). */
export function useCreateOperario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: operariosApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.operarios.all }),
  })
}

export function useUpdateOperario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: OperarioUpdate }) => operariosApi.update(id, body),
    onSuccess: (op) => {
      qc.setQueryData(queryKeys.operarios.detail(op.id_operario), op)
      return qc.invalidateQueries({ queryKey: queryKeys.operarios.all })
    },
  })
}

export function useDeleteOperario() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => operariosApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.operarios.all }),
  })
}
