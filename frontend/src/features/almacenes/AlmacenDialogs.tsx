/**
 * Modales de almacén reutilizados por Inicio y el detalle:
 *  - <AlmacenFormModal>  crear / editar (usa AlmacenForm)
 *  - <EliminarAlmacenDialog>
 */
import { useId } from 'react'
import { useCreateAlmacen, useDeleteAlmacen, useUpdateAlmacen } from '@/api/almacenes'
import type { Almacen } from '@/api/types'
import { Button, Modal, useToast } from '@/components/ui'
import { AlmacenForm } from './AlmacenForm'
import { EliminarDialog } from './EliminarDialog'

export interface AlmacenFormModalProps {
  open: boolean
  /** null/undefined = crear. */
  almacen?: Almacen | null
  onClose: () => void
  onGuardado?: (almacen: Almacen) => void
}

export function AlmacenFormModal({ open, almacen, onClose, onGuardado }: AlmacenFormModalProps) {
  const formId = useId()
  const toast = useToast()
  const crear = useCreateAlmacen()
  const editar = useUpdateAlmacen()
  const pending = crear.isPending || editar.isPending
  const esEdicion = !!almacen

  return (
    <Modal
      open={open}
      onClose={onClose}
      dismissable={!pending}
      size="lg"
      title={esEdicion ? 'Editar almacén' : 'Nuevo almacén'}
      description={esEdicion ? almacen.nombre : 'Los campos marcados con * son obligatorios.'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={pending}>
            Cancelar
          </Button>
          <Button type="submit" form={formId} loading={pending}>
            {esEdicion ? 'Guardar cambios' : 'Crear almacén'}
          </Button>
        </>
      }
    >
      <AlmacenForm
        formId={formId}
        hideActions
        almacen={almacen ?? null}
        onSubmit={async (body) => {
          const res = almacen ? await editar.mutateAsync({ id: almacen.id_almacen, body }) : await crear.mutateAsync(body)
          toast.success(almacen ? 'Almacén actualizado' : 'Almacén creado')
          onGuardado?.(res)
          return res
        }}
        onSuccess={onClose}
      />
    </Modal>
  )
}

export interface EliminarAlmacenDialogProps {
  almacen: Almacen | null
  /** true si es el único almacén (tras eliminarlo se pedirá crear otro). */
  esUltimo?: boolean
  onClose: () => void
  onEliminado?: () => void
}

export function EliminarAlmacenDialog({ almacen, esUltimo, onClose, onEliminado }: EliminarAlmacenDialogProps) {
  const del = useDeleteAlmacen()
  return (
    <EliminarDialog
      open={!!almacen}
      title="Eliminar almacén"
      description={
        <>
          <p>
            Se eliminará <strong className="text-fg">{almacen?.nombre}</strong>. Esta acción no se puede deshacer.
          </p>
          <p className="mt-2">Si el almacén tiene zonas, operarios u órdenes asociadas, el sistema puede impedirlo.</p>
          {esUltimo && <p className="mt-2 font-medium text-warning">Es tu único almacén: tendrás que crear otro para seguir usando el panel.</p>}
        </>
      }
      accion={() => del.mutateAsync(almacen!.id_almacen)}
      mensajeExito="Almacén eliminado"
      tituloError="No se pudo eliminar el almacén"
      onClose={onClose}
      {...(onEliminado ? { onEliminado } : {})}
    />
  )
}
