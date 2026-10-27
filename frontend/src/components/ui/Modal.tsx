/**
 * Modal accesible sobre <dialog> nativo (focus trap, Esc, top-layer).
 *
 *   <Modal open={abierto} onClose={() => setAbierto(false)} title="Nueva zona"
 *          footer={<><Button variant="secondary" onClick={cerrar}>Cancelar</Button><Button type="submit" form="form-zona">Guardar</Button></>}>
 *     <form id="form-zona" onSubmit={...}>...</form>
 *   </Modal>
 *
 * En móvil ocupa todo el ancho y se ancla abajo (hoja inferior).
 */
import { useEffect, useId, useRef, type ReactNode } from 'react'
import { cn } from '@/lib/cn'
import { Button } from './Button'

export interface ModalProps {
  open: boolean
  onClose: () => void
  title: ReactNode
  description?: ReactNode
  children?: ReactNode
  footer?: ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
  /** Impide cerrar con Esc / clic fuera (ej. mientras se guarda). */
  dismissable?: boolean
  className?: string
}

const SIZES = { sm: 'sm:max-w-sm', md: 'sm:max-w-lg', lg: 'sm:max-w-2xl', xl: 'sm:max-w-4xl' }

export function Modal({ open, onClose, title, description, children, footer, size = 'md', dismissable = true, className }: ModalProps) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const descId = useId()

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      aria-describedby={description ? descId : undefined}
      onCancel={(e) => {
        e.preventDefault()
        if (dismissable) onClose()
      }}
      onClick={(e) => {
        if (dismissable && e.target === e.currentTarget) onClose()
      }}
      className={cn(
        'm-0 mt-auto max-h-[92dvh] w-full max-w-none overflow-hidden rounded-t-xl border border-border bg-surface p-0 text-fg shadow-pop',
        'sm:m-auto sm:max-h-[88dvh] sm:rounded-xl',
        SIZES[size],
        className,
      )}
    >
      {open && (
        <div className="flex max-h-[inherit] flex-col">
          <header className="flex items-start justify-between gap-4 border-b border-border px-5 pt-4 pb-3">
            <div className="min-w-0">
              <h2 id={titleId} className="text-lg font-semibold">
                {title}
              </h2>
              {description && (
                <p id={descId} className="mt-0.5 text-sm text-fg-muted">
                  {description}
                </p>
              )}
            </div>
            {dismissable && <Button variant="ghost" size="sm" iconOnly icon="x" aria-label="Cerrar" onClick={onClose} />}
          </header>
          <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>
          {footer && (
            <footer className="flex flex-col-reverse gap-2 border-t border-border bg-surface-2/60 px-5 py-3 sm:flex-row sm:justify-end">
              {footer}
            </footer>
          )}
        </div>
      )}
    </dialog>
  )
}
