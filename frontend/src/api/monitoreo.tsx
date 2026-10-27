/**
 * Tiempo real del monitoreo (docs/SENSORES.md): WebSocket `/api/v1/ws/monitoreo?token=<JWT>&id_zona=<opcional>`.
 *
 *   const m = useMonitoreo(idZona?)   // { conexion, dispositivos: Map<id, DispositivoVivo>, alertasAbiertas }
 *
 * - Aplica `snapshot`, `lectura` y `alerta` (ABIERTA / RESUELTA) a un estado local.
 * - Reconecta con backoff (1 s → 30 s) salvo rechazo del servidor (cierre 4401 / 4403); se cierra al desmontar.
 * - Cada alerta invalida las queries de dispositivos y alertas; `onAlerta` permite avisar (toast).
 *
 * La app abre UNA conexión: `MonitoreoProvider` (en el layout, roles EMPRESA / OPERARIO) y las pantallas leen
 * `useMonitoreoVivo()`. En desarrollo pasa por el proxy de Vite (`ws: true` en vite.config.ts).
 */
import { useQueryClient } from '@tanstack/react-query'
import { createContext, use, useEffect, useRef, useState, type ReactNode } from 'react'
import { useSession } from '@/auth/SessionContext'
import { API_URL } from './client'
import { alertasKeys, dispositivosKeys, type Alerta, type EstadoDispositivo, type Lectura } from './dispositivos'

export type EstadoConexion = 'conectando' | 'conectado' | 'reconectando' | 'cerrado'

export interface DispositivoVivo {
  id_dispositivo: string
  nombre?: string
  id_zona?: string
  estado: EstadoDispositivo
}

export interface Monitoreo {
  conexion: EstadoConexion
  dispositivos: Map<string, DispositivoVivo>
  /** Todas las alertas abiertas de los dispositivos visibles. */
  alertasAbiertas: Alerta[]
}

type Mensaje =
  | { tipo: 'snapshot'; dispositivos: DispositivoVivo[] }
  | ({ tipo: 'lectura'; id_dispositivo: string } & Lectura)
  | { tipo: 'alerta'; evento: 'ABIERTA' | 'RESUELTA'; alerta: Alerta }

const estadoVacio = (): EstadoDispositivo => ({ conectado: false, ultima_lectura: null, puerta_abierta_desde: null, alertas_abiertas: [] })

/** URL del WebSocket a partir de la URL de la API (relativa → mismo host; absoluta → http→ws). */
export function urlMonitoreo(token: string, idZona?: string): string {
  const base = API_URL.startsWith('http') ? API_URL.replace(/^http/, 'ws') : `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}${API_URL}`
  const q = new URLSearchParams({ token, ...(idZona ? { id_zona: idZona } : {}) })
  return `${base}/ws/monitoreo?${q.toString()}`
}

/** Aplica un mensaje del servidor al mapa de dispositivos (inmutable). */
export function aplicarMensaje(prev: Map<string, DispositivoVivo>, m: Mensaje): Map<string, DispositivoVivo> {
  if (m.tipo === 'snapshot') {
    return new Map(m.dispositivos.map((d) => [d.id_dispositivo, { ...d, estado: { ...estadoVacio(), ...d.estado } }]))
  }
  const next = new Map(prev)
  if (m.tipo === 'lectura') {
    const { tipo: _t, id_dispositivo, ...lectura } = m
    const d = next.get(id_dispositivo) ?? { id_dispositivo, estado: estadoVacio() }
    const antes = d.estado
    const abierta = lectura.puerta === true
    next.set(id_dispositivo, {
      ...d,
      estado: {
        ...antes,
        conectado: true,
        ultima_lectura: lectura,
        puerta_abierta_desde: abierta ? (antes.puerta_abierta_desde ?? lectura.ts) : lectura.puerta === false ? null : antes.puerta_abierta_desde,
      },
    })
    return next
  }
  const id = m.alerta.id_dispositivo
  if (!id) return prev
  const d = next.get(id) ?? { id_dispositivo: id, estado: estadoVacio() }
  const otras = d.estado.alertas_abiertas.filter((a) => a.id_alerta !== m.alerta.id_alerta)
  next.set(id, { ...d, estado: { ...d.estado, alertas_abiertas: m.evento === 'ABIERTA' ? [...otras, m.alerta] : otras } })
  return next
}

export function useMonitoreo(idZona?: string, onAlerta?: (evento: 'ABIERTA' | 'RESUELTA', alerta: Alerta, dispositivo?: DispositivoVivo) => void): Monitoreo {
  const { token, isAuthenticated, rol } = useSession()
  const qc = useQueryClient()
  const [conexion, setConexion] = useState<EstadoConexion>('conectando')
  const [dispositivos, setDispositivos] = useState<Map<string, DispositivoVivo>>(() => new Map())
  const onAlertaRef = useRef(onAlerta)
  onAlertaRef.current = onAlerta
  const dispRef = useRef(dispositivos)
  dispRef.current = dispositivos
  const habilitado = isAuthenticated && !!token && rol !== 'PROVEEDOR'

  useEffect(() => {
    if (!habilitado || !token) return
    let ws: WebSocket | null = null
    let intento = 0
    let timer: ReturnType<typeof setTimeout> | undefined
    let vivo = true

    const conectar = () => {
      setConexion(intento === 0 ? 'conectando' : 'reconectando')
      ws = new WebSocket(urlMonitoreo(token, idZona))
      ws.onopen = () => {
        intento = 0
        setConexion('conectado')
      }
      ws.onmessage = (ev) => {
        let m: Mensaje
        try {
          m = JSON.parse(String(ev.data)) as Mensaje
        } catch {
          return
        }
        setDispositivos((prev) => aplicarMensaje(prev, m))
        if (m.tipo === 'alerta') {
          void qc.invalidateQueries({ queryKey: alertasKeys.all })
          void qc.invalidateQueries({ queryKey: dispositivosKeys.all })
          onAlertaRef.current?.(m.evento, m.alerta, m.alerta.id_dispositivo ? dispRef.current.get(m.alerta.id_dispositivo) : undefined)
        }
      }
      ws.onclose = (ev) => {
        if (!vivo) return
        // 4401 (token inválido / expirado) y 4403 (rol o contraseña temporal): reintentar no sirve.
        if (ev.code === 4401 || ev.code === 4403) {
          setConexion('cerrado')
          return
        }
        setConexion('reconectando')
        // ponytail: backoff exponencial sin jitter; con muchas pestañas/clientes conviene añadir jitter.
        const espera = Math.min(30_000, 1000 * 2 ** intento++)
        timer = setTimeout(conectar, espera)
      }
    }
    conectar()
    return () => {
      vivo = false
      clearTimeout(timer)
      ws?.close()
      setDispositivos(new Map())
      setConexion('cerrado')
    }
  }, [habilitado, token, idZona, qc])

  const alertasAbiertas = [...dispositivos.values()].flatMap((d) => d.estado.alertas_abiertas)
  return { conexion, dispositivos, alertasAbiertas }
}

/* ------------------------------------------------------------------ */

const MonitoreoContext = createContext<Monitoreo | null>(null)

/**
 * Una conexión para toda la app (EMPRESA / OPERARIO). `onAlerta` se usa para el toast global.
 * Para PROVEEDOR no abre nada.
 */
export function MonitoreoProvider({ children, onAlerta }: { children: ReactNode; onAlerta?: Parameters<typeof useMonitoreo>[1] }) {
  const m = useMonitoreo(undefined, onAlerta)
  return <MonitoreoContext value={m}>{children}</MonitoreoContext>
}

/** Estado en vivo compartido (null fuera del provider). */
export function useMonitoreoVivo(): Monitoreo | null {
  return use(MonitoreoContext)
}
