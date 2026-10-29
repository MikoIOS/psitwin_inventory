import { afterEach, describe, expect, it, vi } from 'vitest'
import { saikiApi } from './saiki'

describe('Saiki progress transport', () => {
  afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers() })
  it('reads progress and completes with the final answer', async () => {
    const encoder = new TextEncoder()
    const body = new ReadableStream({ start(c) {
      c.enqueue(encoder.encode(JSON.stringify({ type: 'progress', phase: 'consulting', detail: 'Consultando información', timeout_ms: 10000 }) + '\n'))
      c.enqueue(encoder.encode(JSON.stringify({ type: 'result', result: { answer: 'Tienes 2 operarios.', model: 'backend', warnings: [] } }) + '\n')); c.close()
    } })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body)))
    const progress = vi.fn()
    expect((await saikiApi.ask({ question: '¿Cuántos operarios tengo?' }, undefined, progress)).answer).toContain('2 operarios')
    expect(progress).toHaveBeenCalledWith(expect.objectContaining({ phase: 'consulting' }))
  })
  it('aborts a transport that does not do useful work for 10 seconds', async () => {
    vi.useFakeTimers()
    let signal!: AbortSignal
    vi.stubGlobal('fetch', vi.fn((_url, options: RequestInit) => new Promise((_resolve, reject) => {
      signal = options.signal as AbortSignal
      signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')))
    })))
    const pending = saikiApi.ask({ question: 'Consulta' })
    const check = expect(pending).rejects.toMatchObject({ status: 504 })
    await vi.advanceTimersByTimeAsync(10001)
    await check
    expect(signal.aborted).toBe(true)
  })
})
