/**
 * Dispositivos de monitoreo (un ESP32 por equipo de frío) y sus alertas. Contrato: docs/SENSORES.md.
 *   POST /dispositivos (EMPRESA) → dispositivo + `token` en claro UNA vez
 *   GET /dispositivos · GET /dispositivos/{id} (EMPRESA; OPERARIO solo su almacén) — incluyen `estado` en vivo
 *   PUT /dispositivos/{id} · DELETE /dispositivos/{id} · POST /dispositivos/{id}/token (EMPRESA)
 *   GET /dispositivos/{id}/lecturas?desde=&hasta= → `{resolucion, puntos}`: ≤ 24 h crudo (≤ 2000 puntos); > 24 h por minuto
 *   GET /alertas (solo EMPRESA) · PATCH /alertas/{id}/estado — «abierta» = ACTIVA o VISTA; el motor la pasa a RESUELTA
 * Fechas de REST sin zona horaria = UTC (usar `ms()` de features/monitoreo/monitoreoUtils).
 * Tiempo real (lecturas y alertas): `useMonitoreo()` en `./monitoreo`.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { api, seg } from './client'

export type Parametro = 't_int' | 't_amb' | 'hum' | 'corriente'
export const PARAMETROS: Parametro[] = ['t_int', 't_amb', 'hum', 'corriente']

export interface LimiteRango {
  min?: number | null
  max?: number | null
  /** Segundos fuera de rango antes de abrir la alerta. */
  duracion_s?: number | null
}

export interface LimitesPuerta {
  /** Segundos abierta antes de alertar (default 60; p. ej. 20 en vitrinas). */
  max_abierta_s?: number | null
  /** Aperturas por hora (ventana móvil) antes de alertar; null = sin límite. */
  max_aperturas_hora?: number | null
}

export interface Limites {
  t_int?: LimiteRango
  t_amb?: LimiteRango
  hum?: LimiteRango
  corriente?: LimiteRango
  puerta?: LimitesPuerta
}

/** Una lectura (todos los campos opcionales: null = sin sensor o lectura inválida). */
export interface Lectura {
  ts: string
  t_int?: number | null
  puerta?: boolean | null
  t_amb?: number | null
  hum?: number | null
  corriente?: number | null
}

export type TipoAlertaSensor =
  | 'TEMPERATURA_FUERA_RANGO'
  | 'HUMEDAD_FUERA_RANGO'
  | 'CORRIENTE_FUERA_RANGO'
  | 'PUERTA_ABIERTA'
  | 'APERTURAS_EXCESIVAS'
  | 'SENSOR_SIN_DATOS'

export const TIPOS_ALERTA_SENSOR: TipoAlertaSensor[] = [
  'TEMPERATURA_FUERA_RANGO',
  'HUMEDAD_FUERA_RANGO',
  'CORRIENTE_FUERA_RANGO',
  'PUERTA_ABIERTA',
  'APERTURAS_EXCESIVAS',
  'SENSOR_SIN_DATOS',
]

/** Alerta (colección existente) con los campos de sensor. Una por episodio. */
export interface Alerta {
  id_alerta: string
  tipo_alerta: TipoAlertaSensor | (string & {})
  estado: 'ACTIVA' | 'VISTA' | 'RESUELTA' | 'IGNORADA' | (string & {})
  titulo?: string | null
  mensaje?: string | null
  nivel_riesgo?: string | null
  id_almacen?: string | null
  id_dispositivo?: string | null
  /** t_int, t_amb, hum, corriente o puerta. */
  parametro?: string | null
  valor?: number | null
  limite?: number | null
  valor_extremo?: number | null
  inicio?: string | null
  fin?: string | null
  duracion_s?: number | null
  fecha_creacion?: string
  fecha_resolucion?: string | null
}

/** Estado en vivo de un dispositivo (REST y snapshot del WebSocket). */
export interface EstadoDispositivo {
  conectado: boolean
  ultima_lectura: Lectura | null
  puerta_abierta_desde: string | null
  alertas_abiertas: Alerta[]
}

export interface Dispositivo {
  id_dispositivo: string
  id_empresa?: string
  id_almacen: string
  id_zona: string
  id_rack: string | null
  nombre: string
  activo: boolean
  limites: Limites
  /** Límites que aplica el motor (defaults y rango del rack ya resueltos). */
  limites_efectivos?: Limites
  ultima_lectura_ts?: string | null
  estado?: EstadoDispositivo
}

export interface DispositivoCreate {
  id_almacen: string
  id_zona: string
  id_rack?: string | null
  nombre: string
  limites?: Limites
}

export interface DispositivoUpdate {
  nombre?: string
  id_rack?: string | null
  activo?: boolean
  limites?: Limites
}

/** Respuesta de crear: el dispositivo + su token en claro (solo esta vez). */
export type DispositivoConToken = Dispositivo & { token: string }

/** Tema MQTT donde publica el dispositivo. */
export const temaMqtt = (id: string) => `psitwin/dispositivos/${id}/lecturas`

export const dispositivosApi = {
  list: () => api.get<Dispositivo[]>('/dispositivos'),
  get: (id: string) => api.get<Dispositivo>(`/dispositivos/${seg(id)}`),
  create: (body: DispositivoCreate) => api.post<DispositivoConToken>('/dispositivos', body),
  update: (id: string, body: DispositivoUpdate) => api.put<Dispositivo>(`/dispositivos/${seg(id)}`, body),
  remove: (id: string) => api.delete<unknown>(`/dispositivos/${seg(id)}`),
  regenerarToken: (id: string) => api.post<{ token: string }>(`/dispositivos/${seg(id)}/token`),
  lecturas: (id: string, desde: string, hasta: string) =>
    api.get<unknown[] | { resolucion?: string; puntos?: unknown[] }>(`/dispositivos/${seg(id)}/lecturas`, { query: { desde, hasta } }),
}

export const alertasApi = {
  list: () => api.get<Alerta[]>('/alertas'),
  cambiarEstado: (id: string, estado: Alerta['estado']) => api.patch<Alerta>(`/alertas/${seg(id)}/estado`, { estado }),
}

export const dispositivosKeys = {
  all: ['dispositivos'] as const,
  list: () => ['dispositivos', 'list'] as const,
  detail: (id: string) => ['dispositivos', 'detail', id] as const,
  lecturas: (id: string, desde: string, hasta: string) => ['dispositivos', 'lecturas', id, desde, hasta] as const,
}
export const alertasKeys = { all: ['alertas'] as const, list: () => ['alertas', 'list'] as const }

/** EMPRESA u OPERARIO (el backend acota al almacén del operario). */
const usePuedeMonitorear = () => {
  const { isAuthenticated, rol } = useSession()
  return isAuthenticated && rol !== 'PROVEEDOR'
}

export function useDispositivos() {
  return useQuery({ queryKey: dispositivosKeys.list(), queryFn: dispositivosApi.list, enabled: usePuedeMonitorear() })
}

export function useDispositivo(id: string | undefined) {
  return useQuery({ queryKey: dispositivosKeys.detail(id ?? ''), queryFn: () => dispositivosApi.get(id!), enabled: !!id })
}

/**
 * Lecturas históricas normalizadas a `Lectura` (en series por minuto toma el promedio de cada campo).
 * `horas` hacia atrás desde ahora.
 */
export function useLecturas(id: string | undefined, horas: number) {
  // Se redondea al minuto para que la key no cambie en cada render.
  const hasta = new Date(Math.ceil(Date.now() / 60_000) * 60_000)
  const desde = new Date(hasta.getTime() - horas * 3_600_000)
  return useQuery({
    queryKey: dispositivosKeys.lecturas(id ?? '', desde.toISOString(), hasta.toISOString()),
    queryFn: async () => {
      // `{ id_dispositivo, desde, hasta, resolucion: 'cruda' | 'minuto', puntos: [...] }` (se tolera un array directo).
      const r = await dispositivosApi.lecturas(id!, desde.toISOString(), hasta.toISOString())
      return (Array.isArray(r) ? r : (r.puntos ?? [])).map(aLectura)
    },
    enabled: !!id,
    refetchInterval: 60_000,
  })
}

/** Acepta lectura cruda `{ts, t_int…}` o agregada por minuto (`{minuto|ts, t_int: {min,max,prom}}` o `t_int_prom`). */
function aLectura(raw: unknown): Lectura {
  const r = (raw ?? {}) as Record<string, unknown>
  const valor = (campo: string): number | null => {
    const v = r[campo]
    if (typeof v === 'number') return v
    if (v && typeof v === 'object') {
      const o = v as Record<string, unknown>
      const p = o.prom ?? o.promedio ?? o.avg ?? o.mean
      return typeof p === 'number' ? p : null
    }
    const p = r[`${campo}_prom`] ?? r[`${campo}_promedio`] ?? r[`${campo}_avg`]
    return typeof p === 'number' ? p : null
  }
  const puerta = r.puerta
  return {
    ts: String(r.ts ?? r.minuto ?? r.timestamp ?? r.fecha ?? ''),
    t_int: valor('t_int'),
    t_amb: valor('t_amb'),
    hum: valor('hum'),
    corriente: valor('corriente'),
    // Por minuto: `puerta: {fraccion_abierta}` → abierta si estuvo abierta la mayor parte del minuto.
    puerta:
      typeof puerta === 'boolean'
        ? puerta
        : typeof puerta === 'number'
          ? puerta >= 0.5
          : puerta && typeof puerta === 'object' && typeof (puerta as Record<string, unknown>).fraccion_abierta === 'number'
            ? ((puerta as Record<string, number>).fraccion_abierta ?? 0) >= 0.5
            : null,
  }
}

/**
 * Historial de alertas de sensores (solo EMPRESA: `/alertas` es de la empresa). El OPERARIO ve las alertas abiertas
 * a través del estado en vivo de cada dispositivo.
 */
export function useAlertasSensores() {
  const { isAuthenticated, rol } = useSession()
  return useQuery({
    queryKey: alertasKeys.list(),
    queryFn: alertasApi.list,
    enabled: isAuthenticated && rol === 'EMPRESA',
    select: (list) => list.filter((a) => !!a.id_dispositivo || (TIPOS_ALERTA_SENSOR as string[]).includes(a.tipo_alerta)),
  })
}

function useInvalidar() {
  const qc = useQueryClient()
  return () => Promise.all([qc.invalidateQueries({ queryKey: dispositivosKeys.all }), qc.invalidateQueries({ queryKey: alertasKeys.all })])
}

export function useCreateDispositivo() {
  const inv = useInvalidar()
  return useMutation({ mutationFn: dispositivosApi.create, onSuccess: () => inv() })
}

export function useUpdateDispositivo() {
  const inv = useInvalidar()
  return useMutation({ mutationFn: ({ id, body }: { id: string; body: DispositivoUpdate }) => dispositivosApi.update(id, body), onSuccess: () => inv() })
}

export function useDeleteDispositivo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: dispositivosApi.remove,
    onSuccess: (_d, id) => qc.invalidateQueries({ queryKey: dispositivosKeys.all, predicate: (q) => q.queryKey[2] !== id }),
  })
}

export function useRegenerarToken() {
  return useMutation({ mutationFn: dispositivosApi.regenerarToken })
}

/** «Atender» una alerta: la marca VISTA (el motor la resuelve solo cuando el valor vuelve al rango). */
export function useAtenderAlerta() {
  const inv = useInvalidar()
  return useMutation({ mutationFn: (id: string) => alertasApi.cambiarEstado(id, 'VISTA'), onSuccess: () => inv() })
}
