/**
 * Formulario de proveedor (crear / editar).
 * - RUC: 11 dígitos, solo se envía al crear (el PUT no lo acepta; en edición se muestra bloqueado).
 * - Correo, teléfono y dirección opcionales (vacío → null); tiempo_entrega_estimado_dias entero ≥ 0.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import { z } from 'zod'
import { ESTADO_PROVEEDOR_OPCIONES } from '@/api/enums'
import type {EstadoProveedor, Proveedor} from '@/api/types'
import { Button, Field, Input, Select, useApiErrorHandler } from '@/components/ui'
import { MIN_PASSWORD_TEMPORAL, PasswordTemporalInput } from '@/components/CredencialesModal'
import { generarPasswordTemporal } from '@/lib/password'
import { correoOpcional, MSG, numero, numStr, texto, textoOpcional } from '@/lib/zod'

const ESTADOS = ['ACTIVO', 'INACTIVO'] as const satisfies readonly EstadoProveedor[]

const base = {
  nombre: texto({ min: 2, max: 150 }),
  correo: correoOpcional(),
  telefono: textoOpcional({ max: 20 }).refine(
    (v) => v === null || /^\+?[\d\s()-]{6,20}$/.test(v),
    'Teléfono no válido (solo dígitos, espacios, +, - o paréntesis)',
  ),
  direccion: textoOpcional({ max: 250 }),
  tiempo_entrega_estimado_dias: numero({ min: 0, entero: true }),
  estado: z.enum(ESTADOS, { error: MSG.seleccion }),
  /** Solo al crear: con correo + contraseña temporal se crea la cuenta de acceso del proveedor. Vacía = sin cuenta. */
  password_temporal: z.string().trim(),
}

const rucCreacion = z
  .string()
  .trim()
  .min(1, MSG.requerido)
  .regex(/^\d{11}$/, 'El RUC debe tener exactamente 11 dígitos')

/** En edición el RUC no se valida ni se envía (no es editable). */
export const proveedorSchemaCrear = z.object({ ...base, ruc: rucCreacion }).superRefine((v, ctx) => {
  if (v.password_temporal === '') return
  if (v.password_temporal.length < MIN_PASSWORD_TEMPORAL) ctx.addIssue({ code: 'custom', path: ['password_temporal'], message: `Mínimo ${MIN_PASSWORD_TEMPORAL} caracteres (o déjala vacía)` })
  if (!v.correo) ctx.addIssue({ code: 'custom', path: ['correo'], message: 'La cuenta de acceso necesita un correo' })
})
export const proveedorSchemaEditar = z.object({ ...base, ruc: z.string() })

export type ProveedorFormInput = z.input<typeof proveedorSchemaCrear>
export type ProveedorFormOutput = z.output<typeof proveedorSchemaCrear>


function proveedorDefaults(p?: Proveedor | null): ProveedorFormInput {
  return {
    nombre: p?.nombre ?? '',
    ruc: p?.ruc ?? '',
    correo: p?.correo ?? '',
    telefono: p?.telefono ?? '',
    direccion: p?.direccion ?? '',
    tiempo_entrega_estimado_dias: numStr(p?.tiempo_entrega_estimado_dias),
    estado: p?.estado ?? 'ACTIVO',
    password_temporal: p ? '' : generarPasswordTemporal(),
  }
}

export interface ProveedorFormProps {
  proveedor?: Proveedor | null
  onSubmit: (values: ProveedorFormOutput) => Promise<unknown>
  onSuccess?: () => void
  onCancel?: () => void
  submitLabel?: string
  formId?: string
  hideActions?: boolean
}

export function ProveedorForm({ proveedor, onSubmit, onSuccess, onCancel, submitLabel = 'Guardar', formId, hideActions }: ProveedorFormProps) {
  const handleError = useApiErrorHandler()
  const editando = !!proveedor
  const form = useForm<ProveedorFormInput, unknown, ProveedorFormOutput>({
    resolver: zodResolver(editando ? proveedorSchemaEditar : proveedorSchemaCrear),
    defaultValues: proveedorDefaults(proveedor),
  })
  const { register, handleSubmit, formState } = form
  const err = formState.errors

  const submit = handleSubmit(async (values) => {
    try {
      await onSubmit(values)
      onSuccess?.()
    } catch (e) {
      handleError(e, { form, title: editando ? 'No se pudo actualizar el proveedor' : 'No se pudo registrar el proveedor' })
    }
  })

  return (
    <form id={formId} onSubmit={submit} noValidate className="flex flex-col gap-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Razón social / nombre" error={err.nombre?.message} required className="sm:col-span-2">
          <Input placeholder="Distribuidora Andina SAC" autoComplete="organization" {...register('nombre')} />
        </Field>
        <Field
          label="RUC"
          error={err.ruc?.message}
          required={!editando}
          hint={editando ? 'El RUC no se puede modificar.' : '11 dígitos. No podrá cambiarse después.'}
        >
          <Input
            inputMode="numeric"
            maxLength={11}
            placeholder="20123456789"
            className={editando ? 'cursor-not-allowed bg-surface-2 font-mono text-fg-muted' : 'font-mono'}
            autoComplete="off"
            readOnly={editando}
            aria-readonly={editando || undefined}
            {...register('ruc')}
          />
        </Field>
        <Field label="Estado" error={err.estado?.message} required hint="Solo los proveedores activos pueden recibir órdenes nuevas.">
          <Select options={ESTADO_PROVEEDOR_OPCIONES} placeholder={false} {...register('estado')} />
        </Field>
        <Field label="Correo" error={err.correo?.message} hint="Es su usuario para iniciar sesión y donde recibe avisos.">
          <Input type="email" inputMode="email" placeholder="ventas@proveedor.com" autoComplete="off" {...register('correo')} />
        </Field>
        <Field label="Teléfono" error={err.telefono?.message}>
          <Input type="tel" inputMode="tel" placeholder="987654321" autoComplete="tel" {...register('telefono')} />
        </Field>
        <Field label="Dirección" error={err.direccion?.message} className="sm:col-span-2">
          <Input placeholder="Av. Industrial 123, Lima" autoComplete="street-address" {...register('direccion')} />
        </Field>
        <Field
          label="Tiempo de entrega estimado"
          error={err.tiempo_entrega_estimado_dias?.message}
          required
          hint="Días que suele tardar en entregar un pedido."
        >
          <Input type="number" inputMode="numeric" step={1} min={0} suffix="días" placeholder="3" {...register('tiempo_entrega_estimado_dias')} />
        </Field>
      </div>

      {!editando && (
        <Field
          label="Contraseña temporal (cuenta de acceso)"
          error={err.password_temporal?.message}
          hint="Con correo y contraseña el proveedor podrá iniciar sesión, registrar sus productos y despachar órdenes. Déjala vacía para no crear la cuenta todavía."
        >
          <Controller control={form.control} name="password_temporal" render={({ field }) => <PasswordTemporalInput value={field.value} onChange={field.onChange} />} />
        </Field>
      )}

      {!hideActions && (
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          {onCancel && (
            <Button variant="secondary" onClick={onCancel} disabled={formState.isSubmitting}>
              Cancelar
            </Button>
          )}
          <Button type="submit" loading={formState.isSubmitting}>
            {submitLabel}
          </Button>
        </div>
      )}
    </form>
  )
}
