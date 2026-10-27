/**
 * Mapa de ubicaciones de la empresa: rack → zona → almacén.
 * Útil para etiquetar inventarios ("Almacén Principal › Zona A › Rack A-01"),
 * filtrar por almacén y acotar datos globales (inventarios) a la empresa.
 */
import { useAlmacenes } from './almacenes'
import { useRacks } from './racks'
import { useZonas } from './zonas'
import type { Almacen, Rack, Zona } from './types'

export interface RackUbicado {
  rack: Rack
  zona: Zona
  almacen: Almacen
  /** "Zona A › Rack A-01" */
  etiquetaCorta: string
  /** "Almacén Principal › Zona A › Rack A-01" */
  etiqueta: string
}

export interface Ubicaciones {
  racks: RackUbicado[]
  porRack: Map<string, RackUbicado>
  almacenes: Almacen[]
  zonas: Zona[]
  /** true si el rack pertenece a un almacén de la empresa autenticada. */
  perteneceAEmpresa: (idRack: string) => boolean
  isLoading: boolean
  error: Error | null
}

/** "Rack A-01" (usa el código real del backend; si faltara, cae al nivel). */
export function etiquetaRack(rack: Pick<Rack, 'nivel'> & Partial<Pick<Rack, 'codigo'>>): string {
  return rack.codigo ? `Rack ${rack.codigo}` : `Nivel ${rack.nivel}`
}

/** "Rack A-01 · Nivel 2" */
export function etiquetaRackConNivel(rack: Pick<Rack, 'nivel'> & Partial<Pick<Rack, 'codigo'>>): string {
  return rack.codigo ? `Rack ${rack.codigo} · Nivel ${rack.nivel}` : `Nivel ${rack.nivel}`
}

export function useUbicaciones(): Ubicaciones {
  const almacenesQ = useAlmacenes()
  const zonasQ = useZonas()
  const racksQ = useRacks()

  const almacenes = almacenesQ.data ?? []
  const almacenPorId = new Map(almacenes.map((a) => [a.id_almacen, a]))
  const zonas = (zonasQ.data ?? []).filter((z) => almacenPorId.has(z.id_almacen))
  const zonaPorId = new Map(zonas.map((z) => [z.id_zona, z]))

  const racks: RackUbicado[] = []
  for (const rack of racksQ.data ?? []) {
    const zona = zonaPorId.get(rack.id_zona)
    const almacen = zona ? almacenPorId.get(zona.id_almacen) : undefined
    if (!zona || !almacen) continue
    const etiquetaCorta = `${zona.nombre} › ${etiquetaRack(rack)}`
    racks.push({ rack, zona, almacen, etiquetaCorta, etiqueta: `${almacen.nombre} › ${etiquetaCorta}` })
  }
  const porRack = new Map(racks.map((r) => [r.rack.id_rack, r]))

  return {
    racks,
    porRack,
    almacenes,
    zonas,
    perteneceAEmpresa: (idRack) => porRack.has(idRack),
    isLoading: almacenesQ.isLoading || zonasQ.isLoading || racksQ.isLoading,
    error: almacenesQ.error ?? zonasQ.error ?? racksQ.error,
  }
}
