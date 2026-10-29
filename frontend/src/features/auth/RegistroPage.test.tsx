// @vitest-environment jsdom
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RegistroPage, { registrationSchema } from './RegistroPage'

vi.mock('@/api/auth', () => ({ useRegister: () => ({ mutate: vi.fn(), isPending: false }), useAplicarLogin: () => vi.fn(), authApi: {} }))
vi.mock('@/components/ui', async original => ({ ...await original<typeof import('@/components/ui')>(), useToast: () => ({ success: vi.fn() }), useApiErrorHandler: () => vi.fn() }))

describe('Company registration', () => {
  beforeEach(() => sessionStorage.clear())
  it('shows business, Gmail and password sections together in the required order', () => {
    const html = renderToStaticMarkup(<MemoryRouter><RegistroPage /></MemoryRouter>)
    expect(html).not.toContain('Continuar con Google')
    expect(html).toContain('name="correo"')
    expect(html).toContain('name="password"')
    expect(html).toContain('name="confirmar"')
    for (const field of ['nombre', 'nombre_ceo', 'ruc', 'sector', 'telefono']) expect(html).toContain(`name="${field}"`)
    expect(html).toContain('placeholder="Nombre"')
    expect(html).toContain('placeholder="Alimentos"')
    expect(html).not.toContain('Crear mi cuenta')
    expect(html.indexOf('company-heading')).toBeLessThan(html.indexOf('email-heading'))
    expect(html.indexOf('email-heading')).toBeLessThan(html.indexOf('password-heading'))
    expect(html).toContain('Registrar empresa')
    expect(html).toContain('Mostrar contraseña')
  })
  it('does not trust browser-stored verification without a backend check', () => {
    sessionStorage.setItem('psitwin.google.registration', 'verified-test-ticket')
    sessionStorage.setItem('psitwin.google.email', 'ceo@gmail.com')
    sessionStorage.setItem('psitwin.google.company', JSON.stringify({ nombre: 'Empresa', nombre_ceo: 'Carlos', ruc: '20100070970', sector: 'Alimentos', telefono: '987654321' }))
    const html = renderToStaticMarkup(<MemoryRouter><RegistroPage /></MemoryRouter>)
    expect(html).toContain('Datos de la empresa')
    expect(html).toContain('name="nombre_ceo"')
    expect(html).not.toContain('apellido')
    expect(html).not.toContain('nombre completo')
    expect(html).toContain('name="password"')
    expect(html).toContain('name="confirmar"')
    expect(html).not.toContain('Usar registro con contraseña')
    expect(html).not.toContain('Ocultar registro con contraseña')
    expect(html).not.toContain('Correo verificado')
    expect(html).not.toContain('value="ceo@gmail.com"')
    expect(html).not.toContain('Comprobando verificación')
  })
  it('validates password policy and confirmation without requiring a CEO surname', () => {
    const body = { correo: 'ceo@gmail.com', nombre: 'Empresa', nombre_ceo: 'Carlos', ruc: '20100070970', sector: 'Alimentos', telefono: '987654321', password: 'secure-password', confirmar: 'secure-password' }
    expect(registrationSchema.safeParse(body).success).toBe(true)
    expect(registrationSchema.safeParse({ ...body, confirmar: 'different-password' }).success).toBe(false)
    expect(registrationSchema.safeParse({ ...body, password: 'short', confirmar: 'short' }).success).toBe(false)
  })
})
