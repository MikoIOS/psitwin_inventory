/**
 * Detalle de recepción. La recepción es de un solo paso: sus líneas ya ingresaron al inventario al
 * registrarla. Aquí se consulta (cabecera con el estado ACTUAL de la orden + líneas con rack, aceptado y
 * movimiento); el OPERARIO además resuelve las líneas EN_EVALUACION (`DetallesRecepcionTable`). EMPRESA: solo lectura.
 */
import { useParams } from 'react-router'
import { ACCIONES_ORDEN } from '@/api/enums'
import { useInventarios } from '@/api/inventarios'
import { useDetallesReposicion, useOrden } from '@/api/ordenesReposicion'
import { useDetallesRecepcionPorOrden, useRecepcion } from '@/api/recepciones'
import { useUbicaciones } from '@/api/ubicaciones'
import { Card, ErrorState, Icon, LinkButton, LoadingBlock, PageHeader, StatusBadge } from '@/components/ui'
import { formatFechaHora, formatNumero, shortId } from '@/lib/format'
import { calcularPendientes } from '@/lib/ordenes'
import { paths } from '@/paths'
import { ProgressBar } from '@/features/ordenes/ProgressBar'
import { codigoOrden, codigoRecepcion, useNombres } from '@/features/ordenes/useNombres'
import { useRol } from '@/auth/useRol'
import { DetallesRecepcionTable } from './DetallesRecepcionTable'

export default function RecepcionDetallePage() {
  const { idRecepcion } = useParams()
  const nombres = useNombres()
  const { esOperario } = useRol()
  const ub = useUbicaciones()

  const recQ = useRecepcion(idRecepcion)
  const idOrden = recQ.data?.id_orden_reposicion
  const ordenQ = useOrden(idOrden)
  const detallesQ = useDetallesReposicion(idOrden)
  const recibidosQ = useDetallesRecepcionPorOrden(idOrden)
  const inventariosQ = useInventarios()

  const back = { to: paths.recepciones, label: 'Recepciones' }

  if (recQ.isLoading || (idOrden && ordenQ.isLoading)) return <LoadingBlock label="Cargando recepción…" />
  if (recQ.error || !recQ.data) {
    return (
      <>
        <PageHeader title="Recepción" eyebrow="Recepción de mercadería" back={back} />
        <ErrorState error={recQ.error ?? new Error('Recepción no encontrada')} onRetry={() => void recQ.refetch()} />
      </>
    )
  }

  const rec = recQ.data
  const orden = ordenQ.data
  const lineas = detallesQ.data ? calcularPendientes(detallesQ.data, recibidosQ.data ?? []) : undefined
  const completas = (lineas ?? []).filter((l) => l.pendiente === 0)
  const totalSolicitado = (lineas ?? []).reduce((a, l) => a + l.solicitada, 0)
  const totalAceptado = (lineas ?? []).reduce((a, l) => a + Math.min(l.aceptada, l.solicitada), 0)

  const detallePorId = new Map((detallesQ.data ?? []).map((d) => [d.id_detalle_reposicion, d]))
  const invPorId = new Map((inventariosQ.data ?? []).map((i) => [i.id_inventario, i]))
  const productoDe = (idDet: string) => {
    const linea = detallePorId.get(idDet)
    return linea ? nombres.producto(linea.id_producto) : `Línea ${shortId(idDet)}`
  }
  const ubicacionDe = (idInventario: string) => {
    const inv = invPorId.get(idInventario)
    return (inv && ub.porRack.get(inv.id_rack)?.etiquetaCorta) ?? `Inventario ${shortId(idInventario)}`
  }

  return (
    <>
      <PageHeader
        eyebrow="Recepción de mercadería"
        title={<span className="font-mono">{codigoRecepcion(rec.id_recepcion)}</span>}
        back={back}
        meta={
          <>
            <span className="text-sm text-fg-muted">{formatFechaHora(rec.fecha_recepcion)}</span>
            <span className="inline-flex items-center gap-1 text-sm text-fg-muted">
              <Icon name="user" className="size-4" />
              {nombres.operario(rec.id_operario)}
            </span>
          </>
        }
        actions={
          orden ? (
            <LinkButton to={paths.orden(orden.id_orden_reposicion)} icon="clipboard">
              Ver orden {codigoOrden(orden)}
            </LinkButton>
          ) : undefined
        }
      />

      <div className="flex flex-col gap-5">
        {orden ? (
          <Card padding="md" accent={orden.estado === 'RECIBIDA' ? 'success' : orden.estado === 'PARCIAL' ? 'warning' : 'accent'}>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="label-stencil">Orden {codigoOrden(orden)}</p>
                <p className="mt-0.5 font-semibold text-fg">
                  {nombres.proveedor(orden.id_proveedor)} → {nombres.almacen(orden.id_almacen)}
                </p>
                {rec.observaciones_generales && <p className="mt-1 text-sm text-fg-muted">{rec.observaciones_generales}</p>}
              </div>
              <div className="flex items-center gap-2" aria-live="polite">
                <span className="text-sm text-fg-muted">Estado de la orden:</span>
                <StatusBadge estado={orden.estado} />
              </div>
            </div>
            {lineas && lineas.length > 0 && (
              <div className="mt-4">
                <ProgressBar value={totalAceptado} max={totalSolicitado} label="Avance total de la orden" />
                <p className="mt-1 text-xs text-fg-subtle">
                  {formatNumero(totalAceptado)} de {formatNumero(totalSolicitado)} unidades aceptadas · {completas.length} de {lineas.length} producto(s)
                  completos
                </p>
              </div>
            )}
          </Card>
        ) : (
          <ErrorState error={ordenQ.error ?? new Error('No se encontró la orden de esta recepción')} onRetry={() => void ordenQ.refetch()} />
        )}

        <Card
          padding="md"
          title="Mercadería recibida"
          description="Lo aceptado ingresó al inventario al registrar la recepción (movimiento de entrada automático)."
        >
          <DetallesRecepcionTable
            detalles={rec.detalles}
            nombreProducto={productoDe}
            ubicacion={ubicacionDe}
            puedeResolver={esOperario && !!orden && ACCIONES_ORDEN.puedeRecibir(orden.estado)}
          />
        </Card>
      </div>
    </>
  )
}
