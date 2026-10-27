import type { ReactNode } from 'react'
import { Button } from './Button'
import { Icon } from './Icon'
import { Modal } from './Modal'

export interface ConfirmDialogProps {
  open: boolean
  title: ReactNode
  description?: ReactNode
  confirmLabel?: string
  cancelLabel?: string
  /** danger = acción destructiva (eliminar, cancelar orden). */
  tone?: 'danger' | 'primary'
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
}

/**
 *   <ConfirmDialog open={!!aEliminar} title="Eliminar zona" description="Esta acción no se puede deshacer."
 *     confirmLabel="Eliminar" tone="danger" loading={del.isPending}
 *     onConfirm={() => del.mutate(id, {...})} onCancel={() => setAEliminar(null)} />
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  tone = 'primary',
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Modal
      open={open}
      onClose={onCancel}
      title={title}
      size="sm"
      dismissable={!loading}
      footer={
        <>
          <Button variant="secondary" onClick={onCancel} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button variant={tone === 'danger' ? 'danger' : 'primary'} onClick={onConfirm} loading={loading} autoFocus>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <div className="flex gap-3">
        {tone === 'danger' && (
          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-danger-soft text-danger">
            <Icon name="alert" className="size-5" />
          </span>
        )}
        <div className="text-sm text-fg-muted">{description ?? '¿Deseas continuar?'}</div>
      </div>
    </Modal>
  )
}
