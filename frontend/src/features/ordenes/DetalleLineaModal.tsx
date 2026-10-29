/**
 * Agregar / editar una línea (DetalleReposicion) de una orden PENDIENTE.
 * Al editar, el producto no cambia (PUT solo acepta cantidad_solicitada y costo_unitario).
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { useCreateDetalleReposicion, useUpdateDetalleReposicion } from '@/api/ordenesReposicion'
import type { DetalleReposicion } from '@/api/types'
import { useOfertas } from '@/api/abastecimiento'
import { subtotalCentimos } from '@/lib/abastecimiento'
import { Button, Field, Input, Select, Modal, useApiErrorHandler, useToast } from '@/components/ui'
import { formatMoneda } from '@/lib/format'
import { idRequerido, numero, numStr } from '@/lib/zod'

const schema = z.object({
  id_producto: idRequerido('Elige un producto'),
  cantidad_solicitada: numero({ mayorQue: 0 }),
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
    },
  })
  const { register, handleSubmit, formState, watch } = form
  const err = formState.errors

  const offers = useOfertas(true, idProveedor)
  const offer = offers.data?.find(o => o.id_producto === watch('id_producto'))
  const unit = detalle?.unidad ?? offer?.unidad ?? 'unidad'
  const price = detalle?.precio_centimos ?? offer?.precio_centimos
  const subtotal = price == null ? null : subtotalCentimos(watch('cantidad_solicitada') || '0', price)
  const submit = handleSubmit(async ({ id_producto, cantidad_solicitada }) => {
    if ((unit === 'unidad' && !Number.isInteger(cantidad_solicitada)) || Math.abs(cantidad_solicitada * 1000 - Math.round(cantidad_solicitada * 1000)) > .000001) {
      form.setError('cantidad_solicitada', { message: 'Usa unidades enteras o kilos con hasta tres decimales' }); return
    }
    if (!detalle && (!offer || cantidad_solicitada > offer.cantidad_disponible)) {
      form.setError('cantidad_solicitada', { message: 'La cantidad supera la oferta disponible' }); return
    }
    try {
      if (detalle) {
        await actualizar.mutateAsync({ id: detalle.id_detalle_reposicion, body: { cantidad_solicitada } })
        toast.success('Línea actualizada')
      } else {
        await crear.mutateAsync({ idOrden, body: { id_producto, cantidad_solicitada, id_oferta: offer!.id_oferta } })
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
          <Select options={(offers.data ?? []).filter(o => !productosEnOrden.includes(o.id_producto)).map(o => ({ value: o.id_producto, label: `${o.producto} · ${o.cantidad_disponible} ${o.unidad} disponibles` }))} {...register('id_producto')} />
          {offers.isError && <p role="alert">No se pudieron consultar las ofertas.</p>}
        </Field>
      )}
      <Field label="Cantidad solicitada" error={err.cantidad_solicitada?.message} required>
        <Input type="number" inputMode="decimal" min={unit === 'kg' ? .001 : 1} step={unit === 'kg' ? .001 : 1} suffix={unit} {...register('cantidad_solicitada')} />
      </Field>
      <Field label="Precio por unidad" hint="Precio conservado al confirmar la solicitud."><p>{formatMoneda(price == null ? null : price / 100)} / {unit}</p></Field>
      <p className="text-sm text-fg-muted sm:col-span-2">
        Subtotal: <span className="font-mono font-semibold text-fg tabular">{formatMoneda(subtotal == null ? null : subtotal / 100)}</span>
      </p>
    </form>
  )
}
