/**
 * Detalle de solicitud / orden de reposición, compartido por los tres roles (docs/ROLES.md §5):
 *  - OPERARIO: edita cabecera y líneas en PENDIENTE / OBSERVADA (ve el comentario de la empresa), «Reenviar» una
 *    OBSERVADA, elimina una PENDIENTE y registra la recepción (ENVIADA / PARCIAL) partiendo del despacho.
 *  - EMPRESA: Validar (→ ENVIADA), Devolver con comentario (→ OBSERVADA), Cancelar. Todo lo demás, solo lectura.
 *  - PROVEEDOR: ve las órdenes ENVIADA / PARCIAL / RECIBIDA dirigidas a él y registra su despacho.
 * Líneas con pendiente calculada en el frontend (calcularPendientes).
 */
import { useState, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router'
import { ACCIONES_ORDEN, ESTADO_ORDEN_LABEL, ORIGEN_ORDEN_LABEL } from '@/api/enums'
import {
  useCancelarOrden,
  useDeleteDetalleReposicion,
  useDeleteOrden,
  useDetallesReposicion,
  useDevolverOrden,
  useOrden,
  useReenviarOrden,
  useValidarOrden,
} from '@/api/ordenesReposicion'
import { useDetallesRecepcionPorOrden, useRecepcionesPorOrden } from '@/api/recepciones'
import type { DetalleReposicion } from '@/api/types'
import {
  Button,
  Card,
  ConfirmDialog,
  DataTable,
  EmptyState,
  ErrorState,
  Field,
  Icon,
  LoadingBlock,
  Modal,
  PageHeader,
  StatusBadge,
  Textarea,
  useApiErrorHandler,
  useToast,
} from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatFecha, formatFechaHora, formatMoneda, formatNumero, textoOVacio } from '@/lib/format'
import { calcularPendientes, type LineaPendiente } from '@/lib/ordenes'
import { paths } from '@/paths'
import { RecepcionCrearModal } from '@/features/recepciones/RecepcionCrearModal'
import { useProductos } from '@/api/productos'
import { useEmpresa } from '@/auth/useEmpresa'
import { useRol } from '@/auth/useRol'
import { FormAlert } from '@/features/inventario/formUtils'
import { DespachoModal } from './DespachoModal'
import { DetalleLineaModal } from './DetalleLineaModal'
import { OrdenEditarModal } from './OrdenForm'
import { OrdenStepper } from './OrdenStepper'
import { ProgressBar } from './ProgressBar'
import { codigoOrden, codigoRecepcion, useNombres } from './useNombres'

type Accion = 'validar' | 'reenviar' | 'cancelar' | 'eliminar'

export default function OrdenDetallePage() {
  const { idOrden } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const handleError = useApiErrorHandler()
  const nombres = useNombres()

  const ordenQ = useOrden(idOrden)
  const detallesQ = useDetallesReposicion(idOrden)
  const recibidosQ = useDetallesRecepcionPorOrden(idOrden)
  const recepcionesQ = useRecepcionesPorOrden(idOrden)

  const { esEmpresa, esOperario, esProveedor } = useRol()
  const productos = useProductos()
  const { empresa } = useEmpresa()
  const validar = useValidarOrden()
  const reenviar = useReenviarOrden()
  const devolver = useDevolverOrden()
  const cancelar = useCancelarOrden()
  const [devolviendo, setDevolviendo] = useState(false)
  const [comentario, setComentario] = useState('')
  const [despachando, setDespachando] = useState(false)
  const eliminar = useDeleteOrden()
  const eliminarLinea = useDeleteDetalleReposicion()

  const [accion, setAccion] = useState<Accion | null>(null)
  const [editarAbierto, setEditarAbierto] = useState(false)
  const [lineaModal, setLineaModal] = useState<{ detalle: DetalleReposicion | null } | null>(null)
  const [lineaAEliminar, setLineaAEliminar] = useState<DetalleReposicion | null>(null)
  const [recepcionAbierta, setRecepcionAbierta] = useState(false)

  const back = esProveedor ? { to: paths.inicio, label: 'Órdenes por despachar' } : { to: paths.ordenes, label: 'Solicitudes' }

  if (ordenQ.isLoading) return <LoadingBlock label="Cargando orden…" />
  if (ordenQ.error || !ordenQ.data) {
    return (
      <>
        <PageHeader title="Orden de reposición" eyebrow="Reposición" back={back} />
        <ErrorState error={ordenQ.error ?? new Error('Orden no encontrada')} onRetry={() => void ordenQ.refetch()} />
      </>
    )
  }

  const orden = ordenQ.data
  const id = orden.id_orden_reposicion
  const estado = orden.estado
  /** Cabecera y líneas: solo el OPERARIO, en PENDIENTE / OBSERVADA. */
  const editable = esOperario && ACCIONES_ORDEN.puedeEditar(estado)
  const puedeRecibir = esOperario && ACCIONES_ORDEN.puedeRecibir(estado)
  const puedeDespachar = esProveedor && ACCIONES_ORDEN.puedeRecibir(estado)
  const despacho = orden.despacho
  // El PROVEEDOR no puede leer almacenes: para él el destino es la empresa.
  const destino = esProveedor ? (empresa?.nombre ?? 'Empresa') : nombres.almacen(orden.id_almacen)

  const detalles = detallesQ.data
  const lineas = detalles ? calcularPendientes(detalles, recibidosQ.data ?? []) : undefined
  const total = (detalles ?? []).reduce((acc, d) => acc + d.cantidad_solicitada * (d.costo_unitario ?? 0), 0)
  const sinCosto = (detalles ?? []).filter((d) => d.costo_unitario === null).length
  const totalSolicitado = (lineas ?? []).reduce((a, l) => a + l.solicitada, 0)
  const totalAceptado = (lineas ?? []).reduce((a, l) => a + Math.min(l.aceptada, l.solicitada), 0)
  const sinLineas = !!detalles && detalles.length === 0

  const mutaciones = { validar, reenviar, cancelar, eliminar }
  const ejecutar = (a: Accion) => {
    const opts = {
      onSuccess: () => {
        setAccion(null)
        if (a === 'eliminar') {
          toast.success('Solicitud eliminada')
          navigate(paths.ordenes, { replace: true })
          return
        }
        const mensajes: Record<Exclude<Accion, 'eliminar'>, string> = {
          validar: 'Orden enviada: el proveedor ya puede verla y registrar su despacho.',
          reenviar: 'Solicitud reenviada a la empresa para su validación.',
          cancelar: 'Solicitud cancelada.',
        }
        toast.success(mensajes[a])
      },
      onError: (e: unknown) => {
        setAccion(null)
        handleError(e, { title: 'No se pudo completar la acción' })
      },
    }
    mutaciones[a].mutate(id, opts)
  }

  const confirmaciones: Record<Accion, { title: string; description: ReactNode; label: string; tone: 'danger' | 'primary' }> = {
    validar: {
      title: 'Validar y enviar al proveedor',
      description: 'La orden quedará Enviada y visible para el proveedor. Las líneas ya no se podrán modificar.',
      label: 'Validar',
      tone: 'primary',
    },
    reenviar: {
      title: 'Reenviar a la empresa',
      description: 'La solicitud volverá a Pendiente para que la empresa la valide.',
      label: 'Reenviar',
      tone: 'primary',
    },
    cancelar: {
      title: 'Cancelar solicitud',
      description: 'Pasará a Cancelada y no podrá reactivarse.',
      label: 'Cancelar solicitud',
      tone: 'danger',
    },
    eliminar: {
      title: 'Eliminar solicitud',
      description: 'Se eliminará la solicitud y sus líneas. Esta acción no se puede deshacer.',
      label: 'Eliminar',
      tone: 'danger',
    },
  }
  const conf = accion ? confirmaciones[accion] : null

  const acciones = (
    <>
      {esOperario && (
        <>
          {editable && (
            <Button variant="ghost" icon="edit" onClick={() => setEditarAbierto(true)}>
              Editar
            </Button>
          )}
          {ACCIONES_ORDEN.puedeEliminar(estado) && (
            <Button variant="ghost" icon="trash" className="text-danger hover:text-danger" onClick={() => setAccion('eliminar')}>
              Eliminar
            </Button>
          )}
          {ACCIONES_ORDEN.puedeReenviar(estado) && (
            <Button icon="check" onClick={() => setAccion('reenviar')} disabled={sinLineas || !detalles}>
              Reenviar
            </Button>
          )}
          {puedeRecibir && (
            <Button icon="inbox" size="lg" className="sm:h-10 sm:text-sm" onClick={() => setRecepcionAbierta(true)}>
              Registrar recepción
            </Button>
          )}
        </>
      )}
      {esEmpresa && (
        <>
          {ACCIONES_ORDEN.puedeCancelar(estado) && (
            <Button variant="ghost" icon="x" onClick={() => setAccion('cancelar')}>
              Cancelar
            </Button>
          )}
          {ACCIONES_ORDEN.puedeDevolver(estado) && (
            <Button
              variant="secondary"
              icon="arrow-left"
              onClick={() => {
                setComentario('')
                setDevolviendo(true)
              }}
            >
              Devolver
            </Button>
          )}
          {ACCIONES_ORDEN.puedeValidar(estado) && (
            <Button icon="check" onClick={() => setAccion('validar')} disabled={sinLineas || !detalles}>
              Validar
            </Button>
          )}
        </>
      )}
      {puedeDespachar && (
        <Button icon="truck" size="lg" className="sm:h-10 sm:text-sm" onClick={() => setDespachando(true)} disabled={!detalles || sinLineas}>
          {despacho ? 'Actualizar despacho' : 'Registrar despacho'}
        </Button>
      )}
    </>
  )

  return (
    <>
      <PageHeader
        eyebrow={ACCIONES_ORDEN.puedeEditar(estado) ? 'Solicitud de reposición' : 'Orden de reposición'}
        title={<span className="font-mono">{codigoOrden(orden)}</span>}
        back={back}
        meta={
          <>
            <StatusBadge estado={estado} />
            <span className="text-sm text-fg-muted">
              {nombres.proveedor(orden.id_proveedor)} → {destino}
            </span>
          </>
        }
        actions={acciones}
      />

      {ACCIONES_ORDEN.puedeEditar(estado) && sinLineas && (
        <p className="-mt-3 mb-4 flex items-center gap-2 text-sm text-fg-muted">
          <Icon name="info" className="size-4 text-info" />
          {esOperario ? 'Agrega al menos un producto para que la empresa pueda validarla.' : 'La solicitud aún no tiene productos: no se puede validar.'}
        </p>
      )}
      {orden.comentario_empresa && !esProveedor && (
        <FormAlert tone={estado === 'OBSERVADA' ? 'warning' : 'info'} title={estado === 'OBSERVADA' ? 'Devuelta por la empresa' : 'Comentario de la empresa'} className="mb-4">
          {orden.comentario_empresa}
          {estado === 'OBSERVADA' && esOperario && ' — Corrige la solicitud y pulsa «Reenviar».'}
        </FormAlert>
      )}

      <div className="flex flex-col gap-5">
        <Card padding="md">
          <OrdenStepper orden={orden} className="mb-5" />
          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm lg:grid-cols-4">
            <Dato label="Proveedor">{nombres.proveedor(orden.id_proveedor)}</Dato>
            <Dato label={esProveedor ? 'Destino' : 'Almacén'}>{destino}</Dato>
            <Dato label="Recepción estimada">{formatFechaHora(orden.fecha_estimada_recepcion)}</Dato>
            <Dato label="Origen">{ORIGEN_ORDEN_LABEL[orden.origen] ?? orden.origen}</Dato>
            <Dato label="Fecha de orden">{formatFechaHora(orden.fecha_orden ?? orden.fecha_creacion)}</Dato>
            <Dato label="Última actualización">{formatFechaHora(orden.fecha_actualizacion)}</Dato>
            <Dato label="Observación" className="col-span-2">
              {textoOVacio(orden.observacion)}
            </Dato>
          </dl>
        </Card>

        <Card
          padding="md"
          title="Productos solicitados"
          description={
            editable
              ? 'Puedes agregar, editar o quitar líneas mientras la solicitud esté Pendiente u Observada.'
              : esOperario ? `Líneas bloqueadas: la orden está ${ESTADO_ORDEN_LABEL[estado].toLowerCase()}.` : 'Productos y cantidades solicitadas.'
          }
          actions={
            editable ? (
              <Button icon="plus" size="sm" onClick={() => setLineaModal({ detalle: null })}>
                Agregar producto
              </Button>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-2 px-3 py-1 text-xs text-fg-muted">
                <Icon name="alert" className="size-3.5" />
                Solo lectura
              </span>
            )
          }
        >
          <DataTable<LineaPendiente>
            caption="Líneas de la orden"
            data={lineas}
            loading={detallesQ.isLoading}
            error={detallesQ.error}
            onRetry={() => void detallesQ.refetch()}
            rowKey={(l) => l.detalle.id_detalle_reposicion}
            rowClassName={(l) => (l.completa ? 'bg-success-soft/30' : undefined)}
            empty={
              <EmptyState
                compact
                icon="box"
                title="Sin productos"
                description={editable ? 'Agrega los productos que deseas solicitar.' : 'Esta orden no tiene líneas.'}
                action={
                  editable ? (
                    <Button icon="plus" size="sm" onClick={() => setLineaModal({ detalle: null })}>
                      Agregar producto
                    </Button>
                  ) : undefined
                }
              />
            }
            columns={[
              { id: 'producto', header: 'Producto', mobile: 'title', cell: (l) => nombres.producto(l.detalle.id_producto) },
              {
                id: 'estado',
                header: 'Estado',
                mobile: 'badge',
                className: 'md:hidden',
                cell: (l) =>
                  l.completa ? <StatusBadge estado="RECIBIDA" /> : l.aceptada > 0 ? <StatusBadge estado="PARCIAL" /> : null,
              },
              { id: 'solicitada', header: 'Solicitada', align: 'right', cell: (l) => formatNumero(l.solicitada) },
              { id: 'costo', header: 'Costo unit.', align: 'right', cell: (l) => formatMoneda(l.detalle.costo_unitario) },
              {
                id: 'subtotal',
                header: 'Subtotal',
                align: 'right',
                cell: (l) => (l.detalle.costo_unitario === null ? '—' : formatMoneda(l.solicitada * l.detalle.costo_unitario)),
              },
              {
                id: 'aceptada',
                header: 'Aceptada',
                align: 'right',
                cell: (l) => (
                  <span title={l.rechazada > 0 ? `${formatNumero(l.rechazada)} rechazada(s)` : undefined}>
                    {formatNumero(l.aceptada)}
                    {l.rechazada > 0 && <span className="ml-1 text-xs text-danger">(−{formatNumero(l.rechazada)})</span>}
                  </span>
                ),
              },
              {
                id: 'pendiente',
                header: 'Pendiente',
                align: 'right',
                cell: (l) => <span className={cn('font-semibold', l.pendiente > 0 ? 'text-fg' : 'text-success')}>{formatNumero(l.pendiente)}</span>,
              },
              {
                id: 'avance',
                header: 'Avance',
                className: 'min-w-36',
                cell: (l) => <ProgressBar value={l.aceptada} max={l.solicitada} label={`Avance de ${nombres.producto(l.detalle.id_producto)}`} />,
              },
            ]}
            {...(editable
              ? {
                  actions: (l: LineaPendiente) => (
                    <>
                      <Button
                        size="sm"
                        variant="ghost"
                        icon="edit"
                        iconOnly
                        aria-label={`Editar ${nombres.producto(l.detalle.id_producto)}`}
                        onClick={() => setLineaModal({ detalle: l.detalle })}
                      />
                      <Button
                        size="sm"
                        variant="ghost"
                        icon="trash"
                        iconOnly
                        className="text-danger hover:text-danger"
                        aria-label={`Quitar ${nombres.producto(l.detalle.id_producto)}`}
                        onClick={() => setLineaAEliminar(l.detalle)}
                      />
                    </>
                  ),
                }
              : {})}
          />

          {lineas && lineas.length > 0 && (
            <div className="mt-4 flex flex-col gap-3 border-t border-border pt-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex min-w-0 flex-1 flex-col gap-1 sm:max-w-sm">
                <p className="label-stencil">Avance de recepción</p>
                <ProgressBar value={totalAceptado} max={totalSolicitado} label="Avance total de la orden" />
                <p className="text-xs text-fg-subtle">
                  {formatNumero(totalAceptado)} de {formatNumero(totalSolicitado)} unidades aceptadas
                </p>
              </div>
              <div className="text-right">
                <p className="label-stencil">Total de la orden</p>
                <p className="font-mono text-xl font-semibold tabular">{formatMoneda(total)}</p>
                {sinCosto > 0 && <p className="text-xs text-fg-subtle">{sinCosto} línea(s) sin costo unitario</p>}
              </div>
            </div>
          )}
          {recibidosQ.error && (
            <p role="alert" className="mt-3 text-sm text-danger">
              No se pudieron cargar las cantidades recibidas; la columna «Pendiente» puede no estar actualizada.
            </p>
          )}
        </Card>

        {(despacho || puedeDespachar) && (
          <Card
            padding="md"
            title="Despacho del proveedor"
            description={
              despacho
                ? `Registrado el ${formatFechaHora(orden.fecha_despacho ?? despacho.fecha)} — el operario parte de estos datos al recibir.`
                : 'Aún no registras lo que envías de esta orden.'
            }
            {...(puedeDespachar
              ? {
                  actions: (
                    <Button icon="truck" size="sm" onClick={() => setDespachando(true)} disabled={!detalles || sinLineas}>
                      {despacho ? 'Actualizar despacho' : 'Registrar despacho'}
                    </Button>
                  ),
                }
              : {})}
          >
            {despacho && (
              <>
                <DataTable
                  caption="Líneas del despacho"
                  data={despacho.lineas}
                  rowKey={(l) => l.id_detalle_reposicion}
                  columns={[
                    {
                      id: 'producto',
                      header: 'Producto',
                      mobile: 'title',
                      cell: (l) => nombres.producto(l.id_producto ?? detalles?.find((d) => d.id_detalle_reposicion === l.id_detalle_reposicion)?.id_producto ?? ''),
                    },
                    { id: 'cantidad', header: 'Despachada', align: 'right', cell: (l) => formatNumero(l.cantidad) },
                    { id: 'vence', header: 'Vencimiento', cell: (l) => (l.fecha_vencimiento ? formatFecha(l.fecha_vencimiento) : '—') },
                    { id: 'temp', header: 'Temperatura', align: 'right', cell: (l) => (l.temperatura === null || l.temperatura === undefined ? '—' : `${formatNumero(l.temperatura)} °C`) },
                  ]}
                />
                {despacho.observacion && <p className="mt-3 text-sm text-fg-muted">Observación: {despacho.observacion}</p>}
              </>
            )}
          </Card>
        )}

        {!esProveedor && (
        <Card
          padding="md"
          title="Recepciones"
          description={
            puedeRecibir
              ? 'Registra cada entrega del proveedor. El estado pasa a Parcial o Recibida automáticamente.'
              : ACCIONES_ORDEN.puedeRecibir(estado)
                ? 'Las registra el operario del almacén cuando llega la mercadería.'
              : estado === 'RECIBIDA'
                ? 'La orden fue recibida por completo.'
                : 'Las recepciones se habilitan cuando la orden está Enviada.'
          }
          actions={
            puedeRecibir ? (
              <Button icon="inbox" size="sm" onClick={() => setRecepcionAbierta(true)}>
                Registrar recepción
              </Button>
            ) : undefined
          }
        >
          <DataTable
            caption="Recepciones de la orden"
            data={recepcionesQ.data}
            loading={recepcionesQ.isLoading}
            error={recepcionesQ.error}
            onRetry={() => void recepcionesQ.refetch()}
            rowKey={(r) => r.id_recepcion}
            onRowClick={(r) => navigate(paths.recepcion(r.id_recepcion))}
            empty={<EmptyState compact icon="inbox" title="Sin recepciones" description="Aún no se registró ninguna entrega de esta orden." />}
            columns={[
              { id: 'codigo', header: 'Recepción', mobile: 'title', cell: (r) => <span className="font-mono font-semibold">{codigoRecepcion(r.id_recepcion)}</span> },
              { id: 'fecha', header: 'Fecha', cell: (r) => formatFechaHora(r.fecha_recepcion) },
              { id: 'operario', header: 'Operario', cell: (r) => nombres.operario(r.id_operario) },
              { id: 'obs', header: 'Observaciones', mobile: 'hidden', cell: (r) => textoOVacio(r.observaciones_generales) },
            ]}
          />
        </Card>
        )}
      </div>

      <Modal
        open={devolviendo}
        onClose={() => setDevolviendo(false)}
        dismissable={!devolver.isPending}
        title="Devolver al operario"
        description="La solicitud quedará Observada. El operario verá tu comentario, la corregirá y la reenviará."
        footer={
          <>
            <Button variant="secondary" onClick={() => setDevolviendo(false)} disabled={devolver.isPending}>
              Volver
            </Button>
            <Button
              icon="arrow-left"
              loading={devolver.isPending}
              disabled={comentario.trim() === ''}
              onClick={() =>
                devolver.mutate(
                  { id, comentario: comentario.trim() },
                  {
                    onSuccess: () => {
                      setDevolviendo(false)
                      toast.success('La solicitud volvió al operario con tu comentario.', 'Solicitud devuelta')
                    },
                    onError: (e) => handleError(e, { title: 'No se pudo devolver la solicitud' }),
                  },
                )
              }
            >
              Devolver
            </Button>
          </>
        }
      >
        <Field label="Comentario para el operario" required hint="Qué debe corregir (cantidades, proveedor, productos…).">
          <Textarea rows={3} maxLength={1000} value={comentario} onChange={(e) => setComentario(e.target.value)} placeholder="Reduce la cantidad de arroz a 20 unidades" />
        </Field>
      </Modal>

      {puedeDespachar && detalles && (
        <DespachoModal
          open={despachando}
          onClose={() => setDespachando(false)}
          orden={orden}
          detalles={detalles}
          producto={(idP) => productos.data?.find((x) => x.id_producto === idP)}
        />
      )}

      {conf && accion && (
        <ConfirmDialog
          open
          title={conf.title}
          description={conf.description}
          confirmLabel={conf.label}
          cancelLabel="Volver"
          tone={conf.tone}
          loading={mutaciones[accion].isPending}
          onConfirm={() => ejecutar(accion)}
          onCancel={() => setAccion(null)}
        />
      )}

      {editable && <OrdenEditarModal orden={orden} open={editarAbierto} onClose={() => setEditarAbierto(false)} />}

      {editable && (
        <DetalleLineaModal
          open={!!lineaModal}
          onClose={() => setLineaModal(null)}
          idOrden={id}
          detalle={lineaModal?.detalle ?? null}
          nombreProducto={lineaModal?.detalle ? nombres.producto(lineaModal.detalle.id_producto) : ''}
          productosEnOrden={(detalles ?? []).map((d) => d.id_producto)}
          idProveedor={orden.id_proveedor}
        />
      )}

      <ConfirmDialog
        open={!!lineaAEliminar}
        title="Quitar producto"
        description={lineaAEliminar ? `Se quitará «${nombres.producto(lineaAEliminar.id_producto)}» de la orden.` : undefined}
        confirmLabel="Quitar"
        cancelLabel="Volver"
        tone="danger"
        loading={eliminarLinea.isPending}
        onCancel={() => setLineaAEliminar(null)}
        onConfirm={() =>
          lineaAEliminar &&
          eliminarLinea.mutate(lineaAEliminar.id_detalle_reposicion, {
            onSuccess: () => {
              toast.success('Producto quitado de la orden')
              setLineaAEliminar(null)
            },
            onError: (e) => {
              setLineaAEliminar(null)
              handleError(e, { title: 'No se pudo quitar el producto' })
            },
          })
        }
      />

      {puedeRecibir && (
        <RecepcionCrearModal
          open={recepcionAbierta}
          onClose={() => setRecepcionAbierta(false)}
          orden={orden}
          onCreated={(r) => {
            setRecepcionAbierta(false)
            navigate(paths.recepcion(r.id_recepcion))
          }}
        />
      )}

      <p className="mt-6 text-xs text-fg-subtle">
        Creada el {formatFecha(orden.fecha_orden ?? orden.fecha_creacion)} · id <span className="font-mono">{id}</span>
      </p>
    </>
  )
}

function Dato({ label, children, className }: { label: string; children: ReactNode; className?: string }) {
  return (
    <div className={cn('min-w-0', className)}>
      <dt className="label-stencil">{label}</dt>
      <dd className="mt-0.5 break-words text-fg">{children}</dd>
    </div>
  )
}
