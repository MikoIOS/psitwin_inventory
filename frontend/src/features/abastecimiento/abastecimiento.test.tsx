// @vitest-environment jsdom
import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, it, expect, vi } from 'vitest'
import { subtotalCentimos } from '@/lib/abastecimiento'
import { OfertaSolicitudForm } from '@/features/ordenes/OfertaSolicitudForm'
import { PedidosScatter } from './PedidosHistoryPanel'
import type { PedidoHistorico } from '@/api/abastecimiento'

const { offers } = vi.hoisted(() => ({ offers: vi.fn() }))
vi.mock('@/api/abastecimiento', () => ({ useOfertas: offers }))
vi.mock('@/features/saiki/SaikiSession', () => ({ useSaikiSessionOptional: () => null }))

describe('Abastecimiento', () => {
  it('calculates integer cents with decimal kilograms and half-up rounding', () => {
    expect(subtotalCentimos('20.5', 450)).toBe(9225)
    expect(subtotalCentimos('0.001', 450)).toBe(0)
    expect(subtotalCentimos('0.005', 100)).toBe(1)
    expect(subtotalCentimos('1.0001', 450)).toBeNull()
    expect(subtotalCentimos('-1', 450)).toBeNull()
    expect(subtotalCentimos('20,5', 450)).toBe(9225)
  })
  it('positions points by elapsed time and keeps individual requests without synthetic dates', () => {
    const rows = [0, 1, 10].map((day, i) => ({ fecha: new Date(Date.UTC(2026, 0, day + 1)).toISOString(), cantidad: 10, id_origen: String(i), unidad: 'kg', proveedor: 'Proveedor', estado: 'ENVIADA' })) as PedidoHistorico[]
    const html = renderToStaticMarkup(<PedidosScatter rows={rows} />)
    const doc = new DOMParser().parseFromString(html, 'text/html')
    const circles = [...doc.querySelectorAll('circle')]
    expect(circles).toHaveLength(3)
    const positions = circles.map(c => Number(c.getAttribute('cx')))
    expect((positions[2]! - positions[1]!) / (positions[1]! - positions[0]!)).toBeCloseTo(9)
    expect(html).not.toContain('<polyline')
  })
  it('distinguishes an unavailable offers service from an empty catalog', () => {
    offers.mockReturnValue({ isError: true, isPending: false })
    const html = renderToStaticMarkup(<OfertaSolicitudForm crear={{} as any} idProveedor="v" onCreated={vi.fn()} />)
    expect(html).toContain('No se pudo consultar las ofertas')
    expect(html).not.toContain('No hay ofertas disponibles')
  })
  it('requires review before sending and reuses the key after an uncertain network failure', async () => {
    vi.stubGlobal('IS_REACT_ACT_ENVIRONMENT', true)
    offers.mockReturnValue({ data: [{ id_oferta: 'offer', id_producto: 'p', id_proveedor: 'v', proveedor: 'Proveedor', producto: 'Mango', unidad: 'kg', precio_centimos: 450, cantidad_disponible: 100 }], refetch: vi.fn() })
    const mutateAsync = vi.fn().mockRejectedValue(new Error('network'))
    const element = document.createElement('div'); document.body.append(element)
    const root = createRoot(element)
    try {
      await act(async () => root.render(<OfertaSolicitudForm crear={{ mutateAsync, isPending: false } as any} idProveedor="v" onCreated={vi.fn()} />))
      const input = element.querySelector('input[type="number"]') as HTMLInputElement
      await act(async () => {
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(input, '20.5')
        input.dispatchEvent(new Event('input', { bubbles: true }))
      })
      const submit = () => element.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
      await act(async () => { submit() })
      expect(mutateAsync).not.toHaveBeenCalled()
      expect(element.textContent).toContain('Confirmar solicitud')
      await act(async () => { submit() })
      expect(mutateAsync).toHaveBeenCalledTimes(1)
      const key = mutateAsync.mock.calls[0]![0].clave_idempotencia
      await act(async () => { submit() })
      await act(async () => { submit() })
      expect(mutateAsync).toHaveBeenCalledTimes(2)
      expect(mutateAsync.mock.calls[1]![0].clave_idempotencia).toBe(key)
      expect(mutateAsync.mock.calls[0]![0].lineas[0].cantidad_solicitada).toBe(20.5)
    } finally { await act(async () => root.unmount()); element.remove(); vi.unstubAllGlobals() }
  })
})
