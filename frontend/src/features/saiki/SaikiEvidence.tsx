import { useState } from 'react'
import { useDispositivos, useLecturas, type Parametro } from '@/api/dispositivos'
import { useMonitoreoVivo } from '@/api/monitoreo'
import { Button, Card, Field, Select } from '@/components/ui'
import { Grafico } from '@/features/monitoreo/Grafico'
import { ETIQUETA_PARAMETRO, UNIDAD, limiteEfectivo, ms, sinDatos, useAhora } from '@/features/monitoreo/monitoreoUtils'
import { paths } from '@/paths'
import { useSaikiSession } from './SaikiSession'

const asRecord = (value: unknown): Record<string, unknown> => value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}

export function SaikiEvidence() {
  const session = useSaikiSession()
  const devices = useDispositivos()
  const live = useMonitoreoVivo()
  const selected = session.sensorContext?.id_dispositivo ?? ''
  const [parameter, setParameter] = useState<Parametro>('t_int')
  const hours = session.sensorContext?.sensor_horas ?? 24
  const device = devices.data?.find(d => d.id_dispositivo === selected)
  const readings = useLecturas(device?.id_dispositivo, hours)
  const now = useAhora()
  const state = device ? live?.dispositivos.get(device.id_dispositivo)?.estado ?? device.estado : undefined
  const available = live?.conexion === 'conectado' && !sinDatos(state, now)
  const limits = device ? limiteEfectivo(device, parameter) : {}
  const points = (readings.data ?? []).flatMap(reading => {
    const value = reading[parameter]
    const time = ms(reading.ts)
    return typeof value === 'number' && Number.isFinite(value) && Number.isFinite(time) ? [{ t: time, v: value }] : []
  }).sort((a, b) => a.t - b.t)
  const data = asRecord(session.result?.data)
  const summary = asRecord(data.inventory_summary ?? asRecord(data.get_warehouse_status).inventory_summary)
  const rows = Array.isArray(summary.rows) ? summary.rows.map(asRecord) : []
  return <div className="space-y-5">
    {Object.keys(summary).length > 0 && <Card title="Datos de tu última consulta" description="Información devuelta por el backend; no es una simulación.">
      <div className="mb-4 grid grid-cols-3 gap-2">
        {[['Productos', summary.distinct_products], ...Object.entries(asRecord(summary.totales_por_unidad)).map(([unit, value]) => [unit, value]), ...(summary.totales_por_unidad ? [] : [['Unidades', summary.total_units]]), ['Almacenes', summary.warehouse_count]].map(([label, value]) => <div key={String(label)} className="rounded-xl bg-surface-2 p-3"><p className="text-xs text-fg-muted">{String(label)}</p><p className="text-xl font-semibold">{typeof value === 'number' ? value.toLocaleString() : 'Sin datos'}</p></div>)}
      </div>
      {!!rows.length && <div className="max-h-64 overflow-auto"><table className="w-full text-left text-sm"><caption className="sr-only">Productos y ubicaciones de la última consulta</caption><thead><tr>{['Producto', 'Stock', 'Ubicación'].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={index} className="border-t border-border"><td className="p-2">{String(row.product_name ?? 'Sin nombre')}</td><td className="p-2">{typeof row.stock === 'number' ? row.stock : 'Sin datos'} {String(row.unidad ?? 'unidad')}</td><td className="p-2">{[row.warehouse_name, row.zone_name, row.rack_name].filter(Boolean).map(String).join(' / ')}</td></tr>)}</tbody></table></div>}
      <Button variant="ghost" size="sm" onClick={() => session.openGuide({ to: paths.inventario, title: 'Inventario', description: 'Revisa el inventario y sigue preguntando a Saiki.' })}>Continuar en inventario ↗</Button>
    </Card>}
    <Card title="Explora tus sensores" description="Elige un equipo para ver sus lecturas y pedirle a Saiki que las explique.">
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Equipo"><Select disabled={devices.isPending || devices.isError} value={selected} onChange={event => session.setSensorContext(event.target.value ? { id_dispositivo: event.target.value, sensor_horas: hours } : undefined)} options={(devices.data ?? []).map(d => ({ value: d.id_dispositivo, label: d.nombre }))} placeholder={devices.isError ? 'Error al cargar equipos' : devices.isPending ? 'Cargando equipos…' : 'Selecciona un equipo'} /></Field>
        <Field label="Medición"><Select value={parameter} onChange={event => setParameter(event.target.value as Parametro)} placeholder={false} options={(['t_int', 't_amb', 'hum', 'corriente'] as Parametro[]).map(p => ({ value: p, label: ETIQUETA_PARAMETRO[p] }))} /></Field>
        <Field label="Periodo"><Select value={hours} onChange={event => session.setSensorContext({ ...(selected ? { id_dispositivo: selected } : {}), sensor_horas: Number(event.target.value) })} placeholder={false} options={[1, 6, 24, 168].map(h => ({ value: String(h), label: h === 168 ? 'Últimos 7 días' : `Últimas ${h} h` }))} /></Field>
      </div>
      {devices.isError && <p role="alert" className="mt-4">No se pudo consultar los equipos. Revisa la conexión.</p>}
      {!devices.isPending && !devices.isError && !devices.data?.length && <p className="py-6 text-center text-sm text-fg-muted">Sin datos disponibles. Todavía no hay equipos registrados.</p>}
      {device && <>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-2"><p className="text-sm text-fg-muted">{available ? 'Equipo con lecturas actuales' : 'Sin datos disponibles en tiempo real. El gráfico puede contener lecturas históricas.'}</p><span className="text-xs text-fg-muted">{device.nombre} · {UNIDAD[parameter]}</span></div>
        {readings.isPending ? <p role="status" className="py-8 text-center">Consultando lecturas…</p> : readings.isError ? <p role="alert" className="py-8">No se pudieron cargar las lecturas.</p> : points.length === 1 ? <p className="py-8 text-center text-sm">Solo hay una lectura: {points[0]!.v} {UNIDAD[parameter]} · {new Date(points[0]!.t).toLocaleString()}. Se necesitan dos puntos para trazar una serie.</p> : <Grafico puntos={points} min={limits.min} max={limits.max} unidad={UNIDAD[parameter]} titulo={`${ETIQUETA_PARAMETRO[parameter]} de ${device.nombre}`} />}
        <div className="flex flex-wrap gap-2">
          <Button size="sm" disabled={session.pending} onClick={() => void session.send(`Explica el gráfico de ${ETIQUETA_PARAMETRO[parameter]} (${UNIDAD[parameter]}) del equipo ${device.nombre} durante las últimas ${hours} horas: tendencia, valores disponibles, umbrales e incidentes registrados. Si faltan lecturas, indícalo. Diferencia datos actuales e históricos y no confirmes averías sin evidencia.`, { id_dispositivo: device.id_dispositivo, sensor_horas: hours })}>Saiki, explícame este equipo</Button>
          <Button size="sm" variant="secondary" onClick={() => session.openGuide({ to: paths.dispositivo(device.id_dispositivo), title: device.nombre, description: 'Aquí tienes la ubicación, lecturas e historial de este equipo. Sigo escuchándote.' })}>Ver equipo con Saiki ↗</Button>
        </div>
      </>}
    </Card>
  </div>
}
