import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, seg } from '@/api/client'
import { aLectura, type Parametro } from '@/api/dispositivos'
import { Button, Card, ErrorState, Field, Select } from '@/components/ui'
import { Grafico } from './Grafico'
import { ETIQUETA_PARAMETRO, ms, UNIDAD } from './monitoreoUtils'

export type CampoSensor = Parametro | 'puerta'
export function HistorialSensor({ id, campo }: { id: string; campo: CampoSensor }) {
  const [periodo, setPeriodo] = useState('24')
  const [inicio, setInicio] = useState('')
  const [fin, setFin] = useState('')
  const [pagina, setPagina] = useState(1)
  const [anchor] = useState(() => Date.now())
  const custom = periodo === 'custom'
  const desde = custom ? (inicio ? new Date(inicio).toISOString() : '') : new Date(anchor - Number(periodo) * 3600000).toISOString()
  const hasta = custom ? (fin ? new Date(fin).toISOString() : '') : new Date(anchor).toISOString()
  const valid = !!desde && !!hasta && desde <= hasta
  const query = useQuery({ queryKey: ['dispositivos', 'historial', id, campo, desde, hasta, pagina],
    queryFn: ({ signal }) => api.get<{ puntos: unknown[]; hay_mas: boolean; resolucion: string; resumen: Record<string, { min: number; max: number; prom: number; n: number }> }>(`/dispositivos/${seg(id)}/lecturas`,
      { query: { desde, hasta, pagina, limite: 250, tipo: campo }, signal }), enabled: valid })
  const rows = (query.data?.puntos ?? []).map(aLectura)
  const unit = campo === 'puerta' ? '' : UNIDAD[campo]
  const value = (row: ReturnType<typeof aLectura>) => campo === 'puerta' ? (row.puerta == null ? null : Number(row.puerta)) : row[campo]
  const points = rows.flatMap(row => value(row) == null ? [] : [{ t: ms(row.ts), v: value(row)! }])
  const summary = query.data?.resumen[campo]
  return <Card title={`Historial · ${ETIQUETA_PARAMETRO[campo]}`}>
    <div className="mb-4 flex flex-wrap items-end gap-3">
      <Field label="Periodo"><Select value={periodo} onChange={e => { setPeriodo(e.target.value); setPagina(1) }} placeholder={false} options={[
        { value: '1', label: 'Última hora' }, { value: '24', label: 'Últimas 24 horas' }, { value: '168', label: 'Últimos 7 días' }, { value: '720', label: 'Últimos 30 días' }, { value: 'custom', label: 'Rango personalizado' },
      ]} /></Field>
      {custom && <><Field label="Fecha inicial"><input type="datetime-local" value={inicio} onChange={e => { setInicio(e.target.value); setPagina(1) }} /></Field><Field label="Fecha final"><input type="datetime-local" value={fin} onChange={e => { setFin(e.target.value); setPagina(1) }} /></Field></>}
    </div>
    {!valid && <p>Selecciona un rango válido.</p>}
    {query.error ? <ErrorState error={query.error} onRetry={() => void query.refetch()} /> : <>
      {summary && <p className="text-sm text-fg-muted">Periodo completo por minutos: mínimo {summary.min} · máximo {summary.max} · promedio {summary.prom.toFixed(2)} {unit} · {summary.n} mediciones</p>}
      <p className="text-xs text-fg-muted">{query.data?.resolucion === 'minuto' ? 'Promedios por minuto; los extremos se conservan en el resumen.' : 'Lecturas originales (retención de 7 días).'} Gráfico y tabla: página {pagina}.</p>
      <Grafico puntos={points} unidad={unit} titulo={ETIQUETA_PARAMETRO[campo]} />
      {query.isFetching && <p role="status">Consultando historial…</p>}
      {!query.isFetching && !points.length && <p>Sin mediciones disponibles para este tipo y periodo.</p>}
      <div className="max-h-72 overflow-auto"><table className="w-full text-left text-sm"><caption>Lecturas registradas</caption><thead><tr><th>Fecha y hora</th><th>Valor</th><th>Unidad</th></tr></thead><tbody>{rows.map((row, i) => <tr key={`${row.ts}-${i}`}><td>{new Date(ms(row.ts)).toLocaleString()}</td><td>{value(row) ?? 'Sin lectura'}</td><td>{unit}</td></tr>)}</tbody></table></div>
      <div className="mt-3 flex gap-3"><Button variant="secondary" disabled={pagina === 1 || query.isFetching} onClick={() => setPagina(p => p - 1)}>Anterior</Button><Button variant="secondary" disabled={!query.data?.hay_mas || query.isFetching} onClick={() => setPagina(p => p + 1)}>Siguiente</Button></div>
    </>}
  </Card>
}
