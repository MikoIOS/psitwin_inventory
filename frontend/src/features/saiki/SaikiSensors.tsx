import { useEffect, useRef, useState } from 'react'
import { useSaikiSessionOptional } from './SaikiSession'
import { useLocation } from 'react-router'
import { useAlertasSensores, useDispositivos } from '@/api/dispositivos'
import { useMonitoreoVivo } from '@/api/monitoreo'
import { useSession } from '@/auth/SessionContext'
import { useEmpresa } from '@/auth/useEmpresa'
import { Button, Card, LinkButton } from '@/components/ui'
import { paths } from '@/paths'
import { AgentAudioVisualizerWave } from '@/components/agents-ui/agent-audio-visualizer-wave'
import { sinDatos, useAhora, ms } from '@/features/monitoreo/monitoreoUtils'

export function useSaludo() {
  const { operario, proveedor } = useSession()
  const { empresa } = useEmpresa()
  const [hora, setHora] = useState(() => new Date().getHours())
  useEffect(() => { const timer = setInterval(() => setHora(new Date().getHours()), 60_000); return () => clearInterval(timer) }, [])
  return `${hora < 12 ? 'Buenos días' : hora < 19 ? 'Buenas tardes' : 'Buenas noches'}${operario?.nombre || proveedor?.nombre || empresa?.nombre ? `, ${operario?.nombre || proveedor?.nombre || empresa?.nombre}` : ''}`
}

export function SaikiSensors() {
  const vivo = useMonitoreoVivo()
  const devices = useDispositivos()
  const history = useAlertasSensores()
  const location = useLocation()
  const now = useAhora()
  const selected = new URLSearchParams(location.search).get('incidente')
  const available = vivo?.conexion === 'conectado' && [...vivo.dispositivos.values()].some(d => !sinDatos(d.estado, now))
  const incidents = [...(history.data ?? vivo?.alertasAbiertas ?? [])].sort((a, b) => {
    const rank = (level?: string | null) => level === 'CRITICO' ? 0 : level === 'ALTO' ? 1 : 2
    const open = (state: string) => ['ACTIVA', 'VISTA'].includes(state)
    return Number(b.id_alerta === selected) - Number(a.id_alerta === selected) || Number(open(b.estado)) - Number(open(a.estado)) || rank(a.nivel_riesgo) - rank(b.nivel_riesgo)
  })
  return <Card title="Supervisión de sensores" description={devices.isError || history.isError ? 'Error al consultar los sensores' : devices.isPending || history.isPending ? 'Consultando sensores…' : available ? 'Lecturas e incidentes registrados' : 'Sin lecturas actuales disponibles'}>
    {devices.isError || history.isError ? <p role="status">No se pudo consultar el historial. Intenta de nuevo.</p> : null}
    <p className="mb-3 text-sm text-fg-muted">Una alerta no confirma una avería. Contrasta las lecturas antes de diagnosticar el sensor o el equipo.</p>
    <details open={!!selected}>
      <summary className="cursor-pointer">{history.isError ? 'Historial de incidentes no disponible' : `Historial de incidentes (${incidents.length})`}</summary>
      <div className="max-h-80 space-y-3 overflow-auto pt-3">
        {incidents.map(a => {
          const d = devices.data?.find(d => d.id_dispositivo === a.id_dispositivo)
          return <article key={a.id_alerta} className="rounded-lg border border-border p-3" aria-label={a.id_alerta === selected ? 'Incidente seleccionado' : undefined}>
            <p className="font-semibold">{a.nivel_riesgo} · {d?.nombre ?? 'Equipo sin nombre disponible'} · {a.estado}</p>
            <p>{a.mensaje || a.titulo}</p>
            <p className="text-sm text-fg-muted">{a.parametro ?? 'Parámetro no registrado'}: {a.valor ?? 'sin valor'} · Límite: {a.limite ?? 'sin límite registrado'} · Extremo: {a.valor_extremo ?? 'sin dato'}</p>
            <p className="text-xs text-fg-muted">{a.fecha_creacion ? new Date(ms(a.fecha_creacion)).toLocaleString() : 'Fecha no disponible'}</p>
            {a.id_dispositivo && <LinkButton size="sm" to={paths.dispositivo(a.id_dispositivo)}>Ver equipo, ubicación y lecturas</LinkButton>}
          </article>
        })}
        {!incidents.length && !history.isError && <p>{history.isPending ? 'Consultando historial…' : 'No hay incidentes registrados disponibles.'}</p>}
      </div>
    </details>
  </Card>
}

export function SaikiNotification() {
  const session = useSaikiSessionOptional()
  const voice = session?.voice
  const pending = session?.pending
  const spoken = useRef(new Set<string>())
  const initialized = useRef(false)
  const vivo = useMonitoreoVivo()
  const { rol, empresa } = useSession()
  const location = useLocation()
  const saludo = useSaludo()
  const key = `saiki-incidentes:${empresa?.id_empresa ?? 'sesion'}:${rol}`
  const [hidden, setHidden] = useState<Record<string, number>>({})
  const [now, setNow] = useState(Date.now)
  useEffect(() => {
    try { setHidden(JSON.parse(localStorage.getItem(key) ?? '{}')) } catch { setHidden({}) }
  }, [key])
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(t) }, [])
  const alert = vivo?.conexion === 'conectado' ? [...vivo.alertasAbiertas]
    .filter(a => ['CRITICO', 'ALTO'].includes(a.nivel_riesgo ?? '') && (hidden[a.id_alerta] ?? 0) <= now)
    .sort((a, b) => Number(b.nivel_riesgo === 'CRITICO') - Number(a.nivel_riesgo === 'CRITICO'))[0] : undefined
  useEffect(() => {
    if (vivo?.conexion !== 'conectado') return
    const alerts = vivo.alertasAbiertas
    if (!initialized.current) {
      alerts.forEach(a => spoken.current.add(a.id_alerta))
      initialized.current = true
      return // Never replay existing incidents after loading a session.
    }
    const announcements: string[] = []
    for (const a of alerts) {
      if (spoken.current.has(a.id_alerta)) continue
      if (pending && voice?.voiceEnabled && voice.preferences.sensorAlerts && voice.isEnabled()) continue
      spoken.current.add(a.id_alerta)
      if (!pending && voice?.voiceEnabled && voice.preferences.sensorAlerts && voice.isEnabled())
        announcements.push(`${a.mensaje || a.titulo}. Estado: ${a.estado}.`)
    }
    if (announcements.length) voice?.speak(`Alerta de sensores. ${announcements.slice(0, 3).join(' ')} ${announcements.length > 3 ? `Hay ${announcements.length - 3} incidentes adicionales.` : ''} Puedes consultar el historial en Monitoreo.`)
  }, [vivo?.alertasAbiertas, vivo?.conexion, pending, voice])
  const dismiss = (until: number) => {
    if (!alert) return
    const next = { ...hidden, [alert.id_alerta]: until }
    setHidden(next)
    try { localStorage.setItem(key, JSON.stringify(next)) } catch { /* In-memory suppression remains available. */ }
  }
  useEffect(() => {
    if (!alert || location.pathname === paths.saiki) return
    const timer = setTimeout(() => {
      setHidden(previous => {
        const next = { ...previous, [alert.id_alerta]: Number.MAX_SAFE_INTEGER }
        try { localStorage.setItem(key, JSON.stringify(next)) } catch { /* Optional persistence. */ }
        return next
      })
    }, 20_000)
    return () => clearTimeout(timer)
  }, [alert?.id_alerta, key, location.pathname])
  if (!alert || rol !== 'EMPRESA' || location.pathname === paths.saiki) return null
  return <aside role="status" aria-label="Aviso de Saiki" className="fixed top-1/2 left-1/2 z-50 w-[min(92vw,32rem)] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-violet-400 bg-surface p-6 shadow-2xl shadow-violet-500/30">
    <AgentAudioVisualizerWave size="sm" state="idle" color="#6587ff" colorShift={1.5} className="mx-auto" />
    <p className="font-semibold">{saludo}. Soy Saiki.</p>
    <p className="mt-2 font-semibold text-danger">{alert.nivel_riesgo} · {vivo?.dispositivos.get(alert.id_dispositivo ?? '')?.nombre ?? 'Dispositivo'}{alert.codigo_rack || alert.id_rack ? ` · Rack ${alert.codigo_rack || alert.id_rack}` : ''}</p>
    <p className="my-3">{alert.mensaje || alert.titulo}</p>
    <p className="mb-3 text-sm text-fg-muted">Te recomiendo revisar las lecturas y el equipo asociado. La alerta por sí sola no confirma una avería.</p>
    <div className="flex flex-wrap gap-2">
      <LinkButton to={`${paths.saiki}?incidente=${encodeURIComponent(alert.id_alerta)}`} onClick={() => dismiss(Number.MAX_SAFE_INTEGER)}>Ver detalles en Saiki</LinkButton>
      <Button variant="secondary" onClick={() => dismiss(Date.now() + 15 * 60_000)}>Posponer 15 min</Button>
      <Button variant="ghost" onClick={() => dismiss(Number.MAX_SAFE_INTEGER)}>Descartar</Button>
    </div>
    <p className="mt-3 text-xs text-fg-muted">Se oculta en 20 segundos. El incidente seguirá disponible en el historial.</p>
  </aside>
}
