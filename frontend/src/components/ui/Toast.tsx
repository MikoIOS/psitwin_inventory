/**
 * Notificaciones efímeras.
 *   const toast = useToast()
 *   toast.success('Zona creada')
 *   toast.error('Stock insuficiente', 'No se pudo registrar')
 */
import { createContext, use, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { cn } from '@/lib/cn'
import { Icon, type IconName } from './Icon'

export type ToastKind = 'success' | 'error' | 'info' | 'warning'

interface ToastItem {
  id: number
  kind: ToastKind
  message: ReactNode
  title?: ReactNode
}

export interface ToastApi {
  show: (kind: ToastKind, message: ReactNode, title?: ReactNode) => void
  success: (message: ReactNode, title?: ReactNode) => void
  error: (message: ReactNode, title?: ReactNode) => void
  info: (message: ReactNode, title?: ReactNode) => void
  warning: (message: ReactNode, title?: ReactNode) => void
  dismiss: (id: number) => void
}

const ToastContext = createContext<ToastApi | null>(null)

const DURATION: Record<ToastKind, number> = { success: 4000, info: 5000, warning: 7000, error: 8000 }
const STYLE: Record<ToastKind, { icon: IconName; bar: string; iconColor: string }> = {
  success: { icon: 'check-circle', bar: 'bg-success', iconColor: 'text-success' },
  error: { icon: 'alert', bar: 'bg-danger', iconColor: 'text-danger' },
  warning: { icon: 'alert', bar: 'bg-warning', iconColor: 'text-warning' },
  info: { icon: 'info', bar: 'bg-info', iconColor: 'text-info' },
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const seq = useRef(0)
  const layer = useRef<HTMLDivElement>(null)

  // Los <dialog> modales viven en el top layer y taparían un contenedor `fixed` normal.
  // Se reabre el popover en cada cambio para quedar encima del último dialog abierto.
  useEffect(() => {
    const el = layer.current
    if (!el || typeof el.showPopover !== 'function') return
    try {
      if (el.matches(':popover-open')) el.hidePopover()
      if (items.length > 0) el.showPopover()
    } catch {
      /* navegador sin soporte de popover: queda como contenedor fixed */
    }
  }, [items])

  const dismiss = useCallback((id: number) => setItems((l) => l.filter((t) => t.id !== id)), [])

  const show = useCallback(
    (kind: ToastKind, message: ReactNode, title?: ReactNode) => {
      const id = ++seq.current
      setItems((l) => [...l.slice(-3), { id, kind, message, ...(title !== undefined ? { title } : {}) }])
      window.setTimeout(() => dismiss(id), DURATION[kind])
    },
    [dismiss],
  )

  const api = useMemo<ToastApi>(
    () => ({
      show,
      dismiss,
      success: (m, t) => show('success', m, t),
      error: (m, t) => show('error', m, t),
      info: (m, t) => show('info', m, t),
      warning: (m, t) => show('warning', m, t),
    }),
    [show, dismiss],
  )

  return (
    <ToastContext value={api}>
      {children}
      <div
        ref={layer}
        popover="manual"
        aria-live="polite"
        aria-relevant="additions"
        className="pointer-events-none fixed inset-x-0 top-auto bottom-0 z-[60] m-0 h-auto w-auto overflow-visible border-0 bg-transparent flex flex-col items-center gap-2 p-4 sm:inset-x-auto sm:right-0 sm:items-end"
      >
        {items.map((t) => {
          const s = STYLE[t.kind]
          return (
            <div
              key={t.id}
              role={t.kind === 'error' ? 'alert' : 'status'}
              className="pointer-events-auto relative flex w-full max-w-sm overflow-hidden rounded-lg border border-border bg-surface text-fg shadow-pop [animation:toast-in_180ms_ease-out]"
            >
              <span className={cn('w-1 shrink-0', s.bar)} aria-hidden="true" />
              <div className="flex flex-1 items-start gap-3 py-3 pr-2 pl-3">
                <Icon name={s.icon} className={cn('mt-0.5 size-5 shrink-0', s.iconColor)} />
                <div className="min-w-0 flex-1 text-sm">
                  {t.title && <p className="font-semibold">{t.title}</p>}
                  <p className={cn(t.title ? 'text-fg-muted' : 'text-fg')}>{t.message}</p>
                </div>
                <button
                  type="button"
                  onClick={() => dismiss(t.id)}
                  className="flex size-7 shrink-0 items-center justify-center rounded text-fg-subtle hover:bg-surface-2 hover:text-fg"
                  aria-label="Cerrar notificación"
                >
                  <Icon name="x" className="size-4" />
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </ToastContext>
  )
}

export function useToast(): ToastApi {
  const ctx = use(ToastContext)
  if (!ctx) throw new Error('useToast debe usarse dentro de <ToastProvider>')
  return ctx
}
