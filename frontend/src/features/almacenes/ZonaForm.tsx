/**
 * Formulario de zona (crear / editar) + modal.
 * El tipo sale del catálogo de alimentos. «Refrigerada» la decide la empresa (el tipo solo sugiere el valor inicial):
 * en una zona refrigerada cada rack lleva su temperatura mín/máx. La temperatura de la zona no se pide (null).
 * `capacidad` del backend = número de NIVELES de la zona (un rack por nivel).
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useId } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import type { Zona, ZonaUpdate } from '@/api/types'
import { useCreateZona, useUpdateZona } from '@/api/zonas'
import { Button, Checkbox, Field, Input, Modal, Select, useApiErrorHandler, useToast } from '@/components/ui'
import { TIPOS_ZONA, tipoZona, zonaRefrigerada } from '@/lib/catalogo'
import { MSG, numero, numStr, texto } from '@/lib/zod'

export const zonaSchema = z
  .object({
    nombre: texto({ min: 2, max: 100 }),
    tipo_zona: z.string().min(1, MSG.seleccion),
    capacidad: numero({ min: 1, entero: true }),
    refrigerada: z.boolean(),
  })
  .transform((v) => ({ ...v, temperatura_min: null, temperatura_max: null }))

type In = z.input<typeof zonaSchema>
type Out = z.output<typeof zonaSchema>

const _check: (v: Out) => ZonaUpdate = (v) => v
void _check

function defaults(z?: Zona | null): In {
  return {
    nombre: z?.nombre ?? '',
    // Un tipo antiguo (fuera del catálogo) obliga a elegir uno nuevo.
    tipo_zona: tipoZona(z?.tipo_zona) ? z!.tipo_zona : '',
    capacidad: numStr(z?.capacidad),
    refrigerada: z?.refrigerada ?? false,
  }
}

interface ZonaFormProps {
  zona?: Zona | null
  formId: string
  onSubmit: (body: ZonaUpdate) => Promise<unknown>
  onSuccess: () => void
}

export function ZonaForm({ zona, formId, onSubmit, onSuccess }: ZonaFormProps) {
  const handleError = useApiErrorHandler()
  const form = useForm<In, unknown, Out>({ resolver: zodResolver(zonaSchema), defaultValues: defaults(zona) })
  const { register, handleSubmit, formState, setValue } = form
  const err = formState.errors

  const submit = handleSubmit(async (values) => {
    try {
      await onSubmit(values)
      onSuccess()
    } catch (e) {
      handleError(e, { form, title: 'No se pudo guardar la zona' })
    }
  })

  return (
    <form id={formId} onSubmit={submit} noValidate className="grid gap-4 sm:grid-cols-2">
      <Field label="Nombre de la zona" error={err.nombre?.message} required>
        <Input placeholder="Zona A" {...register('nombre')} />
      </Field>
      <Field
        label="Tipo de zona"
        error={err.tipo_zona?.message}
        required
      >
        <Select
          options={TIPOS_ZONA.map((t) => ({ value: t.nombre, label: t.nombre }))}
          {...register('tipo_zona', { onChange: (e: { target: { value: string } }) => setValue('refrigerada', zonaRefrigerada(e.target.value)) })}
        />
      </Field>
      <Checkbox
        className="sm:col-span-2"
        label="Zona refrigerada"
        description="Cada rack de la zona tendrá temperatura mínima y máxima; solo ahí se guardan productos que requieren refrigeración."
        {...register('refrigerada')}
      />
      <Field label="Niveles" error={err.capacidad?.message} required className="sm:col-span-2" hint="Cantidad de racks que puede tener la zona (un rack por nivel).">
        <Input type="number" inputMode="numeric" step={1} min={1} placeholder="5" {...register('capacidad')} />
      </Field>
    </form>
  )
}

export interface ZonaFormModalProps {
  open: boolean
  idAlmacen: string
  /** null/undefined = crear. */
  zona?: Zona | null
  onClose: () => void
}

export function ZonaFormModal({ open, idAlmacen, zona, onClose }: ZonaFormModalProps) {
  const formId = useId()
  const toast = useToast()
  const crear = useCreateZona()
  const editar = useUpdateZona()
  const pending = crear.isPending || editar.isPending

  return (
    <Modal
      open={open}
      onClose={onClose}
      dismissable={!pending}
      title={zona ? 'Editar zona' : 'Nueva zona'}
      {...(zona ? { description: zona.nombre } : {})}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={pending}>
            Cancelar
          </Button>
          <Button type="submit" form={formId} loading={pending}>
            {zona ? 'Guardar cambios' : 'Crear zona'}
          </Button>
        </>
      }
    >
      <ZonaForm
        formId={formId}
        zona={zona ?? null}
        onSubmit={async (body) => {
          if (zona) await editar.mutateAsync({ id: zona.id_zona, body })
          else await crear.mutateAsync({ ...body, id_almacen: idAlmacen })
          toast.success(zona ? 'Zona actualizada' : 'Zona creada')
        }}
        onSuccess={onClose}
      />
    </Modal>
  )
}
