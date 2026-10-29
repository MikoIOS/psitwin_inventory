import { inventarioDetalleId } from '@/api/inventarios'
/**
 * Formularios de inventario.
 *
 *  - <InventarioCrearForm>: producto + rack (cascada Almacén → Zona → Rack) + stock actual/mínimo/máximo.
 *    Valida mínimo ≤ máximo y que el producto no tenga ya inventario en ese rack.
 *  - <InventarioLimitesForm>: edita solo stock mínimo / máximo. El stock actual se reenvía sin cambios
 *    (los cambios de stock se registran con movimientos).
 *
 * Ambos hacen la mutación ellos mismos y muestran los errores de la API dentro del formulario.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'
import { useCreateInventario, useInventariosPorProducto, useUpdateInventario } from '@/api/inventarios'
import { useProducto } from '@/api/productos'
import { useRack } from '@/api/racks'
import { useZona } from '@/api/zonas'
import type { Inventario, InventarioCreate, InventarioUpdate } from '@/api/types'
import { useUbicaciones } from '@/api/ubicaciones'
import { ProductoSelect, NivelSelect } from '@/components/selects'
import { useRol } from '@/auth/useRol'
import { Button, Field, Input, LoadingBlock, useToast } from '@/components/ui'
import { formatNumero } from '@/lib/format'
import { idRequerido, numero, numStr } from '@/lib/zod'
import { ApiErrorAlert, FormAlert, RackCascada, useInlineApiError } from './formUtils'

type ConLimites = { stock_minimo: number; stock_maximo: number }

function validarLimites(v: ConLimites, ctx: z.RefinementCtx) {
  if (v.stock_minimo > v.stock_maximo) {
    ctx.addIssue({ code: 'custom', path: ['stock_maximo'], message: 'El máximo debe ser mayor o igual al mínimo' })
  }
}

/* ------------------------------------------------------------------ */
/* Crear                                                                */
/* ------------------------------------------------------------------ */

const crearSchema = z
  .object({
    id_producto: idRequerido('Selecciona un producto'),
    id_almacen: idRequerido('Selecciona un almacén'),
    id_zona: idRequerido('Selecciona una zona'),
    id_rack: idRequerido('Selecciona un rack'),
    id_nivel: z.string(),
    stock_actual: numero({ min: 0 }),
    stock_minimo: numero({ min: 0 }),
    stock_maximo: numero({ min: 0 }),
  })
  .superRefine(validarLimites)
  .superRefine((v, ctx) => {
    if (v.stock_actual > v.stock_maximo) {
      ctx.addIssue({ code: 'custom', path: ['stock_actual'], message: 'El stock inicial no puede superar el stock máximo' })
    }
  })

type CrearIn = z.input<typeof crearSchema>
type CrearOut = z.output<typeof crearSchema>

export interface InventarioCrearFormProps {
  /** Producto preseleccionado. */
  idProducto?: string | undefined
  /** Si true, el producto no se puede cambiar (ej. desde el detalle del producto). */
  productoFijo?: boolean
  /** Rack sugerido (ej. el rack de referencia del producto). */
  idRack?: string | null | undefined
  onSuccess?: (inv: Inventario) => void
  onCancel?: () => void
}

export function InventarioCrearForm(props: InventarioCrearFormProps) {
  const { esEmpresa } = useRol()
  const ub = useUbicaciones()
  if (props.idRack && ub.isLoading) return <LoadingBlock label="Cargando ubicaciones…" />
  const u = props.idRack ? ub.porRack.get(props.idRack) : undefined
  const defaults: CrearIn = {
    id_producto: props.idProducto ?? '',
    id_almacen: u?.almacen.id_almacen ?? '',
    id_zona: u?.zona.id_zona ?? '',
    id_rack: u?.rack.id_rack ?? '',
    id_nivel: '',
    stock_actual: '0',
    stock_minimo: esEmpresa ? '' : '0',
    stock_maximo: esEmpresa ? '' : '0',
  }
  return <CrearInner {...props} defaults={defaults} />
}

function CrearInner({ productoFijo, onSuccess, onCancel, defaults }: InventarioCrearFormProps & { defaults: CrearIn }) {
  const { esEmpresa } = useRol()
  const toast = useToast()
  const crear = useCreateInventario()
  const apiError = useInlineApiError()
  const form = useForm<CrearIn, unknown, CrearOut>({ resolver: zodResolver(crearSchema), defaultValues: defaults })
  const { register, handleSubmit, setValue, formState, control, setError } = form
  const err = formState.errors
  const [idProducto, idAlmacen, idZona, idRack] = useWatch({ control, name: ['id_producto', 'id_almacen', 'id_zona', 'id_rack'] })
  const existentes = useInventariosPorProducto(idProducto || undefined)
  const producto = useProducto(idProducto || undefined)
  const zona = useZona(idZona || undefined).data
  const rack = useRack(idRack || undefined).data
  const p = producto.data

  const submit = handleSubmit(async ({ id_almacen: _a, id_zona: _z, ...values }) => {
    apiError.clear()
    if (existentes.data?.some((inv) => inv.id_rack === values.id_rack && (inv.id_nivel ?? '') === values.id_nivel)) {
      setError('id_rack', { message: 'Este producto ya tiene inventario en ese rack' }, { shouldFocus: true })
      return
    }
    // El backend también lo valida (409); aquí se avisa antes, en el campo que corresponde.
    if (p?.requiere_refrigeracion && zona && !zona.refrigerada) {
      setError('id_zona', { message: 'El producto requiere refrigeración y esta zona no es refrigerada' }, { shouldFocus: true })
      return
    }
    const libre = rack ? rack.libre_kg : null
    const carga = values.stock_actual * (p?.peso ?? 0)
    if (libre !== null && carga > libre) {
      setError('stock_actual', { message: `Pesa ${formatNumero(carga)} kg y el rack solo soporta ${formatNumero(libre)} kg más` }, { shouldFocus: true })
      return
    }
    const body: InventarioCreate = { ...values, id_nivel: values.id_nivel || null, id_almacen: idAlmacen }
    try {
      const inv = await crear.mutateAsync(body)
      toast.success('Inventario creado')
      onSuccess?.(inv)
    } catch (e) {
      apiError.handle(e, { form, titulo: 'No se pudo crear el inventario' })
    }
  })

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <ApiErrorAlert error={apiError.error} />
      <Field label="Nivel de destino"><NivelSelect idRack={idRack || undefined} {...register('id_nivel')} /></Field>

      {productoFijo ? (
        <div className="rounded-md border border-border bg-surface-2/60 px-4 py-3">
          <p className="label-stencil">Producto</p>
          <p className="font-semibold text-fg">{producto.data?.nombre ?? '…'}</p>
        </div>
      ) : (
        <Field label="Producto" error={err.id_producto?.message} required>
          <ProductoSelect {...register('id_producto')} />
        </Field>
      )}
      {p && (
        <FormAlert tone="info" title={p.requiere_refrigeracion ? 'Este producto requiere refrigeración' : 'Este producto no requiere refrigeración'}>
          {p.requiere_refrigeracion
            ? `Conservar entre ${p.temperatura_min_almacenamiento ?? '—'} y ${p.temperatura_max_almacenamiento ?? '—'} °C: solo puede ir en una zona refrigerada.`
            : 'Puede ubicarse en cualquier zona.'}
          {p.peso ? ` Peso por unidad: ${formatNumero(p.peso)} kg.` : ''}
        </FormAlert>
      )}

      <RackCascada
        legend="Ubicación (rack)"
        soloDisponibles
        idAlmacen={idAlmacen}
        idZona={idZona}
        registros={{
          almacen: register('id_almacen', {
            onChange: () => {
              setValue('id_zona', '')
              setValue('id_nivel', '')
              setValue('id_rack', '')
            },
          }),
          zona: register('id_zona', { onChange: () => { setValue('id_rack', ''); setValue('id_nivel', '') } }),
          rack: register('id_rack', { onChange: () => setValue('id_nivel', '') }),
        }}
        errores={{ almacen: err.id_almacen?.message, zona: err.id_zona?.message, rack: err.id_rack?.message }}
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Stock inicial" error={err.stock_actual?.message} required hint="No puede superar el stock máximo.">
          <Input type="number" readOnly min={0} step="any" suffix="" {...register('stock_actual')} />
        </Field>
        <Field label="Stock mínimo" error={err.stock_minimo?.message} required hint="Debajo de este valor: stock bajo.">
          <Input type="number" disabled={!esEmpresa} min={0} step="any" suffix="" placeholder="20" {...register('stock_minimo')} />
        </Field>
        <Field label="Stock máximo" error={err.stock_maximo?.message} required hint="Encima de este valor: sobre stock.">
          <Input type="number" disabled={!esEmpresa} min={0} step="any" suffix="" placeholder="200" {...register('stock_maximo')} />
        </Field>
      </div>

      <FormActions onCancel={onCancel} submitting={formState.isSubmitting} submitLabel="Crear inventario" />
    </form>
  )
}

/* ------------------------------------------------------------------ */
/* Editar límites                                                       */
/* ------------------------------------------------------------------ */

const limitesSchema = z
  .object({
    stock_minimo: numero({ min: 0 }),
    stock_maximo: numero({ min: 0 }),
  })
  .superRefine(validarLimites)

type LimIn = z.input<typeof limitesSchema>
type LimOut = z.output<typeof limitesSchema>

export interface InventarioLimitesFormProps {
  inventario: Inventario
  onSuccess?: (inv: Inventario) => void
  onCancel?: () => void
}

export function InventarioLimitesForm({ inventario, onSuccess, onCancel }: InventarioLimitesFormProps) {
  const toast = useToast()
  const actualizar = useUpdateInventario()
  const apiError = useInlineApiError()
  const form = useForm<LimIn, unknown, LimOut>({
    resolver: zodResolver(limitesSchema),
    defaultValues: { stock_minimo: numStr(inventario.stock_minimo), stock_maximo: numStr(inventario.stock_maximo) },
  })
  const { register, handleSubmit, formState } = form
  const err = formState.errors

  const submit = handleSubmit(async (values) => {
    apiError.clear()
    const body: InventarioUpdate = values
    try {
      const inv = await actualizar.mutateAsync({ id: inventarioDetalleId(inventario), body })
      toast.success('Límites de stock actualizados')
      onSuccess?.(inv)
    } catch (e) {
      apiError.handle(e, { form, titulo: 'No se pudo actualizar el inventario' })
    }
  })

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <ApiErrorAlert error={apiError.error} />
      <FormAlert tone="info" title={`Stock actual: ${formatNumero(inventario.stock_actual)} und.`}>
        El stock actual no se edita: sube con las recepciones y baja con los movimientos de salida.
      </FormAlert>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Stock mínimo" error={err.stock_minimo?.message} required>
          <Input type="number" inputMode="numeric" min={0} step={1} suffix="und." {...register('stock_minimo')} />
        </Field>
        <Field label="Stock máximo" error={err.stock_maximo?.message} required>
          <Input type="number" inputMode="numeric" min={0} step={1} suffix="und." {...register('stock_maximo')} />
        </Field>
      </div>
      <FormActions onCancel={onCancel} submitting={formState.isSubmitting} submitLabel="Guardar límites" />
    </form>
  )
}

/* ------------------------------------------------------------------ */

export function FormActions({ onCancel, submitting, submitLabel }: { onCancel?: (() => void) | undefined; submitting: boolean; submitLabel: string }) {
  return (
    <div className="flex flex-col-reverse gap-2 border-t border-border pt-4 sm:flex-row sm:justify-end">
      {onCancel && (
        <Button variant="secondary" onClick={onCancel} disabled={submitting}>
          Cancelar
        </Button>
      )}
      <Button type="submit" loading={submitting} size="lg" className="sm:h-10 sm:text-sm">
        {submitLabel}
      </Button>
    </div>
  )
}
