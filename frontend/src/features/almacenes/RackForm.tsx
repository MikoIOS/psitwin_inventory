/**
 * Modal de rack, con dos usos según el rol (docs/ROLES.md):
 *  - CREAR (EMPRESA): código, nivel (un rack por nivel: solo se ofrecen los niveles libres de la zona), carga máxima
 *    en kg y, si la zona es refrigerada, temperatura mín/máx (obligatorias). Nace Libre.
 *  - EDITAR (OPERARIO): solo estado (Libre / Lleno / No disponible) y temperatura. Código, nivel y carga no se editan
 *    (la empresa borra y recrea el rack).
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useId } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { ESTADO_RACK_OPCIONES, ESTADOS_RACK_EDITABLES } from '@/api/enums'
import { useCreateRack, useUpdateRack } from '@/api/racks'
import type { EstadoRackEditable, Rack } from '@/api/types'
import { Button, Field, Input, Modal, Select, useApiErrorHandler, useToast } from '@/components/ui'
import { MSG, numero, numeroOpcional, numStr, texto } from '@/lib/zod'

const esquema = (editando: boolean, refrigerada: boolean) =>
  z
    .object({
      codigo: editando ? z.string() : texto({ max: 50 }).transform((v) => v.toUpperCase()),
      nivel: editando ? z.string().transform(Number) : numero({ min: 1, entero: true }),
      capacidad: editando ? z.string().transform(Number) : numero({ mayorQue: 0 }),
      estado: z.string().min(1, MSG.seleccion).pipe(z.enum(ESTADOS_RACK_EDITABLES, { error: MSG.seleccion })),
      temperatura_min: numeroOpcional(),
      temperatura_max: numeroOpcional(),
    })
    .superRefine((v, ctx) => {
      if (!refrigerada) return
      if (v.temperatura_min === null) ctx.addIssue({ code: 'custom', path: ['temperatura_min'], message: MSG.requerido })
      if (v.temperatura_max === null) ctx.addIssue({ code: 'custom', path: ['temperatura_max'], message: MSG.requerido })
      if (v.temperatura_min !== null && v.temperatura_max !== null && v.temperatura_min > v.temperatura_max) {
        ctx.addIssue({ code: 'custom', path: ['temperatura_max'], message: 'Debe ser mayor o igual a la mínima' })
      }
    })

type Esquema = ReturnType<typeof esquema>
type In = z.input<Esquema>
type Out = z.output<Esquema>

const esEditable = (e: string): e is EstadoRackEditable => (ESTADOS_RACK_EDITABLES as readonly string[]).includes(e)

export interface RackFormModalProps {
  open: boolean
  idZona: string
  /** null/undefined = crear (EMPRESA). Con rack = editar estado / temperatura (OPERARIO). */
  rack?: Rack | null
  /** La zona es refrigerada: el rack lleva temperatura mín/máx. */
  refrigerada: boolean
  /** Niveles de la zona (zona.capacidad). */
  niveles: number
  /** Niveles que ya tienen rack en la zona. */
  nivelesOcupados: number[]
  onClose: () => void
  onGuardado?: (rack: Rack) => void
}

/** Se monta solo mientras está abierto, así el formulario arranca siempre con los valores del rack actual. */
export function RackFormModal(props: RackFormModalProps) {
  return props.open ? <RackFormModalAbierto {...props} /> : null
}

function RackFormModalAbierto({ open, idZona, rack, refrigerada, niveles, nivelesOcupados, onClose, onGuardado }: RackFormModalProps) {
  const libres = Array.from({ length: niveles }, (_, i) => i + 1).filter((n) => !nivelesOcupados.includes(n))
  const formId = useId()
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const crear = useCreateRack()
  const editar = useUpdateRack()
  const pending = crear.isPending || editar.isPending
  const editando = !!rack

  const form = useForm<In, unknown, Out>({
    resolver: zodResolver(esquema(editando, refrigerada)),
    defaultValues: {
      codigo: rack?.codigo ?? '',
      nivel: numStr(rack?.nivel ?? libres[0]),
      capacidad: numStr(rack?.capacidad),
      estado: rack ? (esEditable(rack.estado) ? rack.estado : '') : 'DISPONIBLE',
      temperatura_min: numStr(rack?.temperatura_min),
      temperatura_max: numStr(rack?.temperatura_max),
    },
  })
  const { register, handleSubmit, formState } = form
  const err = formState.errors

  const submit = handleSubmit(async (v) => {
    const temperatura = refrigerada ? { temperatura_min: v.temperatura_min, temperatura_max: v.temperatura_max } : {}
    try {
      const res = rack
        ? await editar.mutateAsync({ id: rack.id_rack, body: { estado: v.estado, ...temperatura } })
        : await crear.mutateAsync({ id_zona: idZona, codigo: v.codigo, nivel: v.nivel, capacidad: v.capacidad, ...temperatura })
      toast.success(rack ? 'Rack actualizado' : 'Rack creado')
      onGuardado?.(res)
      onClose()
    } catch (e) {
      handleError(e, { form, title: 'No se pudo guardar el rack' })
    }
  })

  return (
    <Modal
      open={open}
      onClose={onClose}
      dismissable={!pending}
      size="sm"
      title={rack ? `Rack ${rack.codigo}` : 'Nuevo rack'}
      {...(rack ? { description: `Nivel ${rack.nivel} · carga máxima ${rack.capacidad} kg` } : {})}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={pending}>
            Cancelar
          </Button>
          <Button type="submit" form={formId} loading={pending} disabled={!rack && libres.length === 0}>
            {rack ? 'Guardar cambios' : 'Crear rack'}
          </Button>
        </>
      }
    >
      <form id={formId} onSubmit={submit} noValidate className="grid gap-4 sm:grid-cols-2">
        {rack ? (
          <Field label="Estado" error={err.estado?.message} required className="sm:col-span-2" hint="Solo los racks Libres reciben mercadería.">
            <Select options={ESTADO_RACK_OPCIONES} {...register('estado')} />
          </Field>
        ) : (
          <>
            <Field label="Código" error={err.codigo?.message} required className="sm:col-span-2" hint="Identificador visible en etiquetas, p. ej. A-01.">
              <Input placeholder="A-01" autoComplete="off" className="font-mono uppercase" maxLength={50} {...register('codigo')} />
            </Field>
            <Field
              label="Nivel"
              error={err.nivel?.message}
              required
              hint={libres.length === 0 ? `La zona ya tiene sus ${niveles} niveles ocupados.` : `Un rack por nivel (${niveles} niveles en la zona).`}
            >
              <Select options={libres.map((n) => ({ value: String(n), label: `Nivel ${n}` }))} placeholder={false} {...register('nivel')} />
            </Field>
            <Field label="Carga máxima" error={err.capacidad?.message} required hint="Peso que soporta el rack. No se puede cambiar después.">
              <Input type="number" inputMode="decimal" step="any" min={0} suffix="kg" placeholder="500" {...register('capacidad')} />
            </Field>
          </>
        )}
        {refrigerada && (
          <>
            <Field label="Temperatura mínima" error={err.temperatura_min?.message} required>
              <Input type="number" inputMode="decimal" step="any" suffix="°C" placeholder="2" {...register('temperatura_min')} />
            </Field>
            <Field label="Temperatura máxima" error={err.temperatura_max?.message} required>
              <Input type="number" inputMode="decimal" step="any" suffix="°C" placeholder="8" {...register('temperatura_max')} />
            </Field>
          </>
        )}
      </form>
    </Modal>
  )
}
