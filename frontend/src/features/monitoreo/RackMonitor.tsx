import { useState } from 'react'
import { useUbicaciones } from '@/api/ubicaciones'
import { type Dispositivo } from '@/api/dispositivos'
import { Button, Card, ErrorState, Field, Select } from '@/components/ui'
import { HistorialSensor, type CampoSensor } from './HistorialSensor'
import { ETIQUETA_PARAMETRO, estadoParametro, ESTADO_SENSOR, formatValor, limiteEfectivo, ms, useAhora } from './monitoreoUtils'
import { useDispositivosVivos } from './ValoresVivos'

const campos: CampoSensor[] = ['t_int', 't_amb', 'hum', 'corriente', 'puerta']
const colores: Record<CampoSensor, string> = {
  t_int: '!bg-amber-300/10 hover:!bg-amber-300/20', t_amb: '!bg-orange-300/10 hover:!bg-orange-300/20',
  hum: '!bg-blue-300/10 hover:!bg-blue-300/20', corriente: '!bg-violet-300/10 hover:!bg-violet-300/20', puerta: '!bg-teal-300/10 hover:!bg-teal-300/20',
}
export function camposDisponibles(d: Omit<Dispositivo, 'estado'> & { estado?: Dispositivo['estado'] }): CampoSensor[] {
  return campos.filter(p => d.parametros_disponibles?.includes(p) || d.estado?.ultima_lectura?.[p] != null)
}
export function RackMonitor() {
  const ubicaciones = useUbicaciones()
  const { lista, q } = useDispositivosVivos()
  const [almacen, setAlmacen] = useState('')
  const [zona, setZona] = useState('')
  const [rack, setRack] = useState('')
  const [campo, setCampo] = useState<CampoSensor | ''>('')
  const [device, setDevice] = useState('')
  const now = useAhora()
  const devices = lista.filter(x => x.dispositivo.id_rack === rack && x.dispositivo.id_zona === zona && x.dispositivo.id_almacen === almacen)
  const available = campos.filter(p => devices.some(x => camposDisponibles({ ...x.dispositivo, estado: x.estado }).includes(p)))
  const selected = available.includes(campo as CampoSensor) ? campo as CampoSensor : available[0]
  const matches = devices.filter(x => camposDisponibles({ ...x.dispositivo, estado: x.estado }).includes(selected!))
  const item = matches.find(x => x.dispositivo.id_dispositivo === device) ?? matches[0]
  const d = item?.dispositivo
  const last = item?.estado?.ultima_lectura
  const reset = () => { setCampo(''); setDevice('') }
  if (ubicaciones.error || q.error) return <ErrorState error={ubicaciones.error ?? q.error!} />
  return <div className="mb-6 space-y-4"><Card title="Monitoreo por rack">
    <div className="grid gap-3 sm:grid-cols-3">
      <Field label="Almacén"><Select value={almacen} placeholder="Selecciona almacén" options={ubicaciones.almacenes.map(a => ({ value: a.id_almacen, label: a.nombre }))} onChange={e => { setAlmacen(e.target.value); setZona(''); setRack(''); reset() }} /></Field>
      <Field label="Zona"><Select value={zona} disabled={!almacen} placeholder="Selecciona zona" options={ubicaciones.zonas.filter(z => z.id_almacen === almacen).map(z => ({ value: z.id_zona, label: z.nombre }))} onChange={e => { setZona(e.target.value); setRack(''); reset() }} /></Field>
      <Field label="Rack"><Select value={rack} disabled={!zona} placeholder="Selecciona rack" options={ubicaciones.racks.filter(r => r.zona.id_zona === zona).map(({ rack: r }) => {
        const ds = lista.filter(x => x.dispositivo.id_rack === r.id_rack)
        const types = campos.filter(p => ds.some(x => camposDisponibles({ ...x.dispositivo, estado: x.estado }).includes(p)))
        return { value: r.id_rack, label: `Rack ${r.codigo ?? r.nivel} · ${types.length ? types.map(p => ETIQUETA_PARAMETRO[p]).join(' · ') : ds.length ? 'Tipos aún sin lecturas' : 'Sin sensores'}` }
      })} onChange={e => { setRack(e.target.value); reset() }} /></Field>
    </div>
    <div className="my-4 flex flex-wrap gap-2">{available.map(p => <Button key={p} icon={p === 'hum' ? 'droplet' : p === 'corriente' ? 'zap' : p === 'puerta' ? 'door' : 'thermometer'} variant="secondary" aria-pressed={selected === p} className={`${colores[p]} transition-colors ${selected === p ? 'ring-2 ring-indigo-300' : ''}`} onClick={() => { setCampo(p); setDevice('') }}>{ETIQUETA_PARAMETRO[p]}</Button>)}</div>
    {rack && !devices.length && <p>Este rack no tiene sensores registrados.</p>}
    {rack && devices.length > 0 && !available.length && <p>Los dispositivos registrados aún no han comunicado sus tipos de sensores.</p>}
    {d && selected && <>
      {matches.length > 1 && <Field label="Dispositivo"><Select value={d.id_dispositivo} options={matches.map(x => ({ value: x.dispositivo.id_dispositivo, label: x.dispositivo.nombre }))} onChange={e => setDevice(e.target.value)} /></Field>}
      <p className="font-semibold">{d.nombre} · {ETIQUETA_PARAMETRO[selected]}</p>
      <p className="text-xs text-fg-muted">{d.id_dispositivo} · {ubicaciones.porRack.get(rack)?.etiqueta}</p>
      <p>Conexión: {item.estado?.conectado ? 'Conectado' : 'Desconectado'} · Lectura: {!last ? 'Sin lecturas' : Math.abs(now - ms(last.ts)) > (item.estado?.max_edad_lectura_s ?? 5) * 1000 ? 'Desactualizada' : 'Reciente'}</p>
      <p>Medición: {ESTADO_SENSOR[estadoParametro(d, item.estado, selected, now, item.rack)].label} · {selected === 'puerta' ? last?.puerta == null ? 'Sin lectura' : last.puerta ? 'Abierta' : 'Cerrada' : formatValor(last?.[selected], selected)}</p>
      <p className="text-sm text-fg-muted">{last ? new Date(ms(last.ts)).toLocaleString() : 'Sin fecha de medición'} · Umbrales: {selected === 'puerta' ? JSON.stringify(d.limites_efectivos?.puerta ?? {}) : `${limiteEfectivo(d, selected, item.rack).min ?? 'Sin mínimo'} / ${limiteEfectivo(d, selected, item.rack).max ?? 'Sin máximo'}`}</p>
    </>}
  </Card>{d && selected && <HistorialSensor key={`${d.id_dispositivo}-${selected}`} id={d.id_dispositivo} campo={selected} />}</div>
}
