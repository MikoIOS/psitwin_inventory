/**
 * Resolución de nombres (producto, proveedor, almacén, operario) a partir de sus ids.
 * Compartido por los módulos de órdenes y recepciones.
 */
import { useAlmacenes } from '@/api/almacenes'
import { useOperarios } from '@/api/operarios'
import { useProductos } from '@/api/productos'
import { useProveedores } from '@/api/proveedores'
import { useSession } from '@/auth/SessionContext'
import type { Almacen, Operario, OrdenReposicion, Producto, Proveedor } from '@/api/types'
import { shortId } from '@/lib/format'

const indexar = <T, K extends keyof T>(list: T[] | undefined, key: K) =>
  new Map<string, T>((list ?? []).map((x) => [String(x[key]), x]))

export function nombreProducto(p: Producto | undefined, id?: string): string {
  if (!p) return id ? `Producto ${shortId(id)}` : '—'
  return p.marca ? `${p.nombre} — ${p.marca}` : p.nombre
}

export function nombreOperario(o: Operario | undefined, id?: string): string {
  if (!o) return id ? `Operario ${shortId(id)}` : '—'
  return `${o.nombre} ${o.apellido}`
}

/** Código corto legible de una orden: "OR-1A2B3C4D". */
export function codigoOrden(o: Pick<OrdenReposicion, 'id_orden_reposicion'> | string): string {
  return `OR-${shortId(typeof o === 'string' ? o : o.id_orden_reposicion)}`
}

export function codigoRecepcion(id: string): string {
  return `RC-${shortId(id)}`
}

export function useNombres() {
  const productosQ = useProductos()
  const proveedoresQ = useProveedores()
  const almacenesQ = useAlmacenes()
  const operariosQ = useOperarios()

  const productos = indexar<Producto, 'id_producto'>(productosQ.data, 'id_producto')
  const proveedores = indexar<Proveedor, 'id_proveedor'>(proveedoresQ.data, 'id_proveedor')
  const almacenes = indexar<Almacen, 'id_almacen'>(almacenesQ.data, 'id_almacen')
  const operarios = indexar<Operario, 'id_operario'>(operariosQ.data, 'id_operario')
  // Lo que el rol no puede listar se completa con su propia sesión (el operario y el proveedor se conocen a sí mismos).
  const { operario: yo, proveedor: miProveedor } = useSession()
  if (yo) operarios.set(yo.id_operario, yo)
  if (miProveedor) proveedores.set(miProveedor.id_proveedor, miProveedor)

  return {
    productos,
    proveedores,
    almacenes,
    operarios,
    producto: (id: string) => nombreProducto(productos.get(id), id),
    proveedor: (id: string) => proveedores.get(id)?.nombre ?? `Proveedor ${shortId(id)}`,
    almacen: (id: string) => almacenes.get(id)?.nombre ?? `Almacén ${shortId(id)}`,
    operario: (id: string) => nombreOperario(operarios.get(id), id),
  }
}
