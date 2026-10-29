/**
 * Formularios de producto según el rol (docs/ROLES.md §4):
 *  - `ProductoForm` (PROVEEDOR): crea / edita SUS productos. El tipo de zona se elige del catálogo solo para
 *    desplegar la cascada familia → categoría (no se guarda). Peso obligatorio (kg por unidad). Sin rack.
 *    Si requiere refrigeración: temperaturas mín/máx obligatorias (mín ≤ máx); si no, se envían null.
 *  - `RackReferenciaForm` (OPERARIO): asigna el rack de referencia del producto (`PUT /productos/{id} { id_rack }`).
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'
import { useCreateProducto, useUpdateProducto } from '@/api/productos'
import type { Producto, ProductoCreate, ProductoUpdate } from '@/api/types'
import { useUbicaciones } from '@/api/ubicaciones'
import { Checkbox, Field, Input, LoadingBlock, Select, useToast } from '@/components/ui'
import { categoriasDe, familiasDe, TIPOS_ZONA, tipoDeFamilia } from '@/lib/catalogo'
import { idRequerido, numero, numeroOpcional, numStr, texto, textoOpcional } from '@/lib/zod'
import { FormActions } from '@/features/inventario/InventarioForm'
import { ApiErrorAlert, RackCascada, useInlineApiError } from '@/features/inventario/formUtils'

const schema = z
  .object({
    unidad: z.enum(['kg', 'unidad']),
    activo: z.boolean(),
    nombre: texto({ max: 150 }),
    categoria: z.string().min(1, 'Selecciona una categoría'),
    familia: z.string().min(1, 'Selecciona una familia'),
    marca: textoOpcional({ max: 100 }),
    // El peso es obligatorio: con él se calcula la carga de los racks (kg). La cantidad es opcional.
    peso: numero({ mayorQue: 0 }),
    volumen: numeroOpcional({ mayorQue: 0 }),
    requiere_refrigeracion: z.boolean(),
    temperatura_min_almacenamiento: numeroOpcional({ min: -100, max: 100 }),
    temperatura_max_almacenamiento: numeroOpcional({ min: -100, max: 100 }),
    lead_time_dias: numero({ min: 0, entero: true }),
    vida_util_dias: numero({ min: 1, entero: true }),
    /** Solo para la cascada del catálogo (no se envía). */
    tipo: z.string().min(1, 'Selecciona el tipo de producto'),
  })
  .superRefine((v, ctx) => {
    if (!v.requiere_refrigeracion) return
    const min = v.temperatura_min_almacenamiento
    const max = v.temperatura_max_almacenamiento
    if (min === null) ctx.addIssue({ code: 'custom', path: ['temperatura_min_almacenamiento'], message: 'Indica la temperatura mínima' })
    if (max === null) ctx.addIssue({ code: 'custom', path: ['temperatura_max_almacenamiento'], message: 'Indica la temperatura máxima' })
    if (min !== null && max !== null && min > max) {
      ctx.addIssue({ code: 'custom', path: ['temperatura_max_almacenamiento'], message: 'La máxima debe ser mayor o igual a la mínima' })
    }
  })
  .transform(({ tipo: _t, ...v }) => ({
    ...v,
    temperatura_min_almacenamiento: v.requiere_refrigeracion ? v.temperatura_min_almacenamiento : null,
    temperatura_max_almacenamiento: v.requiere_refrigeracion ? v.temperatura_max_almacenamiento : null,
  }))

type In = z.input<typeof schema>
type Out = z.output<typeof schema>

// Garantiza en compilación que la salida coincide con los bodies del backend.
const _checkCreate: (v: Out) => ProductoCreate = (v) => ({ ...v, stock: 0 })
const _checkUpdate: (v: Out) => ProductoUpdate = (v) => v
void _checkCreate
void _checkUpdate

export interface ProductoFormProps {
  producto?: Producto | null
  onSuccess?: (p: Producto) => void
  onCancel?: () => void
}

export function ProductoForm({ producto, onSuccess, onCancel }: ProductoFormProps) {
  const p = producto
  const defaults: In = {
    unidad: p?.unidad ?? 'unidad',
    activo: p?.activo ?? true,
    nombre: p?.nombre ?? '',
    categoria: p?.categoria ?? '',
    familia: p?.familia ?? '',
    marca: p?.marca ?? '',
    peso: numStr(p?.peso),
    volumen: numStr(p?.volumen),
    requiere_refrigeracion: p?.requiere_refrigeracion ?? false,
    temperatura_min_almacenamiento: numStr(p?.temperatura_min_almacenamiento),
    temperatura_max_almacenamiento: numStr(p?.temperatura_max_almacenamiento),
    lead_time_dias: numStr(p?.lead_time_dias),
    vida_util_dias: numStr(p?.vida_util_dias),
    tipo: tipoDeFamilia(p?.familia),
  }
  const toast = useToast()
  const crear = useCreateProducto()
  const actualizar = useUpdateProducto()
  const apiError = useInlineApiError()

  const form = useForm<In, unknown, Out>({ resolver: zodResolver(schema), defaultValues: defaults })
  const { register, handleSubmit, setValue, formState, control } = form
  const err = formState.errors
  const [refrigera, tipo, familia, categoria, unit] = useWatch({ control, name: ['requiere_refrigeracion', 'tipo', 'familia', 'categoria', 'unidad'] })
  // Los valores actuales fuera del catálogo (productos antiguos) se conservan como opción.
  const conActual = (lista: string[], actual: string) => [...new Set([...lista, ...(actual ? [actual] : [])])].map((v) => ({ value: v, label: v }))
  const submit = handleSubmit(async (values) => {
    apiError.clear()
    try {
      const guardado = producto
        ? await actualizar.mutateAsync({ id: producto.id_producto, body: values })
        : await crear.mutateAsync({ ...values, stock: 0 })
      toast.success(producto ? 'Producto actualizado' : 'Producto disponible en el catálogo; configura ahora su oferta')
      onSuccess?.(guardado)
    } catch (e) {
      apiError.handle(e, { form, titulo: producto ? 'No se pudo actualizar el producto' : 'No se pudo crear el producto' })
    }
  })

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <ApiErrorAlert error={apiError.error} />

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Unidad de comercialización" required><Select disabled={!!p} options={[{ value: 'kg', label: 'Kilogramo (kg)' }, { value: 'unidad', label: 'Unidad indivisible' }]} {...register('unidad', { onChange: e => { if (e.target.value === 'kg') setValue('peso', '1') } })} /></Field>
        <Checkbox label="Producto activo" {...register('activo')} />
        <Field label="Nombre" error={err.nombre?.message} required className="sm:col-span-2">
          <Input placeholder="Arroz extra 5 kg" {...register('nombre')} />
        </Field>
        <Field label="Marca" error={err.marca?.message} className="sm:col-span-2">
          <Input placeholder="Marca Demo" {...register('marca')} />
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Tipo de producto" error={err.tipo?.message} required hint="Define las familias y categorías disponibles.">
          <Select
            options={TIPOS_ZONA.map((t) => ({ value: t.nombre, label: t.nombre }))}
            {...register('tipo', {
              onChange: () => {
                setValue('familia', '')
                setValue('categoria', '')
              },
            })}
          />
        </Field>
        <Field label="Familia" error={err.familia?.message} required {...(!tipo ? { hint: 'Elige primero el tipo.' } : {})}>
          <Select options={conActual(familiasDe(tipo), familia)} disabled={!tipo} {...register('familia', { onChange: () => setValue('categoria', '') })} />
        </Field>
        <Field label="Categoría" error={err.categoria?.message} required {...(!familia ? { hint: 'Elige primero la familia.' } : {})}>
          <Select options={conActual(categoriasDe(tipo, familia), categoria)} disabled={!familia} {...register('categoria')} />
        </Field>
      </div>

      <fieldset className="rounded-md border border-border p-4">
        <legend className="label-stencil px-1">Características y abastecimiento</legend>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Peso" error={err.peso?.message} required hint={unit === 'kg' ? 'Se comercializa por kilogramo; el factor de carga es 1.' : 'Por unidad. Con él se calcula la carga de los racks.'}>
            <Input type="number" inputMode="decimal" step="any" min={0} suffix="kg" placeholder="1.0" readOnly={unit === 'kg'} {...register('peso')} />
          </Field>
          {/* El backend guarda este dato en el campo `volumen`. */}
          <Field label="Cantidad" error={err.volumen?.message} hint="Opcional. Unidades por empaque.">
            <Input type="number" inputMode="decimal" step="any" min={0} suffix="und." placeholder="12" {...register('volumen')} />
          </Field>
          <Field label="Tiempo de reposición" error={err.lead_time_dias?.message} required hint="Lead time del proveedor.">
            <Input type="number" inputMode="numeric" step={1} min={0} suffix="días" placeholder="3" {...register('lead_time_dias')} />
          </Field>
          <Field label="Vida útil" error={err.vida_util_dias?.message} required>
            <Input type="number" inputMode="numeric" step={1} min={1} suffix="días" placeholder="180" {...register('vida_util_dias')} />
          </Field>
        </div>
      </fieldset>

      <fieldset className="rounded-md border border-border p-4">
        <legend className="label-stencil px-1">Conservación</legend>
        <Checkbox
          label="Requiere refrigeración"
          description="Indica el rango de temperatura de almacenamiento."
          {...register('requiere_refrigeracion')}
        />
        {refrigera && (
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <Field label="Temperatura mínima" error={err.temperatura_min_almacenamiento?.message} required>
              <Input type="number" inputMode="decimal" step="any" suffix="°C" placeholder="2" {...register('temperatura_min_almacenamiento')} />
            </Field>
            <Field label="Temperatura máxima" error={err.temperatura_max_almacenamiento?.message} required>
              <Input type="number" inputMode="decimal" step="any" suffix="°C" placeholder="8" {...register('temperatura_max_almacenamiento')} />
            </Field>
          </div>
        )}
      </fieldset>

      <FormActions onCancel={onCancel} submitting={formState.isSubmitting} submitLabel={producto ? 'Guardar cambios' : 'Crear producto'} />
    </form>
  )
}

/* ------------------------------------------------------------------ */

const rackSchema = z.object({
  id_almacen: idRequerido('Selecciona un almacén'),
  id_zona: idRequerido('Selecciona una zona'),
  id_rack: idRequerido('Selecciona un rack'),
})
type RackIn = z.input<typeof rackSchema>

/** OPERARIO: asigna el rack de referencia de un producto (dónde se guarda habitualmente). */
export function RackReferenciaForm({ producto, onSuccess, onCancel }: { producto: Producto; onSuccess?: (p: Producto) => void; onCancel?: () => void }) {
  const ub = useUbicaciones()
  if (ub.isLoading) return <LoadingBlock label="Cargando ubicaciones…" />
  const u = producto.id_rack ? ub.porRack.get(producto.id_rack) : undefined
  // El operario solo tiene un almacén: va preseleccionado.
  const idAlmacen = u?.almacen.id_almacen ?? (ub.almacenes.length === 1 ? ub.almacenes[0]!.id_almacen : '')
  return (
    <RackReferenciaInner
      producto={producto}
      defaults={{ id_almacen: idAlmacen, id_zona: u?.zona.id_zona ?? '', id_rack: u?.rack.id_rack ?? '' }}
      {...(onSuccess ? { onSuccess } : {})}
      {...(onCancel ? { onCancel } : {})}
    />
  )
}

function RackReferenciaInner({ producto, defaults, onSuccess, onCancel }: { producto: Producto; defaults: RackIn; onSuccess?: (p: Producto) => void; onCancel?: () => void }) {
  const toast = useToast()
  const actualizar = useUpdateProducto()
  const apiError = useInlineApiError()
  const form = useForm<RackIn>({ resolver: zodResolver(rackSchema), defaultValues: defaults })
  const { register, handleSubmit, setValue, formState, control } = form
  const err = formState.errors
  const [idAlmacen, idZona] = useWatch({ control, name: ['id_almacen', 'id_zona'] })

  const submit = handleSubmit(async ({ id_rack }) => {
    apiError.clear()
    try {
      const p = await actualizar.mutateAsync({ id: producto.id_producto, body: { id_rack } })
      toast.success('Rack de referencia asignado')
      onSuccess?.(p)
    } catch (e) {
      apiError.handle(e, { form, titulo: 'No se pudo asignar el rack' })
    }
  })

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-5">
      <ApiErrorAlert error={apiError.error} />
      <RackCascada
        legend="Rack de referencia"
        hint="Dónde se guarda habitualmente este producto. El stock real por ubicación se gestiona en Inventario."
        idAlmacen={idAlmacen}
        idZona={idZona}
        registros={{
          almacen: register('id_almacen', {
            onChange: () => {
              setValue('id_zona', '')
              setValue('id_rack', '')
            },
          }),
          zona: register('id_zona', { onChange: () => setValue('id_rack', '') }),
          rack: register('id_rack'),
        }}
        errores={{ almacen: err.id_almacen?.message, zona: err.id_zona?.message, rack: err.id_rack?.message }}
      />
      <FormActions onCancel={onCancel} submitting={formState.isSubmitting} submitLabel="Asignar rack" />
    </form>
  )
}
