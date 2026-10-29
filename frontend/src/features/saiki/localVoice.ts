import { api, API_URL } from '@/api/client'
import { getToken } from '@/lib/storage'
import type { TtsProvider, TtsVoice } from './ttsProvider'

async function audioRequest(path: string, body: BodyInit, type: string, signal: AbortSignal) {
  const requestSignal = AbortSignal.any([signal, AbortSignal.timeout(125_000)])
  const response = await fetch(`${API_URL}/saiki/voice/${path}`, { method: 'POST', signal: requestSignal, body,
    headers: { Authorization: `Bearer ${getToken() ?? ''}`, 'Content-Type': type } })
  if (!response.ok) {
    console.warn('[saiki-voice]', path, response.status) // Never log audio, tokens or transcripts.
    const code = response.status === 401 ? 'session-expired' : response.status === 403 ? 'forbidden'
      : response.status === 429 ? 'busy' : response.status === 415 ? 'unsupported-audio'
      : response.status === 408 || response.status === 504 ? 'timeout'
      : response.status === 422 && path === 'transcribe' ? 'no-speech' : 'local-unavailable'
    throw new Error(code)
  }
  return response
}

let controller: AbortController | undefined
let playback: HTMLAudioElement | undefined
let objectUrl: string | undefined
let frame = 0
let context: AudioContext | undefined
let localVoices: TtsVoice[] = [{ id: 'em_santa', name: 'Kokoro em_santa', lang: 'es' }, { id: 'em_alex', name: 'Kokoro em_alex', lang: 'es' }]
export function unlockLocalAudio() {
  try { context ??= new AudioContext(); void context.resume() } catch { /* Playback reports its own error. */ }
}
export const localTts: TtsProvider = {
  id: 'kokoro-local',
  available: () => typeof Audio !== 'undefined',
  voices: () => localVoices,
  subscribe(listener) {
    let alive = true
    void api.get<{ voices: TtsVoice[] }>('/saiki/voice/config').then(config => {
      if (alive && Array.isArray(config.voices)) { localVoices = config.voices; listener() }
    }).catch(() => { /* A synthesis request reports the actionable error. */ })
    return () => { alive = false }
  },
  speak(text, options, callbacks) {
    localTts.cancel()
    const current = new AbortController()
    controller = current
    void (async () => {
      try {
        // Create/unlock the context within the initiating user interaction.
        context ??= new AudioContext()
        await context.resume()
        const response = await audioRequest('synthesize', JSON.stringify({ text,
          voice: ['em_santa', 'em_alex'].includes(options.voiceId) ? options.voiceId : 'em_santa', speed: options.rate }), 'application/json', current.signal)
        const blob = await response.blob()
        if (current.signal.aborted) return
        objectUrl = URL.createObjectURL(blob)
        const audio = new Audio(objectUrl)
        playback = audio
        audio.volume = options.volume
        const analyser = context.createAnalyser()
        analyser.fftSize = 256
        const source = context.createMediaElementSource(audio)
        source.connect(analyser); analyser.connect(context.destination)
        const values = new Uint8Array(analyser.fftSize)
        const update = () => {
          if (current.signal.aborted || audio.paused) return
          analyser.getByteTimeDomainData(values)
          const rms = Math.sqrt(values.reduce((sum, v) => sum + ((v - 128) / 128) ** 2, 0) / values.length)
          callbacks.boundary(Math.min(1, rms * 5))
          frame = requestAnimationFrame(update)
        }
        audio.onplaying = () => { callbacks.start(); update() }
        audio.onended = () => { if (!current.signal.aborted) { localTts.cancel(); callbacks.end() } }
        audio.onerror = () => { if (!current.signal.aborted) { localTts.cancel(); callbacks.error() } }
        await audio.play()
      } catch { if (!current.signal.aborted) { localTts.cancel(); callbacks.error() } }
    })()
  },
  cancel() {
    controller?.abort(); controller = undefined
    cancelAnimationFrame(frame)
    if (playback) { playback.onended = null; playback.onerror = null; playback.pause(); playback.removeAttribute('src'); playback.load() }
    playback = undefined
    if (objectUrl) URL.revokeObjectURL(objectUrl)
    objectUrl = undefined
  },
}

/** Local STT through our backend; never uses browser cloud recognition. */
export class LocalRecognition {
  lang = 'es'; continuous = false; interimResults = false
  onstart: (() => void) | null = null
  onend: (() => void) | null = null
  onlevel: ((level: number) => void) | null = null
  onprocessing: (() => void) | null = null
  onerror: ((event: { error: string }) => void) | null = null
  onresult: ((event: { resultIndex: number; results: { length: number; [index: number]: { isFinal: boolean; [index: number]: { transcript: string } } } }) => void) | null = null
  private stream: MediaStream | undefined
  private recorder?: MediaRecorder
  private controller = new AbortController()
  private timer?: ReturnType<typeof setTimeout>
  private silenceTimer?: ReturnType<typeof setInterval>
  private audioContext: AudioContext | undefined
  private stopMonitoring() {
    clearInterval(this.silenceTimer)
    const context = this.audioContext
    this.audioContext = undefined
    if (context) void context.close().catch(() => {})
  }
  private monitorSilence(stream: MediaStream) {
    // Manual send and the duration limit still work without audio analysis.
    try {
      const context = new AudioContext()
      this.audioContext = context
      const analyser = context.createAnalyser()
      analyser.fftSize = 2048
      context.createMediaStreamSource(stream).connect(analyser)
      void context.resume().catch(() => {})
      const samples = new Float32Array(analyser.fftSize)
      let heardSpeech = false
      let lastSpeech = Date.now()
      this.silenceTimer = setInterval(() => {
        if (context.state !== 'running') return
        analyser.getFloatTimeDomainData(samples)
        const rms = Math.sqrt(samples.reduce((sum, value) => sum + value * value, 0) / samples.length)
        this.onlevel?.(Math.min(1, rms * 8))
        if (rms > .008) { heardSpeech = true; lastSpeech = Date.now() }
        if (heardSpeech && Date.now() - lastSpeech >= 1500) this.finish()
      }, 100)
    } catch { this.stopMonitoring() }
  }
  start() {
    void (async () => {
      try {
        this.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, channelCount: { ideal: 1 }, sampleRate: { ideal: 16000 } }, video: false })
        if (this.controller.signal.aborted) { this.stream.getTracks().forEach(t => t.stop()); return }
        const mimeType = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/mp4'].find(t => MediaRecorder.isTypeSupported(t))
        const recorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : undefined)
        this.recorder = recorder
        recorder.onerror = () => {
          if (this.controller.signal.aborted) return
          this.onerror?.({ error: 'audio-capture' })
          this.abort()
        }
        const chunks: BlobPart[] = []
        recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data) }
        recorder.onstop = () => {
          const stream = this.stream; this.stream = undefined
          stream?.getTracks().forEach(t => t.stop())
          clearTimeout(this.timer)
          this.stopMonitoring()
          if (this.controller.signal.aborted) return
          this.onprocessing?.()
          void (async () => {
            try {
              const type = recorder.mimeType || mimeType || 'audio/webm'
              const response = await audioRequest('transcribe', new Blob(chunks, { type }), type, this.controller.signal)
              const { text } = await response.json() as { text: string }
              if (!this.controller.signal.aborted && text.trim()) this.onresult?.({ resultIndex: 0, results: { length: 1, 0: { isFinal: true, 0: { transcript: text } } } })
            } catch (error) {
              if (!this.controller.signal.aborted) this.onerror?.({ error: error instanceof Error && error.name === 'TimeoutError' ? 'timeout' : error instanceof TypeError ? 'network' : error instanceof Error ? error.message : 'local-unavailable' })
            }
            finally { if (!this.controller.signal.aborted) this.onend?.() }
          })()
        }
        recorder.start(); this.monitorSilence(this.stream); this.onstart?.()
        this.timer = setTimeout(() => this.finish(), 30_000)
      } catch (error) {
        this.stopMonitoring()
        this.stream?.getTracks().forEach(t => t.stop())
        if (!this.controller.signal.aborted) {
          const name = error instanceof Error ? error.name : ''
          this.onerror?.({ error: name === 'NotAllowedError' || name === 'SecurityError' ? 'not-allowed' : name === 'NotFoundError' ? 'audio-capture' : 'device-unavailable' })
        }
      }
    })()
  }
  finish() { if (this.recorder?.state === 'recording') this.recorder.stop() }
  abort() {
    this.controller.abort(); clearTimeout(this.timer); this.stopMonitoring()
    this.finish(); this.stream?.getTracks().forEach(t => t.stop())
  }
}
