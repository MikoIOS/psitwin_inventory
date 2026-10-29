import { useEffect, useRef, useState } from 'react'
import { intelligibleInput } from './saikiInput'
import { preferredVoice, type TtsOptions, type TtsProvider } from './ttsProvider'
import { saikiSpeech } from './saikiSpeech'
import { LocalRecognition, unlockLocalAudio } from './localVoice'
import { BrowserRecognition, nativeRecognitionConstructor, type Recognition } from './browserRecognition'

type Engine = 'browser' | 'local'
const defaults = { voiceId: '', rate: 1, volume: 1, enabled: true, sensorAlerts: false, sttEngine: 'local' as Engine, ttsEngine: 'browser' as Engine }
function loadPreferences(key: string) {
  try {
    const saved = JSON.parse(localStorage.getItem(key) ?? '{}') as Partial<typeof defaults>
    return { voiceId: typeof saved.voiceId === 'string' && saved.voiceId ? saved.voiceId : defaults.voiceId,
      rate: 1,
      volume: typeof saved.volume === 'number' ? Math.max(0, Math.min(1, saved.volume)) : 1,
      enabled: saved.enabled !== false, sensorAlerts: saved.sensorAlerts === true,
      sttEngine: 'local' as const,
      ttsEngine: 'browser' as const }
  } catch { return defaults }
}

/** One opt-in voice session. Recognition never runs during a request or playback. */
export function useSaikiVoice(onText: (text: string) => void, preferencesKey = 'psitwin.saiki.voice', provider?: TtsProvider, recognitionConstructor?: new () => Recognition) {
  const [preferences, setPreferences] = useState(() => loadPreferences(preferencesKey))
  const tts = provider ?? saikiSpeech
  const ttsRef = useRef(tts)
  ttsRef.current = tts
  const preferenceRef = useRef(preferences)
  preferenceRef.current = preferences
  const [runtimeEngine, setRuntimeEngine] = useState<Engine>(typeof MediaRecorder !== 'undefined' && typeof navigator.mediaDevices?.getUserMedia === 'function' ? 'local' : 'browser')
  const fallbackUsed = useRef(false)
  const [voices, setVoices] = useState(() => tts.voices())
  const [active, setActive] = useState(false)
  const [paused, setPaused] = useState(false)
  const [listening, setListening] = useState(false)
  const [requesting, setRequesting] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [preparing, setPreparing] = useState(false)
  const [error, setError] = useState('')
  const [voiceEnabled, setVoiceEnabled] = useState(preferences.enabled)
  const enabled = useRef(preferences.enabled)
  const [audioLevel, setAudioLevel] = useState(0)
  const callback = useRef(onText)
  callback.current = onText
  const recognition = useRef<Recognition | null>(null)
  const utterance = useRef<object | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const speechTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const flags = useRef({ active: false, paused: false, busy: false, speaking: false, mounted: true })
  const Constructor = recognitionConstructor ?? (runtimeEngine === 'browser'
    ? nativeRecognitionConstructor() ? BrowserRecognition : undefined
    : typeof MediaRecorder !== 'undefined' && typeof navigator.mediaDevices?.getUserMedia === 'function' ? LocalRecognition : undefined)

  function stopRecognition() {
    clearTimeout(timer.current)
    const r = recognition.current
    recognition.current = null
    if (r) { r.onlevel = null; r.onstart = null; r.onprocessing = null; r.onend = null; r.onerror = null; r.onresult = null; r.abort() }
    if (flags.current.mounted) setListening(false)
    if (flags.current.mounted) setTranscribing(false)
    if (flags.current.mounted) setRequesting(false)
  }
  function cancelSpeech() {
    clearTimeout(speechTimer.current)
    utterance.current = null
    ttsRef.current.cancel()
    flags.current.speaking = false
    if (flags.current.mounted) setSpeaking(false)
    if (flags.current.mounted) setPreparing(false)
    if (flags.current.mounted) setAudioLevel(0)
  }
  function eligible() {
    const f = flags.current
    return f.mounted && f.active && !f.paused && !f.busy && !f.speaking
  }
  function schedule() {
    clearTimeout(timer.current)
    if (eligible()) timer.current = setTimeout(beginRecognition, 450)
  }
  function beginRecognition() {
    if (!Constructor || !eligible() || recognition.current) return
    const r: Recognition = new Constructor()
    recognition.current = r
    setRequesting(true)
    r.lang = 'es-MX'
    r.continuous = true
    r.interimResults = false
    r.onlevel = level => { if (recognition.current === r && eligible()) setAudioLevel(level) }
    r.onstart = () => { if (recognition.current === r) { setRequesting(false); setListening(true); setTranscribing(false) } }
    r.onprocessing = () => { if (recognition.current === r) { setListening(false); setTranscribing(true) } }
    r.onend = () => {
      if (recognition.current !== r) return
      recognition.current = null
      setRequesting(false)
      setListening(false)
      setTranscribing(false)
      schedule() // Browsers end recognition after silence; the opt-in session stays open.
    }
    r.onerror = e => {
      if (recognition.current !== r) return
      if (e.error === 'no-speech' || e.error === 'aborted') return
      if (!recognitionConstructor && runtimeEngine === 'browser' && !fallbackUsed.current && ['network', 'service-not-allowed', 'language-not-supported'].includes(e.error) && typeof MediaRecorder !== 'undefined' && typeof navigator.mediaDevices?.getUserMedia === 'function') {
        fallbackUsed.current = true
        stopRecognition()
        setError('El reconocimiento del navegador falló; usando transcripción local.')
        setRuntimeEngine('local')
        return
      }
      if (!recognitionConstructor && runtimeEngine === 'local' && !fallbackUsed.current && nativeRecognitionConstructor() && ['local-unavailable', 'network', 'unsupported-audio', 'timeout'].includes(e.error)) {
        fallbackUsed.current = true
        stopRecognition()
        setError('El transcriptor local no respondió; usando reconocimiento del navegador.')
        setRuntimeEngine('browser')
        return
      }
      flags.current.paused = true
      setPaused(true)
      setError(e.error === 'not-allowed' || e.error === 'service-not-allowed'
        ? 'El micrófono no tiene permiso. Habilítalo en el navegador y pulsa Reanudar.'
        : e.error === 'audio-capture' || e.error === 'device-unavailable'
        ? 'No se pudo abrir el micrófono. Comprueba que esté conectado y disponible y pulsa Reanudar.'
        : e.error === 'session-expired' ? 'Tu sesión expiró. Inicia sesión nuevamente para usar la voz local.'
        : e.error === 'forbidden' ? 'Tu sesión no tiene permiso para usar la voz local.'
        : e.error === 'busy' ? 'El motor local está ocupado. Pulsa Reanudar para intentarlo de nuevo.'
        : e.error === 'unsupported-audio' ? 'El formato de audio no es compatible con el transcriptor local.'
        : e.error === 'timeout' ? 'La transcripción tardó demasiado. Pulsa Reanudar o cambia el motor de reconocimiento.'
        : e.error === 'network' ? 'No se pudo conectar al servicio de reconocimiento. Revisa la conexión o elige el motor local.'
        : runtimeEngine === 'browser' ? 'El reconocimiento del navegador no está disponible. Puedes elegir el motor local o continuar por texto.'
        : 'No se pudo transcribir con el motor local. Revisa el diagnóstico de voz del servidor o elige reconocimiento del navegador.')
      stopRecognition()
    }
    r.onresult = e => {
      if (!eligible() || recognition.current !== r) return
      const parts: string[] = []
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const result = e.results[i]
        if (result?.isFinal && result[0]?.transcript) parts.push(result[0].transcript)
      }
      const text = parts.join(' ').trim()
      if (!intelligibleInput(text)) return
      flags.current.busy = true
      stopRecognition()
      callback.current(text)
    }
    try { r.start() } catch {
      stopRecognition()
      flags.current.paused = true
      setPaused(true)
      setError('El micrófono no está disponible. Pulsa Reanudar para volver a intentarlo.')
    }
  }
  function start() {
    unlockLocalAudio()
    if (globalThis.isSecureContext === false) { setError('El micrófono requiere HTTPS o localhost.'); return }
    if (!Constructor) { setError('Este navegador no admite reconocimiento de voz. Puedes seguir por texto.'); return }
    if (!enabled.current) toggleVoice()
    flags.current.active = true
    flags.current.paused = false
    setActive(true)
    setPaused(false)
    setError('')
    beginRecognition()
  }
  function pause() {
    flags.current.paused = true
    setPaused(true)
    stopRecognition()
    cancelSpeech()
  }
  function resume() {
    unlockLocalAudio()
    setError('')
    flags.current.paused = false
    setPaused(false)
    beginRecognition()
  }
  function exit() {
    flags.current.active = false
    flags.current.paused = false
    setActive(false)
    setPaused(false)
    setError('')
    stopRecognition()
    cancelSpeech()
  }
  function hold() {
    flags.current.busy = true
    stopRecognition()
    cancelSpeech()
  }
  function interrupt() {
    cancelSpeech()
    beginRecognition()
  }
  function release() {
    flags.current.busy = false
    schedule()
  }
  function speak(text: string) {
    if (!tts.available() || !text.trim() || !enabled.current) return
    if (tts.id === 'jorge-browser' && !tts.voices().length) {
      setError('Jorge (México) no está disponible en este navegador. La respuesta sigue disponible por texto.')
      return
    }
    stopRecognition()
    cancelSpeech()
    // Prefer sentence boundaries; keep each local inference bounded.
    const chunks: string[] = []
    let remaining = text.trim()
    while (remaining.length > 240) {
      const space = remaining.lastIndexOf(' ', 240)
      const punctuation = [...remaining.slice(0, 240).matchAll(/[.!?;:]\s/g)].at(-1)?.index
      const boundary = punctuation != null && punctuation > 60 ? punctuation + 1 : space > 80 ? space : 240
      chunks.push(remaining.slice(0, boundary))
      remaining = remaining.slice(boundary).trim()
    }
    if (remaining) chunks.push(remaining)
    flags.current.speaking = true
    setPreparing(true)
    function next() {
      clearTimeout(speechTimer.current)
      const chunk = chunks.shift()
      if (!chunk) { flags.current.speaking = false; setPreparing(false); setSpeaking(false); setAudioLevel(0); schedule(); return }
      const u = {}
      utterance.current = u
      setSpeaking(false)
      setPreparing(true)
      const fail = () => {
        if (utterance.current !== u) return
        chunks.length = 0
        utterance.current = null
        tts.cancel()
        setError('No se pudo reproducir la voz. La respuesta sigue disponible por texto.')
        next()
      }
      speechTimer.current = setTimeout(fail, tts.id === 'saiki-auto' || preferences.ttsEngine === 'local' ? 120_000 : 15_000)
      try { tts.speak(chunk, preferenceRef.current, {
        start: () => { if (utterance.current === u) { clearTimeout(speechTimer.current); speechTimer.current = setTimeout(fail, 90_000); setError(''); setPreparing(false); setSpeaking(true); setAudioLevel(0) } },
        boundary: level => { if (utterance.current === u) setAudioLevel(previous => level ?? (previous > .5 ? .3 : .8)) },
        end: () => { if (utterance.current !== u) return; utterance.current = null; setAudioLevel(0); next() },
        error: fail,
      }) } catch { fail() }
    }
    next()
  }
  useEffect(() => {
    if (eligible()) beginRecognition()
  }, [runtimeEngine])
  useEffect(() => {
    flags.current.mounted = true
    return () => {
      flags.current.mounted = false
      flags.current.active = false
      stopRecognition()
      cancelSpeech()
    }
  }, [])
  useEffect(() => {
    const refresh = () => setVoices(tts.voices().sort((a, b) => Number(b.lang.toLowerCase().startsWith('es')) - Number(a.lang.toLowerCase().startsWith('es')) || a.name.localeCompare(b.name)))
    refresh()
    return tts.subscribe(refresh)
  }, [tts])
  function configure(patch: Partial<TtsOptions> & { sensorAlerts?: boolean; sttEngine?: Engine; ttsEngine?: Engine }) {
    if (patch.sttEngine || patch.ttsEngine) {
      if (flags.current.active) pause()
      else { stopRecognition(); cancelSpeech() }
    }
    setPreferences(previous => {
      const updated = { ...previous, ...(patch.ttsEngine ? { voiceId: '' } : {}), ...patch, rate: 1 }
      preferenceRef.current = updated
      try { localStorage.setItem(preferencesKey, JSON.stringify(updated)) } catch { /* memory fallback */ }
      return updated
    })
  }
  function toggleVoice() {
    unlockLocalAudio()
    enabled.current = !enabled.current
    setVoiceEnabled(enabled.current)
    setPreferences(previous => {
      const updated = { ...previous, enabled: enabled.current }
      try { localStorage.setItem(preferencesKey, JSON.stringify(updated)) } catch { /* memory fallback */ }
      return updated
    })
    if (!enabled.current) { cancelSpeech(); schedule() }
  }
  function replay(text: string) {
    unlockLocalAudio()
    if (!enabled.current) toggleVoice()
    speak(text)
  }
  function finishRecording() { recognition.current?.finish?.() }
  const selectedVoice = preferredVoice(voices, provider ? preferences.voiceId : '')
  return { active, paused, listening, requesting, transcribing, speaking, preparing, error: error || (!Constructor ? globalThis.isSecureContext === false ? 'El micrófono necesita HTTPS o localhost; esta dirección no permite capturar audio.' : 'Este navegador no ofrece captura de micrófono. Abre Saiki en Chrome o Edge actualizado.' : ''), voiceEnabled, toggleVoice, audioLevel, recognitionEngine: runtimeEngine, canListen: !!Constructor, canSpeak: tts.available(), voices, selectedVoice, preferences, configure, finishRecording,
    start, pause, resume, exit, hold, release, speak, replay, interrupt, unlockAudio: unlockLocalAudio,
    isEnabled: () => flags.current.active && !flags.current.paused }
}
