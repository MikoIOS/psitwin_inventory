/**
 * Saiki: asistente del backend (modelo local vía Ollama). Solo EMPRESA.
 * `ask` puede tardar: el modelo genera la respuesta en el servidor. 503 si Ollama no está disponible.
 */
import { api } from './client'

export interface SaikiAskBody {
  question: string
  history?: { role: 'user' | 'assistant'; content: string }[]
  id_inventario?: string
  id_producto?: string
}

export interface SaikiAnswer {
  answer: string
  model: string
  warnings: string[]
}

export interface SaikiHealth {
  ready: boolean
  model: string
  detail?: string
}

export const saikiApi = {
  health: () => api.get<SaikiHealth>('/saiki/health'),
  ask: (body: SaikiAskBody) => api.post<SaikiAnswer>('/saiki/ask', body),
}
