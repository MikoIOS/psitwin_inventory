/**
 * Detalle de zona: CRUD de racks mostrados como una grilla de posiciones (filas = niveles, color = estado)
 * y, para el rack seleccionado, el inventario que contiene (stock_actual vs mínimo/máximo con StockBadge).
 * El rack seleccionado se guarda en `?rack=<id>` para poder compartir el enlace.
 */
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'
import { useAlmacen } from '@/api/almacenes'
import { ApiError } from '@/api/client'
import { ESTADO_RACK_LABEL, ESTADOS_RACK_EDITABLES } from '@/api/enums'
import { useInventarios, useInventariosPorRack } from '@/api/inventarios'
import { useProductos } from '@/api/productos'
import { useDeleteRack, useRacksPorZona } from '@/api/racks'
import type { Inventario, Rack } from '@/api/types'
import { useZona } from '@/api/zonas'
import { useRol } from '@/auth/useRol'
import {
  Badge,
  Button,
  Card,
  DataTable,
  EmptyState,
  ErrorState,
  LinkButton,
  LoadingBlock,
  PageHeader,
  StatusBadge,
  StockBadge,
} from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatNumero } from '@/lib/format'
import { colorOcupacion, porcentajeCarga, temperaturaRack } from '@/lib/racks'
import { paths } from '@/paths'
import { EliminarDialog } from './EliminarDialog'
import { RackGrilla } from './RackGrilla'
import { RackFormModal } from './RackForm'
import { agruparPorNivel, codigoRack, estiloRack } from './ubicacionUtils'

export default function ZonaDetallePage() {
  const { idAlmacen = '', idZona } = useParams()
  const almacenQ = useAlmacen(idAlmacen || undefined)
  const zonaQ = useZona(idZona)
  const zona = zonaQ.data
  const back = { to: paths.almacen(idAlmacen), label: almacenQ.data?.nombre ?? 'Almacén' }

  if (zonaQ.isLoading) return <LoadingBlock label="Cargando zona…" />
  if (zonaQ.error || !zona || (zona.id_almacen && idAlmacen && zona.id_almacen !== idAlmacen)) {
    const noExiste = !zona || (zonaQ.error instanceof ApiError && zonaQ.error.isNotFound)
    return (
      <>
        <PageHeader title="Zona" back={back} />
        {zonaQ.error && !noExiste ? (
          <ErrorState error={zonaQ.error} onRetry={() => void zonaQ.refetch()} />
        ) : (
          <EmptyState
            icon="layers"
            title="Zona no encontrada"
            description="Puede que haya sido eliminada o que no pertenezca a este almacén."
            action={<LinkButton to={back.to}>Volver al almacén</LinkButton>}
          />
        )}
      </>
    )
  }

  return <Contenido idZona={zona.id_zona} back={back} />
}

/* ------------------------------------------------------------------ */

function Contenido({ idZona, back }: { idZona: string; back: { to: string; label: string } }) {
  const zona = useZona(idZona).data!
  const racksQ = useRacksPorZona(idZona)
  const invQ = useInventarios()
  const [params, setParams] = useSearchParams()
  const [form, setForm] = useState<{ rack: Rack | null } | null>(null)
  const [aEliminar, setAEliminar] = useState<Rack | null>(null)
  const del = useDeleteRack()
  const { esEmpresa, esOperario } = useRol()

  const racks = racksQ.data ?? []
  const niveles = agruparPorNivel(racks)
  const posiciones = new Map<string, string>()
  for (const n of niveles) for (const { rack, posicion } of n.racks) posiciones.set(rack.id_rack, codigoRack(rack, posicion))

  // Resumen de inventario por rack (una sola petición cacheada, compartida con Inicio / Inventario).
  const invPorRack = new Map<string, Inventario[] | undefined>()
  if (invQ.data) for (const r of racks) invPorRack.set(r.id_rack, [])
  for (const inv of invQ.data ?? []) invPorRack.set(inv.id_rack, [...(invPorRack.get(inv.id_rack) ?? []), inv])

  const paramRack = params.get('rack')
  const seleccionado = racks.find((r) => r.id_rack === paramRack) ?? racks[0] ?? null
  const seleccionar = (id: string) =>
    setParams(
      (p) => {
        p.set('rack', id)
        return p
      },
      { replace: true, preventScrollReset: true },
    )

  const conteoEstados = new Map<string, number>()
  for (const r of racks) conteoEstados.set(r.estado, (conteoEstados.get(r.estado) ?? 0) + 1)
  const estadosLeyenda = [...ESTADOS_RACK_EDITABLES, ...(['ACTIVO', 'INACTIVO'] as const).filter((e) => conteoEstados.has(e))]

  return (
    <>
      <PageHeader
        back={back}
        eyebrow={`Zona · ${back.label}`}
        title={zona.nombre}
        meta={
          <>
            <Badge tone="accent">{zona.tipo_zona}</Badge>
            <Badge tone="info" dot={false}>
              {zona.refrigerada ? 'Refrigerada' : 'No refrigerada'}
            </Badge>
            <Badge tone="neutral" dot={false}>
              {racks.length} de {formatNumero(zona.capacidad)} niveles
            </Badge>
          </>
        }
        {...(esEmpresa
          ? {
              actions: (
                <Button icon="plus" onClick={() => setForm({ rack: null })}>
                  Nuevo rack
                </Button>
              ),
            }
          : {})}
      />

      {racksQ.isLoading ? (
        <LoadingBlock label="Cargando racks…" />
      ) : racksQ.error ? (
        <ErrorState error={racksQ.error} onRetry={() => void racksQ.refetch()} />
      ) : racks.length === 0 ? (
        <EmptyState
          icon="layers"
          title="Esta zona no tiene racks"
          description={esEmpresa ? 'Agrega racks para ubicar productos e inventario en esta zona.' : 'La empresa aún no creó racks en esta zona.'}
          {...(esEmpresa
            ? {
                action: (
                  <Button icon="plus" onClick={() => setForm({ rack: null })}>
                    Crear primer rack
                  </Button>
                ),
              }
            : {})}
        />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_26rem]">
          <section aria-labelledby="titulo-grilla" className="min-w-0">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h2 id="titulo-grilla" className="label-stencil">
                Posiciones <span className="tabular">({racks.length})</span>
              </h2>
              <ul className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-fg-muted" aria-label="Leyenda de estados">
                {estadosLeyenda.map((e) => (
                  <li key={e} className="inline-flex items-center gap-1.5">
                    <span className={cn('size-2.5 rounded-sm', estiloRack(e).punto)} aria-hidden="true" />
                    {ESTADO_RACK_LABEL[e]} <span className="tabular font-mono">({conteoEstados.get(e) ?? 0})</span>
                  </li>
                ))}
              </ul>
            </div>

            <RackGrilla racks={racks} invPorRack={invPorRack} seleccionado={seleccionado?.id_rack} onSelect={(r) => seleccionar(r.id_rack)} />
            <p className="mt-2 text-xs text-fg-subtle">Selecciona una posición para ver su inventario. El nivel más alto se muestra arriba.</p>
          </section>

          {seleccionado && (
            <RackPanel
              key={seleccionado.id_rack}
              rack={seleccionado}
              codigo={posiciones.get(seleccionado.id_rack) ?? ''}
              {...(esOperario ? { onEditar: () => setForm({ rack: seleccionado }) } : {})}
              {...(esEmpresa ? { onEliminar: () => setAEliminar(seleccionado) } : {})}
            />
          )}
        </div>
      )}

      <RackFormModal
        open={!!form}
        idZona={idZona}
        rack={form?.rack ?? null}
        refrigerada={zona.refrigerada}
        niveles={zona.capacidad}
        nivelesOcupados={racks.map((r) => r.nivel)}
        onClose={() => setForm(null)}
        onGuardado={(r) => seleccionar(r.id_rack)}
      />
      <EliminarDialog
        open={!!aEliminar}
        title="Eliminar rack"
        description={
          <>
            Se eliminará el rack <strong className="text-fg">{aEliminar ? posiciones.get(aEliminar.id_rack) : ''}</strong>.
            {aEliminar && (invPorRack.get(aEliminar.id_rack)?.length ?? 0) > 0
              ? ' Contiene inventario: el sistema puede impedir la eliminación.'
              : ' Esta acción no se puede deshacer.'}
          </>
        }
        accion={() => del.mutateAsync(aEliminar!.id_rack)}
        mensajeExito="Rack eliminado"
        tituloError="No se pudo eliminar el rack"
        onClose={() => setAEliminar(null)}
        onEliminado={() =>
          setParams(
            (p) => {
              p.delete('rack')
              return p
            },
            { replace: true, preventScrollReset: true },
          )
        }
      />
    </>
  )
}

/* ------------------------------------------------------------------ */

/* ------------------------------------------------------------------ */

function RackPanel({ rack, codigo, onEditar, onEliminar }: { rack: Rack; codigo: string; onEditar?: () => void; onEliminar?: () => void }) {
  const invQ = useInventariosPorRack(rack.id_rack)
  const productosQ = useProductos()
  const productoPorId = new Map((productosQ.data ?? []).map((p) => [p.id_producto, p]))
  const pct = porcentajeCarga(rack)
  const temp = temperaturaRack(rack)

  return (
    <Card
      as="section"
      aria-live="polite"
      eyebrow="Rack seleccionado"
      title={
        <span className="flex flex-wrap items-center gap-2">
          <span className="font-mono">{codigo}</span>
          <StatusBadge estado={rack.estado} />
        </span>
      }
      description={`Nivel ${rack.nivel} · Carga máxima ${formatNumero(rack.capacidad)} kg${temp ? ` · ${temp}` : ''}`}
      actions={
        <>
          {onEditar && (
            <Button variant="secondary" size="sm" icon="edit" onClick={onEditar}>
              Estado{temp ? ' y temperatura' : ''}
            </Button>
          )}
          {onEliminar && (
            <Button variant="ghost" size="sm" iconOnly icon="trash" aria-label={`Eliminar rack ${codigo}`} onClick={onEliminar} className="hover:text-danger" />
          )}
        </>
      }
      className="self-start xl:sticky xl:top-4"
    >
      {pct !== null && (
        <div className="mb-4">
          <div className="mb-1 flex justify-between text-xs text-fg-muted">
            <span>Carga en el rack</span>
            <span className="tabular font-mono">
              {formatNumero(rack.carga_kg)} / {formatNumero(rack.capacidad)} kg · <strong className="text-fg">{formatNumero(rack.libre_kg)} kg libres</strong>
            </span>
          </div>
          <div
            className="h-2 overflow-hidden rounded-full bg-surface-3"
            role="meter"
            aria-label="Ocupación del rack"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.min(100, pct)}
          >
            <div className={cn('h-full rounded-full', colorOcupacion(pct))} style={{ width: `${Math.min(100, pct)}%` }} />
          </div>
        </div>
      )}

      <DataTable
        caption={`Inventario del rack ${codigo}`}
        data={invQ.data}
        loading={invQ.isLoading}
        error={invQ.error}
        onRetry={() => void invQ.refetch()}
        rowKey={(i) => i.id_detalle_inventario ?? i.id_inventario}
        empty={<EmptyState compact icon="box" title="Rack vacío" description="Este rack no tiene inventario registrado." />}
        columns={[
          {
            id: 'producto',
            header: 'Producto',
            mobile: 'title',
            cell: (i) => {
              const p = productoPorId.get(i.id_producto) ?? i.producto
              return p ? (
                <Link to={paths.producto(i.id_producto)} className="font-medium hover:underline">
                  {p.nombre}
                </Link>
              ) : (
                <span className="font-mono text-xs text-fg-subtle">{productosQ.isLoading ? 'Cargando…' : i.id_producto.slice(0, 8)}</span>
              )
            },
          },
          { id: 'estado', header: 'Estado', mobile: 'badge', cell: (i) => <StockBadge inventario={i} /> },
          {
            id: 'stock',
            header: 'Actual',
            align: 'right',
            cell: (i) => <span className="tabular font-mono font-semibold">{formatNumero(i.stock_actual)}</span>,
          },
          {
            id: 'rango',
            header: 'Mín / Máx',
            align: 'right',
            cell: (i) => (
              <span className="tabular font-mono text-fg-muted">
                {formatNumero(i.stock_minimo)} / {formatNumero(i.stock_maximo)}
              </span>
            ),
          },
        ]}
      />
    </Card>
  )
}
