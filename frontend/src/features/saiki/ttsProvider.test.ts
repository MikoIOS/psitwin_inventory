import { afterEach, describe, expect, it, vi } from 'vitest'
import { browserTts, jorgeTts, saikiTts, preferredVoice } from './ttsProvider'

describe('real installed voice selection', () => {
  afterEach(() => vi.restoreAllMocks())
  const voices = [
    { id: 'female', name: 'Dalia', lang: 'es-MX' },
    { id: 'male', name: 'Microsoft Raul', lang: 'es-MX' },
    { id: 'jorge', name: 'Microsoft Jorge Online (Natural)', lang: 'es-MX' },
  ]
  it('prioritizes Jorge when actually exposed by the browser', () => {
    expect(preferredVoice(voices)?.id).toBe('jorge')
  })
  it('uses the actual fallback name without inventing Jorge', () => {
    expect(preferredVoice(voices.slice(0, 2))?.name).toBe('Microsoft Raul')
    expect(preferredVoice([])).toBeUndefined()
  })
  it('respects an explicit installed selection and ignores a removed voice', () => {
    expect(preferredVoice(voices, 'female')?.id).toBe('female')
    expect(preferredVoice(voices, 'removed')?.id).toBe('jorge')
  })
  it('prefers a real male Spanish fallback when no Latin American voices are installed', () => {
    expect(preferredVoice([{ id: 'helena', name: 'Microsoft Helena', lang: 'es-ES' },
      { id: 'pablo', name: 'Microsoft Pablo', lang: 'es-ES' }])?.name).toBe('Microsoft Pablo')
  })
  it('Saiki always uses Jorge even when an old preference selects a different voice', () => {
    vi.spyOn(browserTts, 'voices').mockReturnValue(voices)
    const speak = vi.spyOn(browserTts, 'speak').mockImplementation(() => {})
    const callbacks = { start: vi.fn(), boundary: vi.fn(), end: vi.fn(), error: vi.fn() }
    jorgeTts.speak('Respuesta nueva', { voiceId: 'female', rate: 2, volume: .1 }, callbacks)
    expect(speak).toHaveBeenCalledWith('Respuesta nueva', { voiceId: 'jorge', rate: 1, volume: 1 }, callbacks)
    expect(jorgeTts.voices().map(v => v.id)).toEqual(['jorge'])
  })
  it('automatically speaks with the actual installed Spanish voice if Jorge is absent', () => {
    vi.spyOn(browserTts, 'voices').mockReturnValue(voices.slice(0, 2))
    const speak = vi.spyOn(browserTts, 'speak').mockImplementation(() => {})
    const callbacks = { start: vi.fn(), boundary: vi.fn(), end: vi.fn(), error: vi.fn() }
    saikiTts.speak('Respuesta nueva', { voiceId: 'missing', rate: 1, volume: 0 }, callbacks)
    expect(speak).toHaveBeenCalledWith('Respuesta nueva', { voiceId: 'male', rate: 1, volume: 1 }, callbacks)
    expect(saikiTts.voices().some(v => /Jorge/.test(v.name))).toBe(false)
  })
  it('Saiki does not silently replace Jorge when she is unavailable', () => {
    vi.spyOn(browserTts, 'voices').mockReturnValue(voices.slice(0, 2))
    const speak = vi.spyOn(browserTts, 'speak').mockImplementation(() => {})
    const callbacks = { start: vi.fn(), boundary: vi.fn(), end: vi.fn(), error: vi.fn() }
    jorgeTts.speak('Respuesta nueva', { voiceId: 'male', rate: 1, volume: 1 }, callbacks)
    expect(speak).not.toHaveBeenCalled()
    expect(callbacks.error).toHaveBeenCalledOnce()
  })
})
