/**
 * Inventario de la empresa: stock real por producto y rack (Inventario.stock_actual).
 * Pestañas con los endpoints específicos del backend: todos / stock-bajo / sin-stock / sobre-stock.
 * El backend no filtra por empresa: se acota con useUbicaciones().perteneceAEmpresa(id_rack).
 *
 * La pestaña se refleja en la URL (`/inventario?estado=stock-bajo|sin-stock|sobre-stock`) para poder enlazarla.
 */
import { useState } from 'react'
import { useSearchParams } from 'react-router'
import {
  useInventarios,
  useInventariosSinStock,
  useInventariosSobreStock,
  useInventariosStockBajo,
} from '@/api/inventarios'
import { useProductos } from '@/api/productos'
import type { Inventario } from '@/api/types'
import { useUbicaciones } from '@/api/ubicaciones'
import { useRol } from '@/auth/useRol'
import { Button, Card, EmptyState, Field, Input, Modal, PageHeader, Select } from '@/components/ui'
import { cn } from '@/lib/cn'
import { InventarioCrearForm } from './InventarioForm'
import { InventariosTable } from './InventariosTable'

const PESTANAS = [
  { id: 'todos', label: 'Todos' },
  { id: 'stock-bajo', label: 'Stock bajo' },
  { id: 'sin-stock', label: 'Sin stock' },
  { id: 'sobre-stock', label: 'Sobre stock' },
] as const

type PestanaId = (typeof PESTANAS)[number]['id']

const TONO_CONTADOR: Record<PestanaId, string> = {
  todos: 'bg-surface-3 text-fg-muted',
  'stock-bajo': 'bg-warning-soft text-warning',
  'sin-stock': 'bg-danger-soft text-danger',
  'sobre-stock': 'bg-info-soft text-info',
}

const normalizar = (s: string) => s.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().trim()

export default function InventarioPage() {
  const [params, setParams] = useSearchParams()
  const estadoParam = params.get('estado')
  const pestana: PestanaId = PESTANAS.some((p) => p.id === estadoParam) ? (estadoParam as PestanaId) : 'todos'
  const [busqueda, setBusqueda] = useState('')
  const [idAlmacen, setIdAlmacen] = useState('')
  const [creando, setCreando] = useState(false)

  const ub = useUbicaciones()
  const productos = useProductos()
  const { esOperario } = useRol()
  const consultas = {
    todos: useInventarios(),
    'stock-bajo': useInventariosStockBajo(),
    'sin-stock': useInventariosSinStock(),
    'sobre-stock': useInventariosSobreStock(),
  } satisfies Record<PestanaId, unknown>

  const deEmpresa = (list: Inventario[] | undefined) =>
    list && !ub.isLoading ? list.filter((inv) => ub.perteneceAEmpresa(inv.id_rack)) : undefined

  const q = consultas[pestana]
  const productoPorId = new Map((productos.data ?? []).map((p) => [p.id_producto, p]))
  const termino = normalizar(busqueda)

  const filas = deEmpresa(q.data)
    ?.filter((inv) => {
      if (idAlmacen && ub.porRack.get(inv.id_rack)?.almacen.id_almacen !== idAlmacen) return false
      if (!termino) return true
      const p = productoPorId.get(inv.id_producto)
      return p ? normalizar(`${p.nombre} ${p.marca ?? ""} ${p.categoria}`).includes(termino) : false
    })
    .sort((a, b) => {
      const na = productoPorId.get(a.id_producto)?.nombre ?? ''
      const nb = productoPorId.get(b.id_producto)?.nombre ?? ''
      return na.localeCompare(nb, 'es') || (ub.porRack.get(a.id_rack)?.etiqueta ?? '').localeCompare(ub.porRack.get(b.id_rack)?.etiqueta ?? '', 'es')
    })

  const cambiarPestana = (id: PestanaId) => {
    const next = new URLSearchParams(params)
    if (id === 'todos') next.delete('estado')
    else next.set('estado', id)
    setParams(next, { replace: true })
  }

  const hayFiltros = busqueda !== '' || idAlmacen !== ''
  const sinInventarios = pestana === 'todos' && !hayFiltros

  return (
    <>
      <PageHeader
        title="Inventario"
        eyebrow="Existencias"
        description={
          esOperario
            ? 'Stock real de cada producto por rack. El stock sube con las recepciones y baja con las salidas; aquí defines sus límites.'
            : 'Stock real de cada producto por rack (solo lectura). Abre el historial de un inventario para ver quién lo creó o cambió.'
        }
        {...(esOperario
          ? {
              actions: (
                <Button icon="plus" onClick={() => setCreando(true)}>
                  Nuevo inventario
                </Button>
              ),
            }
          : {})}
      />

      <div className="mb-4 flex flex-col gap-4">
        <div role="group" aria-label="Filtrar por estado de stock" className="-mx-1 flex gap-1 overflow-x-auto px-1 pb-1">
          {PESTANAS.map((p) => {
            const activa = p.id === pestana
            const total = deEmpresa(consultas[p.id].data)?.length
            return (
              <button
                key={p.id}
                type="button"
                aria-pressed={activa}
                onClick={() => cambiarPestana(p.id)}
                className={cn(
                  'inline-flex h-10 shrink-0 items-center gap-2 rounded-[var(--radius-ui)] border px-3.5 text-sm font-medium transition-colors',
                  activa ? 'border-accent bg-accent-soft text-fg' : 'border-border bg-surface text-fg-muted hover:bg-surface-2 hover:text-fg',
                )}
              >
                {p.label}
                <span className={cn('min-w-6 rounded-full px-1.5 py-0.5 text-center font-mono text-xs font-semibold', TONO_CONTADOR[p.id])}>
                  {total === undefined ? '·' : total}
                </span>
              </button>
            )
          })}
        </div>

        <Card padding="sm">
          <div className="grid gap-3 sm:grid-cols-[2fr_1fr]">
            <Field label="Buscar producto" hideLabel>
              <Input type="search" placeholder="Buscar por producto, marca o categoría…" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
            </Field>
            <Field label="Almacén" hideLabel>
              <Select
                value={idAlmacen}
                onChange={(e) => setIdAlmacen(e.target.value)}
                placeholder="Todos los almacenes"
                options={ub.almacenes.map((a) => ({ value: a.id_almacen, label: a.nombre }))}
              />
            </Field>
          </div>
        </Card>
      </div>

      <InventariosTable
        caption="Inventarios"
        data={filas}
        loading={q.isLoading || ub.isLoading}
        error={q.error ?? ub.error}
        onRetry={() => void q.refetch()}
        empty={
          sinInventarios ? (
            <EmptyState
              icon="layers"
              title="Aún no hay inventarios"
              description="Un inventario vincula un producto con un rack y define su stock actual, mínimo y máximo. Los crea el operario del almacén."
              {...(esOperario
                ? {
                    action: (
                      <Button icon="plus" onClick={() => setCreando(true)}>
                        Crear inventario
                      </Button>
                    ),
                  }
                : {})}
            />
          ) : (
            <EmptyState
              icon="check-circle"
              title={hayFiltros ? 'Sin resultados' : `Sin inventarios con ${PESTANAS.find((p) => p.id === pestana)?.label.toLowerCase()}`}
              description={hayFiltros ? 'Prueba con otra búsqueda o almacén.' : 'No hay alertas en esta categoría.'}
            />
          )
        }
      />

      <Modal open={creando} onClose={() => setCreando(false)} size="lg" title="Nuevo inventario" description="Asigna un producto a un rack y define sus niveles de stock.">
        <InventarioCrearForm onCancel={() => setCreando(false)} onSuccess={() => setCreando(false)} />
      </Modal>
    </>
  )
}
