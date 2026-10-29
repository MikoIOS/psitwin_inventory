import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { SessionProvider, useSession } from './SessionContext'
import { clearToken, getToken } from '@/lib/storage'
import type { Empresa } from '@/api/types'

describe('Stored PsiTwin session', () => {
  let root: Root
  let session: ReturnType<typeof useSession>
  const company = { id_empresa: 'test-company', nombre: 'Empresa', nombre_ceo: 'Carlos' } as Empresa
  const token = `header.${btoa(JSON.stringify({ sub: 'test-company', rol: 'EMPRESA', exp: Date.now() / 1000 + 3600 }))}.signature`
  function Harness() { session = useSession(); return <div>{session.isAuthenticated ? 'authenticated' : 'anonymous'}</div> }
  function mount() {
    root = createRoot(document.createElement('div'))
    act(() => root.render(<QueryClientProvider client={new QueryClient()}><SessionProvider><Harness /></SessionProvider></QueryClientProvider>))
  }
  beforeEach(() => { Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true }); clearToken(); localStorage.clear(); mount() })
  afterEach(() => { act(() => root.unmount()); clearToken() })
  it('restores the complete company session after remount and clears it on logout', () => {
    act(() => session.iniciarSesion(token, { rol: 'EMPRESA', empresa: company }))
    expect(session.isAuthenticated).toBe(true)
    act(() => root.unmount())
    mount()
    expect(session.isAuthenticated).toBe(true)
    expect(session.empresa?.nombre_ceo).toBe('Carlos')
    expect(session.token).toBe(token)
    act(() => session.cerrarSesion())
    expect(session.isAuthenticated).toBe(false)
    expect(session.empresa).toBeNull()
    expect(getToken()).toBeNull()
    expect(localStorage.getItem('psitwin.sesion')).toBeNull()
  })
})
