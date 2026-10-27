/**
 * Agregar / editar una línea (DetalleReposicion) de una orden PENDIENTE.
 * Al editar, el producto no cambia (PUT solo acepta cantidad_solicitada y costo_unitario).
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { useCreateDetalleReposicion, useUpdateDetalleReposicion } from '@/api/ordenesReposicion'
import type { DetalleReposicion } from '@/api/types'
import { ProductoSelect } from '@/components/selects'
import { Button, Field, Input, Modal, useApiErrorHandler, useToast } from '@/components/ui'
import { formatMoneda } from '@/lib/format'
import { idRequerido, numero, numeroOpcional, numStr } from '@/lib/zod'

const schema = z.object({
  id_producto: idRequerido('Elige un producto'),
  cantidad_solicitada: numero({ mayorQue: 0, entero: true }),
  costo_unitario: numeroOpcional({ min: 0 }),
})
type In = z.input<typeof schema>
type Out = z.output<typeof schema>

export interface DetalleLineaModalProps {
  open: boolean
  onClose: () => void
  idOrden: string
  /** Línea a editar (si no se pasa, se agrega una nueva). */
  detalle?: DetalleReposicion | null
  /** Nombre del producto (solo en edición). */
  nombreProducto?: string
  /** Productos ya incluidos en la orden (se excluyen al agregar). */
  productosEnOrden: readonly string[]
  /** Proveedor de la solicitud: solo se ofrecen sus productos. */
  idProveedor: string
}

export function DetalleLineaModal({ open, onClose, idOrden, detalle, nombreProducto, productosEnOrden, idProveedor }: DetalleLineaModalProps) {
  const crear = useCreateDetalleReposicion()
  const actualizar = useUpdateDetalleReposicion()
  const pending = crear.isPending || actualizar.isPending
  return (
    <Modal
      open={open}
      onClose={onClose}
      dismissable={!pending}
      title={detalle ? 'Editar línea' : 'Agregar producto'}
      description={detalle ? nombreProducto : 'La línea solo puede modificarse mientras la orden esté Pendiente.'}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={pending}>
            Cancelar
          </Button>
          <Button type="submit" form="form-detalle-linea" icon="check" loading={pending}>
            {detalle ? 'Guardar' : 'Agregar'}
          </Button>
        </>
      }
    >
      {open && (
        <LineaForm
          key={detalle?.id_detalle_reposicion ?? 'nuevo'}
          idOrden={idOrden}
          detalle={detalle ?? null}
          productosEnOrden={productosEnOrden}
          idProveedor={idProveedor}
          crear={crear}
          actualizar={actualizar}
          onDone={onClose}
        />
      )}
    </Modal>
  )
}

interface LineaFormProps {
  idOrden: string
  detalle: DetalleReposicion | null
  productosEnOrden: readonly string[]
  /** Proveedor de la solicitud: solo se ofrecen sus productos. */
  idProveedor: string
  crear: ReturnType<typeof useCreateDetalleReposicion>
  actualizar: ReturnType<typeof useUpdateDetalleReposicion>
  onDone: () => void
}

function LineaForm({ idOrden, detalle, productosEnOrden, idProveedor, crear, actualizar, onDone }: LineaFormProps) {
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const form = useForm<In, unknown, Out>({
    resolver: zodResolver(schema),
    defaultValues: {
      id_producto: detalle?.id_producto ?? '',
      cantidad_solicitada: numStr(detalle?.cantidad_solicitada),
      costo_unitario: numStr(detalle?.costo_unitario),
    },
  })
  const { register, handleSubmit, formState, watch } = form
  const err = formState.errors

  const cantidad = Number(watch('cantidad_solicitada') || 0)
  const costo = Number((watch('costo_unitario') || '').replace(',', '.'))
  const subtotal = Number.isFinite(cantidad * costo) && watch('costo_unitario') ? cantidad * costo : null

  const submit = handleSubmit(async ({ id_producto, cantidad_solicitada, costo_unitario }) => {
    try {
      if (detalle) {
        await actualizar.mutateAsync({ id: detalle.id_detalle_reposicion, body: { cantidad_solicitada, costo_unitario } })
        toast.success('Línea actualizada')
      } else {
        await crear.mutateAsync({ idOrden, body: { id_producto, cantidad_solicitada, costo_unitario } })
        toast.success('Producto agregado a la orden')
      }
      onDone()
    } catch (e) {
      handleError(e, { form, title: detalle ? 'No se pudo actualizar la línea' : 'No se pudo agregar el producto' })
    }
  })

  return (
    <form id="form-detalle-linea" onSubmit={submit} noValidate className="grid gap-4 sm:grid-cols-2">
      {!detalle && (
        <Field label="Producto" error={err.id_producto?.message} required className="sm:col-span-2">
          <ProductoSelect
            excluir={productosEnOrden}
            // Productos del proveedor de la solicitud (los antiguos sin proveedor se ofrecen siempre).
            filtrar={(p) => !p.id_proveedor || !idProveedor || p.id_proveedor === idProveedor}
            {...register('id_producto')}
          />
        </Field>
      )}
      <Field label="Cantidad solicitada" error={err.cantidad_solicitada?.message} required>
        <Input type="number" inputMode="numeric" min={1} step={1} suffix="u." {...register('cantidad_solicitada')} />
      </Field>
      <Field label="Costo unitario" error={err.costo_unitario?.message} hint="Opcional.">
        <Input type="number" inputMode="decimal" min={0} step="any" suffix="S/" {...register('costo_unitario')} />
      </Field>
      <p className="text-sm text-fg-muted sm:col-span-2">
        Subtotal: <span className="font-mono font-semibold text-fg tabular">{formatMoneda(subtotal)}</span>
      </p>
    </form>
  )
}
