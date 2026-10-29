/**
 * Detalle de almacén: datos del almacén (editar / eliminar), CRUD de zonas (cada una con nº de racks y enlace
 * a su detalle) y operarios registrados en él (solo lectura; el almacén se asigna al crear el operario).
 */
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { useAlmacen, useAlmacenes } from '@/api/almacenes'
import { ApiError } from '@/api/client'
import { etiquetaTurno, operarioActivo } from '@/api/enums'
import { useOperarios } from '@/api/operarios'
import { useRacks } from '@/api/racks'
import type { Almacen, Zona } from '@/api/types'
import { useDeleteZona, useZonasPorAlmacen } from '@/api/zonas'
import { useIdEmpresa } from '@/auth/useEmpresa'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Icon,
  LinkButton,
  LoadingBlock,
  PageHeader,
  Spinner,
  StatusBadge,
} from '@/components/ui'
import { formatCoordenadas, formatNumero } from '@/lib/format'
import { useRol } from '@/auth/useRol'
import { paths } from '@/paths'
import { AlmacenFormModal, EliminarAlmacenDialog } from './AlmacenDialogs'
import { EliminarDialog } from './EliminarDialog'
import { ZonaFormModal } from './ZonaForm'

export default function AlmacenDetallePage() {
  const { idAlmacen } = useParams()
  const idEmpresa = useIdEmpresa()
  const almacenQ = useAlmacen(idAlmacen)
  const almacen = almacenQ.data
  const back = { to: paths.inicio, label: 'Almacenes' }

  if (almacenQ.isLoading) return <LoadingBlock label="Cargando almacén…" />
  if (almacenQ.error || !almacen) {
    const noExiste = almacenQ.error instanceof ApiError && almacenQ.error.isNotFound
    return (
      <>
        <PageHeader title="Almacén" back={back} />
        {noExiste ? (
          <EmptyState icon="warehouse" title="Almacén no encontrado" description="Puede que haya sido eliminado." action={<LinkButton to={paths.inicio}>Volver a almacenes</LinkButton>} />
        ) : (
          <ErrorState error={almacenQ.error} onRetry={() => void almacenQ.refetch()} />
        )}
      </>
    )
  }
  if (idEmpresa && almacen.id_empresa && almacen.id_empresa !== idEmpresa) {
    return (
      <>
        <PageHeader title="Almacén" back={back} />
        <EmptyState icon="warehouse" title="Almacén no disponible" description="Este almacén no pertenece a tu empresa." />
      </>
    )
  }
  return <Contenido almacen={almacen} />
}

/* ------------------------------------------------------------------ */

function Contenido({ almacen }: { almacen: Almacen }) {
  const navigate = useNavigate()
  const totalAlmacenes = useAlmacenes().data?.length ?? 0
  const [editarAlmacen, setEditarAlmacen] = useState(false)
  const [eliminarAlmacen, setEliminarAlmacen] = useState(false)
  const [zonaForm, setZonaForm] = useState<{ zona: Zona | null } | null>(null)
  const { esEmpresa } = useRol()

  const coords =
    Number.isFinite(almacen.latitud) && Number.isFinite(almacen.longitud) ? { lat: almacen.latitud, lon: almacen.longitud } : null

  return (
    <>
      <PageHeader
        back={{ to: paths.inicio, label: esEmpresa ? 'Almacenes' : 'Inicio' }}
        eyebrow="Almacén"
        title={almacen.nombre}
        meta={
          <>
            <Badge tone="accent">{almacen.tipo_almacen}</Badge>
            <span className="inline-flex items-center gap-1 font-mono text-sm text-fg-muted">
              <Icon name="pin" className="size-4" />
              {formatCoordenadas(almacen.latitud, almacen.longitud)}
            </span>
          </>
        }
        {...(esEmpresa
          ? {
              actions: (
                <>
                  <Button variant="secondary" icon="edit" onClick={() => setEditarAlmacen(true)}>
                    Editar
                  </Button>
                  <Button variant="ghost" icon="trash" onClick={() => setEliminarAlmacen(true)} className="hover:text-danger">
                    Eliminar
                  </Button>
                  <Button icon="plus" onClick={() => setZonaForm({ zona: null })}>
                    Nueva zona
                  </Button>
                </>
              ),
            }
          : {})}
      />

      <div className="mb-5"><LinkButton to={paths.plano(almacen.id_almacen)}>Plano del almacén</LinkButton></div>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <ZonasSection idAlmacen={almacen.id_almacen} onNueva={() => setZonaForm({ zona: null })} onEditar={(zona) => setZonaForm({ zona })} />

        <aside className="flex flex-col gap-6">
          <Card eyebrow="Ficha" title="Datos del almacén">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
              <DatoFicha label="Área" valor={formatNumero(almacen.area_m2, 'm²')} />
              <DatoFicha label="Aforo" valor={formatNumero(almacen.aforo, 'pers.')} />
              <DatoFicha label="Tipo" valor={almacen.tipo_almacen} className="col-span-2" mono={false} />
              <DatoFicha
                label="Coordenadas"
                className="col-span-2"
                valor={
                  coords ? (
                    <a
                      href={`https://www.openstreetmap.org/?mlat=${coords.lat}&mlon=${coords.lon}#map=17/${coords.lat}/${coords.lon}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-info hover:underline"
                    >
                      {formatCoordenadas(coords.lat, coords.lon)}
                      <span className="sr-only"> (abre el mapa en una pestaña nueva)</span>
                    </a>
                  ) : (
                    '—'
                  )
                }
              />
            </dl>
          </Card>

          {esEmpresa && <OperariosCard idAlmacen={almacen.id_almacen} />}
        </aside>
      </div>

      <AlmacenFormModal open={editarAlmacen} almacen={almacen} onClose={() => setEditarAlmacen(false)} />
      <EliminarAlmacenDialog
        almacen={eliminarAlmacen ? almacen : null}
        esUltimo={totalAlmacenes === 1}
        onClose={() => setEliminarAlmacen(false)}
        onEliminado={() => navigate(paths.inicio, { replace: true })}
      />
      <ZonaFormModal open={!!zonaForm} idAlmacen={almacen.id_almacen} zona={zonaForm?.zona ?? null} onClose={() => setZonaForm(null)} />
    </>
  )
}

function DatoFicha({ label, valor, className, mono = true }: { label: string; valor: React.ReactNode; className?: string; mono?: boolean }) {
  return (
    <div className={className}>
      <dt className="text-xs text-fg-subtle">{label}</dt>
      <dd className={mono ? 'tabular font-mono font-medium text-fg' : 'font-medium text-fg'}>{valor}</dd>
    </div>
  )
}

/* ------------------------------------------------------------------ */

function ZonasSection({ idAlmacen, onNueva, onEditar }: { idAlmacen: string; onNueva: () => void; onEditar: (z: Zona) => void }) {
  const zonasQ = useZonasPorAlmacen(idAlmacen)
  const racksQ = useRacks()
  const del = useDeleteZona()
  const [aEliminar, setAEliminar] = useState<Zona | null>(null)
  const { esEmpresa } = useRol()

  const racksPorZona = new Map<string, number>()
  for (const r of racksQ.data ?? []) racksPorZona.set(r.id_zona, (racksPorZona.get(r.id_zona) ?? 0) + 1)
  const zonas = [...(zonasQ.data ?? [])].sort((a, b) => a.nombre.localeCompare(b.nombre, 'es', { numeric: true }))

  return (
    <section aria-labelledby="titulo-zonas" className="min-w-0">
      <h2 id="titulo-zonas" className="label-stencil mb-3">
        Zonas {zonasQ.data && <span className="tabular">({zonas.length})</span>}
      </h2>

      {zonasQ.isLoading ? (
        <LoadingBlock label="Cargando zonas…" />
      ) : zonasQ.error ? (
        <ErrorState error={zonasQ.error} onRetry={() => void zonasQ.refetch()} />
      ) : zonas.length === 0 ? (
        <EmptyState
          icon="layers"
          title="Este almacén no tiene zonas"
          description={esEmpresa ? 'Divide el almacén en zonas (secos, refrigerado, picking…) y luego agrega racks a cada una.' : 'La empresa aún no creó zonas.'}
          {...(esEmpresa
            ? {
                action: (
                  <Button icon="plus" onClick={onNueva}>
                    Crear primera zona
                  </Button>
                ),
              }
            : {})}
        />
      ) : (
        <ul className="grid gap-4 md:grid-cols-2">
          {zonas.map((z) => (
            <li key={z.id_zona}>
              <ZonaCard
                zona={z}
                racks={racksQ.isLoading ? undefined : (racksPorZona.get(z.id_zona) ?? 0)}
                onEditar={() => onEditar(z)}
                onEliminar={() => setAEliminar(z)}
              />
            </li>
          ))}
        </ul>
      )}

      <EliminarDialog
        open={!!aEliminar}
        title="Eliminar zona"
        description={
          <>
            Se eliminará <strong className="text-fg">{aEliminar?.nombre}</strong>. Si tiene racks con inventario, el sistema puede impedirlo.
          </>
        }
        accion={() => del.mutateAsync(aEliminar!.id_zona)}
        mensajeExito="Zona eliminada"
        tituloError="No se pudo eliminar la zona"
        onClose={() => setAEliminar(null)}
      />
    </section>
  )
}

function ZonaCard({ zona: z, racks, onEditar, onEliminar }: { zona: Zona; racks: number | undefined; onEditar: () => void; onEliminar: () => void }) {
  const fria = z.refrigerada
  const { esEmpresa } = useRol()
  const link = paths.zona(z.id_almacen, z.id_zona)
  return (
    <Card as="article" padding="none" accent="accent" className="flex h-full flex-col">
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div className="min-w-0">
          <p className="label-stencil mb-1 truncate">{z.tipo_zona}</p>
          <h3 className="text-base leading-tight font-semibold">
            <Link to={link} className="hover:underline">
              {z.nombre}
            </Link>
          </h3>
        </div>
        <dl className="grid grid-cols-3 gap-2 text-sm">
          <div>
            <dt className="text-xs text-fg-subtle">Racks</dt>
            <dd className="tabular font-mono font-semibold">{racks === undefined ? <Spinner size="sm" label="Cargando racks" /> : racks}</dd>
          </div>
          <div>
            <dt className="text-xs text-fg-subtle">Niveles</dt>
            <dd className="tabular font-mono font-semibold">{formatNumero(z.capacidad)}</dd>
          </div>
          <div>
            <dt className="text-xs text-fg-subtle">Conservación</dt>
            <dd className="tabular flex items-center gap-1 font-mono text-xs font-semibold">
              {fria && <Icon name="snowflake" className="size-3.5 text-info" />}
              {fria ? 'Refrigerada' : 'No refrigerada'}
            </dd>
          </div>
        </dl>
        <div className="mt-auto flex items-center gap-2 pt-1">
          <LinkButton to={link} variant="secondary" size="sm" iconRight="chevron-right" className="flex-1" aria-label={`Ver racks de ${z.nombre}`}>
            Ver racks
          </LinkButton>
          {esEmpresa && (
            <>
              <Button variant="ghost" size="sm" iconOnly icon="edit" aria-label={`Editar ${z.nombre}`} onClick={onEditar} />
              <Button variant="ghost" size="sm" iconOnly icon="trash" aria-label={`Eliminar ${z.nombre}`} onClick={onEliminar} className="hover:text-danger" />
            </>
          )}
        </div>
      </div>
    </Card>
  )
}

/* ------------------------------------------------------------------ */

function OperariosCard({ idAlmacen }: { idAlmacen: string }) {
  const q = useOperarios({ idAlmacen, estrictoAlmacen: true })
  const operarios = [...(q.data ?? [])].sort((a, b) => `${a.apellido} ${a.nombre}`.localeCompare(`${b.apellido} ${b.nombre}`, 'es'))
  const activos = operarios.filter((o) => operarioActivo(o.estado)).length

  return (
    <Card
      eyebrow="Personal"
      title="Operarios"
      {...(q.data ? { description: `${activos} activo${activos === 1 ? '' : 's'} de ${operarios.length}` } : {})}
      actions={
        <LinkButton to={paths.operarios} variant="ghost" size="sm" iconRight="chevron-right">
          Gestionar
        </LinkButton>
      }
    >
      {q.isLoading ? (
        <div className="flex justify-center py-4">
          <Spinner label="Cargando operarios" />
        </div>
      ) : q.error ? (
        <ErrorState error={q.error} onRetry={() => void q.refetch()} />
      ) : operarios.length === 0 ? (
        <p className="text-sm text-fg-muted">
          No hay operarios registrados.{' '}
          <Link to={paths.operarios} className="font-medium text-info hover:underline">
            Registrar operarios
          </Link>
        </p>
      ) : (
        <ul className="-my-2 divide-y divide-border">
          {operarios.map((o) => (
            <li key={o.id_operario} className="flex items-center justify-between gap-3 py-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">
                  {o.nombre} {o.apellido}
                </p>
                <p className="truncate text-xs text-fg-subtle">
                  {o.cargo} · Turno {etiquetaTurno(o.turno)}
                </p>
              </div>
              <StatusBadge estado={o.estado} />
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
