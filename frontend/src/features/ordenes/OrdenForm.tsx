import { OfertaSolicitudForm } from './OfertaSolicitudForm'
/**
 * Formularios de solicitud de reposición (solo OPERARIO, en modal):
 *  - OrdenCrearModal: proveedor ACTIVO, fecha estimada (datetime-local → ISO UTC) y observación. El almacén es el
 *    del operario (lo fuerza el backend). Nace PENDIENTE; las líneas se agregan en el detalle.
 *    La fecha estimada es opcional en el backend, pero el formulario la exige (se sugiere según el tiempo de
 *    entrega del proveedor) porque alimenta el seguimiento.
 *  - OrdenEditarModal (PENDIENTE / OBSERVADA): proveedor, fecha estimada y observación.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { useCreateOrden, useUpdateOrden } from '@/api/ordenesReposicion'
import type { OrdenReposicion } from '@/api/types'
import { ProveedorSelect } from '@/components/selects'
import { Button, Field, Input, Modal, Textarea, useApiErrorHandler, useToast } from '@/components/ui'
import { datetimeLocalToIso, isoToDatetimeLocal } from '@/lib/format'
import { idRequerido, textoOpcional } from '@/lib/zod'

/** datetime-local obligatorio → ISO UTC. */
export const fechaEstimada = () =>
  z
    .string()
    .min(1, 'Indica la fecha estimada de recepción')
    .transform((v) => datetimeLocalToIso(v))
    .pipe(z.string({ error: 'Fecha no válida' }))

/** Fecha sugerida = ahora + días de entrega del proveedor (redondeada a la hora). */
export function fechaSugerida(dias: number | undefined): string {
  const d = new Date()
  d.setDate(d.getDate() + Math.max(0, dias ?? 0))
  d.setMinutes(0, 0, 0)
  d.setHours(d.getHours() + 1)
  return isoToDatetimeLocal(d.toISOString())
}

/* ------------------------------------------------------------------ */

export interface OrdenCrearModalProps {
  open: boolean
  onClose: () => void
  /** Proveedor preseleccionado (ej. `?proveedor=<id>`). */
  idProveedor?: string | undefined
  onCreated: (orden: OrdenReposicion) => void
}

export function OrdenCrearModal({ open, onClose, idProveedor, onCreated }: OrdenCrearModalProps) {
  const crear = useCreateOrden()
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Nueva solicitud de reposición"
      description="Selecciona ofertas, revisa los importes y confirma para que la empresa apruebe."
      size="lg"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={crear.isPending}>
            Cancelar
          </Button>
        </>
      }
    >
      {open && <OfertaSolicitudForm crear={crear} idProveedor={idProveedor} onCreated={onCreated} />}
    </Modal>
  )
}

const editarSchema = z.object({
  id_proveedor: idRequerido('Elige un proveedor activo'),
  fecha_estimada_recepcion: fechaEstimada(),
  observacion: textoOpcional({ max: 500 }),
})
type EditarIn = z.input<typeof editarSchema>
type EditarOut = z.output<typeof editarSchema>

export function OrdenEditarModal({ orden, open, onClose }: { orden: OrdenReposicion; open: boolean; onClose: () => void }) {
  const actualizar = useUpdateOrden()
  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Editar solicitud"
      description="Proveedor, fecha estimada y observación. Los productos se editan en la tabla de líneas."
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={actualizar.isPending}>
            Cancelar
          </Button>
          <Button type="submit" form="form-orden-editar" icon="check" loading={actualizar.isPending}>
            Guardar cambios
          </Button>
        </>
      }
    >
      {open && <OrdenEditarForm actualizar={actualizar} orden={orden} onDone={onClose} />}
    </Modal>
  )
}

interface OrdenEditarFormProps {
  actualizar: ReturnType<typeof useUpdateOrden>
  orden: OrdenReposicion
  onDone: () => void
}

function OrdenEditarForm({ actualizar, orden, onDone }: OrdenEditarFormProps) {
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const form = useForm<EditarIn, unknown, EditarOut>({
    resolver: zodResolver(editarSchema),
    defaultValues: {
      id_proveedor: orden.id_proveedor,
      fecha_estimada_recepcion: isoToDatetimeLocal(orden.fecha_estimada_recepcion),
      observacion: orden.observacion ?? '',
    },
  })
  const err = form.formState.errors

  const submit = form.handleSubmit(async (body) => {
    try {
      await actualizar.mutateAsync({ id: orden.id_orden_reposicion, body })
      toast.success('Solicitud actualizada')
      onDone()
    } catch (e) {
      handleError(e, { form, title: 'No se pudo actualizar la orden' })
    }
  })

  return (
    <form id="form-orden-editar" onSubmit={submit} noValidate className="flex flex-col gap-4">
      <Field label="Proveedor" error={err.id_proveedor?.message} hint="Solo proveedores activos." required>
        <ProveedorSelect {...form.register('id_proveedor')} />
      </Field>
      <Field label="Fecha estimada de recepción" error={err.fecha_estimada_recepcion?.message} hint="Hora local." required>
        <Input type="datetime-local" {...form.register('fecha_estimada_recepcion')} />
      </Field>
      <Field label="Observación" error={err.observacion?.message}>
        <Textarea {...form.register('observacion')} />
      </Field>
    </form>
  )
}
