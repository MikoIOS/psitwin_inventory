/**
 * Solicitudes / órdenes de reposición: listado con filtros (estado, almacén, proveedor).
 * EMPRESA: todas (solo lectura aquí; valida / devuelve / cancela en el detalle). OPERARIO: las de su almacén y
 * «Nueva solicitud».
 */
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { ESTADO_ORDEN_LABEL, ORIGEN_ORDEN_LABEL } from '@/api/enums'
import { useOrdenes } from '@/api/ordenesReposicion'
import type { EstadoOrden, OrdenReposicion } from '@/api/types'
import { AlmacenSelect, ProveedorSelect } from '@/components/selects'
import { Button, DataTable, EmptyState, Field, PageHeader, StatusBadge } from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatFecha, formatFechaHora } from '@/lib/format'
import { paths } from '@/paths'
import { OrdenCrearModal } from './OrdenForm'
import { useRol } from '@/auth/useRol'
import { codigoOrden, useNombres } from './useNombres'

const ESTADOS = Object.keys(ESTADO_ORDEN_LABEL) as EstadoOrden[]

const porFechaDesc = (a: OrdenReposicion, b: OrdenReposicion) =>
  (b.fecha_orden ?? b.fecha_creacion ?? '').localeCompare(a.fecha_orden ?? a.fecha_creacion ?? '')

export default function OrdenesPage() {
  const navigate = useNavigate()

  const q = useOrdenes()
  const nombres = useNombres()

  const [estado, setEstado] = useState<EstadoOrden | ''>('')
  const [idAlmacen, setIdAlmacen] = useState('')
  const [idProveedor, setIdProveedor] = useState('')
  const [crearAbierto, setCrearAbierto] = useState(false)
  const { esEmpresa, esOperario } = useRol()

  const irAOrden = (o: OrdenReposicion) => navigate(paths.orden(o.id_orden_reposicion))

  const base = (q.data ?? []).filter(
    (o) => (!idAlmacen || o.id_almacen === idAlmacen) && (!idProveedor || o.id_proveedor === idProveedor),
  )
  const conteo = new Map<EstadoOrden, number>()
  for (const o of base) conteo.set(o.estado, (conteo.get(o.estado) ?? 0) + 1)
  const filtradas = q.data ? base.filter((o) => !estado || o.estado === estado).sort(porFechaDesc) : undefined
  const hayFiltros = !!(estado || idAlmacen || idProveedor)

  return (
    <>
      <PageHeader
        title="Solicitudes de reposición"
        eyebrow="Reposición"
        description={
          esOperario
            ? 'Pide mercadería a un proveedor: la empresa valida la solicitud (o te la devuelve con un comentario), el proveedor despacha y tú la recibes.'
            : 'Solicitudes de los operarios. Valida las Pendientes para enviarlas al proveedor, o devuélvelas con un comentario.'
        }
        {...(esOperario
          ? {
              actions: (
                <Button icon="plus" onClick={() => setCrearAbierto(true)}>
                  Nueva solicitud
                </Button>
              ),
            }
          : {})}
      />

      <section aria-label="Filtros" className="mb-4 flex flex-col gap-3">
        <div className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1" role="group" aria-label="Filtrar por estado">
          <ChipEstado activo={estado === ''} onClick={() => setEstado('')} label="Todas" n={base.length} />
          {ESTADOS.map((e) => (
            <ChipEstado key={e} activo={estado === e} onClick={() => setEstado(e)} label={ESTADO_ORDEN_LABEL[e]} n={conteo.get(e) ?? 0} />
          ))}
        </div>
        <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          {esEmpresa && (
            <Field label="Almacén">
              <AlmacenSelect placeholder="Todos los almacenes" value={idAlmacen} onChange={(e) => setIdAlmacen(e.target.value)} />
            </Field>
          )}
          <Field label="Proveedor">
            <ProveedorSelect
              soloActivos={false}
              placeholder="Todos los proveedores"
              value={idProveedor}
              onChange={(e) => setIdProveedor(e.target.value)}
            />
          </Field>
          {hayFiltros && (
            <Button
              variant="ghost"
              icon="x"
              onClick={() => {
                setEstado('')
                setIdAlmacen('')
                setIdProveedor('')
              }}
            >
              Limpiar filtros
            </Button>
          )}
        </div>
      </section>

      <DataTable
        caption="Órdenes de reposición"
        data={filtradas}
        loading={q.isLoading}
        error={q.error}
        onRetry={q.refetch}
        rowKey={(o) => o.id_orden_reposicion}
        onRowClick={irAOrden}
        empty={
          hayFiltros ? (
            <EmptyState icon="search" title="Sin resultados" description="Ninguna orden coincide con los filtros." />
          ) : (
            <EmptyState
              icon="clipboard"
              title="Aún no hay solicitudes"
              description={esOperario ? 'Crea una solicitud para pedir mercadería a un proveedor.' : 'Las solicitudes las crean los operarios desde su almacén.'}
              {...(esOperario
                ? {
                    action: (
                      <Button icon="plus" onClick={() => setCrearAbierto(true)}>
                        Nueva solicitud
                      </Button>
                    ),
                  }
                : {})}
            />
          )
        }
        columns={[
          {
            id: 'codigo',
            header: 'Orden',
            mobile: 'title',
            cell: (o) => <span className="font-mono text-sm font-semibold">{codigoOrden(o)}</span>,
          },
          { id: 'estado', header: 'Estado', mobile: 'badge', cell: (o) => <StatusBadge estado={o.estado} /> },
          { id: 'proveedor', header: 'Proveedor', cell: (o) => nombres.proveedor(o.id_proveedor) },
          { id: 'almacen', header: 'Almacén', cell: (o) => nombres.almacen(o.id_almacen) },
          { id: 'creada', header: 'Fecha', cell: (o) => formatFecha(o.fecha_orden ?? o.fecha_creacion) },
          { id: 'estimada', header: 'Recepción estimada', cell: (o) => formatFechaHora(o.fecha_estimada_recepcion) },
          {
            id: 'origen',
            header: 'Origen',
            mobile: 'hidden',
            cell: (o) => ORIGEN_ORDEN_LABEL[o.origen] ?? o.origen,
          },
        ]}
      />

      <OrdenCrearModal
        open={crearAbierto}
        onClose={() => setCrearAbierto(false)}
        idProveedor={undefined}
        onCreated={(o) => {
          setCrearAbierto(false)
          irAOrden(o)
        }}
      />
    </>
  )
}

function ChipEstado({ activo, onClick, label, n }: { activo: boolean; onClick: () => void; label: string; n: number }) {
  return (
    <button
      type="button"
      aria-pressed={activo}
      onClick={onClick}
      className={cn(
        'inline-flex h-9 shrink-0 items-center gap-2 rounded-full border px-3.5 text-sm font-medium transition-colors',
        activo ? 'border-fg bg-fg text-bg' : 'border-border-strong bg-surface text-fg-muted hover:bg-surface-2 hover:text-fg',
      )}
    >
      {label}
      <span className={cn('font-mono text-xs tabular', activo ? 'text-bg/80' : 'text-fg-subtle')}>{n}</span>
    </button>
  )
}
