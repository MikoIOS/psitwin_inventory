/**
 * Movimientos: historial INMUTABLE. Solo se listan y se crean (nunca editar ni eliminar).
 *   POST /movimientos · GET /movimientos · GET /movimientos/{id}
 *   GET /movimientos/inventario/{id} · /producto/{id} · /rack/{id} · /operario/{id}
 *   GET /movimientos/tipo/{tipo} · GET /movimientos/motivo/{motivo}
 *
 * La respuesta incluye `id_producto`, `id_rack` y `fecha_hora`: úsalos directamente (no inferirlos del inventario).
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { api, ApiError, seg } from './client'
import { norm } from './normalize'
import { queryKeys } from './queryKeys'
import type { MotivoMovimiento, Movimiento, MovimientoCreate, TipoMovimiento } from './types'

export const movimientosApi = {
  create: async (body: MovimientoCreate): Promise<Movimiento> => norm.movimiento.one(await api.post('/movimientos', body)),
  list: async (): Promise<Movimiento[]> => norm.movimiento.list(await api.get('/movimientos')),
  get: async (id: string): Promise<Movimiento> => norm.movimiento.one(await api.get(`/movimientos/${seg(id)}`)),
  listByInventario: async (idInventario: string): Promise<Movimiento[]> =>
    norm.movimiento.list(await api.get(`/movimientos/inventario/${seg(idInventario)}`)),
  listByProducto: async (idProducto: string): Promise<Movimiento[]> =>
    norm.movimiento.list(await api.get(`/movimientos/producto/${seg(idProducto)}`)),
  listByRack: async (idRack: string): Promise<Movimiento[]> =>
    norm.movimiento.list(await api.get(`/movimientos/rack/${seg(idRack)}`)),
  listByOperario: async (idOperario: string): Promise<Movimiento[]> =>
    norm.movimiento.list(await api.get(`/movimientos/operario/${seg(idOperario)}`)),
  listByTipo: async (tipo: TipoMovimiento): Promise<Movimiento[]> =>
    norm.movimiento.list(await api.get(`/movimientos/tipo/${seg(tipo)}`)),
  /** Si el endpoint no existe (404), trae todos y filtra en cliente. */
  listByMotivo: async (motivo: MotivoMovimiento): Promise<Movimiento[]> => {
    try {
      return norm.movimiento.list(await api.get(`/movimientos/motivo/${seg(motivo)}`))
    } catch (err) {
      if (err instanceof ApiError && (err.status === 404 || err.status === 405)) {
        const todos = await movimientosApi.list()
        return todos.filter((m) => m.motivo_movimiento === motivo)
      }
      throw err
    }
  },
}

/** Ordena del más reciente al más antiguo cuando hay fecha. */
function recientesPrimero(list: Movimiento[]): Movimiento[] {
  return [...list].sort((a, b) => (b.fecha_hora ?? '').localeCompare(a.fecha_hora ?? ''))
}

export function useMovimientos() {
  const { rol } = useSession()
  return useQuery({ queryKey: queryKeys.movimientos.list(), queryFn: movimientosApi.list, select: recientesPrimero, enabled: rol !== 'PROVEEDOR' })
}

export function useMovimiento(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.movimientos.detail(id ?? ''),
    queryFn: () => movimientosApi.get(id!),
    enabled: !!id,
  })
}

export function useMovimientosPorInventario(idInventario: string | undefined) {
  return useQuery({
    queryKey: queryKeys.movimientos.byInventario(idInventario ?? ''),
    queryFn: () => movimientosApi.listByInventario(idInventario!),
    enabled: !!idInventario,
    select: recientesPrimero,
  })
}

export function useMovimientosPorProducto(idProducto: string | undefined) {
  return useQuery({
    queryKey: queryKeys.movimientos.byProducto(idProducto ?? ''),
    queryFn: () => movimientosApi.listByProducto(idProducto!),
    enabled: !!idProducto,
    select: recientesPrimero,
  })
}

export function useMovimientosPorRack(idRack: string | undefined) {
  return useQuery({
    queryKey: queryKeys.movimientos.byRack(idRack ?? ''),
    queryFn: () => movimientosApi.listByRack(idRack!),
    enabled: !!idRack,
    select: recientesPrimero,
  })
}

export function useMovimientosPorOperario(idOperario: string | undefined) {
  return useQuery({
    queryKey: queryKeys.movimientos.byOperario(idOperario ?? ''),
    queryFn: () => movimientosApi.listByOperario(idOperario!),
    enabled: !!idOperario,
    select: recientesPrimero,
  })
}

export function useMovimientosPorTipo(tipo: TipoMovimiento | undefined) {
  return useQuery({
    queryKey: queryKeys.movimientos.byTipo(tipo ?? 'ENTRADA'),
    queryFn: () => movimientosApi.listByTipo(tipo!),
    enabled: !!tipo,
    select: recientesPrimero,
  })
}

export function useMovimientosPorMotivo(motivo: MotivoMovimiento | undefined) {
  return useQuery({
    queryKey: queryKeys.movimientos.byMotivo(motivo ?? 'RECEPCION'),
    queryFn: () => movimientosApi.listByMotivo(motivo!),
    enabled: !!motivo,
    select: recientesPrimero,
  })
}

/**
 * OPERARIO: registra una SALIDA (VENTA / VENCIMIENTO); el autor sale del token.
 * Invalida inventarios (stock), movimientos (historial), racks (carga en kg) y productos.
 */
export function useCreateMovimiento() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: movimientosApi.create,
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: queryKeys.inventarios.all }),
        qc.invalidateQueries({ queryKey: queryKeys.movimientos.all }),
        qc.invalidateQueries({ queryKey: queryKeys.productos.all }),
        qc.invalidateQueries({ queryKey: queryKeys.racks.all }),
      ]),
  })
}
