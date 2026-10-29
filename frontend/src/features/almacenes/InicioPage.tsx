/**
 * Inicio / dashboard: almacenes de la empresa (tarjetas) + resumen de alertas de inventario.
 * Los contadores usan GET /inventarios acotado a la empresa con useUbicaciones().perteneceAEmpresa.
 * Nº de zonas y racks por almacén: se derivan de useUbicaciones (listas ya cacheadas, sin peticiones extra).
 */
import { useState } from 'react'
import { Link } from 'react-router'
import { useAlmacenes } from '@/api/almacenes'
import { useInventarios } from '@/api/inventarios'
import type { Almacen, EstadoStock } from '@/api/types'
import { useUbicaciones } from '@/api/ubicaciones'
import { useEmpresa } from '@/auth/useEmpresa'
import { Badge, Button, Card, EmptyState, ErrorState, Icon, LinkButton, LoadingBlock, PageHeader, Spinner, type IconName } from '@/components/ui'
import { cn } from '@/lib/cn'
import { formatCoordenadas, formatNumero } from '@/lib/format'
import { resumenStock } from '@/lib/stock'
import { paths } from '@/paths'
import { AlmacenFormModal, EliminarAlmacenDialog } from './AlmacenDialogs'
import PlanoImagen from '@/assets/PlanoImagen.jpeg'


export default function InicioPage() {
  const { empresa } = useEmpresa()
  const almacenesQ = useAlmacenes()
  const ubic = useUbicaciones()
  const [formAbierto, setFormAbierto] = useState(false)
  const [aEditar, setAEditar] = useState<Almacen | null>(null)
  const [aEliminar, setAEliminar] = useState<Almacen | null>(null)

  const almacenes = [...(almacenesQ.data ?? [])].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))

  const zonasPorAlmacen = new Map<string, number>()
  for (const z of ubic.zonas) zonasPorAlmacen.set(z.id_almacen, (zonasPorAlmacen.get(z.id_almacen) ?? 0) + 1)
  const racksPorAlmacen = new Map<string, number>()
  for (const r of ubic.racks) racksPorAlmacen.set(r.almacen.id_almacen, (racksPorAlmacen.get(r.almacen.id_almacen) ?? 0) + 1)
  const conteosCargando = ubic.isLoading

  const abrirNuevo = () => {
    setAEditar(null)
    setFormAbierto(true)
  }
  const abrirEditar = (a: Almacen) => {
    setAEditar(a)
    setFormAbierto(true)
  }

  return (
    <>
      <PageHeader
        eyebrow="Inicio"
        title="Almacenes"
        description={empresa?.nombre ? `Panel de ${empresa.nombre}. Entra a un almacén para gestionar sus zonas y racks.` : undefined}
        actions={
          <Button icon="plus" onClick={abrirNuevo}>
            Nuevo almacén
          </Button>
        }
      />

      <ResumenAlertas />

      <section aria-labelledby="titulo-almacenes" className="mt-8">
        <div className="mb-3 flex items-baseline justify-between gap-3">
          <h2 id="titulo-almacenes" className="label-stencil">
            Mis almacenes {almacenesQ.data && <span className="tabular">({almacenes.length})</span>}
          </h2>
        </div>

        {almacenesQ.isLoading ? (
          <LoadingBlock label="Cargando almacenes…" />
        ) : almacenesQ.error ? (
          <ErrorState error={almacenesQ.error} onRetry={() => void almacenesQ.refetch()} />
        ) : almacenes.length === 0 ? (
          <EmptyState
            icon="warehouse"
            title="Aún no tienes almacenes"
            description="Crea un almacén para empezar a organizar zonas, racks e inventario."
            action={
              <Button icon="plus" onClick={abrirNuevo}>
                Nuevo almacén
              </Button>
            }
          />
        ) : (
          <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {almacenes.map((a) => (
              <li key={a.id_almacen}>
                <AlmacenCard
                  almacen={a}
                  zonas={conteosCargando ? undefined : (zonasPorAlmacen.get(a.id_almacen) ?? 0)}
                  racks={conteosCargando ? undefined : (racksPorAlmacen.get(a.id_almacen) ?? 0)}
                  onEditar={() => abrirEditar(a)}
                  onEliminar={() => setAEliminar(a)}
                />
              </li>
            ))}
          </ul>
        )}
      </section>

      <figure className="mt-8 overflow-hidden rounded-[calc(var(--radius-ui)+2px)] border border-border bg-surface shadow-card">
        <img
          src={PlanoImagen}
          alt="Plano del almacén"
          className="h-auto w-full object-contain"
          loading="lazy"
        />
      </figure>
      
      <AlmacenFormModal open={formAbierto} almacen={aEditar} onClose={() => setFormAbierto(false)} />
      <EliminarAlmacenDialog almacen={aEliminar} esUltimo={almacenes.length === 1} onClose={() => setAEliminar(null)} />
    </>
  )
}

/* ------------------------------------------------------------------ */

function AlmacenCard({
  almacen: a,
  zonas,
  racks,
  onEditar,
  onEliminar,
}: {
  almacen: Almacen
  zonas: number | undefined
  racks: number | undefined
  onEditar: () => void
  onEliminar: () => void
}) {
  return (
    <Card as="article" padding="none" className="flex h-full flex-col overflow-hidden">
      <div className="hazard-stripe h-1" aria-hidden="true" />
      <div className="flex flex-1 flex-col gap-4 p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="label-stencil mb-1 truncate">{a.tipo_almacen}</p>
            <h3 className="text-lg leading-tight font-semibold">
              <Link to={paths.almacen(a.id_almacen)} className="hover:underline">
                {a.nombre}
              </Link>
            </h3>
            <p className="mt-1 flex items-center gap-1 text-sm text-fg-muted">
              <Icon name="pin" className="size-4 shrink-0" />
              <span className="truncate font-mono text-xs">{formatCoordenadas(a.latitud, a.longitud, 4)}</span>
            </p>
          </div>
          <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-accent-ink">
            <Icon name="warehouse" className="size-5" />
          </span>
        </div>

        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-[var(--radius-ui)] border border-border bg-surface-2/50 p-3 text-sm">
          <Dato label="Área" valor={formatNumero(a.area_m2, 'm²')} />
          <Dato label="Aforo" valor={formatNumero(a.aforo, 'pers.')} />
          <Dato label="Zonas" valor={zonas === undefined ? <Spinner size="sm" label="Cargando zonas" /> : formatNumero(zonas)} />
          <Dato label="Racks" valor={racks === undefined ? <Spinner size="sm" label="Cargando racks" /> : formatNumero(racks)} />
        </dl>

        <div className="mt-auto flex items-center gap-2">
          <LinkButton to={paths.almacen(a.id_almacen)} variant="secondary" iconRight="chevron-right" className="flex-1" aria-label={`Ver zonas de ${a.nombre}`}>
            Ver zonas
          </LinkButton>
          <Button variant="ghost" iconOnly icon="edit" aria-label={`Editar ${a.nombre}`} onClick={onEditar} />
          <Button variant="ghost" iconOnly icon="trash" aria-label={`Eliminar ${a.nombre}`} onClick={onEliminar} className="hover:text-danger" />
        </div>
      </div>
    </Card>
  )
}

function Dato({ label, valor }: { label: string; valor: React.ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-fg-subtle">{label}</dt>
      <dd className="tabular font-mono font-semibold text-fg">{valor}</dd>
    </div>
  )
}

/* ------------------------------------------------------------------ */

const ALERTAS: { estado: EstadoStock; label: string; descripcion: string; icon: IconName; tone: 'danger' | 'warning' | 'info' }[] = [
  { estado: 'SIN_STOCK', label: 'Sin stock', descripcion: 'Stock actual en 0', icon: 'alert', tone: 'danger' },
  { estado: 'STOCK_BAJO', label: 'Stock bajo', descripcion: 'Por debajo del mínimo', icon: 'arrows', tone: 'warning' },
  { estado: 'SOBRE_STOCK', label: 'Sobre stock', descripcion: 'Por encima del máximo', icon: 'layers', tone: 'info' },
]

const TONE_CLASES = {
  danger: { borde: 'border-l-danger', icono: 'bg-danger-soft text-danger' },
  warning: { borde: 'border-l-warning', icono: 'bg-warning-soft text-warning' },
  info: { borde: 'border-l-info', icono: 'bg-info-soft text-info' },
}

function ResumenAlertas() {
  const invQ = useInventarios()
  const ubic = useUbicaciones()
  const cargando = invQ.isLoading || ubic.isLoading
  const error = invQ.error ?? ubic.error

  const deEmpresa = (invQ.data ?? []).filter((i) => ubic.perteneceAEmpresa(i.id_rack))
  const r = resumenStock(deEmpresa)
  const valores: Record<string, number> = { SIN_STOCK: r.sinStock, STOCK_BAJO: r.stockBajo, SOBRE_STOCK: r.sobreStock }
  const totalAlertas = r.sinStock + r.stockBajo + r.sobreStock

  return (
    <section aria-labelledby="titulo-alertas">
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="titulo-alertas" className="label-stencil">
          Alertas de inventario
        </h2>
        <Link to={paths.inventario} className="inline-flex min-h-6 items-center gap-1 text-sm font-medium text-fg-muted hover:text-fg">
          Ver inventario
          <Icon name="chevron-right" className="size-4" />
        </Link>
      </div>

      {error && !cargando ? (
        <ErrorState
          error={error}
          title="No se pudieron cargar las alertas"
          onRetry={() => {
            void invQ.refetch()
          }}
        />
      ) : (
        <>
          <ul className="grid gap-3 sm:grid-cols-3">
            {ALERTAS.map((al) => {
              const t = TONE_CLASES[al.tone]
              const n = valores[al.estado] ?? 0
              return (
                <li key={al.estado}>
                  <Link
                    to={`${paths.inventario}?estado=${al.estado.toLowerCase().replace('_', '-')}`}
                    className={cn(
                      'flex items-center gap-3 rounded-[calc(var(--radius-ui)+2px)] border border-l-4 border-border bg-surface p-4 shadow-card transition-colors hover:bg-surface-2',
                      t.borde,
                    )}
                  >
                    <span className={cn('flex size-10 shrink-0 items-center justify-center rounded-lg', t.icono)}>
                      <Icon name={al.icon} className="size-5" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-medium text-fg">{al.label}</span>
                      <span className="block text-xs text-fg-subtle">{al.descripcion}</span>
                    </span>
                    <span className="tabular font-mono text-2xl font-semibold text-fg" aria-live="polite">
                      {cargando ? <Spinner size="sm" label={`Cargando ${al.label}`} /> : n}
                    </span>
                  </Link>
                </li>
              )
            })}
          </ul>
          {!cargando && (
            <p className="mt-2 flex flex-wrap items-center gap-2 text-xs text-fg-subtle">
              {r.total === 0 ? (
                'Todavía no hay inventario registrado en tus almacenes.'
              ) : totalAlertas === 0 ? (
                <>
                  <Badge tone="success">Todo en orden</Badge> {r.total} registros de inventario con stock normal.
                </>
              ) : (
                <>
                  {totalAlertas} de {r.total} registros de inventario requieren atención.
                </>
              )}
            </p>
          )}
        </>
      )}
    </section>
  )
}
