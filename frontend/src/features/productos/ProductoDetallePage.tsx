/**
 * Detalle de producto: ficha completa, existencias reales por ubicación (inventarios del producto,
 * con StockBadge y acciones) e historial de movimientos del producto. Editar / eliminar con confirmación.
 * Producto.stock NO se muestra como stock: el total es Σ Inventario.stock_actual.
 */
import { useState, type ReactNode } from 'react'
import { useNavigate, useParams } from 'react-router'
import { ApiError } from '@/api/client'
import { useInventariosPorProducto } from '@/api/inventarios'
import { useMovimientosPorProducto } from '@/api/movimientos'
import { useDeleteProducto, useProducto } from '@/api/productos'
import { useUbicaciones } from '@/api/ubicaciones'
import {
  Badge,
  Button,
  Card,
  ConfirmDialog,
  EmptyState,
  ErrorState,
  LinkButton,
  LoadingBlock,
  Modal,
  PageHeader,
  useToast,
} from '@/components/ui'
import { formatNumero, shortId } from '@/lib/format'
import { resumenStock } from '@/lib/stock'
import { paths } from '@/paths'
import { FormAlert } from '@/features/inventario/formUtils'
import { InventarioCrearForm } from '@/features/inventario/InventarioForm'
import { InventariosTable } from '@/features/inventario/InventariosTable'
import { MovimientoModal } from '@/features/movimientos/MovimientoForm'
import { MovimientosTable } from '@/features/movimientos/MovimientosTable'
import { useRol } from '@/auth/useRol'
import { ProductoForm, RackReferenciaForm } from './ProductoForm'
import { RefrigeracionBadge } from './stockProducto'

const HISTORIAL_MAX = 20

function Dato({ label, children, mono }: { label: string; children: ReactNode; mono?: boolean }) {
  return (
    <div className="min-w-0">
      <dt className="label-stencil">{label}</dt>
      <dd className={mono ? 'font-mono text-sm text-fg' : 'text-sm text-fg'}>{children}</dd>
    </div>
  )
}

function Cifra({ label, value, tone }: { label: string; value: ReactNode; tone?: string }) {
  return (
    <div className="rounded-[calc(var(--radius-ui)+2px)] border border-border bg-surface px-4 py-3 shadow-card">
      <p className="label-stencil">{label}</p>
      <p className={`mt-1 font-mono text-2xl font-semibold tabular ${tone ?? 'text-fg'}`}>{value}</p>
    </div>
  )
}

export default function ProductoDetallePage() {
  const { idProducto } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const q = useProducto(idProducto)
  const ub = useUbicaciones()
  const { esOperario, esProveedor } = useRol()
  // El PROVEEDOR no puede leer inventario ni movimientos: solo ve la ficha de su producto.
  const inventarios = useInventariosPorProducto(esProveedor ? undefined : idProducto)
  const movimientos = useMovimientosPorProducto(esProveedor ? undefined : idProducto)
  const [asignando, setAsignando] = useState(false)
  const eliminar = useDeleteProducto()

  const [editando, setEditando] = useState(false)
  const [creandoInv, setCreandoInv] = useState(false)
  const [registrando, setRegistrando] = useState(false)
  const [confirmando, setConfirmando] = useState(false)
  const [errorEliminar, setErrorEliminar] = useState<string | null>(null)

  const back = { to: paths.productos, label: 'Productos' }

  if (q.isLoading) return <LoadingBlock label="Cargando producto…" />
  if (q.error || !q.data) {
    const noExiste = q.error instanceof ApiError && q.error.isNotFound
    return (
      <>
        <PageHeader title="Producto" eyebrow="Catálogo" back={back} />
        {noExiste ? (
          <EmptyState icon="box" title="Producto no encontrado" description="Puede que haya sido eliminado." action={<LinkButton to={paths.productos}>Volver al catálogo</LinkButton>} />
        ) : (
          <ErrorState error={q.error} onRetry={() => void q.refetch()} />
        )}
      </>
    )
  }

  const p = q.data
  const invs = inventarios.data && !ub.isLoading ? inventarios.data.filter((i) => ub.perteneceAEmpresa(i.id_rack)) : undefined
  const resumen = invs ? resumenStock(invs) : undefined
  const total = invs?.reduce((acc, i) => acc + i.stock_actual, 0)
  const rackRef = p.id_rack ? ub.porRack.get(p.id_rack) : undefined
  const alertas = resumen ? resumen.sinStock + resumen.stockBajo + resumen.sobreStock : 0
  const historial = movimientos.data?.slice(0, HISTORIAL_MAX)

  const confirmarEliminar = () => {
    setErrorEliminar(null)
    eliminar.mutate(p.id_producto, {
      onSuccess: () => {
        toast.success(`"${p.nombre}" eliminado`, 'Producto eliminado')
        setConfirmando(false)
        navigate(paths.productos, { replace: true })
      },
      onError: (e) => {
        if (e instanceof ApiError && e.isHandledGlobally) return
        setErrorEliminar(e instanceof ApiError ? e.detail : 'No se pudo eliminar el producto.')
      },
    })
  }

  return (
    <>
      <PageHeader
        title={p.nombre}
        eyebrow="Producto"
        back={back}
        meta={
          <>
            <Badge tone="neutral" dot={false}>
              {p.categoria}
            </Badge>
            {p.familia && (
              <Badge tone="neutral" dot={false}>
                {p.familia}
              </Badge>
            )}
            <RefrigeracionBadge producto={p} />
            <span className="font-mono text-xs text-fg-subtle">#{shortId(p.id_producto)}</span>
          </>
        }
        actions={
          <>
            {esOperario && (
              <>
                <Button icon="arrows" onClick={() => setRegistrando(true)} disabled={!invs || invs.length === 0}>
                  Registrar salida
                </Button>
                <Button variant="secondary" icon="pin" onClick={() => setAsignando(true)}>
                  {p.id_rack ? 'Cambiar rack de referencia' : 'Asignar rack de referencia'}
                </Button>
              </>
            )}
            {esProveedor && (
              <>
                <Button variant="secondary" icon="edit" onClick={() => setEditando(true)}>
                  Editar
                </Button>
                <Button
                  variant="ghost"
                  icon="trash"
                  onClick={() => {
                    setErrorEliminar(null)
                    setConfirmando(true)
                  }}
                >
                  Eliminar
                </Button>
              </>
            )}
          </>
        }
      />

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Cifra label="Stock total" value={total === undefined ? '…' : formatNumero(total)} />
        <Cifra label="Ubicaciones" value={invs ? formatNumero(invs.length) : '…'} />
        <Cifra label="Con alerta" value={resumen ? formatNumero(alertas) : '…'} tone={alertas > 0 ? 'text-warning' : 'text-fg'} />
        <Cifra label="Movimientos" value={movimientos.data ? formatNumero(movimientos.data.length) : '…'} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Ficha del producto" className="lg:col-span-1">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Dato label="Marca">{p.marca || '—'}</Dato>
            <Dato label="Categoría">{p.categoria || '—'}</Dato>
            <Dato label="Familia">{p.familia || '—'}</Dato>
            <Dato label="Peso" mono>
              {formatNumero(p.peso, 'kg')}
            </Dato>
            <Dato label="Cantidad por empaque" mono>
              {formatNumero(p.volumen, 'und.')}
            </Dato>
            <Dato label="Reposición" mono>
              {formatNumero(p.lead_time_dias, 'días')}
            </Dato>
            <Dato label="Vida útil" mono>
              {formatNumero(p.vida_util_dias, 'días')}
            </Dato>
            <Dato label="Refrigeración">
              {p.requiere_refrigeracion
                ? `Sí · ${formatNumero(p.temperatura_min_almacenamiento)} a ${formatNumero(p.temperatura_max_almacenamiento)} °C`
                : 'No'}
            </Dato>
            <div className="col-span-2">
              <Dato label="Rack de referencia">{rackRef?.etiqueta ?? (ub.isLoading ? '…' : 'Sin rack asignado')}</Dato>
            </div>
          </dl>
        </Card>

        {!esProveedor && (
        <section className="flex flex-col gap-3 lg:col-span-2" aria-labelledby="existencias-titulo">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <h2 id="existencias-titulo" className="text-base font-semibold text-fg">
                Existencias por ubicación
              </h2>
              <p className="text-sm text-fg-muted">Stock real de cada rack (inventario).</p>
            </div>
            {esOperario && (
              <Button size="sm" variant="secondary" icon="plus" onClick={() => setCreandoInv(true)}>
                Nuevo inventario
              </Button>
            )}
          </div>
          <InventariosTable
            caption={`Inventarios de ${p.nombre}`}
            data={invs}
            mostrarProducto={false}
            loading={inventarios.isLoading || ub.isLoading}
            error={inventarios.error ?? ub.error}
            onRetry={() => void inventarios.refetch()}
            empty={
              <EmptyState
                compact
                icon="layers"
                title="Sin inventario"
                description="Este producto aún no tiene stock asignado a ningún rack."
                {...(esOperario
                  ? {
                      action: (
                        <Button size="sm" icon="plus" onClick={() => setCreandoInv(true)}>
                          Crear inventario
                        </Button>
                      ),
                    }
                  : {})}
              />
            }
          />
        </section>
        )}
      </div>

      {!esProveedor && (
      <section className="mt-8 flex flex-col gap-3" aria-labelledby="historial-titulo">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 id="historial-titulo" className="text-base font-semibold text-fg">
              Historial de movimientos
            </h2>
            <p className="text-sm text-fg-muted">
              {movimientos.data && movimientos.data.length > HISTORIAL_MAX
                ? `Últimos ${HISTORIAL_MAX} de ${formatNumero(movimientos.data.length)}.`
                : 'Entradas, salidas y ajustes de este producto.'}
            </p>
          </div>
          <LinkButton size="sm" variant="ghost" iconRight="chevron-right" to={`${paths.movimientos}?producto=${encodeURIComponent(p.id_producto)}`}>
            Ver en Movimientos
          </LinkButton>
        </div>
        <MovimientosTable
          caption={`Movimientos de ${p.nombre}`}
          data={historial}
          ocultarProducto
          loading={movimientos.isLoading}
          error={movimientos.error}
          onRetry={() => void movimientos.refetch()}
          empty={<EmptyState compact icon="arrows" title="Sin movimientos" description="Aún no se registran entradas, salidas ni ajustes." />}
        />
      </section>
      )}

      <Modal open={asignando} onClose={() => setAsignando(false)} size="lg" title="Rack de referencia" description={p.nombre}>
        {asignando && <RackReferenciaForm producto={p} onCancel={() => setAsignando(false)} onSuccess={() => setAsignando(false)} />}
      </Modal>

      <Modal open={editando} onClose={() => setEditando(false)} size="lg" title="Editar producto" description={p.nombre}>
        <ProductoForm producto={p} onCancel={() => setEditando(false)} onSuccess={() => setEditando(false)} />
      </Modal>

      <Modal open={creandoInv} onClose={() => setCreandoInv(false)} size="lg" title="Nuevo inventario" description={`Asigna ${p.nombre} a un rack.`}>
        <InventarioCrearForm
          idProducto={p.id_producto}
          productoFijo
          idRack={invs && invs.length === 0 ? p.id_rack : undefined}
          onCancel={() => setCreandoInv(false)}
          onSuccess={() => setCreandoInv(false)}
        />
      </Modal>

      <MovimientoModal open={registrando} onClose={() => setRegistrando(false)} idProducto={p.id_producto} />

      <ConfirmDialog
        open={confirmando}
        title="Eliminar producto"
        tone="danger"
        confirmLabel="Eliminar"
        loading={eliminar.isPending}
        onCancel={() => setConfirmando(false)}
        onConfirm={confirmarEliminar}
        description={
          <div className="flex flex-col gap-3">
            <p>
              ¿Eliminar <strong className="text-fg">{p.nombre}</strong> del catálogo? Esta acción no se puede deshacer.
            </p>
            {invs && invs.length > 0 && (
              <p>Tiene {invs.length === 1 ? '1 ubicación' : `${invs.length} ubicaciones`} con inventario: el sistema puede rechazar la eliminación.</p>
            )}
            {errorEliminar && <FormAlert title="No se pudo eliminar">{errorEliminar}</FormAlert>}
          </div>
        }
      />
    </>
  )
}
