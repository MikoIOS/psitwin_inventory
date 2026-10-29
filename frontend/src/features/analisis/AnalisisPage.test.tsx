// @vitest-environment jsdom
import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'
import AnalisisPage from './AnalisisPage'

const { useQuery } = vi.hoisted(() => ({ useQuery: vi.fn() }))
vi.mock('@tanstack/react-query', () => ({ useQuery }))
vi.mock('@/auth/useEmpresa', () => ({ useEmpresa: () => ({ empresa: { id_empresa: 'e', nombre: 'Empresa demo' } }) }))
vi.mock('@/features/saiki/SaikiSession', () => ({ useSaikiSession: () => ({ pending: false }) }))
vi.mock('react-router', () => ({ useNavigate: () => vi.fn() }))

function queries() {
  useQuery.mockImplementation(({ queryKey }) => {
    const key = queryKey[1]
    const data = key === 'filters' ? { almacenes: [{ id: 'w', nombre: 'Almacén demo 01' }], productos: [{ id: 'p', nombre: 'Producto demo' }] }
      : key === 'historico' ? { total: 7, promedio_diario: 7, documentos: 1, dias_observados: 1, fecha_inicio: '2025-01-01', fecha_fin: '2025-01-01', serie: [{ fecha: '2025-01-01', cantidad: 7 }], registros: [{ fecha: '2025-01-01', id_producto: 'p', id_almacen: 'w', cantidad: 7, es_imputado: false }], advertencias: [] }
      : key === 'metadata' ? { runtime: { validado: true } }
      : key === 'ranking' ? { filas: [], series_totales: 10 } : undefined
    return { data, isPending: false, isError: false }
  })
}

describe('Analysis views', () => {
  it('opens history with one grouping control and no duplicated forecast panels or horizons', () => {
    queries()
    const html = renderToStaticMarkup(<AnalisisPage />)
    expect(html).toContain('Ver historial por')
    expect(html).not.toContain('Días a pronosticar')
    expect(html).not.toContain('Acumulado a')
    expect(html).not.toContain('Demanda prevista y stock registrado')
    expect(html).toContain('Almacén demo 01')
    expect(html).toContain('Producto demo')
    expect(useQuery.mock.calls.some(([q]) => q.queryKey[1] === 'ranking' && q.enabled)).toBe(false)
    expect(useQuery.mock.calls.some(([q]) => q.queryKey[1] === 'forecast' && q.enabled)).toBe(false)
  })
  it('switches to a single forecast horizon without showing historical grouping', async () => {
    queries()
    vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true)
    const container = document.createElement('div')
    const root = createRoot(container)
    try {
      await act(async () => root.render(<AnalisisPage />))
      const button = Array.from(container.querySelectorAll('button')).find(b => b.textContent === 'Pronósticos')!
      await act(async () => button.dispatchEvent(new MouseEvent('click', { bubbles: true })))
      expect(container.textContent).toContain('Días a pronosticar')
      expect(container.textContent).not.toContain('Ver historial por')
      expect(container.textContent).not.toContain('Acumulado a')
      expect(container.querySelectorAll('select')).toHaveLength(4)
    } finally {
      await act(async () => root.unmount())
      vi.unstubAllGlobals()
    }
  })
})
