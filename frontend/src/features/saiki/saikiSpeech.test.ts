import { describe, it, expect, vi, afterEach } from 'vitest'
import { resilientSpeech } from './saikiSpeech'
import type { TtsProvider, TtsCallbacks } from './ttsProvider'
const provider = (id: string): TtsProvider => ({ id, available: () => true, voices: () => [{ id: 'em_alex', name: 'Kokoro em_alex', lang: 'es' }], subscribe: () => () => {}, cancel: vi.fn(), speak: vi.fn() })
afterEach(() => vi.useRealTimers())
describe('speech recovery', () => {
  it('recovers native synthesis failures locally and reports the actual voice', () => {
    const primary = provider('browser'), local = provider('local')
    const speech = resilientSpeech(primary, local)
    const listener = vi.fn(); speech.subscribe(listener)
    const callbacks = { start: vi.fn(), end: vi.fn(), error: vi.fn(), boundary: vi.fn() }
    speech.speak('Respuesta', { voiceId: '', rate: 1, volume: 1 }, callbacks)
    const native = vi.mocked(primary.speak).mock.calls[0]![2]
    native.error(); native.error()
    expect(local.speak).toHaveBeenCalledOnce()
    expect(vi.mocked(local.speak).mock.calls[0]![1].voiceId).toBe('em_alex')
    const fallback: TtsCallbacks = vi.mocked(local.speak).mock.calls[0]![2]
    fallback.start(); fallback.end()
    expect(callbacks.start).toHaveBeenCalledOnce(); expect(callbacks.end).toHaveBeenCalledOnce()
    expect(callbacks.error).not.toHaveBeenCalled()
    expect(listener).toHaveBeenCalledOnce()
    expect(speech.voices()[0]?.name).toBe('Kokoro em_alex')
    speech.cancel()
  })
  it('cancels stalled native speech and ignores late recovery after cancellation', () => {
    vi.useFakeTimers()
    const primary = provider('browser'), local = provider('local'), speech = resilientSpeech(primary, local)
    const callbacks = { start: vi.fn(), end: vi.fn(), error: vi.fn(), boundary: vi.fn() }
    speech.speak('Respuesta', { voiceId: '', rate: 1, volume: 1 }, callbacks)
    const native = vi.mocked(primary.speak).mock.calls[0]![2]
    speech.cancel(); native.error(); vi.advanceTimersByTime(9000)
    expect(local.speak).not.toHaveBeenCalled()
  })
})
