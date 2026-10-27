/**
 * Stepper visual del ciclo de vida de una orden:
 *   PENDIENTE (↔ OBSERVADA si la empresa la devuelve) → ENVIADA → PARCIAL → RECIBIDA   (o → CANCELADA)
 * Es solo informativo: PARCIAL y RECIBIDA los calcula el backend a partir de las recepciones.
 */
import { ESTADO_ORDEN_LABEL } from '@/api/enums'
import type { EstadoOrden, OrdenReposicion } from '@/api/types'
import { Icon } from '@/components/ui'
import { cn } from '@/lib/cn'

/** El primer paso es la solicitud: Pendiente, u Observada / Aprobada (dato antiguo) si está en ese estado. */
const flujo = (e: EstadoOrden): EstadoOrden[] => [e === 'OBSERVADA' || e === 'APROBADA' ? e : 'PENDIENTE', 'ENVIADA', 'PARCIAL', 'RECIBIDA']

type Fase = 'hecho' | 'actual' | 'futuro' | 'cancelado'

interface Paso {
  estado: EstadoOrden
  fase: Fase
}

function pasos(orden: Pick<OrdenReposicion, 'estado'>): Paso[] {
  if (orden.estado === 'CANCELADA') {
    return [
      { estado: 'PENDIENTE', fase: 'hecho' },
      { estado: 'CANCELADA', fase: 'cancelado' },
    ]
  }
  const FLUJO = flujo(orden.estado)
  const idx = FLUJO.indexOf(orden.estado)
  return FLUJO.map((estado, i) => ({
    estado,
    fase: orden.estado === 'RECIBIDA' || i < idx ? 'hecho' : i === idx ? 'actual' : 'futuro',
  }))
}

export function OrdenStepper({ orden, className }: { orden: Pick<OrdenReposicion, 'estado'>; className?: string }) {
  const lista = pasos(orden)
  return (
    <nav aria-label="Estado de la orden" className={className}>
      <ol className="flex items-start">
        {lista.map((p, i) => {
          const esActual = p.fase === 'actual' || p.fase === 'cancelado' || (p.estado === 'RECIBIDA' && p.fase === 'hecho')
          return (
            <li
              key={p.estado}
              aria-current={esActual ? 'step' : undefined}
              className="relative flex min-w-0 flex-1 flex-col items-center gap-1.5 text-center"
            >
              {i > 0 && (
                <span
                  aria-hidden="true"
                  className={cn(
                    'absolute top-3.5 right-1/2 h-0.5 w-full -translate-y-1/2',
                    p.fase === 'futuro' ? 'bg-border-strong' : p.fase === 'cancelado' ? 'bg-danger/60' : 'bg-success',
                  )}
                />
              )}
              <span
                className={cn(
                  'relative z-10 flex size-7 items-center justify-center rounded-full border-2 font-mono text-xs font-bold',
                  p.fase === 'hecho' && 'border-success bg-success text-white',
                  p.fase === 'actual' && 'border-accent bg-accent text-accent-fg ring-4 ring-accent/25',
                  p.fase === 'futuro' && 'border-border-strong bg-surface text-fg-subtle',
                  p.fase === 'cancelado' && 'border-danger bg-danger text-white ring-4 ring-danger/20',
                )}
              >
                {p.fase === 'hecho' ? (
                  <Icon name="check" className="size-4" />
                ) : p.fase === 'cancelado' ? (
                  <Icon name="x" className="size-4" />
                ) : (
                  i + 1
                )}
              </span>
              <span
                className={cn(
                  'max-w-full truncate px-0.5 text-[0.6875rem] leading-tight sm:text-xs',
                  p.fase === 'futuro' ? 'text-fg-subtle' : 'font-semibold text-fg',
                  p.fase === 'cancelado' && 'text-danger',
                )}
              >
                {ESTADO_ORDEN_LABEL[p.estado]}
                <span className="sr-only">
                  {p.fase === 'hecho' ? ' (completado)' : p.fase === 'actual' ? ' (estado actual)' : p.fase === 'cancelado' ? ' (estado actual)' : ' (pendiente)'}
                </span>
              </span>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
