import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import GoogleCallbackPage from './GoogleCallbackPage'
import { api } from '@/api/client'

const apply = vi.hoisted(() => vi.fn())
vi.mock('@/api/auth', () => ({ useAplicarLogin: () => apply, authApi: { fromGoogle: (raw: { access_token: string }) => ({ token: raw.access_token }) } }))
vi.mock('@/api/client', async original => ({ ...await original<typeof import('@/api/client')>(), api: { post: vi.fn() } }))
describe('Google callback navigation', () => {
  let root: Root
  let router: ReturnType<typeof createMemoryRouter>
  beforeEach(() => {
    Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true })
    sessionStorage.clear()
    window.history.replaceState(null, '', '/auth/google/callback?code=test-code&state=test-state')
    root = createRoot(document.createElement('div'))
    router = createMemoryRouter([
      { path: '/auth/google/callback', element: <GoogleCallbackPage /> },
      { path: '/', element: <h1>Dashboard</h1> }, { path: '/registro', element: <h1>Registro</h1> },
    ], { initialEntries: ['/auth/google/callback'] })
  })
  afterEach(() => { act(() => root.unmount()); router.dispose(); vi.clearAllMocks() })
  it('applies the Google session and goes straight to the dashboard', async () => {
    vi.mocked(api.post).mockResolvedValue({ access_token: 'app-jwt', empresa: { nombre_ceo: 'Carlos' } })
    await act(async () => { root.render(<RouterProvider router={router} />) })
    expect(apply).toHaveBeenCalledWith({ token: 'app-jwt' })
    expect(router.state.location.pathname).toBe('/')
    expect(window.location.search).toBe('')
    expect(api.post).toHaveBeenCalledOnce()
  })
  it('takes an unlinked identity to company registration without creating a session', async () => {
    vi.mocked(api.post).mockResolvedValue({ registration_required: true, registration_ticket: 'verified-registration-ticket', verified_email: 'ceo@gmail.com' })
    await act(async () => { root.render(<RouterProvider router={router} />) })
    expect(apply).not.toHaveBeenCalled()
    expect(router.state.location.pathname).toBe('/registro')
    expect(sessionStorage.getItem('psitwin.google.registration')).toBe('verified-registration-ticket')
    expect(sessionStorage.getItem('psitwin.google.email')).toBe('ceo@gmail.com')
  })
})
