/**
 * Inicio (`/`) según el rol:
 *  - EMPRESA: sus almacenes (`features/almacenes/InicioPage`).
 *  - OPERARIO: su almacén → zonas → racks (grilla con carga en kg y temperatura) y solicitudes / órdenes por recibir.
 *  - PROVEEDOR: órdenes ENVIADAS / PARCIALES dirigidas a él (para registrar su despacho).
 */
import { useNavigate } from 'react-router'
import { useAlmacen } from '@/api/almacenes'
import { ACCIONES_ORDEN } from '@/api/enums'
import { useInventarios } from '@/api/inventarios'
import { useOrdenes } from '@/api/ordenesReposicion'
import { useRacks } from '@/api/racks'
import type { Inventario, OrdenReposicion } from '@/api/types'
import { useZonasPorAlmacen } from '@/api/zonas'
import { useRol } from '@/auth/useRol'
import { Badge, Card, DataTable, EmptyState, ErrorState, LinkButton, LoadingBlock, PageHeader, StatusBadge } from '@/components/ui'
import { formatFecha, formatFechaHora, formatNumero } from '@/lib/format'
import { paths } from '@/paths'
import InicioEmpresa from '@/features/almacenes/InicioPage'
import { RackGrilla } from '@/features/almacenes/RackGrilla'
import { codigoOrden } from '@/features/ordenes/useNombres'

export default function InicioPorRol() {
  const { rol } = useRol()
  if (rol === 'OPERARIO') return <InicioOperario />
  if (rol === 'PROVEEDOR') return <InicioProveedor />
  return <InicioEmpresa />
}

function InicioOperario() {
  const navigate = useNavigate()
  const { operario, idAlmacen } = useRol()
  const almacen = useAlmacen(idAlmacen).data
  const zonasQ = useZonasPorAlmacen(idAlmacen)
  const racksQ = useRacks()
  const invQ = useInventarios()
  const ordenesQ = useOrdenes()

  const invPorRack = new Map<string, Inventario[] | undefined>()
  if (invQ.data) for (const r of racksQ.data ?? []) invPorRack.set(r.id_rack, [])
  for (const i of invQ.data ?? []) invPorRack.set(i.id_rack, [...(invPorRack.get(i.id_rack) ?? []), i])

  const ordenes = ordenesQ.data ?? []
  const porRecibir = ordenes.filter((o) => ACCIONES_ORDEN.puedeRecibir(o.estado))
  const observadas = ordenes.filter((o) => o.estado === 'OBSERVADA')
  const pendientes = ordenes.filter((o) => o.estado === 'PENDIENTE')
  const zonas = [...(zonasQ.data ?? [])].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es', { numeric: true }))

  return (
    <>
      <PageHeader
        eyebrow={almacen ? `Almacén · ${almacen.nombre}` : 'Mi almacén'}
        title={operario ? `Hola, ${operario.nombre}` : 'Inicio'}
        description="Lo que hay por recibir y el estado de los racks de tu almacén."
        actions={
          <LinkButton to={paths.ordenes} icon="clipboard">
            Solicitudes de reposición
          </LinkButton>
        }
      />

      <div className="flex flex-col gap-6">
        <Card
          padding="md"
          title="Por atender"
          description={`${porRecibir.length} por recibir · ${observadas.length} devuelta(s) por la empresa · ${pendientes.length} esperando validación`}
          {...(observadas.length > 0 ? { accent: 'warning' as const } : {})}
        >
          <DataTable<OrdenReposicion>
            caption="Solicitudes y órdenes por atender"
            data={ordenesQ.data ? [...observadas, ...porRecibir] : undefined}
            loading={ordenesQ.isLoading}
            error={ordenesQ.error}
            onRetry={() => void ordenesQ.refetch()}
            rowKey={(o) => o.id_orden_reposicion}
            onRowClick={(o) => navigate(paths.orden(o.id_orden_reposicion))}
            empty={<EmptyState compact icon="clipboard" title="Nada por atender" description="No hay órdenes por recibir ni solicitudes devueltas." />}
            columns={[
              { id: 'codigo', header: 'Orden', mobile: 'title', cell: (o) => <span className="font-mono font-semibold">{codigoOrden(o)}</span> },
              { id: 'estado', header: 'Estado', mobile: 'badge', cell: (o) => <StatusBadge estado={o.estado} /> },
              {
                id: 'que',
                header: 'Qué hacer',
                cell: (o) =>
                  o.estado === 'OBSERVADA' ? 'Corregir y reenviar' : o.despacho ? 'Recibir (el proveedor ya registró su despacho)' : 'Recibir cuando llegue',
              },
              { id: 'estimada', header: 'Llegada estimada', cell: (o) => formatFechaHora(o.fecha_estimada_recepcion) },
            ]}
          />
        </Card>

        <section aria-labelledby="titulo-racks" className="flex flex-col gap-4">
          <h2 id="titulo-racks" className="text-lg font-semibold text-fg">
            Racks de {almacen?.nombre ?? 'mi almacén'}
          </h2>
          {zonasQ.isLoading || racksQ.isLoading ? (
            <LoadingBlock label="Cargando zonas y racks…" />
          ) : (zonasQ.error ?? racksQ.error) ? (
            <ErrorState error={zonasQ.error ?? racksQ.error} onRetry={() => void zonasQ.refetch()} />
          ) : zonas.length === 0 ? (
            <EmptyState icon="layers" title="Tu almacén aún no tiene zonas" description="La empresa debe configurar zonas y racks." />
          ) : (
            zonas.map((z) => {
              const racks = (racksQ.data ?? []).filter((r) => r.id_zona === z.id_zona)
              return (
                <Card
                  key={z.id_zona}
                  padding="md"
                  eyebrow={z.tipo_zona}
                  title={z.nombre}
                  description={`${z.refrigerada ? 'Refrigerada' : 'No refrigerada'} · ${racks.length} de ${formatNumero(z.capacidad)} niveles`}
                  actions={
                    <LinkButton to={paths.zona(z.id_almacen, z.id_zona)} size="sm" variant="secondary" iconRight="chevron-right">
                      Ver zona
                    </LinkButton>
                  }
                >
                  {racks.length === 0 ? (
                    <p className="text-sm text-fg-muted">Esta zona no tiene racks.</p>
                  ) : (
                    <RackGrilla
                      racks={racks}
                      invPorRack={invPorRack}
                      onSelect={(r) => navigate(`${paths.zona(z.id_almacen, z.id_zona)}?rack=${encodeURIComponent(r.id_rack)}`)}
                    />
                  )}
                </Card>
              )
            })
          )}
        </section>
      </div>
    </>
  )
}

function InicioProveedor() {
  const navigate = useNavigate()
  const { proveedor } = useRol()
  const q = useOrdenes() // PROVEEDOR: solo ENVIADA / PARCIAL dirigidas a él
  const ordenes = [...(q.data ?? [])].sort((a, b) => (a.fecha_estimada_recepcion ?? '9').localeCompare(b.fecha_estimada_recepcion ?? '9'))

  return (
    <>
      <PageHeader
        eyebrow="Proveedor"
        title={proveedor?.nombre ?? 'Inicio'}
        description="Órdenes que la empresa te envió. Abre una para registrar lo que despachas (cantidad, vencimiento y temperatura)."
        actions={
          <LinkButton to={paths.productos} icon="box">
            Mis productos
          </LinkButton>
        }
      />
      <DataTable<OrdenReposicion>
        caption="Órdenes por despachar"
        data={q.data ? ordenes : undefined}
        loading={q.isLoading}
        error={q.error}
        onRetry={() => void q.refetch()}
        rowKey={(o) => o.id_orden_reposicion}
        onRowClick={(o) => navigate(paths.orden(o.id_orden_reposicion))}
        empty={<EmptyState icon="truck" title="No tienes órdenes por despachar" description="Cuando la empresa valide una solicitud dirigida a ti aparecerá aquí." />}
        columns={[
          { id: 'codigo', header: 'Orden', mobile: 'title', cell: (o) => <span className="font-mono font-semibold">{codigoOrden(o)}</span> },
          { id: 'estado', header: 'Estado', mobile: 'badge', cell: (o) => <StatusBadge estado={o.estado} /> },
          { id: 'fecha', header: 'Fecha', cell: (o) => formatFecha(o.fecha_orden ?? o.fecha_creacion) },
          { id: 'estimada', header: 'Entrega esperada', cell: (o) => formatFechaHora(o.fecha_estimada_recepcion) },
          {
            id: 'despacho',
            header: 'Despacho',
            cell: (o) => (o.despacho ? <Badge tone="success">Registrado {formatFecha(o.fecha_despacho)}</Badge> : <Badge tone="warning">Por registrar</Badge>),
          },
        ]}
      />
    </>
  )
}
