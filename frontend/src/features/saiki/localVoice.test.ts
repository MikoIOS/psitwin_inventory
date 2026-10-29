// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { LocalRecognition, localTts } from './localVoice'

describe('local voice transport', () => {
  afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); vi.clearAllMocks() })
  it('offers the two requested Spanish voices', () => {
    expect(localTts.voices().map(v => v.id)).toEqual(['em_santa', 'em_alex'])
    expect(localTts.id).toBe('kokoro-local')
  })
  it('submits after speech followed by silence and releases audio analysis', async () => {
    vi.useFakeTimers()
    let level = .1
    const close = vi.fn(async () => {})
    vi.stubGlobal('AudioContext', class {
      state = 'running'
      resume = async () => {}
      close = close
      createMediaStreamSource = () => ({ connect: vi.fn() })
      createAnalyser = () => ({ fftSize: 2048, getFloatTimeDomainData: (data: Float32Array) => data.fill(level) })
    })
    const stop = vi.fn()
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: async () => ({ getTracks: () => [{ stop }] }) } })
    vi.stubGlobal('MediaRecorder', class {
      static isTypeSupported = () => true
      mimeType = 'audio/webm'; state = 'inactive'
      ondataavailable?: (event: { data: Blob }) => void
      onstop?: () => void
      start() { this.state = 'recording' }
      stop() { this.state = 'inactive'; this.ondataavailable?.({ data: new Blob(['audio']) }); this.onstop?.() }
    })
    const fetcher = vi.fn(async () => ({ ok: true, json: async () => ({ text: 'Explica mis sensores' }) }))
    vi.stubGlobal('fetch', fetcher)
    const recognition = new LocalRecognition()
    const result = vi.fn()
    recognition.onresult = result
    recognition.start()
    await Promise.resolve()
    await vi.advanceTimersByTimeAsync(200)
    expect(fetcher).not.toHaveBeenCalled()
    level = 0
    await vi.advanceTimersByTimeAsync(1600)
    expect(result).toHaveBeenCalledOnce()
    expect(stop).toHaveBeenCalled()
    expect(close).toHaveBeenCalledOnce()
    recognition.abort()
  })
  it('stops a microphone granted after cancellation without submitting audio', async () => {
    let grant!: (stream: MediaStream) => void
    const stop = vi.fn()
    const fetcher = vi.fn()
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: () => new Promise<MediaStream>(resolve => { grant = resolve }) } })
    vi.stubGlobal('fetch', fetcher)
    const recognition = new LocalRecognition()
    recognition.start(); recognition.abort()
    grant({ getTracks: () => [{ stop }] } as unknown as MediaStream)
    await Promise.resolve(); await Promise.resolve()
    expect(stop).toHaveBeenCalledOnce()
    expect(fetcher).not.toHaveBeenCalled()
  })
  it('releases the microphone and reports recorder failures without submitting broken audio', async () => {
    const stop = vi.fn()
    let recorder!: { onerror?: () => void }
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: async () => ({ getTracks: () => [{ stop }] }) } })
    vi.stubGlobal('MediaRecorder', class {
      static isTypeSupported = () => true
      state = 'inactive'
      onerror?: () => void
      constructor() { recorder = this }
      start() { this.state = 'recording' }
      stop() { this.state = 'inactive' }
    })
    const fetcher = vi.fn()
    vi.stubGlobal('fetch', fetcher)
    const recognition = new LocalRecognition()
    const error = vi.fn()
    recognition.onerror = error
    recognition.start()
    await Promise.resolve()
    recorder.onerror?.()
    expect(error).toHaveBeenCalledWith({ error: 'audio-capture' })
    expect(stop).toHaveBeenCalled()
    expect(fetcher).not.toHaveBeenCalled()
  })
  it('records only after opt-in and sends audio to the authenticated local backend', async () => {
    const stop = vi.fn()
    let recorder!: FakeRecorder
    class FakeRecorder {
      static isTypeSupported = () => true
      mimeType = 'audio/webm'; state = 'inactive'
      ondataavailable?: (event: { data: Blob }) => void
      onstop?: () => void
      constructor() { recorder = this }
      start() { this.state = 'recording' }
      stop() { this.state = 'inactive'; this.ondataavailable?.({ data: new Blob(['test audio']) }); this.onstop?.() }
    }
    vi.stubGlobal('MediaRecorder', FakeRecorder)
    const getUserMedia = vi.fn(async () => ({ getTracks: () => [{ stop }] }))
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia } })
    const fetcher = vi.fn(async (_url: string, _options: RequestInit) => ({ ok: true, json: async () => ({ text: 'Consulta mi inventario' }) }))
    vi.stubGlobal('fetch', fetcher)
    const recognition = new LocalRecognition()
    const result = vi.fn()
    recognition.onresult = result
    expect(getUserMedia).not.toHaveBeenCalled()
    recognition.start()
    await vi.waitFor(() => expect(recorder.state).toBe('recording'))
    recognition.finish()
    await vi.waitFor(() => expect(result).toHaveBeenCalledOnce())
    expect(fetcher.mock.calls[0]?.[0]).toBe('/api/v1/saiki/voice/transcribe')
    expect(stop).toHaveBeenCalled()
    recognition.abort()
  })
  it.each([[401, 'session-expired'], [403, 'forbidden'], [415, 'unsupported-audio'], [422, 'no-speech'], [429, 'busy'], [503, 'local-unavailable'], [504, 'timeout']])('preserves HTTP %s as %s', async (status, code) => {
    const stop = vi.fn()
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: async () => ({ getTracks: () => [{ stop }] }) } })
    vi.stubGlobal('MediaRecorder', class {
      static isTypeSupported = () => true
      mimeType = ''; state = 'inactive'
      ondataavailable?: (event: { data: Blob }) => void
      onstop?: () => void
      start() { this.state = 'recording' }
      stop() { this.state = 'inactive'; this.ondataavailable?.({ data: new Blob(['fixture audio']) }); this.onstop?.() }
    })
    const warning = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const fetcher = vi.fn(async () => ({ ok: false, status }))
    vi.stubGlobal('fetch', fetcher)
    const recognition = new LocalRecognition()
    const error = vi.fn()
    recognition.onerror = error
    recognition.start()
    await Promise.resolve()
    recognition.finish()
    await vi.waitFor(() => expect(error).toHaveBeenCalledWith({ error: code }))
    expect(stop).toHaveBeenCalled()
    recognition.abort()
    warning.mockRestore()
  })
})
