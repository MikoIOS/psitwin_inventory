import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { analisisApi } from '@/api/analisis'
import { Card, Field, Select, Input, Button } from '@/components/ui'
import { DemandChart } from './DemandChart'

export function HistoricalDemandPanel({ tenant, warehouse, product, warehouseNames = {}, productNames = {} }: { tenant: string; warehouse: string; product: string; warehouseNames?: Record<string, string>; productNames?: Record<string, string> }) {
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [frequency, setFrequency] = useState('diaria')
  const [page, setPage] = useState(0)
  const key = [tenant, warehouse, product, start, end, frequency].join('|')
  const [lastKey, setLastKey] = useState(key)
  // Reset pagination when any filter changes, before issuing the next query.
  if (key !== lastKey) { setLastKey(key); setPage(0) }
  const invalid = !!start && !!end && start > end
  const query = useQuery({ queryKey: ['analisis', 'historico', tenant, warehouse, product, start, end, frequency, page],
    queryFn: () => analisisApi.historical({ frecuencia: frequency, offset: page * 100, limite: 100,
      ...(warehouse ? { id_almacen: warehouse } : {}), ...(product ? { id_producto: product } : {}),
      ...(start ? { fecha_inicio: start } : {}), ...(end ? { fecha_fin: end } : {}) }), enabled: !!tenant && !invalid })
  const data = query.data
  const number = (v: number | null | undefined) => v == null ? '—' : v.toLocaleString('es-PE', { maximumFractionDigits: 2 })
  return <Card title="Historial de demanda" description="Demanda registrada en el dataset. Las fechas y los totales de esta vista son históricos.">
    <div className="mb-5 grid gap-4 sm:grid-cols-3">
      <Field label="Desde"><Input type="date" value={start} onChange={e => setStart(e.target.value)} /></Field>
      <Field label="Hasta"><Input type="date" value={end} onChange={e => setEnd(e.target.value)} /></Field>
      <Field label="Ver historial por"><Select value={frequency} placeholder={false} onChange={e => setFrequency(e.target.value)} options={[{ value: 'diaria', label: 'Día' }, { value: 'semanal', label: 'Semana' }, { value: 'mensual', label: 'Mes' }]} /></Field>
    </div>
    {invalid && <p role="alert">La fecha de inicio debe ser anterior o igual a la fecha final.</p>}
    {query.isError && <p role="alert">No se pudo consultar el historial. <Button onClick={() => void query.refetch()}>Reintentar</Button></p>}
    {query.isPending && !invalid && <p role="status">Consultando historial…</p>}
    {!invalid && data && <>
      <div className="mb-5 flex flex-wrap gap-8 text-sm">{product && <><p>Demanda total: <strong>{number(data.total)}</strong></p><p>Promedio diario: <strong>{number(data.promedio_diario)}</strong></p></>}<p>Registros: <strong>{number(data.documentos)}</strong></p></div>
      {!data.documentos ? <p>No hay registros importados para estos filtros.</p> : <>
        <p className="mb-3 text-xs text-fg-muted">{data.fecha_inicio} a {data.fecha_fin} · {data.dias_observados} fechas presentes · agrupación {frequency}</p>
        {product ? <DemandChart history={data.serie} predictions={[]} historyUnit={frequency === 'diaria' ? 'días' : frequency === 'semanal' ? 'periodos semanales' : 'periodos mensuales'} /> : <p className="text-sm text-fg-muted">Selecciona un producto para representar una serie sin mezclar productos ni unidades.</p>}
        <details className="mt-5"><summary className="cursor-pointer text-sm font-medium">Ver registros históricos ({number(data.documentos)})</summary>
        <div className="mt-3 max-h-96 overflow-auto"><table className="w-full text-left text-sm"><thead><tr>{['Fecha', 'Almacén', 'Producto', 'Demanda', 'Imputado en CSV'].map(label => <th key={label} className="p-2">{label}</th>)}</tr></thead><tbody>{data.registros.map(row => <tr className="border-t border-border" key={`${row.id_almacen}|${row.id_producto}|${row.fecha}`}><td className="whitespace-nowrap p-2">{row.fecha}</td><td className="p-2" title={row.id_almacen}>{warehouseNames[row.id_almacen] ?? row.id_almacen}</td><td className="p-2" title={row.id_producto}>{productNames[row.id_producto] ?? row.id_producto}</td><td className="p-2">{number(row.cantidad)}</td><td className="p-2">{row.es_imputado ? 'Sí' : 'No'}</td></tr>)}</tbody></table></div>
        <div className="my-3 flex items-center gap-3"><Button disabled={!page} onClick={() => setPage(page - 1)}>Anterior</Button><span>Página {page + 1}</span><Button disabled={(page + 1) * 100 >= data.documentos} onClick={() => setPage(page + 1)}>Siguiente</Button></div>
        </details>
      </>}
      {data.advertencias.filter(w => !/es_imputado|Promedio por fechas presentes|Demanda del CSV/i.test(w)).map(w => <p key={w} className="mt-2 text-xs text-fg-muted">{w}</p>)}
    </>}
  </Card>
}
