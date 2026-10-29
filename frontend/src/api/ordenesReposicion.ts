/**
 * Solicitudes / órdenes de reposición y sus líneas (docs/ROLES.md §5).
 * Estados: PENDIENTE → (OBSERVADA ↔ PENDIENTE) → ENVIADA → PARCIAL → RECIBIDA; CANCELADA.
 *
 *   OPERARIO  POST /ordenes-reposicion `{ id_proveedor, lineas?, … }` · PUT/DELETE /{id} · líneas (POST /{id}/detalles,
 *             PUT/DELETE /detalles-reposicion/{id}) solo en PENDIENTE / OBSERVADA · PATCH /{id}/reenviar (OBSERVADA → PENDIENTE)
 *   EMPRESA   PATCH /{id}/validar (→ ENVIADA) · /{id}/devolver `{ comentario }` (→ OBSERVADA) · /{id}/cancelar
 *   PROVEEDOR GET /ordenes-reposicion/proveedor/me (ENVIADA / PARCIAL) · POST /{id}/despacho
 *   Lectura   GET /ordenes-reposicion/empresa/{id} (EMPRESA: todas; OPERARIO: las de su almacén) · GET /{id} · GET /{id}/detalles
 *
 * Usar `ACCIONES_ORDEN` de `./enums` para decidir qué botones mostrar.
 */
import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { requireIdEmpresa, useIdEmpresa } from '@/auth/useEmpresa'
import { api, seg } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type {
  DetalleReposicion,
  DetalleReposicionCreate,
  DetalleReposicionUpdate,
  DespachoBody,
  OrdenReposicion,
  OrdenReposicionCreate,
  OrdenReposicionUpdate,
} from './types'

export const ordenesApi = {
  create: async (body: OrdenReposicionCreate): Promise<OrdenReposicion> =>
    norm.orden.one(await api.post('/ordenes-reposicion', body)),
  listByEmpresa: async (idEmpresa: string): Promise<OrdenReposicion[]> =>
    norm.orden.list(await api.get(`/ordenes-reposicion/empresa/${seg(idEmpresa)}`)),
  listProveedorMe: async (): Promise<OrdenReposicion[]> => norm.orden.list(await api.get('/ordenes-reposicion/proveedor/me')),
  get: async (id: string): Promise<OrdenReposicion> => norm.orden.one(await api.get(`/ordenes-reposicion/${seg(id)}`)),
  update: async (id: string, body: OrdenReposicionUpdate): Promise<OrdenReposicion> =>
    norm.orden.one(await api.put(`/ordenes-reposicion/${seg(id)}`, body)),
  remove: (id: string) => api.delete<unknown>(`/ordenes-reposicion/${seg(id)}`),
  validar: async (id: string): Promise<OrdenReposicion> =>
    norm.orden.one(await api.patch(`/ordenes-reposicion/${seg(id)}/validar`)),
  devolver: async (id: string, comentario: string): Promise<OrdenReposicion> =>
    norm.orden.one(await api.patch(`/ordenes-reposicion/${seg(id)}/devolver`, { comentario })),
  reenviar: async (id: string): Promise<OrdenReposicion> =>
    norm.orden.one(await api.patch(`/ordenes-reposicion/${seg(id)}/reenviar`)),
  despachar: async (id: string, body: DespachoBody): Promise<OrdenReposicion> =>
    norm.orden.one(await api.post(`/ordenes-reposicion/${seg(id)}/despacho`, body)),
  cancelar: async (id: string): Promise<OrdenReposicion> =>
    norm.orden.one(await api.patch(`/ordenes-reposicion/${seg(id)}/cancelar`)),
}

export const detallesReposicionApi = {
  create: async (idOrden: string, body: DetalleReposicionCreate): Promise<DetalleReposicion> =>
    norm.detalleReposicion.one(await api.post(`/ordenes-reposicion/${seg(idOrden)}/detalles`, body)),
  listByOrden: async (idOrden: string): Promise<DetalleReposicion[]> =>
    norm.detalleReposicion.list(await api.get(`/ordenes-reposicion/${seg(idOrden)}/detalles`)),
  get: async (id: string): Promise<DetalleReposicion> =>
    norm.detalleReposicion.one(await api.get(`/detalles-reposicion/${seg(id)}`)),
  update: async (id: string, body: DetalleReposicionUpdate): Promise<DetalleReposicion> =>
    norm.detalleReposicion.one(await api.put(`/detalles-reposicion/${seg(id)}`, body)),
  remove: (id: string) => api.delete<unknown>(`/detalles-reposicion/${seg(id)}`),
}

/* ---------------------------- Queries: orden ---------------------------- */

/**
 * Órdenes visibles para la sesión: EMPRESA todas; OPERARIO las de su almacén; PROVEEDOR las ENVIADA / PARCIAL
 * dirigidas a él (`/proveedor/me`).
 */
export function useOrdenes() {
  const { rol } = useSession()
  const idEmpresa = useIdEmpresa()
  const esProveedor = rol === 'PROVEEDOR'
  return useQuery({
    queryKey: esProveedor ? queryKeys.ordenes.proveedorMe() : queryKeys.ordenes.byEmpresa(idEmpresa ?? ''),
    queryFn: () => (esProveedor ? ordenesApi.listProveedorMe() : ordenesApi.listByEmpresa(requireIdEmpresa(idEmpresa))),
    enabled: esProveedor || !!idEmpresa,
  })
}

export function useOrden(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.ordenes.detail(id ?? ''),
    queryFn: () => ordenesApi.get(id!),
    enabled: !!id,
  })
}

/* --------------------------- Mutations: orden --------------------------- */

function onOrdenActualizada(qc: QueryClient, orden: OrdenReposicion) {
  void qc.invalidateQueries({ queryKey: ['abastecimiento'] })
  qc.setQueryData(queryKeys.ordenes.detail(orden.id_orden_reposicion), orden)
  return qc.invalidateQueries({ queryKey: queryKeys.ordenes.all })
}

/** OPERARIO: crea la solicitud (almacén = el suyo). Nace PENDIENTE. */
export function useCreateOrden() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ordenesApi.create, onSuccess: (orden) => onOrdenActualizada(qc, orden) })
}

export function useUpdateOrden() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: OrdenReposicionUpdate }) => ordenesApi.update(id, body),
    onSuccess: (orden) => onOrdenActualizada(qc, orden),
  })
}

export function useDeleteOrden() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => ordenesApi.remove(id),
    onSuccess: (_data, id) => {
      qc.removeQueries({ queryKey: queryKeys.ordenes.detail(id) })
      qc.removeQueries({ queryKey: queryKeys.detallesReposicion.byOrden(id) })
      return Promise.all([
        qc.invalidateQueries({ queryKey: queryKeys.ordenes.all }),
        qc.invalidateQueries({ queryKey: queryKeys.detallesReposicion.all }),
      ])
    },
  })
}

/** EMPRESA: PENDIENTE → ENVIADA (queda visible para el proveedor). */
export function useValidarOrden() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ordenesApi.validar, onSuccess: (o) => onOrdenActualizada(qc, o) })
}

/** EMPRESA: PENDIENTE → OBSERVADA con comentario para el operario. */
export function useDevolverOrden() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, comentario }: { id: string; comentario: string }) => ordenesApi.devolver(id, comentario),
    onSuccess: (o) => onOrdenActualizada(qc, o),
  })
}

/** OPERARIO: OBSERVADA → PENDIENTE (tras corregir). */
export function useReenviarOrden() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ordenesApi.reenviar, onSuccess: (o) => onOrdenActualizada(qc, o) })
}

/** PROVEEDOR: registra lo que despacha (reemplaza el despacho anterior). */
export function useDespacharOrden() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: DespachoBody }) => ordenesApi.despachar(id, body),
    onSuccess: (o) => onOrdenActualizada(qc, o),
  })
}

/** EMPRESA: PENDIENTE | OBSERVADA | APROBADA → CANCELADA */
export function useCancelarOrden() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: ordenesApi.cancelar, onSuccess: (o) => onOrdenActualizada(qc, o) })
}

/* ----------------------- Detalles de reposición ----------------------- */

export function useDetallesReposicion(idOrden: string | undefined) {
  return useQuery({
    queryKey: queryKeys.detallesReposicion.byOrden(idOrden ?? ''),
    queryFn: () => detallesReposicionApi.listByOrden(idOrden!),
    enabled: !!idOrden,
  })
}

export function useDetalleReposicion(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.detallesReposicion.detail(id ?? ''),
    queryFn: () => detallesReposicionApi.get(id!),
    enabled: !!id,
  })
}

function invalidarDetallesReposicion(qc: QueryClient) {
  return Promise.all([
    qc.invalidateQueries({ queryKey: queryKeys.detallesReposicion.all }),
    qc.invalidateQueries({ queryKey: queryKeys.ordenes.all }),
  ])
}

/** Agrega una línea (solo con orden PENDIENTE). */
export function useCreateDetalleReposicion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ idOrden, body }: { idOrden: string; body: DetalleReposicionCreate }) =>
      detallesReposicionApi.create(idOrden, body),
    onSuccess: () => invalidarDetallesReposicion(qc),
  })
}

export function useUpdateDetalleReposicion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: DetalleReposicionUpdate }) => detallesReposicionApi.update(id, body),
    onSuccess: () => invalidarDetallesReposicion(qc),
  })
}

export function useDeleteDetalleReposicion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => detallesReposicionApi.remove(id),
    onSuccess: () => invalidarDetallesReposicion(qc),
  })
}
