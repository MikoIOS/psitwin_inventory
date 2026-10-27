/**
 * Carga de racks en KG. La calcula el BACKEND: `rack.carga_kg` (Σ stock × peso del producto) y `rack.libre_kg`
 * (capacidad − carga; puede ser negativo en racks antiguos sobrecargados). Aquí solo hay presentación.
 */
import type { Rack } from '@/api/types'
import { formatNumero } from '@/lib/format'

/** Porcentaje de carga (puede superar 100); null si el rack no tiene capacidad. */
export function porcentajeCarga(rack: Pick<Rack, 'capacidad' | 'carga_kg'>): number | null {
  return rack.capacidad > 0 ? Math.round(((rack.carga_kg ?? 0) / rack.capacidad) * 100) : null
}

/** Clase de color de la barra de carga (tokens). */
export function colorOcupacion(porcentaje: number | null): string {
  if (porcentaje === null) return 'bg-fg-subtle'
  if (porcentaje >= 100) return 'bg-danger'
  if (porcentaje >= 85) return 'bg-warning'
  return 'bg-accent'
}

/** "2 a 8 °C" o null si el rack no tiene temperatura (zona no refrigerada). */
export function temperaturaRack(rack: Pick<Rack, 'temperatura_min' | 'temperatura_max'>): string | null {
  if (rack.temperatura_min === null || rack.temperatura_min === undefined || rack.temperatura_max === null || rack.temperatura_max === undefined) return null
  return `${formatNumero(rack.temperatura_min)} a ${formatNumero(rack.temperatura_max)} °C`
}
