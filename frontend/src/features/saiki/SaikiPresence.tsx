import { useEffect, useState, type CSSProperties } from 'react'
import { AgentAudioVisualizerWave } from '@/components/agents-ui/agent-audio-visualizer-wave'
import { Button } from '@/components/ui'
import { useSaikiSession } from './SaikiSession'
import { useMonitoreoVivo } from '@/api/monitoreo'

export function SaikiPresence({ compact = false }: { compact?: boolean }) {
  const session = useSaikiSession()
  const { voice } = session
  const alerts = useMonitoreoVivo()?.alertasAbiertas.length ?? 0
  const state = session.state === 'idle' && alerts > 0 ? 'alert' : session.state
  const [reduced, setReduced] = useState(false)
  useEffect(() => {
    if (!window.matchMedia) return
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduced(media.matches)
    update(); media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])
  return <div className={`saiki-presence ${compact ? 'saiki-presence--compact' : ''}`} data-state={state} style={{ '--saiki-level': voice.audioLevel ?? 0 } as CSSProperties}>
    <div className="saiki-presence__grid" aria-hidden="true" />
    <div className="relative z-10 flex items-center justify-between px-5 pt-4">
      <span className="font-mono text-[10px] tracking-[.26em] text-blue-200/80">PSITWIN / SAIKI</span>
      <span className="flex items-center gap-2 text-xs text-blue-100"><span className={`size-2 rounded-full ${voice.listening ? 'animate-pulse bg-emerald-300' : voice.paused ? 'bg-amber-300' : 'bg-blue-300'}`} />{voice.active ? voice.paused ? 'En pausa' : 'Sesión de voz' : 'Asistente personal'}</span>
    </div>
    <div className="saiki-presence__orb" aria-hidden="true">
      <div className="saiki-presence__ring" />
      <div className="saiki-presence__ring saiki-presence__ring--inner" />
      <div className="saiki-presence__glow" />
      <div className="saiki-presence__sphere" />
      {reduced ? <div className="h-px w-2/3 bg-gradient-to-r from-blue-400 to-fuchsia-400" /> :
        <AgentAudioVisualizerWave size={compact ? 'md' : 'xl'} state={session.state} volume={voice.audioLevel ?? 0} color="#758BFF" colorShift={1.2} lineWidth={2} className="relative z-10 aspect-square size-full" />}
      <span className="saiki-presence__wordmark">Ψ</span>
    </div>
    <div className="relative z-10 px-5 pb-5 text-center">
      {!compact && <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">Tu operación, en conversación.</h1>}
      <p role="status" className="mt-2 text-sm text-blue-100/80">{session.status}</p>
      {!compact && <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-blue-200/60">Pregunta, explora tus datos y sigue hablando con Saiki mientras navegas.</p>}
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {(session.pending || voice.speaking || voice.preparing || voice.listening || voice.transcribing) && <Button variant="secondary" onClick={session.stop}>Detener respuesta</Button>}
        {!voice.active ? <Button icon="mic" disabled={!voice.canListen} onClick={() => { voice.start(); session.setMinimized(false) }} className="!border-violet-400 !bg-violet-500 !text-white hover:!bg-violet-400">Iniciar conversación por voz</Button> : <>
          <Button variant="secondary" onClick={voice.paused ? voice.resume : voice.pause} className="!border-white/20 !bg-white/10 !text-white">{voice.paused ? 'Reanudar' : 'Pausar'}</Button>
          {(voice.speaking || voice.preparing) && <Button variant="ghost" onClick={voice.interrupt} className="!text-blue-100">Interrumpir y preguntar</Button>}
          {!compact && <Button variant="ghost" onClick={() => session.setMinimized(true)} className="!text-blue-100">Mini ventana</Button>}
          <Button variant="ghost" onClick={voice.exit} className="!text-blue-100">Salir de la voz</Button>
        </>}
      </div>
      {!voice.canListen && <p className="mt-2 text-xs text-blue-100">Voz no disponible en este navegador. Puedes seguir por texto.</p>}
      {!voice.active && <p className="mt-2 text-xs text-blue-100">{voice.preferences.sttEngine === 'browser' ? 'Al activar el micrófono aceptas usar el reconocimiento del navegador, que puede enviar audio a su proveedor.' : 'El audio se transcribe en el servidor de PsiTwin y no se guarda. Usa HTTPS o localhost y permite el micrófono.'}</p>}
      {voice.error && <p role="alert" className="mt-3 text-sm text-amber-200">{voice.error}</p>}
    </div>
  </div>
}
