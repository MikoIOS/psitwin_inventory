/**
 * Productos (catálogo). El stock real NO está aquí: usar Inventario.stock_actual.
 * PROVEEDOR: crea / edita / borra los suyos (`GET /productos` le devuelve solo los suyos). OPERARIO: leer y
 * asignar el rack de referencia (`PUT { id_rack }`). EMPRESA: solo lectura.
 *   POST /productos · GET /productos · GET /productos/refrigerados
 *   GET /productos/almacen/{id_almacen} · GET /productos/rack/{id_rack} · GET /productos/categoria/{categoria}
 *   GET /productos/{id} · PUT /productos/{id} · DELETE /productos/{id}
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSession } from '@/auth/SessionContext'
import { api, seg } from './client'
import { norm, requireList } from './normalize'
import { queryKeys } from './queryKeys'
import type { Producto, ProductoCreate, ProductoUpdate } from './types'

export const productosApi = {
  create: async (body: ProductoCreate): Promise<Producto> => norm.producto.one(await api.post('/productos', body)),
  list: async (): Promise<Producto[]> => norm.producto.list(requireList(await api.get('/productos'))),
  listRefrigerados: async (): Promise<Producto[]> => norm.producto.list(await api.get('/productos/refrigerados')),
  listByAlmacen: async (idAlmacen: string): Promise<Producto[]> =>
    norm.producto.list(await api.get(`/productos/almacen/${seg(idAlmacen)}`)),
  listByRack: async (idRack: string): Promise<Producto[]> =>
    norm.producto.list(await api.get(`/productos/rack/${seg(idRack)}`)),
  listByCategoria: async (categoria: string): Promise<Producto[]> =>
    norm.producto.list(await api.get(`/productos/categoria/${seg(categoria)}`)),
  get: async (id: string): Promise<Producto> => norm.producto.one(await api.get(`/productos/${seg(id)}`)),
  update: async (id: string, body: ProductoUpdate | { id_rack: string }): Promise<Producto> =>
    norm.producto.one(await api.put(`/productos/${seg(id)}`, body)),
  remove: (id: string) => api.delete<unknown>(`/productos/${seg(id)}`),
}

/** Productos visibles para la sesión (el backend acota: los de la empresa, o solo los suyos para el PROVEEDOR). */
export function useProductos() {
  const { isAuthenticated } = useSession()
  return useQuery({ queryKey: queryKeys.productos.list(), queryFn: productosApi.list, enabled: isAuthenticated })
}

export function useProductosPorAlmacen(idAlmacen: string | undefined) {
  return useQuery({
    queryKey: queryKeys.productos.byAlmacen(idAlmacen ?? ''),
    queryFn: () => productosApi.listByAlmacen(idAlmacen!),
    enabled: !!idAlmacen,
  })
}

export function useProductosPorRack(idRack: string | undefined) {
  return useQuery({
    queryKey: queryKeys.productos.byRack(idRack ?? ''),
    queryFn: () => productosApi.listByRack(idRack!),
    enabled: !!idRack,
  })
}

export function useProducto(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.productos.detail(id ?? ''),
    queryFn: () => productosApi.get(id!),
    enabled: !!id,
  })
}

/** PROVEEDOR: crea un producto suyo (empresa y proveedor salen del token). */
export function useCreateProducto() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: productosApi.create,
    onSuccess: () => Promise.all([qc.invalidateQueries({ queryKey: queryKeys.productos.all }), qc.invalidateQueries({ queryKey: ['abastecimiento'] })]),
  })
}

export function useUpdateProducto() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: ProductoUpdate | { id_rack: string } }) => productosApi.update(id, body),
    onSuccess: (producto) => {
      void qc.invalidateQueries({ queryKey: ['abastecimiento'] })
      qc.setQueryData(queryKeys.productos.detail(producto.id_producto), producto)
      return qc.invalidateQueries({ queryKey: queryKeys.productos.all })
    },
  })
}

export function useDeleteProducto() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => productosApi.remove(id),
    onSuccess: (_d, id) =>
      Promise.all([
        // Sin el detalle del producto borrado: la página que lo muestra lo volvería a pedir (404) antes de navegar.
        qc.invalidateQueries({ queryKey: queryKeys.productos.all, predicate: (q) => q.queryKey[1] !== 'detail' || q.queryKey[2] !== id }),
        qc.invalidateQueries({ queryKey: queryKeys.inventarios.all }),
      ]),
  })
}
