/**
 * Historial de movimientos (SOLO LECTURA: nunca editar ni eliminar) + registro de movimiento manual.
 *
 * Filtros (reflejados en la URL: `?tipo=&motivo=&operario=&producto=`):
 * se usa el endpoint más específico disponible (producto → operario → tipo → motivo → todos)
 * y el resto de filtros se aplica en cliente. Todo se acota a la empresa autenticada.
 */
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useSearchParams } from 'react-router'
import { MOTIVO_MOVIMIENTO_LABEL, TIPO_MOVIMIENTO_OPCIONES } from '@/api/enums'
import {
  movimientosApi,
  useMovimientosPorMotivo,
  useMovimientosPorOperario,
  useMovimientosPorProducto,
  useMovimientosPorTipo,
} from '@/api/movimientos'
import { queryKeys } from '@/api/queryKeys'
import type { MotivoMovimiento, Movimiento, TipoMovimiento } from '@/api/types'
import { useRol } from '@/auth/useRol'
import { OperarioSelect, ProductoSelect } from '@/components/selects'
import { Button, Card, EmptyState, Field, PageHeader, Select } from '@/components/ui'
import { formatNumero } from '@/lib/format'
import { MovimientoModal } from './MovimientoForm'
import { MovimientosTable, useContextoMovimientos } from './MovimientosTable'

const TIPOS: readonly string[] = ['ENTRADA', 'SALIDA', 'AJUSTE']
const MOTIVOS = Object.keys(MOTIVO_MOVIMIENTO_LABEL) as MotivoMovimiento[]
const MOTIVO_OPCIONES = MOTIVOS.map((m) => ({ value: m, label: MOTIVO_MOVIMIENTO_LABEL[m] }))
const PAGINA = 50

const recientesPrimero = (list: Movimiento[]) =>
  [...list].sort((a, b) => (b.fecha_hora ?? '').localeCompare(a.fecha_hora ?? ''))

export default function MovimientosPage() {
  const [params, setParams] = useSearchParams()
  const [limite, setLimite] = useState(PAGINA)
  const [registrando, setRegistrando] = useState(false)

  const tipoParam = params.get('tipo') ?? ''
  const motivoParam = params.get('motivo') ?? ''
  const tipo = TIPOS.includes(tipoParam) ? (tipoParam as TipoMovimiento) : undefined
  const motivo = (MOTIVOS as string[]).includes(motivoParam) ? (motivoParam as MotivoMovimiento) : undefined
  const operario = params.get('operario') || undefined
  const producto = params.get('producto') || undefined

  // Endpoint base según el filtro más específico.
  const base = producto ? 'producto' : operario ? 'operario' : tipo ? 'tipo' : motivo ? 'motivo' : 'todos'
  const qProducto = useMovimientosPorProducto(base === 'producto' ? producto : undefined)
  const qOperario = useMovimientosPorOperario(base === 'operario' ? operario : undefined)
  const qTipo = useMovimientosPorTipo(base === 'tipo' ? tipo : undefined)
  const qMotivo = useMovimientosPorMotivo(base === 'motivo' ? motivo : undefined)
  const qTodos = useQuery({
    queryKey: queryKeys.movimientos.list(),
    queryFn: movimientosApi.list,
    select: recientesPrimero,
    enabled: base === 'todos',
  })
  const q = { producto: qProducto, operario: qOperario, tipo: qTipo, motivo: qMotivo, todos: qTodos }[base]

  const ctx = useContextoMovimientos()
  const { esEmpresa, esOperario } = useRol()

  const filtrados =
    q.data && !ctx.isLoading
      ? q.data.filter((m) => {
          if (!ctx.perteneceAEmpresa(m)) return false
          if (tipo && m.tipo_movimiento !== tipo) return false
          if (motivo && m.motivo_movimiento !== motivo) return false
          if (operario && base !== 'operario' && m.id_operario !== operario) return false
          // base === 'producto' ya viene filtrado por el backend (incluye inventarios que ya no existan).
          if (producto && base !== 'producto' && ctx.contexto(m).inventario?.id_producto !== producto) return false
          return true
        })
      : undefined

  const setFiltro = (clave: string, valor: string) => {
    const next = new URLSearchParams(params)
    if (valor) next.set(clave, valor)
    else next.delete(clave)
    setParams(next, { replace: true })
    setLimite(PAGINA)
  }

  const hayFiltros = !!(tipo || motivo || operario || producto)
  const visibles = filtrados?.slice(0, limite)

  return (
    <>
      <PageHeader
        title="Movimientos"
        eyebrow="Historial"
        description="Registro inmutable de entradas y salidas de stock, con su autor. Las entradas las genera cada recepción; las salidas las registra el operario."
        {...(esOperario
          ? {
              actions: (
                <Button icon="plus" onClick={() => setRegistrando(true)}>
                  Registrar salida
                </Button>
              ),
            }
          : {})}
      />

      <Card padding="sm" className="mb-4">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1.4fr_1.4fr_auto] lg:items-end">
          <Field label="Tipo">
            <Select value={tipo ?? ''} onChange={(e) => setFiltro('tipo', e.target.value)} placeholder="Todos los tipos" options={TIPO_MOVIMIENTO_OPCIONES} />
          </Field>
          <Field label="Motivo">
            <Select value={motivo ?? ''} onChange={(e) => setFiltro('motivo', e.target.value)} placeholder="Todos los motivos" options={MOTIVO_OPCIONES} />
          </Field>
          {esEmpresa && (
            <Field label="Operario">
              <OperarioSelect
                soloActivos={false}
                value={operario ?? ''}
                onChange={(e) => setFiltro('operario', e.target.value)}
                placeholder="Todos los operarios"
              />
            </Field>
          )}
          <Field label="Producto">
            <ProductoSelect value={producto ?? ''} onChange={(e) => setFiltro('producto', e.target.value)} placeholder="Todos los productos" />
          </Field>
          <Button
            variant="ghost"
            icon="x"
            disabled={!hayFiltros}
            onClick={() => {
              setParams(new URLSearchParams(), { replace: true })
              setLimite(PAGINA)
            }}
          >
            Limpiar
          </Button>
        </div>
      </Card>

      {filtrados && (
        <p className="mb-2 text-sm text-fg-muted" aria-live="polite">
          {formatNumero(filtrados.length)} {filtrados.length === 1 ? 'movimiento' : 'movimientos'}
          {filtrados.length > limite && ` · mostrando los ${formatNumero(limite)} más recientes`}
        </p>
      )}

      <MovimientosTable
        data={visibles}
        loading={q.isLoading || ctx.isLoading}
        error={q.error ?? ctx.error}
        onRetry={() => void q.refetch()}
        empty={
          <EmptyState
            icon="arrows"
            title={hayFiltros ? 'Sin movimientos con estos filtros' : 'Aún no hay movimientos'}
            description={
              hayFiltros
                ? 'Prueba con otra combinación de filtros.'
                : 'Aquí aparecen las salidas registradas y las entradas generadas al recibir mercadería.'
            }
            action={
              !hayFiltros &&
              esOperario && (
                <Button icon="plus" onClick={() => setRegistrando(true)}>
                  Registrar salida
                </Button>
              )
            }
          />
        }
      />

      {filtrados && filtrados.length > limite && (
        <div className="mt-4 flex justify-center">
          <Button variant="secondary" icon="chevron-down" onClick={() => setLimite((l) => l + PAGINA)}>
            Mostrar más
          </Button>
        </div>
      )}

      <MovimientoModal open={registrando} onClose={() => setRegistrando(false)} idProducto={producto} />
    </>
  )
}
