import { describe, expect, it, vi } from 'vitest'
import { requireList } from './normalize'

describe('query response validation', () => {
  it('accepts real empty lists and paginated lists', () => {
    expect(requireList([])).toEqual([])
    expect(requireList({ items: [{ id: 'real' }] })).toEqual([{ id: 'real' }])
  })
  it.each([null, {}, { detail: 'Server error' }, [null]])('rejects a malformed response instead of inventing an empty list', response => {
    const warning = vi.spyOn(console, 'warn').mockImplementation(() => {})
    expect(() => requireList(response)).toThrow('formato de datos no válido')
    expect(warning).toHaveBeenCalled()
    warning.mockRestore()
  })
})
