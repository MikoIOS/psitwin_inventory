// @vitest-environment jsdom
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { DemandChart } from './DemandChart'

describe('Real-data demand visualization', () => {
  it('does not fabricate a curve or quantiles without data', () => {
    const html = renderToStaticMarkup(<DemandChart history={[]} predictions={[]} />)
    expect(html).toContain('Sin historial no se genera un pronóstico')
    expect(html).not.toContain('<polyline')
    expect(html).not.toContain('forecast-band')
  })
  it('renders the supplied historical, forecast and ordered quantile series', () => {
    const html = renderToStaticMarkup(<DemandChart history={[{ fecha: '2026-10-01', cantidad: 10 }, { fecha: '2026-10-02', cantidad: 20 }]} predictions={[{ fecha: '2026-10-03', cantidad: 15, q10: 5, q50: 14, q90: 25 }, { fecha: '2026-10-04', cantidad: 18, q10: 6, q50: 17, q90: 30 }]} />)
    expect(html).toContain('forecast-band')
    expect((html.match(/<polyline/g) ?? []).length).toBe(3)
    expect(html).toContain('banda central 80 %')
    expect(html).toContain('2 días de 2 disponibles')
    expect(html).not.toContain('NaN')
  })
  it('does not display a prediction band when quantiles are unavailable', () => {
    const html = renderToStaticMarkup(<DemandChart history={[]} predictions={[{ fecha: '2026-10-03', cantidad: 15, q10: null, q50: null, q90: null }]} />)
    expect(html).not.toContain('data-testid="forecast-band"')
    expect(html).not.toContain('NaN')
  })
})
