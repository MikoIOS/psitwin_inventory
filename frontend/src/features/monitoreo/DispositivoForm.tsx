import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
/**
 * Gestión de dispositivos (solo EMPRESA):
 *  - `DispositivoFormModal`: crear (almacén → zona → rack opcional) o editar (nombre, rack, activo); en ambos, límites
 *    por parámetro (min / max / duración) y puerta (máx. segundos abierta, máx. aperturas por hora).
 *    Campos vacíos no se envían: el backend usa sus defaults (t_int 120 s, t_amb y hum 300 s, corriente 30 s,
 *    puerta 60 s) y, para t_int sin min/max, el rango de temperatura del rack.
 *  - `TokenModal`: muestra el token UNA sola vez (al crear o regenerar) con copiar, y el tema MQTT y el formato del
 *    mensaje para cargar en el ESP32.
 */
import { zodResolver } from '@hookform/resolvers/zod'
import { useId, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { z } from 'zod'
import { PARAMETROS, temaMqtt, useCreateDispositivo, useUpdateDispositivo, type Dispositivo, type DispositivoConToken, type Limites } from '@/api/dispositivos'
import { AlmacenSelect, RackSelect, ZonaSelect } from '@/components/selects'
import { Button, Checkbox, Field, Input, Modal, useApiErrorHandler, useToast } from '@/components/ui'
import { copiarAlPortapapeles } from '@/lib/password'
import { idRequerido, numeroOpcional, numStr, texto } from '@/lib/zod'
import { ETIQUETA_PARAMETRO, UNIDAD } from './monitoreoUtils'

const rango = () => z.object({ min: numeroOpcional(), max: numeroOpcional(), duracion_s: numeroOpcional({ min: 1, entero: true }) })

const schema = z
  .object({
    nombre: texto({ max: 100 }),
    id_almacen: idRequerido('Elige un almacén'),
    id_zona: idRequerido('Elige una zona'),
    id_rack: z.string(),
    id_nivel: z.string(),
    activo: z.boolean(),
    t_int: rango(),
    t_amb: rango(),
    hum: rango(),
    corriente: rango(),
    max_abierta_s: numeroOpcional({ min: 1, entero: true }),
    max_aperturas_hora: numeroOpcional({ min: 1, entero: true }),
  })
  .superRefine((v, ctx) => {
    for (const p of PARAMETROS) {
      const { min, max } = v[p]
      if (min != null && max != null && min > max) ctx.addIssue({ code: 'custom', path: [p, 'max'], message: 'Debe ser ≥ al mínimo' })
    }
  })
type In = z.input<typeof schema>
type Out = z.output<typeof schema>

/** Quita los null/undefined: lo no indicado lo decide el backend (defaults / rango del rack). */
const limpio = <T extends object>(o: T) => Object.fromEntries(Object.entries(o).filter(([, v]) => v != null)) as Partial<T>

function aLimites(v: Out): Limites {
  const l: Limites = {}
  for (const p of PARAMETROS) {
    const r = limpio(v[p])
    if (Object.keys(r).length) l[p] = r
  }
  const puerta = limpio({ max_abierta_s: v.max_abierta_s, max_aperturas_hora: v.max_aperturas_hora })
  if (Object.keys(puerta).length) l.puerta = puerta
  return l
}

function defaults(d: Dispositivo | null): In {
  const r = (p: (typeof PARAMETROS)[number]) => ({ min: numStr(d?.limites?.[p]?.min), max: numStr(d?.limites?.[p]?.max), duracion_s: numStr(d?.limites?.[p]?.duracion_s) })
  return {
    nombre: d?.nombre ?? '',
    id_almacen: d?.id_almacen ?? '',
    id_zona: d?.id_zona ?? '',
    id_rack: d?.id_rack ?? '',
    id_nivel: d?.id_nivel ?? '',
    activo: d?.activo ?? true,
    t_int: r('t_int'),
    t_amb: r('t_amb'),
    hum: r('hum'),
    corriente: r('corriente'),
    max_abierta_s: numStr(d?.limites?.puerta?.max_abierta_s),
    max_aperturas_hora: numStr(d?.limites?.puerta?.max_aperturas_hora),
  }
}

const DURACION_DEFECTO: Record<(typeof PARAMETROS)[number], number> = { t_int: 120, t_amb: 300, hum: 300, corriente: 30 }

export function DispositivoFormModal({
  open,
  onClose,
  dispositivo,
  onCreado,
}: {
  open: boolean
  onClose: () => void
  /** null = crear. */
  dispositivo: Dispositivo | null
  onCreado?: (d: DispositivoConToken) => void
}) {
  return open ? <Abierto onClose={onClose} dispositivo={dispositivo} {...(onCreado ? { onCreado } : {})} /> : null
}

function Abierto({ onClose, dispositivo, onCreado }: { onClose: () => void; dispositivo: Dispositivo | null; onCreado?: (d: DispositivoConToken) => void }) {
  const formId = useId()
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const crear = useCreateDispositivo()
  const editar = useUpdateDispositivo()
  const editando = !!dispositivo
  const form = useForm<In, unknown, Out>({ resolver: zodResolver(schema), defaultValues: defaults(dispositivo) })
  const { register, handleSubmit, setValue, control, formState } = form
  const selectedRack = form.watch('id_rack')
  const levels = useQuery({ queryKey: ['niveles', selectedRack], queryFn: () => api.get<{id_nivel: string; numero: number}[]>('/abastecimiento/racks/' + encodeURIComponent(selectedRack) + '/niveles'), enabled: !!selectedRack })
  const err = formState.errors
  const [idAlmacen, idZona] = useWatch({ control, name: ['id_almacen', 'id_zona'] })
  const pending = crear.isPending || editar.isPending

  const submit = handleSubmit(async (v) => {
    const limites = aLimites(v)
    try {
      if (dispositivo) {
        await editar.mutateAsync({ id: dispositivo.id_dispositivo, body: { nombre: v.nombre, id_rack: v.id_rack || null, id_nivel: v.id_nivel || null, activo: v.activo, limites } })
        toast.success('Dispositivo actualizado')
      } else {
        const d = await crear.mutateAsync({ id_almacen: v.id_almacen, id_zona: v.id_zona, id_rack: v.id_rack || null, id_nivel: v.id_nivel || null, nombre: v.nombre, limites })
        onCreado?.(d)
      }
      onClose()
    } catch (e) {
      handleError(e, { form, title: 'No se pudo guardar el dispositivo' })
    }
  })

  return (
    <Modal
      open
      onClose={onClose}
      dismissable={!pending}
      size="xl"
      title={editando ? 'Editar dispositivo' : 'Nuevo dispositivo'}
      description="Un ESP32 por equipo de frío (cámara, vitrina, congelador). Deja vacío lo que no quieras fijar: se usan los valores por defecto."
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={pending}>
            Cancelar
          </Button>
          <Button type="submit" form={formId} loading={pending}>
            {editando ? 'Guardar cambios' : 'Crear dispositivo'}
          </Button>
        </>
      }
    >
      <form id={formId} onSubmit={submit} noValidate className="flex flex-col gap-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Nombre" error={err.nombre?.message} required className="sm:col-span-2">
            <Input placeholder="Vitrina lácteos 1" {...register('nombre')} />
          </Field>
          <Field label="Almacén" error={err.id_almacen?.message} required hint={editando ? 'No se puede cambiar.' : undefined}>
            <AlmacenSelect
              disabled={editando}
              {...register('id_almacen', {
                onChange: () => {
                  setValue('id_zona', '')
                  setValue('id_rack', '')
                },
              })}
            />
          </Field>
          <Field label="Zona" error={err.id_zona?.message} required hint={editando ? 'No se puede cambiar.' : undefined}>
            <ZonaSelect idAlmacen={idAlmacen || undefined} disabled={editando} {...register('id_zona', { onChange: () => setValue('id_rack', '') })} />
          </Field>
          <Field label="Nivel del sensor"><select {...register('id_nivel')} disabled={!selectedRack}><option value="">Sin nivel asignado</option>{levels.data?.map(n => <option key={n.id_nivel} value={n.id_nivel}>Nivel {n.numero}</option>)}</select></Field>
          <Field label="Rack" hint="Opcional. Si no fijas la temperatura interna, se usa el rango de este rack.">
            <RackSelect idZona={idZona || undefined} placeholder="Sin rack" {...register('id_rack', { onChange: () => setValue('id_nivel', '') })} />
          </Field>
          {editando && <Checkbox label="Activo" description="Un dispositivo inactivo no envía datos (se descartan sus mensajes)." {...register('activo')} />}
        </div>

        <fieldset className="rounded-md border border-border p-4">
          <legend className="label-stencil px-1">Límites</legend>
          <div className="grid gap-3">
            {PARAMETROS.map((p) => (
              <div key={p} className="grid grid-cols-[minmax(0,8rem)_1fr_1fr_1fr] items-end gap-3">
                <span className="pb-2 text-sm font-medium text-fg">{ETIQUETA_PARAMETRO[p]}</span>
                <Field label="Mínimo" error={err[p]?.min?.message}>
                  <Input type="number" inputMode="decimal" step="any" suffix={UNIDAD[p]} {...register(`${p}.min`)} />
                </Field>
                <Field label="Máximo" error={err[p]?.max?.message}>
                  <Input type="number" inputMode="decimal" step="any" suffix={UNIDAD[p]} {...register(`${p}.max`)} />
                </Field>
                <Field label="Tolerancia" error={err[p]?.duracion_s?.message} hint={`Por defecto ${DURACION_DEFECTO[p]} s`}>
                  <Input type="number" inputMode="numeric" min={1} step={1} suffix="s" {...register(`${p}.duracion_s`)} />
                </Field>
              </div>
            ))}
            <div className="grid grid-cols-[minmax(0,8rem)_1fr_1fr_1fr] items-end gap-3">
              <span className="pb-2 text-sm font-medium text-fg">Puerta</span>
              <Field label="Máx. abierta" error={err.max_abierta_s?.message} hint="Por defecto 60 s (p. ej. 20 s en vitrinas)">
                <Input type="number" inputMode="numeric" min={1} step={1} suffix="s" {...register('max_abierta_s')} />
              </Field>
              <Field label="Máx. aperturas / hora" error={err.max_aperturas_hora?.message} hint="Vacío = sin límite">
                <Input type="number" inputMode="numeric" min={1} step={1} {...register('max_aperturas_hora')} />
              </Field>
            </div>
          </div>
        </fieldset>
      </form>
    </Modal>
  )
}

/* ------------------------------------------------------------------ */

/** Token del dispositivo (se muestra UNA vez) + datos para programar el ESP32. */
export function TokenModal({ datos, onClose }: { datos: { id: string; nombre: string; token: string } | null; onClose: () => void }) {
  const [copiado, setCopiado] = useState<string | null>(null)
  if (!datos) return null
  const ejemplo = JSON.stringify({ token: datos.token, ts: '2026-10-09T12:00:00.500Z', t_int: 4.2, puerta: false, t_amb: 22.1, hum: 55, corriente: 2.3 })
  const copiar = async (que: string, texto: string) => setCopiado((await copiarAlPortapapeles(texto)) ? que : null)
  return (
    <Modal
      open
      onClose={onClose}
      size="lg"
      title="Token del dispositivo"
      description={`${datos.nombre} · cárgalo en el ESP32. Por seguridad no se volverá a mostrar: si se pierde, regenéralo.`}
      footer={<Button onClick={onClose}>Listo</Button>}
    >
      <div className="flex flex-col gap-4 text-sm">
        <div>
          <p className="label-stencil mb-1">Token</p>
          <div className="flex items-center gap-2">
            <code className="min-w-0 flex-1 rounded border border-border bg-surface-2 px-3 py-2 font-mono break-all" data-testid="token-dispositivo">
              {datos.token}
            </code>
            <Button variant="secondary" size="sm" icon={copiado === 'token' ? 'check' : 'copy'} onClick={() => void copiar('token', datos.token)}>
              {copiado === 'token' ? 'Copiado' : 'Copiar'}
            </Button>
          </div>
        </div>
        <div>
          <p className="label-stencil mb-1">Tema MQTT (publicar cada 0,5 s)</p>
          <code className="block rounded border border-border bg-surface-2 px-3 py-2 font-mono break-all">{temaMqtt(datos.id)}</code>
        </div>
        <div>
          <p className="label-stencil mb-1">Mensaje (JSON)</p>
          <code className="block rounded border border-border bg-surface-2 px-3 py-2 font-mono text-xs break-all">{ejemplo}</code>
          <p className="mt-1 text-xs text-fg-muted">
            Todos los campos de medida son opcionales (`null` = sin sensor). `ts` es opcional: si falta se usa la hora de llegada. Broker:
            puerto 1883 del servidor, con el usuario de dispositivos.
          </p>
        </div>
        <Button variant="ghost" size="sm" icon={copiado === 'todo' ? 'check' : 'copy'} className="self-start" onClick={() => void copiar('todo', `Tema: ${temaMqtt(datos.id)}\nMensaje: ${ejemplo}`)}>
          {copiado === 'todo' ? 'Copiado' : 'Copiar tema y mensaje'}
        </Button>
      </div>
    </Modal>
  )
}
