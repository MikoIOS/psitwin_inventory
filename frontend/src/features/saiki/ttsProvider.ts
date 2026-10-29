export interface TtsVoice { id: string; name: string; lang: string }
export interface TtsOptions { voiceId: string; rate: number; volume: number }
export interface TtsCallbacks { start(): void; boundary(level?: number): void; end(): void; error(): void }
export interface TtsProvider {
  readonly id: string
  available(): boolean
  voices(): TtsVoice[]
  subscribe(listener: () => void): () => void
  speak(text: string, options: TtsOptions, callbacks: TtsCallbacks): void
  cancel(): void
}
export function preferredVoice<T extends TtsVoice>(voices: T[], selected = ''): T | undefined {
  const spanish = voices.filter(v => /^es(?:-|$)/i.test(v.lang))
  return voices.find(v => v.id === selected)
    ?? spanish.find(v => /jorge/i.test(v.name) && /^es-MX$/i.test(v.lang))
    ?? spanish.find(v => /raul|raúl|andres|andrés|pablo|diego|gonzalo|tomas|tomás/i.test(v.name) && !/^es-ES$/i.test(v.lang))
    ?? spanish.find(v => /^es-MX$/i.test(v.lang))
    ?? spanish.find(v => !/^es-ES$/i.test(v.lang))
    ?? spanish.find(v => /pablo|alvaro|álvaro|jorge|raul|raúl|diego|gonzalo|tomas|tomás/i.test(v.name)) ?? spanish[0]
}
// Keep a strong reference until completion (some browsers otherwise lose events).
let browserUtterance: SpeechSynthesisUtterance | undefined
export const browserTts: TtsProvider = {
  id: 'web-speech',
  available: () => typeof window.speechSynthesis?.speak === 'function',
  voices: () => (window.speechSynthesis?.getVoices?.() ?? []).map(v => ({ id: v.voiceURI, name: v.name, lang: v.lang })),
  subscribe(listener) {
    window.speechSynthesis?.addEventListener?.('voiceschanged', listener)
    return () => window.speechSynthesis?.removeEventListener?.('voiceschanged', listener)
  },
  speak(text, options, callbacks) {
    const u = new SpeechSynthesisUtterance(text)
    browserUtterance = u
    const voices = window.speechSynthesis.getVoices?.() ?? []
    const chosen = preferredVoice(voices.map(v => ({ id: v.voiceURI, name: v.name, lang: v.lang })), options.voiceId)
    u.voice = voices.find(v => v.voiceURI === chosen?.id) ?? null
    u.lang = u.voice?.lang ?? 'es-PE'
    u.rate = 1; u.volume = options.volume
    u.onstart = () => { if (browserUtterance === u) callbacks.start() }
    u.onboundary = () => { if (browserUtterance === u) callbacks.boundary() }
    u.onend = () => { if (browserUtterance === u) { browserUtterance = undefined; callbacks.end() } }
    u.onerror = () => { if (browserUtterance === u) { browserUtterance = undefined; callbacks.error() } }
    window.speechSynthesis.resume?.()
    window.speechSynthesis.speak(u)
  },
  cancel() {
    if (browserUtterance) browserUtterance.onstart = browserUtterance.onend = browserUtterance.onerror = browserUtterance.onboundary = null
    browserUtterance = undefined
    window.speechSynthesis?.cancel()
  },
}

/** Saiki has one fixed voice; never substitute a differently named voice. */
export const jorgeTts: TtsProvider = {
  ...browserTts,
  id: 'jorge-browser',
  voices: () => browserTts.voices().filter(v => /\bjorge\b/i.test(v.name) && /^es-MX$/i.test(v.lang)),
  speak(text, options, callbacks) {
    const jorge = jorgeTts.voices()[0]
    if (!jorge) { callbacks.error(); return }
    browserTts.speak(text, { ...options, voiceId: jorge.id, rate: 1, volume: 1 }, callbacks)
  },
}

/** Automatic installed Spanish voice; Jorge is preferred, never falsely named. */
export const saikiTts: TtsProvider = {
  ...browserTts,
  id: 'saiki-browser',
  voices: () => browserTts.voices().filter(v => /^es(?:-|$)/i.test(v.lang)),
  speak(text, _options, callbacks) {
    const voice = preferredVoice(saikiTts.voices())
    browserTts.speak(text, { voiceId: voice?.id ?? '', rate: 1, volume: 1 }, callbacks)
  },
}
