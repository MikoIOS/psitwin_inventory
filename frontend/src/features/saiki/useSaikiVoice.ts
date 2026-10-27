import { useEffect, useRef, useState } from 'react'

interface Recognition {
  lang: string
  onstart: (() => void) | null
  onend: (() => void) | null
  onerror: (() => void) | null
  onresult: ((event: { results: { [index: number]: { [index: number]: { transcript: string } } } }) => void) | null
  start(): void
  abort(): void
}

export function useSaikiVoice(onText: (text: string) => void) {
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [error, setError] = useState('')
  const recognition = useRef<Recognition | null>(null)
  const api = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition }
  const Constructor = api.SpeechRecognition ?? api.webkitSpeechRecognition
  useEffect(() => () => { recognition.current?.abort(); window.speechSynthesis?.cancel() }, [])
  const listen = () => {
    if (listening) { recognition.current?.abort(); return }
    if (!Constructor) return
    window.speechSynthesis?.cancel()
    setError('')
    const r = new Constructor()
    recognition.current = r
    r.lang = 'es-PE'
    r.onstart = () => setListening(true)
    r.onend = () => setListening(false)
    r.onerror = () => { setListening(false); setError('No se pudo escuchar. Revisa el permiso del micrófono o escribe tu pregunta.') }
    r.onresult = e => { const text = e.results[0]?.[0]?.transcript; if (text) onText(text) }
    try { r.start() } catch { setError('El micrófono no está disponible.') }
  }
  const speak = (text: string) => {
    if (!window.speechSynthesis) return
    recognition.current?.abort()
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'es-PE'
    utterance.onstart = () => setSpeaking(true)
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    window.speechSynthesis.speak(utterance)
  }
  return { listening, speaking, error, canListen: !!Constructor, canSpeak: 'speechSynthesis' in window, listen, speak,
    stop: () => { recognition.current?.abort(); window.speechSynthesis?.cancel(); setSpeaking(false) } }
}
