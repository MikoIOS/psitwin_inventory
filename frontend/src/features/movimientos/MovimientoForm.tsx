import { inventarioDetalleId } from '@/api/inventarios'
/**
 * Formulario de MOVIMIENTO DE SALIDA (reutilizable). Las entradas ya no se registran a mano: llegan por recepción.
 *
 *   <MovimientoForm inventario={inv} onSuccess={cerrar} onCancel={cerrar} />      // inventario fijo
 *   <MovimientoForm idProducto={p.id_producto} onSuccess={...} />                  // producto preseleccionado
 *   <MovimientoModal open={abierto} onClose={cerrar} inventario={inv} />           // en un modal
 *
 * Reglas:
 *  - Siempre SALIDA, con motivo VENTA o VENCIMIENTO. cantidad > 0.
 *  - Solo lo usa el OPERARIO: el autor del movimiento sale de su token (no hay selector de operario).
 *  - cantidad > stock_actual: aviso en cliente; el 409 del backend se muestra en el formulario.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'
import { ApiError } from '@/api/client'
import { motivosManualesOpciones } from '@/api/enums'
import { useInventario, useInventariosPorProducto } from '@/api/inventarios'
import { useCreateMovimiento } from '@/api/movimientos'
import { useProducto } from '@/api/productos'
import type { Inventario, Movimiento, MovimientoCreate, TipoMovimiento } from '@/api/types'
import { useUbicaciones } from '@/api/ubicaciones'
import { InventarioSelect, ProductoSelect } from '@/components/selects'
import { Field, Input, Modal, Select, StockBadge, Textarea, useToast } from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatNumero } from '@/lib/format'
import { idRequerido, numero, textoOpcional } from '@/lib/zod'
import { FormActions } from '@/features/inventario/InventarioForm'
import { ApiErrorAlert, FormAlert, useInlineApiError } from '@/features/inventario/formUtils'

const MOTIVOS_SALIDA = ['VENTA', 'VENCIMIENTO'] as const

const schema = z
  .object({
    id_producto: z.string(),
    id_inventario: idRequerido('Selecciona la ubicación (inventario)'),
    motivo_movimiento: z.string().min(1, 'Selecciona el motivo').pipe(z.enum(MOTIVOS_SALIDA)),
    cantidad: numero({ mayorQue: 0, entero: true }),
    observacion: textoOpcional({ max: 500 }),
  })
  .transform((v) => ({ ...v, tipo_movimiento: 'SALIDA' as const }))

type In = z.input<typeof schema>
type Out = z.output<typeof schema>

/** Stock resultante según el tipo (misma regla que el backend). */
export function calcularStockNuevo(tipo: TipoMovimiento, actual: number, cantidad: number): number {
  if (tipo === 'ENTRADA') return actual + cantidad
  if (tipo === 'SALIDA') return actual - cantidad
  return cantidad
}

export interface MovimientoFormProps {
  /** Inventario preseleccionado y fijo (acción rápida desde una fila de inventario). */
  inventario?: Inventario | undefined
  /** Producto preseleccionado (el inventario se elige entre sus ubicaciones). */
  idProducto?: string | undefined
  onSuccess?: (m: Movimiento) => void
  onCancel?: () => void
}

export function MovimientoForm({ inventario: invFijo, idProducto, onSuccess, onCancel }: MovimientoFormProps) {
  const toast = useToast()
  const crear = useCreateMovimiento()
  const apiError = useInlineApiError()
  const ub = useUbicaciones()

  const form = useForm<In, unknown, Out>({
    resolver: zodResolver(schema),
    defaultValues: {
      id_producto: invFijo?.id_producto ?? idProducto ?? '',
      id_inventario: invFijo ? inventarioDetalleId(invFijo) : '',
      motivo_movimiento: 'VENTA',
      cantidad: '',
      observacion: '',
    },
  })
  const { register, handleSubmit, setValue, formState, control } = form
  const err = formState.errors
  const [idProd, idInv, cantidadRaw] = useWatch({ control, name: ['id_producto', 'id_inventario', 'cantidad'] })

  // Stock actual del inventario elegido (detalle fresco; si no, el de la lista del producto o el fijo).
  const detalle = useInventario(idInv || undefined)
  const lista = useInventariosPorProducto(invFijo ? undefined : idProd || undefined)
  const inv = detalle.data ?? lista.data?.find((i) => inventarioDetalleId(i) === idInv) ?? (invFijo && inventarioDetalleId(invFijo) === idInv ? invFijo : undefined)
  const producto = useProducto(inv?.id_producto ?? (idProd || undefined))
  const ubicacion = inv ? ub.porRack.get(inv.id_rack) : undefined

  const cantidadTxt = (cantidadRaw ?? '').trim()
  const cantidad = cantidadTxt === '' ? NaN : Number(cantidadTxt.replace(',', '.'))
  const cantidadValida = Number.isFinite(cantidad) && cantidad > 0
  const stockNuevo = inv && cantidadValida ? calcularStockNuevo('SALIDA', inv.stock_actual, cantidad) : undefined
  const excedeStock = inv !== undefined && cantidadValida && cantidad > inv.stock_actual
  const submit = handleSubmit(async ({ id_producto: _p, ...values }) => {
    apiError.clear()
    if (!inv) return
    const body: MovimientoCreate = { ...values, id_inventario: inv.id_inventario, id_detalle_inventario: inventarioDetalleId(inv) }
    try {
      const mov = await crear.mutateAsync(body)
      toast.success(
        `Stock ${formatNumero(mov.stock_anterior)} → ${formatNumero(mov.stock_nuevo)}`,
        'Salida registrada',
      )
      onSuccess?.(mov)
    } catch (e) {
      // 409 (p. ej. stock insuficiente u operario inactivo): refrescar el stock mostrado y explicar el motivo.
      if (e instanceof ApiError && e.isConflict) void detalle.refetch()
      apiError.handle(e, { form, titulo: 'No se pudo registrar la salida' })
    }
  })


  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <ApiErrorAlert error={apiError.error} />

      {/* Inventario */}
      {invFijo ? (
        <div className="rounded-md border border-border bg-surface-2/60 px-4 py-3">
          <p className="label-stencil">Inventario</p>
          <p className="font-semibold text-fg">{producto.data?.nombre ?? '…'}</p>
          <p className="text-sm text-fg-muted">{ubicacion?.etiqueta ?? 'Ubicación no disponible'}</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Producto" error={err.id_producto?.message} required>
            <ProductoSelect
              {...register('id_producto', {
                onChange: () => {
                  setValue('id_inventario', '')
                },
              })}
            />
          </Field>
          <Field label="Ubicación (inventario)" error={err.id_inventario?.message} required>
            <InventarioSelect
              idProducto={idProd || undefined}
              emptyText="Este producto no tiene inventario: créalo en Inventario"
              {...register('id_inventario')}
            />
          </Field>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Motivo" error={err.motivo_movimiento?.message} required>
          <Select options={motivosManualesOpciones('SALIDA')} placeholder={false} {...register('motivo_movimiento')} />
        </Field>
        <Field
          label="Cantidad"
          error={err.cantidad?.message}
          required
          hint="Unidades que salen de esta ubicación."
        >
          <Input type="number" inputMode="numeric" min={1} step={1} suffix="und." size="lg" {...register('cantidad')} />
        </Field>
      </div>

      {/* Vista previa del stock */}
      {inv && (
        <div
          className={cn(
            'flex flex-wrap items-center justify-between gap-3 rounded-md border px-4 py-3',
            excedeStock ? 'border-danger/40 bg-danger-soft/50' : 'border-border bg-surface-2/60',
          )}
          aria-live="polite"
        >
          <div className="flex items-baseline gap-2 font-mono tabular">
            <span className="label-stencil">Stock</span>
            <span className="text-lg font-semibold text-fg">{formatNumero(inv.stock_actual)}</span>
            <span className="text-fg-subtle" aria-hidden="true">
              →
            </span>
            <span className="sr-only">nuevo stock</span>
            <span className={cn('text-lg font-semibold', stockNuevo === undefined ? 'text-fg-subtle' : stockNuevo < 0 ? 'text-danger' : 'text-fg')}>
              {stockNuevo === undefined ? '?' : formatNumero(stockNuevo)}
            </span>
          </div>
          <StockBadge inventario={stockNuevo === undefined || stockNuevo < 0 ? inv : { ...inv, stock_actual: stockNuevo }} />
        </div>
      )}

      {excedeStock && inv && (
        <FormAlert tone="warning" title="Stock insuficiente">
          La salida ({formatNumero(cantidad)} und.) supera el stock actual de esta ubicación ({formatNumero(inv.stock_actual)} und.).
          El sistema rechazará el movimiento.
        </FormAlert>
      )}

      <Field label="Observación" error={err.observacion?.message} hint="Opcional. Ej.: n.º de guía o detalle del vencimiento.">
        <Textarea rows={2} maxLength={500} {...register('observacion')} />
      </Field>

      <FormActions onCancel={onCancel} submitting={formState.isSubmitting} submitLabel="Registrar salida" />
    </form>
  )
}

/* ------------------------------------------------------------------ */

export interface MovimientoModalProps extends Omit<MovimientoFormProps, 'onCancel'> {
  open: boolean
  onClose: () => void
}

/** MovimientoForm dentro de un Modal (se reinicia cada vez que se abre). */
export function MovimientoModal({ open, onClose, onSuccess, ...formProps }: MovimientoModalProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      size="lg"
      title="Registrar movimiento de salida"
      description="Salida por venta o vencimiento. El historial no se puede editar ni eliminar."
    >
      <MovimientoForm
        {...formProps}
        onCancel={onClose}
        onSuccess={(m) => {
          onClose()
          onSuccess?.(m)
        }}
      />
    </Modal>
  )
}
