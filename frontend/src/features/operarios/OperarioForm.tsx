/**
 * Formulario de cuenta de operario (crear / editar). Solo lo usa la EMPRESA.
 * Al crear: almacén (el único que verá), correo de acceso y contraseña temporal (generar / copiar); el operario
 * deberá cambiarla en su primer ingreso. Al editar la contraseña no se toca (usar «Restablecer contraseña»).
 * Turno y estado son texto libre en el backend: se ofrecen los valores conocidos y se conserva cualquier otro.
 *
 * `onSubmit` recibe los valores validados y debe devolver una promesa; si rechaza, el form muestra el error.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { Controller, useForm } from 'react-hook-form'
import { z } from 'zod'
import { ESTADO_OPERARIO_OPCIONES, etiquetaEstadoOperario, etiquetaTurno, TURNO_OPCIONES, type Opcion } from '@/api/enums'
import type { Operario } from '@/api/types'
import { MIN_PASSWORD_TEMPORAL, PasswordTemporalInput } from '@/components/CredencialesModal'
import { AlmacenSelect } from '@/components/selects'
import { Button, Field, Input, Select, useApiErrorHandler } from '@/components/ui'
import { generarPasswordTemporal } from '@/lib/password'
import { MSG, texto } from '@/lib/zod'

const base = {
  nombre: texto({ min: 2, max: 100 }),
  apellido: texto({ min: 2, max: 100 }),
  cargo: texto({ min: 2, max: 100 }),
  id_almacen: z.string().min(1, 'Elige el almacén del operario'),
  turno: texto({ min: 2, max: 50, mensaje: MSG.seleccion }),
  estado: texto({ min: 2, max: 50, mensaje: MSG.seleccion }),
}
/** Crear: correo y contraseña temporal obligatorios. Editar: correo opcional (cuentas antiguas sin correo), sin contraseña. */
const esquema = (editando: boolean) =>
  z
    .object({ ...base, correo: z.string().trim().toLowerCase(), password_temporal: z.string().trim() })
    .superRefine((v, ctx) => {
      if (v.correo === '' ? !editando : !z.email().safeParse(v.correo).success) {
        ctx.addIssue({ code: 'custom', path: ['correo'], message: v.correo === '' ? MSG.requerido : MSG.correo })
      }
      if (!editando && v.password_temporal.length < MIN_PASSWORD_TEMPORAL) {
        ctx.addIssue({ code: 'custom', path: ['password_temporal'], message: `Mínimo ${MIN_PASSWORD_TEMPORAL} caracteres` })
      }
    })
export const operarioSchema = esquema(false)

/** Opciones conocidas + el valor actual si es uno desconocido (texto libre del backend). */
function conValorActual(opciones: Opcion[], actual: string | undefined, etiqueta: (v: string) => string): Opcion[] {
  if (!actual || opciones.some((o) => o.value === actual)) return opciones
  return [...opciones, { value: actual, label: `${etiqueta(actual)} (actual)` }]
}

export type OperarioFormInput = z.input<typeof operarioSchema>
export type OperarioFormOutput = z.output<typeof operarioSchema>

export const CARGOS_SUGERIDOS = ['Almacenero', 'Supervisor', 'Montacarguista', 'Auxiliar de almacén', 'Jefe de almacén', 'Recepcionista', 'Despachador']

function operarioDefaults(o?: Operario | null, idAlmacen?: string): OperarioFormInput {
  return {
    id_almacen: o?.id_almacen ?? idAlmacen ?? '',
    nombre: o?.nombre ?? '',
    apellido: o?.apellido ?? '',
    cargo: o?.cargo ?? '',
    correo: o?.correo ?? '',
    password_temporal: o ? '' : generarPasswordTemporal(),
    turno: o?.turno ?? 'MAÑANA',
    estado: o?.estado ?? 'ACTIVO',
  }
}

export interface OperarioFormProps {
  operario?: Operario | null
  onSubmit: (values: OperarioFormOutput) => Promise<unknown>
  onSuccess?: () => void
  onCancel?: () => void
  submitLabel?: string
  formId?: string
  hideActions?: boolean
  /** Almacén preseleccionado al crear. */
  idAlmacenInicial?: string | undefined
}

export function OperarioForm({
  operario,
  onSubmit,
  onSuccess,
  onCancel,
  submitLabel = 'Guardar',
  formId,
  hideActions,
  idAlmacenInicial,
}: OperarioFormProps) {
  const handleError = useApiErrorHandler()
  const editando = !!operario
  const form = useForm<OperarioFormInput, unknown, OperarioFormOutput>({
    resolver: zodResolver(esquema(editando)),
    defaultValues: operarioDefaults(operario, idAlmacenInicial),
  })
  const { register, handleSubmit, formState, control } = form
  const err = formState.errors

  const submit = handleSubmit(async (values) => {
    try {
      await onSubmit(values)
      onSuccess?.()
    } catch (e) {
      handleError(e, { form, title: editando ? 'No se pudo actualizar el operario' : 'No se pudo registrar el operario' })
    }
  })

  return (
    <form id={formId} onSubmit={submit} noValidate className="flex flex-col gap-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Nombre" error={err.nombre?.message} required>
          <Input placeholder="Carlos" autoComplete="off" {...register('nombre')} />
        </Field>
        <Field label="Apellido" error={err.apellido?.message} required>
          <Input placeholder="Pérez" autoComplete="off" {...register('apellido')} />
        </Field>
        <Field label="Cargo" error={err.cargo?.message} required className="sm:col-span-2">
          <Input placeholder="Almacenero" list="cargos-operario" autoComplete="off" {...register('cargo')} />
        </Field>
        <Field label="Correo de acceso" error={err.correo?.message} required={!editando} className="sm:col-span-2" hint="Es su usuario para iniciar sesión.">
          <Input type="email" placeholder="operario@empresa.com" autoComplete="off" {...register('correo')} />
        </Field>
        {!editando && (
          <Field
            label="Contraseña temporal"
            error={err.password_temporal?.message}
            required
            className="sm:col-span-2"
            hint="Entrégasela al operario: deberá cambiarla en su primer ingreso."
          >
            <Controller control={control} name="password_temporal" render={({ field }) => <PasswordTemporalInput value={field.value} onChange={field.onChange} />} />
          </Field>
        )}
        <datalist id="cargos-operario">
          {CARGOS_SUGERIDOS.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
        <Field
          label="Almacén"
          error={err.id_almacen?.message}
          required
          className="sm:col-span-2"
          hint="El operario solo ve y trabaja en este almacén (zonas, racks, inventario, solicitudes y recepciones)."
        >
          <AlmacenSelect {...register('id_almacen')} />
        </Field>
        <Field label="Turno" error={err.turno?.message} required>
          <Select options={conValorActual(TURNO_OPCIONES, operario?.turno, etiquetaTurno)} placeholder={false} {...register('turno')} />
        </Field>
        <Field
          label="Estado"
          error={err.estado?.message}
          required
          hint="Un operario inactivo no puede iniciar sesión."
        >
          <Select options={conValorActual(ESTADO_OPERARIO_OPCIONES, operario?.estado, etiquetaEstadoOperario)} placeholder={false} {...register('estado')} />
        </Field>
      </div>

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
