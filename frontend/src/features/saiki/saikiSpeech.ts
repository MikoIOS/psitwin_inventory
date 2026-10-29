import { saikiTts, type TtsProvider } from './ttsProvider'
import { localTts } from './localVoice'

/** Recover from installed browser voices that fail at synthesis time. */
export function resilientSpeech(primary: TtsProvider, local: TtsProvider): TtsProvider {
  let localActive = false, generation = 0
  let timer: ReturnType<typeof setTimeout> | undefined
  const listeners = new Set<() => void>()
  return {
    id: 'saiki-auto',
    available: () => primary.available() || local.available(),
    voices: () => localActive ? local.voices().filter(v => v.id === 'em_alex') : primary.voices(),
    subscribe(listener) {
      listeners.add(listener)
      const first = primary.subscribe(listener), second = local.subscribe(listener)
      return () => { listeners.delete(listener); first(); second() }
    },
    speak(text, options, callbacks) {
      const current = ++generation
      let switched = false
      const fallback = () => {
        if (current !== generation || switched) return
        switched = true; clearTimeout(timer); primary.cancel()
        localActive = true; listeners.forEach(listener => listener())
        if (!local.available()) { callbacks.error(); return }
        local.speak(text, { ...options, voiceId: 'em_alex', rate: 1, volume: 1 }, {
          start: () => { if (current === generation) callbacks.start() },
          boundary: level => { if (current === generation) callbacks.boundary(level) },
          end: () => { if (current === generation) callbacks.end() },
          error: () => { if (current === generation) callbacks.error() },
        })
      }
      if (localActive || !primary.available()) { fallback(); return }
      timer = setTimeout(fallback, 8000)
      try {
        primary.speak(text, options, {
          start: () => { if (current === generation && !switched) { clearTimeout(timer); callbacks.start() } },
          boundary: level => { if (current === generation && !switched) callbacks.boundary(level) },
          end: () => { if (current === generation && !switched) { clearTimeout(timer); callbacks.end() } },
          error: fallback,
        })
      } catch { fallback() }
    },
    cancel() { generation++; clearTimeout(timer); primary.cancel(); local.cancel() },
  }
}

export const saikiSpeech = resilientSpeech(saikiTts, localTts)
