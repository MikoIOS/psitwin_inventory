/**
 * Grilla visual de racks de una zona (filas = niveles, el más alto arriba; color = estado) con la
 * carga de cada rack (kg / carga máxima, kg libres y barra). Compartida por la vista de zona
 * y el inicio del operario.
 *
 *   <RackGrilla racks={racks} invPorRack={map} seleccionado={id} onSelect={(r) => ...} />
 *
 * La carga viene del backend (`rack.carga_kg` / `libre_kg`); `invPorRack` solo aporta nº de productos y alertas.
 * En racks con temperatura (zona refrigerada) se muestra su rango.
 */
import { ESTADO_RACK_LABEL } from '@/api/enums'
import type { Inventario, Rack } from '@/api/types'
import { Icon } from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatNumero } from '@/lib/format'
import { colorOcupacion, porcentajeCarga, temperaturaRack } from '@/lib/racks'
import { estadoStock } from '@/lib/stock'
import { agruparPorNivel, codigoRack, estiloRack } from './ubicacionUtils'

export interface RackGrillaProps {
  racks: Rack[]
  invPorRack?: Map<string, Inventario[] | undefined>
  seleccionado?: string | null | undefined
  onSelect?: (rack: Rack) => void
  /** Mostrar nº de productos y alertas de stock en cada celda. Por defecto true. */
  detalleStock?: boolean
}

export function RackGrilla({ racks, invPorRack, seleccionado, onSelect, detalleStock = true }: RackGrillaProps) {
  const niveles = agruparPorNivel(racks)
  return (
    <div className="overflow-hidden rounded-[calc(var(--radius-ui)+2px)] border border-border bg-surface shadow-card">
      {niveles.map((n) => (
        <div key={n.nivel} role="group" aria-label={`Nivel ${n.nivel}`} className="flex border-b-4 border-border-strong last:border-b-0">
          <div className="flex w-14 shrink-0 flex-col items-center justify-center border-r border-border bg-surface-2 py-3 sm:w-16">
            <span className="label-stencil">Nivel</span>
            <span className="tabular font-mono text-lg font-semibold">{n.nivel}</span>
          </div>
          <ul className="grid flex-1 grid-cols-[repeat(auto-fill,minmax(8.5rem,1fr))] gap-2 p-2 sm:p-3">
            {n.racks.map(({ rack, posicion }) => (
              <li key={rack.id_rack}>
                <RackCelda
                  rack={rack}
                  codigo={codigoRack(rack, posicion)}
                  inventarios={invPorRack?.get(rack.id_rack)}
                  seleccionado={seleccionado === rack.id_rack}
                  detalleStock={detalleStock}
                  {...(onSelect ? { onClick: () => onSelect(rack) } : {})}
                />
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

export interface RackCeldaProps {
  rack: Rack
  codigo: string
  inventarios: Inventario[] | undefined
  seleccionado: boolean
  onClick?: () => void
  detalleStock?: boolean
}

export function RackCelda({ rack, codigo, inventarios, seleccionado, onClick, detalleStock = true }: RackCeldaProps) {
  const est = estiloRack(rack.estado)
  const n = inventarios?.length
  const alertas = inventarios?.filter((i) => estadoStock(i) !== 'STOCK_OK').length ?? 0
  const label = ESTADO_RACK_LABEL[rack.estado] ?? rack.estado
  const pct = porcentajeCarga(rack)
  const temp = temperaturaRack(rack)

  const aria = [
    `Rack ${codigo}`,
    label,
    `${formatNumero(rack.carga_kg)} de ${formatNumero(rack.capacidad)} kg`,
    `${formatNumero(rack.libre_kg)} kg libres`,
    temp,
    detalleStock && n !== undefined ? `${n} productos` : null,
    detalleStock && alertas ? `${alertas} con alerta de stock` : null,
  ]
    .filter(Boolean)
    .join(', ')

  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag
      {...(onClick ? { type: 'button' as const, onClick, 'aria-pressed': seleccionado } : { role: 'group' })}
      aria-label={aria}
      className={cn(
        'relative flex h-full min-h-28 w-full flex-col overflow-hidden rounded-[var(--radius-ui)] border-2 p-2.5 text-left transition-shadow',
        onClick && 'hover:shadow-pop',
        est.celda,
        seleccionado && 'ring-2 ring-focus ring-offset-2 ring-offset-surface',
      )}
    >
      {rack.estado === 'MANTENIMIENTO' && <span className="hazard-stripe absolute inset-x-0 top-0 h-1" aria-hidden="true" />}
      <span className="flex items-center justify-between gap-2">
        <span className="font-mono text-xs font-semibold text-fg">{codigo}</span>
        <span className={cn('size-2.5 rounded-full', est.punto)} aria-hidden="true" />
      </span>
      <span className="mt-1 text-xs font-medium text-fg-muted">{label}</span>
      {temp && <span className="font-mono text-[0.6875rem] text-info">{temp}</span>}

      {detalleStock && (
        <span className="mt-1 flex items-end justify-between gap-2">
          <span className="tabular font-mono text-xs text-fg-muted">{n === undefined ? '—' : `${n} prod.`}</span>
          {alertas > 0 && (
            <span className="inline-flex items-center gap-0.5 font-mono text-xs font-semibold text-danger" title={`${alertas} con alerta de stock`}>
              <Icon name="alert" className="size-3.5" />
              {alertas}
            </span>
          )}
        </span>
      )}

      <span className="mt-auto flex flex-col gap-1 pt-2" aria-hidden="true">
        <span className="flex justify-between gap-1 tabular font-mono text-[0.6875rem] text-fg-muted">
          <span>
            {formatNumero(rack.carga_kg)}/{formatNumero(rack.capacidad)} kg
          </span>
          <span className={cn('font-semibold', rack.libre_kg < 0 ? 'text-danger' : 'text-fg')}>{formatNumero(rack.libre_kg)} libre</span>
        </span>
        <span className="h-1.5 overflow-hidden rounded-full bg-surface-3">
          <span className={cn('block h-full rounded-full', colorOcupacion(pct))} style={{ width: `${Math.min(100, pct ?? 0)}%` }} />
        </span>
      </span>
    </Tag>
  )
}
