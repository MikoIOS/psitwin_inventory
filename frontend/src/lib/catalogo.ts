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

export const TIPOS_ZONA: TipoZona[] = [
  {
    nombre: 'Productos Frescos y Refrigerados',
    refrigerada: true,
    familias: {
      Lácteos: ['Leches y alternativas vegetales', 'Quesos (frescos, madurados, untables)', 'Yogures y postres lácteos'],
      'Carnes y Aves': ['Carne de res (vacuno)', 'Carne de cerdo', 'Pollo y aves de corral'],
      'Embutidos y Fiambrería': ['Jamones y fiambres cocidos', 'Chorizos y salames (curados)'],
    },
  },
  {
    nombre: 'Almacén Seco (Abarrotes / Despensa)',
    refrigerada: false,
    familias: {
      'Granos y Pastas': ['Arroz y legumbres (lentejas, frijoles)', 'Pastas secas (fideos, pastas rellenas secas)', 'Harinas y sémolas'],
      'Aceites y Condimentos': ['Aceites de cocina (girasol, oliva)', 'Salsas preparadas (kétchup, mayonesa, tomate)', 'Especias y sazonadores'],
      'Conservas y Enlatados': ['Conservas de pescado (atún, sardinas)', 'Vegetales enlatados (maíz, arvejas)'],
    },
  },
  {
    nombre: 'Bebidas',
    refrigerada: false,
    familias: {
      'Bebidas Analcohólicas (Sin alcohol)': ['Aguas (mineral, con gas, sin gas)', 'Gaseosas y refrescos', 'Jugos y néctares de fruta'],
      'Bebidas Alcohólicas': ['Cervezas', 'Vinos y Espumantes', 'Destilados y Licores (ron, whisky, vodka)'],
    },
  },
  {
    nombre: 'Congelados',
    refrigerada: true,
    familias: {
      'Alimentos Congelados': ['Vegetales y frutas congeladas', 'Platos preparados (pizzas, hamburguesas)', 'Helados y postres fríos'],
    },
  },
]

export const tipoZona = (nombre: string | null | undefined) => TIPOS_ZONA.find((t) => t.nombre === nombre)
/** Sugerencia de «refrigerada» para un tipo del catálogo (tipos fuera del catálogo → false). */
export const zonaRefrigerada = (tipo: string | null | undefined) => tipoZona(tipo)?.refrigerada ?? false
export const familiasDe = (tipo: string | null | undefined) => Object.keys(tipoZona(tipo)?.familias ?? {})
export const categoriasDe = (tipo: string | null | undefined, familia: string) => tipoZona(tipo)?.familias[familia] ?? []

/** Tipo de zona del catálogo al que pertenece una familia (para reabrir la cascada al editar un producto). */
export const tipoDeFamilia = (familia: string | null | undefined) =>
  TIPOS_ZONA.find((t) => familia != null && familia in t.familias)?.nombre ?? ''
