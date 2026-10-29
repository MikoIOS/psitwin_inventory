// @vitest-environment jsdom
import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { createMemoryRouter, Outlet, RouterProvider } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { SaikiSessionProvider, useSaikiSession } from './SaikiSession'
import { saikiApi, type SaikiAnswer } from '@/api/saiki'

const voice = vi.hoisted(() => ({ active: true, voiceEnabled: true, paused: false, speaking: false, listening: true, canListen: true, canSpeak: true, error: '', start: vi.fn(), pause: vi.fn(), resume: vi.fn(), exit: vi.fn(), hold: vi.fn(), release: vi.fn(), speak: vi.fn(), isEnabled: () => true }))
const voiceInput = vi.hoisted(() => ({ onText: (_text: string) => {} }))
vi.mock('./useSaikiVoice', () => ({ useSaikiVoice: (onText: (text: string) => void) => { voiceInput.onText = onText; return voice } }))
vi.mock('@/auth/SessionContext', () => ({ useSession: () => ({ rol: 'EMPRESA', empresa: { id_empresa: 'company' } }) }))
vi.mock('@/api/saiki', () => ({ saikiApi: { ask: vi.fn() } }))

describe('Saiki persists across guided navigation', () => {
  let root: Root
  let router: ReturnType<typeof createMemoryRouter>
  let session: ReturnType<typeof useSaikiSession>
  function Screen() { session = useSaikiSession(); return <div>{session.messages.length}</div> }
  beforeEach(async () => {
    localStorage.clear()
    Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true })
    router = createMemoryRouter([{ element: <SaikiSessionProvider><Outlet /></SaikiSessionProvider>, children: [{ path: '/saiki', element: <Screen /> }, { path: '/inventario', element: <Screen /> }] }], { initialEntries: ['/saiki'] })
    root = createRoot(document.createElement('div'))
    await act(async () => { root.render(<RouterProvider router={router} />) })
  })
  afterEach(() => { act(() => root.unmount()); router.dispose(); vi.clearAllMocks() })
  it('restores the written company history without speaking old messages', async () => {
    act(() => root.unmount())
    localStorage.setItem('psitwin.saiki.history.company', JSON.stringify([{ de: 'usuario', texto: 'Hola' }, { de: 'saiki', texto: 'Hola, soy Saiki.' }]))
    localStorage.setItem('psitwin.saiki.history.foreign', JSON.stringify([{ de: 'saiki', texto: 'PRIVATE' }]))
    root = createRoot(document.createElement('div'))
    await act(async () => { root.render(<RouterProvider router={router} />) })
    expect(session.messages.map(message => message.texto)).toEqual(['Hola', 'Hola, soy Saiki.'])
    expect(voice.speak).not.toHaveBeenCalled()
  })
  it('discards noise before calling the backend or adding messages but keeps unknown valid questions', async () => {
    await act(async () => { await session.send('mmm eh ...') })
    expect(saikiApi.ask).not.toHaveBeenCalled()
    expect(session.messages).toHaveLength(0)
    vi.mocked(saikiApi.ask).mockResolvedValue({ answer: '¿Qué periodo necesitas revisar?', model: 'test', warnings: [] })
    await act(async () => { await session.send('¿Puedes explicarme la rotación?') })
    expect(saikiApi.ask).toHaveBeenCalledOnce()
    expect(session.messages[0]?.texto).toBe('¿Puedes explicarme la rotación?')
  })
  it('keeps the question, answer and voice while changing screen and sends follow-up history', async () => {
    let resolve!: (answer: SaikiAnswer) => void
    vi.mocked(saikiApi.ask).mockImplementationOnce(() => new Promise(done => { resolve = done }))
    let pending!: Promise<void>
    await act(async () => { pending = session.send('Abre inventario') })
    expect(router.state.location.pathname).toBe('/inventario')
    expect(session.messages[0]?.texto).toBe('Abre inventario')
    expect(session.pending).toBe(true)
    expect(session.voice.active).toBe(true)
    await act(async () => { resolve({ answer: 'No hay inventario registrado.', model: 'test', warnings: [] }); await pending })
    expect(session.messages).toHaveLength(2)
    expect(voice.speak).toHaveBeenCalledWith(expect.stringContaining('No hay inventario registrado.'))
    vi.mocked(saikiApi.ask).mockResolvedValueOnce({ answer: 'Respuesta siguiente.', model: 'test', warnings: [] })
    await act(async () => { await session.send('¿Qué debo registrar primero?') })
    expect(vi.mocked(saikiApi.ask).mock.calls[1]?.[0]).toMatchObject({ history: [{ role: 'user', content: 'Abre inventario' }, { role: 'assistant', content: 'No hay inventario registrado.' }], context: { pagina_actual: '/inventario' } })
  })
  it('does not navigate for an informational question and aborts on logout/unmount', async () => {
    let resolve!: (answer: SaikiAnswer) => void
    vi.mocked(saikiApi.ask).mockImplementationOnce(() => new Promise(done => { resolve = done }))
    let pending!: Promise<void>
    await act(async () => { pending = session.send('¿Cómo está mi inventario?') })
    expect(router.state.location.pathname).toBe('/saiki')
    const signal = vi.mocked(saikiApi.ask).mock.calls[0]?.[1]
    act(() => root.render(<div />))
    expect(signal?.aborted).toBe(true)
    await act(async () => { resolve({ answer: 'Respuesta tardía', model: 'test', warnings: [] }); await pending })
    expect(voice.speak).not.toHaveBeenCalled()
  })
  it('keeps a selected device for follow-up questions and clears it for inventory', async () => {
    vi.mocked(saikiApi.ask).mockResolvedValue({ answer: 'Datos del equipo.', model: 'test', warnings: [] })
    await act(async () => { await session.send('Explica este sensor', { id_dispositivo: 'device', sensor_horas: 6 }) })
    await act(async () => { await session.send('¿Y qué recomiendas?') })
    expect(vi.mocked(saikiApi.ask).mock.calls[1]?.[0]).toMatchObject({ id_dispositivo: 'device', sensor_horas: 6 })
    await act(async () => { await session.send('¿Cómo está mi inventario?') })
    expect(vi.mocked(saikiApi.ask).mock.calls[2]?.[0].id_dispositivo).toBeUndefined()
    expect(session.sensorContext).toBeUndefined()
  })
  it('stops immediately, accepts a new question and discards the cancelled reply', async () => {
    let resolve!: (answer: SaikiAnswer) => void
    vi.mocked(saikiApi.ask).mockImplementationOnce(() => new Promise(done => { resolve = done }))
    let old!: Promise<void>
    await act(async () => { old = session.send('Consulta anterior') })
    const signal = vi.mocked(saikiApi.ask).mock.calls[0]![1]!
    act(() => session.stop())
    expect(signal.aborted).toBe(true)
    expect(session.pending).toBe(false)
    vi.mocked(saikiApi.ask).mockResolvedValueOnce({ answer: 'Respuesta nueva', model: 'test', warnings: [] })
    await act(async () => { await session.send('Consulta nueva') })
    await act(async () => { resolve({ answer: 'Respuesta antigua', model: 'test', warnings: [] }); await old })
    expect(session.messages.some(m => m.texto === 'Respuesta antigua')).toBe(false)
    expect(session.messages.some(m => m.texto === 'Respuesta nueva')).toBe(true)
    expect(session.pending).toBe(false)
  })
  it('speaks a typed answer even when the microphone session is inactive', async () => {
    voice.active = false
    vi.mocked(saikiApi.ask).mockResolvedValue({ answer: 'Respuesta escrita y hablada', model: 'test', warnings: [] })
    await act(async () => { await session.send('Explícame mi inventario') })
    expect(voice.speak).toHaveBeenCalledWith('Respuesta escrita y hablada')
    expect(voice.start).not.toHaveBeenCalled()
    voice.active = true
  })
  it('passes selected product and inventory and preserves order on duplicate sends', async () => {
    act(() => { session.setIdProducto('product'); session.setIdInventario('inventory') })
    let resolve!: (answer: SaikiAnswer) => void
    vi.mocked(saikiApi.ask).mockImplementationOnce(() => new Promise(done => { resolve = done }))
    let first!: Promise<void>
    await act(async () => { first = session.send('Revisa este producto'); await session.send('Revisa este producto') })
    expect(saikiApi.ask).toHaveBeenCalledOnce()
    expect(vi.mocked(saikiApi.ask).mock.calls[0]?.[0]).toMatchObject({ id_producto: 'product', id_inventario: 'inventory' })
    expect(voice.release).not.toHaveBeenCalled()
    await act(async () => { resolve({ answer: 'Datos del producto', model: 'test', warnings: [] }); await first })
    expect(session.messages.map(m => m.de)).toEqual(['usuario', 'saiki'])
  })
  it('keeps spoken session commands in the written conversation without sending them to AI', () => {
    act(() => voiceInput.onText('Saiki, pausa'))
    expect(session.messages[0]).toEqual({ de: 'usuario', texto: 'Saiki, pausa' })
    expect(session.messages[1]?.texto).toContain('Sesión de voz en pausa')
    expect(voice.pause).toHaveBeenCalledOnce()
    act(() => voiceInput.onText('Saiki, salir'))
    expect(session.messages[2]).toEqual({ de: 'usuario', texto: 'Saiki, salir' })
    expect(session.messages[3]?.texto).toContain('Sesión de voz terminada')
    expect(voice.exit).toHaveBeenCalledOnce()
    expect(saikiApi.ask).not.toHaveBeenCalled()
  })
})
