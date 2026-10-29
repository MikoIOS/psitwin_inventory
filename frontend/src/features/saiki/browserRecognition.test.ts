import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { BrowserRecognition, type RecognitionResultEvent } from './browserRecognition'

class Native {
  static current: Native
  lang = ''; continuous = false; interimResults = false
  onspeechend?: () => void
  onstart?: () => void
  onend?: () => void
  onresult?: (event: RecognitionResultEvent) => void
  onerror?: (event: { error: string }) => void
  constructor() { Native.current = this }
  start() { this.onstart?.() }
  stop() { this.onend?.() }
  abort = vi.fn()
}
const event = (text: string, isFinal = true): RecognitionResultEvent => ({ resultIndex: 0, results: { length: 1, 0: { isFinal, 0: { transcript: text } } } })
describe('browser recognition turns', () => {
  beforeEach(() => { vi.useFakeTimers(); vi.stubGlobal('SpeechRecognition', Native) })
  afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals() })
  it('waits for final Spanish text, deduplicates repeated result events and sends once', () => {
    const recognition = new BrowserRecognition()
    const result = vi.fn()
    recognition.onresult = result
    recognition.start()
    expect(Native.current.lang).toBe('es-MX')
    Native.current.onresult?.(event('Abre mi', false))
    vi.advanceTimersByTime(1500)
    expect(result).not.toHaveBeenCalled()
    Native.current.onresult?.(event('Abre mi inventario'))
    Native.current.onresult?.(event('Abre mi inventario'))
    vi.advanceTimersByTime(850)
    Native.current.onend?.()
    expect(result).toHaveBeenCalledExactlyOnceWith(event('Abre mi inventario'))
    recognition.abort()
  })
  it('collects multiple final segments and flushes when recognition ends', () => {
    const recognition = new BrowserRecognition()
    const result = vi.fn()
    recognition.onresult = result
    recognition.start()
    Native.current.onresult?.({ resultIndex: 1, results: { length: 2,
      0: { isFinal: true, 0: { transcript: 'Revisa mis sensores.' } },
      1: { isFinal: true, 0: { transcript: '¿Hay alertas?' } } } })
    recognition.finish()
    expect(result).toHaveBeenCalledExactlyOnceWith(event('Revisa mis sensores. ¿Hay alertas?'))
    recognition.abort()
  })
  it('discards pending and late results on interruption or unmount', () => {
    const recognition = new BrowserRecognition()
    const result = vi.fn()
    recognition.onresult = result
    recognition.start()
    const late = Native.current.onresult
    Native.current.onresult?.(event('Esto se cancela'))
    recognition.abort()
    late?.(event('Voz sintetizada de Saiki'))
    vi.advanceTimersByTime(1000)
    expect(result).not.toHaveBeenCalled()
    expect(Native.current.abort).toHaveBeenCalledOnce()
  })
  it('reports permission failures to the voice session', () => {
    const recognition = new BrowserRecognition()
    const error = vi.fn()
    recognition.onerror = error
    recognition.start()
    Native.current.onerror?.({ error: 'not-allowed' })
    expect(error).toHaveBeenCalledWith({ error: 'not-allowed' })
    recognition.abort()
  })
  it('ends capture after speech so browsers flush final text without sending partials', () => {
    const recognition = new BrowserRecognition()
    const result = vi.fn()
    recognition.onresult = result
    recognition.start()
    const stop = vi.spyOn(Native.current, 'stop').mockImplementation(() => {
      Native.current.onresult?.(event('Consulta mi inventario'))
      Native.current.onend?.()
    })
    Native.current.onresult?.(event('Consulta mi', false))
    Native.current.onspeechend?.()
    expect(result).not.toHaveBeenCalled()
    vi.advanceTimersByTime(850)
    expect(stop).toHaveBeenCalledOnce()
    expect(result).toHaveBeenCalledExactlyOnceWith(event('Consulta mi inventario'))
    recognition.abort()
  })

})
