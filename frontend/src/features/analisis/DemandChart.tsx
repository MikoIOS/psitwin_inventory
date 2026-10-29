import { useId, useState } from 'react'
import type { DemandPoint, ForecastPoint } from '@/api/analisis'

const W = 960, H = 300, M = { l: 58, r: 18, t: 24, b: 38 }
const number = (v: number) => v.toLocaleString('es-PE', { maximumFractionDigits: 1 })
const timestamp = (day: string) => Date.parse(day + 'T00:00:00Z')
const label = (day: string) => new Date(timestamp(day)).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', timeZone: 'UTC' })

export function DemandChart({ history, predictions, historyUnit = 'días' }: { history: DemandPoint[]; predictions: ForecastPoint[]; historyUnit?: string }) {
  const [full, setFull] = useState(false)
  const gradient = useId().replace(/:/g, '')
  const historical = full ? history : history.slice(-180)
  const all = [...historical, ...predictions]
  if (!all.length) return <div className="flex min-h-72 items-center justify-center rounded-xl border border-dashed border-border bg-surface-2 text-center text-sm text-fg-muted">Selecciona almacén y producto para consultar datos reales.<br />Sin historial no se genera un pronóstico.</div>
  const start = timestamp(all[0]!.fecha), end = timestamp(all[all.length - 1]!.fecha)
  const max = Math.max(1, ...all.map(p => p.cantidad), ...predictions.map(p => p.q90 ?? p.cantidad)) * 1.08
  const x = (day: string) => M.l + (timestamp(day) - start) / Math.max(86_400_000, end - start) * (W - M.l - M.r)
  const y = (v: number) => M.t + (1 - v / max) * (H - M.t - M.b)
  const line = (points: DemandPoint[]) => points.map(p => `${x(p.fecha)},${y(p.cantidad)}`).join(' ')
  const quantiles = predictions.filter(p => p.q10 !== null && p.q90 !== null)
  const band = [...quantiles.map(p => `${x(p.fecha)},${y(p.q90!)}`), ...[...quantiles].reverse().map(p => `${x(p.fecha)},${y(p.q10!)}`)].join(' ')
  const cut = historical[historical.length - 1]
  const series = predictions.length && cut ? [cut, ...predictions] : predictions
  return <div>
    <div className="mb-3 flex flex-wrap items-center justify-between gap-3 text-xs text-fg-muted"><div className="flex flex-wrap gap-4">{!!history.length && <span>● Demanda histórica</span>}{!!predictions.length && <span className="text-blue-500">● Pronóstico medio</span>}{!!quantiles.length && <span className="text-violet-500">▰ Q10–Q90 · banda central 80 %</span>}</div>{history.length > 180 && <label className="flex cursor-pointer items-center gap-2"><input type="checkbox" checked={full} onChange={e => setFull(e.target.checked)} /> Historial completo ({history.length} {historyUnit})</label>}</div>
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Demanda histórica y pronóstico de demanda con banda Q10 a Q90" className="h-auto min-h-48 w-full">
      <defs><linearGradient id={gradient} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8b5cf6" stopOpacity=".25" /><stop offset="1" stopColor="#3b82f6" stopOpacity=".05" /></linearGradient></defs>
      {[0, .25, .5, .75, 1].map(r => <g key={r}><line x1={M.l} x2={W - M.r} y1={y(max * r)} y2={y(max * r)} className="stroke-border" strokeDasharray="3 5" /><text x={M.l - 10} y={y(max * r) + 4} textAnchor="end" className="fill-fg-subtle text-[11px]">{number(max * r)}</text></g>)}
      {band && <polygon points={band} fill={`url(#${gradient})`} data-testid="forecast-band" />}
      {!!historical.length && <polyline points={line(historical)} fill="none" className="stroke-fg-subtle" strokeWidth="1.5" />}
      {!!series.length && <polyline points={line(series)} fill="none" stroke="#3b82f6" strokeWidth="2.5" />}
      {predictions.some(p => p.q50 !== null) && <polyline points={line(predictions.filter(p => p.q50 !== null).map(p => ({ fecha: p.fecha, cantidad: p.q50! })))} fill="none" stroke="#8b5cf6" strokeWidth="1" strokeDasharray="4 3" />}
      {cut && <><line x1={x(cut.fecha)} x2={x(cut.fecha)} y1={M.t} y2={H - M.b} className="stroke-border-strong" strokeDasharray="5 5" /><text x={Math.min(x(cut.fecha) + 6, W - 130)} y={16} className="fill-fg-subtle text-[10px]">Corte {label(cut.fecha)}</text></>}
      {[all[0]!, all[Math.floor((all.length - 1) / 2)]!, all[all.length - 1]!].map((p, i) => <text key={i} x={x(p.fecha)} y={H - 12} textAnchor={i === 0 ? 'start' : i === 2 ? 'end' : 'middle'} className="fill-fg-subtle text-[11px]">{label(p.fecha)}</text>)}
    </svg>
    <p className="mt-2 text-xs text-fg-subtle">{full ? 'Todo el historial disponible' : `Últimos ${historical.length} ${historyUnit} de ${history.length} disponibles`} · cantidades de demanda, no saldo de inventario. {!!predictions.length && 'La línea discontinua del pronóstico representa Q50.'}</p>
  </div>
}
