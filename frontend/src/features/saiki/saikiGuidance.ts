import { paths } from '@/paths'

const normalize = (text: string) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
export interface SaikiGuide { to: string; title: string; description: string }

/** Only known read-only screens. Never execute URLs or actions returned by a model. */
export function suggestedGuide(question: string): SaikiGuide | null {
  const text = normalize(question)
  if (/analisis de demanda|autogluon|mayor demanda|demanda proyectada|wape/.test(text))
    return { to: paths.analisis, title: 'Análisis de demanda', description: 'Aquí puedes comparar el historial, las proyecciones y la evaluación del modelo. Sigo disponible para explicarte los resultados.' }
  if (/sensor|temperatura|humedad|refrigera|grafico|monitoreo|incidente/.test(text))
    return { to: paths.monitoreo, title: 'Monitoreo de sensores', description: 'Abre un equipo para ver su ubicación, lecturas e historial. Puedes seguir preguntándome mientras lo revisas.' }
  if (/inventario|stock|existencia/.test(text))
    return { to: paths.inventario, title: 'Inventario', description: 'Aquí puedes revisar tus existencias. La mini ventana de Saiki te acompaña mientras navegas.' }
  if (/producto|catalogo/.test(text))
    return { to: paths.productos, title: 'Productos', description: 'Consulta el producto y sus datos registrados; sigo disponible para tus preguntas.' }
  return null
}

export function requestsNavigation(question: string): boolean {
  return /\b(ve|vamos|ir|abre|abrir|muestra|muestrame|lleva|llevame|navega)\b|\bquiero ver\b/.test(normalize(question))
}

export function voiceCommand(text: string): 'pause' | 'exit' | null {
  const normalized = normalize(text).replace(/[.,!?¿¡]/g, '').trim()
  if (/^(saiki )?(pausa|pausar|pausa la voz|pausa la sesion)$/.test(normalized)) return 'pause'
  if (/^(saiki )?(salir|sal de la voz|cerrar voz|cierra la voz|terminar sesion de voz)$/.test(normalized)) return 'exit'
  return null
}

/** Remove model reasoning and formatting that is not useful to speech synthesis. */
export function cleanAnswer(text: string): string {
  return text.replace(/<think>[\s\S]*?<\/think>/gi, '').replace(/<think>[\s\S]*$/gi, '').trim()
}
export function speechText(text: string): string {
  return cleanAnswer(text).replace(/```[\s\S]*?```/g, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/[*#`|]/g, '').trim()
}
