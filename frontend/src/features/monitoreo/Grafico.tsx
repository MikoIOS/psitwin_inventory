/**
 * Gráfico de línea simple en SVG (sin librerías): una serie temporal con banda de límites (min/max) en guiones.
 * `escalon` dibuja la puerta (0 cerrada / 1 abierta) como escalones.
 */
import { formatNumero } from '@/lib/format'

export interface Punto {
  t: number
  v: number
}

const W = 600
const H = 140
const M = { l: 44, r: 8, t: 8, b: 20 }

export function Grafico({
  puntos,
  min,
  max,
  unidad,
  escalon = false,
  titulo,
}: {
  puntos: Punto[]
  min?: number | null | undefined
  max?: number | null | undefined
  unidad: string
  escalon?: boolean
  titulo: string
}) {
  if (puntos.length < 2) return <p className="py-6 text-center text-sm text-fg-muted">Sin lecturas en este periodo.</p>
  const t0 = puntos[0]!.t
  const t1 = puntos[puntos.length - 1]!.t
  const valores = puntos.map((p) => p.v).concat(escalon ? [0, 1] : [min, max].filter((x): x is number => x != null))
  let vMin = Math.min(...valores)
  let vMax = Math.max(...valores)
  if (vMax === vMin) {
    vMax += 1
    vMin -= 1
  }
  const pad = (vMax - vMin) * 0.08
  vMin -= pad
  vMax += pad
  const x = (t: number) => M.l + ((t - t0) / Math.max(1, t1 - t0)) * (W - M.l - M.r)
  const y = (v: number) => M.t + (1 - (v - vMin) / (vMax - vMin)) * (H - M.t - M.b)
  const pts = puntos.flatMap((p, i) => (escalon && i > 0 ? [`${x(p.t)},${y(puntos[i - 1]!.v)}`, `${x(p.t)},${y(p.v)}`] : [`${x(p.t)},${y(p.v)}`]))
  const hora = (t: number) => new Date(t).toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })
  const ticks = escalon ? [0, 1] : [vMin + pad, (vMin + vMax) / 2, vMax - pad]

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={titulo}>
      {ticks.map((v) => (
        <g key={v}>
          <line x1={M.l} x2={W - M.r} y1={y(v)} y2={y(v)} className="stroke-border" strokeWidth={0.5} />
          <text x={M.l - 4} y={y(v) + 3} textAnchor="end" className="fill-fg-subtle font-mono text-[9px]">
            {escalon ? (v ? 'abierta' : 'cerrada') : `${formatNumero(Math.round(v * 10) / 10)}${unidad}`}
          </text>
        </g>
      ))}
      {[min, max].map((v, i) =>
        v == null ? null : <line key={i} x1={M.l} x2={W - M.r} y1={y(v)} y2={y(v)} className="stroke-danger" strokeWidth={1} strokeDasharray="4 3" />,
      )}
      <polyline points={pts.join(' ')} fill="none" className="stroke-accent" strokeWidth={1.5} strokeLinejoin="round" />
      <text x={M.l} y={H - 4} className="fill-fg-subtle font-mono text-[9px]">
        {hora(t0)}
      </text>
      <text x={W - M.r} y={H - 4} textAnchor="end" className="fill-fg-subtle font-mono text-[9px]">
        {hora(t1)}
      </text>
    </svg>
  )
}
