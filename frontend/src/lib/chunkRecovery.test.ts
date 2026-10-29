import { beforeEach, describe, expect, it, vi } from 'vitest'
import { isChunkLoadError, recoverChunk, installChunkRecovery } from './chunkRecovery'

const failure = new TypeError('error loading dynamically imported module: https://example.test/assets/MonitoreoPage-old.js')
describe('Recuperación de módulos después de un deployment', () => {
  beforeEach(() => sessionStorage.clear())
  it('reconoce errores de importación en Firefox, Chrome y Safari', () => {
    for (const message of [failure.message, 'Failed to fetch dynamically imported module: /assets/old.js', 'Importing a module script failed.']) {
      expect(isChunkLoadError(new TypeError(message))).toBe(true)
    }
    expect(isChunkLoadError(new Error('Cannot read properties of undefined'))).toBe(false)
  })
  it('recarga una sola vez y conserva el límite después de volver a cargar', () => {
    const reload = vi.fn()
    const options = { storage: sessionStorage, reload, online: true, now: 100_000 }
    expect(recoverChunk(failure, options)).toBe(true)
    expect(recoverChunk(failure, { ...options, reload: vi.fn(), now: 100_500 })).toBe(false)
    expect(reload).toHaveBeenCalledTimes(1)
    expect(recoverChunk(failure, { ...options, now: 170_000 })).toBe(true)
  })
  it('no recarga por errores de render, sin conexión o sin almacenamiento', () => {
    const reload = vi.fn()
    const options = { storage: sessionStorage, reload, online: true, now: 100_000 }
    expect(recoverChunk(new Error('Render failed'), options)).toBe(false)
    expect(recoverChunk(failure, { ...options, online: false })).toBe(false)
    expect(recoverChunk(failure, { ...options, storage: { getItem: () => { throw new Error('Blocked') }, setItem: vi.fn() } })).toBe(false)
    expect(reload).not.toHaveBeenCalled()
  })
  it('registra la recuperación para el evento de Vite', () => {
    const listen = vi.spyOn(window, 'addEventListener')
    installChunkRecovery()
    expect(listen).toHaveBeenCalledWith('vite:preloadError', expect.any(Function))
    window.removeEventListener('vite:preloadError', listen.mock.calls[0]![1]!)
    listen.mockRestore()
  })
})
