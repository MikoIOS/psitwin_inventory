export interface RecognitionResultEvent {
  resultIndex: number
  results: { length: number; [index: number]: { isFinal: boolean; [index: number]: { transcript: string } } }
}
export interface Recognition {
  onlevel?: ((level: number) => void) | null
  onprocessing?: (() => void) | null
  lang: string
  continuous: boolean
  interimResults: boolean
  onstart: (() => void) | null
  onend: (() => void) | null
  onerror: ((event: { error: string }) => void) | null
  onresult: ((event: RecognitionResultEvent) => void) | null
  start(): void
  abort(): void
  finish?(): void
}
interface NativeRecognition extends Recognition { stop(): void; onspeechend?: (() => void) | null }
type NativeConstructor = new () => NativeRecognition
export function nativeRecognitionConstructor(): NativeConstructor | undefined {
  const host = globalThis as typeof globalThis & { SpeechRecognition?: NativeConstructor; webkitSpeechRecognition?: NativeConstructor }
  return host.SpeechRecognition ?? host.webkitSpeechRecognition
}

/** Collect final segments once, allowing a short pause within the same turn. */
export class BrowserRecognition implements Recognition {
  lang = 'es-MX'; continuous = true; interimResults = false
  onstart: (() => void) | null = null
  onend: (() => void) | null = null
  onprocessing: (() => void) | null = null
  onerror: Recognition['onerror'] = null
  onresult: Recognition['onresult'] = null
  private native?: NativeRecognition
  private final = new Map<number, string>()
  private timer?: ReturnType<typeof setTimeout>
  private aborted = false
  private submitted = false
  start() {
    const Constructor = nativeRecognitionConstructor()
    if (!Constructor) throw new Error('speech-unavailable')
    const native = new Constructor()
    this.native = native
    native.lang = this.lang
    native.continuous = true
    native.interimResults = true
    native.onstart = () => { if (!this.aborted) this.onstart?.() }
    native.onerror = event => { if (!this.aborted) this.onerror?.(event) }
    native.onresult = event => {
      if (this.aborted || this.submitted) return
      clearTimeout(this.timer)
      let interim = false
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i]
        if (result?.isFinal) this.final.set(i, result[0]?.transcript ?? '')
        else interim = true
      }
      if (!interim && this.final.size) this.timer = setTimeout(() => this.submit(), 800)
    }
    native.onspeechend = () => {
      if (this.aborted || this.submitted) return
      this.onprocessing?.()
      clearTimeout(this.timer)
      this.timer = setTimeout(() => {
        if (!this.aborted && !this.submitted) {
          try { native.stop() } catch { /* Recognition may already have ended. */ }
        }
      }, 800)
    }
    native.onend = () => {
      if (this.aborted) return
      this.submit()
      if (!this.aborted) this.onend?.()
    }
    native.start()
  }
  private submit() {
    clearTimeout(this.timer)
    if (this.aborted || this.submitted || !this.final.size) return
    this.submitted = true
    const transcript = [...this.final.entries()].sort(([a], [b]) => a - b).map(([, text]) => text).join(' ').trim()
    if (transcript) this.onresult?.({ resultIndex: 0, results: { length: 1, 0: { isFinal: true, 0: { transcript } } } })
  }
  finish() { this.native?.stop() }
  abort() {
    this.aborted = true
    clearTimeout(this.timer)
    if (this.native) {
      this.native.onstart = this.native.onend = this.native.onspeechend = null
      this.native.onerror = this.native.onresult = null
      this.native.abort()
    }
  }
}
