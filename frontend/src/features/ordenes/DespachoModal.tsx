/**
 * Despacho del PROVEEDOR (`POST /ordenes-reposicion/{id}/despacho`): por cada línea de la orden indica cuánto envía,
 * la fecha de vencimiento y la temperatura (obligatoria si el producto requiere refrigeración), más una observación.
 * Un nuevo despacho reemplaza al anterior. El operario parte de estos datos al registrar la recepción.
 */
import { useState } from 'react'
import { ApiError } from '@/api/client'
import { useDespacharOrden } from '@/api/ordenesReposicion'
import type { DetalleReposicion, OrdenReposicion, Producto } from '@/api/types'
import { Button, Field, Input, Modal, Textarea, useToast } from '@/components/ui'
import { FormAlert } from '@/features/inventario/formUtils'

interface Fila {
  cantidad: string
  fecha_vencimiento: string
  temperatura: string
}

export interface DespachoModalProps {
  open: boolean
  onClose: () => void
  orden: OrdenReposicion
  detalles: DetalleReposicion[]
  producto: (idProducto: string) => Producto | undefined
}

export function DespachoModal(props: DespachoModalProps) {
  return props.open ? <DespachoAbierto {...props} /> : null
}

function DespachoAbierto({ open, onClose, orden, detalles, producto }: DespachoModalProps) {
  const [operationKey] = useState(() => crypto.randomUUID())
  const sent = new Map<string, number>()
  for (const dispatch of orden.despachos ?? (orden.despacho ? [orden.despacho] : []))
    for (const line of dispatch.lineas) sent.set(line.id_detalle_reposicion, (sent.get(line.id_detalle_reposicion) ?? 0) + line.cantidad)
  const toast = useToast()
  const despachar = useDespacharOrden()
  const previo = new Map((orden.despacho?.lineas ?? []).map((l) => [l.id_detalle_reposicion, l]))
  const [filas, setFilas] = useState<Record<string, Fila>>(() =>
    Object.fromEntries(
      detalles.map((d) => {
        const p = previo.get(d.id_detalle_reposicion)
        return [
          d.id_detalle_reposicion,
          {
            cantidad: String(Math.max(0, d.cantidad_solicitada - (sent.get(d.id_detalle_reposicion) ?? 0))),
            fecha_vencimiento: p?.fecha_vencimiento?.slice(0, 10) ?? '',
            temperatura: p?.temperatura === null || p?.temperatura === undefined ? '' : String(p.temperatura),
          },
        ]
      }),
    ),
  )
  const [observacion, setObservacion] = useState(orden.despacho?.observacion ?? '')
  const [enviado, setEnviado] = useState(false)
  const [accepted, setAccepted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const set = (id: string, campo: keyof Fila, v: string) => setFilas((f) => ({ ...f, [id]: { ...f[id]!, [campo]: v } }))

  const errores = (d: DetalleReposicion) => {
    const f = filas[d.id_detalle_reposicion]!
    const cant = Number(f.cantidad)
    return {
      cantidad: f.cantidad.trim() === '' || !Number.isFinite(cant) || cant < 0 || cant > d.cantidad_solicitada - (sent.get(d.id_detalle_reposicion) ?? 0) || (d.unidad !== 'kg' && !Number.isInteger(cant)) ? 'Cantidad no válida o superior a lo pendiente de despacho' : undefined,
      temperatura:
        f.temperatura.trim() !== '' && !Number.isFinite(Number(f.temperatura))
          ? 'Número no válido'
          : producto(d.id_producto)?.requiere_refrigeracion && cant > 0 && f.temperatura.trim() === ''
            ? 'Obligatoria (producto refrigerado)'
            : undefined,
    }
  }
  const lineas = detalles.filter((d) => Number(filas[d.id_detalle_reposicion]!.cantidad) > 0)
  const valido = lineas.length > 0 && detalles.every((d) => Object.values(errores(d)).every((e) => !e))

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setEnviado(true)
    setError(null)
    if (!valido || !accepted) return
    despachar.mutate(
      {
        id: orden.id_orden_reposicion,
        body: {
          clave_idempotencia: operationKey,
          conformidad: true,
          lineas: lineas.map((d) => {
            const f = filas[d.id_detalle_reposicion]!
            return {
              id_detalle_reposicion: d.id_detalle_reposicion,
              cantidad: Number(f.cantidad),
              fecha_vencimiento: f.fecha_vencimiento ? new Date(`${f.fecha_vencimiento}T00:00:00`).toISOString() : null,
              temperatura: f.temperatura.trim() === '' ? null : Number(f.temperatura),
            }
          }),
          observacion: observacion.trim() || null,
        },
      },
      {
        onSuccess: () => {
          toast.success('El almacén verá estos datos al recibir la mercadería.', 'Despacho registrado')
          onClose()
        },
        onError: (err) => {
          if (err instanceof ApiError && err.isHandledGlobally) return
          setError(err instanceof ApiError ? err.detail : 'Ocurrió un error inesperado.')
        },
      },
    )
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      dismissable={!despachar.isPending}
      size="xl"
      title={orden.despacho ? 'Registrar siguiente despacho' : 'Registrar despacho'}
      description="Indica lo que envías de cada producto. Pon 0 en lo que no despachas esta vez."
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={despachar.isPending}>
            Cancelar
          </Button>
          <Button type="submit" form="form-despacho" icon="truck" loading={despachar.isPending} disabled={!accepted}>
            Registrar despacho
          </Button>
        </>
      }
    >
      <form id="form-despacho" onSubmit={submit} noValidate className="flex flex-col gap-4">
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={accepted} onChange={e => setAccepted(e.target.checked)} />He revisado y acepto la solicitud aprobada y las cantidades que voy a despachar.</label>
        {detalles.map((d) => {
          const p = producto(d.id_producto)
          const f = filas[d.id_detalle_reposicion]!
          const err = enviado ? errores(d) : { cantidad: undefined, temperatura: undefined }
          return (
            <fieldset key={d.id_detalle_reposicion} className="rounded-[var(--radius-ui)] border border-border p-3">
              <legend className="px-1 text-sm font-semibold text-fg">
                {p?.nombre ?? 'Producto'} <span className="font-normal text-fg-muted">· solicitadas {d.cantidad_solicitada}</span>
              </legend>
              <div className="grid gap-3 sm:grid-cols-3">
                <Field label="Cantidad despachada" error={err.cantidad} required>
                  <Input type="number" inputMode="decimal" min={0} max={Math.max(0, d.cantidad_solicitada - (sent.get(d.id_detalle_reposicion) ?? 0))} step={d.unidad === 'kg' ? '.001' : '1'} suffix={d.unidad ?? 'unidad'} value={f.cantidad} onChange={(e) => set(d.id_detalle_reposicion, 'cantidad', e.target.value)} />
                </Field>
                <Field label="Vencimiento" hint="Opcional.">
                  <Input type="date" value={f.fecha_vencimiento} onChange={(e) => set(d.id_detalle_reposicion, 'fecha_vencimiento', e.target.value)} />
                </Field>
                <Field label="Temperatura" error={err.temperatura} required={!!p?.requiere_refrigeracion} hint={p?.requiere_refrigeracion ? 'Producto refrigerado.' : 'Opcional.'}>
                  <Input type="number" inputMode="decimal" step="any" suffix="°C" value={f.temperatura} onChange={(e) => set(d.id_detalle_reposicion, 'temperatura', e.target.value)} />
                </Field>
              </div>
            </fieldset>
          )
        })}
        <Field label="Observación" hint="Opcional. Ej.: guía de remisión, transporte.">
          <Textarea rows={2} maxLength={500} value={observacion} onChange={(e) => setObservacion(e.target.value)} />
        </Field>
        {enviado && lineas.length === 0 && <FormAlert tone="warning" title="Indica al menos un producto con cantidad mayor que 0" />}
        {error && (
          <FormAlert tone="danger" title="No se pudo registrar el despacho">
            {error}
          </FormAlert>
        )}
      </form>
    </Modal>
  )
}
