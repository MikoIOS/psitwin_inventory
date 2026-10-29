/**
 * Saiki: asistente del backend (modelo local vía Ollama). Solo EMPRESA.
 * `ask` puede tardar: el modelo genera la respuesta en el servidor. 503 si Ollama no está disponible.
 */
import { api, API_URL, ApiError, forzarLogout } from './client'
import { getToken } from '@/lib/storage'

export interface SaikiProgress { phase: string; detail: string; timeout_ms?: number }

async function streamAnswer(body: SaikiAskBody, signal?: AbortSignal, onProgress?: (progress: SaikiProgress) => void): Promise<SaikiAnswer> {
  const controller = new AbortController()
  const abort = () => controller.abort(signal?.reason)
  signal?.addEventListener('abort', abort, { once: true })
  if (signal?.aborted) abort()
  let timedOut = false
  let timer: ReturnType<typeof setTimeout>
  let notice: ReturnType<typeof setTimeout> | undefined
  const arm = (ms: number) => {
    clearTimeout(timer); clearTimeout(notice)
    timer = setTimeout(() => { timedOut = true; controller.abort() }, ms)
    if (ms > 10000) notice = setTimeout(() => onProgress?.({ phase: 'waiting', detail: 'La operación lleva 10 segundos sin novedades. Puedes detenerla o seguir esperando.' }), 10000)
  }
  arm(10000)
  try {
    const response = await fetch(`${API_URL}/saiki/events`, { method: 'POST', signal: controller.signal,
      headers: { Authorization: `Bearer ${getToken() ?? ''}`, 'Content-Type': 'application/json', Accept: 'application/x-ndjson' }, body: JSON.stringify(body) })
    if (!response.ok) { if (response.status === 401) forzarLogout('expirada'); throw await ApiError.fromResponse(response) }
    if (!response.body) throw new Error('El servidor no devolvió una respuesta')
    const reader = response.body.getReader(), decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })
      let end: number
      while ((end = buffer.indexOf('\n')) >= 0) {
        const line = buffer.slice(0, end).trim(); buffer = buffer.slice(end + 1)
        if (!line) continue
        const event = JSON.parse(line) as { type: string; result?: SaikiAnswer; detail?: string; status?: number; phase?: string; timeout_ms?: number }
        if (event.type === 'result' && event.result) return event.result
        if (event.type === 'error') throw new ApiError(event.status ?? 503, event.detail ?? 'No fue posible consultar la información.', {}, event)
        if (event.type === 'progress') {
          arm(event.timeout_ms ?? 10000)
          onProgress?.({ phase: event.phase ?? 'thinking', detail: event.detail ?? 'Pensando', ...(event.timeout_ms ? { timeout_ms: event.timeout_ms } : {}) })
        }
      }
      if (done) throw new Error('La respuesta se interrumpió. Puedes reintentar.')
    }
  } catch (error) {
    if (timedOut) throw new ApiError(504, 'La consulta dejó de responder. Puedes reintentar.', {}, null)
    throw error
  } finally { clearTimeout(timer!); clearTimeout(notice); controller.abort(); signal?.removeEventListener('abort', abort) }
}

export interface SaikiAskBody {
  question: string
  context?: Record<string, unknown>
  history?: { role: 'user' | 'assistant'; content: string }[]
  id_inventario?: string
  id_producto?: string
  id_almacen?: string
  horizonte_dias?: 1 | 7 | 30 | 90
  id_zona?: string
  id_rack?: string
  id_nivel?: string
  page?: number
  page_size?: number
  id_dispositivo?: string
  sensor_horas?: number
}

export interface SaikiAnswer {
  answer: string
  model: string
  warnings: string[]
  data?: Record<string, unknown>
  visualization?: Record<string, unknown>
  sources?: string[]
}

export interface SaikiHealth {
  ready: boolean
  model: string
  detail?: string
}

export const saikiApi = {
  health: () => api.get<SaikiHealth>('/saiki/health'),
  ask: streamAnswer,
}
