import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router'
import { describe, expect, it, vi } from 'vitest'
import LoginPage, { loginSchema } from './LoginPage'

vi.mock('@/api/auth', () => ({ useLogin: () => ({ mutate: vi.fn(), isPending: false }) }))
vi.mock('@/components/ui', async original => ({ ...await original<typeof import('@/components/ui')>(), useApiErrorHandler: () => vi.fn() }))

describe('Gmail and PsiTwin password login', () => {
  it('shows only email and PsiTwin password without a Google login button', () => {
    const html = renderToStaticMarkup(<MemoryRouter><LoginPage /></MemoryRouter>)
    expect(html).toContain('Correo Gmail')
    expect(html).toContain('usuario@gmail.com')
    expect(html).toContain('name="password"')
    expect(html).not.toContain('Iniciar sesión con Google')
    expect(html).not.toContain('O ingresa')
  })
  it('preserves legacy issued email credentials and requires a password', () => {
    for (const email of ['ceo@gmail.com', 'CEO@GMAIL.COM', 'operario@example.com', 'proveedor@example.org']) expect(loginSchema.safeParse({ correo: email, password: 'registered-password' }).success).toBe(true)
    for (const email of ['not-an-email', 'ceo@', '']) expect(loginSchema.safeParse({ correo: email, password: 'registered-password' }).success).toBe(false)
    expect(loginSchema.safeParse({ correo: 'ceo@gmail.com', password: '' }).success).toBe(false)
  })
})
