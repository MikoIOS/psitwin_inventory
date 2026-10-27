/**
 * Recepciones de mercadería (UN SOLO PASO).
 *
 *   POST /recepciones · GET /recepciones · GET /recepciones/{id}
 *   GET /recepciones/orden/{id_orden} · GET /recepciones/operario/{id_operario}
 *   POST /detalles-recepcion/{id}/resolver
 *
 * - `POST /recepciones` crea la recepción E INGRESA cada línea al inventario (detalle + movimiento
 *   ENTRADA/RECEPCION + estado de la orden). Cada línea exige `id_inventario`.
 *   NO llamar después a `POST /recepciones/{id}/detalles`: duplicaría el ingreso (por eso no está aquí).
 * - Las recepciones traen sus `detalles` (esquema único). EN_EVALUACION = pendiente de resolver.
 * - Solo con orden ENVIADA o PARCIAL; operario ACTIVO (409 si no) y del almacén de la orden (400 si no).
 * - OJO: el backend crea la recepción y luego cada detalle; si un detalle falla (p. ej. 409 por sobre-recepción)
 *   queda una recepción vacía o parcial. Validar en el formulario ANTES de enviar.
 */
import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { api, seg } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type { DetalleRecepcion, RecepcionMercaderia, RecepcionMercaderiaCreate, ResolverEvaluacionBody } from './types'

export const recepcionesApi = {
  create: async (body: RecepcionMercaderiaCreate): Promise<RecepcionMercaderia> =>
    norm.recepcion.one(await api.post('/recepciones', body)),
  list: async (): Promise<RecepcionMercaderia[]> => norm.recepcion.list(await api.get('/recepciones')),
  get: async (id: string): Promise<RecepcionMercaderia> => norm.recepcion.one(await api.get(`/recepciones/${seg(id)}`)),
  listByOrden: async (idOrden: string): Promise<RecepcionMercaderia[]> =>
    norm.recepcion.list(await api.get(`/recepciones/orden/${seg(idOrden)}`)),
  listByOperario: async (idOperario: string): Promise<RecepcionMercaderia[]> =>
    norm.recepcion.list(await api.get(`/recepciones/operario/${seg(idOperario)}`)),
  resolverDetalle: async (idDetalle: string, body: ResolverEvaluacionBody): Promise<DetalleRecepcion> =>
    norm.detalleRecepcion.one(await api.post(`/detalles-recepcion/${seg(idDetalle)}/resolver`, body)),
}

function recientesPrimero(list: RecepcionMercaderia[]) {
  return [...list].sort((a, b) => (b.fecha_recepcion ?? '').localeCompare(a.fecha_recepcion ?? ''))
}

const usePuedeVer = () => useSession().rol !== 'PROVEEDOR'

/** Todas las recepciones (el backend no filtra por empresa). */
export function useRecepciones() {
  return useQuery({ queryKey: queryKeys.recepciones.list(), queryFn: recepcionesApi.list, select: recientesPrimero, enabled: usePuedeVer() })
}

export function useRecepcion(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.recepciones.detail(id ?? ''),
    queryFn: () => recepcionesApi.get(id!),
    enabled: !!id,
  })
}

export function useRecepcionesPorOrden(idOrden: string | undefined) {
  return useQuery({
    queryKey: queryKeys.recepciones.byOrden(idOrden ?? ''),
    queryFn: () => recepcionesApi.listByOrden(idOrden!),
    enabled: usePuedeVer() && !!idOrden,
    select: recientesPrimero,
  })
}

export function useRecepcionesPorOperario(idOperario: string | undefined) {
  return useQuery({
    queryKey: queryKeys.recepciones.byOperario(idOperario ?? ''),
    queryFn: () => recepcionesApi.listByOperario(idOperario!),
    enabled: !!idOperario,
    select: recientesPrimero,
  })
}

/** Detalles de todas las recepciones de una orden → usar con `calcularPendientes` (`@/lib/ordenes`). */
export function useDetallesRecepcionPorOrden(idOrden: string | undefined) {
  return useQuery({
    queryKey: queryKeys.recepciones.byOrden(idOrden ?? ''),
    queryFn: () => recepcionesApi.listByOrden(idOrden!),
    enabled: usePuedeVer() && !!idOrden,
    select: (list) => list.flatMap((r) => r.detalles),
  })
}

/** Todo lo que cambia cuando entra mercadería: orden, recepciones, stock y movimientos. */
function invalidarTrasIngreso(qc: QueryClient) {
  return Promise.all(
    [queryKeys.ordenes.all, queryKeys.detallesReposicion.all, queryKeys.recepciones.all, queryKeys.inventarios.all, queryKeys.movimientos.all, queryKeys.productos.all, queryKeys.racks.all].map(
      (queryKey) => qc.invalidateQueries({ queryKey }),
    ),
  )
}

/** Registra la recepción e ingresa sus líneas al inventario (un solo paso). */
export function useCreateRecepcion() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: recepcionesApi.create, onSuccess: () => invalidarTrasIngreso(qc) })
}

/** Resuelve una línea EN_EVALUACION (CONFORME → ingresa lo aceptado; RECHAZADO → no ingresa). */
export function useResolverDetalleRecepcion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ idDetalle, body }: { idDetalle: string; body: ResolverEvaluacionBody }) => recepcionesApi.resolverDetalle(idDetalle, body),
    onSuccess: () => invalidarTrasIngreso(qc),
  })
}
