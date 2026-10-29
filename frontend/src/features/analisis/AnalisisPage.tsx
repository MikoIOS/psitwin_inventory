import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { analisisApi, type DemandHorizon } from '@/api/analisis'
import { useEmpresa } from '@/auth/useEmpresa'
import { Badge, Button, Card, Field, Select } from '@/components/ui'
import { useSaikiSession } from '@/features/saiki/SaikiSession'
import { paths } from '@/paths'
import { useNavigate } from 'react-router'
import { DemandChart } from './DemandChart'
import { HistoricalDemandPanel } from './HistoricalDemandPanel'
import { PedidosHistoryPanel } from '@/features/abastecimiento/PedidosHistoryPanel'

const n = (v: number | null | undefined) => v == null ? '—' : v.toLocaleString('es-PE', { maximumFractionDigits: 2 })
const STATES: Record<string, string> = { CALCULANDO: 'Calculando…', SIN_HISTORIAL: 'Sin historial', HISTORIAL_INSUFICIENTE: 'Historial insuficiente', MODELO_NO_DISPONIBLE: 'Modelo no disponible', ERROR_MODELO: 'Error de inferencia', DISPONIBLE: 'Disponible' }

export default function AnalisisPage() {
  const { empresa } = useEmpresa()
  const saiki = useSaikiSession()
  const navigate = useNavigate()
  const [view, setView] = useState<'historial' | 'pronosticos' | 'pedidos'>('historial')
  const [warehouse, setWarehouse] = useState('')
  const [product, setProduct] = useState('')
  const [source, setSource] = useState('salidas')
  const [horizon, setHorizon] = useState<DemandHorizon>(30)
  const filters = useQuery({ queryKey: ['analisis', 'filters', empresa?.id_empresa], queryFn: analisisApi.filters, enabled: !!empresa })
  const warehouses = filters.data?.almacenes ?? []
  const products = filters.data?.productos ?? []
  const selectedWarehouse = warehouses.some(w => w.id === warehouse) ? warehouse : warehouses.length === 1 ? warehouses[0]!.id : ''
  const selectedProduct = products.some(p => p.id === product) ? product : ''
  const predicting = view === 'pronosticos'
  const meta = useQuery({ queryKey: ['analisis', 'metadata'], queryFn: analisisApi.metadata, enabled: predicting })
  const forecast = useQuery({ queryKey: ['analisis', 'forecast', empresa?.id_empresa, selectedWarehouse, selectedProduct, source], queryFn: () => analisisApi.forecast(selectedWarehouse, selectedProduct, source), enabled: predicting && !!selectedWarehouse && !!selectedProduct,
    refetchInterval: q => predicting && q.state.data?.estado === 'CALCULANDO' ? 3000 : false })
  const ranking = useQuery({ queryKey: ['analisis', 'ranking', empresa?.id_empresa, selectedWarehouse, selectedProduct, horizon, source], queryFn: () => analisisApi.summary(horizon, selectedWarehouse, selectedProduct, source), enabled: predicting && !!empresa,
    refetchInterval: q => predicting && q.state.data?.calculando ? 5000 : false })
  const ready = ranking.data?.filas.filter(r => r.demanda_acumulada !== null) ?? []
  const total = ready.length === 1 ? ready.reduce((sum, row) => sum + row.demanda_acumulada!, 0) : null
  const explain = () => {
    saiki.setIdProducto(selectedProduct); saiki.setIdInventario(''); navigate(paths.saiki)
    void saiki.send(predicting ? `Analiza la demanda proyectada a ${horizon} días.` : 'Analiza la demanda histórica y las tendencias observadas.', undefined,
      { ...(selectedWarehouse ? { id_almacen: selectedWarehouse } : {}), ...(selectedProduct ? { id_producto: selectedProduct } : {}), horizonte_dias: horizon, context: { fuente: source, grafico: { tipo: 'pronostico', fuente: source, id_almacen: selectedWarehouse, id_producto: selectedProduct, horizonte_dias: horizon } } })
  }
  return <div className="space-y-6">
    <header className="rounded-2xl border border-blue-400/20 bg-gradient-to-br from-[#101b38] via-[#172544] to-[#32234d] p-6 text-white">
      <p className="mb-3 font-mono text-[10px] tracking-[.3em] text-blue-200">PSITWIN / INTELIGENCIA DE DEMANDA</p><h1 className="text-3xl font-semibold">Análisis de demanda</h1><p className="mt-3 text-sm text-blue-100/70">Consulta la demanda histórica y futura para planificar tus existencias.</p>
    </header>
    {view !== 'pedidos' && <Card><div className="grid gap-4 sm:grid-cols-3">
      <Field label="Empresa"><p className="flex h-10 items-center text-sm">{empresa?.nombre ?? 'Empresa autenticada'}</p></Field>
      <Field label="Almacén"><Select value={selectedWarehouse} onChange={e => setWarehouse(e.target.value)} placeholder="Todos los almacenes" options={warehouses.map(w => ({ value: w.id, label: w.nombre }))} /></Field>
      <Field label="Producto"><Select value={selectedProduct} onChange={e => setProduct(e.target.value)} placeholder="Todos los productos" options={products.map(p => ({ value: p.id, label: p.nombre }))} /></Field>
    </div></Card>}
    <div className="flex gap-3" role="group" aria-label="Vista del análisis">
      <Button aria-pressed={view === 'pedidos'} variant={view === 'pedidos' ? 'primary' : 'ghost'} onClick={() => setView('pedidos')}>Pedidos de abastecimiento</Button>
      <Button aria-pressed={view === 'historial'} variant={view === 'historial' ? 'primary' : 'ghost'} onClick={() => setView('historial')}>Historial</Button>
      <Button aria-pressed={predicting} variant={predicting ? 'primary' : 'ghost'} onClick={() => setView('pronosticos')}>Pronósticos</Button>
    </div>
    {filters.isError && <p role="alert">No se pudieron cargar los filtros. <Button onClick={() => void filters.refetch()}>Reintentar</Button></p>}
    {view === 'pedidos' ? <PedidosHistoryPanel /> : !predicting ? <HistoricalDemandPanel tenant={empresa?.id_empresa ?? ''} warehouse={selectedWarehouse} product={selectedProduct}
      warehouseNames={Object.fromEntries(warehouses.map(w => [w.id, w.nombre]))} productNames={Object.fromEntries(products.map(p => [p.id, p.nombre]))} /> : <>
      <Card title="Pronósticos de demanda"><div className="flex flex-wrap items-end justify-between gap-4">
        <Field label="Fuente de demanda"><Select value={source} onChange={e => setSource(e.target.value)} placeholder={false} options={[{ value: 'salidas', label: 'Salidas / CSV histórico' }, { value: 'solicitudes', label: 'Solicitudes de abastecimiento' }]} /></Field>
        <Field label="Días a pronosticar"><Select value={horizon} onChange={e => setHorizon(Number(e.target.value) as DemandHorizon)} placeholder={false} options={[1, 7, 30, 90].map(h => ({ value: String(h), label: `${h} ${h === 1 ? 'día' : 'días'}` }))} /></Field>
        <Badge tone={meta.data?.runtime.validado ? 'success' : 'warning'}>{meta.data?.runtime.validado ? 'Modelo disponible' : 'Modelo no disponible'}</Badge>
        <div><p className="text-xs text-fg-muted">Demanda esperada · {horizon} días desde el corte del historial</p><p className="text-3xl font-semibold">{total == null && ready.length > 1 ? 'Selecciona una serie' : n(total)}</p><p className="text-xs text-fg-muted">{ready.length} series disponibles de {ranking.data?.series_totales ?? 0}</p></div>
      </div></Card>
      {(ranking.isError || forecast.isError || meta.isError) && <p role="alert">No se pudo consultar el pronóstico. <Button onClick={() => { void ranking.refetch(); void meta.refetch(); if (selectedProduct && selectedWarehouse) void forecast.refetch() }}>Reintentar</Button></p>}
      <Card title="Demanda prevista y stock registrado" description="El stock procede del inventario; las solicitudes pendientes no se cuentan como stock disponible.">
        <div className="overflow-auto"><table className="w-full text-left text-sm"><thead><tr>{['Producto / almacén', `Demanda · ${horizon} días`, 'Stock', 'Brecha', 'Estado'].map(label => <th key={label} className="p-3">{label}</th>)}</tr></thead><tbody>{ranking.data?.filas.map(row => <tr key={`${row.id_almacen}|${row.id_producto}`} className="border-t border-border">
          <td className="p-3"><button className="text-left text-blue-500 hover:underline" onClick={() => { setWarehouse(row.id_almacen); setProduct(row.id_producto) }}>{row.producto}</button><p className="text-xs text-fg-muted">{row.almacen}</p></td>
          <td className="p-3">{n(row.demanda_acumulada)} {row.unidad ?? ''}</td><td className="p-3">{n(row.stock_actual)}</td><td className="p-3">{n(row.brecha_stock)}</td><td className="p-3">{STATES[row.estado] ?? row.estado}</td>
        </tr>)}</tbody></table></div>
        {!ranking.data?.filas.length && <p className="py-4 text-sm">{ranking.isPending ? 'Consultando series…' : 'No hay series para estos filtros.'}</p>}
        {!selectedProduct && <p className="mt-3 text-sm text-fg-muted">Selecciona un producto de la tabla para ver su curva y las fechas del pronóstico.</p>}
      </Card>
      {selectedWarehouse && selectedProduct && forecast.data && <Card title={products.find(p => p.id === selectedProduct)?.nombre ?? 'Serie seleccionada'} description={`${STATES[forecast.data.estado]} · Corte del historial: ${forecast.data.fecha_corte}`}>
        <DemandChart history={forecast.data.historico} predictions={forecast.data.estado === 'DISPONIBLE' ? forecast.data.predicciones.slice(0, horizon) : []} />
        {forecast.data.detalle && <p role="status" className="mt-3 text-sm">{forecast.data.detalle}</p>}
        <p className="mt-3 text-xs text-fg-muted">Pronóstico posterior al corte del historial; no es una garantía de demanda futura.</p>
      </Card>}
    </>}
    {view !== 'pedidos' && <div className="flex items-center justify-between gap-4 rounded-2xl border border-violet-400/20 p-5"><p>Consulta {predicting ? 'el pronóstico' : 'el historial'} con Saiki</p><Button disabled={saiki.pending} onClick={explain}>Preguntar a Saiki</Button></div>}
  </div>
}
