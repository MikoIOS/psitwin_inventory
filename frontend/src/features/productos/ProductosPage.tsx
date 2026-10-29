/**
 * Catálogo de productos de la empresa: búsqueda por nombre, filtro por categoría y "solo refrigerados".
 * El stock mostrado es la suma de Inventario.stock_actual de sus ubicaciones (nunca Producto.stock).
 */
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { ApiError } from '@/api/client'
import { useDeleteProducto, useProductos } from '@/api/productos'
import type { Producto } from '@/api/types'
import {
  Button,
  Card,
  Checkbox,
  ConfirmDialog,
  DataTable,
  type Column,
  EmptyState,
  Field,
  Input,
  Modal,
  PageHeader,
  Select,
  StockBadge,
  useToast,
} from '@/components/ui'
import { formatNumero } from '@/lib/format'
import { paths } from '@/paths'
import { FormAlert } from '@/features/inventario/formUtils'
import { useRol } from '@/auth/useRol'
import { ProductoForm, RackReferenciaForm } from './ProductoForm'
import { RefrigeracionBadge, useStockPorProducto } from './stockProducto'

const normalizar = (s: string) => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().trim()

export default function ProductosPage() {
  const navigate = useNavigate()
  const toast = useToast()
  const q = useProductos()
  const stock = useStockPorProducto()
  const eliminar = useDeleteProducto()
  const { esProveedor, esOperario } = useRol()
  const [asignando, setAsignando] = useState<Producto | null>(null)

  const [busqueda, setBusqueda] = useState('')
  const [categoria, setCategoria] = useState('')
  const [soloRefrigerados, setSoloRefrigerados] = useState(false)
  const [creando, setCreando] = useState(false)
  const [editando, setEditando] = useState<Producto | null>(null)
  const [aEliminar, setAEliminar] = useState<Producto | null>(null)
  const [errorEliminar, setErrorEliminar] = useState<string | null>(null)

  const categorias = [...new Set((q.data ?? []).map((p) => p.categoria).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'es'))
  const termino = normalizar(busqueda)
  const filas = q.data
    ?.filter(
      (p) =>
        (!termino || normalizar(p.nombre).includes(termino)) &&
        (!categoria || p.categoria === categoria) &&
        (!soloRefrigerados || p.requiere_refrigeracion),
    )
    .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
  const hayFiltros = !!termino || !!categoria || soloRefrigerados

  const confirmarEliminar = () => {
    if (!aEliminar) return
    setErrorEliminar(null)
    eliminar.mutate(aEliminar.id_producto, {
      onSuccess: () => {
        toast.success(`"${aEliminar.nombre}" eliminado`, 'Producto eliminado')
        setAEliminar(null)
      },
      onError: (e) => {
        if (e instanceof ApiError && e.isHandledGlobally) return
        setErrorEliminar(e instanceof ApiError ? e.detail : 'No se pudo eliminar el producto.')
      },
    })
  }

  const columnasStock: Column<Producto>[] = [

          {
            id: 'stock',
            header: 'Stock (inventario)',
            align: 'right',
            cell: (p) => {
              const s = stock.mapa.get(p.id_producto)
              if (stock.isLoading) return <span className="text-fg-subtle">…</span>
              if (!s) return <span className="text-xs text-fg-subtle">Sin inventario</span>
              return (
                <div className="flex flex-col items-end gap-0.5">
                  <span className="font-mono font-semibold">{formatNumero(s.total)}</span>
                  <span className="text-xs text-fg-subtle">
                    {s.ubicaciones} {s.ubicaciones === 1 ? 'ubicación' : 'ubicaciones'}
                  </span>
                </div>
              )
            },
          },
          {
            id: 'estado',
            header: 'Alerta',
            mobile: 'badge',
            cell: (p) => {
              const s = stock.mapa.get(p.id_producto)
              return s && s.peor !== 'STOCK_OK' ? <StockBadge estado={s.peor} /> : null
            },
          },
  ]

  const accionesFila = (p: Producto) =>
    esOperario ? (
      <Button size="sm" variant="ghost" icon="pin" onClick={() => setAsignando(p)} aria-label={`Asignar rack de referencia a ${p.nombre}`}>
        {p.id_rack ? 'Cambiar rack' : 'Asignar rack'}
      </Button>
    ) : (
      <>
        <Button size="sm" variant="ghost" icon="edit" iconOnly aria-label={`Editar ${p.nombre}`} onClick={() => setEditando(p)} />
        <Button
          size="sm"
          variant="ghost"
          icon="trash"
          iconOnly
          aria-label={`Eliminar ${p.nombre}`}
          onClick={() => {
            setErrorEliminar(null)
            setAEliminar(p)
          }}
        />
      </>
    )

  return (
    <>
      <PageHeader
        title="Productos"
        eyebrow="Catálogo"
        description={
          esProveedor
            ? 'Los productos que ofreces a la empresa. Solo tú puedes crearlos y editarlos.'
            : 'Catálogo que registran los proveedores. El stock mostrado proviene del inventario de cada ubicación.'
        }
        {...(esProveedor
          ? {
              actions: (
                <Button icon="plus" onClick={() => setCreando(true)}>
                  Nuevo producto
                </Button>
              ),
            }
          : {})}
      />

      <Card padding="sm" className="mb-4">
        <div className="grid gap-3 sm:grid-cols-[2fr_1fr] lg:grid-cols-[2fr_1fr_auto] lg:items-center">
          <Field label="Buscar por nombre" hideLabel>
            <Input type="search" placeholder="Buscar por nombre…" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
          </Field>
          <Field label="Categoría" hideLabel>
            <Select
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
              placeholder="Todas las categorías"
              options={categorias.map((c) => ({ value: c, label: c }))}
            />
          </Field>
          <Checkbox label="Solo refrigerados" checked={soloRefrigerados} onChange={(e) => setSoloRefrigerados(e.target.checked)} className="sm:col-span-2 lg:col-span-1" />
        </div>
      </Card>

      <DataTable
        caption="Catálogo de productos"
        data={filas}
        loading={q.isLoading}
        error={q.error}
        onRetry={() => void q.refetch()}
        rowKey={(p) => p.id_producto}
        onRowClick={(p) => navigate(`${paths.abastecimiento}?producto=${encodeURIComponent(p.id_producto)}`)}
        empty={
          hayFiltros ? (
            <EmptyState icon="search" title="Sin resultados" description="Ningún producto coincide con los filtros." />
          ) : (
            <EmptyState
              icon="box"
              title="Aún no hay productos"
              description={esProveedor ? 'Registra tu primer producto para que la empresa pueda solicitarlo.' : 'Los productos los registran los proveedores desde su cuenta.'}
              {...(esProveedor
                ? {
                    action: (
                      <Button icon="plus" onClick={() => setCreando(true)}>
                        Crear producto
                      </Button>
                    ),
                  }
                : {})}
            />
          )
        }
        columns={[
          {
            id: 'nombre',
            header: 'Producto',
            mobile: 'title',
            cell: (p) => (
              <div className="min-w-0">
                <p className="font-semibold text-fg">{p.nombre}</p>
                <p className="truncate text-xs text-fg-subtle">{p.marca}</p>
              </div>
            ),
          },
          {
            id: 'categoria',
            header: 'Categoría',
            cell: (p) => (
              <div className="min-w-0">
                <p className="truncate">{p.categoria}</p>
                <p className="truncate text-xs text-fg-subtle">{p.familia}</p>
              </div>
            ),
          },
          { id: 'frio', header: 'Conservación', mobile: 'badge', cell: (p) => <RefrigeracionBadge producto={p} /> },
          ...(esProveedor ? [] : columnasStock),
          { id: 'lead', header: 'Reposición', align: 'right', cell: (p) => <span className="font-mono">{formatNumero(p.lead_time_dias, 'd')}</span> },
          { id: 'vida', header: 'Vida útil', align: 'right', cell: (p) => <span className="font-mono">{formatNumero(p.vida_util_dias, 'd')}</span> },
        ]}
        {...(esProveedor || esOperario ? { actions: accionesFila } : {})}
      />

      <Modal open={creando} onClose={() => setCreando(false)} size="lg" title="Nuevo producto" description="Datos del catálogo. El rack lo asigna después el operario del almacén.">
        <ProductoForm
          onCancel={() => setCreando(false)}
          onSuccess={(p) => {
            setCreando(false)
            navigate(`${paths.abastecimiento}?producto=${encodeURIComponent(p.id_producto)}`)
          }}
        />
      </Modal>

      <Modal open={!!editando} onClose={() => setEditando(null)} size="lg" title="Editar producto" description={editando?.nombre}>
        {editando && <ProductoForm producto={editando} onCancel={() => setEditando(null)} onSuccess={() => setEditando(null)} />}
      </Modal>

      <Modal open={!!asignando} onClose={() => setAsignando(null)} size="lg" title="Rack de referencia" description={asignando?.nombre}>
        {asignando && <RackReferenciaForm producto={asignando} onCancel={() => setAsignando(null)} onSuccess={() => setAsignando(null)} />}
      </Modal>

      <ConfirmDialog
        open={!!aEliminar}
        title="Eliminar producto"
        tone="danger"
        confirmLabel="Eliminar"
        loading={eliminar.isPending}
        onCancel={() => setAEliminar(null)}
        onConfirm={confirmarEliminar}
        description={
          aEliminar && (
            <div className="flex flex-col gap-3">
              <p>
                ¿Eliminar <strong className="text-fg">{aEliminar.nombre}</strong> del catálogo? Esta acción no se puede deshacer.
              </p>
              {stock.mapa.has(aEliminar.id_producto) && (
                <p>Tiene inventario registrado: el sistema puede rechazar la eliminación mientras existan ubicaciones o movimientos.</p>
              )}
              {errorEliminar && <FormAlert title="No se pudo eliminar">{errorEliminar}</FormAlert>}
            </div>
          )
        }
      />
    </>
  )
}
