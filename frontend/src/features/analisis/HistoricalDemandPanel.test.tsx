// @vitest-environment jsdom
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'
import { HistoricalDemandPanel } from './HistoricalDemandPanel'

const { useQuery } = vi.hoisted(() => ({ useQuery: vi.fn() }))
vi.mock('@tanstack/react-query', () => ({ useQuery }))

describe('Imported demand panel', () => {
  it('renders real totals, source IDs, imputation and history without fake forecasts', () => {
    useQuery.mockReturnValue({ data: { total: 10, promedio_diario: 5, dias_observados: 2, documentos: 2,
      fecha_inicio: '2025-01-01', fecha_fin: '2025-01-02', advertencias: [],
      serie: [{ fecha: '2025-01-01', cantidad: 3 }, { fecha: '2025-01-02', cantidad: 7 }],
      registros: [{ fecha: '2025-01-01', id_almacen: 'warehouse-source', id_producto: 'product-source', cantidad: 3, es_imputado: true }] } })
    const html = renderToStaticMarkup(<HistoricalDemandPanel tenant="e" warehouse="w" product="p" />)
    expect(html).toContain('warehouse-source')
    expect(html).toContain('product-source')
    expect(html).toContain('Sí')
    expect(html).toContain('Demanda total')
    expect(html).toContain('<polyline')
    expect(html).not.toContain('forecast-band')
    expect(useQuery.mock.lastCall?.[0].queryKey).toContain('e')
    expect(useQuery.mock.lastCall?.[0].queryKey).toContain('w')
  })
  it('does not fabricate history when the API returns no records', () => {
    useQuery.mockReturnValue({ data: { total: 0, promedio_diario: null, dias_observados: 0, documentos: 0, serie: [], registros: [], advertencias: [] } })
    const html = renderToStaticMarkup(<HistoricalDemandPanel tenant="e" warehouse="" product="" />)
    expect(html).toContain('No hay registros importados')
    expect(html).not.toContain('<polyline')
    expect(html).not.toContain('NaN')
  })
  it('shows a query failure and disables queries without a tenant', () => {
    useQuery.mockReturnValue({ isError: true })
    const html = renderToStaticMarkup(<HistoricalDemandPanel tenant="" warehouse="" product="" />)
    expect(html).toContain('No se pudo consultar el historial')
    expect(useQuery.mock.lastCall?.[0].enabled).toBe(false)
  })
})
