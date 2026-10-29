/**
 * Presentación del monitoreo: etiquetas, unidades, límites efectivos y estado (color) por parámetro y dispositivo.
 * Estado: `alerta` (alerta abierta) > `fuera` (fuera de rango, aún sin alerta) > `sin_datos` > `normal`.
 */
import { useEffect, useState } from 'react'
import type { Alerta, Dispositivo, EstadoDispositivo, LimiteRango, Parametro } from '@/api/dispositivos'
import type { Rack } from '@/api/types'
import type { BadgeTone } from '@/components/ui'

export type EstadoSensor = 'normal' | 'fuera' | 'alerta' | 'sin_datos'

export const ETIQUETA_PARAMETRO: Record<Parametro | 'puerta', string> = {
  t_int: 'Temp. interna',
  t_amb: 'Temp. ambiente',
  hum: 'Humedad',
  corriente: 'Corriente',
  puerta: 'Puerta',
}
export const UNIDAD: Record<Parametro, string> = { t_int: '°C', t_amb: '°C', hum: '%', corriente: 'A' }

const ETIQUETA_ALERTA: Record<string, string> = {
  TEMPERATURA_FUERA_RANGO: 'Temperatura fuera de rango',
  HUMEDAD_FUERA_RANGO: 'Humedad fuera de rango',
  CORRIENTE_FUERA_RANGO: 'Corriente fuera de rango',
  PUERTA_ABIERTA: 'Puerta abierta',
  APERTURAS_EXCESIVAS: 'Aperturas excesivas',
  SENSOR_SIN_DATOS: 'Sensor sin datos',
  LECTURA_DESACTUALIZADA: 'Lectura desactualizada',
}
export const etiquetaAlerta = (tipo: string) => ETIQUETA_ALERTA[tipo] ?? tipo

export const ESTADO_SENSOR: Record<EstadoSensor, { tono: BadgeTone; label: string; borde: string }> = {
  normal: { tono: 'success', label: 'Normal', borde: 'border-success/45' },
  fuera: { tono: 'warning', label: 'Fuera de rango', borde: 'border-warning' },
  alerta: { tono: 'danger', label: 'Alerta', borde: 'border-danger' },
  sin_datos: { tono: 'neutral', label: 'Sin datos', borde: 'border-border-strong' },
}

/** ms de una fecha de la API. Las que vienen de Mongo llegan sin zona horaria pero son UTC: se les añade `Z`. */
export function ms(fecha: string | null | undefined): number {
  if (!fecha) return NaN
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(fecha) ? fecha : `${fecha}Z`).getTime()
}

/** Sin lecturas en este tiempo el dispositivo se muestra «sin datos» (el backend alerta a los 5 s). */
export const SIN_DATOS_MS = 5_000

/**
 * Límite efectivo: `limites_efectivos` del backend si viene (defaults y rack ya resueltos); si no, el del dispositivo
 * y, para `t_int` sin min/max y con rack, el rango del rack.
 */
export function limiteEfectivo(d: Pick<Dispositivo, 'limites' | 'limites_efectivos'>, p: Parametro, rack?: Pick<Rack, 'temperatura_min' | 'temperatura_max'>): LimiteRango {
  const efectivo = d.limites_efectivos?.[p]
  if (efectivo) return efectivo
  const l = d.limites?.[p] ?? {}
  if (p === 't_int' && l.min == null && l.max == null && rack) return { ...l, min: rack.temperatura_min, max: rack.temperatura_max }
  return l
}

const fueraDeRango = (v: number | null | undefined, l: LimiteRango) => v != null && ((l.min != null && v < l.min) || (l.max != null && v > l.max))

/** Alerta abierta que corresponde al parámetro (por `parametro` o por tipo). */
export function alertaDe(alertas: Alerta[], p: Parametro | 'puerta'): Alerta | undefined {
  return alertas.find(
    (a) =>
      a.parametro === p ||
      (p === 'puerta' && a.parametro === 'aperturas_hora') ||
      (!a.parametro &&
        ((p === 'puerta' && (a.tipo_alerta === 'PUERTA_ABIERTA' || a.tipo_alerta === 'APERTURAS_EXCESIVAS')) ||
          (p === 'hum' && a.tipo_alerta === 'HUMEDAD_FUERA_RANGO') ||
          (p === 'corriente' && a.tipo_alerta === 'CORRIENTE_FUERA_RANGO'))),
  )
}

export function sinDatos(e: EstadoDispositivo | undefined, ahora: number): boolean {
  const ts = e?.ultima_lectura?.ts
  return !e?.conectado || !ts || Math.abs(ahora - ms(ts)) > (e.max_edad_lectura_s ?? SIN_DATOS_MS / 1000) * 1000
}

export function estadoParametro(
  d: Pick<Dispositivo, 'limites' | 'limites_efectivos'>,
  e: EstadoDispositivo | undefined,
  p: Parametro | 'puerta',
  ahora: number,
  rack?: Pick<Rack, 'temperatura_min' | 'temperatura_max'>,
): EstadoSensor {
  if (e && alertaDe(e.alertas_abiertas, p)) return 'alerta'
  if (sinDatos(e, ahora)) return 'sin_datos'
  if (e?.ultima_lectura?.[p] == null) return 'sin_datos'
  if (p === 'puerta') {
    const desde = e?.puerta_abierta_desde
    const max = d.limites_efectivos?.puerta?.max_abierta_s ?? d.limites?.puerta?.max_abierta_s ?? 60
    return desde && ahora - ms(desde) > max * 1000 ? 'fuera' : 'normal'
  }
  return fueraDeRango(e?.ultima_lectura?.[p], limiteEfectivo(d, p, rack)) ? 'fuera' : 'normal'
}

const GRAVEDAD: Record<EstadoSensor, number> = { normal: 0, sin_datos: 1, fuera: 2, alerta: 3 }

export function estadoDispositivo(d: Pick<Dispositivo, 'limites' | 'limites_efectivos' | 'activo'>, e: EstadoDispositivo | undefined, ahora: number, rack?: Pick<Rack, 'temperatura_min' | 'temperatura_max'>): EstadoSensor {
  if (e?.alertas_abiertas.length) return 'alerta'
  if (sinDatos(e, ahora)) return 'sin_datos'
  return (['t_int', 't_amb', 'hum', 'corriente', 'puerta'] as const)
    .filter(p => e?.ultima_lectura?.[p] != null)
    .map((p) => estadoParametro(d, e, p, ahora, rack))
    .reduce((a, b) => (GRAVEDAD[b] > GRAVEDAD[a] ? b : a), 'normal' as EstadoSensor)
}

/** Reloj que avanza cada `ms` (para «abierta hace X s» y «sin datos»). */
export function useAhora(ms = 1000): number {
  const [ahora, setAhora] = useState(() => Date.now())
  useEffect(() => {
    const t = setInterval(() => setAhora(Date.now()), ms)
    return () => clearInterval(t)
  }, [ms])
  return ahora
}

/** "45 s", "3 min 05 s", "2 h 10 min". */
export function duracion(seg: number): string {
  const s = Math.max(0, Math.floor(seg))
  if (s < 60) return `${s} s`
  if (s < 3600) return `${Math.floor(s / 60)} min ${String(s % 60).padStart(2, '0')} s`
  return `${Math.floor(s / 3600)} h ${Math.floor((s % 3600) / 60)} min`
}

export const formatValor = (v: number | null | undefined, p: Parametro) => (v == null ? '—' : `${v.toFixed(p === 'hum' ? 0 : 1)} ${UNIDAD[p]}`)
