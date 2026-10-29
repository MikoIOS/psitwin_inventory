import { inventarioDetalleId } from '@/api/inventarios'
/**
 * Selects reutilizables conectados a la API. Todos aceptan los props de un <select> nativo,
 * así que funcionan con `register()` de react-hook-form o de forma controlada:
 *
 *   <Field label="Almacén" error={errors.id_almacen?.message} required>
 *     <AlmacenSelect {...register('id_almacen')} />
 *   </Field>
 *   <Field label="Zona"><ZonaSelect idAlmacen={watch('id_almacen')} {...register('id_zona')} /></Field>
 *   <Field label="Rack"><RackSelect idZona={watch('id_zona')} {...register('id_rack')} /></Field>
 *
 * En cascada, al cambiar el padre resetea el hijo: `setValue('id_zona', '')`.
 */
import { useAlmacenes } from '@/api/almacenes'
import { ESTADO_RACK_LABEL, etiquetaEstadoOperario, etiquetaTurno, operarioActivo } from '@/api/enums'
import { useInventariosPorProducto } from '@/api/inventarios'
import { useOperarios } from '@/api/operarios'
import { useProductos } from '@/api/productos'
import { useProveedores } from '@/api/proveedores'
import { useRacksPorZona } from '@/api/racks'
import { etiquetaRackConNivel, useUbicaciones } from '@/api/ubicaciones'
import type { Producto } from '@/api/types'
import { useZonasPorAlmacen } from '@/api/zonas'
import type { SelectOption, SelectProps } from '@/components/ui/Select'
import { formatNumero } from '@/lib/format'
import { AsyncSelect } from './AsyncSelect'
import { useQuery } from '@tanstack/react-query'
import { abastecimientoApi } from '@/api/abastecimiento'

type BaseProps = Omit<SelectProps, 'options' | 'children'>

export function NivelSelect({ idRack, ...props }: BaseProps & { idRack: string | undefined }) {
  const query = useQuery({ queryKey: ['niveles', idRack], queryFn: () => abastecimientoApi.niveles(idRack!), enabled: !!idRack })
  return <AsyncSelect {...props} options={query.data?.map(n => ({ value: n.id_nivel, label: `Nivel ${n.numero} · ${n.codigo}` }))}
    loading={query.isLoading} error={query.error} blockedReason={idRack ? undefined : 'Primero elige un rack'} emptyText="Este rack no tiene niveles registrados" resetKey={idRack} />
}

const porLabel = (a: SelectOption, b: SelectOption) => a.label.localeCompare(b.label, 'es')

/* ------------------------------------------------------------------ */

export function AlmacenSelect(props: BaseProps) {
  const q = useAlmacenes()
  const options = q.data?.map((a) => ({ value: a.id_almacen, label: a.nombre })).sort(porLabel)
  return <AsyncSelect {...props} options={options} loading={q.isLoading} error={q.error} emptyText="No hay almacenes" />
}

/* ------------------------------------------------------------------ */

export interface ZonaSelectProps extends BaseProps {
  idAlmacen: string | undefined
}

export function ZonaSelect({ idAlmacen, ...props }: ZonaSelectProps) {
  const q = useZonasPorAlmacen(idAlmacen || undefined)
  const options = q.data
    ?.map((z) => ({ value: z.id_zona, label: z.tipo_zona ? `${z.nombre} — ${z.tipo_zona}` : z.nombre }))
    .sort(porLabel)
  return (
    <AsyncSelect
      {...props}
      options={options}
      loading={q.isLoading}
      error={q.error}
      blockedReason={idAlmacen ? undefined : 'Primero elige un almacén'}
      emptyText="Este almacén no tiene zonas"
      resetKey={idAlmacen}
    />
  )
}

/* ------------------------------------------------------------------ */

export interface RackSelectProps extends BaseProps {
  idZona: string | undefined
  /** Deshabilita racks en MANTENIMIENTO / LLENO / INACTIVO. Por defecto false. */
  soloDisponibles?: boolean
}

export function RackSelect({ idZona, soloDisponibles = false, ...props }: RackSelectProps) {
  const q = useRacksPorZona(idZona || undefined)
  const options = q.data
    ?.slice()
    .sort((a, b) => a.nivel - b.nivel || (a.codigo ?? '').localeCompare(b.codigo ?? '', 'es', { numeric: true }))
    .map((r) => {
      const noDisponible = r.estado !== 'DISPONIBLE' && r.estado !== 'ACTIVO'
      return {
        value: r.id_rack,
        label: `${etiquetaRackConNivel(r)} · cap. ${formatNumero(r.capacidad)}${noDisponible ? ` (${ESTADO_RACK_LABEL[r.estado] ?? r.estado})` : ''}`,
        disabled: soloDisponibles && noDisponible,
      }
    })
  return (
    <AsyncSelect
      {...props}
      options={options}
      loading={q.isLoading}
      error={q.error}
      blockedReason={idZona ? undefined : 'Primero elige una zona'}
      emptyText="Esta zona no tiene racks"
      resetKey={idZona}
    />
  )
}

/* ------------------------------------------------------------------ */

export interface ProductoSelectProps extends BaseProps {
  /** Ids a excluir (ej. productos ya agregados a la orden). */
  excluir?: readonly string[]
  filtrar?: (p: Producto) => boolean
}

export function ProductoSelect({ excluir, filtrar, ...props }: ProductoSelectProps) {
  const q = useProductos()
  const excl = new Set(excluir ?? [])
  const options = q.data
    ?.filter((p) => !excl.has(p.id_producto) && (!filtrar || filtrar(p)))
    .map((p) => ({ value: p.id_producto, label: p.marca ? `${p.nombre} — ${p.marca}` : p.nombre }))
    .sort(porLabel)
  return <AsyncSelect {...props} options={options} loading={q.isLoading} error={q.error} emptyText="No hay productos" />
}

/* ------------------------------------------------------------------ */

export interface OperarioSelectProps extends BaseProps {
  /** Solo operarios ACTIVO. Por defecto true. */
  soloActivos?: boolean
  /** Filtra por almacén (ej. recepción: operario del almacén de la orden). */
  idAlmacen?: string | undefined
  /** Con `idAlmacen`: excluir también a los operarios sin almacén (recepción: el backend lo exige). */
  estrictoAlmacen?: boolean
}

export function OperarioSelect({ soloActivos = true, idAlmacen, estrictoAlmacen = false, ...props }: OperarioSelectProps) {
  const q = useOperarios({ soloActivos, idAlmacen, estrictoAlmacen })
  const options = q.data
    ?.map((o) => ({
      value: o.id_operario,
      label: `${o.apellido}, ${o.nombre} — ${o.cargo} (${etiquetaTurno(o.turno)})${!operarioActivo(o.estado) ? ` · ${etiquetaEstadoOperario(o.estado).toLowerCase()}` : ''}`,
    }))
    .sort(porLabel)
  return (
    <AsyncSelect
      {...props}
      options={options}
      loading={q.isLoading}
      error={q.error}
      emptyText={idAlmacen ? 'No hay operarios activos en este almacén' : 'No hay operarios activos'}
      resetKey={idAlmacen}
    />
  )
}

/* ------------------------------------------------------------------ */

export interface ProveedorSelectProps extends BaseProps {
  /** Solo proveedores ACTIVO. Por defecto true. */
  soloActivos?: boolean
}

export function ProveedorSelect({ soloActivos = true, ...props }: ProveedorSelectProps) {
  const q = useProveedores({ soloActivos })
  const options = q.data?.map((p) => ({ value: p.id_proveedor, label: `${p.nombre} · RUC ${p.ruc}` })).sort(porLabel)
  return (
    <AsyncSelect
      {...props}
      options={options}
      loading={q.isLoading}
      error={q.error}
      emptyText={soloActivos ? 'No hay proveedores activos' : 'No hay proveedores'}
    />
  )
}

/* ------------------------------------------------------------------ */

export interface InventarioSelectProps extends BaseProps {
  valueKind?: 'detalle' | 'inventario'
  idProducto: string | undefined
  /** Limita a racks de este almacén (ej. almacén de la orden en recepciones). */
  idAlmacen?: string | undefined
  /** Texto cuando no hay inventario (útil para ofrecer "crear inventario aquí"). */
  emptyText?: string
}

/** Ubicaciones (inventarios) de un producto: "Zona A › Rack A-01 — stock 40". */
export function InventarioSelect({ valueKind = 'detalle', idProducto, idAlmacen, emptyText, ...props }: InventarioSelectProps) {
  const q = useInventariosPorProducto(idProducto || undefined)
  const ub = useUbicaciones()
  const options = ub.isLoading
    ? undefined
    : q.data
        ?.filter((inv) => {
          const u = ub.porRack.get(inv.id_rack)
          return u && (!idAlmacen || u.almacen.id_almacen === idAlmacen)
        })
        .filter((inv, index, rows) => valueKind === 'detalle' || rows.findIndex(row => row.id_inventario === inv.id_inventario) === index)
        .map((inv) => {
          const u = ub.porRack.get(inv.id_rack)!
          return {
            value: valueKind === 'inventario' ? inv.id_inventario : inventarioDetalleId(inv),
            label: valueKind === 'inventario' ? u.almacen.nombre : `${idAlmacen ? u.etiquetaCorta : u.etiqueta} — stock ${formatNumero(inv.stock_actual)}`,
          }
        })
        .sort(porLabel)
  return (
    <AsyncSelect
      {...props}
      options={options}
      loading={q.isLoading || ub.isLoading}
      error={q.error ?? ub.error}
      blockedReason={idProducto ? undefined : 'Primero elige un producto'}
      emptyText={emptyText ?? (idAlmacen ? 'Sin inventario en este almacén' : 'Este producto no tiene inventario')}
      resetKey={`${idProducto ?? ''}:${idAlmacen ?? ''}`}
    />
  )
}
