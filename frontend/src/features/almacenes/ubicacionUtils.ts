/** Utilidades de presentación del módulo almacenes (zonas y racks). */
import type { EstadoRack, Rack } from '@/api/types'

/** Clases (tokens) por estado de rack para la grilla de posiciones. Incluye estados antiguos ACTIVO/INACTIVO. */
export const ESTADO_RACK_ESTILO: Record<EstadoRack, { celda: string; punto: string }> = {
  DISPONIBLE: { celda: 'border-success/45 bg-success-soft', punto: 'bg-success' },
  ACTIVO: { celda: 'border-success/45 bg-success-soft', punto: 'bg-success' },
  LLENO: { celda: 'border-accent/70 bg-accent-soft', punto: 'bg-accent' },
  MANTENIMIENTO: { celda: 'border-warning/50 bg-warning-soft', punto: 'bg-warning' },
  INACTIVO: { celda: 'border-border-strong bg-neutral-soft', punto: 'bg-fg-subtle' },
}

export function estiloRack(estado: string) {
  return ESTADO_RACK_ESTILO[estado as EstadoRack] ?? ESTADO_RACK_ESTILO.INACTIVO
}

export interface NivelRacks {
  nivel: number
  racks: { rack: Rack; posicion: number }[]
}

/**
 * Agrupa racks por nivel (de arriba hacia abajo, el nivel más alto primero, como una estantería).
 * `posicion` es el orden dentro del nivel (1, 2, …), ordenado por código del rack.
 */
export function agruparPorNivel(racks: Rack[]): NivelRacks[] {
  const map = new Map<number, Rack[]>()
  for (const r of racks) map.set(r.nivel, [...(map.get(r.nivel) ?? []), r])
  return [...map.entries()]
    .sort(([a], [b]) => b - a)
    .map(([nivel, lista]) => ({
      nivel,
      racks: [...lista]
        .sort((a, b) => (a.codigo ?? '').localeCompare(b.codigo ?? '', 'es', { numeric: true }) || a.id_rack.localeCompare(b.id_rack))
        .map((rack, i) => ({ rack, posicion: i + 1 })),
    }))
}

/** Código visible de un rack: su `codigo` real del backend (o "N2 · P1" si faltara). */
export function codigoRack(rack: Pick<Rack, 'codigo' | 'nivel'>, posicion: number): string {
  return rack.codigo || `N${rack.nivel} · P${posicion}`
}
