/**
 * Líneas de una recepción (esquema único de detalle) + acción «Resolver» para las que están EN_EVALUACION
 * (`POST /detalles-recepcion/{id}/resolver`): aceptar (todo o parte; lo aceptado ingresa al inventario elegido
 * al registrar la recepción) o rechazar. Solo el OPERARIO resuelve (el autor sale de su token); la empresa solo lee.
 */
import { useState } from 'react'
import { ApiError } from '@/api/client'
import { useResolverDetalleRecepcion } from '@/api/recepciones'
import type { DetalleRecepcion } from '@/api/types'
import { Button, DataTable, EmptyState, Field, Icon, Input, Modal, Select, StatusBadge, Textarea, useToast } from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatFecha, formatNumero, shortId, textoOVacio } from '@/lib/format'
import { FormAlert } from '@/features/inventario/formUtils'

export interface DetallesRecepcionTableProps {
  detalles: DetalleRecepcion[] | undefined
  /** Nombre del producto de la línea de la orden (`id_detalle_reposicion`). */
  nombreProducto: (idDetalleReposicion: string) => string
  /** Etiqueta de la ubicación de un inventario ("Zona A › Rack A-01"). */
  ubicacion: (idInventario: string) => string
  /** false si la orden ya no admite ingresos (oculta «Resolver»). */
  puedeResolver: boolean
}

const enEvaluacion = (d: DetalleRecepcion) => d.estado_recepcion === 'EN_EVALUACION' && !d.id_movimiento

export function DetallesRecepcionTable({ detalles, nombreProducto, ubicacion, puedeResolver }: DetallesRecepcionTableProps) {
  const [aResolver, setAResolver] = useState<DetalleRecepcion | null>(null)
  const hayPendientes = puedeResolver && !!detalles?.some(enEvaluacion)

  return (
    <>
      <DataTable<DetalleRecepcion>
        caption="Líneas de la recepción"
        data={detalles}
        loading={!detalles}
        rowKey={(d) => d.id_detalle_recepcion}
        empty={<EmptyState compact icon="inbox" title="Sin líneas" description="Esta recepción no tiene productos registrados." />}
        columns={[
          { id: 'producto', header: 'Producto', mobile: 'title', cell: (d) => nombreProducto(d.id_detalle_reposicion) },
          { id: 'estado', header: 'Estado', mobile: 'badge', cell: (d) => <StatusBadge estado={d.estado_recepcion} /> },
          { id: 'recibida', header: 'Recibida', align: 'right', cell: (d) => formatNumero(d.cantidad_recibida) },
          {
            id: 'rechazada',
            header: 'Rechazada',
            align: 'right',
            cell: (d) => <span className={cn(d.cantidad_rechazada > 0 && 'text-danger')}>{formatNumero(d.cantidad_rechazada)}</span>,
          },
          {
            id: 'aceptada',
            header: 'Aceptada',
            align: 'right',
            cell: (d) =>
              enEvaluacion(d) ? (
                <span className="text-xs text-warning">Por resolver</span>
              ) : (
                <span className="font-semibold text-success" title={d.id_movimiento ? `Movimiento #${shortId(d.id_movimiento)}` : 'Sin ingreso al inventario'}>
                  {formatNumero(d.cantidad_aceptada)}
                </span>
              ),
          },
          { id: 'ubicacion', header: 'Rack', cell: (d) => ubicacion(d.id_inventario) },
          {
            id: 'lote',
            header: 'Lote',
            cell: (d) => (
              <>
                <span className="font-mono">{d.lote === 'SIN_LOTE' ? '—' : d.lote}</span>
                {d.fecha_vencimiento && <span className="block text-xs text-fg-muted">Vence {formatFecha(d.fecha_vencimiento)}</span>}
              </>
            ),
          },
          { id: 'comentario', header: 'Comentario', mobile: 'hidden', cell: (d) => textoOVacio(d.comentario_recepcion ?? d.motivo_rechazo) },
        ]}
        {...(hayPendientes
          ? {
              actions: (d: DetalleRecepcion) =>
                enEvaluacion(d) ? (
                  <Button size="sm" icon="check" onClick={() => setAResolver(d)}>
                    Resolver
                  </Button>
                ) : null,
            }
          : {})}
      />
      {detalles?.some(enEvaluacion) && (
        <p className="mt-3 flex items-start gap-2 rounded-[var(--radius-ui)] border border-warning/30 bg-warning-soft/60 px-3 py-2 text-sm text-fg">
          <Icon name="info" className="mt-0.5 size-4 shrink-0 text-warning" />
          Las líneas en evaluación no ingresan al inventario hasta resolverse.
        </p>
      )}

      <Modal
        open={!!aResolver}
        onClose={() => setAResolver(null)}
        title="Resolver evaluación"
        description={aResolver ? `${nombreProducto(aResolver.id_detalle_reposicion)} · ${formatNumero(aResolver.cantidad_recibida)} u. recibidas · ${ubicacion(aResolver.id_inventario)}` : undefined}
      >
        {aResolver && (
          <ResolverForm key={aResolver.id_detalle_recepcion} detalle={aResolver} onClose={() => setAResolver(null)} />
        )}
      </Modal>
    </>
  )
}

function ResolverForm({ detalle, onClose }: { detalle: DetalleRecepcion; onClose: () => void }) {
  const toast = useToast()
  const resolver = useResolverDetalleRecepcion()
  const recibida = detalle.cantidad_recibida
  const [decision, setDecision] = useState<'CONFORME' | 'RECHAZADO'>('CONFORME')
  const [aceptadaTxt, setAceptadaTxt] = useState(String(recibida))
  const [comentario, setComentario] = useState('')
  const [enviado, setEnviado] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const aceptada = decision === 'RECHAZADO' ? 0 : Number(aceptadaTxt)
  const aceptadaOk = decision === 'RECHAZADO' || (Number.isInteger(aceptada) && aceptada >= 1 && aceptada <= recibida)
  const comentarioOk = comentario.trim() !== ''

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setEnviado(true)
    setError(null)
    if (!aceptadaOk || !comentarioOk) return
    resolver.mutate(
      {
        idDetalle: detalle.id_detalle_recepcion,
        body: {
          estado_recepcion: decision,
          comentario_resolucion: comentario.trim(),
          cantidad_aceptada: aceptada,
          cantidad_rechazada: recibida - aceptada,
        },
      },
      {
        onSuccess: (d) => {
          toast.success(
            d.cantidad_aceptada > 0 ? `${formatNumero(d.cantidad_aceptada)} u. ingresaron al inventario.` : 'La línea quedó rechazada: no ingresa al inventario.',
            'Evaluación resuelta',
          )
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
    <form onSubmit={submit} noValidate className="flex flex-col gap-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Decisión" required>
          <Select
            size="lg"
            placeholder={false}
            options={[
              { value: 'CONFORME', label: 'Aceptar (ingresa al inventario)' },
              { value: 'RECHAZADO', label: 'Rechazar todo' },
            ]}
            value={decision}
            onChange={(e) => setDecision(e.target.value as 'CONFORME' | 'RECHAZADO')}
          />
        </Field>
        {decision === 'CONFORME' && (
          <Field
            label="Cantidad aceptada"
            required
            error={enviado && !aceptadaOk ? `Entero entre 1 y ${formatNumero(recibida)}` : undefined}
            hint={aceptadaOk && aceptada < recibida ? `Se rechazan ${formatNumero(recibida - aceptada)} u.` : undefined}
          >
            <Input size="lg" type="number" inputMode="numeric" min={1} max={recibida} step={1} suffix="u." value={aceptadaTxt} onChange={(e) => setAceptadaTxt(e.target.value)} />
          </Field>
        )}
      </div>
      <Field label="Comentario de la resolución" required error={enviado && !comentarioOk ? 'Campo obligatorio' : undefined}>
        <Textarea rows={2} maxLength={1000} value={comentario} onChange={(e) => setComentario(e.target.value)} placeholder="Revisión de calidad aprobada" />
      </Field>
      {error && (
        <FormAlert tone="danger" title="No se pudo resolver">
          {error}
        </FormAlert>
      )}
      <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
        <Button variant="secondary" onClick={onClose} disabled={resolver.isPending}>
          Cancelar
        </Button>
        <Button type="submit" icon="check" loading={resolver.isPending}>
          Resolver
        </Button>
      </div>
    </form>
  )
}
