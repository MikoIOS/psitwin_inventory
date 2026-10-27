/**
 * Piezas compartidas por la lista y el detalle de monitoreo:
 *  - `ValoresVivos`: t_int, puerta («abierta hace X s»), t_amb, hum y corriente con su color de estado.
 *  - `IndicadorConexion`: estado del WebSocket.
 *  - `useDispositivosVivos()`: dispositivos del REST con el estado en vivo del WebSocket encima.
 */
import { PARAMETROS, useDispositivos, type Dispositivo, type EstadoDispositivo, type Parametro } from '@/api/dispositivos'
import { useMonitoreoVivo, type EstadoConexion } from '@/api/monitoreo'
import { useRacks } from '@/api/racks'
import type { Rack } from '@/api/types'
import { Badge } from '@/components/ui'
import { cn } from '@/lib/cn'
import { duracion, ESTADO_SENSOR, ms, ETIQUETA_PARAMETRO, estadoParametro, formatValor, limiteEfectivo, type EstadoSensor } from './monitoreoUtils'

const TEXTO: Record<EstadoSensor, string> = { normal: 'text-fg', fuera: 'text-warning', alerta: 'text-danger', sin_datos: 'text-fg-subtle' }

export function ValoresVivos({
  dispositivo,
  estado,
  rack,
  ahora,
  grande = false,
}: {
  dispositivo: Dispositivo
  estado: EstadoDispositivo | undefined
  rack: Rack | undefined
  ahora: number
  grande?: boolean
}) {
  const l = estado?.ultima_lectura
  const puertaEstado = estadoParametro(dispositivo, estado, 'puerta', ahora, rack)
  const desde = estado?.puerta_abierta_desde
  return (
    <dl className={cn('grid gap-x-3 gap-y-2', grande ? 'grid-cols-2 sm:grid-cols-5' : 'grid-cols-2')}>
      {PARAMETROS.map((p: Parametro) => {
        const e = estadoParametro(dispositivo, estado, p, ahora, rack)
        const lim = limiteEfectivo(dispositivo, p, rack)
        return (
          <div key={p} className="min-w-0" data-testid={`valor-${p}`} data-estado={e}>
            <dt className="truncate text-xs text-fg-muted">{ETIQUETA_PARAMETRO[p]}</dt>
            <dd className={cn('font-mono font-semibold tabular', grande ? 'text-xl' : 'text-base', TEXTO[e])}>{formatValor(l?.[p], p)}</dd>
            {grande && (lim.min != null || lim.max != null) && (
              <dd className="font-mono text-[0.6875rem] text-fg-subtle">
                {lim.min ?? '—'} a {lim.max ?? '—'}
              </dd>
            )}
          </div>
        )
      })}
      <div className="min-w-0" data-testid="valor-puerta" data-estado={puertaEstado}>
        <dt className="text-xs text-fg-muted">{ETIQUETA_PARAMETRO.puerta}</dt>
        <dd className={cn('font-semibold', grande ? 'text-xl' : 'text-base', TEXTO[puertaEstado])}>
          {l?.puerta == null ? '—' : l.puerta ? 'Abierta' : 'Cerrada'}
        </dd>
        {l?.puerta && desde && <dd className={cn('text-xs', TEXTO[puertaEstado])}>hace {duracion((ahora - ms(desde)) / 1000)}</dd>}
      </div>
    </dl>
  )
}

const CONEXION: Record<EstadoConexion, { tono: 'success' | 'warning' | 'neutral'; label: string }> = {
  conectado: { tono: 'success', label: 'En vivo' },
  conectando: { tono: 'warning', label: 'Conectando…' },
  reconectando: { tono: 'warning', label: 'Reconectando…' },
  cerrado: { tono: 'neutral', label: 'Sin conexión' },
}

export function IndicadorConexion() {
  const c = useMonitoreoVivo()?.conexion ?? 'cerrado'
  return (
    <Badge tone={CONEXION[c].tono} title="Conexión en tiempo real con los sensores">
      <span data-testid="conexion-ws" data-estado={c}>
        {CONEXION[c].label}
      </span>
    </Badge>
  )
}

export function BadgeEstadoSensor({ estado }: { estado: EstadoSensor }) {
  return <Badge tone={ESTADO_SENSOR[estado].tono}>{ESTADO_SENSOR[estado].label}</Badge>
}

/** Dispositivos del REST con el estado en vivo del WebSocket encima, y el rack de cada uno (límite de t_int). */
export function useDispositivosVivos() {
  const q = useDispositivos()
  const vivo = useMonitoreoVivo()
  const racks = new Map((useRacks().data ?? []).map((r) => [r.id_rack, r]))
  const lista = (q.data ?? []).map((d) => ({
    dispositivo: d,
    estado: vivo?.dispositivos.get(d.id_dispositivo)?.estado ?? d.estado,
    rack: d.id_rack ? racks.get(d.id_rack) : undefined,
  }))
  return { q, lista }
}
