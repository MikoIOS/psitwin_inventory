/**
 * Confirmación de eliminación con manejo de errores del backend.
 * Un 409 (regla de negocio: el registro tiene datos dependientes) se muestra dentro del diálogo;
 * el resto de errores pasa por `useApiErrorHandler` (toast).
 *
 *   <EliminarDialog open={!!zona} title="Eliminar zona" description="…"
 *     accion={() => del.mutateAsync(zona.id_zona)} mensajeExito="Zona eliminada" onClose={() => setZona(null)} />
 */
import { useState, type ReactNode } from 'react'
import { ApiError } from '@/api/client'
import { ConfirmDialog, Icon, useApiErrorHandler, useToast } from '@/components/ui'

export interface EliminarDialogProps {
  open: boolean
  title: ReactNode
  description: ReactNode
  confirmLabel?: string
  /** Ejecuta la eliminación (normalmente `mutation.mutateAsync(id)`). */
  accion: () => Promise<unknown>
  mensajeExito: string
  /** Título del toast de error. */
  tituloError?: string
  onClose: () => void
  /** Se llama tras eliminar correctamente (después de cerrar). */
  onEliminado?: () => void
}

export function EliminarDialog({
  open,
  title,
  description,
  confirmLabel = 'Eliminar',
  accion,
  mensajeExito,
  tituloError = 'No se pudo eliminar',
  onClose,
  onEliminado,
}: EliminarDialogProps) {
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const [pending, setPending] = useState(false)
  const [bloqueo, setBloqueo] = useState<string | null>(null)

  const cerrar = () => {
    if (pending) return
    setBloqueo(null)
    onClose()
  }

  const confirmar = async () => {
    setPending(true)
    setBloqueo(null)
    try {
      await accion()
      toast.success(mensajeExito)
      setPending(false)
      onClose()
      onEliminado?.()
    } catch (e) {
      setPending(false)
      if (e instanceof ApiError && e.isConflict) setBloqueo(e.detail)
      else handleError(e, { title: tituloError })
    }
  }

  return (
    <ConfirmDialog
      open={open}
      title={title}
      tone="danger"
      confirmLabel={confirmLabel}
      loading={pending}
      onCancel={cerrar}
      onConfirm={() => void confirmar()}
      description={
        <div className="flex flex-col gap-3">
          <div>{description}</div>
          {bloqueo && (
            <p role="alert" className="flex items-start gap-2 rounded-[var(--radius-ui)] border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger">
              <Icon name="alert" className="mt-0.5 size-4 shrink-0" />
              <span>
                <strong className="font-semibold">No se puede eliminar.</strong> {bloqueo}
              </span>
            </p>
          )}
        </div>
      }
    />
  )
}
