import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router'
import { abastecimientoApi, type PedidoHistorico } from '@/api/abastecimiento'
import { Button, Card, Field, Input, Select } from '@/components/ui'
import { useSaikiSessionOptional } from '@/features/saiki/SaikiSession'
import { paths } from '@/paths'

export function PedidosHistoryPanel() {
  const [product, setProduct] = useState('')
  const [provider, setProvider] = useState('')
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [cancelled, setCancelled] = useState(false)
  const session = useSaikiSessionOptional()
  const navigate = useNavigate()
  const catalog = useQuery({ queryKey: ['abastecimiento', 'catalogo'], queryFn: abastecimientoApi.catalogo })
  const offers = useQuery({ queryKey: ['abastecimiento', 'ofertas', false, ''], queryFn: () => abastecimientoApi.ofertas() })
  const invalid = !!start && !!end && start > end
  const query = useQuery({ queryKey: ['abastecimiento', 'historial', product, provider, start, end, cancelled],
    queryFn: () => abastecimientoApi.historial({ id_producto: product, id_proveedor: provider, desde: start, hasta: end, incluir_canceladas: cancelled }), enabled: !invalid })
  const providerOptions = [...new Map(offers.data?.map(o => [o.id_proveedor, { value: o.id_proveedor, label: o.proveedor }])).values()]
  const setters = { setChartContext: session?.setChartContext, setIdProducto: session?.setIdProducto, setIdInventario: session?.setIdInventario }
  useEffect(() => {
    setters.setChartContext?.({ tipo: 'pedidos', id_producto: product, id_proveedor: provider, desde: start, hasta: end, incluir_canceladas: cancelled })
    setters.setIdProducto?.(product); setters.setIdInventario?.('')
  }, [product, provider, start, end, cancelled, setters.setChartContext, setters.setIdProducto, setters.setIdInventario])
  const groups = new Map<string, PedidoHistorico[]>()
  for (const row of query.data?.registros ?? []) {
    const key = `${row.id_producto}:${row.unidad}`
    groups.set(key, [...(groups.get(key) ?? []), row])
  }
  const explain = () => {
    if (!session) return
    navigate(paths.saiki)
    void session.send('Explícame el gráfico del historial de pedidos: fechas, cantidades e intervalos registrados.', undefined, product ? { id_producto: product } : {})
  }
  return <Card title="Historial de pedidos" description="Solicitudes de abastecimiento registradas en PsiTwin.">
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Field label="Producto del historial"><Select value={product} onChange={e => setProduct(e.target.value)} options={(catalog.data ?? []).map(p => ({ value: p.id_producto, label: p.nombre }))} placeholder="Todos los productos" /></Field>
      <Field label="Proveedor del historial"><Select value={provider} onChange={e => setProvider(e.target.value)} options={providerOptions} placeholder="Todos los proveedores" /></Field>
      <Field label="Fecha inicial"><Input type="date" value={start} onChange={e => setStart(e.target.value)} /></Field>
      <Field label="Fecha final"><Input type="date" value={end} onChange={e => setEnd(e.target.value)} /></Field>
    </div>
    <label className="my-4 flex items-center gap-2 text-sm"><input type="checkbox" checked={cancelled} onChange={e => setCancelled(e.target.checked)} />Incluir solicitudes canceladas y rechazadas</label>
    {invalid && <p role="alert">La fecha inicial debe ser anterior o igual a la final.</p>}
    {query.isError && <p role="alert">No se pudo consultar los pedidos. <Button onClick={() => void query.refetch()}>Reintentar</Button></p>}
    {query.isPending && !invalid && <p role="status">Consultando pedidos…</p>}
    {!query.isError && !query.isPending && !query.data?.registros.length && <p>No hay pedidos para estos filtros.</p>}
    {[...groups].map(([key, rows]) => <div className="mt-5 rounded-xl border border-border p-4" key={key}>
      <h3 className="mb-3 font-semibold">{catalog.data?.find(p => p.id_producto === rows[0]?.id_producto)?.nombre ?? rows[0]?.id_producto} · {rows[0]?.unidad}</h3>
      <PedidosScatter rows={rows} />
    </div>)}
    {!!query.data?.registros.length && <details className="mt-4"><summary>Ver pedidos individuales ({query.data.registros.length})</summary><div className="max-h-80 overflow-auto"><table className="w-full text-left text-sm"><thead><tr>{['Fecha', 'Producto', 'Proveedor', 'Cantidad solicitada', 'Estado', 'Aceptado', 'Faltante'].map(h => <th key={h} className="p-2">{h}</th>)}</tr></thead><tbody>{query.data.registros.map(row => <tr key={row.id_origen} className="border-t border-border"><td className="p-2">{new Date(row.fecha).toLocaleString('es-PE')}</td><td className="p-2">{catalog.data?.find(p => p.id_producto === row.id_producto)?.nombre ?? row.id_producto}</td><td className="p-2">{row.proveedor}</td><td className="p-2">{row.cantidad} {row.unidad}</td><td className="p-2">{row.estado}</td><td className="p-2">{row.aceptada}</td><td className="p-2">{row.faltante}</td></tr>)}</tbody></table></div></details>}
    {session && <Button className="mt-4" variant="secondary" disabled={session.pending || !query.data?.registros.length} onClick={explain}>Saiki, explícame estos pedidos</Button>}
  </Card>
}

export function PedidosScatter({ rows }: { rows: PedidoHistorico[] }) {
  const width = 800, height = 240, margin = 48
  const times = rows.map(r => Date.parse(r.fecha))
  const start = Math.min(...times), end = Math.max(...times)
  const maximum = Math.max(1, ...rows.map(r => r.cantidad))
  const x = (t: number) => margin + (t - start) / Math.max(86400000, end - start) * (width - margin * 2)
  const y = (value: number) => height - margin - value / maximum * (height - margin * 2)
  return <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Pedidos por fecha real y cantidad solicitada" className="w-full">
    <line x1={margin} x2={width - margin} y1={height - margin} y2={height - margin} className="stroke-border" />
    {[0, .5, 1].map(f => <text key={f} x={margin - 8} y={y(maximum * f)} textAnchor="end" className="fill-fg-muted text-xs">{(maximum * f).toLocaleString('es-PE')}</text>)}
    {rows.map((row, i) => <circle key={row.id_origen} data-request={row.id_origen} cx={x(times[i]!)} cy={y(row.cantidad)} r={5} className="fill-blue-400"><title>{new Date(row.fecha).toLocaleString('es-PE')} · {row.cantidad} {row.unidad} · {row.proveedor} · {row.estado}</title></circle>)}
    {[start, end].map((t, i) => <text key={i} x={x(t)} y={height - 15} textAnchor={i ? 'end' : 'start'} className="fill-fg-muted text-xs">{new Date(t).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' })}</text>)}
  </svg>
}
