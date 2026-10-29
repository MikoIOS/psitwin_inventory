import { describe, expect, it } from 'vitest'
import { ApiError } from './client'

describe('Google configuration errors', () => {
  it('explains missing OAuth configuration without exposing arbitrary server errors', async () => {
    const response = (body: unknown) => new Response(JSON.stringify(body), { status: 503, headers: { 'content-type': 'application/json' } })
    const known = await ApiError.fromResponse(response({ detail: { code: 'GOOGLE_NOT_CONFIGURED', detail: 'private diagnostic' } }))
    expect(known.detail).toContain('Google aún no está configurado')
    expect(known.detail).not.toContain('private diagnostic')
    const unknown = await ApiError.fromResponse(response({ detail: 'private diagnostic' }))
    expect(unknown.detail).not.toContain('private diagnostic')
  })
})
