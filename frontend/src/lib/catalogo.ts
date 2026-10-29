import catalogo from '../../../backend/app/knowledge/catalogo_alimentos.json'
/**
 * Catálogo fijo de alimentos: tipo de zona → familias → categorías.
 * El backend guarda `tipo_zona`, `familia` y `categoria` como texto libre, así que el catálogo vive aquí.
 * `Zona.refrigerada` la decide la empresa (campo real del backend); el tipo del catálogo solo SUGIERE el valor inicial.
 */
export interface TipoZona {
  nombre: string
  refrigerada: boolean
  familias: Record<string, string[]>
}

export const TIPOS_ZONA: TipoZona[] = catalogo


export const tipoZona = (nombre: string | null | undefined) => TIPOS_ZONA.find((t) => t.nombre === nombre)
/** Sugerencia de «refrigerada» para un tipo del catálogo (tipos fuera del catálogo → false). */
export const zonaRefrigerada = (tipo: string | null | undefined) => tipoZona(tipo)?.refrigerada ?? false
export const familiasDe = (tipo: string | null | undefined) => Object.keys(tipoZona(tipo)?.familias ?? {})
export const categoriasDe = (tipo: string | null | undefined, familia: string) => tipoZona(tipo)?.familias[familia] ?? []

/** Tipo de zona del catálogo al que pertenece una familia (para reabrir la cascada al editar un producto). */
export const tipoDeFamilia = (familia: string | null | undefined) =>
  TIPOS_ZONA.find((t) => familia != null && familia in t.familias)?.nombre ?? ''
