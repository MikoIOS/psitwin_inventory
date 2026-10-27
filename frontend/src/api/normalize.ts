/**
 * Normalización de respuestas del backend:
 * - si llega `id` en lugar de `id_almacen` / `id_zona` / `id_rack` / etc., se copia al nombre canónico
 *   (el backend real responde `id` en almacenes y zonas);
 * - almacén: `latitud` / `longitud` llegan como string decimal → number;
 * - recepción: `detalles[]` (esquema único de detalle) se normalizan y se garantiza el array.
 * Todas las funciones de `src/api/<recurso>.ts` pasan sus respuestas por aquí.
 */

import type {
  Almacen,
  DetalleRecepcion,
  DetalleReposicion,
  Empresa,
  Inventario,
  Movimiento,
  Operario,
  OrdenReposicion,
  Producto,
  Proveedor,
  Rack,
  RecepcionMercaderia,
  Zona,
} from './types'

type AnyRecord = Record<string, unknown>

function isRecord(v: unknown): v is AnyRecord {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

/** Copia `id` (o alias) → `key` si `key` no viene en la respuesta. */
export function normalizeId<T>(raw: unknown, key: string, aliases: string[] = []): T {
  if (!isRecord(raw)) return raw as T
  if (raw[key] !== undefined && raw[key] !== null) return raw as T
  for (const alt of ['id', ...aliases]) {
    if (raw[alt] !== undefined && raw[alt] !== null) return { ...raw, [key]: raw[alt] } as T
  }
  return raw as T
}

export function normalizeList<T>(raw: unknown, key: string, aliases: string[] = []): T[] {
  const list = Array.isArray(raw) ? raw : isRecord(raw) && Array.isArray(raw.items) ? (raw.items as unknown[]) : []
  return list.map((item) => normalizeId<T>(item, key, aliases))
}

/** Normalizador por entidad: `norm.almacen.one(raw)` / `norm.almacen.list(raw)`. */
function makeNormalizer<T>(key: string, aliases: string[] = []) {
  return {
    one: (raw: unknown) => normalizeId<T>(raw, key, aliases),
    list: (raw: unknown) => normalizeList<T>(raw, key, aliases),
  }
}


export const norm = {
  empresa: makeNormalizer<Empresa>('id_empresa'),
  almacen: {
    one: (raw: unknown) => normalizeAlmacen(raw),
    list: (raw: unknown) => normalizeList<unknown>(raw, 'id_almacen').map(normalizeAlmacen),
  },
  zona: makeNormalizer<Zona>('id_zona'),
  rack: makeNormalizer<Rack>('id_rack'),
  producto: makeNormalizer<Producto>('id_producto'),
  inventario: {
    one: (raw: unknown) => normalizeInventario(raw),
    list: (raw: unknown) => normalizeList<unknown>(raw, 'id_inventario').map(normalizeInventario),
  },
  operario: makeNormalizer<Operario>('id_operario'),
  movimiento: makeNormalizer<Movimiento>('id_movimiento'),
  proveedor: makeNormalizer<Proveedor>('id_proveedor'),
  orden: makeNormalizer<OrdenReposicion>('id_orden_reposicion', ['id_orden']),
  detalleReposicion: makeNormalizer<DetalleReposicion>('id_detalle_reposicion', ['id_detalle']),
  recepcion: {
    one: (raw: unknown) => normalizeRecepcion(raw),
    list: (raw: unknown) => normalizeList<unknown>(raw, 'id_recepcion').map(normalizeRecepcion),
  },
  detalleRecepcion: makeNormalizer<DetalleRecepcion>('id_detalle_recepcion', ['id_detalle']),
}

/** Inventario puede traer producto/rack anidados con ids antiguos. */
function normalizeInventario(raw: unknown): Inventario {
  const inv = normalizeId<AnyRecord>(raw, 'id_inventario')
  if (!isRecord(inv)) return inv as unknown as Inventario
  const out: AnyRecord = { ...inv }
  if (isRecord(inv.producto)) out.producto = normalizeId(inv.producto, 'id_producto')
  if (isRecord(inv.rack)) out.rack = normalizeId(inv.rack, 'id_rack')
  return out as unknown as Inventario
}

/** Decimal serializado como string ("-12.05") → number. Valores no numéricos → NaN. */
function aNumero(v: unknown): unknown {
  if (typeof v === 'string' && v.trim() !== '') return Number(v)
  return v
}

function normalizeAlmacen(raw: unknown): Almacen {
  const a = normalizeId<AnyRecord>(raw, 'id_almacen')
  if (!isRecord(a)) return a as unknown as Almacen
  return { ...a, latitud: aNumero(a.latitud), longitud: aNumero(a.longitud), area_m2: aNumero(a.area_m2) } as unknown as Almacen
}

function normalizeRecepcion(raw: unknown): RecepcionMercaderia {
  const r = normalizeId<AnyRecord>(raw, 'id_recepcion')
  if (!isRecord(r)) return r as unknown as RecepcionMercaderia
  const detalles = Array.isArray(r.detalles) ? r.detalles.map((d) => normalizeId(d, 'id_detalle_recepcion', ['id_detalle'])) : []
  // Compatibilidad con datos antiguos que usaban `observacion`.
  const observaciones_generales = r.observaciones_generales ?? r.observacion ?? null
  return { ...r, detalles, observaciones_generales } as unknown as RecepcionMercaderia
}
