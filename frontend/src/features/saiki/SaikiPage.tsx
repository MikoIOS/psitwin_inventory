import { ReporteSaiki } from './ReporteSaiki'
import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { saikiApi } from '@/api/saiki'
import { InventarioSelect, ProductoSelect } from '@/components/selects'
import { Badge, Button, Card, Field, Spinner, Textarea } from '@/components/ui'
import { cn } from '@/lib/cn'
import { SaikiSensors, useSaludo } from './SaikiSensors'
import { SaikiPresence } from './SaikiPresence'
import { SaikiEvidence } from './SaikiEvidence'
import { useSaikiSession } from './SaikiSession'
import { speechText } from './saikiGuidance'
import { useRol } from '@/auth/useRol'

const SUGGESTIONS = [
  { label: 'Revisar sensores', question: '¿Qué sensores presentan alertas críticas?' },
  { label: 'Resumen de inventario', question: 'Muéstrame el estado de mi inventario.' },
  { label: 'Revisar incidentes', question: 'Analiza el historial de incidentes de refrigeración y recomienda revisiones.' },
]

export default function SaikiPage() {
  const { esEmpresa } = useRol()
  const session = useSaikiSession()
  const { messages, pending, voice } = session
  const [question, setQuestion] = useState('')
  const greeting = useSaludo()
  const end = useRef<HTMLDivElement>(null)
  const health = useQuery({ queryKey: ['saiki', 'health'], queryFn: saikiApi.health, staleTime: 60_000, retry: false })
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }) }, [messages, pending])
  const submit = (event: FormEvent) => { event.preventDefault(); if (question.trim() && !pending) { void session.send(question); setQuestion('') } }
  return <div className="space-y-6">
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div><p className="label-stencil mb-1 text-fg-subtle">Asistente de tu operación</p><h2 className="text-2xl font-semibold tracking-tight">{greeting}.</h2><p className="mt-1 text-sm text-fg-muted">Tus datos, una explicación clara y una voz que te acompaña.</p></div>
      <Badge tone={health.data?.ready ? 'success' : 'neutral'}>{health.isPending ? 'Conectando con Saiki…' : health.data?.ready ? 'Saiki disponible' : 'Saiki no disponible'}</Badge>
    </div>
    {session.minimized && voice.active ? <Card><div className="flex flex-wrap items-center justify-between gap-3"><p>Tu conversación continúa en la mini ventana.</p><Button variant="secondary" onClick={() => session.setMinimized(false)}>Ampliar Saiki</Button></div></Card> : <SaikiPresence />}
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_19rem]">
      <Card padding="none" className="flex min-h-[30rem] flex-col overflow-hidden">
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-border p-4"><h2 className="font-semibold">Conversación</h2><div className="flex gap-2">{voice.canSpeak && <Button size="sm" variant="ghost" aria-pressed={voice.voiceEnabled ?? true} onClick={voice.toggleVoice}>Voz {voice.voiceEnabled === false ? 'desactivada' : 'activada'}</Button>}{(pending || voice.speaking) && <Button size="sm" variant="ghost" onClick={session.stop}>Detener respuesta</Button>}</div></header>
        <div className="max-h-[35rem] min-h-64 flex-1 space-y-4 overflow-y-auto p-4" aria-live="polite">
          {!messages.length && <div className="py-5"><p className="mb-4 text-sm text-fg-muted">Empieza por lo que necesitas revisar.</p><div className="flex flex-wrap gap-2">{SUGGESTIONS.map(item => <Button key={item.label} size="sm" variant="secondary" onClick={() => void session.send(item.question)}>{item.label} <span aria-hidden="true">↗</span></Button>)}</div><p className="mt-5 max-w-lg text-sm leading-relaxed text-fg-subtle">En modo voz, haz tu pregunta y espera la respuesta. Después Saiki vuelve a escucharte. La conversación sigue abierta al navegar.</p></div>}
          {messages.map((message, index) => <div key={index} className={cn('flex', message.de === 'usuario' ? 'justify-end' : 'justify-start')}>
            <div className={cn('max-w-[92%] rounded-2xl border px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap', message.de === 'usuario' ? 'border-blue-400/30 bg-blue-500/10' : message.de === 'error' ? 'border-danger/30 bg-danger-soft text-danger' : 'border-border bg-surface-2')} role={message.de === 'error' ? 'alert' : undefined}>
              <p className="mb-1 text-[10px] font-semibold tracking-widest text-fg-subtle uppercase">{message.de === 'usuario' ? 'Tú' : message.de === 'error' ? 'No se pudo consultar' : 'Saiki'}</p>
              <p>{message.texto}</p>
              {message.de === 'error' && !pending && <Button size="sm" variant="ghost" onClick={() => { const previous = messages.slice(0, index).reverse().find(m => m.de === 'usuario'); if (previous) void session.send(previous.texto) }}>Reintentar</Button>}
              {message.de === 'saiki' && voice.canSpeak && <div className="mt-2"><Button size="sm" variant="ghost" disabled={pending} onClick={() => voice.replay(speechText(message.texto))}>Escuchar respuesta</Button></div>}
              {message.avisos?.map(warning => <p key={warning} className="mt-2 text-xs text-fg-subtle">{warning}</p>)}
            </div>
          </div>)}
          {pending && <p role="status" className="flex items-center gap-2 text-sm text-fg-muted"><Spinner size="sm" label={session.status} /> {session.status}…</p>}
          <div ref={end} />
        </div>
        <ReporteSaiki />
        {voice.selectedVoice && <p className="px-4 pb-2 text-xs text-fg-muted">Voz disponible: {voice.selectedVoice.name}</p>}
        {voice.listening && voice.recognitionEngine === 'local' && <div className="px-4 pb-2 text-xs text-fg-muted"><label htmlFor="saiki-microphone-level">Entrada del micrófono</label><meter id="saiki-microphone-level" min={0} max={1} value={voice.audioLevel} className="ml-2" /><span className="ml-2">{voice.audioLevel > .02 ? 'Recibiendo sonido' : 'Esperando sonido'}</span></div>}
        <form onSubmit={submit} className="flex items-end gap-2 border-t border-border p-3">
          <Button type="button" icon="mic" iconOnly variant={voice.listening ? 'primary' : 'secondary'} aria-label={voice.active ? voice.paused ? 'Reanudar micrófono' : 'Pausar micrófono' : 'Activar micrófono'} aria-pressed={voice.listening} disabled={!voice.canListen || pending} onClick={voice.active ? voice.paused ? voice.resume : voice.pause : voice.start} />
          <Textarea aria-label="Pregunta para Saiki" rows={2} maxLength={1000} placeholder={voice.listening ? 'Te escucho. También puedes escribir…' : '¿Qué necesitas revisar?'} value={question} onChange={event => setQuestion(event.target.value)} onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); if (!pending && question.trim()) { void session.send(question); setQuestion('') } } }} />
          <Button type="submit" loading={pending} disabled={!question.trim()}>Enviar</Button>
        </form>
      </Card>
      <div className="space-y-4">
        {session.guide && <Card title="Siguiente paso" className="border-blue-400/30"><p className="mb-3 text-sm text-fg-muted">{session.guide.description}</p><Button variant="secondary" fullWidth onClick={() => session.openGuide(session.guide!)}>Ir a {session.guide.title} ↗</Button></Card>}
        <Card title="Contexto de la consulta" description="Opcional. Mantiene el producto seleccionado al navegar.">
          <div className="space-y-4">
            {session.sensorContext?.id_dispositivo && <div className="rounded-lg bg-blue-500/5 p-3 text-sm"><p>La conversación sigue el equipo que seleccionaste en los gráficos.</p><Button size="sm" variant="ghost" onClick={() => session.setSensorContext(undefined)}>Quitar equipo seleccionado</Button></div>}
            {Object.keys(session.inventoryContext ?? {}).length > 0 && <div className="rounded-lg border border-border p-3 text-sm"><p>Saiki utiliza la ubicación y los filtros de tu última vista de inventario o plano.</p><Button variant="ghost" size="sm" onClick={() => session.setInventoryContext({})}>Quitar ubicación y filtros</Button></div>}
            <Field label="Producto"><ProductoSelect value={session.idProducto} onChange={event => { session.setIdProducto(event.target.value); session.setIdInventario('') }} /></Field>
            <Field label="Inventario"><InventarioSelect valueKind="inventario" idProducto={session.idProducto || undefined} value={session.idInventario} onChange={event => session.setIdInventario(event.target.value)} /></Field>
            {(session.idProducto || session.idInventario) && <Button variant="ghost" size="sm" onClick={() => { session.setIdProducto(''); session.setIdInventario('') }}>Quitar contexto</Button>}
          </div>
        </Card>
        <Card title="Navega conmigo"><p className="text-sm leading-relaxed text-fg-muted">Di «abre inventario» o «muéstrame los sensores». Saiki abre esa sección y continúa en una mini ventana si la sesión de voz está activa.</p></Card>
      </div>
    </div>
    <SaikiEvidence />
    {esEmpresa && <SaikiSensors />}
  </div>
}
