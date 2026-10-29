import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from './client'
import { inventariosApi, inventarioDetalleId } from './inventarios'

vi.mock('./client', () => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() }, seg: encodeURIComponent }))
const row = { id_inventario: 'header', id_detalle_inventario: 'detail-a', id_producto: 'rice', id_rack: 'rack-a', stock_actual: 41, stock_minimo: 5, stock_maximo: 100 }
describe('Inventory header and rack-detail contract', () => {
  beforeEach(() => vi.resetAllMocks())
  it('lists details and preserves distinct row identities sharing the same header', async () => {
    vi.mocked(api.get).mockResolvedValue([row, { ...row, id_detalle_inventario: 'detail-b', id_rack: 'rack-b', stock_actual: 8 }])
    const rows = await inventariosApi.list()
    expect(api.get).toHaveBeenCalledWith('/detalles-inventario')
    expect(rows.map(inventarioDetalleId)).toEqual(['detail-a', 'detail-b'])
    expect(rows.map(r => r.id_inventario)).toEqual(['header', 'header'])
    expect(rows.map(r => r.stock_actual)).toEqual([41, 8])
  })
  it('creates the warehouse header before its product/rack detail', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ id_inventario: 'header' }).mockResolvedValueOnce(row)
    const body = { id_almacen: 'warehouse', id_producto: 'rice', id_rack: 'rack-a', stock_actual: 41, stock_minimo: 5, stock_maximo: 100 }
    expect(await inventariosApi.create(body)).toMatchObject(row)
    expect(api.post).toHaveBeenNthCalledWith(1, '/inventarios', { id_almacen: 'warehouse' })
    const { id_almacen: _, ...detail } = body
    expect(api.post).toHaveBeenNthCalledWith(2, '/detalles-inventario', { ...detail, id_inventario: 'header' })
  })
  it('does not create a detail if the warehouse header cannot be authorized', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Forbidden warehouse'))
    await expect(inventariosApi.create({ id_almacen: 'foreign', id_producto: 'rice', id_rack: 'rack-a', stock_actual: 0, stock_minimo: 0, stock_maximo: 10 })).rejects.toThrow('Forbidden')
    expect(api.post).toHaveBeenCalledTimes(1)
  })
  it('preserves the chosen level when creating a location', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ id_inventario: 'header' }).mockResolvedValueOnce(row)
    await inventariosApi.create({ id_almacen: 'warehouse', id_producto: 'rice', id_rack: 'rack-a',
      id_nivel: 'level-2', stock_actual: 0, stock_minimo: 0, stock_maximo: 0 })
    expect(api.post).toHaveBeenNthCalledWith(2, '/detalles-inventario', {
      id_inventario: 'header', id_producto: 'rice', id_rack: 'rack-a', id_nivel: 'level-2',
      stock_actual: 0, stock_minimo: 0, stock_maximo: 0,
    })
  })
  it('uses detail endpoints for filters, editing, deletion and history', async () => {
    vi.mocked(api.get).mockResolvedValue([])
    await inventariosApi.listStockBajo(); await inventariosApi.listSinStock(); await inventariosApi.listSobreStock()
    await inventariosApi.listByProducto('rice'); await inventariosApi.listByRack('rack-a')
    await inventariosApi.get('detail-a'); await inventariosApi.historial('detail-a')
    for (const path of ['stock-bajo','sin-stock','sobre-stock','producto/rice','rack/rack-a','detail-a','detail-a/historial']) expect(api.get).toHaveBeenCalledWith('/detalles-inventario/' + path)
    vi.mocked(api.put).mockResolvedValue(row)
    await inventariosApi.update('detail-a', { stock_minimo: 5, stock_maximo: 100 })
    await inventariosApi.remove('detail-a')
    expect(api.put).toHaveBeenCalledWith('/detalles-inventario/detail-a', { stock_minimo: 5, stock_maximo: 100 })
    expect(api.delete).toHaveBeenCalledWith('/detalles-inventario/detail-a')
  })
})
