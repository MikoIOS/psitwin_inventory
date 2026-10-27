/**
 * Query keys centralizadas de TanStack Query.
 *
 * Jerarquía: [recurso, tipoDeConsulta, ...params]. Invalidar `queryKeys.<recurso>.all`
 * invalida TODAS las consultas de ese recurso (listas, filtros y detalles).
 * Nunca escribir keys a mano en componentes: usar siempre este objeto.
 */
import type { EstadoOperario, EstadoOrden, EstadoProveedor, MotivoMovimiento, TipoMovimiento, TurnoOperario } from './types'

type Id = string

export const queryKeys = {
  empresa: {
    all: ['empresa'] as const,
    me: () => ['empresa', 'me'] as const,
  },
  almacenes: {
    all: ['almacenes'] as const,
    list: () => ['almacenes', 'list'] as const,
    byEmpresa: (idEmpresa: Id) => ['almacenes', 'empresa', idEmpresa] as const,
    detail: (id: Id) => ['almacenes', 'detail', id] as const,
  },
  zonas: {
    all: ['zonas'] as const,
    list: () => ['zonas', 'list'] as const,
    byAlmacen: (idAlmacen: Id) => ['zonas', 'almacen', idAlmacen] as const,
    detail: (id: Id) => ['zonas', 'detail', id] as const,
  },
  racks: {
    all: ['racks'] as const,
    list: () => ['racks', 'list'] as const,
    byZona: (idZona: Id) => ['racks', 'zona', idZona] as const,
    detail: (id: Id) => ['racks', 'detail', id] as const,
    disponibles: (idAlmacen: Id, idProducto: Id, cantidad: number) => ['racks', 'disponibles', idAlmacen, idProducto, cantidad] as const,
  },
  productos: {
    all: ['productos'] as const,
    list: (idEmpresa?: Id) => ['productos', 'list', idEmpresa ?? null] as const,
    refrigerados: () => ['productos', 'refrigerados'] as const,
    byAlmacen: (idAlmacen: Id) => ['productos', 'almacen', idAlmacen] as const,
    byRack: (idRack: Id) => ['productos', 'rack', idRack] as const,
    byCategoria: (categoria: string) => ['productos', 'categoria', categoria] as const,
    detail: (id: Id) => ['productos', 'detail', id] as const,
  },
  inventarios: {
    all: ['inventarios'] as const,
    list: () => ['inventarios', 'list'] as const,
    stockBajo: () => ['inventarios', 'stock-bajo'] as const,
    sinStock: () => ['inventarios', 'sin-stock'] as const,
    sobreStock: () => ['inventarios', 'sobre-stock'] as const,
    byProducto: (idProducto: Id) => ['inventarios', 'producto', idProducto] as const,
    byRack: (idRack: Id) => ['inventarios', 'rack', idRack] as const,
    detail: (id: Id) => ['inventarios', 'detail', id] as const,
    historial: (id: Id) => ['inventarios', 'historial', id] as const,
  },
  operarios: {
    all: ['operarios'] as const,
    list: () => ['operarios', 'list'] as const,
    byEmpresa: (idEmpresa: Id) => ['operarios', 'empresa', idEmpresa] as const,
    byEstado: (estado: EstadoOperario) => ['operarios', 'estado', estado] as const,
    byTurno: (turno: TurnoOperario) => ['operarios', 'turno', turno] as const,
    detail: (id: Id) => ['operarios', 'detail', id] as const,
  },
  movimientos: {
    all: ['movimientos'] as const,
    list: () => ['movimientos', 'list'] as const,
    detail: (id: Id) => ['movimientos', 'detail', id] as const,
    byInventario: (idInventario: Id) => ['movimientos', 'inventario', idInventario] as const,
    byProducto: (idProducto: Id) => ['movimientos', 'producto', idProducto] as const,
    byRack: (idRack: Id) => ['movimientos', 'rack', idRack] as const,
    byOperario: (idOperario: Id) => ['movimientos', 'operario', idOperario] as const,
    byTipo: (tipo: TipoMovimiento) => ['movimientos', 'tipo', tipo] as const,
    byMotivo: (motivo: MotivoMovimiento) => ['movimientos', 'motivo', motivo] as const,
  },
  proveedores: {
    all: ['proveedores'] as const,
    list: () => ['proveedores', 'list'] as const,
    byEmpresa: (idEmpresa: Id) => ['proveedores', 'empresa', idEmpresa] as const,
    byEstado: (estado: EstadoProveedor) => ['proveedores', 'estado', estado] as const,
    detail: (id: Id) => ['proveedores', 'detail', id] as const,
  },
  ordenes: {
    all: ['ordenes-reposicion'] as const,
    list: () => ['ordenes-reposicion', 'list'] as const,
    byEmpresa: (idEmpresa: Id) => ['ordenes-reposicion', 'empresa', idEmpresa] as const,
    byAlmacen: (idAlmacen: Id) => ['ordenes-reposicion', 'almacen', idAlmacen] as const,
    byProveedor: (idProveedor: Id) => ['ordenes-reposicion', 'proveedor', idProveedor] as const,
    byEstado: (estado: EstadoOrden) => ['ordenes-reposicion', 'estado', estado] as const,
    detail: (id: Id) => ['ordenes-reposicion', 'detail', id] as const,
    proveedorMe: () => ['ordenes-reposicion', 'proveedor', 'me'] as const,
  },
  detallesReposicion: {
    all: ['detalles-reposicion'] as const,
    byOrden: (idOrden: Id) => ['detalles-reposicion', 'orden', idOrden] as const,
    detail: (id: Id) => ['detalles-reposicion', 'detail', id] as const,
  },
  recepciones: {
    all: ['recepciones'] as const,
    list: () => ['recepciones', 'list'] as const,
    byOrden: (idOrden: Id) => ['recepciones', 'orden', idOrden] as const,
    byOperario: (idOperario: Id) => ['recepciones', 'operario', idOperario] as const,
    detail: (id: Id) => ['recepciones', 'detail', id] as const,
  },
} as const
